"""R19: chronological evidence does not force a new room or conflated hangar."""
import importlib.util
from copy import deepcopy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools/moag_topology"))
import cargo_history_r19 as r19
import identity_alternatives_r18 as r18
import integrated_spatial_r15 as r15
import solver_r11 as r11

class R19SourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m,cls.audit,cls.old=r19.build()

    def test_history_pages_and_lower_upper_not_same_object(self):
        a=self.audit
        self.assertEqual([x["page_id"] for x in a["evidence"]],
                         ["B1-082","B1-083","B1-091"])
        self.assertEqual(a["old_cargo"],"M-L1-CG-001")
        self.assertEqual(a["new_upper_cargo"],"M-L3-CG-001")
        self.assertTrue(a["old_lower_and_new_third_have_no_asserted_direct_passage"])
        self.assertTrue(a["allow_old_lower_cargo_to_be_physically_present_after_primary_cessation"])
        self.assertTrue(a["source_citation_urls_not_verified_live_during_R19"])
        self.assertEqual(a["canonical_R09_fingerprint"],r11.digest(r11.inputs()[-1]))

    def test_previous_identity_alternatives_and_route_counts_unmodified(self):
        self.assertTrue(r18.validate(self.m,self.old))
        self.assertEqual(len(self.old["not_yet_decidable"]),6)
        self.assertEqual(self.audit["r15_bound_visits_unchanged"],25)
        self.assertEqual(self.audit["r15_unbound_visits_unchanged"],353)
        self.assertEqual(len(self.m["r14"]["steps"]),378)
        self.assertEqual(len(self.m["r13"]["volumes"]),12)
        self.assertFalse(self.audit["archicad_write"])

    def test_ordinal_timeline_not_real_calendar_year_or_z(self):
        ev=self.audit["events"]
        self.assertEqual(set(ev),set(r19.PHASES))
        for eid in ev.values():
            self.assertEqual(self.m["variables"][eid]["domain"],[0,6])
        self.assertTrue(self.audit["historical_rank_is_not_physical_z_or_calendar_year"])
        self.assertEqual(self.audit["new_rooms_created"],0)
        self.assertEqual(self.audit["new_metric_coordinates"],0)

    def test_evidence_is_enforced_and_fail_closed(self):
        self.assertTrue(r19.validate(self.m,self.audit,self.old))
        a=deepcopy(self.audit);a["no_old_cargo_equivalence_to_sleepers_approved"]=False
        with self.assertRaisesRegex(ValueError,"R19_FALSE_GEOMETRY_OR_HISTORIC_CLAIM"):
            r19.validate(self.m,a,self.old)
        a=deepcopy(self.audit);a["historical_rank_is_not_physical_z_or_calendar_year"]=False
        with self.assertRaisesRegex(ValueError,"R19_FALSE_GEOMETRY_OR_HISTORIC_CLAIM"):
            r19.validate(self.m,a,self.old)
        m=deepcopy(self.m)
        c=next(x for x in m["constraints"] if
               x["id"]==self.audit["new_upper_before_old_halt_constraint"])
        c["rows"][0]["rhs"]=0
        with self.assertRaisesRegex(ValueError,"R19_SOURCE_TEMPORAL_ORDER_LOST"):
            r19.validate(m,self.audit,self.old)


@unittest.skipUnless(importlib.util.find_spec("ortools"),"Official OR-Tools required")
class R19ActualSolverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m,cls.audit,cls.old=r19.build()

    def test_full_joint_model_satisfiable_with_historic_evidence(self):
        cp=r15.cp_solve(self.m)
        self.assertEqual(cp["status"],"SAT")
        w=cp["witness"]["values"]
        ev=self.audit["events"]
        self.assertLess(w[ev[r19.FIRST_EVENT]],w[ev[r19.SECOND_EVENT]])
        self.assertLess(w[ev[r19.SECOND_EVENT]],w[ev[r19.THIRD_EVENT]])
        self.assertNotEqual(w[self.audit["old_identity_token"]],
                            w[self.audit["third_identity_token"]])

    def test_three_source_conflicts_unsat_but_ablations_sat(self):
        for title,extra,needed,family in r19.negative_tests(self.m,self.audit):
            self.assertEqual(r15.cp_solve(self.m,[extra],
                             exclude_families=(family,))["status"],"SAT",title)
            bad=r15.cp_solve(self.m,[extra])
            self.assertEqual(bad["status"],"INFEASIBLE",title)
            core={e["id"] for e in bad["unsat_core"]}
            self.assertTrue({extra["id"],needed}<=core,title)

    def test_unverified_old_hangar_identity_both_outcomes_remain_sat(self):
        for a,b in [
           ("M-L1-CG-001","M-L1-AH-OLD-001"),
           ("MOAG-G-0053","M-L1-CG-001"),
           ("MOAG-G-0057","M-L1-AH-OLD-001")]:
            for kind in ("same","different"):
                q=r18.query(self.old,a,b,kind)
                self.assertEqual(r15.cp_solve(self.m,[q])["status"],"SAT",a+" "+kind)

if __name__=="__main__":unittest.main()
