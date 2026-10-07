"""Read-only BIM blocker audits. No Archicad calls and no mutation commands.

Completeness and intent are evidence contracts, never inferred from an empty
response or from a successful create operation. See docs/BIM_QA.md.
"""
from __future__ import annotations

import argparse
import copy
import json
import math
from pathlib import Path

RULES_PATH = Path(__file__).parent / 'docs' / 'archicad_modeling_qa_rules.v1.json'
IMPLEMENTED = {
    'BIM-QA-001',
    'BIM-QA-002',
    'BIM-QA-003',
    'BIM-QA-008',
    'BIM-QA-009',
    'BIM-QA-010',
    'BIM-QA-011',
}
RESULTS = {'PASS', 'FAIL', 'NOT_VERIFIED', 'BLOCKED_BY_TRANSPORT'}
EPS = 1e-6  # metres; fixed, not caller-controlled

FRAGMENTATION_EXCEPTION_CATEGORIES = {
    'construction',
    'geometry',
    'renovation',
    'material',
    'story',
    'ownership',
    'api_limitation',
}
ECONOMY_STRATEGIES = {
    'NATIVE_ELEMENT',
    'HOSTED_NATIVE',
    'NATIVE_OPERATION',
    'COMPLEX_PROFILE',
    'GDL',
    'MINIMAL_MULTI_ELEMENT',
}


def result(status, reason, guids=()):
    return {'status': status, 'reason': reason, 'guids': sorted(set(guids))}


def text(value):
    return isinstance(value, str) and bool(value.strip())


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def integer(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _approved_fragmentation_exception(value):
    if not isinstance(value, dict):
        return False
    if value.get('category') not in FRAGMENTATION_EXCEPTION_CATEGORIES:
        return False
    if not text(value.get('reason')) or not text(value.get('reviewedBy')) or value.get('approved') is not True:
        return False
    # An API/transport limitation is never an automatic licence to degrade BIM
    # semantics. A human-reviewed fallback decision is required explicitly.
    if value.get('category') == 'api_limitation' and value.get('fallbackReviewed') is not True:
        return False
    return True


def snapshot_from_readback(response, requested_guids, metadata):
    """Adapt a captured Tapir envelope or SafeBIMLayer operation result.

    Tapir's details `id` is an element label, NOT a GUID. Correspondence uses
    the retained GetDetailsOfElements request order, with exact cardinality.
    Metadata carries the independently captured inventory/intent/trace evidence.
    """
    snapshot = dict(metadata)
    snapshot['elements'] = []
    try:
        if not isinstance(response, dict) or response.get('success') is False or response.get('succeeded') is False or 'error' in response:
            raise ValueError('Tapir error')
        if 'readbackResponse' in response:
            if response.get('guids') != requested_guids:
                raise ValueError('Safe BIM GUID list differs from retained request')
            response = response['readbackResponse']
        if response.get('success') is False or response.get('succeeded') is False or 'error' in response:
            raise ValueError('Tapir error')
        envelope = response.get('result', {'addOnCommandResponse': response})
        if envelope.get('success') is False or envelope.get('succeeded') is False or 'error' in envelope:
            raise ValueError('Tapir result error')
        payload = envelope['addOnCommandResponse']
        if 'error' in payload or payload.get('success') is False or payload.get('succeeded') is False:
            raise ValueError('Tapir command error')
        rows = payload['detailsOfElements']
        if (not isinstance(rows, list) or len(rows) != len(requested_guids)
                or any(not text(g) for g in requested_guids)
                or len(set(requested_guids)) != len(requested_guids)):
            raise ValueError('Missing, duplicate or unmatched read-back rows')
        for guid, row in zip(requested_guids, rows):
            if not isinstance(row, dict) or 'error' in row or not text(row.get('type')) or not isinstance(row.get('details'), dict):
                raise ValueError('Malformed element details')
            if row.get('elementId', {}).get('guid', guid) != guid:
                raise ValueError('Read-back GUID mismatch')
            snapshot['elements'].append(dict(row, guid=guid))
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        snapshot['elements'] = []
        snapshot['transportError'] = str(exc)
    return snapshot


def attach_story_inventory(snapshot, response):
    """Attach and validate the retained full Tapir GetStories response."""
    out = copy.deepcopy(snapshot) if isinstance(snapshot, dict) else {}
    out['storiesComplete'] = False
    try:
        if not isinstance(response, dict) or response.get('success') is False or response.get('succeeded') is False or 'error' in response:
            raise ValueError('Story transport error')
        envelope = response.get('result', {'addOnCommandResponse': response})
        if not isinstance(envelope, dict) or envelope.get('success') is False or envelope.get('succeeded') is False or 'error' in envelope:
            raise ValueError('Story result error')
        payload = envelope['addOnCommandResponse']
        if not isinstance(payload, dict) or payload.get('success') is False or payload.get('succeeded') is False or 'error' in payload:
            raise ValueError('Story command error')
        stories = payload['stories']
        first, last = payload['firstStory'], payload['lastStory']
        if (not isinstance(stories, list) or not integer(first) or not integer(last) or first > last):
            raise ValueError('Malformed story inventory')
        indices, levels = [], []
        for story in stories:
            if (not isinstance(story, dict) or not integer(story.get('index'))
                    or not number(story.get('level')) or not text(story.get('name'))):
                raise ValueError('Malformed story row')
            indices.append(story['index'])
            levels.append(story['level'])
        if sorted(indices) != list(range(first, last + 1)) or len(set(levels)) != len(levels):
            raise ValueError('Incomplete, duplicate or inconsistent story range')
        out['stories'] = stories
        out['storiesComplete'] = True
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        out['storyTransportError'] = str(exc)
    return out


def attach_bounding_boxes(snapshot, response, requested_guids):
    """Attach Tapir Get3DBoundingBoxes rows by exact retained request order."""
    out = copy.deepcopy(snapshot) if isinstance(snapshot, dict) else {}
    out['boundingBoxesComplete'] = False
    try:
        if not isinstance(response, dict) or response.get('success') is False or response.get('succeeded') is False or 'error' in response:
            raise ValueError('Bounding-box transport error')
        envelope = response.get('result', {'addOnCommandResponse': response})
        if not isinstance(envelope, dict) or envelope.get('success') is False or envelope.get('succeeded') is False or 'error' in envelope:
            raise ValueError('Bounding-box result error')
        payload = envelope['addOnCommandResponse']
        if not isinstance(payload, dict) or payload.get('success') is False or payload.get('succeeded') is False or 'error' in payload:
            raise ValueError('Bounding-box command error')
        boxes, guids = payload['boundingBoxes3D'], list(requested_guids)
        rows = out.get('elements')
        if (not isinstance(boxes, list) or len(boxes) != len(guids) or not isinstance(rows, list)
                or any(not text(g) for g in guids) or len(set(guids)) != len(guids)):
            raise ValueError('Bounding-box request/response cardinality or GUID mismatch')
        index = {r.get('guid'): r for r in rows if isinstance(r, dict)}
        if len(index) != len(rows) or not set(guids).issubset(index):
            raise ValueError('Bounding-box GUID is absent from element read-back')
        for guid, item in zip(guids, boxes):
            if not isinstance(item, dict) or 'error' in item or not isinstance(item.get('boundingBox3D'), dict):
                raise ValueError('Bounding-box row is missing or contains an error')
            box = item['boundingBox3D']
            keys = ('xMin', 'yMin', 'zMin', 'xMax', 'yMax', 'zMax')
            if not all(number(box.get(k)) for k in keys):
                raise ValueError('Malformed bounding box')
            if any(box[a] > box[b] for a, b in (('xMin','xMax'), ('yMin','yMax'), ('zMin','zMax'))):
                raise ValueError('Inverted bounding box')
            index[guid]['boundingBox3D'] = dict(box)
        out['boundingBoxesComplete'] = True
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        out['boundingBoxTransportError'] = str(exc)
    return out


def _inventory(s):
    if s.get('transportError'):
        return None, result('BLOCKED_BY_TRANSPORT', 'Read-back transport failed or returned invalid data')
    if not all(text(s.get(k)) for k in ('projectId', 'snapshotId', 'auditScope')):
        return None, result('NOT_VERIFIED', 'Missing project/snapshot/scope binding')
    rows = s.get('elements')
    if not isinstance(rows, list):
        return None, result('NOT_VERIFIED', 'Missing element inventory')
    index = {}
    for row in rows:
        if (not isinstance(row, dict) or not text(row.get('guid')) or not text(row.get('type'))
                or not isinstance(row.get('details'), dict) or row['guid'] in index):
            return None, result('NOT_VERIFIED', 'Malformed or duplicate inventory GUID')
        index[row['guid']] = row
    if s.get('inventoryComplete') is not True:
        return index, result('NOT_VERIFIED', 'Inventory completeness has not been demonstrated')
    return index, None


def _native(s, index, kind):
    intents = s.get('openingIntents')
    if not isinstance(intents, list):
        return result('NOT_VERIFIED', 'Missing intended opening inventory')
    uncertain = s.get('openingIntentsComplete') is not True
    failed = []
    seen = set()
    for intent in intents:
        if (not isinstance(intent, dict) or intent.get('kind') not in ('Window', 'Door')
                or not text(intent.get('guid')) or not text(intent.get('hostGuid'))):
            uncertain = True
            continue
        if intent['guid'] in seen:
            uncertain = True
        seen.add(intent['guid'])
        if intent['kind'] != kind:
            continue
        row = index.get(intent['guid'])
        if row is None:
            uncertain = True
            continue
        if row['type'] != kind:
            failed.append(row['guid'])
            continue
        owner = row['details'].get('ownerElementId')
        owner_guid = owner.get('guid') if isinstance(owner, dict) else None
        if not text(owner_guid):
            uncertain = True
            continue
        if owner_guid != intent['hostGuid']:
            failed.append(row['guid'])
            continue
        host = index.get(owner_guid)
        if host is None:
            uncertain = True
        elif host['type'] != 'Wall':
            failed.append(row['guid'])
        owner_type = row['details'].get('ownerElementType')
        if owner_type is not None and owner_type != 'Wall':
            failed.append(row['guid'])
    if any(row['type'] == kind and guid not in seen for guid, row in index.items()):
        uncertain = True
    if failed:
        return result('FAIL', f'Intended {kind} is not native or has an incorrect wall host', failed)
    if uncertain:
        return result('NOT_VERIFIED', f'Incomplete {kind} intent/type/host evidence')
    return result('PASS', f'All intended {kind} elements have native type and intended Wall hosts')


def _point(p):
    if not isinstance(p, dict) or not all(number(p.get(k)) for k in ('x', 'y')):
        raise ValueError('Invalid coordinate')
    return p['x'], p['y']


def _walls(s, index):
    systems = s.get('wallSystems')
    if not isinstance(systems, list) or s.get('wallSystemsComplete') is not True:
        return result('NOT_VERIFIED', 'Missing complete intended continuous-wall systems')
    if not isinstance(s.get('openingIntents'), list) or s.get('openingIntentsComplete') is not True:
        return result('NOT_VERIFIED', 'Opening inventory required to audit wall construction')
    covered, failed, uncertain = set(), [], False
    system_ids = set()
    try:
        for system in systems:
            if not isinstance(system, dict) or not text(system.get('id')) or system['id'] in system_ids:
                raise ValueError('Invalid system identity')
            system_ids.add(system['id'])
            guids = system['guids']
            if not isinstance(guids, list) or not guids or any(not text(g) for g in guids):
                raise ValueError('Invalid wall GUIDs')
            if len(set(guids)) != len(guids) or covered.intersection(guids):
                raise ValueError('Wall belongs to multiple systems')
            covered.update(guids)
            a, b = _point(system['begCoordinate']), _point(system['endCoordinate'])
            dx, dy = b[0]-a[0], b[1]-a[1]
            length = math.hypot(dx, dy)
            if not number(length) or length <= EPS or not all(number(system.get(k)) for k in ('floorIndex', 'zCoordinate', 'height')) or system['height'] <= 0:
                raise ValueError('Invalid wall system geometry')
            intervals = []
            for guid in guids:
                row = index.get(guid)
                if row is None:
                    uncertain = True
                    continue
                if row['type'] != 'Wall':
                    failed.append(guid)
                    continue
                d = row['details']
                if d.get('geometryType') != 'Straight' or not number(d.get('arcAngle')) or abs(d['arcAngle']) > EPS:
                    raise ValueError('Curved or unknown wall geometry is unsupported')
                p, q = _point(d.get('begCoordinate')), _point(d.get('endCoordinate'))
                for actual, expected in ((row.get('floorIndex'), system['floorIndex']), (d.get('zCoordinate'), system['zCoordinate']), (d.get('height'), system['height'])):
                    if not number(actual):
                        raise ValueError('Missing wall story/elevation/height')
                    if abs(actual-expected) > EPS:
                        failed.append(guid)
                projections = []
                for point in (p, q):
                    if abs(dx*(point[1]-a[1])-dy*(point[0]-a[0]))/length > EPS:
                        failed.append(guid)
                    projections.append(((point[0]-a[0])*dx+(point[1]-a[1])*dy)/length)
                lo, hi = sorted(projections)
                if not all(number(v) for v in projections):
                    raise ValueError('Non-finite derived wall geometry')
                if hi-lo <= EPS or lo < -EPS or hi > length+EPS:
                    failed.append(guid)
                intervals.append((lo, hi))
            intervals.sort()
            if len(intervals) == len(guids):
                cursor = 0.0
                for lo, hi in intervals:
                    if abs(lo-cursor) > EPS:
                        failed.extend(guids)
                    cursor = hi
                if abs(cursor-length) > EPS:
                    failed.extend(guids)
            if len(guids) > 1 and not _approved_fragmentation_exception(system.get('fragmentationException')):
                failed.extend(g for g in guids if g in index)
        if covered != {g for g, row in index.items() if row['type'] == 'Wall'}:
            uncertain = True
    except (KeyError, TypeError, ValueError):
        uncertain = True
    if failed:
        return result('FAIL', 'Unexplained fragmentation or inconsistent continuous wall geometry', failed)
    if uncertain:
        return result('NOT_VERIFIED', 'Incomplete wall coverage/geometry evidence')
    return result('PASS', 'Continuous walls verified; all splits have reviewed BIM reasons')


def _story_assignment(s, index):
    if s.get('storyTransportError') or s.get('boundingBoxTransportError'):
        return result('BLOCKED_BY_TRANSPORT', 'Story or 3D bounding-box read-back failed or was malformed')
    if s.get('storiesComplete') is not True or not isinstance(s.get('stories'), list):
        return result('NOT_VERIFIED', 'Complete GetStories read-back is required')
    stories = {row['index']: row for row in s['stories']
               if isinstance(row, dict) and integer(row.get('index')) and number(row.get('level'))}
    if len(stories) != len(s['stories']):
        return result('NOT_VERIFIED', 'Malformed or duplicate story read-back')
    intents = s.get('storyIntents')
    controlled = s.get('controlledGuids')
    if not isinstance(intents, list) or s.get('storyIntentsComplete') is not True:
        return result('NOT_VERIFIED', 'Missing complete story assignment intent')
    if (not isinstance(controlled, list) or s.get('controlledInventoryComplete') is not True
            or any(not text(g) for g in controlled) or len(set(controlled)) != len(controlled)):
        return result('NOT_VERIFIED', 'Missing complete controlled inventory for story audit')

    expected_by_guid = {}
    failed = []
    uncertain = False

    for intent in intents:
        if (not isinstance(intent, dict) or not text(intent.get('guid'))
                or not integer(intent.get('floorIndex'))
                or not number(intent.get('storyLevel'))
                or intent.get('elevationMode') not in ('STORY_ONLY', 'ABSOLUTE_BASE')):
            uncertain = True
            continue
        guid = intent['guid']
        if guid in expected_by_guid:
            uncertain = True
            continue
        expected_by_guid[guid] = intent

    if set(expected_by_guid) != set(controlled):
        uncertain = True

    for guid in controlled:
        row = index.get(guid)
        intent = expected_by_guid.get(guid)
        if row is None or intent is None:
            uncertain = True
            continue
        actual_floor = row.get('floorIndex')
        if not integer(actual_floor):
            uncertain = True
            continue
        if actual_floor != intent['floorIndex']:
            failed.append(guid)
        story = stories.get(intent['floorIndex'])
        if story is None:
            uncertain = True
        elif abs(story['level'] - intent['storyLevel']) > EPS:
            failed.append(guid)

        if intent['elevationMode'] == 'ABSOLUTE_BASE':
            expected_base = intent.get('baseElevation')
            if not number(expected_base):
                uncertain = True
                continue
            if s.get('boundingBoxesComplete') is not True:
                uncertain = True
                continue
            box = row.get('boundingBox3D')
            actual_base = box.get('zMin') if isinstance(box, dict) else None
            if not number(actual_base):
                uncertain = True
            elif abs(actual_base - expected_base) > EPS:
                failed.append(guid)

    if failed:
        return result('FAIL', 'Element is assigned to the wrong story or base elevation', failed)
    if uncertain:
        return result('NOT_VERIFIED', 'Incomplete story/elevation assignment evidence')
    return result('PASS', 'All controlled elements match their intended story/elevation contract')


def _duplicates(s, index):
    registry, journal = s.get('identityRegistry'), s.get('operationJournal')
    if not isinstance(registry, list) or not isinstance(journal, list):
        return result('NOT_VERIFIED', 'Identity registry and operation journal required')
    controlled = s.get('controlledGuids')
    if not isinstance(controlled, list) or any(not text(g) for g in controlled) or len(set(controlled)) != len(controlled):
        return result('NOT_VERIFIED', 'Missing or malformed controlled element inventory')
    uncertain = not all(s.get(k) is True for k in ('identityRegistryComplete', 'operationJournalComplete', 'controlledInventoryComplete'))
    entities, roles, covered, failed = {}, {}, set(), []
    for entry in registry:
        if not isinstance(entry, dict) or not all(text(entry.get(k)) for k in ('guid', 'entityId', 'role', 'identityScope')):
            uncertain = True
            continue
        guid = entry['guid']
        if guid not in index or guid in covered:
            uncertain = True
        covered.add(guid)
        for table, key in ((entities, (entry['identityScope'], entry['entityId'])), (roles, (entry['identityScope'], entry['role']))):
            if key in table and table[key] != guid and guid in index and table[key] in index:
                failed.extend((guid, table[key]))
            table[key] = guid
    if covered != set(controlled) or not covered.issubset(index):
        uncertain = True
    journal_covered, operation_ids = set(), set()
    for operation in journal:
        if not isinstance(operation, dict) or not text(operation.get('operationId')) or operation.get('status') not in ('DONE', 'RECONCILED'):
            uncertain = True
            continue
        guids = operation.get('guids')
        if not isinstance(guids, list) or any(not text(g) or g not in covered for g in guids):
            uncertain = True
        else:
            journal_covered.update(guids)
        if operation['operationId'] in operation_ids:
            uncertain = True
        operation_ids.add(operation['operationId'])
    if journal_covered != set(controlled):
        uncertain = True
    if failed:
        return result('FAIL', 'Duplicate generated identity or semantic role', failed)
    if uncertain:
        return result('NOT_VERIFIED', 'Incomplete identity coverage or unresolved journal operations')
    return result('PASS', 'No duplicate generated identities or roles in complete scoped evidence')


def _element_economy(s, index):
    """Enforce operation-over-fragmentation from trusted semantic intent.

    maxElementCount is not inferred from generated geometry. It must come from a
    trusted planner/reference contract describing the smallest known semantically
    correct representation for that role.
    """
    intents = s.get('elementEconomyIntents')
    controlled = s.get('controlledGuids')
    if not isinstance(intents, list) or s.get('elementEconomyComplete') is not True:
        return result('NOT_VERIFIED', 'Missing complete minimum-element-count intent')
    if (not isinstance(controlled, list) or s.get('controlledInventoryComplete') is not True
            or any(not text(g) for g in controlled) or len(set(controlled)) != len(controlled)):
        return result('NOT_VERIFIED', 'Missing complete controlled inventory for element-economy audit')

    failed = []
    uncertain = False
    covered = set()
    intent_ids = set()

    for intent in intents:
        if not isinstance(intent, dict) or not text(intent.get('id')) or intent['id'] in intent_ids:
            uncertain = True
            continue
        intent_ids.add(intent['id'])
        guids = intent.get('guids')
        max_count = intent.get('maxElementCount')
        strategy = intent.get('strategyKind')
        if (not text(intent.get('semanticRole'))
                or not isinstance(guids, list) or not guids
                or any(not text(g) for g in guids) or len(set(guids)) != len(guids)
                or not integer(max_count) or max_count < 1
                or strategy not in ECONOMY_STRATEGIES):
            uncertain = True
            continue

        if strategy == 'NATIVE_OPERATION' and not text(intent.get('operationName')):
            uncertain = True
        if strategy == 'MINIMAL_MULTI_ELEMENT' and max_count < 2:
            uncertain = True

        if covered.intersection(guids):
            uncertain = True
        covered.update(guids)

        for guid in guids:
            if guid not in index or guid not in controlled:
                uncertain = True

        if len(guids) > max_count:
            if not _approved_fragmentation_exception(intent.get('fragmentationException')):
                failed.extend(g for g in guids if g in index)

    if covered != set(controlled):
        uncertain = True

    if failed:
        return result(
            'FAIL',
            'A semantic role uses more BIM elements than its approved minimal representation',
            failed,
        )
    if uncertain:
        return result(
            'NOT_VERIFIED',
            'Incomplete or ambiguous minimum-element-count / operation-strategy evidence',
        )
    return result(
        'PASS',
        'Controlled elements use the approved minimal semantic representation or reviewed exception',
    )


def _dependency(s, stage, audits, current, rules):
    pipeline = {p['id']: p for p in rules['pipeline']}
    if not text(stage) or stage not in pipeline:
        return result('NOT_VERIFIED', 'Unknown pipeline stage')
    if not all(text(s.get(k)) for k in ('projectId', 'snapshotId', 'auditScope')):
        return result('NOT_VERIFIED', 'Missing dependency project/snapshot/scope binding')
    if not isinstance(audits, dict):
        return result('NOT_VERIFIED', 'Malformed predecessor audits')
    statuses = []
    visited = set()

    def check(pass_id, own=False):
        if pass_id in visited:
            return
        visited.add(pass_id)
        if own:
            outcomes = current
        else:
            audit = audits.get(pass_id)
            if not isinstance(audit, dict) or any(audit.get(k) != s.get(k) for k in ('projectId', 'snapshotId', 'auditScope')):
                statuses.append('NOT_VERIFIED')
                outcomes = {}
            else:
                outcomes = audit.get('rules', {})
                if audit.get('stage') != pass_id:
                    statuses.append('NOT_VERIFIED')
                if audit.get('status') != 'PASS':
                    status = audit.get('status')
                    statuses.append(status if text(status) and status in RESULTS else 'NOT_VERIFIED')
        if not isinstance(outcomes, dict):
            outcomes = {}
        for rule in rules['rules']:
            if rule['id'] == 'BIM-QA-010':
                continue
            if 'ALL_PASSES' in rule['scope'] or pass_id in rule['scope']:
                value = outcomes.get(rule['id'], {})
                status = value.get('status') if isinstance(value, dict) else None
                statuses.append(status if text(status) and status in RESULTS else 'NOT_VERIFIED')
        for predecessor in pipeline[pass_id]['requires']:
            check(predecessor)

    check(stage, True)
    for status in ('FAIL', 'BLOCKED_BY_TRANSPORT', 'NOT_VERIFIED'):
        if status in statuses:
            return result(status, 'A required current or predecessor blocker is unresolved')
    return result('PASS', 'All required current and predecessor blockers are PASS for this snapshot')


def audit_snapshot(snapshot, stage, previous_audits=None):
    rules = json.loads(RULES_PATH.read_text(encoding='utf-8'))
    if not isinstance(snapshot, dict):
        snapshot = {}
    index, issue = _inventory(snapshot)
    outcomes = {r['id']: result('NOT_VERIFIED', 'Checker is not implemented') for r in rules['rules']}
    if issue:
        for rule_id in IMPLEMENTED - {'BIM-QA-010'}:
            outcomes[rule_id] = issue
    else:
        outcomes['BIM-QA-001'] = _walls(snapshot, index)
        outcomes['BIM-QA-002'] = _native(snapshot, index, 'Window')
        outcomes['BIM-QA-003'] = _native(snapshot, index, 'Door')
        outcomes['BIM-QA-008'] = _story_assignment(snapshot, index)
        outcomes['BIM-QA-009'] = _duplicates(snapshot, index)
        outcomes['BIM-QA-011'] = _element_economy(snapshot, index)
    outcomes['BIM-QA-010'] = _dependency(snapshot, stage, previous_audits or {}, outcomes, rules)
    return {**{k: snapshot.get(k) for k in ('projectId', 'snapshotId', 'auditScope')},
            'stage': stage, 'status': outcomes['BIM-QA-010']['status'], 'rules': outcomes}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', required=True)
    parser.add_argument('--stage', required=True)
    parser.add_argument('--previous-audits')
    parser.add_argument('--output')
    args = parser.parse_args()
    try:
        snapshot = json.loads(Path(args.snapshot).read_text(encoding='utf-8'))
        previous = json.loads(Path(args.previous_audits).read_text(encoding='utf-8')) if args.previous_audits else {}
        report = audit_snapshot(snapshot, args.stage, previous)
    except (OSError, ValueError, TypeError) as exc:
        report = {'status': 'NOT_VERIFIED', 'reason': f'Cannot read audit input: {exc}'}
    rendered = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(rendered + '\n', encoding='utf-8')
    print(rendered)
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
