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
WALL_LAYER = '43f067bd-8bb4-4e06-a6a8-bb27c3cd2589'


def elements(guids):
    return [{'elementId': {'guid': guid}} for guid in guids]


def wall_body(bounds):
    xmin, ymin, zmin, xmax, ymax, zmax = bounds
    vertices = [[x, y, z] for z in (zmin, zmax)
                for x, y in ((xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax))]
    faces = [[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4],
             [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]
    return dict(vertices=vertices, faces=[dict(contours=[face]) for face in faces])


class LayoutDetailsReadbackTests(unittest.TestCase):
    def test_live_nested_element_id_matches_same_guid_in_direct_format(self):
        def api_for(wrapped):
            def reply(command, arguments):
                self.assertEqual(command, 'GetDetailsOfElements')
                self.assertEqual(arguments['elements'], elements([WALL]))
                self.assertIn('elementId', arguments['fields'])
                element_id = {'guid': WALL.upper()}
                if wrapped:
                    element_id = {'elementId': element_id}
                return {'detailsOfElements': [{'elementId': element_id, 'type': 'Wall',
                                               'floorIndex': 3, 'details': {'height': 2.772}}]}
            return reply

        direct = N.PROJECT.retained_details_digest(api_for(False), [WALL])
        self.assertEqual(N.PROJECT.retained_details_digest(api_for(True), [WALL]), direct)

    def test_retained_details_rejects_foreign_ambiguous_or_missing_guid(self):
        for identity in (
            None, {'guid': OTHER}, {'elementId': {'guid': OTHER}}, {'elementId': {'guid': 123}},
            {'guid': WALL, 'elementId': {'guid': OTHER}}, {'other': {'guid': WALL}},
        ):
            with self.subTest(identity=identity):
                def reply(*_):
                    return {'detailsOfElements': [{'elementId': identity, 'type': 'Wall'}]}

                with self.assertRaisesRegex(ValueError, 'LAYOUT_RETAINED_DETAILS_IDENTITY_DRIFT'):
                    N.PROJECT.editable_details(reply, [WALL])


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
        self.zone_area_delta = 0
        self.partial_wall_batch = False
        self.wall_layer_group = 1
        self.zone_categories = [
            {'name': 'Жилье и Отдых', 'attributeId': {'guid': GROUP.upper()}},
            {'name': 'Транзитные Помещения', 'attributeId': {'guid': OTHER.upper()}},
        ]
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
        if command == 'GetLayerOfElementDefaults':
            return {'layersOfElementDefaults': [dict(elementType='Wall', layerId={'guid': WALL_LAYER}, layerName='Стены')]}
        if command == 'GetLayers':
            return {'layers': [dict(attributeId={'guid': WALL_LAYER}, index=33, name='Стены',
                                    intersectionGroupNr=self.wall_layer_group, isHidden=False, isLocked=False)]}
        if command == 'GetBuildingMaterials':
            return {'buildingMaterials': [dict(attributeId=row['attributeId'], index=i, name='Кирпич',
                                               connPriority=600) for i, row in enumerate(parameters['attributeIds'], 1)]}
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
        if command == 'GetAttributesByType' and self.recipe['kind'] == 'layout':
            if parameters['attributeType'] == 'ZoneCategory':
                rows = self.zone_categories
            else:
                rows = [{'name': name, 'attributeId': {'guid': WALL}}
                        for name in sorted(set(self.recipe['wallMaterials'].values()))]
            return {'attributes': [dict(row, index=i, folderPath=[], modificationTime=1)
                                   for i, row in enumerate(rows, 1)]}
        read = self.registered_read(command)
        if read is not None:
            return read
        if command == 'Get3DBoundingBoxes':
            # The test's read-only admission starts with an empty fixture.
            self.assertEqual(parameters['elements'], [])
            return {'boundingBoxes3D': []}
        if command == 'GetDetailsOfElements':
            rows = []
            for element in parameters['elements']:
                guid = element['elementId']['guid']
                fields = dict(self.items[guid]['details'])
                if 'elementId' in parameters.get('fields', ()):
                    fields['elementId'] = {'elementId': {'guid': guid.upper()}}
                rows.append(fields)
            return {'detailsOfElements': rows}
        if command == 'GetQuantitiesOfElements':
            quantities = []
            for element in parameters['elements']:
                detail = self.items[element['elementId']['guid']]['details']['details']
                polygon = detail['polygonOutline']
                width = polygon[1]['x'] - polygon[0]['x']
                depth = polygon[2]['y'] - polygon[1]['y']
                area = width * depth + self.zone_area_delta
                data = dict.fromkeys(('netArea', 'perimeter', 'netPerimeter', 'volume', 'height',
                                      'wallsPerimeter', 'wallsSurface', 'doorsSurface', 'windowsSurface'), 0)
                data.update(area=area, calculatedArea=area, netArea=area)
                quantities.append(dict(type='Zone', quantities=data, composites=[]))
            return {'quantitiesOfElements': quantities}
        if command == 'CreateWalls' and len(parameters['wallsData']) > 1:
            start = len(self.writes)
            result = []
            for row in parameters['wallsData']:
                result.extend(self.transport(port, command, {'wallsData': [row]})['elements'])
            self.writes[start:] = [command]
            return {'elements': result[:-1] if self.partial_wall_batch else result}
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
        if command == 'CreateZones':
            guid = str(UUID(int=len(self.items) + 1))
            row, = parameters['zonesData']
            floor = row['floorIndex']
            level = next(story['level'] for story in self.stories if story['index'] == floor)
            details = {key: row[key] for key in ('name', 'numberStr', 'categoryAttributeId', 'height',
                                                'bottomOffset', 'stampPosition')}
            details.update(isManual=True, polygonOutline=row['geometry']['polygonCoordinates'],
                           relativeTopStory=0, zCoordinate=level)
            self.items[guid] = dict(details=dict(type='Zone', floorIndex=floor, details=details),
                                    element=dict(guid=guid, type='Zone', homeStory=floor, bodies=[]))
            return {'elements': elements([guid])}
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
                details.pop('ownerWallId')
            body = dict(vertices=[[0, 0, 0], [1, 1, 1]])
            layer = {}
            if command == 'CreateWalls' and self.recipe['kind'] == 'layout':
                start, end = params['begCoordinate'], params['endCoordinate']
                side = params['thickness'] / 2
                xmin, ymin = (start['x'] - side, start['y']) if start['x'] == end['x'] else (start['x'], start['y'] - side)
                xmax, ymax = (end['x'] + side, end['y']) if start['x'] == end['x'] else (end['x'], end['y'] + side)
                if 'wallJunctions' in self.recipe:
                    if start['x'] == end['x']:
                        ymin += params['thickness']
                        ymax -= params['thickness']
                    details['junctionSequence'] = 5000
                    layer['layerIndex'] = params['layerIndex']
                body = wall_body((xmin, ymin, details['zCoordinate'], xmax, ymax,
                                  details['zCoordinate'] + params['height']))
            kind = command[6:-1]
            self.items[guid] = dict(
                details=dict(type=kind, floorIndex=floor, details=details, **layer),
                element=dict(guid=guid, type=kind, homeStory=floor,
                             bodies=[body]))
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

    def test_verified_copy_of_saved_r06_reopens_and_exports_without_replay(self):
        job = self.stage('r06-two-storey-design.json', 'two-storeys')
        ready = job.preflight()
        saved = N.Job(job.path).execute(ready['confirmSha256'])
        job.project.write_bytes(b'Drifted copy after the verified native save')
        original_files = {
            str(path): N.sha256(path)
            for path in [job.project, job.source, *(job.path / name for name in (
                'job.json', 'preflight.json', 'attempted.json', 'saved.json',
                'guarded-save.snapshot', 'scene-v1-attempts.sqlite3'))]
        }
        recovery = self.root / 'reopen-saved-r06'
        staged = N.Job(job.path).stage_reopen_copy(recovery)
        recovery_project = recovery / job.project.name
        self.assertEqual(N.sha256(recovery_project), saved['savedSha256'])
        self.assertEqual(staged['verificationProject'], str(recovery_project))
        with self.assertRaisesRegex(ValueError, 'EXACT_TEST_PLN_NOT_OPEN'):
            N.Job(job.path).verify_reopen_copy(recovery)
        self.project = recovery_project
        self.pid += 1
        verified = N.Job(job.path).verify_reopen_copy(recovery)
        self.assertEqual(verified['status'], 'SAVE_REOPEN_COPY_VERIFIED')
        self.assertEqual(verified['verificationNativeWrites'], 0)
        self.assertEqual(verified['operationReadback'], saved['operationReadback'])
        from apa_integrated_services import document_reopened_job

        report = document_reopened_job(job.path, self.root / 'bim-docs', reopen_copy=recovery)
        self.assertEqual(report['stories'], [3, 4])
        self.assertEqual(report['elements'], 17)
        self.assertEqual(report['verificationProject'], str(recovery_project))
        self.assertEqual(report['publisherPdf'], 'NOT_TESTED')
        self.assertEqual(len(self.writes), 18)
        self.assertFalse((job.path / 'reopened.json').exists())
        self.assertEqual({path: N.sha256(path) for path in original_files}, original_files)

        design = N.read_json(DESIGNS / 'r06-two-storey-design.json')
        design['brief'].update(mode='CONTINUE_EXISTING_PROJECT', targetProjectPath=str(recovery_project))
        window = next(row for row in design['variants'][0]['layout']['passages'] if row['id'] == 'living-window')
        window['width'] = 1.6
        updated = self.root / 'verified-copy-window-design.json'
        N.write_new_json(updated, design)
        staged_update = N.stage(Namespace(
            action='stage-update', job=self.root / 'update-from-copy',
            source=recovery_project, source_sha=saved['savedSha256'],
            addon=self.addon, addon_sha=N.sha256(self.addon), design=updated, variant='two-storeys',
            prior_job=job.path, prior_reopen_copy=recovery, build=3001,
            source_revision=RUNTIME['sourceRevision'], build_identity=RUNTIME['buildIdentity']))
        update = N.Job(Path(staged_update['job']))
        self.assertEqual(N.sha256(update.project), saved['savedSha256'])
        self.assertEqual(update.recipe['sourceReopenReceiptSha256'], N.sha256(recovery / 'reopened.json'))
        self.assertEqual(update.recipe['change']['parameters']['windowsWithDetails'][0]['width'], 1.6)
        self.assertEqual(len(self.writes), 18)

        recovery_project.write_bytes(b'No longer the verified saved model')
        with self.assertRaisesRegex(ValueError, 'PROTECTED_FILE_CHANGED'):
            document_reopened_job(job.path, self.root / 'invalid-docs', reopen_copy=recovery)
        self.assertFalse((self.root / 'invalid-docs').exists())

    def test_recovery_rejects_unsealed_save_before_creating_a_copy(self):
        job = self.stage('r06-two-storey-design.json', 'two-storeys')
        ready = job.preflight()
        N.Job(job.path).execute(ready['confirmSha256'])
        (job.path / 'guarded-save.snapshot').write_bytes(b'Changed after capture')
        recovery = self.root / 'invalid-copy'
        with self.assertRaisesRegex(ValueError, 'PERSISTENCE_EVIDENCE_DRIFT'):
            N.Job(job.path).stage_reopen_copy(recovery)
        self.assertFalse(recovery.exists())
        self.assertEqual(self.writes.count('SaveProject'), 1)

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

    def stage_layout(self):
        from tests.test_apa_room_layout import sample

        intent = self.root / 'rooms.json'
        N.write_new_json(intent, sample())
        path = self.root / 'layout-mcp-rooms'
        record = N.stage(Namespace(action='stage-layout', job=path, source=self.source,
                                   source_sha=N.sha256(self.source), addon=self.addon,
                                   addon_sha=N.sha256(self.addon), design=intent, build=3001,
                                   source_revision=RUNTIME['sourceRevision'], build_identity=RUNTIME['buildIdentity']))
        job = N.Job(path)
        self.project = job.project
        self.recipe = job.recipe
        self.assertEqual(record['nativeWrites'], 0)
        return job

    def test_layout_binds_distinct_native_categories_from_room_names(self):
        job = self.stage_layout()
        attributes = job.layout_attributes()
        self.assertEqual(attributes['status'], 'LAYOUT_NATIVE_ATTRIBUTES_READ')
        self.assertEqual(attributes['zoneCategorySelection']['mode'], 'BY_ROOM_PURPOSE')
        self.assertEqual(attributes['modelWrites'], 0)
        mapped = attributes['zoneCategorySelection']['rooms']
        self.assertEqual(mapped['hall']['name'], 'Транзитные Помещения')
        self.assertEqual(mapped['living']['name'], 'Жилье и Отдых')
        result = job.preflight()
        self.assertEqual(result['facts']['zoneCategories'], mapped)
        bound = {s['id']: s['params']['zonesData'][0]['categoryAttributeId']['guid']
                 for s in result['facts']['graph']['operations'] if s['command'] == 'CreateZones'}
        self.assertEqual(bound, {'exp-zone-hall': OTHER, 'exp-zone-living': GROUP})
        self.assertEqual(result['modelWrites'], 0)
        self.assertEqual(self.writes, [])

    def test_layout_blocks_missing_and_ambiguous_native_zone_category(self):
        job = self.stage_layout()
        transit = self.zone_categories.pop()
        for reason, extra_rows in (
            ('LAYOUT_ZONE_CATEGORY_MISSING:hall', []),
            ('LAYOUT_ZONE_CATEGORY_AMBIGUOUS:hall', [
                transit, {'name': 'транзитные помещения', 'attributeId': {'guid': WALL}}]),
        ):
            with self.subTest(reason=reason):
                self.zone_categories[1:] = extra_rows
                selection = job.layout_attributes()['zoneCategorySelection']
                self.assertEqual(selection['status'], 'BLOCKED')
                self.assertIn(reason, selection['reason'])
                with self.assertRaisesRegex(ValueError, reason):
                    job.preflight()
                self.assertFalse((job.path / 'preflight.json').exists())
                self.assertEqual(self.writes, [])

    def test_layout_experiment_reopen_and_manual_inclusion(self):
        job = self.stage_layout()
        ready = job.preflight()
        self.assertEqual(set(ready['facts']['spatialScan']), {'experiment', 'acceptance'})
        strategy = ready['facts']['wallStrategy']
        self.assertEqual(strategy['selectedStrategyId'], 'native_create_walls_batch')
        self.assertEqual(strategy['optimumStatus'], 'OPTIMUM_NOT_PROVEN')
        self.assertEqual(strategy['candidates'][0]['plannedNativeCalls'], 5)
        self.assertEqual(strategy['candidates'][1]['plannedNativeCalls'], 1)
        self.assertEqual(self.writes, [])
        reopened = self.save_reopen(job, ready)
        proof = reopened['operationReadback']
        first = proof['operationGuids']
        self.assertEqual(len(first), 9)
        self.assertEqual(len(set(first.values())), 9)
        self.assertTrue(all(key.startswith('exp-') for key in first))
        self.assertEqual(self.writes.count('CreateWalls'), 1)
        batch, = [row for row in proof['executionTrace'] if row['command'] == 'CreateWalls']
        self.assertEqual(batch['bulkMetrics']['itemCount'], 5)
        self.assertEqual(batch['bulkMetrics']['nativeSceneWriterCalls'], 1)
        self.assertEqual(self.items[first['exp-door-entry']]['details']['details']['ownerElementId']['guid'],
                         first['exp-wall-bottom'])
        self.assertEqual(self.items[first['exp-door-passage']]['details']['details']['ownerElementId']['guid'],
                         first['exp-wall-part-1'])
        self.assertEqual(self.writes.count('CreateZones'), 2)
        self.assertEqual([j['kind'] for j in reopened['wallSystem']['joints']], ['L'] * 4 + ['T'] * 2)
        self.assertAlmostEqual(reopened['roomReadback']['exp-zone-hall']['measuredAreaM2'], 8.3916)
        self.assertEqual(self.writes.count('SaveProject'), 1)
        self.assertEqual(self.source.read_bytes(), b'Protected donor fixture')
        with self.assertRaisesRegex(ValueError, 'UNEXPECTED_GUID_COUNT'):
            N.Job(job.path).verify_inclusion()

        # Inject the result of a user copy via the simulated transport. No
        # acceptance-area operation is dispatched by the real APA workflow.
        recipe = dict(job.recipe, graph=job.recipe['inclusionGraph'],
                      wallMaterials={key.replace('exp-', 'accept-', 1): value
                                     for key, value in job.recipe['wallMaterials'].items()})
        graph = N.PROJECT.bind_design(recipe, self.stories,
            lambda command, args: self.transport(19723, command, args), job.router)['graph']
        new = {}
        for step in graph['operations']:
            params = N.RUN.resolve_params(step, new)
            reply = self.transport(19723, step['command'], params)
            new[step['id']] = dict(guid=N.RUN.created_guid(reply).lower(),
                                   kind=N.APA.SCENE.GRAPH.CREATES[step['command']])
        before = list(self.writes)
        verified = N.Job(job.path).verify_inclusion()
        self.assertEqual(verified['addedGuidCount'], 9)
        self.assertEqual(verified['wallSystem']['status'], 'WALL_JUNCTION_BREP_CHECK_PASS')
        self.assertEqual(verified['retainedGuidCount'], 9)
        self.assertEqual(verified['operationGuids'], {key: row['guid'] for key, row in new.items()})
        self.assertAlmostEqual(verified['roomReadback']['accept-zone-hall']['measuredAreaM2'], 8.3916)
        self.assertEqual(self.writes, before)
        copied = self.items[new['accept-door-entry']['guid']]['details']
        copied['layerIndex'] = 99
        with self.assertRaisesRegex(ValueError, 'EDITABLE_PARAMETERS_DRIFT:accept-door-entry'):
            N.Job(job.path).verify_inclusion()
        del copied['layerIndex']
        self.items[first['exp-zone-hall']]['details']['details']['name'] = 'Изменённое исходное помещение'
        with self.assertRaisesRegex(ValueError, 'CHANGED_EXISTING_PARAMETERS'):
            N.Job(job.path).verify_inclusion()

    def test_layout_blocks_acceptance_area_on_failed_experiment(self):
        job = self.stage_layout()
        ready = job.preflight()
        self.zone_area_delta = .4
        with self.assertRaisesRegex(ValueError, 'NO_REPLAY'):
            N.Job(job.path).execute(ready['confirmSha256'])
        self.assertEqual(self.writes.count('CreateZones'), 1)
        self.assertEqual(self.writes.count('CreateWalls'), 1)
        self.assertNotIn('SaveProject', self.writes)
        writes = list(self.writes)
        self.assertTrue(all(item['details']['details']['begCoordinate']['x'] < 6
                            for item in self.items.values() if item['element']['type'] == 'Wall'))
        with self.assertRaisesRegex(ValueError, 'NO_REPLAY'):
            N.Job(job.path).execute(ready['confirmSha256'])
        self.assertEqual(self.writes, writes)
        self.assertEqual(ready['modelWrites'], 0)
        self.assertTrue((job.path / 'attempted.json').is_file())

    def test_layout_partial_wall_batch_stops_before_openings_or_save_without_replay(self):
        job = self.stage_layout()
        ready = job.preflight()
        self.partial_wall_batch = True
        with self.assertRaisesRegex(ValueError, 'NO_REPLAY'):
            N.Job(job.path).execute(ready['confirmSha256'])
        self.assertEqual(self.writes, ['CreateWalls'])
        self.assertFalse((job.path / 'saved.json').exists())
        with self.assertRaisesRegex(ValueError, 'NO_REPLAY'):
            N.Job(job.path).execute(ready['confirmSha256'])
        self.assertEqual(self.writes, ['CreateWalls'])

    def test_layout_blocks_zero_layer_intersection_group(self):
        job = self.stage_layout()
        self.wall_layer_group = 0
        with self.assertRaisesRegex(ValueError, 'LAYOUT_WALL_LAYER_INTERSECTION_NOT_QUALIFIED'):
            job.preflight()
        self.assertEqual(self.writes, [])
        self.assertFalse((job.path / 'preflight.json').exists())

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
