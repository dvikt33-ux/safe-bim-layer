"""S1.2 crash ownership, message identity, and passive AI. Offline only."""
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sync_bridge.ai_broker import AIBroker, CloudProvider, ProviderTimeout
from sync_bridge.bridge import InjectedCrash, InstanceConflict, SafeBIMBridge
from sync_bridge.context import ContextReady
from sync_bridge.local_provider import LocalOpenAICompatibleProvider
from sync_bridge.mailbox import GITHUB_BACKEND_STATUS, REMOTE_MAILBOX_PROTOCOL, GitHubMailbox
from sync_bridge.protocol import envelope
from sync_bridge.remote_inbox import DURABLE_REMOTE_INBOX_ROLE, DurableRemoteInbox
from sync_bridge.security import PeerIdentity
from sync_bridge.startup import simulate_startup
from sync_bridge.store import BridgeStore, ResultConflict
from sync_bridge.ui_model import SafeBIMUI
from tests_sync.closing import ClosingDirectory
from tests_sync.test_sync_bridge import HttpResponse, ScriptedHttp

OWNER = PeerIdentity('S-1-5-21-1', 'session-7')


class MutableClock:
    def __init__(self):
        self.moment = datetime(2026, 9, 28, 12, 0, tzinfo=timezone.utc)

    def __call__(self):
        return self.moment.isoformat()

    def advance(self, seconds):
        self.moment += timedelta(seconds=seconds)


class QuietHttp:
    def request(self, method, url, headers, body=None):
        return HttpResponse(200, {'messages': []})


def opened(directory, name, clock=None):
    store = BridgeStore(Path(directory) / name)
    service = SafeBIMBridge(
        store, GitHubMailbox(QuietHttp()), owner=OWNER, instance_id='bridge-1', clock=clock)
    return service


def hello(instance_id, request_id):
    return envelope(
        'HELLO', {'logicalProjectId': 'house'}, instance_id=instance_id,
        request_id=request_id, message_id='hello-' + request_id).to_dict()


class LeaseOwnershipTests(unittest.TestCase):
    def test_same_public_id_is_not_ownership(self):
        clock = MutableClock()
        with ClosingDirectory() as directory:
            first = opened(directory, 'a.sqlite3', clock)
            first.start()
            second = opened(directory, 'a.sqlite3', clock)
            with self.assertRaises(InstanceConflict):
                second.start()
            first.stop()
            second.start()
            self.assertTrue(second.running)
            second.stop()

    def test_stale_lease_after_crash_allows_takeover(self):
        clock = MutableClock()
        with ClosingDirectory() as directory:
            crashed = opened(directory, 'a.sqlite3', clock)
            crashed.start()
            crashed.handshake(hello('AC-1', 'h1'), OWNER)
            replacement = opened(directory, 'a.sqlite3', clock)
            with self.assertRaises(InstanceConflict):
                replacement.start()
            crashed.crash()
            clock.advance(31)
            replacement.start()
            replacement.handshake(hello('AC-1', 'h2'), OWNER)
            self.assertEqual(replacement.store.client('AC-1')['connection_state'], 'CONNECTED')
            self.assertEqual(replacement.store.client('AC-1')['epoch'], replacement.epoch)
            with self.assertRaises(InstanceConflict):
                replacement.handshake(hello('AC-1', 'h3'), OWNER)


class MessageIdentityTests(unittest.TestCase):
    def test_same_message_id_different_payload_is_conflict(self):
        with ClosingDirectory() as directory:
            service = opened(directory, 'a.sqlite3')
            service.start()
            first = service.accept_remote_message({'messageId': 'M', 'body': {'recipe': 'A'}})
            conflict = service.accept_remote_message({'messageId': 'M', 'body': {'recipe': 'B'}})
            duplicate = service.accept_remote_message({'messageId': 'M', 'body': {'recipe': 'A'}})
            self.assertTrue(first['jobCreated'])
            self.assertEqual(conflict['status'], 'MESSAGE_ID_CONFLICT')
            self.assertFalse(conflict['jobCreated'])
            self.assertEqual(duplicate['status'], 'DUPLICATE')
            jobs = service.store.jobs()
            self.assertEqual(len(jobs), 1)
            self.assertEqual(jobs[0]['payload']['recipe'], 'A')

    def test_remote_publish_does_not_treat_different_payload_as_duplicate(self):
        with ClosingDirectory() as directory:
            remote = DurableRemoteInbox(Path(directory) / 'remote.sqlite3')
            mailbox = GitHubMailbox(remote)
            first = mailbox.publish_result({'messageId': 'M', 'result': {'n': 1}})
            conflict = mailbox.publish_result({'messageId': 'M', 'result': {'n': 2}})
            fresh = GitHubMailbox(remote)
            again = fresh.publish_result({'messageId': 'M', 'result': {'n': 1}})
            self.assertEqual(first['status'], 'PUBLISHED')
            self.assertEqual(conflict['status'], 'MESSAGE_ID_CONFLICT')
            self.assertEqual(again['status'], 'ALREADY_PUBLISHED')
            self.assertEqual(remote.count(), 1)
            self.assertEqual(DURABLE_REMOTE_INBOX_ROLE, 'TEST_STAND_IN_ONLY')


class AtomicResultTests(unittest.TestCase):
    def test_result_and_outbox_commit_together(self):
        with ClosingDirectory() as directory:
            path = Path(directory) / 'a.sqlite3'
            service = opened(directory, 'a.sqlite3')
            service.start()

            def boom():
                raise InjectedCrash('before commit')

            service.store.fault_before_result_commit = boom
            with self.assertRaises(InjectedCrash):
                service.queue_result('job-x', {'status': 'mock'})
            self.assertIsNone(service.store.result('job-x'))
            self.assertIsNone(service.store.message('result-job-x'))
            service.store.fault_before_result_commit = None
            service.queue_result('job-x', {'status': 'mock'})
            service.store.close()
            reopened = BridgeStore(path)
            self.assertEqual(reopened.result('job-x')['result']['status'], 'mock')
            self.assertEqual(reopened.message('result-job-x')['state'], 'PENDING')
            reopened.close()

    def test_job_result_is_immutable_and_sent_must_match(self):
        with ClosingDirectory() as directory:
            service = opened(directory, 'a.sqlite3')
            service.start()
            service.queue_result('job-y', {'status': 'one'})
            with self.assertRaises(ResultConflict):
                service.queue_result('job-y', {'status': 'two'})
            self.assertEqual(service.store.result('job-y')['result']['status'], 'one')
            service.store.set_message_state('result-job-y', 'SENT', 0)
            service.store.put_result('job-z', {'status': 'stored'}, 'PENDING')
            service.store.put_message(
                'result-job-z', 'result', 't',
                {'job_id': 'job-z', 'result': {'status': 'other'}, 'messageId': 'result-job-z'},
                'PENDING', 'outbox')
            service.mailbox = GitHubMailbox(ScriptedHttp([HttpResponse(200, {'ok': True})]))
            flushed = service.flush_outbox()
            self.assertEqual(flushed, [{'messageId': 'result-job-z', 'status': 'RESULT_MISMATCH'}])
            self.assertNotEqual(service.store.result('job-z')['upload_state'], 'SENT')
            self.assertNotEqual(service.store.message('result-job-z')['state'], 'SENT')


class ContextStreamTests(unittest.TestCase):
    def test_context_generation_is_per_instance(self):
        with ClosingDirectory() as directory:
            service = opened(directory, 'a.sqlite3')
            service.start()
            service.store.put_context_request('req-a', 'P1', 'selection', 'CAPTURING', 't', instance_id='AC-A')
            service.store.put_context_request('req-b', 'P2', 'selection', 'CAPTURING', 't', instance_id='AC-B')
            service.store.set_meta('context_op_capture_revision:req-a', '0')
            service.store.set_meta('context_op_capture_revision:req-b', '0')
            b2 = ContextReady(1, 'req-b', 'snap-b2', 'P2', 'hash-b', 't', {'source': 'mock'}, 2)
            a1 = ContextReady(1, 'req-a', 'snap-a1', 'P1', 'hash-a', 't', {'source': 'mock'}, 1)
            self.assertEqual(service.apply_context_ready(b2), 'CONTEXT_READY')
            service.context.current = ContextReady(1, 'req-b', 'snap-b2', 'P2', 'hash-b', 't', {}, 99)
            self.assertEqual(service.apply_context_ready(a1), 'CONTEXT_READY')
            blocked = ContextReady(1, 'req-a', 'snap-a2', 'P1', 'hash-a2', 't', {'source': 'mock'}, 2)
            self.assertEqual(service.apply_context_ready(blocked), 'REQUEST_GENERATION_CONFLICT')
            self.assertEqual(service.store.context_request('req-a')['snapshot_id'], 'snap-a1')
            service.store.put_context_request('req-a2', 'P1', 'selection', 'CAPTURING', 't', instance_id='AC-A')
            service.store.set_meta('context_op_capture_revision:req-a2', '0')
            a2 = ContextReady(1, 'req-a2', 'snap-a2', 'P1', 'hash-a2', 't', {'source': 'mock'}, 2)
            self.assertEqual(service.apply_context_ready(a2), 'CONTEXT_READY')
            stale = ContextReady(1, 'req-a2', 'snap-a1', 'P1', 'hash-a', 't', {'source': 'mock'}, 1)
            self.assertEqual(service.apply_context_ready(stale), 'IGNORED_STALE')
            self.assertEqual(service.store.context_request('req-a2')['snapshot_id'], 'snap-a2')


class PassiveAITests(unittest.TestCase):
    def test_cloud_health_does_not_load_qwen(self):
        class Endpoint:
            def __init__(self):
                self.health_calls = 0
                self.complete_calls = 0

            def health(self):
                self.health_calls += 1
                return {'status': 'CONNECTED'}

            def complete(self, prompt):
                self.complete_calls += 1
                return {'kind': 'proposal', 'text': 'local'}

        class Cloud:
            def health(self):
                return {'status': 'CONNECTED'}

            def complete(self, prompt):
                raise ProviderTimeout('timeout')

        endpoint = Endpoint()
        local = LocalOpenAICompatibleProvider(endpoint)
        broker = AIBroker(CloudProvider(Cloud()), local)
        report = broker.health()
        self.assertEqual(report['route'], 'cloud')
        self.assertEqual(local.load_state, 'UNLOADED')
        self.assertEqual(endpoint.health_calls, 0)
        proposal = broker.complete('сводка')
        self.assertFalse(proposal.executable)
        self.assertEqual(broker.last_route, 'local')
        self.assertEqual(endpoint.health_calls, 1)
        self.assertEqual(endpoint.complete_calls, 1)
        broker.complete('ещё')
        self.assertEqual(endpoint.health_calls, 1)


class FreshUIAndStatusTests(unittest.TestCase):
    def test_fresh_ui_does_not_claim_ai_online(self):
        ui = SafeBIMUI()
        line = next(item for item in ui.render().splitlines() if item.startswith('ИИ:'))
        self.assertEqual(line, 'ИИ: ○ Подключение')
        self.assertNotIn('●', line)
        ui.set_online()
        self.assertIn('Онлайн', next(item for item in ui.render().splitlines() if item.startswith('ИИ:')))
        ui.set_local_ai()
        self.assertIn('Локальная', next(item for item in ui.render().splitlines() if item.startswith('ИИ:')))
        ui.set_offline_ai()
        self.assertIn('Офлайн', next(item for item in ui.render().splitlines() if item.startswith('ИИ:')))

    def test_pipe_listening_is_not_an_archicad_handshake(self):
        started = simulate_startup(auth_ok=False)
        self.assertIn('named-pipe-listening', started['steps'])
        self.assertNotIn('archicad-handshake', started['steps'])
        self.assertEqual(started['local'], 'LOCAL_READY')
        self.assertEqual(started['archicad'], 'ARCHICAD_DISCONNECTED')
        self.assertEqual(REMOTE_MAILBOX_PROTOCOL, 'OFFLINE_MOCK_VERIFIED')
        self.assertEqual(GITHUB_BACKEND_STATUS, 'NOT_YET_LIVE_VERIFIED')
        self.assertEqual(DURABLE_REMOTE_INBOX_ROLE, 'TEST_STAND_IN_ONLY')


if __name__ == '__main__':
    unittest.main()
