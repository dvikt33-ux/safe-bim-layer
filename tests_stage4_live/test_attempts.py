from copy import deepcopy
from dataclasses import asdict
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from closed_loop.wall_attempts import (AttemptJournal, prepare_attempt, reconcile_attempt,
    RecoverableWallOrchestrator, durable_json, job_from_dict)
from closed_loop.live_wall import model_hash
from closed_loop.models import (AcceptanceContract, Criterion, Action, Fact, Observation,
                               ExecutionResult, PlannerDecision, ModelFingerprint, State)
from closed_loop.mocks import FixedPlanner, FixtureObserver, FixtureReadBack
from closed_loop.orchestrator import BeforeMutationTransportError, IllegalTransition


def wall(guid, begin, end):
    return {'guid': guid, 'type': 'Wall', 'homeStory': 0,
        'materialBindings': {'structureType': 0, 'buildingMaterial': {'guid': 'material'}},
        'placement': {'referenceGeometry': {'kind': 'WallReferenceLine', 'arcAngle': 0,
            'begin': {'x': begin, 'y': 0}, 'end': {'x': end, 'y': 0},
            'height': 3, 'thickness': .3, 'bottomOffsetFromHomeStory': 0, 'offset': 0}}, 'bodies': []}


def fixture():
    before = {'stories': [{'index': 0, 'elevation': 0}], 'elements': [wall('source', 0, 1)]}
    after = deepcopy(before)
    after['elements'].append(wall('created', 1, 2))
    attempt = prepare_attempt(before, Action('create_wall', {'sourceGuid': 'source', 'length': 1.0}), 'fixture.pln', 1, 'goal')
    return before, after, attempt


class AttemptTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.before, self.after, self.attempt = fixture()
        self.journal = AttemptJournal(self.root / 'attempts', self.attempt)
        self.journal.claim()
        self.network = patch('socket.socket', side_effect=AssertionError('Fixtures cannot use transport'))
        self.network.start()
        self.addCleanup(self.network.stop)

    def dispatch(self):
        self.journal.dispatch({'command': 'CreateWalls', 'parameters': self.attempt['signature']['nativeParameters']})

    def reconcile(self, model=None):
        return reconcile_attempt(self.attempt, self.before, model or self.after, 'fixture.pln', self.journal.value)

    def test_uuid_signature_and_journal_exist_before_native_dispatch(self):
        self.assertEqual(self.journal.value['nativeCalls'], 0)
        self.assertEqual(json.loads(self.journal.path.read_text())['mutationAttemptId'], self.attempt['mutationAttemptId'])
        for field in ('sourceGuid', 'sourceEndpoint', 'expectedBegin', 'expectedEnd', 'expectedLength',
                      'homeStory', 'height', 'thickness', 'structureType', 'materialIdentity', 'tolerance', 'preModelHash'):
            self.assertIn(field, self.attempt['signature'])

    def test_id_cannot_be_claimed_or_dispatched_twice(self):
        with self.assertRaises(FileExistsError): AttemptJournal(self.root/'attempts', self.attempt).claim()
        self.dispatch()
        with self.assertRaises(ValueError): self.dispatch()
        self.assertEqual(self.journal.value['nativeCalls'], 1)

    def test_lost_response_exact_signature_applied_without_native_guid_receipt(self):
        self.dispatch()
        result = self.reconcile()
        self.assertEqual(result['status'], 'RECONCILED_APPLIED')
        self.assertEqual(result['createdGuid'], 'created')
        self.assertFalse(result['retryAllowed'])

    def test_confirmed_non_dispatch_plus_fresh_unchanged_model_not_applied(self):
        self.journal.mark_not_dispatched('controlled helper stopped before native call')
        result = self.reconcile(self.before)
        self.assertEqual(result['status'], 'RECONCILED_NOT_APPLIED')
        self.assertTrue(result['retryAllowed'])

    def test_unchanged_model_after_actual_dispatch_is_ambiguous_not_absence_proof(self):
        self.dispatch()
        self.assertEqual(self.reconcile(self.before)['status'], 'RECONCILIATION_AMBIGUOUS')
        with self.assertRaises(ValueError): self.journal.mark_not_dispatched('cannot assert this')

    def test_two_candidates_block_even_if_native_receipt_names_one(self):
        self.dispatch()
        self.journal.confirm({'elements': [{'elementId': {'guid': 'created'}}]})
        self.after['elements'].append(wall('second', 1, 2))
        result = self.reconcile()
        self.assertEqual(result['terminalReason'], 'BLOCKED_RECONCILIATION_AMBIGUOUS')
        self.assertEqual(len(result['candidateGuids']), 2)
        self.assertFalse(result['retryAllowed'])

    def test_wrong_geometry_source_identity_receipt_and_signature_block(self):
        self.dispatch()
        self.journal.confirm({'elements': [{'elementId': {'guid': 'created'}}]})
        original = deepcopy((self.attempt, self.before, self.after, self.journal.value))
        for fault in ('signature', 'source', 'geometry', 'receipt'):
            self.attempt, self.before, self.after, self.journal.value = deepcopy(original)
            with self.subTest(fault=fault):
                if fault == 'signature': self.attempt['signature']['height'] = 99
                if fault == 'source': self.after['elements'][0]['placement']['referenceGeometry']['end']['x'] = 99
                if fault == 'geometry': self.after['elements'][1]['placement']['referenceGeometry']['end']['x'] = 99
                if fault == 'receipt': self.journal.value['nativeResponseHash'] = 'forged'
                self.assertEqual(self.reconcile()['status'], 'RECONCILIATION_AMBIGUOUS')
        self.assertEqual(reconcile_attempt(*original[:3], 'other.pln', original[3])['status'], 'RECONCILIATION_AMBIGUOUS')


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.before, self.after, _ = fixture()
        self.calls, self.observation_calls = [], []
        owner = self
        def observation(data, count):
            return Observation('fixture.pln', model_hash(data), {'segments': Fact(count, evidenceRefs=('readback',))},
                               {'readback': {'model': data, 'segments': count}})
        self.initial, self.first = observation(self.before, 0), observation(self.after, 1)
        final = deepcopy(self.after)
        final['elements'].append(wall('next', 2, 2.5))
        self.final = observation(final, 2)
        class Observer(FixtureObserver):
            def observe(self):
                owner.observation_calls.append(self.observation.modelHash)
                return super().observe()
        self.observer = Observer(self.initial)
        class Planner:
            offline = True
            def plan(self, job, observed):
                count = observed.facts['segments'].actual
                return PlannerDecision('PLANNED', Action('create_wall', {'sourceGuid': 'source' if count == 0 else 'created',
                    'length': 1.0 if count == 0 else .5}), plannedAgainstModelIdentity=observed.modelIdentity,
                    plannedAgainstModelHash=observed.modelHash)
        class Executor:
            offline = True
            fault = 'lost'
            def prepare(self, job, action, observed):
                data = observed.evidence['readback']['model']
                self.active = prepare_attempt(data, action, observed.modelIdentity, job.iteration, job.goalId)
                self.journal = AttemptJournal(owner.root/'attempts', self.active)
                return self.active
            def execute(self, action):
                self.journal.claim()
                owner.calls.append(self.active['mutationAttemptId'])
                # The existing durable EXECUTING job must already contain the ID.
                persisted = json.loads((owner.root/'job.json').read_text())
                if persisted['mutationAttempts'][-1]['mutationAttemptId'] != self.active['mutationAttemptId']:
                    raise AssertionError('ID not durable before execution')
                if self.fault == 'before':
                    self.journal.mark_not_dispatched('controlled pre-native fault')
                    raise BeforeMutationTransportError('transport unavailable before native call')
                if self.fault == 'not-applied':
                    self.journal.mark_not_dispatched('controlled uncertain-state injection with zero native calls')
                    raise TimeoutError('injected uncertain state, known non-dispatch receipt')
                self.journal.dispatch({'command': 'CreateWalls', 'parameters': self.active['signature']['nativeParameters']})
                if self.fault == 'crash': raise SystemExit(86)
                if self.fault == 'lost': raise TimeoutError('response lost after simulated create')
                return ExecutionResult('PASS', True, True, {'mutationAttemptId': self.active['mutationAttemptId']})
        self.planner, self.executor, self.reader = Planner(), Executor(), FixtureReadBack([self.first, self.final])
        self.contract = AcceptanceContract('goal', (Criterion('C', True, 'segments', 2, correctable=True),))
        self.orch = RecoverableWallOrchestrator(self.contract, 'Two proven Wall segments', self.observer,
            self.planner, self.executor, self.reader, self.root/'job.json', max_iterations=5)

    def restore(self):
        return RecoverableWallOrchestrator.restore(self.root/'job.json', observer=self.observer, planner=self.planner,
            executor=self.executor, readback=self.reader, model_check=self.observer)

    def recovery(self, applied=True):
        owner = self
        self.executor.fault = None
        self.observer.observation = self.first if applied else self.initial
        self.reader.observations = [self.final] if applied else [self.first, self.final]
        self.reader.calls = 0
        class Reconciler:
            def reconcile(self, attempt):
                current = owner.after if applied else owner.before
                journal = json.loads((owner.root/'attempts'/(attempt['mutationAttemptId']+'.json')).read_text())
                verdict = reconcile_attempt(attempt, owner.before, current, 'fixture.pln', journal)
                return verdict, owner.first if applied else owner.initial
        return self.restore().reconcile_and_continue(Reconciler())

    def test_unknown_cannot_run_or_transition_to_retry(self):
        self.assertEqual(self.orch.run().finalStatus, 'UNKNOWN_OUTCOME')
        with self.assertRaises(IllegalTransition): self.orch.run()
        with self.assertRaises(IllegalTransition): self.orch.transition(State.PLANNING)
        self.assertEqual(len(self.calls), 1)

    def test_applied_resume_audits_and_continues_second_segment_without_duplicate(self):
        self.orch.run()
        job = self.recovery()
        self.assertEqual(job.finalStatus, 'VERIFIED')
        self.assertEqual(job.iterations[0].reconciliationStatus, 'RECONCILED_APPLIED')
        self.assertEqual(len(self.calls), 2)
        self.assertEqual(len(set(self.calls)), 2)
        checkpoint=json.loads((self.root/job.recoveryCheckpoint['evidenceRef']).read_text())
        self.assertEqual(checkpoint['state'],'UNKNOWN_OUTCOME')
        self.assertIsNone(checkpoint['iterations'][0]['readback'])
        self.assertEqual(job.iterations[-1].executorRequest.parameters['sourceGuid'], 'created')
        self.assertEqual(self.observation_calls[-1], self.first.modelHash)

    def test_not_applied_requires_new_observation_plan_and_new_attempt_id(self):
        self.executor.fault = 'not-applied'
        self.orch.run()
        old_id = self.calls[0]
        job = self.recovery(applied=False)
        self.assertEqual(job.finalStatus, 'VERIFIED')
        self.assertEqual(job.iterations[0].reconciliationStatus, 'RECONCILED_NOT_APPLIED')
        self.assertEqual(len(self.calls), 3)
        self.assertEqual(self.calls.count(old_id), 1)
        self.assertEqual(self.observation_calls[-1], self.initial.modelHash)

    def test_crash_checkpoint_restores_without_repeating_first_mutation(self):
        self.executor.fault = 'crash'
        with self.assertRaises(SystemExit): self.orch.run()
        self.assertEqual(json.loads((self.root/'job.json').read_text())['state'], 'EXECUTING')
        job = self.recovery()
        self.assertTrue(job.recoveredFromCrash)
        self.assertEqual(job.finalStatus, 'VERIFIED')
        checkpoint=json.loads((self.root/job.recoveryCheckpoint['evidenceRef']).read_text())
        self.assertEqual(checkpoint['state'],'EXECUTING')
        self.assertIsNone(checkpoint['iterations'][0]['readback'])
        self.assertEqual(len(self.calls), 2)
        self.assertEqual(len(set(self.calls)), 2)

    def test_pre_native_transport_failure_is_blocked_not_unknown(self):
        self.executor.fault = 'before'
        job = self.orch.run()
        self.assertEqual(job.finalStatus, 'BLOCKED')
        self.assertIn('BLOCKED_BY_TRANSPORT', job.terminalReason)
        self.assertEqual(self.executor.journal.value['nativeCalls'], 0)

    def test_confirmed_response_with_missing_readback_never_verifies(self):
        from dataclasses import replace
        self.executor.fault = None
        original = self.executor.execute
        self.executor.execute = lambda action: replace(original(action), details={
            'mutationAttemptId': self.executor.active['mutationAttemptId'], 'nativeResponseConfirmed': True})
        def fail(action, result): raise ConnectionError('Fixture factual read-back failure')
        self.reader.read_back = fail
        job = self.orch.run()
        self.assertEqual(job.finalStatus, 'BLOCKED')
        self.assertIn('BLOCKED_BY_TRANSPORT', job.terminalReason)
        self.assertEqual(len(self.calls), 1)

    def test_ambiguous_recovery_blocks_without_execute(self):
        self.orch.run()
        self.after['elements'].append(wall('duplicate-candidate', 1, 2))
        job = self.recovery()
        self.assertEqual(job.finalStatus, 'BLOCKED')
        self.assertEqual(job.terminalReason, 'BLOCKED_RECONCILIATION_AMBIGUOUS')
        self.assertEqual(len(self.calls), 1)

    def test_additive_old_job_schema_loads_without_stage4_fields(self):
        row = self.orch.job.to_dict()
        for key in ('mutationAttempts','retryAllowed','retryReason','recoveredFromCrash','recoveryCheckpoint'):
            row.pop(key)
        restored = job_from_dict(json.loads(json.dumps(row)))
        self.assertEqual(restored.mutationAttempts, [])
        self.assertFalse(restored.retryAllowed)


if __name__ == '__main__': unittest.main()
