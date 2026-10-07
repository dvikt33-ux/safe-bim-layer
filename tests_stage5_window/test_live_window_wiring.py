from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from closed_loop.live_window import (
    WindowPlanner, WindowSession, acceptance, verify_window,
)
from closed_loop.models import LiveObservation, Fact, WindowAction
from tests_stage5_window.test_window_attempts import fixture


class FakeRecipe:
    def select_wall(self, data):
        return {
            'wallGuid':'host',
            'centerOffsetAlongHost':5.0,
            'sillHeightFromWallBase':0.9,
            'width':1.2,
            'height':1.5,
            'wallBodyBefore':{},
            'selectionRule':'fixture',
        }


class FakeSession:
    def __init__(self, path, before):
        self.output = Path(path)
        self.output.mkdir()
        self.goal_id = 'stage5-window-fixture'
        self.window_row = None
        self.window_recipe = FakeRecipe()
        self.active_plan = None
        self.before_path = self.output/'before.json'
        import json
        self.before_path.write_text(json.dumps(before), encoding='utf-8')


class LiveWindowWiringTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.before, self.after, self.action, _ = fixture()

    def test_window_planner_emits_bound_window_action(self):
        session = FakeSession(self.root/'session', self.before)
        planner = WindowPlanner(session)
        observed = LiveObservation(
            'fixture.pln', 'hash',
            {'x':Fact(True, evidenceRefs=('live.snapshot',))},
            {'live.snapshot':{'path':str(session.before_path), 'modelHash':'hash', 'elementCount':1}},
        )
        class Job:
            iteration = 1
            goalId = session.goal_id
        decision = planner.plan(Job(), observed)
        self.assertEqual(decision.status, 'PLANNED')
        self.assertIsInstance(decision.action, WindowAction)
        self.assertEqual(decision.action.parameters, {
            'sourceGuid':'host', 'centerOffset':5.0, 'sillHeight':0.9,
            'width':1.2, 'height':1.5,
        })
        self.assertEqual(decision.plannedAgainstModelHash, 'hash')

    def test_live_acceptance_is_window_only_and_all_required(self):
        contract = acceptance('stage5-window-test')
        self.assertEqual(len(contract.criteria), 15)
        self.assertTrue(all(c.required for c in contract.criteria))
        self.assertEqual({c.check for c in contract.criteria}, {
            'windowCreated','hostMatches','homeStoryMatches',
            'centerOffsetMatches','sillHeightMatches','widthMatches',
            'heightMatches','refSideMatches','reflectedMatches','windowHasBody',
            'hostReferenceStable','hostApertureChanged','hostOuterEnvelopeStable',
            'hostMaterialsUnchanged','elementCountDeltaOne',
        })

    def test_verify_window_requires_full_factual_geometry(self):
        result = {'createdGuid':'window'}
        witness = verify_window(self.before, self.after, result, self.action)
        self.assertTrue(witness['pass'])
        self.assertTrue(witness['hostApertureChanged'])
        broken = deepcopy(self.after)
        broken['elements'][-1]['placement']['referenceGeometry']['height'] = 2.0
        with self.assertRaises(ValueError):
            verify_window(self.before, broken, result, self.action)


if __name__ == '__main__':
    unittest.main()
