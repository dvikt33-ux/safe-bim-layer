"""Prepare or verify an isolated two-Wall fixture for rebound Stage 4 live tests."""
import argparse
import contextlib
import io
import json
import math
from pathlib import Path
import urllib.request
from uuid import uuid4

from .live_wall import ROOT, TOL, load, model_hash
from .stage4_preflight import preflight
from .wall_attempts import durable_json

PORT = 19723
MATERIAL_GUID = '922C639B-9875-48DF-A3FC-E0A8AC5F2839'
Y = 600.706201417
PRED_BEGIN_X = 1699.218814915
PRED_END_X = 1700.218814915
SEED_END_X = 1700.718814915
STORY = 0
Z_OFFSET = 0.0
HEIGHT = 6.0
THICKNESS = 0.3
OFFSET = 0.0


def _segment(begin_x, end_x):
    return {'begCoordinate': {'x': begin_x, 'y': Y},
        'endCoordinate': {'x': end_x, 'y': Y},
        'floorIndex': STORY, 'zCoordinate': Z_OFFSET, 'height': HEIGHT,
        'thickness': THICKNESS, 'offset': OFFSET, 'arcAngle': 0,
        'referenceLineLocation': 'Center', 'structureType': 'Basic',
        'buildingMaterialId': {'guid': MATERIAL_GUID}}


def _close(a, b):
    return abs(float(a)-float(b)) <= TOL


def _matches(element, begin_x, end_x):
    if element.get('type') != 'Wall' or element.get('homeStory') != STORY:
        return False
    ref = element.get('placement', {}).get('referenceGeometry', {})
    bind = element.get('materialBindings', {})
    return (ref.get('kind') == 'WallReferenceLine' and ref.get('arcAngle') == 0
        and _close(ref.get('begin', {}).get('x', math.inf), begin_x)
        and _close(ref.get('begin', {}).get('y', math.inf), Y)
        and _close(ref.get('end', {}).get('x', math.inf), end_x)
        and _close(ref.get('end', {}).get('y', math.inf), Y)
        and _close(ref.get('bottomOffsetFromHomeStory', math.inf), Z_OFFSET)
        and _close(ref.get('height', math.inf), HEIGHT)
        and _close(ref.get('thickness', math.inf), THICKNESS)
        and _close(ref.get('offset', math.inf), OFFSET)
        and bind.get('buildingMaterial', {}).get('guid','').lower() == MATERIAL_GUID.lower())


def _fixture_matches(data):
    walls = data.get('elements', [])
    pred = [e for e in walls if _matches(e, PRED_BEGIN_X, PRED_END_X)]
    seed = [e for e in walls if _matches(e, PRED_END_X, SEED_END_X)]
    return pred, seed


def _target_colliders(data):
    target = ((PRED_BEGIN_X, SEED_END_X), (Y-THICKNESS/2, Y+THICKNESS/2),
              (Z_OFFSET, Z_OFFSET+HEIGHT))
    collisions = []
    for element in data.get('elements', []) + data.get('unresolvedBodyOwners', []):
        for body in element.get('bodies', []):
            pts = body.get('vertices', [])
            if not pts:
                continue
            box = tuple((min(float(p[i]) for p in pts), max(float(p[i]) for p in pts)) for i in range(3))
            overlap = [min(target[i][1], box[i][1])-max(target[i][0], box[i][0]) for i in range(3)]
            if all(v > TOL for v in overlap):
                collisions.append(element.get('guid'))
                break
    return sorted({g for g in collisions if g})


def _call_create(output, parameters):
    attempt = str(uuid4())
    payload = {'command':'API.ExecuteAddOnCommand','parameters':{
        'addOnCommandId':{'commandNamespace':'TapirCommand','commandName':'CreateWalls'},
        'addOnCommandParameters':parameters}}
    durable_json(output/'mutation-intent.json', {'mutationAttemptId':attempt,
        'command':'CreateWalls','physicalCallLimit':1,'automaticRetry':False,
        'parameters':parameters,'phase':'PRE_DISPATCH'})
    raw_request = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    (output/'CreateWalls.request.json').write_bytes(raw_request)
    durable_json(output/'mutation-dispatch.json', {'mutationAttemptId':attempt,
        'command':'CreateWalls','physicalMutationCalls':1,'phase':'DISPATCH_STARTED'})
    req = urllib.request.Request(f'http://127.0.0.1:{PORT}', raw_request, {'Content-Type':'application/json'})
    with urllib.request.urlopen(req, timeout=120) as response:
        raw = response.read()
    (output/'CreateWalls.response.json').write_bytes(raw)
    envelope = json.loads(raw)
    if envelope.get('succeeded') is not True:
        raise RuntimeError('CreateWalls failed after dispatch; do not retry blindly: '+str(envelope))
    result = envelope.get('result', {}).get('addOnCommandResponse', {})
    values = [x.get('elementId', {}).get('guid') for x in result.get('elements', [])]
    values = [x for x in values if x]
    if len(values) != 2 or len(set(v.lower() for v in values)) != 2:
        raise RuntimeError('CreateWalls did not return exactly two unique GUIDs; do not retry blindly')
    durable_json(output/'mutation-confirmed.json', {'mutationAttemptId':attempt,
        'command':'CreateWalls','physicalMutationCalls':1,'phase':'CONFIRMED','createdGuids':values})
    return values


def prepare(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    report = {'status':'BLOCKED','provenance':'LIVE_FIXTURE_SETUP','physicalMutationCalls':0,
        'automaticRetry':False,'fixtureGeometry':{'predecessor':[PRED_BEGIN_X,Y,PRED_END_X,Y],
        'seed':[PRED_END_X,Y,SEED_END_X,Y],'story':STORY,'zOffset':Z_OFFSET,
        'height':HEIGHT,'thickness':THICKNESS,'buildingMaterialGuid':MATERIAL_GUID}}
    gate = preflight(output/'identity-gate')
    report['identityGate'] = gate['status']
    if gate['status'] != 'PASS':
        report['reason'] = gate.get('reason')
        durable_json(output/'fixture-report.json', report)
        return report
    report['projectPath'] = gate['identity']['projectPath']
    dump_module = load('stage4_fixture_dump','archicad-addon/Examples/model_dump_v1.py')
    with contextlib.redirect_stdout(io.StringIO()):
        before, _ = dump_module.dump(output/'before.json', PORT)
    report['beforeModelHash'] = model_hash(before)
    pred, seed = _fixture_matches(before)
    if len(pred) == 1 and len(seed) == 1:
        report.update(status='PASS', reusedExistingFixture=True,
            predecessorGuid=pred[0]['guid'], seedGuid=seed[0]['guid'],
            elementCountBefore=len(before.get('elements',[])),
            elementCountAfter=len(before.get('elements',[])))
        durable_json(output/'fixture-report.json', report)
        return report
    if pred or seed:
        report['reason'] = 'Partial or ambiguous Stage 4 fixture already exists; no mutation attempted'
        report['matchingPredecessors'] = [e['guid'] for e in pred]
        report['matchingSeeds'] = [e['guid'] for e in seed]
        durable_json(output/'fixture-report.json', report)
        return report
    material_seen = any(e.get('materialBindings',{}).get('buildingMaterial',{}).get('guid','').lower()
        == MATERIAL_GUID.lower() for e in before.get('elements',[]) if e.get('type') == 'Wall')
    if not material_seen:
        report['reason'] = 'Archived Stage 1 fixture building material is absent from rebound PLN'
        durable_json(output/'fixture-report.json', report)
        return report
    colliders = _target_colliders(before)
    if colliders:
        report['reason'] = 'Archived Stage 1 fixture corridor is occupied in rebound PLN'
        report['colliderGuids'] = colliders[:50]
        durable_json(output/'fixture-report.json', report)
        return report
    params = {'wallsData':[_segment(PRED_BEGIN_X,PRED_END_X),_segment(PRED_END_X,SEED_END_X)]}
    try:
        returned = _call_create(output, params)
        report['physicalMutationCalls'] = 1
        report['nativeCreatedGuids'] = returned
        with contextlib.redirect_stdout(io.StringIO()):
            after, _ = dump_module.dump(output/'after.json', PORT)
        report['afterModelHash'] = model_hash(after)
        pred, seed = _fixture_matches(after)
        before_ids = {e['guid'].lower() for e in before.get('elements',[])}
        after_ids = {e['guid'].lower() for e in after.get('elements',[])}
        added = sorted(after_ids-before_ids)
        if len(pred) != 1 or len(seed) != 1:
            raise RuntimeError('Factual read-back did not contain exactly one predecessor and one seed Wall')
        expected = {pred[0]['guid'].lower(), seed[0]['guid'].lower()}
        if set(added) != expected or set(g.lower() for g in returned) != expected:
            raise RuntimeError('Fixture element-set delta or native receipt does not match factual read-back')
        report.update(status='PASS', reusedExistingFixture=False,
            predecessorGuid=pred[0]['guid'], seedGuid=seed[0]['guid'],
            elementCountBefore=len(before.get('elements',[])),
            elementCountAfter=len(after.get('elements',[])), addedGuids=added)
    except Exception as exc:
        report.update(status='UNKNOWN_OUTCOME' if report.get('physicalMutationCalls') else 'BLOCKED',
            reason=f'{type(exc).__name__}: {exc}', automaticRetry=False)
    durable_json(output/'fixture-report.json', report)
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--live',action='store_true',required=True)
    result=prepare(parser.parse_args().output)
    print(json.dumps(result,ensure_ascii=True))
    return 0 if result['status']=='PASS' else 1


if __name__=='__main__':
    raise SystemExit(main())
