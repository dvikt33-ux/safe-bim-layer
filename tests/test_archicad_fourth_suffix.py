"""12 verified GUIDs + one-shot 13 remaining native creates (synthetic only)."""
import sqlite3
from pathlib import Path
import sys
import unittest
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import continue_apa_after_s2_slab as FINAL
import repair_apa_suffix3_slab as REPAIR
from test_archicad_suffix3_slab_repair import Suffix3SlabRepairTests
from test_archicad_basic_slab_integration import MATERIAL_NAME


class FourthSuffixTests(unittest.TestCase):
    def setUp(self):
        Suffix3SlabRepairTests.setUp(self)
        ticket = REPAIR.preflight(self.api, MATERIAL_NAME)
        out = REPAIR.execute(self.api, MATERIAL_NAME, ticket["token"])
        self.assertEqual(out["status"], "S2_SLAB_REPAIRED_VERIFIED_UNSAVED", out)
        self.native.writes.clear()

    def read_api(self, cmd, params):
        result = self.bad_slab_api(cmd, params)
        if cmd == "GetDetailsOfElements":
            guid = params["elements"][0]["elementId"]["guid"]
            saved = self.native.created.get(guid)
            if (saved and saved[0] == "CreateSlabs"
                    and saved[1]["slabsData"][0]["floorIndex"] == 0):
                result["detailsOfElements"][0]["details"]["zCoordinate"] = 0.0
        return result

    def test_read_only_ticket_exact_12_plus_13(self):
        before = len(self.native.writes)
        ticket = FINAL.proof(self.read_api, MATERIAL_NAME)
        self.assertEqual(ticket["status"], "READY_FOR_EXPLICIT_THIRTEEN_STEP_CONTINUATION")
        self.assertEqual(ticket["reusedCount"], 12)
        self.assertEqual(ticket["remainingCount"], 13)
        self.assertEqual(ticket["modelWriteAttempts"], 0)
        self.assertEqual(len(ticket["reused"]), 12)
        self.assertEqual(len(self.native.writes), before)

    def test_full_thirteen_creates_whole_25_readback_and_no_retry(self):
        token = FINAL.proof(self.read_api, MATERIAL_NAME)["token"]
        out = FINAL.execute(self.read_api, MATERIAL_NAME, token)
        self.assertEqual(out["status"], "COMPLETE_UNSAVED", out)
        self.assertTrue(out["allGuidsReadback"])
        self.assertEqual(out["reusedCount"], 12)
        self.assertEqual(out["newCreatedCount"], 13)
        self.assertEqual(len(self.native.created), 25)
        self.assertEqual(len(self.native.writes), 13)
        self.assertFalse(out["plnSaved"])
        with sqlite3.connect(self.journal) as db:
            self.assertEqual(db.execute(
                "SELECT COUNT(*) FROM steps WHERE scene_id=? AND state='PASS'",
                (FINAL.FOURTH_SCENE_ID,)).fetchone()[0], 13)
        with self.assertRaisesRegex(ValueError, "FOURTH_SCENE_ALREADY_RESERVED"):
            FINAL.proof(self.read_api, MATERIAL_NAME)

    def test_bad_token_and_inventory_change_block_before_any_write(self):
        with self.assertRaisesRegex(ValueError, "THIRTEEN_STEP_TOKEN_MISMATCH"):
            FINAL.execute(self.read_api, MATERIAL_NAME, "invalid")
        self.assertFalse(self.native.writes)
        self.native.existing.append(str(uuid.uuid4()))
        with self.assertRaisesRegex(ValueError, "NATIVE_32_GUIDS_NOT_EXACT_HISTORY"):
            FINAL.proof(self.read_api, MATERIAL_NAME)
        self.assertFalse(self.native.writes)

    def test_changed_s2_slab_z_fails_preflight_without_mutation(self):
        def drift(cmd,params):
            result = self.read_api(cmd,params)
            if cmd=="GetDetailsOfElements":
                guid=params["elements"][0]["elementId"]["guid"]
                if guid == REPAIR.TARGET_GUID:
                    result["detailsOfElements"][0]["details"]["zCoordinate"]=0.0
            return result
        with self.assertRaisesRegex(ValueError, "REPAIRED_SLAB_GLOBAL_Z_OR_LEVEL_DRIFT"):
            FINAL.proof(drift,MATERIAL_NAME)
        self.assertFalse(self.native.writes)

    def test_partial_fourth_suffix_cannot_be_restarted(self):
        token = FINAL.proof(self.read_api, MATERIAL_NAME)["token"]
        self.native.fail_at = "CreateWindows"
        out = FINAL.execute(self.read_api, MATERIAL_NAME, token)
        self.assertEqual(out["status"], "PARTIAL_OR_UNKNOWN_OUTCOME")
        count = len(self.native.writes)
        with self.assertRaisesRegex(ValueError, "FOURTH_SCENE_ALREADY_RESERVED"):
            FINAL.proof(self.read_api, MATERIAL_NAME)
        self.assertEqual(len(self.native.writes), count)


if __name__ == "__main__":
    unittest.main()
