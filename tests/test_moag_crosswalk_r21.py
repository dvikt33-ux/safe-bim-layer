"""МОАГ R21: every reused legacy label reviewed; real source identity only."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools/moag_topology"))
import contextual_crosswalk_r21 as r21
import integrated_spatial_r15 as r15
import identity_alternatives_r18 as r18
import solver_r11 as r11


class BookSourceCrosswalkR21(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m,cls.audit,cls.h,cls.ident=r21.build()

    def test_all_30_uses_of_five_overloaded_legacy_labels_audited(self):
        a=self.audit
        self.assertEqual(a["reviewed_aliases"],{
            "L1-ANGAR-HALL":4,"L1-CIRCULAR-CONTROL":3,
            "L1-CIRCULAR-STAIRS":4,"L1-OLD-FREIGHT-HANGAR":8,
            "L1-SEALED":11})
        self.assertEqual(len(a["all_30_legacy_uses"]),30)
        self.assertEqual(len({x["stage_id"] for x in a["all_30_legacy_uses"]}),30)
        self.assertTrue(all(x["unchanged_original_route_anchor"] and
                            not x["new_physical_room_created"] and
                            not x["metric_geometry_authorized"]
                            for x in a["all_30_legacy_uses"]))

    def test_sleepers_not_assigned_to_main_circulation(self):
        x=next(x for x in self.audit["all_30_legacy_uses"] if x["stage_id"]=="RT015-G")
        self.assertEqual(x["original_R14_stable_anchor"],"MOAG-G-0017")
        self.assertEqual(x["evidence_backed_episode_referent"],"MOAG-G-0057")
        self.assertIn("LEGACY_ANCHOR_CONFLICT",x["review_class"])
        self.assertEqual(x["source_observations"],["P-216"])

    def test_old_hangar_and_old_control_room_are_not_circular_hall_or_main_corridor(self):
        a={x["stage_id"]:x for x in self.audit["all_30_legacy_uses"]}
        self.assertEqual(a["RT024-F"]["original_R14_stable_anchor"],"MOAG-G-0017")
        self.assertEqual(a["RT024-F"]["evidence_backed_episode_referent"],
                         "M-L1-AH-OLD-001")
        for sid in ("RT024-H","RT024-I"):
            self.assertEqual(a[sid]["original_R14_stable_anchor"],"MOAG-G-0060")
            self.assertEqual(a[sid]["evidence_backed_episode_referent"],
                             "M-L1-AH-OLD-CTRL-001")
        self.assertEqual(a["RT015-L"]["evidence_backed_episode_referent"],
                         "MOAG-G-0060")
        self.assertEqual(a["RT030-D"]["evidence_backed_episode_referent"],
                         "MOAG-G-0017")
        self.assertEqual(a["RT030-D"]["source_observations"],["P-362"])

    def test_old_cargo_corrridor_and_sealed_gates_not_new_rooms_or_one_door(self):
        a=self.audit["all_30_legacy_uses"]
        for row in a:
            if row["original_legacy_alias"]=="L1-OLD-FREIGHT-HANGAR":
                self.assertEqual(row["review_class"],
                    "CARGO_AREA_OR_CORRIDOR_NOT_AN_INDIVIDUAL_ROOM")
            if row["original_legacy_alias"]=="L1-SEALED":
                self.assertEqual(row["review_class"],
                    "SEALED_SECTOR_OR_EPISODE_GATE_NOT_ONE_SHARED_DOOR")

    def test_5_book_sourced_same_episode_relations_and_3_unresolved_pairs(self):
        a=self.audit
        proven={(x["episode"],x["referent"]):x["book_observation"]
                 for x in a["evidence_backed_episode_corrections"]}
        self.assertEqual(proven,{
          ("RT024-F","M-L1-AH-OLD-001"):"P-313",
          ("RT024-H","M-L1-AH-OLD-CTRL-001"):"P-313",
          ("RT024-I","RT024-H"):"P-316",
          ("RT015-L","MOAG-G-0060"):"P-221",
          ("RT031-G","RT031-F"):"P-376"})
        self.assertEqual(len(a["unresolved_cross_episode_pairs"]),3)
        self.assertTrue(all(not p["same_physical_entity_proven"] and
                            not p["different_physical_entities_proven"]
                            for p in a["unresolved_cross_episode_pairs"]))

    def test_no_master_or_route_rewrite_or_archicad_write(self):
        a=self.audit
        self.assertEqual(a["R09_fingerprint"],r11.digest(r11.inputs()[-1]))
        self.assertEqual(a["original_R09_edge_count"],845)
        self.assertEqual(len(self.m["r14"]["steps"]),378)
        self.assertEqual(len(self.m["r13"]["volumes"]),12)
        self.assertEqual(len(self.m["unbound_route_steps"]),353)
        self.assertEqual(a["R15_bound_visits_unchanged"],25)
        self.assertEqual(a["new_source_rooms"],0)
        self.assertEqual(a["new_physical_portals"],0)
        self.assertEqual(a["new_metric_XYZ_constraints"],0)
        self.assertFalse(a["archicad_write"])

    def test_forged_legacy_geometry_or_identity_fails_closed(self):
        a=deepcopy(self.audit)
        a["all_30_legacy_uses"][0]["metric_geometry_authorized"]=True
        with self.assertRaisesRegex(ValueError,"R21_UNSOURCED_LEGACY_ALIAS_PROMOTED"):
            r21.validate(self.m,a,self.h,self.ident)
        a=deepcopy(self.audit)
        a["unresolved_cross_episode_pairs"][0]["same_physical_entity_proven"]=True
        with self.assertRaisesRegex(ValueError,"R21_UNSOURCED_CROSS_SCENE_MERGE"):
            r21.validate(self.m,a,self.h,self.ident)
        m=deepcopy(self.m)
        bad=next(c for c in m["constraints"] if c["id"]==
                "R21-SAME::RT024-F::M-L1-AH-OLD-001")
        bad["rows"][0]["rhs"]=1
        with self.assertRaisesRegex(ValueError,"R21_BOOK_CONTEXT_IDENTITY_NOT_COMPILED"):
            r21.validate(m,self.audit,self.h,self.ident)


@unittest.skipUnless(importlib.util.find_spec("ortools"),"Official OR-Tools required")
class CPActualBookCrosswalkR21(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m,cls.audit,cls.h,cls.ident=r21.build()

    def test_full_r20_with_contextual_crosswalk_SAT(self):
        result=r15.cp_solve(self.m)
        self.assertEqual(result["status"],"SAT")
        self.assertTrue(r15.verify(self.m,result["witness"]))
        v=result["witness"]["values"];t=self.audit["reference_tokens"]
        for left,right,_ in r21.SOURCED_SAME:
            self.assertEqual(v[t[left]],v[t[right]])

    def test_wrong_old_hangar_and_control_identity_inversions_are_UNSAT(self):
        for left,right,src in r21.SOURCED_SAME:
            q=r21.disagree(self.audit,left,right,"TEST-R21-FALSE-SPLIT-"+left)
            self.assertEqual(r15.cp_solve(self.m,[q],
                  exclude_families=("r21_source_identity",))["status"],"SAT")
            bad=r15.cp_solve(self.m,[q])
            self.assertEqual(bad["status"],"INFEASIBLE")
            ids={x["id"] for x in bad["unsat_core"]}
            self.assertIn(q["id"],ids)
            self.assertIn("R21-SAME::"+left+"::"+right,ids)
            self.assertTrue(any(s.get("id")==src for c in bad["unsat_core"]
                                for s in c.get("sources",[])))

    def test_unproven_episode_identity_sameness_and_difference_both_SAT(self):
        for row in self.audit["unresolved_cross_episode_pairs"]:
            for kind in ("same","different"):
                q=r21.compare(self.audit,row["a"],row["b"],kind,
                              "TEST-R21-UNPROVEN-"+kind)
                self.assertEqual(r15.cp_solve(self.m,[q])["status"],"SAT")

if __name__=="__main__":
    unittest.main()
