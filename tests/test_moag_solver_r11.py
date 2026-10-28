"""Semantic safety and actual CP-SAT conflict regression, without BIM writes."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools/moag_topology'))
import solver_r11 as r11


class AdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = r11.build(1)

    def test_original_graph_and_unknown_historical_numbers_preserved(self):
        before = r11.digest(r11.inputs()[-1])
        self.assertEqual(before, self.model['R09_fingerprint'])
        self.assertEqual(self.model['R09_quantities']['total_vertices'], 593)
        self.assertEqual(self.model['R09_quantities']['total_typed_edges'], 845)
        self.assertIn('MOAG-G-0073', {e['id'] for e in self.model['entities']})
        self.assertEqual(self.model['hypothesis_edges_used_as_hard_constraints'], 0)

    def test_uncertain_bedrooms_and_steps_never_become_strict(self):
        ids = {c['id'] for c in self.model['constraints']}
        self.assertNotIn('MOAG-Z-Z04', ids)
        self.assertNotIn('MOAG-Z-Z05', ids)
        self.assertIn('MOAG-Z-Z01', ids)
        well = next(e for e in self.model['entities'] if e['id'] == 'MOAG-G-0050')
        self.assertEqual(well['global_level_domain'], [1,2,3])

    def test_all_three_global_blocks_have_independent_local_scopes(self):
        self.assertEqual(self.model['global_blocks'], [1,2,3])
        upper = r11.build(2)
        self.assertTrue(any(c['id'] == 'POS06-001' for c in upper['constraints']))
        self.assertTrue(all(e['global_level_domain'] == [2] for e in upper['entities']))

    def test_r05_metric_bounds_remain_hypotheses(self):
        self.assertFalse(self.model['metric_area_constraints_enabled'])
        e = next(e for e in self.model['entities'] if e['id'] == 'M-L1-FH-001')
        self.assertEqual(e['metric_intervals_status'], 'hypothesis')
        self.assertIsNone(e['metric_z_m'])


@unittest.skipUnless(importlib.util.find_spec('ortools'), 'Install requirements-r11.txt for real solver tests')
class RealSolverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = r11.build(1)

    def test_unsat_core_replays_and_explains_book_source(self):
        c = next(c for c in self.model['constraints'] if c['id'] == 'MOAG-Z-Z01')
        inverse = {**deepcopy(c), 'id': 'TEST-INVERSE', 'a': c['b'], 'b': c['a']}
        result = r11.cp_solve(self.model, self.model['constraints'] + [inverse])
        self.assertEqual(result['status'], 'INFEASIBLE')
        core = result['unsat_core']
        self.assertIn('TEST-INVERSE', {x['id'] for x in core})
        self.assertTrue(any('page=4' in s.get('url', '') for x in core for s in x['sources']))
        self.assertEqual(r11.cp_solve(self.model, core)['status'], 'INFEASIBLE')

    def test_alternatives_verified_and_corruption_rejected(self):
        result = r11.cp_solve(self.model)
        self.assertEqual(len(result['witnesses']), 3)
        self.assertEqual(len({tuple(w['z']) for w in result['witnesses']}), 3)
        w = deepcopy(result['witnesses'][0]); w['z'] = [0] * len(w['z'])
        with self.assertRaisesRegex(ValueError, 'RELATION_VIOLATION'):
            r11.verify(self.model, w)

    def test_no_universal_base_above_hangar_inference(self):
        for a, b in [('M-L1-FH-001','MOAG-G-0008'), ('MOAG-G-0008','M-L1-FH-001')]:
            probe = {'id':'TEST-COUNTERMODEL', 'a':a, 'b':b, 'kind':1, 'sources':[]}
            self.assertEqual(r11.cp_solve(self.model, self.model['constraints'] + [probe], count=1)['status'], 'SAT')


if __name__ == '__main__':
    unittest.main()
