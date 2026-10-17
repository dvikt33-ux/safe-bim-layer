"""Only new AC29 dynamic Create/Modify scope integration contracts."""
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
from tempfile import TemporaryDirectory
import unittest
import copy
from unittest.mock import patch
from contextlib import closing, contextmanager


@contextmanager
def database(path):
    with closing(sqlite3.connect(path)) as db:
        with db:
            yield db

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
    return {"coordinates":{"x":3.5,"y":7.25,"z":0.},"width":.1,"depth":.05,
            "height":2.9,"floorIndex":0,
            "axisRotationAngle":0.,"buildingMaterialId":{"guid":"e7ef3819-b3e8-419f-b313-5172e6b0412c"},
            "coreAnchor":"Center","circleBased":False,
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
            S.verify_contract(m,p,r,V.installed_verifiers(),
                approved_project_sha="a"*64,
                local_authorization="USER_APPROVED_SAFE_NATIVE_COLUMNS")

    def test_duplicate_scene_and_unknown_are_not_deleted(self):
        with TemporaryDirectory() as td:
            path=Path(td)/"ledger.sqlite"
            with database(path) as db:
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
            with database(path) as db:
                row=db.execute("SELECT state FROM scenes").fetchone()
            self.assertEqual(row[0],"PARTIAL_OR_UNKNOWN_OUTCOME")

    def test_existing_scene_never_replayed(self):
        with TemporaryDirectory() as td:
            path=Path(td)/"ledger.sqlite"
            with database(path) as db:
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


class WorkflowExecution(unittest.TestCase):
    """Actual DynamicCommands + EvidenceAPI + SQLite, synthetic native boundary."""

    def execute_case(self, folder, *, bad_readback=False, historical=False,
                     drift=False):
        import archicad_project_accelerator as A
        import archicad_connected_components as C
        from archicad_dynamic_commands import DynamicCommands
        root = "08d528f0-ab6a-4ece-a62d-74e3a0d7c46c"
        child = "18d528f0-ab6a-4ece-a62d-74e3a0d7c46c"
        old = setup()[2]['retainedGuids'][0]
        model = {'elements': [{'guid':old, 'type':'Object', 'homeStory':0,
                              'bodies':[], 'relationships':{}, 'materialBindings':{}}]}
        r = DynamicCommands({'common_schemas':{},
            '_metadata':{'provider_version':A.RUN.EXPECTED_TAPIR},
            'commands':{'CreateColumns':{'name':'CreateColumns',
                'version':'1', 'parameters':{'type':'object'},
                'returns':{'type':'object'}}}})
        r.review_policy('CreateColumns','CREATE','MODEL',
                        {'source':'synthetic integration contract','sha256':'1'*64})
        preview=A.prepare_native_task(r, {'schemaVersion':'apa-native-task/1',
            'request':'synthetic single native batch', 'graph':setup()[1]['graph']})
        path=Path(folder)/'synthetic.pln';path.write_bytes(b'synthetic saved PLN')
        saved=hashlib.sha256(path.read_bytes()).hexdigest()
        _,_,spec=setup()
        spec.update(projectSha256=saved,
            sourcePlanHash=preview['sourcePlanHash'],
            commandContractHash=r.contract_hash('CreateColumns'),
            expectedBeforeGuidSetHash=A.RUN.digest([old]),
            expectedBeforeNativeBrepHash=A.RUN.digest({old:[]}))
        ledger=Path(folder)/'original.sqlite'
        with database(ledger) as db:
            db.execute('CREATE TABLE scenes(scene_id TEXT PRIMARY KEY,plan_hash TEXT,state TEXT,result TEXT)')
            if historical:
                db.execute('INSERT INTO scenes VALUES(?,?,?,?)',
                    ('HistoricUnknown','old','PARTIAL_OR_UNKNOWN_OUTCOME','{}'))
        api = None
        writes=[]
        def transport(command,params):
            if command=='API.IsAddOnCommandAvailable':return {'available':True}
            if command=='GetAddOnVersion':return {'version':A.RUN.EXPECTED_TAPIR}
            if command=='GetAllElements':
                return {'elements':[{'elementId':{'guid':e['guid']}} for e in model['elements']]}
            if command=='GetDetailsOfElements':
                item=source_column();detail=copy.deepcopy(item)
                detail['origin']=detail.pop('coordinates')
                detail['zCoordinate']=detail['origin'].pop('z')
                detail['isSlanted']=False
                if bad_readback:detail['height']=99.
                return {'detailsOfElements':[{'type':'Column','floorIndex':0,'details':detail}]}
            if command=='CreateColumns':
                with database(ledger) as db:
                    self.assertEqual(db.execute('SELECT state FROM scenes WHERE scene_id=?',
                        (spec['sceneId'],)).fetchone()[0],'STARTED')
                writes.append(command)
                item=source_column();x,y=(item['coordinates'][k] for k in ('x','y'))
                vertices=[[x+sx*item['width']/2,y+sy*item['depth']/2,z]
                          for sx in (-1,1) for sy in (-1,1) for z in (0.,item['height'])]
                model['elements'].extend([
                    {'guid':root,'type':'Column','homeStory':0,'bodies':[]},
                    {'guid':child,'type':'ColumnSegment','homeStory':0,
                     'relationships':{'hostGuid':root},
                     'materialBindings':{'buildingMaterial':item['buildingMaterialId']},
                     'bodies':[{'closed':True,'vertices':vertices}]}])
                return {'elements':[{'elementId':{'guid':root}}]}
            raise AssertionError(command)
        api=A.EvidenceAPI(transport,folder,execute=True)
        w=A.RUN.SceneWriter(api,ledger)
        binding={'path':str(path),'name':'synthetic','port':19727,
                 'tapirVersion':A.RUN.EXPECTED_TAPIR,'storyIndex':0}
        capture_count=0
        def capture(*_):
            nonlocal capture_count
            capture_count+=1
            if drift and capture_count>=3 and not writes:
                model['elements'][0]['bodies']=[{'closed':True,'vertices':[[1.,2.,3.]]}]
            return copy.deepcopy(model)
        proof = ({'status':'PREVIOUS_UNKNOWN_EFFECT_ABSENT_FROM_CURRENT_MODEL_PASS',
                  'sceneId':'HistoricUnknown','savedProjectSHA256':saved,
                  'guidSetHash':spec['expectedBeforeGuidSetHash'],
                  'brepSignaturesHash':spec['expectedBeforeNativeBrepHash'],
                  'modelWrites':0} if historical else None)
        with patch.object(A.RUN,'guarded_project',return_value=binding), \
             patch('archicad_bim_documentation.capture_full_model',side_effect=capture):
            if drift:
                with self.assertRaisesRegex(ValueError,'BREP_CHANGED|RETAINED_MODEL_CHANGED'):
                    A.run_scoped_native_task(r,api,preview,w,spec,
                        approved_project_sha=saved,current_project_sha=lambda:saved,
                        local_authorization=spec['authorizationRef'],reconciliation=proof)
                self.assertEqual(writes,[])
                return
            result=A.run_scoped_native_task(r,api,preview,w,spec,
                approved_project_sha=saved,current_project_sha=lambda:saved,
                local_authorization=spec['authorizationRef'],reconciliation=proof)
            self.assertEqual(len(writes),1)
            with self.assertRaisesRegex(ValueError,'ALREADY_USED_NEVER_RETRY'):
                A.run_scoped_native_task(r,api,preview,w,spec,
                    approved_project_sha=saved,current_project_sha=lambda:saved,
                    local_authorization=spec['authorizationRef'],reconciliation=proof)
        with database(ledger) as db:
            state=db.execute('SELECT state FROM scenes WHERE scene_id=?',
                             (spec['sceneId'],)).fetchone()[0]
            if historical:
                self.assertEqual(db.execute('SELECT state FROM scenes WHERE scene_id=?',
                    ('HistoricUnknown',)).fetchone()[0],'PARTIAL_OR_UNKNOWN_OUTCOME')
        self.assertEqual(state,'PARTIAL_OR_UNKNOWN_OUTCOME' if bad_readback else 'PASS')
        self.assertEqual(result['status'],'STOPPED_UNKNOWN_OUTCOME' if bad_readback else
                         'WORKFLOW_CALLABLE_VERIFIED')

    def test_core_to_existing_workflow_writer_sqlite_and_native_readback(self):
        with TemporaryDirectory() as folder:self.execute_case(folder)

    def test_readback_failure_is_unknown_and_never_replayed(self):
        with TemporaryDirectory() as folder:self.execute_case(folder,bad_readback=True)

    def test_reconciled_history_is_preserved_during_new_operation(self):
        with TemporaryDirectory() as folder:self.execute_case(folder,historical=True)

    def test_pre_dispatch_geometry_drift_prevents_write(self):
        with TemporaryDirectory() as folder:self.execute_case(folder,drift=True)

    def test_column_verifier_accepts_actual_pinned_native_create_schema(self):
        import archicad_project_accelerator as A
        from archicad_dynamic_commands import DynamicCommands
        catalog=A.SCENE.GRAPH.CONTRACTS.load_catalog(
            Path(__file__).resolve().parents[1]/'schemas/tapir-live-1.5.10/tapir-scene-live.json')
        r=DynamicCommands(catalog)
        parameters={'columnsData':[source_column()]}
        r.prepare('CreateColumns',parameters)
        V.checked_column_source(parameters)


if __name__=="__main__":
    unittest.main()
