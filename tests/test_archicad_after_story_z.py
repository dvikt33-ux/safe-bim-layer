"""AC29 observed +3m native wall Z: resume 8 known GUIDs and create 17 only."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import continue_apa_partial_scene as CONT
import continue_apa_after_story_z as AFTER
from test_archicad_basic_slab_integration import MATERIAL_NAME
from test_archicad_partial_scene_continuation import PartialSceneContinuationTests


class AfterStoryZRecoveryTests(unittest.TestCase):
    def setUp(self):
        # Reuse the source-tested 20+5 fixture, including the committed repair.
        PartialSceneContinuationTests.setUp(self)
        old_token = CONT.proof(self.native, MATERIAL_NAME)["token"]
        self.partial_readback = self.native

        def false_second_story_readback(command, params):
            reply = self.native(command, params)
            if command == "GetDetailsOfElements":
                guid = params["elements"][0]["elementId"]["guid"]
                row = self.native.created.get(guid)
                if (row and row[0] == "CreateWalls"
                        and row[1]["wallsData"][0]["floorIndex"] == 1):
                    reply["detailsOfElements"][0]["details"]["zCoordinate"] = 4.0
            return reply

        self.drift_readback = false_second_story_readback
        stopped = CONT.continue_scene(false_second_story_readback,
                                      MATERIAL_NAME, old_token)
        self.assertEqual(stopped["status"], "PARTIAL_OR_UNKNOWN_OUTCOME", stopped)
        self.assertEqual(stopped["failedStep"], "s2-wall-south")
        self.assertEqual(len(self.native.created), 8)
        self.assertEqual(self.native.writes.count("CreateWalls"), 3)

    def test_exact_read_only_eight_existing_and_seventeen_remaining(self):
        before = len(self.native.writes)
        proposal = AFTER.proof(self.native, MATERIAL_NAME)
        self.assertEqual(proposal["status"],
                         "READY_FOR_EXPLICIT_SEVENTEEN_STEP_CONTINUATION")
        self.assertEqual(proposal["reusedCount"], 8)
        self.assertEqual(proposal["remainingCount"], 17)
        self.assertEqual(proposal["modelWriteAttempts"], 0)
        self.assertEqual(len(self.native.writes), before)

    def test_resume_17_only_with_journal_and_complete_25_readbacks(self):
        token = AFTER.proof(self.native, MATERIAL_NAME)["token"]
        out = AFTER.execute(self.native, MATERIAL_NAME, token)
        self.assertEqual(out["status"], "COMPLETE_UNSAVED", out)
        self.assertTrue(out["allGuidsReadback"])
        self.assertEqual(out["newCreatedCount"], 17)
        self.assertEqual(out["reusedCount"], 8)
        self.assertEqual(len(self.native.created), 25)
        self.assertEqual(len(self.native.writes), 21)  # suffix 3+third 17 creates+1 ModifySlabs
        self.assertEqual(self.native.writes.count("ModifySlabs"), 1)
        self.assertEqual(sum(x.startswith("Create") for x in self.native.writes), 20)
        before = len(self.native.writes)
        with self.assertRaisesRegex(ValueError, "THIRD_SCENE_ALREADY_RESERVED"):
            AFTER.proof(self.native, MATERIAL_NAME)
        self.assertEqual(len(self.native.writes), before)

    def test_wrong_token_and_live_z_drift_refuse_without_creates(self):
        before = len(self.native.writes)
        with self.assertRaisesRegex(ValueError, "APPROVAL_TOKEN_MISMATCH"):
            AFTER.execute(self.native, MATERIAL_NAME, "wrong")
        self.assertEqual(len(self.native.writes), before)
        with self.assertRaisesRegex(ValueError, "WALL_STORY_Z_READBACK_MISMATCH"):
            AFTER.proof(self.drift_readback, MATERIAL_NAME)
        self.assertEqual(len(self.native.writes), before)

    def test_second_story_slab_read_only_diagnosis_preserves_third_ledger(self):
        import diagnose_apa_suffix3_slab_readback as DIAG
        token = AFTER.proof(self.native, MATERIAL_NAME)["token"]

        def absolute_slab_level_from_native(command, params):
            reply = self.native(command, params)
            if command == "GetDetailsOfElements":
                guid = params["elements"][0]["elementId"]["guid"]
                entry = self.native.created.get(guid)
                if (entry and entry[0] == "CreateSlabs"
                        and entry[1]["slabsData"][0]["floorIndex"] == 1):
                    reply["detailsOfElements"][0]["details"]["level"] = 3.0
                    reply["detailsOfElements"][0]["details"]["zCoordinate"] = 3.0
            return reply

        failed = AFTER.execute(absolute_slab_level_from_native,
                               MATERIAL_NAME, token)
        self.assertEqual(failed["status"], "PARTIAL_OR_UNKNOWN_OUTCOME")
        self.assertEqual(failed["failedStep"], "s2-slab")
        count = len(self.native.writes)
        report = DIAG.collect(absolute_slab_level_from_native)
        self.assertEqual(report["status"], "READ_ONLY_THIRD_SUFFIX_SLAB_DIAGNOSIS")
        self.assertEqual(report["failedSlab"]["journalState"], "CREATED_UNVERIFIED")
        self.assertEqual(report["inventory"]["missingPreviouslyVerifiedGuids"], [])
        self.assertEqual(report["inventory"]["nativeGuidsNotInThirdJournal"], [])
        self.assertEqual(report["inventory"]["journaledGuidsAbsentFromModel"], [])
        level = report["failedSlab"]["fieldComparison"]["level"]
        self.assertEqual(level["requestedLocal"], 0.0)
        self.assertEqual(level["requestedPlusStory"], 3.0)
        self.assertEqual(level["native"], 3.0)
        self.assertFalse(level["matchesLocal"])
        self.assertTrue(level["matchesAbsolute"])
        self.assertEqual(len(self.native.writes), count)

    def test_extra_live_guid_fails_closed(self):
        import uuid
        self.native.existing.append(str(uuid.uuid4()))
        before = len(self.native.writes)
        with self.assertRaisesRegex(ValueError, "INVENTORY_DRIFT"):
            AFTER.proof(self.native, MATERIAL_NAME)
        self.assertEqual(len(self.native.writes), before)


if __name__ == "__main__":
    unittest.main()
