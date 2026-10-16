"""Real pinned schemas and original APA path; all geometry is TEST FIXTURE.

No native API calls, production benchmarks or LIVE_PASS are represented here.
"""
import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import archicad_project_accelerator as APA
from archicad_strategy_discovery import source_data_hash

GUID = '11111111-1111-4111-8111-111111111111'
MAT = {'guid': '22222222-2222-4222-8222-222222222222'}


def router():
    r = APA.native_command_router(ROOT/'schemas/tapir-live-1.5.10/tapir-scene-live.json',
                                  include_functional_modules=False)
    for command in ('MoveElements', 'CreateWalls', 'CreateSlabs', 'CreateWindows',
                    'CreateDoors', 'ModifyWalls', 'ModifySlabs'):
        r.review_policy(command, 'MODIFY' if command.startswith('Modify') else 'CREATE',
                        'MODEL', {'source': 'Pinned contract review FOR OFFLINE TEST ONLY',
                                  'sha256': r.contract_hash(command)})
    return r


def qualify(target):
    target['sourceVerification'] = {'status': 'SOURCE_VERIFIED',
        'evidenceRef': 'SYNTHETIC_TEST_DRAWING_AND_READBACK',
        'dataHash': source_data_hash(target)}
    return target


def wall(x=0):
    return qualify({'type': 'Wall', 'familySignature': 'TEST_BASIC_WALL_MAT_AND_GEOMETRY',
        'storyIndex': 1, 'storyElevation': 3., 'anchor': {'x': x, 'y': 0., 'z': 3.2},
        'sourceRef': 'TEST_KR_WALL_01', 'nativeCreateData': {
            'begCoordinate': {'x': x, 'y': 0.}, 'endCoordinate': {'x': x+4., 'y': 0.},
            'floorIndex': 1, 'zCoordinate': .2, 'height': 3., 'thickness': .2,
            'offset': 0., 'arcAngle': 0., 'referenceLineLocation': 'Center',
            'structureType': 'Basic', 'buildingMaterialId': MAT}})


def slab():
    return qualify({'type': 'Slab', 'familySignature': 'TEST_SLAB_MAT_POLYGON_AND_SETTINGS',
        'storyIndex': 1, 'storyElevation': 3., 'anchor': {'x': 0., 'y': 0., 'z': 3.},
        'sourceRef': 'TEST_KR_SLAB_01', 'nativeCreateData': {
            'floorIndex': 1, 'level': 3., 'thickness': .2, 'referencePlaneLocation': 'Top',
            'polygonCoordinates': [{'x': 0., 'y': 0.}, {'x': 4., 'y': 0.},
                                   {'x': 4., 'y': 4.}, {'x': 0., 'y': 4.}],
            'polygonArcs': [], 'holes': [], 'favoriteName': 'TEST_SLAB_FAVORITE'},
        'settingsQualification': {'status': 'SOURCE_VERIFIED',
            'favoriteName': 'TEST_SLAB_FAVORITE', 'settingsHash': 'a'*64,
            'attributesVerified': True, 'structureType': 'Basic'}})


def source(target):
    return {'guid': GUID, 'type': target['type'], 'familySignature': target['familySignature'],
            'storyIndex': target['storyIndex'], 'anchor': copy.deepcopy(target['anchor']),
            'nativeReadbackVerified': True, 'nativeDependenciesVerified': True,
            'dependentElementGuids': [], 'nativeSignatureSHA256': 'b'*64}


def hosted(kind='Window', offset=1.):
    host = wall()['nativeCreateData']
    return qualify({'type': kind, 'familySignature': 'TEST_HOSTED_LIBRARY_AND_GEOMETRY',
        'storyIndex': 1, 'storyElevation': 3., 'anchor': {'x': offset, 'y': 0., 'z': 4.2},
        'sourceRef': 'TEST_KR_HOSTED_01', 'nativeCreateData': {
            'ownerWallId': {'guid': GUID}, 'centerOffset': offset, 'width': .8, 'height': 1.,
            'sillHeight': 1., 'reflected': False, 'refSide': False, 'oSide': False,
            'libraryPartName': 'TEST_EXACT_'+kind},
        'libraryQualification': {'status': 'SOURCE_VERIFIED', 'settingsHash': 'c'*64,
                                 'libraryPartName': 'TEST_EXACT_'+kind},
        'hostContext': {'guid': GUID, 'type': 'Wall', 'storyIndex': 1,
            'nativeReadbackVerified': True, 'relationshipsComplete': True,
            'wallData': host, 'existingOpenings': []}})


def plan(targets, existing=None, r=None, benchmarks=None):
    return APA.prepare_auto_optimized_native_task(r or router(), {
        'schemaVersion': 'apa-native-auto/2', 'request': 'OFFLINE TEST FIXTURE ONLY',
        'existing': existing or [], 'targets': targets, 'benchmarks': benchmarks or {}})


def command(result):
    return result['selectedNativeTaskPreview']['workflow']['graph']['operations'][0]


class V2Tests(unittest.TestCase):
    def test_wall_batch_real_schema_original_preview_and_story_offset(self):
        out = plan([wall(), wall(5)])
        self.assertEqual(command(out)['command'], 'CreateWalls')
        self.assertEqual(len(command(out)['params']['wallsData']), 2)
        self.assertEqual(out['calibrationStatus'], 'UNCALIBRATED')
        self.assertEqual(out['selectedNativeTaskPreview']['executor'], 'SceneWriter')
        self.assertFalse(out['selectedNativeTaskPreview']['executionPermission'])
        bad = wall(); bad['nativeCreateData']['zCoordinate'] = 3.2; qualify(bad)
        self.assertEqual(plan([bad])['status'], 'BLOCKED_NO_COMPLETE_QUALIFIED_STRATEGY')

    def test_slab_requires_qualified_favorite_materials_and_explicit_holes(self):
        out = plan([slab()])
        self.assertEqual(command(out)['command'], 'CreateSlabs')
        bad = slab(); del bad['settingsQualification']; qualify(bad)
        self.assertEqual(plan([bad])['status'], 'BLOCKED_NO_COMPLETE_QUALIFIED_STRATEGY')
        bad = slab(); bad['nativeCreateData']['buildingMaterialId'] = MAT; qualify(bad)
        self.assertEqual(plan([bad])['status'], 'BLOCKED_NO_COMPLETE_QUALIFIED_STRATEGY')

    def test_copy_vs_create_real_schema_uncalibrated_and_dependency_closure(self):
        for factory in (wall, slab):
            target = factory(); prototype = source(target)
            prototype['anchor']['x'] = -10.
            out = plan([target], [prototype])
            self.assertEqual(out['status'], 'COST_COMPARISON_BLOCKED_UNCALIBRATED_ALTERNATIVES')
            self.assertEqual(out['discovery']['qualifiedStrategies'], 2)
            prototype['dependentElementGuids'] = [MAT['guid']]
            self.assertEqual(command(plan([target], [prototype]))['command'],
                             'CreateWalls' if target['type'] == 'Wall' else 'CreateSlabs')

    def test_modify_walls_and_slabs_original_route_and_exact_baseline(self):
        for factory, name, field, changes in (
            (wall, 'ModifyWalls', 'wallsWithDetails', {'height': 3.1}),
            (slab, 'ModifySlabs', 'slabsWithDetails', {'thickness': .25})):
            target = factory(); baseline = source(target)
            target.update(operation='MODIFY', baselineSignatureSHA256='b'*64,
                          nativeModifyData={'elementId': {'guid': GUID}, **changes})
            qualify(target)
            out = plan([target], [baseline])
            self.assertEqual(command(out)['command'], name)
            self.assertEqual(command(out)['params'][field][0]['elementId']['guid'], GUID)
            baseline['nativeSignatureSHA256'] = 'd'*64
            with self.assertRaisesRegex(ValueError, 'EXACT_INDEPENDENT_BASELINE'):
                plan([target], [baseline])

    def test_slab_outline_cannot_silently_erase_holes(self):
        target = slab(); baseline = source(target)
        target.update(operation='MODIFY', baselineSignatureSHA256='b'*64,
                      nativeModifyData={'elementId': {'guid': GUID},
                                        'polygonOutline': target['nativeCreateData']['polygonCoordinates']})
        qualify(target)
        with self.assertRaisesRegex(ValueError, 'PRESERVE_EXPLICIT_HOLES'):
            plan([target], [baseline])
        target['nativeModifyData'].update(holes=[], polygonArcs=[]); qualify(target)
        self.assertEqual(command(plan([target], [baseline]))['command'], 'ModifySlabs')

    def test_existing_polygon_validator_rejects_self_crossing_slab(self):
        target = slab()
        points = target['nativeCreateData']['polygonCoordinates']
        points[1], points[2] = points[2], points[1]
        qualify(target)
        out = plan([target])
        self.assertEqual(out['status'], 'BLOCKED_NO_COMPLETE_QUALIFIED_STRATEGY')
        self.assertTrue(any('POLYGON_INVALID' in r['reason']
                            for r in out['discovery']['rejectedStrategies']))

    def test_hosted_batches_actual_schemas_and_no_independent_host_copy(self):
        for kind in ('Window', 'Door'):
            out = plan([hosted(kind, 1.), hosted(kind, 3.)])
            self.assertEqual(command(out)['command'], 'Create'+kind+'s')
            self.assertEqual(out['discovery']['qualifiedStrategies'], 1)
        target = hosted(); baseline = source(target)
        baseline['ownerWallGuid'] = MAT['guid']
        self.assertEqual(command(plan([target], [baseline]))['command'], 'CreateWindows')
        baseline['ownerWallGuid'] = GUID
        self.assertEqual(plan([target], [baseline])['status'], 'NO_CHANGES_REQUIRED')

    def test_host_mismatch_overlap_clearance_and_source_tampering_fail(self):
        target = hosted(); target['hostContext']['guid'] = MAT['guid']; qualify(target)
        self.assertEqual(plan([target])['status'], 'BLOCKED_NO_COMPLETE_QUALIFIED_STRATEGY')
        with self.assertRaisesRegex(ValueError, 'BATCH_HOST_OPENING_COLLISION'):
            plan([hosted(offset=1.), hosted(offset=1.2)])
        target = hosted(); target['hostContext']['existingOpenings'] = [{'start': .7, 'end': 1.5}]
        qualify(target)
        self.assertEqual(plan([target])['status'], 'BLOCKED_NO_COMPLETE_QUALIFIED_STRATEGY')
        target = hosted(); target['nativeCreateData']['width'] = 9.
        with self.assertRaisesRegex(ValueError, 'PROVENANCE_OR_HASH'):
            plan([target])
        qualify(target)
        self.assertEqual(plan([target])['status'], 'BLOCKED_NO_COMPLETE_QUALIFIED_STRATEGY')

    def test_unreviewed_or_unavailable_command_and_mixed_partial_batch_block(self):
        r = router(); r.policies.pop('CreateWalls')
        self.assertEqual(plan([wall()], r=r)['status'], 'BLOCKED_NO_COMPLETE_QUALIFIED_STRATEGY')
        r = router(); r.register_availability('CreateWalls', False)
        self.assertEqual(plan([wall()], r=r)['status'], 'BLOCKED_NO_COMPLETE_QUALIFIED_STRATEGY')
        with self.assertRaisesRegex(ValueError, 'HOMOGENEOUS_COMPLETE_BATCH'):
            plan([wall(), slab()])

    def test_original_execution_rejects_missing_scope_before_any_api_call(self):
        r = router(); out = plan([wall()], r=r)
        def no_api(*args):
            self.fail('Native API must not be called without a scope')
        with self.assertRaisesRegex(ValueError, 'EXACT_STEP_SCOPE'):
            APA.run_auto_optimized_native_task(r, no_api, out, None, {})
        out['nativeWritePermission'] = True
        with self.assertRaisesRegex(ValueError, 'NOT_READY'):
            APA.run_auto_optimized_native_task(r, no_api, out, None, {})

    def test_v2_benchmarks_require_identical_workload_and_native_evidence_kind(self):
        target = wall(); prototype = source(target); prototype['anchor']['x'] = -10.
        r = router()
        with self.assertRaisesRegex(ValueError, 'EXACT_BENCHMARK_FIELDS'):
            plan([target], [prototype], r, {'CreateWalls': {
                'batchSize': 1, 'endToEndMs': 100, 'evidenceRef': 'SYNTHETIC_FIXTURE',
                'contractHash': r.contract_hash('CreateWalls')}})


if __name__ == '__main__':
    unittest.main()
