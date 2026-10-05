"""Exercise the actual Stage 4 adapter boundary with an in-memory native helper."""
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from closed_loop.live_wall_hardening import ControlledWallExecutor
from closed_loop.live_wall import model_hash
from closed_loop.models import Action, LiveObservation
from closed_loop.wall_attempts import durable_json
from closed_loop.orchestrator import BeforeMutationTransportError
from tests_stage4_live.test_attempts import fixture


class AdapterFaultTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.before, self.after, self.attempt = fixture()
        self.calls = []
        owner = self
        class Session:
            output = owner.root
            goal_id = 'fixture-live-path'
            identity = {'projectPath': 'fixture.pln'}
            active_plan = {'sourceGuid': 'source', 'length': 1.0, 'modelHash': model_hash(owner.before), 'jobIteration': 1}
            def check_identity(self): pass
        self.session = Session()
        self.baseline = SimpleNamespace()
        self.baseline.guid_from = lambda result: result['elements'][0]['elementId']['guid']
        def dump(stem):
            value = owner.before if stem == 'before' else owner.after
            durable_json(owner.session.step/'executor'/(stem+'.json'), value)
            return deepcopy(value)
        def api(command, parameters, stem):
            self.calls.append(command)
            return {'elements': [{'elementId': {'guid': 'created'}}]}
        def run(request):
            self.baseline.dump('before')
            result = self.baseline.api('CreateWalls', self.attempt['signature']['nativeParameters'], 'create_wall')
            self.baseline.dump('after-create')
            return {'status': 'PASS', 'createdGuid': 'created'}
        self.baseline.dump, self.baseline.api, self.baseline.run = dump, api, run
        self.action = Action(**self.attempt['action'])

    def execute(self, fault):
        executor = ControlledWallExecutor(self.session, fault=fault)
        executor.active_attempt = self.attempt
        with patch('socket.socket', side_effect=AssertionError('No live transport in fixture')), \
                patch('closed_loop.live_wall_hardening.load', return_value=self.baseline):
            return executor.execute(self.action)

    def test_success_result_and_request_retain_attempt_id(self):
        result = self.execute(None)
        self.assertEqual(result.status, 'PASS')
        self.assertEqual(result.details['mutationAttemptId'], self.attempt['mutationAttemptId'])
        self.assertTrue(result.details['nativeResponseConfirmed'])
        self.assertEqual(self.calls, ['CreateWalls'])

    def test_lost_response_is_injected_after_exactly_one_native_create(self):
        with self.assertRaises(TimeoutError): self.execute('lost-response')
        self.assertEqual(self.calls, ['CreateWalls'])
        import json
        journal = json.loads((self.root/'mutation-attempts'/(self.attempt['mutationAttemptId']+'.json')).read_text())
        self.assertEqual(journal['phase'], 'CONFIRMED')
        self.assertEqual(journal['nativeCalls'], 1)

    def test_known_pre_dispatch_transport_failure_makes_zero_native_calls(self):
        with self.assertRaises(BeforeMutationTransportError): self.execute('before-transport')
        self.assertEqual(self.calls, [])

    def test_uncertain_non_application_has_durable_zero_dispatch_evidence(self):
        with self.assertRaises(TimeoutError): self.execute('not-applied')
        self.assertEqual(self.calls, [])
        import json
        journal = json.loads((self.root/'mutation-attempts'/(self.attempt['mutationAttemptId']+'.json')).read_text())
        self.assertEqual(journal['phase'], 'NOT_DISPATCHED')
        self.assertFalse(journal['dispatchStarted'])

    def test_confirmed_native_response_with_failed_dump_is_not_factual_acceptance(self):
        result = self.execute('readback-unavailable')
        self.assertEqual(result.status, 'PASS')
        self.assertTrue(result.readbackRequired)
        self.assertTrue(result.details['nativeResponseConfirmed'])
        self.assertEqual(self.calls, ['CreateWalls'])

    def test_crash_occurs_after_native_create_before_audit(self):
        with patch('closed_loop.live_wall_hardening.os._exit', side_effect=SystemExit(86)):
            with self.assertRaises(SystemExit): self.execute('crash')
        self.assertEqual(self.calls, ['CreateWalls'])
        self.assertFalse((self.root/'iteration-1/executor-result.json').exists())


if __name__ == '__main__': unittest.main()
