"""Offline transport, queue, and UI tests. No Archicad process is started."""
import json
import tempfile
import unittest
from pathlib import Path

from sync_bridge.ai_broker import AIBroker, CloudProvider, Proposal, ProviderError, ProviderTimeout
from sync_bridge.bridge import InstanceConflict, SafeBIMBridge
from sync_bridge.connections import ConnectionBoard
from sync_bridge.context import UI_REFRESH, UI_STALE, ContextReady
from sync_bridge.git_fallback import narrow_fetch
from sync_bridge.local_provider import LocalOpenAICompatibleProvider
from sync_bridge.mailbox import GitHubMailbox, OfflineError
from sync_bridge.pipe_win32 import MAX_PIPE_INSTANCES, NamedPipeUnavailable, WindowsNamedPipe, production_transport
from sync_bridge.protocol import ProtocolError, decode_frame, encode_frame, envelope, parse_envelope
from sync_bridge.security import PeerIdentity, admit_peer, sddl_for_user
from sync_bridge.startup import FORBIDDEN_STEPS, simulate_startup
from sync_bridge.store import BridgeStore
from sync_bridge.ui_model import SafeBIMUI


class HttpResponse:
    def __init__(self, status, json_body=None, headers=None):
        self.status = status
        self.json = json_body if json_body is not None else {}
        self.headers = headers or {}


class ScriptedHttp:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def request(self, method, url, headers, body=None):
        self.calls.append((method, url, dict(headers), body))
        if not self.responses:
            raise ConnectionError('no scripted response')
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def bridge(directory, http=None, broker=None):
    store = BridgeStore(Path(directory) / 'bridge.sqlite3')
    mailbox = GitHubMailbox(http or ScriptedHttp([HttpResponse(200, {'messages': []}, {'ETag': 'v1'})]))
    service = SafeBIMBridge(store, mailbox, owner=PeerIdentity('S-1-5-21-1', 'session-7'), broker=broker)
    service.start()
    return service


class ProtocolAndPipeTests(unittest.TestCase):
    def test_frame_roundtrip(self):
        message = envelope('HELLO', {'role': 'palette'}, instance_id='ac-1', request_id='r1', message_id='m1')
        decoded, rest = decode_frame(encode_frame(message))
        self.assertEqual(decoded.kind, 'HELLO')
        self.assertEqual(decoded.protocol_version, 1)
        self.assertEqual(rest, b'')

    def test_truncated_frame_rejected(self):
        message = envelope('HELLO', {'role': 'palette'}, instance_id='ac-1', request_id='r1', message_id='m1')
        with self.assertRaises(ProtocolError):
            decode_frame(encode_frame(message)[:3])

    def test_protocol_version_mismatch_rejected(self):
        message = envelope('HELLO', {}, instance_id='ac-1', request_id='r1', message_id='m1').to_dict()
        parse_envelope(message)
        message['protocolVersion'] = 99
        with self.assertRaises(ProtocolError):
            parse_envelope(message)
        missing = dict(message)
        del missing['protocolVersion']
        with self.assertRaises(ProtocolError):
            parse_envelope(missing)
        invalid = envelope('HELLO', {}, instance_id='ac-1', request_id='r2', message_id='m2').to_dict()
        invalid['kind'] = 'CreateWalls'
        with self.assertRaises(ProtocolError):
            parse_envelope(invalid)
        invalid['kind'] = 'HELLO'
        invalid['payload'] = ['not', 'an', 'object']
        with self.assertRaises(ProtocolError):
            parse_envelope(invalid)

    def test_named_pipe_is_primary_and_rejects_foreign_session(self):
        calls = []

        class Kernel:
            def CreateNamedPipeW(self, name, access, mode, instances, out_size, in_size, timeout, sddl):
                calls.append((name, instances, mode, sddl))
                return 42

            def CloseHandle(self, handle):
                calls.append(('close', handle))

        pipe = WindowsNamedPipe('S-1-5-21-9', 'session-7', kernel=Kernel())
        opened = pipe.open_server()
        self.assertEqual(opened.max_instances, MAX_PIPE_INSTANCES)
        self.assertTrue(opened.reject_remote)
        self.assertIn('(A;;GA;;;S-1-5-21-9)', opened.sddl)
        self.assertNotIn('WD', opened.sddl)
        self.assertEqual(calls[0][1], MAX_PIPE_INSTANCES)
        owner = PeerIdentity('S-1-5-21-9', 'session-7')
        self.assertFalse(admit_peer(owner, PeerIdentity('S-1-5-21-9', 'session-other')))
        self.assertFalse(admit_peer(owner, PeerIdentity('S-1-5-21-other', 'session-7')))
        with self.assertRaises(NamedPipeUnavailable):
            production_transport('S-1-5-21-9', 'session-7')
        pipe.close()

    def test_sddl_requires_a_sid(self):
        with self.assertRaises(ValueError):
            sddl_for_user('Everyone')


class QueueAndRestartTests(unittest.TestCase):
    def test_duplicate_remote_message_creates_one_job(self):
        with tempfile.TemporaryDirectory() as directory:
            service = bridge(directory)
            payload = {'messageId': 'msg-1', 'kind': 'remote-job', 'snapshotId': 'snap-0001',
                       'body': {'recipe': 'mock'}}
            first = service.accept_remote_message(payload)
            second = service.accept_remote_message(payload)
            self.assertTrue(first['jobCreated'])
            self.assertEqual(second['status'], 'DUPLICATE')
            self.assertEqual(len(service.store.jobs()), 1)

    def test_restart_keeps_queue_and_sqlite_reopen(self):
        with tempfile.TemporaryDirectory() as directory:
            service = bridge(directory)
            service.accept_remote_message({'messageId': 'msg-2', 'body': {'recipe': 'mock'}})
            path = service.store.path
            service.stop()
            reopened = BridgeStore(path)
            self.assertEqual(reopened.message('msg-2')['state'], 'ACCEPTED')
            again = SafeBIMBridge(reopened, service.mailbox, owner=service.owner, instance_id='bridge-2')
            again.start()
            self.assertTrue(again.health()['running'])
            self.assertEqual(len(again.store.jobs()), 1)

    def test_corrupt_message_does_not_kill_bridge(self):
        with tempfile.TemporaryDirectory() as directory:
            service = bridge(directory)
            service.store.put_message('bad', 'remote-job', 't', {'body': {}}, 'ACCEPTED', 'inbox')
            service.store.corrupt_message_payload('bad')
            self.assertEqual(service.recover_corrupt('bad')['status'], 'CORRUPT')
            self.assertTrue(service.health()['running'])
            self.assertEqual(service.store.jobs(), [])

    def test_second_bridge_instance_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            service = bridge(directory)
            other = SafeBIMBridge(service.store, service.mailbox, owner=service.owner, instance_id='bridge-2')
            with self.assertRaises(InstanceConflict):
                other.start()


class MailboxTests(unittest.TestCase):
    def test_internet_lost_during_fetch_and_publish_then_reconnect(self):
        with tempfile.TemporaryDirectory() as directory:
            http = ScriptedHttp([ConnectionError('down'), HttpResponse(200, {'messages': []}, {'ETag': 'v2'})])
            service = bridge(directory, http)
            service.connections.set('ARCHICAD', 'CONNECTING', 'waiting')
            service.queue_result('job-1', {'status': 'mock'})
            lost = service.tick()
            self.assertEqual(lost['status'], 'OFFLINE')
            self.assertEqual(service.connections.get('ARCHICAD')['status'], 'CONNECTING')
            self.assertNotEqual(service.connections.get('ARCHICAD')['detail'], 'нет интернета')
            self.assertEqual(service.connections.get('BRIDGE')['status'], 'CONNECTED')
            self.assertEqual(service.store.pending_outbox()[0]['state'], 'PENDING')
            http.responses.append(HttpResponse(200, {}, {}))
            restored = service.tick()
            self.assertEqual(restored['status'], 'CHANGED')
            self.assertEqual(service.store.pending_outbox(), [])
            self.assertEqual(service.store.message('result-job-1')['state'], 'SENT')

    def test_publish_loss_keeps_retry_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            http = ScriptedHttp([ConnectionError('down'), HttpResponse(200, {}, {})])
            service = bridge(directory, http)
            service.queue_result('job-9', {'status': 'mock'})
            first = service.flush_outbox()
            self.assertEqual(first[0]['status'], 'QUEUED')
            self.assertEqual(service.store.message('result-job-9')['retry_count'], 1)
            service.flush_outbox()
            calls_after_success = len(http.calls)
            service.flush_outbox()
            self.assertEqual(service.store.message('result-job-9')['state'], 'SENT')
            self.assertEqual(len(http.calls), calls_after_success)
            self.assertEqual(service.store.pending_outbox(), [])

    def test_stale_etag_and_duplicate_github_delivery(self):
        message = {'messageId': 'same', 'body': {'recipe': 'mock'}}
        http = ScriptedHttp([
            HttpResponse(200, {'messages': [message]}, {'ETag': '"1"'}),
            HttpResponse(304, {}, {'ETag': '"1"'}),
            HttpResponse(200, {'messages': [message, message]}, {'ETag': '"1"'}),
        ])
        with tempfile.TemporaryDirectory() as directory:
            service = bridge(directory, http)
            first = service.tick()
            self.assertEqual(first['accepted'][0]['jobCreated'], True)
            second = service.tick()
            self.assertEqual(second['status'], 'NOT_MODIFIED')
            third = service.tick()
            self.assertTrue(all(item['status'] == 'DUPLICATE' for item in third['accepted']))
            self.assertEqual(len(service.store.jobs()), 1)

    def test_rate_limit_backoff_and_single_poll(self):
        http = ScriptedHttp([HttpResponse(429, {}, {'Retry-After': '9'})])
        mailbox = GitHubMailbox(http)
        from sync_bridge.polling import PollScheduler
        scheduler = PollScheduler(mailbox)
        limited = scheduler.poll_once()
        self.assertEqual(limited['status'], 'RATE_LIMITED')
        self.assertGreaterEqual(limited['retryAfter'], 9)
        self.assertLessEqual(limited['retryAfter'], 300)
        self.assertGreater(limited['retryAfter'], 0)

    def test_auth_expired_keeps_local_ready(self):
        http = ScriptedHttp([HttpResponse(401, {'error': 'bad credentials'}, {})])
        with tempfile.TemporaryDirectory() as directory:
            service = bridge(directory, http)
            result = service.tick()
            self.assertEqual(result['status'], 'NEEDS_AUTH')
            self.assertTrue(service.health()['running'])
            self.assertTrue(service.needs_auth)
            self.assertEqual(service.connections.get('BRIDGE')['status'], 'CONNECTED')

    def test_malformed_remote_payload_creates_no_job(self):
        http = ScriptedHttp([HttpResponse(200, {'messages': [{'nope': 1}, 'bad']}, {'ETag': 'v'})])
        with tempfile.TemporaryDirectory() as directory:
            service = bridge(directory, http)
            result = service.tick()
            self.assertTrue(all(item['jobCreated'] is False for item in result['accepted']))
            self.assertEqual(service.store.jobs(), [])

    def test_git_fallback_is_narrow_and_redacts_auth(self):
        seen = []

        def runner(argv):
            seen.append(argv)
            return type('R', (), {'code': 128, 'stderr': 'could not read Username ghp_SECRETVALUE'})()

        result = narrow_fetch('refs/heads/bridge-mailbox', runner)
        self.assertEqual(result['status'], 'NEEDS_AUTH')
        self.assertEqual(seen[0], ['git', 'fetch', 'origin', 'refs/heads/bridge-mailbox'])
        self.assertNotIn('pull', seen[0])
        self.assertNotIn('ghp_SECRETVALUE', result['stderr'])
        self.assertIn('[redacted]', result['stderr'])


class ContextTests(unittest.TestCase):
    def test_idempotent_request_wrong_project_cancel_and_order(self):
        with tempfile.TemporaryDirectory() as directory:
            service = bridge(directory)
            request = {'requestId': 'ctx-1', 'logicalProjectId': 'house', 'requestedScope': 'selection'}
            first = service.context_request(request)
            second = service.context_request(request)
            self.assertEqual(first, second)
            self.assertEqual(service.context.lease, 'VALID')
            self.assertIn('Контекст #', service.context.ui_banner)
            wrong = ContextReady(1, 'ctx-1', 'snap-0099', 'other', 'hash', 't', {'source': 'mock'}, 99)
            self.assertEqual(service.apply_context_ready(wrong), 'CONTEXT_ERROR')
            service.context.cancel('ctx-1')
            late = ContextReady(1, 'ctx-1', 'snap-0100', 'house', 'hash', 't', {'source': 'mock'}, 100)
            self.assertEqual(service.apply_context_ready(late), 'CONTEXT_ERROR')
            service.context.lease = 'VALID'
            service.context.current = ContextReady(1, 'ctx-2', 'snap-0003', 'house', 'h', 't', {}, 3)
            service.store.put_context_request('ctx-2', 'house', 'selection', 'VALID', 't')
            older = ContextReady(1, 'ctx-2', 'snap-0001', 'house', 'h', 't', {}, 1)
            self.assertEqual(service.apply_context_ready(older), 'IGNORED_STALE')
            service.context.mark_changed()
            self.assertEqual(service.context.ui_banner, UI_STALE)
            self.assertEqual(service.context.refresh_label(), UI_REFRESH)

    def test_duplicate_instance_id_conflicts_and_foreign_session_is_denied(self):
        with tempfile.TemporaryDirectory() as directory:
            service = bridge(directory)
            owner = service.owner
            hello = envelope('HELLO', {'logicalProjectId': 'P1'}, instance_id='ac-a', request_id='h1', message_id='hm1').to_dict()
            service.handshake(hello, owner)
            other = envelope('HELLO', {'logicalProjectId': 'P2'}, instance_id='ac-b', request_id='h2', message_id='hm2').to_dict()
            service.handshake(other, owner)
            self.assertEqual(service.store.client('ac-a')['connection_state'], 'CONNECTED')
            self.assertEqual(service.store.client('ac-b')['connection_state'], 'CONNECTED')
            with self.assertRaises(InstanceConflict):
                service.handshake(hello, owner)
            with self.assertRaises(PermissionError):
                service.handshake(other, PeerIdentity('S-1-5-21-1', 'other-session'))
            with self.assertRaises(PermissionError):
                service.handshake(other, PeerIdentity('S-1-5-21-other', 'session-7'))


class AIAndUITests(unittest.TestCase):
    def test_cloud_timeout_uses_local_and_never_executes(self):
        class Cloud:
            def health(self):
                return {'status': 'CONNECTED'}

            def complete(self, prompt):
                raise ProviderTimeout('cloud timeout')

        class Local:
            def health(self):
                return {'status': 'CONNECTED'}

            def complete(self, prompt):
                return {'kind': 'mock_recipe', 'text': 'показать сводку, не создавать элементы'}

        broker = AIBroker(CloudProvider(Cloud()), LocalOpenAICompatibleProvider(Local()))
        proposal = broker.complete('сводка')
        self.assertEqual(broker.last_route, 'local')
        self.assertFalse(proposal.executable)
        self.assertIsInstance(proposal, Proposal)

    def test_local_unavailable_has_no_bim_side_effect(self):
        class Down:
            def health(self):
                raise ConnectionError('down')

            def complete(self, prompt):
                raise ConnectionError('cloud down')

        broker = AIBroker(CloudProvider(Down()), LocalOpenAICompatibleProvider(None))
        with self.assertRaises(ProviderError):
            broker.complete('сводка')
        self.assertEqual(broker.last_route, 'unavailable')
        provider = LocalOpenAICompatibleProvider(None, ttl_seconds=10)
        self.assertEqual(provider.lazy_start(), 'UNAVAILABLE')
        provider.cancel()
        self.assertEqual(provider.fallback_status, 'CANCELLED')
        self.assertEqual(provider.unload(), 'UNLOADED')

    def test_ui_toggles_and_does_not_show_tapir_when_healthy(self):
        ui = SafeBIMUI()
        ui.connections.set('BRIDGE', 'CONNECTED')
        ui.connections.set('REMOTE', 'CONNECTED')
        ui.set_online()
        ui.click('command')
        self.assertTrue(ui.command_open)
        ui.click('command')
        self.assertFalse(ui.command_open)
        ui.click('ai')
        ui.on_ai_response(Proposal('proposal', 'готово', 'cloud'))
        self.assertTrue(ui.ai_open)
        ui.on_future_code_success()
        self.assertFalse(ui.code_open)
        rendered = ui.render()
        self.assertIn('ИИ: ● Онлайн', rendered)
        self.assertIn('Проект: —', rendered)
        self.assertNotIn('Test_House', rendered)
        self.assertIn('Archicad:', rendered)
        self.assertIn('Bridge:', rendered)
        self.assertIn('GitHub:', rendered)
        self.assertIn('\nAI:', rendered)
        self.assertNotIn('Tapir', rendered)
        self.assertNotIn('CreateWalls', rendered)
        ui.set_offline_ai()
        offline_line = next(line for line in ui.render().splitlines() if line.startswith('ИИ:'))
        self.assertNotIn('●', offline_line)
        self.assertIn('Офлайн', offline_line)
        self.assertEqual(ui.connections.get('AI')['status'], 'OFFLINE')
        self.assertEqual(ui.connections.get('ARCHICAD')['status'], 'CONNECTING')
        self.assertEqual(ui.connections.get('REMOTE')['status'], 'CONNECTED')
        ui.connections.set('ARCHICAD', 'CONNECTED', 'ac-1')
        ui.connections.mark_internet_offline()
        self.assertEqual(ui.connections.get('ARCHICAD')['status'], 'CONNECTED')
        self.assertFalse(ui.connections.confused())
        ui.show_error('Нет связи с интернетом. Локальная очередь сохранена.')
        self.assertIn('Нет связи', ui.render())
        self.assertNotIn('TECHNICAL', ui.render())

    def test_zero_setup_startup_survives_missing_auth(self):
        started = simulate_startup(auth_ok=False)
        self.assertEqual(started['local'], 'LOCAL_READY')
        self.assertEqual(started['remote'], 'REMOTE_NEEDS_AUTH')
        self.assertEqual(started['archicad'], 'ARCHICAD_DISCONNECTED')
        self.assertNotEqual(started['local'], 'LOCAL_ERROR')
        self.assertIn('named-pipe-handshake', started['steps'])
        self.assertTrue(started['ready'])
        for forbidden in FORBIDDEN_STEPS:
            self.assertNotIn(forbidden, started['steps'])
        self.assertIn('Локальный Safe BIM', started['error'])

    def test_package_does_not_import_bim_runtime(self):
        root = Path(__file__).resolve().parents[1] / 'sync_bridge'
        for path in root.glob('*.py'):
            text = path.read_text(encoding='utf-8')
            self.assertNotIn('safe_bim_layer', text)
            self.assertNotIn('safe_bim_operations', text)
            self.assertNotIn('MutationGateway', text)
            self.assertNotIn('ExecuteAddOnCommand', text)


if __name__ == '__main__':
    unittest.main()
