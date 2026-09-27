"""Offline schema builders for a future house test.

These functions validate Tapir payloads and fingerprints. They do not call
Tapir, do not belong to SafeBIMOperations.OPERATIONS, and cannot reach DONE.
Geometry agreement is never ownership and never production enablement.
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from safe_bim_layer import SafeBIMError, TapirClient
from safe_bim_verification import VerificationError, number, wall_z_contract

SCHEMA_PATH = Path(__file__).with_name('tapir-1.5.8.json')
WRITE_COMMANDS = frozenset({
    'CreateWalls', 'CreateSlabs', 'CreateMeshes', 'CreateMorphs', 'CreateRoofs',
    'ModifyWalls', 'ModifySlabs', 'ModifyMeshes', 'ModifyMorphs', 'ModifyRoofs',
    'CreateWindows', 'CreateDoors',
})

SCHEMA_ONLY = 'SCHEMA_ONLY'
READY_FOR_LIVE_PROBE = 'READY_FOR_LIVE_PROBE'
LIVE_VERIFIED = 'LIVE_VERIFIED'
PRODUCTION_ENABLED = 'PRODUCTION_ENABLED'
INSUFFICIENT_SCHEMA = 'INSUFFICIENT_SCHEMA'
READY_FOR_PROBE = 'READY_FOR_PROBE'
UNVERIFIED = 'UNVERIFIED'

# None of the new primitives are production operations. Straight walls remain
# available only through the existing dispatcher, which this module never calls.
NEW_PRIMITIVE_CAPABILITIES = {
    'arc_wall': READY_FOR_LIVE_PROBE,
    'mesh': READY_FOR_LIVE_PROBE,
    'morph': READY_FOR_LIVE_PROBE,
    'roof': SCHEMA_ONLY,
}

HOUSE_OUTLINE = (
    ('A', {'x': 0.0, 'y': 0.0}),
    ('B', {'x': 8.0, 'y': 0.0}),
    ('C', {'x': 10.0, 'y': 2.0}),
    ('D', {'x': 10.0, 'y': 6.0}),
    ('E', {'x': 8.0, 'y': 8.0}),
    ('F', {'x': 2.0, 'y': 8.0}),
    ('G', {'x': 0.0, 'y': 6.0}),
)
ARC_CENTER = {'x': 8.0, 'y': 6.0}
ARC_RADIUS = 2.0
GROUND_POLYGON = ((-1.0, -1.0), (11.0, -1.0), (11.0, 9.0), (-1.0, 9.0))
GROUND_Z = -0.5
WALL_HEIGHT = 3.0
WALL_THICKNESS = 0.25
ROOF_EAVES_Z = 3.0
ROOF_RIDGE_Z = 5.0
ROOF_OVERHANG = 0.5
PORCH_SIZE = {'x': 3.0, 'y': 1.5, 'z': 0.5}
# XY was not specified. This origin is a labeled placeholder, not a measurement.
PORCH_PLACEHOLDER_BASE = {'x': 0.0, 'y': -1.5, 'z': GROUND_Z}


class OfflinePrimitiveError(SafeBIMError):
    pass


def schema_client() -> TapirClient:
    """Schema validator with live/write calls refused."""
    client = TapirClient(schema_path=str(SCHEMA_PATH))

    def refuse(command, params=None):
        raise OfflinePrimitiveError(f'offline house primitive refused Tapir call: {command}')

    client.call = refuse
    return client


def _num(value):
    try:
        return number(value)
    except VerificationError as exc:
        raise OfflinePrimitiveError(str(exc)) from exc


def _finite_point(point, dims):
    if not isinstance(point, dict) or set(point) != set(dims):
        raise OfflinePrimitiveError(f'point must contain exactly {dims}')
    return {axis: _num(point[axis]) for axis in dims}


def _floor(value):
    if isinstance(value, bool) or not isinstance(value, int):
        raise OfflinePrimitiveError('integer floor_index required')
    return value


def _positive(value, label):
    number_value = _num(value)
    if number_value <= 0:
        raise OfflinePrimitiveError(f'{label} must be positive')
    return number_value


def _base(primitive, command, payload, fingerprint, capability, **extra):
    record = {
        'primitive': primitive,
        'command': command,
        'payload': payload,
        'fingerprint': fingerprint,
        'capability_state': capability,
        'production_enabled': False,
        'dispatch_allowed': False,
        'ownershipProven': False,
        'schema_valid': True,
    }
    record.update(extra)
    if record['production_enabled'] or record['capability_state'] == PRODUCTION_ENABLED:
        raise OfflinePrimitiveError('new house primitive cannot be production-enabled')
    return record


def _validate(client, command, payload):
    client = client or schema_client()
    call = getattr(client, 'call', None)
    if getattr(call, '__func__', None) is TapirClient.call:
        raise OfflinePrimitiveError('refusing a client that can perform a live Tapir call')
    client.validate_payload(command, payload)
    return client


def central_angle_ccw(center, start, end):
    """Geometric CCW angle. This is not an Archicad arcAngle sign."""
    center, start, end = (_finite_point(p, ('x', 'y')) for p in (center, start, end))
    v1 = (start['x'] - center['x'], start['y'] - center['y'])
    v2 = (end['x'] - center['x'], end['y'] - center['y'])
    return math.atan2(v1[0] * v2[1] - v1[1] * v2[0], v1[0] * v2[0] + v1[1] * v2[1])


def prepare_arc_wall(start, end, arc_angle, floor_index, height, thickness,
                     story_elevation, absolute_bottom, center=None, radius=None, client=None):
    """Schema-valid CreateWalls arc payload. Does not execute it.

    beg/end are chord endpoints. arc_angle is radians. Wall GetDetails arc
    capability stays UNVERIFIED: geometryType has no Arc value and arcAngle is
    not a required read-back field. Sign is not defined by CreateWalls.
    """
    start, end = _finite_point(start, ('x', 'y')), _finite_point(end, ('x', 'y'))
    if start == end:
        raise OfflinePrimitiveError('arc chord endpoints must differ')
    angle = _num(arc_angle)
    if angle == 0 or abs(angle) >= 2 * math.pi:
        raise OfflinePrimitiveError('true arcAngle must be a non-zero radians value below one turn')
    floor = _floor(floor_index)
    try:
        vertical = wall_z_contract(floor, story_elevation, absolute_bottom, _positive(height, 'height'))
    except VerificationError as exc:
        raise OfflinePrimitiveError(str(exc)) from exc
    thick = _positive(thickness, 'thickness')
    sign_note = 'CreateWalls.arcAngle sign is not defined; PolyArc right-hand sign is not evidence'
    if center is not None or radius is not None:
        if center is None or radius is None:
            raise OfflinePrimitiveError('center and radius must be supplied together')
        radius = _positive(radius, 'radius')
        ccw = central_angle_ccw(center, start, end)
        if abs(abs(ccw) - abs(angle)) > 1e-6:
            raise OfflinePrimitiveError('arcAngle magnitude does not match the supplied center/radius')
        for point in (start, end):
            distance = math.hypot(point['x'] - center['x'], point['y'] - center['y'])
            if abs(distance - radius) > 1e-6:
                raise OfflinePrimitiveError('chord endpoint is not on the supplied arc')
        sign_note += f'; geometric CCW angle is {ccw}'
    payload = {'wallsData': [{
        'begCoordinate': start, 'endCoordinate': end, 'floorIndex': floor,
        'zCoordinate': vertical['write_relative_z'], 'height': vertical['height'],
        'thickness': thick, 'arcAngle': angle, 'referenceLineLocation': 'Center',
        'structureType': 'Basic',
    }]}
    _validate(client, 'CreateWalls', payload)
    fingerprint = {
        **vertical, 'begCoordinate': start, 'endCoordinate': end, 'arcAngle': angle,
        'thickness': thick, 'center': center, 'radius': radius,
    }
    return _base('arc_wall', 'CreateWalls', payload, fingerprint, READY_FOR_LIVE_PROBE,
                 readback_capability=UNVERIFIED, arc_angle_sign='UNVERIFIED', assumptions=[sign_note],
                 expected_readback_model={
                     'geometryType': 'NOT_DISTINGUISHED_BY_SCHEMA', 'arcAngle': angle,
                     'begCoordinate': start, 'endCoordinate': end,
                     'zCoordinate': vertical['expected_readback_z'],
                     'bottomOffset': vertical['write_relative_z'], 'height': vertical['height'],
                     'thickness': thick, 'structureType': 'Basic',
                 })


def assess_arc_readback(prepared, floor_index, details):
    """Diagnostic comparison only. Missing arcAngle cannot prove a straight wall either."""
    reasons = []
    fingerprint = prepared['fingerprint']
    if not isinstance(details, dict):
        return _diagnostic('MISMATCH', ['malformed'])
    if floor_index != fingerprint['story_index']:
        reasons.append('floorIndex')
    for key, expected in (
        ('begCoordinate', fingerprint['begCoordinate']), ('endCoordinate', fingerprint['endCoordinate']),
        ('arcAngle', fingerprint['arcAngle']), ('height', fingerprint['height']),
        ('zCoordinate', fingerprint['expected_readback_z']),
    ):
        if key not in details:
            reasons.append(f'{key} missing')
        elif key == 'zCoordinate':
            try:
                if abs(number(details[key]) - expected) > 1e-6:
                    reasons.append('zCoordinate')
            except VerificationError:
                reasons.append('zCoordinate')
        elif details[key] != expected:
            reasons.append(key)
    if 'zCoordinate' in details:
        try:
            if abs(number(details['zCoordinate']) - fingerprint['write_relative_z']) <= 1e-6 and abs(fingerprint['write_relative_z'] - fingerprint['expected_readback_z']) > 1e-6:
                reasons.append('readback z must not be accepted as the write offset')
        except VerificationError:
            reasons.append('zCoordinate')
    return _diagnostic('MATCH' if not reasons else 'MISMATCH', reasons, readback_capability=UNVERIFIED)


def prepare_flat_mesh(polygon, absolute_z, floor_index, vertex_z=None, client=None):
    """CreateMeshes payload that keeps level and vertex Z semantically separate."""
    floor = _floor(floor_index)
    level = _num(absolute_z)
    if vertex_z is None:
        vertex_z = level
    else:
        vertex_z = _num(vertex_z)
    points = _polygon3(polygon, vertex_z)
    payload = {'meshesData': [{
        'floorIndex': floor, 'level': level, 'polygonCoordinates': points,
    }]}
    _validate(client, 'CreateMeshes', payload)
    fingerprint = {
        'requested_level': level, 'requested_vertex_z': vertex_z, 'floor_index': floor,
        'polygon_outline': points, 'level_vertex_identity': False,
    }
    return _base('mesh', 'CreateMeshes', payload, fingerprint, READY_FOR_LIVE_PROBE,
                 readback_capability=UNVERIFIED, z_semantics='AMBIGUOUS',
                 assumptions=[
                     'Schema describes level only as the Z reference of coordinates.',
                     'Equal requested_level and requested_vertex_z are a caller coincidence, not proof they share absolute/relative meaning.',
                 ])


def _polygon3(polygon, z):
    if not isinstance(polygon, (list, tuple)) or len(polygon) < 3:
        raise OfflinePrimitiveError('mesh polygon needs at least 3 points')
    points = []
    for item in polygon:
        if isinstance(item, dict):
            xy = _finite_point({'x': item['x'], 'y': item['y']}, ('x', 'y'))
        elif isinstance(item, (list, tuple)) and len(item) == 2:
            xy = {'x': _num(item[0]), 'y': _num(item[1])}
        else:
            raise OfflinePrimitiveError('mesh polygon point must be {x,y} or (x,y)')
        points.append({**xy, 'z': z})
    if len({(p['x'], p['y']) for p in points}) != len(points):
        raise OfflinePrimitiveError('mesh polygon has a repeated point')
    area = sum(a['x'] * b['y'] - b['x'] * a['y'] for a, b in zip(points, points[1:] + points[:1]))
    if abs(area) <= 1e-9:
        raise OfflinePrimitiveError('mesh polygon is degenerate')
    return points


def assess_mesh_readback(prepared, details):
    fingerprint = prepared['fingerprint']
    if not isinstance(details, dict):
        return _diagnostic('MISMATCH', ['malformed'])
    reasons = []
    for key in ('level', 'polygonCoordinates', 'floorIndex', 'skirtType', 'skirtLevel'):
        if key not in details:
            reasons.append(f'{key} missing')
    if 'floorIndex' in details and details['floorIndex'] != fingerprint['floor_index']:
        reasons.append('floorIndex')
    if 'level' in details:
        try:
            if abs(number(details['level']) - fingerprint['requested_level']) > 1e-6:
                reasons.append('level')
        except VerificationError:
            reasons.append('level')
    outline = details.get('polygonCoordinates')
    if isinstance(outline, list):
        expected = fingerprint['polygon_outline']
        if len(outline) != len(expected):
            reasons.append('polygon')
        else:
            for actual, wanted in zip(outline, expected):
                try:
                    if any(abs(number(actual[axis]) - wanted[axis]) > 1e-6 for axis in ('x', 'y', 'z')):
                        reasons.append('vertex_z' if abs(number(actual['z']) - wanted['z']) > 1e-6 else 'polygon')
                except (TypeError, KeyError, VerificationError):
                    reasons.append('polygon')
    return _diagnostic('MATCH' if not reasons else 'MISMATCH', reasons, z_semantics='AMBIGUOUS')


def prepare_morph_box(base_point, size, floor_index, client=None):
    """basePoint + size box. size/body mapping and Z/story relation stay unverified."""
    base = _finite_point(base_point, ('x', 'y', 'z'))
    if not isinstance(size, dict) or set(size) != {'x', 'y', 'z'}:
        raise OfflinePrimitiveError('size must contain exactly x/y/z')
    dims = {axis: _positive(size[axis], f'size.{axis}') for axis in ('x', 'y', 'z')}
    floor = _floor(floor_index)
    payload = {'morphsData': [{'basePoint': base, 'size': dims, 'floorIndex': floor}]}
    _validate(client, 'CreateMorphs', payload)
    fingerprint = {
        'basePoint': base, 'size': dims, 'floorIndex': floor,
        'absolute_bottom': base['z'], 'absolute_top': base['z'] + dims['z'],
        'base_z_is_absolute': 'UNVERIFIED',
    }
    return _base('morph', 'CreateMorphs', payload, fingerprint, READY_FOR_LIVE_PROBE,
                 readback_capability=UNVERIFIED,
                 assumptions=['Schema does not define how a size box is tessellated into MorphDetails.body or origin.'])


def experimental_morph_body(vertices, client=None):
    """Schema model only. Not the porch primitive and not production-enabled."""
    if not isinstance(vertices, list) or len(vertices) < 2:
        raise OfflinePrimitiveError('experimental body needs at least 2 vertices')
    body = {'vertices': [_finite_point(point, ('x', 'y', 'z')) for point in vertices]}
    payload = {'morphsData': [{'basePoint': {'x': 0.0, 'y': 0.0, 'z': 0.0}, 'body': body}]}
    _validate(client, 'CreateMorphs', payload)
    return _base('morph_body_experimental', 'CreateMorphs', payload, {'body': body}, SCHEMA_ONLY,
                 readback_capability=UNVERIFIED, experimental=True,
                 assumptions=['Vertices are local to Morph placement, not world coordinates.'])


def assess_morph_echo(prepared, echo):
    fingerprint = prepared['fingerprint']
    if not isinstance(echo, dict) or 'body' not in echo or 'origin' not in echo:
        return _diagnostic('MISMATCH', ['incomplete body/details'])
    reasons = []
    origin = echo.get('origin')
    if origin != fingerprint['basePoint']:
        reasons.append('basePoint')
    if echo.get('size') != fingerprint['size']:
        reasons.append('size')
    if echo.get('floorIndex') != fingerprint['floorIndex']:
        reasons.append('floorIndex')
    try:
        if abs(number(echo.get('absolute_bottom')) - fingerprint['absolute_bottom']) > 1e-6:
            reasons.append('absolute_bottom')
        if abs(number(echo.get('absolute_top')) - fingerprint['absolute_top']) > 1e-6:
            reasons.append('absolute_top')
    except VerificationError:
        reasons.append('z')
    return _diagnostic('MATCH' if not reasons else 'MISMATCH', reasons)


def _roof_rectangle(x0, y0, x1, y1):
    return [{'x': x0, 'y': y0}, {'x': x1, 'y': y0}, {'x': x1, 'y': y1}, {'x': x0, 'y': y1}]


def prepare_roof_candidates(eaves_z=ROOF_EAVES_Z, ridge_z=ROOF_RIDGE_Z, overhang=ROOF_OVERHANG,
                            floor_index=0, thickness=0.2, client=None):
    """Two schema-valid candidates. Neither is selected or claimed to be the gable."""
    eaves, ridge = _num(eaves_z), _num(ridge_z)
    if ridge <= eaves:
        raise OfflinePrimitiveError('ridge Z must be above eaves Z')
    overhang = _positive(overhang, 'overhang')
    floor = _floor(floor_index)
    thick = _positive(thickness, 'thickness')
    # Bounding-box probe footprint. Not a true offset of the arc outline.
    x0, x1, y0, y1 = -overhang, 10.0 + overhang, -overhang, 8.0 + overhang
    ridge_y = (y0 + y1) / 2
    run = ridge_y - y0
    angle = math.atan((ridge - eaves) / run)
    assumptions = [
        'Footprint is the wall bounding box expanded by overhang, not a true offset of arc D-E.',
        'Ridge is assumed parallel to X at the expanded mid-Y. Ridge direction was not specified.',
        'level=eaves_z is an unverified assumption; schema does not define level.',
        f'thickness={thick} is a probe placeholder, not an architectural specification.',
        'TypeSpecificDetails has no RoofDetails, so no candidate can be verified.',
    ]
    footprint = _roof_rectangle(x0, y0, x1, y1)
    multi_payload = {'roofsData': [{
        'level': eaves, 'floorIndex': floor, 'thickness': thick, 'polygonCoordinates': footprint,
        'eavesOverhang': overhang, 'structureType': 'Basic',
        'levels': [{'levelHeight': ridge - eaves, 'levelAngle': angle}],
    }]}
    south = {
        'level': eaves, 'floorIndex': floor, 'thickness': thick,
        'polygonCoordinates': _roof_rectangle(x0, y0, x1, ridge_y), 'structureType': 'Basic',
        'pivotLine': {'begCoordinate': {'x': x0, 'y': y0}, 'endCoordinate': {'x': x1, 'y': y0}},
        'angle': angle,
    }
    north = {
        'level': eaves, 'floorIndex': floor, 'thickness': thick,
        'polygonCoordinates': _roof_rectangle(x0, ridge_y, x1, y1), 'structureType': 'Basic',
        'pivotLine': {'begCoordinate': {'x': x1, 'y': y1}, 'endCoordinate': {'x': x0, 'y': y1}},
        'angle': angle,
    }
    split_payload = {'roofsData': [south, north]}
    _validate(client, 'CreateRoofs', multi_payload)
    _validate(client, 'CreateRoofs', split_payload)
    missing = ['RoofDetails', 'ridge Z', 'eaves Z', 'slope', 'plane count', 'pivot line read-back']
    desired = {'eaves_z': eaves, 'ridge_z': ridge, 'overhang': overhang, 'angle_radians': angle,
               'ridge_y': ridge_y, 'run': run}
    multi = _base('roof_multiplane', 'CreateRoofs', multi_payload, {**desired, 'polygon': footprint},
                  SCHEMA_ONLY, schema_classification=INSUFFICIENT_SCHEMA, selected=False,
                  readback_capability=INSUFFICIENT_SCHEMA, assumptions=assumptions + [
                      'levels[].levelHeight/levelAngle have no documented mapping to ridge_z or eaves_z.',
                  ], missing_readback_fields=missing, expected_geometry='UNSPECIFIED_MULTI_PLANE')
    split = _base('roof_two_single_planes', 'CreateRoofs', split_payload, {**desired, 'planes': 2},
                  SCHEMA_ONLY, schema_classification=INSUFFICIENT_SCHEMA, selected=False,
                  readback_capability=INSUFFICIENT_SCHEMA, assumptions=assumptions + [
                      'Schema says a pivotLine plane rises on the left of beg->end, angle in radians.',
                      'That documents a probe shape; it does not prove the resulting solid is the requested gable.',
                  ], missing_readback_fields=missing,
                  expected_geometry='TWO_PLANES_MEETING_AT_ASSUMED_RIDGE_IF_LEVEL_AND_PIVOT_ASSUMPTIONS_HOLD')
    return {
        'selected': None, 'winner': None, 'capability_state': SCHEMA_ONLY, 'production_enabled': False,
        'safer_live_probe': 'roof_two_single_planes',
        'safer_reason': 'pivotLine and angle have a documented side and radian unit; multi-plane levels do not identify ridge/eaves.',
        'candidates': {'A_multiplane': multi, 'B_two_single_planes': split},
    }


def assess_roof_readback(candidate, details):
    return _diagnostic('UNVERIFIED', ['RoofDetails absent from TypeSpecificDetails'],
                       schema_classification=INSUFFICIENT_SCHEMA, readback_capability=INSUFFICIENT_SCHEMA)


def _diagnostic(geometry, reasons, **extra):
    result = {'geometry': geometry, 'reasons': reasons, 'ownershipProven': False,
              'production_enabled': False, 'capability_state': SCHEMA_ONLY}
    result.update(extra)
    return result


def prepare_straight_segment(start, end, floor_index, height, thickness, story_elevation, absolute_bottom, client=None):
    start, end = _finite_point(start, ('x', 'y')), _finite_point(end, ('x', 'y'))
    if start == end:
        raise OfflinePrimitiveError('straight segment endpoints must differ')
    try:
        vertical = wall_z_contract(_floor(floor_index), story_elevation, absolute_bottom, _positive(height, 'height'))
    except VerificationError as exc:
        raise OfflinePrimitiveError(str(exc)) from exc
    thick = _positive(thickness, 'thickness')
    payload = {'wallsData': [{
        'begCoordinate': start, 'endCoordinate': end, 'floorIndex': vertical['story_index'],
        'zCoordinate': vertical['write_relative_z'], 'height': vertical['height'],
        'thickness': thick, 'referenceLineLocation': 'Center', 'structureType': 'Basic',
    }]}
    _validate(client, 'CreateWalls', payload)
    return _base('straight_wall_preview', 'CreateWalls', payload, {**vertical, 'begCoordinate': start,
                 'endCoordinate': end, 'thickness': thick}, SCHEMA_ONLY, dispatch_allowed=False,
                 assumptions=['Preview payload only. The house plan does not dispatch even existing wall operations.'])


def build_house_plan(client=None):
    client = client or schema_client()
    points = dict(HOUSE_OUTLINE)
    straight_names = (('A', 'B'), ('B', 'C'), ('C', 'D'), ('E', 'F'), ('F', 'G'), ('G', 'A'))
    straight = [prepare_straight_segment(points[a], points[b], 0, WALL_HEIGHT, WALL_THICKNESS, 0.0, 0.0, client)
                for a, b in straight_names]
    ccw = central_angle_ccw(ARC_CENTER, points['D'], points['E'])
    arc_candidates = [
        prepare_arc_wall(points['D'], points['E'], sign * ccw, 0, WALL_HEIGHT, WALL_THICKNESS, 0.0, 0.0,
                         center=ARC_CENTER, radius=ARC_RADIUS, client=client)
        for sign in (1, -1)
    ]
    mesh = prepare_flat_mesh(GROUND_POLYGON, GROUND_Z, 0, vertex_z=GROUND_Z, client=client)
    porch = prepare_morph_box(PORCH_PLACEHOLDER_BASE, PORCH_SIZE, 0, client=client)
    roof = prepare_roof_candidates(client=client)
    steps = [
        _step('mesh_ground', [], mesh),
        _step('straight_walls', ['mesh_ground'], {'segments': straight, 'production_enabled': False}),
        _step('arc_wall', ['straight_walls'], {'selected_angle': None, 'candidates': arc_candidates,
                                                'production_enabled': False}),
        _step('morph_porch', ['arc_wall'], porch),
        _step('roof', ['straight_walls', 'arc_wall'], roof),
    ]
    plan = {
        'name': 'house-offline-plan', 'dispatch_allowed': False, 'production_enabled': False,
        'on_mismatch': 'STOP', 'continue_after_unknown': False, 'automatic_repair_write': False,
        'steps': steps,
    }
    return validate_house_plan(plan)


def _step(step_id, depends_on, prepared):
    return {'id': step_id, 'depends_on': depends_on, 'prepared': prepared,
            'production_enabled': False, 'dispatch_allowed': False, 'on_mismatch': 'STOP'}


def validate_house_plan(plan):
    if plan.get('dispatch_allowed') or plan.get('production_enabled'):
        raise OfflinePrimitiveError('house plan cannot be dispatchable')
    ids = [step['id'] for step in plan['steps']]
    expected = ['mesh_ground', 'straight_walls', 'arc_wall', 'morph_porch', 'roof']
    if ids != expected:
        raise OfflinePrimitiveError(f'house plan order must be {expected}')
    seen = set()
    for step in plan['steps']:
        if step.get('production_enabled') or step.get('dispatch_allowed'):
            raise OfflinePrimitiveError(f'{step["id"]} cannot be production-enabled')
        if any(dep not in seen for dep in step['depends_on']):
            raise OfflinePrimitiveError(f'{step["id"]} dependency is not an earlier step')
        seen.add(step['id'])
    if plan['steps'][-1]['prepared'].get('selected') is not None:
        raise OfflinePrimitiveError('roof candidate must not be selected')
    return plan


def control_action(event):
    if event in {'MISMATCH', 'UNKNOWN_OUTCOME', 'INCOMPLETE_READBACK'}:
        return 'STOP'
    raise OfflinePrimitiveError(f'no automatic continuation for {event}')


def dispatch_house_plan(plan, client=None):
    validate_house_plan(plan)
    raise OfflinePrimitiveError('house plan is offline-only; refusing every Create/Modify call')
