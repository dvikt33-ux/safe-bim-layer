"""Whole pavilion workflow on a synthetic native adapter. Never live evidence."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import archicad_project_accelerator as A
from test_archicad_scene_run import FakeNative


class WholeNative(FakeNative):
    def __call__(self, command, params):
        if command == "API.GetProductInfo":
            self.calls.append(command)
            return {"version": 29, "buildNumber": 5101, "languageCode": "RUS"}
        if command == "GetAllElements":
            self.calls.append(command)
            return {"elements": [{"elementId": {"guid": g}} for g in [*self.existing, *self.created]]}
        return super().__call__(command, params)


class AcceleratorWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.state = self.root / "persistent-state"
        self.state.mkdir()
        self.intent = json.loads((ROOT / "examples/accelerator/pavilion.intent.json").read_text())
        self.native = WholeNative()
        self.counter = 0

    def run_project(self, mode="preflight", token=None, native=None):
        self.counter += 1
        return A.run_project(self.intent, A.RUN.DEFAULT_SCENE_SCHEMA,
                             self.root / f"evidence-{self.counter}", self.state,
                             mode, native or self.native, "pavilion-test-001", token)

    def test_whole_intent_to_plan_preflight_execute_final_readback_and_evidence(self):
        offline = self.run_project("offline")
        self.assertEqual(offline["status"], "ACCELERATOR_COMPILED_OFFLINE")
        self.assertFalse(self.native.calls)
        ticket = self.run_project()
        self.assertEqual(ticket["status"], "READY_FOR_EXPLICIT_TEST_RUN")
        self.assertFalse(self.native.writes)
        self.assertFalse((self.state / "scene-v1-attempts.sqlite3").exists())
        result = self.run_project("execute", ticket["confirmPlanHash"])
        self.assertEqual(result["status"], "COMPLETE_UNSAVED")
        self.assertEqual(result["evidenceKind"], "SYNTHETIC")
        self.assertEqual(len(result["addedGuids"]), 12)
        self.assertEqual(result["removedGuids"], [])
        self.assertTrue(result["wholeAssemblyReadback"])
        self.assertEqual(result["modelWriteAttempts"], 12)
        self.assertFalse(result["plnSaved"])
        folder = self.root / "evidence-3"
        manifest = json.loads((folder / "SHA256.json").read_text())
        for name, digest in manifest.items():
            self.assertEqual(A.hashlib.sha256((folder / name).read_bytes()).hexdigest(), digest)
        self.assertGreater(result["commandCounts"]["GetDetailsOfElements"], 24)

    def test_changed_intent_invalidates_approval_before_any_write(self):
        ticket = self.run_project()
        self.intent["projectId"] = "different-project"
        result = self.run_project("execute", ticket["confirmPlanHash"])
        self.assertEqual(result["status"], "BLOCKED")
        self.assertFalse(self.native.writes)

    def test_timeout_stops_whole_scene_and_durable_ledger_blocks_replay(self):
        ticket = self.run_project()
        self.native.fail_at = "CreateSlabs"
        first = self.run_project("execute", ticket["confirmPlanHash"])
        self.assertEqual(first["status"], "PARTIAL_OR_UNKNOWN_OUTCOME")
        count = len(self.native.writes)
        second = self.run_project("execute", ticket["confirmPlanHash"])
        self.assertEqual(second["status"], "BLOCKED")
        self.assertEqual(len(self.native.writes), count)

    def test_final_assembly_drift_is_not_pass(self):
        ticket = self.run_project()
        def drift(command, params):
            row = self.native(command, params)
            if command == "GetDetailsOfElements" and len(self.native.created) == 12:
                if row["detailsOfElements"][0]["type"] == "Wall":
                    row["detailsOfElements"][0]["details"]["height"] = 9
            return row
        result = self.run_project("execute", ticket["confirmPlanHash"], drift)
        self.assertEqual(result["status"], "PARTIAL_OR_UNKNOWN_OUTCOME")
        self.assertNotIn("wholeAssemblyReadback", result)

    def test_wrong_exact_project_stops_before_inventory(self):
        self.native.wrong_project = True
        result = self.run_project()
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(self.native.calls, ["GetProjectInfo"])

    def test_mandatory_unsupported_scope_is_blocked_without_live_calls(self):
        for primitive in ("typical-floor-v1", "mep-network-v1"):
            self.intent["components"][0]["primitive"] = primitive
            self.assertEqual(self.run_project()["status"], "BLOCKED")
        self.assertFalse(self.native.calls)

    def test_schema_json_edit_cannot_keep_original_source_provenance(self):
        folder = self.root / "schema"
        folder.mkdir()
        for p in A.RUN.DEFAULT_SCENE_SCHEMA.parent.iterdir():
            if p.is_file():
                (folder / p.name).write_bytes(p.read_bytes())
        path = folder / "tapir-scene-live.json"
        doc = json.loads(path.read_text(encoding="utf-8"))
        doc["commands"]["CreateWalls"]["parameters"] = {"type": "object"}
        A.write_json(path, doc)
        with self.assertRaisesRegex(ValueError, "SCHEMA_EXPORT_CONTENT_MISMATCH"):
            A.compile_intent(self.intent, path)

    def test_changed_readonly_inventory_is_blocked(self):
        calls = 0
        def changing(command, params):
            nonlocal calls
            row = self.native(command, params)
            if command == "GetAllElements":
                calls += 1
                if calls == 3:
                    row["elements"] = [{"elementId": {"guid": "00000000-0000-4000-8000-000000000000"}}]
            return row
        result = self.run_project(native=changing)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertFalse(self.native.writes)


if __name__ == "__main__":
    unittest.main()
