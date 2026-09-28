from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from sync_bridge.host import (
    BridgeHost,
    DefaultGitHubTokenProvider,
    HostConfig,
    TapirReadTransport,
)
from sync_bridge.security import PeerIdentity


class FakePipe:
    def __init__(self):
        self.handle = 123
        self.closed = False

    def close(self):
        self.closed = True
        self.handle = None


class FakeTransport:
    def __init__(self, binding=None, error=None):
        self.value = binding or {
            'instanceId': 'archicad-default',
            'logicalProjectId': 'project-a',
            'applicationVersion': '29',
        }
        self.error = error

    def binding(self):
        if self.error is not None:
            raise self.error
        return dict(self.value)

    def call(self, command, params):
        raise AssertionError('context capture was not requested by bootstrap test')


class FakeTapirBackend:
    def __init__(self, project):
        self.project = project
        self.calls = []

    def _tapir(self, name):
        self.calls.append(name)
        return lambda params=None: dict(self.project)


class RuntimeBootstrapTests(unittest.TestCase):
    def test_config_defaults_to_localappdata_and_persistent_db(self):
        env = {'LOCALAPPDATA': r'C:\Users\Example\AppData\Local'}
        config = HostConfig.from_environment(env)
        self.assertEqual(config.data_dir, Path(env['LOCALAPPDATA']) / 'SafeBIM')
        self.assertEqual(config.db_path, config.data_dir / 'bridge.sqlite3')
        self.assertEqual(config.github_repo, 'safe-bim-bridge')
        self.assertEqual(config.github_root, 'safe-bim-mailbox')

    def test_token_provider_prefers_explicit_environment_without_runner(self):
        calls = []

        def runner(*args, **kwargs):
            calls.append((args, kwargs))
            raise AssertionError('runner must not be called')

        env = {'SAFE_BIM_GITHUB_TOKEN': 'from-env'}
        provider = DefaultGitHubTokenProvider(env=env, runner=runner)
        self.assertEqual(provider(), 'from-env')
        self.assertEqual(provider.source, 'environment')
        self.assertEqual(calls, [])

    def test_token_provider_reuses_existing_gh_login_without_env_mutation(self):
        env = {}
        calls = []

        def runner(command, **kwargs):
            calls.append((command, kwargs))
            return SimpleNamespace(returncode=0, stdout='from-gh\n')

        provider = DefaultGitHubTokenProvider(env=env, runner=runner)
        self.assertEqual(provider(), 'from-gh')
        self.assertEqual(provider(), 'from-gh')
        self.assertEqual(provider.source, 'gh-cli')
        self.assertEqual(env, {})
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0], ['gh', 'auth', 'token', '-h', 'github.com'])

    def test_token_provider_missing_login_is_nonfatal(self):
        def runner(command, **kwargs):
            return SimpleNamespace(returncode=1, stdout='')

        provider = DefaultGitHubTokenProvider(env={}, runner=runner)
        self.assertIsNone(provider())
        self.assertEqual(provider.source, 'none')

    def test_tapir_binding_hashes_local_project_identity(self):
        backend = FakeTapirBackend({
            'projectPath': r'C:\Users\Secret\Project.pln',
            'projectName': 'Project',
            'isUntitled': False,
            'isTeamwork': False,
        })
        transport = TapirReadTransport(backend=backend)
        binding = transport.binding()
        self.assertEqual(binding['instanceId'], 'archicad-default')
        self.assertTrue(binding['logicalProjectId'].startswith('live-local-'))
        self.assertNotIn('Secret', binding['logicalProjectId'])
        self.assertNotIn('Project.pln', binding['logicalProjectId'])
        self.assertEqual(backend.calls, ['GetProjectInfo'])

    def test_tapir_transport_refuses_non_s24_command_before_backend(self):
        backend = FakeTapirBackend({})
        transport = TapirReadTransport(backend=backend)
        with self.assertRaises(RuntimeError):
            transport.call('CreateWalls', {})
        self.assertEqual(backend.calls, [])

    def test_host_starts_with_pipe_store_bridge_and_live_binding(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp)
            config = HostConfig(data_dir=data, db_path=data / 'bridge.sqlite3')
            pipe = FakePipe()
            transport = FakeTransport()
            host = BridgeHost(
                config,
                identity=PeerIdentity('S-1-5-21-test', '7'),
                token_provider=lambda: None,
                pipe_factory=lambda sid, session: pipe,
                transport=transport,
            )
            try:
                status = host.start()
                self.assertTrue(status['running'])
                self.assertTrue(status['pipeOpen'])
                self.assertEqual(status['archicad']['logicalProjectId'], 'project-a')
                client = host.store.client('archicad-default')
                self.assertEqual(client['connection_state'], 'CONNECTED')
                self.assertEqual(client['logical_project_id'], 'project-a')
                self.assertEqual(int(client['epoch']), host.bridge.epoch)
            finally:
                host.close()
            self.assertTrue(pipe.closed)
            self.assertFalse(host.running)

    def test_archicad_absence_does_not_prevent_local_host_start(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp)
            config = HostConfig(data_dir=data, db_path=data / 'bridge.sqlite3')
            pipe = FakePipe()
            host = BridgeHost(
                config,
                identity=PeerIdentity('S-1-5-21-test-missing', '8'),
                token_provider=lambda: None,
                pipe_factory=lambda sid, session: pipe,
                transport=FakeTransport(error=ConnectionError('not running')),
            )
            try:
                status = host.start()
                self.assertTrue(status['running'])
                self.assertIsNone(status['archicad'])
                self.assertEqual(
                    status['bridge']['connections']['ARCHICAD']['status'], 'OFFLINE')
            finally:
                host.close()

    def test_refresh_rebinds_same_instance_when_project_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp)
            config = HostConfig(data_dir=data, db_path=data / 'bridge.sqlite3')
            pipe = FakePipe()
            transport = FakeTransport()
            host = BridgeHost(
                config,
                identity=PeerIdentity('S-1-5-21-test-change', '9'),
                token_provider=lambda: None,
                pipe_factory=lambda sid, session: pipe,
                transport=transport,
            )
            try:
                host.start()
                transport.value = {
                    'instanceId': 'archicad-default',
                    'logicalProjectId': 'project-b',
                    'applicationVersion': '29',
                }
                refreshed = host.refresh_archicad()
                self.assertEqual(refreshed['status'], 'ARCHICAD_CONNECTED')
                self.assertEqual(refreshed['logicalProjectId'], 'project-b')
                client = host.store.client('archicad-default')
                self.assertEqual(client['logical_project_id'], 'project-b')
                self.assertEqual(client['connection_state'], 'CONNECTED')
            finally:
                host.close()


if __name__ == '__main__':
    unittest.main()
