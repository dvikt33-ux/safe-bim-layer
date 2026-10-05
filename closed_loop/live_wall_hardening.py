"""Stage 4 adapters: only the unchanged v0 CreateWalls physical write path."""
from copy import deepcopy
from dataclasses import asdict
import os
from pathlib import Path

from .live_wall import (LiveExecutor, LiveReadBack, LiveModelCheck, LiveModelFingerprint,
    LiveExecutionResult, load, read, model_hash)
from .orchestrator import StaleBeforeWrite, BeforeMutationTransportError
from .wall_attempts import (AttemptJournal, durable_json, prepare_attempt, reconcile_attempt)


class ControlledWallExecutor(LiveExecutor):
    def __init__(self, session, fault=None):
        super().__init__(session)
        self.fault = fault
        self.active_attempt = None

    def prepare(self, job, action, observation):
        before = read(observation.evidence['live.snapshot']['path'])
        self.active_attempt = prepare_attempt(before, action, observation.modelIdentity, job.iteration, job.goalId)
        durable_json(self.session.output / f'attempt-prepared-{job.iteration}.json', self.active_attempt)
        return deepcopy(self.active_attempt)

    def execute(self, action):
        session, attempt = self.session, self.active_attempt
        if attempt is None or asdict(action) != attempt['action']:
            raise BeforeMutationTransportError('Missing or mismatched durable attempt')
        plan = session.active_plan
        if (action.type != 'create_wall' or action.parameters != {'sourceGuid': plan['sourceGuid'], 'length': plan['length']} or
                attempt['signature']['preModelHash'] != plan['modelHash']):
            raise BeforeMutationTransportError('Action differs from bound plan')
        step = session.output / f'iteration-{plan["jobIteration"]}'
        step.mkdir(exist_ok=False)
        session.step = step
        journal = AttemptJournal(session.output / 'mutation-attempts', attempt)
        journal.claim()
        os.environ['SAFE_BIM_MVP_EVIDENCE'] = str(step)
        executor = load('stage4_frozen_executor', 'scripts/archicad_executor.py')
        original_dump, original_api = executor.dump, executor.api
        session.executor_before_hash = None
        fault = self.fault
        self.fault = None  # one injection, never a second native replay

        def guarded_dump(stem):
            if stem != 'before' and fault == 'readback-unavailable':
                raise ConnectionError('Injected factual read-back failure after native response')
            data = original_dump(stem)
            if stem == 'before':
                session.check_identity()
                signature = model_hash(data)
                session.executor_before_hash = signature
                if signature != plan['modelHash']:
                    journal.mark_not_dispatched('Stale executor pre-write model')
                    raise StaleBeforeWrite(LiveModelFingerprint(session.identity['projectPath'], signature))
            return data

        def guarded_api(command, parameters, stem):
            if command != 'CreateWalls':
                if journal.value['dispatchStarted']:
                    raise RuntimeError('Unexpected command after mutation dispatch; outcome requires reconciliation')
                raise BeforeMutationTransportError('Only frozen CreateWalls may be dispatched')
            session.check_identity()
            if fault in ('before-transport', 'not-applied'):
                journal.mark_not_dispatched('Controlled fault before invoking the native mutation transport')
                if fault == 'before-transport':
                    raise BeforeMutationTransportError('Injected known pre-dispatch transport failure')
                raise TimeoutError('Injected uncertainty after EXECUTING checkpoint; confirmed zero native dispatch')
            native_request = {'command': command, 'parameters': parameters}
            journal.dispatch(native_request)
            durable_json(step / 'native-dispatch.json', {'goalId': session.goal_id,
                'mutationAttemptId': attempt['mutationAttemptId'], 'command': command,
                'plannedHash': plan['modelHash'], 'executorBeforeHash': session.executor_before_hash,
                'signature': attempt['signature'], 'request': native_request})
            result = original_api(command, parameters, stem)
            journal.confirm(result)
            if fault == 'lost-response':
                raise TimeoutError('Injected lost response after actual native CreateWalls')
            if fault == 'crash':
                # Dedicated child process only: a real process restart, after a
                # flushed receipt, before normal executor read-back/audit.
                os._exit(86)
            return result

        executor.dump, executor.api = guarded_dump, guarded_api
        request = {'action': 'create_wall', 'mode': 'execute', **action.parameters}
        durable_json(step / 'executor-request.json', {'goalId': session.goal_id,
                     'mutationAttemptId': attempt['mutationAttemptId'], 'request': request})
        try:
            result = executor.run(request)
        except (StaleBeforeWrite, BeforeMutationTransportError):
            raise
        except TimeoutError as exc:
            if not journal.value['dispatchStarted'] and fault != 'not-applied':
                journal.mark_not_dispatched(str(exc))
                raise BeforeMutationTransportError(str(exc)) from exc
            raise
        except Exception as exc:
            if not journal.value['dispatchStarted']:
                journal.mark_not_dispatched(str(exc))
                raise BeforeMutationTransportError(str(exc)) from exc
            if journal.value['phase'] != 'CONFIRMED':
                raise
            # A retained native receipt proves dispatch, never model acceptance.
            result = {'status': 'PASS', 'createdGuid': executor.guid_from(journal.value['nativeResponse'])}
        result = dict(result, mutationAttemptId=attempt['mutationAttemptId'],
                      nativeResponseConfirmed=journal.value['phase'] == 'CONFIRMED')
        durable_json(step / 'executor-result.json', result)
        status = 'PASS' if result.get('status') == 'PASS' else 'UNKNOWN_OUTCOME'
        return LiveExecutionResult(status, True, True, result)


class ControlledWallReadBack(LiveReadBack):
    def __init__(self, session, fault=None):
        super().__init__(session)
        self.fault = fault

    def read_back(self, action, result):
        if self.fault == 'readback-unavailable':
            self.fault = None
            raise ConnectionError('Injected fresh read-back failure; native receipt is not model evidence')
        return super().read_back(action, result)


class WallReconciler:
    offline = False
    def __init__(self, session):
        self.session = session

    def reconcile(self, attempt):
        session = self.session
        step = session.output / f'iteration-{attempt["iteration"]}'
        before = read(step / 'executor/before.json')
        current, path, signature = session.snapshot('reconciliation')
        journal_path = session.output / 'mutation-attempts' / (attempt['mutationAttemptId'] + '.json')
        journal = read(journal_path)
        verdict = reconcile_attempt(attempt, before, current, session.identity['projectPath'], journal)
        verdict.update(evidenceRefs=[str(path), str(journal_path)], factualReadback=True)
        durable_json(step / 'reconciliation.json', verdict)
        if verdict['status'] == 'RECONCILED_APPLIED':
            session.active_plan = {'number': len(session.rows)+1, 'jobIteration': attempt['iteration'],
                'modelHash': attempt['signature']['preModelHash'], 'sourceGuid': attempt['signature']['sourceGuid'],
                'length': attempt['signature']['expectedLength']}
            session.step = step
            session.last_check = session.executor_before_hash = attempt['signature']['preModelHash']
            result = LiveExecutionResult('PASS', True, True, {'createdGuid': verdict['createdGuid'],
                'mutationAttemptId': attempt['mutationAttemptId'], 'nativeResponseConfirmed': journal['phase'] == 'CONFIRMED'})
            observed = LiveReadBack(session).read_back(Action(**attempt['action']), result)
            # The actual observation used by the resumed Auditor is this second,
            # freshly bracketed capture. Bind the verdict to that exact hash.
            verdict['freshModelHash'] = observed.modelHash
            durable_json(step / 'reconciliation.json', verdict)
        else:
            observed = session.observation('reconciliation-observe')
            verdict['freshModelHash'] = observed.modelHash
            durable_json(step / 'reconciliation.json', verdict)
        return verdict, observed


# Imported here to keep the write allowlist visibly restricted above.
from .models import Action
