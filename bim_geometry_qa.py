"""Offline geometry-evidence QA for Safe BIM Archicad roof/wall/rafter blockers.

This module is deliberately read-only. It does not call Archicad. Rules 004-007
require a trusted geometry collector because Tapir 1.5.8 GetDetailsOfElements does
not expose Roof type-specific geometry. Missing or partial geometry evidence is
NOT_VERIFIED; explicit collector/transport failure is BLOCKED_BY_TRANSPORT.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

RESULTS = {'PASS', 'FAIL', 'NOT_VERIFIED', 'BLOCKED_BY_TRANSPORT'}
GEOMETRY_RULES = ('BIM-QA-004', 'BIM-QA-005', 'BIM-QA-006', 'BIM-QA-007')
EPS = 1e-9
DEFAULT_GAP_TOLERANCE = 0.001
MAX_GAP_TOLERANCE = 0.01
DEFAULT_PROTRUSION_TOLERANCE = 0.005
MAX_PROTRUSION_TOLERANCE = 0.02
DEFAULT_RAFTER_PLANE_TOLERANCE = 0.005
DEFAULT_RAFTER_ENDPOINT_TOLERANCE = 0.01
MAX_RAFTER_TOLERANCE = 0.02

EXPECTED_ROOF_RELATIONS = {'DISJOINT', 'POINT_TOUCH', 'RIDGE', 'VALLEY', 'HIP', 'SEAM'}
ACTUAL_ROOF_RELATIONS = {'DISJOINT', 'POINT', 'EDGE', 'AREA_OVERLAP', 'VOLUME_OVERLAP', 'CROSSING'}
EDGE_RELATIONS = {'RIDGE', 'VALLEY', 'HIP', 'SEAM'}
COLLISION_RELATIONS = {'AREA_OVERLAP', 'VOLUME_OVERLAP', 'CROSSING'}
WALL_ROOF_OPERATIONS = {'TRIM_TO_ROOF_SHELL', 'SEO', 'NATIVE_ROOF_RELATIONSHIP'}
AXIS_SOURCES = {'BEAM_READBACK_RECONSTRUCTED', 'TRUSTED_GEOMETRY_COLLECTOR'}
PLANE_SOURCES = {'TRUSTED_GEOMETRY_COLLECTOR', 'REFERENCE_MODEL'}


def result(status, reason, guids=()):
    return {'status': status, 'reason': reason, 'guids': sorted(set(guids))}


def text(value):
    return isinstance(value, str) and bool(value.strip())


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _point3(value):
    if not isinstance(value, dict) or not all(number(value.get(axis)) for axis in ('x', 'y', 'z')):
        raise ValueError('Invalid 3D point')
    return (float(value['x']), float(value['y']), float(value['z']))


def _vec_sub(a, b):
    return (a[0]-b[0], a[1]-b[1], a[2]-b[2])


def _norm(v):
    return math.sqrt(sum(component*component for component in v))


def _distance(a, b):
    return _norm(_vec_sub(a, b))


def _dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def _plane_distance(point, plane_point, normal):
    n = _norm(normal)
    if n <= EPS:
        raise ValueError('Zero roof-plane normal')
    return abs(_dot(_vec_sub(point, plane_point), normal)) / n


def _bounded_tolerance(value, default, maximum):
    if value is None:
        return default
    if not number(value) or value < 0 or value > maximum:
        raise ValueError('Invalid or excessive geometry tolerance')
    return float(value)


def _base_inventory(snapshot):
    if not isinstance(snapshot, dict):
        return None, result('NOT_VERIFIED', 'Snapshot is not an object')
    if snapshot.get('geometryTransportError'):
        return None, result('BLOCKED_BY_TRANSPORT', 'Geometry collector/transport failed')
    if not all(text(snapshot.get(k)) for k in ('projectId', 'snapshotId', 'auditScope')):
        return None, result('NOT_VERIFIED', 'Missing project/snapshot/scope binding')
    if snapshot.get('inventoryComplete') is not True or not isinstance(snapshot.get('elements'), list):
        return None, result('NOT_VERIFIED', 'Missing complete scoped element inventory')
    index = {}
    for row in snapshot['elements']:
        if (not isinstance(row, dict) or not text(row.get('guid')) or not text(row.get('type'))
                or row['guid'] in index):
            return None, result('NOT_VERIFIED', 'Malformed or duplicate inventory GUID')
        details = row.get('details', {})
        if not isinstance(details, dict):
            return None, result('NOT_VERIFIED', 'Malformed element details container')
        index[row['guid']] = row
    return index, None


def _pair_key(a, b):
    return tuple(sorted((a, b)))


def _roof_pair_evidence(snapshot, index):
    if snapshot.get('roofTopologyComplete') is not True:
        return None, result('NOT_VERIFIED', 'Roof topology completeness is not demonstrated')
    roof_guids = snapshot.get('roofGuids')
    pairs = snapshot.get('roofPairEvidence')
    if (not isinstance(roof_guids, list) or any(not text(g) for g in roof_guids)
            or len(set(roof_guids)) != len(roof_guids) or not isinstance(pairs, list)
            or snapshot.get('roofPairEvidenceComplete') is not True):
        return None, result('NOT_VERIFIED', 'Missing complete roof GUID/pair evidence')

    uncertain = False
    failed_type = []
    for guid in roof_guids:
        row = index.get(guid)
        if row is None:
            uncertain = True
        elif row.get('type') != 'Roof':
            failed_type.append(guid)
    if failed_type:
        return None, result('FAIL', 'Roof topology references a non-Roof element', failed_type)

    expected_keys = {_pair_key(a, b) for i, a in enumerate(roof_guids) for b in roof_guids[i+1:]}
    pair_map = {}
    try:
        for item in pairs:
            if not isinstance(item, dict):
                raise ValueError
            a, b = item.get('a'), item.get('b')
            if not text(a) or not text(b) or a == b or a not in roof_guids or b not in roof_guids:
                raise ValueError
            key = _pair_key(a, b)
            if key in pair_map:
                raise ValueError
            if item.get('expectedRelation') not in EXPECTED_ROOF_RELATIONS:
                raise ValueError
            if item.get('actualRelation') not in ACTUAL_ROOF_RELATIONS:
                raise ValueError
            gap = item.get('gapDistance')
            if not number(gap) or gap < 0:
                raise ValueError
            _bounded_tolerance(item.get('gapTolerance'), DEFAULT_GAP_TOLERANCE, MAX_GAP_TOLERANCE)
            if item.get('probeComplete') is not True:
                uncertain = True
            pair_map[key] = item
    except (TypeError, ValueError):
        return None, result('NOT_VERIFIED', 'Malformed roof pair geometry evidence')

    if set(pair_map) != expected_keys:
        uncertain = True
    if uncertain:
        return None, result('NOT_VERIFIED', 'Roof pair evidence does not completely cover the scoped roof set')
    return pair_map, None


def roof_collisions(snapshot, index):
    pair_map, issue = _roof_pair_evidence(snapshot, index)
    if issue:
        return issue
    failed = []
    for item in pair_map.values():
        actual = item['actualRelation']
        expected = item['expectedRelation']
        if actual in COLLISION_RELATIONS:
            failed.extend((item['a'], item['b']))
            continue
        if expected == 'DISJOINT' and actual != 'DISJOINT':
            failed.extend((item['a'], item['b']))
        elif expected == 'POINT_TOUCH' and actual not in ('POINT',):
            failed.extend((item['a'], item['b']))
        elif expected in EDGE_RELATIONS and actual == 'POINT':
            failed.extend((item['a'], item['b']))
    if failed:
        return result('FAIL', 'Unintended roof overlap/crossing or wrong contact topology detected', failed)
    return result('PASS', 'No unintended roof collision/contact topology detected in complete pair evidence')


def roof_gaps(snapshot, index):
    pair_map, issue = _roof_pair_evidence(snapshot, index)
    if issue:
        return issue
    failed = []
    for item in pair_map.values():
        expected = item['expectedRelation']
        actual = item['actualRelation']
        tolerance = _bounded_tolerance(item.get('gapTolerance'), DEFAULT_GAP_TOLERANCE, MAX_GAP_TOLERANCE)
        gap = float(item['gapDistance'])
        if expected in EDGE_RELATIONS:
            if actual != 'EDGE' or gap > tolerance:
                failed.extend((item['a'], item['b']))
        elif expected == 'POINT_TOUCH':
            if actual != 'POINT' or gap > tolerance:
                failed.extend((item['a'], item['b']))
        elif expected == 'DISJOINT' and actual == 'DISJOINT':
            continue
    if failed:
        return result('FAIL', 'Expected ridge/valley/hip/seam continuity contains a gap or wrong contact', failed)
    return result('PASS', 'All intended roof adjacencies close within bounded tolerance')


def wall_tops(snapshot, index):
    if snapshot.get('wallRoofRelationsComplete') is not True:
        return result('NOT_VERIFIED', 'Wall-to-roof relation completeness is not demonstrated')
    walls = snapshot.get('roofAdjacentWallGuids')
    relations = snapshot.get('wallRoofRelations')
    if (not isinstance(walls, list) or any(not text(g) for g in walls)
            or len(set(walls)) != len(walls) or not isinstance(relations, list)):
        return result('NOT_VERIFIED', 'Missing roof-adjacent wall inventory or relation evidence')

    seen = set()
    failed = []
    uncertain = False
    for wall_guid in walls:
        row = index.get(wall_guid)
        if row is None:
            uncertain = True
        elif row.get('type') != 'Wall':
            failed.append(wall_guid)

    try:
        for relation in relations:
            if not isinstance(relation, dict) or not text(relation.get('wallGuid')):
                raise ValueError
            wall_guid = relation['wallGuid']
            if wall_guid in seen or wall_guid not in walls:
                raise ValueError
            seen.add(wall_guid)
            roof_guids = relation.get('roofGuids')
            if (not isinstance(roof_guids, list) or not roof_guids or any(not text(g) for g in roof_guids)
                    or len(set(roof_guids)) != len(roof_guids)):
                raise ValueError
            for roof_guid in roof_guids:
                row = index.get(roof_guid)
                if row is None:
                    uncertain = True
                elif row.get('type') != 'Roof':
                    failed.append(roof_guid)
            if relation.get('operationKind') not in WALL_ROOF_OPERATIONS:
                failed.append(wall_guid)
            if relation.get('operationApplied') is not True:
                failed.append(wall_guid)
            if relation.get('steppedFragments') is not False:
                failed.append(wall_guid)
            protrusion = relation.get('maxProtrusion')
            if not number(protrusion) or protrusion < 0:
                uncertain = True
            else:
                tolerance = _bounded_tolerance(
                    relation.get('protrusionTolerance'),
                    DEFAULT_PROTRUSION_TOLERANCE,
                    MAX_PROTRUSION_TOLERANCE,
                )
                if protrusion > tolerance:
                    failed.append(wall_guid)
            if relation.get('geometryVerified') is not True:
                uncertain = True
    except (TypeError, ValueError):
        return result('NOT_VERIFIED', 'Malformed wall-to-roof relation evidence')

    if seen != set(walls):
        uncertain = True
    if failed:
        return result('FAIL', 'Wall top is not proven as a proper native roof-controlled result', failed)
    if uncertain:
        return result('NOT_VERIFIED', 'Incomplete wall-top operation/geometry evidence')
    return result('PASS', 'All roof-adjacent wall tops use verified native roof relationships without protrusion')


def rafter_alignment(snapshot, index):
    if snapshot.get('rafterEvidenceComplete') is not True:
        return result('NOT_VERIFIED', 'Rafter geometry completeness is not demonstrated')
    rafter_guids = snapshot.get('rafterGuids')
    evidence = snapshot.get('rafterEvidence')
    if (not isinstance(rafter_guids, list) or any(not text(g) for g in rafter_guids)
            or len(set(rafter_guids)) != len(rafter_guids) or not isinstance(evidence, list)):
        return result('NOT_VERIFIED', 'Missing rafter inventory or geometry evidence')

    seen = set()
    failed = []
    uncertain = False
    try:
        for item in evidence:
            if not isinstance(item, dict) or not text(item.get('beamGuid')) or not text(item.get('roofGuid')):
                raise ValueError
            beam_guid, roof_guid = item['beamGuid'], item['roofGuid']
            if beam_guid in seen or beam_guid not in rafter_guids:
                raise ValueError
            seen.add(beam_guid)
            beam = index.get(beam_guid)
            roof = index.get(roof_guid)
            if beam is None or roof is None:
                uncertain = True
                continue
            if beam.get('type') != 'Beam':
                failed.append(beam_guid)
                continue
            if roof.get('type') != 'Roof':
                failed.append(roof_guid)
                continue
            if item.get('axisSource') not in AXIS_SOURCES or item.get('roofPlaneSource') not in PLANE_SOURCES:
                uncertain = True
                continue

            a = _point3(item.get('axisStart'))
            b = _point3(item.get('axisEnd'))
            bearing = _point3(item.get('bearingPoint'))
            upper = _point3(item.get('upperTargetPoint'))
            plane_point = _point3(item.get('roofPlanePoint'))
            normal = _point3(item.get('roofPlaneNormal'))
            if _distance(a, b) <= EPS or _norm(normal) <= EPS:
                raise ValueError

            plane_tol = _bounded_tolerance(
                item.get('planeTolerance'),
                DEFAULT_RAFTER_PLANE_TOLERANCE,
                MAX_RAFTER_TOLERANCE,
            )
            endpoint_tol = _bounded_tolerance(
                item.get('endpointTolerance'),
                DEFAULT_RAFTER_ENDPOINT_TOLERANCE,
                MAX_RAFTER_TOLERANCE,
            )
            if _plane_distance(a, plane_point, normal) > plane_tol or _plane_distance(b, plane_point, normal) > plane_tol:
                failed.append(beam_guid)

            direct = (_distance(a, bearing), _distance(b, upper))
            reverse = (_distance(b, bearing), _distance(a, upper))
            best = direct if max(direct) <= max(reverse) else reverse
            if best[0] > endpoint_tol or best[1] > endpoint_tol:
                failed.append(beam_guid)

            details = beam.get('details', {})
            if 'beamShape' in details and details.get('beamShape') != 'Straight':
                failed.append(beam_guid)
            if 'arcAngle' in details and (not number(details.get('arcAngle')) or abs(details['arcAngle']) > EPS):
                failed.append(beam_guid)
    except (TypeError, ValueError):
        return result('NOT_VERIFIED', 'Malformed rafter/roof-plane geometry evidence')

    if seen != set(rafter_guids):
        uncertain = True
    if failed:
        return result('FAIL', 'One or more rafters do not align with accepted roof/bearing/upper-target geometry', failed)
    if uncertain:
        return result('NOT_VERIFIED', 'Incomplete rafter/roof-plane geometry evidence')
    return result('PASS', 'All scoped rafter axes align with roof planes and required endpoints')


def audit_geometry_snapshot(snapshot):
    index, issue = _base_inventory(snapshot)
    if issue:
        return {
            'projectId': snapshot.get('projectId') if isinstance(snapshot, dict) else None,
            'snapshotId': snapshot.get('snapshotId') if isinstance(snapshot, dict) else None,
            'auditScope': snapshot.get('auditScope') if isinstance(snapshot, dict) else None,
            'status': issue['status'],
            'rules': {rule_id: issue for rule_id in GEOMETRY_RULES},
        }

    outcomes = {
        'BIM-QA-004': roof_collisions(snapshot, index),
        'BIM-QA-005': roof_gaps(snapshot, index),
        'BIM-QA-006': wall_tops(snapshot, index),
        'BIM-QA-007': rafter_alignment(snapshot, index),
    }
    statuses = [value['status'] for value in outcomes.values()]
    status = 'PASS'
    for candidate in ('FAIL', 'BLOCKED_BY_TRANSPORT', 'NOT_VERIFIED'):
        if candidate in statuses:
            status = candidate
            break
    return {
        'projectId': snapshot.get('projectId'),
        'snapshotId': snapshot.get('snapshotId'),
        'auditScope': snapshot.get('auditScope'),
        'status': status,
        'rules': outcomes,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', required=True)
    parser.add_argument('--output')
    args = parser.parse_args()
    try:
        snapshot = json.loads(Path(args.snapshot).read_text(encoding='utf-8'))
        report = audit_geometry_snapshot(snapshot)
    except (OSError, ValueError, TypeError) as exc:
        report = {'status': 'NOT_VERIFIED', 'reason': f'Cannot read geometry audit input: {exc}'}
    rendered = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(rendered + '\n', encoding='utf-8')
    print(rendered)
    return 0 if report.get('status') == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
