import copy
import hashlib
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import archicad_bim_documentation as D
from test_archicad_scene_run import FakeNative
from test_archicad_functional_expansion import cube

OLD = '00000000-0000-4000-8000-000000000001'
NEW = '00000000-0000-4000-8000-000000000009'


class DocumentationTests(unittest.TestCase):
    def native(self):
        a = cube((2, 3, 4)); a.update(guid=OLD, type='Wall', homeStory=0,
            materialBindings={'buildingMaterial': {'guid': NEW}}, relationships={},
            placement={'referenceGeometry': {'height': 4}})
        b = cube((2, 3, .2)); b.update(guid=NEW, type='Slab', homeStory=1,
            materialBindings={}, relationships={}, placement={})
        return {'elements': [a, b], 'stories': [{'index': 0, 'elevation': 0}, {'index': 1, 'elevation': 3}]}

    def snapshot(self, native=None):
        n = native or self.native()
        # Signatures are exercised on real BREP in the live integration. Here
        # isolate documentation consumption from native material pool format.
        with patch.object(D.C, 'retained_geometry_signatures', side_effect=lambda raw, gs:
                {g: D.RUN.digest(next(e for e in raw['elements'] if e['guid'] == g)) for g in gs}):
            return D.make_snapshot(n, [OLD, NEW])

    def test_two_specifications_share_actual_geometry_and_version(self):
        s = self.snapshot(); p = D.bundle(s, 0)
        self.assertEqual(set(p['specifications']), {'Wall', 'Slab'})
        self.assertAlmostEqual(p['specifications']['Wall']['rows'][0]['quantities']['volumeCubicMeters'], 24)
        self.assertEqual(p['specifications']['Slab']['rows'][0]['storyElevationMeters'], 3)
        self.assertEqual(len(p['plan']['elements']), 1)
        self.assertEqual({v['modelVersion'] for v in p['specifications'].values()}, {s['modelVersion']})
        self.assertEqual(p['nativeViews'], {})

    def test_missing_cut_fill_and_curved_quantities_are_explicit(self):
        n = self.native(); n['elements'][0]['bodies'][0]['curved'] = True
        s = self.snapshot(n)
        wall = next(e for e in s['elements'] if e['guid'] == OLD)
        self.assertEqual(wall['floorPlanStatus'], 'NATIVE_CUT_FILL_NOT_AVAILABLE')
        self.assertEqual(wall['quantities']['status'], 'NATIVE_QUANTITIES_NOT_VERIFIED')
        self.assertNotIn('volumeCubicMeters', wall['quantities'])

    def test_model_change_invalidates_all_prepared_outputs(self):
        before = self.snapshot(); n = self.native()
        n['elements'][0]['placement']['referenceGeometry']['height'] = 5
        after = self.snapshot(n); delta = D.compare_versions(before, after)
        self.assertEqual(delta['changedGuids'], [OLD])
        self.assertNotEqual(D.bundle(before, 0)['plan']['modelVersion'], D.bundle(after, 0)['plan']['modelVersion'])
        self.assertEqual(D.compare_versions(before, before)['status'], 'BIM_FACTS_UNCHANGED')

    def test_view_dependent_cut_fills_do_not_create_a_false_model_revision(self):
        native = self.native()
        with patch.object(D.C, 'retained_geometry_signatures', return_value={OLD: 'wall', NEW: 'slab'}):
            before = D.make_snapshot(native, [OLD, NEW])
            after = D.make_snapshot(native, [OLD, NEW], {OLD: {'floorPlanPolygons': [{'coordinates': [{'x': 0, 'y': 0}]}]}})
        self.assertEqual(before['modelVersion'], after['modelVersion'])
        delta = D.compare_versions(before, after)
        self.assertEqual(delta['changedNativeModelGuids'], [])
        self.assertEqual(delta['changedDrawingFactGuids'], [OLD])

    def test_section_database_incomplete_dump_is_reread_only_once(self):
        replies = [{'elements': []}, {'elements': [{'guid': OLD}]}]; calls = []
        def api(c, p): calls.append(c); return replies.pop(0)
        with patch.object(D.C.G, 'normalize_dump', side_effect=lambda v: v):
            self.assertEqual(D.capture_full_model(api, [OLD])['elements'][0]['guid'], OLD)
            with self.assertRaises(ValueError): D.capture_full_model(lambda *_: {'elements': []}, [OLD])
        self.assertEqual(calls, ['GetModelDumpV1', 'GetModelDumpV1'])

    def test_missing_story_guid_and_duplicate_guid_rejected(self):
        with self.assertRaises(ValueError): D.bundle(self.snapshot(), 9)
        with self.assertRaises(ValueError): D.make_snapshot(self.native(), [OLD, OLD])
        with self.assertRaises(ValueError): D.make_snapshot(self.native(), ['missing'])
        n = self.native(); n['elements'][0]['homeStory'] = 12
        with self.assertRaises(ValueError): self.snapshot(n)

    def test_csv_export_preserves_shared_revision_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            p = D.bundle(self.snapshot(), 0); out = Path(temp) / 'package'
            D.write_package(p, out)
            self.assertTrue((out / 'Wall.csv').read_text(encoding='utf-8-sig').count(p['modelVersion']) == 1)
            self.assertTrue((out / 'Slab.csv').exists())
            with self.assertRaises(FileExistsError): D.write_package(p, out)

    def test_exact_scope_rejects_tamper_and_protected_wall(self):
        params = {'wallsWithDetails': [{'elementId': {'guid': OLD}, 'height': 2}]}
        with self.assertRaisesRegex(ValueError, 'ONLY_NEW_TEST'):
            D.operation_scope('ModifyWalls', params, 'source', [OLD], [OLD], 'test')
        params['wallsWithDetails'][0]['elementId']['guid'] = NEW
        scope = D.operation_scope('ModifyWalls', params, 'source', [OLD], [NEW], 'test')
        changed = copy.deepcopy(params); changed['wallsWithDetails'][0]['height'] = 3
        with self.assertRaisesRegex(ValueError, 'SCOPE_MISMATCH'): D.qualify_operation(scope, 'ModifyWalls', changed, 'source')
        with self.assertRaises(ValueError): D.operation_scope('DeleteElements', {}, 'source', [OLD], [], 'test')
        with self.assertRaises(ValueError): D.operation_scope('RebuildView', {}, 'source', [OLD], [], 'test')

    def operation(self, writer, scene='doc-test-section'):
        params = {'sectionsData': [{'startCoordinate': {'x': 0, 'y': 0},
            'endCoordinate': {'x': 4, 'y': 0}, 'depth': 3, 'floorIndex': 0, 'name': 'TEST'}]}
        scope = D.operation_scope('CreateSections', params, 'source', [OLD], [], 'synthetic test')
        pre = {'sourcePlanHash': 'source', 'binding': writer.guarded_binding(),
            'integrationBindings': {'dependencies': {'documentationOperation': scope}}}
        token = D.RUN.digest({'sceneId': scene, 'sourcePlanHash': 'source', 'command': 'CreateSections',
            'parameters': params, 'target': pre['binding']})
        return pre, params, token

    def test_section_is_journalled_and_cannot_replay(self):
        with tempfile.TemporaryDirectory() as temp:
            fake = FakeNative(); calls = []
            def api(c, p):
                if c == 'CreateSections': calls.append(c); return {'elements': [{'elementId': {'guid': NEW}}]}
                return fake(c, p)
            w = D.RUN.SceneWriter(api, Path(temp) / 'scene.sqlite')
            pre, params, token = self.operation(w)
            invoke = lambda: w.execute_bound_operation(pre, 'doc-test-section', 'CreateSections', params, token,
                lambda: {'status': 'PASS'}, lambda *_: {'status': 'NATIVE_SECTION_PASS'})
            self.assertEqual(invoke()['status'], 'PASS')
            with self.assertRaisesRegex(ValueError, 'NEVER_RETRY'): invoke()
            self.assertEqual(calls, ['CreateSections'])

    def test_unknown_outcome_and_failed_readback_never_replay(self):
        for mode in ('timeout', 'readback'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temp:
                fake = FakeNative(); calls = []
                def api(c, p):
                    if c == 'CreateSections':
                        calls.append(c)
                        if mode == 'timeout': raise TimeoutError('unknown')
                        return {'elements': [{'elementId': {'guid': NEW}}]}
                    return fake(c, p)
                w = D.RUN.SceneWriter(api, Path(temp) / 'scene.sqlite'); pre, params, token = self.operation(w)
                invoke = lambda: w.execute_bound_operation(pre, 'doc-test-section', 'CreateSections', params, token,
                    lambda: {}, lambda *_: {'status': 'NOT_VERIFIED'})
                self.assertEqual(invoke()['status'], 'PARTIAL_OR_UNKNOWN_OUTCOME')
                with self.assertRaises(ValueError): invoke()
                self.assertEqual(calls, ['CreateSections'])
                with closing(sqlite3.connect(w.journal_path)) as db:
                    self.assertEqual(db.execute('SELECT state FROM steps').fetchone()[0], 'UNKNOWN_OUTCOME')

    def test_scope_required_for_view_and_before_readback_failure_blocks_write(self):
        with tempfile.TemporaryDirectory() as temp:
            fake = FakeNative(); w = D.RUN.SceneWriter(fake, Path(temp) / 'scene.sqlite')
            pre, params, token = self.operation(w)
            pre.pop('integrationBindings')
            with self.assertRaises(ValueError):
                w.execute_bound_operation(pre, 'doc-test-section', 'CreateSections', params, token, lambda: {}, lambda *_: {})
            pre, params, token = self.operation(w)
            def failed(): raise ValueError('baseline drift')
            with self.assertRaisesRegex(ValueError, 'baseline drift'):
                w.execute_bound_operation(pre, 'doc-test-section', 'CreateSections', params, token, failed, lambda *_: {})
            self.assertNotIn('CreateSections', fake.calls)

    def test_native_dump_window_side_effect_is_followed_by_journalled_database_activation(self):
        with tempfile.TemporaryDirectory() as temp:
            fake = FakeNative(); calls = []; window = ['3DModel']
            def api(c, p):
                calls.append(c)
                if c == 'GetModelDumpV1':
                    window[0] = '3DModel'; return {'elements': [{'guid': OLD}]}
                if c == 'ChangeWindow': window[0] = 'FloorPlan'; return {'success': True}
                if c == 'GetCurrentWindowType': return {'currentWindowType': window[0]}
                if c == 'CreateSections':
                    self.assertEqual(window[0], 'FloorPlan')
                    return {'elements': [{'elementId': {'guid': NEW}}]}
                return fake(c, p)
            writer = D.RUN.SceneWriter(api, Path(temp) / 'scene.sqlite')
            _, params, _ = self.operation(writer)
            with patch.object(D.C.G, 'normalize_dump', side_effect=lambda v: v), \
                 patch.object(D.C, 'retained_geometry_signatures', return_value={OLD: 'retained'}), \
                 patch.object(Path, 'read_bytes', return_value=b'saved'):
                result = D.execute_operation(writer, 'doc-window-order', 'CreateSections', params, 'source',
                    {OLD: 'retained'}, lambda *_: {'status': 'NATIVE_SECTION_PASS'}, 'synthetic test',
                    saved_sha256=hashlib.sha256(b'saved').hexdigest(), activate_navigator_id=OLD, expected_window='FloorPlan')
            self.assertEqual(result['status'], 'PASS')
            self.assertLess(calls.index('GetModelDumpV1'), calls.index('ChangeWindow'))
            self.assertLess(calls.index('ChangeWindow'), calls.index('CreateSections'))
            json.dumps(result)
            with closing(sqlite3.connect(writer.journal_path)) as db:
                self.assertEqual(db.execute('SELECT COUNT(*) FROM scenes WHERE state="PASS"').fetchone()[0], 2)

    def test_persistence_requires_explicit_scope_and_cannot_open_a_foreign_project(self):
        with tempfile.TemporaryDirectory() as temp:
            fake = FakeNative(); w = D.RUN.SceneWriter(fake, Path(temp) / 'scene.sqlite')
            params = {'projectFilePath': 'OTHER.pln'}
            scope = D.operation_scope('OpenProject', params, 'source', [OLD], [], 'synthetic test')
            pre = {'sourcePlanHash': 'source', 'binding': w.guarded_binding(),
                'integrationBindings': {'dependencies': {'documentationOperation': scope}}}
            token = D.RUN.digest({'sceneId': 'doc-open-foreign', 'sourcePlanHash': 'source',
                'command': 'OpenProject', 'parameters': params, 'target': pre['binding']})
            with self.assertRaisesRegex(ValueError, 'FOREIGN_PROJECT'):
                w.execute_bound_operation(pre, 'doc-open-foreign', 'OpenProject', params, token, lambda: {}, lambda *_: {})
            self.assertNotIn('OpenProject', fake.calls)
            ordinary = D.C.RUN.SCENE.GRAPH.CONTRACTS.compile_batch(
                D.C.RUN.SCENE.GRAPH.CONTRACTS.load_catalog(w.schema_path),
                {'requests': [{'id': 'save', 'command': 'SaveProject', 'params': {}}]}, runtime_version='1.5.10')
            self.assertEqual(ordinary['results'][0]['disposition'], 'SPECIAL_REVIEW')
            self.assertFalse(ordinary['executionSupported'])

    def test_missing_floor_story_blocks_public_refresh_before_native_writes(self):
        with tempfile.TemporaryDirectory() as temp:
            calls = []; native = self.native()
            def api(c, p): calls.append(c); return native
            w = D.RUN.SceneWriter(api, Path(temp) / 'scene.sqlite')
            with patch.object(D.C.G, 'normalize_dump', side_effect=lambda v: v), \
                 patch.object(D.C, 'retained_geometry_signatures', return_value={OLD: 'wall', NEW: 'slab'}):
                with self.assertRaisesRegex(ValueError, 'STORY_MISSING'):
                    D.refresh_package(w, 'doc-bad-story', OLD, 9, [OLD, NEW], {}, {OLD: 'wall'}, 'test', 'hash')
            self.assertEqual(calls, ['GetModelDumpV1'])


if __name__ == '__main__': unittest.main()
