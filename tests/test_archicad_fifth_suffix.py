"""One-shot fifth suffix 13 existing + 12 creates, synthetic offline only."""
from contextlib import redirect_stdout
import io
from pathlib import Path
import sys
import unittest
import uuid
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))

import archicad_scene_run as RUN
import continue_apa_after_orphan_partition as FIFTH
import continue_apa_after_s2_slab as FOURTH
from test_archicad_orphan_s2_partition import OrphanS2WallDiagnosisTests
from test_archicad_basic_slab_integration import MATERIAL_NAME


class FifthSuffixTests(unittest.TestCase):
    bad_slab_api = OrphanS2WallDiagnosisTests.bad_slab_api
    read_api = OrphanS2WallDiagnosisTests.read_api

    def setUp(self):
        OrphanS2WallDiagnosisTests.setUp(self)
        old_guid=next(reversed(self.native.created))
        self.native.created[FIFTH.VERIFIED_ORPHAN_GUID]=self.native.created.pop(old_guid)
        # Synthetic source tokens differ from the exact pinned live token.
        # Patch only the offline fixture, never loosen the live file guard.
        token_patch=patch.object(
            FIFTH,"APPROVED_FOURTH_PLAN_HASH",self.stopped["planHash"])
        token_patch.start()
        self.addCleanup(token_patch.stop)
        self.before_writes=len(self.native.writes)

    def test_read_only_13_prefix_and_12_new_steps(self):
        t=FIFTH.proof(self.read_api,MATERIAL_NAME)
        self.assertEqual(t["status"],"READY_FOR_EXPLICIT_TWELVE_STEP_CONTINUATION")
        self.assertEqual(t["reusedCount"],13)
        self.assertEqual(t["remainingCount"],12)
        self.assertEqual(t["maxCreateTimeoutSeconds"],120)
        self.assertEqual(t["modelWriteAttempts"],0)
        self.assertEqual(len(t["before"]),33)
        self.assertEqual(len(t["reused"]),13)
        self.assertEqual(t["reused"]["s2-partition-1"]["guid"],
                         FIFTH.VERIFIED_ORPHAN_GUID)
        self.assertEqual(len(self.native.writes),self.before_writes)

    def test_full_12_creates_result_45_all_typed_readbacks(self):
        ticket=FIFTH.proof(self.read_api,MATERIAL_NAME)
        result=FIFTH.execute(self.read_api,MATERIAL_NAME,ticket["token"])
        self.assertEqual(result["status"],"COMPLETE_UNSAVED",result)
        self.assertEqual(result["newCreatedCount"],12)
        self.assertEqual(result["reusedCount"],13)
        self.assertTrue(result["allGuidsReadback"])
        self.assertFalse(result["plnSaved"])
        self.assertEqual(len(self.native.created),25)
        self.assertEqual(len(self.native.writes),self.before_writes+12)
        self.assertTrue(all(x.startswith("Create") for x in
                            self.native.writes[self.before_writes:]))
        with self.assertRaisesRegex(ValueError,"FIFTH_SCENE_ALREADY_RESERVED"):
            FIFTH.proof(self.read_api,MATERIAL_NAME)

    def test_fail_closed_on_wrong_token_or_guid_drift(self):
        with self.assertRaisesRegex(ValueError,"EXPLICIT_TWELVE_STEP_TOKEN_MISMATCH"):
            FIFTH.execute(self.read_api,MATERIAL_NAME,"not-the-token")
        self.assertEqual(len(self.native.writes),self.before_writes)
        self.native.existing.append(str(uuid.uuid4()))
        with self.assertRaisesRegex(ValueError,"NATIVE_NOT_EXACTLY_32_PLUS_ONE_UNJOURNALED"):
            FIFTH.proof(self.read_api,MATERIAL_NAME)
        self.assertEqual(len(self.native.writes),self.before_writes)

    def test_partial_timeout_does_not_replay(self):
        ticket=FIFTH.proof(self.read_api,MATERIAL_NAME)
        self.native.fail_at="CreateWindows"
        out=FIFTH.execute(self.read_api,MATERIAL_NAME,ticket["token"])
        self.assertEqual(out["status"],"PARTIAL_OR_UNKNOWN_OUTCOME",out)
        count=len(self.native.writes)
        with self.assertRaisesRegex(ValueError,"FIFTH_SCENE_ALREADY_RESERVED"):
            FIFTH.proof(self.read_api,MATERIAL_NAME)
        self.assertEqual(len(self.native.writes),count)

    def test_transport_allows_120_only_for_native_creates(self):
        ticket=FIFTH.proof(self.read_api,MATERIAL_NAME)
        events=[]
        def transport(port,cmd,params=None,*,timeout=15):
            self.assertEqual(port,19726)
            events.append((cmd,timeout))
            return self.read_api(cmd,params or {})
        with patch.object(RUN,"tapir",side_effect=transport):
            with redirect_stdout(io.StringIO()) as s:
                rc=FIFTH.main(["--port","19726","--material",MATERIAL_NAME,
                               "--confirm-token",ticket["token"]])
        self.assertEqual(rc,0,s.getvalue())
        created=[limit for cmd,limit in events if cmd.startswith("Create")]
        self.assertEqual(len(created),12)
        self.assertEqual(set(created),{120})
        self.assertEqual({lim for cmd,lim in events if not cmd.startswith("Create")},
                         {15})
        self.assertEqual(len(self.native.writes),self.before_writes+12)


if __name__=="__main__":
    unittest.main()
