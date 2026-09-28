"""S1.4 immutable context generation identity. Offline only."""
import unittest
from pathlib import Path

from sync_bridge.context import ContextReady
from sync_bridge.instance_lock import MUTEX_VERIFICATION
from sync_bridge.mailbox import GITHUB_BACKEND_STATUS, GitHubMailbox
from sync_bridge.store import BridgeStore
from sync_bridge.bridge import SafeBIMBridge
from tests_sync.closing import ClosingDirectory
from tests_sync.test_s1_3_liveness import OWNER, MutableClock, QuietHttp, opened


def _row(service, request_id='req-a'):
    return service.store.context_request(request_id)


def _mark(service, instance_id='AC-A'):
    return service.store.meta(f'context_sequence:instance:{instance_id}')


class ContextIdentityTests(unittest.TestCase):
    def test_generation_identity_is_immutable_across_restart(self):
        clock = MutableClock()
        with ClosingDirectory() as directory:
            service = opened(directory, 'a.sqlite3', clock)
            service.start()
            first = service.context_request({
                'requestId': 'req-a', 'logicalProjectId': 'P1',
                'requestedScope': 'selection', 'instanceId': 'AC-A',
            })
            stored = _row(service)['response']
            replay = ContextReady(
                stored['protocolVersion'], stored['requestId'], stored['snapshotId'],
                stored['logicalProjectId'], stored['rootHash'], stored['capturedAt'],
                stored['payload'], stored['sequence'])
            self.assertEqual(service.apply_context_ready(replay), 'IDEMPOTENT')
            self.assertEqual(_row(service)['snapshot_id'], first['snapshotId'])
            self.assertEqual(_row(service)['response']['capturedAt'], stored['capturedAt'])
            self.assertEqual(_mark(service), '1')

            conflicts = [
                ('snapshot', ContextReady(
                    1, 'req-a', 'snap-other', 'P1', stored['rootHash'], stored['capturedAt'],
                    stored['payload'], 1)),
                ('hash', ContextReady(
                    1, 'req-a', stored['snapshotId'], 'P1', 'other-hash', stored['capturedAt'],
                    stored['payload'], 1)),
                ('payload', ContextReady(
                    1, 'req-a', stored['snapshotId'], 'P1', stored['rootHash'], stored['capturedAt'],
                    {'source': 'other'}, 1)),
            ]
            for name, ready in conflicts:
                with self.subTest(name=name):
                    self.assertEqual(service.apply_context_ready(ready), 'CONTEXT_SEQUENCE_CONFLICT')
                    self.assertEqual(_row(service)['snapshot_id'], first['snapshotId'])
                    self.assertEqual(_row(service)['response']['rootHash'], stored['rootHash'])
                    self.assertEqual(_row(service)['response']['payload'], stored['payload'])
                    self.assertEqual(_mark(service), '1')

            rejected = [
                ('protocol', ContextReady(
                    99, 'req-a', stored['snapshotId'], 'P1', stored['rootHash'], stored['capturedAt'],
                    stored['payload'], 1), 'PROTOCOL_ERROR'),
                ('empty-snapshot', ContextReady(
                    1, 'req-a', '  ', 'P1', stored['rootHash'], stored['capturedAt'],
                    stored['payload'], 1), 'CONTEXT_ERROR'),
                ('sequence-zero', ContextReady(
                    1, 'req-a', stored['snapshotId'], 'P1', stored['rootHash'], stored['capturedAt'],
                    stored['payload'], 0), 'CONTEXT_ERROR'),
                ('payload-type', ContextReady(
                    1, 'req-a', stored['snapshotId'], 'P1', stored['rootHash'], stored['capturedAt'],
                    ['not', 'a', 'dict'], 1), 'CONTEXT_ERROR'),
            ]
            for name, ready, status in rejected:
                with self.subTest(name=name):
                    self.assertEqual(service.apply_context_ready(ready), status)
                    self.assertEqual(_row(service)['snapshot_id'], first['snapshotId'])
                    self.assertEqual(_mark(service), '1')

            path = service.store.path
            service.stop()
            service.store.close()
            restarted = SafeBIMBridge(
                BridgeStore(path), GitHubMailbox(QuietHttp()), owner=OWNER, clock=clock)
            restarted.start()
            self.assertEqual(restarted.apply_context_ready(conflicts[0][1]), 'CONTEXT_SEQUENCE_CONFLICT')
            self.assertEqual(restarted.apply_context_ready(replay), 'IDEMPOTENT')
            self.assertEqual(_row(restarted)['snapshot_id'], first['snapshotId'])
            self.assertEqual(_mark(restarted), '1')
            self.assertEqual(MUTEX_VERIFICATION, 'OFFLINE_CONTRACT_VERIFIED')
            self.assertEqual(GITHUB_BACKEND_STATUS, 'NOT_YET_LIVE_VERIFIED')
