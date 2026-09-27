import math
import unittest
from unittest.mock import patch

from safe_bim_house_primitives import (
    GROUND_POLYGON, GROUND_Z, INSUFFICIENT_SCHEMA, PORCH_SIZE, PRODUCTION_ENABLED,
    READY_FOR_LIVE_PROBE, SCHEMA_ONLY, UNVERIFIED, OfflinePrimitiveError,
    assess_arc_readback, assess_mesh_readback, assess_morph_echo, assess_roof_readback,
    build_house_plan, control_action, dispatch_house_plan, experimental_morph_body,
    prepare_arc_wall, prepare_flat_mesh, prepare_morph_box, prepare_roof_candidates,
    schema_client,
)
from safe_bim_layer import SafeBIMError, TapirClient
from safe_bim_operations import OPERATIONS, normalized_params


class ArcWallTests(unittest.TestCase):
    def test_payload_radians_chord_and_story_zero_z(self):
        prepared = prepare_arc_wall({'x': 10, 'y': 6}, {'x': 8, 'y': 8}, math.pi / 2, 0, 3, 0.25, 0, 0,
                                    center={'x': 8, 'y': 6}, radius=2)
        wall = prepared['payload']['wallsData'][0]
        self.assertAlmostEqual(wall['arcAngle'], math.pi / 2)
        self.assertEqual(wall['begCoordinate'], {'x': 10.0, 'y': 6.0})
        self.assertEqual(wall['endCoordinate'], {'x': 8.0, 'y': 8.0})
        self.assertAlmostEqual(wall['zCoordinate'], 0.0)
        self.assertAlmostEqual(prepared['fingerprint']['write_relative_z'], 0.0)
        self.assertAlmostEqual(prepared['fingerprint']['expected_readback_z'], 0.0)
        self.assertEqual(prepared['capability_state'], READY_FOR_LIVE_PROBE)
        self.assertEqual(prepared['readback_capability'], UNVERIFIED)
        self.assertFalse(prepared['production_enabled'])
        self.assertIn('arcAngle', prepared['fingerprint'])

    def test_nonzero_story_keeps_write_offset_separate_from_readback(self):
        prepared = prepare_arc_wall({'x': 0, 'y': 0}, {'x': 2, 'y': 0}, math.pi / 2, 1, 0.6, 0.25, 4.5, 3.9)
        wall = prepared['payload']['wallsData'][0]
        self.assertAlmostEqual(wall['zCoordinate'], -0.6)
        self.assertAlmostEqual(prepared['fingerprint']['expected_readback_z'], 3.9)
        self.assertAlmostEqual(prepared['fingerprint']['expected_absolute_top_z'], 4.5)
        echo = {'begCoordinate': {'x': 0.0, 'y': 0.0}, 'endCoordinate': {'x': 2.0, 'y': 0.0},
                'arcAngle': math.pi / 2, 'height': 0.6, 'zCoordinate': 3.9}
        self.assertEqual(assess_arc_readback(prepared, 1, echo)['geometry'], 'MATCH')
        self.assertFalse(assess_arc_readback(prepared, 1, echo)['ownershipProven'])
        relative = dict(echo, zCoordinate=-0.6)
        rejected = assess_arc_readback(prepared, 1, relative)
        self.assertEqual(rejected['geometry'], 'MISMATCH')
        self.assertFalse(rejected['production_enabled'])

    def test_bad_angle_and_bad_readback(self):
        with self.assertRaises(OfflinePrimitiveError):
            prepare_arc_wall({'x': 0, 'y': 0}, {'x': 1, 'y': 0}, 0, 0, 3, 0.25, 0, 0)
        with self.assertRaises(OfflinePrimitiveError):
            prepare_arc_wall({'x': 0, 'y': 0}, {'x': 1, 'y': 0}, float('nan'), 0, 3, 0.25, 0, 0)
        with self.assertRaises(OfflinePrimitiveError):
            prepare_arc_wall({'x': 10, 'y': 6}, {'x': 8, 'y': 8}, math.pi, 0, 3, 0.25, 0, 0,
                             center={'x': 8, 'y': 6}, radius=2)
        prepared = prepare_arc_wall({'x': 0, 'y': 0}, {'x': 1, 'y': 0}, 0.4, 0, 3, 0.25, 0, 0)
        missing = {'begCoordinate': {'x': 0.0, 'y': 0.0}, 'endCoordinate': {'x': 1.0, 'y': 0.0},
                   'height': 3.0, 'zCoordinate': 0.0}
        self.assertIn('arcAngle missing', assess_arc_readback(prepared, 0, missing)['reasons'])
        wrong = dict(missing, arcAngle=1.2)
        self.assertEqual(assess_arc_readback(prepared, 0, wrong)['geometry'], 'MISMATCH')


class MeshTests(unittest.TestCase):
    def test_flat_ground_splits_level_and_vertex_z(self):
        prepared = prepare_flat_mesh(GROUND_POLYGON, GROUND_Z, 0)
        mesh = prepared['payload']['meshesData'][0]
        self.assertAlmostEqual(mesh['level'], -0.5)
        self.assertTrue(all(abs(point['z'] + 0.5) < 1e-9 for point in mesh['polygonCoordinates']))
        self.assertFalse(prepared['fingerprint']['level_vertex_identity'])
        self.assertEqual(prepared['z_semantics'], 'AMBIGUOUS')
        self.assertEqual(prepared['capability_state'], READY_FOR_LIVE_PROBE)

    def test_wrong_vertex_floor_polygon_and_incomplete(self):
        prepared = prepare_flat_mesh(GROUND_POLYGON, -0.5, 0, vertex_z=-0.5)
        good = {'level': -0.5, 'floorIndex': 0, 'skirtType': 'SurfaceOnlyWithoutSkirt', 'skirtLevel': 0,
                'polygonCoordinates': prepared['fingerprint']['polygon_outline']}
        self.assertEqual(assess_mesh_readback(prepared, good)['geometry'], 'MATCH')
        moved = [dict(point, z=-0.2) for point in good['polygonCoordinates']]
        self.assertIn('vertex_z', assess_mesh_readback(prepared, dict(good, polygonCoordinates=moved))['reasons'])
        self.assertIn('floorIndex', assess_mesh_readback(prepared, dict(good, floorIndex=2))['reasons'])
        self.assertIn('polygon', assess_mesh_readback(prepared, dict(good, polygonCoordinates=moved[:3]))['reasons'])
        incomplete = assess_mesh_readback(prepared, {'level': -0.5})
        self.assertEqual(incomplete['geometry'], 'MISMATCH')
        self.assertFalse(incomplete['production_enabled'])

    def test_malformed_polygon_and_non_finite_z(self):
        with self.assertRaises(OfflinePrimitiveError):
            prepare_flat_mesh([(-1, -1), (11, -1)], -0.5, 0)
        with self.assertRaises(OfflinePrimitiveError):
            prepare_flat_mesh(GROUND_POLYGON, float('nan'), 0)
        with self.assertRaises(OfflinePrimitiveError):
            prepare_flat_mesh(GROUND_POLYGON, float('inf'), 0)


class MorphTests(unittest.TestCase):
    def test_box_bottom_and_top(self):
        prepared = prepare_morph_box({'x': 0, 'y': -1.5, 'z': -0.5}, PORCH_SIZE, 0)
        item = prepared['payload']['morphsData'][0]
        self.assertEqual(item['size'], {'x': 3.0, 'y': 1.5, 'z': 0.5})
        self.assertNotIn('body', item)
        self.assertAlmostEqual(prepared['fingerprint']['absolute_bottom'], -0.5)
        self.assertAlmostEqual(prepared['fingerprint']['absolute_top'], 0.0)
        self.assertEqual(prepared['capability_state'], READY_FOR_LIVE_PROBE)
        self.assertFalse(prepared['production_enabled'])

    def test_wrong_echo_and_incomplete_details(self):
        prepared = prepare_morph_box({'x': 1, 'y': 2, 'z': -0.5}, PORCH_SIZE, 0)
        echo = {'origin': {'x': 1.0, 'y': 2.0, 'z': -0.5}, 'size': PORCH_SIZE, 'floorIndex': 0,
                'body': {'vertices': []}, 'absolute_bottom': -0.5, 'absolute_top': 0.0}
        self.assertEqual(assess_morph_echo(prepared, echo)['geometry'], 'MATCH')
        self.assertIn('basePoint', assess_morph_echo(prepared, dict(echo, origin={'x': 9, 'y': 9, 'z': -0.5}))['reasons'])
        self.assertIn('size', assess_morph_echo(prepared, dict(echo, size={'x': 1, 'y': 1, 'z': 1}))['reasons'])
        self.assertIn('absolute_top', assess_morph_echo(prepared, dict(echo, absolute_top=2))['reasons'])
        self.assertEqual(assess_morph_echo(prepared, {'origin': echo['origin']})['reasons'], ['incomplete body/details'])

    def test_experimental_body_is_not_the_porch_primitive(self):
        experimental = experimental_morph_body([{'x': 0, 'y': 0, 'z': 0}, {'x': 1, 'y': 0, 'z': 0}])
        self.assertTrue(experimental['experimental'])
        self.assertEqual(experimental['capability_state'], SCHEMA_ONLY)
        self.assertNotEqual(experimental['primitive'], 'morph')


class RoofTests(unittest.TestCase):
    def test_both_candidates_are_explicit_and_unselected(self):
        model = prepare_roof_candidates()
        self.assertIsNone(model['selected'])
        self.assertIsNone(model['winner'])
        self.assertEqual(model['capability_state'], SCHEMA_ONLY)
        multi = model['candidates']['A_multiplane']
        split = model['candidates']['B_two_single_planes']
        self.assertEqual(multi['schema_classification'], INSUFFICIENT_SCHEMA)
        self.assertEqual(split['schema_classification'], INSUFFICIENT_SCHEMA)
        self.assertNotIn('pivotLine', multi['payload']['roofsData'][0])
        self.assertEqual(len(split['payload']['roofsData']), 2)
        self.assertIn('pivotLine', split['payload']['roofsData'][0])
        self.assertAlmostEqual(split['payload']['roofsData'][0]['angle'], math.atan(2.0 / 4.5))
        self.assertTrue(multi['assumptions'])
        self.assertIn('RoofDetails', multi['missing_readback_fields'])
        self.assertEqual(model['safer_live_probe'], 'roof_two_single_planes')
        self.assertIsNone(model['winner'])

    def test_readback_unavailable_is_fail_closed(self):
        model = prepare_roof_candidates()
        for candidate in model['candidates'].values():
            verdict = assess_roof_readback(candidate, {'ridge_z': 5.0, 'eaves_z': 3.0})
            self.assertEqual(verdict['geometry'], 'UNVERIFIED')
            self.assertEqual(verdict['schema_classification'], INSUFFICIENT_SCHEMA)
            self.assertFalse(verdict['production_enabled'])
            self.assertFalse(verdict['ownershipProven'])


class HousePlanTests(unittest.TestCase):
    def test_order_dependencies_and_no_production_enablement(self):
        plan = build_house_plan()
        self.assertEqual([step['id'] for step in plan['steps']],
                         ['mesh_ground', 'straight_walls', 'arc_wall', 'morph_porch', 'roof'])
        self.assertEqual(plan['steps'][2]['depends_on'], ['straight_walls'])
        self.assertIsNone(plan['steps'][2]['prepared']['selected_angle'])
        self.assertEqual(len(plan['steps'][2]['prepared']['candidates']), 2)
        self.assertIsNone(plan['steps'][4]['prepared']['selected'])
        self.assertFalse(plan['dispatch_allowed'])
        self.assertTrue(all(step['production_enabled'] is False for step in plan['steps']))
        self.assertEqual(control_action('MISMATCH'), 'STOP')
        self.assertEqual(control_action('UNKNOWN_OUTCOME'), 'STOP')
        with self.assertRaises(OfflinePrimitiveError):
            control_action('CONTINUE')

    def test_builders_and_plan_perform_no_physical_write(self):
        calls = []
        with patch('urllib.request.urlopen', side_effect=AssertionError('network write attempted')):
            client = schema_client()
            client.call = lambda command, params=None: calls.append(command)
            prepare_arc_wall({'x': 0, 'y': 0}, {'x': 1, 'y': 0}, 0.2, 0, 3, 0.25, 0, 0, client=client)
            prepare_flat_mesh(GROUND_POLYGON, -0.5, 0, client=client)
            prepare_morph_box({'x': 0, 'y': 0, 'z': -0.5}, PORCH_SIZE, 0, client=client)
            prepare_roof_candidates(client=client)
            plan = build_house_plan(client)
            with self.assertRaises(OfflinePrimitiveError):
                dispatch_house_plan(plan, client)
        self.assertEqual(calls, [])

    def test_live_client_is_refused_before_validation(self):
        with self.assertRaises(OfflinePrimitiveError):
            prepare_flat_mesh(GROUND_POLYGON, -0.5, 0, client=TapirClient(schema_path='tapir-1.5.8.json'))

    def test_dispatcher_was_not_extended(self):
        self.assertEqual(OPERATIONS, frozenset({
            'create_wall_loop', 'create_basic_slab', 'create_plinth_segment', 'insert_window', 'insert_door'}))
        for name in ('create_arc_wall', 'create_mesh', 'create_morph', 'create_roof'):
            self.assertNotIn(name, OPERATIONS)
            with self.assertRaises(SafeBIMError):
                normalized_params(name, {})
        self.assertNotIn(PRODUCTION_ENABLED, {READY_FOR_LIVE_PROBE, SCHEMA_ONLY, UNVERIFIED})


if __name__ == '__main__':
    unittest.main()
