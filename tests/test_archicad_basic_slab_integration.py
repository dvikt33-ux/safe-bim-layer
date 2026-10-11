"""Fail-closed synthetic regression for inherited Composite 0.30 -> Basic 0.20.

No Archicad runtime; tests native-shaped readback, journal, and no replay.
"""
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import archicad_project_accelerator as A
from test_archicad_building_shell_integration import NamedStoriesNative

MATERIAL_GUID = "922C639B-9875-48DF-A3FC-E0A8AC5F2839"
MATERIAL_NAME = "APA Example Concrete - Synthetic Only"


class CompositeDefaultNative(NamedStoriesNative):
    def __init__(self):
        super().__init__()
        self.modified = {}
        self.material_available = True
        self.modify_timeout = False
        self.modify_noop = False

    def __call__(self, command, params):
        if command == "GetAttributesByType":
            self.calls.append(command)
            if params != {"attributeType": "BuildingMaterial"}:
                raise AssertionError("Unexpected material inventory request")
            return {"attributes": ([{"attributeId": {"guid": MATERIAL_GUID},
                                    "name": MATERIAL_NAME, "index": 1,
                                    "modificationTime": 0}]
                                   if self.material_available else [])}
        if command == "ModifySlabs":
            self.calls.append(command)
            self.writes.append(command)
            if self.modify_timeout:
                raise TimeoutError("Unknown native ModifySlabs outcome")
            row = params["slabsWithDetails"][0]
            guid = row["elementId"]["guid"]
            if guid not in self.created or self.created[guid][0] != "CreateSlabs":
                raise AssertionError("Unverified slab modify target")
            if not self.modify_noop:
                self.modified[guid] = dict(row)
            return {"executionResults": [{"success": True}]}
        result = super().__call__(command, params)
        if command == "GetDetailsOfElements":
            guid = params["elements"][0]["elementId"]["guid"]
            if guid in self.created and self.created[guid][0] == "CreateSlabs":
                details = result["detailsOfElements"][0]["details"]
                if guid in self.modified:
                    row = self.modified[guid]
                    details["thickness"] = row["thickness"]
                    details["structureType"] = row["structureType"]
                    details["buildingMaterialId"] = row["buildingMaterialId"]
                else:
                    details["thickness"] = 0.30
                    details["structureType"] = "Composite"
                    details["compositeId"] = {"guid": "A8836EE9-5C72-492B-A7F6-30EFED26B3EE"}
        return result


class BasicSlabIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.state = self.root / "state"
        self.state.mkdir()
        self.native = CompositeDefaultNative()
        self.intent = json.loads((ROOT / "examples/accelerator/building-shell.intent.json")
                                 .read_text(encoding="utf-8"))
        self.intent["components"][0]["specification"]["slabBasicMaterialName"] = MATERIAL_NAME
        self.counter = 0

    def run_project(self, mode, token=None, run_id="apa-basic-slab-001"):
        self.counter += 1
        return A.run_project(
            self.intent, A.RUN.DEFAULT_SCENE_SCHEMA,
            self.root / ("out-" + str(self.counter)), self.state,
            mode=mode, transport=self.native, run_id=run_id, confirm_hash=token)

    def test_inherited_composite_corrected_and_reverified_twice(self):
        pre = self.run_project("preflight")
        self.assertEqual(pre["status"], "READY_FOR_EXPLICIT_TEST_RUN", pre)
        self.assertEqual(pre["modelWriteAttempts"], 0)
        self.assertFalse(self.native.writes)
        result = self.run_project("execute", pre["confirmPlanHash"])
        self.assertEqual(result["status"], "COMPLETE_UNSAVED", result)
        self.assertTrue(result["wholeAssemblyReadback"])
        self.assertEqual(result["modelWriteAttempts"], 27)  # 25 creates + 2 guarded modifies
        self.assertEqual(self.native.writes.count("ModifySlabs"), 2)
        self.assertEqual(len(result["addedGuids"]), 25)
        for sid in ("s1-slab", "s2-slab"):
            guid = result["scene"]["steps"][sid]["guid"]
            self.assertEqual(self.native.modified[guid]["structureType"], "Basic")
            self.assertEqual(self.native.modified[guid]["thickness"], 0.2)
            self.assertEqual(self.native.modified[guid]["buildingMaterialId"]["guid"],
                             MATERIAL_GUID)
        with sqlite3.connect(self.state / "scene-v1-attempts.sqlite3") as db:
            self.assertEqual(db.execute(
                "SELECT COUNT(*) FROM steps WHERE state='PASS'").fetchone()[0], 25)

    def test_missing_material_blocks_before_any_model_mutation(self):
        self.native.material_available = False
        result = self.run_project("preflight")
        self.assertEqual(result["status"], "BLOCKED", result)
        self.assertIn("BASIC_SLAB_MATERIAL_MISSING_OR_AMBIGUOUS", result["reason"])
        self.assertEqual(result["modelWriteAttempts"], 0)
        self.assertFalse(self.native.writes)

    def test_modify_timeout_retains_existing_slab_guid_no_replay(self):
        pre = self.run_project("preflight")
        self.native.modify_timeout = True
        result = self.run_project("execute", pre["confirmPlanHash"])
        self.assertEqual(result["status"], "PARTIAL_OR_UNKNOWN_OUTCOME", result)
        self.assertEqual(result["scene"]["failedStep"], "s1-slab")
        self.assertEqual(result["modelWriteAttempts"], 6)  # 4 walls, slab, ModifySlabs
        with sqlite3.connect(self.state / "scene-v1-attempts.sqlite3") as db:
            state, guid, record = db.execute(
                "SELECT state,guid,output FROM steps WHERE step_id='s1-slab'").fetchone()
            self.assertEqual(state, "BASIC_MODIFY_ATTEMPTED")
            self.assertEqual(guid, result["addedGuids"][-1])
            self.assertEqual(json.loads(record)["command"], "ModifySlabs")
        before = len(self.native.writes)
        retry = self.run_project("execute", pre["confirmPlanHash"])
        self.assertEqual(retry["status"], "BLOCKED", retry)
        self.assertEqual(len(self.native.writes), before)

    def test_fake_modify_success_without_actual_change_is_not_pass(self):
        pre = self.run_project("preflight")
        self.native.modify_noop = True
        result = self.run_project("execute", pre["confirmPlanHash"])
        self.assertEqual(result["status"], "PARTIAL_OR_UNKNOWN_OUTCOME", result)
        self.assertIn("SLAB_READBACK_MISMATCH", result["scene"]["reason"])
        self.assertEqual(result["scene"]["failedStep"], "s1-slab")
        self.assertNotIn("wholeAssemblyReadback", result)

    def test_spec_rejects_blank_material_name(self):
        self.intent["components"][0]["specification"]["slabBasicMaterialName"] = " "
        out = self.run_project("offline")
        self.assertEqual(out["status"], "BLOCKED")
        self.assertEqual(out["modelWriteAttempts"], 0)


if __name__ == "__main__":
    unittest.main()
