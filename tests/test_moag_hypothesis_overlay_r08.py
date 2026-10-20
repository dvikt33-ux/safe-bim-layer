"""МОАГ R08: symmetry must be a hypothesis, route gaps cannot create doors."""
from __future__ import annotations
import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/moag_topology"))
import hypothesis_overlay_r08 as overlay
import unified_evidence_graph_r07 as r07
import assemble_evidence_graph_r06 as r06


class MOAGHypothesisOverlay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p = overlay.SYNTH
        cls.g = overlay.read(p / "full_indexed_parametric_graph_r04.json")
        cls.f = overlay.read(p / "progressive_fragments_r05.json")
        cls.b = overlay.read(p / "area_volume_bounds_r05.json")
        cls.routes = overlay.read(overlay.BASE / "v2/character_routes.json")
        cls.source = r06.assemble(cls.g, cls.f, cls.routes, cls.b)
        cls.master = r07.build(cls.g, cls.f, cls.b, cls.routes,
                              assembled=cls.source)
        cls.output = overlay.build(cls.g, cls.f, cls.b, cls.routes,
                                   source=cls.source, master=cls.master)

    def test_one_data_model_multiple_interpretations_not_one_station_plan(self):
        r = self.output
        c = r["counts"]
        self.assertEqual(c["proven_nodes_unchanged"], 575)
        self.assertEqual(c["proven_edges_unchanged"], 761)
        self.assertEqual(c["proven_components_unchanged"], 39)
        self.assertEqual(c["unknown_route_intervals_kept"], 18)
        self.assertEqual(c["unlocated_fixed_elements_kept"], 12)
        self.assertEqual(c["symmetry_and_nonsymmetry_option_groups"], 8)
        self.assertEqual(c["unselected_layout_options"], 16)
        self.assertEqual(c["hypothetical_nodes"], 18)
        self.assertEqual(r["merged_visualization_node_count"], 593)
        self.assertFalse(r["gates"]["hypotheses_can_change_proven_connectivity"])
        self.assertFalse(r["gates"]["symmetry_assumed_as_fact"])
        self.assertEqual(r["counts"]["hypothetical_edges"], 64)
        self.assertEqual(r["merged_visualization_relation_count"], 825)
        self.assertEqual(len(r["composed_graph"]["nodes"]), 593)
        self.assertEqual(len(r["composed_graph"]["edges"]), 825)
        self.assertTrue(r["composed_graph"][
            "graph_unity_does_not_mean_spatial_connectivity"])
        self.assertEqual(r["unified_evidence_graph"]["nodes"],
                         self.master["nodes"])
        self.assertEqual(r["unified_evidence_graph"]["edges"],
                         self.master["edges"])

    def test_every_gap_preserved_without_creating_physical_corridor(self):
        x = self.output
        self.assertEqual(len(x["unknown_transits"]), 18)
        self.assertEqual(len(set(z["hypothetical_node_id"]
                                 for z in x["unknown_transits"])), 18)
        self.assertEqual(
            sum(e["layer"] == "HYPOTHETICAL_GAP_SEGMENT_NOT_CONFIRMED_PATH"
                for e in x["hypothetical_edges"]), 36)
        for node in x["hypothetical_nodes"]:
            self.assertFalse(node["physical_corridor_exists_proven"])
            self.assertTrue(node["not_a_separate_room"])
            self.assertIsNone(node["absolute_XY"])
            self.assertIsNone(node["absolute_Z"])
        self.assertTrue(all(not e["asserts_construction_of_room_or_corridor"]
                            for e in x["hypothetical_edges"]
                            if e["layer"] ==
                            "HYPOTHETICAL_GAP_SEGMENT_NOT_CONFIRMED_PATH"))

    def test_fixed_unplaced_rooms_are_visible_and_have_level_scopes(self):
        x = self.output
        self.assertEqual(len(x["unlocated_fixed_stational_elements"]), 12)
        ids = {i["index_id"]
               for i in x["unlocated_fixed_stational_elements"]}
        self.assertEqual(ids, {
            row["physical_index_id"]
            for row in self.source["unconnected_index_source_review_queue"]
            if row["spatial_inventory_role"] == overlay.STATIONARY})
        n = {x["id"]: x for x in x["unified_evidence_graph"]["nodes"]}
        scopes = [e for e in x["hypothetical_edges"]
                  if e["layer"] == "HYPOTHETICAL_LOCATION_SCOPE_NOT_ACCESS"]
        self.assertTrue(scopes)
        for e in scopes:
            self.assertIn(e["from"], ids)
            self.assertIn(e["to"], overlay.LEVEL_ANCHORS.values())
            self.assertTrue(set(n[e["from"]]["possible_global_levels"]) &
                            set(n[e["to"]]["possible_global_levels"]))
            self.assertFalse(e["asserts_floor_plate_or_xy"])

    def test_symmetric_and_asymmetric_candidates_coexist_without_selection(self):
        x = self.output
        self.assertEqual(len(x["mutually_alternative_layout_groups"]), 8)
        self.assertTrue(all(
            z["selected_variant"] is None and
            not z["applies_stationwide_symmetry"] and
            len(z["mutually_alternative_conceptual_models"]) == 2
            for z in x["mutually_alternative_layout_groups"]))
        candidates = [e for e in x["hypothetical_edges"]
                      if e["layer"] ==
                      "HYPOTHETICAL_SYMMETRY_OR_FUNCTIONAL_LAYOUT"]
        self.assertEqual(len(candidates), 16)
        self.assertTrue(any("SYMMETRY" in e["basis"] for e in candidates))
        self.assertTrue(any(e["basis"] == "NON_SYMMETRIC_ALTERNATIVE"
                            for e in candidates))
        self.assertTrue(all(e["rejection_test"] and
                            e["does_not_assert_a_direct_door"] and
                            e["does_not_infer_new_global_deck"]
                            for e in candidates))
        self.assertTrue(all(not x["selected_as_reconstruction"]
                            for x in self.output["speculative_layout_variants"]))

    def test_all_hypotheses_fail_closed_on_proven_access_and_coordinates(self):
        for e in self.output["hypothetical_edges"]:
            self.assertFalse(e["connects_proven_components"])
            self.assertFalse(e["direct_access_proven"])
            self.assertFalse(e["metric_geometry_proven"])
        self.assertEqual(len(self.master["nodes"]), 575)
        self.assertEqual(len(self.master["edges"]), 761)

    def test_disjoint_level_candidate_rejected(self):
        options = copy.deepcopy(overlay.read(overlay.OPTIONS))
        options["alternative_groups"][0]["options"][0]["to"] = "M-STA-L3-001"
        with self.assertRaisesRegex(ValueError, "HYPOTHESIS_DISJOINT_LEVELS"):
            overlay.build(self.g, self.f, self.b, self.routes,
                          source=self.source, master=self.master,
                          option_file=options)

    def test_foreign_station_hatch_candidate_rejected(self):
        options = copy.deepcopy(overlay.read(overlay.OPTIONS))
        options["alternative_groups"][0]["options"][0]["to"] = (
            "M-L3-CABLE-HATCH-001")
        with self.assertRaisesRegex(
                ValueError, "HYPOTHESIS_UNKNOWN_OR_FOREIGN_STATION_ENDPOINT"):
            overlay.build(self.g, self.f, self.b, self.routes,
                          source=self.source, master=self.master,
                          option_file=options)

    def test_permanent_identity_exclusion_not_turned_to_hypothesis(self):
        options = copy.deepcopy(overlay.read(overlay.OPTIONS))
        options["alternative_groups"][0]["options"][0]["from"] = (
            "M-L1-CH-ST-001")
        options["alternative_groups"][0]["options"][0]["to"] = (
            "M-L1-AH-OLD-ST-001")
        with self.assertRaisesRegex(
                ValueError, "PROHIBITED_IDENTITY_AS_SPATIAL_HYPOTHESIS"):
            overlay.build(self.g, self.f, self.b, self.routes,
                          source=self.source, master=self.master,
                          option_file=options)

    def test_unknown_transition_between_levels_remains_vertical_option(self):
        master = copy.deepcopy(self.master)
        gap = self.source["narrative_gaps"][0]
        ids = {"ROUTE::" + gap["route_id"] + "::" + gap["from"]: [1],
               "ROUTE::" + gap["route_id"] + "::" + gap["to"]: [2]}
        for n in master["nodes"]:
            if n["id"] in ids:
                n["possible_global_levels"] = ids[n["id"]]
        x = overlay.build(self.g, self.f, self.b, self.routes,
                          source=self.source, master=master)
        first = x["unknown_transits"][0]
        self.assertTrue(first["vertical_transition_unresolved"])
        self.assertEqual(first["candidate_level_domain"], [1, 2])
        self.assertFalse(x["gates"]["extra_global_decks_inferred"])


if __name__ == "__main__":
    unittest.main()
