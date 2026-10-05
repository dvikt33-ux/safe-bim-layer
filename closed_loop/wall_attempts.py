"""Durable, single-dispatch Wall attempts and evidence-based reconciliation."""
from copy import deepcopy
from dataclasses import asdict
import json
import math
import os
from pathlib import Path
from uuid import uuid4

from .live_wall import load, model_hash, TOL
from .models import (Action, AuditCriterion, Criterion, ExecutionResult, Fact, Iteration, Job,
    LiveExecutionResult, LiveModelFingerprint, LiveObservation, ModelFingerprint,
    Observation, PlannerDecision, State, Verdict)
from .orchestrator import Orchestrator, fingerprint, audit_decision, IllegalTransition
from .auditor import audit


def durable_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_name(path.name + '.pending')
    with pending.open('w', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())
    pending.replace(path)


def semantic_element(element):
    value = deepcopy(element)
    for body in value.get('bodies', []):
        body.pop('nativeBodyIndex', None)
    return value


def indexed(data):
    elements = data['elements']
    result = {element['guid'].lower(): element for element in elements}
    if len(result) != len(elements):
        raise ValueError('Duplicate model GUIDs')
    return result


def wall_signature(before, action, identity):
    if action.type != 'create_wall' or set(action.parameters) != {'sourceGuid', 'length'}:
        raise ValueError('Frozen Wall continuation contract required')
    length = action.parameters['length']
    if type(length) not in (int, float) or length not in (1.0, 0.5):
        raise ValueError('Only the proven 1.0/0.5 m segments are allowed')
    baseline = load('stage4_signature_v0', 'scripts/archicad_executor.py')
    source, plan = baseline.wall_from_source(before, action.parameters['sourceGuid'], length)
    native = plan['createParameters']['wallsData'][0]
    return {'sourceGuid': source['guid'], 'sourceEndpoint': native['begCoordinate'],
        'expectedBegin': native['begCoordinate'], 'expectedEnd': native['endCoordinate'],
        'expectedLength': length, 'homeStory': native['floorIndex'], 'height': native['height'],
        'expectedAbsoluteBottom': plan['z'],
        'homeStoryElevation': plan['z']-native['zCoordinate'],
        'thickness': native['thickness'], 'bottomOffsetFromHomeStory': native['zCoordinate'],
        'offset': native['offset'], 'structureType': native['structureType'],
        'materialIdentity': native['buildingMaterialId']['guid'], 'tolerance': TOL,
        'preModelHash': model_hash(before), 'modelIdentity': identity,
        'sourceSemanticHash': fingerprint(semantic_element(source)), 'nativeParameters': plan['createParameters']}


def prepare_attempt(before, action, identity, iteration, goal_id):
    signature = wall_signature(before, action, identity)
    return {'mutationAttemptId': str(uuid4()), 'mutationAttemptState': 'PREPARED',
        'goalId': goal_id, 'iteration': iteration, 'action': asdict(action),
        'signature': signature, 'signatureHash': fingerprint(signature),
        'reconciliationStatus': None, 'reconciliationEvidence': {},
        'retryAllowed': False, 'retryReason': None}


class AttemptJournal:
    """Exclusive durable claim before native dispatch. Never overwrite an old ID."""
    def __init__(self, directory, attempt):
        self.directory = Path(directory)
        self.path = self.directory / (attempt['mutationAttemptId'] + '.json')
        self.value = {'mutationAttemptId': attempt['mutationAttemptId'],
            'signatureHash': attempt['signatureHash'], 'phase': 'CLAIMED',
            'dispatchStarted': False, 'nativeCalls': 0, 'nativeResponse': None}

    def claim(self):
        self.directory.mkdir(parents=True, exist_ok=True)
        # Exclusive creation, not exists()+write. A crash leaves the ID spent.
        with self.path.with_suffix('.claim').open('x', encoding='utf-8') as stream:
            stream.write(self.value['mutationAttemptId'])
            stream.flush()
            os.fsync(stream.fileno())
        durable_json(self.path, self.value)

    def mark_not_dispatched(self, reason):
        if self.value['dispatchStarted']:
            raise ValueError('Cannot claim non-dispatch after a physical attempt')
        self.value.update(phase='NOT_DISPATCHED', reason=reason)
        durable_json(self.path, self.value)

    def dispatch(self, native_request):
        if self.value['phase'] != 'CLAIMED' or self.value['nativeCalls']:
            raise ValueError('MutationAttemptId has already been dispatched')
        self.value.update(phase='DISPATCHED', dispatchStarted=True, nativeCalls=1,
                          nativeRequest=native_request, nativeRequestHash=fingerprint(native_request))
        durable_json(self.path, self.value)

    def confirm(self, response):
        if self.value['phase'] != 'DISPATCHED':
            raise ValueError('Native confirmation without matching dispatch')
        self.value.update(phase='CONFIRMED', nativeResponse=response,
                          nativeResponseHash=fingerprint(response))
        durable_json(self.path, self.value)


def matching_wall(element, signature):
    if element.get('type') != 'Wall' or element.get('homeStory') != signature['homeStory']:
        return False
    ref = element.get('placement', {}).get('referenceGeometry', {})
    material = element.get('materialBindings', {})
    if (ref.get('kind') != 'WallReferenceLine' or ref.get('arcAngle') != 0 or
            material.get('buildingMaterial', {}).get('guid', '').lower() != signature['materialIdentity'].lower() or
            material.get('structureType') != 0):
        return False
    comparisons = [(ref.get(field), signature[field]) for field in ('height', 'thickness', 'bottomOffsetFromHomeStory', 'offset')]
    comparisons += [(ref.get(point, {}).get(axis), signature[expected][axis])
                    for point, expected in (('begin', 'expectedBegin'), ('end', 'expectedEnd')) for axis in ('x', 'y')]
    return all(type(actual) in (int, float) and math.isfinite(actual) and abs(actual-expected) <= signature['tolerance']
               for actual, expected in comparisons)


def reconcile_attempt(attempt, before, current, identity, journal):
    result = {'mutationAttemptId': attempt.get('mutationAttemptId'), 'status': 'RECONCILIATION_AMBIGUOUS',
        'terminalReason': 'BLOCKED_RECONCILIATION_AMBIGUOUS', 'retryAllowed': False,
        'candidateGuids': [], 'freshModelHash': model_hash(current)}
    try:
        signature = attempt['signature']
        expected = wall_signature(before, Action(**attempt['action']), identity)
        if (signature != expected or fingerprint(signature) != attempt['signatureHash'] or
                journal['mutationAttemptId'] != attempt['mutationAttemptId'] or journal['signatureHash'] != attempt['signatureHash']):
            raise ValueError('Signature, identity or journal does not match retained attempt')
        bm, cm = indexed(before), indexed(current)
        story = next((row for row in current['stories'] if row['index']==signature['homeStory']),None)
        if story is None or abs(story['elevation']-signature['homeStoryElevation'])>signature['tolerance']:
            raise ValueError('Home-story elevation changed; signature no longer describes the same physical placement')
        source = cm.get(signature['sourceGuid'].lower())
        if source is None or fingerprint(semantic_element(source)) != signature['sourceSemanticHash']:
            raise ValueError('Source Wall changed; cannot reconcile against stale geometry')
        candidates = [cm[g]['guid'] for g in sorted(cm.keys()-bm.keys()) if matching_wall(cm[g], signature)]
        result['candidateGuids'] = candidates
        if journal['phase'] == 'NOT_DISPATCHED':
            if journal['dispatchStarted'] or journal['nativeCalls'] != 0 or model_hash(current) != signature['preModelHash']:
                raise ValueError('Non-application requires confirmed non-dispatch and unchanged fresh model')
            result.update(status='RECONCILED_NOT_APPLIED', terminalReason=None, retryAllowed=True,
                          retryReason='Confirmed non-dispatch plus unchanged fresh model; fresh observe/plan required')
        elif journal['phase'] in ('DISPATCHED', 'CONFIRMED') and journal['dispatchStarted'] and journal['nativeCalls'] == 1:
            request = {'command': 'CreateWalls', 'parameters': signature['nativeParameters']}
            if journal['nativeRequest'] != request or journal['nativeRequestHash'] != fingerprint(request):
                raise ValueError('Native request not bound to the Wall signature')
            if len(candidates) != 1:
                raise ValueError('Exactly one new Wall must match the mutation signature')
            receipt = journal.get('nativeResponse')
            if receipt is not None:
                if journal['nativeResponseHash'] != fingerprint(receipt):
                    raise ValueError('Native receipt hash mismatch')
                guids = [row['elementId']['guid'] for row in receipt['elements']]
                if len(guids) != 1 or guids[0].lower() != candidates[0].lower():
                    raise ValueError('Native GUID receipt conflicts with reconciliation candidate')
            result.update(status='RECONCILED_APPLIED', terminalReason=None, createdGuid=candidates[0])
        else:
            raise ValueError('No sufficient evidence of dispatch or non-dispatch')
    except (ValueError, KeyError, TypeError) as exc:
        result['reason'] = str(exc)
    return result


def job_from_dict(value):
    """Additive Stage 2/3 deserialization; missing Stage 4 fields keep defaults."""
    value = deepcopy(value)
    def action(row): return Action(**row) if row else None
    def observation(row):
        if row is None: return None
        row = deepcopy(row)
        row['facts'] = {k: Fact(**v) for k, v in row['facts'].items()}
        return (LiveObservation if row.get('provenance') == 'LIVE' else Observation)(**row)
    def verdicts(rows):
        return [AuditCriterion(**(r | {'verdict': Verdict(r['verdict'])})) for r in rows] if rows is not None else None
    value['state'] = State(value['state'])
    value['acceptanceCriteria'] = tuple(Criterion(**c) for c in value['acceptanceCriteria'])
    value['actions'] = [action(a) for a in value['actions']]
    value['auditHistory'] = [verdicts(rows) for rows in value['auditHistory']]
    iterations = []
    for row in value['iterations']:
        row['stateBefore'] = State(row['stateBefore'])
        for key in ('observation', 'readback'): row[key] = observation(row[key])
        row['executorRequest'] = action(row['executorRequest'])
        if row['plannerDecision']:
            row['plannerDecision']['action'] = action(row['plannerDecision']['action'])
            row['plannerDecision'] = PlannerDecision(**row['plannerDecision'])
        if row['executorResult']:
            cls = LiveExecutionResult if row['executorResult'].get('executionMode') == 'LIVE' else ExecutionResult
            row['executorResult'] = cls(**row['executorResult'])
        if row['preExecutionFingerprint']:
            cls = LiveModelFingerprint if row['preExecutionFingerprint'].get('provenance') == 'LIVE' else ModelFingerprint
            row['preExecutionFingerprint'] = cls(**row['preExecutionFingerprint'])
        row['auditResult'] = verdicts(row['auditResult'])
        iterations.append(Iteration(**row))
    value['iterations'] = iterations
    return Job(**value)


class RecoverableWallOrchestrator(Orchestrator):
    @classmethod
    def restore(cls, output, *, observer, planner, executor, readback, model_check, clock=None):
        from datetime import datetime, timezone
        from .models import AcceptanceContract
        from scripts.audit_pack import read_json
        raw = read_json(output)
        job = job_from_dict(raw)
        if job.state not in (State.EXECUTING, State.READING_BACK, State.UNKNOWN_OUTCOME):
            raise IllegalTransition('Recovery accepts only unresolved mutation checkpoints')
        if not job.mutationAttempts or not job.iterations or not job.iterations[-1].mutationAttemptId:
            raise ValueError('Checkpoint has no durable Stage 4 attempt; no automatic recovery')
        if not all(getattr(c, 'offline', None) is (job.executionMode == 'OFFLINE')
                   for c in (observer, planner, executor, readback, model_check)):
            raise ValueError('Recovery component execution mode mismatch')
        ids = [a['mutationAttemptId'] for a in job.mutationAttempts]
        if len(ids) != len(set(ids)) or ids[-1] != job.iterations[-1].mutationAttemptId:
            raise ValueError('Duplicate or inconsistent checkpoint attempt IDs')
        checkpoint_hash = fingerprint(raw)
        checkpoint_path = Path(output).parent/'checkpoints'/f'recovery-{job.iteration}-{ids[-1]}-{checkpoint_hash[:12]}.json'
        if checkpoint_path.exists():
            if read_json(checkpoint_path) != raw:
                raise ValueError('Immutable checkpoint collision')
        else:
            durable_json(checkpoint_path,raw)
        self = cls.__new__(cls)
        self.job, self.output, self.execution_mode = job, Path(output), job.executionMode
        self.contract = AcceptanceContract(job.goalId, job.acceptanceCriteria)
        self.observer, self.planner, self.executor, self.readback, self.model_check = observer, planner, executor, readback, model_check
        self.clock = clock or (lambda: datetime.now(timezone.utc).isoformat())
        self._model_identity = job.iterations[0].observation.modelIdentity
        job.recoveredFromCrash = job.state != State.UNKNOWN_OUTCOME
        job.recoveryCheckpoint = {'state': job.state, 'iteration': job.iteration,
                                  'mutationAttemptId': ids[-1], 'checkpointHash': checkpoint_hash,
                                  'evidenceRef':checkpoint_path.relative_to(Path(output).parent).as_posix()}
        job.state, job.finalStatus = State.UNKNOWN_OUTCOME, 'UNKNOWN_OUTCOME'
        job.iterations[-1].mutationAttemptState = job.mutationAttempts[-1]['mutationAttemptState'] = 'UNKNOWN'
        if job.iterations[-1].executorResult is None:
            cls_result = LiveExecutionResult if job.executionMode == 'LIVE' else ExecutionResult
            job.iterations[-1].executorResult = cls_result('UNKNOWN_OUTCOME',True,True,{
                'mutationAttemptId':ids[-1], 'uncertaintyReason':'Recovered unfinished physical attempt; reconciliation required'})
        self._record('recovery-checkpoint-loaded', job.recoveryCheckpoint)
        return self

    def reconcile_and_continue(self, reconciler):
        if self.job.state != State.UNKNOWN_OUTCOME:
            raise IllegalTransition('Explicit reconciliation requires UNKNOWN_OUTCOME')
        step, attempt = self.job.iterations[-1], self.job.mutationAttempts[-1]
        try:
            verdict, observed = reconciler.reconcile(deepcopy(attempt))
            observed = self._observe(observed)
            if verdict['mutationAttemptId'] != attempt['mutationAttemptId'] or verdict['freshModelHash'] != observed.modelHash:
                raise ValueError('Reconciliation verdict does not bind fresh observation/attempt')
        except Exception as exc:
            verdict = {'status': 'RECONCILIATION_AMBIGUOUS', 'mutationAttemptId': attempt['mutationAttemptId'],
                       'terminalReason': 'BLOCKED_RECONCILIATION_AMBIGUOUS', 'retryAllowed': False, 'reason': str(exc)}
            observed = None
        step.reconciliationStatus = attempt['reconciliationStatus'] = verdict['status']
        step.reconciliationEvidence = attempt['reconciliationEvidence'] = deepcopy(verdict)
        attempt['mutationAttemptState'] = step.mutationAttemptState = verdict['status']
        self.job.retryAllowed = attempt['retryAllowed'] = verdict.get('retryAllowed', False)
        self.job.retryReason = attempt['retryReason'] = verdict.get('retryReason')
        self._record('reconciliation', verdict)
        if verdict['status'] not in ('RECONCILED_APPLIED', 'RECONCILED_NOT_APPLIED') or observed is None:
            self.job.state, self.job.finalStatus = State.BLOCKED, 'BLOCKED'
            self.job.terminalReason = 'BLOCKED_RECONCILIATION_AMBIGUOUS'
            self._record('recovery-blocked', verdict)
            return deepcopy(self.job)
        if verdict['status'] == 'RECONCILED_NOT_APPLIED' and verdict.get('retryAllowed') is not True:
            raise ValueError('Non-application lacks fresh-plan retry verdict')
        # Only this explicit evidence-backed recovery operation can leave the
        # terminal uncertainty. Ordinary transition()/run() still forbid retry.
        self.job.state, self.job.finalStatus, self.job.terminalReason = State.OBSERVING, None, None
        self._record('recovery-transition', {'before': 'UNKNOWN_OUTCOME', 'after': 'OBSERVING',
                                            'reconciliationStatus': verdict['status'], 'oldAttemptRepeated': False})
        if verdict['status'] == 'RECONCILED_APPLIED':
            step.readback = deepcopy(observed)
            step.auditResult = audit(self.contract, observed)
            self.job.auditHistory.append(deepcopy(step.auditResult))
            decision = audit_decision(step.auditResult)
            self._record('recovered-audit', {'result': [asdict(r) for r in step.auditResult], 'decision': decision})
            if decision != State.REPLANNING:
                self.job.state = State.AUDITING
                self.transition(decision, 'Factual reconciled read-back acceptance')
                return deepcopy(self.job)
        if self.job.iteration >= self.job.maxIterations:
            self.transition(State.BLOCKED, 'BLOCKED_ITERATION_LIMIT: iteration limit reached during recovery')
            return deepcopy(self.job)
        try:
            observed = self._observe(self.observer.observe())
        except Exception as exc:
            self.transition(State.BLOCKED, f'BLOCKED_BY_TRANSPORT: fresh recovery observation failed: {exc}')
            return deepcopy(self.job)
        self._record('observation', asdict(observed))
        self.transition(State.PLANNING, 'Fresh observation and planning after explicit reconciliation')
        return self._iterate(observed)
