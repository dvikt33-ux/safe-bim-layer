import json
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from closed_loop.auditor import audit
from closed_loop.live_wall import model_hash
from closed_loop.models import (
    AcceptanceContract, Action, Criterion, ExecutionResult, Fact,
    ModelFingerprint, Observation, PlannerDecision, WindowAction,
)
from closed_loop.orchestrator import Orchestrator
from closed_loop.window_attempts import prepare_window_attempt
from closed_loop.wall_attempts import job_from_dict
from tests_stage5_window.test_window_attempts import fixture


class WindowObserver:
    offline = True

    def __init__(self, data):
        self.data = deepcopy(data)
        self.check_hash = model_hash(self.data)
        self.observe_calls = 0

    def _observation(self):
        self.observe_calls += 1
        return Observation(
            'fixture.pln',
            model_hash(self.data),
            {
                'windowCreated': Fact(False, evidenceRefs=('model',)),
                'hostMatches': Fact(False, evidenceRefs=('model',)),
                'apertureChanged': Fact(False, evidenceRefs=('model',)),
            },
            {'model': deepcopy(self.data)},
        )

    def observe(self):
        return self._observation()

    def check(self, reference):
        return ModelFingerprint('fixture.pln', self.check_hash)


class WindowPlanner:
    offline = True

    def __init__(self, action):
        self.action = action
        self.calls = 0

    def plan(self, job, observation):
        self.calls += 1
        return PlannerDecision(
            'PLANNED',
            deepcopy(self.action),
            plannedAgainstModelIdentity=observation.modelIdentity,
            plannedAgainstModelHash=observation.modelHash,
        )


class WindowExecutor:
    offline = True

    def __init__(self):
        self.active = None
        self.calls = 0

    def prepare(self, job, action, observed):
        self.active = prepare_window_attempt(
            observed.evidence['model'], action, observed.modelIdentity, job.iteration, job.goalId)
        return deepcopy(self.active)

    def execute(self, action):
        self.calls += 1
        return ExecutionResult(
            'PASS', True, True,
            {'mutationAttemptId': self.active['mutationAttemptId'], 'nativeResponseConfirmed': True},
        )


class WindowReadBack:
    offline = True

    def __init__(self, after):
        self.after = deepcopy(after)
        self.calls = 0

    def read_back(self, action, result):
        self.calls += 1
        created = next(e for e in self.after['elements'] if e.get('type') == 'Window')
        host = next(e for e in self.after['elements'] if e.get('guid') == action.parameters['sourceGuid'])
        ref = created['placement']['referenceGeometry']
        return Observation(
            'fixture.pln',
            model_hash(self.after),
            {
                'windowCreated': Fact(True, evidenceRefs=('model', 'window')),
                'hostMatches': Fact(
                    created['relationships']['hostGuid'].lower() == host['guid'].lower(),
                    evidenceRefs=('model', 'window')),
                'centerOffset': Fact(ref['centerOffsetAlongHost'], evidenceRefs=('model', 'window')),
                'apertureChanged': Fact(True, evidenceRefs=('model', 'host')),
            },
            {
                'model': deepcopy(self.after),
                'window': deepcopy(created),
                'host': deepcopy(host),
            },
        )


def contract():
    return AcceptanceContract('stage5-window-offline', (
        Criterion('W01', True, 'windowCreated', True),
        Criterion('W02', True, 'hostMatches', True),
        Criterion('W03', True, 'centerOffset', 5.0, tolerance=1e-7),
        Criterion('W04', True, 'apertureChanged', True),
    ))


class WindowOrchestratorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.before, self.after, self.action, _ = fixture()
        self.observer = WindowObserver(self.before)
        self.planner = WindowPlanner(self.action)
        self.executor = WindowExecutor()
        self.reader = WindowReadBack(self.after)

    def build(self):
        return Orchestrator(
            contract(),
            'Create one Hosted Window in the factual host Wall and verify it by read-back.',
            self.observer,
            self.planner,
            self.executor,
            self.reader,
            self.root/'job.json',
            max_iterations=2,
            model_check=self.observer,
            execution_mode='OFFLINE',
        )

    def test_one_window_closed_loop_reaches_verified(self):
        job = self.build().run()
        self.assertEqual(job.finalStatus, 'VERIFIED')
        self.assertEqual(self.executor.calls, 1)
        self.assertEqual(self.reader.calls, 1)
        self.assertEqual(len(job.mutationAttempts), 1)
        self.assertEqual(job.actions[0].type, 'create_window')
        self.assertEqual(job.actions[0].parameters['sourceGuid'], 'host')
        self.assertTrue(all(row.verdict.value == 'PASS' for row in job.auditHistory[-1]))

    def test_persisted_window_action_restores_as_window_action(self):
        job = self.build().run()
        restored = job_from_dict(json.loads(json.dumps(job.to_dict())))
        self.assertIsInstance(restored.actions[0], WindowAction)
        self.assertIsInstance(restored.iterations[0].plannerDecision.action, WindowAction)
        self.assertIsInstance(restored.iterations[0].executorRequest, WindowAction)

    def test_stale_host_model_invalidates_plan_without_executor_call(self):
        orch = self.build()
        self.observer.check_hash = 'external-change'
        job = orch.run()
        self.assertEqual(self.executor.calls, 0)
        self.assertTrue(job.iterations[0].decisionInvalidated)
        self.assertEqual(job.iterations[0].staleVerdict, 'STALE')
        self.assertNotEqual(job.finalStatus, 'VERIFIED')

    def test_readback_missing_required_window_fact_never_verifies(self):
        orch = self.build()
        original = self.reader.read_back

        def incomplete(action, result):
            observed = original(action, result)
            facts = dict(observed.facts)
            facts.pop('apertureChanged')
            return Observation(observed.modelIdentity, observed.modelHash, facts, observed.evidence)

        self.reader.read_back = incomplete
        job = orch.run()
        self.assertEqual(job.finalStatus, 'WAITING_FOR_DATA')
        self.assertEqual(self.executor.calls, 1)


if __name__ == '__main__':
    unittest.main()
