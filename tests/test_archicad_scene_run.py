"""Offline system tests for a complete 12-element Archicad scene, never live."""
import importlib.util
import json
import sqlite3
import tempfile
import unittest
import uuid
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import archicad_scene_v1 as SCENE
import archicad_scene_run as RUN


class FakeNative:
    def __init__(self):
        self.calls = []
        self.writes = []
        self.created = {}
        self.existing = []
        self.collision = False
        self.fail_at = None
        self.wrong_project = False
        self.wrong_version = False

    def __call__(self, command, params):
        self.calls.append(command)
        if command == "GetProjectInfo":
            return {"projectName": RUN.EXPECTED_NAME if not self.wrong_project else "OTHER",
                    "projectPath": RUN.EXPECTED_PATH if not self.wrong_project else "C:\\other.pln",
                    "isUntitled": False, "isTeamwork": False}
        if command == "GetStories":
            return {"actStory": 0, "stories": [
                {"index": 0, "floorId": 1, "level": 0.0},
                {"index": 1, "floorId": 2, "level": 3.0}]}
        if command == "GetAddOnVersion":
            return {"version": "1.5.9" if self.wrong_version else "1.5.10"}
        if command == "GetAllElements":
            return {"elements": [{"elementId": {"guid": key}} for key in self.existing]}
        if command == "Get3DBoundingBoxes":
            return {"boundingBoxes3D": [
                {"boundingBox3D": {"xMin": 200.1 if self.collision else -10,
                                   "xMax": 200.2 if self.collision else -9,
                                   "yMin": 200.1 if self.collision else -10,
                                   "yMax": 200.2 if self.collision else -9,
                                   "zMin": 0, "zMax": 1}}
                for _ in params["elements"]]}
        if command in RUN.ALLOWED_WRITES:
            self.writes.append(command)
            if self.fail_at == command:
                raise TimeoutError("unknown native outcome; do not retry")
            guid = str(uuid.uuid5(uuid.NAMESPACE_DNS, "scene-"+str(len(self.writes))))
            self.created[guid] = (command, json.loads(json.dumps(params)))
            return {"elements": [{"elementId": {"guid": guid}}]}
        if command == "GetDetailsOfElements":
            guid = params["elements"][0]["elementId"]["guid"]
            cmd, arguments = self.created[guid]
            item = list(arguments.values())[0][0]
            kind = cmd[6:-1]
            if kind == "Wall":
                data = dict(item)
                data.update(geometryType="Straight", begThickness=item["thickness"],
                            endThickness=item["thickness"])
            elif kind == "Slab":
                data = {"thickness": item["thickness"], "level": item["level"],
                        "polygonOutline": item["polygonCoordinates"]}
            elif kind == "Column":
                point = item["coordinates"]
                data = {"origin": {"x": point["x"], "y": point["y"]},
                        "zCoordinate": point["z"], "height": item["height"],
                        "width": item["width"], "depth": item["depth"]}
            else:
                data = dict(item)
                data["ownerElementId"] = data.pop("ownerWallId")
                data["ownerElementType"] = "Wall"
            return {"detailsOfElements": [{
                "type": kind, "floorIndex": 0, "details": data
            }]}
        raise AssertionError("Unexpected native API command: "+command)


class SceneV1SystemTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Path(self.tmp.name) / "scene-v1-attempts.sqlite3"
        self.native = FakeNative()
        self.runner = RUN.SceneWriter(self.native, self.db)

    def test_single_source_dimensions_and_twelve_elements(self):
        proposal = SCENE.prepare(200, 200)
        self.assertEqual(proposal["status"], "SCENE_PREVIEW_OFFLINE")
        self.assertEqual(len(proposal["graph"]["operations"]), 12)
        self.assertEqual(proposal["metrics"]["grossFootprintSquareMeters"], 12)
        self.assertEqual(proposal["metrics"]["grossVolumeCubicMeters"], 36)
        self.assertEqual(proposal["metrics"]["interiorClearAreaSquareMeters"], 9.36)
        self.assertEqual(proposal["metrics"]["wallReferenceLineLengthsMeters"],
                         {"long": 3.8, "short": 2.8})
        self.assertEqual(proposal["metrics"]["perimeterMeters"], 14)
        self.assertEqual(proposal["metrics"]["elementKinds"],
                         {"Wall": 4, "Slab": 1, "Column": 4, "Window": 2, "Door": 1})
        self.assertEqual(proposal["sourcePlanHash"], SCENE.prepare(200, 200)["sourcePlanHash"])
        self.assertEqual(proposal["graph"]["operations"][2]["params"]["wallsData"][0]
                         ["begCoordinate"], {"x": 203.9, "y": 202.9})
        self.assertFalse(proposal["plnChanged"])

    def test_read_only_preflight_makes_no_changes(self):
        out = self.runner.preflight(200, 200)
        self.assertEqual(out["status"], "READY_FOR_EXPLICIT_TEST_RUN")
        self.assertFalse(self.native.writes)
        self.assertFalse(self.db.exists())

    def test_all_twelve_native_creates_and_host_guids(self):
        preflight = self.runner.preflight(200, 200)
        out = self.runner.execute(200, 200, "scene-safe-run-001",
                                  preflight["sourcePlanHash"])
        self.assertEqual(out["status"], "COMPLETE_UNSAVED")
        self.assertEqual(out["createdCount"], 12)
        self.assertEqual(len(self.native.writes), 12)
        self.assertEqual(self.native.writes.count("CreateWalls"), 4)
        self.assertEqual(self.native.writes.count("CreateColumns"), 4)
        self.assertEqual(self.native.writes.count("CreateSlabs"), 1)
        self.assertEqual(self.native.writes.count("CreateWindows"), 2)
        self.assertEqual(self.native.writes.count("CreateDoors"), 1)
        self.assertTrue(out["allGuidsReadback"])
        self.assertFalse(out["plnSaved"])
        north = out["steps"]["wall-north"]["guid"]
        south = out["steps"]["wall-south"]["guid"]
        for gid, (command, params) in self.native.created.items():
            if command == "CreateWindows":
                self.assertEqual(params["windowsData"][0]["ownerWallId"]["guid"], north)
            if command == "CreateDoors":
                self.assertEqual(params["doorsData"][0]["ownerWallId"]["guid"], south)
        with sqlite3.connect(self.db) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM steps").fetchone()[0], 12)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM steps WHERE state='PASS'").fetchone()[0], 12)

    def test_scene_replay_and_duplicate_intent_are_blocked(self):
        ticket = self.runner.preflight(200, 200)
        self.assertEqual(self.runner.execute(200, 200, "scene-safe-run-001",
                         ticket["sourcePlanHash"])["status"], "COMPLETE_UNSAVED")
        count = len(self.native.writes)
        with self.assertRaisesRegex(ValueError, "SCENE_ALREADY_RESERVED"):
            self.runner.execute(200, 200, "scene-safe-run-001", ticket["sourcePlanHash"])
        with self.assertRaisesRegex(ValueError, "SCENE_ALREADY_RESERVED"):
            self.runner.execute(200, 200, "scene-safe-run-002", ticket["sourcePlanHash"])
        self.assertEqual(len(self.native.writes), count)

    def test_existing_model_spatial_collision_blocks_all_writes(self):
        self.native.existing = ["F0E8C2B3-1248-4D92-8890-EA1379E18152"]
        self.native.collision = True
        with self.assertRaisesRegex(ValueError, "SPATIAL_COLLISION"):
            self.runner.preflight(200, 200)
        self.assertFalse(self.native.writes)

    def test_existing_geometry_elsewhere_is_allowed(self):
        self.native.existing = ["F0E8C2B3-1248-4D92-8890-EA1379E18152"]
        p = self.runner.preflight(200, 200)
        self.assertEqual(p["existingElementsSpatiallyChecked"], 1)
        self.assertFalse(self.native.writes)

    def test_unknown_outcome_is_partial_and_not_replayed(self):
        t = self.runner.preflight(200, 200)
        self.native.fail_at = "CreateSlabs"
        r = self.runner.execute(200, 200, "scene-partial-001", t["sourcePlanHash"])
        self.assertEqual(r["status"], "PARTIAL_OR_UNKNOWN_OUTCOME")
        self.assertEqual(r["failedStep"], "slab")
        self.assertEqual(self.native.writes.count("CreateWalls"), 4)
        self.assertEqual(self.native.writes.count("CreateSlabs"), 1)
        self.assertEqual(self.native.writes.count("CreateWindows"), 0)
        with sqlite3.connect(self.db) as db:
            state = db.execute("SELECT state FROM steps WHERE step_id='slab'").fetchone()[0]
            self.assertEqual(state, "ATTEMPTED")
        with self.assertRaisesRegex(ValueError, "SCENE_ALREADY_RESERVED"):
            self.runner.execute(200, 200, "scene-partial-001", t["sourcePlanHash"])

    def test_wrong_project_or_version_blocks(self):
        self.native.wrong_project = True
        with self.assertRaisesRegex(ValueError, "WRONG_PROJECT"):
            self.runner.preflight(200, 200)
        self.native.wrong_project = False
        self.native.wrong_version = True
        with self.assertRaisesRegex(ValueError, "TAPIR_VERSION_MISMATCH"):
            self.runner.preflight(200, 200)
        self.assertFalse(self.native.writes)

    def test_wrong_plan_hash_blocks_with_no_writes(self):
        with self.assertRaisesRegex(ValueError, "PLAN_HASH_MISMATCH"):
            self.runner.execute(200, 200, "scene-safe-run-003", "bad-hash")
        self.assertFalse(self.native.writes)
        self.assertFalse(self.db.exists())


if __name__ == "__main__":
    unittest.main()
