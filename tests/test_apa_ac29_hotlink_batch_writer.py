"""Offline native batch Hotlink verifier: 1 provider call, all real child owners."""
from __future__ import annotations

import hashlib
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import apa_ac29_hotlink_batch_geometry as G
import apa_ac29_hotlink_batch_verifier as V
import apa_ac29_hotlink_batch_oneshot as B

def guid(n):
    return "00000000-0000-4000-8000-" + str(n).zfill(12)


def vertices(x1,x2,y1=0,y2=5,z1=0,z2=3):
    return [[x,y,z] for x in (x1,x2) for y in (y1,y2)
            for z in (z1,z2)]


def element(id_,kind,verts=None):
    return {"guid":guid(id_),"type":kind,
            "bodies":([] if verts is None else [{"vertices":verts}])}


class MockNative:
    def __init__(self, source_path):
        self.module=source_path
        self.node=guid(10)
        self.root=guid(11)
        self.old = {"elements":[
            element(1,"Wall",vertices(0,330.475)),
            element(11,"Hotlink"),
            element(12,"Wall",vertices(646.475,660.475)),
            element(13,"Slab",vertices(660.475,676.95))
        ]}
        self.new_roots=[guid(21),guid(22)]
        self.origin={"x":346.475,"y":0,"z":0}
        self.kind={guid(1):"Wall",guid(11):"Hotlink",
                   guid(12):"Wall",guid(13):"Slab"}
        self.owners={guid(12):self.root,guid(13):self.root}
        self.roots={self.root:self.origin}
        self.after=None

    def api(self, command, params):
        if command=="GetHotlinks":
            return {"hotlinks":[{"location":str(self.module),
                     "hotlinkNodeId":{"guid":self.node},"children":[]}]}
        if command=="GetDetailsOfElements":
            rows=[]
            for req in params["elements"]:
                guid_=req["elementId"]["guid"].lower()
                if guid_ in self.roots:
                    rows.append({"type":"Hotlink","floorIndex":0,
                                 "details":{"hotlinkNodeId":{"guid":self.node},
                                            "hotlinkType":"Module",
                                            "origin":self.roots[guid_],
                                            "rotationAngle":0,"mirrored":False}})
                else:
                    rows.append({"type":self.kind[guid_],"floorIndex":0,
                                 "hotlinkId":{"guid":self.owners[guid_]}
                                 if guid_ in self.owners else None,
                                 "details":{}})
            return {"detailsOfElements":rows}
        raise AssertionError("Unrecognized native read: "+command)

    def add_batch(self, plan):
        rows=list(self.old["elements"])
        for index,root in enumerate(self.new_roots):
            origin=plan["origins"][index]
            self.roots[root]=origin
            rows.append(element(21+index,"Hotlink"))
            shift=origin["x"]-self.origin["x"]
            first=23+index*2
            second=first+1
            rows.append(element(first,"Wall",
                vertices(646.475+shift,660.475+shift)))
            rows.append(element(second,"Slab",
                vertices(660.475+shift,676.95+shift)))
            for number,kind in ((first,"Wall"),(second,"Slab")):
                self.owners[guid(number)]=root
                self.kind[guid(number)]=kind
        self.after={"elements":rows}
        return self.after


class NativeBatchTests(unittest.TestCase):
    def setUp(self):
        folder=tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root=Path(folder.name)
        self.source=self.root/"accepted.pln"
        self.module=self.root/"module.pln"
        self.scratch=self.root/"batch.pln"
        self.state=self.root/"state"
        self.source.write_bytes(b"accepted native test sample")
        self.module.write_bytes(b"unmodified source module")
        self.mock=MockNative(self.module)
        self.proof=G.placed_prototype(
            self.mock.api,self.mock.old,self.mock.node,self.mock.root,
            self.mock.origin)
        self.plan=G.planned_batch(self.proof,2,10)
        self.parameters=V.batch_parameters(self.mock.node,self.plan["origins"])

    def test_stage_preserves_original_and_creates_disposable_only(self):
        m=B.unique_stage(self.source,self.module,self.scratch,self.state,
                         self.mock.node,self.mock.root,2,10,19726)
        self.assertEqual(m["status"],"STAGED_NO_MODEL_WRITES")
        self.assertEqual(B.digest(self.scratch), B.digest(self.source))
        self.assertEqual(B.validate_stage(self.state), m)
        with self.assertRaisesRegex(ValueError,"FRESH_TEST_COPY"):
            B.unique_stage(self.source,self.module,self.scratch,self.state,
                           self.mock.node,self.mock.root,2,10,19726)
        self.assertEqual(self.source.read_bytes(),b"accepted native test sample")

    def test_stage_count_and_duplicate_module_rejected(self):
        for number in (0,33):
            with self.assertRaisesRegex(ValueError,"BOUNDED_COUNT"):
                B.unique_stage(self.source,self.module,self.scratch,self.state,
                               self.mock.node,self.mock.root,number,10,19726)
        with self.assertRaisesRegex(ValueError,"FRESH_TEST_COPY"):
            B.unique_stage(self.source,self.source,self.scratch,self.state,
                           self.mock.node,self.mock.root,2,10,19726)

    def test_existing_node_batch_native_schema_and_one_operation(self):
        self.assertEqual(len(self.parameters["hotlinkInstances"]),2)
        self.assertEqual(len(set(x["hotlinkNodeId"]["guid"] for x in
                             self.parameters["hotlinkInstances"])),1)
        self.assertEqual([p["origin"] for p in
                          self.parameters["hotlinkInstances"]],
                         self.plan["origins"])
        self.assertEqual(V.parse_batch_response(
            {"elements":[{"elementId":{"guid":g}} for g in self.mock.new_roots]},
            2,set(self.proof["allBoxes"])),self.mock.new_roots)

    def test_full_native_after_proof_checks_each_member_and_world_brep(self):
        v=V.installed_batch_verifier(self.module,B.digest(self.module),
             self.mock.node,self.mock.root,self.mock.origin,2,10,self.plan
        )["VerifiedHotlinkBatchReuseV1"]
        before_guids=set(self.proof["allBoxes"])
        before=v.before(api=self.mock.api,command="CreateHotlinkInstances",
                        parameters=self.parameters,affected=[],
                        native_before=self.mock.old)
        self.assertEqual(before["status"],"HOTLINK_BATCH_NATIVE_SOURCE_AND_BREP_PASS")
        after_model=self.mock.add_batch(self.plan)
        after_guids={x["guid"] for x in after_model["elements"]}
        res=v.after(api=self.mock.api,command="CreateHotlinkInstances",
                    parameters=self.parameters,native_response={"elements":[
                    {"elementId":{"guid":root}} for root in self.mock.new_roots]},
                    before_guids=before_guids,after_guids=after_guids,
                    affected=[],native_before=self.mock.old,
                    native_after=after_model,source_proof=before)
        self.assertEqual(res["status"],"HOTLINK_BATCH_ALL_INSTANCES_NATIVE_BREP_PASS")
        self.assertEqual(res["verifiedOwners"],4)
        self.assertEqual(res["nativeBatchWrites"],1)
        self.assertEqual(res["newGuidCount"],6)

    def test_wrong_owner_is_rejected(self):
        v=V.installed_batch_verifier(self.module,B.digest(self.module),
             self.mock.node,self.mock.root,self.mock.origin,2,10,self.plan
        )["VerifiedHotlinkBatchReuseV1"]
        before=v.before(api=self.mock.api,command="CreateHotlinkInstances",
                        parameters=self.parameters,affected=[],
                        native_before=self.mock.old)
        model=self.mock.add_batch(self.plan)
        self.mock.owners[guid(23)]=self.mock.root
        with self.assertRaisesRegex(ValueError,"ORPHANED"):
            v.after(api=self.mock.api,command="CreateHotlinkInstances",
                parameters=self.parameters,native_response={"elements":[
                    {"elementId":{"guid":g}} for g in self.mock.new_roots]},
                before_guids=set(self.proof["allBoxes"]),
                after_guids={e["guid"] for e in model["elements"]},
                affected=[],native_before=self.mock.old,native_after=model,
                source_proof=before)

    def test_wrong_destination_bbox_is_rejected(self):
        v=V.installed_batch_verifier(self.module,B.digest(self.module),
             self.mock.node,self.mock.root,self.mock.origin,2,10,self.plan
        )["VerifiedHotlinkBatchReuseV1"]
        before=v.before(api=self.mock.api,command="CreateHotlinkInstances",
                        parameters=self.parameters,affected=[],
                        native_before=self.mock.old)
        model=self.mock.add_batch(self.plan)
        model["elements"][-1]["bodies"][0]["vertices"][0][0]+=0.1
        # All eight corners change for exact bbox drift instead of one vertex.
        for pt in model["elements"][-1]["bodies"][0]["vertices"]:
            pt[0]+=0.1
        with self.assertRaisesRegex(ValueError,"WORLD_BREP_COORDINATES"):
            v.after(api=self.mock.api,command="CreateHotlinkInstances",
                parameters=self.parameters,native_response={"elements":[
                    {"elementId":{"guid":g}} for g in self.mock.new_roots]},
                before_guids=set(self.proof["allBoxes"]),
                after_guids={e["guid"] for e in model["elements"]},
                affected=[],native_before=self.mock.old,native_after=model,
                source_proof=before)

    def test_source_sha_change_or_plan_tampering_rejected(self):
        corrupted=dict(self.plan, count=3)
        with self.assertRaisesRegex(ValueError,"APPROVED_PLAN_DRIFT"):
            V.installed_batch_verifier(self.module,B.digest(self.module),
               self.mock.node,self.mock.root,self.mock.origin,2,10,corrupted)
        self.module.write_bytes(b"corrupted fixture")
        with self.assertRaisesRegex(ValueError,"IMMUTABLE_SHA_REQUIRED"):
            V.installed_batch_verifier(self.module,
               hashlib.sha256(b"unmodified source module").hexdigest(),
               self.mock.node,self.mock.root,self.mock.origin,2,10,self.plan)

    def test_response_cardinality_duplicate_and_known_guid_rejected(self):
        with self.assertRaisesRegex(ValueError,"CARDINALITY"):
            V.parse_batch_response({"elements":[]},2,set())
        with self.assertRaisesRegex(ValueError,"NEW_NATIVE_ROOT_IDS"):
            V.parse_batch_response({"elements":[
                {"elementId":{"guid":guid(21)}},
                {"elementId":{"guid":guid(21)}}]},2,set())
        with self.assertRaisesRegex(ValueError,"NEW_NATIVE_ROOT_IDS"):
            V.parse_batch_response({"elements":[
                {"elementId":{"guid":guid(21)}},
                {"elementId":{"guid":guid(22)}}]},2,{guid(22)})

    def test_no_native_dispatch_without_readonly_plan(self):
        B.unique_stage(self.source,self.module,self.scratch,self.state,
                       self.mock.node,self.mock.root,2,10,19726)
        with self.assertRaises(FileNotFoundError):
            B.execute(self.state)

    def test_no_repeat_after_attempt_and_no_false_reopen(self):
        B.unique_stage(self.source,self.module,self.scratch,self.state,
                       self.mock.node,self.mock.root,2,10,19726)
        B.save_new(self.state/"attempted.json",{"status":"RESERVED"})
        with self.assertRaisesRegex(ValueError,"STAGE_OR_IMMUTABLE_SOURCE_DRIFT"):
            B.execute(self.state)
        with self.assertRaises(FileNotFoundError):
            B.verify_reopen(self.state)

    def test_saved_copy_dependent_original_router_reused(self):
        source=(ROOT/"scripts/apa_ac29_hotlink_batch_oneshot.py").read_text()
        self.assertIn("APA.native_command_router",source)
        self.assertIn("build_existing_workflow_scopes(",source)
        self.assertIn("RUN.SceneWriter(",source)
        self.assertIn("APA.run_native_task(",source)
        self.assertIn("GuardedSaveTransport(",source)
        self.assertIn("CREATE_SCENE",source)
        self.assertIn("SAVE_SCENE",source)
        self.assertIn("NATIVE_NO_OPEN_PROJECT_CONFIRMED",source)
        self.assertNotIn('api("OpenProject"',source)


if __name__=="__main__":
    unittest.main()
