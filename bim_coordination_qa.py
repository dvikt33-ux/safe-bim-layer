"""Fail-closed offline coordination and dimensional QA for Safe BIM Archicad.

Rules BIM-QA-012..017 verify roof reach, wall junction continuity, vertical
load-bearing continuity, wall/opening conflicts, opening clearances and masonry
module fit.

No regulatory or project dimension is hard-coded here. Every threshold/module
must resolve through a VERIFIED ruleRegistry entry carried by the trusted
collector snapshot. Missing or unverified rule data => NOT_VERIFIED with
reasonCode DATA_MISSING, never PASS.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

RESULTS = {'PASS', 'FAIL', 'NOT_VERIFIED', 'BLOCKED_BY_TRANSPORT'}
COORDINATION_RULES = (
    'BIM-QA-012',
    'BIM-QA-013',
    'BIM-QA-014',
    'BIM-QA-015',
    'BIM-QA-016',
    'BIM-QA-017',
)
CHECKER_ID = 'SAFE_BIM_COORDINATION_QA_V1'
EPS = 1e-9
SOURCE_KINDS = {'NORMATIVE', 'PROJECT', 'REFERENCE'}
JUNCTION_KINDS = {'T', 'L', 'X', 'END', 'COLLINEAR'}
OPENING_TYPES = {'Window', 'Door'}
CLEARANCE_KINDS = {
    'WINDOW_TO_CORNER',
    'DOOR_TO_CORNER',
    'DOOR_TO_WALL',
    'OPENING_TO_ADJACENT_WALL',
    'BETWEEN_OPENINGS',
    'PIER_WIDTH',
    'JAMB_WIDTH',
}
MASONRY_DIMENSION_KINDS = {
    'PIER_WIDTH',
    'JAMB_OFFSET',
    'OPENING_OFFSET',
    'BETWEEN_OPENINGS',
    'RETURN_LENGTH',
    'WALL_RUN',
}
SUPPORT_KINDS = {'WALL', 'BEAM', 'COLUMN', 'FOUNDATION', 'TRANSFER_STRUCTURE'}


class DataMissing(ValueError):
    pass


def result(status, reason, guids=(), reason_code=None):
    payload = {
        'status': status,
        'reason': reason,
        'guids': sorted(set(guids)),
    }
    if reason_code:
        payload['reasonCode'] = reason_code
    return payload


def text(value):
    return isinstance(value, str) and bool(value.strip())


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _base_inventory(snapshot):
    if not isinstance(snapshot, dict):
        return None, result('NOT_VERIFIED', 'Snapshot is not an object')
    if snapshot.get('coordinationTransportError'):
        return None, result(
            'BLOCKED_BY_TRANSPORT',
            'Coordination geometry collector/transport failed',
        )
    if not all(text(snapshot.get(k)) for k in ('projectId', 'snapshotId', 'auditScope')):
        return None, result('NOT_VERIFIED', 'Missing project/snapshot/scope binding')
    if snapshot.get('inventoryComplete') is not True or not isinstance(snapshot.get('elements'), list):
        return None, result('NOT_VERIFIED', 'Missing complete scoped element inventory')
    index = {}
    for row in snapshot['elements']:
        if (
            not isinstance(row, dict)
            or not text(row.get('guid'))
            or not text(row.get('type'))
            or row['guid'] in index
        ):
            return None, result('NOT_VERIFIED', 'Malformed or duplicate inventory GUID')
        if not isinstance(row.get('details', {}), dict):
            return None, result('NOT_VERIFIED', 'Malformed element details container')
        index[row['guid']] = row
    return index, None


def _rule_registry(snapshot):
    if snapshot.get('ruleRegistryComplete') is not True:
        raise DataMissing('Rule Registry completeness is not demonstrated')
    entries = snapshot.get('ruleRegistry')
    if not isinstance(entries, list):
        raise DataMissing('Rule Registry is missing')
    registry = {}
    for entry in entries:
        if not isinstance(entry, dict) or not text(entry.get('id')) or entry['id'] in registry:
            raise DataMissing('Rule Registry contains malformed or duplicate entries')
        if entry.get('status') != 'VERIFIED':
            raise DataMissing(f"Rule {entry.get('id')} is not VERIFIED")
        kind = entry.get('sourceKind')
        if kind not in SOURCE_KINDS or not text(entry.get('verifiedAt')):
            raise DataMissing(f"Rule {entry['id']} has incomplete provenance")
        if kind == 'NORMATIVE':
            if not all(text(entry.get(k)) for k in ('document', 'edition', 'clause')):
                raise DataMissing(f"Normative rule {entry['id']} lacks document/edition/clause")
        else:
            if not text(entry.get('basis')) or entry.get('approved') is not True:
                raise DataMissing(f"Project/reference rule {entry['id']} lacks approved basis")
        if not isinstance(entry.get('parameters'), dict):
            raise DataMissing(f"Rule {entry['id']} has no parameters")
        registry[entry['id']] = entry
    return registry


def _rule_entry(registry, rule_id):
    if not text(rule_id) or rule_id not in registry:
        raise DataMissing(f'Rule Registry entry not found: {rule_id!r}')
    return registry[rule_id]


def _rule_number(registry, rule_id, parameter):
    entry = _rule_entry(registry, rule_id)
    value = entry['parameters'].get(parameter)
    if not number(value):
        raise DataMissing(f'Rule {rule_id} parameter {parameter} is missing/non-numeric')
    return float(value)


def _rule_number_list(registry, rule_id, parameter):
    entry = _rule_entry(registry, rule_id)
    values = entry['parameters'].get(parameter)
    if not isinstance(values, list) or not values or any(not number(v) for v in values):
        raise DataMissing(f'Rule {rule_id} parameter {parameter} is missing/non-numeric list')
    return [float(v) for v in values]


def _not_verified_data_missing(message):
    return result('NOT_VERIFIED', str(message), reason_code='DATA_MISSING')


def roof_to_wall_coverage(snapshot, index, registry):
    if snapshot.get('roofCoverageComplete') is not True:
        return result('NOT_VERIFIED', 'Roof-to-wall coverage completeness is not demonstrated')
    evidence = snapshot.get('roofCoverageEvidence')
    if not isinstance(evidence, list):
        return result('NOT_VERIFIED', 'Missing roof-to-wall coverage evidence')
    failed, uncertain, seen = [], False, set()
    try:
        for item in evidence:
            if (
                not isinstance(item, dict)
                or not text(item.get('id'))
                or item['id'] in seen
                or not text(item.get('wallGuid'))
                or not text(item.get('roofGuid'))
            ):
                uncertain = True
                continue
            seen.add(item['id'])
            wall = index.get(item['wallGuid'])
            roof = index.get(item['roofGuid'])
            if wall is None or roof is None:
                uncertain = True
                continue
            if wall.get('type') != 'Wall':
                failed.append(item['wallGuid'])
                continue
            if roof.get('type') != 'Roof':
                failed.append(item['roofGuid'])
                continue
            if item.get('probeSource') != 'TRUSTED_GEOMETRY_COLLECTOR' or item.get('probeComplete') is not True:
                uncertain = True
                continue
            actual = item.get('actualOverhang')
            if not number(actual):
                uncertain = True
                continue
            minimum = _rule_number(registry, item.get('ruleId'), item.get('parameter', 'minimumOverhang'))
            if float(actual) + EPS < minimum:
                failed.extend((item['wallGuid'], item['roofGuid']))
    except DataMissing as exc:
        return _not_verified_data_missing(exc)
    if failed:
        return result('FAIL', 'Roof does not reach the required wall line/overhang', failed)
    if uncertain:
        return result('NOT_VERIFIED', 'Incomplete roof-to-wall coverage evidence')
    return result('PASS', 'Roof reach/overhang satisfies all verified design-rule requirements')


def wall_connectivity(snapshot, index, registry):
    if snapshot.get('wallJunctionsComplete') is not True:
        return result('NOT_VERIFIED', 'Wall junction completeness is not demonstrated')
    evidence = snapshot.get('wallJunctions')
    if not isinstance(evidence, list):
        return result('NOT_VERIFIED', 'Missing wall junction evidence')
    failed, uncertain, seen = [], False, set()
    try:
        for item in evidence:
            if (
                not isinstance(item, dict)
                or not text(item.get('id'))
                or item['id'] in seen
                or not text(item.get('a'))
                or not text(item.get('b'))
                or item.get('expectedKind') not in JUNCTION_KINDS
            ):
                uncertain = True
                continue
            seen.add(item['id'])
            a, b = index.get(item['a']), index.get(item['b'])
            if a is None or b is None:
                uncertain = True
                continue
            if a.get('type') != 'Wall' or b.get('type') != 'Wall':
                failed.extend((item['a'], item['b']))
                continue
            gap = item.get('gapDistance')
            if not number(gap) or gap < 0 or item.get('probeComplete') is not True:
                uncertain = True
                continue
            max_gap = _rule_number(registry, item.get('ruleId'), item.get('parameter', 'maxGap'))
            if item.get('actualConnected') is not True or float(gap) > max_gap + EPS:
                failed.extend((item['a'], item['b']))
    except DataMissing as exc:
        return _not_verified_data_missing(exc)
    if failed:
        return result('FAIL', 'Required wall junction contains a gap or is not actually connected', failed)
    if uncertain:
        return result('NOT_VERIFIED', 'Incomplete wall-junction evidence')
    return result('PASS', 'All intended wall junctions are connected within verified tolerances')


def vertical_loadbearing_continuity(snapshot, index, registry):
    if snapshot.get('loadBearingSupportComplete') is not True:
        return result('NOT_VERIFIED', 'Load-bearing support completeness is not demonstrated')
    evidence = snapshot.get('loadBearingSupportEvidence')
    if not isinstance(evidence, list):
        return result('NOT_VERIFIED', 'Missing load-bearing support evidence')
    failed, uncertain, seen = [], False, set()
    try:
        for item in evidence:
            if (
                not isinstance(item, dict)
                or not text(item.get('upperWallGuid'))
                or item['upperWallGuid'] in seen
                or item.get('supportKind') not in SUPPORT_KINDS
            ):
                uncertain = True
                continue
            seen.add(item['upperWallGuid'])
            upper = index.get(item['upperWallGuid'])
            if upper is None:
                uncertain = True
                continue
            if upper.get('type') != 'Wall':
                failed.append(item['upperWallGuid'])
                continue
            if item.get('probeComplete') is not True:
                uncertain = True
                continue

            support_kind = item['supportKind']
            support_guid = item.get('supportGuid')
            if support_kind != 'FOUNDATION':
                if not text(support_guid) or support_guid not in index:
                    uncertain = True
                    continue
                support = index[support_guid]
                expected_type = {'WALL': 'Wall', 'BEAM': 'Beam', 'COLUMN': 'Column'}.get(support_kind)
                if expected_type and support.get('type') != expected_type:
                    failed.extend((item['upperWallGuid'], support_guid))
                    continue
                if support_kind == 'TRANSFER_STRUCTURE':
                    if not isinstance(item.get('transferException'), dict):
                        failed.append(item['upperWallGuid'])
                        continue
                    exc = item['transferException']
                    if (
                        exc.get('approved') is not True
                        or not text(exc.get('reason'))
                        or not text(exc.get('reviewedBy'))
                    ):
                        failed.append(item['upperWallGuid'])
                        continue

            overlap = item.get('supportRatio')
            offset = item.get('horizontalOffset')
            if not number(overlap) or not number(offset) or overlap < 0 or offset < 0:
                uncertain = True
                continue
            min_ratio = _rule_number(registry, item.get('ruleId'), item.get('ratioParameter', 'minSupportRatio'))
            max_offset = _rule_number(registry, item.get('ruleId'), item.get('offsetParameter', 'maxHorizontalOffset'))
            if float(overlap) + EPS < min_ratio or float(offset) > max_offset + EPS:
                failed.append(item['upperWallGuid'])
                if text(support_guid):
                    failed.append(support_guid)
    except DataMissing as exc:
        return _not_verified_data_missing(exc)
    if failed:
        return result('FAIL', 'Load-bearing wall lacks verified vertical support continuity', failed)
    if uncertain:
        return result('NOT_VERIFIED', 'Incomplete load-bearing support evidence')
    return result('PASS', 'All scoped load-bearing walls have verified support continuity')


def wall_opening_conflict(snapshot, index, registry):
    if snapshot.get('wallOpeningConflictComplete') is not True:
        return result('NOT_VERIFIED', 'Wall/opening conflict coverage is not demonstrated')
    evidence = snapshot.get('wallOpeningConflictEvidence')
    if not isinstance(evidence, list):
        return result('NOT_VERIFIED', 'Missing wall/opening conflict evidence')
    failed, uncertain, seen = [], False, set()
    try:
        for item in evidence:
            if (
                not isinstance(item, dict)
                or not text(item.get('id'))
                or item['id'] in seen
                or not text(item.get('approachWallGuid'))
                or not text(item.get('openingGuid'))
            ):
                uncertain = True
                continue
            seen.add(item['id'])
            wall = index.get(item['approachWallGuid'])
            opening = index.get(item['openingGuid'])
            if wall is None or opening is None:
                uncertain = True
                continue
            if wall.get('type') != 'Wall' or opening.get('type') not in OPENING_TYPES:
                failed.extend((item['approachWallGuid'], item['openingGuid']))
                continue
            distance = item.get('clearDistance')
            if not number(distance) or distance < 0 or item.get('probeComplete') is not True:
                uncertain = True
                continue
            minimum = _rule_number(registry, item.get('ruleId'), item.get('parameter', 'minClearance'))
            if item.get('intersectsOpening') is True or float(distance) + EPS < minimum:
                failed.extend((item['approachWallGuid'], item['openingGuid']))
    except DataMissing as exc:
        return _not_verified_data_missing(exc)
    if failed:
        return result('FAIL', 'Wall/partition conflicts with an opening or violates required clearance', failed)
    if uncertain:
        return result('NOT_VERIFIED', 'Incomplete wall/opening conflict evidence')
    return result('PASS', 'No checked wall/partition enters an opening zone and all clearances comply')


def opening_edge_clearance(snapshot, index, registry):
    if snapshot.get('openingClearanceComplete') is not True:
        return result('NOT_VERIFIED', 'Opening-clearance completeness is not demonstrated')
    evidence = snapshot.get('openingClearanceEvidence')
    if not isinstance(evidence, list):
        return result('NOT_VERIFIED', 'Missing opening-clearance evidence')
    failed, uncertain, seen = [], False, set()
    try:
        for item in evidence:
            if (
                not isinstance(item, dict)
                or not text(item.get('id'))
                or item['id'] in seen
                or not text(item.get('openingGuid'))
                or item.get('relationKind') not in CLEARANCE_KINDS
            ):
                uncertain = True
                continue
            seen.add(item['id'])
            opening = index.get(item['openingGuid'])
            if opening is None:
                uncertain = True
                continue
            if opening.get('type') not in OPENING_TYPES:
                failed.append(item['openingGuid'])
                continue
            measured = item.get('measuredDistance')
            if not number(measured) or measured < 0 or item.get('probeComplete') is not True:
                uncertain = True
                continue
            parameter = item.get('parameter')
            if not text(parameter):
                uncertain = True
                continue
            minimum = _rule_number(registry, item.get('ruleId'), parameter)
            if float(measured) + EPS < minimum:
                failed.append(item['openingGuid'])
                neighbor = item.get('neighborGuid')
                if text(neighbor):
                    failed.append(neighbor)
    except DataMissing as exc:
        return _not_verified_data_missing(exc)
    if failed:
        return result('FAIL', 'Opening edge/corner/pier clearance violates a verified rule', failed)
    if uncertain:
        return result('NOT_VERIFIED', 'Incomplete opening-clearance evidence')
    return result('PASS', 'All measured opening/corner/pier clearances satisfy verified rules')


def _distance_to_module(value, step, residues):
    value = float(value)
    step = float(step)
    if step <= 0:
        raise DataMissing('Masonry moduleStep must be positive')
    best = math.inf
    for residue in residues:
        residue = float(residue)
        k = round((value - residue) / step)
        best = min(best, abs(value - (residue + k * step)))
    return best


def masonry_module_fit(snapshot, index, registry):
    if snapshot.get('masonryModuleComplete') is not True:
        return result('NOT_VERIFIED', 'Masonry-module completeness is not demonstrated')
    evidence = snapshot.get('masonryModuleEvidence')
    if not isinstance(evidence, list):
        return result('NOT_VERIFIED', 'Missing masonry-module evidence')
    failed, uncertain, seen = [], False, set()
    try:
        for item in evidence:
            if (
                not isinstance(item, dict)
                or not text(item.get('id'))
                or item['id'] in seen
                or not text(item.get('wallGuid'))
                or item.get('dimensionKind') not in MASONRY_DIMENSION_KINDS
            ):
                uncertain = True
                continue
            seen.add(item['id'])
            wall = index.get(item['wallGuid'])
            if wall is None:
                uncertain = True
                continue
            if wall.get('type') != 'Wall':
                failed.append(item['wallGuid'])
                continue
            measured = item.get('measuredValue')
            if not number(measured) or measured < 0 or item.get('probeComplete') is not True:
                uncertain = True
                continue
            rule_id = item.get('ruleId')
            step = _rule_number(registry, rule_id, item.get('stepParameter', 'moduleStep'))
            tolerance = _rule_number(registry, rule_id, item.get('toleranceParameter', 'moduleTolerance'))
            residues = _rule_number_list(registry, rule_id, item.get('residuesParameter', 'allowedResidues'))
            if tolerance < 0 or step <= 0:
                raise DataMissing(f'Rule {rule_id} contains invalid module parameters')
            if any(r < -EPS or r >= step + EPS for r in residues):
                raise DataMissing(f'Rule {rule_id} has an allowedResidue outside [0, moduleStep)')
            if _distance_to_module(float(measured), step, residues) > tolerance + EPS:
                failed.append(item['wallGuid'])
                related = item.get('openingGuid')
                if text(related):
                    failed.append(related)
    except DataMissing as exc:
        return _not_verified_data_missing(exc)
    if failed:
        return result('FAIL', 'Masonry dimensions/offsets do not fit the verified modular coordination rule', failed)
    if uncertain:
        return result('NOT_VERIFIED', 'Incomplete masonry-module evidence')
    return result('PASS', 'All scoped masonry dimensions fit verified modular coordination rules')


def audit_coordination_snapshot(snapshot):
    index, issue = _base_inventory(snapshot)
    base = {
        'checkerId': CHECKER_ID,
        'projectId': snapshot.get('projectId') if isinstance(snapshot, dict) else None,
        'snapshotId': snapshot.get('snapshotId') if isinstance(snapshot, dict) else None,
        'auditScope': snapshot.get('auditScope') if isinstance(snapshot, dict) else None,
    }
    if issue:
        rules = {rule_id: issue for rule_id in COORDINATION_RULES}
        return {**base, 'status': issue['status'], 'rules': rules}

    try:
        registry = _rule_registry(snapshot)
    except DataMissing as exc:
        issue = _not_verified_data_missing(exc)
        return {**base, 'status': issue['status'], 'rules': {r: issue for r in COORDINATION_RULES}}

    rules = {
        'BIM-QA-012': roof_to_wall_coverage(snapshot, index, registry),
        'BIM-QA-013': wall_connectivity(snapshot, index, registry),
        'BIM-QA-014': vertical_loadbearing_continuity(snapshot, index, registry),
        'BIM-QA-015': wall_opening_conflict(snapshot, index, registry),
        'BIM-QA-016': opening_edge_clearance(snapshot, index, registry),
        'BIM-QA-017': masonry_module_fit(snapshot, index, registry),
    }
    statuses = [value['status'] for value in rules.values()]
    status = 'PASS'
    for candidate in ('FAIL', 'BLOCKED_BY_TRANSPORT', 'NOT_VERIFIED'):
        if candidate in statuses:
            status = candidate
            break
    return {**base, 'status': status, 'rules': rules}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', required=True)
    parser.add_argument('--output')
    args = parser.parse_args()
    try:
        snapshot = json.loads(Path(args.snapshot).read_text(encoding='utf-8'))
        report = audit_coordination_snapshot(snapshot)
    except (OSError, ValueError, TypeError) as exc:
        report = {
            'checkerId': CHECKER_ID,
            'status': 'NOT_VERIFIED',
            'reason': f'Cannot read coordination audit input: {exc}',
        }
    rendered = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(rendered + '\n', encoding='utf-8')
    print(rendered)
    return 0 if report.get('status') == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
