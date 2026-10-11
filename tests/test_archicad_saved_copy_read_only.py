"""Synthetic independent verification of manually reopened saved Unicode PLN.

No test opens/saves/mutates a real file or Archicad.
"""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import continue_apa_after_orphan_partition as FIFTH
import verify_apa_saved_copy_read_only as SAVED
from test_archicad_fifth_suffix import FifthSuffixTests
from test_archicad_basic_slab_integration import MATERIAL_NAME


class SavedCopyReadonlyTests(unittest.TestCase):
    bad_slab_api = FifthSuffixTests.bad_slab_api
    read_api = FifthSuffixTests.read_api

    def setUp(self):
        FifthSuffixTests.setUp(self)
        ticket=FIFTH.proof(self.read_api,MATERIAL_NAME)
        result=FIFTH.execute(self.read_api,MATERIAL_NAME,ticket["token"])
        self.assertEqual(result["status"],"COMPLETE_UNSAVED",result)
        self.initial_write_count=len(self.native.writes)
        self.filepatch=patch.object(SAVED.os.path,"isfile",return_value=True)
        self.sizepatch=patch.object(SAVED.os.path,"getsize",return_value=100000)
        self.filepatch.start()
        self.sizepatch.start()
        self.addCleanup(self.filepatch.stop)
        self.addCleanup(self.sizepatch.stop)

    def copy_api(self,cmd,params):
        if cmd=="GetProjectInfo":
            return {"projectName":SAVED.EXPECTED_COPY_NAME,
                    "projectPath":SAVED.COPY_PATH,
                    "isUntitled":False,"isTeamwork":False}
        return self.read_api(cmd,params)

    def test_new_copy_full_model_45_guids_25_native_elements(self):
        result=SAVED.verify_copy(self.copy_api)
        self.assertEqual(result["status"],"OPEN_SAVED_COPY_TYPED_READBACK_PASS")
        self.assertEqual(result["actualTotalGuids"],45)
        self.assertEqual(result["plannedBuildingElementsVerified"],25)
        self.assertEqual(result["plannedBuildingKinds"],{
            "Wall":12,"Slab":2,"Door":5,"Window":6})
        self.assertEqual(sum(result["plannedElementsByNativeStory"].values()),25)
        self.assertEqual(result["nativeWriteCalls"],0)
        self.assertTrue(result["hostedOpeningGuidsVerified"])
        self.assertTrue(result["original20GuidsPreserved"])
        self.assertEqual(result["savedCopyWasManuallyReopened"],
                         "USER_CONFIRMATION_REQUIRED")
        self.assertEqual(len(self.native.writes),self.initial_write_count)

    def test_guard_refuses_old_scratch_pln(self):
        with self.assertRaisesRegex(ValueError,"WRONG_OPEN_PROJECT"):
            SAVED.verify_copy(self.read_api)
        self.assertEqual(len(self.native.writes),self.initial_write_count)

    def test_guard_refuses_unexpected_copy_path(self):
        def other_copy(cmd,params):
            if cmd=="GetProjectInfo":
                row=dict(self.copy_api(cmd,params))
                row["projectPath"]=SAVED.COPY_PATH+".bak"
                return row
            return self.copy_api(cmd,params)
        with self.assertRaisesRegex(ValueError,"WRONG_OPEN_PROJECT"):
            SAVED.verify_copy(other_copy)
        self.assertEqual(len(self.native.writes),self.initial_write_count)

    def test_disappearing_native_guid_fails_closed(self):
        guid=next(iter(self.native.created))
        self.native.created.pop(guid)
        with self.assertRaisesRegex(ValueError,"SAVED_COPY_45_GUIDS"):
            SAVED.verify_copy(self.copy_api)
        self.assertEqual(len(self.native.writes),self.initial_write_count)

    def test_wrong_second_storey_slab_z_fails_closed(self):
        def broken_slab(cmd,params):
            row=self.copy_api(cmd,params)
            if cmd=="GetDetailsOfElements":
                guid=params["elements"][0]["elementId"]["guid"]
                if guid.lower()=="1020bdf5-afec-455e-bab9-d17999ac1567":
                    row["detailsOfElements"][0]["details"]["zCoordinate"]=0
            return row
        with self.assertRaisesRegex(ValueError,"SAVED_COPY_SLAB_ABSOLUTE_STORY_Z_MISMATCH"):
            SAVED.verify_copy(broken_slab)
        self.assertEqual(len(self.native.writes),self.initial_write_count)

    def test_missing_copy_on_disk_fails_before_any_native_call(self):
        with patch.object(SAVED.os.path,"isfile",return_value=False):
            with self.assertRaisesRegex(ValueError,"SAVED_COPY_FILE_NOT_FOUND"):
                SAVED.verify_copy(self.copy_api)
        self.assertEqual(len(self.native.writes),self.initial_write_count)

    def test_read_only_native_allowlist(self):
        calls=[]
        def never_call(cmd,params):
            calls.append(cmd)
            if cmd not in SAVED.ALLOWED_READS:
                raise AssertionError("forbidden command")
            return self.copy_api(cmd,params)
        result=SAVED.verify_copy(never_call)
        self.assertEqual(result["status"],"OPEN_SAVED_COPY_TYPED_READBACK_PASS")
        self.assertTrue(calls)
        self.assertEqual(set(calls)-SAVED.ALLOWED_READS,set())
        self.assertEqual(len(self.native.writes),self.initial_write_count)


if __name__=="__main__":
    unittest.main()
