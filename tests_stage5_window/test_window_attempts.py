from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from closed_loop.models import Action
from closed_loop.orchestrator import fingerprint
from closed_loop.wall_attempts import AttemptJournal
from closed_loop.window_attempts import (
    prepare_window_attempt, reconcile_window_attempt, window_signature,
)


def host_wall(guid='host'):
    return {
        'guid': guid,
        'type': 'Wall',
        'homeStory': 0,
        'placement': {'referenceGeometry': {
            'kind': 'WallReferenceLine',
            'arcAngle': 0,
            'referenceLineLocation': 1,
            'begin': {'x': 0.0, 'y': 0.0},
            'end': {'x': 10.0, 'y': 0.0},
            'height': 3.0,
            'thickness': 0.3,
            'bottomOffsetFromHomeStory': 0.0,
            'offset': 0.0,
        }},
        'materialBindings': {'structureType': 0, 'buildingMaterial': {'guid': 'mat'}},
        'bodies': [{
            'closed': True,
            'vertices': [[0,0,0],[10,0,0],[10,.3,0],[0,.3,0],
                         [0,0,3],[10,0,3],[10,.3,3],[0,.3,3]],
            'faces': [{'nativeFaceIndex': 0, 'materialId': 1}],
        }],
    }


def window(guid='window', host='host', center=5.0):
    return {
        'guid': guid,
        'type': 'Window',
        'homeStory': 0,
        'relationships': {'hostGuid': host},
        'placement': {'referenceGeometry': {
            'centerOffsetAlongHost': center,
            'sillHeight': 0.9,
            'width': 1.2,
            'height': 1.5,
            'refSide': False,
            'reflected': False,
        }},
        'bodies': [{'closed': True, 'vertices': [[4.4,0,0.9],[5.6,0,2.4]], 'faces': [{'materialId': 1}]}],
    }


def fixture():
    before = {'stories': [{'index': 0, 'elevation': 0.0}], 'elements': [host_wall()]}
    after = deepcopy(before)
    # Aperture/topology evidence: same Wall placement, changed body topology.
    after['elements'][0]['bodies'][0]['vertices'].extend([[4.4,0,0.9],[5.6,0,2.4]])
    after['elements'][0]['bodies'][0]['faces'].append({'nativeFaceIndex': 1, 'materialId': 1, 'holes': [[8,9]]})
    after['elements'].append(window())
    action = Action('create_window', {
        'sourceGuid': 'host',
        'centerOffset': 5.0,
        'sillHeight': 0.9,
        'width': 1.2,
        'height': 1.5,
    })
    attempt = prepare_window_attempt(before, action, 'fixture.pln', 1, 'stage5-window')
    return before, after, action, attempt


class WindowAttemptTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.before, self.after, self.action, self.attempt = fixture()
        self.journal = AttemptJournal(self.root/'attempts', self.attempt)
        self.journal.claim()

    def dispatch(self):
        self.journal.dispatch({
            'command': 'CreateWindows',
            'parameters': self.attempt['signature']['nativeParameters'],
        })

    def reconcile(self, model=None):
        return reconcile_window_attempt(
            self.attempt, self.before, model or self.after, 'fixture.pln', self.journal.value)

    def test_typed_action_allowlist_is_additive(self):
        self.assertEqual(Action('create_wall', {'sourceGuid':'x','length':1.0}).type, 'create_wall')
        self.assertEqual(self.action.type, 'create_window')
        with self.assertRaises(ValueError):
            Action('create_door', {})

    def test_signature_binds_host_geometry_and_native_request_before_dispatch(self):
        signature = window_signature(self.before, self.action, 'fixture.pln')
        self.assertEqual(signature['sourceGuid'], 'host')
        self.assertEqual(signature['centerOffset'], 5.0)
        self.assertEqual(signature['sillHeight'], 0.9)
        self.assertEqual(signature['width'], 1.2)
        self.assertEqual(signature['height'], 1.5)
        native = signature['nativeParameters']['windowsData'][0]
        self.assertEqual(native['ownerWallId']['guid'], 'host')
        self.assertFalse(native['reflected'])
        self.assertEqual(self.journal.value['nativeCalls'], 0)

    def test_invalid_opening_outside_host_is_rejected_before_attempt(self):
        bad = Action('create_window', {
            'sourceGuid':'host','centerOffset':0.2,'sillHeight':0.9,'width':1.2,'height':1.5})
        with self.assertRaisesRegex(ValueError, 'inside host Wall ends'):
            prepare_window_attempt(self.before, bad, 'fixture.pln', 1, 'goal')

    def test_confirmed_non_dispatch_reconciles_not_applied(self):
        self.journal.mark_not_dispatched('pre-native transport failure')
        result = self.reconcile(self.before)
        self.assertEqual(result['status'], 'RECONCILED_NOT_APPLIED')
        self.assertTrue(result['retryAllowed'])
        self.assertEqual(result['candidateGuids'], [])

    def test_lost_response_reconciles_exact_hosted_window_without_duplicate(self):
        self.dispatch()
        result = self.reconcile()
        self.assertEqual(result['status'], 'RECONCILED_APPLIED')
        self.assertEqual(result['createdGuid'], 'window')
        self.assertFalse(result['retryAllowed'])
        self.assertEqual(result['candidateGuids'], ['window'])

    def test_confirmed_receipt_must_match_factual_candidate(self):
        self.dispatch()
        self.journal.confirm({'elements':[{'elementId':{'guid':'other'}}]})
        result = self.reconcile()
        self.assertEqual(result['status'], 'RECONCILIATION_AMBIGUOUS')
        self.assertIn('receipt conflicts', result['reason'])

    def test_wrong_window_dimensions_do_not_reconcile(self):
        self.dispatch()
        self.after['elements'][-1]['placement']['referenceGeometry']['width'] = 2.0
        result = self.reconcile()
        self.assertEqual(result['status'], 'RECONCILIATION_AMBIGUOUS')
        self.assertEqual(result['candidateGuids'], [])

    def test_two_matching_new_windows_are_ambiguous(self):
        self.dispatch()
        self.after['elements'].append(window('window-2'))
        result = self.reconcile()
        self.assertEqual(result['status'], 'RECONCILIATION_AMBIGUOUS')
        self.assertEqual(len(result['candidateGuids']), 2)

    def test_host_reference_geometry_change_blocks_reconciliation(self):
        self.dispatch()
        self.after['elements'][0]['placement']['referenceGeometry']['end']['x'] = 11.0
        result = self.reconcile()
        self.assertEqual(result['status'], 'RECONCILIATION_AMBIGUOUS')
        self.assertIn('aperture/topology', result['reason'])

    def test_dispatch_without_host_aperture_change_is_ambiguous(self):
        self.dispatch()
        current = deepcopy(self.before)
        current['elements'].append(window())
        result = self.reconcile(current)
        self.assertEqual(result['status'], 'RECONCILIATION_AMBIGUOUS')
        self.assertIn('aperture/topology', result['reason'])


if __name__ == '__main__':
    unittest.main()
