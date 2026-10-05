"""Offline fixtures shared by completion tests and saved acceptance evidence."""
from copy import deepcopy
from closed_loop.models import AcceptanceContract, Action, Criterion, Fact, ModelFingerprint, Observation, PlannerDecision
from closed_loop.mocks import FixtureObserver, FixtureReadBack, FixedPlanner, MockExecutor
from closed_loop.orchestrator import Orchestrator


def observed(model_hash, actual=0.5):
    return Observation('fixture-model', model_hash,
        {'length': Fact(actual, evidenceRefs=('fixture.measurement',))}, {'fixture.measurement': {'actual': actual}})


class SequenceObserver(FixtureObserver):
    def __init__(self, observations):
        super().__init__(observations[0])
        self.observations = deepcopy(observations)

    def observe(self):
        value = self.observations[self.calls]
        self.calls += 1
        return deepcopy(value)


class ChangedFixtureCheck:
    offline = True

    def __init__(self, executor):
        self.executor = executor
        self.executorCountsAtCheck = []

    def check(self, reference):
        self.executorCountsAtCheck.append(len(self.executor.requests))
        return ModelFingerprint('fixture-model', 'hash-B')


class HashPlanner(FixedPlanner):
    def __init__(self, stop_after_stale=False):
        super().__init__(PlannerDecision('PLANNED', Action('create_wall', {})))
        self.stop_after_stale = stop_after_stale

    def plan(self, job, observation):
        self.decision = PlannerDecision('PLANNED', Action('create_wall', {'plannedHash': observation.modelHash}))
        if self.stop_after_stale and observation.modelHash == 'hash-B':
            self.decision = PlannerDecision('BLOCKED', reason='fixture intentionally stops after re-observation')
        return super().plan(job, observation)


def build_case(name, output):
    executor = MockExecutor()
    planner = FixedPlanner(PlannerDecision('PLANNED', Action('create_wall', {'length': 1.0})))
    observer = FixtureObserver(observed('same-hash'))
    check = None
    if name in ('stale-rejected', 'stale-replan'):
        observer = SequenceObserver([observed('hash-A'), observed('hash-B')])
        planner = HashPlanner(stop_after_stale=name == 'stale-rejected')
        check = ChangedFixtureCheck(executor)
        after = [observed('hash-C', 1.0)]
    elif name == 'no-progress':
        after = [observed('same-hash'), observed('same-hash')]
    elif name == 'changed-model':
        after = [observed('hash-1'), observed('hash-2'), observed('hash-3', 1.0)]
    elif name == 'changed-audit':
        after = [observed('same-hash', 0.5), observed('same-hash', 0.75), observed('same-hash', 1.0)]
    else:
        raise ValueError(name)
    acceptance = AcceptanceContract('stage2-completion-'+name, (Criterion('C01', True, 'length', 1.0, 1e-6, True),))
    orch = Orchestrator(acceptance, 'Offline Stage 2 completion: '+name, observer, planner,
        executor, FixtureReadBack(after), output, max_iterations=5, model_check=check,
        no_progress_limit=2, clock=lambda: '2026-10-05T00:00:00+00:00')
    return orch, observer, planner, executor, check
