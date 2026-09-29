"""S1.3 lease liveness and context stream watermark. Offline only."""
import os
import subprocess
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sync_bridge.bridge import InjectedCrash, InstanceConflict, LeaseLost, SafeBIMBridge
from sync_bridge.context import ContextReady
from sync_bridge.instance_lock import MUTEX_VERIFICATION, OWNERSHIP_GATE, SQLITE_LEASE_ROLE
from sync_bridge.mailbox import GITHUB_BACKEND_STATUS, GitHubMailbox
from sync_bridge.security import PeerIdentity
from sync_bridge.store import BridgeStore
from tests_sync.closing import ClosingDirectory
from tests_sync.test_sync_bridge import HttpResponse, ScriptedHttp

OWNER = PeerIdentity('S-1-5-21-1', 'session-7')
TTL = 30


class MutableClock:
    def __init__(self):
        self.moment = datetime(2026, 9, 28, 12, 0, tzinfo=timezone.utc)

    def __call__(self):
        return self.moment.isoformat()

    def advance(self, seconds):
        self.moment += timedelta(seconds=seconds)


class QuietHttp:
    def __init__(self):
        self.calls = []

    def request(self, method, url, headers, body=None):
        self.calls.append((method, url, dict(headers), body))
        return HttpResponse(200, {'messages': []})


def opened(directory, name, clock, peer=OWNER):
    store = BridgeStore(Path(directory) / name)
    return SafeBIMBridge(
        store, GitHubMailbox(QuietHttp()), owner=peer, instance_id='bridge-1',
        clock=clock, lease_ttl_seconds=TTL)


def _windows_competing_mutex_probe(user_sid: str) -> str:
    """Try the production mutex from another Windows process."""
    repo = Path(__file__).resolve().parents[1]
    code = r"""
import sys
from sync_bridge.instance_lock import SingleInstanceLock

lock = SingleInstanceLock(sys.argv[1])
status = lock.try_acquire()
print(status)
if status in ('acquired', 'abandoned'):
    lock.release()
"""
    env = dict(os.environ)
    env['PYTHONPATH'] = str(repo)
    result = subprocess.run(
        [sys.executable, '-c', code, user_sid],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr + result.stdout)
    return result.stdout.strip()


class LiveLeaseTests(unittest.TestCase):
    def test_live_owner_survives_many_ttls_and_stop_releases(self):
        clock = MutableClock()
        with ClosingDirectory() as directory:
            live_peer = PeerIdentity(
                'S-1-5-21-31313131-32323232-33333333-3434',
                'session-7',
            )
            owner = opened(directory, 'a.sqlite3', clock, live_peer)
            owner.start()
            try:
                self.assertIn('CreateMutexW', [call[0] for call in owner.instance_lock.kernel.calls])
                self.assertEqual(owner.health()['ownership'], OWNERSHIP_GATE)
                self.assertEqual(owner.health()['sqliteLeaseRole'], SQLITE_LEASE_ROLE)

                clock.advance(TTL * 10 + 5)
                self.assertLess(owner.store.meta('lease_expires'), clock())

                if os.name == 'nt':
                    # Win32 mutexes are recursive for the owning thread.
                    # A real competitor must therefore be another process.
                    self.assertEqual(
                        _windows_competing_mutex_probe(live_peer.user_sid),
                        'blocked',
                    )
                    other = None
                else:
                    other = opened(directory, 'a.sqlite3', clock)
                    with self.assertRaises(InstanceConflict):
                        other.start()

                self.assertTrue(owner.heartbeat())
                self.assertGreater(owner.store.meta('lease_expires'), clock())

                if os.name == 'nt':
                    self.assertEqual(
                        _windows_competing_mutex_probe(live_peer.user_sid),
                        'blocked',
                    )
                else:
                    with self.assertRaises(InstanceConflict):
                        other.start()

                self.assertTrue(owner.instance_lock.held())
            finally:
                owner.stop()

            if os.name == 'nt':
                self.assertIn(
                    _windows_competing_mutex_probe(live_peer.user_sid),
                    ('acquired', 'abandoned'),
                )
            else:
                other.start()
                try:
                    self.assertTrue(other.running)
                finally:
                    other.stop()

            self.assertEqual(MUTEX_VERIFICATION, 'OFFLINE_CONTRACT_VERIFIED')
            self.assertEqual(GITHUB_BACKEND_STATUS, 'GITHUB_LIVE_VERIFIED')

    def test_crashed_owner_allows_immediate_takeover(self):
        """Abandoned mutex allows takeover without waiting for SQLite TTL."""
        clock = MutableClock()
        with ClosingDirectory() as directory:
            crashed = opened(directory, 'a.sqlite3', clock)
            crashed.start()
            crashed_epoch = crashed.epoch
            replacement = opened(directory, 'a.sqlite3', clock)
            try:
                crashed.crash()
                self.assertFalse(crashed.instance_lock.held())
                self.assertTrue(bool(crashed.store.meta('lease_token')))
                replacement.start()
                self.assertTrue(replacement.running)
                self.assertEqual(replacement.lease_state, 'HELD')
                self.assertEqual(replacement.epoch, crashed_epoch + 1)
                self.assertEqual(replacement.store.meta('lease_role'), 'DIAGNOSTIC_ONLY')
            finally:
                replacement.close()
                crashed.close()

class LeaseLossTests(unittest.TestCase):
    def test_detected_loss_stops_work_until_a_new_process(self):
        clock = MutableClock()
        with ClosingDirectory() as directory:
            http = QuietHttp()
            store = BridgeStore(Path(directory) / 'a.sqlite3')
            owner = SafeBIMBridge(
                store, GitHubMailbox(http), owner=OWNER, clock=clock, lease_ttl_seconds=TTL)
            owner.start()
            owner.queue_result('job-1', {'status': 'one'})
            owner.instance_lock.abandon()
            self.assertTrue(owner.running)
            lost = owner.tick()
            self.assertEqual(lost['status'], 'LEASE_LOST')
            self.assertEqual(lost['published'], [])
            self.assertEqual(http.calls, [])
            self.assertEqual(owner.connections.get('BRIDGE')['status'], 'ERROR')
            self.assertEqual(owner.connections.get('BRIDGE')['detail'], 'LEASE_LOST')
            with self.assertRaises(LeaseLost):
                owner.accept_remote_message({'messageId': 'N', 'body': {'recipe': 'y'}})
            self.assertIsNone(owner.store.job_for_message('N'))
            with self.assertRaises(LeaseLost):
                owner.context_request({
                    'requestId': 'ctx-lost', 'logicalProjectId': 'P1',
                    'requestedScope': 'selection', 'instanceId': 'AC-A',
                })
            self.assertIsNone(owner.store.meta('context_captures'))
            with self.assertRaises(LeaseLost):
                owner.flush_outbox()
            self.assertEqual(owner.store.message('result-job-1')['state'], 'PENDING')
            restored = opened(directory, 'a.sqlite3', clock)
            restored.mailbox = GitHubMailbox(ScriptedHttp([HttpResponse(200, {'ok': True})]))
            try:
                restored.start()
                self.assertTrue(restored.running)
                accepted = restored.accept_remote_message(
                    {'messageId': 'N', 'body': {'recipe': 'y'}})
                self.assertTrue(accepted['jobCreated'])
                with self.assertRaises(LeaseLost):
                    owner.accept_remote_message(
                        {'messageId': 'N2', 'body': {'recipe': 'z'}})
            finally:
                restored.close()
                owner.close()

class ContextWatermarkTests(unittest.TestCase):
    def test_request_path_watermark_rejects_stale_and_survives_restart(self):
        clock = MutableClock()
        with ClosingDirectory() as directory:
            service = opened(directory, 'a.sqlite3', clock)
            service.start()
            first = service.context_request({
                'requestId': 'req-a', 'logicalProjectId': 'P1',
                'requestedScope': 'selection', 'instanceId': 'AC-A',
            })
            second = service.context_request({
                'requestId': 'req-b', 'logicalProjectId': 'P2',
                'requestedScope': 'selection', 'instanceId': 'AC-B',
            })
            self.assertEqual(first['sequence'], 1)
            self.assertEqual(second['sequence'], 2)
            self.assertEqual(service.store.meta('context_sequence:instance:AC-A'), '1')
            self.assertEqual(service.store.meta('context_sequence:instance:AC-B'), '2')
            self.assertEqual(service.context.current.request_id, 'req-b')
            old = ContextReady(1, 'req-a', 'snap-old', 'P1', 'hash-old', 't', {'source': 'mock'}, 0)
            self.assertEqual(service.apply_context_ready(old), 'CONTEXT_ERROR')
            self.assertEqual(service.store.context_request('req-a')['snapshot_id'], first['snapshotId'])
            blocked = ContextReady(1, 'req-a', 'snap-a2', 'P1', 'hash-2', 't', {'source': 'mock'}, 2)
            self.assertEqual(service.apply_context_ready(blocked), 'REQUEST_GENERATION_CONFLICT')
            self.assertEqual(service.store.context_request('req-a')['snapshot_id'], first['snapshotId'])
            service.store.put_context_request(
                'req-a2', 'P1', 'selection', 'CAPTURING', 't', instance_id='AC-A')
            service.store.set_meta('context_op_capture_revision:req-a2', '0')
            accepted = ContextReady(
                1, 'req-a2', 'snap-a2', 'P1', 'hash-2', 't', {'source': 'mock'}, 2)
            self.assertEqual(service.apply_context_ready(accepted), 'CONTEXT_READY')
            stale = ContextReady(
                1, 'req-a2', 'snap-a1', 'P1', 'hash-1', 't', {'source': 'mock'}, 1)
            self.assertEqual(service.apply_context_ready(stale), 'IGNORED_STALE')
            self.assertEqual(service.store.context_request('req-a2')['snapshot_id'], 'snap-a2')
            path = service.store.path
            service.stop()
            service.store.close()
            restarted = SafeBIMBridge(
                BridgeStore(path), GitHubMailbox(QuietHttp()), owner=OWNER, clock=clock)
            try:
                restarted.start()
                self.assertEqual(restarted.apply_context_ready(stale), 'IGNORED_STALE')
                self.assertEqual(
                    restarted.store.context_request('req-a2')['snapshot_id'], 'snap-a2')
                self.assertEqual(
                    restarted.store.context_request('req-a')['snapshot_id'], first['snapshotId'])
                self.assertEqual(
                    restarted.store.meta('context_sequence:instance:AC-A'), '2')
            finally:
                restarted.close()

    def test_watermark_and_ready_state_commit_together(self):
        clock = MutableClock()
        with ClosingDirectory() as directory:
            service = opened(directory, 'a.sqlite3', clock)
            service.start()
            try:
                def boom():
                    raise InjectedCrash('between context writes')

                service.store.fault_before_context_commit = boom
                with self.assertRaises(InjectedCrash):
                    service.context_request({
                        'requestId': 'req-fail', 'logicalProjectId': 'P1',
                        'requestedScope': 'selection', 'instanceId': 'AC-A',
                    })
                failed = service.store.context_request('req-fail')
                self.assertEqual(failed['state'], 'CAPTURING')
                self.assertIsNone(failed['snapshot_id'])
                self.assertIsNone(service.store.meta('context_sequence:instance:AC-A'))
                service.store.fault_before_context_commit = None
                ready = service.context_request({
                    'requestId': 'req-ok', 'logicalProjectId': 'P1',
                    'requestedScope': 'selection', 'instanceId': 'AC-A',
                })
                stored = service.store.context_request('req-ok')
                self.assertEqual(stored['state'], 'VALID')
                self.assertEqual(stored['snapshot_id'], ready['snapshotId'])
                self.assertEqual(
                    service.store.meta('context_sequence:instance:AC-A'),
                    str(ready['sequence']))
            finally:
                service.close()
