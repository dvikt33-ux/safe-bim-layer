"""R20: preserve physical room identities and recorded intermediate circulation."""
from pathlib import Path
from copy import deepcopy
import importlib.util
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools/moag_topology"))
import sealed_paths_r20 as r20
import integrated_spatial_r15 as r15
import solver_r11 as r11

class R20BookSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m,cls.audit,cls.h,cls.ident=r20.build()

    def test_true_book_stage_trace_has_corroborated_endpoints(self):
        o=self.audit["recorded_route_overlay"]
        self.assertEqual(o["source_edge"],"MOAG-RG-E144")
        self.assertEqual(o["endpoint_stage_ids"],["RT031-D","RT031-F"])
        self.assertEqual(o["intermediate_stage_id"],"RT031-E")
        self.assertEqual(o["stage_original_graph_anchors"],
                         ["MOAG-G-0021","MOAG-G-0053","MOAG-G-0017"])
        self.assertFalse(o["geometry_or_direct_door_established"])
        self.assertFalse(o["same_physical_gate_as_RT015_or_RT024_established"])

    def test_sleeping_hall_legacy_mismatch_is_exposed_not_silent_merge(self):
        x=self.audit["legacy_anchor_discrepancy"]
        self.assertEqual(x["route_stage_id"],"RT015-G")
        self.assertEqual(x["old_inherited_R14_anchor"],"MOAG-G-0017")
        self.assertEqual(x["source_supported_episode_referent"],"MOAG-G-0057")
        self.assertFalse(x["graph_repair_approved"])
        self.assertFalse(x["r15_geometry_binding_changed"])
        self.assertEqual(len(self.m["unbound_route_steps"]),353)

    def test_separate_sleepers_hangar_from_next_round_hall_and_three_fork_branches(self):
        self.assertEqual(self.audit["source_sleeping_hall_token"],
                         self.ident["tokens"]["MOAG-G-0057"])
        self.assertEqual(len(self.audit["source_qualified_constraints"]),7)
        c={x["id"]:x for x in self.m["constraints"]}
        self.assertTrue(c["R20-SLEEPERS-VS-ROUND-ARE-DIFFERENT"]["any_of"])
        self.assertIn("P-217",{x["id"] for x in c["R20-SLEEPERS-VS-ROUND-ARE-DIFFERENT"]["sources"]})
        self.assertIn("P-213",{x["id"] for x in c["R20-SEALED-FORK-HAS-AT-LEAST-THREE-RECORDED-OPTIONS"]["sources"]})
        self.assertEqual(self.audit["fork_count_var"]+1,self.audit["episode_gate_open_var"])

    def test_no_geometry_or_permanent_gate_state_claims(self):
        self.assertEqual(len(self.m["r13"]["volumes"]),12)
        self.assertEqual(len(self.m["r14"]["steps"]),378)
        self.assertEqual(self.audit["R15_bound_visits"],25)
        self.assertEqual(self.audit["R15_unbound_visits"],353)
        self.assertEqual(self.audit["R09_fingerprint"],r11.digest(r11.inputs()[-1]))
        self.assertTrue(self.audit["no_new_direct_doors"])
        self.assertTrue(self.audit["no_new_physical_rooms"])
        self.assertTrue(self.audit["no_XYZ_or_area_inferred"])
        self.assertTrue(r20.validate(self.m,self.audit,self.h,self.ident))

    def test_semantic_falsification_rejected(self):
        a=deepcopy(self.audit)
        a["legacy_anchor_discrepancy"]["graph_repair_approved"]=True
        with self.assertRaisesRegex(ValueError,"R20_UNSOURCED_GEO_DOOR_OR_CROSSWALK_PROMOTION"):
            r20.validate(self.m,a,self.h,self.ident)
        a=deepcopy(self.audit)
        a["recorded_route_overlay"]["geometry_or_direct_door_established"]=True
        with self.assertRaisesRegex(ValueError,"R20_UNSOURCED_GEO_DOOR_OR_CROSSWALK_PROMOTION"):
            r20.validate(self.m,a,self.h,self.ident)
        m=deepcopy(self.m)
        c=next(x for x in m["constraints"] if x["id"]=="R20-E144-NOT-A-DIRECT-DOOR-REPRESENTATION")
        c["rows"][0]["rhs"]=1
        with self.assertRaisesRegex(ValueError,"R20_BOOK_RELATION_NOT_COMPILED"):
            r20.validate(m,self.audit,self.h,self.ident)

@unittest.skipUnless(importlib.util.find_spec("ortools"),"Official R11 OR-Tools required")
class R20RealSolverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m,cls.audit,cls.h,cls.ident=r20.build()

    def test_complete_joint_model_still_sat_and_source_claims_hold(self):
        z=r15.cp_solve(self.m)
        self.assertEqual(z["status"],"SAT")
        self.assertTrue(r15.verify(self.m,z["witness"]))
        v=z["witness"]["values"]
        t=self.audit["referent_variables"]
        self.assertEqual(v[t["RT015-G"]],v[self.audit["source_sleeping_hall_token"]])
        self.assertEqual(v[t["RT015-I"]],v[t[r20.ROUND]])
        self.assertNotEqual(v[t[r20.ROUND]],v[self.audit["source_sleeping_hall_token"]])
        self.assertGreaterEqual(v[self.audit["fork_count_var"]],3)
        self.assertEqual(v[self.audit["episode_gate_open_var"]],1)
        self.assertEqual(v[self.audit["intermediate_stage_present_var"]],1)
        self.assertEqual(v[self.audit["recorded_path_direct_door_representation_var"]],0)

    def test_five_source_falsification_tests_unsat_but_ablated_sat(self):
        for name,probe,source,family in r20.negative(self.m,self.audit):
            before=r15.cp_solve(self.m,[probe],exclude_families=(family,))
            after=r15.cp_solve(self.m,[probe])
            self.assertEqual(before["status"],"SAT",name)
            self.assertEqual(after["status"],"INFEASIBLE",name)
            c={x["id"] for x in after["unsat_core"]}
            self.assertTrue({probe["id"],source}<=c,name)

if __name__=="__main__":unittest.main()
