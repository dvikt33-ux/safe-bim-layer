"""Stage 5 live adapter for exactly one model-bound Hosted Window."""
from copy import deepcopy
from datetime import datetime, timezone
import math
import os
from pathlib import Path

from .live_wall import LiveSession, load, model_hash, read, save, TOL
from .models import (
    AcceptanceContract, Criterion, Fact, LiveExecutionResult,
    LiveModelFingerprint, LiveObservation, PlannerDecision, WindowAction,
)
from .orchestrator import BeforeMutationTransportError, StaleBeforeWrite
from .wall_attempts import AttemptJournal
from .window_attempts import prepare_window_attempt


def _emap(data):
    return {e['guid'].lower(): e for e in data.get('elements', [])}


def _envelope(element):
    points = [p for body in element.get('bodies', []) for p in body.get('vertices', [])]
    if not points:
        return None
    return [[min(p[i] for p in points), max(p[i] for p in points)] for i in range(3)]


def _body_signature(element):
    # nativeBodyIndex is technical noise; all topology/geometry/material fields remain.
    bodies = deepcopy(element.get('bodies', []))
    for body in bodies:
        body.pop('nativeBodyIndex', None)
    from .orchestrator import fingerprint
    return fingerprint(bodies)


def verify_window(before, after, result, action):
    bm, am = _emap(before), _emap(after)
    created_guid = result.get('createdGuid')
    if not created_guid:
        raise ValueError('Executor result contains no created Window GUID')
    added = set(am)-set(bm)
    removed = set(bm)-set(am)
    if added != {created_guid.lower()} or removed:
        raise ValueError('Element GUID delta is not exactly the native created Window')

    source_guid = action.parameters['sourceGuid']
    before_host = bm.get(source_guid.lower())
    after_host = am.get(source_guid.lower())
    created = am.get(created_guid.lower())
    if not before_host or not after_host or not created:
        raise ValueError('Host or created Window absent from factual read-back')
    if created.get('type') != 'Window':
        raise ValueError('Created GUID is not a Window')

    host_guid = created.get('relationships', {}).get('hostGuid')
    ref = created.get('placement', {}).get('referenceGeometry', {})
    expected = {
        'centerOffsetAlongHost': float(action.parameters['centerOffset']),
        'sillHeight': float(action.parameters['sillHeight']),
        'width': float(action.parameters['width']),
        'height': float(action.parameters['height']),
    }
    numeric_matches = {}
    for key, value in expected.items():
        actual = ref.get(key)
        numeric_matches[key] = (
            type(actual) in (int, float) and math.isfinite(actual)
            and abs(float(actual)-value) <= TOL)

    before_ref = before_host.get('placement', {}).get('referenceGeometry', {})
    after_ref = after_host.get('placement', {}).get('referenceGeometry', {})
    host_reference_stable = (
        before_host.get('homeStory') == after_host.get('homeStory')
        and before_ref == after_ref)
    host_body_changed = _body_signature(before_host) != _body_signature(after_host)
    outer_envelope_stable = _envelope(before_host) == _envelope(after_host)
    materials_before = {
        f.get('materialId') for b in before_host.get('bodies', []) for f in b.get('faces', [])}
    materials_after = {
        f.get('materialId') for b in after_host.get('bodies', []) for f in b.get('faces', [])}
    host_materials_unchanged = materials_before == materials_after
    window_has_body = any(
        body.get('vertices') and body.get('faces') for body in created.get('bodies', []))

    witness = {
        'createdGuid': created_guid,
        'sourceGuid': source_guid,
        'windowCreated': True,
        'hostGuid': host_guid,
        'hostMatches': isinstance(host_guid, str) and host_guid.lower() == source_guid.lower(),
        'homeStoryMatches': created.get('homeStory') == before_host.get('homeStory'),
        'centerOffsetMatches': numeric_matches['centerOffsetAlongHost'],
        'sillHeightMatches': numeric_matches['sillHeight'],
        'widthMatches': numeric_matches['width'],
        'heightMatches': numeric_matches['height'],
        'refSideMatches': ref.get('refSide') in (False, 0),
        'reflectedMatches': ref.get('reflected') in (False, 0),
        'windowHasBody': window_has_body,
        'hostReferenceStable': host_reference_stable,
        'hostApertureChanged': host_body_changed,
        'hostOuterEnvelopeStable': outer_envelope_stable,
        'hostMaterialsUnchanged': host_materials_unchanged,
        'elementCountDeltaOne': len(after.get('elements', [])) == len(before.get('elements', []))+1,
        'requested': deepcopy(action.parameters),
        'actualReferenceGeometry': deepcopy(ref),
        'elementCountBefore': len(before.get('elements', [])),
        'elementCountAfter': len(after.get('elements', [])),
        'hostBodyHashBefore': _body_signature(before_host),
        'hostBodyHashAfter': _body_signature(after_host),
        'createdWindow': created,
    }
    required = (
        'windowCreated', 'hostMatches', 'homeStoryMatches', 'centerOffsetMatches',
        'sillHeightMatches', 'widthMatches', 'heightMatches', 'refSideMatches',
        'reflectedMatches', 'windowHasBody', 'hostReferenceStable',
        'hostApertureChanged', 'hostOuterEnvelopeStable',
        'hostMaterialsUnchanged', 'elementCountDeltaOne',
    )
    witness['pass'] = all(witness[key] for key in required)
    if not witness['pass']:
        raise ValueError('Factual Hosted Window read-back does not satisfy the bound action')
    return witness


class WindowSession(LiveSession):
    def __init__(self, output, goal_id, approved_plan=None):
        super().__init__(output, goal_id, {}, {})
        self.window_recipe = load('stage5_hosted_window_recipe',
                                  'scripts/archicad_write_cycles/hosted_window_cycle.py')
        self.approved_plan = deepcopy(approved_plan)
        self.window_row = None
        self.executor_before_hash = None
        self.active_attempt = None
        self.journal = None
        self.step = None

    def values(self):
        names = (
            'windowCreated', 'hostMatches', 'homeStoryMatches',
            'centerOffsetMatches', 'sillHeightMatches', 'widthMatches',
            'heightMatches', 'refSideMatches', 'reflectedMatches',
            'windowHasBody', 'hostReferenceStable', 'hostApertureChanged',
            'hostOuterEnvelopeStable', 'hostMaterialsUnchanged',
            'elementCountDeltaOne',
        )
        if self.window_row is None:
            return {name: False for name in names}
        return {name: bool(self.window_row.get(name)) for name in names}

    def observation(self, role):
        data, path, signature = self.snapshot(role)
        values = self.values()
        evidence = {
            'live.snapshot': {
                'path': str(path), 'modelHash': signature,
                'elementCount': len(data.get('elements', [])),
            },
            'live.progress': {
                'checks': values, 'goalId': self.goal_id,
                'witnessPath': self.window_row.get('witnessPath') if self.window_row else None,
            },
        }
        return LiveObservation(
            self.identity['projectPath'], signature,
            {key: Fact(value, evidenceRefs=('live.progress','live.snapshot'))
             for key, value in values.items()},
            evidence,
        )


class WindowObserver:
    offline = False
    def __init__(self, session):
        self.session = session
    def observe(self):
        return self.session.observation('observe')


class WindowPlanner:
    offline = False
    def __init__(self, session):
        self.session = session

    def plan(self, job, observation):
        if self.session.window_row is not None:
            return PlannerDecision('BLOCKED', reason='Stage 5 allows exactly one Hosted Window mutation')
        data = read(observation.evidence['live.snapshot']['path'])
        approved = self.session.approved_plan
        if approved is not None:
            if observation.modelIdentity != approved['modelIdentity']:
                return PlannerDecision('BLOCKED', reason='Approved Stage 5 plan belongs to another project')
            if observation.modelHash != approved['modelHash']:
                return PlannerDecision('BLOCKED', reason='Approved Stage 5 plan is stale; fresh plan-only approval required')
            action = WindowAction(**approved['plannerDecision']['action'])
            plan = {
                'wallGuid':action.parameters['sourceGuid'],
                'centerOffsetAlongHost':action.parameters['centerOffset'],
                'sillHeightFromWallBase':action.parameters['sillHeight'],
                'width':action.parameters['width'],
                'height':action.parameters['height'],
                'selectionRule':'explicit operator-approved Stage 5 plan-only action',
            }
        else:
            try:
                plan = self.session.window_recipe.select_wall(data)
            except Exception as exc:
                return PlannerDecision('BLOCKED', reason='No safe Hosted Window host: '+str(exc))
            action = WindowAction('create_window', {
                'sourceGuid': plan['wallGuid'],
                'centerOffset': plan['centerOffsetAlongHost'],
                'sillHeight': plan['sillHeightFromWallBase'],
                'width': plan['width'],
                'height': plan['height'],
            })
        self.session.active_plan = {
            'jobIteration': job.iteration,
            'modelHash': observation.modelHash,
            'selection': {k:v for k,v in plan.items() if k != 'wallBodyBefore'},
            'action': deepcopy(action.parameters),
        }
        save(self.session.output/f'plan-{job.iteration}.json', {
            'goalId': job.goalId,
            'modelIdentity': observation.modelIdentity,
            'modelHash': observation.modelHash,
            'selection': self.session.active_plan['selection'],
            'typedAction': {'type': action.type, 'parameters': action.parameters},
        })
        return PlannerDecision(
            'PLANNED', action,
            plannedAgainstModelIdentity=observation.modelIdentity,
            plannedAgainstModelHash=observation.modelHash,
        )


class WindowModelCheck:
    offline = False
    def __init__(self, session):
        self.session = session

    def check(self, reference):
        _, _, signature = self.session.snapshot('stale-check')
        return LiveModelFingerprint(self.session.identity['projectPath'], signature)


class WindowExecutor:
    offline = False
    def __init__(self, session):
        self.session = session

    def prepare(self, job, action, observed):
        data = read(observed.evidence['live.snapshot']['path'])
        attempt = prepare_window_attempt(
            data, action, observed.modelIdentity, job.iteration, job.goalId)
        self.session.active_attempt = deepcopy(attempt)
        return attempt

    def execute(self, action):
        session = self.session
        plan = session.active_plan
        if action.type != 'create_window' or action.parameters != plan['action']:
            return LiveExecutionResult(
                'BLOCKED', False, True,
                {'mutationAttemptId': session.active_attempt['mutationAttemptId'],
                 'reason':'Action differs from bound Hosted Window plan'})
        step = session.output/f'iteration-{plan["jobIteration"]}'
        step.mkdir(exist_ok=False)
        session.step = step
        os.environ['SAFE_BIM_MVP_EVIDENCE'] = str(step)

        executor = load('stage5_window_executor', 'scripts/archicad_executor.py')
        original_dump, original_api = executor.dump, executor.api
        journal = AttemptJournal(step/'attempts', session.active_attempt)
        journal.claim()
        session.journal = journal

        def guarded_dump(stem):
            data = original_dump(stem)
            if stem == 'before':
                session.check_identity()
                signature = model_hash(data)
                session.executor_before_hash = signature
                if signature != plan['modelHash']:
                    journal.mark_not_dispatched('fresh executor-before snapshot is stale')
                    raise StaleBeforeWrite(
                        LiveModelFingerprint(session.identity['projectPath'], signature))
            return data

        def guarded_api(command, parameters, stem):
            if command != 'CreateWindows':
                raise ValueError('Stage 5 authorizes only CreateWindows')
            session.check_identity()
            native_request = {'command': command, 'parameters': parameters}
            journal.dispatch(native_request)
            save(step/'native-dispatch.json', {
                'goalId': session.goal_id,
                'mutationAttemptId': session.active_attempt['mutationAttemptId'],
                'command': command,
                'plannedHash': plan['modelHash'],
                'executorBeforeHash': session.executor_before_hash,
                'atUtc': datetime.now(timezone.utc).isoformat(),
            })
            response = original_api(command, parameters, stem)
            journal.confirm(response)
            return response

        executor.dump, executor.api = guarded_dump, guarded_api
        request = {'action':'create_window','mode':'execute', **action.parameters}
        save(step/'executor-request.json', {
            'goalId':session.goal_id,
            'mutationAttemptId':session.active_attempt['mutationAttemptId'],
            'request':request,
        })
        try:
            result = executor.run(request)
        except StaleBeforeWrite:
            raise
        except Exception as exc:
            if not journal.value['dispatchStarted']:
                journal.mark_not_dispatched('executor failed before CreateWindows dispatch')
                raise BeforeMutationTransportError(str(exc))
            raise
        save(step/'executor-result.json', result)
        if result.get('status') != 'PASS':
            return LiveExecutionResult(
                'UNKNOWN_OUTCOME', True, True,
                {**result, 'mutationAttemptId':session.active_attempt['mutationAttemptId'],
                 'nativeResponseConfirmed': journal.value['phase'] == 'CONFIRMED'})
        return LiveExecutionResult(
            'PASS', True, True,
            {**result, 'mutationAttemptId':session.active_attempt['mutationAttemptId'],
             'nativeResponseConfirmed': journal.value['phase'] == 'CONFIRMED'})


class WindowReadBack:
    offline = False
    def __init__(self, session):
        self.session = session

    def read_back(self, action, result):
        session = self.session
        after, path, signature = session.snapshot('read-back')
        before = read(session.step/'executor'/'before.json')
        witness = verify_window(before, after, result.details, action)
        witness_path = session.step/'readback-witness.json'
        save(witness_path, witness)
        row = {k:v for k,v in witness.items() if k != 'createdWindow'}
        row.update({
            'goalId':session.goal_id,
            'plannedHash':session.active_plan['modelHash'],
            'executorBeforeHash':session.executor_before_hash,
            'readbackHash':signature,
            'witnessPath':str(witness_path),
            'readbackPath':str(path),
            'mutationAttemptId':session.active_attempt['mutationAttemptId'],
        })
        session.window_row = row
        save(session.step/'summary.json', row)
        return session.observation_from_existing(after, path, signature) if hasattr(
            session, 'observation_from_existing') else _window_observation_from_snapshot(
                session, after, path, signature)


def _window_observation_from_snapshot(session, data, path, signature):
    values = session.values()
    return LiveObservation(
        session.identity['projectPath'], signature,
        {key:Fact(value, evidenceRefs=('live.progress','live.snapshot'))
         for key,value in values.items()},
        {
            'live.snapshot': {
                'path':str(path), 'modelHash':signature,
                'elementCount':len(data.get('elements', [])),
            },
            'live.progress': {
                'checks':values, 'goalId':session.goal_id,
                'witnessPath':session.window_row['witnessPath'],
            },
        },
    )


def acceptance(goal_id):
    checks = (
        'windowCreated', 'hostMatches', 'homeStoryMatches',
        'centerOffsetMatches', 'sillHeightMatches', 'widthMatches',
        'heightMatches', 'refSideMatches', 'reflectedMatches',
        'windowHasBody', 'hostReferenceStable', 'hostApertureChanged',
        'hostOuterEnvelopeStable', 'hostMaterialsUnchanged',
        'elementCountDeltaOne',
    )
    return AcceptanceContract(
        goal_id,
        tuple(Criterion(f'W{i:02}', True, check, True) for i, check in enumerate(checks, 1)),
    )
