"""Confirmed live wall/plinth Z split. Offline only; no Archicad and no extra write."""
import copy
import tempfile
import unittest
from pathlib import Path

from safe_bim_layer import SafeBIMLayer
from safe_bim_operations import SafeBIMOperations
from safe_bim_runtime import JobStatus, ResumableExecutor, SQLiteCheckpointStore, StepSpec
from safe_bim_verification import VerificationError, assess_wall_vertical, verify_details, wall_z_contract
from tests_safety.fake_bim import PROJECT, FakeBIM

LIVE_GUID = '371A5BAE-5E48-4F87-A789-04FB07F07124'
SPECIMEN = dict(start={'x': 20.0, 'y': 20.0}, end={'x': 21.2, 'y': 20.0},
                grade_z=3.9, project_zero_z=4.5, floor_index=1, thickness=0.25)


def contract():
    return wall_z_contract(1, 4.5, 3.9, 0.6)


def detail(z, height=0.6, floor=1, structure='Basic', **extra):
    row = {'zCoordinate': z, 'height': height, 'structureType': structure}
    row.update(extra)
    return row


class WallReadbackZTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp.name)
        self.counter = 0

    def tearDown(self):
        self.temp.cleanup()

    def make(self, operation, params, count=1, job='job'):
        self.counter += 1
        fake = FakeBIM()
        ops = SafeBIMOperations(fake)
        store = SQLiteCheckpointStore(self.folder / f'{self.counter}.sqlite3')
        store.create_job(job, 'wall z', PROJECT, [
            StepSpec(str(i), operation, copy.deepcopy(params), params.get('floor_index')) for i in range(count)])
        ex = ResumableExecutor(store, ops.execute, ops.reconcile, ops.current_project)
        return fake, ops, store, ex

    def test_contract_splits_write_offset_from_absolute_readback(self):
        fp = contract()
        self.assertAlmostEqual(fp['write_relative_z'], -0.6)
        self.assertAlmostEqual(fp['relative_offset'], -0.6)
        self.assertAlmostEqual(fp['expected_readback_z'], 3.9)
        self.assertAlmostEqual(fp['expected_absolute_bottom_z'], 3.9)
        self.assertAlmostEqual(fp['expected_absolute_top_z'], 4.5)
        self.assertEqual(fp['story_index'], 1)
        self.assertAlmostEqual(fp['story_elevation'], 4.5)
        self.assertNotAlmostEqual(fp['write_relative_z'], fp['expected_readback_z'])

    def test_case_a_live_semantics_verify_and_payload_stays_relative(self):
        fake, _, store, ex = self.make('create_plinth_segment', SPECIMEN, job='specimen')
        self.assertEqual(ex.run('specimen'), JobStatus.DONE)
        sent = fake.dispatches[0][1]['wallsData'][0]
        self.assertAlmostEqual(sent['zCoordinate'], -0.6)
        self.assertNotAlmostEqual(sent['zCoordinate'], 3.9)
        stored = next(iter(fake.elements.values()))['details']
        self.assertAlmostEqual(stored['zCoordinate'], 3.9)
        self.assertAlmostEqual(stored['bottomOffset'], -0.6)
        result = store.job('specimen')['steps'][0]['result']
        self.assertTrue(result['readbackVerified'])
        self.assertAlmostEqual(result['actual_bottom'], 3.9)
        self.assertAlmostEqual(result['actual_top'], 4.5)
        fp = result['expectedZFingerprint']
        self.assertAlmostEqual(fp['write_relative_z'], -0.6)
        self.assertAlmostEqual(fp['expected_readback_z'], 3.9)
        note = assess_wall_vertical(fp, 1, detail(3.9))
        self.assertEqual(note['geometry'], 'MATCH')
        self.assertFalse(note['ownershipProven'])

    def test_case_b_relative_readback_is_not_absolute_bottom(self):
        fp = contract()
        note = assess_wall_vertical(fp, 1, detail(-0.6))
        self.assertEqual(note['geometry'], 'MISMATCH')
        self.assertIn('zCoordinate', note['reasons'])
        self.assertIsNone(note['absolute_bottom'])
        # The retired formula would have hidden this as 4.500 + -0.600 = 3.900.
        self.assertAlmostEqual(4.5 + (-0.6), 3.9)
        fake, _, store, ex = self.make('create_plinth_segment', SPECIMEN)
        def relative_echo(rows):
            for row in rows:
                row['details']['zCoordinate'] = -0.6
            return rows
        fake.on_details = relative_echo
        self.assertNotEqual(ex.run('job'), JobStatus.DONE)
        self.assertEqual(len(fake.dispatches), 1)
        self.assertFalse(store.job('job')['steps'][0]['result'].get('readbackVerified', False))
        self.assertEqual(ex.resume('job'), JobStatus.WAITING_USER)
        self.assertEqual(len(fake.dispatches), 1)

    def test_case_c_story_zero_hides_the_old_bug(self):
        params = dict(start={'x': 0, 'y': 0}, end={'x': 1, 'y': 0}, grade_z=-0.6,
                      project_zero_z=0.0, floor_index=0, thickness=0.25)
        fp = wall_z_contract(0, 0.0, -0.6, 0.6)
        self.assertAlmostEqual(fp['write_relative_z'], fp['expected_readback_z'])
        fake, _, store, ex = self.make('create_plinth_segment', params, job='zero')
        self.assertEqual(ex.run('zero'), JobStatus.DONE)
        self.assertAlmostEqual(fake.dispatches[0][1]['wallsData'][0]['zCoordinate'], -0.6)
        self.assertAlmostEqual(next(iter(fake.elements.values()))['details']['zCoordinate'], -0.6)
        self.assertAlmostEqual(store.job('zero')['steps'][0]['result']['actual_bottom'], -0.6)
        self.assertAlmostEqual(store.job('zero')['steps'][0]['result']['actual_top'], 0.0)

    def test_cases_d_through_i_reject_bad_vertical_facts(self):
        fp = contract()
        samples = {
            'D-floor': (2, detail(3.9), 'floorIndex'),
            'E-height': (1, detail(3.9, height=0.5), 'height'),
            'F-structure': (1, detail(3.9, structure='Composite'), 'structureType'),
            'G-absolute-z': (1, detail(3.3), 'zCoordinate'),
            'H-missing-z': (1, {'height': 0.6, 'structureType': 'Basic'}, 'zCoordinate'),
            'I-nan': (1, detail(float('nan')), 'VerificationError'),
            'I-inf': (1, detail(float('inf')), 'VerificationError'),
        }
        for name, (floor, row, reason) in samples.items():
            with self.subTest(name=name):
                note = assess_wall_vertical(fp, floor, row)
                self.assertEqual(note['geometry'], 'MISMATCH')
                self.assertTrue(any(reason in item for item in note['reasons']))
        fake, _, _, ex = self.make('create_plinth_segment', SPECIMEN)
        def corrupt(rows):
            rows[0]['details']['zCoordinate'] = float('nan')
            return rows
        fake.on_details = corrupt
        self.assertNotEqual(ex.run('job'), JobStatus.DONE)
        self.assertEqual(len(fake.dispatches), 1)

    def test_nonzero_wall_loop_write_stays_zero_and_readback_is_elevation(self):
        params = dict(contour=[{'x': 0, 'y': 0}, {'x': 2, 'y': 0}, {'x': 2, 'y': 2}, {'x': 0, 'y': 2}],
                      floor_index=1, height=3.0, thickness=0.25)
        fake, _, store, ex = self.make('create_wall_loop', params, job='loop')
        self.assertEqual(ex.run('loop'), JobStatus.DONE)
        self.assertGreaterEqual(len(fake.dispatches), 1)
        self.assertTrue(all(len(item[1]['wallsData']) == 1 for item in fake.dispatches))
        sent = [item[1]['wallsData'][0]['zCoordinate'] for item in fake.dispatches]
        self.assertTrue(all(abs(z) < 1e-9 for z in sent))
        stored = [row['details']['zCoordinate'] for row in fake.elements.values()]
        self.assertEqual(len(stored), len(fake.dispatches))
        self.assertTrue(all(abs(z - 4.5) < 1e-9 for z in stored))
        for step in store.job('loop')['steps']:
            self.assertAlmostEqual(step['result']['actual_bottom'], 4.5)
            self.assertAlmostEqual(step['result']['actual_top'], 7.5)

    def test_specimen_geometry_match_is_not_applied_without_receipt(self):
        fp = contract()
        row = detail(3.9, bottomOffset=-0.6, begCoordinate={'x': 20, 'y': 20}, endCoordinate={'x': 21.2, 'y': 20})
        self.assertEqual(assess_wall_vertical(fp, 1, row)['geometry'], 'MATCH')
        fake = FakeBIM()
        fake.elements[LIVE_GUID] = {'type': 'Wall', 'floorIndex': 1, 'id': 'human', 'details': row}
        ops = SafeBIMOperations(fake)
        evidence = ops.reconcile('create_plinth_segment', SPECIMEN, previous=None)
        self.assertNotEqual(evidence['classification'], 'APPLIED')
        self.assertNotEqual(evidence.get('geometry'), 'MATCH')
        self.assertFalse(evidence.get('readbackVerified', False))
        self.assertEqual(fake.dispatches, [])
        prepared = SafeBIMLayer(fake).prepare('create_plinth_segment', SPECIMEN)
        self.assertAlmostEqual(prepared['payload']['wallsData'][0]['zCoordinate'], -0.6)
        self.assertAlmostEqual(prepared['expected'][0]['zCoordinate'], 3.9)
        with self.assertRaises(VerificationError):
            verify_details(prepared, [LIVE_GUID], [{
                'verifiedGuid': LIVE_GUID, 'type': 'Wall', 'floorIndex': 1,
                'details': detail(-0.6, bottomOffset=-0.6,
                                  begCoordinate={'x': 20, 'y': 20}, endCoordinate={'x': 21.2, 'y': 20},
                                  relativeTopStory=0, begThickness=0.25, endThickness=0.25,
                                  offset=0, referenceLineLocation='Center')}])

    def test_unverified_receipt_can_match_geometry_and_still_not_retry(self):
        fake, ops, store, ex = self.make('create_plinth_segment', SPECIMEN, job='unknown')
        def fail_once(rows):
            for row in rows:
                row['details']['zCoordinate'] = -0.6
            return rows
        fake.on_details = fail_once
        self.assertEqual(ex.run('unknown'), JobStatus.UNKNOWN_OUTCOME)
        self.assertEqual(len(fake.dispatches), 1)
        created = next(iter(fake.elements))
        fake.elements[LIVE_GUID] = fake.elements.pop(created)
        receipt = store.job('unknown')['steps'][0]['result']
        self.assertIn(created, receipt.get('guids', []))
        self.assertFalse(receipt.get('readbackVerified', False))
        store.job  # keep the store open; rewrite the provisional GUID in place
        step = store.job('unknown')['steps'][0]
        replaced = copy.deepcopy(step['result'])
        replaced['guids'] = [LIVE_GUID]
        store.set_step('unknown', 0, JobStatus.UNKNOWN_OUTCOME, result=replaced, lease=store.job('unknown')['generation'])
        fake.on_details = lambda rows: rows
        self.assertEqual(ex.resume('unknown'), JobStatus.WAITING_USER)
        self.assertEqual(len(fake.dispatches), 1)
        evidence = store.job('unknown')['steps'][0]['result']['reconciliation']
        self.assertEqual(evidence['geometry'], 'MATCH')
        self.assertNotEqual(evidence['classification'], 'APPLIED')
        self.assertFalse(evidence['readbackVerified'])
        self.assertFalse(evidence['retryAllowed'])
        self.assertEqual(ex.resume('unknown'), JobStatus.WAITING_USER)
        self.assertEqual(len(fake.dispatches), 1)

    def test_old_relative_expected_spec_does_not_become_done(self):
        prepared = SafeBIMLayer(FakeBIM()).prepare('create_plinth_segment', SPECIMEN)
        old = copy.deepcopy(prepared)
        old['expected'][0]['zCoordinate'] = old['expectedZFingerprint']['write_relative_z']
        old['expectedZFingerprint'].pop('expected_readback_z')
        row = {'verifiedGuid': 'wall-old', 'type': 'Wall', 'floorIndex': 1, 'details': {
            **old['expected'][0], 'zCoordinate': 3.9}}
        with self.assertRaises(VerificationError):
            verify_details(old, ['wall-old'], [row])
        note = assess_wall_vertical(old['expectedZFingerprint'], 1, row['details'])
        self.assertEqual(note['geometry'], 'MATCH')
        self.assertFalse(note['ownershipProven'])

    def test_slab_contract_is_not_rewritten_as_wall_readback(self):
        prepared = SafeBIMLayer(FakeBIM()).prepare('create_basic_slab', {
            'contour': [{'x': 0, 'y': 0}, {'x': 2, 'y': 0}, {'x': 2, 'y': 2}, {'x': 0, 'y': 2}],
            'level': 0.2, 'floor_index': 1, 'thickness': 0.25, 'reference_plane': 'TOP'})
        self.assertNotIn('write_relative_z', prepared['expectedZFingerprint'])
        self.assertNotIn('expected_readback_z', prepared['expectedZFingerprint'])
        self.assertAlmostEqual(prepared['expected'][0]['zCoordinate'], 4.7)


if __name__ == '__main__':
    unittest.main()
