"""Fail-closed typed Archicad Wall continuation executor.

This is the only mutation surface exposed by the chat bridge MVP.  Remote JOBs
cannot pass arbitrary Tapir command names or arbitrary wall coordinates.  They
identify one existing straight Basic Wall, one endpoint, and a short extension
length.  The executor re-reads the source immediately before the write, checks
it against the caller's expected source state, derives CreateWalls parameters,
executes exactly one CreateWalls command, and performs factual read-back.

Any ambiguous write outcome is terminal UNKNOWN_OUTCOME and must never be
automatically retried.
"""
from __future__ import annotations

import math
import re

TOL = 1e-7
MAX_EXTENSION_METERS = 10.0
RECIPE = 'continue_wall_v1'
WRITE_COMMAND_ALLOWLIST = frozenset({'CreateWalls'})
_GUID = re.compile(r'^[{]?[0-9A-Fa-f-]{32,38}[}]?$')


class WallWriteValidationError(ValueError):
    pass


def _number(value, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise WallWriteValidationError(f'{name} must be numeric')
    value = float(value)
    if not math.isfinite(value):
        raise WallWriteValidationError(f'{name} must be finite')
    return value


def _integer(value, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise WallWriteValidationError(f'{name} must be an integer')
    return int(value)


def _guid(value, name: str) -> str:
    if not isinstance(value, str) or not _GUID.match(value):
        raise WallWriteValidationError(f'{name} must be a GUID string')
    return value


def _xy(value, name: str) -> dict:
    if not isinstance(value, dict) or set(value) != {'x', 'y'}:
        raise WallWriteValidationError(f'{name} must contain only x and y')
    return {'x': _number(value['x'], name + '.x'), 'y': _number(value['y'], name + '.y')}


def _close(a, b) -> bool:
    return abs(float(a) - float(b)) <= TOL


def _same_xy(a: dict, b: dict) -> bool:
    return _close(a['x'], b['x']) and _close(a['y'], b['y'])


def _unwrap(response, command: str) -> dict:
    if not isinstance(response, dict):
        raise RuntimeError(f'{command} returned a non-object response')
    if 'error' in response:
        raise RuntimeError(f'{command} returned error')
    if 'result' not in response:
        return response
    result = response.get('result')
    if not isinstance(result, dict):
        raise RuntimeError(f'{command} returned malformed result')
    payload = result.get('addOnCommandResponse')
    if not isinstance(payload, dict):
        raise RuntimeError(f'{command} returned no addOnCommandResponse')
    if 'error' in payload:
        raise RuntimeError(f'{command} returned add-on error')
    return payload


def _validate_expected_source(value: dict) -> dict:
    required = {
        'floorIndex', 'begCoordinate', 'endCoordinate', 'zCoordinate', 'height',
        'begThickness', 'endThickness', 'offset', 'buildingMaterialGuid',
    }
    if not isinstance(value, dict) or set(value) != required:
        raise WallWriteValidationError(
            'expectedSource fields must be exactly: ' + ','.join(sorted(required)))
    height = _number(value['height'], 'expectedSource.height')
    beg_thickness = _number(value['begThickness'], 'expectedSource.begThickness')
    end_thickness = _number(value['endThickness'], 'expectedSource.endThickness')
    if height <= 0 or beg_thickness <= 0 or end_thickness <= 0:
        raise WallWriteValidationError('expected source dimensions must be positive')
    return {
        'floorIndex': _integer(value['floorIndex'], 'expectedSource.floorIndex'),
        'begCoordinate': _xy(value['begCoordinate'], 'expectedSource.begCoordinate'),
        'endCoordinate': _xy(value['endCoordinate'], 'expectedSource.endCoordinate'),
        'zCoordinate': _number(value['zCoordinate'], 'expectedSource.zCoordinate'),
        'height': height,
        'begThickness': beg_thickness,
        'endThickness': end_thickness,
        'offset': _number(value['offset'], 'expectedSource.offset'),
        'buildingMaterialGuid': _guid(
            value['buildingMaterialGuid'], 'expectedSource.buildingMaterialGuid'),
    }


def validate_job(payload: dict) -> dict:
    required = {
        'recipe', 'instanceId', 'logicalProjectId', 'sourceGuid',
        'sourceEndpoint', 'lengthMeters', 'expectedSource',
    }
    if not isinstance(payload, dict) or set(payload) != required:
        raise WallWriteValidationError(
            'JOB fields must be exactly: ' + ','.join(sorted(required)))
    if payload.get('recipe') != RECIPE:
        raise WallWriteValidationError(f'only recipe={RECIPE} is allowed')
    instance_id = payload.get('instanceId')
    project_id = payload.get('logicalProjectId')
    if not isinstance(instance_id, str) or not instance_id.strip():
        raise WallWriteValidationError('instanceId required')
    if not isinstance(project_id, str) or not project_id.strip():
        raise WallWriteValidationError('logicalProjectId required')
    endpoint = payload.get('sourceEndpoint')
    if endpoint not in ('begin', 'end'):
        raise WallWriteValidationError('sourceEndpoint must be begin or end')
    length = _number(payload.get('lengthMeters'), 'lengthMeters')
    if length <= 0 or length > MAX_EXTENSION_METERS:
        raise WallWriteValidationError(
            f'lengthMeters must be >0 and <= {MAX_EXTENSION_METERS}')
    return {
        'recipe': RECIPE,
        'instanceId': instance_id.strip(),
        'logicalProjectId': project_id.strip(),
        'sourceGuid': _guid(payload.get('sourceGuid'), 'sourceGuid'),
        'sourceEndpoint': endpoint,
        'lengthMeters': length,
        'expectedSource': _validate_expected_source(payload.get('expectedSource')),
    }


def _source_row(payload: dict, source_guid: str) -> dict:
    rows = payload.get('detailsOfElements')
    if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict):
        raise RuntimeError('GetDetailsOfElements must return exactly one source row')
    row = rows[0]
    if row.get('type') != 'Wall':
        raise WallWriteValidationError('sourceGuid is not a Wall')
    details = row.get('details')
    if not isinstance(details, dict):
        raise WallWriteValidationError('source Wall has no readable details')
    if details.get('geometryType') != 'Straight':
        raise WallWriteValidationError('only straight Wall sources are allowed')
    if details.get('structureType') != 'Basic':
        raise WallWriteValidationError('only Basic Wall sources are allowed')
    if details.get('referenceLineLocation') != 'Center':
        raise WallWriteValidationError('only centered reference-line Walls are allowed')
    if not _close(details.get('arcAngle', math.inf), 0.0):
        raise WallWriteValidationError('curved Wall source is not allowed')
    row['_sourceGuid'] = source_guid
    return row


def _fresh_source(row: dict) -> dict:
    d = row['details']
    material = d.get('buildingMaterialId')
    if not isinstance(material, dict):
        raise WallWriteValidationError('source building material is missing')
    result = {
        'floorIndex': _integer(row.get('floorIndex'), 'source.floorIndex'),
        'begCoordinate': _xy(d.get('begCoordinate'), 'source.begCoordinate'),
        'endCoordinate': _xy(d.get('endCoordinate'), 'source.endCoordinate'),
        'zCoordinate': _number(d.get('zCoordinate'), 'source.zCoordinate'),
        'height': _number(d.get('height'), 'source.height'),
        'begThickness': _number(d.get('begThickness'), 'source.begThickness'),
        'endThickness': _number(d.get('endThickness'), 'source.endThickness'),
        'offset': _number(d.get('offset'), 'source.offset'),
        'buildingMaterialGuid': _guid(material.get('guid'), 'source.buildingMaterialGuid'),
    }
    if result['height'] <= 0 or result['begThickness'] <= 0 or result['endThickness'] <= 0:
        raise WallWriteValidationError('source dimensions must be positive')
    if not _close(result['begThickness'], result['endThickness']):
        raise WallWriteValidationError('tapered Wall source is not allowed')
    dx = result['endCoordinate']['x'] - result['begCoordinate']['x']
    dy = result['endCoordinate']['y'] - result['begCoordinate']['y']
    if math.hypot(dx, dy) <= TOL:
        raise WallWriteValidationError('source Wall reference line has zero length')
    return result


def _stale_checks(expected: dict, fresh: dict) -> dict:
    checks = {
        'floorIndex': expected['floorIndex'] == fresh['floorIndex'],
        'begCoordinate': _same_xy(expected['begCoordinate'], fresh['begCoordinate']),
        'endCoordinate': _same_xy(expected['endCoordinate'], fresh['endCoordinate']),
        'zCoordinate': _close(expected['zCoordinate'], fresh['zCoordinate']),
        'height': _close(expected['height'], fresh['height']),
        'begThickness': _close(expected['begThickness'], fresh['begThickness']),
        'endThickness': _close(expected['endThickness'], fresh['endThickness']),
        'offset': _close(expected['offset'], fresh['offset']),
        'buildingMaterialGuid': (
            expected['buildingMaterialGuid'].lower() ==
            fresh['buildingMaterialGuid'].lower()),
    }
    checks['pass'] = all(checks.values())
    return checks


def _plan(fresh: dict, endpoint: str, length: float) -> dict:
    a, b = fresh['begCoordinate'], fresh['endCoordinate']
    dx, dy = b['x'] - a['x'], b['y'] - a['y']
    size = math.hypot(dx, dy)
    ux, uy = dx / size, dy / size
    if endpoint == 'end':
        start = dict(b)
        ex, ey = ux, uy
    else:
        start = dict(a)
        ex, ey = -ux, -uy
    end = {'x': start['x'] + ex * length, 'y': start['y'] + ey * length}
    params = {'wallsData': [{
        'begCoordinate': start,
        'endCoordinate': end,
        'floorIndex': fresh['floorIndex'],
        'zCoordinate': fresh['zCoordinate'],
        'height': fresh['height'],
        'thickness': fresh['begThickness'],
        'offset': fresh['offset'],
        'arcAngle': 0,
        'referenceLineLocation': 'Center',
        'structureType': 'Basic',
        'buildingMaterialId': {'guid': fresh['buildingMaterialGuid']},
    }]}
    return {'start': start, 'end': end, 'createParameters': params}


def _created_guid(payload: dict) -> str:
    rows = payload.get('elements')
    if not isinstance(rows, list):
        raise RuntimeError('CreateWalls returned no elements array')
    values = [
        row.get('elementId', {}).get('guid')
        for row in rows if isinstance(row, dict)
        if isinstance(row.get('elementId'), dict)
    ]
    values = [value for value in values if isinstance(value, str) and value]
    if len(values) != 1:
        raise RuntimeError('CreateWalls did not return exactly one GUID')
    return _guid(values[0], 'createdGuid')


def _readback_rows(payload: dict, source_guid: str, created_guid: str) -> tuple[dict, dict]:
    rows = payload.get('detailsOfElements')
    if not isinstance(rows, list) or len(rows) != 2:
        raise RuntimeError('read-back must return source and created Wall rows')
    source = rows[0] if isinstance(rows[0], dict) else None
    created = rows[1] if isinstance(rows[1], dict) else None
    if source is None or created is None:
        raise RuntimeError('read-back rows must be objects')
    if source.get('type') != 'Wall' or created.get('type') != 'Wall':
        raise RuntimeError('read-back did not return two Walls')
    source['_sourceGuid'] = source_guid
    created['_createdGuid'] = created_guid
    return source, created


def _verify_created(created: dict, source: dict, plan: dict, length: float) -> dict:
    d = created.get('details')
    if not isinstance(d, dict):
        return {'pass': False, 'reason': 'created Wall has no details'}
    try:
        begin = _xy(d.get('begCoordinate'), 'created.begCoordinate')
        end = _xy(d.get('endCoordinate'), 'created.endCoordinate')
        material = d.get('buildingMaterialId') or {}
        actual_length = math.hypot(end['x'] - begin['x'], end['y'] - begin['y'])
        checks = {
            'sourceStillWall': source.get('type') == 'Wall',
            'createdTypeWall': created.get('type') == 'Wall',
            'straight': d.get('geometryType') == 'Straight',
            'basic': d.get('structureType') == 'Basic',
            'referenceLineCenter': d.get('referenceLineLocation') == 'Center',
            'floorIndex': created.get('floorIndex') == source.get('floorIndex'),
            'begin': _same_xy(begin, plan['start']),
            'end': _same_xy(end, plan['end']),
            'length': _close(actual_length, length),
            'height': _close(d.get('height', math.inf), source['details'].get('height', -math.inf)),
            'begThickness': _close(
                d.get('begThickness', math.inf), source['details'].get('begThickness', -math.inf)),
            'endThickness': _close(
                d.get('endThickness', math.inf), source['details'].get('endThickness', -math.inf)),
            'buildingMaterial': (
                str(material.get('guid', '')).lower() ==
                str(source['details'].get('buildingMaterialId', {}).get('guid', '')).lower()),
        }
        checks['pass'] = all(checks.values())
        return {
            'pass': checks['pass'],
            'checks': checks,
            'actual': {
                'begin': begin,
                'end': end,
                'lengthMeters': actual_length,
                'floorIndex': created.get('floorIndex'),
                'height': d.get('height'),
                'begThickness': d.get('begThickness'),
                'endThickness': d.get('endThickness'),
                'buildingMaterialId': material,
            },
        }
    except (WallWriteValidationError, TypeError, ValueError):
        return {'pass': False, 'reason': 'created Wall read-back is malformed'}


class ContinueWallExecutor:
    def __init__(self, transport, binding_reader=None):
        self.transport = transport
        self.binding_reader = binding_reader or getattr(transport, 'binding', None)

    def execute(self, payload: dict) -> dict:
        try:
            job = validate_job(payload)
        except WallWriteValidationError as exc:
            return {
                'status': 'BLOCKED', 'stage': 'VALIDATION', 'reason': str(exc),
                'mutationApplied': False, 'automaticRetry': False,
            }

        try:
            binding = self.binding_reader() if callable(self.binding_reader) else None
        except Exception:
            binding = None
        if not isinstance(binding, dict):
            return {
                'status': 'BLOCKED', 'stage': 'BINDING',
                'reason': 'Archicad binding unavailable',
                'mutationApplied': False, 'automaticRetry': False,
            }
        if (binding.get('instanceId') != job['instanceId']
                or binding.get('logicalProjectId') != job['logicalProjectId']):
            return {
                'status': 'BLOCKED', 'stage': 'BINDING',
                'reason': 'instance/project identity changed',
                'mutationApplied': False, 'automaticRetry': False,
                'observedBinding': {
                    'instanceId': binding.get('instanceId'),
                    'logicalProjectId': binding.get('logicalProjectId'),
                },
            }

        try:
            source_payload = _unwrap(self.transport.call(
                'GetDetailsOfElements',
                {'elements': [{'elementId': {'guid': job['sourceGuid']}}]}),
                'GetDetailsOfElements')
            source_row = _source_row(source_payload, job['sourceGuid'])
            fresh = _fresh_source(source_row)
            stale = _stale_checks(job['expectedSource'], fresh)
            if not stale['pass']:
                return {
                    'status': 'BLOCKED', 'stage': 'STALE_SOURCE',
                    'reason': 'source Wall changed since planning',
                    'sourceGuid': job['sourceGuid'], 'staleChecks': stale,
                    'mutationApplied': False, 'automaticRetry': False,
                }
            plan = _plan(fresh, job['sourceEndpoint'], job['lengthMeters'])
        except (WallWriteValidationError, RuntimeError, KeyError, TypeError, ValueError) as exc:
            return {
                'status': 'BLOCKED', 'stage': 'PRE_WRITE_READ',
                'reason': str(exc), 'sourceGuid': job['sourceGuid'],
                'mutationApplied': False, 'automaticRetry': False,
            }

        try:
            raw_create = self.transport.write_call('CreateWalls', plan['createParameters'])
        except Exception as exc:
            return {
                'status': 'UNKNOWN_OUTCOME', 'stage': 'CREATE_WALLS',
                'reason': type(exc).__name__,
                'sourceGuid': job['sourceGuid'],
                'mutationApplied': None, 'automaticRetry': False,
            }

        try:
            created_guid = _created_guid(_unwrap(raw_create, 'CreateWalls'))
        except Exception as exc:
            return {
                'status': 'UNKNOWN_OUTCOME', 'stage': 'CREATE_WALLS_RESULT',
                'reason': str(exc), 'sourceGuid': job['sourceGuid'],
                'mutationApplied': None, 'automaticRetry': False,
            }

        try:
            readback = _unwrap(self.transport.call(
                'GetDetailsOfElements',
                {'elements': [
                    {'elementId': {'guid': job['sourceGuid']}},
                    {'elementId': {'guid': created_guid}},
                ]}),
                'GetDetailsOfElements')
            source_after, created = _readback_rows(
                readback, job['sourceGuid'], created_guid)
        except Exception as exc:
            return {
                'status': 'UNKNOWN_OUTCOME', 'stage': 'READ_BACK',
                'reason': type(exc).__name__, 'sourceGuid': job['sourceGuid'],
                'createdGuid': created_guid,
                'mutationApplied': True, 'automaticRetry': False,
            }

        verification = _verify_created(
            created, source_after, plan, job['lengthMeters'])
        return {
            'status': 'PASS' if verification.get('pass') else 'BLOCKED',
            'stage': 'VERIFIED' if verification.get('pass') else 'READ_BACK_MISMATCH',
            'recipe': RECIPE,
            'instanceId': job['instanceId'],
            'logicalProjectId': job['logicalProjectId'],
            'sourceGuid': job['sourceGuid'],
            'createdGuid': created_guid,
            'sourceEndpoint': job['sourceEndpoint'],
            'lengthMeters': job['lengthMeters'],
            'expectedGeometry': {'begin': plan['start'], 'end': plan['end']},
            'verification': verification,
            'mutationApplied': True,
            'automaticRetry': False,
        }
