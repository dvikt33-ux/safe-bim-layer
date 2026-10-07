"""Stage 5 durable Hosted Window attempts and evidence-based reconciliation."""
from copy import deepcopy
import math

from .live_wall import model_hash, load, TOL
from .models import WindowAction
from .orchestrator import fingerprint
from .wall_attempts import AttemptJournal, indexed, durable_json
from uuid import uuid4


WINDOW_FIELDS = ('sourceGuid', 'centerOffset', 'sillHeight', 'width', 'height')


def _number(value, name, *, positive=False):
    if isinstance(value, bool) or type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError(name+' must be a finite number')
    value = float(value)
    if positive and value <= 0:
        raise ValueError(name+' must be positive')
    return value


def _host_signature(wall):
    value = deepcopy(wall)
    for body in value.get('bodies', []):
        body.pop('nativeBodyIndex', None)
    return fingerprint(value)


def window_signature(before, action, identity):
    if action.type != 'create_window' or set(action.parameters) != set(WINDOW_FIELDS):
        raise ValueError('Frozen Hosted Window action contract required')
    params = action.parameters
    source_guid = params['sourceGuid']
    if not isinstance(source_guid, str) or not source_guid.strip():
        raise ValueError('sourceGuid must identify the host Wall')

    elements = indexed(before)
    host = elements.get(source_guid.lower())
    if not host or host.get('type') != 'Wall':
        raise ValueError('sourceGuid is not a Wall in the factual model')
    ref = host.get('placement', {}).get('referenceGeometry', {})
    if ref.get('kind') != 'WallReferenceLine' or ref.get('arcAngle') != 0:
        raise ValueError('Stage 5 Hosted Window requires a straight Wall reference line')

    center = _number(params['centerOffset'], 'centerOffset')
    sill = _number(params['sillHeight'], 'sillHeight')
    width = _number(params['width'], 'width', positive=True)
    height = _number(params['height'], 'height', positive=True)
    wall_height = _number(ref.get('height'), 'host height', positive=True)
    begin, end = ref.get('begin', {}), ref.get('end', {})
    length = math.hypot(float(end.get('x', 0))-float(begin.get('x', 0)),
                        float(end.get('y', 0))-float(begin.get('y', 0)))
    if length <= 0:
        raise ValueError('Host Wall reference line is degenerate')
    if center-width/2 <= TOL or center+width/2 >= length-TOL:
        raise ValueError('Window opening must remain inside host Wall ends')
    if sill < -TOL or sill+height > wall_height+TOL:
        raise ValueError('Window opening must remain inside host Wall height')

    native = {'windowsData': [{
        'ownerWallId': {'guid': host['guid']},
        'centerOffset': center,
        'sillHeight': sill,
        'width': width,
        'height': height,
        'reflected': False,
        'refSide': False,
        'oSide': False,
    }]}
    return {
        'sourceGuid': host['guid'],
        'preModelHash': model_hash(before),
        'modelIdentity': identity,
        'hostHomeStory': host.get('homeStory'),
        'hostSemanticHash': _host_signature(host),
        'hostLength': length,
        'hostHeight': wall_height,
        'centerOffset': center,
        'sillHeight': sill,
        'width': width,
        'height': height,
        'nativeParameters': native,
        'tolerance': TOL,
    }


def prepare_window_attempt(before, action, identity, iteration, goal_id):
    signature = window_signature(before, action, identity)
    return {
        'mutationAttemptId': str(uuid4()),
        'mutationAttemptState': 'PREPARED',
        'goalId': goal_id,
        'iteration': iteration,
        'action': {'type': action.type, 'parameters': deepcopy(action.parameters)},
        'signature': signature,
        'signatureHash': fingerprint(signature),
        'reconciliationStatus': None,
        'reconciliationEvidence': {},
        'retryAllowed': False,
        'retryReason': None,
    }


def matching_window(element, signature):
    if element.get('type') != 'Window' or element.get('homeStory') != signature['hostHomeStory']:
        return False
    host = element.get('relationships', {}).get('hostGuid')
    if not isinstance(host, str) or host.lower() != signature['sourceGuid'].lower():
        return False
    ref = element.get('placement', {}).get('referenceGeometry', {})
    numeric = {
        'centerOffsetAlongHost': signature['centerOffset'],
        'sillHeight': signature['sillHeight'],
        'width': signature['width'],
        'height': signature['height'],
    }
    for key, expected in numeric.items():
        actual = ref.get(key)
        if type(actual) not in (int, float) or not math.isfinite(actual):
            return False
        if abs(float(actual)-expected) > signature['tolerance']:
            return False
    if ref.get('refSide') not in (False, 0) or ref.get('reflected') not in (False, 0):
        return False
    return bool(element.get('bodies'))


def _host_aperture_changed(before_host, current_host):
    # A hosted Window changes host topology but must not replace/move the Wall.
    br = before_host.get('placement', {}).get('referenceGeometry', {})
    cr = current_host.get('placement', {}).get('referenceGeometry', {})
    stable = (before_host.get('homeStory') == current_host.get('homeStory') and br == cr)
    if not stable:
        return False
    before_bodies, current_bodies = before_host.get('bodies', []), current_host.get('bodies', [])
    if not before_bodies or not current_bodies:
        return False
    return fingerprint(before_bodies) != fingerprint(current_bodies)


def reconcile_window_attempt(attempt, before, current, identity, journal):
    result = {
        'mutationAttemptId': attempt.get('mutationAttemptId'),
        'status': 'RECONCILIATION_AMBIGUOUS',
        'terminalReason': 'BLOCKED_RECONCILIATION_AMBIGUOUS',
        'retryAllowed': False,
        'candidateGuids': [],
        'freshModelHash': model_hash(current),
    }
    try:
        action = WindowAction(**attempt['action'])
        expected = window_signature(before, action, identity)
        signature = attempt['signature']
        if (signature != expected or fingerprint(signature) != attempt['signatureHash']
                or journal['mutationAttemptId'] != attempt['mutationAttemptId']
                or journal['signatureHash'] != attempt['signatureHash']):
            raise ValueError('Signature, identity or journal does not match retained Window attempt')

        bm, cm = indexed(before), indexed(current)
        before_host = bm.get(signature['sourceGuid'].lower())
        current_host = cm.get(signature['sourceGuid'].lower())
        if before_host is None or current_host is None:
            raise ValueError('Host Wall missing during reconciliation')

        candidates = [cm[g]['guid'] for g in sorted(cm.keys()-bm.keys())
                      if matching_window(cm[g], signature)]
        result['candidateGuids'] = candidates

        if journal['phase'] == 'NOT_DISPATCHED':
            if journal['dispatchStarted'] or journal['nativeCalls'] != 0:
                raise ValueError('Non-application requires confirmed zero dispatch')
            if model_hash(current) != signature['preModelHash']:
                raise ValueError('Non-application requires unchanged fresh model')
            if _host_signature(current_host) != signature['hostSemanticHash']:
                raise ValueError('Host Wall changed despite confirmed non-dispatch')
            result.update(
                status='RECONCILED_NOT_APPLIED',
                terminalReason=None,
                retryAllowed=True,
                retryReason='Confirmed non-dispatch plus unchanged fresh model; fresh observe/plan required',
            )
        elif journal['phase'] in ('DISPATCHED', 'CONFIRMED') and journal['dispatchStarted'] and journal['nativeCalls'] == 1:
            expected_request = {'command': 'CreateWindows', 'parameters': signature['nativeParameters']}
            if journal.get('nativeRequest') != expected_request or journal.get('nativeRequestHash') != fingerprint(expected_request):
                raise ValueError('Native request not bound to retained Window signature')
            if len(candidates) != 1:
                raise ValueError('Exactly one new hosted Window must match the retained signature')
            if not _host_aperture_changed(before_host, current_host):
                raise ValueError('Host Wall does not contain factual aperture/topology change')
            receipt = journal.get('nativeResponse')
            if receipt is not None:
                if journal.get('nativeResponseHash') != fingerprint(receipt):
                    raise ValueError('Native Window receipt hash mismatch')
                guids = [row.get('elementId', {}).get('guid') for row in receipt.get('elements', [])]
                if len(guids) != 1 or not guids[0] or guids[0].lower() != candidates[0].lower():
                    raise ValueError('Native Window GUID receipt conflicts with reconciliation candidate')
            result.update(status='RECONCILED_APPLIED', terminalReason=None, createdGuid=candidates[0])
        else:
            raise ValueError('No sufficient evidence of Window dispatch or non-dispatch')
    except (ValueError, KeyError, TypeError) as exc:
        result['reason'] = str(exc)
    return result
