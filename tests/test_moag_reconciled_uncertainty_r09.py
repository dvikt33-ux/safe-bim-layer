"""МОАГ R09: reconciled uncertainty graph, not an extra station geometry."""
from __future__ import annotations
import copy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/moag_topology"))
import reconcile_uncertainty_r09 as r09


class ReconciledR09(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p = r09.SYNTH
        cls.g = r09.read(p / "full_indexed_parametric_graph_r04.json")
        cls.f = r09.read(p / "progressive_fragments_r05.json")
        cls.b = r09.read(p / "area_volume_bounds_r05.json")
        cls.r = r09.read(r09.BASE / "v2/character_routes.json")
        cls.result = r09.build(cls.g, cls.f, cls.b, cls.r)

    def test_single_master_contains_all_without_creating_rooms(self):
        data = self.result
        q = data["quantities"]
        self.assertEqual(q["total_vertices"], 593)
        self.assertEqual(q["hypothetical_vertices"], 18)
        self.assertEqual(q["total_typed_edges"], 845)
        self.assertEqual(q["hypothetical_edges"], 84)
        self.assertEqual(data["source_invariants"]["proven_nodes"], 575)
        self.assertEqual(data["source_invariants"]["proven_edges"], 761)
        self.assertEqual(data["source_invariants"]["proven_components"], 39)
        self.assertEqual(data["source_invariants"]["approved_direct_access"], 25)
        self.assertFalse(data["gates"]["archicad_write"])
        self.assertFalse(data["gates"]["BIM_release_approved"])
        self.assertEqual(len(data["all_197_unlocated_index_provenance"]), 197)

    def test_ambiguous_gaps_are_single_virtual_nodes_with_two_names(self):
        result = self.result
        q = result["quantities"]
        self.assertEqual(q["unknown_route_gaps_reconciled"], 18)
        self.assertEqual(q["observed_transitions_still_without_direct_geometry"], 306)
        gaps = result["gap_placeholders"]
        self.assertEqual(len({x["canonical_hypothetical_node_id"]
                              for x in gaps}), 18)
        self.assertEqual(len({x["secondary_register_alias"] for x in gaps}), 18)
        self.assertTrue(all(x["same_missing_information_not_two_physical_corridors"]
                            and x["no_intermediate_room_count_proven"]
                            and x["level_domains_have_different_meanings"]
                            for x in gaps))
        self.assertTrue(all(
            set(x["joint_candidate_level_domain"]) <=
            set(x["union_of_boundary_level_domains"]) for x in gaps))

    def test_duplicate_candidates_are_crosswalks_not_double_links(self):
        result = self.result
        q = result["quantities"]
        self.assertEqual(q["primary_layout_variant_count"], 16)
        self.assertEqual(q["secondary_placement_variant_count"], 24)
        self.assertEqual(q["cross_referenced_same_endpoint_candidates"], 4)
        self.assertEqual(q["distinct_secondary_placement_edges_added"], 20)
        self.assertEqual(q["fixed_objects_with_multiple_options"], 12)
        self.assertEqual(q["unselected_compositional_patterns"], 3)
        for x in result["overlapping_proposals_kept_as_cross_references"]:
            self.assertTrue(x["same_pair_only_not_equivalent_spatial_hypothesis"])
            self.assertTrue(x["source_reconciliation_required"])
        self.assertTrue(all(x["none_of_the_above_is_allowed"]
                            and x["not_selected"]
                            for x in result["unlocated_fixed_element_options"]))

    def test_hypothesis_edges_never_change_access_or_component_count(self):
        data = self.result
        proven = data["source_invariants"]["proven_edges"]
        soft = data["edges"][proven:]
        self.assertTrue(all(not e.get("joins_approved_evidence_component", False)
                            and not e.get("proves_direct_access", False)
                            and not e.get("direct_access_proven", False)
                            and not e.get("connects_proven_components", False)
                            and e.get("metric_geometry_proven") is False
                            for e in soft))
        self.assertFalse(data["gates"]["hypothesis_may_merge_evidence_components"])
        self.assertTrue(data["gates"]["symmetry_is_never_mandatory"])
        self.assertEqual(data["quantities"]["hypothetical_edges"], len(soft))

    def test_divergent_source_graph_fails_instead_of_fusing(self):
        left = r09.r08a.build(self.g, self.f, self.b, self.r)
        right = r09.r08b.build(self.g, self.f, self.b, self.r)
        invalid = copy.deepcopy(right)
        invalid["edges"][0]["source_ids"] = ["FAKE-SOURCE"]
        with self.assertRaisesRegex(ValueError, "R08_PROVEN_GRAPHS_DIVERGED"):
            r09.build(self.g, self.f, self.b, self.r, left=left, right=invalid)

    def test_inconsistent_secondary_gap_source_rejected(self):
        left = r09.r08a.build(self.g, self.f, self.b, self.r)
        right = r09.r08b.build(self.g, self.f, self.b, self.r)
        invalid = copy.deepcopy(right)
        invalid["unknown_route_segments"][0]["source_pages"] = ["B9-999"]
        with self.assertRaisesRegex(ValueError, "R08_ROUTE_GAP_PROVENANCE_OR_LEVEL_CONFLICT"):
            r09.build(self.g, self.f, self.b, self.r, left=left, right=invalid)


if __name__ == "__main__":
    unittest.main()
