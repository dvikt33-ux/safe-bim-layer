"""Focused no-replay, local grant, and history gates for APA scoped native mailbox."""
from datetime import datetime,timedelta,timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch
import json
import sqlite3
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import apa_ac29_autonomous_job_bridge as BRIDGE
import apa_ac29_scoped_native_executor as S

SHA="a"*64
GUID="b8d528f0-ab6a-4ece-a62d-74e3a0d7c46c"


def source():
    return {
        "schema":"APA_AC29_SCOPED_NATIVE_TASK_V1",
        "projectSha256":SHA,
        "projectPath":str(Path("C:/BDD.pln")),
        "command":"CreateWalls",
        "parameters":{"wallsData":[{"height":3}]},
        "sourcePlanHash":SHA,
        "parametersHash":SHA,
        "commandContractHash":SHA,
        "expectedBeforeGuidSetHash":SHA,
        "expectedBeforeNativeBrepHash":SHA,
        "expectedGuidCount":298,
        "affectedGuids":[],
        "sceneId":"NewNativeWall001",
        "saveSceneId":"SaveNativeWall001",
        "stepId":"CreateNativeWall001",
        "authorizationRef":"USER_APPROVED_EXACT_WALL",
        "sourceEvidenceRef":"https://github.com/dvikt33-ux/safe-bim-layer/pull/151",
    }


class TaskScopeTests(TestCase):
    def setUp(self):
        self.stub=SimpleNamespace(
            approved_saved_sha=lambda:SHA,
            approved_guid_count=lambda:298,
            WORKING=Path("C:/BDD.pln"),
        )
        self.task=source()

    def test_task_bounded_to_exact_project_and_effect(self):
        self.assertEqual(S.qualify_task(self.task,self.stub),self.task)
        for wrong in [
            dict(self.task,projectSha256="f"*64),
            dict(self.task,projectPath="C:/other.pln"),
            dict(self.task,command="DeleteElements"),
            dict(self.task,affectedGuids=[GUID]),
            dict(self.task,sceneId=self.task["saveSceneId"]),
        ]:
            with self.subTest(wrong=wrong),self.assertRaises(ValueError):
                S.qualify_task(wrong,self.stub)

    def test_material_only_modify_requires_exact_existing_guid(self):
        p=dict(self.task,command="ModifySlabs",affectedGuids=[GUID])
        self.assertEqual(S.qualify_task(p,self.stub),p)
        p["affectedGuids"].append(GUID)
        with self.assertRaises(ValueError):
            S.qualify_task(p,self.stub)

    def test_immutable_local_job_and_task_blobs_are_required(self):
        with TemporaryDirectory() as temp:
            root=Path(temp)
            (root/"controller-grants").mkdir()
            folder=root/"attempted"
            folder.mkdir()
            (folder/"attempted.json").write_text(
                json.dumps({"sourceBlob":"1"*40}),encoding="utf8")
            b=SimpleNamespace(ROOT=root)
            job={"jobId":"ac29-scoped-native-test"}
            with self.assertRaisesRegex(ValueError,"LOCAL_BLOB_BOUND_GRANT_REQUIRED"):
                S.require_local_grant(b,job,folder,self.task,"2"*40)
            grant={
                "schema":"APA_AC29_LOCAL_SCOPED_NATIVE_GRANT_V1",
                "jobId":job["jobId"],
                "jobBlobSha1":"1"*40,
                "taskBlobSha1":"2"*40,
                "projectSha256":SHA,
                "authorizationRef":"USER_APPROVED_EXACT_WALL",
                "command":"CreateWalls",
                "sourcePlanHash":SHA,
                "expectedBeforeGuidSetHash":SHA,
                "expectedBeforeNativeBrepHash":SHA,
            }
            file=root/"controller-grants"/(job["jobId"]+".json")
            file.write_text(json.dumps(grant),encoding="utf8")
            self.assertEqual(S.require_local_grant(
                b,job,folder,self.task,"2"*40),grant)
            for mutation in [
                dict(grant,taskBlobSha1="3"*40),
                dict(grant,projectSha256="f"*64),
                dict(grant,authorizationRef="USER_APPROVED_WRONG"),
            ]:
                file.write_text(json.dumps(mutation),encoding="utf8")
                with self.assertRaisesRegex(ValueError,"GRANT_NOT_EXACT_BLOB_BOUND"):
                    S.require_local_grant(b,job,folder,self.task,"2"*40)

    def test_historical_unknown_pair_blocks_without_mutating_sqlite(self):
        with TemporaryDirectory() as temp:
            p=Path(temp)/"journal.sqlite"
            from contextlib import closing
            with closing(sqlite3.connect(p)) as db:
                db.execute("CREATE TABLE scenes(scene_id TEXT PRIMARY KEY,state TEXT)")
                db.executemany("INSERT INTO scenes VALUES(?,?)",[
                    ("BDD_BULK150_GRID_AND_LINE_20261016","PARTIAL_OR_UNKNOWN_OUTCOME"),
                    ("MultiCopyFailed001","PARTIAL_OR_UNKNOWN_OUTCOME"),
                    ("CreatedAndSavedOne","PASS"),
                ])
                db.commit()
            data=p.read_bytes()
            unresolved=S.pending_ledger(p,["NextCreate001","NextSave001"])
            self.assertEqual(len(unresolved),2)
            self.assertEqual(p.read_bytes(),data)
            with self.assertRaisesRegex(ValueError,"NO_RETRY"):
                S.pending_ledger(p,["BDD_BULK150_GRID_AND_LINE_20261016",
                                   "NextSave001"])

    def test_approved_mutation_never_calls_archicad_with_two_unknown_scenes(self):
        import os
        from contextlib import closing
        from types import SimpleNamespace
        import archicad_project_accelerator as APA
        with TemporaryDirectory() as temp:
            root=Path(temp)
            folder=root/"attempt"
            folder.mkdir()
            (folder/"attempted.json").write_text(
                json.dumps({"sourceBlob":"1"*40}),encoding="utf8")
            task=source()
            job={"jobId":"ac29-secure-scoped-mutation",
                 "sourceTask":{"repo":"dvikt33-ux/safe-bim-layer",
                               "ref":"2"*40,"path":"examples/accelerator/test.json",
                               "blobSha1":"3"*40}}
            grant={
                "schema":"APA_AC29_LOCAL_SCOPED_NATIVE_GRANT_V1",
                "jobId":job["jobId"],"jobBlobSha1":"1"*40,
                "taskBlobSha1":"3"*40,"projectSha256":SHA,
                "authorizationRef":task["authorizationRef"],
                "command":task["command"],
                "sourcePlanHash":task["sourcePlanHash"],
                "expectedBeforeGuidSetHash":task["expectedBeforeGuidSetHash"],
                "expectedBeforeNativeBrepHash":task["expectedBeforeNativeBrepHash"]
            }
            (root/"controller-grants").mkdir()
            (root/"controller-grants"/(job["jobId"]+".json")).write_text(
                json.dumps(grant),encoding="utf8")
            ledger=root/"APA_BDD_Window1p8"/"apa_scene_writer.sqlite"
            ledger.parent.mkdir()
            with closing(sqlite3.connect(ledger)) as db:
                db.execute("CREATE TABLE scenes(scene_id TEXT PRIMARY KEY,state TEXT)")
                db.executemany("INSERT INTO scenes VALUES(?,?)",[
                    ("BDD_BULK150_GRID_AND_LINE_20261016",
                     "PARTIAL_OR_UNKNOWN_OUTCOME"),
                    ("FailedNativeMultiCopy20261017","PARTIAL_OR_UNKNOWN_OUTCOME")
                ])
                db.commit()
            stub=SimpleNamespace(
                ROOT=root,WORKING=Path(task["projectPath"]),ORIGINAL=root/"original.pln",
                SOURCE_SHA="c"*64,
                approved_saved_sha=lambda:SHA,
                approved_guid_count=lambda:298,
                remote_json=lambda *args:(task,"3"*40),
                sha=lambda p:("c"*64 if p==root/"original.pln" else SHA)
            )
            with patch.dict(os.environ,{"LOCALAPPDATA":str(root)}), \
                 patch.object(APA,"EvidenceAPI",
                              side_effect=AssertionError("NATIVE_API_CONSTRUCTED")):
                with self.assertRaisesRegex(ValueError,"PENDING_HISTORY"):
                    S.execute(stub,job,folder)
            with closing(sqlite3.connect(ledger)) as db:
                rows=db.execute("SELECT state FROM scenes ORDER BY scene_id").fetchall()
            self.assertEqual(rows,[
                ("PARTIAL_OR_UNKNOWN_OUTCOME",),
                ("PARTIAL_OR_UNKNOWN_OUTCOME",)])

    def test_bridge_ingress_accepts_native_preview_but_not_unpinned_mutation(self):
        now=datetime.now(timezone.utc)
        dates=lambda t:t.strftime("%Y-%m-%dT%H:%M:%SZ")
        base={
            "schema":"APA_AC29_AUTONOMOUS_JOB_V1",
            "jobId":"ac29-scope-preflight-read-only",
            "action":"SCOPED_NATIVE_REGISTRY_PREFLIGHT",
            "createdAt":dates(now-timedelta(seconds=30)),
            "expiresAt":dates(now+timedelta(hours=1)),
            "projectSha256":SHA,
            "sourceTask":None,
        }
        with patch.object(BRIDGE,"approved_saved_sha",return_value=SHA):
            self.assertEqual(
                BRIDGE.validate_job(base,base["jobId"])["action"],
                "SCOPED_NATIVE_REGISTRY_PREFLIGHT")
            requested=dict(base,action="APPROVED_SCOPED_NATIVE_MUTATION")
            with self.assertRaisesRegex(ValueError,"READ_TASK_NOT_PINNED"):
                BRIDGE.validate_job(requested,requested["jobId"])


if __name__=="__main__":
    from unittest import main
    main()
