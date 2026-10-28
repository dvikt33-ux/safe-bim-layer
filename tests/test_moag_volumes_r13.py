"""R13: explicit separation between certified book relationships and demo volume boxes."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools/moag_topology"))
import scenario_volumes_r13 as r13
import solver_r11 as r11


class SourceBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m=r13.build()

    def test_three_stepped_author_qualitative_domains_not_hull_meshes(self):
        m=self.m
        self.assertEqual(len(m["blocks"]),3)
        self.assertEqual([x["id"] for x in m["blocks"]],[1,2,3])
        self.assertEqual([x["bounds"][0] for x in m["blocks"]],[80,64,48])
        self.assertFalse(m["block_rectangles_are_hull_mesh"])
        self.assertFalse(m["author_exterior_exact_mesh_verified"])
        self.assertFalse(m["geometry_approved"])
        self.assertFalse(m["archicad_write"])

    def test_source_backed_entities_and_raised_operator_enclosures(self):
        m=self.m
        self.assertEqual(len(m["volumes"]),12)
        self.assertEqual(sum(bool(v["parent"]) for v in m["volumes"]),3)
        self.assertEqual({v["id"] for v in m["volumes"] if v["parent"]},
            {"M-L1-FH-001-CTRL","M-L1-FH-002-CTRL","M-L1-AH-OLD-CTRL-001"})
        self.assertTrue(all(v["source_refs"] and v["sample_size"]
                            and not v["metric_length_known"] for v in m["volumes"]))
        for v in m["volumes"]:
            if v["parent"]:
                self.assertTrue(v["parent_enclosure_source"]["sources"])
                self.assertTrue(all(s.get("url") for s in v["parent_enclosure_source"]["sources"]))
        self.assertEqual(len(set(m["R09_fingerprints"].values())),1)
        self.assertEqual(next(iter(m["R09_fingerprints"].values())),r11.digest(r11.inputs()[-1]))

    def test_abstract_boxes_not_claimed_as_room_shapes(self):
        self.assertTrue(all(v["shape"]=="BOUNDING_BOX_ONLY_NOT_REAL_ROOM_SHAPE"
                            for v in self.m["volumes"]))
        self.assertTrue(all(not v["area_profile_used_as_measured_m2"]
                            for v in self.m["volumes"]))
        self.assertFalse(self.m["full_floors_inferred"])
        self.assertFalse(self.m["minimum_distance_between_bases_proven"])
        self.assertFalse(self.m["cross_block_internal_routes_verified"])

    def test_only_named_distinct_spaces_cannot_overlap(self):
        pairs={frozenset((a["a"],a["b"])) for a in self.m["disjoint_3d_pairs"]}
        self.assertEqual(len(pairs),4)
        self.assertIn(frozenset(("MOAG-G-0008","MOAG-G-0009")),pairs)
        self.assertIn(frozenset(("M-L1-FH-001","M-L1-FH-002")),pairs)
        self.assertNotIn(frozenset(("MOAG-G-0008","M-L1-FH-001")),pairs)

    def test_author_plan_hints_stay_relative_on_sheet(self):
        hints=self.m["schematic_plan_label_order"]
        self.assertEqual(len(hints),4)
        self.assertTrue(all(x["status"]=="AUTHOR_LABEL_POSITION_NOT_PHYSICAL_COORDINATE" for x in hints))

    def test_unauthorized_geometry_or_parent_is_rejected(self):
        m=deepcopy(self.m)
        m["geometry_approved"]=True
        with self.assertRaisesRegex(ValueError,"UNAUTHORIZED_BIM"):
            r13.validate(m)
        m=deepcopy(self.m)
        child=next(v for v in m["volumes"] if v["parent"])
        child["parent"]="MOAG-G-0009"
        with self.assertRaisesRegex(ValueError,"UNPROVEN_PARENTHOOD"):
            r13.validate(m)
        m=deepcopy(self.m)
        m["volumes"][0]["metric_length_known"]=True
        with self.assertRaisesRegex(ValueError,"UNSUPPORTED_MEASURED"):
            r13.validate(m)


@unittest.skipUnless(importlib.util.find_spec("ortools"),"Install R11 solver requirements")
class RealVolumeSolverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m=r13.build()

    def test_3d_scenario_is_consistent_and_witness_verified(self):
        res=r13.cp_solve(self.m)
        self.assertEqual(res["status"],"SAT")
        self.assertTrue(r13.verify(self.m,res["witness"]))

    def test_inject_child_outside_source_proven_parent_unsat_with_source(self):
        inverse={"id":"TEST-UPPER-OUTSIDE","type":"SYNTHETIC_CHILD_OUTSIDE_PARENT",
                 "child":"M-L1-FH-001-CTRL","parent":"M-L1-FH-001"}
        bad=r13.cp_solve(self.m,inverse)
        self.assertEqual(bad["status"],"INFEASIBLE")
        ids={x["id"] for x in bad["unsat_core"]}
        self.assertIn("TEST-UPPER-OUTSIDE",ids)
        self.assertIn("R13-ENCLOSE-M-L1-FH-001-CTRL",ids)
        src=[s for x in bad["unsat_core"] for s in x.get("sources",[])]
        self.assertTrue(any("p=14" in x["url"] for x in src))

    def test_corrupted_3d_witness_fails_closed(self):
        w=deepcopy(r13.cp_solve(self.m)["witness"])
        ids={v["id"]:i for i,v in enumerate(self.m["volumes"])}
        w["x"][ids["M-L1-FH-001-CTRL"]]=80
        with self.assertRaisesRegex(ValueError,"OUTSIDE_SCENARIO_HULL_BOUNDING_DOMAIN"):
            r13.verify(self.m,w)
        w=deepcopy(r13.cp_solve(self.m)["witness"])
        w["z"][ids["M-L1-FH-001-CTRL"]]=w["z"][ids["M-L1-FH-001"]]
        with self.assertRaisesRegex(ValueError,"UPPER_ROOM_NOT_ABOVE_PARENT_FLOOR"):
            r13.verify(self.m,w)

if __name__=="__main__":
    unittest.main()
