"""Single-run offline floor scenario: Graph + existing native resolution/readback helpers.

No real Archicad connection: the FakeNative implementation is imported from
the existing 12-element scene system tests. No SceneWriter.execute is called.
"""
import sys
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import archicad_typical_floor_graph as FLOOR
import archicad_scene_run as RUN
from test_archicad_scene_run import FakeNative


class TypicalFloorGraphTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.preview = FLOOR.prepare()

    def test_single_parametric_floor_graph(self):
        p = self.preview
        self.assertEqual(p["status"], "FLOOR_PREVIEW_OFFLINE")
        self.assertEqual(p["metrics"]["elementCount"], 101)
        self.assertEqual(p["metrics"]["elementKinds"],
                         {"Wall": 36, "Slab": 1, "Column": 28,
                          "Window": 24, "Door": 12})
        self.assertEqual(p["metrics"]["roomCount"], 12)
        self.assertEqual(p["metrics"]["grossFootprintSquareMeters"], 648)
        self.assertEqual(p["metrics"]["grossVolumeCubicMeters"], 1944)
        self.assertEqual(len(p["executionOrder"]), 101)
        self.assertEqual(len(set(p["executionOrder"])), 101)
        self.assertFalse(p["liveWriteAuthorized"])
        self.assertFalse(p["modelChanged"])
        self.assertEqual(p["nativeOperationsVerified"], 0)

    def test_nothing_silent_about_unavailable_native_primitives(self):
        s = self.preview["semantic"]
        self.assertEqual({x["type"] for x in s["cores"]},
                         {"STAIR_CORE", "LIFT_CORE", "MEP_CORE"})
        self.assertTrue(all(x["nativeImplementation"] == "UNSUPPORTED"
                            for x in s["cores"]))
        self.assertTrue(all(x["nativeZone"] == "UNSUPPORTED"
                            for x in s["rooms"]))
        self.assertEqual(set(s["materials"].values()), {"UNSUPPORTED"})
        self.assertEqual(s["physicalJunctionsAndClashes"], "NOT_VERIFIED")

    def test_hosted_openings_refer_to_planned_walls(self):
        by_id = {x["id"]: x for x in self.preview["graph"]["operations"]}
        for step in self.preview["graph"]["operations"]:
            if step["command"] not in ("CreateWindows", "CreateDoors"):
                continue
            entry = next(iter(step["params"].values()))[0]
            host = entry["ownerWallId"]["guid"]["$createdGuid"]
            self.assertIn(host, by_id)
            self.assertEqual(by_id[host]["command"], "CreateWalls")
            parent = next(iter(by_id[host]["params"].values()))[0]
            axis_length = ((parent["begCoordinate"]["x"]-parent["endCoordinate"]["x"])**2
                           + (parent["begCoordinate"]["y"]-parent["endCoordinate"]["y"])**2)**0.5
            self.assertGreaterEqual(entry["centerOffset"]-entry["width"]/2, 0)
            self.assertLessEqual(entry["centerOffset"]+entry["width"]/2, axis_length)

    def test_end_to_end_mock_with_existing_native_readback(self):
        """101 API-like create calls; every GUID and host is verified in memory."""
        fake = FakeNative()
        created = {"__plan__": self.preview["graph"]}
        by_id = {x["id"]: x for x in self.preview["graph"]["operations"]}
        results = []
        for sid in self.preview["executionOrder"]:
            step = by_id[sid]
            cmd = step["command"]
            self.assertIn(cmd, FLOOR.SUPPORTED)
            host = (RUN.check_previous_wall(fake, step, created)
                    if cmd in ("CreateWindows", "CreateDoors") else None)
            resolved = RUN.resolve_params(step, created)
            guid = RUN.created_guid(fake(cmd, resolved))
            details = RUN.requested_details(fake, guid)
            kind = RUN.verify_readback(cmd, resolved, details, host)
            self.assertNotIn(guid, (record["guid"] for record in created.values()
                                    if isinstance(record, dict) and "guid" in record))
            created[sid] = {"guid": guid, "kind": kind}
            results.append(sid)
        self.assertEqual(len(results), 101)
        self.assertEqual(len(fake.writes), 101)
        self.assertEqual(Counter(fake.writes), {
            "CreateWalls": 36, "CreateColumns": 28,
            "CreateWindows": 24, "CreateDoors": 12,
            "CreateSlabs": 1,
        })
        self.assertEqual(len(fake.created), 101)

    def test_parametric_recompile_no_manual_geometry_copies(self):
        a = FLOOR.prepare(FLOOR.FloorParameters(length=30, bays=5))
        b = FLOOR.prepare(FLOOR.FloorParameters(length=30, bays=5))
        moved = FLOOR.prepare(FLOOR.FloorParameters(
            anchor_x=250, length=30, bays=5))
        self.assertEqual(a["metrics"]["elementCount"], 85)
        self.assertEqual(a["sourcePlanHash"], b["sourcePlanHash"])
        self.assertNotEqual(a["sourcePlanHash"], moved["sourcePlanHash"])
        self.assertEqual(len(a["semantic"]["rooms"]), 10)
        self.assertEqual(a["metrics"]["grossFootprintSquareMeters"], 540)

    def test_native_story_0_is_first_storey_not_named_zero_floor(self):
        self.assertEqual(self.preview["metrics"]["firstStoryIndexInAPI"], 0)
        with self.assertRaisesRegex(ValueError, "UNSUPPORTED_STORY"):
            FLOOR.prepare(FLOOR.FloorParameters(story_index=1))
        with self.assertRaisesRegex(ValueError, "UNSUPPORTED_STORY"):
            FLOOR.prepare(FLOOR.FloorParameters(story_level=4.5))

    def test_invalid_and_large_geometry_fail_closed(self):
        for value in (FLOOR.FloorParameters(length=10, bays=6),
                      FLOOR.FloorParameters(window_width=5),
                      FLOOR.FloorParameters(corridor_width=16),
                      FLOOR.FloorParameters(anchor_x=float("nan"))):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    FLOOR.prepare(value)

    def test_unknown_host_rejected_by_existing_graph_compiler(self):
        from copy import deepcopy
        g = deepcopy(self.preview["graph"])
        step = next(v for v in g["operations"] if v["command"] == "CreateDoors")
        step["params"]["doorsData"][0]["ownerWallId"]["guid"] = {
            "$createdGuid": "nonexistent-parent"}
        catalog = FLOOR.GRAPH.CONTRACTS.load_catalog(
            FLOOR.GRAPH.CONTRACTS.DEFAULT_SCHEMA)
        report = FLOOR.GRAPH.compile_graph(catalog, g)
        self.assertEqual(report["status"], "INVALID")

    def test_501_nodes_rejected_before_schema_calls(self):
        original = self.preview["graph"]["operations"][0]
        graph = {"operations": [
            {**original, "id": f"overflow-{i:03}"} for i in range(501)
        ]}
        with self.assertRaisesRegex(ValueError, "1..500"):
            FLOOR.GRAPH.compile_graph({"commands": {}}, graph)


if __name__ == "__main__":
    unittest.main()
