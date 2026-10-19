"""End-to-end MOAG graph fragment and editable area interval tests."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"docs/research/apa-results/moag/synthesis"
sys.path.insert(0,str(ROOT/"tools/moag_topology"))
SPEC=importlib.util.spec_from_file_location("moag_full_assembly",
    ROOT/"tools/moag_topology/assemble_spatial_constraints_r05.py")
MOD=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)

class JoinedR05(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        def read(p):return json.loads((BASE/p).read_text(encoding="utf-8"))
        cls.graph=read("full_indexed_parametric_graph_r04.json")
        cls.fragments=read("progressive_fragments_r05.json")
        cls.bounds=read("area_volume_bounds_r05.json")
        cls.demo=read("demo_override_r04_NONCANON.json")
        cls.options=read("demo_layout_candidates_r05_NONCANON.json")

    def test_full_source_inventory_and_constrained_blocks(self):
        r=MOD.run(self.graph,self.fragments,self.bounds)
        self.assertEqual(r["graph_inventory"]["r04_source_nodes"],117)
        self.assertEqual(r["graph_inventory"]["r03_entities"],37)
        self.assertEqual(r["graph_inventory"]["r05_new_entities"],43)
        self.assertEqual(r["graph_inventory"]["observations"],690)
        self.assertEqual(r["topology"]["counts"]["all_nodes"],197)
        self.assertGreater(r["topology"]["counts"]["new_links_that_joined_fragments"],0)
        self.assertEqual(r["area_and_volume"]["counts"]["with_area"],157)
        self.assertFalse(r["gates"]["coordinates_proven"])
        self.assertFalse(r["gates"]["geometry_approved"])

    def test_variants_filtered_by_level_and_area_not_fake_unique_geometry(self):
        r=MOD.run(self.graph,self.fragments,self.bounds,self.demo,variants=self.options)
        self.assertEqual(r["status"],"CONSISTENT_PARTIAL_NOT_PROVEN")
        by={v["id"]:v for v in r["compared_variants"]}
        self.assertTrue(by["A_EXPLICIT_LEVELS"]["passes_known_topology_and_area"])
        self.assertFalse(by["B_CARGO_IN_CHILD_SUITE"]["passes_known_topology_and_area"])
        self.assertFalse(by["C_LOWER_CARGO_IN_UPPER_BLOCK"]["passes_known_topology_and_area"])
        self.assertTrue(r["variation_summary"]["unique_among_submitted"])
        self.assertFalse(r["variation_summary"]["unique_in_all_possible_geometry"])

    def test_anchored_local_suite_cannot_create_absolute_plan(self):
        r=MOD.run(self.graph,self.fragments,self.bounds,
                  anchors={"M-L2-EMMA-SUITE-001":{"global_level":2}})
        found={x["node_id"]:x["global_level"] for x in r["topology"]["known_or_inferred_levels"]}
        self.assertEqual(found["M-L2-EMMA-KITCHEN-001"],2)
        self.assertFalse(r["topology"]["gates"]["metric_coordinates_known"])

    def test_inconsistent_room_or_hangar_reported(self):
        r=MOD.run(self.graph,self.fragments,self.bounds,self.demo,
                  room_sizes={"M-L2-EMMA-SUITE-001":{"max_area_m2":30}})
        self.assertEqual(r["status"],"CONFLICTS")
        failures=[x for x in r["area_and_volume"]["checks"] if x["status"]=="FAIL"]
        self.assertTrue(any(x["id"]=="DISJOINT_ROOMS_M-L2-EMMA-SUITE-001" for x in failures))

if __name__=="__main__":
    unittest.main()
