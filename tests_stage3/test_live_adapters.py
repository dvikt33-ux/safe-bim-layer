from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from dataclasses import replace

from closed_loop.live_wall import model_hash, verify_wall
from closed_loop.models import (AcceptanceContract, Criterion, Action, Fact, PlannerDecision,
    LiveObservation, LiveModelFingerprint, LiveExecutionResult)
from closed_loop.orchestrator import Orchestrator, StaleBeforeWrite


class AdapterTests(unittest.TestCase):
    def test_fingerprint_ignores_timing_and_element_order_but_tracks_geometry(self):
        a = {'nativeSeconds': 1.0, 'elements': [{'guid': 'a', 'x': 1}, {'guid': 'b', 'x': 2}], 'stories': []}
        b = {'nativeSeconds': 9.0, 'elements': list(reversed(a['elements'])), 'stories': []}
        self.assertEqual(model_hash(a), model_hash(b))
        b['elements'] = [{'guid': 'a', 'x': 3}, {'guid': 'b', 'x': 2}]
        self.assertNotEqual(model_hash(a), model_hash(b))

    def build(self, output, timeout=False, stale=False):
        def observation(count):
            return LiveObservation('test-model', f'hash-{count}', {'segments': Fact(count, evidenceRefs=('test',))},
                                   {'test': {'simulated': True, 'segments': count}})
        class Observer:
            offline = False
            def observe(self): return observation(0)
            def check(self, reference): return LiveModelFingerprint(reference.modelIdentity, reference.modelHash)
        class Planner:
            offline = False
            def plan(self, job, observed):
                return PlannerDecision('PLANNED', Action('create_wall', {}),
                    plannedAgainstModelIdentity=observed.modelIdentity, plannedAgainstModelHash=observed.modelHash)
        class Executor:
            offline = False
            calls = 0
            def execute(self, action):
                self.calls += 1
                if timeout: raise TimeoutError('synthetic adapter failure')
                if stale and self.calls == 1: raise StaleBeforeWrite(LiveModelFingerprint('test-model', 'changed'))
                return LiveExecutionResult('PASS', True, True, {'simulated': True})
        class Reader:
            offline = False
            calls = 0
            def read_back(self, action, result):
                self.calls += 1
                return observation(self.calls)
        executor = Executor()
        orch = Orchestrator(AcceptanceContract('unit-job', (Criterion('C', True, 'segments', 2, correctable=True),)),
            'Synthetic live-interface unit test; no Archicad transport', Observer(), Planner(), executor, Reader(),
            output, max_iterations=4, execution_mode='LIVE')
        return orch, executor

    def test_live_mode_gate_waits_for_second_readback(self):
        with tempfile.TemporaryDirectory() as temp, patch('socket.socket', side_effect=AssertionError('No network')):
            orch, executor = self.build(Path(temp)/'job.json')
            job = orch.run()
            self.assertEqual(job.finalStatus, 'VERIFIED')
            self.assertEqual(executor.calls, 2)
            self.assertEqual(job.auditHistory[0][0].verdict, 'FAIL')
            self.assertEqual(job.auditHistory[1][0].verdict, 'PASS')

    def test_live_timeout_stops_without_retry(self):
        with tempfile.TemporaryDirectory() as temp, patch('socket.socket', side_effect=AssertionError('No network')):
            orch, executor = self.build(Path(temp)/'job.json', timeout=True)
            self.assertEqual(orch.run().finalStatus, 'UNKNOWN_OUTCOME')
            self.assertEqual(executor.calls, 1)

    def test_executor_prewrite_stale_reobserves_without_repeating_mutation(self):
        with tempfile.TemporaryDirectory() as temp, patch('socket.socket', side_effect=AssertionError('No network')):
            orch, executor = self.build(Path(temp)/'job.json', stale=True)
            job = orch.run()
            self.assertEqual(job.finalStatus, 'VERIFIED')
            self.assertEqual(executor.calls, 3)  # one rejected preflight, only two simulated writes
            self.assertTrue(job.iterations[0].decisionInvalidated)
            self.assertIsNone(job.iterations[0].executorResult)


if __name__ == '__main__': unittest.main()
