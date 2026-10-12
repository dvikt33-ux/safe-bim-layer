"""Offline-only exact scratch slab recovery proof. No Windows PLN, no network."""
import json
import sqlite3
from contextlib import closing
from pathlib import Path
import sys
import tempfile
import unittest
import uuid
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import archicad_scene_run as RUN
import archicad_building_shell as BUILD
import repair_apa_partial_slab as REPAIR
from test_archicad_basic_slab_integration import (
    CompositeDefaultNative, MATERIAL_NAME, MATERIAL_GUID)


class PartialSlabRecoveryTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.parent = Path(temp.name)
        self.run = self.parent / "20261011-031123-7181b47c"
        (self.run / "execute").mkdir(parents=True)
        self.ledger = self.parent / "persistent-ledger" / "scene-v1-attempts.sqlite3"
        self.ledger.parent.mkdir()
        self.native = CompositeDefaultNative()
        self.native.existing = [
            str(uuid.uuid5(uuid.NAMESPACE_DNS, "apa-original-"+str(i)))
            for i in range(20)]
        self.addCleanup(lambda: None)

        intent = json.loads((ROOT / "examples/accelerator/building-shell.intent.json")
                            .read_text(encoding="utf-8"))
        self.preview = BUILD.prepare(intent["components"][0])
        ops = {s["id"]: s for s in self.preview["graph"]["operations"]}
        self.scene_id = "apa-house-20261011-031123-7181b47c"
        self.plan_hash = "a" * 64
        self.rows = {}
        for sid in (*REPAIR.WALL_IDS, REPAIR.FAILED_STEP):
            step = ops[sid]
            guid = REPAIR.SLAB_GUID if sid == REPAIR.FAILED_STEP else str(
                uuid.uuid5(uuid.NAMESPACE_DNS, "apa-partial-"+sid))
            self.native.created[guid] = (step["command"], step["params"])
            self.rows[sid] = guid

        (self.run / "execute" / "result.json").write_text(json.dumps({
            "status": "PARTIAL_OR_UNKNOWN_OUTCOME",
            "scene": {"failedStep": REPAIR.FAILED_STEP,
                      "sceneId": self.scene_id, "planHash": self.plan_hash}
        }), encoding="utf-8")
        (self.run / "execute" / "plan.json").write_text(json.dumps({
            "graph": self.preview["graph"],
            "storyBindings": self.preview["storyBindings"]
        }), encoding="utf-8")
        (self.run / "execute" / "inventory-before.json").write_text(
            json.dumps(self.native.existing), encoding="utf-8")
        with closing(sqlite3.connect(self.ledger)) as db, db:
            db.execute("CREATE TABLE scenes (scene_id TEXT PRIMARY KEY,plan_hash TEXT NOT NULL,"
                       "state TEXT NOT NULL,result TEXT NOT NULL)")
            db.execute("CREATE TABLE steps (scene_id TEXT NOT NULL,step_id TEXT NOT NULL,"
                       "state TEXT NOT NULL,guid TEXT,output TEXT NOT NULL,"
                       "PRIMARY KEY(scene_id,step_id))")
            db.execute("INSERT INTO scenes VALUES (?,?,?,?)",
                       (self.scene_id, self.plan_hash, "PARTIAL_OR_UNKNOWN_OUTCOME", "{}"))
            for sid, guid in self.rows.items():
                db.execute("INSERT INTO steps VALUES (?,?,?,?,?)",
                           (self.scene_id, sid,
                            "CREATED_UNVERIFIED" if sid == REPAIR.FAILED_STEP else "PASS",
                            guid, "{}"))
        self.target_patch = patch.multiple(
            RUN, EXPECTED_NAME="APA_Test_House_01",
            EXPECTED_PATH=RUN.APPROVED_SCRATCH_PATH, PORT=19726)
        self.target_patch.start()
        self.addCleanup(self.target_patch.stop)

    def test_read_only_preflight_exact_old_scene(self):
        p = REPAIR.preflight(self.native, self.run, MATERIAL_NAME)
        self.assertEqual(p["status"], "READY_FOR_EXPLICIT_SINGLE_SLAB_REPAIR")
        self.assertEqual(p["materialGuid"], MATERIAL_GUID)
        self.assertEqual(p["slabGuid"], REPAIR.SLAB_GUID)
        self.assertEqual(p["modelWriteAttempts"], 0)
        self.assertEqual(self.native.writes, [])
        with closing(sqlite3.connect(self.ledger)) as db, db:
            self.assertIsNone(db.execute(
                "SELECT name FROM sqlite_master WHERE name=?",
                (REPAIR.REPAIR_TABLE,)).fetchone())

    def test_one_exact_modify_then_durable_readback_and_replay_rejection(self):
        ticket = REPAIR.preflight(self.native, self.run, MATERIAL_NAME)
        out = REPAIR.repair(self.native, self.run, MATERIAL_NAME, ticket["token"])
        self.assertEqual(out["status"], "SINGLE_SLAB_REPAIR_VERIFIED_UNSAVED", out)
        self.assertEqual(self.native.writes, ["ModifySlabs"])
        self.assertEqual(len(self.native.created), 5)
        with closing(sqlite3.connect(self.ledger)) as db, db:
            record = db.execute(
                "SELECT state FROM apa_partial_slab_repairs").fetchone()
            self.assertEqual(record[0], "READBACK_PASS")
            original = db.execute(
                "SELECT state FROM steps WHERE step_id=?",
                (REPAIR.FAILED_STEP,)).fetchone()
            self.assertEqual(original[0], "CREATED_UNVERIFIED")
        with self.assertRaisesRegex(ValueError, "ALREADY_RESERVED|MATCHES_HISTORICAL"):
            REPAIR.repair(self.native, self.run, MATERIAL_NAME, ticket["token"])
        self.assertEqual(self.native.writes, ["ModifySlabs"])

    def test_wrong_token_cannot_mutate(self):
        with self.assertRaisesRegex(ValueError, "TOKEN_MISMATCH"):
            REPAIR.repair(self.native, self.run, MATERIAL_NAME, "wrong")
        self.assertEqual(self.native.writes, [])

    def test_timeout_keeps_immutable_prewrite_reservation(self):
        ticket = REPAIR.preflight(self.native, self.run, MATERIAL_NAME)
        self.native.modify_timeout = True
        out = REPAIR.repair(self.native, self.run, MATERIAL_NAME, ticket["token"])
        self.assertEqual(out["status"], "REPAIR_OUTCOME_UNCERTAIN_NO_RETRY", out)
        self.assertEqual(self.native.writes, ["ModifySlabs"])
        with closing(sqlite3.connect(self.ledger)) as db, db:
            row = db.execute(
                "SELECT state,slab_guid FROM apa_partial_slab_repairs").fetchone()
            self.assertEqual(row, ("UNKNOWN_NEEDS_MANUAL_INSPECTION", REPAIR.SLAB_GUID))
        with self.assertRaisesRegex(ValueError, "ALREADY_RESERVED"):
            REPAIR.preflight(self.native, self.run, MATERIAL_NAME)

    def test_fake_success_without_change_never_passes(self):
        ticket = REPAIR.preflight(self.native, self.run, MATERIAL_NAME)
        self.native.modify_noop = True
        out = REPAIR.repair(self.native, self.run, MATERIAL_NAME, ticket["token"])
        self.assertEqual(out["status"], "REPAIR_OUTCOME_UNCERTAIN_NO_RETRY", out)
        self.assertIn("SLAB_REPAIR_TYPED_READBACK_MISMATCH", out["error"])

    def test_extra_model_element_blocks_without_write(self):
        self.native.existing.append(str(uuid.uuid4()))
        with self.assertRaisesRegex(ValueError, "INVENTORY_CHANGED"):
            REPAIR.preflight(self.native, self.run, MATERIAL_NAME)
        self.assertEqual(self.native.writes, [])

    def test_absent_material_blocks_without_write(self):
        self.native.material_available = False
        with self.assertRaisesRegex(ValueError, "BASIC_SLAB_MATERIAL_MISSING"):
            REPAIR.preflight(self.native, self.run, MATERIAL_NAME)
        self.assertEqual(self.native.writes, [])


if __name__ == "__main__":
    unittest.main()
