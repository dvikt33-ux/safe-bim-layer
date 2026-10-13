"""Isolated planning grid: dimensions from geometry, 2D only, fail closed."""
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import trc_sad_grid_2d as G


class GridTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = json.loads(G.PLAN.DEFAULT_SPEC.read_text(encoding="utf-8"))

    def test_8400_modules_close_exactly_into_project_size(self):
        g = G.geometry(self.spec)
        self.assertEqual((len(g["x"]), len(g["y"])), (23, 18))
        self.assertEqual(g["x"][-1], 184.8)
        self.assertEqual(g["y"][-1], 142.8)
        self.assertEqual((g["totalWidthMm"], g["totalDepthMm"]), (184800, 142800))
        self.assertEqual(g["primaryModuleMm"], 16800)
        self.assertEqual(g["subModuleMm"], 8400)

    def test_russian_axis_labels_are_unique_and_valid_count(self):
        self.assertEqual(len(G.Y_LABELS), 18)
        self.assertEqual(len(set(G.Y_LABELS)), 18)
        self.assertEqual(G.Y_LABELS[0], "А")
        self.assertEqual(G.Y_LABELS[-1], "Ф")

    def test_native_only_2d_commands_each_floor(self):
        for i in (1, 2, 3):
            plan = G.build_floor(self.spec, i)
            self.assertEqual(plan["nativeFloorIndex"], i-1)
            self.assertEqual([c for c, p in plan["commands"]],
                             ["CreatePolylines", "CreateCircles", "CreateTexts"])
            self.assertEqual(plan["native3DOperations"], 0)
            self.assertGreater(plan["counts"]["polylines"], 75)
            self.assertEqual(plan["counts"]["circles"], 82)
            self.assertGreater(plan["counts"]["texts"], 85)
            for p in plan["commands"][0][1]["polylinesData"]:
                self.assertEqual(p["floorInd"], i-1)
            for p in plan["commands"][2][1]["textsData"]:
                self.assertEqual(p["floorIndex"], i-1)
                self.assertEqual(p["coordinate"]["z"], (0., 3., 6.)[i-1])

    def test_span_and_total_labels_are_not_guessed(self):
        plan = G.build_floor(self.spec, 1)
        labels = [v["text"] for v in plan["commands"][2][1]["textsData"]]
        self.assertEqual(labels.count("8400"), 39)
        self.assertIn("184800", labels)
        self.assertIn("142800", labels)
        self.assertTrue(any("АТРИУМ: 42000 x 50400 мм" in s for s in labels))
        self.assertEqual(G.geometry(self.spec)["atriumBounds"],
                         [71.4, 37.8, 113.4, 88.2])

    def test_grid_is_not_structural_columns_or_fake_3d(self):
        result = G.build_floor(self.spec, 2)
        cmds = [c for c, p in result["commands"]]
        self.assertNotIn("CreateWalls", cmds)
        self.assertNotIn("CreateColumns", cmds)
        self.assertNotIn("SetStories", cmds)
        self.assertNotIn("SaveProject", cmds)

    def test_reject_unapproved_floor(self):
        with self.assertRaisesRegex(ValueError, "ONLY_EXISTING_FLOORS"):
            G.build_floor(self.spec, 0)


if __name__ == "__main__":
    unittest.main()
