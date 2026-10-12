"""Offline contract tests for the pinned Tatarstan read-only snapshot."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import apa_tatarstan_readonly_snapshot as S


A = "11111111-1111-1111-1111-111111111111"
B = "22222222-2222-2222-2222-222222222222"


class FakeApi:
    def __init__(self, *, wrong_project=False, no_native=False, drift=False):
        self.calls = []
        self.wrong_project = wrong_project
        self.no_native = no_native
        self.drift = drift
        self.inventory_calls = 0

    def __call__(self, name, params=None, timeout=120):
        self.calls.append(name)
        if name == "GetProjectInfo":
            return {
                "projectPath": S.EXPECTED_PATH if not self.wrong_project else r"C:\other.pln",
                "projectName": S.EXPECTED_NAME,
                "isUntitled": False, "isTeamwork": False,
            }
        if name == "GetAddOnVersion":
            return {"version": "1.5.10"}
        if name == "GetStories":
            return {"stories": [
                {"index": 0, "level": 0.0}, {"index": 1, "level": 3.0},
                {"index": 2, "level": 6.0},
            ]}
        if name == "GetAllElements":
            self.inventory_calls += 1
            ids = [A, B]
            if self.drift and self.inventory_calls > 1:
                ids = [A]
            return {"elements": [{"elementId": {"guid": g}} for g in ids]}
        if name == "GetDetailsOfElements":
            ids = [e["elementId"]["guid"] for e in params["elements"]]
            return {"detailsOfElements": [
                {"type": "Wall" if g == A else "Roof", "id": g,
                 "floorIndex": 0 if g == A else 2, "details": {"height": 3.0}}
                for g in ids
            ]}
        if name == "Get3DBoundingBoxes":
            return {"boundingBoxes3D": [
                {"boundingBox3D": {
                    "xMin": 39.0, "yMin": 39.0, "zMin": 0.0,
                    "xMax": 45.0, "yMax": 45.0, "zMax": 6.0,
                }} for _ in params["elements"]
            ]}
        if name == "GetModelDumpV1":
            if self.no_native:
                raise RuntimeError("COMMAND_NOT_INSTALLED")
            return {"schemaVersion": "1.0", "elements": [],
                    "bodies": [{"parentGuid": A, "vertices": [], "faces": []}],
                    "materials": [], "nativeBodySlots": 1}
        raise AssertionError("Unexpected command: " + name)


class SnapshotContractTests(unittest.TestCase):
    def test_full_native_readonly_snapshot(self):
        fake = FakeApi()
        snapshot, native = S.collect(fake)
        self.assertEqual(snapshot["inventory_count"], 2)
        self.assertEqual(snapshot["typed_element_counts"], {"Wall": 1, "Roof": 1})
        self.assertEqual(snapshot["bounding_boxes_available"], 2)
        self.assertEqual(snapshot["native_status"], "NATIVE_GEOMETRY_RETURNED")
        self.assertIsNotNone(native)
        self.assertEqual(fake.inventory_calls, 2)
        self.assertEqual(snapshot["sent_model_write_commands"], 0)
        self.assertTrue(set(fake.calls) <= S.READ_COMMANDS)
        self.assertFalse(snapshot["upload_to_github"])

    def test_native_unavailable_falls_back_to_typed_bounds(self):
        fake = FakeApi(no_native=True)
        snapshot, native = S.collect(fake)
        self.assertIsNone(native)
        self.assertEqual(snapshot["native_status"],
                         "UNAVAILABLE_TYPED_AND_AABB_FALLBACK")
        self.assertIn("COMMAND_NOT_INSTALLED", snapshot["native_error"])
        self.assertEqual(snapshot["inventory_count"], 2)

    def test_wrong_project_aborts_before_inventory(self):
        fake = FakeApi(wrong_project=True)
        with self.assertRaisesRegex(RuntimeError, "WRONG_PROJECT_ABORTED"):
            S.collect(fake)
        self.assertEqual(fake.calls, ["GetProjectInfo"])

    def test_drift_aborts_instead_of_marking_snapshot_complete(self):
        fake = FakeApi(drift=True)
        with self.assertRaisesRegex(RuntimeError, "MODEL_OR_PROJECT_DRIFT"):
            S.collect(fake)
        self.assertEqual(fake.inventory_calls, 2)

    def test_non_read_command_refused_before_http(self):
        with self.assertRaisesRegex(ValueError, "WRITE_OR_UNKNOWN_COMMAND_REFUSED"):
            S.tapir("CreateWalls", {"wallsData": []}, port=19724)

    def test_local_archive_has_typed_and_native_files(self):
        snapshot, native = S.collect(FakeApi())
        with tempfile.TemporaryDirectory() as tmp:
            output = S.write_archive(snapshot, native, Path(tmp))
            with zipfile.ZipFile(output) as zf:
                self.assertIsNone(zf.testzip())
                self.assertEqual(set(zf.namelist()),
                                 {"snapshot.json", "native-model.json", "README.txt"})
                saved = json.loads(zf.read("snapshot.json"))
                self.assertEqual(saved["inventory_count"], 2)

    def test_typed_fallback_archive_does_not_invent_native_mesh(self):
        snapshot, native = S.collect(FakeApi(no_native=True))
        with tempfile.TemporaryDirectory() as tmp:
            output = S.write_archive(snapshot, native, Path(tmp))
            with zipfile.ZipFile(output) as zf:
                self.assertEqual(set(zf.namelist()), {"snapshot.json", "README.txt"})
                self.assertIn("ONLY", json.loads(zf.read("snapshot.json"))["geometry_coverage"])


if __name__ == "__main__":
    unittest.main()
