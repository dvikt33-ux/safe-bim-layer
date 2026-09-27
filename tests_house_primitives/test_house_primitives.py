import json
import math
import unittest
from pathlib import Path
from unittest.mock import patch

from safe_bim_house_primitives import (
    GROUND_POLYGON, GROUND_Z, HOUSE_PLAN_STEPS, INSUFFICIENT_READBACK, INSUFFICIENT_SCHEMA,
    PORCH_PLACEHOLDER_BASE, PORCH_SIZE, PRODUCTION_ENABLED, READY_FOR_LIVE_PROBE, SCHEMA_ONLY,
    UNVERIFIED, OfflinePrimitiveError, assess_arc_readback, assess_mesh_readback, assess_morph_echo,
    assess_morph_readback,
    assess_roof_readback, build_house_plan, control_action, dispatch_house_plan,
    evaluate_final_reread, experimental_morph_body, porch_proposal, prepare_arc_wall,
    prepare_flat_mesh, prepare_morph_box, prepare_roof_candidates, require_live_morph_payload,
    schema_client, validate_house_plan, validate_pinned_schema,
)
from safe_bim_layer import SafeBIMError, TapirClient
from safe_bim_operations import OPERATIONS, normalized_params


def _box_body(size, z):
    return {
        'vertices': [
            {'x': 0.0, 'y': 0.0, 'z': z},
            {'x': size['x'], 'y': 0.0, 'z': z},
            {'x': size['x'], 'y': size['y'], 'z': z},
            {'x': 0.0, 'y': 0.0, 'z': z + size['z']},
        ],
        'polygons': [{'vertexIds': [0, 1, 2]}],
    }


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
        self.assertEqual(prepared['arc_angle_sign'], 'UNVERIFIED')
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

    def test_house_arc_keeps_both_signs_unselected(self):
        plan = build_house_plan()
        prepared = plan['steps'][2]['prepared']
        self.assertIsNone(prepared['selected_angle'])
        signs = [item['payload']['wallsData'][0]['arcAngle'] for item in prepared['candidates']]
        self.assertEqual(len(signs), 2)
        self.assertTrue(signs[0] * signs[1] < 0)
        self.assertTrue(all(item['arc_angle_sign'] == 'UNVERIFIED' for item in prepared['candidates']))
        self.assertEqual(prepared['arc_sign_choice'], 'UNVERIFIED')

    def test_geometry_type_straight_is_not_arc_proof(self):
        prepared = prepare_arc_wall({'x': 0, 'y': 0}, {'x': 1, 'y': 0}, 0.4, 0, 3, 0.25, 0, 0)
        straight = {'begCoordinate': {'x': 0.0, 'y': 0.0}, 'endCoordinate': {'x': 1.0, 'y': 0.0},
                    'height': 3.0, 'zCoordinate': 0.0, 'geometryType': 'Straight'}
        verdict = assess_arc_readback(prepared, 0, straight)
        self.assertNotEqual(verdict['geometry'], 'MATCH')
        self.assertIn('arcAngle missing', verdict['reasons'])
        with_angle = dict(straight, arcAngle=0.4)
        self.assertEqual(assess_arc_readback(prepared, 0, with_angle)['geometry'], 'MATCH')


class MeshTests(unittest.TestCase):
    def test_flat_ground_does_not_double_apply_z(self):
        prepared = prepare_flat_mesh(GROUND_POLYGON, GROUND_Z, 0, 0.0)
        mesh = prepared['payload']['meshesData'][0]
        fingerprint = prepared['fingerprint']
        self.assertAlmostEqual(mesh['level'], -0.5)
        self.assertTrue(all(abs(point['z']) < 1e-9 for point in mesh['polygonCoordinates']))
        self.assertEqual(fingerprint['vertical_formula'], 'story_elevation + mesh.level + meshPolyZ')
        self.assertTrue(all(abs(value + 0.5) < 1e-9 for value in fingerprint['expected_absolute_vertex_z']))
        self.assertEqual(prepared['z_semantics'], 'SOURCE_SUPPORTED')
        self.assertNotEqual(prepared['capability_state'], PRODUCTION_ENABLED)
        self.assertFalse(prepared['production_enabled'])

    def test_nonzero_story_keeps_base_plane_relative(self):
        prepared = prepare_flat_mesh(GROUND_POLYGON, -0.5, 2, 3.0)
        mesh = prepared['payload']['meshesData'][0]
        self.assertAlmostEqual(mesh['level'], -3.5)
        self.assertTrue(all(abs(point['z']) < 1e-9 for point in mesh['polygonCoordinates']))
        self.assertTrue(all(abs(value + 0.5) < 1e-9 for value in prepared['fingerprint']['expected_absolute_vertex_z']))

    def test_wrong_vertex_floor_polygon_and_incomplete(self):
        prepared = prepare_flat_mesh(GROUND_POLYGON, -0.5, 0, 0.0)
        good = {'level': -0.5, 'floorIndex': 0, 'skirtType': 'SurfaceOnlyWithoutSkirt', 'skirtLevel': 0,
                'polygonCoordinates': prepared['fingerprint']['expected_readback_polygon']}
        self.assertEqual(assess_mesh_readback(prepared, good)['geometry'], 'MATCH')
        doubled = [dict(point, z=-0.5) for point in good['polygonCoordinates']]
        self.assertEqual(assess_mesh_readback(prepared, dict(good, polygonCoordinates=doubled))['geometry'], 'MISMATCH')
        moved = [dict(point, z=-0.2) for point in good['polygonCoordinates']]
        self.assertIn('vertex_z', assess_mesh_readback(prepared, dict(good, polygonCoordinates=moved))['reasons'])
        self.assertIn('floorIndex', assess_mesh_readback(prepared, dict(good, floorIndex=2))['reasons'])
        self.assertIn('polygon', assess_mesh_readback(prepared, dict(good, polygonCoordinates=moved[:3]))['reasons'])
        incomplete = assess_mesh_readback(prepared, {'level': -0.5})
        self.assertEqual(incomplete['geometry'], 'MISMATCH')
        self.assertFalse(incomplete['production_enabled'])

    def test_malformed_polygon_and_non_finite_z(self):
        with self.assertRaises(OfflinePrimitiveError):
            prepare_flat_mesh([(-1, -1), (11, -1)], -0.5, 0, 0.0)
        with self.assertRaises(OfflinePrimitiveError):
            prepare_flat_mesh(GROUND_POLYGON, float('nan'), 0, 0.0)
        with self.assertRaises(OfflinePrimitiveError):
            prepare_flat_mesh(GROUND_POLYGON, float('inf'), 0, 0.0)


def _source_morph_details(prepared):
    fingerprint = prepared['fingerprint']
    faces = ((0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7))
    return {
        'origin': dict(fingerprint['origin']),
        'xAxis': dict(fingerprint['xAxis']),
        'yAxis': dict(fingerprint['yAxis']),
        'zAxis': dict(fingerprint['zAxis']),
        'floorIndex': fingerprint['floorIndex'],
        'body': {
            'vertices': [dict(point) for point in fingerprint['local_vertices']],
            'polygons': [{'vertexIds': list(face)} for face in faces],
        },
    }


class MorphTests(unittest.TestCase):
    def test_box_uses_local_cuboid_and_absolute_origin(self):
        prepared = prepare_morph_box({'x': 1, 'y': 2, 'z': -0.5}, PORCH_SIZE, 0, position_confirmed=True)
        item = prepared['payload']['morphsData'][0]
        self.assertEqual(item['size'], {'x': 3.0, 'y': 1.5, 'z': 0.5})
        self.assertNotIn('body', item)
        self.assertEqual(prepared['fingerprint']['origin'], {'x': 1.0, 'y': 2.0, 'z': -0.5})
        self.assertEqual(prepared['fingerprint']['local_vertices'][0], {'x': 0.0, 'y': 0.0, 'z': 0.0})
        self.assertNotIn('absolute_bottom', prepared['fingerprint'])
        self.assertEqual(prepared['capability_state'], READY_FOR_LIVE_PROBE)
        self.assertFalse(prepared['production_enabled'])
        self.assertEqual(prepared['readback_capability'], UNVERIFIED)

    def test_empty_or_echo_body_is_not_a_match(self):
        prepared = prepare_morph_box({'x': 1, 'y': 2, 'z': -0.5}, PORCH_SIZE, 0, position_confirmed=True)
        details = _source_morph_details(prepared)
        empty = dict(details, body={'vertices': []})
        verdict = assess_morph_echo(prepared, empty)
        self.assertNotEqual(verdict['geometry'], 'MATCH')
        self.assertFalse(verdict['ownershipProven'])
        self.assertFalse(verdict['production_enabled'])
        echo_only = {'origin': details['origin'], 'size': PORCH_SIZE, 'floorIndex': 0,
                     'absolute_bottom': -0.5, 'absolute_top': 0.0, 'body': {'vertices': []}}
        self.assertNotEqual(assess_morph_echo(prepared, echo_only)['geometry'], 'MATCH')
        missing = assess_morph_readback(prepared, {'origin': details['origin'], 'body': details['body']})
        self.assertNotEqual(missing['geometry'], 'MATCH')
        self.assertTrue(any('missing' in reason for reason in missing['reasons']))
        malformed = dict(details, body={'vertices': [{'x': 0}], 'polygons': [{'vertexIds': [0, 1, 2]}]})
        self.assertIn('malformed vertex', assess_morph_readback(prepared, malformed)['reasons'])
        faceless = dict(details, body={'vertices': details['body']['vertices']})
        self.assertNotEqual(assess_morph_readback(prepared, faceless)['geometry'], 'MATCH')
        wrong_point = dict(details, origin={'x': 9, 'y': 9, 'z': -0.5})
        self.assertIn('origin', assess_morph_readback(prepared, wrong_point)['reasons'])

    def test_complete_body_is_not_ownership(self):
        prepared = prepare_morph_box({'x': 1, 'y': 2, 'z': -0.5}, PORCH_SIZE, 0, position_confirmed=True)
        verdict = assess_morph_readback(prepared, _source_morph_details(prepared))
        self.assertEqual(verdict['geometry'], 'MATCH')
        self.assertFalse(verdict['ownershipProven'])
        self.assertNotEqual(verdict['capability_state'], PRODUCTION_ENABLED)
        self.assertFalse(verdict['production_enabled'])

    def test_experimental_body_is_not_the_porch_primitive(self):
        experimental = experimental_morph_body([{'x': 0, 'y': 0, 'z': 0}, {'x': 1, 'y': 0, 'z': 0}])
        self.assertTrue(experimental['experimental'])
        self.assertEqual(experimental['capability_state'], SCHEMA_ONLY)
        self.assertNotEqual(experimental['primitive'], 'morph')


class RoofTests(unittest.TestCase):
    def test_gable_is_two_independent_single_planes(self):
        model = prepare_roof_candidates()
        self.assertIsNone(model['selected'])
        self.assertIsNone(model['winner'])
        self.assertEqual(model['pivot_side'], 'LIVE_PROBE_REQUIRED')
        self.assertNotEqual(model['capability_state'], PRODUCTION_ENABLED)
        south = model['planes']['south']
        north = model['planes']['north']
        self.assertEqual(len(south['payload']['roofsData']), 1)
        self.assertEqual(len(north['payload']['roofsData']), 1)
        self.assertIn('pivotLine', south['payload']['roofsData'][0])
        self.assertNotIn('levels', south['payload']['roofsData'][0])
        self.assertAlmostEqual(south['payload']['roofsData'][0]['angle'], math.atan(2.0 / 4.5))
        self.assertEqual(south['pivot_side'], 'LIVE_PROBE_REQUIRED')
        self.assertFalse(south['production_enabled'])
        self.assertFalse(north['production_enabled'])

    def test_assumptions_are_not_observed_facts(self):
        model = prepare_roof_candidates()
        for candidate in model['planes'].values():
            fingerprint = candidate['fingerprint']
            self.assertEqual(fingerprint['observed'], 'NONE')
            self.assertFalse(fingerprint['verified'])
            self.assertEqual(candidate['observed'], 'NONE')
            self.assertFalse(candidate['verified'])
            self.assertEqual(fingerprint['level_write_meaning'], 'absolute_z_converted_by_ResolveFloorIndexAndOffset')
            self.assertEqual(fingerprint['readback_pivot_fields'], ['begin', 'end'])
            self.assertNotIn('eaves_z', fingerprint)
            self.assertNotIn('ridge_z', fingerprint)
        self.assertEqual(model['observed'], 'NONE')
        self.assertFalse(model['verified'])

    def test_nonzero_story_converts_level_but_readback_z_stays_absolute(self):
        model = prepare_roof_candidates(story_elevation=4.5)
        fingerprint = model['planes']['south']['fingerprint']
        self.assertAlmostEqual(model['planes']['south']['payload']['roofsData'][0]['level'], 3.0)
        self.assertAlmostEqual(fingerprint['expected_readback_level'], 3.0 - 4.5)
        self.assertAlmostEqual(fingerprint['expected_zCoordinate'], 3.0)

    def test_missing_readback_is_mismatch_not_success(self):
        model = prepare_roof_candidates()
        for candidate in model['planes'].values():
            verdict = assess_roof_readback(candidate, {'ridge_z': 5.0, 'eaves_z': 3.0, 'pivotLine': {
                'begCoordinate': {'x': 0, 'y': 0}, 'endCoordinate': {'x': 1, 'y': 0}}})
            self.assertEqual(verdict['geometry'], 'MISMATCH')
            self.assertNotEqual(verdict['geometry'], 'MATCH')
            self.assertEqual(verdict['pivot_side'], 'LIVE_PROBE_REQUIRED')
            self.assertFalse(verdict['verified'])
            self.assertFalse(verdict['production_enabled'])
            self.assertFalse(verdict['ownershipProven'])
            self.assertTrue(any('missing' in reason for reason in verdict['reasons']))

    def test_source_fields_match_without_certifying_pivot_side(self):
        candidate = prepare_roof_candidates()['planes']['south']
        fingerprint = candidate['fingerprint']
        details = {
            'roofClass': 'SinglePlane',
            'structureType': 'Basic',
            'thickness': fingerprint['thickness'],
            'level': fingerprint['expected_readback_level'],
            'zCoordinate': fingerprint['expected_zCoordinate'],
            'angle': fingerprint['angle'],
            'pivotLine': {'begin': fingerprint['pivot_begin'], 'end': fingerprint['pivot_end']},
            'polygonOutline': fingerprint['expected_readback_polygon'],
        }
        verdict = assess_roof_readback(candidate, details)
        self.assertEqual(verdict['geometry'], 'MATCH')
        self.assertEqual(verdict['pivot_side'], 'LIVE_PROBE_REQUIRED')
        self.assertFalse(verdict['production_enabled'])
        self.assertFalse(verdict['ownershipProven'])


class HousePlanTests(unittest.TestCase):
    def test_order_dependencies_and_no_production_enablement(self):
        plan = build_house_plan()
        self.assertEqual([step['id'] for step in plan['steps']], list(HOUSE_PLAN_STEPS))
        self.assertEqual(plan['steps'][2]['depends_on'], ['straight_walls'])
        self.assertIsNone(plan['steps'][2]['prepared']['selected_angle'])
        self.assertEqual(len(plan['steps'][2]['prepared']['candidates']), 2)
        self.assertEqual(plan['steps'][4]['id'], 'roof_south')
        self.assertEqual(plan['steps'][5]['id'], 'roof_north')
        self.assertIsNone(plan['steps'][4]['prepared']['selected'])
        self.assertEqual(plan['steps'][4]['prepared']['pivot_side'], 'LIVE_PROBE_REQUIRED')
        self.assertEqual(len(plan['steps'][4]['prepared']['payload']['roofsData']), 1)
        self.assertEqual(len(plan['steps'][5]['prepared']['payload']['roofsData']), 1)
        self.assertFalse(plan['dispatch_allowed'])
        self.assertTrue(all(step['production_enabled'] is False for step in plan['steps']))
        self.assertEqual(control_action('MISMATCH'), 'STOP')
        self.assertEqual(control_action('UNKNOWN_OUTCOME'), 'STOP')
        self.assertEqual(control_action('MISSING_RECEIPT'), 'STOP')
        with self.assertRaises(OfflinePrimitiveError):
            control_action('CONTINUE')

    def test_final_reread_is_read_only_and_missing_receipt_stops(self):
        plan = build_house_plan()
        step = plan['steps'][-1]
        self.assertEqual(step['id'], 'final_reread')
        self.assertEqual(step['depends_on'], list(HOUSE_PLAN_STEPS[:-1]))
        prepared = step['prepared']
        self.assertTrue(prepared['read_only'])
        self.assertFalse(prepared['writes_allowed'])
        self.assertFalse(prepared['adoption_allowed'])
        self.assertFalse(prepared['model_search_allowed'])
        self.assertEqual(prepared['on_missing_receipt'], 'STOP')
        self.assertEqual(prepared['command'], 'GetDetailsOfElements')
        missing = evaluate_final_reread(None)
        self.assertEqual(missing['action'], 'STOP')
        self.assertEqual(missing['decision'], 'STOP')
        self.assertFalse(missing['retryAllowed'])
        self.assertFalse(missing['repairWrite'])
        self.assertEqual(missing['writes'], 0)
        self.assertEqual(evaluate_final_reread([{'verifiedGuid': ''}])['action'], 'STOP')
        read = evaluate_final_reread([{'verifiedGuid': 'ABC'}])
        self.assertEqual(read['action'], 'READ_ONLY')
        self.assertEqual(read['elements'], [{'elementId': {'guid': 'ABC'}}])
        self.assertEqual(read['writes'], 0)
        self.assertFalse(read['adoptionAllowed'])
        self.assertFalse(read['modelSearchAllowed'])
        self.assertNotIn('elementType', read)

    def test_unconfirmed_porch_has_no_live_payload(self):
        proposal = porch_proposal()
        self.assertIsNone(proposal['xy'])
        self.assertTrue(proposal['requires_confirmation'])
        self.assertFalse(proposal['position_confirmed'])
        self.assertIsNone(proposal['payload'])
        self.assertFalse(proposal['live_payload_allowed'])
        with self.assertRaises(OfflinePrimitiveError):
            require_live_morph_payload(proposal)
        with self.assertRaises(OfflinePrimitiveError):
            prepare_morph_box(PORCH_PLACEHOLDER_BASE, PORCH_SIZE, 0)
        plan = build_house_plan()
        porch = plan['steps'][3]['prepared']
        self.assertIsNone(porch['xy'])
        self.assertIsNone(porch['payload'])
        self.assertNotIn('basePoint', str(porch))
        self.assertFalse(porch['live_payload_allowed'])
        with self.assertRaises(OfflinePrimitiveError):
            require_live_morph_payload(porch)
        confirmed = prepare_morph_box({'x': 4, 'y': 1, 'z': -0.5}, PORCH_SIZE, 0, position_confirmed=True)
        self.assertIn('morphsData', require_live_morph_payload(confirmed))

    def test_capability_mutation_fails_validation(self):
        plan = build_house_plan()
        plan['steps'][0]['prepared']['production_enabled'] = True
        plan['steps'][0]['prepared']['capability_state'] = PRODUCTION_ENABLED
        with self.assertRaises(OfflinePrimitiveError):
            validate_house_plan(plan)
        plan = build_house_plan()
        plan['steps'][4]['prepared']['capability_state'] = 'LIVE_VERIFIED'
        with self.assertRaises(OfflinePrimitiveError):
            validate_house_plan(plan)
        plan = build_house_plan()
        plan['steps'][1]['production_enabled'] = True
        with self.assertRaises(OfflinePrimitiveError):
            validate_house_plan(plan)

    def test_builders_and_plan_perform_no_physical_write(self):
        calls = []
        with patch('urllib.request.urlopen', side_effect=AssertionError('network write attempted')):
            prepare_arc_wall({'x': 0, 'y': 0}, {'x': 1, 'y': 0}, 0.2, 0, 3, 0.25, 0, 0)
            prepare_flat_mesh(GROUND_POLYGON, -0.5, 0, 0.0)
            prepare_morph_box({'x': 0, 'y': 0, 'z': -0.5}, PORCH_SIZE, 0, position_confirmed=True)
            prepare_roof_candidates()
            plan = build_house_plan()
            with self.assertRaises(OfflinePrimitiveError):
                dispatch_house_plan(plan)
        self.assertEqual(calls, [])

    def test_live_client_is_refused_before_validation(self):
        with self.assertRaises(OfflinePrimitiveError):
            prepare_flat_mesh(GROUND_POLYGON, -0.5, 0, 0.0, client=TapirClient(schema_path='tapir-1.5.8.json'))

    def test_dispatcher_was_not_extended(self):
        self.assertEqual(OPERATIONS, frozenset({
            'create_wall_loop', 'create_basic_slab', 'create_plinth_segment', 'insert_window', 'insert_door'}))
        for name in ('create_arc_wall', 'create_mesh', 'create_morph', 'create_roof'):
            self.assertNotIn(name, OPERATIONS)
            with self.assertRaises(SafeBIMError):
                normalized_params(name, {})
        self.assertNotIn(PRODUCTION_ENABLED, {READY_FOR_LIVE_PROBE, SCHEMA_ONLY, UNVERIFIED})


class NoWriteBypassTests(unittest.TestCase):
    def test_stock_subclass_monkeypatch_hostile_and_proxy_write_nothing(self):
        writes = []

        class Sub(TapirClient):
            def call(self, command, params=None):
                writes.append(('subclass', command))
                return {}

        class Hostile:
            def validate_payload(self, command, payload):
                self.call(command, payload)

            def call(self, command, params=None):
                writes.append(('hostile', command))

        class Exposed:
            def __init__(self):
                self.calls = []

            def call(self, command, params=None):
                self.calls.append(command)
                writes.append(('exposed', command))

            def validate_payload(self, command, payload):
                self.call(command, payload)

        class CallableProxy:
            def __call__(self, command, params=None):
                writes.append(('proxy', command))

            def call(self, command, params=None):
                return self(command, params)

            def validate_payload(self, command, payload):
                return self(command, payload)

        stock = TapirClient(schema_path='tapir-1.5.8.json')
        subclass = Sub(schema_path='tapir-1.5.8.json')
        patched = schema_client()
        patched.call = lambda command, params=None: writes.append(('patched', command))
        hostile = Hostile()
        exposed = Exposed()
        proxy = CallableProxy()
        for client in (stock, subclass, patched, hostile, exposed, proxy):
            with self.assertRaises(OfflinePrimitiveError):
                prepare_flat_mesh(GROUND_POLYGON, -0.5, 0, 0.0, client=client)
            with self.assertRaises(OfflinePrimitiveError):
                prepare_arc_wall({'x': 0, 'y': 0}, {'x': 1, 'y': 0}, 0.2, 0, 3, 0.25, 0, 0, client=client)
            with self.assertRaises(OfflinePrimitiveError):
                build_house_plan(client)
        self.assertEqual(writes, [])
        self.assertEqual(exposed.calls, [])

    def test_pinned_validator_is_used_and_class_methods_are_not(self):
        writes = []

        def boom(*args, **kwargs):
            writes.append(args[:1])
            raise AssertionError('injected TapirClient method called')

        with patch.object(TapirClient, 'call', boom), patch.object(TapirClient, 'validate_payload', boom):
            prepare_flat_mesh(GROUND_POLYGON, -0.5, 0, 0.0)
            with self.assertRaises(OfflinePrimitiveError):
                validate_pinned_schema('CreateMeshes', {})
        self.assertEqual(writes, [])


class SnapshotPinTests(unittest.TestCase):
    def test_159_snapshot_is_pinned_and_158_remains(self):
        root = Path(__file__).resolve().parents[1]
        self.assertTrue((root / 'tapir-1.5.8.json').is_file())
        document = json.loads((root / 'tapir-1.5.9.json').read_text(encoding='utf-8'))
        meta = document['_metadata']
        self.assertEqual(meta['provider_version'], '1.5.9')
        self.assertEqual(meta['upstream_tag'], '1.5.9')
        self.assertEqual(meta['upstream_commit'], 'd0dbb11b13942e014661e1402b07958b70cd9dba')
        self.assertEqual(document['commands']['GetAddOnVersion']['returns']['required'], ['version'])
        self.assertIn('RoofDetails', document['common_schemas'])
        self.assertIn('MorphDetails', document['common_schemas'])
        self.assertIn('MeshDetails', document['common_schemas'])


if __name__ == '__main__':
    unittest.main()
