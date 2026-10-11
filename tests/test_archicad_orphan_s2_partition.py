"""Simulates native CreateWalls succeeding but the response timing out.

This produces the owner's observed ATTEMPTED/NULL GUID + exactly one unlogged
native Wall. Only GET commands are allowed when reconciling.
"""
from pathlib import Path
import sys
import unittest
import uuid

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))

import archicad_scene_run as RUN
import continue_apa_after_s2_slab as FOURTH
import inspect_apa_orphan_s2_partition as ORPHAN
from test_archicad_fourth_suffix import FourthSuffixTests
from test_archicad_basic_slab_integration import MATERIAL_NAME


class OrphanS2WallDiagnosisTests(unittest.TestCase):
    bad_slab_api = FourthSuffixTests.bad_slab_api

    read_api = FourthSuffixTests.read_api

    def setUp(self):
        FourthSuffixTests.setUp(self)
        RUN.bind_approved_scratch_pln(19726)
        self.before_native_writes=len(self.native.writes)
        self.api=self.read_api
        ticket=FOURTH.proof(self.api,MATERIAL_NAME)

        def write_but_timeout(cmd,params):
            reply=self.read_api(cmd,params)
            if cmd=="CreateWalls":
                # Graphisoft processed the create, but the client never
                # received its GUID because a modal blocked completion.
                raise TimeoutError("timed out after native create")
            return reply

        self.stopped=FOURTH.execute(write_but_timeout,MATERIAL_NAME,ticket["token"])
        self.assertEqual(self.stopped["status"],"PARTIAL_OR_UNKNOWN_OUTCOME")
        self.assertEqual(self.stopped["failedStep"],"s2-partition-1")
        self.assertEqual(len(self.native.created),13)
        self.assertEqual(len(self.native.writes),self.before_native_writes+1)

    def test_full_live_shaped_orphan_guid_verified_without_mutations(self):
        before=len(self.native.writes)
        out=ORPHAN.reconcile(self.api)
        self.assertEqual(out["status"],"READ_ONLY_ORPHAN_S2_PARTITION_VERIFIED")
        self.assertEqual(out["journalState"],"ATTEMPTED")
        self.assertEqual(out["nativeFloorIndex"],1)
        self.assertEqual(out["nativeAbsoluteZ"],3.0)
        self.assertEqual(out["totalModelElements"],33)
        self.assertEqual(out["remainingPlannedCreates"],12)
        self.assertEqual(out["plannedElementsVerified"],13)
        self.assertFalse(out["replayOfFourthSceneAllowed"])
        self.assertEqual(len(self.native.writes),before)

    def test_mismatched_native_wall_z_blocked_before_mutations(self):
        before=len(self.native.writes)
        def drift(cmd,params):
            res=self.api(cmd,params)
            if cmd=="GetDetailsOfElements":
                guid=params["elements"][0]["elementId"]["guid"]
                new_ids=set(self.native.created)-set(
                    list(self.native.created)[:-1])
                if guid in new_ids:
                    res["detailsOfElements"][0]["details"]["zCoordinate"]=0.0
            return res
        with self.assertRaisesRegex(ValueError,"WALL_STORY_Z_READBACK_MISMATCH"):
            ORPHAN.reconcile(drift)
        self.assertEqual(len(self.native.writes),before)

    def test_two_unjournaled_native_guids_refuse(self):
        before=len(self.native.writes)
        self.native.existing.append(str(uuid.uuid4()))
        with self.assertRaisesRegex(ValueError,"NATIVE_NOT_EXACTLY_32_PLUS_ONE_UNJOURNALED"):
            ORPHAN.reconcile(self.api)
        self.assertEqual(len(self.native.writes),before)

    def test_missing_orphan_native_guid_refuses(self):
        before=len(self.native.writes)
        last=next(reversed(self.native.created))
        self.native.created.pop(last)
        with self.assertRaisesRegex(ValueError,"NATIVE_NOT_EXACTLY_32_PLUS_ONE_UNJOURNALED"):
            ORPHAN.reconcile(self.api)
        self.assertEqual(len(self.native.writes),before)

    def test_prior_suffix_never_replayed_even_after_verified_orphan(self):
        before=len(self.native.writes)
        ORPHAN.reconcile(self.api)
        with self.assertRaisesRegex(ValueError,"FOURTH_SCENE_ALREADY_RESERVED"):
            FOURTH.proof(self.api,MATERIAL_NAME)
        self.assertEqual(len(self.native.writes),before)


if __name__=="__main__":
    unittest.main()
