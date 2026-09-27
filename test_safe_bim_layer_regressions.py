import unittest

from safe_bim_layer import SafeBIMLayer, SafeBIMError, ModalStateError


class FakeTapir:
    def __init__(self, active=0, timeout_on=None, create_before_timeout=False):
        self.active = active
        self.timeout_on = timeout_on
        self.create_before_timeout = create_before_timeout
        self.calls = []
        self.schema = {'commands': {}}
        self.created = []

    def validate_payload(self, command, payload):
        self.calls.append(('validate', command, payload))

    def active_story(self):
        self.calls.append(('GetStories',))
        return self.active

    def change_floor_plan_navigator_item(self, guid):
        return self.call('ChangeWindow', {'navigatorItemId': {'guid': guid}})

    def call(self, command, payload):
        self.calls.append((command, payload))
        if command == 'GetNavigatorItemTree':
            return {'result': {'addOnCommandResponse': {'navigatorItemTree': [
                {'type': 'StoryItem', 'prefix': '1', 'navigatorItemId': {'guid': 'story-1'}}]}}}
        if command == 'ChangeWindow':
            self.active = 1
            return {'result': {'addOnCommandResponse': {'success': True}}}
        if command == self.timeout_on:
            if self.create_before_timeout:
                self.created.append(payload)
            raise TimeoutError('simulated modal-blocked timeout')
        if command == 'CreateWalls':
            self.created.append(payload)
            return {'result': {'addOnCommandResponse': {'elements': [
                {'elementId': {'guid': 'plinth-1'}}]}}}
        if command == 'GetElementsByType':
            return {'result': {'addOnCommandResponse': {'elements': []}}}
        if command == 'GetDetailsOfElements':
            return {'result': {'addOnCommandResponse': {'detailsOfElements': [{
                'type': 'Wall', 'floorIndex': 0,
                'details': {'zCoordinate': -0.6, 'height': 0.6,
                            'structureType': 'Basic'}}]}}}
        if command == 'GetStories':
            return {'result': {'addOnCommandResponse': {'stories': [
                {'index': 0, 'level': 0.0}]}}}
        return {'result': {'addOnCommandResponse': {}}}


class SafeBIMRegressionTests(unittest.TestCase):
    def test_switches_from_floor_zero_and_reads_back_before_write(self):
        fake = FakeTapir(active=0)
        layer = SafeBIMLayer(fake)
        state = layer.ensure_active_story(1)
        self.assertEqual(state['after'], 1)
        self.assertLess(next(i for i, c in enumerate(fake.calls) if c[0] == 'ChangeWindow'),
                        len(fake.calls))
        self.assertEqual(fake.active, 1)

    def test_switch_failure_is_fail_closed(self):
        fake = FakeTapir(active=0)
        fake.call = lambda command, payload: {'result': {'addOnCommandResponse': {
            'navigatorItemTree': []}}} if command == 'GetNavigatorItemTree' else {}
        with self.assertRaises(SafeBIMError):
            SafeBIMLayer(fake).ensure_active_story(1)

    def test_timeout_is_unknown_and_never_retryable(self):
        fake = FakeTapir(active=1, timeout_on='CreateWalls', create_before_timeout=True)
        layer = SafeBIMLayer(fake)
        result = layer.create_wall_loop(
            [{'x': 0, 'y': 0}, {'x': 1, 'y': 0}, {'x': 1, 'y': 1}, {'x': 0, 'y': 1}],
            1, 3, 0.2)
        self.assertEqual(result['status'], 'UNKNOWN_OUTCOME')
        self.assertFalse(result['retryAllowed'])
        self.assertTrue(result['reconciliationRequired'])
        self.assertEqual(len([c for c in fake.calls if c[0] == 'CreateWalls']), 1)

    def test_plinth_segment_verifies_vertical_fingerprint(self):
        fake = FakeTapir()
        result = SafeBIMLayer(fake).create_plinth_segment(
            {'x': 100, 'y': 100}, {'x': 101, 'y': 100},
            grade_z=-0.6, project_zero_z=0.0, floor_index=0)
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual(result['actual_bottom'], -0.6)
        self.assertEqual(result['actual_top'], 0.0)

    def test_modal_error_is_non_retryable(self):
        class ModalTapir(FakeTapir):
            def call(self, command, payload):
                if command == 'CreateWalls':
                    raise ModalStateError('Invalid program status: modal dialog')
                return super().call(command, payload)
        with self.assertRaises(ModalStateError):
            SafeBIMLayer(ModalTapir()).create_wall_loop(
                [{'x': 0, 'y': 0}, {'x': 1, 'y': 0},
                 {'x': 1, 'y': 1}, {'x': 0, 'y': 1}], 0, 0.6, 0.25)


if __name__ == '__main__':
    unittest.main()
