"""Exercise AC30 campaigns against the actual router and a temporary SQLite ledger."""
from argparse import Namespace
from contextlib import closing
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

import apa_ac30_native as N


WALL = '4a3e34b6-8d28-11e8-9eb6-529269fb1459'
OTHER = 'fe89700a-8d2a-11e8-9eb6-529269fb1459'
GROUP = '72a79740-3137-4bb5-9f83-b6e1ffbe56c1'
RUNTIME = dict(contract='APA_NATIVE_RUNTIME_IDENTITY_V1', nativeModelWrites=0,
               sourceRevision='1' * 40, buildIdentity='2' * 64, sdkMajor=30,
               developerId=826567491, localId=368333322)


def elements(guids):
    return [{'elementId': {'guid': guid}} for guid in guids]


class AC30JobTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name).resolve()
        self.job = root / 'wall-job'
        self.source = root / 'source.pln'
        self.source.write_bytes(b'PLN fixture')
        addon = root / 'fixture.apx'
        addon.write_bytes((RUNTIME['sourceRevision'] + RUNTIME['buildIdentity']).encode())
        candidate = root / 'candidate.json'
        N.write_new_json(candidate, dict(originalSha256=N.sha256(self.source), wallGuid=WALL, groupGuid=GROUP,
                                         observedBaselineHeight=3.2, candidateHeight=3.6))
        N.stage(Namespace(action='stage-wall', job=self.job, source=self.source, source_sha=N.sha256(self.source),
                          addon=addon, addon_sha=N.sha256(addon), candidate=candidate, build=3001,
                          source_revision=RUNTIME['sourceRevision'], build_identity=RUNTIME['buildIdentity']))
        self.project = self.job / 'model' / 'APA-AC30-wall-test.pln'
        self.pid = 12345
        self.mode = False
        self.height = 3.2
        self.fail_after_modify = False
        self.writes = []
        self.runtime = dict(RUNTIME)
        for target, effect in (
            ('apa_ac30_native.open_test_port', lambda path: 19723 if path == self.project else None),
            ('apa_ac30_native.listener', lambda port, **_: dict(pid=self.pid, startedAt=str(self.pid), port=port)),
            ('apa_ac30_native.native_command', self.transport),
            ('apa_ac30_native.DOC.capture_full_model', lambda *_: self.model()),
        ):
            mock = patch(target, side_effect=effect)
            mock.start()
            self.addCleanup(mock.stop)

    def model(self):
        return dict(elements=[
            dict(guid=guid, type='Wall', homeStory=0, bodies=[dict(vertices=[[0, 0, 0], [1, 1, height]])])
            for guid, height in ((WALL, self.height), (OTHER, 2.4))
        ])

    def transport(self, port, command, parameters, **kwargs):
        if command == 'GetProjectInfo':
            return dict(projectPath=str(self.project), projectName=self.project.stem, isUntitled=False, isTeamwork=False)
        if command == 'API.GetProductInfo':
            return dict(version=30, buildNumber=3001)
        if command == 'GetAddOnVersion':
            return {'version': '2.0.0'}
        if command == 'GetAPARuntimeInfoV1':
            return self.runtime
        if command == 'GetStories':
            return {'stories': [dict(index=0, floorId=1, name='First', level=0.)]}
        if command == 'API.IsAddOnCommandAvailable':
            return {'available': True}
        if command == 'GetAllElements':
            return {'elements': elements([WALL, OTHER])}
        if command == 'GetDetailsOfElements':
            return {'detailsOfElements': [dict(type='Wall', id='wall', floorIndex=0, layerIndex=1, drawIndex=1,
                       details=dict(geometryType='Straight', begCoordinate={'x': 0, 'y': 0},
                                    endCoordinate={'x': 1, 'y': 0}, zCoordinate=0,
                                    height=self.height, bottomOffset=0, offset=0))]}
        if command == 'GetGroupsOfElements':
            return {'groupGuids': [{'groupId': {'guid': GROUP}}]}
        if command == 'GetElementsOfGroups':
            return {'elementsOfGroups': [{'elements': elements([WALL, OTHER])}]}
        if command == 'GetSuspendGroupsMode':
            return {'suspendGroups': self.mode}
        if command == 'SetSuspendGroupsMode':
            self.writes.append(command)
            self.mode = parameters['suspendGroups']
            return {'executionResult': {'success': True}}
        if command == 'ModifyWalls':
            self.writes.append(command)
            self.assertTrue(self.mode)
            self.assertEqual(parameters, {'wallsWithDetails': [{'elementId': {'guid': WALL}, 'height': 3.6}]})
            self.height = 3.6
            if self.fail_after_modify:
                raise RuntimeError('connection dropped after native dispatch')
            return {'executionResults': [{'success': True}]}
        if command == 'SaveProject':
            self.writes.append(command)
            self.assertFalse(self.mode)
            self.assertEqual(parameters, {})
            self.project.write_bytes(b'New fixture bytes')
            return {'success': True}
        self.fail(f'Unexpected command {command}')

    def test_exact_wall_session_saves_once_and_checks_geometry_after_reopen(self):
        ready = N.Job(self.job).preflight()
        self.assertEqual(self.writes, [])
        with self.assertRaisesRegex(ValueError, 'EXACT_LOCAL_PREFLIGHT_CONFIRMATION_REQUIRED'):
            N.Job(self.job).execute('bad confirmation')
        result = N.Job(self.job).execute(ready['confirmSha256'])
        self.assertEqual(result['status'], 'SAVED_PENDING_REAL_REOPEN')
        self.assertEqual(self.writes, ['SetSuspendGroupsMode', 'ModifyWalls', 'SetSuspendGroupsMode', 'SaveProject'])
        self.assertEqual(self.source.read_bytes(), b'PLN fixture')
        self.assertEqual(N.Job(self.job).execute(ready['confirmSha256'])['status'], 'ALREADY_APPLIED')
        with self.assertRaises(FileNotFoundError):
            N.Job(self.job).reopened()
        with patch('apa_ac30_native.reservation_owner_exited', return_value=True):
            N.Job(self.job).closed()
        self.pid += 1
        verified = N.Job(self.job).reopened()
        self.assertEqual(verified['status'], 'SAVE_REOPEN_VERIFIED')
        self.assertEqual(verified['operationReadback']['actualHeight'], 3.6)
        self.assertEqual(self.writes.count('SaveProject'), 1)

    def test_unknown_modify_restores_groups_and_cannot_retry_or_save(self):
        ready = N.Job(self.job).preflight()
        self.fail_after_modify = True
        with self.assertRaisesRegex(ValueError, 'WALL_OUTCOME_UNKNOWN_NO_REPLAY'):
            N.Job(self.job).execute(ready['confirmSha256'])
        self.assertFalse(self.mode)
        self.assertEqual(self.project.read_bytes(), self.source.read_bytes())
        with self.assertRaisesRegex(ValueError, 'RECONCILE_WITH_READBACK_NO_REPLAY'):
            N.Job(self.job).execute(ready['confirmSha256'])
        self.assertEqual(self.writes, ['SetSuspendGroupsMode', 'ModifyWalls', 'SetSuspendGroupsMode'])
        with closing(sqlite3.connect(self.job / 'scene-v1-attempts.sqlite3')) as ledger:
            state = ledger.execute("SELECT state FROM scenes WHERE scene_id LIKE '%-Wall'").fetchone()
        self.assertEqual(state, ('PARTIAL_OR_UNKNOWN_OUTCOME',))

    def test_runtime_replacement_blocks_before_any_write(self):
        ready = N.Job(self.job).preflight()
        self.runtime['buildIdentity'] = 'f' * 64
        with self.assertRaisesRegex(ValueError, 'WRONG_LOADED_TAPIR_APX'):
            N.Job(self.job).execute(ready['confirmSha256'])
        self.assertFalse((self.job / 'attempted.json').exists())
        self.assertEqual(self.writes, [])
