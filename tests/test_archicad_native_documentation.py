import copy
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import archicad_bim_documentation as D
import archicad_native_documentation as N
from test_archicad_scene_run import FakeNative

OLD = '00000000-0000-4000-8000-000000000001'
NEW = '00000000-0000-4000-8000-000000000009'


class NativeDocumentationTests(unittest.TestCase):
    def scope(self, command, parameters, tests=()):
        return D.operation_scope(command, parameters, 'source', [OLD], tests, 'synthetic explicit scope')

    def test_accepted_element_move_is_denied_but_new_marker_can_move(self):
        params = {'elementsWithMoveVectors': [{'elementId': {'guid': OLD},
            'moveVector': {'x': 0, 'y': -5, 'z': 0}, 'copy': False}]}
        with self.assertRaises(ValueError): self.scope('MoveElements', params, [OLD])
        params['elementsWithMoveVectors'][0]['elementId']['guid'] = NEW
        self.scope('MoveElements', params, [NEW])
        params['elementsWithMoveVectors'][0]['moveVector']['z'] = 1
        with self.assertRaises(ValueError): self.scope('MoveElements', params, [NEW])

    def test_copy_requires_retained_source_and_no_unregistered_target(self):
        row = {'elementId': {'guid': OLD}, 'moveVector': {'x': 44, 'y': 39, 'z': 0}, 'copy': True}
        self.scope('MoveElements', {'elementsWithMoveVectors': [row]})
        row['elementId']['guid'] = NEW
        with self.assertRaises(ValueError): self.scope('MoveElements', {'elementsWithMoveVectors': [row]})

    def test_only_new_view_can_change_frame(self):
        row = {'navigatorItemId': {'guid': NEW}, 'viewSettings': {'drawingScale': 100,
            'saveZoom': True, 'ignoreSavedZoom': False,
            'zoom': {'xMin': -51, 'xMax': -39, 'yMin': -1, 'yMax': 8}}}
        params = {'navigatorItemIdsWithViewSettings': [row]}
        self.scope('SetViewSettings', params, [NEW])
        row['viewSettings']['zoom']['xMax'] = -52
        with self.assertRaises(ValueError): self.scope('SetViewSettings', params, [NEW])
        row['viewSettings']['zoom']['xMax'] = -39
        row['navigatorItemId']['guid'] = OLD
        with self.assertRaises(ValueError): self.scope('SetViewSettings', params, [OLD])

    def test_explicit_master_is_required_despite_optional_installed_schema(self):
        params = {'layoutsData': [{'layoutName': 'test'}]}
        with self.assertRaisesRegex(ValueError, 'EXPLICIT_MASTER'): self.scope('CreateLayout', params)
        params['layoutsData'][0]['masterLayoutName'] = 'test master'
        self.scope('CreateLayout', params)

    def test_update_native_reply_is_not_execution_results_array(self):
        D.native_response('UpdateDrawings', {'success': True})
        with self.assertRaises(ValueError): D.native_response('UpdateDrawings', {'executionResults': [{'success': True}]})
        with self.assertRaises(ValueError): self.scope('UpdateDrawings', {'elements': [{'elementId': {'guid': OLD}}]}, [OLD])

    def test_publish_requires_explicit_local_selected_items(self):
        params = {'publisherSetName': 'layout', 'outputPath': str(Path.cwd() / 'new-export'),
            'selectedNavigatorItemIds': [{'navigatorItemId': {'guid': NEW}}]}
        self.scope('PublishPublisherSet', params)
        params['selectedNavigatorItemIds'] = []
        with self.assertRaises(ValueError): self.scope('PublishPublisherSet', params)
        params['selectedNavigatorItemIds'] = [{'navigatorItemId': {'guid': NEW}}]
        params['outputPath'] = '//server/share'
        with self.assertRaises(ValueError): self.scope('PublishPublisherSet', params)

    def test_empty_native_publish_reply_does_not_prove_output(self):
        D.native_response('PublishPublisherSet', {})
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, 'NO_FILE'): N.publication_files(temp)
            file = Path(temp) / 'native.pdf'; file.write_bytes(b'%PDF-test')
            proof = N.publication_files(temp)
            self.assertTrue(proof['files'][0]['pdfSignature'])
            self.assertIn('NOT_VERIFIED', proof['selectedPublisherSubset'])
            file.write_bytes(b'')
            with self.assertRaisesRegex(ValueError, 'EMPTY_FILE'): N.publication_files(temp)

    def test_layout_error_is_precise_and_other_native_errors_fail_closed(self):
        calls = []
        def api(*_):
            calls.append(1); return {'error': {'code': -2130313109, 'message': 'ShowAllIn3D'}}
        with self.assertRaisesRegex(ValueError, 'LAYOUT_MODEL_WINDOW'): D.capture_full_model(api, [OLD])
        self.assertEqual(len(calls), 1)
        with self.assertRaisesRegex(ValueError, 'NATIVE_DUMP_REJECTED'):
            D.capture_full_model(lambda *_: {'error': {'code': 123, 'message': 'other'}}, [OLD])

    def test_layout_recovery_is_one_journalled_window_change_then_full_proof(self):
        with tempfile.TemporaryDirectory() as temp:
            fake = FakeNative(); window = ['Layout']; calls = []
            def api(command, params):
                calls.append(command)
                if command == 'GetCurrentWindowType': return {'currentWindowType': window[0]}
                if command == 'GetNavigatorItemTree':
                    return {'type': 'StoryItem', 'prefix': '0', 'navigatorItemId': {'guid': NEW}}
                if command == 'ChangeWindow': window[0] = 'FloorPlan'; return {'success': True}
                if command == 'GetModelDumpV1': return {'elements': [{'guid': OLD}]}
                return fake(command, params)
            writer = D.RUN.SceneWriter(api, Path(temp) / 'journal.sqlite')
            with patch.object(Path, 'read_bytes', return_value=b'saved'), \
                    patch.object(D.C.G, 'normalize_dump', side_effect=lambda v: v), \
                    patch.object(D.C, 'retained_geometry_signatures', return_value={OLD: 'sig'}):
                result = D.restore_model_window(writer, 'layout-recovery', 'source',
                    {OLD: 'sig'}, 'synthetic view scope', hashlib.sha256(b'saved').hexdigest())
            self.assertEqual(result['count'], 1)
            self.assertEqual(calls.count('ChangeWindow'), 1)
            self.assertLess(calls.index('ChangeWindow'), calls.index('GetModelDumpV1'))
            self.assertFalse(any(c.startswith(('Create', 'Modify', 'Publish')) for c in calls))

    def test_half_facade_is_not_accepted_from_owner_count(self):
        proof = N.projection_span_check([0, 8.029887626], [0, 4.029887626])
        self.assertIn('NOT_VERIFIED', proof['status'])
        proof = N.projection_span_check([0, 8.029887626], [0, 8.0299122679], .0001)
        self.assertTrue(proof['status'].endswith('PASS'))
        self.assertEqual(proof['completeDrawingAcceptance'], 'NOT_IMPLIED')

    def test_nonfinite_projection_span_is_rejected(self):
        for values in ([0, float('nan')], [], [True, 8]):
            with self.assertRaises(ValueError): N.projection_span_check([0, 8], values)

    def details(self, polygons=True):
        row = {'type': 'Drawing', 'details': {'pos': {'x': .5, 'y': .03}, 'angle': 0,
            'ratio': 1, 'drawingScale': .01, 'modelOffset': {'x': 0, 'y': 0},
            'navigatorItemId': {'guid': OLD}, 'bounds': {'xMin': .02, 'xMax': .14}}}
        if polygons:
            row['floorPlanPolygons'] = [{'coordinates': [{'x': .02, 'y': .03},
                {'x': .14, 'y': .03}, {'x': .14, 'y': .1}]}]
        return {'detailsOfElements': [row]}

    def test_drawing_link_guid_is_distinct_from_requested_view_guid(self):
        proof = N.drawing_link(lambda *_: self.details(), NEW, NEW)
        self.assertEqual(proof['status'], 'NATIVE_DRAWING_LINK_METADATA_NOT_VERIFIED')
        self.assertNotEqual(proof['requestedSourceViewGuid'], proof['nativeReportedLinkGuid'])

    def test_native_drawing_contours_are_paper_xy_not_world_xyz(self):
        proof = N.drawing_graphics(lambda *_: self.details(), NEW, NEW, 'model')
        self.assertEqual(proof['contourCount'], 1)
        self.assertEqual(proof['derivedViewPolygons'][0]['coordinates'][0], {'u': -48, 'v': 0})
        self.assertEqual(proof['coordinateSystem'], 'Native Layout paperXY meters')
        self.assertEqual(proof['allVerticalPrimitives'], 'NOT_VERIFIED')

    def test_elevation_without_cut_fill_is_not_fabricated(self):
        proof = N.drawing_graphics(lambda *_: self.details(False), NEW, NEW, 'model')
        self.assertEqual(proof['contourCount'], 0)
        self.assertIn('NOT_VERIFIED', proof['status'])

    def test_malformed_native_contours_are_rejected(self):
        row = self.details(); row['detailsOfElements'][0]['floorPlanPolygons'][0]['coordinates'][0]['x'] = float('inf')
        with self.assertRaises(ValueError): N.drawing_graphics(lambda *_: row, NEW, NEW, 'model')

    def test_dimension_anchors_require_verified_actual_model_owner(self):
        reply = {'dimensionsData': [{'witnessPoints': [
            {'coordinate': {'x': 45, 'y': y}, 'baseElementId': {'guid': NEW},
             'dimensionPosition': 0, 'dimensionValue': value}
            for y, value in [(-.2, 0), (0, .2)]]}]}
        proof = N.dimension_graphics(lambda *_: reply, NEW, {NEW: OLD}, 'model')
        self.assertEqual(proof['points'][1]['modelOwnerGuid'], OLD)
        self.assertIn('not project XYZ', proof['coordinateSystem'])
        with self.assertRaises(ValueError): N.dimension_graphics(lambda *_: reply, NEW, {}, 'model')

    def test_schedule_definitions_do_not_claim_native_rows_or_csv(self):
        proof = N.schedule_inventory(lambda *_: {'type': 'ScheduleItem', 'navigatorItemId': {'guid': NEW}, 'name': 'Wall'})
        self.assertEqual(len(proof['definitions']), 1)
        self.assertIn('NOT_VERIFIED', proof['nativeRows'])
        self.assertIn('UNSUPPORTED', proof['configureScheme'])


if __name__ == '__main__':
    unittest.main()
