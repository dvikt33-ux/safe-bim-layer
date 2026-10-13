"""TRC-SAD pure-offline geometry and actual existing APA graph contract tests."""
import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import trc_sad_plan as T

BINDINGS = {"1": {"nativeIndex": 0, "elevation": 0.0},
            "2": {"nativeIndex": 1, "elevation": 6.3},
            "3": {"nativeIndex": 2, "elevation": 12.6}}


class TrcSadPlanTests(unittest.TestCase):
    def setUp(self):
        self.spec = json.loads(T.DEFAULT_SPEC.read_text(encoding="utf8"))

    def test_conservation_of_four_slab_parts_and_atrium_hole(self):
        result = T.prepare(self.spec)
        self.assertEqual(result["floorSlabAreasSquareMeters"],
                         {"1": 25507.44, "2": 23602.32, "3": 23602.32})
        self.assertAlmostEqual(result["aboveGroundSlabAreaSquareMeters"], 72712.08)
        self.assertAlmostEqual(result["atriumVoidSquareMeters"], 1905.12)
        self.assertIsNone(result["basementAreaSquareMeters"])
        self.assertFalse(result["liveWriteAuthorized"])
        self.assertEqual(result["nativeWrites"], 0)
        self.assertIsNone(result["nativeGraph"])

    def test_real_existing_compiler_validates_native_dag_offline(self):
        result = T.prepare(self.spec, BINDINGS)
        self.assertEqual(result["status"], "NATIVE_DAG_PREVIEW_OFFLINE_NOT_AUTHORIZED")
        self.assertEqual(result["nativeGraphStatus"], "SCHEMA_VALID_NOT_EXECUTION_AUTHORIZED")
        commands = [op["command"] for op in result["nativeGraph"]["operations"]]
        self.assertEqual(commands.count("CreateWalls"), 24)
        self.assertEqual(commands.count("CreateSlabs"), 9)
        self.assertEqual(len(result["executionOrder"]), 33)
        self.assertFalse(result["plnChanged"])
        self.assertEqual(result["nativeWrites"], 0)

    def test_upper_floors_do_not_have_slabs_over_atrium(self):
        result = T.prepare(self.spec, BINDINGS)
        slabs = [op for op in result["nativeGraph"]["operations"]
                 if op["command"] == "CreateSlabs"]
        self.assertEqual(sum("s1-slab" in s["id"] for s in slabs), 1)
        self.assertEqual(sum("s2-slab" in s["id"] for s in slabs), 4)
        self.assertEqual(sum("s3-slab" in s["id"] for s in slabs), 4)
        for s in slabs:
            self.assertEqual(s["params"]["slabsData"][0]["thickness"], .22)

    def test_no_fake_upper_story_egress_doors(self):
        result = T.prepare(self.spec, BINDINGS)
        commands = {op["command"] for op in result["nativeGraph"]["operations"]}
        self.assertEqual(commands, {"CreateWalls", "CreateSlabs"})
        self.assertNotIn("CreateDoors", commands)

    def test_inconsistent_geometry_and_story_data_fail_closed(self):
        bad = copy.deepcopy(self.spec)
        bad["shell"][0][0] += 1
        with self.assertRaisesRegex(ValueError, "UNAPPROVED_SHELL"):
            T.prepare(bad)
        bad = copy.deepcopy(self.spec)
        bad["floors"][2]["elevation"] = 6.1
        with self.assertRaisesRegex(ValueError, "STORY_LEVEL"):
            T.prepare(bad)
        bad = copy.deepcopy(BINDINGS)
        bad["2"]["nativeIndex"] = bad["1"]["nativeIndex"]
        with self.assertRaisesRegex(ValueError, "DUPLICATE_NATIVE_STORY"):
            T.prepare(self.spec, bad)
        with self.assertRaisesRegex(ValueError, "EXACT_NATIVE_STORY"):
            T.prepare(self.spec, {"1": BINDINGS["1"]})

    def test_areas_come_only_from_rectangles_not_caption(self):
        preview = T.prepare(self.spec)
        items = {r["id"]: r for r in preview["programReservations"]}
        self.assertAlmostEqual(items["cinema"]["reservedAreaSquareMeters"], 2756)
        self.assertAlmostEqual(items["games"]["reservedAreaSquareMeters"], 1802)
        self.assertEqual(items["cinema"]["status"],
                         "UNVERIFIED_PROGRAM_RESERVATION_NOT_NATIVE_ZONE")
        self.assertEqual(sum(r["id"] == "food_rear" for r in items.values()), 1)

    def test_inset_shell_reference_axes_stay_inside_building(self):
        shell = [tuple(p) for p in self.spec["shell"]]
        axes = T.inset_axes(shell, .15)
        self.assertEqual(len(axes), 6)
        self.assertGreater(min(x for x, y in axes), 0)
        self.assertGreater(min(y for x, y in axes), 0)
        self.assertLess(max(x for x, y in axes), 184.8)
        self.assertLess(max(y for x, y in axes), 142.8)


if __name__ == "__main__":
    unittest.main()
