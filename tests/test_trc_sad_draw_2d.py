"""Pure 2D plan recipe contract tests; never call local Archicad."""
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import trc_sad_draw_2d as T


class TwoDTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = json.loads(T.DATA.read_text(encoding="utf8"))

    def test_2d_commands_only_and_real_native_floor_indexes(self):
        for i in (1, 2, 3):
            p = T.plan_floor(self.spec, str(i))
            self.assertEqual(p["nativeFloorIndex"], i - 1)
            self.assertEqual([cmd for cmd, params in p["commands"]],
                             ["CreateHatches", "CreatePolylines", "CreateTexts"])
            self.assertGreater(p["counts"]["polylines"], 5)
            self.assertTrue(all(row.get("floorInd") == i - 1
                                for row in p["commands"][0][1]["hatchesData"]))
            self.assertTrue(all(row.get("floorIndex") == i - 1
                                for row in p["commands"][2][1]["textsData"]))

    def test_movie_is_front_60_percent_bowling_is_rear_40(self):
        p = {r["id"]: r for r in self.spec["program"]}
        movie, game = p["cinema"]["rect"], p["games"]["rect"]
        self.assertEqual(movie[1], 33)
        self.assertEqual(movie[3], game[1])
        self.assertEqual(game[3], 119)
        self.assertAlmostEqual(T._area(movie) / (T._area(movie) + T._area(game)), .6)

    def test_rear_food_area_hatch_clips_central_lift_and_stair(self):
        food = next(z for z in self.spec["program"] if z["id"] == "food_rear")
        rects = T._nonoverlap(food["rect"],
                              [[76, 96, 88, 112], [100, 96, 112, 112]])
        self.assertAlmostEqual(sum(T._area(r) for r in rects), 1219 - 384)
        self.assertEqual(T._area(food["rect"]), 1219)

    def test_no_internal_model_mutation_commands(self):
        plan = T.plan_floor(self.spec, "3")
        text = " ".join(str(p) for p in plan["commands"])
        for command in ("CreateWalls", "CreateSlabs", "SetStories",
                        "SaveProject", "CreateColumns", "CreateMorphs"):
            self.assertNotIn(command, text)

    def test_live_guard_exact_port_project_stories(self):
        replies = {
            "GetProjectInfo": {"projectName": T.PROJECT_NAME,
                               "projectPath": T.PROJECT_PATH,
                               "isUntitled": False, "isTeamwork": False},
            "GetAddOnVersion": {"version": "1.5.10"},
            "GetStories": {"stories": [
                {"index": i, "level": v[0], "height": v[1]}
                for i, v in T.EXPECTED_STORIES.items()]},
        }
        result = T.guarded_live(lambda c, p: replies[c])
        self.assertEqual(result["projectName"], T.PROJECT_NAME)
        replies["GetStories"]["stories"][1]["level"] = 6.3
        with self.assertRaisesRegex(ValueError, "STORY_STRUCTURE_CHANGED"):
            T.guarded_live(lambda c, p: replies[c])

    def test_native_creation_response_fails_on_partial_error(self):
        ok = {"elements": [{"elementId": {"guid": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"}}]}
        self.assertEqual(len(T.element_ids(ok, 1)), 1)
        with self.assertRaises(ValueError):
            T.element_ids({"elements": []}, 1)
        with self.assertRaises(ValueError):
            T.element_ids({"elements": [{"error": "bad"}]}, 1)


if __name__ == "__main__":
    unittest.main()
