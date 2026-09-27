import unittest

from safe_bim_layer import SafeBIMLayer, SafeBIMError, ModalStateError


from tests_safety.fake_bim import FakeBIM


class FakeTapir(FakeBIM):
    """Updated fixture returns the complete strict read-back, not just three fields."""
    def __init__(self, active=0, timeout_on=None, create_before_timeout=False):
        super().__init__()
        self.active = active
        self.created = []
        def created(command, guids):
            self.created.append(self.dispatches[-1][1])
            if command == timeout_on:
                raise TimeoutError('simulated lost mutation response')
        self.on_created = created


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
        result = layer.create_plinth_segment(
            {'x': 0, 'y': 0}, {'x': 1, 'y': 0}, grade_z=0.0, project_zero_z=3.0, floor_index=1)
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
        result = SafeBIMLayer(ModalTapir()).create_plinth_segment(
            {'x': 0, 'y': 0}, {'x': 1, 'y': 0}, grade_z=-0.6, project_zero_z=0.0, floor_index=0)
        self.assertEqual(result['status'], 'UNKNOWN_OUTCOME')
        self.assertFalse(result['retryAllowed'])


if __name__ == '__main__':
    unittest.main()
