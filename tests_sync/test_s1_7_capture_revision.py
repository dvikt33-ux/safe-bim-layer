"""S1.7 capture revision fence. Offline only. No Archicad."""
import unittest

from sync_bridge.bridge import InjectedCrash
from sync_bridge.context import ContextReady
from sync_bridge.instance_lock import MUTEX_VERIFICATION
from sync_bridge.mailbox import GITHUB_BACKEND_STATUS
from tests_sync.test_s1_3_liveness import MutableClock, QuietHttp, opened
from tests_sync.test_s1_6_context_invalidation import _evidence, _replay
from tests_sync.test_s1_reliability import reopen


def _request(request_id, instance_id='AC-A', project_id='P1'):
    return {
        'requestId': request_id,
        'logicalProjectId': project_id,
        'requestedScope': 'selection',
        'instanceId': instance_id,
    }


class CaptureRevisionFenceTests(unittest.TestCase):
    def test_inflight_capture_after_invalidation_is_blocked_and_new_request_is_current(self):
        clock = MutableClock()
        with opened_service(clock) as service:
            def boom():
                raise InjectedCrash('capture assigned')

            service.context.fault_after_capture_assigned = boom
            with self.assertRaises(InjectedCrash):
                service.context_request(_request('r1'))
            service.context.fault_after_capture_assigned = None
            self.assertEqual(service.store.context_request('r1')['state'], 'CAPTURING')
            self.assertIsNone(service.store.context_request('r1')['snapshot_id'])
            self.assertEqual(service.store.meta('context_op_capture_revision:r1'), '0')
            self.assertEqual(service.context.mark_changed(instance_id='AC-A'), 'CONTEXT_CHANGED')
            self.assertEqual(service.store.meta('context_revision:instance:AC-A'), '1')
            ready = _assigned_ready(service, 'r1')
            rejected = service.apply_context_ready(ready)
            self.assertEqual(rejected, 'CAPTURE_REVISION_CONFLICT')
            self.assertNotEqual(rejected, 'CONTEXT_READY')
            self.assertNotEqual(service.context.context_admission('r1'), 'CURRENT')
            self.assertEqual(service.store.meta('context_revision:instance:AC-A'), '1')
            self.assertEqual(service.store.meta('context_validity:instance:AC-A'), 'STALE')
            self.assertEqual(service.store.meta('context_op_capture_revision:r1'), '0')
            self.assertEqual(service.store.context_request('r1')['state'], 'CAPTURING')
            self.assertIsNone(service.store.context_request('r1')['snapshot_id'])
            resumed = service.context_request(_request('r1'))
            self.assertEqual(resumed['kind'], 'CAPTURE_REVISION_CONFLICT')
            self.assertNotEqual(resumed.get('kind'), 'CONTEXT_READY')
            self.assertEqual(service.store.meta('context_op_capture_revision:r1'), '0')
            second = service.context_request(_request('r2'))
            self.assertEqual(second['kind'], 'CONTEXT_READY')
            self.assertEqual(service.store.meta('context_capture_revision:r2'), '1')
            self.assertEqual(service.store.meta('context_revision:instance:AC-A'), '1')
            self.assertEqual(service.context.context_admission('r2'), 'CURRENT')
            self.assertNotEqual(service.context.context_admission('r1'), 'CURRENT')
            self.assertEqual(service.store.context_request('r1')['state'], 'CAPTURING')

    def test_restart_does_not_rebind_an_inflight_capture(self):
        clock = MutableClock()
        with opened_service(clock) as service:
            for _ in range(3):
                service.context.mark_changed(instance_id='AC-A')
            self.assertEqual(service.store.meta('context_revision:instance:AC-A'), '3')

            def boom():
                raise InjectedCrash('capture assigned')

            service.context.fault_after_capture_assigned = boom
            with self.assertRaises(InjectedCrash):
                service.context_request(_request('r1'))
            self.assertEqual(service.store.meta('context_op_capture_revision:r1'), '3')
            restarted = reopen(service, QuietHttp())
            self.assertEqual(restarted.store.meta('context_op_capture_revision:r1'), '3')
            self.assertEqual(restarted.context.mark_changed(instance_id='AC-A'), 'CONTEXT_CHANGED')
            self.assertEqual(restarted.store.meta('context_revision:instance:AC-A'), '4')
            resumed = restarted.context_request(_request('r1'))
            self.assertEqual(resumed['kind'], 'CAPTURE_REVISION_CONFLICT')
            self.assertNotEqual(resumed.get('kind'), 'CONTEXT_READY')
            self.assertEqual(restarted.store.meta('context_op_capture_revision:r1'), '3')
            self.assertEqual(restarted.store.context_request('r1')['state'], 'CAPTURING')
            self.assertIsNone(restarted.store.context_request('r1')['snapshot_id'])
            self.assertNotEqual(restarted.context.context_admission('r1'), 'CURRENT')
            self.assertEqual(restarted.store.meta('context_revision:instance:AC-A'), '4')
            self.assertEqual(restarted.store.meta('context_validity:instance:AC-A'), 'STALE')

    def test_completed_request_stays_immutable_and_validity_cannot_override_mismatch(self):
        clock = MutableClock()
        with opened_service(clock) as service:
            first = service.context_request(_request('r1'))
            before = _evidence(service, 'r1', 'instance:AC-A')
            self.assertEqual(service.context.mark_changed(instance_id='AC-A'), 'CONTEXT_CHANGED')
            stored = service.store.context_request('r1')
            self.assertEqual(stored['state'], 'VALID')
            self.assertEqual(stored['snapshot_id'], before['snapshot_id'])
            self.assertEqual(stored['response'], before['response'])
            self.assertEqual(service.store.meta('context_identity:instance:AC-A:1'), before['identity'])
            self.assertEqual(service.store.meta('context_capture_revision:r1'), '0')
            self.assertEqual(service.store.meta('context_revision:instance:AC-A'), '1')
            service.store.set_meta('context_validity:instance:AC-A', 'VALID')
            self.assertEqual(service.context.context_admission('r1'), 'STALE_CONTEXT')
            repeated = service.context_request(_request('r1'))
            self.assertEqual(repeated['kind'], 'CONTEXT_STALE')
            self.assertNotEqual(repeated, first)
            self.assertEqual(service.apply_context_ready(_replay(first)), 'IDEMPOTENT_STALE')
            self.assertEqual(service.store.context_request('r1')['state'], 'VALID')
            self.assertEqual(service.store.context_request('r1')['response'], before['response'])
            self.assertEqual(MUTEX_VERIFICATION, 'OFFLINE_CONTRACT_VERIFIED')
            self.assertEqual(GITHUB_BACKEND_STATUS, 'NOT_YET_LIVE_VERIFIED')

    def test_revision_check_fault_does_not_publish_a_partial_snapshot(self):
        clock = MutableClock()
        with opened_service(clock) as service:
            def assigned():
                raise InjectedCrash('capture assigned')

            service.context.fault_after_capture_assigned = assigned
            with self.assertRaises(InjectedCrash):
                service.context_request(_request('r1'))
            service.context.fault_after_capture_assigned = None
            service.context.mark_changed(instance_id='AC-A')

            def boom():
                raise InjectedCrash('during revision check')

            service.store.fault_before_context_commit = boom
            with self.assertRaises(InjectedCrash):
                service.apply_context_ready(_assigned_ready(service, 'r1'))
            self.assertEqual(service.store.context_request('r1')['state'], 'CAPTURING')
            self.assertIsNone(service.store.context_request('r1')['snapshot_id'])
            self.assertIsNone(service.store.meta('context_capture_revision:r1'))
            self.assertIsNone(service.store.meta('context_sequence:instance:AC-A'))
            self.assertEqual(service.store.meta('context_revision:instance:AC-A'), '1')
            self.assertEqual(service.store.meta('context_validity:instance:AC-A'), 'STALE')
            self.assertEqual(service.store.meta('context_op_capture_revision:r1'), '0')
            service.store.fault_before_context_commit = None
            self.assertEqual(service.apply_context_ready(_assigned_ready(service, 'r1')), 'CAPTURE_REVISION_CONFLICT')
            self.assertIsNone(service.store.context_request('r1')['snapshot_id'])


class _Opened:
    def __init__(self, clock):
        self.clock = clock
        self.directory = None
        self.service = None

    def __enter__(self):
        from tests_sync.closing import ClosingDirectory
        self.directory = ClosingDirectory()
        path = self.directory.__enter__()
        self.service = opened(path, 'a.sqlite3', self.clock)
        self.service.start()
        return self.service

    def __exit__(self, *exc):
        try:
            store = getattr(self.service, 'store', None)
            if store is not None and store._db is not None:
                self.service.stop()
                store.close()
        finally:
            self.directory.__exit__(*exc)


def opened_service(clock):
    return _Opened(clock)


def _assigned_ready(service, request_id):
    sequence, snapshot_id = service.context._assigned(request_id)
    row = service.store.context_request(request_id)
    return ContextReady(
        1, request_id, snapshot_id, row['project_id'], f'mock-{row["project_id"]}-{sequence}',
        't', {'source': 'mock', 'instanceId': row.get('instance_id')}, sequence)
