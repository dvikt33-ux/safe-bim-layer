"""Synthetic integration of parameterized building intent with EXISTING scene writer.
No live Archicad, PLN writes, structural calculations or approvals.
"""
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import archicad_project_accelerator as A
import archicad_building_shell as BUILD
from test_archicad_project_accelerator import WholeNative


class NamedStoriesNative(WholeNative):
    def __call__(self, command, params):
        if command == "GetStories":
            self.calls.append(command)
            return {"actStory": 0, "stories": [
                {"index": 0, "floorId": 1, "level": 0., "name": "1 этаж"},
                {"index": 1, "floorId": 2, "level": 3., "name": "2 этаж"}]}
        if command == "GetDetailsOfElements":
            row = super().__call__(command, params)
            guid = params["elements"][0]["elementId"]["guid"]
            source, args = self.created[guid]
            if source in ("CreateDoors", "CreateWindows"):
                parent_guid = next(iter(args.values()))[0]["ownerWallId"]["guid"]
                _, p = self.created[parent_guid]
                native_floor = p["wallsData"][0]["floorIndex"]
            else:
                native_floor = next(iter(args.values()))[0]["floorIndex"]
            row["detailsOfElements"][0]["floorIndex"] = native_floor
            if source == "CreateWalls" and native_floor == 1:
                row["detailsOfElements"][0]["details"]["zCoordinate"] = 3.0
            return row
        return super().__call__(command, params)


class ExactScratchProjectNative(NamedStoriesNative):
    """Synthetic transport representing observed GetStories from port 19726."""
    def __call__(self, command, params):
        if command == "GetStories":
            self.calls.append(command)
            return {"actStory": 0, "stories": [
                {"index": 0, "floorId": 1, "level": 0., "name": "Первый Этаж"},
                {"index": 1, "floorId": 2, "level": 3., "name": ""},
                {"index": 2, "floorId": 3, "level": 6., "name": ""}]}
        return super().__call__(command, params)


class MultiStoreyEndToEndTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.state = self.root / "ledger"
        self.state.mkdir()
        self.native = NamedStoriesNative()
        self.intent = json.loads((ROOT / "examples/accelerator/building-shell.intent.json")
                                 .read_text(encoding="utf-8"))
        self.i = 0

    def call(self, mode, token=None, native=None):
        self.i += 1
        return A.run_project(self.intent, A.RUN.DEFAULT_SCENE_SCHEMA,
                             self.root / ("run-" + str(self.i)), self.state, mode,
                             native or self.native, "building-shell-integrated-1", token)

    def test_two_storey_high_level_graph_not_fragmented(self):
        preview = A.compile_intent(self.intent, A.RUN.DEFAULT_SCENE_SCHEMA)
        graph = preview["graph"]["operations"]
        self.assertEqual(len(graph), 25)
        self.assertEqual(preview["metrics"]["elementKinds"],
                         {"Wall": 12, "Slab": 2, "Door": 5, "Window": 6})
        self.assertEqual(preview["metrics"]["grossFloorAreaSquareMeters"], 160)
        self.assertEqual(preview["metrics"]["storeyCount"], 2)
        self.assertEqual(len({x["id"] for x in graph}), len(graph))
        self.assertEqual(len([x for x in graph if "-wall-" in x["id"]]), 8)
        self.assertFalse(preview["metrics"]["structuralVerified"])
        self.assertFalse(preview["metrics"]["normativeVerified"])
        self.assertFalse(self.native.writes)

    def test_full_offline_preflight_synthetic_execution_and_readback(self):
        offline = self.call("offline")
        self.assertEqual(offline["status"], "ACCELERATOR_COMPILED_OFFLINE", offline)
        self.assertFalse(self.native.calls)
        preflight = self.call("preflight")
        self.assertEqual(preflight["status"], "READY_FOR_EXPLICIT_TEST_RUN", preflight)
        self.assertFalse(self.native.writes)
        result = self.call("execute", preflight["confirmPlanHash"])
        self.assertEqual(result["status"], "COMPLETE_UNSAVED", result)
        self.assertEqual(len(result["addedGuids"]), 25)
        self.assertTrue(result["wholeAssemblyReadback"])
        self.assertEqual(result["modelWriteAttempts"], 25)
        self.assertEqual(self.native.writes.count("CreateWalls"), 12)
        self.assertEqual(self.native.writes.count("CreateSlabs"), 2)
        self.assertEqual(self.native.writes.count("CreateDoors"), 5)
        self.assertEqual(self.native.writes.count("CreateWindows"), 6)
        self.assertFalse(result["plnSaved"])
        self.assertEqual(self.call("execute", preflight["confirmPlanHash"])["status"],
                         "BLOCKED")

    def test_story_mismatch_blocks_before_any_mutation(self):
        original = self.native.__call__
        def changed(command, params):
            if command == "GetStories":
                payload = original(command, params)
                payload["stories"][1]["level"] = 4.0
                return payload
            return original(command, params)
        result = self.call("preflight", native=changed)
        self.assertEqual(result["status"], "BLOCKED", result)
        self.assertFalse(self.native.writes)

    def test_changed_brief_invalidates_approval(self):
        before = self.call("preflight")
        self.intent["components"][0]["specification"]["width"] = 12
        after = self.call("execute", before["confirmPlanHash"])
        self.assertEqual(after["status"], "BLOCKED")
        self.assertFalse(self.native.writes)

    def test_actual_scratch_story_bindings_and_disposable_project_preflight(self):
        from unittest.mock import patch

        actual_intent = json.loads(
            (ROOT / "examples/accelerator/apa-test-house-01.intent.json")
            .read_text(encoding="utf-8"))
        native = ExactScratchProjectNative()
        with (patch.object(A.RUN, "PORT", 19726),
              patch.object(A.RUN, "EXPECTED_PATH",
                           r"C:\LocalAI\APA_Test_House_01.pln"),
              patch.object(A.RUN, "EXPECTED_NAME", "APA_Test_House_01")):
            first = A.run_project(actual_intent, A.RUN.DEFAULT_SCENE_SCHEMA,
                                  self.root / "actual-scratch-preflight",
                                  self.state, mode="preflight", transport=native)
            self.assertEqual(first["status"], "READY_FOR_EXPLICIT_TEST_RUN", first)
            self.assertFalse(native.writes)
            second = A.run_project(actual_intent, A.RUN.DEFAULT_SCENE_SCHEMA,
                                   self.root / "actual-scratch-exec",
                                   self.state, mode="execute", transport=native,
                                   run_id="actual-scratch-001",
                                   confirm_hash=first["confirmPlanHash"])
            self.assertEqual(second["status"], "COMPLETE_UNSAVED", second)
            self.assertEqual(len(second["addedGuids"]), 25)
            self.assertTrue(second["wholeAssemblyReadback"])
            self.assertEqual(second["binding"]["port"], 19726)

    def test_strict_scratch_pln_override_does_not_allow_protected_projects(self):
        from unittest.mock import patch

        old_path = A.RUN.EXPECTED_PATH
        old_name = A.RUN.EXPECTED_NAME
        old_port = A.RUN.PORT
        try:
            with self.assertRaisesRegex(ValueError, "TEST_PLN_NOT_APPROVED"):
                A.RUN.bind_approved_scratch_pln(
                    19724, r"C:\Users\Admin\Documents\APA_Pavilion_MVP_SUCCESS.pln")
            self.assertEqual(A.RUN.EXPECTED_PATH, old_path)
            A.RUN.bind_approved_scratch_pln(19726)
            self.assertEqual(A.RUN.EXPECTED_PATH,
                             r"C:\LocalAI\APA_Test_House_01.pln")
            self.assertEqual(A.RUN.PORT, 19726)
        finally:
            A.RUN.EXPECTED_PATH = old_path
            A.RUN.EXPECTED_NAME = old_name
            A.RUN.PORT = old_port

    def test_unknown_structure_is_not_reported_as_engineered(self):
        preview = BUILD.prepare(self.intent["components"][0], A.RUN.DEFAULT_SCENE_SCHEMA)
        self.assertIn("NOT_FOR_CONSTRUCTION", preview["limitations"][0])
        with self.assertRaisesRegex(ValueError, "ROOM_BAYS_NOT_FIT"):
            self.intent["components"][0]["specification"]["roomBays"] = 20
            BUILD.prepare(self.intent["components"][0], A.RUN.DEFAULT_SCENE_SCHEMA)


if __name__ == "__main__":
    unittest.main()
