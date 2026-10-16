"""Only discovery/graph/dispatch integration; no native tool functional tests."""
import copy
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'scripts'), str(ROOT/'tests')]
import archicad_project_accelerator as A
from archicad_dynamic_commands import DynamicCommands
from archicad_strategy_discovery import catalog_capabilities, source_data_hash, select_catalog_alternative
import test_apa_strategy_discovery_v2 as V2


def step(id_, type_, params, effect='CREATE'):
    s = {'id': id_, 'effect': effect, 'impact': 'MODEL',
         'elementType': type_, 'parameters': copy.deepcopy(params)}
    return qualify(s)


def qualify(s):
    s['sourceVerification'] = {'status': 'SOURCE_VERIFIED',
        'evidenceRef': 'SYNTHETIC_INTEGRATION_FIXTURE_NOT_BUILDING_DATA', 'dataHash': source_data_hash(s)}
    return s


def task(steps):
    return {'schemaVersion': 'apa-capability-task/1', 'request': 'OFFLINE INTEGRATION FIXTURE',
            'steps': steps, 'measurements': {}}


def dependency_task():
    wall = step('host', 'Wall', {'wallsData': [V2.wall()['nativeCreateData']]})
    data = V2.hosted()['nativeCreateData']
    data['ownerWallId']['guid'] = {'$result': {'step': 'host', 'pointer': '/elements/0/elementId/guid'}}
    return task([step('window', 'Window', {'windowsData': [data]}), wall])


class CatalogIntegration(unittest.TestCase):
    def test_all_catalog_contracts_are_visible_with_separate_runtime_state(self):
        r = V2.router(); view = catalog_capabilities(r)
        self.assertEqual(len(view), len(r.catalog['commands']))
        self.assertTrue(all('inputSchema' in v and 'effect' in v and 'runtimeStatus' in v for v in view))
        self.assertTrue(all(v['runtimeStatus'] == 'NOT_PROBED' for v in view))

    def test_automatic_command_assignment_and_dependency_order_use_original_graph(self):
        r = V2.router(); out = A.prepare_auto_optimized_native_task(r, dependency_task())
        self.assertEqual(out['status'], 'ONE_SOURCE_QUALIFIED_STRATEGY_PREPARED')
        p = out['selectedNativeTaskPreview']
        self.assertEqual(p['executor'], 'SceneWriter')
        self.assertEqual(p['workflow']['executionOrder'], ['host', 'window'])
        self.assertEqual(out['stepDiscovery'][0]['matchingCommands'], ['CreateWindows'])
        self.assertFalse(p['executionPermission'])
        # Verify delegation only. Existing native commands are not re-tested.
        with patch.object(r, 'run_workflow', return_value={'status': 'OFFLINE_DELEGATION'}) as run:
            result = A.run_auto_optimized_native_task(r, None, out, None, {})
        self.assertEqual(result['status'], 'OFFLINE_DELEGATION')
        self.assertEqual(run.call_args.args[1], p['workflow'])

    def test_invalid_generated_host_pointer_fit_or_cycle_is_never_prepared(self):
        for mode in ('type', 'pointer', 'fit', 'cycle'):
            t = dependency_task()
            if mode == 'type':
                t['steps'][1]['elementType'] = 'Column'
            elif mode == 'pointer':
                t['steps'][0]['parameters']['windowsData'][0]['ownerWallId']['guid']['$result']['pointer'] = '/missing/guid'
            elif mode == 'fit':
                t['steps'][0]['parameters']['windowsData'][0]['width'] = 100.
            else:
                t['steps'][1]['after'] = ['window']
            for s in t['steps']: qualify(s)
            out = A.prepare_auto_optimized_native_task(V2.router(), t)
            self.assertEqual(out['status'], 'NO_COMPLETE_CATALOG_STRATEGY', mode)
            self.assertIsNone(out['selectedNativeTaskPreview'])

    def test_no_cost_still_prepares_all_matching_schema_alternatives(self):
        r = V2.router()
        row = copy.deepcopy(r.catalog['commands']['CreateWalls'])
        r.add_provider('Fixture', {'CreateWalls': row}, 'OFFLINE TEST SOURCE')
        name = 'AddOn.Fixture.CreateWalls'
        r.review_policy(name, 'CREATE', 'MODEL', {'source': 'SYNTHETIC REVIEW', 'sha256': r.contract_hash(name)})
        t = task([step('wall', 'Wall', {'wallsData': [V2.wall()['nativeCreateData']]})])
        out = A.prepare_auto_optimized_native_task(r, t)
        self.assertEqual(out['status'], 'QUALIFIED_CATALOG_ALTERNATIVES_UNCALIBRATED')
        self.assertEqual(len(out['alternatives']), 2)
        self.assertTrue(all(c['nativeTaskPreview']['executor'] == 'SceneWriter' for c in out['alternatives']))
        with self.assertRaisesRegex(ValueError, 'UNAVAILABLE_OR_SOURCE_ONLY'):
            select_catalog_alternative(out, next(c['id'] for c in out['alternatives'] if c['executionBlockers']))
        chosen = select_catalog_alternative(out, next(c['id'] for c in out['alternatives'] if not c['executionBlockers']))
        self.assertEqual(chosen['selectionMethod'], 'EXPLICIT_CANDIDATE_CHOICE_NOT_COST_OPTIMIZATION')

    def test_unreviewed_effect_and_unavailable_runtime_do_not_match(self):
        r = V2.router(); t = task([step('wall', 'Wall', {'wallsData': [V2.wall()['nativeCreateData']]})])
        r.register_availability('CreateWalls', False)
        self.assertEqual(A.prepare_auto_optimized_native_task(r, t)['status'], 'NO_COMPLETE_CATALOG_STRATEGY')
        r = V2.router()
        r.review_policy('CreateWalls', 'UNKNOWN', 'MODEL', {'source': 'EXPLICIT TEST QUARANTINE',
                        'sha256': r.contract_hash('CreateWalls')})
        self.assertEqual(A.prepare_auto_optimized_native_task(r, t)['status'], 'NO_COMPLETE_CATALOG_STRATEGY')

    def test_complete_graph_costs_are_delegated_to_existing_optimizer(self):
        r = V2.router()
        r.add_provider('Fixture', {'CreateWalls': copy.deepcopy(r.catalog['commands']['CreateWalls'])}, 'OFFLINE TEST')
        name = 'AddOn.Fixture.CreateWalls'
        r.catalog['commands'][name]['availability'] = 'LIVE_EXPORT_REGISTERED'  # SYNTHETIC fixture only
        r.fingerprint = A.RUN.digest(r.catalog)
        r.review_policy(name, 'CREATE', 'MODEL', {'source': 'SYNTHETIC POLICY', 'sha256': r.contract_hash(name)})
        t = task([step('wall', 'Wall', {'wallsData': [V2.wall()['nativeCreateData']]})])
        preview = A.prepare_auto_optimized_native_task(r, t)
        for alt in preview['alternatives']:
            t['measurements'][alt['nativeTaskPreview']['sourcePlanHash']] = {
                'endToEndMs': 100, 'measurementKind': 'NATIVE_END_TO_END',
                'evidenceRef': 'SYNTHETIC_INTEGRATION_FIXTURE_NOT_REAL_TIMING',
                'contractHashes': {c: r.contract_hash(c) for c in alt['commands']},
                'taskHash': preview['measurementTaskHash']}
        chosen = preview['alternatives'][0]
        with patch('archicad_strategy_discovery.prepare_optimized_native_task', return_value={
            'selectedStrategyId': chosen['id'], 'selectedNativeTaskPreview': chosen['nativeTaskPreview'],
            'compared': [], 'nativeWritePermission': False, 'automaticNativeExecution': False}) as optimizer:
            result = A.prepare_auto_optimized_native_task(r, t)
        self.assertEqual(result['selectionMethod'], 'EXISTING_FAST_DOWNWARD_COMPLETE_GRAPH_COSTS')
        self.assertEqual(len(optimizer.call_args.args[2]), 2)

    def test_general_opening_uses_existing_contract_without_an_adapter(self):
        r = V2.router()
        r.review_policy('CreateOpenings', 'CREATE', 'MODEL', {'source': 'OFFLINE FIXTURE POLICY',
                       'sha256': r.contract_hash('CreateOpenings')})
        s = step('hole', 'Opening', {'openingsData': [{'ownerElementId': {'guid': V2.GUID},
            'basePoint': {'x': 1., 'y': 0., 'z': 4.}, 'width': .8, 'height': 1.}]})
        out = A.prepare_auto_optimized_native_task(r, task([s]))
        self.assertEqual(out['alternatives'][0]['commands'], ['CreateOpenings'])
        self.assertFalse(out['nativeWritePermission'])

    def test_native_grid_and_exact_stair_reuse_existing_qualifier(self):
        catalog = json.loads((ROOT/'schemas/accelerator/dynamic-runtime-catalog.json').read_text())
        for name in ('CreateNativeGridElementsV1', 'CreateExactStairsV1'):
            catalog['commands'][name]['availability'] = 'SOURCE_SNAPSHOT_NOT_RUNTIME_PROBED'
            catalog['commands'][name]['sourceSnapshot'] = 'HISTORIC_TEST_ONLY'
        r = DynamicCommands(catalog)
        for name in ('CreateNativeGridElementsV1', 'CreateExactStairsV1'):
            r.review_policy(name, 'CREATE', 'MODEL', {'source': 'OFFLINE SOURCE CONTRACT REVIEW', 'sha256': r.contract_hash(name)})
        grid = step('axis', 'GridElement', {'gridsData': [{'x': 0., 'y': 0., 'angle': 0.,
            'floorIndex': 0, 'expectedLibraryPartIndex': 1,
            'parameters': [{'name': 'FIXTURE_LENGTH', 'nativeType': 2, 'value': 4.}]}]})
        stair = step('stair', 'Stair', {'stairsData': [{'favoriteName': 'FIXTURE_STAIR',
            'baseLinePoints': [{'x': 0., 'y': 0.}, {'x': 4., 'y': 0.}],
            'zCoordinate': 0., 'floorIndex': 0, 'totalHeight': 3., 'flightWidth': 1.,
            'stepNum': 20, 'riserHeight': .15, 'treadDepth': .28,
            'treadDepthLocked': True, 'finishVisible': False}]})
        for s in (grid, stair):
            out = A.prepare_auto_optimized_native_task(r, task([s]))
            self.assertEqual(out['status'], 'SOURCE_CONTRACT_PLAN_REQUIRES_RUNTIME_QUALIFICATION')
            self.assertEqual(len(out['alternatives']), 1)
        stair['parameters']['stairsData'][0]['riserHeight'] = .5; qualify(stair)
        self.assertEqual(A.prepare_auto_optimized_native_task(r, task([stair]))['status'], 'NO_COMPLETE_CATALOG_STRATEGY')


if __name__ == '__main__':
    unittest.main()
