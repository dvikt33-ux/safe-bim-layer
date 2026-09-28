"""S1 reliability contracts. Offline only. No Archicad process and no PLN write."""
import unittest
from pathlib import Path

from sync_bridge.ai_broker import AIBroker, CloudProvider, ProviderError, ProviderTimeout
from sync_bridge.bridge import InjectedCrash, InstanceConflict, SafeBIMBridge
from sync_bridge.context import ContextReady
from sync_bridge.local_provider import LocalOpenAICompatibleProvider
from sync_bridge.mailbox import ETAG_POLICY, GitHubMailbox
from sync_bridge.pipe_win32 import (
    MAX_PIPE_INSTANCES,
    PIPE_REJECT_REMOTE_CLIENTS,
    PIPE_VERIFICATION,
    PipeApplicationGate,
    WindowsNamedPipe,
)
from sync_bridge.polling import PollScheduler
from sync_bridge.protocol import ProtocolError, envelope
from sync_bridge.remote_inbox import DurableRemoteInbox
from sync_bridge.security import SESSION_ISOLATION, PeerIdentity
from sync_bridge.startup import simulate_startup, status_board
from sync_bridge.store import BridgeStore
from sync_bridge.ui_model import SafeBIMUI
from tests_sync.closing import ClosingDirectory
from tests_sync.test_sync_bridge import HttpResponse, ScriptedHttp


def reopen(service, http):
    path = service.store.path
    owner = service.owner
    instance_id = service.instance_id
    service.crash()
    service.store.set_meta('lease_expires', '2000-01-01T00:00:00+00:00')
    service.store.close()
    store = BridgeStore(path)
    mailbox = GitHubMailbox(http)
    again = SafeBIMBridge(store, mailbox, owner=owner, instance_id=instance_id)
    again.start()
    return again


class DurablePublishTests(unittest.TestCase):
    def test_publish_ack_lost_then_process_restart_is_idempotent(self):
        with ClosingDirectory() as directory:
            remote = DurableRemoteInbox(Path(directory) / 'remote.sqlite3')
            remote.drop_next_ack = True
            store = BridgeStore(Path(directory) / 'bridge.sqlite3')
            mailbox = GitHubMailbox(remote)
            service = SafeBIMBridge(store, mailbox, owner=PeerIdentity('S-1-5-21-1', 'session-7'))
            service.start()
            service.queue_result('job-1', {'status': 'mock'})
            uncertain = service.flush_outbox()
            self.assertEqual(uncertain[0]['status'], 'UNCERTAIN')
            self.assertEqual(service.store.message('result-job-1')['state'], 'UNCERTAIN')
            self.assertEqual(remote.count(), 1)
            self.assertEqual(remote.accepted_ids(), ['result-job-1'])
            restarted = reopen(service, remote)
            published = restarted.flush_outbox()
            self.assertEqual(published[0]['status'], 'ALREADY_PUBLISHED')
            self.assertEqual(published[0]['authority'], 'remote')
            self.assertEqual(remote.count(), 1)
            self.assertEqual(remote.accepted_ids(), ['result-job-1'])
            self.assertEqual(restarted.store.message('result-job-1')['state'], 'SENT')
            puts = [call for call in remote.calls if call[0] == 'PUT']
            self.assertEqual(len(puts), 2)
            self.assertEqual(puts[0][2]['Idempotency-Key'], 'result-job-1')
            self.assertEqual(puts[1][2]['Idempotency-Key'], 'result-job-1')


class ETagAndCrashTests(unittest.TestCase):
    def test_etag_header_is_sent_and_persisted_after_completed_tick(self):
        http = ScriptedHttp([
            HttpResponse(200, {'messages': []}, {'ETag': '"abc"'}),
            HttpResponse(304, {}, {}),
        ])
        with ClosingDirectory() as directory:
            store = BridgeStore(Path(directory) / 'bridge.sqlite3')
            service = SafeBIMBridge(store, GitHubMailbox(http), owner=PeerIdentity('S-1-5-21-1', 'session-7'))
            service.start()
            self.assertEqual(service.health()['etagPolicy'], ETAG_POLICY)
            first = service.tick()
            self.assertNotIn('If-None-Match', http.calls[0][2])
            self.assertEqual(store.meta('remote_etag'), '"abc"')
            self.assertEqual(first['processed'], 0)
            restarted = reopen(service, ScriptedHttp([HttpResponse(304, {}, {})]))
            second = restarted.tick()
            self.assertEqual(restarted.mailbox.http.calls[0][2].get('If-None-Match'), '"abc"')
            self.assertEqual(second['status'], 'NOT_MODIFIED')
            self.assertEqual(second['processed'], 0)
            self.assertEqual(restarted.store.jobs(), [])

    def test_duplicate_inbound_after_crash_before_tick_finishes(self):
        message = {'messageId': 'M', 'body': {'recipe': 'mock'}}
        http = ScriptedHttp([HttpResponse(200, {'messages': [message]}, {'ETag': '"new"'})])
        with ClosingDirectory() as directory:
            store = BridgeStore(Path(directory) / 'bridge.sqlite3')
            service = SafeBIMBridge(store, GitHubMailbox(http), owner=PeerIdentity('S-1-5-21-1', 'session-7'))
            service.start()

            def boom():
                raise InjectedCrash('tick interrupted after persist')

            service.fault_after_persist = boom
            with self.assertRaises(InjectedCrash):
                service.tick()
            self.assertEqual(len(service.store.jobs()), 1)
            self.assertIsNone(service.store.meta('remote_etag'))
            replay = ScriptedHttp([HttpResponse(200, {'messages': [message]}, {'ETag': '"new"'})])
            restarted = reopen(service, replay)
            result = restarted.tick()
            self.assertNotIn('If-None-Match', replay.calls[0][2])
            self.assertEqual(result['accepted'][0]['status'], 'DUPLICATE')
            self.assertEqual(len(restarted.store.jobs()), 1)
            self.assertEqual(restarted.store.jobs()[0]['source_message_id'], 'M')


class ProtocolAndPipeContractTests(unittest.TestCase):
    def test_supported_protocol_version_is_accepted(self):
        message = envelope('HELLO', {'role': 'palette'}, instance_id='ac-1', request_id='r1', message_id='m1')
        self.assertEqual(message.protocol_version, 1)

    def test_named_pipe_offline_contract(self):
        self.assertEqual(PIPE_VERIFICATION, 'OFFLINE_CONTRACT_VERIFIED')
        self.assertTrue(SESSION_ISOLATION)
        calls = []

        class Kernel:
            def CreateNamedPipeW(self, name, access, mode, instances, out_size, in_size, timeout, sddl):
                calls.append((name, instances, mode, sddl))
                return 7

        pipe = WindowsNamedPipe('S-1-5-21-9', 'session-7', kernel=Kernel())
        opened = pipe.open_server()
        self.assertEqual(opened.max_instances, MAX_PIPE_INSTANCES)
        self.assertTrue(opened.reject_remote)
        self.assertTrue(calls[0][2] & PIPE_REJECT_REMOTE_CLIENTS)
        self.assertIn('(A;;GA;;;S-1-5-21-9)', opened.sddl)
        self.assertNotIn('WD', opened.sddl)
        gate = PipeApplicationGate()
        early = envelope('CONTEXT_REQUEST', {'logicalProjectId': 'P1'}, instance_id='AC-A', request_id='r', message_id='m')
        with self.assertRaises(ProtocolError):
            gate.accept(early)
        self.assertEqual(gate.accept(envelope('HELLO', {}, instance_id='AC-A', request_id='h', message_id='hm')), 'HANDSHAKE')
        self.assertEqual(gate.accept(early), 'APPLICATION')
        text = Path(__file__).resolve().parents[1].joinpath('sync_bridge', 'pipe_win32.py').read_text(encoding='utf-8')
        self.assertIn('OFFLINE_CONTRACT_VERIFIED', text)
        self.assertNotIn('Windows integration verified', text)

    def test_bridge_requires_handshake_and_denies_foreign_peers(self):
        with ClosingDirectory() as directory:
            store = BridgeStore(Path(directory) / 'bridge.sqlite3')
            service = SafeBIMBridge(store, GitHubMailbox(ScriptedHttp([])), owner=PeerIdentity('S-1-5-21-1', 'session-7'))
            service.start()
            owner = service.owner
            from sync_bridge.protocol import encode_frame
            app = encode_frame(envelope('CONTEXT_REQUEST', {'logicalProjectId': 'P1'}, instance_id='AC-A', request_id='r', message_id='m'))
            with self.assertRaises(ProtocolError):
                service.accept_client_frame(owner, app)
            hello = encode_frame(envelope('HELLO', {'logicalProjectId': 'P1'}, instance_id='AC-A', request_id='h', message_id='hm'))
            service.accept_client_frame(owner, hello)
            self.assertEqual(service.accept_client_frame(owner, app)['kind'], 'CONTEXT_REQUEST')
            with self.assertRaises(PermissionError):
                service.accept_client_frame(PeerIdentity('S-1-5-21-other', 'session-7'), hello)
            with self.assertRaises(PermissionError):
                service.accept_client_frame(PeerIdentity(owner.user_sid, 'other-session'), hello)


class MultiArchicadTests(unittest.TestCase):
    def test_instances_are_isolated_and_duplicate_id_conflicts(self):
        with ClosingDirectory() as directory:
            store = BridgeStore(Path(directory) / 'bridge.sqlite3')
            service = SafeBIMBridge(store, GitHubMailbox(ScriptedHttp([])), owner=PeerIdentity('S-1-5-21-1', 'session-7'))
            service.start()
            owner = service.owner
            service.handshake(envelope('HELLO', {'logicalProjectId': 'P1'}, instance_id='AC-A', request_id='h1', message_id='hm1').to_dict(), owner)
            service.handshake(envelope('HELLO', {'logicalProjectId': 'P2'}, instance_id='AC-B', request_id='h2', message_id='hm2').to_dict(), owner)
            first = service.context_request({'requestId': 'ra', 'logicalProjectId': 'P1', 'requestedScope': 'selection', 'instanceId': 'AC-A'})
            second = service.context_request({'requestId': 'rb', 'logicalProjectId': 'P2', 'requestedScope': 'selection', 'instanceId': 'AC-B'})
            self.assertEqual(first['logicalProjectId'], 'P1')
            self.assertNotIn('P2', str(first))
            self.assertEqual(second['logicalProjectId'], 'P2')
            self.assertNotIn('P1', str(second['payload']))
            cross = service.context_request({'requestId': 'rx', 'logicalProjectId': 'P2', 'requestedScope': 'selection', 'instanceId': 'AC-A'})
            self.assertEqual(cross['kind'], 'CONTEXT_ERROR')
            service.disconnect_archicad('AC-A')
            self.assertEqual(service.store.client('AC-A')['connection_state'], 'DISCONNECTED')
            self.assertEqual(service.store.client('AC-B')['connection_state'], 'CONNECTED')
            self.assertEqual(service.connections.get('ARCHICAD')['status'], 'CONNECTED')
            with self.assertRaises(InstanceConflict):
                service.handshake(envelope('HELLO', {'logicalProjectId': 'P2'}, instance_id='AC-B', request_id='h3', message_id='hm3').to_dict(), owner)


class BackoffTests(unittest.TestCase):
    def test_rate_limit_timeout_and_backoff_contract(self):
        auth = ScriptedHttp([HttpResponse(403, {'message': 'bad credentials'}, {})])
        self.assertEqual(PollScheduler(GitHubMailbox(auth)).poll_once()['status'], 'NEEDS_AUTH')
        secondary = ScriptedHttp([HttpResponse(403, {'message': 'You have exceeded a secondary rate limit'}, {'Retry-After': '12'})])
        limited = PollScheduler(GitHubMailbox(secondary)).poll_once()
        self.assertEqual(limited['status'], 'RATE_LIMITED')
        self.assertGreaterEqual(limited['retryAfter'], 12)
        self.assertLessEqual(limited['retryAfter'], 300)
        capped = PollScheduler(GitHubMailbox(ScriptedHttp([HttpResponse(429, {}, {'Retry-After': '10000'})])))
        capped.delay = 250
        self.assertEqual(capped.poll_once()['retryAfter'], 300)
        http = ScriptedHttp([HttpResponse(500, {}, {}), TimeoutError('slow'), HttpResponse(200, {'messages': []}, {'ETag': 'ok'})])
        scheduler = PollScheduler(GitHubMailbox(http))
        first = scheduler.poll_once()
        second = scheduler.poll_once()
        self.assertEqual(first['status'], 'OFFLINE')
        self.assertEqual(second['status'], 'OFFLINE')
        self.assertGreater(second['delay'], first['delay'])
        self.assertLessEqual(second['delay'], 300)
        self.assertGreaterEqual(second['delay'], 15)
        third = scheduler.poll_once()
        self.assertEqual(third['status'], 'CHANGED')
        self.assertEqual(scheduler.delay, scheduler.config.active_seconds)
        self.assertEqual(scheduler.calls, 3)
        text = Path(__file__).resolve().parents[1].joinpath('sync_bridge', 'polling.py').read_text(encoding='utf-8')
        self.assertNotIn('sleep(', text)

    def test_single_poll_and_jitter_use_injected_rng(self):
        class Reenter:
            def __init__(self):
                self.scheduler = None
                self.inner = None

            def request(self, method, url, headers, body=None):
                self.inner = self.scheduler.poll_once()
                return HttpResponse(200, {'messages': []}, {'ETag': 'v'})

        http = Reenter()
        scheduler = PollScheduler(GitHubMailbox(http))
        http.scheduler = scheduler
        result = scheduler.poll_once()
        self.assertEqual(result['status'], 'CHANGED')
        self.assertEqual(http.inner['status'], 'BUSY')
        self.assertEqual(scheduler.calls, 1)
        self.assertFalse(scheduler.in_flight)
        values = iter((0.0, 1.0))
        jittered = PollScheduler(GitHubMailbox(ScriptedHttp([HttpResponse(500, {}, {}), HttpResponse(500, {}, {})])), rng=lambda: next(values))
        low = jittered.poll_once()['delay']
        high = jittered.poll_once()['delay']
        self.assertNotEqual(low, high)
        self.assertGreaterEqual(low, 15)
        self.assertGreaterEqual(high, 15)
        self.assertLessEqual(high, 300)


class MalformedAndContextTests(unittest.TestCase):
    def test_malformed_message_is_quarantined_without_blocking_valid(self):
        bad = {'nope': 1}
        valid = {'messageId': 'ok-1', 'body': {'recipe': 'mock'}}
        valid_next = {'messageId': 'ok-2', 'body': {'recipe': 'mock'}}
        http = ScriptedHttp([
            HttpResponse(200, {'messages': [bad, valid]}, {'ETag': 'a'}),
            HttpResponse(200, {'messages': [bad, valid_next]}, {'ETag': 'b'}),
        ])
        with ClosingDirectory() as directory:
            store = BridgeStore(Path(directory) / 'bridge.sqlite3')
            service = SafeBIMBridge(store, GitHubMailbox(http), owner=PeerIdentity('S-1-5-21-1', 'session-7'))
            service.start()
            first = service.tick()
            self.assertEqual([item['status'] for item in first['accepted']], ['DEAD_LETTER', 'QUEUED'])
            self.assertEqual(len(service.store.jobs()), 1)
            self.assertEqual(len(service.store.messages_by_state('DEAD_LETTER')), 1)
            self.assertTrue(service.health()['running'])
            second = service.tick()
            self.assertEqual(second['accepted'][0]['status'], 'DEAD_LETTER')
            self.assertTrue(second['accepted'][1]['jobCreated'])
            self.assertEqual(len(service.store.jobs()), 2)
            self.assertEqual(len(service.store.messages_by_state('DEAD_LETTER')), 1)

    def test_duplicate_context_request_after_restart_does_not_recapture(self):
        with ClosingDirectory() as directory:
            store = BridgeStore(Path(directory) / 'bridge.sqlite3')
            service = SafeBIMBridge(store, GitHubMailbox(ScriptedHttp([])), owner=PeerIdentity('S-1-5-21-1', 'session-7'))
            service.start()
            request = {'requestId': 'ctx-1', 'logicalProjectId': 'house', 'requestedScope': 'selection'}
            first = service.context_request(request)
            captures = service.store.meta('context_captures')
            restarted = reopen(service, ScriptedHttp([]))
            second = restarted.context_request(request)
            self.assertEqual(second['snapshotId'], first['snapshotId'])
            self.assertEqual(restarted.store.meta('context_captures'), captures)
            self.assertEqual(restarted.store.jobs(), [])

    def test_context_ready_rejects_wrong_id_project_hash_generation_and_cancel(self):
        with ClosingDirectory() as directory:
            store = BridgeStore(Path(directory) / 'bridge.sqlite3')
            service = SafeBIMBridge(store, GitHubMailbox(ScriptedHttp([])), owner=PeerIdentity('S-1-5-21-1', 'session-7'))
            service.start()
            request = {'requestId': 'ctx-9', 'logicalProjectId': 'house', 'requestedScope': 'selection'}
            service.context_request(request)
            missing = ContextReady(1, 'missing', 'snap', 'house', 'hash-ok', 't', {}, 2)
            self.assertEqual(service.apply_context_ready(missing), 'CONTEXT_ERROR')
            self.assertIsNone(service.store.context_request('missing'))
            empty = ContextReady(1, 'ctx-9', 'snap-x', 'house', '   ', 't', {}, 2)
            self.assertEqual(service.apply_context_ready(empty), 'CONTEXT_ERROR')
            self.assertEqual(service.store.context_request('ctx-9')['state'], 'VALID')
            wrong = ContextReady(1, 'ctx-9', 'snap-x', 'other', 'hash-ok', 't', {}, 2)
            self.assertEqual(service.apply_context_ready(wrong), 'CONTEXT_ERROR')
            self.assertEqual(service.store.context_request('ctx-9')['project_id'], 'house')
            self.assertEqual(service.store.context_request('ctx-9')['state'], 'VALID')
            captured = service.store.context_request('ctx-9')['snapshot_id']
            newer = ContextReady(1, 'ctx-9', 'snap-0004', 'house', 'hash-ok', 't', {'source': 'mock'}, 4)
            self.assertEqual(service.apply_context_ready(newer), 'REQUEST_GENERATION_CONFLICT')
            self.assertEqual(service.store.context_request('ctx-9')['snapshot_id'], captured)
            service.context.cancel('ctx-9')
            restarted = reopen(service, ScriptedHttp([]))
            late = ContextReady(1, 'ctx-9', 'snap-0009', 'house', 'hash-ok', 't', {}, 9)
            self.assertEqual(restarted.apply_context_ready(late), 'CONTEXT_ERROR')
            self.assertEqual(restarted.store.context_request('ctx-9')['state'], 'CANCELLED')
            self.assertEqual(restarted.context.lease, 'CANCELLED')
            self.assertEqual(restarted.store.context_request('ctx-9')['snapshot_id'], captured)

    def test_older_generation_after_restart_is_ignored(self):
        with ClosingDirectory() as directory:
            store = BridgeStore(Path(directory) / 'bridge.sqlite3')
            service = SafeBIMBridge(store, GitHubMailbox(ScriptedHttp([])), owner=PeerIdentity('S-1-5-21-1', 'session-7'))
            service.start()
            service.store.put_context_request('ctx-4', 'house', 'selection', 'CAPTURING', 't')
            service.store.set_meta('context_op_capture_revision:ctx-4', '0')
            self.assertEqual(service.apply_context_ready(ContextReady(1, 'ctx-4', 'snap-0004', 'house', 'hash-ok', 't', {}, 4)), 'CONTEXT_READY')
            restarted = reopen(service, ScriptedHttp([]))
            self.assertEqual(restarted.apply_context_ready(ContextReady(1, 'ctx-4', 'snap-0001', 'house', 'hash-ok', 't', {}, 1)), 'IGNORED_STALE')
            self.assertEqual(restarted.store.context_request('ctx-4')['snapshot_id'], 'snap-0004')


class AIAndStartupStateTests(unittest.TestCase):
    def test_ai_routing_states_do_not_execute(self):
        class Flaky:
            def __init__(self):
                self.calls = 0

            def health(self):
                return {'status': 'CONNECTED'}

            def complete(self, prompt):
                self.calls += 1
                if self.calls == 1:
                    raise ProviderTimeout('cloud timeout')
                return {'kind': 'proposal', 'text': 'cloud restored'}

        class LocalEp:
            def health(self):
                return {'status': 'CONNECTED'}

            def complete(self, prompt):
                return {'kind': 'mock_recipe', 'text': 'local proposal'}

        broker = AIBroker(CloudProvider(Flaky()), LocalOpenAICompatibleProvider(LocalEp()))
        first = broker.complete('сводка')
        self.assertEqual(broker.last_route, 'local')
        self.assertFalse(first.executable)
        second = broker.complete('сводка')
        self.assertEqual(broker.last_route, 'cloud')
        self.assertEqual(second.provider, 'cloud')
        self.assertFalse(second.executable)

        class Idle:
            def health(self):
                return {'status': 'CONNECTED'}

            def complete(self, prompt):
                raise AssertionError('completion during STARTING')

        class Down:
            def health(self):
                raise ConnectionError('down')

            def complete(self, prompt):
                raise ConnectionError('down')

        local = LocalOpenAICompatibleProvider(Idle())
        self.assertEqual(local.begin_start(), 'STARTING')
        self.assertEqual(local.health()['status'], 'STARTING')
        self.assertNotEqual(local.health()['status'], 'OFFLINE')
        starting = AIBroker(CloudProvider(Down()), local)
        self.assertEqual(starting.health()['route'], 'starting')
        with self.assertRaises(ProviderError):
            starting.complete('сводка')
        self.assertEqual(starting.last_route, 'starting')

        calls = []

        class Spy:
            def health(self):
                return {'status': 'CONNECTED'}

            def complete(self, prompt):
                calls.append(prompt)
                return {'kind': 'proposal', 'text': 'should not run'}

        with ClosingDirectory() as directory:
            store = BridgeStore(Path(directory) / 'bridge.sqlite3')
            service = SafeBIMBridge(
                store, GitHubMailbox(ScriptedHttp([])), owner=PeerIdentity('S-1-5-21-1', 'session-7'),
                broker=AIBroker(CloudProvider(Down()), LocalOpenAICompatibleProvider(Spy())))
            service.start()
            before = len(service.store.jobs())
            service.ai_cancel()
            self.assertEqual(service.broker.last_route, 'cancelled')
            self.assertEqual(len(service.store.jobs()), before)
            self.assertEqual(service.store.pending_outbox(), [])
            self.assertEqual(calls, [])

    def test_startup_board_keeps_auth_loss_independent(self):
        board = status_board(local_ready=True, auth_ok=False, ai='AI_OFFLINE', archicad_connected=False)
        self.assertEqual(board['LOCAL'], 'LOCAL_READY')
        self.assertEqual(board['REMOTE'], 'REMOTE_NEEDS_AUTH')
        self.assertEqual(board['AI'], 'AI_OFFLINE')
        self.assertEqual(board['ARCHICAD'], 'ARCHICAD_DISCONNECTED')
        started = simulate_startup(auth_ok=False, cloud_ok=False, archicad_ok=False)
        self.assertEqual(started['board'], board)
        self.assertTrue(started['ready'])
        self.assertNotEqual(started['local'], 'LOCAL_ERROR')
        other = status_board(local_ready=True, auth_ok=True, ai='AI_STARTING', archicad_connected=True)
        self.assertEqual(other['AI'], 'AI_STARTING')
        self.assertNotEqual(other['AI'], 'AI_OFFLINE')
        self.assertEqual(other['ARCHICAD'], 'ARCHICAD_CONNECTED')
        ui = SafeBIMUI()
        ui.apply_board(board)
        rendered = ui.render()
        self.assertIn('LOCAL_READY', rendered)
        self.assertIn('REMOTE_NEEDS_AUTH', rendered)
        self.assertIn('AI_OFFLINE', rendered)
        self.assertIn('ARCHICAD_DISCONNECTED', rendered)
        self.assertNotIn('LOCAL_ERROR', rendered)


if __name__ == '__main__':
    unittest.main()
