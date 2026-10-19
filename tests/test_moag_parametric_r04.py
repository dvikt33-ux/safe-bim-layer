"""Source-integrated, fail-closed tests for R04 parameter changes, NO Archicad writes."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("apa_moag_r04_eval",ROOT/"tools/moag_topology/parametric_evaluator_r04.py")
MOD=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)
P=ROOT/"docs/research/apa-results/moag/synthesis"

class MOAGParametricR04(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph=json.loads((P/"full_indexed_parametric_graph_r04.json").read_text(encoding="utf-8"))
        cls.demo=json.loads((P/"demo_override_r04_NONCANON.json").read_text(encoding="utf-8"))

    def test_full_source_inventory(self):
        g=self.graph
        self.assertEqual(len(g["indexed_source_entities"]),117)
        self.assertEqual(len(g["indexed_r03_entities"]),37)
        self.assertEqual(len(g["source_relationships"]),166)
        self.assertEqual(len(g["derived_r03_relationships"]),27)
        self.assertEqual(len(g["vertical_strata"]),6)
        self.assertEqual(len(g["movements"]),378)
        self.assertEqual(len(g["movement_sequence"]),326)
        self.assertEqual(len(g["observations"]),690)
        allids=[n["id"] for n in g["indexed_source_entities"]+g["indexed_r03_entities"]]
        self.assertEqual(len(allids),len(set(allids)))
        endpoints={x["id"] for x in g["indexed_source_entities"]+g["indexed_r03_entities"]}
        for e in g["source_relationships"]+g["derived_r03_relationships"]+g["vertical_strata"]:
            self.assertIn(e["from"],endpoints)
            self.assertIn(e["to"],endpoints)
        self.assertFalse(g["gates"]["archicad_write"])
        self.assertFalse(g["gates"]["metric_geometry_solved"])

    def test_unknown_metrics_are_never_silently_filled(self):
        r=MOD.evaluate(self.graph,{})
        self.assertEqual(r["counts"]["failed"],0)
        self.assertGreater(r["counts"]["unevaluable"],8)
        self.assertIsNone(r["parameter_values"]["cargo_cruiser_length_m"])
        self.assertIsNone(r["parameter_values"]["lower_level_diameter_m"])
        self.assertEqual(r["parameter_values"]["human_reference_height_m"],1.60)

    def test_demo_is_noncanonical_and_operational(self):
        result=MOD.evaluate(self.graph,self.demo)
        self.assertEqual(result["counts"]["failed"],0)
        self.assertEqual(result["counts"]["unevaluable"],0)
        self.assertEqual(result["status"],"PARTIAL_NO_APPROVED_GEOMETRY")
        self.assertFalse(result["gates"]["geometry_approved"])

    def test_shrinking_cargo_hangar_causes_constraint_failure(self):
        demo=dict(self.demo)
        demo["lower_old_cargo_hangar_clear_width_m"]=30
        result=MOD.evaluate(self.graph,demo)
        self.assertGreater(result["counts"]["failed"],0)
        bad={x["id"] for x in result["rules"] if x["status"]=="FAIL"}
        self.assertIn("R011",bad)

    def test_upper_cruiser_berth_and_local_time_guards(self):
        demo=dict(self.demo)
        self.assertEqual(MOD.evaluate(self.graph,demo)["counts"]["failed"],0)
        demo["upper_cargo_hangar_clear_width_m"]=10
        failed={x["id"] for x in MOD.evaluate(self.graph,demo)["rules"] if x["status"]=="FAIL"}
        self.assertIn("R015",failed)
        demo=dict(self.demo)
        demo["children_gallery_above_plaza_m"]=20
        failed={x["id"] for x in MOD.evaluate(self.graph,demo)["rules"] if x["status"]=="FAIL"}
        self.assertIn("R019",failed)
        demo=dict(self.demo)
        demo["children_to_upper_lift_vertical_delta_m"]=200
        failed={x["id"] for x in MOD.evaluate(self.graph,demo)["rules"] if x["status"]=="FAIL"}
        self.assertIn("R020",failed)
        with self.assertRaisesRegex(ValueError,"CRUISER_COUNT_POSITIVE_INTEGER_REQUIRED"):
            MOD.evaluate(self.graph,{"upper_cruisers_simultaneous_in_hangar_count":1.5})

    def test_size_order_violation_fails(self):
        demo=dict(self.demo)
        demo["upper_level_diameter_m"]=2000
        bad={x["id"] for x in MOD.evaluate(self.graph,demo)["rules"] if x["status"]=="FAIL"}
        self.assertIn("R001",bad)
        self.assertIn("R003",bad)

    def test_cannot_edit_text_measure_or_unknown_parameter(self):
        with self.assertRaisesRegex(ValueError,"SOURCE_OBSERVATION_READONLY"):
            MOD.evaluate(self.graph,{"energy_gallery_visible_downward_depth_m":23})
        with self.assertRaisesRegex(ValueError,"UNKNOWN_PARAMETER_OVERRIDE"):
            MOD.evaluate(self.graph,{"extra_guessed_hangar_m":1234})
        with self.assertRaisesRegex(ValueError,"CRUISER_COUNT_POSITIVE_INTEGER_REQUIRED"):
            MOD.evaluate(self.graph,{"cargo_cruisers_simultaneous_in_hangar":2.5})

    def test_stable_indexed_room_resizing_feeds_shared_constraints(self):
        editable=dict(self.demo)
        del editable["fighter_hangar_1_clear_width_m"]
        overrides={"M-L1-FH-001":{"width_m":1}}
        result=MOD.evaluate(self.graph,editable,entity_overrides=overrides)
        self.assertEqual(result["parameter_values"]["fighter_hangar_1_clear_width_m"],1.0)
        self.assertIn("R004",{x["id"] for x in result["rules"] if x["status"]=="FAIL"})
        self.assertEqual(result["entity_geometry_overrides"],overrides)
        with self.assertRaisesRegex(ValueError,"CONFLICTING_NAMED_AND_INDEXED_PARAMETER"):
            MOD.evaluate(self.graph,self.demo,entity_overrides=overrides)
        with self.assertRaisesRegex(ValueError,"UNRECOGNIZED_PHYSICAL_INDEX"):
            MOD.evaluate(self.graph,{},entity_overrides={"MOAG-G-9999":{"width_m":10}})
        source_only=MOD.evaluate(self.graph,{},entity_overrides={"MOAG-G-0001":{"diameter_m":20}})
        self.assertEqual(source_only["unbound_indexed_geometry_ids"],["MOAG-G-0001"])
        self.assertFalse(source_only["gates"]["geometry_approved"])

    def test_apa_read_only_geometry_helpers(self):
        plan=[{"id":"hangar","rectangle":{"xMin":0,"xMax":50,"yMin":0,"yMax":50}},
              {"id":"upper_room","rectangle":{"xMin":10,"xMax":20,"yMin":10,"yMax":20}}]
        result=MOD.evaluate(self.graph,{},plan)
        self.assertEqual(result["apa_geometric_readonly_check"]["status"],"EXISTING_APA_SPATIAL_PRIMITIVES_USED_READ_ONLY")
        self.assertEqual(len(result["apa_geometric_readonly_check"]["overlap_candidates"]),1)
        self.assertTrue(result["apa_geometric_readonly_check"]["overlap_candidates"][0]["a_contains_b"])

if __name__=="__main__":
    unittest.main()
