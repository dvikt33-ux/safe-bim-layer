"""Offline architectural min/max area, clear volume and placement test suite."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"docs/research/apa-results/moag/synthesis"
SPEC=importlib.util.spec_from_file_location("moag_area_volume_solver",
    ROOT/"tools/moag_topology/area_volume_solver_r05.py")
MOD=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)

class AreaVolumeR05(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bounds=json.loads((BASE/"area_volume_bounds_r05.json").read_text(encoding="utf-8"))
        cls.graph=json.loads((BASE/"full_indexed_parametric_graph_r04.json").read_text(encoding="utf-8"))
        cls.demo=json.loads((BASE/"demo_override_r04_NONCANON.json").read_text(encoding="utf-8"))
        cls.fragment=json.loads((BASE/"progressive_fragments_r05.json").read_text(encoding="utf-8"))

    def test_every_index_either_has_interval_or_declared_not_area(self):
        expected={x["id"] for x in self.graph["indexed_source_entities"]+
                  self.graph["indexed_r03_entities"]+self.fragment["physical_entities"]}
        actual={x["id"] for x in self.bounds["profiles"]}
        self.assertEqual(len(expected),197)
        self.assertEqual(actual,expected)
        x=MOD.solve(self.bounds,self.graph)
        self.assertEqual(x["counts"]["indexed"],197)
        self.assertEqual(x["counts"]["with_area"],157)
        self.assertEqual(x["counts"]["not_area"],40)
        self.assertEqual(x["counts"]["fails"],0)
        self.assertFalse(x["gates"]["all_areas_book_facts"])
        self.assertFalse(x["gates"]["geometry_unique"])
        self.assertEqual(x["per_index"]["M-L1-STARSHIP-OUTER-GATE-001"]["status"],
                         "NOT_AREA_BEARING")

    def test_editable_project_ranges_do_not_approve_dimensions(self):
        r=MOD.solve(self.bounds,self.graph)
        self.assertIsNone(r["per_index"]["M-STA-L1-001"]["chosen_area_m2"])
        self.assertGreater(r["per_index"]["M-L1-CG-001"]["max_area_m2"],
                           r["per_index"]["M-L1-CG-001"]["min_area_m2"])
        self.assertEqual(r["per_index"]["M-STA-CORE-001"]["role"],"VERTICAL_CORE_SECTION")
        self.assertFalse(r["gates"]["ship_turning_verified"])

    def test_local_mezzanine_floor_area_is_not_new_global_deck(self):
        r=MOD.solve(self.bounds,self.graph)
        ring=r["per_index"]["M-L2-RES-001"]
        self.assertEqual(ring["local_story_factor_range"],[1,2])
        self.assertEqual(ring["usable_floor_area_range_m2"][0],ring["min_area_m2"])
        self.assertEqual(ring["usable_floor_area_range_m2"][1],ring["max_area_m2"]*2)
        hall=r["per_index"]["M-L1-CH-001"]
        self.assertEqual(hall["local_story_factor_range"],[1,1.25])
        self.assertIsNone(r["per_index"]["M-STA-L1-001"]["usable_floor_area_range_m2"])
        self.assertIsNone(r["per_index"]["M-STA-CORE-001"]["usable_floor_area_range_m2"])
        self.assertFalse(r["gates"]["geometry_unique"])

    def test_r04_shared_parameters_feed_levels_hangars_and_volume(self):
        r=MOD.solve(self.bounds,self.graph,self.demo)
        self.assertEqual(r["counts"]["fails"],0,
                         [x for x in r["checks"] if x["status"]=="FAIL"])
        self.assertAlmostEqual(r["per_index"]["M-L1-CG-001"]["chosen_area_m2"],620*290)
        self.assertAlmostEqual(r["per_index"]["M-L3-CG-001"]["chosen_area_m2"],420*200)
        self.assertAlmostEqual(r["per_index"]["M-L1-CG-001"]["chosen_height_m"],120)
        self.assertEqual(r["counts"]["unresolved_relative_level_area_orders"],2)
        self.assertEqual(r["status"],"INTERVALS_CONSISTENT_NOT_GEOMETRY_PROVEN")

    def test_standing_area_minimum_tightens_after_ship_growth(self):
        too_large=dict(self.demo)
        too_large["cargo_cruiser_width_m"]=430
        r=MOD.solve(self.bounds,self.graph,too_large)
        failures={x["id"] for x in r["checks"] if x["status"]=="FAIL"}
        self.assertIn("BERTH_MIN_M-L1-CG-001",failures)
        self.assertIn("AFTER_TIGHTENING_M-L1-CG-001",failures)

    def test_room_sum_cannot_exceed_suite(self):
        changes={"M-L2-EMMA-SUITE-001":{"max_area_m2":40}}
        r=MOD.solve(self.bounds,self.graph,area_overrides=changes)
        fails={x["id"] for x in r["checks"] if x["status"]=="FAIL"}
        self.assertIn("DISJOINT_ROOMS_M-L2-EMMA-SUITE-001",fails)
        self.assertIn("TIGHTENED_INTERVAL_M-L2-EMMA-SUITE-001",fails)

    def test_area_rank_secondary_to_known_level_and_capacity(self):
        scenarios=[
            {"id":"wrong_level","assignments":{"M-L1-CG-001":"M-STA-L3-001"}},
            {"id":"too_small","assignments":{"M-L1-CG-001":"M-L2-EMMA-SUITE-001"}},
            {"id":"valid_area_not_geometry","assignments":{"M-L1-CG-001":"M-STA-L1-001"}},
        ]
        r=MOD.solve(self.bounds,self.graph,self.demo,candidates=scenarios)
        by={x["id"]:x for x in r["placement_variant_comparisons"]}
        self.assertFalse(by["wrong_level"]["admissible_by_area"])
        self.assertFalse(by["too_small"]["admissible_by_area"])
        self.assertTrue(by["valid_area_not_geometry"]["admissible_by_area"])
        self.assertFalse(by["valid_area_not_geometry"]["geometry_proven"])

    def test_major_spaces_raise_level_minimum_without_fabricating_area(self):
        r=MOD.solve(self.bounds,self.graph,area_overrides={
            "M-STA-L1-001":{"min_area_m2":1000}})
        self.assertEqual(r["counts"]["fails"],0)
        lower=r["per_index"]["M-STA-L1-001"]
        self.assertGreater(lower["min_area_m2"],1000)
        lower_budget=next(x for x in r["level_allocation_budgets"]
                          if x["id"]=="L1-DISJOINT-01")
        self.assertGreaterEqual(lower["min_area_m2"],
                                lower_budget["min_member_footprints_m2"])
        self.assertIsNone(lower["chosen_area_m2"])
        self.assertFalse(r["gates"]["geometry_unique"])

    def test_multiple_individually_fitting_halls_can_overfill_one_level(self):
        demo=dict(self.demo)
        demo["lower_level_diameter_m"]=700
        demo["children_level_diameter_m"]=600
        # Upper remains 530: global order is valid.
        r=MOD.solve(self.bounds,self.graph,demo,area_overrides={
            "M-L1-WASTE-001":{"chosen_area_m2":200000}})
        checks={x["id"]:x for x in r["checks"]}
        self.assertEqual(checks["BLOCK_FOOTPRINT_ORDER_1"]["status"],"PASS")
        self.assertEqual(checks["BLOCK_FOOTPRINT_ORDER_2"]["status"],"PASS")
        self.assertEqual(checks["LEVEL_FOOTPRINT_BUDGET_L1-DISJOINT-01"]["status"],"FAIL")
        self.assertEqual(checks["LEVEL_VOLUME_BUDGET_L1-DISJOINT-01"]["status"],"PASS")

    def test_upper_hall_can_fit_by_area_but_break_vertical_volume_budget(self):
        r=MOD.solve(self.bounds,self.graph,self.demo,area_overrides={
            "M-L3-PRODUCTION-ROUND-001":{"chosen_area_m2":85000,"chosen_height_m":170}})
        checks={x["id"]:x for x in r["checks"]}
        self.assertEqual(checks["LEVEL_FOOTPRINT_BUDGET_L3-DISJOINT-01"]["status"],"PASS")
        self.assertEqual(checks["LEVEL_VOLUME_BUDGET_L3-DISJOINT-01"]["status"],"FAIL")
        self.assertFalse(r["gates"]["geometry_unique"])

    def test_editing_single_space_and_invalid_overrides(self):
        r=MOD.solve(self.bounds,self.graph,area_overrides={
            "M-L2-DINING-001":{"min_area_m2":45,"max_area_m2":500,
                               "chosen_area_m2":80}})
        self.assertEqual(r["counts"]["fails"],0)
        self.assertEqual(r["per_index"]["M-L2-DINING-001"]["chosen_area_m2"],80)
        with self.assertRaisesRegex(ValueError,"NON_AREA_ENTITY_CANNOT_HAVE_AREA"):
            MOD.solve(self.bounds,self.graph,area_overrides={
                "M-L2-LIB-GLASS-DOOR-001":{"chosen_area_m2":2}})
        with self.assertRaisesRegex(ValueError,"CONFLICT_WITH_SHARED_APA_ENVELOPE"):
            MOD.solve(self.bounds,self.graph,self.demo,area_overrides={
                "M-L1-CG-001":{"chosen_area_m2":12}})
        with self.assertRaisesRegex(ValueError,"UNKNOWN_ENTITY_OVERRIDE"):
            MOD.solve(self.bounds,self.graph,area_overrides={
                "MISSING_ROOM":{"max_area_m2":500}})

    def test_oversized_global_envelope_and_height_bounds_rejected(self):
        changes=dict(self.demo)
        changes["upper_level_diameter_m"]=3000
        failed={x["id"] for x in MOD.solve(self.bounds,self.graph,changes)["checks"]
                if x["status"]=="FAIL"}
        self.assertIn("CHOSEN_AREA_M-STA-L3-001",failed)
        self.assertIn("BLOCK_FOOTPRINT_ORDER_2",failed)

if __name__=="__main__":
    unittest.main()
