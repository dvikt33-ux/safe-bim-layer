"""Deterministic fixture-only interfaces. No transport or model writes."""
from copy import deepcopy
from .models import Action, ExecutionResult, Observation, PlannerDecision


class FixtureObserver:
    offline = True

    def __init__(self, observation: Observation):
        self.observation = deepcopy(observation)
        self.calls = 0

    def observe(self):
        self.calls += 1
        return deepcopy(self.observation)


class FixedPlanner:
    offline = True

    def __init__(self, decision: PlannerDecision):
        self.decision = deepcopy(decision)
        self.observedHashes = []

    def plan(self, job, observation):
        self.observedHashes.append(observation.modelHash)
        return deepcopy(self.decision)


class MockExecutor:
    offline = True

    def __init__(self, result=None):
        self.result = result or ExecutionResult('PASS', True, True, {'simulation': True})
        self.requests: list[Action] = []

    def execute(self, action):
        self.requests.append(deepcopy(action))
        return deepcopy(self.result)


class FixtureReadBack:
    offline = True

    def __init__(self, observations):
        self.observations = deepcopy(list(observations))
        self.calls = 0

    def read_back(self, action, result):
        if self.calls >= len(self.observations):
            raise RuntimeError('No read-back fixture available; outcome must not be retried')
        value = self.observations[self.calls]
        self.calls += 1
        return deepcopy(value)
