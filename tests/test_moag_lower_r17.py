"""R17 guards: source-specific sector boundaries do not invent metric layouts."""
import importlib.util
import sys
from copy import deepcopy
from pathlib import Path
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools/moag_topology"))
import lower_evidence_r17 as r17
import integrated_spatial_r15 as r15
import solver_r11 as r11


class SourceBoundaryR17(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model,cls.info=r17.build()

    def test_five_real_lower_index_focus_not_fake_3d_rooms(self):
        f={x["id"]:x for x in self.info["focus"]}
        self.assertEqual({k:x["unbound_visits"] for k,x in f.items()},{
            "MOAG-G-0021":11,"MOAG-G-0053":8,"MOAG-G-0014":6,
            "MOAG-G-0017":4,"MOAG-G-0059":4})
        self.assertTrue(all(not x["physical_volume_created"] for x in f.values()))
        self.assertEqual(len(self.model["r13"]["volumes"]),12)
        self.assertEqual(len(self.model["r14"]["steps"]),378)
        self.assertEqual(self.info["R15_bound_visits_count"],25)
        self.assertEqual(self.info["R15_unbound_visits_count"],353)
        self.assertEqual(self.info["R09_fingerprint"],r11.digest(r11.inputs()[-1]))

    def test_book_separates_living_base_sector_from_hangar_sector_not_xy(self):
        s=self.info["functional_sectors"]
        self.assertEqual(s["source_page"],"B2-014")
        self.assertFalse(s["metric_separation_proven"])
        self.assertFalse(s["new_disjoint_3d_boxes_created"])
        self.assertFalse(s["rank_or_direction_from_picture_inferred"])
        self.assertFalse(s["sector_count_of_whole_station_inferred"])
        cid=s["relation_id"]
        c=next(x for x in self.model["constraints"] if x["id"]==cid)
        self.assertTrue(c["any_of"])
        self.assertEqual(c["family"],"r17_sector")
        self.assertIn("53370&p=14",c["sources"][0]["url"])

    def test_real_named_indices_and_hangar_route_visits_inherit_sector(self):
        v=self.info["source_index_membership_variables"]
        self.assertEqual(set(v),{"MOAG-G-0008","MOAG-G-0009",
                 "MOAG-G-0017","MOAG-G-0018","RT030-D","RT030-E"})
        c={x["id"]:x for x in self.model["constraints"]}
        self.assertTrue(all(c["R17-MEMBER::"+eid]["family"]=="r17_membership"
                            for eid in v))

    def test_e69_e70_direct_doors_and_e20_access_not_identified_as_one_type(self):
        p={x["id"]:x for x in self.info["source_portal_relations"]}
        self.assertEqual(set(p),{"MOAG-RG-E69","MOAG-RG-E70","MOAG-RG-E20"})
        self.assertEqual((p["MOAG-RG-E69"]["from"],p["MOAG-RG-E69"]["to"]),
                         ("MOAG-G-0058","MOAG-G-0060"))
        self.assertEqual((p["MOAG-RG-E70"]["from"],p["MOAG-RG-E70"]["to"]),
                         ("MOAG-G-0060","MOAG-G-0061"))
        self.assertEqual((p["MOAG-RG-E20"]["from"],p["MOAG-RG-E20"]["to"]),
                         ("MOAG-G-0017","MOAG-G-0018"))
        self.assertIn("ACCESS_TO",p["MOAG-RG-E20"]["type"])
        self.assertTrue(all(not x["XY_or_slab_claimed"] and
                            not x["new_physical_door_id_created"] for x in p.values()))

    def test_stairs_not_merged_across_operator_and_bridge_scenes(self):
        a=self.info["stairs_ambiguity"]
        self.assertEqual(a["source_index"],"MOAG-G-0059")
        self.assertEqual(len(a["route_occurrences"]),4)
        self.assertFalse(a["mandatory_XYZ_equivalence"])
        self.assertFalse(a["mandatory_different_stairs"])
        self.assertTrue(a["do_not_promote_cross_scene_identity"])

    def test_reject_evidence_promotion_and_door_destruction(self):
        a=deepcopy(self.info)
        a["functional_sectors"]["new_disjoint_3d_boxes_created"]=True
        with self.assertRaisesRegex(ValueError,"R17_PREMATURE_GEOMETRIC_ASSERTION"):
            r17.validate(self.model,a)
        a=deepcopy(self.info)
        a["source_portal_relations"][0]["metric_door_width_proven"]=True
        with self.assertRaisesRegex(ValueError,"R17_SOURCE_ACCESS_PROMOTED"):
            r17.validate(self.model,a)
        m=deepcopy(self.model)
        c=next(x for x in m["constraints"] if x["id"]==a["functional_sectors"]["relation_id"])
        c["rows"][0]["rhs"]=0
        with self.assertRaisesRegex(ValueError,"R17_SECTOR_INEQUALITY_CHANGED"):
            r17.validate(m,self.info)


@unittest.skipUnless(importlib.util.find_spec("ortools"),"Install official OR-Tools R11 requirements")
class RealR17CPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model,cls.info=r17.build()

    def test_source_categorical_split_and_all_r16_satisfiable(self):
        c=r15.cp_solve(self.model)
        self.assertEqual(c["status"],"SAT")
        self.assertTrue(r15.verify(self.model,c["witness"]))
        s=self.info["functional_sectors"]
        v=c["witness"]["values"]
        self.assertNotEqual(v[s["base"]],v[s["hangar"]])

    def test_synthetic_same_sector_only_contradicts_source_on(self):
        s=self.info["functional_sectors"]
        same=r15.probe("TEST-R17-SAME-SECTOR",[
            r15.row([(s["base"],1),(s["hangar"],-1)],0),
            r15.row([(s["hangar"],1),(s["base"],-1)],0)])
        self.assertEqual(r15.cp_solve(self.model,[same],
                          exclude_families=("r17_sector",))["status"],"SAT")
        bad=r15.cp_solve(self.model,[same])
        self.assertEqual(bad["status"],"INFEASIBLE")
        core={x["id"] for x in bad["unsat_core"]}
        self.assertIn(s["relation_id"],core)
        self.assertIn(same["id"],core)

    def test_false_detachment_of_actual_indexed_corridor_visit_unsat(self):
        v=self.info["source_index_membership_variables"]
        p=r15.probe("TEST-R17-DETACH-REAL-ANGAR-VISIT",[
            r15.row([(v["RT030-D"],1),(v["MOAG-G-0017"],-1)],1),
            r15.row([(v["MOAG-G-0017"],1),(v["RT030-D"],-1)],1)])
        p["any_of"]=True
        self.assertEqual(r15.cp_solve(self.model,[p],
                          exclude_families=("r17_membership",))["status"],"SAT")
        bad=r15.cp_solve(self.model,[p])
        self.assertEqual(bad["status"],"INFEASIBLE")
        ids={x["id"] for x in bad["unsat_core"]}
        self.assertIn(p["id"],ids)
        self.assertTrue(any(x.startswith("R17-MEMBER::") for x in ids))

    def test_source_direct_bridge_door_cannot_be_marked_absent(self):
        var=self.info["portal_flags"]["MOAG-RG-E69"]
        removed=r15.probe("TEST-R17-REMOVE-GALLERY-CONTROL-DOOR",[
            r15.row([(var,-1)],0)])
        self.assertEqual(r15.cp_solve(self.model,[removed],
                          exclude_families=("r17_passage",))["status"],"SAT")
        self.assertEqual(r15.cp_solve(self.model,[removed])["status"],"INFEASIBLE")


if __name__=="__main__":
    unittest.main()
