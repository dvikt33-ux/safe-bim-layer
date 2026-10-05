"""Offline host integration tests for the chat Wall write MVP."""
from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from sync_bridge.host import BridgeHost, HostConfig
from sync_bridge.security import PeerIdentity
from sync_bridge.wall_write import RECIPE


SOURCE_GUID = '5D743058-EAEF-4DB9-BB12-00F6D62E0813'
CREATED_GUID = 'CCA6E865-2393-4DDA-B75B-223555F196B2'
MATERIAL_GUID = '922C639B-9875-48DF-A3FC-E0A8AC5F2839'


class FakePipe:
    def __init__(self):
        self.handle = 1

    def close(self):
        self.handle = None


def source_row(begin=None, end=None):
    return {
        'type': 'Wall',
        'floorIndex': 0,
        'details': {
            'geometryType': 'Straight',
            'arcAngle': 0,
            'structureType': 'Basic',
            'zCoordinate': 0,
            'begCoordinate': begin or {'x': 60.0, 'y': 0.0},
            'endCoordinate': end or {'x': 60.0, 'y': 30.0},
            'height': 12.0,
            'offset': 0.0,
            'begThickness': 0.25,
            'endThickness': 0.25,
            'buildingMaterialId': {'guid': MATERIAL_GUID},
            'referenceLineLocation': 'Center',
        },
    }


def created_row():
    return source_row(
        begin={'x': 60.0, 'y': 30.0},
        end={'x': 60.0, 'y': 30.25})


def job():
    return {
        'recipe': RECIPE,
        'instanceId': 'archicad-default',
        'logicalProjectId': 'project-a',
        'sourceGuid': SOURCE_GUID,
        'sourceEndpoint': 'end',
        'lengthMeters': 0.25,
        'expectedSource': {
            'floorIndex': 0,
            'begCoordinate': {'x': 60.0, 'y': 0.0},
            'endCoordinate': {'x': 60.0, 'y': 30.0},
            'zCoordinate': 0.0,
            'height': 12.0,
            'begThickness': 0.25,
            'endThickness': 0.25,
            'offset': 0.0,
            'buildingMaterialGuid': MATERIAL_GUID,
        },
    }


class FakeWriteTransport:
    def __init__(self):
        self.writes = []

    def binding(self):
        return {
            'instanceId': 'archicad-default',
            'logicalProjectId': 'project-a',
            'projectName': 'Offline',
            'applicationVersion': '29',
        }

    def call(self, command, params):
        if command == 'GetProjectInfo':
            return {
                'projectName': 'Offline',
                'projectPath': r'C:\Offline.pln',
                'isUntitled': False,
                'isTeamwork': False,
            }
        if command == 'GetDetailsOfElements':
            if len(params['elements']) == 1:
                return {'detailsOfElements': [copy.deepcopy(source_row())]}
            return {'detailsOfElements': [
                copy.deepcopy(source_row()), copy.deepcopy(created_row())]}
        raise AssertionError(command)

    def write_call(self, command, params):
        self.writes.append((command, copy.deepcopy(params)))
        return {'elements': [{'elementId': {'guid': CREATED_GUID}}]}


def make_host(root: Path, transport):
    return BridgeHost(
        HostConfig(data_dir=root, db_path=root / 'bridge.sqlite3'),
        identity=PeerIdentity('S-1-5-21-wall-write-test', '7'),
        token_provider=lambda: None,
        pipe_factory=lambda sid, session: FakePipe(),
        transport=transport,
    )


class WallWriteHostTests(unittest.TestCase):
    def test_queued_job_is_claimed_once_and_result_is_durable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            transport = FakeWriteTransport()
            host = make_host(root, transport)
            try:
                host.start()
                message = {
                    'messageId': 'wall-job-1',
                    'kind': 'JOB',
                    'body': job(),
                }
                host.store.put_message(
                    'wall-job-1', 'JOB', 't', message, 'ACCEPTED', 'inbox')
                host.store.put_remote_job(
                    'job-wall-job-1', None, job(), 'QUEUED', 'wall-job-1', 't')

                first = host._execute_one_write_job()
                second = host._execute_one_write_job()

                self.assertEqual(first[0]['result']['status'], 'PASS')
                self.assertEqual(second, [])
                self.assertEqual(len(transport.writes), 1)
                state = next(
                    item for item in host.store.jobs()
                    if item['job_id'] == 'job-wall-job-1')
                self.assertEqual(state['state'], 'COMPLETE')
                stored = host.store.result('job-wall-job-1')
                self.assertEqual(stored['result']['createdGuid'], CREATED_GUID)
                self.assertEqual(len(host.store.pending_outbox()), 1)
            finally:
                host.close()

    def test_non_job_remote_kind_never_reaches_write_executor(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            transport = FakeWriteTransport()
            host = make_host(root, transport)
            try:
                host.start()
                host.store.put_message(
                    'not-job', 'PING', 't',
                    {'messageId': 'not-job', 'kind': 'PING', 'body': job()},
                    'ACCEPTED', 'inbox')
                host.store.put_remote_job(
                    'job-not-job', None, job(), 'QUEUED', 'not-job', 't')
                result = host._execute_one_write_job()[0]['result']
                self.assertEqual(result['status'], 'BLOCKED')
                self.assertEqual(result['stage'], 'REMOTE_KIND')
                self.assertEqual(transport.writes, [])
            finally:
                host.close()

    def test_running_job_after_restart_becomes_unknown_without_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first_transport = FakeWriteTransport()
            first = make_host(root, first_transport)
            first.start()
            first.store.put_message(
                'interrupted', 'JOB', 't',
                {'messageId': 'interrupted', 'kind': 'JOB', 'body': job()},
                'ACCEPTED', 'inbox')
            first.store.put_remote_job(
                'job-interrupted', None, job(), 'QUEUED', 'interrupted', 't')
            self.assertTrue(first.store.claim_job('job-interrupted'))
            first.close()

            second_transport = FakeWriteTransport()
            second = make_host(root, second_transport)
            try:
                second.start()
                recovered = second.store.result('job-interrupted')
                self.assertEqual(
                    recovered['result']['status'], 'UNKNOWN_OUTCOME')
                self.assertFalse(
                    recovered['result']['automaticRetry'])
                self.assertEqual(second_transport.writes, [])
                state = next(
                    item for item in second.store.jobs()
                    if item['job_id'] == 'job-interrupted')
                self.assertEqual(state['state'], 'COMPLETE')
            finally:
                second.close()


if __name__ == '__main__':
    unittest.main()
