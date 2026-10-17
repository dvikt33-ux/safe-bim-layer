"""Targeted contracts for the new APA multi-family native copy adapter."""
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import apa_ac29_multi_prototype_native_copy as multi

COLUMN = "b8d528f0-ab6a-4ece-a62d-74e3a0d7c46c"
BEAM = "f8d528f0-ab6a-4ece-a62d-74e3a0d7c46c"
OBJECT = "a8d528f0-ab6a-4ece-a62d-74e3a0d7c46c"
CHILD = "c8d528f0-ab6a-4ece-a62d-74e3a0d7c46c"


def task():
    return {
        "schemaVersion": "apa-ac29-multi-native-copy/1",
        "projectSha256": "1"*64,
        "projectPath": "C:\\Projects\\approved.pln",
        "expectedGuidCount": 290,
        "expectedGuidSetHash": "2"*64,
        "expectedModelSignatureHash": "3"*64,
        "sceneId": "APPROVED_MULTI_COPY_01",
        "saveSceneId": "APPROVED_MULTI_SAVE_01",
        "authorizationRef": "USER_APPROVED_3_NATIVE_PROTOTYPES",
        "sourceEvidenceRef": "https://github.com/owner/repo/blob/pinned/plan.json",
        "prototypes": [
            {"prototypeGuid": COLUMN, "prototypeType": "Column",
             "sourceAnchor": {"x": 1.0, "y": 2.0, "z": 0.0},
             "targets": [{"x": 3.0, "y": 2.0, "z": 0.0}]},
            {"prototypeGuid": BEAM, "prototypeType": "Beam",
             "sourceAnchor": {"x": 5.0, "y": 2.0, "z": 0.0},
             "targets": [{"x": 8.0, "y": 2.0, "z": 0.0}]},
            {"prototypeGuid": OBJECT, "prototypeType": "Object",
             "sourceAnchor": {"x": 8.0, "y": 4.0, "z": 0.0},
             "targets": [{"x": 10.0, "y": 4.0, "z": 0.0}]},
        ],
        "save": True,
    }


def element(kind, vertices=None, *, parent=None):
    if vertices is None:
        vertices = [[0.0,0.0,0.0],[0.1,0.0,0.0],[0.1,0.05,0.0]]
    return {
        "type": kind,
        "homeStory": 0,
        "relationships": {"hostGuid": parent} if parent else {},
        "materialBindings": {"buildingMaterial": {"guid": "e7ef3819-b3e8-419f-b313-5172e6b0412c"}},
        "bodies": [{"vertices": vertices,
                    "faces": [{"contours": [[0,1,2]]}],
                    "closed": True}],
    }


class TaskValidation(unittest.TestCase):
    def check(self, t):
        return multi.validate_task(
            t, expected_project_sha="1"*64,
            expected_project_path="C:\\Projects\\approved.pln")

    def test_valid_three_families(self):
        t = task()
        self.assertIs(self.check(t), t)
        self.assertEqual(multi.expected_new_types(t),
                         {"Column":1,"ColumnSegment":1,
                          "Beam":1,"BeamSegment":1,"Object":1})

    def test_reject_unauthorized_project_and_unknown_type(self):
        t=task();t["projectSha256"]="4"*64
        with self.assertRaisesRegex(ValueError,"PROJECT"):
            self.check(t)
        t=task();t["prototypes"][1]["prototypeType"]="Wall"
        with self.assertRaisesRegex(ValueError,"SUPPORTED_PROTOTYPE"):
            self.check(t)

    def test_reject_duplicate_locations_even_between_prototypes(self):
        t=task();t["prototypes"][1]["targets"]=copy.deepcopy(t["prototypes"][0]["targets"])
        with self.assertRaisesRegex(ValueError,"DUPLICATE"):
            self.check(t)

    def test_reject_unsupported_z_offset(self):
        t=task();t["prototypes"][0]["targets"][0]["z"]=1.5
        with self.assertRaisesRegex(ValueError,"VERTICAL_OFFSET"):
            self.check(t)

    def test_reject_more_than_200_without_chunk_replay(self):
        t=task()
        t["prototypes"][0]["targets"]=[
            {"x":float(i+20),"y":2.,"z":0.} for i in range(199)]
        with self.assertRaisesRegex(ValueError,"MORE_THAN_200"):
            self.check(t)

    def test_reject_fabricated_authorization(self):
        t=task();t["authorizationRef"]="NOT_APPROVED"
        with self.assertRaisesRegex(ValueError,"AUTHORIZATION"):
            self.check(t)


class NativeVerification(unittest.TestCase):
    def test_one_beam_segment_owner_required(self):
        root=element("Beam")
        child=element("BeamSegment",parent=BEAM)
        self.assertEqual(len(multi.owned_children(
            {BEAM:root,CHILD:child}, BEAM, "Beam")),1)

    def test_object_must_not_have_subelement(self):
        child=element("BeamSegment",parent=OBJECT)
        with self.assertRaisesRegex(ValueError,"OBJECT_HAS_DEPENDENTS"):
            multi.owned_children({OBJECT:element("Object"),CHILD:child},
                                 OBJECT,"Object")

    def test_unsupported_hosted_root_fails(self):
        root=element("Object",parent=COLUMN)
        with self.assertRaisesRegex(ValueError,"NOT_STANDALONE"):
            multi.safe_native_lineage(root)

    def test_translated_BREP_keeps_faces_and_material(self):
        src=element("Object",[[1.,2.,0.],[1.1,2.,0.],[1.1,2.05,0.]])
        dest=element("Object",[[9.,3.,0.],[9.1,3.,0.],[9.1,3.05,0.]])
        origin={"x":1.,"y":2.,"z":0.}
        target={"x":9.,"y":3.,"z":0.}
        self.assertEqual(multi.solid_fingerprint(src,[],origin,parent_guid=OBJECT),
                         multi.solid_fingerprint(dest,[],target,parent_guid=OBJECT))

    def test_open_BREP_not_accepted_as_solid(self):
        src=element("BeamSegment");src["bodies"][0]["closed"]=False
        with self.assertRaisesRegex(ValueError,"NOT_CLOSED"):
            multi.body_fingerprint(src,{"x":0.,"y":0.,"z":0.})

    def test_overlapping_different_target_solids_are_rejected(self):
        t=task()
        t["prototypes"]=t["prototypes"][:1]
        t["prototypes"][0]["targets"]=[
            {"x":3.,"y":2.,"z":0.},{"x":3.05,"y":2.,"z":0.}]
        original=element("ColumnSegment",
            [[1.,2.,0.],[1.1,2.,0.],[1.1,2.05,2.9]])
        root=element("Column");root["bodies"]=[]
        bodies={COLUMN:root,CHILD:original}
        with self.assertRaisesRegex(ValueError,"NEW_SOLIDS_INTERSECT"):
            multi.verify_batch_layout(t["prototypes"],
                {COLUMN:(root,[(CHILD,original)])},{},
                {COLUMN:t["prototypes"][0]["targets"]})

    def test_owned_root_and_child_are_one_destination_not_self_collision(self):
        t=task()
        t["prototypes"]=t["prototypes"][:1]
        root=element("Column",
            [[1.,2.,0.],[1.1,2.,0.],[1.1,2.05,2.9]])
        child=element("ColumnSegment",
            [[1.,2.,0.],[1.1,2.,0.],[1.1,2.05,2.9]],parent=COLUMN)
        plan=multi.verify_batch_layout(
            t["prototypes"],{COLUMN:(root,[(CHILD,child)])},{},
            {COLUMN:t["prototypes"][0]["targets"]})
        self.assertEqual(plan["evaluatedSolidBoxes"],2)

    def test_beam_profile_uses_native_axis_and_source_z(self):
        beam={"type":"Beam","floorIndex":0,"details":{
            "begCoordinate":{"x":5.,"y":2.},
            "endCoordinate":{"x":6.,"y":2.},
            "zCoordinate":0.,"width":0.1,"height":0.2}}
        a=multi.source_detail_fingerprint(beam,"Beam",{"x":5.,"y":2.,"z":0.})
        copied=copy.deepcopy(beam)
        copied["details"]["begCoordinate"]["x"]=8.
        copied["details"]["endCoordinate"]["x"]=9.
        b=multi.source_detail_fingerprint(copied,"Beam",{"x":8.,"y":2.,"z":0.})
        self.assertEqual(a,b)


if __name__=="__main__":
    unittest.main()
