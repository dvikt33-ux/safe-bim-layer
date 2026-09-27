import unittest

from safe_bim_layer import SafeBIMLayer, SafeBIMError


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
            return {'result': {'addOnCommandResponse': {'elements': []}}}
        if command == 'GetElementsByType':
            return {'result': {'addOnCommandResponse': {'elements': []}}}
        if command == 'GetDetailsOfElements':
            return {'result': {'addOnCommandResponse': {'detailsOfElements': []}}}
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


if __name__ == '__main__':
    unittest.main()
