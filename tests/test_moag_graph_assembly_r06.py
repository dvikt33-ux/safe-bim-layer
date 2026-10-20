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

    def test_physical_component_reduction_uses_real_physical_bridges(self):
        counts = self.result["counts"]
        self.assertEqual(counts["before_routes_physical_components"]
                         - counts["after_routes_physical_components"],
                         counts["physical_components_joined"])
        self.assertEqual(counts["physical_components_joined"],
                         counts["physical_fragment_bridge_events"])
        self.assertGreater(counts["physical_components_joined"], 0)
        self.assertTrue(all(x["source_ids"]
                            for x in self.result["physical_fragment_bridge_events"]))

    def test_trace_is_inspectable_without_claiming_plan_geometry(self):
        a, b = "M-L2-EMMA-SUITE-001", "M-L2-EMMA-KITCHEN-001"
        chain = MOD.trace_between(self.result, a, b)
        self.assertEqual(chain["status"],
                         "QUALITATIVE_ASSOCIATION_CHAIN_NOT_TRAVEL_ITINERARY")
        self.assertEqual(chain["edge_chain"][0]["edge_id"], "MOAG-R05-001")
        self.assertIn("P-511", chain["edge_chain"][0]["source_ids"])
        self.assertFalse(chain["geometry_proven"])
        with self.assertRaisesRegex(ValueError, "UNKNOWN_TRACE_ENDPOINT"):
            MOD.trace_between(self.result, "NOT-AN-INDEX", b)

    def test_source_proven_r03_internal_links_are_not_ignored(self):
        r = self.result
        e = {x["id"]: x for x in r["typed_evidence_edges"]}
        for id in ["MOAG-R3-RC-009", "MOAG-R3-RC-010",
                   "MOAG-R3-RC-011", "MOAG-R3-RC-017",
                   "MOAG-R3-RC-019", "MOAG-R3-RC-023",
                   "MOAG-R3-RC-025"]:
            self.assertTrue(e[id]["connects_evidence_graph"], id)
            self.assertFalse(e[id]["metric_geometry_proven"])
        self.assertGreater(r["counts"]["r03_local_relation_component_reductions"], 0)

    def test_curated_stairs_and_workshop_relation_reduce_disconnected_islands(self):
        r = self.result
        curated = [x for x in r["typed_evidence_edges"]
                   if x["type"] == "R06_OBSERVATION_DERIVED_SPACE_LINK"]
        self.assertEqual(len(curated), 14)
        self.assertGreater(r["counts"]["r06_explicit_link_component_reductions"], 0)
        self.assertTrue(all(x["source_ids"] and not x["metric_geometry_proven"]
                            for x in curated))
        trace = MOD.trace_between(r, "M-L1-WASTE-001",
                                  "M-L1-WASTE-FURNACE-001")
        self.assertEqual(trace["status"],
                         "QUALITATIVE_ASSOCIATION_CHAIN_NOT_TRAVEL_ITINERARY")
        self.assertIn(trace["edge_chain"][0]["edge_id"],
                      {"S06-004", "MOAG-R3-RC-022"})

    def test_cargo_and_hangar_bridges_attach_without_invented_direct_doors(self):
        e = {x["id"]: x for x in self.result["typed_evidence_edges"]}
        expected = {
            "S06-007": ("M-L1-FH-001", "V-BOAT-L1-001", "P-364"),
            "S06-008": ("M-L1-FH-001", "M-L1-FH-LOCK-001", "P-385"),
            "S06-009": ("MOAG-G-0045", "MOAG-G-0046", "P-356"),
            "S06-010": ("MOAG-G-0046", "MOAG-G-0047", "P-357"),
            "S06-011": ("MOAG-G-0046", "MOAG-G-0048", "P-358"),
            "S06-012": ("M-L1-CG-001", "M-L1-CG-CTRL-001", "P-240"),
            "S06-013": ("MOAG-G-0089", "MOAG-G-0090", "P-190"),
            "S06-014": ("M-L3-LOG-001", "M-L3-CG-001", "P-200"),
        }
        for id, (a, b, source) in expected.items():
            self.assertEqual((e[id]["from"], e[id]["to"]), (a, b))
            self.assertIn(source, e[id]["source_ids"])
            self.assertFalse(e[id]["metric_geometry_proven"])
            self.assertFalse(e[id]["detail"]["not_a_direct_door"]
                             if id == "S06-008" else
                             not e[id]["detail"]["not_a_direct_door"])
        self.assertEqual(self.result["counts"]["physical_indices"], 197)

    def test_isolated_room_metric_excludes_ships_and_global_containers(self):
        counts = self.result["counts"]
        r = counts["isolated_candidates_by_role"]
        self.assertEqual(sum(r.values()), counts["isolated_physical_indices"])
        self.assertEqual(
            counts["isolated_fixed_room_corridor_door_or_technical_infrastructure"],
            r["FIXED_ROOM_CORRIDOR_DOOR_OR_TECHNICAL_INFRASTRUCTURE"])
        self.assertGreater(r["VEHICLE_OR_VEHICLE_CLASS_NOT_STATION_ROOM"], 0)
        self.assertGreater(r["GLOBAL_OR_HISTORICAL_CONTAINER_NOT_INDEPENDENT_ROOM"], 0)
        queue = self.result["unconnected_index_source_review_queue"]
        self.assertEqual(len(queue), counts["isolated_physical_indices"])
        self.assertTrue(all(x["spatial_inventory_role"] in r for x in queue))
        self.assertTrue(all(
            x["not_automatically_a_separate_room"]
            for x in queue if x["spatial_inventory_role"] !=
            "FIXED_ROOM_CORRIDOR_DOOR_OR_TECHNICAL_INFRASTRUCTURE"))

    def test_b3_foreign_station_hatches_are_quarantined_not_moag_access(self):
        s = self.result
        ids = set(s["quarantined_foreign_station_candidate_indices"])
        self.assertEqual(ids, {
            "M-L3-CABLE-HATCH-001", "M-L3-CABLE-HATCH-002",
            "M-L3-COMMS-HATCHES-001"})
        self.assertEqual(s["counts"]["unverified_moag_station_identity_indices"], 3)
        node = {x["id"]: x for x in s["nodes"]
                if x["layer"] == "PHYSICAL_INDEX"}
        self.assertTrue(all(not node[i]["moag_station_identity_verified"]
                            for i in ids))
        self.assertEqual(set(s["quarantined_foreign_station_source_observations"]),
                         {"P-671", "P-674"})
        bad = copy.deepcopy(
            json.loads((BASE / "synthesis/explicit_spatial_bridges_r06.json")
                       .read_text(encoding="utf-8")))
        bad["typed_edges"][-1]["source_ids"] = ["P-671"]
        with self.assertRaisesRegex(ValueError, "FOREIGN_STATION_SOURCE_NOT_MOAG_PROOF"):
            MOD.assemble(self.graph, self.fragments, self.routes, self.bounds,
                         explicit_bridges=bad)

    def test_concept_promotions_do_not_count_as_spatial_joins(self):
        r = self.result
        self.assertEqual(r["counts"]["reference_promotion_crosswalks"], 17)
        self.assertEqual(r["counts"]["promotions_needing_identity_review"], 5)
        self.assertTrue(all(x["not_a_physical_connection"]
            for x in r["reference_promotion_crosswalks_not_spatial_links"]))
        self.assertNotIn("M-L1-CG-001", {x["new_physical_id"]
            for x in r["reference_promotion_crosswalks_not_spatial_links"]})
        self.assertIn("M-L1-CG-001", {x["new_physical_id"]
            for x in r["promotion_identity_review_queue"]})

    def test_unsourced_or_cross_level_curated_stitch_is_rejected(self):
        base = json.loads((BASE / "synthesis/explicit_spatial_bridges_r06.json")
                          .read_text(encoding="utf-8"))
        invalid = copy.deepcopy(base)
        invalid["typed_edges"][0]["source_ids"] = ["UNREAD-PAGE"]
        with self.assertRaisesRegex(ValueError, "EXPLICIT_LINK_SOURCE_NOT_VERIFIED"):
            MOD.assemble(self.graph, self.fragments, self.routes,
                         self.bounds, explicit_bridges=invalid)
        invalid = copy.deepcopy(base)
        invalid["typed_edges"][0]["to"] = "M-L3-CG-001"
        with self.assertRaisesRegex(ValueError, "EXPLICIT_LINK_DISJOINT_LEVELS"):
            MOD.assemble(self.graph, self.fragments, self.routes,
                         self.bounds, explicit_bridges=invalid)
        invalid = copy.deepcopy(base)
        invalid["typed_edges"][0]["relation"] = "REMOTE_OPERATOR_IS_DIRECT_DOOR"
        with self.assertRaisesRegex(ValueError, "UNSUPPORTED_EXPLICIT_SPATIAL_LINK"):
            MOD.assemble(self.graph, self.fragments, self.routes,
                         self.bounds, explicit_bridges=invalid)

    def test_referential_context_overlay_not_confused_with_walkability(self):
        result = self.result
        counts = result["counts"]
        self.assertLess(counts["context_affiliation_components_with_physical_indices"],
                        counts["after_routes_physical_components"])
        self.assertGreater(counts["context_component_promotions_joined"], 0)
        context = result["referential_context_overlay"]
        self.assertTrue(context["not_a_travel_graph"])
        self.assertTrue(context["not_physical_room_unification"])
        self.assertTrue(all(not g["metric_layout_proven"]
                            for g in context["source_backed_affiliation_groups"]))
        strict = MOD.trace_between(result, "MOAG-G-0001", "M-STA-L1-001")
        # A referential promotion never fabricates a traversable connector:
        # the chain may exist through other evidence, but not via promotion.
        self.assertTrue(all(not step["edge_id"].startswith("PROMOTION::")
                            for step in strict["edge_chain"]))

    def test_stage_counters_monotonically_reduce_components(self):
        counts = self.result["counts"]
        stages = [counts[k] for k in (
            "after_r04_physical_components", "after_r03_physical_components",
            "after_r05_physical_components",
            "after_explicit_physical_components",
            "after_routes_physical_components")]
        self.assertEqual(stages, sorted(stages, reverse=True))
        self.assertEqual(stages[0] - stages[1],
                         counts["r03_local_relation_component_reductions"])
        self.assertEqual(stages[1] - stages[2],
                         counts["r05_typed_link_component_reductions"])
        self.assertEqual(stages[2] - stages[3],
                         counts["r06_explicit_link_component_reductions"])

    def test_isolated_index_research_queue_preserves_unconnected_status(self):
        result = self.result
        queue = result["unconnected_index_source_review_queue"]
        self.assertEqual(len(queue), result["counts"]["isolated_physical_indices"])
        self.assertEqual(len(queue), result["counts"]["unconnected_index_research_tasks"])
        self.assertEqual(len({q["physical_index_id"] for q in queue}), len(queue))
        self.assertTrue(all(q["status"] ==
                            "SOURCE_LOOKUP_REQUIRED_NOT_AUTO_CONNECTED" for q in queue))
        self.assertTrue(all(q["priority"].startswith(("P1_", "P2_", "P3_"))
                            for q in queue))
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

    def test_gaps_generate_research_frontiers_not_new_passages(self):
        r = self.result
        frontiers = r["research_frontiers_not_edges"]
        self.assertEqual(len(frontiers), r["counts"]["narrative_gaps"])
        self.assertTrue(all(x["source_pages"] and
                            x["status"] == "RESEARCH_FRONTIER_NOT_AN_ADDED_GRAPH_EDGE"
                            for x in frontiers))
        self.assertTrue(all(x["priority"].startswith(("P1_", "P2_"))
                            for x in frontiers))
        self.assertFalse(any(e["type"] == "RESEARCH_FRONTIER_NOT_AN_ADDED_GRAPH_EDGE"
                             for e in r["typed_evidence_edges"]))

    def test_multilevel_ventilation_alias_keeps_conflict_visible(self):
        items = self.result["route_location_review"]
        self.assertTrue(any(x["code"] == "MULTILEVEL_ALIAS_REVIEW"
                            and x["route_id"] == "RT-011"
                            and x["target"] == "MOAG-G-0016" for x in items))
        self.assertFalse(self.result["gates"]["metric_z_known"])

    def test_external_flight_or_other_craft_entry_not_station_passage(self):
        edge = {x["id"]: x for x in self.result["typed_evidence_edges"]}
        self.assertIn("STEP::RT-032::RT032-F::RT032-G", edge)
        self.assertIn("STEP::RT-049::RT049-N::RT049-O", edge)
        for key in ("STEP::RT-032::RT032-F::RT032-G",
                    "STEP::RT-049::RT049-N::RT049-O"):
            self.assertEqual(
                edge[key]["type"],
                "EXTERIOR_OR_OTHER_VEHICLE_EVENT_NOT_INTERNAL_PASSAGE")
            self.assertFalse(edge[key]["joins_components"])
            self.assertFalse(edge[key]["connects_evidence_graph"])
            self.assertTrue(edge[key]["source_ids"])

    def test_circular_control_room_reused_legacy_id_does_not_fuse_two_episodes(self):
        result = self.result
        visit = {x["id"]: x for x in result["typed_evidence_edges"]
                 if x["type"] == "ROUTE_VISITS_INDEX"}
        expected = {
            "VISIT::RT-015::RT015-J": "M-L1-CH-ST-001",
            "VISIT::RT-015::RT015-K": "M-L1-CH-GAL-001",
            "VISIT::RT-015::RT015-L": "M-L1-CH-CTRL-001",
            "VISIT::RT-024::RT024-G": "M-L1-AH-OLD-ST-001",
            "VISIT::RT-024::RT024-H": "M-L1-AH-OLD-CTRL-001",
            "VISIT::RT-024::RT024-I": "M-L1-AH-OLD-CTRL-001",
            "VISIT::RT-024::RT024-J": "M-L1-AH-OLD-ST-001",
        }
        for id, target in expected.items():
            self.assertIn(id, visit)
            self.assertEqual(visit[id]["to"], target, id)
        self.assertNotIn("VISIT::RT-023::RT023-A", visit)
        self.assertEqual(result["counts"]["route_context_disambiguations"], 7)
        self.assertEqual(result["counts"]["route_context_quarantines"], 1)
        self.assertEqual(
            result["route_context_quarantine_audit"][0]["source_observation_id"],
            "P-299")
        self.assertTrue(all(not item["not_a_metric_position"] is False
                            for item in result["route_context_disambiguation_audit"]))

    def test_circular_alias_repairs_must_have_same_page_review(self):
        corrections = copy.deepcopy(
            json.loads((BASE / "synthesis/route_context_corrections_r06.json")
                       .read_text(encoding="utf-8")))
        corrections["corrections"][0]["new_index_id"] = "M-L1-AH-OLD-ST-001"
        with self.assertRaisesRegex(ValueError, "ROUTE_CORRECTION_IDENTITY_NOT_SOURCE_BACKED"):
            MOD.assemble(self.graph, self.fragments, self.routes, self.bounds,
                         route_corrections=corrections)
        corrections = copy.deepcopy(
            json.loads((BASE / "synthesis/route_context_corrections_r06.json")
                       .read_text(encoding="utf-8")))
        corrections["corrections"][0]["source_page_id"] = "B1-110"
        with self.assertRaisesRegex(ValueError, "CONTEXT_CORRECTION_SOURCE_MISMATCH"):
            MOD.assemble(self.graph, self.fragments, self.routes, self.bounds,
                         route_corrections=corrections)
        corrections = copy.deepcopy(
            json.loads((BASE / "synthesis/route_context_corrections_r06.json")
                       .read_text(encoding="utf-8")))
        corrections["corrections"].append(copy.deepcopy(corrections["corrections"][0]))
        with self.assertRaisesRegex(ValueError, "UNKNOWN_OR_DUPLICATE_ROUTE_CONTEXT_CORRECTION"):
            MOD.assemble(self.graph, self.fragments, self.routes, self.bounds,
                         route_corrections=corrections)
        # Regression: removing a repair must fail rather than silently
        # relink the p110 dispatch stairs to the p76 stair.
        corrections = copy.deepcopy(
            json.loads((BASE / "synthesis/route_context_corrections_r06.json")
                       .read_text(encoding="utf-8")))
        corrections["corrections"] = [r for r in corrections["corrections"]
                                      if r["step_id"] != "RT024-G"]
        with self.assertRaisesRegex(ValueError, "AMBIGUOUS_ROUTE_ALIAS_REQUIRES_CONTEXT"):
            MOD.assemble(self.graph, self.fragments, self.routes, self.bounds,
                         route_corrections=corrections)

    def test_gap_frontiers_obey_corrected_scene_aliases(self):
        # A synthetic gap within the p110 route must use the p110
        # stair/control, never the unrelated p76 circular hall.
        routes = copy.deepcopy(self.routes)
        r = next(x for x in routes["routes"] if x["id"] == "RT-024")
        s = next(x for x in r["nodes"] if x["id"] == "RT024-H")
        s["movement_method"] = "NARRATIVE_GAP"
        updated = MOD.assemble(self.graph, self.fragments, routes, self.bounds)
        gaps = [x for x in updated["research_frontiers_not_edges"]
                if x["route_id"] == "RT-024"]
        self.assertTrue(gaps)
        self.assertTrue(all(x["endpoint_resolution"] ==
                            "SCENE_CORRECTED_LEVEL_CHECKED_NO_FOREIGN_STATION"
                            for x in gaps))
        self.assertTrue(all(x["left_indexed_witness"] not in
                            ("MOAG-G-0059", "MOAG-G-0060")
                            for x in gaps))
        self.assertTrue(all(x["right_indexed_witness"] not in
                            ("MOAG-G-0059", "MOAG-G-0060")
                            for x in gaps))
        self.assertTrue(any(x["left_indexed_witness"] ==
                            "M-L1-AH-OLD-ST-001" and
                            x["right_indexed_witness"] ==
                            "M-L1-AH-OLD-CTRL-001" for x in gaps))
        self.assertEqual(len(self.result["research_frontiers_not_edges"]), 18)

    def test_context_proximity_and_inferred_review_never_fuse_spaces(self):
        by = {x["id"]: x for x in self.result["typed_evidence_edges"]}
        for edge_id in ("MOAG-RG-E28", "MOAG-RG-E52",
                        "MOAG-RG-E39", "MOAG-RG-E51", "MOAG-RG-E55"):
            self.assertIn(edge_id, by)
            self.assertFalse(by[edge_id]["connects_evidence_graph"], edge_id)
            self.assertFalse(by[edge_id]["joins_components"], edge_id)
            self.assertEqual(by[edge_id]["type"],
                             "R04_PROVISIONAL_CONTEXT_NOT_CONNECTING")

    def test_incorrect_route_room_level_does_not_join_components(self):
        bad = copy.deepcopy(self.routes)
        item = bad["routes"][0]["nodes"][0]
        self.assertEqual(item["existing_graph_node"], "L2-GALLERY")
        item["global_level"] = 1
        checked = MOD.assemble(self.graph, self.fragments, bad, self.bounds)
        self.assertTrue(any(x["code"] == "ROUTE_LOCATION_LEVEL_CONFLICT"
                            and x["connection_accepted"] is False
                            for x in checked["route_location_review"]))
        self.assertNotIn("VISIT::RT-001::RT001-A",
                         {x["id"] for x in checked["typed_evidence_edges"]})
        self.assertFalse(checked["gates"]["metric_z_known"])

    def test_ventilation_contact_crosses_level_without_setting_deck(self):
        result = self.result
        review = [x for x in result["route_location_review"]
                  if x["code"] == "MULTILEVEL_ALIAS_REVIEW"]
        self.assertTrue(any(x["target"] == "MOAG-G-0016"
                            and x["route_id"] == "RT-011"
                            and x["observed_level"] == 2
                            and x["connection_accepted"]
                            for x in review))
        self.assertFalse(result["gates"]["metric_z_known"])
        self.assertEqual(result["counts"]["documented_multilevel_network_contacts"], 1)
        vent = next(x for x in review if x["route_id"] == "RT-011"
                    and x["target"] == "MOAG-G-0016")
        self.assertEqual(vent["semantic_review"],
                         "DOCUMENTED_LEVEL_CROSSING_NETWORK_CONTACT")
        self.assertEqual(vent["vertical_transition_witnesses"][0]["other_level"], 1)
        self.assertEqual(vent["vertical_transition_witnesses"][0]["source_page_id"],
                         "B1-057")

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
