"""Offline only: read-only fourth suffix timeout; no duplicate native writes."""
from pathlib import Path
import sqlite3
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import diagnose_apa_suffix4_timeout as DIAG
import continue_apa_after_s2_slab as FOURTH
from test_archicad_fourth_suffix import FourthSuffixTests
from test_archicad_basic_slab_integration import MATERIAL_NAME


class FourthTimeoutDiagnosisTests(FourthSuffixTests):
    def test_before_reserved_scene_no_restart_inference(self):
        count = len(self.native.writes)
        d, plan = DIAG.read_journal()
        self.assertEqual(d["status"], "READ_ONLY_FOURTH_SUFFIX_JOURNAL")
        self.assertFalse(d["fourthSceneReserved"])
        self.assertEqual(d["fourthJournal"], [])
        self.assertEqual(d["previousBaselineCount"], 32)
        self.assertEqual(len(d["plannedRemainingStepIds"]), 13)
        self.assertEqual(len(self.native.writes), count)
        DIAG.read_native(self.read_api, d, plan)
        self.assertEqual(d["native"]["total"], 32)
        self.assertEqual(d["native"]["newGuidCount"], 0)
        self.assertTrue(d["native"]["modelMatchesRecordedGuids"])
        self.assertEqual(len(self.native.writes), count)

    def test_completed_scene_is_reported_not_replayed(self):
        token = FOURTH.proof(self.read_api, MATERIAL_NAME)["token"]
        completed = FOURTH.execute(self.read_api, MATERIAL_NAME, token)
        self.assertEqual(completed["status"], "COMPLETE_UNSAVED")
        count = len(self.native.writes)
        d, plan = DIAG.read_journal()
        self.assertTrue(d["fourthSceneReserved"])
        self.assertEqual(d["fourthSceneState"], "COMPLETE_UNSAVED")
        self.assertEqual(len(d["fourthJournal"]), 13)
        self.assertEqual(d["journaledNewCount"], 13)
        DIAG.read_native(self.read_api, d, plan)
        self.assertEqual(d["native"]["total"], 45)
        self.assertEqual(d["native"]["newGuidCount"], 13)
        self.assertEqual(d["native"]["missingOriginal32"], [])
        self.assertTrue(d["native"]["modelMatchesRecordedGuids"])
        self.assertEqual(len(self.native.writes), count)

    def test_ambiguous_native_timeout_must_not_be_restarted(self):
        self.native.fail_at = "CreateWindows"
        token = FOURTH.proof(self.read_api, MATERIAL_NAME)["token"]
        result = FOURTH.execute(self.read_api, MATERIAL_NAME, token)
        self.assertEqual(result["status"], "PARTIAL_OR_UNKNOWN_OUTCOME")
        count = len(self.native.writes)
        d, plan = DIAG.read_journal()
        self.assertTrue(d["fourthSceneReserved"])
        self.assertEqual(d["fourthSceneState"], "PARTIAL_OR_UNKNOWN_OUTCOME")
        self.assertTrue(d["ambiguousWithoutGuid"])
        DIAG.read_native(self.read_api, d, plan)
        self.assertTrue(d["native"]["modelMatchesRecordedGuids"])
        self.assertEqual(len(self.native.writes), count)
        with self.assertRaisesRegex(ValueError, "FOURTH_SCENE_ALREADY_RESERVED"):
            FOURTH.proof(self.read_api, MATERIAL_NAME)

    def test_journal_only_works_even_when_native_times_out(self):
        d, plan = DIAG.read_journal()
        count = len(self.native.writes)
        def timed_out(_command, _params):
            raise TimeoutError("unreachable local Archicad")
        with self.assertRaises(TimeoutError):
            DIAG.read_native(timed_out, d, plan)
        self.assertEqual(d["fourthSceneReserved"], False)
        self.assertEqual(len(self.native.writes), count)

    def test_wrong_project_blocks_native_details(self):
        d, plan = DIAG.read_journal()
        self.native.wrong_project = True
        with self.assertRaisesRegex(ValueError, "NOT_THE_APPROVED_SCRATCH_PROJECT"):
            DIAG.read_native(self.read_api, d, plan)
        self.assertNotIn("native", d)

    def test_duplicate_readonly_has_zero_mutation(self):
        count = len(self.native.writes)
        for _ in range(3):
            with patch.object(DIAG.REPAIR, "EVIDENCE", self.run):
                report, _ = DIAG.read_journal()
                self.assertEqual(report["nativeWriteCalls"], 0)
        self.assertEqual(len(self.native.writes), count)


if __name__ == "__main__":
    unittest.main()
