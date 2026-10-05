from dataclasses import replace
from pathlib import Path
import tempfile
import unittest

from closed_loop.models import Action, LiveObservation, Fact
from tests_stage3 import test_live_adapters


class LivePathGuardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

    def build(self):
        return test_live_adapters.AdapterTests().build(Path(self.temp.name)/'job.json')

    def test_no_progress_is_independent_and_blocks_in_live_adapter_path(self):
        orch, executor = self.build()
        observed = orch.observer.observe()
        orch.readback.read_back = lambda action, result: observed
        job = orch.run()
        self.assertEqual(job.terminalReason, 'BLOCKED_NO_PROGRESS')
        self.assertEqual(job.iteration, 2)
        self.assertLess(job.iteration, job.maxIterations)
        self.assertEqual(executor.calls, 2)

    def test_iteration_limit_with_changing_live_adapter_fingerprint(self):
        orch, executor = self.build()
        orch.job.maxIterations = 3
        observed = orch.observer.observe()
        calls = []
        def reader(action, result):
            calls.append(True)
            return replace(observed, modelHash='changing-'+str(len(calls)))
        orch.readback.read_back = reader
        job = orch.run()
        self.assertEqual(job.finalStatus, 'BLOCKED')
        self.assertIn('BLOCKED_ITERATION_LIMIT', job.terminalReason)
        self.assertNotIn('NO_PROGRESS', job.terminalReason)
        self.assertEqual(executor.calls, 3)

    def test_external_between_iteration_change_is_seen_by_next_planning(self):
        orch, executor = self.build()
        first = orch.observer.observe()
        external = replace(first, modelHash='external-model-B')
        observations = iter([first, external])
        orch.observer.observe = lambda: next(observations)
        planned = []
        original = orch.planner.plan
        def planner(job, observed):
            planned.append(observed.modelHash)
            decision = original(job, observed)
            return replace(decision, action=Action('create_wall', {'plannedModelHash': observed.modelHash}))
        orch.planner.plan = planner
        job = orch.run()
        self.assertEqual(job.finalStatus, 'VERIFIED')
        self.assertEqual(planned, [first.modelHash, 'external-model-B'])
        self.assertEqual(job.iterations[1].planningModelHash, 'external-model-B')

    def test_confirmed_native_response_without_readback_blocks_transport_not_verified(self):
        orch, executor = self.build()
        execute = executor.execute
        executor.execute = lambda action: replace(execute(action), details={'nativeResponseConfirmed': True})
        def fail(action, result): raise ConnectionError('factual read-back unavailable')
        orch.readback.read_back = fail
        job = orch.run()
        self.assertEqual(job.finalStatus, 'BLOCKED')
        self.assertIn('BLOCKED_BY_TRANSPORT', job.terminalReason)
        self.assertEqual(executor.calls, 1)


if __name__ == '__main__': unittest.main()
