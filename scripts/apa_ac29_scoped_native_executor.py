"""One reviewed native mutation through installed APA DynamicCommands + SceneWriter.

A GitHub task is immutable data, NOT local permission. The worker calls this
only after a local grant bound to the job/task SHA-1 blobs. No UNKNOWN scene
is ignored or rewritten. After native typed/BREP PASS, SaveProject is separately
journaled using the already installed GuardedSaveTransport.
"""
from __future__ import annotations
import json
import os
import re
import sqlite3
from contextlib import closing
from pathlib import Path

SUPPORTED={
    "CreateColumns":("CREATE","VerifiedNativeColumns"),
    "CreateBeams":("CREATE","VerifiedNativeBasicBeam"),
    "CreateWalls":("CREATE","VerifiedNativeBasicWall"),
    "CreateRoofs":("CREATE","VerifiedNativeBasicRoof"),
    "ModifySlabs":("MODIFY","VerifiedBasicSlabMaterial"),
    "MoveElements":("MODIFY","VerifiedNativeTranslation"),
}
ID=re.compile(r"^[A-Za-z][A-Za-z0-9_-]{3,79}$")
HASH=re.compile(r"^[a-f0-9]{64}$")
GUID=re.compile(r"^[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}$")

def need(ok,why):
    if not ok:raise ValueError(why)

def qualify_task(task,bridge):
    keys={"schema","projectSha256","projectPath","command","parameters",
          "sourcePlanHash","parametersHash","commandContractHash",
          "expectedBeforeGuidSetHash","expectedBeforeNativeBrepHash",
          "expectedGuidCount","affectedGuids","sceneId","saveSceneId",
          "stepId","authorizationRef","sourceEvidenceRef"}
    need(isinstance(task,dict) and set(task)==keys and
         task["schema"]=="APA_AC29_SCOPED_NATIVE_TASK_V1" and
         task["projectSha256"]==bridge.approved_saved_sha() and
         task["projectPath"]==str(bridge.WORKING) and
         task["expectedGuidCount"]==bridge.approved_guid_count() and
         all(isinstance(task[k],str) and HASH.fullmatch(task[k])
             for k in ("sourcePlanHash","parametersHash","commandContractHash",
                 "expectedBeforeGuidSetHash","expectedBeforeNativeBrepHash")) and
         all(isinstance(task[k],str) and ID.fullmatch(task[k])
             for k in ("sceneId","saveSceneId","stepId")) and
         task["sceneId"]!=task["saveSceneId"] and
         task["command"] in SUPPORTED and
         isinstance(task["parameters"],dict) and
         isinstance(task["affectedGuids"],list) and
         len(task["affectedGuids"])<=200 and
         len(set(task["affectedGuids"]))==len(task["affectedGuids"]) and
         all(isinstance(g,str) and GUID.fullmatch(g)
             for g in task["affectedGuids"]) and
         bool(task["affectedGuids"])==(SUPPORTED[task["command"]][0]=="MODIFY") and
         isinstance(task["authorizationRef"],str) and
         task["authorizationRef"].startswith("USER_APPROVED_") and
         len(task["authorizationRef"])<=200 and
         isinstance(task["sourceEvidenceRef"],str) and
         task["sourceEvidenceRef"].startswith(
             "https://github.com/dvikt33-ux/safe-bim-layer/"),
         "SCOPED_NATIVE_TASK_EXACT_SOURCE_SCHEMA_OR_PROJECT_INVALID")
    return task

def require_local_grant(bridge,job,folder,task,task_blob):
    path=bridge.ROOT/"controller-grants"/(job["jobId"]+".json")
    need(path.is_file(),"SCOPED_NATIVE_LOCAL_BLOB_BOUND_GRANT_REQUIRED")
    actual=json.loads(path.read_text(encoding="utf8"))
    attempted=json.loads((folder/"attempted.json").read_text(encoding="utf8"))
    expected={
        "schema":"APA_AC29_LOCAL_SCOPED_NATIVE_GRANT_V1",
        "jobId":job["jobId"],
        "jobBlobSha1":attempted["sourceBlob"],
        "taskBlobSha1":task_blob,
        "projectSha256":task["projectSha256"],
        "authorizationRef":task["authorizationRef"],
        "command":task["command"],
        "sourcePlanHash":task["sourcePlanHash"],
        "expectedBeforeGuidSetHash":task["expectedBeforeGuidSetHash"],
        "expectedBeforeNativeBrepHash":task["expectedBeforeNativeBrepHash"],
    }
    need(actual==expected,"SCOPED_NATIVE_LOCAL_GRANT_NOT_EXACT_BLOB_BOUND")
    return actual

def pending_ledger(ledger,new_ids):
    need(ledger.is_file(),"SCOPED_NATIVE_ORIGINAL_SQLITE_REQUIRED")
    with closing(sqlite3.connect(
        f"file:{ledger.as_posix()}?mode=ro",uri=True)) as db:
        rows=db.execute("SELECT scene_id,state FROM scenes").fetchall()
    need(not set(new_ids)&{name for name,_ in rows},
         "SCOPED_NATIVE_SCENE_ALREADY_USED_NO_RETRY")
    return [{"sceneId":name,"state":state}
            for name,state in rows if state!="PASS"]

def execute(bridge,job,folder):
    task,blob=bridge.remote_json(
        job["sourceTask"]["repo"],job["sourceTask"]["path"],
        job["sourceTask"]["ref"],job["sourceTask"]["blobSha1"])
    qualify_task(task,bridge)
    require_local_grant(bridge,job,folder,task,blob)
    need(bridge.sha(bridge.WORKING)==task["projectSha256"] and
         bridge.sha(bridge.ORIGINAL)==bridge.SOURCE_SHA,
         "SCOPED_NATIVE_SAVED_PLN_DRIFT")

    # The original BDD ledger presently contains two historical UNKNOWNs.
    # Until separately reconciled from their actual SQLite/RAW logs, no
    # mutation can be dispatched, even with a valid local grant.
    ledger=Path(os.environ["LOCALAPPDATA"])/"APA_BDD_Window1p8"/"apa_scene_writer.sqlite"
    pending=pending_ledger(ledger,[task["sceneId"],task["saveSceneId"]])
    need(not pending,"SCOPED_NATIVE_PENDING_HISTORY_REQUIRES_INDEPENDENT_RECONCILIATION:"+
         ",".join(row["sceneId"] for row in pending))

    import archicad_project_accelerator as APA
    import archicad_scene_run as RUN
    import archicad_bim_documentation as D
    import archicad_connected_components as C
    import apa_ac29_reusable_native_copy as COPY

    effect,verifier_id=SUPPORTED[task["command"]]
    from apa_ac29_dynamic_native_verifiers import installed_verifiers
    registry=installed_verifiers()
    need(verifier_id in registry and registry[verifier_id].command==task["command"],
         "SCOPED_NATIVE_CODE_OWNED_VERIFIER_NOT_INSTALLED")
    schema=bridge.ROOT/"schemas/tapir-live-1.5.10/tapir-scene-live.json"
    need(schema.is_file(),"SCOPED_NATIVE_INSTALLED_CATALOG_MISSING")
    RUN.bind_authorized_saved_copy(19727,str(bridge.WORKING),
        bridge.WORKING.stem,task["projectSha256"],task["authorizationRef"])
    guard=COPY.GuardedSaveTransport(
        APA.native_transport,RUN.bind_authorized_saved_copy,
        bridge.WORKING,bridge.ORIGINAL,lambda:bridge.sha(bridge.WORKING),
        lambda:bridge.sha(bridge.ORIGINAL),bridge.WORKING.stem,19727,
        task["authorizationRef"])
    output=folder/"scoped-execution"
    output.mkdir()
    api=APA.EvidenceAPI(guard,output,execute=True)
    need(APA.archicad29(api).get("buildNumber")==5101,
         "SCOPED_NATIVE_ARCHICAD_BUILD_NOT_VERIFIED")
    router=APA.native_command_router(schema,include_functional_modules=False)
    need(router.contract_hash(task["command"])==task["commandContractHash"],
         "SCOPED_NATIVE_NATIVE_CONTRACT_HASH_DRIFT")
    source=task["sourceEvidenceRef"]
    router.review_policy(task["command"],effect,"MODEL",{
        "source":source,"sha256":task["commandContractHash"]})
    router.review_policy("SaveProject","TRANSACTION","PROJECT",{
        "source":source,"sha256":router.contract_hash("SaveProject")})
    graph={"operations":[{
        "id":task["stepId"],"command":task["command"],
        "params":task["parameters"],"after":[]}]}
    preview=APA.prepare_native_task(router,{
        "schemaVersion":"apa-native-task/1",
        "request":"Exact reviewed AC29 source-qualified mutation",
        "graph":graph})
    need(preview["sourcePlanHash"]==task["sourcePlanHash"] and
         RUN.digest(task["parameters"])==task["parametersHash"],
         "SCOPED_NATIVE_APPROVED_GRAPH_OR_PARAMETERS_CHANGED")
    old=sorted(APA.inventory_guids(api))
    need(len(old)==task["expectedGuidCount"] and
         RUN.digest(old)==task["expectedBeforeGuidSetHash"],
         "SCOPED_NATIVE_APPROVED_GUID_SET_DRIFT")
    prior=D.capture_full_model(api,old)
    nodes={e["guid"].lower():e for e in prior["elements"]}
    need(len(nodes)==len(old) and set(nodes)==set(old) and
         RUN.digest({g:C.ROOF.geometry_signature(nodes[g]) for g in old})==
             task["expectedBeforeNativeBrepHash"],
         "SCOPED_NATIVE_APPROVED_PREWRITE_BREP_DRIFT")
    affected=task["affectedGuids"]
    need(set(affected)<=set(old),"SCOPED_NATIVE_AFFECTED_GUID_NOT_IN_MODEL")
    spec={
        "schemaVersion":"apa-ac29-dynamic-mutation-scope/1",
        "projectSha256":task["projectSha256"],
        "sourcePlanHash":task["sourcePlanHash"],
        "authorizationRef":task["authorizationRef"],
        "sourceEvidenceRef":source,
        "sceneId":task["sceneId"],"stepId":task["stepId"],
        "command":task["command"],"effect":effect,"impact":"MODEL",
        "commandContractHash":task["commandContractHash"],
        "parametersHash":task["parametersHash"],
        "expectedBeforeGuidSetHash":task["expectedBeforeGuidSetHash"],
        "expectedBeforeNativeBrepHash":task["expectedBeforeNativeBrepHash"],
        "affectedGuids":affected,
        "retainedGuids":sorted(set(old)-set(affected)),
        "verifierId":verifier_id,
    }
    writer=RUN.SceneWriter(api,ledger,schema_path=schema,
                           allow_3d_view_for_write=True)
    result=APA.run_scoped_native_task(
        router,api,preview,writer,spec,
        approved_project_sha=task["projectSha256"],
        local_authorization=task["authorizationRef"],
        current_project_sha=lambda:bridge.sha(bridge.WORKING))
    need(result.get("status")=="WORKFLOW_CALLABLE_VERIFIED",
         "SCOPED_NATIVE_UNKNOWN_OUTCOME_NEVER_REPEAT_OR_SAVE")
    ids=sorted(APA.inventory_guids(api))
    full=D.capture_full_model(api,ids)
    signatures=C.retained_geometry_signatures(full,ids)
    need(set(signatures)==set(ids),"SCOPED_NATIVE_COMPLETE_AFTER_BREP_MISSING")
    with closing(sqlite3.connect(f"file:{ledger.as_posix()}?mode=ro",uri=True)) as db:
        journal=db.execute("SELECT state,result FROM scenes WHERE scene_id=?",
                           (task["sceneId"],)).fetchone()
    nodes={r["guid"].lower():r for r in full["elements"]}
    need(journal is not None and journal[0]=="PASS" and
         json.loads(journal[1]).get("readback",{}).get("afterNativeBrepHash")==
         RUN.digest({g:C.ROOF.geometry_signature(nodes[g]) for g in ids}),
         "SCOPED_NATIVE_INDEPENDENT_JOURNAL_BREP_CHANGED")
    guard.enable_after_verified_copy()
    def before_save(live):
        need(bridge.sha(bridge.WORKING)==task["projectSha256"] and
             sorted(APA.inventory_guids(live))==ids and
             C.retained_geometry_signatures(D.capture_full_model(live,ids),ids)==signatures,
             "SCOPED_NATIVE_PRE_SAVE_MODEL_DRIFT")
        return {"status":"SCOPED_NATIVE_VERIFIED_BEFORE_SAVE_PASS"}
    def after_save(reply,_):
        need(reply=={"success":True} and guard.new_saved_sha and
             bridge.sha(bridge.WORKING)==guard.new_saved_sha and
             bridge.sha(bridge.ORIGINAL)==bridge.SOURCE_SHA,
             "SCOPED_NATIVE_GUARDED_SAVE_NOT_CONFIRMED")
        return {"status":"SCOPED_NATIVE_GUARDED_SAVE_READBACK_PASS",
                "savedSha256":guard.new_saved_sha}
    saved=router.execute(writer,task["saveSceneId"],
        router.prepare("SaveProject",{}),[],signatures,
        task["projectSha256"],task["authorizationRef"],
        "PROJECT",after_save,verify_before=before_save)
    need(saved.get("status")=="PASS" and api.calls["SaveProject"]==1,
         "SCOPED_NATIVE_SAVE_UNKNOWN_NO_RETRY")
    return {"status":"SCOPED_NATIVE_VERIFIED_MODEL_AND_SAVE_PASS",
            "command":task["command"],"sourceTaskBlob":blob,
            "finalGuidCount":len(ids),"savedSha256":guard.new_saved_sha,
            "modelWrites":1,"nativeSaveCalls":1,
            "authorizedNativeExecution":True,"automaticRetry":False}
