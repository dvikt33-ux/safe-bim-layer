"""Synthetic reproduction of reported AC29 +3m slab-placement defect and repair.

Uses existing tests' exact native-shaped 20+5+3 scene and immutable ledger,
does not connect to real Archicad, and never reruns an old reservation.
"""
import sqlite3
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import continue_apa_after_story_z as THIRD
import repair_apa_suffix3_slab as REPAIR2
from test_archicad_after_story_z import AfterStoryZRecoveryTests
from test_archicad_basic_slab_integration import MATERIAL_NAME


class Suffix3SlabRepairTests(unittest.TestCase):
    def setUp(self):
        AfterStoryZRecoveryTests.setUp(self)
        self.api = self.bad_slab_api
        proposal = THIRD.proof(self.api, MATERIAL_NAME)
        stopped = THIRD.execute(self.api, MATERIAL_NAME, proposal["token"])
        self.assertEqual(stopped["status"], "PARTIAL_OR_UNKNOWN_OUTCOME", stopped)
        self.assertEqual(stopped["failedStep"], "s2-slab")
        self.assertEqual(len(self.native.created), 12)
        self.native.writes.clear()

    def bad_slab_api(self, command, params):
        reply = self.native(command, params)
        if (command == "CreateSlabs"
                and params["slabsData"][0]["floorIndex"] == 1):
            # The regression is pinned to the exact owner-provided live GUID.
            synthetic_guid = reply["elements"][0]["elementId"]["guid"]
            self.native.created[REPAIR2.TARGET_GUID] = self.native.created.pop(
                synthetic_guid)
            reply["elements"][0]["elementId"]["guid"] = REPAIR2.TARGET_GUID
        if command == "GetDetailsOfElements":
            guid = params["elements"][0]["elementId"]["guid"]
            element = self.native.created.get(guid)
            if (element and element[0] == "CreateSlabs"
                    and element[1]["slabsData"][0]["floorIndex"] == 1):
                row = reply["detailsOfElements"][0]["details"]
                if guid in self.native.modified:
                    row["level"] = 0.0
                    row["zCoordinate"] = 3.0
                else:
                    row["level"] = -3.0
                    row["zCoordinate"] = 0.0
        return reply

    def test_read_only_preflight_reconstructs_exact_32_guids(self):
        proposal = REPAIR2.preflight(self.api, MATERIAL_NAME)
        self.assertEqual(proposal["status"], "READY_FOR_EXPLICIT_SINGLE_S2_SLAB_REPAIR")
        self.assertEqual(proposal["modelWriteAttempts"], 0)
        self.assertEqual(proposal["nativeCurrentZ"], 0.0)
        self.assertEqual(proposal["targetStoryLevel"], 3.0)
        self.assertEqual(self.native.writes, [])
        with sqlite3.connect(self.journal) as db:
            self.assertIsNone(db.execute(
                "SELECT name FROM sqlite_master WHERE name=?",
                (REPAIR2.REPAIR_TABLE,)).fetchone())

    def test_one_modify_corrects_absolute_z_basic_and_material(self):
        token = REPAIR2.preflight(self.api, MATERIAL_NAME)["token"]
        success = REPAIR2.execute(self.api, MATERIAL_NAME, token)
        self.assertEqual(success["status"], "S2_SLAB_REPAIRED_VERIFIED_UNSAVED", success)
        self.assertEqual(success["zCoordinate"], 3.0)
        self.assertEqual(success["localLevel"], 0.0)
        self.assertEqual(success["thickness"], .2)
        self.assertEqual(self.native.writes, ["ModifySlabs"])
        self.assertEqual(len(self.native.created), 12)
        self.assertIn("zCoordinate", self.native.modified[REPAIR2.TARGET_GUID])
        with sqlite3.connect(self.journal) as db:
            state = db.execute(
                "SELECT state FROM apa_suffix3_slab_repairs").fetchone()
            self.assertEqual(state[0], "READBACK_PASS")
        with self.assertRaisesRegex(ValueError, "ALREADY_RESERVED"):
            REPAIR2.preflight(self.api, MATERIAL_NAME)
        self.assertEqual(self.native.writes, ["ModifySlabs"])

    def test_invalid_token_blocks_before_write(self):
        with self.assertRaisesRegex(ValueError, "TOKEN_REQUIRED"):
            REPAIR2.execute(self.api, MATERIAL_NAME, "wrong")
        self.assertEqual(self.native.writes, [])

    def test_modify_timeout_is_never_replayed(self):
        token = REPAIR2.preflight(self.api, MATERIAL_NAME)["token"]
        self.native.modify_timeout = True
        result = REPAIR2.execute(self.api, MATERIAL_NAME, token)
        self.assertEqual(result["status"], "SUFFIX3_REPAIR_UNKNOWN_NO_RETRY")
        self.assertEqual(self.native.writes, ["ModifySlabs"])
        with self.assertRaisesRegex(ValueError, "ALREADY_RESERVED"):
            REPAIR2.preflight(self.api, MATERIAL_NAME)

    def test_inventory_drift_refuses_without_write(self):
        import uuid
        self.native.existing.append(str(uuid.uuid4()))
        with self.assertRaisesRegex(ValueError, "GUIDS_NOT_EXACT_JOURNAL"):
            REPAIR2.preflight(self.api, MATERIAL_NAME)
        self.assertFalse(self.native.writes)

    def test_no_effect_modify_is_not_success(self):
        token = REPAIR2.preflight(self.api, MATERIAL_NAME)["token"]
        self.native.modify_noop = True
        result = REPAIR2.execute(self.api, MATERIAL_NAME, token)
        self.assertEqual(result["status"], "SUFFIX3_REPAIR_UNKNOWN_NO_RETRY")
        self.assertIn("FINAL_TYPED_READBACK_MISMATCH", result["reason"])
        self.assertEqual(self.native.writes, ["ModifySlabs"])


if __name__ == "__main__":
    unittest.main()
