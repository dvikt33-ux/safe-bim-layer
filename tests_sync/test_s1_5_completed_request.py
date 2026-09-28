"""S1.5 completed context request identity. Offline only."""
import unittest
from pathlib import Path

from sync_bridge.bridge import SafeBIMBridge
from sync_bridge.context import PROTOCOL_VERSION, ContextReady
from sync_bridge.instance_lock import MUTEX_VERIFICATION
from sync_bridge.mailbox import GITHUB_BACKEND_STATUS, GitHubMailbox
from sync_bridge.store import BridgeStore
from tests_sync.closing import ClosingDirectory
from tests_sync.test_s1_3_liveness import OWNER, MutableClock, QuietHttp, opened


def _frozen(service, request_id='r1'):
    row = service.store.context_request(request_id)
    stream = 'instance:AC-A'
    sequence = row['response']['sequence']
    return {
        'state': row['state'],
        'snapshot_id': row['snapshot_id'],
        'response': row['response'],
        'watermark': service.store.meta(f'context_sequence:{stream}'),
        'identity': service.store.meta(f'context_identity:{stream}:{sequence}'),
    }


class CompletedRequestTests(unittest.TestCase):
    def test_completed_request_id_rejects_a_later_generation(self):
        clock = MutableClock()
        with ClosingDirectory() as directory:
            service = opened(directory, 'a.sqlite3', clock)
            service.start()
            first = service.context_request({
                'requestId': 'r1', 'logicalProjectId': 'P1',
                'requestedScope': 'selection', 'instanceId': 'AC-A',
            })
            self.assertEqual(first['sequence'], 1)
            self.assertEqual(first['protocolVersion'], PROTOCOL_VERSION)
            before = _frozen(service)
            higher = ContextReady(
                PROTOCOL_VERSION, 'r1', 'snap-new', 'P1', 'hash-new', 't', {'source': 'other'}, 2)
            self.assertEqual(service.apply_context_ready(higher), 'REQUEST_GENERATION_CONFLICT')
            self.assertEqual(_frozen(service), before)
            wrong_project = ContextReady(
                PROTOCOL_VERSION, 'r1', first['snapshotId'], 'P2', first['rootHash'],
                first['capturedAt'], first['payload'], 1)
            self.assertEqual(service.apply_context_ready(wrong_project), 'CONTEXT_ERROR')
            self.assertEqual(service.store.context_request('r1')['state'], 'VALID')
            self.assertEqual(_frozen(service), before)
            replay = ContextReady(
                first['protocolVersion'], first['requestId'], first['snapshotId'],
                first['logicalProjectId'], first['rootHash'], first['capturedAt'],
                first['payload'], first['sequence'])
            self.assertEqual(service.apply_context_ready(replay), 'IDEMPOTENT')
            self.assertEqual(_frozen(service), before)
            path = service.store.path
            service.stop()
            service.store.close()
            restarted = SafeBIMBridge(
                BridgeStore(path), GitHubMailbox(QuietHttp()), owner=OWNER, clock=clock)
            restarted.start()
            self.assertEqual(restarted.apply_context_ready(higher), 'REQUEST_GENERATION_CONFLICT')
            self.assertEqual(_frozen(restarted), before)
            second = restarted.context_request({
                'requestId': 'r2', 'logicalProjectId': 'P1',
                'requestedScope': 'selection', 'instanceId': 'AC-A',
            })
            self.assertEqual(second['sequence'], 2)
            self.assertEqual(restarted.store.context_request('r2')['state'], 'VALID')
            self.assertEqual(restarted.store.context_request('r1')['snapshot_id'], first['snapshotId'])
            self.assertEqual(restarted.store.context_request('r1')['response']['sequence'], 1)
            self.assertEqual(restarted.apply_context_ready(higher), 'REQUEST_GENERATION_CONFLICT')
            self.assertEqual(MUTEX_VERIFICATION, 'OFFLINE_CONTRACT_VERIFIED')
            self.assertEqual(GITHUB_BACKEND_STATUS, 'IMPLEMENTED_NOT_LIVE_VERIFIED')
