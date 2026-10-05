import json
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from closed_loop.auditor import audit
from closed_loop.models import (AcceptanceContract, Action, Criterion, ExecutionResult, Fact,
                                Observation, PlannerDecision, State, Verdict)
from closed_loop.mocks import FixtureObserver, FixtureReadBack, FixedPlanner, MockExecutor
from closed_loop.orchestrator import IllegalTransition, Orchestrator, TERMINAL, TRANSITIONS


def contract(correctable=False, optional=False):
    criteria = [Criterion('C01', True, 'length', 1.0, 1e-6, correctable)]
    if optional:
        criteria.append(Criterion('C02', False, 'optional', 5.0))
    return AcceptanceContract('fixture-goal', tuple(criteria))


def observation(actual=1.0, status='OBSERVED', refs=('fixture.measurement',), model='fixture-model', model_hash='after'):
    return Observation(model, model_hash, {'length': Fact(actual, status, refs)},
                       {'fixture.measurement': {'actual': actual, 'status': status}})


class Stage2Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.counter = 0

    def build(self, acceptance=None, after=None, planner=None, executor=None, readback=None, **kwargs):
        self.counter += 1
        output = Path(self.temp.name) / f'job-{self.counter}.json'
        planner = planner or FixedPlanner(PlannerDecision('PLANNED', Action('create_wall', {'length': 1.0})))
        executor = executor or MockExecutor()
        readback = readback or FixtureReadBack(after if after is not None else [observation()])
        orch = Orchestrator(acceptance or contract(), 'Fixture goal specification',
            FixtureObserver(observation(0.0, model_hash='before')), planner, executor, readback,
            output, clock=lambda: '2026-10-05T00:00:00+00:00', **kwargs)
        return orch, planner, executor, readback

    def run_job(self, **kwargs):
        orch, planner, executor, readback = self.build(**kwargs)
        # The complete Stage 2 user scenario is tested with network access forbidden.
        with patch('socket.socket', side_effect=AssertionError('Stage 2 must remain offline')):
            job = orch.run()
        return job, orch, planner, executor, readback

    def test_end_to_end_verified_and_durable_complete_trail(self):
        job, orch, _, executor, _ = self.run_job()
        self.assertEqual(job.state, State.VERIFIED)
        self.assertEqual(len(executor.requests), 1)
        saved = json.loads(orch.output.read_text(encoding='utf-8'))
        self.assertEqual(saved, json.loads(json.dumps(job.to_dict())))
        self.assertFalse(saved['liveMutationAttempted'])
        self.assertEqual(saved['executionMode'], 'OFFLINE')
        step = saved['iterations'][0]
        for key in ('stateBefore', 'observation', 'plannerDecision', 'executorRequest', 'executorResult', 'readback', 'auditResult'):
            self.assertIsNotNone(step[key], key)
        self.assertEqual([event['payload']['after'] for event in saved['evidenceTrail'] if event['kind'] == 'transition'],
            ['OBSERVING', 'PLANNING', 'EXECUTING', 'READING_BACK', 'AUDITING', 'VERIFIED'])
        self.assertEqual(saved['auditHistory'][0][0]['evidenceRefs'], ['fixture.measurement'])
        self.assertEqual(saved['observedModelHash'], 'after')

    def test_correctable_fail_replans_from_readback(self):
        job, _, planner, executor, _ = self.run_job(acceptance=contract(True),
            after=[observation(0.5, model_hash='changed-1'), observation(1.0, model_hash='changed-2')])
        self.assertEqual(job.finalStatus, 'VERIFIED')
        self.assertEqual(job.iteration, 2)
        self.assertEqual(planner.observedHashes, ['before', 'changed-1'])
        self.assertEqual(len(executor.requests), 2)
        self.assertEqual(job.auditHistory[0][0].verdict, Verdict.FAIL)
        self.assertEqual(job.auditHistory[1][0].verdict, Verdict.PASS)
        states = [e['payload']['after'] for e in job.evidenceTrail if e['kind'] == 'transition']
        self.assertEqual(states[5:7], ['REPLANNING', 'PLANNING'])

    def test_uncorrectable_fail_blocks(self):
        self.assertEqual(self.run_job(after=[observation(0.5)])[0].finalStatus, 'BLOCKED')

    def test_missing_check_waits_for_data(self):
        after = Observation('fixture-model', 'after', {}, {})
        job = self.run_job(after=[after])[0]
        self.assertEqual(job.finalStatus, 'WAITING_FOR_DATA')
        self.assertEqual(job.auditHistory[-1][0].verdict, Verdict.DATA_MISSING)

    def test_evidence_status_never_promoted_to_pass(self):
        for status, expected in [('NOT_VERIFIED', 'BLOCKED'), ('DATA_MISSING', 'WAITING_FOR_DATA'),
                                 ('CONFLICT', 'BLOCKED'), ('BLOCKED_BY_TRANSPORT', 'BLOCKED')]:
            with self.subTest(status=status):
                job = self.run_job(after=[observation(1.0, status)])[0]
                self.assertEqual(job.finalStatus, expected)
                self.assertEqual(job.auditHistory[-1][0].verdict.value, status)

    def test_missing_or_dangling_evidence_references_block(self):
        for refs in ((), ('not-retained',)):
            with self.subTest(refs=refs):
                job = self.run_job(after=[observation(refs=refs)])[0]
                self.assertEqual(job.finalStatus, 'BLOCKED')
                self.assertEqual(job.auditHistory[-1][0].verdict, Verdict.NOT_VERIFIED)

    def test_empty_retained_evidence_cannot_verify(self):
        for payload in (None, {}, [], ''):
            observed = Observation('fixture-model', 'after', {'length': Fact(1.0, evidenceRefs=('empty',))}, {'empty': payload})
            with self.subTest(payload=payload):
                job = self.run_job(after=[observed])[0]
                self.assertEqual(job.finalStatus, 'BLOCKED')

    def test_executor_pass_without_readback_cannot_verify(self):
        job, _, _, executor, readback = self.run_job(executor=MockExecutor(ExecutionResult('PASS', True, False)))
        self.assertEqual(job.finalStatus, 'BLOCKED')
        self.assertEqual(len(executor.requests), 1)
        self.assertEqual(readback.calls, 0)
        self.assertEqual(job.auditHistory, [])

    def test_readback_unavailable_after_attempt_is_unknown_and_never_retried(self):
        job, orch, _, executor, _ = self.run_job(after=[])
        self.assertEqual(job.finalStatus, 'UNKNOWN_OUTCOME')
        with self.assertRaises(IllegalTransition):
            orch.run()
        self.assertEqual(len(executor.requests), 1)

    def test_executor_timeout_is_unknown_and_never_retried(self):
        class TimeoutExecutor(MockExecutor):
            def execute(self, action):
                self.requests.append(action)
                raise TimeoutError('fixture timeout')
        job, orch, _, executor, _ = self.run_job(executor=TimeoutExecutor())
        self.assertEqual(job.finalStatus, 'UNKNOWN_OUTCOME')
        with self.assertRaises(IllegalTransition):
            orch.run()
        self.assertEqual(len(executor.requests), 1)
        self.assertIn('TimeoutError', job.terminalReason)

    def test_executor_results_route_fail_closed(self):
        for status, attempted, expected in [('UNKNOWN_OUTCOME', True, 'UNKNOWN_OUTCOME'),
                                            ('FAIL', True, 'UNKNOWN_OUTCOME'),
                                            ('BLOCKED', False, 'BLOCKED')]:
            with self.subTest(status=status):
                job = self.run_job(executor=MockExecutor(ExecutionResult(status, attempted, True)))[0]
                self.assertEqual(job.finalStatus, expected)

    def test_readback_identity_mismatch_blocks(self):
        job = self.run_job(after=[observation(model='different-model')])[0]
        self.assertEqual(job.finalStatus, 'BLOCKED')
        self.assertEqual(job.auditHistory, [])

    def test_iteration_limit_blocks_unresolved_correctable_fail(self):
        job, _, _, executor, _ = self.run_job(acceptance=contract(True),
            after=[observation(0.5), observation(0.5)], max_iterations=2)
        self.assertEqual(job.finalStatus, 'BLOCKED')
        self.assertEqual(job.iteration, 2)
        self.assertEqual(len(executor.requests), 2)

    def test_planner_waiting_or_blocked_does_not_call_executor(self):
        for status in ('WAITING_FOR_DATA', 'BLOCKED'):
            with self.subTest(status=status):
                job, _, _, executor, _ = self.run_job(planner=FixedPlanner(PlannerDecision(status, reason='fixture')))
                self.assertEqual(job.finalStatus, status)
                self.assertEqual(executor.requests, [])

    def test_malformed_planner_result_blocks_before_execution(self):
        class BadPlanner(FixedPlanner):
            def plan(self, job, observation):
                return {'status': 'PLANNED', 'action': {'type': 'create_wall'}}
        job, _, _, executor, _ = self.run_job(planner=BadPlanner(PlannerDecision('BLOCKED')))
        self.assertEqual(job.finalStatus, 'BLOCKED')
        self.assertEqual(executor.requests, [])

    def test_malformed_executor_result_is_unknown(self):
        class BadExecutor(MockExecutor):
            def execute(self, action):
                self.requests.append(action)
                return {'status': 'PASS'}
        job, _, _, executor, _ = self.run_job(executor=BadExecutor())
        self.assertEqual(job.finalStatus, 'UNKNOWN_OUTCOME')
        self.assertEqual(len(executor.requests), 1)

    def test_optional_nonpass_does_not_close_required_gate(self):
        job = self.run_job(acceptance=contract(optional=True))[0]
        self.assertEqual(job.finalStatus, 'VERIFIED')
        self.assertEqual(job.auditHistory[-1][1].verdict, Verdict.DATA_MISSING)

    def test_required_missing_data_takes_precedence_over_replan(self):
        acceptance = AcceptanceContract('goal', (Criterion('C01', True, 'length', 1.0, correctable=True),
                                                 Criterion('C02', True, 'missing', 5.0)))
        job = self.run_job(acceptance=acceptance, after=[observation(0.5)])[0]
        self.assertEqual(job.finalStatus, 'WAITING_FOR_DATA')

    def test_all_terminal_states_cannot_transition_or_run(self):
        orch = self.build()[0]
        for state in TERMINAL:
            orch.job.state = state
            with self.subTest(state=state):
                for target in State:
                    with self.assertRaises(IllegalTransition):
                        orch.transition(target)
                with self.assertRaises(IllegalTransition):
                    orch.run()

    def test_all_illegal_state_edges_are_rejected(self):
        orch = self.build()[0]
        for source in State:
            for target in State:
                if target not in TRANSITIONS.get(source, set()):
                    with self.subTest(source=source, target=target):
                        orch.job.state = source
                        with self.assertRaises(IllegalTransition):
                            orch.transition(target)
                        self.assertEqual(orch.job.state, source)

    def test_all_declared_legal_edges_are_exercised(self):
        # Concrete scenarios above test real flows; this checks every graph edge,
        # including an externally reported ambiguous outcome during audit.
        for source, targets in TRANSITIONS.items():
            for target in targets:
                with self.subTest(source=source, target=target):
                    orch = self.build()[0]
                    if target == State.VERIFIED:
                        orch.run()  # Install genuine fixture read-back and computed audit.
                    orch.job.state = source
                    orch.transition(target)
                    self.assertEqual(orch.job.state, target)

    def test_verified_without_readback_and_audit_is_rejected(self):
        orch = self.build()[0]
        orch.job.state = State.AUDITING
        with self.assertRaises(IllegalTransition):
            orch.transition(State.VERIFIED)

    def test_verified_with_nonpass_audit_is_rejected(self):
        orch = self.build(after=[observation(status='NOT_VERIFIED')])[0]
        orch.run()
        orch.job.state = State.AUDITING
        with self.assertRaises(IllegalTransition):
            orch.transition(State.VERIFIED)

    def test_verified_recomputes_audit_from_retained_readback(self):
        orch = self.build()[0]
        orch.run()
        orch.job.state = State.AUDITING
        orch.job.iterations[-1].readback = observation(0.5)
        with self.assertRaises(IllegalTransition):
            orch.transition(State.VERIFIED)

    def test_live_component_and_live_payload_are_rejected(self):
        live_executor = MockExecutor()
        live_executor.offline = False
        with self.assertRaises(ValueError):
            self.build(executor=live_executor)
        with self.assertRaises(ValueError):
            ExecutionResult('PASS', True, True, executionMode='LIVE')
        with self.assertRaises(ValueError):
            Observation('model', 'hash', {}, {}, provenance='LIVE')

    def test_existing_job_file_is_preserved_and_cannot_be_restarted(self):
        orch = self.build()[0]
        content = orch.output.read_bytes()
        with self.assertRaises(FileExistsError):
            Orchestrator(contract(), 'fixture', orch.observer, orch.planner, orch.executor, orch.readback, orch.output)
        self.assertEqual(orch.output.read_bytes(), content)

    def test_snapshots_are_detached_from_interface_mutation(self):
        class MutatingPlanner(FixedPlanner):
            def plan(self, job, observed):
                observed.evidence['fixture.measurement']['actual'] = 999
                job.specification = 'modified'
                return super().plan(job, observed)
        job = self.run_job(planner=MutatingPlanner(PlannerDecision('PLANNED', Action('create_wall', {}))))[0]
        self.assertEqual(job.specification, 'Fixture goal specification')
        self.assertEqual(job.iterations[0].observation.evidence['fixture.measurement']['actual'], 0.0)

    def test_invalid_contracts_and_parameters_are_rejected(self):
        invalid = [
            {'goalId': '', 'criteria': [{'id': 'C', 'required': True, 'check': 'x', 'expected': 1}]},
            {'goalId': 'goal', 'criteria': []},
            {'goalId': 'goal', 'criteria': [{'id': 'C', 'required': False, 'check': 'x', 'expected': 1}]},
            {'goalId': 'goal', 'criteria': [{'id': 'C', 'required': 'true', 'check': 'x', 'expected': 1}]},
            {'goalId': 'goal', 'criteria': [{'id': 'C', 'required': True, 'check': 'x', 'expected': math.nan}]},
            {'goalId': 'goal', 'criteria': [{'id': 'C', 'required': True, 'check': 'x', 'expected': 1, 'tolerance': -1}]},
        ]
        for payload in invalid:
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    AcceptanceContract.from_dict(payload)
        with self.assertRaises(ValueError):
            AcceptanceContract('goal', (Criterion('C', True, 'x', 1), Criterion('C', True, 'y', 2)))
        with self.assertRaises(ValueError):
            Action('create_window', {})
        with self.assertRaises(ValueError):
            Fact(math.inf)
        for limit in (0, -1, True, 1.5):
            with self.assertRaises(ValueError):
                self.build(max_iterations=limit)

    def test_auditor_numeric_tolerance_and_bool_distinction(self):
        self.assertEqual(audit(contract(), observation(1.0000005))[0].verdict, Verdict.PASS)
        self.assertEqual(audit(contract(), observation(1.000002))[0].verdict, Verdict.FAIL)
        self.assertEqual(audit(contract(), observation(True))[0].verdict, Verdict.FAIL)

    def test_fact_pass_cannot_be_supplied_as_observed_evidence(self):
        with self.assertRaises(ValueError):
            Fact(1.0, 'PASS', ('fixture',))

    def test_nested_boolean_is_not_numeric_evidence(self):
        acceptance = AcceptanceContract('goal', (Criterion('C01', True, 'length', {'value': 1}),))
        self.assertEqual(audit(acceptance, observation({'value': True}))[0].verdict, Verdict.FAIL)

    def test_observer_failure_blocks_without_actions(self):
        orch, _, executor, _ = self.build()
        def unavailable():
            raise ConnectionError('fixture observation unavailable')
        orch.observer.observe = unavailable
        self.assertEqual(orch.run().finalStatus, 'BLOCKED')
        self.assertEqual(executor.requests, [])

    def test_execution_request_is_saved_before_interface_call(self):
        orch, _, executor, _ = self.build()
        original = executor.execute
        def inspect(action):
            saved = json.loads(orch.output.read_text(encoding='utf-8'))
            self.assertEqual(saved['state'], 'EXECUTING')
            self.assertEqual(saved['iterations'][-1]['executorRequest']['type'], 'create_wall')
            return original(action)
        executor.execute = inspect
        self.assertEqual(orch.run().finalStatus, 'VERIFIED')


if __name__ == '__main__':
    unittest.main()
