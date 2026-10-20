"""Negative evidence: MOAG geometry cannot inherit another station's rooms."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
REVIEW = (ROOT / "docs/research/apa-results/moag/v2/reviews/"
          "B3_p61_65_context_screening_r06_20261020.json")


class MOAGOtherStationScreening(unittest.TestCase):
    def test_other_station_never_promoted(self):
        data = json.loads(REVIEW.read_text(encoding="utf-8"))
        self.assertEqual(
            [r["page_id"] for r in data["pages"]],
            ["B3-061", "B3-062", "B3-063", "B3-064", "B3-065"])
        self.assertEqual(len({r["page_id"] for r in data["pages"]}), 5)
        self.assertTrue(all(x["read"] == "FULL" for x in data["pages"]))
        self.assertTrue(all(not x["moag_physical_evidence"] for x in data["pages"]))
        self.assertEqual(data["moag_space_edges_added"], 0)
        self.assertEqual(data["moag_room_nodes_added"], 0)
        self.assertEqual(data["moag_global_story_additions"], 0)
        self.assertEqual(data["moag_metric_dimensions_added"], 0)
        self.assertFalse(data["geometry_approved"])

    def test_laser_gun_claim_is_character_hypothesis_only(self):
        data = json.loads(REVIEW.read_text(encoding="utf-8"))
        page = next(x for x in data["pages"] if x["page_id"] == "B3-062")
        self.assertEqual(len(page["noncanon_hypotheses"]), 1)
        assumption = page["noncanon_hypotheses"][0]
        self.assertEqual(assumption["mode"], "CHARACTER_SPECULATION")
        self.assertFalse(assumption["adopted_as_moag_equipment"])
        self.assertFalse(assumption["adopted_as_geometry"])


if __name__ == "__main__":
    unittest.main()
