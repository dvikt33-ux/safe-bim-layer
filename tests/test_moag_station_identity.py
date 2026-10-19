"""MOAG and 'Млечный Путь' are one station through different story periods."""
import json
from pathlib import Path
import unittest

BASE=Path(__file__).resolve().parents[1]/"docs/research/apa-results/moag"
class StationIdentityTests(unittest.TestCase):
    def test_single_physical_entity_two_historical_names(self):
        d=json.loads((BASE/"v2/station_identity.json").read_text(encoding="utf-8"))
        self.assertEqual(d["canonical_station_id"],"MOAG")
        self.assertTrue({"Млечный Путь","МОАГ"} <= {x["value"] for x in d["names"]})
        self.assertEqual({x["canonical_station_id"] for x in d["names"]},{"MOAG"})
        self.assertEqual({x["station_id"] for x in d["modeling"]["phases"]},{"MOAG"})
        self.assertTrue(d["modeling"]["shared_space_graph"])
        self.assertFalse(d["modeling"]["name_change_must_not_create_new_floor_graph"] is False)
    def test_no_merge_with_other_station(self):
        d=json.loads((BASE/"v2/station_identity.json").read_text(encoding="utf-8"))
        self.assertIn("THIRD_STATION_NOT_MOAG",{x["station_id"] for x in d["separate_entities"]})
        self.assertEqual(d["claim_provenance"]["validation_status"],"DIRECT_TEXT_CONFIRMED")
        self.assertGreaterEqual(len(d["claim_provenance"]["primary_sources"]),3)
        self.assertIn("NAME_EPOCH",d["chronology_note"])
        self.assertIn("CONTROL_EPOCH",d["chronology_note"])
    def test_graph_points_to_identity_and_retains_model_ids(self):
        d=json.loads((BASE/"v1/evidence_graph.json").read_text(encoding="utf-8"))
        self.assertTrue(d["station_identity"]["do_not_split_by_name"])
        self.assertTrue(d["station_identity"]["do_not_merge_other_stations"])
        self.assertEqual(d["station_identity"]["canonical_station_id"],"MOAG")

if __name__=="__main__":
    unittest.main()
