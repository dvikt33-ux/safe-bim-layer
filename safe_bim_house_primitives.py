"""Offline schema builders for a future house test.

Schema checks read the pinned local Tapir document. They do not call an
injected client, do not belong to SafeBIMOperations.OPERATIONS, and cannot
reach DONE. Geometry agreement is never ownership and never production
enablement.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from safe_bim_layer import SafeBIMError, TapirClient
from safe_bim_tapir_compat import SUPPORTED_TAPIR_VERSION
from safe_bim_verification import VerificationError, number, wall_z_contract

SCHEMA_PATH = Path(__file__).with_name('tapir-1.5.9.json')
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
INSUFFICIENT_READBACK = 'INSUFFICIENT_READBACK'
LIVE_PROBE_REQUIRED = 'LIVE_PROBE_REQUIRED'
FORBIDDEN_CAPABILITIES = frozenset({LIVE_VERIFIED, PRODUCTION_ENABLED})
HOUSE_PLAN_STEPS = (
    'mesh_ground', 'straight_walls', 'arc_wall', 'morph_porch',
    'roof_south', 'roof_north', 'final_reread',
)

# None of the new primitives are production operations. Straight walls remain
# available only through the existing dispatcher, which this module never calls.
NEW_PRIMITIVE_CAPABILITIES = {
    'arc_wall': READY_FOR_LIVE_PROBE,
    'mesh': READY_FOR_LIVE_PROBE,
    'morph': READY_FOR_LIVE_PROBE,
    'roof': READY_FOR_LIVE_PROBE,
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
# Historical unlabeled draft. Not a design position and not a payload field.
PORCH_PLACEHOLDER_BASE = {'x': 0.0, 'y': -1.5, 'z': GROUND_Z}
_SCHEMA_DOCUMENT = None


class OfflinePrimitiveError(SafeBIMError):
    pass


def schema_client() -> TapirClient:
    """Refused-call helper for callers outside the builders.

    Builders do not use this object. Schema checks go through
    validate_pinned_schema and never call a client method.
    """
    client = TapirClient(schema_path=str(SCHEMA_PATH))

    def refuse(command, params=None):
        raise OfflinePrimitiveError(f'offline house primitive refused Tapir call: {command}')

    client.call = refuse
    return client


def _pinned_schema():
    global _SCHEMA_DOCUMENT
    if _SCHEMA_DOCUMENT is None:
        _SCHEMA_DOCUMENT = json.loads(SCHEMA_PATH.read_text(encoding='utf-8'))
    return _SCHEMA_DOCUMENT


def _resolve_ref(schema, ref):
    if not ref or not ref.startswith('#/'):
        return None
    key = ref[2:]
    return schema.get(key) or schema.get('common_schemas', {}).get(key)


def _validate_node(schema, node, value, path):
    if '$ref' in node:
        target = _resolve_ref(schema, node['$ref'])
        if target is None:
            raise OfflinePrimitiveError(f'Unresolved Tapir schema ref {node["$ref"]} at {path}')
        return _validate_node(schema, target, value, path)
    typ = node.get('type')
    if typ == 'object':
        if not isinstance(value, dict):
            raise OfflinePrimitiveError(f'{path} must be object')
        allowed = set(node.get('properties', {}))
        missing = [key for key in node.get('required', []) if key not in value]
        if missing:
            raise OfflinePrimitiveError(f'{path} missing required fields {missing}')
        if node.get('additionalProperties') is False:
            extra = [key for key in value if key not in allowed]
            if extra:
                raise OfflinePrimitiveError(f'{path} has unsupported fields {extra}')
        for key, item in value.items():
            if key in node.get('properties', {}):
                _validate_node(schema, node['properties'][key], item, f'{path}.{key}')
    elif typ == 'array':
        if not isinstance(value, list):
            raise OfflinePrimitiveError(f'{path} must be array')
        if 'minItems' in node and len(value) < node['minItems']:
            raise OfflinePrimitiveError(f'{path} has too few items')
        if 'maxItems' in node and len(value) > node['maxItems']:
            raise OfflinePrimitiveError(f'{path} has too many items')
        if 'items' in node:
            for index, item in enumerate(value):
                _validate_node(schema, node['items'], item, f'{path}[{index}]')
    elif typ == 'string':
        if not isinstance(value, str):
            raise OfflinePrimitiveError(f'{path} must be string')
        if 'enum' in node and value not in node['enum']:
            raise OfflinePrimitiveError(f'{path} unsupported enum {value!r}; allowed={node["enum"]}')
    elif typ == 'integer':
        if not isinstance(value, int) or isinstance(value, bool):
            raise OfflinePrimitiveError(f'{path} must be integer')
    elif typ == 'number':
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise OfflinePrimitiveError(f'{path} must be number')
        exclusive = node.get('exclusiveMinimum')
        if exclusive is not None and value <= exclusive:
            raise OfflinePrimitiveError(f'{path} must be > {exclusive}')


def validate_pinned_schema(command, payload):
    """Pure offline check against the pinned Tapir 1.5.9 snapshot. No client and no transport."""
    schema = _pinned_schema()
    spec = schema.get('commands', {}).get(command)
    if not spec:
        raise OfflinePrimitiveError(f'No schema for {command}')
    _validate_node(schema, spec.get('parameters') or {'type': 'object'}, payload, f'{command}.parameters')


def _reject_injected(client):
    """Any caller-supplied object is untrusted. Do not read or call it."""
    if client is not None:
        raise OfflinePrimitiveError('offline builders reject injected clients before calling any validator')


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
    if record['production_enabled'] is not False or record['dispatch_allowed'] is not False:
        raise OfflinePrimitiveError('new house primitive cannot be production-enabled')
    if record['capability_state'] in FORBIDDEN_CAPABILITIES:
        raise OfflinePrimitiveError('new house primitive cannot be production-enabled')
    return record


def _validate(client, command, payload):
    _reject_injected(client)
    validate_pinned_schema(command, payload)


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
    """Diagnostic comparison only. Missing arcAngle cannot prove a straight wall either.

    Tapir emits geometryType \"Straight\" for APIWtyp_Normal even when arcAngle is
    nonzero. That string is not geometric proof and is not consulted here.
    """
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


def prepare_flat_mesh(polygon, absolute_z, floor_index, story_elevation, vertex_relative_z=0.0, client=None):
    """Flat mesh whose surface sits on the reference plane unless a relative offset is given.

    Graphisoft documents API_MeshType.level as the base-plane height from the floor.
    Tapir 1.5.9 stores that value verbatim and stores each polygon z in meshPolyZ.
    GetDetails returns the two fields separately, so absolute Z is reconstructed as
    story_elevation + mesh.level + meshPolyZ. A flat surface on the reference plane
    therefore writes vertex z = 0, not a second copy of the base-plane offset.
    """
    floor = _floor(floor_index)
    story = _num(story_elevation)
    absolute = _num(absolute_z)
    relative = _num(vertex_relative_z)
    level = absolute - story - relative
    points = _polygon3(polygon, relative)
    payload = {'meshesData': [{
        'floorIndex': floor, 'level': level, 'polygonCoordinates': points,
    }]}
    _validate(client, 'CreateMeshes', payload)
    expected_absolute = [story + level + point['z'] for point in points]
    fingerprint = {
        'story_index': floor,
        'story_elevation': story,
        'base_plane_offset': level,
        'vertex_relative_z': [point['z'] for point in points],
        'expected_absolute_vertex_z': expected_absolute,
        'polygon_xy': [{'x': point['x'], 'y': point['y']} for point in points],
        'polygon_outline': points,
        'expected_readback_polygon': _closed_ring(points),
        'vertical_formula': 'story_elevation + mesh.level + meshPolyZ',
        'level_write_meaning': 'story_relative_base_plane_stored_verbatim',
        'floor_index': floor,
    }
    return _base('mesh', 'CreateMeshes', payload, fingerprint, READY_FOR_LIVE_PROBE,
                 readback_capability=UNVERIFIED, z_semantics='SOURCE_SUPPORTED',
                 required_tapir_version=SUPPORTED_TAPIR_VERSION,
                 assumptions=[
                     'API_MeshType.level is the height of the mesh base plane from the floor level.',
                     'Tapir describes level as the Z reference of coordinates and writes polygon z to meshPolyZ.',
                     'GetDetails returns level and polygon z separately; it does not emit a summed absolute vertex Z.',
                     'The closing read-back vertex is the memo duplicate of the first point, not an extra design point.',
                 ])


def _closed_ring(points):
    """Memo read-back includes the repeated closing vertex that AddPolyToMemo writes."""
    if not points:
        return []
    closed = [dict(point) for point in points]
    if closed[0] != closed[-1]:
        closed.append(dict(closed[0]))
    return closed


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
    """Compare raw level and meshPolyZ. Do not treat a summed field Tapir does not return as success."""
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
            if abs(number(details['level']) - fingerprint['base_plane_offset']) > 1e-6:
                reasons.append('level')
        except VerificationError:
            reasons.append('level')
    outline = details.get('polygonCoordinates')
    expected = fingerprint['expected_readback_polygon']
    if isinstance(outline, list):
        if len(outline) != len(expected):
            reasons.append('polygon')
        else:
            for actual, wanted in zip(outline, expected):
                try:
                    if any(abs(number(actual[axis]) - wanted[axis]) > 1e-6 for axis in ('x', 'y', 'z')):
                        reasons.append('vertex_z' if abs(number(actual['z']) - wanted['z']) > 1e-6 else 'polygon')
                        reconstructed = fingerprint['story_elevation'] + number(details.get('level', fingerprint['base_plane_offset'])) + number(actual['z'])
                        if abs(reconstructed - wanted['z'] - fingerprint['story_elevation'] - fingerprint['base_plane_offset']) > 1e-6:
                            reasons.append('absolute_vertex_z')
                except (TypeError, KeyError, VerificationError):
                    reasons.append('polygon')
    elif 'polygonCoordinates' in details:
        reasons.append('polygon')
    return _diagnostic('MATCH' if not reasons else 'MISMATCH', reasons,
                       z_semantics='SOURCE_SUPPORTED', ownershipProven=False, production_enabled=False)


def porch_proposal():
    """Unconfirmed porch model. XY is absent. This is not a live payload."""
    return {
        'primitive': 'morph',
        'requested_size': dict(PORCH_SIZE),
        'requested_z': GROUND_Z,
        'xy': None,
        'placeholder': {
            'xy_specified': False,
            'not_a_design_decision': True,
            'note': 'Porch XY was not specified and is not a project position.',
        },
        'requires_confirmation': True,
        'position_confirmed': False,
        'live_payload_allowed': False,
        'payload': None,
        'capability_state': READY_FOR_LIVE_PROBE,
        'production_enabled': False,
        'dispatch_allowed': False,
        'ownershipProven': False,
        'readback_capability': UNVERIFIED,
        'assumptions': [
            'CreateMorphs size builds a local cuboid; GetDetails origin is the absolute tranmat translation.',
            'Porch XY is unconfirmed. No live payload is available.',
        ],
    }


def _identity_axes():
    return {
        'xAxis': {'x': 1.0, 'y': 0.0, 'z': 0.0},
        'yAxis': {'x': 0.0, 'y': 1.0, 'z': 0.0},
        'zAxis': {'x': 0.0, 'y': 0.0, 'z': 1.0},
    }


def _cuboid_local_vertices(size):
    """BuildCuboidMorphMemo corners, local to the morph placement."""
    sx, sy, sz = size['x'], size['y'], size['z']
    return [
        {'x': 0.0, 'y': 0.0, 'z': 0.0},
        {'x': sx, 'y': 0.0, 'z': 0.0},
        {'x': sx, 'y': sy, 'z': 0.0},
        {'x': 0.0, 'y': sy, 'z': 0.0},
        {'x': 0.0, 'y': 0.0, 'z': sz},
        {'x': sx, 'y': 0.0, 'z': sz},
        {'x': sx, 'y': sy, 'z': sz},
        {'x': 0.0, 'y': sy, 'z': sz},
    ]


_CUBOID_FACE_INDEXES = (
    (0, 1, 2, 3),
    (4, 5, 6, 7),
    (0, 1, 5, 4),
    (1, 2, 6, 5),
    (2, 3, 7, 6),
    (3, 0, 4, 7),
)


def prepare_morph_box(base_point, size, floor_index, client=None, position_confirmed=False):
    """basePoint + size box. Unconfirmed XY cannot produce a live payload.

    CreateMorphs writes an identity transform whose translation is basePoint,
    including absolute z, and a local cuboid from the origin to size.
    """
    if position_confirmed is not True:
        raise OfflinePrimitiveError('unconfirmed morph XY cannot produce a live-ready payload')
    base = _finite_point(base_point, ('x', 'y', 'z'))
    if not isinstance(size, dict) or set(size) != {'x', 'y', 'z'}:
        raise OfflinePrimitiveError('size must contain exactly x/y/z')
    dims = {axis: _positive(size[axis], f'size.{axis}') for axis in ('x', 'y', 'z')}
    floor = _floor(floor_index)
    payload = {'morphsData': [{'basePoint': base, 'size': dims, 'floorIndex': floor}]}
    _validate(client, 'CreateMorphs', payload)
    local_vertices = _cuboid_local_vertices(dims)
    axes = _identity_axes()
    fingerprint = {
        'origin': dict(base),
        'basePoint': base,
        'size': dims,
        'floorIndex': floor,
        **axes,
        'local_vertices': local_vertices,
        'origin_z_meaning': 'absolute_tranmat_translation',
    }
    return _base('morph', 'CreateMorphs', payload, fingerprint, READY_FOR_LIVE_PROBE,
                 readback_capability=UNVERIFIED, position_confirmed=True, requires_confirmation=False,
                 live_payload_allowed=True, xy={'x': base['x'], 'y': base['y']},
                 requested_size=dict(dims), requested_z=base['z'],
                 required_tapir_version=SUPPORTED_TAPIR_VERSION,
                 assumptions=[
                     'Size cuboid vertices are local. GetDetails origin/axes come from tranmat, not from echo size or absolute_bottom.',
                     'morph.level is a separate story-relative field and is not the box bottom.',
                 ])


def require_live_morph_payload(record):
    """Return a sendable morph payload only after explicit XY confirmation."""
    if not isinstance(record, dict) or record.get('position_confirmed') is not True or record.get('requires_confirmation') or record.get('live_payload_allowed') is not True:
        raise OfflinePrimitiveError('unconfirmed porch XY cannot produce a live-ready payload')
    payload = record.get('payload')
    if not isinstance(payload, dict) or 'morphsData' not in payload:
        raise OfflinePrimitiveError('unconfirmed porch XY cannot produce a live-ready payload')
    point = payload['morphsData'][0].get('basePoint')
    if point == PORCH_PLACEHOLDER_BASE and record.get('placeholder', {}).get('not_a_design_decision'):
        raise OfflinePrimitiveError('placeholder porch XY is not a confirmed position')
    return payload


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


def _vertex(point):
    if not isinstance(point, dict) or any(axis not in point for axis in ('x', 'y', 'z')):
        return None
    try:
        return {axis: number(point[axis]) for axis in ('x', 'y', 'z')}
    except VerificationError:
        return None


def _point_key(point):
    return tuple(round(point[axis], 6) for axis in ('x', 'y', 'z'))


def _close_point(actual, expected):
    parsed = _vertex(actual)
    wanted = _vertex(expected)
    if parsed is None or wanted is None:
        return False
    return all(abs(parsed[axis] - wanted[axis]) <= 1e-6 for axis in ('x', 'y', 'z'))


def _assess_cuboid_body(body, local_vertices):
    """Empty or faceless bodies are never a match. Echo size is not consulted."""
    reasons = []
    if not isinstance(body, dict):
        return ['body missing']
    vertices = body.get('vertices')
    if not isinstance(vertices, list) or not vertices:
        return ['empty vertices']
    parsed = []
    for point in vertices:
        vertex = _vertex(point)
        if vertex is None:
            return ['malformed vertex']
        parsed.append(vertex)
    expected_keys = [_point_key(point) for point in local_vertices]
    actual_keys = [_point_key(point) for point in parsed]
    if sorted(actual_keys) != sorted(expected_keys):
        reasons.append('local vertices')
    polygons = body.get('polygons')
    if not isinstance(polygons, list) or not polygons:
        return reasons + ['missing faces']
    faces = []
    for face in polygons:
        if not isinstance(face, dict):
            return reasons + ['malformed face']
        if face.get('holes'):
            return reasons + ['unexpected holes']
        ids = face.get('vertexIds')
        if not isinstance(ids, list) or len(ids) < 3 or any(not isinstance(item, int) or isinstance(item, bool) for item in ids):
            return reasons + ['malformed face']
        if any(item < 0 or item >= len(parsed) for item in ids):
            return reasons + ['malformed face']
        faces.append(frozenset(_point_key(parsed[item]) for item in ids))
    expected_faces = [
        frozenset(_point_key(local_vertices[index]) for index in face)
        for face in _CUBOID_FACE_INDEXES
    ]
    if faces != expected_faces and set(faces) != set(expected_faces):
        reasons.append('polygons')
    if len(faces) != len(expected_faces):
        reasons.append('polygons')
    return reasons


def assess_morph_readback(prepared, details):
    """Verify origin, identity axes, and the local cuboid. Echo fields cannot succeed alone."""
    fingerprint = prepared['fingerprint']
    if not isinstance(details, dict):
        return _diagnostic('MISMATCH', ['malformed'], ownershipProven=False, production_enabled=False)
    reasons = []
    for key in ('origin', 'xAxis', 'yAxis', 'zAxis', 'floorIndex', 'body'):
        if key not in details:
            reasons.append(f'{key} missing')
    if 'origin' in details and not _close_point(details.get('origin'), fingerprint['origin']):
        reasons.append('origin')
    for axis in ('xAxis', 'yAxis', 'zAxis'):
        if axis in details and not _close_point(details.get(axis), fingerprint[axis]):
            reasons.append(axis)
    if 'floorIndex' in details and details.get('floorIndex') != fingerprint['floorIndex']:
        reasons.append('floorIndex')
    if 'body' in details:
        reasons.extend(_assess_cuboid_body(details.get('body'), fingerprint['local_vertices']))
    geometry = 'MATCH' if not reasons else 'MISMATCH'
    return _diagnostic(geometry, reasons, ownershipProven=False, production_enabled=False,
                       readback_capability=UNVERIFIED)


def assess_morph_echo(prepared, echo):
    """Backward-compatible name. Echo size/absolute_bottom/absolute_top are not proof."""
    return assess_morph_readback(prepared, echo)


def _roof_rectangle(x0, y0, x1, y1):
    return [{'x': x0, 'y': y0}, {'x': x1, 'y': y0}, {'x': x1, 'y': y1}, {'x': x0, 'y': y1}]


def _xy(point):
    return {'x': _num(point['x']), 'y': _num(point['y'])}


def _close_xy(actual, expected):
    try:
        return abs(number(actual['x']) - expected['x']) <= 1e-6 and abs(number(actual['y']) - expected['y']) <= 1e-6
    except (TypeError, KeyError, VerificationError):
        return False


def _single_plane_roof(primitive, polygon, pivot_beg, pivot_end, eaves_z, story_elevation, floor,
                       thickness, angle, assumptions, client=None):
    """One CreateRoofs item. Input level is absolute; Tapir stores level minus story elevation."""
    item = {
        'level': eaves_z,
        'floorIndex': floor,
        'thickness': thickness,
        'polygonCoordinates': polygon,
        'structureType': 'Basic',
        'pivotLine': {'begCoordinate': dict(pivot_beg), 'endCoordinate': dict(pivot_end)},
        'angle': angle,
    }
    payload = {'roofsData': [item]}
    _validate(client, 'CreateRoofs', payload)
    fingerprint = {
        'roofClass': 'SinglePlane',
        'input_level': eaves_z,
        'expected_readback_level': eaves_z - story_elevation,
        'expected_zCoordinate': eaves_z,
        'story_elevation': story_elevation,
        'story_index': floor,
        'thickness': thickness,
        'structureType': 'Basic',
        'angle': angle,
        'pivot_begin': dict(pivot_beg),
        'pivot_end': dict(pivot_end),
        'polygon_outline': polygon,
        'expected_readback_polygon': _closed_ring(polygon),
        'level_write_meaning': 'absolute_z_converted_by_ResolveFloorIndexAndOffset',
        'readback_pivot_fields': ['begin', 'end'],
        'requested_geometry': {
            'requested_eaves_z': eaves_z,
            'requested_angle': angle,
        },
        'observed': 'NONE',
        'verified': False,
    }
    return _base(primitive, 'CreateRoofs', payload, fingerprint, READY_FOR_LIVE_PROBE,
                 selected=None, winner=None, pivot_side=LIVE_PROBE_REQUIRED,
                 readback_capability=UNVERIFIED, observed='NONE', verified=False,
                 required_tapir_version=SUPPORTED_TAPIR_VERSION,
                 assumptions=assumptions, schema_classification=READY_FOR_LIVE_PROBE)


def prepare_roof_candidates(eaves_z=ROOF_EAVES_Z, ridge_z=ROOF_RIDGE_Z, overhang=ROOF_OVERHANG,
                            floor_index=0, thickness=0.2, story_elevation=0.0, client=None):
    """South and north single-plane roofs. Neither side is selected or production-certified."""
    eaves, ridge = _num(eaves_z), _num(ridge_z)
    story = _num(story_elevation)
    if ridge <= eaves:
        raise OfflinePrimitiveError('ridge Z must be above eaves Z')
    overhang = _positive(overhang, 'overhang')
    floor = _floor(floor_index)
    thick = _positive(thickness, 'thickness')
    x0, x1, y0, y1 = -overhang, 10.0 + overhang, -overhang, 8.0 + overhang
    ridge_y = (y0 + y1) / 2
    run = ridge_y - y0
    angle = math.atan((ridge - eaves) / run)
    assumptions = [
        'Footprint is the wall bounding box expanded by overhang, not a true offset of arc D-E.',
        'Ridge is assumed parallel to X at the expanded mid-Y. Ridge direction was not specified.',
        'CreateRoofs level is absolute and ResolveFloorIndexAndOffset stores level minus story elevation.',
        'GetDetails returns story-relative level and absolute zCoordinate separately.',
        'Read-back pivotLine uses begin/end, not the create fields begCoordinate/endCoordinate.',
        'Tapir documents a left-of-direction rise and hardcodes posSign true. That does not certify which house side rises.',
        f'thickness={thick} is a probe placeholder, not an architectural specification.',
        'A rectangular multi-plane roof is not the house gable. Each plane is one future mutation and one GUID.',
    ]
    south = _single_plane_roof(
        'roof_south', _roof_rectangle(x0, y0, x1, ridge_y),
        {'x': x0, 'y': y0}, {'x': x1, 'y': y0}, eaves, story, floor, thick, angle, assumptions, client)
    north = _single_plane_roof(
        'roof_north', _roof_rectangle(x0, ridge_y, x1, y1),
        {'x': x1, 'y': y1}, {'x': x0, 'y': y1}, eaves, story, floor, thick, angle, assumptions, client)
    return {
        'selected': None, 'winner': None, 'pivot_side': LIVE_PROBE_REQUIRED,
        'capability_state': READY_FOR_LIVE_PROBE, 'production_enabled': False,
        'dispatch_allowed': False, 'observed': 'NONE', 'verified': False,
        'planes': {'south': south, 'north': north},
    }


def assess_roof_readback(candidate, details):
    """Single-plane read-back. Missing source fields are a mismatch, not success."""
    fingerprint = candidate.get('fingerprint', {})
    if not isinstance(details, dict):
        return _diagnostic('MISMATCH', ['malformed'], pivot_side=LIVE_PROBE_REQUIRED,
                           ownershipProven=False, production_enabled=False, observed='NONE', verified=False)
    reasons = []
    for key in ('roofClass', 'structureType', 'thickness', 'level', 'zCoordinate', 'polygonOutline', 'angle', 'pivotLine'):
        if key not in details:
            reasons.append(f'{key} missing')
    if details.get('roofClass') not in (None, 'SinglePlane') and details.get('roofClass') != fingerprint.get('roofClass'):
        reasons.append('roofClass')
    if 'roofClass' in details and details.get('roofClass') != 'SinglePlane':
        reasons.append('roofClass')
    if details.get('structureType') not in (None, fingerprint.get('structureType')) and 'structureType' in details:
        if details.get('structureType') != fingerprint.get('structureType'):
            reasons.append('structureType')
    for key, expected in (
        ('thickness', fingerprint.get('thickness')),
        ('level', fingerprint.get('expected_readback_level')),
        ('zCoordinate', fingerprint.get('expected_zCoordinate')),
        ('angle', fingerprint.get('angle')),
    ):
        if key not in details:
            continue
        try:
            if abs(number(details[key]) - expected) > 1e-6:
                reasons.append(key)
        except (TypeError, VerificationError):
            reasons.append(key)
    line = details.get('pivotLine')
    if isinstance(line, dict):
        if 'begin' not in line or 'end' not in line:
            reasons.append('pivotLine')
        else:
            if not _close_xy(line['begin'], fingerprint['pivot_begin']) or not _close_xy(line['end'], fingerprint['pivot_end']):
                reasons.append('pivotLine')
        if 'begCoordinate' in line and 'begin' not in line:
            reasons.append('pivotLine')
    elif 'pivotLine' in details:
        reasons.append('pivotLine')
    outline = details.get('polygonOutline')
    expected_outline = fingerprint.get('expected_readback_polygon', [])
    if isinstance(outline, list):
        if len(outline) != len(expected_outline):
            reasons.append('polygonOutline')
        else:
            for actual, wanted in zip(outline, expected_outline):
                if not _close_xy(actual, wanted):
                    reasons.append('polygonOutline')
                    break
    elif 'polygonOutline' in details:
        reasons.append('polygonOutline')
    geometry = 'MATCH' if not reasons else 'MISMATCH'
    return _diagnostic(geometry, reasons, pivot_side=LIVE_PROBE_REQUIRED, ownershipProven=False,
                       production_enabled=False, observed='NONE', verified=False,
                       readback_capability=UNVERIFIED)


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


def _final_reread_prepared():
    return {
        'kind': 'final_reread',
        'read_only': True,
        'writes_allowed': False,
        'adoption_allowed': False,
        'model_search_allowed': False,
        'receipt_policy': 'exact_verified_guids_only',
        'on_missing_receipt': 'STOP',
        'command': 'GetDetailsOfElements',
        'production_enabled': False,
        'dispatch_allowed': False,
        'capability_state': UNVERIFIED,
        'ownershipProven': False,
    }


def build_house_plan(client=None):
    _reject_injected(client)
    points = dict(HOUSE_OUTLINE)
    straight_names = (('A', 'B'), ('B', 'C'), ('C', 'D'), ('E', 'F'), ('F', 'G'), ('G', 'A'))
    straight = [prepare_straight_segment(points[a], points[b], 0, WALL_HEIGHT, WALL_THICKNESS, 0.0, 0.0)
                for a, b in straight_names]
    ccw = central_angle_ccw(ARC_CENTER, points['D'], points['E'])
    arc_candidates = [
        prepare_arc_wall(points['D'], points['E'], sign * ccw, 0, WALL_HEIGHT, WALL_THICKNESS, 0.0, 0.0,
                         center=ARC_CENTER, radius=ARC_RADIUS)
        for sign in (1, -1)
    ]
    mesh = prepare_flat_mesh(GROUND_POLYGON, GROUND_Z, 0, 0.0, vertex_relative_z=0.0)
    porch = porch_proposal()
    roof = prepare_roof_candidates(story_elevation=0.0)
    steps = [
        _step('mesh_ground', [], mesh),
        _step('straight_walls', ['mesh_ground'], {'segments': straight, 'production_enabled': False,
                                                  'dispatch_allowed': False, 'capability_state': SCHEMA_ONLY}),
        _step('arc_wall', ['straight_walls'], {'selected_angle': None, 'candidates': arc_candidates,
                                               'production_enabled': False, 'dispatch_allowed': False,
                                               'capability_state': READY_FOR_LIVE_PROBE,
                                               'arc_sign_choice': 'UNVERIFIED'}),
        _step('morph_porch', ['arc_wall'], porch),
        _step('roof_south', ['straight_walls', 'arc_wall'], roof['planes']['south']),
        _step('roof_north', ['straight_walls', 'arc_wall'], roof['planes']['north']),
        _step('final_reread', list(HOUSE_PLAN_STEPS[:-1]), _final_reread_prepared()),
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


def _reject_capability_mutation(node, path):
    if isinstance(node, dict):
        if 'production_enabled' in node and node['production_enabled'] is not False:
            raise OfflinePrimitiveError(f'{path} cannot be production-enabled')
        if 'dispatch_allowed' in node and node['dispatch_allowed'] is not False:
            raise OfflinePrimitiveError(f'{path} cannot be dispatchable')
        if node.get('capability_state') in FORBIDDEN_CAPABILITIES:
            raise OfflinePrimitiveError(f'{path} capability {node.get("capability_state")} is not allowed')
        for key, value in node.items():
            _reject_capability_mutation(value, f'{path}.{key}')
    elif isinstance(node, list):
        for index, value in enumerate(node):
            _reject_capability_mutation(value, f'{path}[{index}]')


def _contains_point(node, point):
    if isinstance(node, dict):
        if all(node.get(axis) == point[axis] for axis in point):
            return True
        return any(_contains_point(value, point) for value in node.values())
    if isinstance(node, list):
        return any(_contains_point(value, point) for value in node)
    return False


def validate_house_plan(plan):
    if not isinstance(plan, dict) or not isinstance(plan.get('steps'), list):
        raise OfflinePrimitiveError('house plan must contain steps')
    _reject_capability_mutation(plan, 'plan')
    if plan.get('dispatch_allowed') or plan.get('production_enabled'):
        raise OfflinePrimitiveError('house plan cannot be dispatchable')
    ids = [step['id'] for step in plan['steps']]
    if ids != list(HOUSE_PLAN_STEPS):
        raise OfflinePrimitiveError(f'house plan order must be {list(HOUSE_PLAN_STEPS)}')
    seen = set()
    for step in plan['steps']:
        if step.get('production_enabled') is not False or step.get('dispatch_allowed') is not False:
            raise OfflinePrimitiveError(f'{step["id"]} cannot be production-enabled')
        if any(dep not in seen for dep in step['depends_on']):
            raise OfflinePrimitiveError(f'{step["id"]} dependency is not an earlier step')
        seen.add(step['id'])
    by_id = {step['id']: step for step in plan['steps']}
    for roof_id in ('roof_south', 'roof_north'):
        roof = by_id[roof_id]['prepared']
        if roof.get('selected') is not None or roof.get('winner') is not None:
            raise OfflinePrimitiveError('roof candidate must not be selected')
        if roof.get('pivot_side') != LIVE_PROBE_REQUIRED:
            raise OfflinePrimitiveError('roof pivot side is not certified')
        roofs = roof.get('payload', {}).get('roofsData')
        if not isinstance(roofs, list) or len(roofs) != 1 or 'pivotLine' not in roofs[0] or 'levels' in roofs[0]:
            raise OfflinePrimitiveError('each roof step must be one single-plane mutation')
    porch = by_id['morph_porch']['prepared']
    if porch.get('position_confirmed') is True or porch.get('live_payload_allowed') or porch.get('payload'):
        raise OfflinePrimitiveError('unconfirmed porch XY cannot produce a live-ready payload')
    if porch.get('xy') is not None or porch.get('requires_confirmation') is not True:
        raise OfflinePrimitiveError('house porch XY requires confirmation')
    if _contains_point(porch, PORCH_PLACEHOLDER_BASE):
        raise OfflinePrimitiveError('placeholder porch XY must not be stored as a position')
    reread = by_id['final_reread']
    if reread['depends_on'] != list(HOUSE_PLAN_STEPS[:-1]):
        raise OfflinePrimitiveError('final reread must follow every geometry step')
    prepared = reread['prepared']
    if prepared.get('read_only') is not True or prepared.get('writes_allowed') is not False:
        raise OfflinePrimitiveError('final reread must be read-only')
    if prepared.get('adoption_allowed') is not False or prepared.get('model_search_allowed') is not False:
        raise OfflinePrimitiveError('final reread cannot search or adopt elements')
    if prepared.get('on_missing_receipt') != 'STOP' or prepared.get('command') in WRITE_COMMANDS:
        raise OfflinePrimitiveError('final reread cannot write and missing receipt is STOP')
    if prepared.get('command') != 'GetDetailsOfElements':
        raise OfflinePrimitiveError('final reread can only request exact element details')
    return plan


def control_action(event):
    if event in {'MISMATCH', 'UNKNOWN_OUTCOME', 'INCOMPLETE_READBACK', 'MISSING_RECEIPT'}:
        return 'STOP'
    raise OfflinePrimitiveError(f'no automatic continuation for {event}')


def evaluate_final_reread(receipts):
    """Read-only decision for exact receipt GUIDs. Missing receipt is STOP.

    This does not search the model, adopt a similar element, retry, or write.
    """
    stopped = {
        'action': 'STOP', 'decision': 'STOP', 'retryAllowed': False, 'repairWrite': False,
        'continueAllowed': False, 'adoptionAllowed': False, 'modelSearchAllowed': False,
        'writes': 0, 'reason': 'missing verified receipt',
    }
    if not isinstance(receipts, list) or not receipts:
        return stopped
    guids = []
    for receipt in receipts:
        guid = receipt.get('verifiedGuid') if isinstance(receipt, dict) else None
        if not isinstance(guid, str) or not guid:
            return stopped
        guids.append(guid)
    return {
        'action': 'READ_ONLY', 'decision': 'READ_ONLY', 'command': 'GetDetailsOfElements',
        'elements': [{'elementId': {'guid': guid}} for guid in guids],
        'retryAllowed': False, 'repairWrite': False, 'continueAllowed': False,
        'adoptionAllowed': False, 'modelSearchAllowed': False, 'writes': 0,
    }


def dispatch_house_plan(plan, client=None):
    _reject_injected(client)
    validate_house_plan(plan)
    raise OfflinePrimitiveError('house plan is offline-only; refusing every Create/Modify call')
