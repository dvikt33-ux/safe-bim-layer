"""Only new AC29 dynamic Create/Modify scope integration contracts."""
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
from tempfile import TemporaryDirectory
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import apa_ac29_dynamic_write_scopes as S
import apa_ac29_dynamic_native_verifiers as V


def hashval(v):
    return hashlib.sha256(json.dumps(v,sort_keys=True,
                                   separators=(",",":")).encode()).hexdigest()


class FakeRouter:
    def __init__(self):
        self.catalog={"commands":{"CreateColumns":{}}}
        self.policies={"CreateColumns":{"impact":"MODEL"}}
        self.A=type("A",(),{"RUN":type("Run",(),{"digest":staticmethod(hashval)})})()
    def operation_kind(self,cmd):return "CREATE"
    def contract_hash(self,cmd):return "c"*64


def source_column():
    return {"coordinates":{"x":3.5,"y":7.25},"width":.1,"depth":.05,
            "height":2.9,"zCoordinate":0.,"floorIndex":0,
            "axisRotationAngle":0.,"buildingMaterialId":{"guid":"e7ef3819-b3e8-419f-b313-5172e6b0412c"},
            "coreAnchor":"Center","circleBased":False,"isSlanted":False,
            "isWidthAndHeightLinked":False}


def setup():
    router=FakeRouter()
    graph={"operations":[{"id":"create_studs","command":"CreateColumns",
                          "params":{"columnsData":[source_column()]}}]}
    plan={"schema":"APA_DYNAMIC_BIM_WORKFLOW_V1","executionPermission":False,
          "sourcePlanHash":hashval(graph),"graph":graph}
    scope={"schemaVersion":"apa-ac29-dynamic-mutation-scope/1",
           "projectSha256":"a"*64,"sourcePlanHash":plan["sourcePlanHash"],
           "authorizationRef":"USER_APPROVED_SAFE_NATIVE_COLUMNS",
           "sourceEvidenceRef":"https://github.com/org/repo/blob/id/source",
           "sceneId":"ApprovedColumnCreate01",
           "stepId":"create_studs","command":"CreateColumns",
           "effect":"CREATE","impact":"MODEL",
           "commandContractHash":"c"*64,
           "parametersHash":hashval(graph["operations"][0]["params"]),
           "expectedBeforeGuidSetHash":"b"*64,
           "expectedBeforeNativeBrepHash":"d"*64,
           "affectedGuids":[],"retainedGuids":[
               "b8d528f0-ab6a-4ece-a62d-74e3a0d7c46c"],
           "verifierId":"VerifiedNativeColumns"}
    return router,plan,scope


class ScopeContracts(unittest.TestCase):
    def reviewed(self,scope=None):
        router,plan,default=setup()
        S.verify_contract(scope or default,plan,router,V.installed_verifiers(),
            approved_project_sha="a"*64,
            local_authorization="USER_APPROVED_SAFE_NATIVE_COLUMNS")
        return router,plan,default

    def test_source_qualified_create_uses_existing_native_graph(self):
        router,plan,scope=self.reviewed()
        receipt=S.prepare_scope_preview(
            scope,plan,router,V.installed_verifiers(),
            approved_project_sha="a"*64,
            local_authorization="USER_APPROVED_SAFE_NATIVE_COLUMNS")
        self.assertFalse(receipt["nativeWritePermission"])
        self.assertEqual(receipt["modelWrites"],0)

    def test_unregistered_verifier_rejected(self):
        r,p,m=setup();m["verifierId"]="CodeFromSourceManifest"
        with self.assertRaisesRegex(ValueError,"CODE_OWNED_VERIFIER"):
            self.reviewed(m)

    def test_unknown_or_unauthorized_effect_rejected(self):
        r,p,m=setup();m["effect"]="UNKNOWN"
        with self.assertRaisesRegex(ValueError,"SINGLE_REVIEWED"):
            self.reviewed(m)
        r,p,m=setup();m["authorizationRef"]="USER_APPROVED_OTHER_PROJECT"
        with self.assertRaisesRegex(ValueError,"LOCAL_APPROVAL"):
            self.reviewed(m)

    def test_mutation_params_cannot_change_after_approval(self):
        r,p,m=setup()
        p["graph"]["operations"][0]["params"]["columnsData"][0]["height"]=3.5
        with self.assertRaisesRegex(ValueError,"SINGLE_REVIEWED"):
            S.verify_contract(m,p,r,V.installed_verifiers(),
                approved_project_sha="a"*64,
                local_authorization="USER_APPROVED_SAFE_NATIVE_COLUMNS")

    def test_one_write_per_reviewed_graph(self):
        r,p,m=setup()
        p["graph"]["operations"].append(dict(
            id="create_again",command="CreateColumns",
            params=p["graph"]["operations"][0]["params"]))
        with self.assertRaisesRegex(ValueError,"SINGLE_REVIEWED"):
            self.reviewed(m)

    def test_duplicate_scene_and_unknown_are_not_deleted(self):
        with TemporaryDirectory() as td:
            path=Path(td)/"ledger.sqlite"
            with sqlite3.connect(path) as db:
                db.execute("CREATE TABLE scenes(scene_id TEXT,state TEXT)")
                db.execute("INSERT INTO scenes VALUES(?,?)",
                           ("HistoricCopy","PARTIAL_OR_UNKNOWN_OUTCOME"))
            with self.assertRaisesRegex(ValueError,"UNRECONCILED"):
                S.validate_existing_ledger(path,"ApprovedColumnCreate01")
            proof={"status":"PREVIOUS_UNKNOWN_EFFECT_ABSENT_FROM_CURRENT_MODEL_PASS",
                   "sceneId":"HistoricCopy"}
            self.assertEqual(S.validate_existing_ledger(
                path,"ApprovedColumnCreate01",proof),
                [("HistoricCopy","PARTIAL_OR_UNKNOWN_OUTCOME")])
            with sqlite3.connect(path) as db:
                row=db.execute("SELECT state FROM scenes").fetchone()
            self.assertEqual(row[0],"PARTIAL_OR_UNKNOWN_OUTCOME")

    def test_existing_scene_never_replayed(self):
        with TemporaryDirectory() as td:
            path=Path(td)/"ledger.sqlite"
            with sqlite3.connect(path) as db:
                db.execute("CREATE TABLE scenes(scene_id TEXT,state TEXT)")
                db.execute("INSERT INTO scenes VALUES(?,?)",
                           ("ApprovedColumnCreate01","UNKNOWN_OUTCOME"))
            with self.assertRaisesRegex(ValueError,"ALREADY_USED_NEVER_RETRY"):
                S.validate_existing_ledger(path,"ApprovedColumnCreate01")

    def test_source_column_rejects_unsupported_geometry(self):
        params={"columnsData":[source_column()]}
        self.assertEqual(len(V.checked_column_source(params)),1)
        params["columnsData"][0]["axisRotationAngle"]=1.2
        with self.assertRaisesRegex(ValueError,"STRAIGHT_CENTERED"):
            V.checked_column_source(params)

    def test_fresh_prewrite_callback_does_not_call_archicad(self):
        proof=V.verify_column_create_before(
            api=None,command="CreateColumns",
            parameters={"columnsData":[source_column()]},
            affected=[],
            native_before={"elements":[{"guid":"src","type":"Column"}]})
        self.assertTrue(proof["status"].endswith("PASS"))


if __name__=="__main__":
    unittest.main()
