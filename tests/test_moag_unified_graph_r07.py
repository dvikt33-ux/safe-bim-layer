"""МОАГ R07: one typed graph must not promote guesses or identity aliases to doors."""
from pathlib import Path
import copy
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/moag_topology"))
import unified_evidence_graph_r07 as unified

BASE = ROOT / "docs/research/apa-results/moag/synthesis"


class UnifiedGraphR07(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g = unified.read(BASE / "full_indexed_parametric_graph_r04.json")
        cls.f = unified.read(BASE / "progressive_fragments_r05.json")
        cls.b = unified.read(BASE / "area_volume_bounds_r05.json")
        cls.routes = unified.read(ROOT /
            "docs/research/apa-results/moag/v2/character_routes.json")
        cls.output = unified.build(cls.g, cls.f, cls.b, cls.routes)

    def test_one_inventory_without_fake_single_connected_plan(self):
        u = self.output
        c = u["inventory"]
        self.assertEqual(c["physical_or_conceptual_indices"], 197)
        self.assertEqual(c["route_occurrences"], 378)
        self.assertEqual(c["all_vertices"], 575)
        self.assertGreater(c["all_typed_relations"], 500)
        self.assertGreater(c["qualitative_components_with_physical_indices"], 1)
        self.assertFalse(u["gates"]["one_qualitative_spatial_component"])
        self.assertFalse(u["gates"]["metric_XY_Z_proven"])
        self.assertFalse(u["gates"]["archicad_write"])
        self.assertEqual(len(u["component_membership_not_rooms_or_geometry"]), 575)

    def test_access_is_strict_and_context_never_traversable(self):
        u = self.output
        edges = u["edges"]
        self.assertEqual(len(edges), len({x["id"] for x in edges}))
        self.assertEqual(u["inventory"]["direct_access_edges"], 25)
        self.assertEqual(u["inventory"]["direct_access_components"], 173)
        self.assertTrue(all(e["layer"] == "EXPLICIT_ACCESS" and
                            e["joins_approved_evidence_component"]
                            for e in edges if e["proves_direct_access"]))
        contexts = {"REFERENT_CROSSWALK_NOT_PHYSICAL_IDENTITY",
                    "PROHIBITED_IDENTITY_MERGE",
                    "PROHIBITED_IDENTITY_OR_INFERENCE",
                    "UNVERIFIED_CANDIDATE_NOT_A_CONNECTION",
                    "DOCUMENTED_GAP_NO_ROUTE_LINK",
                    "REJECTED_INFERENCE_NOT_A_CONNECTION"}
        self.assertTrue(all(not x["proves_direct_access"] and
                            not x["joins_approved_evidence_component"]
                            for x in edges if x["layer"] in contexts))
        self.assertEqual(
            u["inventory"]["narrative_gaps_not_joined"], 18)
        self.assertEqual(u["inventory"]["source_alias_crosswalks"], 22)

    def test_previous_airlock_hypothesis_closed_not_duplicate_edge(self):
        u = self.output
        self.assertEqual(u["inventory"]["resolved_obsolete_hypotheses"], 1)
        self.assertEqual(u["resolved_obsolete_hypotheses"][0]["hypothesis_id"],
                         "H06-001")
        self.assertEqual(u["resolved_obsolete_hypotheses"][0]["accepted_edge_id"],
                         "S06-008")
        self.assertEqual(sum(x["id"] == "S06-008" for x in u["edges"]), 1)
        self.assertFalse(any(x["id"] == "CANDIDATE:H06-001" for x in u["edges"]))

    def test_cross_level_school_isolation_hypothesis_rejected(self):
        u = self.output
        self.assertEqual(u["inventory"]["rejected_invalid_hypotheses"], 1)
        self.assertEqual(u["rejected_invalid_hypotheses"][0]["hypothesis_id"],
                         "H06-003")
        e = next(x for x in u["edges"] if x["id"] == "REJECTED:H06-003")
        self.assertFalse(e["joins_approved_evidence_component"])
        self.assertEqual(e["layer"], "REJECTED_INFERENCE_NOT_A_CONNECTION")
        self.assertTrue(all(not x["proves_direct_access"]
                            for x in u["edges"] if x["id"].startswith("CANDIDATE:")))
        self.assertEqual(u["inventory"]["open_connector_hypotheses"], 1)

    def test_wrong_claim_of_superseded_hypothesis_is_rejected(self):
        invalid = unified.read(unified.assembler.BRIDGES)
        invalid = copy.deepcopy(invalid)
        invalid["deferred_hypotheses"][0]["superseded_by"] = "S06-010"
        with self.assertRaisesRegex(
                ValueError, "RESOLVED_HYPOTHESIS_MISSING_APPROVED_LINK"):
            unified.build(self.g, self.f, self.b, self.routes,
                          explicit=invalid)

    def test_foreign_station_hatches_not_promoted_to_identity(self):
        e = next(x for x in self.output["edges"]
                 if x["id"] == "R05-NEGATIVE:MOAG-R05-022")
        self.assertEqual(e["layer"], "UNVERIFIED_STATION_PROVENANCE")
        self.assertFalse(e["joins_approved_evidence_component"])


if __name__ == "__main__":
    unittest.main()
