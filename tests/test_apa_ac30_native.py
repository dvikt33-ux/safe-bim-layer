"""Exercise AC30 campaigns against the actual router and a temporary SQLite ledger."""
from argparse import Namespace
from contextlib import closing
from copy import deepcopy
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch
from uuid import UUID

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

import apa_ac30_native as N


WALL = '4a3e34b6-8d28-11e8-9eb6-529269fb1459'
OTHER = 'fe89700a-8d2a-11e8-9eb6-529269fb1459'
GROUP = '72a79740-3137-4bb5-9f83-b6e1ffbe56c1'
RUNTIME = dict(contract='APA_NATIVE_RUNTIME_IDENTITY_V1', nativeModelWrites=0,
               sourceRevision='1' * 40, buildIdentity='2' * 64, sdkMajor=30,
               developerId=826567491, localId=368333322)
DESIGNS = ROOT / 'examples' / 'accelerator'
CAPTURE_FULL_MODEL = N.DOC.capture_full_model


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


class AC30ProjectTests(unittest.TestCase):
    """Use real project inputs, catalog, workflow and ledger with a fake transport."""

    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.source = self.root / 'donor.pln'
        self.source.write_bytes(b'Protected donor fixture')
        self.addon = self.root / 'fixture.apx'
        self.addon.write_bytes((RUNTIME['sourceRevision'] + RUNTIME['buildIdentity']).encode())
        self.project = None
        self.pid = 12345
        self.writes = []
        self.items = {}
        self.stories = [dict(index=index, floorId=index + 4, level=level, name=name)
                        for index, level, name in [(3, 0, 'Ground'), (4, 3, 'Upper')]]
        self.recipe = None
        for target, effect in (
            ('apa_ac30_native.open_test_port', lambda path: 19723 if path == self.project else None),
            ('apa_ac30_native.listener', lambda port, **_: dict(pid=self.pid, startedAt=str(self.pid), port=port)),
            ('apa_ac30_native.native_command', self.transport),
            ('apa_ac30_native.DOC.capture_full_model', self.capture_model),
            ('apa_ac30_native.reservation_owner_exited', lambda *_: True),
        ):
            mock = patch(target, side_effect=effect)
            mock.start()
            self.addCleanup(mock.stop)

    def stage(self, filename, variant, prior=None):
        job = self.root / ('update' if prior else variant)
        source = prior.project if prior else self.source
        N.stage(Namespace(action='stage-update' if prior else 'stage-project', job=job, source=source,
                          source_sha=N.sha256(source), addon=self.addon, addon_sha=N.sha256(self.addon),
                          design=DESIGNS / filename, variant=variant, prior_job=prior.path if prior else None,
                          build=3001, source_revision=RUNTIME['sourceRevision'],
                          build_identity=RUNTIME['buildIdentity']))
        prepared = N.Job(job)
        self.project = prepared.project
        self.recipe = prepared.recipe
        return prepared

    def model(self):
        return dict(stories=[{'index': s['index'], 'elevation': s['level']} for s in self.stories],
                    elements=[row['element'] for row in self.items.values()])

    def capture_model(self, api, guids, **options):
        return self.model() if self.items else CAPTURE_FULL_MODEL(api, guids, **options)

    def registered_read(self, command):
        return {
            'GetProjectInfo': dict(projectPath=str(self.project), projectName=self.project.stem,
                                   isUntitled=False, isTeamwork=False),
            'API.GetProductInfo': dict(version=30, buildNumber=3001),
            'GetAddOnVersion': {'version': '2.0.0'},
            'GetAPARuntimeInfoV1': RUNTIME,
            'GetStories': {'stories': self.stories},
            'API.IsAddOnCommandAvailable': {'available': True},
            'GetAttributesByType': {'attributes': [
                {'name': self.recipe['slabMaterial'], 'attributeId': {'guid': WALL}},
            ]},
            'GetFavoritesByType': {'favorites': [p['operation']['params']['stairsData'][0]['favoriteName']
                                                for p in self.recipe['stairPlans'].values()]},
        }.get(command)

    def transport(self, port, command, parameters, **kwargs):
        if command == 'GetAllElements':
            inventory = {'elements': elements(self.items)}
            if parameters.get('databases'):
                inventory['executionResultForDatabases'] = [{'success': True}]
            return inventory
        if command == 'GetModelDumpV1':
            return dict(nativeBodySlots=0, regenerated3D=True, coordinateSystem='ABSOLUTE_PROJECT_XYZ',
                        deletedBodySlots=[], elements=[], materials=[], bodies=[])
        if command == 'GetNavigatorItemTree':
            return {'navigatorItemTree': {'type': 'StoryItem', 'navigatorItemId': {'guid': OTHER}}}
        if command == 'GetDatabaseIdFromNavigatorItemId':
            return {'databases': [{'databaseId': {'guid': GROUP}}]}
        read = self.registered_read(command)
        if read is not None:
            return read
        if command == 'Get3DBoundingBoxes':
            # The test's read-only admission starts with an empty fixture.
            self.assertEqual(parameters['elements'], [])
            return {'boundingBoxes3D': []}
        if command == 'GetDetailsOfElements':
            return {'detailsOfElements': [self.items[row['elementId']['guid']]['details']
                                          for row in parameters['elements']]}
        self.writes.append(command)
        if command == 'SaveProject':
            self.assertEqual(parameters, {})
            self.project.write_bytes(('Saved fixture ' + str(len(self.writes))).encode())
            return {'success': True}
        if command == 'ModifyWindows':
            edit, = parameters['windowsWithDetails']
            item = self.items[edit['elementId']['guid']]
            item['details']['details']['width'] = edit['width']
            item['element']['bodies'][0]['vertices'][1][0] = edit['width']
            host = item['details']['details']['ownerElementId']['guid']
            self.items[host]['element']['bodies'][0]['vertices'][1][0] = edit['width']
            return {'executionResults': [{'success': True}]}
        if command in {'CreateWalls', 'CreateSlabs', 'CreateDoors', 'CreateWindows'}:
            guid = str(UUID(int=len(self.items) + 1))
            params, = next(iter(parameters.values()))
            details = deepcopy(params)
            floor = details.get('floorIndex')
            if command == 'CreateWalls':
                level = next(row['level'] for row in self.stories if row['index'] == floor)
                details.update(geometryType='Straight', begThickness=params['thickness'],
                               endThickness=params['thickness'], zCoordinate=level + params['zCoordinate'])
            elif command == 'CreateSlabs':
                level = next(row['level'] for row in self.stories if row['index'] == floor)
                details.update(zCoordinate=params['level'], level=params['level'] - level,
                               polygonOutline=params['polygonCoordinates'])
            else:
                host = self.items[params['ownerWallId']['guid']]
                self.assertEqual(host['element']['type'], 'Wall')
                floor = host['element']['homeStory']
                details.update(ownerElementId=params['ownerWallId'], ownerElementType='Wall')
            kind = command[6:-1]
            self.items[guid] = dict(
                details=dict(type=kind, floorIndex=floor, details=details),
                element=dict(guid=guid, type=kind, homeStory=floor,
                             bodies=[dict(vertices=[[0, 0, 0], [1, 1, 1]])]))
            return {'elements': elements([guid])}
        self.fail(f'Unexpected command {command}')

    def save_reopen(self, job, ready):
        saved = N.Job(job.path).execute(ready['confirmSha256'])
        self.assertEqual(saved['status'], 'SAVED_PENDING_REAL_REOPEN')
        N.Job(job.path).closed()
        self.pid += 1
        result = N.Job(job.path).reopened()
        self.assertEqual(result['status'], 'SAVE_REOPEN_VERIFIED')
        return result

    def test_r06_graph_write_window_edit_and_two_story_documentation(self):
        job = self.stage('r06-two-storey-design.json', 'two-storeys')
        ready = job.preflight()
        self.assertEqual(self.writes, [])
        self.assertEqual(len(ready['facts']['workflow']['executionOrder']), 17)
        self.assertEqual(ready['facts']['storyIndices'], [3, 4])
        self.assertEqual(ready['facts']['verifiedEmptyModel']['nativeElementCount'], 0)
        base = self.save_reopen(job, ready)
        self.assertEqual(len(base['operationReadback']['operationGuids']), 17)
        self.assertEqual(N.Job(job.path).execute(ready['confirmSha256'])['status'], 'ALREADY_APPLIED')
        self.assertEqual(len(self.writes), 18)
        self.assertEqual(self.writes.count('SaveProject'), 1)
        docs = N.Job(job.path).documentation(self.root / 'documentation')
        self.assertEqual(docs['stories'], [3, 4])
        self.assertEqual(docs['publisherPdf'], 'NOT_TESTED')

        design = N.read_json(DESIGNS / 'r06-two-storey-design.json')
        design['brief'].update(mode='CONTINUE_EXISTING_PROJECT', targetProjectPath=str(job.project))
        opening = next(row for row in design['variants'][0]['layout']['passages'] if row['id'] == 'living-window')
        opening['width'] = 1.6
        updated = self.root / 'changed-design.json'
        N.write_new_json(updated, design)
        update = self.stage(updated, 'two-storeys', prior=N.Job(job.path))
        update_ready = update.preflight()
        after = self.save_reopen(update, update_ready)
        self.assertEqual(self.writes[18:], ['ModifyWindows', 'SaveProject'])
        self.assertEqual(after['operationReadback']['operationGuids'], base['operationReadback']['operationGuids'])
        self.assertEqual(after['documentationChange']['changedNativeModelGuids'], update.recipe['affectedGuids'])
        new_docs = N.Job(update.path).documentation(self.root / 'updated-documentation')
        self.assertNotEqual(docs['modelVersion'], new_docs['modelVersion'])
        self.assertEqual(N.sha256(job.project), base['savedSha256'])
        self.assertEqual(self.source.read_bytes(), b'Protected donor fixture')

    def test_r07_uses_the_same_preflight_with_stair_dependencies(self):
        job = self.stage('r07-two-storey-house.json', 'house-a')
        ready = job.preflight()
        facts = ready['facts']
        stair = next(row for row in facts['graph']['operations'] if row['command'] == 'CreateStairs')
        self.assertEqual(stair['params']['stairsData'][0]['floorIndex'], 3)
        self.assertEqual(facts['workflow']['dependencies'][stair['id']], stair['after'])
        self.assertEqual(len(facts['workflow']['executionOrder']), 22)
        self.assertEqual(ready['modelWrites'], 0)
        self.assertEqual(self.writes, [])
        self.assertFalse((job.path / 'attempted.json').exists())

    def test_approved_empty_floor_is_rechecked_before_first_create(self):
        job = self.stage('r06-two-storey-design.json', 'two-storeys')
        ready = job.preflight()

        def capture_with_late_body(api, guids, verify_empty=None):
            if verify_empty is N.PROJECT.verify_empty_model:
                return self.capture_model(api, guids, verify_empty=verify_empty)
            # The later dump no longer qualifies as empty, while the default
            # element listing and its signatures remain unchanged.
            return self.model()

        with patch('apa_ac30_native.DOC.capture_full_model', side_effect=capture_with_late_body):
            with self.assertRaisesRegex(ValueError, 'AC30_APPROVED_EMPTY_FLOOR_PLAN_DRIFT'):
                N.Job(job.path).execute(ready['confirmSha256'])
        self.assertEqual(self.writes, [])


class AC30ZeroBodySnapshotTests(unittest.TestCase):
    def setUp(self):
        self.part = '6a08ba99-6c84-4b6e-aa5a-c0caedc741a6'
        self.parent = '9fabbd06-d663-4519-809e-76e90e5a6ba5'
        self.full_part = '{' + self.part + '}-{f7b4967a-9e62-4392-b8dd-e93f566630f7}'
        self.root = WALL
        self.marker = OTHER
        self.database = {'databaseId': {'guid': GROUP}}
        self.complete_guids = [self.root, self.marker]
        self.database_success = True
        self.has_3d_script = False
        self.raw = dict(nativeBodySlots=0, regenerated3D=True, coordinateSystem='ABSOLUTE_PROJECT_XYZ',
                        deletedBodySlots=[], elements=[
                            dict(guid=self.root, type='Elevation', homeStory=0),
                            dict(guid=self.marker, type='Object', homeStory=0, relationships={'hostGuid': GROUP}),
                        ], materials=[], bodies=[])

    def api(self, command, parameters):
        if command == 'GetModelDumpV1':
            return deepcopy(self.raw)
        if command == 'GetNavigatorItemTree':
            return {'navigatorItemTree': {'type': 'StoryItem', 'navigatorItemId': {'guid': WALL}}}
        if command == 'GetDatabaseIdFromNavigatorItemId':
            return {'databases': [self.database]}
        if command == 'GetAllElements':
            self.assertEqual(parameters['databases'], [self.database])
            include = parameters.get('filters') == ['IncludeSubElemObjects']
            return dict(elements=elements(self.complete_guids if include else [self.root]),
                        executionResultForDatabases=[{'success': self.database_success}])
        if command == 'GetDetailsOfElements':
            details = {
                self.root: dict(type='Elevation', floorIndex=0, details={}),
                self.marker: dict(type='Object', floorIndex=0,
                    details=dict(libPart=dict(name='Built-in Elevation Marker', ownUnID={'guid': self.part},
                                              parentUnID={'guid': self.parent}),
                                 ownerElementId={'guid': GROUP})),
            }
            return {'detailsOfElements': [details[row['elementId']['guid']] for row in parameters['elements']]}
        if command == 'GetLibraryPartScripts':
            self.assertEqual(parameters, {'libraryParts': elements([self.marker]), 'scripts': ['3d']})
            return {'libraryParts': [{'unID': self.full_part, 'scripts': {'3d': {'present': self.has_3d_script}}}]}
        self.fail(f'Unexpected command {command}')

    def snapshot(self):
        return CAPTURE_FULL_MODEL(self.api, [self.root], verify_empty=N.PROJECT.verify_empty_model)

    def test_zero_brep_is_allowed_only_with_a_verified_floor_inventory_and_marker(self):
        with self.assertRaisesRegex(ValueError, 'zero bodies'):
            CAPTURE_FULL_MODEL(self.api, [self.root])
        snapshot = self.snapshot()
        proof = snapshot['verifiedEmptyModel']
        self.assertEqual(proof['nativeElementCount'], 2)
        self.assertEqual(proof['nonSpatialRootGuids'], [self.root])
        self.assertEqual(set(proof['markerSignatures']), {self.marker})
        N.PROJECT.check_template_markers(snapshot, proof['markerSignatures'])
        snapshot['elements'][1]['relationships']['ownerGuid'] = self.root
        with self.assertRaisesRegex(ValueError, 'AC30_TEMPLATE_MARKER_READBACK_DRIFT'):
            N.PROJECT.check_template_markers(snapshot, proof['markerSignatures'])

    def test_zero_brep_cannot_hide_objects_omitted_from_the_current_view(self):
        self.complete_guids.append(str(UUID(int=91)))
        with self.assertRaisesRegex(ValueError, 'AC30_EMPTY_FLOOR_INVENTORY_MISMATCH'):
            self.snapshot()

    def test_zero_brep_rejects_unproved_database_inventory(self):
        self.database_success = False
        with self.assertRaisesRegex(ValueError, 'NATIVE_DATABASE_INVENTORY_UNVERIFIED'):
            self.snapshot()

    def test_marker_name_alone_cannot_qualify_a_library_object(self):
        self.part = str(UUID(int=92))
        with self.assertRaisesRegex(ValueError, 'AC30_EMPTY_UNVERIFIED_LIBRARY_OBJECT'):
            self.snapshot()

    def test_marker_with_a_different_revision_or_a_3d_script_is_rejected(self):
        self.has_3d_script = True
        with self.assertRaisesRegex(ValueError, 'AC30_EMPTY_MARKER_REVISION_OR_3D_SCRIPT_UNVERIFIED'):
            self.snapshot()
        self.has_3d_script = False
        self.full_part = '{' + self.part + '}-{' + str(UUID(int=93)) + '}'
        with self.assertRaisesRegex(ValueError, 'AC30_EMPTY_MARKER_REVISION_OR_3D_SCRIPT_UNVERIFIED'):
            self.snapshot()
