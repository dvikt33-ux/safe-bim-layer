"""Offline regression for BDD partial pile recovery; never talks to Archicad."""
import sys
from pathlib import Path
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import apa_bdd_house_native_builder as B
import apa_bdd_house_safe_resume as R


class RecoveryTests(unittest.TestCase):
    def test_live_diagnostic_ids(self):
        self.assertEqual(len(R.DIAG_PARENT_GUIDS), 16)
        self.assertEqual(len(R.DIAG_SEGMENT_GUIDS), 16)
        self.assertFalse(R.DIAG_PARENT_GUIDS & R.DIAG_SEGMENT_GUIDS)
        self.assertEqual(len(B.PILES), 49)
        self.assertEqual(sum(len(x) for x in [
            B.plan()["piles"], B.plan()["grillage"],
            B.plan()["exteriorWalls"], B.plan()["floorJoists"],
            B.plan()["floorPanels"], B.plan()["terracePlatforms"],
            B.plan()["roofEnvelope"]
        ]), 125)

    def test_initial_reconcile_knows_archicad_child_segments(self):
        baseline={B.BASELINE_GUID.lower()}|{"existing-%02d"%i for i in range(20)}
        model=baseline|R.DIAG_PARENT_GUIDS|R.DIAG_SEGMENT_GUIDS
        data={}
        for guid,(x,y) in zip(sorted(R.DIAG_PARENT_GUIDS),B.PILES[:16]):
            data[guid]={"type":"Column","details":{
                "origin":{"x":x,"y":y}, "height":2.4,
                "width":0.3,"depth":0.3,
                "zCoordinate":-3.0,"circleBased":True
            }}
        for guid in R.DIAG_SEGMENT_GUIDS:
            data[guid]={"type":"ColumnSegment","details":{
                "error":"Not yet supported element type"}}
        manifest={"status":"BUILDING","stages":[],
                  "sourcePLNSHA256":"test-original-hash",
                  "initialGUIDs":list(baseline)}
        with mock.patch.object(B,"assert_archicad29"),\
             mock.patch.object(B,"project"),\
             mock.patch.object(B,"hashfile",return_value="test-original-hash"),\
             mock.patch.object(B,"guids",return_value=model),\
             mock.patch.object(B,"api",return_value={}),\
             mock.patch.object(R,"native_details",return_value=data),\
             mock.patch.object(R,"write_checkpoint") as write:
            got=R.initial_reconcile(manifest)
        self.assertEqual(got,baseline)
        self.assertEqual(len(manifest["stages"]),1)
        self.assertEqual(len(manifest["stages"][0]["primaryGuids"]),16)
        self.assertEqual(len(manifest["stages"][0]["autoChildGuids"]),16)
        write.assert_called()

    def test_future_batch_counts_children_without_false_foreign_write(self):
        initial={"old1","old2"}
        parent="PARENT-P1"
        child="CHILD-S1"
        manifest={"stages":[],"status":"BUILDING"}
        def api_call(cmd,p=None):
            if cmd=="CreateColumns":
                return {"elements":[{"elementId":{"guid":parent}}]}
            raise AssertionError(cmd)
        with mock.patch.object(B,"project"),\
             mock.patch.object(B,"guids",side_effect=[initial,
                                                        initial|{parent.lower(),child.lower()}]),\
             mock.patch.object(B,"api",side_effect=api_call),\
             mock.patch.object(R,"native_details",return_value={
                 parent.lower():{"type":"Column","details":{}},
                 child.lower():{"type":"ColumnSegment","details":{}}
             }),\
             mock.patch.object(R,"write_checkpoint"):
            R.record_native_batch(manifest,initial,"Pile","CreateColumns",
                                  "columnsData",[{}],0,12)
        self.assertEqual(manifest["inFlight"],None)
        self.assertEqual(manifest["stages"][0]["primaryGuids"],[parent.lower()])
        self.assertEqual(manifest["stages"][0]["autoChildGuids"],[child.lower()])
        self.assertEqual(manifest["lastCount"],4)


if __name__=="__main__":
    unittest.main()
