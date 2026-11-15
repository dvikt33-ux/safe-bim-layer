"""Lossless root-vs-event GUID normalization and historic receipt safety."""
import json
from pathlib import Path
import tempfile
import unittest

from apa_ac30_change_normalizer import normalize,from_creation_receipts

A="C971AA9C-DD4F-4C95-A0B1-3C331A68A9FE"
B="7DDABE9B-7C3A-4955-AB7F-20CA54EC1BA3"
C="5D759916-D4BC-4E1D-A25F-9FAE18D3B1C4"
def row(guid):
    return {"elementId":{"guid":guid}}

class ChangeNormalizerTests(unittest.TestCase):
    def test_multiple_events_single_proven_root(self):
        packet={"newElements":[row(A),row(B),row(C)]}
        out=normalize(packet,{"Railing":[A]})
        self.assertEqual(out["eventCounts"]["newElements"],3)
        self.assertEqual(out["rootCount"],1)
        self.assertEqual(out["unresolvedGUIDs"],[B,C])
        self.assertEqual(out["unresolvedCount"],2)
        self.assertEqual(out["modelWrites"],0)
    def test_unproven_root_rejected(self):
        with self.assertRaisesRegex(ValueError,"ROOT_NOT_IN_NEW_EVENTS"):
            normalize({"newElements":[row(A)]},{"Railing":[B]})
    def test_duplicate_event_rejected(self):
        with self.assertRaisesRegex(ValueError,"DUPLICATE_GUID_WITHIN_CLASS"):
            normalize({"newElements":[row(A),row(A)]},{"Railing":[A]})
    def test_cross_class_event_rejected(self):
        with self.assertRaisesRegex(ValueError,"OVERLAPPING_CHANGE_CLASSES"):
            normalize({"newElements":[row(A)],"deletedElements":[row(A)]},{"Railing":[A]})
    def test_cross_type_root_rejected(self):
        with self.assertRaisesRegex(ValueError,"ROOT_ASSIGNED_MULTIPLE_TYPES"):
            normalize({"newElements":[row(A)]},{"Railing":[A],"Wall":[A]})
    def test_historical_creation_receipts(self):
        with tempfile.TemporaryDirectory() as folder:
            base=Path(folder)
            packets=[{"diff":{"newElements":[row(A),row(B)]}},
                     {"created":A,"new":[A]},
                     {"status":"PASS","deleted":True,"createdGuid":A},
                     {"command":"CreateNativeAssemblyV1","args":{"kind":"Railing"}},
                     {"result":{"nativeModelWrites":1,"createdElements":[row(A)]}}]
            paths=[]
            for i,obj in enumerate(packets):
                path=base/("%d.json"%i)
                path.write_text(json.dumps(obj),encoding="utf-8")
                paths.append(path)
            record=from_creation_receipts(*paths)
            self.assertEqual(record["rootCount"],1)
            self.assertEqual(record["unresolvedCount"],1)
            self.assertEqual(len(record["sourceSHA256"]),5)
            self.assertEqual(record["historicalCreationCommand"],"CreateNativeAssemblyV1")
            self.assertEqual(record["historicalCreationKind"],"Railing")
            packets[2]["deleted"]=False
            paths[2].write_text(json.dumps(packets[2]),encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"INDEPENDENT_ROOT_CREATION_NOT_PROVEN"):
                from_creation_receipts(*paths)
            packets[2]["deleted"]=True
            paths[2].write_text(json.dumps(packets[2]),encoding="utf-8")
            packets[3]["command"]="CreateRailings"
            paths[3].write_text(json.dumps(packets[3]),encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"CREATE_INTENT_RESPONSE_TYPE_OR_GUID_MISMATCH"):
                from_creation_receipts(*paths)
            packets[3]["command"]="CreateNativeAssemblyV1"
            paths[3].write_text(json.dumps(packets[3]),encoding="utf-8")
            packets[4]["result"]["createdElements"]=[row(B)]
            paths[4].write_text(json.dumps(packets[4]),encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"CREATE_INTENT_RESPONSE_TYPE_OR_GUID_MISMATCH"):
                from_creation_receipts(*paths)
if __name__=="__main__":
    unittest.main(verbosity=2)
