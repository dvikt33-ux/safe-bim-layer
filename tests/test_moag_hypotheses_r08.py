"""MOAG R08 uncertainty overlay: every unknown survives without false topology."""
from pathlib import Path
import copy
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/moag_topology"))
import hypothetical_structure_r08 as module

BASE = ROOT / "docs/research/apa-results/moag/synthesis"

class UncertaintyGraphR08(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g = module.read(BASE / "full_indexed_parametric_graph_r04.json")
        cls.f = module.read(BASE / "progressive_fragments_r05.json")
        cls.b = module.read(BASE / "area_volume_bounds_r05.json")
        cls.routes = module.read(ROOT /
            "docs/research/apa-results/moag/v2/character_routes.json")
        cls.proposals = module.read(BASE / "spatial_hypotheses_r08.json")
        cls.output = module.build(cls.g, cls.f, cls.b, cls.routes)

    def test_twelve_isolates_have_all_alternatives_or_unlocated(self):
        inv = self.output["inventory"]
        self.assertEqual(inv["approved_r07_node_count"], 575)
        self.assertEqual(inv["approved_r07_edge_count"], 761)
        self.assertEqual(inv["unlocated_fixed_object_groups"], 12)
        self.assertEqual(inv["alternative_placement_edges"], 24)
        self.assertEqual(len(self.output["isolated_object_placement_hypotheses"]), 12)
        for group in self.output["isolated_object_placement_hypotheses"]:
            self.assertTrue(group["known_to_exist"])
            self.assertFalse(group["exact_location_known"])
            self.assertTrue(group["alternatives_exclusive_or_neither"])
            self.assertTrue(group["unlocated_option_always_allowed"])
            self.assertEqual(len(group["placement_choices"]), 2)
            self.assertTrue(all(not x["proves_connection"]
                                for x in group["placement_choices"]))

    def test_narrative_gap_is_reserved_not_invented_as_room(self):
        inv = self.output["inventory"]
        self.assertEqual(inv["still_unknown_route_gaps"], 18)
        self.assertEqual(inv["new_unknown_route_placeholders_not_new_rooms"], 18)
        self.assertEqual(inv["route_gap_candidate_edges"], 36)
        self.assertEqual(inv["total_nodes_including_nonphysical_placeholders"], 593)
        self.assertEqual(inv["total_relations_including_unapproved_scenarios"], 821)
        self.assertTrue(all(x["not_counted_as_physical_room"] and
                            x["no_direct_passage_concluded"]
                            for x in self.output["unknown_route_segments"]))
        placeholders = self.output["nodes"][575:]
        self.assertTrue(all(x["not_a_separate_room"] and
                            not x["physical_element_count_inferred"]
                            for x in placeholders))

    def test_none_of_60_hypotheses_changes_verified_connectivity(self):
        u = self.output
        self.assertEqual(u["inventory"]["approved_qualitative_physical_components"], 39)
        self.assertEqual(u["inventory"]["approved_explicit_access_edges"], 25)
        self.assertEqual(u["inventory"]["area_profiles_preserved"], 197)
        new = u["edges"][761:]
        self.assertEqual(len(new), 60)
        self.assertTrue(all(x["layer"] == "R08_HYPOTHESIS_NOT_A_PHYSICAL_LINK"
                            and not x["joins_approved_evidence_component"]
                            and not x["proves_direct_access"]
                            and not x["metric_geometry_proven"] for x in new))
        self.assertFalse(u["gates"]["bim_geometry_authorized"])
        self.assertFalse(u["gates"]["archicad_write"])

    def test_symmetry_is_optional_and_does_not_add_global_decks(self):
        patterns = self.output["nonbinding_symmetry_and_analogy_scenarios"]
        self.assertEqual(len(patterns), 3)
        self.assertEqual({x["kind"] for x in patterns},
                         {"RADIAL_SECTOR_ANALOGY",
                          "REPEATED_BAY_ANALOGY",
                          "CONCENTRIC_BLOCK_DESIGN_SCENARIO"})
        self.assertTrue(all(x["global_decks_added"] == 0 and
                            x["physical_component_merges"] == 0
                            for x in patterns))
        self.assertEqual(self.output["inventory"]["proven_metric_xy_indices"], 0)

    def test_forbid_cross_deck_and_unrelated_identity_merges(self):
        cases = []
        a = copy.deepcopy(self.proposals)
        item = next(x for x in a["isolation_candidate_groups"]
                    if x["target_index_id"] == "M-L2-DINING-001")
        item["possible_anchors"][0] = "M-L3-LOG-001"
        cases.append((a, "HYPOTHESIS_DISJOINT_GLOBAL_LEVELS"))
        b = copy.deepcopy(self.proposals)
        item = next(x for x in b["isolation_candidate_groups"]
                    if x["target_index_id"] == "M-L2-DINING-001")
        item["possible_anchors"][0] = "M-L3-CABLE-HATCH-001"
        cases.append((b, "HYPOTHESIS_CONTRADICTS_NEGATIVE_IDENTITY"))
        for settings, error in cases:
            with self.subTest(error=error):
                with self.assertRaisesRegex(ValueError, error):
                    module.build(self.g, self.f, self.b, self.routes,
                                 proposals=settings)

    def test_no_fabricated_primary_evidence_or_auto_symmetry(self):
        a = copy.deepcopy(self.proposals)
        a["isolation_candidate_groups"][0]["source_observation_or_page_ids"] = [
            "P-671"]
        with self.assertRaisesRegex(ValueError, "HYPOTHESIS_USES_FOREIGN_STATION_SOURCE"):
            module.build(self.g, self.f, self.b, self.routes,
                         proposals=a)
        b = copy.deepcopy(self.proposals)
        b["analogical_patterns"][0]["produces_graph_edges"] = True
        with self.assertRaisesRegex(ValueError, "SYMMETRY_CANNOT_PROVE_METRIC_TOPOLOGY"):
            module.build(self.g, self.f, self.b, self.routes,
                         proposals=b)
        c = copy.deepcopy(self.proposals)
        c["isolation_candidate_groups"] = c["isolation_candidate_groups"][:-1]
        with self.assertRaisesRegex(ValueError, "NOT_ALL_UNLOCATED_FIXED_INDICES_PRESERVED"):
            module.build(self.g, self.f, self.b, self.routes,
                         proposals=c)

if __name__ == "__main__":
    unittest.main()
