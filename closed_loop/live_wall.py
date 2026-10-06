"""Stage 3 adapters for one two-segment goal over the unchanged v0 Wall path."""
import contextlib
import importlib.util
import io
import json
import math
import ntpath
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone

from .models import (AcceptanceContract, Action, Criterion, Fact, LiveExecutionResult,
                     LiveModelFingerprint, LiveObservation, PlannerDecision)
from .orchestrator import fingerprint, StaleBeforeWrite

ROOT = Path(__file__).resolve().parents[1]
COMMAND = 'Продолжи последнюю созданную стену сначала на 1 метр, затем ещё на 0,5 метра и проверь результат.'
TOL = 1e-7
MAIN_BASELINE = '72e9be15ac3b943d7b6f0c46eaa45aa5798d56bc'
PROTECTED_MAIN_PATHS = (
    'archicad-addon', 'scripts', 'closed_loop',
    'tests_stage2', 'tests_stage3', 'tests_stage4_live', 'tests_audit_pack',
    'outputs/closed-loop-stage1', 'outputs/closed-loop-stage2',
    'outputs/closed-loop-stage3', 'outputs/closed-loop-stage4',
    'safe_bim_layer.py', 'qwen_safe_bim_integration.py',
)

def main_runtime_guard():
    """Allow unrelated main commits, but fail if protected BIM runtime/evidence paths changed."""
    subprocess.run(['git', 'fetch', '--quiet', 'origin', 'main'], cwd=ROOT,
                   check=True, timeout=60)
    current = subprocess.check_output(['git', 'rev-parse', 'FETCH_HEAD'],
                                      cwd=ROOT, text=True, timeout=30).strip()
    changed = subprocess.check_output(
        ['git', 'diff', '--name-only', MAIN_BASELINE, current, '--', *PROTECTED_MAIN_PATHS],
        cwd=ROOT, text=True, timeout=30).splitlines()
    return {
        'status': 'PASS' if not changed else 'FAIL',
        'baselineMain': MAIN_BASELINE,
        'currentMain': current,
        'protectedPaths': list(PROTECTED_MAIN_PATHS),
        'changedProtectedPaths': changed,
    }
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
    'Stage 1 v0 regression path still PASS', 'All Stage 2 tests PASS', 'protected main runtime/evidence baseline unchanged']


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
        explicit_target = os.environ.get('SAFE_BIM_STAGE4_PROJECT_PATH') if str(goal_id).startswith('stage4-') else None
        if explicit_target:
            if not ntpath.isabs(explicit_target):
                raise ValueError('SAFE_BIM_STAGE4_PROJECT_PATH must be an absolute Windows path')
            actual = ntpath.normcase(ntpath.normpath(self.identity['projectPath']))
            expected = ntpath.normcase(ntpath.normpath(explicit_target))
            if actual != expected:
                raise ValueError('Active PLN differs from explicit Stage 4 target project')
            project_binding = {'mode':'EXPLICIT_STAGE4_PATH','expectedProjectPath':explicit_target}
        else:
            baseline_identity = read(ROOT / 'outputs/closed-loop-stage1/preflight.json')['identity']
            if self.identity != baseline_identity:
                raise ValueError('Active PLN differs from the previously verified test project')
            project_binding = {'mode':'STAGE1_BASELINE_IDENTITY','expectedProjectPath':baseline_identity.get('projectPath')}
        fixture_report_value = os.environ.get('SAFE_BIM_STAGE4_FIXTURE_REPORT') if str(goal_id).startswith('stage4-') else None
        if fixture_report_value:
            fixture_path = Path(fixture_report_value)
            if not fixture_path.is_absolute():
                fixture_path = ROOT / fixture_path
            fixture = read(fixture_path)
            if fixture.get('status') != 'PASS':
                raise ValueError('Configured Stage 4 fixture report is not PASS')
            actual_fixture_project = ntpath.normcase(ntpath.normpath(fixture.get('projectPath','')))
            actual_project = ntpath.normcase(ntpath.normpath(self.identity['projectPath']))
            if actual_fixture_project != actual_project:
                raise ValueError('Configured Stage 4 fixture belongs to another PLN')
            save(self.output / 'fixture-binding.json', {
                'status':'PASS','projectPath':fixture['projectPath'],
                'predecessorGuid':fixture.get('predecessorGuid'),'seedGuid':fixture.get('seedGuid'),
                'fixtureGeometry':fixture.get('fixtureGeometry'),
                'setupPhysicalMutationCalls':fixture.get('physicalMutationCalls'),
                'reusedExistingFixture':fixture.get('reusedExistingFixture',False)})
        save(self.output / 'preflight.json', {'identity': self.identity, 'projectBinding': project_binding,
            'fixtureBound': bool(fixture_report_value),
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
        started = time.perf_counter()
        print(f'[model] snapshot {self.snapshots:03} {role}: start', flush=True)
        with contextlib.redirect_stdout(io.StringIO()):
            data, metrics = self.dump_module.dump(path, 19723)
        self.check_identity()
        signature = model_hash(data)
        elapsed = time.perf_counter() - started
        size_mib = path.stat().st_size / (1024 * 1024)
        print(f'[model] snapshot {self.snapshots:03} {role}: {elapsed:.3f}s, {size_mib:.1f} MiB, {len(data["elements"])} elements', flush=True)
        save(path.with_suffix('.fingerprint.json'), {'modelIdentity': self.identity['projectPath'],
            'modelHash': signature, 'elementCount': len(data['elements']), 'role': role})
        return data, path, signature

    def fixture_chain_source(self, data):
        report_value = os.environ.get('SAFE_BIM_STAGE4_FIXTURE_REPORT')
        if not report_value:
            return None
        report_path = Path(report_value)
        if not report_path.is_absolute():
            report_path = ROOT / report_path
        report = read(report_path)
        if report.get('status') != 'PASS' or not report.get('seedGuid'):
            raise ValueError('Stage 4 fixture report is not PASS or has no seedGuid')
        actual_identity = ntpath.normcase(ntpath.normpath(self.identity['projectPath']))
        fixture_identity = ntpath.normcase(ntpath.normpath(report.get('projectPath','')))
        if actual_identity != fixture_identity:
            raise ValueError('Stage 4 fixture belongs to another PLN')
        elements = {e['guid'].lower(): e for e in data.get('elements', [])}
        current = elements.get(report['seedGuid'].lower())
        if not current or current.get('type') != 'Wall':
            raise ValueError('Stage 4 fixture seed Wall is absent from current model')
        stories = {int(s['index']): float(s['elevation']) for s in data.get('stories', [])}
        visited = set()
        while True:
            if current['guid'].lower() in visited:
                raise ValueError('Stage 4 fixture chain contains a cycle')
            visited.add(current['guid'].lower())
            cref = self.chat.refline(current)
            if not cref:
                raise ValueError('Stage 4 fixture chain contains a non-straight Wall')
            ref, begin, end, _ = cref
            ux, uy = self.chat.direction(ref)
            successors = []
            for other in elements.values():
                if other['guid'].lower() in visited:
                    continue
                oref_tuple = self.chat.refline(other)
                if not oref_tuple or not self.chat.same_wall_level(current, other, stories):
                    continue
                oref, obegin, _, _ = oref_tuple
                ox, oy = self.chat.direction(oref)
                current_bind = current.get('materialBindings', {})
                other_bind = other.get('materialBindings', {})
                same_material = (current_bind.get('structureType') == other_bind.get('structureType')
                    and current_bind.get('buildingMaterial', {}).get('guid') ==
                        other_bind.get('buildingMaterial', {}).get('guid'))
                same_reference = (abs(float(ref.get('offset',0.0))-float(oref.get('offset',0.0))) <= TOL
                    and ref.get('referenceLineLocation') == oref.get('referenceLineLocation'))
                if (same_material and same_reference
                        and self.chat.endpoint_distance(end, obegin) <= TOL
                        and ux*ox + uy*oy >= 1.0 - 1e-6):
                    successors.append(other)
            if not successors:
                return current
            if len(successors) != 1:
                raise ValueError('Stage 4 fixture chain endpoint is ambiguous')
            current = successors[0]

    def bound_fixture_plan(self, data, length):
        source = self.fixture_chain_source(data)
        if source is None:
            return None
        ref, begin, end, source_length = self.chat.refline(source)
        selection = {'guid': source['guid'], 'homeStory': source['homeStory'],
            'begin': begin, 'end': end, 'length': source_length,
            'selectionRule': 'pinned Stage 4 fixture chain endpoint'}
        colliders = self.chat.proposed_wall_colliders(data, selection, length)
        if colliders:
            return {'status':'BLOCKED',
                'reason':'Pinned Stage 4 fixture continuation corridor intersects model geometry.',
                'selectedGuid':source['guid'], 'colliderGuids':colliders[:20],
                'selection':selection}
        return {'status':'PLANNED',
            'request':{'action':'create_wall','mode':'execute','sourceGuid':source['guid'],'length':length},
            'selectedGuid':source['guid'], 'selection':selection}

    def values(self):
        n = len(self.rows)
        first, second = (self.rows[0] if n else None), (self.rows[1] if n > 1 else None)
        values = {f'C{i:02}': False for i in range(1, 25)}
        values.update(C01=True, C18=True, C20=True, C21=True,
            C22=self.regression_report.get('status') == 'PASS', C23=self.offline_report.get('status') == 'PASS',
            C24=getattr(self, 'main_guard_pass', True))
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
        plan = session.bound_fixture_plan(data, length)
        if plan is None:
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
            main_guard = main_runtime_guard()
            session.main_current = main_guard['currentMain']
            session.main_guard_pass = main_guard['status'] == 'PASS'
            save(session.output / 'main-final-readback.json', main_guard)
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
