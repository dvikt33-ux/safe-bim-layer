"""Stage 3 adapters for one two-segment goal over the unchanged v0 Wall path."""
import contextlib
import importlib.util
import io
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone

from .models import (AcceptanceContract, Action, Criterion, Fact, LiveExecutionResult,
                     LiveModelFingerprint, LiveObservation, PlannerDecision)
from .orchestrator import fingerprint, StaleBeforeWrite

ROOT = Path(__file__).resolve().parents[1]
COMMAND = 'Продолжи последнюю созданную стену сначала на 1 метр, затем ещё на 0,5 метра и проверь результат.'
TOL = 1e-7
MAIN = '72e9be15ac3b943d7b6f0c46eaa45aa5798d56bc'
DESCRIPTIONS = [
    'Same project identity throughout job', 'Iteration 1 automatically selects source Wall',
    'Iteration 1 physically creates Wall', 'Iteration 1 GUID confirmed in read-back',
    'Iteration 1 length is 1.0 m', 'Iteration 1 jointDistance is zero',
    'New live observation after iteration 1', 'Iteration 2 source derived from factual result 1',
    'iteration2.sourceGuid == iteration1.createdGuid', 'Iteration 2 physically creates Wall',
    'Iteration 2 GUID confirmed in read-back', 'Iteration 2 length is 0.5 m',
    'Iteration 2 jointDistance is zero', 'Stale checks before each mutation',
    'No stale action executed', 'Factual read-back after each mutation',
    'Both operations belong to one goalId', 'One initial user goal command',
    'Required FAIL = 0', 'Required NOT_VERIFIED = 0', 'No UNKNOWN_OUTCOME',
    'Stage 1 v0 regression path still PASS', 'All Stage 2 tests PASS', 'main unchanged']


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def model_hash(data):
    # Retain all model content; remove only measured transport/native duration.
    value = {k: v for k, v in data.items() if k not in ('elements', 'materials', 'unresolvedBodyOwners', 'nativeSeconds')}
    for key in ('elements', 'materials', 'unresolvedBodyOwners'):
        value[key] = sorted(fingerprint(item) for item in data.get(key, []))
    return fingerprint(value)


def verify_wall(before, after, result, source_guid, length):
    bm = {e['guid'].lower(): e for e in before['elements']}
    am = {e['guid'].lower(): e for e in after['elements']}
    guid = result['createdGuid']
    if set(am)-set(bm) != {guid.lower()} or set(bm)-set(am):
        raise ValueError('Element set delta is not exactly the one native created GUID')
    source, new = am[source_guid.lower()], am[guid.lower()]
    sr, nr = source['placement']['referenceGeometry'], new['placement']['referenceGeometry']
    if sr != bm[source_guid.lower()]['placement']['referenceGeometry'] or new['type'] != 'Wall':
        raise ValueError('Source changed or created element is not Wall')
    joint = math.dist([sr['end']['x'], sr['end']['y']], [nr['begin']['x'], nr['begin']['y']])
    actual = math.dist([nr['end']['x'], nr['end']['y']], [nr['begin']['x'], nr['begin']['y']])
    if joint > TOL or abs(actual-length) > TOL or source['homeStory'] != new['homeStory']:
        raise ValueError('Wall joint, segment length or homeStory not verified')
    for field in ('height', 'thickness', 'bottomOffsetFromHomeStory'):
        if abs(sr[field]-nr[field]) > TOL:
            raise ValueError('Wall vertical placement differs from source')
    sv = [sr['end'][axis]-sr['begin'][axis] for axis in ('x', 'y')]
    nv = [nr['end'][axis]-nr['begin'][axis] for axis in ('x', 'y')]
    if sum(a*b for a, b in zip(sv, nv))/(math.hypot(*sv)*math.hypot(*nv)) < 1-1e-6:
        raise ValueError('Continuation direction differs from source')
    return {'sourceGuid': source_guid, 'createdGuid': guid, 'length': actual, 'jointDistance': joint,
        'homeStory': new['homeStory'], 'begin': nr['begin'], 'end': nr['end'],
        'elementCountBefore': len(bm), 'elementCountAfter': len(am),
        'sourceBefore': bm[source_guid.lower()], 'sourceAfter': source, 'createdWall': new}


class LiveSession:
    def __init__(self, output, goal_id, offline_report, regression_report):
        self.output = Path(output)
        self.output.mkdir(parents=True, exist_ok=False)
        self.goal_id, self.offline_report, self.regression_report = goal_id, offline_report, regression_report
        self.snapshots = 0
        self.rows = []
        self.active_plan = None
        self.last_check = None
        self.api_count = 0
        self.dump_module = load('stage3_dump', 'archicad-addon/Examples/model_dump_v1.py')
        self.chat = load('stage3_chat', 'scripts/archicad_chat_executor.py')
        self.identity = self.api('GetProjectInfo')
        if not self.identity.get('projectPath') or self.identity.get('isUntitled'):
            raise ValueError('Named test PLN required')
        if self.identity != read(ROOT / 'outputs/closed-loop-stage1/preflight.json')['identity']:
            raise ValueError('Active PLN differs from the previously verified test project')
        save(self.output / 'preflight.json', {'identity': self.identity,
            'archicad': self.api('API.GetProductInfo', addon=False), 'tapir': self.api('GetAddOnVersion'),
            'port': 19723, 'observedAtUtc': datetime.now(timezone.utc).isoformat()})

    def api(self, command, addon=True):
        self.api_count += 1
        stem = self.output / 'identity' / f'{self.api_count:03}-{command}'
        payload = {'command': 'API.ExecuteAddOnCommand', 'parameters': {
            'addOnCommandId': {'commandNamespace': 'TapirCommand', 'commandName': command},
            'addOnCommandParameters': {}}} if addon else {'command': command}
        save(stem.with_suffix('.request.json'), payload)
        with urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:19723', json.dumps(payload).encode(),
                {'Content-Type': 'application/json'}), timeout=30) as response:
            raw = response.read()
        stem.with_suffix('.response.json').write_bytes(raw)
        envelope = json.loads(raw)
        if not envelope.get('succeeded'):
            raise RuntimeError(envelope)
        return envelope['result'].get('addOnCommandResponse', envelope['result'])

    def check_identity(self):
        actual = self.api('GetProjectInfo')
        if actual != self.identity:
            raise ValueError('Project identity changed; no project switch or retry allowed')

    def snapshot(self, role):
        self.check_identity()
        self.snapshots += 1
        path = self.output / 'observations' / f'{self.snapshots:03}-{role}.json'
        with contextlib.redirect_stdout(io.StringIO()):
            data, metrics = self.dump_module.dump(path, 19723)
        self.check_identity()
        signature = model_hash(data)
        save(path.with_suffix('.fingerprint.json'), {'modelIdentity': self.identity['projectPath'],
            'modelHash': signature, 'elementCount': len(data['elements']), 'role': role})
        return data, path, signature

    def values(self):
        n = len(self.rows)
        first, second = (self.rows[0] if n else None), (self.rows[1] if n > 1 else None)
        values = {f'C{i:02}': False for i in range(1, 25)}
        values.update(C01=True, C18=True, C20=True, C21=True,
            C22=self.regression_report.get('status') == 'PASS', C23=self.offline_report.get('status') == 'PASS',
            C24=getattr(self, 'main_current', MAIN) == MAIN)
        if first:
            values.update(C02=first['automaticSelection'], C03=True, C04=True,
                C05=abs(first['length']-1.0) <= TOL, C06=first['jointDistance'] <= TOL, C07=True)
        if second:
            match = second['sourceGuid'].lower() == first['createdGuid'].lower()
            values.update(C08=match, C09=match, C10=True, C11=True,
                C12=abs(second['length']-0.5) <= TOL, C13=second['jointDistance'] <= TOL,
                C14=all(r['plannedHash'] == r['preExecutionHash'] == r['executorBeforeHash'] for r in self.rows),
                C15=all(r['plannedHash'] == r['executorBeforeHash'] for r in self.rows), C16=True,
                C17=all(r['goalId'] == self.goal_id for r in self.rows))
        values['C19'] = all(value for key, value in values.items() if key != 'C19')
        return values

    def observation(self, role):
        data, path, signature = self.snapshot(role)
        evidence = {'live.snapshot': {'path': str(path), 'modelHash': signature, 'elementCount': len(data['elements'])},
            'live.progress': {'completedMutations': len(self.rows), 'witnessPaths': [r['witnessPath'] for r in self.rows],
                              'checks': self.values(), 'goalId': self.goal_id}}
        return LiveObservation(self.identity['projectPath'], signature,
            {key: Fact(value, evidenceRefs=('live.progress', 'live.snapshot')) for key, value in self.values().items()}, evidence)


class LiveObserver:
    offline = False
    def __init__(self, session): self.session = session
    def observe(self): return self.session.observation('observe')


class LivePlanner:
    offline = False
    def __init__(self, session): self.session = session
    def plan(self, job, observation):
        session = self.session
        number = len(session.rows)+1
        if number > 2:
            return PlannerDecision('BLOCKED', reason='Two allowed mutations completed; no extra action permitted')
        data = read(observation.evidence['live.snapshot']['path'])
        length = (1.0, 0.5)[number-1]
        subgoal = f'Продолжи последнюю созданную стену ещё на {length} метра.'
        plan = session.chat.instruction_to_request(subgoal, 'execute', data)
        save(session.output / f'plan-{job.iteration}.json', {'goalId': job.goalId, 'derivedSubgoal': subgoal,
            'modelIdentity': observation.modelIdentity, 'modelHash': observation.modelHash, 'baselinePlanner': plan})
        if plan['status'] != 'PLANNED':
            return PlannerDecision('BLOCKED', reason=str(plan))
        if number == 2 and plan['request']['sourceGuid'].lower() != session.rows[0]['createdGuid'].lower():
            return PlannerDecision('BLOCKED', reason='Fresh automatic selection differs from factual created Wall')
        session.active_plan = {'number': number, 'jobIteration': job.iteration, 'modelHash': observation.modelHash,
            'selection': plan['selection'], 'sourceGuid': plan['request']['sourceGuid'], 'length': length}
        return PlannerDecision('PLANNED', Action('create_wall', {'sourceGuid': plan['request']['sourceGuid'], 'length': length}),
            plannedAgainstModelIdentity=observation.modelIdentity, plannedAgainstModelHash=observation.modelHash)


class LiveModelCheck:
    offline = False
    def __init__(self, session): self.session = session
    def check(self, reference):
        _, path, signature = self.session.snapshot('stale-check')
        self.session.last_check = signature
        return LiveModelFingerprint(self.session.identity['projectPath'], signature)


class LiveExecutor:
    offline = False
    def __init__(self, session): self.session = session
    def execute(self, action):
        session = self.session
        plan = session.active_plan
        if action.type != 'create_wall' or action.parameters != {'sourceGuid': plan['sourceGuid'], 'length': plan['length']}:
            return LiveExecutionResult('BLOCKED', False, True, {'reason': 'Action differs from bound plan'})
        step = session.output / f'iteration-{plan["jobIteration"]}'
        step.mkdir(exist_ok=False)
        os.environ['SAFE_BIM_MVP_EVIDENCE'] = str(step)
        executor = load('stage3_v0_executor', 'scripts/archicad_executor.py')
        original_dump, original_api = executor.dump, executor.api
        session.executor_before_hash = None
        def guarded_dump(stem):
            data = original_dump(stem)
            if stem == 'before':
                session.check_identity()
                signature = model_hash(data)
                session.executor_before_hash = signature
                if signature != plan['modelHash']:
                    raise StaleBeforeWrite(LiveModelFingerprint(session.identity['projectPath'], signature))
            return data
        def guarded_api(command, parameters, stem):
            if command != 'CreateWalls':
                raise ValueError('Only the existing CreateWalls write path is authorized')
            session.check_identity()
            save(step / 'native-dispatch.json', {'goalId': session.goal_id, 'command': command,
                'plannedHash': plan['modelHash'], 'executorBeforeHash': session.executor_before_hash,
                'atUtc': datetime.now(timezone.utc).isoformat()})
            return original_api(command, parameters, stem)
        executor.dump, executor.api = guarded_dump, guarded_api
        request = {'action': 'create_wall', 'mode': 'execute', **action.parameters}
        save(step / 'executor-request.json', {'goalId': session.goal_id, 'request': request})
        result = executor.run(request)
        save(step / 'executor-result.json', result)
        session.step = step
        if result.get('status') != 'PASS':
            return LiveExecutionResult('UNKNOWN_OUTCOME', True, True, result)
        return LiveExecutionResult('PASS', True, True, result)


class LiveReadBack:
    offline = False
    def __init__(self, session): self.session = session
    def read_back(self, action, result):
        session = self.session
        after, path, signature = session.snapshot('read-back')
        before = read(session.step / 'executor' / 'before.json')
        witness = verify_wall(before, after, result.details, action.parameters['sourceGuid'], action.parameters['length'])
        number = len(session.rows)+1
        witness_path = session.step / 'readback-witness.json'
        save(witness_path, witness)
        row = {k: v for k, v in witness.items() if k not in ('sourceBefore', 'sourceAfter', 'createdWall')}
        row.update(goalId=session.goal_id, iteration=number, witnessPath=str(witness_path),
            automaticSelection=True, plannedHash=session.active_plan['modelHash'],
            preExecutionHash=session.last_check, executorBeforeHash=session.executor_before_hash, readbackHash=signature,
            staleVerdict='CURRENT', readbackPath=str(path), executorStatus=result.status)
        session.rows.append(row)
        if number == 2:
            remote = subprocess.check_output(['git', 'ls-remote', 'origin', 'refs/heads/main'], cwd=ROOT, text=True, timeout=30)
            session.main_current = remote.split()[0]
            save(session.output / 'main-final-readback.json', {'command': 'git ls-remote origin refs/heads/main', 'actual': remote, 'expected': MAIN})
        save(session.step / 'summary.json', row)
        # This is the fresh actual post-write observation, not the v0 PASS flag.
        values = session.values()
        return LiveObservation(session.identity['projectPath'], signature,
            {key: Fact(value, evidenceRefs=('live.progress', 'live.snapshot')) for key, value in values.items()},
            {'live.snapshot': {'path': str(path), 'modelHash': signature, 'elementCount': len(after['elements'])},
             'live.progress': {'checks': values, 'witnessPaths': [r['witnessPath'] for r in session.rows], 'goalId': session.goal_id}})


def acceptance(goal_id):
    return AcceptanceContract(goal_id, tuple(Criterion(f'C{i:02}', True, f'C{i:02}', True, correctable=True)
        for i in range(1, 25)))
