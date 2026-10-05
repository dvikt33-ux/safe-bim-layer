from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from closed_loop.models import Action, ModelFingerprint, PlannerDecision
from closed_loop.orchestrator import State
from tests_stage2.completion_fixtures import build_case


class CompletionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

    def build(self, name):
        return build_case(name, Path(self.temp.name) / (name+'.json'))

    def run_case(self, name):
        parts = self.build(name)
        with patch('socket.socket', side_effect=AssertionError('No live transport in Stage 2')):
            job = parts[0].run()
        return job, parts

    def test_A_stale_action_rejected_and_reobserved(self):
        job, (orch, observer, planner, executor, checker) = self.run_case('stale-rejected')
        self.assertEqual(executor.requests, [])
        self.assertEqual(observer.calls, 2)
        self.assertEqual(planner.observedHashes, ['hash-A', 'hash-B'])
        stale = job.iterations[0]
        self.assertTrue(stale.decisionInvalidated)
        self.assertEqual(stale.staleVerdict, 'STALE')
        self.assertIsNone(stale.executorRequest)
        self.assertEqual(stale.planningModelHash, 'hash-A')
        self.assertEqual(stale.preExecutionFingerprint.modelHash, 'hash-B')
        self.assertEqual(checker.executorCountsAtCheck, [0])
        self.assertIn('stale-decision-invalidated', [e['kind'] for e in job.evidenceTrail])

    def test_B_stale_replan_succeeds(self):
        job, (_, observer, planner, executor, checker) = self.run_case('stale-replan')
        self.assertEqual(job.finalStatus, 'VERIFIED')
        self.assertEqual(planner.observedHashes, ['hash-A', 'hash-B'])
        self.assertEqual(observer.calls, 2)
        self.assertEqual(checker.executorCountsAtCheck, [0, 0])
        self.assertEqual(len(executor.requests), 1)
        self.assertEqual(executor.requests[0].parameters['plannedHash'], 'hash-B')
        self.assertEqual(job.iterations[1].staleVerdict, 'CURRENT')
        transitions = [(e['payload']['before'], e['payload']['after']) for e in job.evidenceTrail if e['kind'] == 'transition']
        self.assertIn((State.PLANNING, State.OBSERVING), transitions)

    def test_C_repeated_identical_failure_blocks_before_iteration_limit(self):
        job, (orch, _, _, executor, _) = self.run_case('no-progress')
        self.assertEqual(job.finalStatus, 'BLOCKED')
        self.assertEqual(job.terminalReason, 'BLOCKED_NO_PROGRESS')
        self.assertEqual(job.iteration, 2)
        self.assertLess(job.iteration, job.maxIterations)
        self.assertEqual(len(executor.requests), 2)
        self.assertEqual(job.noProgressLimit, 2)
        self.assertEqual([i.noProgressCount for i in job.iterations], [1, 2])
        self.assertEqual(job.iterations[0].progressSignature, job.iterations[1].progressSignature)
        persisted = json.loads(orch.output.read_text(encoding='utf-8'))
        for i in persisted['iterations']:
            for key in ('observedModelHash', 'planningModelHash', 'preExecutionFingerprint', 'staleVerdict',
                        'actionFingerprint', 'auditFingerprint', 'progressSignature', 'noProgressCount'):
                self.assertIsNotNone(i[key])

    def test_D_changed_model_resets_counter(self):
        job, _ = self.run_case('changed-model')
        self.assertEqual(job.finalStatus, 'VERIFIED')
        self.assertEqual([i.noProgressCount for i in job.iterations], [1, 1, 1])
        self.assertNotEqual(job.iterations[0].progressSignature, job.iterations[1].progressSignature)
        self.assertEqual(job.iterations[0].auditFingerprint, job.iterations[1].auditFingerprint)

    def test_E_changed_audit_resets_counter(self):
        job, _ = self.run_case('changed-audit')
        self.assertEqual(job.finalStatus, 'VERIFIED')
        self.assertEqual([i.noProgressCount for i in job.iterations], [1, 1, 1])
        self.assertNotEqual(job.iterations[0].auditFingerprint, job.iterations[1].auditFingerprint)

    def test_model_identity_change_invalidates_action(self):
        orch, _, _, executor, checker = self.build('stale-replan')
        checker.check = lambda reference: ModelFingerprint('other-model', reference.modelHash)
        job = orch.run()
        self.assertEqual(job.finalStatus, 'BLOCKED')
        self.assertEqual(executor.requests, [])

    def test_unbound_planner_decision_blocks_before_executor(self):
        orch, _, planner, executor, _ = self.build('stale-replan')
        planner.plan = lambda job, observed: PlannerDecision('PLANNED', Action('create_wall', {}))
        self.assertEqual(orch.run().finalStatus, 'BLOCKED')
        self.assertEqual(executor.requests, [])

    def test_model_check_transport_failure_blocks_before_executor(self):
        orch, _, _, executor, checker = self.build('stale-replan')
        def fail(reference):
            raise ConnectionError('fixture checker unavailable')
        checker.check = fail
        self.assertEqual(orch.run().finalStatus, 'BLOCKED')
        self.assertEqual(executor.requests, [])

    def test_no_progress_limit_is_validated(self):
        from closed_loop.orchestrator import Orchestrator
        orch, _, _, _, _ = self.build('no-progress')
        for limit in (0, 1, -1, True, 2.5, '2'):
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                Orchestrator(orch.contract, 'fixture', orch.observer, orch.planner, orch.executor,
                    orch.readback, Path(self.temp.name) / 'unused.json', no_progress_limit=limit)

    def test_changed_action_resets_counter(self):
        orch, _, planner, _, _ = self.build('changed-audit')
        orch.readback.observations[1] = orch.readback.observations[0]
        original = planner.plan
        def changed(job, observed):
            decision = original(job, observed)
            return replace(decision, action=Action('create_wall', {'length': job.iteration}))
        planner.plan = changed
        job = orch.run()
        self.assertEqual(job.finalStatus, 'VERIFIED')
        self.assertEqual([i.noProgressCount for i in job.iterations], [1, 1, 1])

    def test_parameter_order_is_normalized_for_progress_signature(self):
        orch, _, planner, _, _ = self.build('no-progress')
        original = planner.plan
        def reordered(job, observed):
            decision = original(job, observed)
            params = {'length': 1.0, 'fixture': True} if job.iteration == 1 else {'fixture': True, 'length': 1.0}
            return replace(decision, action=Action('create_wall', params))
        planner.plan = reordered
        self.assertEqual(orch.run().terminalReason, 'BLOCKED_NO_PROGRESS')
