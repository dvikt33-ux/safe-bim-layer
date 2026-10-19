"""R05 evidence-first incremental topology: no invented locations."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"docs/research/apa-results/moag/synthesis"
SPEC=importlib.util.spec_from_file_location("moag_progressive_solver",
    ROOT/"tools/moag_topology/progressive_constraint_solver_r05.py")
MOD=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)

class ProgressiveSpatialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g=json.loads((BASE/"full_indexed_parametric_graph_r04.json").read_text(encoding="utf-8"))
        cls.f=json.loads((BASE/"progressive_fragments_r05.json").read_text(encoding="utf-8"))
        cls.o=json.loads((ROOT/"docs/research/apa-results/moag/v2/page_observations.json").read_text(encoding="utf-8"))

    def test_fragment_sources_and_existing_indices(self):
        records={o["id"]:o for o in self.o["observations"]}
        known={x["id"] for x in self.g["indexed_source_entities"]+self.g["indexed_r03_entities"]}
        nodes=self.f["physical_entities"]
        self.assertEqual(len(nodes),43)
        self.assertEqual(len(self.f["typed_edges"]),33)
        for x in nodes:
            self.assertNotIn(x["id"],known)
            known.add(x["id"])
            self.assertFalse(x["geometry_authorized"])
            self.assertIsNone(x["xy"])
            self.assertIsNone(x["dimensions_m"])
            self.assertTrue(x["source_ids"])
            for id in x["source_ids"]:
                self.assertEqual(records[id]["station_id"],"MOAG")
                self.assertEqual(records[id]["evidence_class"],"DIRECT_TEXT")
        for x in self.f["typed_edges"]:
            self.assertIn(x["from"],known)
            self.assertIn(x["to"],known)
            self.assertFalse(x["geometry_authorized"])
            self.assertTrue(all(id in records for id in x["source_ids"]))

    def test_no_anchor_preserves_unknowns(self):
        result=MOD.solve(self.g,self.f)
        self.assertEqual(result["counts"]["all_nodes"],197)
        self.assertGreater(result["counts"]["level_nonunique"],0)
        ids={x["node_id"] for x in result["level_domains_still_open"]}
        self.assertIn("M-L2-EMMA-SUITE-001",ids)
        self.assertIn("M-L2-EMMA-KITCHEN-001",ids)
        self.assertFalse(result["gates"]["planar_embedding_unique"])
        self.assertFalse(result["gates"]["archicad_write"])

    def test_added_anchor_propagates_without_erasing_provenance(self):
        base=MOD.solve(self.g,self.f)
        anchored=MOD.solve(self.g,self.f,{"M-L2-EMMA-SUITE-001":{"global_level":2}})
        self.assertGreater(anchored["counts"]["level_singletons"],base["counts"]["level_singletons"])
        levels={x["node_id"]:x["global_level"] for x in anchored["known_or_inferred_levels"]}
        for id in ["M-L2-EMMA-SUITE-001","M-L2-EMMA-KITCHEN-001",
                   "M-L2-EMMA-LIVING-001","M-L2-EMMA-BEDROOMS-001","M-L2-EMMA-BATH-001"]:
            self.assertEqual(levels[id],2)
        self.assertFalse(anchored["gates"]["planar_embedding_unique"])

    def test_conflicting_anchor_and_evidence_fails_closed(self):
        with self.assertRaisesRegex(ValueError,"ANCHOR_CONTRADICTS_TEXT_LEVEL"):
            MOD.solve(self.g,self.f,{"M-L2-TUNNEL-002":{"global_level":3}})
        corrupted=copy.deepcopy(self.f)
        for node in corrupted["physical_entities"]:
            if node["id"]=="M-L2-LIB-GLASS-DOOR-001":
                node["global_level"]=3
        with self.assertRaisesRegex(ValueError,"INCONSISTENT_LEVELS"):
            MOD.solve(self.g,corrupted)

    def test_distinct_libraries_and_tunnel_numbers(self):
        result=MOD.solve(self.g,self.f)
        negatives={(e["from"],e["to"]) for e in result["identity_exclusions"]}
        self.assertIn(("M-L2-LIB-OVAL-001","M-L2-LIB-NOWINDOW-001"),negatives)
        self.assertIn(("M-L2-TUNNEL-002","M-L2-TUNNEL-008"),negatives)
        hypotheses={(e["from"],e["to"]) for e in result["identity_hypotheses"]}
        self.assertIn(("M-L2-LIB-NOWINDOW-001","M-L2-LIB-MEETING-001"),hypotheses)

    def test_no_source_claims_metric_uniqueness(self):
        result=MOD.solve(self.g,self.f)
        self.assertFalse(result["gates"]["metric_coordinates_known"])
        self.assertFalse(result["gates"]["all_spatial_hypotheses_eliminated"])
        self.assertTrue(result["topological_fragments"])
        self.assertTrue(all(not c["spatial_embedding_unique"] for c in result["topological_fragments"]))

if __name__=="__main__":
    unittest.main()
