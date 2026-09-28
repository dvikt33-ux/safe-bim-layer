"""S1.6 durable per-stream context invalidation. Offline only."""
import unittest
from pathlib import Path

from sync_bridge.bridge import InjectedCrash, SafeBIMBridge
from sync_bridge.context import UI_REFRESH, UI_STALE, ContextReady
from sync_bridge.instance_lock import MUTEX_VERIFICATION
from sync_bridge.mailbox import GITHUB_BACKEND_STATUS, GitHubMailbox
from sync_bridge.store import BridgeStore
from sync_bridge.ui_model import SafeBIMUI
from tests_sync.closing import ClosingDirectory
from tests_sync.test_s1_3_liveness import OWNER, MutableClock, QuietHttp, opened
from tests_sync.test_s1_reliability import reopen


def _evidence(service, request_id, stream):
    row = service.store.context_request(request_id)
    sequence = row['response']['sequence'] if isinstance(row.get('response'), dict) else None
    return {
        'state': row['state'],
        'snapshot_id': row['snapshot_id'],
        'response': row.get('response'),
        'watermark': service.store.meta(f'context_sequence:{stream}'),
        'identity': service.store.meta(f'context_identity:{stream}:{sequence}') if sequence else None,
    }


def _replay(ready):
    return ContextReady(
        ready['protocolVersion'], ready['requestId'], ready['snapshotId'],
        ready['logicalProjectId'], ready['rootHash'], ready['capturedAt'],
        ready['payload'], ready['sequence'])


class DurableInvalidationTests(unittest.TestCase):
    def test_stale_survives_restart_and_cannot_be_revived(self):
        clock = MutableClock()
        with ClosingDirectory() as directory:
            service = opened(directory, 'a.sqlite3', clock)
            service.start()
            first = service.context_request({
                'requestId': 'r1', 'logicalProjectId': 'P1',
                'requestedScope': 'selection', 'instanceId': 'AC-A',
            })
            self.assertEqual(first['sequence'], 1)
            before = _evidence(service, 'r1', 'instance:AC-A')
            captures = service.store.meta('context_captures')
            self.assertEqual(service.context.mark_changed(instance_id='AC-A'), 'CONTEXT_CHANGED')
            stored = service.store.context_request('r1')
            self.assertEqual(stored['state'], 'STALE')
            self.assertEqual(stored['snapshot_id'], before['snapshot_id'])
            self.assertEqual(stored['response'], before['response'])
            self.assertEqual(service.store.meta('context_sequence:instance:AC-A'), before['watermark'])
            self.assertEqual(service.store.meta('context_identity:instance:AC-A:1'), before['identity'])
            self.assertEqual(service.context.stream_view(instance_id='AC-A')['lease'], 'STALE')
            self.assertEqual(service.context.stream_view(instance_id='AC-A')['banner'], UI_STALE)
            path = service.store.path
            service.stop()
            service.store.close()
            restarted = SafeBIMBridge(
                BridgeStore(path), GitHubMailbox(QuietHttp()), owner=OWNER, clock=clock)
            restarted.start()
            self.assertEqual(restarted.store.context_request('r1')['state'], 'STALE')
            repeated = restarted.context_request({
                'requestId': 'r1', 'logicalProjectId': 'P1',
                'requestedScope': 'selection', 'instanceId': 'AC-A',
            })
            self.assertEqual(repeated['kind'], 'CONTEXT_STALE')
            self.assertNotEqual(repeated.get('kind'), 'CONTEXT_READY')
            self.assertNotEqual(repeated, first)
            self.assertTrue(repeated['refreshRequired'])
            self.assertEqual(restarted.store.meta('context_captures'), captures)
            self.assertEqual(restarted.store.context_request('r1')['state'], 'STALE')
            self.assertEqual(restarted.store.context_request('r1')['response']['kind'], 'CONTEXT_READY')
            replay = _replay(first)
            self.assertEqual(restarted.apply_context_ready(replay), 'IDEMPOTENT_STALE')
            self.assertEqual(restarted.store.context_request('r1')['state'], 'STALE')
            self.assertEqual(_evidence(restarted, 'r1', 'instance:AC-A')['response'], before['response'])
            higher = ContextReady(
                first['protocolVersion'], 'r1', 'snap-new', 'P1', 'hash-new', 't',
                {'source': 'other'}, 2)
            self.assertEqual(restarted.apply_context_ready(higher), 'REQUEST_GENERATION_CONFLICT')
            self.assertEqual(restarted.store.context_request('r1')['state'], 'STALE')
            self.assertEqual(restarted.store.context_request('r1')['snapshot_id'], first['snapshotId'])
            wrong = ContextReady(
                first['protocolVersion'], 'r1', first['snapshotId'], 'P2', first['rootHash'],
                first['capturedAt'], first['payload'], 1)
            self.assertEqual(restarted.apply_context_ready(wrong), 'CONTEXT_ERROR')
            self.assertEqual(restarted.store.context_request('r1')['state'], 'STALE')
            second = restarted.context_request({
                'requestId': 'r2', 'logicalProjectId': 'P1',
                'requestedScope': 'selection', 'instanceId': 'AC-A',
            })
            self.assertEqual(second['kind'], 'CONTEXT_READY')
            self.assertEqual(second['sequence'], 2)
            self.assertEqual(restarted.store.context_request('r2')['state'], 'VALID')
            self.assertEqual(restarted.store.context_request('r1')['state'], 'STALE')
            self.assertEqual(restarted.store.context_request('r1')['snapshot_id'], first['snapshotId'])
            self.assertNotEqual(second['snapshotId'], first['snapshotId'])
            self.assertEqual(restarted.context.context_admission('r1'), 'STALE_CONTEXT')
            self.assertEqual(restarted.context.context_admission('r2'), 'CURRENT')

    def test_cross_instance_invalidation_stays_isolated(self):
        clock = MutableClock()
        with ClosingDirectory() as directory:
            service = opened(directory, 'a.sqlite3', clock)
            service.start()
            ready_a = service.context_request({
                'requestId': 'rA', 'logicalProjectId': 'P1',
                'requestedScope': 'selection', 'instanceId': 'AC-A',
            })
            ready_b = service.context_request({
                'requestId': 'rB', 'logicalProjectId': 'P2',
                'requestedScope': 'selection', 'instanceId': 'AC-B',
            })
            evidence_b = _evidence(service, 'rB', 'instance:AC-B')
            self.assertEqual(service.context.mark_changed(instance_id='AC-A'), 'CONTEXT_CHANGED')
            self.assertEqual(service.store.context_request('rA')['state'], 'STALE')
            self.assertEqual(service.store.context_request('rB')['state'], 'VALID')
            self.assertEqual(_evidence(service, 'rB', 'instance:AC-B'), evidence_b)
            self.assertEqual(service.context.lease, 'VALID')
            self.assertIn('Контекст #', service.context.ui_banner)
            self.assertNotEqual(service.context.ui_banner, UI_STALE)
            ui_a = SafeBIMUI()
            ui_b = SafeBIMUI()
            service.context.apply_stream_ui(ui_a, instance_id='AC-A')
            service.context.apply_stream_ui(ui_b, instance_id='AC-B')
            self.assertIn(UI_STALE, ui_a.render())
            self.assertIn(f'[{UI_REFRESH}]', ui_a.render())
            self.assertEqual(ui_a.context_lease_state, 'STALE')
            self.assertEqual(ui_b.context_lease_state, 'VALID')
            self.assertEqual(ui_b.refresh_label, '')
            self.assertTrue(ui_b.context_banner.startswith('Контекст #'))
            self.assertNotIn(UI_STALE, ui_b.render())
            restarted = reopen(service, QuietHttp())
            self.assertEqual(restarted.store.context_request('rA')['state'], 'STALE')
            self.assertEqual(restarted.store.context_request('rB')['state'], 'VALID')
            self.assertEqual(restarted.store.context_request('rB')['response'], ready_b)
            self.assertEqual(restarted.context.stream_view(instance_id='AC-A')['lease'], 'STALE')
            self.assertEqual(restarted.context.stream_view(instance_id='AC-B')['lease'], 'VALID')
            again = restarted.context_request({
                'requestId': 'rB', 'logicalProjectId': 'P2',
                'requestedScope': 'selection', 'instanceId': 'AC-B',
            })
            self.assertEqual(again, ready_b)
            stale = restarted.context_request({
                'requestId': 'rA', 'logicalProjectId': 'P1',
                'requestedScope': 'selection', 'instanceId': 'AC-A',
            })
            self.assertEqual(stale['kind'], 'CONTEXT_STALE')
            self.assertEqual(restarted.store.context_request('rA')['snapshot_id'], ready_a['snapshotId'])
            self.assertEqual(restarted.context.stream_view(instance_id='AC-B')['lease'], 'VALID')

    def test_stream_revision_is_durable_and_capture_binds_to_it(self):
        clock = MutableClock()
        with ClosingDirectory() as directory:
            service = opened(directory, 'a.sqlite3', clock)
            service.start()
            service.context_request({
                'requestId': 'r1', 'logicalProjectId': 'P1',
                'requestedScope': 'selection', 'instanceId': 'AC-A',
            })
            self.assertEqual(service.store.meta('context_capture_revision:r1'), '0')
            self.assertIsNone(service.store.meta('context_revision:instance:AC-A'))
            self.assertEqual(service.context.context_admission('r1'), 'CURRENT')
            self.assertEqual(service.context.mark_changed(instance_id='AC-A'), 'CONTEXT_CHANGED')
            self.assertEqual(service.store.meta('context_revision:instance:AC-A'), '1')
            self.assertEqual(service.store.meta('context_capture_revision:r1'), '0')
            self.assertEqual(service.context.context_admission('r1'), 'STALE_CONTEXT')
            self.assertEqual(service.context.mark_changed(instance_id='AC-A'), 'CONTEXT_CHANGED')
            self.assertEqual(service.store.meta('context_revision:instance:AC-A'), '2')
            restarted = reopen(service, QuietHttp())
            self.assertEqual(restarted.store.meta('context_revision:instance:AC-A'), '2')
            self.assertEqual(restarted.store.context_request('r1')['state'], 'STALE')
            second = restarted.context_request({
                'requestId': 'r2', 'logicalProjectId': 'P1',
                'requestedScope': 'selection', 'instanceId': 'AC-A',
            })
            self.assertEqual(second['kind'], 'CONTEXT_READY')
            self.assertEqual(restarted.store.meta('context_capture_revision:r2'), '2')
            self.assertEqual(restarted.store.meta('context_revision:instance:AC-A'), '2')
            self.assertEqual(restarted.store.meta('context_validity:instance:AC-A'), 'VALID')
            self.assertEqual(restarted.context.context_admission('r2'), 'CURRENT')
            self.assertEqual(restarted.context.context_admission('r1'), 'STALE_CONTEXT')
            self.assertEqual(MUTEX_VERIFICATION, 'OFFLINE_CONTRACT_VERIFIED')
            self.assertEqual(GITHUB_BACKEND_STATUS, 'NOT_YET_LIVE_VERIFIED')

    def test_invalidation_crash_does_not_split_state_and_revision(self):
        clock = MutableClock()
        with ClosingDirectory() as directory:
            service = opened(directory, 'a.sqlite3', clock)
            service.start()
            first = service.context_request({
                'requestId': 'r1', 'logicalProjectId': 'P1',
                'requestedScope': 'selection', 'instanceId': 'AC-A',
            })
            before = _evidence(service, 'r1', 'instance:AC-A')
            revision = service.store.meta('context_revision:instance:AC-A')
            validity = service.store.meta('context_validity:instance:AC-A')

            def boom():
                raise InjectedCrash('between invalidation writes')

            service.store.fault_before_invalidation_commit = boom
            with self.assertRaises(InjectedCrash):
                service.context.mark_changed(instance_id='AC-A')
            self.assertEqual(_evidence(service, 'r1', 'instance:AC-A'), before)
            self.assertEqual(service.store.context_request('r1')['state'], 'VALID')
            self.assertEqual(service.store.meta('context_revision:instance:AC-A'), revision)
            self.assertEqual(service.store.meta('context_validity:instance:AC-A'), validity)
            self.assertNotEqual(validity, 'STALE')
            self.assertEqual(service.context.lease, 'VALID')
            service.store.fault_before_invalidation_commit = None
            service.context.mark_changed(instance_id='AC-A')
            self.assertEqual(service.store.context_request('r1')['state'], 'STALE')
            self.assertEqual(service.store.meta('context_revision:instance:AC-A'), '1')
            self.assertEqual(service.store.meta('context_validity:instance:AC-A'), 'STALE')
            self.assertEqual(service.store.context_request('r1')['snapshot_id'], first['snapshotId'])
            self.assertEqual(service.store.context_request('r1')['response'], before['response'])
            self.assertEqual(service.store.meta('context_identity:instance:AC-A:1'), before['identity'])
            restarted = reopen(service, QuietHttp())
            self.assertEqual(restarted.store.context_request('r1')['state'], 'STALE')
            self.assertEqual(restarted.store.meta('context_revision:instance:AC-A'), '1')
            self.assertEqual(restarted.store.meta('context_validity:instance:AC-A'), 'STALE')
