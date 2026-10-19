"""Regression tests for MOAG R06 source-backed graph stitching.

Route occurrences are proof records, not architectural rooms or extra decks.
"""
from __future__ import annotations
import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/moag_topology"))
BASE = ROOT / "docs/research/apa-results/moag"
SPEC = importlib.util.spec_from_file_location(
    "moag_r06_assemble", ROOT / "tools/moag_topology/assemble_evidence_graph_r06.py")
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


def load(relative):
    return json.loads((BASE / relative).read_text(encoding="utf-8"))


class EvidenceGraphR06Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph = load("synthesis/full_indexed_parametric_graph_r04.json")
        cls.fragments = load("synthesis/progressive_fragments_r05.json")
        cls.bounds = load("synthesis/area_volume_bounds_r05.json")
        cls.routes = load("v2/character_routes.json")
        cls.result = MOD.assemble(cls.graph, cls.fragments, cls.routes, cls.bounds)

    def test_all_indexed_physical_objects_retained(self):
        r = self.result
        self.assertEqual(r["counts"]["physical_indices"], 197)
        self.assertEqual(r["counts"]["route_ledgers"], len(self.routes["routes"]))
        self.assertEqual(r["counts"]["route_occurrences"],
                         sum(len(x["nodes"]) for x in self.routes["routes"]))
        self.assertEqual(r["counts"]["area_profiles"], 157)
        self.assertFalse(r["gates"]["archicad_write"])
        self.assertFalse(r["gates"]["metric_xy_known"])
        self.assertFalse(r["gates"]["global_extra_decks_inferred_from_local_galleries"])

    def test_routes_stitch_components_without_claiming_geometry(self):
        r = self.result
        self.assertLessEqual(r["counts"]["after_routes_components"],
                             r["counts"]["before_routes_components"]
                             + r["counts"]["route_occurrences"])
        self.assertTrue(any(e["type"] == "ROUTE_VISITS_INDEX"
                            for e in r["typed_evidence_edges"]))
        self.assertTrue(any(e["type"] == "OBSERVED_ROUTE_ORDER_NOT_DIRECT_DOOR"
                            for e in r["typed_evidence_edges"]))
        self.assertTrue(all(e["source_ids"] and not e["metric_geometry_proven"]
                            for e in r["typed_evidence_edges"]))
        self.assertEqual(sum(c["route_occurrence_count"]
                             for c in r["connected_evidence_components"]),
                         r["counts"]["route_occurrences"])
        self.assertTrue(all(not c["walkable_subgraph_proven"]
                            for c in r["connected_evidence_components"]))

    def test_narrative_gap_is_not_connected_across_unseen_route(self):
        r = self.result
        self.assertGreater(r["counts"]["narrative_gaps"], 0)
        all_links = {(e["from"], e["to"])
                     for e in r["typed_evidence_edges"]
                     if e["type"] == "OBSERVED_ROUTE_ORDER_NOT_DIRECT_DOOR"}
        for gap in r["narrative_gaps"]:
            left = "ROUTE::" + gap["route_id"] + "::" + gap["from"]
            right = "ROUTE::" + gap["route_id"] + "::" + gap["to"]
            self.assertNotIn((left, right), all_links)

    def test_multilevel_ventilation_alias_keeps_conflict_visible(self):
        items = self.result["route_location_review"]
        self.assertTrue(any(x["code"] == "MULTILEVEL_ALIAS_REVIEW"
                            and x["route_id"] == "RT-011"
                            and x["target"] == "MOAG-G-0016" for x in items))
        self.assertFalse(self.result["gates"]["metric_z_known"])

    def test_invalid_provenance_fails_closed(self):
        data = copy.deepcopy(self.routes)
        data["routes"][0]["nodes"][0]["source_page_id"] = "UNVERIFIED"
        with self.assertRaisesRegex(ValueError, "ROUTE_STEP_WITHOUT_PAGE_PROVENANCE"):
            MOD.assemble(self.graph, self.fragments, data, self.bounds)

    def test_duplicate_route_step_fails_closed(self):
        data = copy.deepcopy(self.routes)
        data["routes"][0]["nodes"][1]["id"] = data["routes"][0]["nodes"][0]["id"]
        with self.assertRaisesRegex(ValueError, "DUPLICATE_ROUTE_STEP"):
            MOD.assemble(self.graph, self.fragments, data, self.bounds)

    def test_vertical_cycles_are_diagnostic_not_false_metric_z(self):
        data = copy.deepcopy(self.routes)
        route = data["routes"][0]
        a, b = route["nodes"][:2]
        route.setdefault("constraints", []).extend([
            {"kind": "RELATIVE_Z", "higher": a["id"], "lower": b["id"],
             "source_page_id": a["source_page_id"]},
            {"kind": "RELATIVE_Z", "higher": b["id"], "lower": a["id"],
             "source_page_id": a["source_page_id"]},
        ])
        result = MOD.assemble(self.graph, self.fragments, data, self.bounds)
        self.assertIn("VERTICAL_ORDER_CYCLE",
                      {x["code"] for x in result["route_location_review"]})
        self.assertFalse(result["gates"]["metric_z_known"])

    def test_area_conflicts_remain_visible_after_route_stitching(self):
        result = MOD.assemble(
            self.graph, self.fragments, self.routes, self.bounds,
            area_overrides={"M-L2-EMMA-SUITE-001": {"max_area_m2": 30}})
        self.assertEqual(result["area_volume"]["status"], "CONFLICTS")
        self.assertGreater(result["counts"]["area_check_failures"], 0)
        self.assertNotEqual(result["status"], "CONSISTENT_PARTIAL")


if __name__ == "__main__":
    unittest.main()
