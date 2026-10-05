"""Offline-only Stage 2 state machine with durable per-step evidence."""
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timezone
import json
import hashlib
from pathlib import Path
from typing import Protocol

from .auditor import audit
from .models import (AcceptanceContract, Action, ExecutionResult, Iteration, Job,
                     ModelFingerprint, Observation, PlannerDecision, State, Verdict, nonempty)


class Observer(Protocol):
    offline: bool
    def observe(self) -> Observation: ...


class Planner(Protocol):
    offline: bool
    def plan(self, job: Job, observation: Observation) -> PlannerDecision: ...


class ModelCheck(Protocol):
    offline: bool
    def check(self, reference: Observation) -> ModelFingerprint: ...


class Executor(Protocol):
    offline: bool
    def execute(self, action: Action) -> ExecutionResult: ...


class ReadBack(Protocol):
    offline: bool
    def read_back(self, action: Action, result: ExecutionResult) -> Observation: ...


TERMINAL = {State.VERIFIED, State.WAITING_FOR_DATA, State.BLOCKED, State.UNKNOWN_OUTCOME}
TRANSITIONS = {
    State.RECEIVED: {State.OBSERVING},
    State.OBSERVING: {State.PLANNING, State.BLOCKED, State.WAITING_FOR_DATA},
    State.PLANNING: {State.OBSERVING, State.EXECUTING, State.BLOCKED, State.WAITING_FOR_DATA},
    State.EXECUTING: {State.READING_BACK, State.BLOCKED, State.UNKNOWN_OUTCOME},
    State.READING_BACK: {State.AUDITING, State.BLOCKED, State.UNKNOWN_OUTCOME},
    State.AUDITING: {State.VERIFIED, State.REPLANNING, State.WAITING_FOR_DATA, State.BLOCKED, State.UNKNOWN_OUTCOME},
    State.REPLANNING: {State.PLANNING, State.BLOCKED},
}


class IllegalTransition(ValueError):
    pass


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    ensure_ascii=False, allow_nan=False).encode('utf-8')).hexdigest()


def audit_decision(results):
    required = [r for r in results if r.required]
    if required and all(r.verdict == Verdict.PASS for r in required):
        return State.VERIFIED
    # Evidence deficiencies take precedence over a correctable geometry FAIL.
    if any(r.verdict in {Verdict.NOT_VERIFIED, Verdict.CONFLICT, Verdict.BLOCKED_BY_TRANSPORT} for r in required):
        return State.BLOCKED
    if any(r.verdict == Verdict.DATA_MISSING for r in required):
        return State.WAITING_FOR_DATA
    failures = [r for r in required if r.verdict == Verdict.FAIL]
    if failures and all(r.correctable for r in failures):
        return State.REPLANNING
    return State.BLOCKED


class Orchestrator:
    def __init__(self, contract: AcceptanceContract, specification: str,
                 observer: Observer, planner: Planner, executor: Executor, readback: ReadBack,
                 output: Path, max_iterations: int = 3, clock=None, model_check: ModelCheck | None = None,
                 no_progress_limit: int = 2):
        nonempty(specification, 'specification')
        if type(max_iterations) is not int or max_iterations < 1:
            raise ValueError('max_iterations must be a positive integer')
        if type(no_progress_limit) is not int or no_progress_limit < 2:
            raise ValueError('no_progress_limit must be an integer >= 2')
        if not isinstance(contract, AcceptanceContract):
            raise ValueError('typed AcceptanceContract required')
        model_check = model_check if model_check is not None else observer
        if not callable(getattr(model_check, 'check', None)):
            raise ValueError('typed offline model checker is required')
        if not all(getattr(component, 'offline', False) is True for component in (observer, planner, executor, readback, model_check)):
            raise ValueError('Stage 2 requires explicitly offline components')
        self.contract = deepcopy(contract)
        self.observer, self.planner, self.executor, self.readback = observer, planner, executor, readback
        self.model_check = model_check
        self.clock = clock or (lambda: datetime.now(timezone.utc).isoformat())
        self.output = Path(output)
        if self.output.exists():
            raise FileExistsError('Existing job evidence must not be overwritten or retried')
        now = self.clock()
        self.job = Job(contract.goalId, specification, deepcopy(contract.criteria), max_iterations, now, now)
        self.job.noProgressLimit = no_progress_limit
        self._record('received', {'contract': {'goalId': contract.goalId, 'criteria': self.job.to_dict()['acceptanceCriteria']}})

    def _save(self):
        self.output.parent.mkdir(parents=True, exist_ok=True)
        pending = self.output.with_name(self.output.name + '.pending')
        pending.write_text(json.dumps(self.job.to_dict(), ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
        pending.replace(self.output)

    def _record(self, kind, payload):
        self.job.updatedAt = self.clock()
        self.job.evidenceTrail.append({'sequence': len(self.job.evidenceTrail)+1,
            'at': self.job.updatedAt, 'iteration': self.job.iteration, 'state': self.job.state,
            'kind': kind, 'payload': deepcopy(payload)})
        self._save()

    def transition(self, target: State, reason=''):
        source = self.job.state
        if target not in TRANSITIONS.get(source, set()):
            raise IllegalTransition(f'{source.value} -> {target.value} is forbidden')
        if target == State.VERIFIED:
            if not self.job.auditHistory or not self.job.iterations or self.job.iterations[-1].readback is None:
                raise IllegalTransition('VERIFIED requires actual audit/read-back evidence')
            latest = self.job.auditHistory[-1]
            computed = audit(self.contract, self.job.iterations[-1].readback)
            if latest != computed or audit_decision(computed) != State.VERIFIED:
                raise IllegalTransition('VERIFIED requires every required criterion PASS')
        self.job.state = target
        if target in TERMINAL:
            self.job.finalStatus, self.job.terminalReason = target.value, reason
        self._record('transition', {'before': source, 'after': target, 'reason': reason})

    def _observe(self, value):
        if not isinstance(value, Observation):
            raise ValueError('typed Observation required')
        self.job.observedModelIdentity = value.modelIdentity
        self.job.observedModelHash = value.modelHash
        return deepcopy(value)

    def run(self) -> Job:
        if self.job.state != State.RECEIVED:
            raise IllegalTransition('Only a newly RECEIVED job may run; terminal jobs cannot auto-retry')
        self.transition(State.OBSERVING)
        try:
            observed = self._observe(self.observer.observe())
        except Exception as exc:
            self.transition(State.BLOCKED, f'observation failed: {type(exc).__name__}: {exc}')
            return deepcopy(self.job)
        self._record('observation', asdict(observed))
        self.transition(State.PLANNING)
        while self.job.iteration < self.job.maxIterations:
            self.job.iteration += 1
            step = Iteration(self.job.iteration, self.job.state, observation=deepcopy(observed), observedModelHash=observed.modelHash)
            self.job.iterations.append(step)
            self._record('iteration-start', {'modelIdentity': observed.modelIdentity, 'modelHash': observed.modelHash})
            try:
                decision = self.planner.plan(deepcopy(self.job), deepcopy(observed))
                if not isinstance(decision, PlannerDecision):
                    raise ValueError('typed PlannerDecision required')
                step.plannerDecision = deepcopy(decision)
            except Exception as exc:
                self.transition(State.BLOCKED, f'planner failed: {type(exc).__name__}: {exc}')
                break
            if decision.status != 'PLANNED':
                self.transition(State(decision.status), decision.reason)
                break
            step.planningModelHash = decision.plannedAgainstModelHash
            step.actionFingerprint = fingerprint(asdict(decision.action))
            if decision.plannedAgainstModelHash is None or decision.plannedAgainstModelIdentity is None:
                self.transition(State.BLOCKED, 'Planner decision lacks model identity/hash binding')
                break
            try:
                current = self.model_check.check(deepcopy(observed))
                if not isinstance(current, ModelFingerprint):
                    raise ValueError('typed ModelFingerprint required')
                step.preExecutionFingerprint = deepcopy(current)
            except Exception as exc:
                self.transition(State.BLOCKED, f'pre-execution model check failed: {type(exc).__name__}: {exc}')
                break
            stale = ((decision.plannedAgainstModelIdentity, decision.plannedAgainstModelHash) !=
                     (observed.modelIdentity, observed.modelHash) or
                     (current.modelIdentity, current.modelHash) !=
                     (decision.plannedAgainstModelIdentity, decision.plannedAgainstModelHash))
            step.staleVerdict = 'STALE' if stale else 'CURRENT'
            self._record('model-check', {'plannedAgainst': {
                'modelIdentity': decision.plannedAgainstModelIdentity, 'modelHash': decision.plannedAgainstModelHash},
                'current': asdict(current), 'staleVerdict': step.staleVerdict})
            if stale:
                step.decisionInvalidated = True
                self._record('stale-decision-invalidated', {'actionFingerprint': step.actionFingerprint,
                    'plannedHash': decision.plannedAgainstModelHash, 'currentHash': current.modelHash,
                    'executorCalled': False})
                if self.job.iteration >= self.job.maxIterations:
                    self.transition(State.BLOCKED, 'iteration limit reached while invalidating stale plans')
                    break
                self.transition(State.OBSERVING, 'stale decision invalidated; fresh observation required')
                try:
                    observed = self._observe(self.observer.observe())
                except Exception as exc:
                    self.transition(State.BLOCKED, f're-observation failed: {type(exc).__name__}: {exc}')
                    break
                self._record('observation', asdict(observed))
                self.transition(State.PLANNING)
                continue
            step.executorRequest = deepcopy(decision.action)
            self.job.actions.append(deepcopy(decision.action))
            self.transition(State.EXECUTING)
            try:
                result = self.executor.execute(deepcopy(decision.action))
                if not isinstance(result, ExecutionResult):
                    raise ValueError('typed ExecutionResult required')
                step.executorResult = deepcopy(result)
            except Exception as exc:
                self.transition(State.UNKNOWN_OUTCOME, f'executor outcome unavailable: {type(exc).__name__}: {exc}')
                break
            if result.status != 'PASS':
                target = State.UNKNOWN_OUTCOME if result.mutationAttempted or result.status == 'UNKNOWN_OUTCOME' else State.BLOCKED
                self.transition(target, f'executor returned {result.status}')
                break
            if not result.readbackRequired:
                self.transition(State.BLOCKED, 'Executor PASS cannot replace read-back')
                break
            self.transition(State.READING_BACK)
            try:
                updated = self.readback.read_back(deepcopy(decision.action), deepcopy(result))
                if not isinstance(updated, Observation):
                    raise ValueError('typed read-back Observation required')
            except Exception as exc:
                self.transition(State.UNKNOWN_OUTCOME if result.mutationAttempted else State.BLOCKED,
                                f'read-back unavailable: {type(exc).__name__}: {exc}')
                break
            step.readback = deepcopy(updated)
            if updated.modelIdentity != observed.modelIdentity:
                self.transition(State.BLOCKED, 'read-back model identity differs from observation')
                break
            observed = self._observe(updated)
            self.transition(State.AUDITING)
            step.auditResult = audit(self.contract, observed)
            self.job.auditHistory.append(deepcopy(step.auditResult))
            target = audit_decision(step.auditResult)
            unresolved = sorted([{'id': r.id, 'verdict': r.verdict, 'actual': r.actual}
                for r in step.auditResult if r.required and r.verdict != Verdict.PASS], key=lambda r: r['id'])
            step.auditFingerprint = fingerprint(unresolved)
            step.progressSignature = fingerprint({'modelIdentity': observed.modelIdentity, 'modelHash': observed.modelHash,
                'unresolved': unresolved, 'actionFingerprint': step.actionFingerprint})
            previous = self.job.iterations[-2] if len(self.job.iterations) > 1 else None
            self.job.noProgressCount = previous.noProgressCount + 1 if previous and previous.progressSignature == step.progressSignature else 1
            step.noProgressCount = self.job.noProgressCount
            self._record('progress-check', {'modelHash': observed.modelHash, 'actionFingerprint': step.actionFingerprint,
                'auditFingerprint': step.auditFingerprint, 'progressSignature': step.progressSignature,
                'noProgressCount': step.noProgressCount, 'noProgressLimit': self.job.noProgressLimit})
            if target == State.REPLANNING and step.noProgressCount >= self.job.noProgressLimit:
                self.transition(State.BLOCKED, 'BLOCKED_NO_PROGRESS')
                break
            self.transition(target, 'decision from required acceptance criteria')
            if target in TERMINAL:
                break
            if self.job.iteration >= self.job.maxIterations:
                self.transition(State.BLOCKED, 'iteration limit reached with required criteria unresolved')
                break
            self.transition(State.PLANNING)
        return deepcopy(self.job)
