"""R15: joint feasibility must change when a real volume/visit binding is added."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools/moag_topology'))
import integrated_spatial_r15 as r15
import solver_r11 as r11


class SourceIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m=r15.build()
        cls.ps={p['id']:p for p in cls.m['points']}

    def test_no_new_graph_and_all_four_source_ledgers_retained(self):
        self.assertEqual(self.m['R09_fingerprint'],r11.digest(r11.inputs()[-1]))
        self.assertEqual(len(self.m['entities']),197)
        self.assertEqual(len(self.m['r14']['routes']),52)
        self.assertEqual(len(self.m['r14']['steps']),378)
        self.assertEqual(sum(x['total_pages'] for x in self.m['four_book_source_ledgers']),412)
        self.assertTrue(all(not p['physical_room_created'] and p['actual_metric_xyz'] is None for p in self.ps.values()))

    def test_dark_oval_descriptions_have_both_endpoints_inside_indexed_bases(self):
        self.assertEqual({p['source']['id'] for p in self.m['base_path_descriptions']},{'P-024','P-305'})
        for p in self.m['base_path_descriptions']:
            start,interval,end=(self.ps[k] for k in p['domain_element_ids'])
            self.assertEqual(start['host_volume'],p['from'])
            self.assertEqual(end['host_volume'],p['to'])
            self.assertNotIn('host_volume',interval)
            self.assertIsNone(p['path_polyline'])

    def test_two_separate_stairs_and_five_wild_intermediate_stages_retained(self):
        r=next(r for r in self.m['r14']['routes'] if r['id']=='RT-006')
        self.assertEqual(r['step_ids'],[f'RT006-{c}' for c in 'ABCDEFG'])
        ids={c['id'] for c in self.m['constraints']}
        self.assertTrue({'R14-Z-RT-007-0','R14-Z-RT-007-1'}<=ids)
        self.assertEqual(self.ps['RT007-A']['host_volume'],'MOAG-G-0008')
        self.assertEqual(self.ps['RT007-A']['containment_source_chain'],['MOAG-RG-E12'])

    def test_multilevel_alias_does_not_force_transit_into_lower_only(self):
        self.assertEqual(self.ps['RT008-B']['possible_blocks'],[1,2,3])
        self.assertEqual(self.ps['RT009-C']['possible_blocks'],[1,2,3])
        self.assertEqual(self.ps['RT008-A']['possible_blocks'],[1])
        self.assertEqual(self.ps['RT008-D']['possible_blocks'],[2])

    def test_candidate_cargo_and_numbered_bases_never_merge(self):
        self.assertNotIn('host_volume',self.ps['RT007-H'])
        self.assertEqual(self.m['historical_bases']['original_id'],'MOAG-G-0073')
        self.assertEqual(self.m['historical_bases']['individual_correspondence_to_named_bases'],'unknown')

    def test_partial_gallery_and_third_perimeter_remain_distinct(self):
        shapes={e['upper']:e['plan_shape_claim'] for e in self.m['r12_envelopes']}
        self.assertEqual(shapes['MOAG-G-0058'],'HALF_CIRCUMFERENCE_ARC_IN_ROUND_HALL')
        self.assertEqual(shapes['MOAG-G-0095'],'FULL_CIRCUMFERENCE_ARC_IN_ROUND_HALL')
        self.assertIn('upper_envelope_source',self.ps['RT013-C'])
        self.assertFalse(self.m['r13']['full_floors_inferred'])

    def test_discarding_height_or_image_constraint_is_rejected(self):
        for cid in ['R14-Z-RT-007-1','IMAGE::DARK-LEFT','VISIT-UPPER::RT013-C']:
            m=deepcopy(self.m);m['constraints']=[c for c in m['constraints'] if c['id']!=cid]
            with self.assertRaisesRegex(ValueError,'LOST|DROPPED|NOT_COMPILED'):
                r15.validate(m)

    def test_detached_base_description_or_promoted_geometry_rejected(self):
        m=deepcopy(self.m);p=m['base_path_descriptions'][0]['domain_element_ids'][-1]
        next(x for x in m['points'] if x['id']==p)['host_volume']='MOAG-G-0010'
        with self.assertRaisesRegex(ValueError,'BASE_PATH_DETACHED'):
            r15.validate(m)
        m=deepcopy(self.m);m['geometry_approved']=True
        with self.assertRaisesRegex(ValueError,'UNSUPPORTED_GEOMETRY'):
            r15.validate(m)


@unittest.skipUnless(importlib.util.find_spec('ortools'),'Install requirements-r11.txt')
class ActualJointSolver(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m=r15.build();cls.ps={p['id']:p for p in cls.m['points']}

    def test_binding_conflict_is_sat_before_coupling_unsat_after(self):
        px=self.ps['RT006-A']['variables'][0];bx=self.m['boxes']['MOAG-G-0008'][0]
        q=r15.probe('TEST-OUTSIDE-DARK',[r15.row([(px,1),(bx,-1)],10)])
        before=r15.cp_solve(self.m,[q],exclude_families=('binding',))
        after=r15.cp_solve(self.m,[q])
        self.assertEqual(before['status'],'SAT')
        self.assertEqual(after['status'],'INFEASIBLE')
        core={c['id'] for c in after['unsat_core']}
        self.assertTrue({'TEST-OUTSIDE-DARK','BIND::RT006-A'}<=core)
        self.assertTrue(any(s.get('url','').endswith('p=42') for c in after['unsat_core'] for s in c['sources']))

    def test_upper_gallery_visit_cannot_be_on_lounge_floor(self):
        result=r15.cp_solve(self.m);self.assertEqual(result['status'],'SAT')
        w=deepcopy(result['witness']);sz=self.ps['RT013-C']['variables'][2]
        floor=self.m['boxes']['MOAG-G-0036'][2]
        w['values'][sz]=w['values'][floor]+62
        with self.assertRaisesRegex(ValueError,'VISIT-UPPER::RT013-C'):
            r15.verify(self.m,w)

    def test_unknown_intermediate_has_separated_feasible_domains(self):
        x=self.ps['RT006-C']['variables'][0]
        for bound in [r15.row([(x,-1)],-20),r15.row([(x,1)],60)]:
            q=r15.probe('TEST-UNLOCATED',[bound]);r=r15.cp_solve(self.m,[q])
            self.assertEqual(r['status'],'SAT')
            self.assertTrue(r15.verify(self.m,r['witness'],[q]))


if __name__=='__main__':unittest.main()
