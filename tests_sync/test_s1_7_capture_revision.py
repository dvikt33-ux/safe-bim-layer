"""S1.7 capture revision fence. Offline only. No Archicad."""
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from sync_bridge.bridge import InjectedCrash, SafeBIMBridge
from sync_bridge.context import ContextReady
from sync_bridge.mailbox import GitHubMailbox
from sync_bridge.security import PeerIdentity
from sync_bridge.store import BridgeStore
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
            self.assertEqual(GITHUB_BACKEND_STATUS, 'IMPLEMENTED_NOT_LIVE_VERIFIED')

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


class UpgradeFenceTests(unittest.TestCase):
    def test_s1_6_capture_without_fence_cannot_become_current(self):
        repo = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old = root / 's16'
            old.mkdir()
            archive = subprocess.run(
                ['git', 'archive', 'b4f6bfe798e28f0dbebf44bfabb6a84ad28a9f05', 'sync_bridge'],
                cwd=repo, check=True, capture_output=True)
            subprocess.run(['tar', '-x'], input=archive.stdout, cwd=old, check=True)
            db_path = root / 's16.sqlite3'
            script = root / 'make_s16.py'

            # The archived S1.6 fixture must not contend with the production
            # mutex held by another test in this Python process.  Keep the
            # actual S1.6 code/database behaviour; isolate only its OS mutex
            # namespace by using a dedicated valid test SID.
            fixture_sid = 'S-1-5-21-71717171-72727272-73737373-7474'
            fixture_script = _S16_SCRIPT.replace('S-1-5-21-1', fixture_sid)
            self.assertNotEqual(
                fixture_script,
                _S16_SCRIPT,
                'S1.6 fixture SID replacement did not match',
            )
            script.write_text(fixture_script)

            made = subprocess.run(
                [sys.executable, str(script), str(db_path)],
                cwd=old,
                env={**os.environ, 'PYTHONPATH': str(old)},
                capture_output=True, text=True)
            self.assertEqual(made.returncode, 0, made.stderr + made.stdout)
            raw = sqlite3.connect(db_path)
            try:
                state = raw.execute(
                    "SELECT state, snapshot_id FROM context_requests WHERE request_id='r1'").fetchone()
                op = raw.execute(
                    "SELECT value FROM meta WHERE key='context_op_capture:r1'").fetchone()
                fence = raw.execute(
                    "SELECT value FROM meta WHERE key='context_op_capture_revision:r1'").fetchone()
            finally:
                raw.close()
            self.assertEqual(state[0], 'CAPTURING')
            self.assertIsNone(state[1])
            self.assertTrue(op and op[0])
            self.assertIsNone(fence)
            service = SafeBIMBridge(
                BridgeStore(db_path), GitHubMailbox(QuietHttp()),
                owner=PeerIdentity(fixture_sid, 'session-7'),
                clock=MutableClock(), instance_id='bridge-s17')
            service.start()
            try:
                self.assertEqual(service.context.mark_changed(instance_id='AC-A'), 'CONTEXT_CHANGED')
                self.assertEqual(service.store.meta('context_revision:instance:AC-A'), '1')
                resumed = service.context_request(_request('r1'))
                self.assertEqual(resumed['kind'], 'CAPTURE_REVISION_MISSING')
                self.assertNotEqual(resumed['kind'], 'CONTEXT_READY')
                self.assertNotEqual(service.context.context_admission('r1'), 'CURRENT')
                self.assertEqual(service.store.context_request('r1')['state'], 'CAPTURING')
                self.assertIsNone(service.store.context_request('r1')['snapshot_id'])
                self.assertIsNone(service.store.meta('context_sequence:instance:AC-A'))
                self.assertIsNone(service.store.meta('context_identity:instance:AC-A:1'))
                self.assertIsNone(service.store.meta('context_capture_revision:r1'))
                self.assertIsNone(service.store.meta('context_op_capture_revision:r1'))
                sequence, snapshot_id = service.store.meta('context_op_capture:r1').split(':', 1)
                rejected = service.apply_context_ready(ContextReady(
                    1, 'r1', snapshot_id, 'P1', 'mock-P1-1', 't', {'source': 'mock'}, int(sequence)))
                self.assertEqual(rejected, 'CAPTURE_REVISION_MISSING')
                self.assertIsNone(service.store.context_request('r1')['snapshot_id'])
                again = service.context_request(_request('r1'))
                self.assertEqual(again['kind'], 'CAPTURE_REVISION_MISSING')
                second = service.context_request(_request('r2'))
                self.assertEqual(second['kind'], 'CONTEXT_READY')
                self.assertEqual(service.context.context_admission('r2'), 'CURRENT')
                self.assertEqual(service.store.meta('context_capture_revision:r2'), '1')
                self.assertEqual(service.store.meta('context_revision:instance:AC-A'), '1')
                self.assertNotEqual(service.context.context_admission('r1'), 'CURRENT')
                self.assertEqual(service.store.context_request('r1')['state'], 'CAPTURING')
            finally:
                service.stop()
                service.store.close()


_S16_SCRIPT = r'''
import sys
from sync_bridge.bridge import InjectedCrash, SafeBIMBridge
from sync_bridge.mailbox import GitHubMailbox
from sync_bridge.security import PeerIdentity
from sync_bridge.store import BridgeStore

class Http:
    def request(self, *args, **kwargs):
        raise AssertionError('s1.6 fixture must not call http')

class Clock:
    def __call__(self):
        return '2026-09-28T00:00:00+00:00'

service = SafeBIMBridge(
    BridgeStore(sys.argv[1]), GitHubMailbox(Http()),
    owner=PeerIdentity('S-1-5-21-1', 'session-7'),
    clock=Clock(), instance_id='bridge-s16')
service.start()

def boom():
    raise InjectedCrash('assigned')

service.context.fault_after_capture_assigned = boom
try:
    service.context_request({
        'requestId': 'r1',
        'logicalProjectId': 'P1',
        'requestedScope': 'selection',
        'instanceId': 'AC-A',
    })
except InjectedCrash:
    pass
else:
    raise SystemExit('s1.6 capture did not stop after assignment')
row = service.store.context_request('r1')
if row['state'] != 'CAPTURING' or row['snapshot_id'] is not None:
    raise SystemExit('s1.6 row is not an unfinished capture')
if not service.store.meta('context_op_capture:r1'):
    raise SystemExit('s1.6 did not assign a capture operation')
if service.store.meta('context_op_capture_revision:r1') is not None:
    raise SystemExit('s1.6 wrote a capture-start revision')
service.stop()
service.store.close()
'''


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
