"""Offline dependency graph tests; never contact a live Archicad process."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "scripts" / "archicad_bim_graph.py"
module_spec = importlib.util.spec_from_file_location("archicad_bim_graph", FILE)
graph = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(graph)


def wall():
    return {"begCoordinate": {"x": 10, "y": 10},
            "endCoordinate": {"x": 14, "y": 10}, "floorIndex": 0,
            "height": 3, "thickness": 0.2, "structureType": "Basic"}


def slab():
    return {"level": 0, "floorIndex": 0, "thickness": 0.2,
            "polygonCoordinates": [
                {"x": 0, "y": 0}, {"x": 5, "y": 0},
                {"x": 5, "y": 5}, {"x": 0, "y": 5}]}


def step(id, command, params, after=None):
    obj = {"id": id, "command": command, "params": params}
    if after is not None:
        obj["after"] = after
    return obj


class BIMGraphTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = graph.CONTRACTS.load_catalog(
            ROOT / "tapir-1.5.8.json")

    def compile(self, *operations, runtime_version=None):
        return graph.compile_graph(
            self.catalog, {"operations": list(operations)}, runtime_version)

    def test_valid_dependent_wall_and_window(self):
        result = self.compile(
            step("window", "CreateWindows", {
                "windowsData": [{
                    "ownerWallId": {"guid": {"$createdGuid": "wall"}},
                    "centerOffset": 1.5, "width": 1.2, "height": 1.5,
                }]
            }),
            step("wall", "CreateWalls", {"wallsData": [wall()]}),
        )
        self.assertEqual(result["status"], "PLAN_VALIDATED_OFFLINE")
        self.assertEqual(result["executionOrder"], ["wall", "window"])
        self.assertEqual(result["operations"][0]["dependsOn"], ["wall"])
        self.assertEqual(result["operations"][0]["references"][0]["producerId"], "wall")
        self.assertNotIn(graph._DUMMY_GUID, str(result))
        self.assertFalse(result["executionSupported"])
        self.assertFalse(result["jobPublished"])

    def test_multiple_command_families_in_one_graph(self):
        result = self.compile(
            step("wall", "CreateWalls", {"wallsData": [wall()]}),
            step("slab", "CreateSlabs", {"slabsData": [slab()]}),
            step("window", "CreateWindows", {
                "windowsData": [{
                    "ownerWallId": {"guid": {"$createdGuid": "wall"}},
                    "centerOffset": 1.5
                }]
            }, after=["slab"]),
            step("stories", "GetStories", {}),
        )
        self.assertEqual(result["status"], "PLAN_VALIDATED_OFFLINE")
        self.assertEqual(result["operationCount"], 4)
        self.assertLess(result["executionOrder"].index("wall"),
                        result["executionOrder"].index("window"))
        self.assertLess(result["executionOrder"].index("slab"),
                        result["executionOrder"].index("window"))

    def test_wrong_host_element_type_blocked(self):
        result = self.compile(
            step("slab", "CreateSlabs", {"slabsData": [slab()]}),
            step("window", "CreateWindows", {
                "windowsData": [{"ownerWallId": {"guid": {"$createdGuid": "slab"}},
                                 "centerOffset": 1.5}]
            }),
        )
        self.assertEqual(result["status"], "INVALID")
        self.assertIn("host must be Wall", str(result["operations"][1]["errors"]))

    def test_get_stories_not_a_guid_producer(self):
        result = self.compile(
            step("read", "GetStories", {}),
            step("window", "CreateWindows", {
                "windowsData": [{"ownerWallId": {"guid": {"$createdGuid": "read"}},
                                 "centerOffset": 1.5}]
            }),
        )
        self.assertEqual(result["status"], "INVALID")

    def test_cycle_detected_and_execution_order_suppressed(self):
        result = self.compile(
            step("a", "GetStories", {}, after=["b"]),
            step("b", "GetProjectInfo", {}, after=["a"]),
        )
        self.assertEqual(result["status"], "INVALID")
        self.assertIsNone(result["executionOrder"])

    def test_unknown_and_self_dependencies_are_invalid(self):
        result = self.compile(
            step("a", "GetStories", {}, after=["missing"]),
            step("b", "GetStories", {}, after=["b"]),
        )
        self.assertEqual(result["status"], "INVALID")

    def test_bad_ref_object_rejected(self):
        result = self.compile(
            step("wall", "CreateWalls", {"wallsData": [wall()]}),
            step("window", "CreateWindows", {
                "windowsData": [{
                    "ownerWallId": {"guid": {"$createdGuid": "wall", "extra": "unsafe"}},
                    "centerOffset": 1.5,
                }]
            }),
        )
        self.assertEqual(result["status"], "INVALID")

    def test_invalid_schema_and_duplicate_step_id(self):
        bad = wall()
        bad["height"] = -1
        result = self.compile(step("w", "CreateWalls", {"wallsData": [bad]}))
        self.assertEqual(result["status"], "INVALID")
        with self.assertRaisesRegex(ValueError, "duplicate"):
            self.compile(step("w", "GetStories", {}),
                         step("w", "GetStories", {}))

    def test_multi_create_guid_producer_is_ambiguous(self):
        result = self.compile(
            step("walls", "CreateWalls", {"wallsData": [wall(), wall()]}),
            step("window", "CreateWindows", {
                "windowsData": [{"ownerWallId": {"guid": {"$createdGuid": "walls"}},
                                 "centerOffset": 1}]
            }),
        )
        self.assertEqual(result["status"], "INVALID")
        self.assertIn("exactly one element", str(result["operations"][1]["errors"]))

    def test_guid_placeholder_in_non_guid_parameter_rejected(self):
        result = self.compile(
            step("wall", "CreateWalls", {"wallsData": [wall()]}),
            step("window", "CreateWindows", {
                "windowsData": [{
                    "ownerWallId": {"guid": {"$createdGuid": "wall"}},
                    "centerOffset": 1,
                    "favoriteName": {"$createdGuid": "wall"},
                }]
            }),
        )
        self.assertEqual(result["status"], "INVALID")
        self.assertIn("only in .guid fields", str(result["operations"][1]["errors"]))

    def test_invalid_producer_fields_do_not_crash_planner(self):
        result = self.compile(
            step("wall", "CreateWalls", "not-an-object"),
            step("window", "CreateWindows", {
                "windowsData": [{"ownerWallId": {"guid": {"$createdGuid": "wall"}},
                                 "centerOffset": 1}]
            }),
        )
        self.assertEqual(result["status"], "INVALID")
        self.assertIn("params must be an object", str(result["operations"][0]["errors"]))

    def test_runtime_schema_mismatch_not_live_ready(self):
        result = self.compile(
            step("a", "CreateWalls", {"wallsData": [wall()]}),
            runtime_version="1.5.10",
        )
        self.assertEqual(result["status"], "REQUIRES_UPDATED_SCHEMA")
        self.assertFalse(result["runtimeSchemaMatch"])
        self.assertFalse(result["executionSupported"])


if __name__ == "__main__":
    unittest.main()
