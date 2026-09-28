"""S1.1 consistency contracts. Offline only. Mailbox idempotency is not reimplemented here."""
import json
import tempfile
import unittest
from pathlib import Path

from sync_bridge.ai_broker import AIBroker, Proposal
from sync_bridge.bridge import InjectedCrash, SafeBIMBridge
from sync_bridge.context import ContextReady
from sync_bridge.local_provider import LocalOpenAICompatibleProvider
from sync_bridge.mailbox import GitHubMailbox
from sync_bridge.protocol import envelope
from sync_bridge.security import PeerIdentity
from sync_bridge.startup import simulate_startup, status_board
from sync_bridge.store import BridgeStore
from sync_bridge.ui_model import SafeBIMUI
from tests_sync.test_s1_reliability import reopen
from tests_sync.test_sync_bridge import ScriptedHttp


def service_in(directory):
    store = BridgeStore(Path(directory) / 'bridge.sqlite3')
    service = SafeBIMBridge(store, GitHubMailbox(ScriptedHttp([])), owner=PeerIdentity('S-1-5-21-1', 'session-7'))
    service.start()
    return service


class ContextConsistencyTests(unittest.TestCase):
    def test_capturing_restart_does_not_start_second_capture(self):
        with tempfile.TemporaryDirectory() as directory:
            service = service_in(directory)
            request = {'requestId': 'ctx-crash', 'logicalProjectId': 'house', 'requestedScope': 'selection'}

            def boom():
                raise InjectedCrash('capture already assigned')

            service.context.fault_after_capture_assigned = boom
            with self.assertRaises(InjectedCrash):
                service.context_request(request)
            stored = service.store.context_request('ctx-crash')
            self.assertEqual(stored['state'], 'CAPTURING')
            self.assertIsNone(stored['response'])
            captures = service.store.meta('context_captures')
            assigned = service.store.meta('context_op_capture:ctx-crash')
            snapshot_id = assigned.split(':', 1)[1]
            jobs = len(service.store.jobs())
            restarted = reopen(service, ScriptedHttp([]))
            continued = restarted.context_request(request)
            self.assertEqual(restarted.store.meta('context_captures'), captures)
            self.assertEqual(continued['snapshotId'], snapshot_id)
            self.assertEqual(continued['logicalProjectId'], 'house')
            self.assertEqual(len(restarted.store.jobs()), jobs)
            again = restarted.context_request(request)
            self.assertEqual(again['snapshotId'], snapshot_id)
            self.assertEqual(restarted.store.meta('context_captures'), captures)

    def test_open_capturing_operation_is_resumed_without_a_new_capture(self):
        with tempfile.TemporaryDirectory() as directory:
            service = service_in(directory)
            service.store.put_context_request('ctx-open', 'house', 'selection', 'CAPTURING', 't')
            before = service.store.meta('context_captures')
            restored = service.context_request({
                'requestId': 'ctx-open', 'logicalProjectId': 'house', 'requestedScope': 'selection'})
            self.assertEqual(restored['state'], 'CAPTURING')
            self.assertTrue(restored['resumed'])
            self.assertEqual(service.store.meta('context_captures'), before)
            self.assertIsNone(service.store.context_request('ctx-open')['response'])
            self.assertEqual(service.store.jobs(), [])

    def test_request_id_payload_conflict_does_not_capture(self):
        with tempfile.TemporaryDirectory() as directory:
            service = service_in(directory)
            original = {
                'requestId': 'ctx-1', 'logicalProjectId': 'P1',
                'requestedScope': 'selection', 'instanceId': 'AC-A',
            }
            service.context_request(original)
            captures = service.store.meta('context_captures')
            jobs = len(service.store.jobs())
            for changed in (
                {'logicalProjectId': 'P2'},
                {'requestedScope': 'story'},
                {'instanceId': 'AC-B'},
            ):
                conflict = service.context_request({**original, **changed})
                self.assertEqual(conflict['kind'], 'REQUEST_ID_CONFLICT')
            self.assertEqual(service.store.meta('context_captures'), captures)
            self.assertEqual(len(service.store.jobs()), jobs)
            stored = service.store.context_request('ctx-1')
            self.assertEqual(stored['project_id'], 'P1')
            self.assertEqual(stored['requested_scope'], 'selection')
            self.assertEqual(stored['instance_id'], 'AC-A')
            self.assertEqual(stored['state'], 'VALID')


class InstanceIsolationTests(unittest.TestCase):
    def test_context_request_never_uses_the_other_instance_project(self):
        with tempfile.TemporaryDirectory() as directory:
            service = service_in(directory)
            owner = service.owner
            service.handshake(envelope('HELLO', {'logicalProjectId': 'P1'}, instance_id='AC-A', request_id='h1', message_id='hm1').to_dict(), owner)
            service.handshake(envelope('HELLO', {'logicalProjectId': 'P2'}, instance_id='AC-B', request_id='h2', message_id='hm2').to_dict(), owner)
            first = service.context_request({
                'requestId': 'ra', 'logicalProjectId': 'P1', 'requestedScope': 'selection', 'instanceId': 'AC-A'})
            second = service.context_request({
                'requestId': 'rb', 'logicalProjectId': 'P2', 'requestedScope': 'selection', 'instanceId': 'AC-B'})
            self.assertEqual(service.context.by_instance['AC-A'].logical_project_id, 'P1')
            self.assertEqual(service.context.by_instance['AC-B'].logical_project_id, 'P2')
            service.context.current = ContextReady(1, 'poison', 'snap-p2', 'P2', 'hash', 't', {'logicalProjectId': 'P2'}, 99)
            service.context.active_project = 'P2'
            again = service.context_request({
                'requestId': 'ra-again', 'logicalProjectId': 'P1', 'requestedScope': 'selection', 'instanceId': 'AC-A'})
            self.assertEqual(again['logicalProjectId'], 'P1')
            self.assertEqual(again['payload']['logicalProjectId'], 'P1')
            self.assertNotIn('P2', json.dumps(again['payload']))
            self.assertEqual(first['logicalProjectId'], 'P1')
            self.assertEqual(second['logicalProjectId'], 'P2')
            service.disconnect_archicad('AC-A')
            self.assertEqual(service.store.client('AC-A')['connection_state'], 'DISCONNECTED')
            self.assertEqual(service.store.client('AC-B')['connection_state'], 'CONNECTED')
            self.assertEqual(service.connections.get('ARCHICAD')['status'], 'CONNECTED')
            repeated = service.context_request({
                'requestId': 'rb', 'logicalProjectId': 'P2', 'requestedScope': 'selection', 'instanceId': 'AC-B'})
            self.assertEqual(repeated['snapshotId'], second['snapshotId'])
            self.assertNotIn('P1', json.dumps(repeated['payload']))


class UiAndLocalAiTests(unittest.TestCase):
    def test_ui_starts_blank_and_keeps_channels_independent(self):
        ui = SafeBIMUI()
        self.assertIsNone(ui.project)
        self.assertIsNone(ui.story)
        self.assertIsNone(ui.selection)
        self.assertIsNone(ui.last_proposal)
        self.assertEqual(ui.refresh_label, '')
        self.assertEqual(ui.context_lease_state, 'NONE')
        ui.apply_context_lease('VALID', 'Контекст устарел')
        self.assertEqual(ui.context_lease_state, 'VALID')
        self.assertEqual(ui.context_banner, 'Контекст устарел')
        ui.set_local_ai()
        self.assertEqual(ui.connections.get('AI')['status'], 'CONNECTED')
        self.assertEqual(ui.connections.get('AI')['detail'], 'локальная')
        self.assertEqual(ui.ai_route, 'local')
        ui.set_offline_ai()
        rendered = ui.render()
        offline = next(line for line in rendered.splitlines() if line.startswith('ИИ:'))
        self.assertNotIn('●', offline)
        self.assertIn('Офлайн', offline)
        for label in ('Archicad:', 'Bridge:', 'GitHub:', 'AI:'):
            self.assertIn(label, rendered)
        board = status_board(local_ready=True, auth_ok=False, ai='AI_OFFLINE', archicad_connected=False)
        ui.apply_board(board)
        self.assertEqual(ui.board['LOCAL'], 'LOCAL_READY')
        self.assertNotEqual(ui.board['LOCAL'], 'LOCAL_ERROR')
        self.assertIn('LOCAL_READY', ui.render())
        self.assertIn('REMOTE_NEEDS_AUTH', ui.render())

    def test_cancel_unload_reset_then_complete(self):
        class Endpoint:
            def health(self):
                return {'status': 'CONNECTED'}

            def complete(self, prompt):
                return {'kind': 'proposal', 'text': 'after reset'}

        provider = LocalOpenAICompatibleProvider(Endpoint())
        self.assertEqual(provider.lazy_start(), 'READY')
        provider.cancel()
        self.assertTrue(provider.cancelled)
        with self.assertRaises(Exception):
            provider.complete('сводка')
        self.assertEqual(provider.unload(), 'UNLOADED')
        self.assertFalse(provider.cancelled)
        provider.reset()
        self.assertEqual(provider.lazy_start(), 'READY')
        proposal = provider.complete('сводка')
        self.assertIsInstance(proposal, Proposal)
        self.assertFalse(proposal.executable)
        self.assertEqual(proposal.text, 'after reset')
        broker = AIBroker(None, provider)
        broker.cancel()
        provider.reset()
        self.assertEqual(provider.begin_start(), 'STARTING')
        self.assertEqual(provider.lazy_start(), 'READY')
        self.assertEqual(broker.complete('ещё').text, 'after reset')


class StartupIndependenceTests(unittest.TestCase):
    def test_local_ready_without_archicad_client(self):
        started = simulate_startup(auth_ok=True, archicad_ok=False, cloud_ok=False)
        self.assertEqual(started['local'], 'LOCAL_READY')
        self.assertEqual(started['archicad'], 'ARCHICAD_DISCONNECTED')
        self.assertEqual(started['remote'], 'REMOTE_CONNECTED')
        self.assertEqual(started['ai'], 'AI_OFFLINE')
        self.assertTrue(started['ready'])
        self.assertNotEqual(started['local'], 'LOCAL_ERROR')
        with tempfile.TemporaryDirectory() as directory:
            service = service_in(directory)
            self.assertTrue(service.health()['running'])
            self.assertEqual(service.connections.get('BRIDGE')['status'], 'CONNECTED')
            self.assertEqual(service.connections.get('ARCHICAD')['status'], 'OFFLINE')
            self.assertNotEqual(service.connections.get('ARCHICAD')['detail'], 'нет интернета')


if __name__ == '__main__':
    unittest.main()
