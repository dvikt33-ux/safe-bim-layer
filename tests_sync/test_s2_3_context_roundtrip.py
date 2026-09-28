"""S2.3 remote context roundtrip. Offline only; no Archicad or PLN access."""
import copy
import unittest
from pathlib import Path

from sync_bridge.bridge import InjectedCrash, SafeBIMBridge
from sync_bridge.context import (
    CONTEXT_ROUNDTRIP_STATUS, ContextReady, SnapshotValidationError, generation_hash)
from sync_bridge.identity import canonical_hash
from sync_bridge.mailbox import GITHUB_BACKEND_STATUS
from sync_bridge.protocol import envelope
from sync_bridge.security import PeerIdentity
from sync_bridge.store import BridgeStore
from tests_sync.closing import ClosingDirectory
from tests_sync.test_s2_2_github_mailbox import FakeContentsHttp, mailbox, remote


OWNER = PeerIdentity('S-1-5-21-2300', 'session-s23')


class CountingProvider:
    def __init__(self, value=None, hook=None):
        self.calls = []
        self.value = value
        self.hook = hook

    def capture(self, request):
        self.calls.append(dict(request))
        if self.hook:
            self.hook(request)
        if self.value is not None:
            return copy.deepcopy(self.value)
        return {
            'source': 's2.3-synthetic',
            'instanceId': request['instanceId'],
            'logicalProjectId': request['logicalProjectId'],
            'generation': request['generation'],
            'elements': [{'id': 'E-1', 'type': 'Wall'}],
        }


class CrashOnceProvider(CountingProvider):
    def capture(self, request):
        self.calls.append(dict(request))
        raise InjectedCrash('during capture')


def request_object(message_id, request_id='R1', instance_id='AC-A', project_id='P1',
                   generation=1, scope='selection'):
    payload = {
        'requestId': request_id,
        'instanceId': instance_id,
        'logicalProjectId': project_id,
        'generation': generation,
        'requestedScope': scope,
    }
    return remote(message_id, payload, kind='CONTEXT_REQUEST') | {
        'requestId': request_id,
        'logicalProjectId': project_id,
    }


def started(directory, http, provider=None):
    service = SafeBIMBridge(
        BridgeStore(Path(directory) / 'bridge.sqlite3'), mailbox(http),
        owner=OWNER, context_provider=provider or CountingProvider())
    service.start()
    return service


def connect(service, instance_id='AC-A', project_id='P1'):
    service.handshake(envelope(
        'HELLO', {'logicalProjectId': project_id}, instance_id=instance_id,
        request_id='hello-' + instance_id, message_id='hello-message-' + instance_id,
    ).to_dict(), OWNER)


def crash_close(service):
    service.crash()
    service.store.set_meta('lease_expires', '2000-01-01T00:00:00+00:00')
    service.store.close()


def result_objects(http):
    return {key: value for key, value in http.objects.items() if '/results/' in key}


def context_ready_message_id(request_id, instance_id='AC-A', project_id='P1'):
    return 'context-ready-' + canonical_hash({
        'requestId': request_id,
        'instanceId': instance_id,
        'logicalProjectId': project_id,
    })[:32]


class RemoteContextRoundtripTests(unittest.TestCase):
    def test_remote_request_captures_and_publishes_context_ready(self):
        http = FakeContentsHttp()
        http.seed('safe-bim-mailbox/inbox/REQ1.json', request_object('REQ1'))
        provider = CountingProvider()
        with ClosingDirectory() as directory:
            service = started(directory, http, provider)
            connect(service)
            tick = service.tick()
            self.assertEqual(tick['accepted'][0]['status'], 'CONTEXT_READY')
            self.assertEqual(len(provider.calls), 1)
            self.assertEqual(len(result_objects(http)), 1)
            ready = next(iter(result_objects(http).values()))
            self.assertEqual(ready['kind'], 'CONTEXT_READY')
            self.assertEqual(ready['payload']['captureRevision'], 0)
            self.assertEqual(ready['payload']['generation'], 1)
            self.assertEqual(service.store.context_request('R1')['state'], 'VALID')

    def test_exact_remote_duplicate_captures_once(self):
        http = FakeContentsHttp()
        http.seed('safe-bim-mailbox/inbox/REQ1.json', request_object('REQ1'))
        provider = CountingProvider()
        with ClosingDirectory() as directory:
            service = started(directory, http, provider)
            connect(service)
            service.tick()
            http.version += 1
            replay = service.tick()
            self.assertEqual(replay['accepted'][0]['status'], 'DUPLICATE')
            self.assertEqual(len(provider.calls), 1)
            self.assertEqual(service.store.meta('context_captures'), '1')

    def test_duplicate_after_restart_keeps_one_capture_and_result(self):
        http = FakeContentsHttp()
        http.seed('safe-bim-mailbox/inbox/REQ1.json', request_object('REQ1'))
        provider = CountingProvider()
        with ClosingDirectory() as directory:
            service = started(directory, http, provider)
            connect(service)
            service.tick()
            service.stop()
            service.store.close()
            http.version += 1
            restarted_provider = CountingProvider()
            restarted = started(directory, http, restarted_provider)
            replay = restarted.tick()
            self.assertEqual(replay['accepted'][0]['status'], 'DUPLICATE')
            self.assertEqual(restarted.store.meta('context_captures'), '1')
            self.assertEqual(restarted_provider.calls, [])
            self.assertEqual(len(result_objects(http)), 1)

    def test_same_request_id_different_payload_is_conflict(self):
        http = FakeContentsHttp()
        http.seed('safe-bim-mailbox/inbox/A.json', request_object('A'))
        provider = CountingProvider()
        with ClosingDirectory() as directory:
            service = started(directory, http, provider)
            connect(service)
            service.tick()
            http.seed('safe-bim-mailbox/inbox/B.json', request_object(
                'B', request_id='R1', generation=2))
            tick = service.tick()
            self.assertIn('REQUEST_ID_CONFLICT', [item['status'] for item in tick['accepted']])
            self.assertEqual(len(provider.calls), 1)
            self.assertEqual(service.store.context_request('R1')['response']['sequence'], 1)

    def test_wrong_instance_is_not_rerouted_or_captured(self):
        http = FakeContentsHttp()
        http.seed('safe-bim-mailbox/inbox/REQ1.json', request_object('REQ1', instance_id='AC-MISSING'))
        provider = CountingProvider()
        with ClosingDirectory() as directory:
            service = started(directory, http, provider)
            connect(service, 'AC-B', 'P1')
            tick = service.tick()
            self.assertEqual(tick['accepted'][0]['status'], 'INSTANCE_NOT_AVAILABLE')
            self.assertEqual(provider.calls, [])
            self.assertEqual(result_objects(http), {})

    def test_wrong_project_preserves_existing_valid_state(self):
        http = FakeContentsHttp()
        provider = CountingProvider()
        with ClosingDirectory() as directory:
            service = started(directory, http, provider)
            connect(service)
            original = service.context_request({
                'requestId': 'LOCAL', 'instanceId': 'AC-A',
                'logicalProjectId': 'P1', 'requestedScope': 'selection'})
            http.seed('safe-bim-mailbox/inbox/REQ1.json', request_object(
                'REQ1', request_id='REMOTE', project_id='P2', generation=2))
            tick = service.tick()
            self.assertEqual(tick['accepted'][0]['status'], 'CONTEXT_ERROR')
            self.assertEqual(service.store.context_request('LOCAL')['response'], original)
            self.assertEqual(service.context.context_admission('LOCAL'), 'CURRENT')
            self.assertEqual(len(provider.calls), 1)

    def test_generation_ordering_is_stream_scoped(self):
        http = FakeContentsHttp()
        http.seed('safe-bim-mailbox/inbox/A.json', request_object('A', request_id='R2', generation=2))
        provider = CountingProvider()
        with ClosingDirectory() as directory:
            service = started(directory, http, provider)
            connect(service)
            service.tick()
            http.seed('safe-bim-mailbox/inbox/B.json', request_object('B', request_id='R1', generation=1))
            tick = service.tick()
            self.assertIn('IGNORED_STALE', [item['status'] for item in tick['accepted']])
            self.assertEqual(len(provider.calls), 1)
            self.assertEqual(service.store.meta('context_sequence:instance:AC-A'), '2')

    def test_resumed_older_capture_is_rejected_before_provider_after_restart(self):
        http = FakeContentsHttp()
        first_provider = CountingProvider()
        with ClosingDirectory() as directory:
            service = started(directory, http, first_provider)
            connect(service)
            service.context.fault_after_provider_returned = lambda: (
                _ for _ in ()).throw(InjectedCrash('before completion'))
            r1 = request_object('A', request_id='R1', generation=1)['payload']
            with self.assertRaises(InjectedCrash):
                service.context_request(r1, completion=service._commit_remote_context_ready)
            self.assertEqual(service.store.context_request('R1')['state'], 'CAPTURING')
            self.assertEqual(len(first_provider.calls), 1)
            crash_close(service)

            resumed_provider = CountingProvider()
            restarted = started(directory, http, resumed_provider)
            connect(restarted)
            r2 = request_object('B', request_id='R2', generation=2)['payload']
            ready = restarted.context_request(
                r2, completion=restarted._commit_remote_context_ready)
            self.assertEqual(ready['kind'], 'CONTEXT_READY')
            newer_row = copy.deepcopy(restarted.store.context_request('R2'))
            newer_outbox = copy.deepcopy(restarted.store.message(
                context_ready_message_id('R2')))

            stale = restarted.context_request(
                r1, completion=restarted._commit_remote_context_ready)

            self.assertEqual(stale['kind'], 'CONTEXT_STALE')
            self.assertEqual(len(resumed_provider.calls), 1)
            self.assertEqual(restarted.store.meta('context_sequence:instance:AC-A'), '2')
            self.assertEqual(restarted.store.context_request('R1')['state'], 'STALE')
            self.assertEqual(restarted.context.context_admission('R1'), 'STALE_CONTEXT')
            self.assertEqual(restarted.store.context_request('R2'), newer_row)
            self.assertEqual(restarted.context.context_admission('R2'), 'CURRENT')
            self.assertEqual(restarted.context.lease, 'VALID')
            self.assertEqual(restarted.context.ui_banner, 'Контекст #2')
            self.assertEqual(restarted.store.message(context_ready_message_id('R2')), newer_outbox)
            self.assertIsNone(restarted.store.message(context_ready_message_id('R1')))

    def test_commit_guard_rejects_older_generation_after_precheck(self):
        http = FakeContentsHttp()
        provider = CountingProvider()
        with ClosingDirectory() as directory:
            service = started(directory, http, provider)
            connect(service)
            r1 = request_object('A', request_id='R1', generation=1)['payload']
            r2 = request_object('B', request_id='R2', generation=2)['payload']
            newer = {}

            def commit_newer_before_r1_transaction():
                service.context.fault_after_provider_returned = None
                newer['response'] = service.context_request(
                    r2, completion=service._commit_remote_context_ready)

            service.context.fault_after_provider_returned = commit_newer_before_r1_transaction
            stale = service.context_request(
                r1, completion=service._commit_remote_context_ready)

            self.assertEqual(newer['response']['kind'], 'CONTEXT_READY')
            self.assertEqual(stale['kind'], 'CONTEXT_STALE')
            self.assertEqual(service.store.meta('context_sequence:instance:AC-A'), '2')
            self.assertEqual(service.store.context_request('R1')['state'], 'STALE')
            self.assertIsNone(service.store.context_request('R1')['snapshot_id'])
            self.assertIsNone(service.store.context_request('R1')['response'])
            self.assertEqual(service.store.context_request('R2')['state'], 'VALID')
            self.assertEqual(service.context.context_admission('R2'), 'CURRENT')
            self.assertEqual(service.context.lease, 'VALID')
            self.assertEqual(service.context.ui_banner, 'Контекст #2')
            self.assertIsNone(service.store.message(context_ready_message_id('R1')))
            self.assertIsNotNone(service.store.message(context_ready_message_id('R2')))

    def test_commit_guard_rejects_equal_generation_different_identity(self):
        http = FakeContentsHttp()
        provider = CountingProvider()
        with ClosingDirectory() as directory:
            service = started(directory, http, provider)
            connect(service)
            r1 = request_object('A', request_id='R1', generation=1)['payload']
            r2 = request_object('B', request_id='R2', generation=1)['payload']
            winner = {}

            def commit_winner_before_r1_transaction():
                service.context.fault_after_provider_returned = None
                winner['response'] = service.context_request(
                    r2, completion=service._commit_remote_context_ready)

            service.context.fault_after_provider_returned = commit_winner_before_r1_transaction
            conflict = service.context_request(
                r1, completion=service._commit_remote_context_ready)

            self.assertEqual(winner['response']['kind'], 'CONTEXT_READY')
            self.assertEqual(conflict['kind'], 'CONTEXT_SEQUENCE_CONFLICT')
            self.assertEqual(service.store.meta('context_sequence:instance:AC-A'), '1')
            self.assertEqual(service.store.context_request('R1')['state'], 'CAPTURING')
            self.assertIsNone(service.store.context_request('R1')['response'])
            self.assertEqual(service.store.context_request('R2')['state'], 'VALID')
            self.assertEqual(service.context.context_admission('R2'), 'CURRENT')
            self.assertEqual(service.context.lease, 'VALID')
            self.assertEqual(service.context.ui_banner, 'Контекст #1')
            self.assertIsNone(service.store.message(context_ready_message_id('R1')))
            self.assertIsNotNone(service.store.message(context_ready_message_id('R2')))

    def test_equal_generation_same_identity_is_idempotent_only(self):
        http = FakeContentsHttp()
        provider = CountingProvider()
        with ClosingDirectory() as directory:
            service = started(directory, http, provider)
            connect(service)
            r1 = request_object('A', request_id='R1', generation=1)['payload']
            first = service.context_request(
                r1, completion=service._commit_remote_context_ready)
            outbox = copy.deepcopy(service.store.message(context_ready_message_id('R1')))
            ready = ContextReady(
                first['protocolVersion'], first['requestId'], first['snapshotId'],
                first['logicalProjectId'], first['rootHash'], first['capturedAt'],
                first['payload'], first['sequence'])

            replay = service.context_request(
                r1, completion=service._commit_remote_context_ready)
            atomic_replay = service._commit_remote_context_ready(
                ready, first, 'instance:AC-A', generation_hash(ready))
            conflict = service.context_request(
                request_object('B', request_id='R2', generation=1)['payload'],
                completion=service._commit_remote_context_ready)

            self.assertEqual(first, replay)
            self.assertEqual(atomic_replay, 'IDEMPOTENT')
            self.assertEqual(len(provider.calls), 1)
            self.assertEqual(conflict['kind'], 'CONTEXT_SEQUENCE_CONFLICT')
            self.assertEqual(service.store.context_request('R1')['state'], 'VALID')
            self.assertIsNone(service.store.context_request('R2'))
            self.assertEqual(service.store.message(context_ready_message_id('R1')), outbox)

    def test_completed_request_identity_is_immutable(self):
        http = FakeContentsHttp()
        http.seed('safe-bim-mailbox/inbox/A.json', request_object('A'))
        with ClosingDirectory() as directory:
            service = started(directory, http)
            connect(service)
            service.tick()
            before = copy.deepcopy(service.store.context_request('R1'))
            http.seed('safe-bim-mailbox/inbox/B.json', request_object(
                'B', request_id='R1', project_id='P2', generation=2))
            tick = service.tick()
            self.assertIn('REQUEST_ID_CONFLICT', [item['status'] for item in tick['accepted']])
            after = service.store.context_request('R1')
            self.assertEqual(after['project_id'], before['project_id'])
            self.assertEqual(after['snapshot_id'], before['snapshot_id'])
            self.assertEqual(after['response'], before['response'])

    def test_invalidation_during_capture_blocks_ready_then_new_request_succeeds(self):
        http = FakeContentsHttp()
        http.seed('safe-bim-mailbox/inbox/A.json', request_object('A'))
        provider = CountingProvider()
        with ClosingDirectory() as directory:
            service = started(directory, http, provider)
            connect(service)
            provider.hook = lambda _request: service.context.mark_changed(instance_id='AC-A')
            first = service.tick()
            self.assertEqual(first['accepted'][0]['status'], 'CAPTURE_REVISION_CONFLICT')
            self.assertEqual(result_objects(http), {})
            self.assertIsNone(service.store.context_request('R1')['snapshot_id'])
            provider.hook = None
            http.seed('safe-bim-mailbox/inbox/B.json', request_object('B', request_id='R2', generation=2))
            second = service.tick()
            self.assertIn('CONTEXT_READY', [item['status'] for item in second['accepted']])
            self.assertEqual(service.store.meta('context_capture_revision:R2'), '1')
            self.assertEqual(len(result_objects(http)), 1)

    def test_no_context_ready_after_revision_conflict(self):
        http = FakeContentsHttp()
        http.seed('safe-bim-mailbox/inbox/A.json', request_object('A'))
        provider = CountingProvider()
        with ClosingDirectory() as directory:
            service = started(directory, http, provider)
            connect(service)
            provider.hook = lambda _request: service.context.mark_changed(instance_id='AC-A')
            service.tick()
            self.assertEqual(service.store.pending_outbox(), [])
            self.assertEqual(result_objects(http), {})
            self.assertNotEqual(service.context.context_admission('R1'), 'CURRENT')

    def test_crash_after_accept_before_capture_resumes(self):
        http = FakeContentsHttp()
        http.seed('safe-bim-mailbox/inbox/A.json', request_object('A'))
        with ClosingDirectory() as directory:
            service = started(directory, http)
            connect(service)
            service.fault_after_persist = lambda: (_ for _ in ()).throw(InjectedCrash('accepted'))
            with self.assertRaises(InjectedCrash):
                service.tick()
            self.assertIsNone(service.store.context_request('R1'))
            self.assertIsNone(service.store.meta('remote_etag'))
            crash_close(service)
            provider = CountingProvider()
            restarted = started(directory, http, provider)
            connect(restarted)
            tick = restarted.tick()
            self.assertEqual(tick['accepted'][0]['status'], 'CONTEXT_READY')
            self.assertEqual(len(provider.calls), 1)

    def test_crash_during_capture_keeps_original_start_fence(self):
        http = FakeContentsHttp()
        http.seed('safe-bim-mailbox/inbox/A.json', request_object('A'))
        with ClosingDirectory() as directory:
            service = started(directory, http, CrashOnceProvider())
            connect(service)
            with self.assertRaises(InjectedCrash):
                service.tick()
            self.assertEqual(service.store.meta('context_op_capture_revision:R1'), '0')
            self.assertEqual(service.store.meta('context_captures'), '1')
            crash_close(service)
            restarted = started(directory, http, CountingProvider())
            restarted.context.mark_changed(instance_id='AC-A')
            tick = restarted.tick()
            self.assertEqual(tick['accepted'][0]['status'], 'CAPTURE_REVISION_CONFLICT')
            self.assertEqual(restarted.store.meta('context_op_capture_revision:R1'), '0')
            self.assertEqual(restarted.store.meta('context_captures'), '1')

    def test_crash_after_provider_before_completion_publishes_nothing(self):
        http = FakeContentsHttp()
        http.seed('safe-bim-mailbox/inbox/A.json', request_object('A'))
        with ClosingDirectory() as directory:
            service = started(directory, http)
            connect(service)
            service.context.fault_after_provider_returned = lambda: (_ for _ in ()).throw(InjectedCrash('returned'))
            with self.assertRaises(InjectedCrash):
                service.tick()
            self.assertEqual(service.store.context_request('R1')['state'], 'CAPTURING')
            self.assertEqual(service.store.pending_outbox(), [])
            self.assertEqual(result_objects(http), {})

    def test_snapshot_and_outbox_commit_atomically(self):
        http = FakeContentsHttp()
        http.seed('safe-bim-mailbox/inbox/A.json', request_object('A'))
        with ClosingDirectory() as directory:
            service = started(directory, http)
            connect(service)
            service.store.fault_before_context_commit = lambda: (_ for _ in ()).throw(InjectedCrash('commit'))
            with self.assertRaises(InjectedCrash):
                service.tick()
            row = service.store.context_request('R1')
            self.assertEqual(row['state'], 'CAPTURING')
            self.assertIsNone(row['response'])
            self.assertEqual(service.store.pending_outbox(), [])

    def test_crash_after_atomic_completion_publishes_after_restart(self):
        http = FakeContentsHttp()
        http.seed('safe-bim-mailbox/inbox/A.json', request_object('A'))
        with ClosingDirectory() as directory:
            service = started(directory, http)
            connect(service)
            service.fault_after_context_commit = lambda: (_ for _ in ()).throw(InjectedCrash('before publish'))
            with self.assertRaises(InjectedCrash):
                service.tick()
            self.assertEqual(service.store.context_request('R1')['state'], 'VALID')
            self.assertEqual(len(service.store.pending_outbox()), 1)
            self.assertEqual(result_objects(http), {})
            crash_close(service)
            restarted = started(directory, http)
            tick = restarted.tick()
            self.assertEqual(tick['accepted'][0]['status'], 'CONTEXT_READY')
            self.assertEqual(len(result_objects(http)), 1)
            self.assertEqual(restarted.store.pending_outbox(), [])

    def test_ack_lost_reconciles_same_context_ready_identity(self):
        http = FakeContentsHttp()
        http.drop_ack_once = True
        http.seed('safe-bim-mailbox/inbox/A.json', request_object('A'))
        with ClosingDirectory() as directory:
            service = started(directory, http)
            connect(service)
            first = service.tick()
            self.assertEqual(first['published'][0]['status'], 'UNCERTAIN')
            message_id = service.store.pending_outbox()[0]['message_id']
            service.stop()
            service.store.close()
            restarted = started(directory, http)
            second = restarted.tick()
            self.assertEqual(second['published'][0]['status'], 'ALREADY_PUBLISHED')
            self.assertEqual(restarted.store.message(message_id)['state'], 'SENT')
            self.assertEqual(http.put_count, 1)

    def test_root_hash_is_deterministic_from_canonical_snapshot(self):
        snapshot = {'z': [3, 2, 1], 'a': {'ok': True}}
        provider = CountingProvider(snapshot)
        http = FakeContentsHttp()
        http.seed('safe-bim-mailbox/inbox/A.json', request_object('A'))
        with ClosingDirectory() as directory:
            service = started(directory, http, provider)
            connect(service)
            service.tick()
            ready = service.store.context_request('R1')['response']
            self.assertEqual(ready['rootHash'], canonical_hash(snapshot))
            self.assertEqual(ready['rootHash'], canonical_hash({'a': {'ok': True}, 'z': [3, 2, 1]}))

    def test_snapshot_canonical_json_rejects_unsupported_values(self):
        http = FakeContentsHttp()
        http.seed('safe-bim-mailbox/inbox/A.json', request_object('A'))
        with ClosingDirectory() as directory:
            service = started(directory, http, CountingProvider({'bad': float('nan')}))
            connect(service)
            with self.assertRaises(SnapshotValidationError):
                service.tick()
            self.assertIsNone(service.store.meta('remote_etag'))
            self.assertEqual(service.store.pending_outbox(), [])

    def test_context_ready_remote_identity_detects_conflict(self):
        http = FakeContentsHttp()
        http.seed('safe-bim-mailbox/inbox/A.json', request_object('A'))
        with ClosingDirectory() as directory:
            service = started(directory, http)
            connect(service)
            service.tick()
            sent = next(item for item in service.store.messages_by_state('SENT')
                        if item['kind'] == 'CONTEXT_READY')
            changed = copy.deepcopy(sent['payload'])
            changed['payload']['snapshot'] = {'different': True}
            conflict = service.mailbox.publish_result(changed)
            self.assertEqual(conflict['status'], 'MESSAGE_ID_CONFLICT')
            self.assertEqual(len(result_objects(http)), 1)

    def test_cross_instance_context_isolation(self):
        http = FakeContentsHttp()
        http.seed('safe-bim-mailbox/inbox/A.json', request_object('A', request_id='RA', instance_id='AC-A', project_id='P1'))
        http.seed('safe-bim-mailbox/inbox/B.json', request_object('B', request_id='RB', instance_id='AC-B', project_id='P2'))
        provider = CountingProvider()
        with ClosingDirectory() as directory:
            service = started(directory, http, provider)
            connect(service, 'AC-A', 'P1')
            connect(service, 'AC-B', 'P2')
            service.tick()
            self.assertEqual(service.store.context_request('RA')['project_id'], 'P1')
            self.assertEqual(service.store.context_request('RB')['project_id'], 'P2')
            self.assertEqual(service.context.by_instance['AC-A'].logical_project_id, 'P1')
            self.assertEqual(service.context.by_instance['AC-B'].logical_project_id, 'P2')
            self.assertEqual(len(result_objects(http)), 2)

    def test_etag_not_advanced_when_context_handling_is_incomplete(self):
        http = FakeContentsHttp()
        http.seed('safe-bim-mailbox/inbox/A.json', request_object('A'))
        with ClosingDirectory() as directory:
            service = started(directory, http, CountingProvider({'bad': {1, 2}}))
            connect(service)
            with self.assertRaises(SnapshotValidationError):
                service.tick()
            self.assertIsNone(service.store.meta('remote_etag'))
            self.assertIsNone(service.mailbox.etag)
            self.assertEqual(service.store.message('A')['state'], 'ACCEPTED')

    def test_auth_loss_leaves_local_bridge_ready(self):
        http = FakeContentsHttp()
        http.force_status = 401
        with ClosingDirectory() as directory:
            service = started(directory, http)
            result = service.tick()
            self.assertEqual(result['status'], 'NEEDS_AUTH')
            self.assertTrue(service.running)
            self.assertEqual(service.connections.get('BRIDGE')['status'], 'CONNECTED')
            self.assertFalse(service.health()['archicadWriteApi'])

    def test_statuses_keep_backend_and_context_verification_distinct(self):
        self.assertEqual(CONTEXT_ROUNDTRIP_STATUS, 'IMPLEMENTED_NOT_LIVE_VERIFIED')
        self.assertEqual(GITHUB_BACKEND_STATUS, 'GITHUB_LIVE_VERIFIED')


if __name__ == '__main__':
    unittest.main()
