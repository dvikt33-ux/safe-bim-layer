"""Synthetic read-only evidence proof + exact 20-operation suffix continuation.

Tests the existing SceneWriter, not a new duplicate native execution mechanism.
Never connects to actual user's Windows PLN.
"""
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
import uuid
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import archicad_scene_run as RUN
import archicad_building_shell as BUILD
import continue_apa_partial_scene as CONT
import repair_apa_partial_slab as REPAIR
from test_archicad_basic_slab_integration import CompositeDefaultNative, MATERIAL_NAME


class ScratchCompositeNative(CompositeDefaultNative):
    def __call__(self, command, params):
        if command == "GetStories":
            self.calls.append(command)
            return {"actStory": 0, "stories": [
                {"index": 0, "floorId": 1, "level": 0.0, "name": "Первый Этаж"},
                {"index": 1, "floorId": 2, "level": 3.0, "name": ""},
                {"index": 2, "floorId": 3, "level": 6.0, "name": ""}]}
        return super().__call__(command, params)


class PartialSceneContinuationTests(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.root = Path(t.name)
        self.run = self.root / "20261011-031123-7181b47c"
        self.out = self.run / "execute"
        self.out.mkdir(parents=True)
        self.journal = self.root / "persistent-ledger" / "scene-v1-attempts.sqlite3"
        self.journal.parent.mkdir()
        self.native = ScratchCompositeNative()
        self.native.existing = [
            str(uuid.uuid5(uuid.NAMESPACE_DNS, "existing-"+str(i)))
            for i in range(20)]
        self.scene_id = "apa-house-20261011-031123-7181b47c"
        self.old_hash = "a" * 64
        intent = json.loads(CONT.ORIGINAL_INTENT.read_text(encoding="utf-8"))
        self.plan = BUILD.prepare(intent["components"][0])
        self.steps = {s["id"]: s for s in self.plan["graph"]["operations"]}
        self.guids = {}
        for sid in CONT.FIRST:
            s = self.steps[sid]
            guid = (REPAIR.SLAB_GUID if sid == REPAIR.FAILED_STEP else
                    str(uuid.uuid5(uuid.NAMESPACE_DNS, "partial-"+sid)))
            self.native.created[guid] = (s["command"], s["params"])
            self.guids[sid] = guid
        (self.out / "result.json").write_text(json.dumps({
            "status": "PARTIAL_OR_UNKNOWN_OUTCOME",
            "scene": {"failedStep": "s1-slab", "sceneId": self.scene_id,
                      "planHash": self.old_hash}
        }), encoding="utf-8")
        (self.out / "plan.json").write_text(
            json.dumps(self.plan, ensure_ascii=False), encoding="utf-8")
        (self.out / "inventory-before.json").write_text(
            json.dumps(self.native.existing), encoding="utf-8")
        manifest = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in self.out.iterdir() if p.is_file()}
        (self.out / "SHA256.json").write_text(json.dumps(manifest), encoding="utf-8")
        with sqlite3.connect(self.journal) as db:
            db.execute("CREATE TABLE scenes (scene_id TEXT PRIMARY KEY,plan_hash TEXT NOT NULL,"
                       "state TEXT NOT NULL,result TEXT NOT NULL)")
            db.execute("CREATE TABLE steps (scene_id TEXT NOT NULL,step_id TEXT NOT NULL,"
                       "state TEXT NOT NULL,guid TEXT,output TEXT NOT NULL,"
                       "PRIMARY KEY(scene_id,step_id))")
            db.execute("INSERT INTO scenes VALUES (?,?,?,?)", (
                self.scene_id, self.old_hash, "PARTIAL_OR_UNKNOWN_OUTCOME", "{}"))
            for sid, guid in self.guids.items():
                db.execute("INSERT INTO steps VALUES (?,?,?,?,?)", (
                    self.scene_id, sid,
                    "CREATED_UNVERIFIED" if sid == REPAIR.FAILED_STEP else "PASS",
                    guid, "{}"))
        self.patcher = patch.object(REPAIR, "EVIDENCE", self.run)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)
        self.target = patch.multiple(
            RUN, EXPECTED_NAME="APA_Test_House_01",
            EXPECTED_PATH=RUN.APPROVED_SCRATCH_PATH, PORT=19726)
        self.target.start()
        self.addCleanup(self.target.stop)
        first = REPAIR.preflight(self.native, self.run, MATERIAL_NAME)
        repaired = REPAIR.repair(self.native, self.run, MATERIAL_NAME, first["token"])
        self.assertEqual(repaired["status"], "SINGLE_SLAB_REPAIR_VERIFIED_UNSAVED")
        self.native.writes.clear()

    def test_twenty_suffix_creates_only_and_checks_all_25(self):
        p = CONT.proof(self.native, MATERIAL_NAME)
        self.assertEqual(p["status"], "READY_FOR_EXPLICIT_TWENTY_STEP_CONTINUATION")
        self.assertEqual(p["remainingCount"], 20)
        self.assertFalse(self.native.writes)
        answer = CONT.continue_scene(self.native, MATERIAL_NAME, p["token"])
        self.assertEqual(answer["status"], "COMPLETE_UNSAVED", answer)
        self.assertEqual(answer["reusedCount"], 5)
        self.assertEqual(answer["newCreatedCount"], 20)
        self.assertEqual(len(self.native.created), 25)
        self.assertEqual(len(self.native.writes), 21)  # 20 Creates + 1 ModifySlabs
        self.assertEqual(self.native.writes.count("ModifySlabs"), 1)
        self.assertEqual(len([x for x in self.native.writes if x.startswith("Create")]), 20)
        with sqlite3.connect(self.journal) as db:
            count = db.execute(
                "SELECT COUNT(*) FROM steps WHERE scene_id=? AND state='PASS'",
                (CONT.SUFFIX_ID,)).fetchone()[0]
            self.assertEqual(count, 20)
            self.assertEqual(db.execute(
                "SELECT state FROM steps WHERE scene_id=? AND step_id='s1-slab'",
                (self.scene_id,)).fetchone()[0], "CREATED_UNVERIFIED")

    def test_wrong_token_blocks_before_new_mutation(self):
        with self.assertRaisesRegex(ValueError, "TOKEN_MISMATCH"):
            CONT.continue_scene(self.native, MATERIAL_NAME, "bad")
        self.assertEqual(self.native.writes, [])

    def test_unknown_outcome_reserves_scene_never_retries(self):
        token = CONT.proof(self.native, MATERIAL_NAME)["token"]
        self.native.fail_at = "CreateDoors"
        first = CONT.continue_scene(self.native, MATERIAL_NAME, token)
        self.assertEqual(first["status"], "PARTIAL_OR_UNKNOWN_OUTCOME")
        count = len(self.native.writes)
        with self.assertRaisesRegex(ValueError, "SUFFIX_ALREADY_RESERVED"):
            CONT.continue_scene(self.native, MATERIAL_NAME, token)
        self.assertEqual(len(self.native.writes), count)

    def test_second_story_wall_mismatch_is_read_only_diagnosed_from_guid(self):
        import diagnose_apa_suffix_wall_readback as DIAG

        token = CONT.proof(self.native, MATERIAL_NAME)["token"]

        def shifted_second_story_readback(command, params):
            response = self.native(command, params)
            if command == "GetDetailsOfElements":
                guid = params["elements"][0]["elementId"]["guid"]
                created = self.native.created.get(guid)
                if (created and created[0] == "CreateWalls"
                        and created[1]["wallsData"][0]["floorIndex"] == 1):
                    response["detailsOfElements"][0]["details"]["zCoordinate"] = 3.0
            return response

        result = CONT.continue_scene(shifted_second_story_readback,
                                     MATERIAL_NAME, token)
        self.assertEqual(result["status"], "PARTIAL_OR_UNKNOWN_OUTCOME")
        self.assertEqual(result["failedStep"], "s2-wall-south")
        prior_writes = len(self.native.writes)
        info = DIAG.collect(shifted_second_story_readback)
        self.assertEqual(info["status"], "READ_ONLY_SUFFIX_DIAGNOSIS")
        self.assertEqual(info["failedStep"], "s2-wall-south")
        self.assertEqual(info["nativeInventory"]["missingFromOriginal25"], [])
        self.assertEqual(info["nativeInventory"]["suffixGuidCount"], 11)
        self.assertEqual(info["nativeInventory"]["nativeGuidsAbsentFromSuffixJournal"], [])
        self.assertEqual(info["failedWall"]["nativeFloorIndex"], 1)
        z = info["failedWall"]["fieldComparison"]["zCoordinate"]
        self.assertEqual(z["requested"], 0.0)
        self.assertEqual(z["native"], 3.0)
        self.assertFalse(z["matches"])
        self.assertEqual(len(self.native.writes), prior_writes)

    def test_unexpected_new_guid_blocks_before_write(self):
        self.native.existing.append(str(uuid.uuid4()))
        with self.assertRaisesRegex(ValueError, "BASELINE_DRIFT"):
            CONT.proof(self.native, MATERIAL_NAME)
        self.assertEqual(self.native.writes, [])

    def test_modified_persisted_evidence_blocks_before_write(self):
        with (self.out / "plan.json").open("a", encoding="utf-8") as f:
            f.write(" ")
        with self.assertRaisesRegex(ValueError, "SHA256_MISMATCH"):
            CONT.proof(self.native, MATERIAL_NAME)
        self.assertEqual(self.native.writes, [])


if __name__ == "__main__":
    unittest.main()
