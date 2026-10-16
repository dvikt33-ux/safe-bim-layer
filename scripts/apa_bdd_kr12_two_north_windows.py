#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BDD house KR-12 / block 1.7: add two north-facing native Windows via EXISTING APA.

Requires the previous window 1.8 SAVED in working PLN after its LIVE PASS.
Calls only existing archicad_project_accelerator.DynamicCommands/SceneWriter,
never direct Tapir writes. No new router, ledger or retry. The original PLN is
protected; working copy gets a verified byte backup before any write.
Two independent SQLite intent-before-write steps, native BREP readbacks.
--apply performs the 2 native writes; --publish sends results to private Github.
On success press Ctrl+S in working Archicad PLN. On failure DO NOT RETRY.
"""
from __future__ import annotations
import argparse,base64,hashlib,json,math,os,shutil,sqlite3,subprocess,sys,uuid
from datetime import datetime,timezone
from pathlib import Path

import archicad_project_accelerator as APA
import archicad_scene_run as RUN
import archicad_connected_components as C
import archicad_bim_documentation as D

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"docs/research/apa-results/bdd-house/APA_EXISTING_SCENE_WRITER_BASELINE_20261016.json"
SOURCE=ROOT/"docs/research/apa-results/bdd-house/KR12_NORTH_TWO_WINDOWS_TYPED_SOURCE_20261016.json"
SCHEMA=ROOT/"schemas/tapir-live-1.5.10/tapir-scene-live.json"
HOST="7b332594-ab82-43b4-bfc2-ab5ad549c2c9"
PREVIOUS="5c63fa89-c4a9-4ec5-811a-d989cf1d8626"
PREVIOUS_HOST="323703e9-2bf2-4488-a24d-0ba20760400d"
PREVIOUS_SCENE="BDD_KR12_W1P8_20261016_FIRST_NATIVE_WINDOW"
PREVIOUS_PASS_TIME=datetime(2026,10,16,17,17,0,tzinfo=timezone.utc).timestamp()
PORT=19727
STAGES=[
 {"name":"west-1600","sceneId":"BDD_KR12_NORTH_WINDOW_1600_NATIVE_20261016",
  "centerOffset":12.605,"sillHeight":.9,"width":1.6,"height":1.5},
 {"name":"middle-800","sceneId":"BDD_KR12_NORTH_WINDOW_800_NATIVE_20261016",
  "centerOffset":8.06,"sillHeight":.9,"width":.8,"height":1.5},
]
ROOT_LOCAL=Path(os.environ.get("LOCALAPPDATA",str(Path.home())))
LOCAL=ROOT_LOCAL/"APA_BDD_NorthWindowPair"
LEDGER=ROOT_LOCAL/"APA_BDD_Window1p8"/"apa_scene_writer.sqlite"
REPORT=LOCAL/"north_windows_report.json"
EVIDENCE=LOCAL/"native_api_readback"

def utc():return datetime.now(timezone.utc).isoformat()
def hashfile(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(2**20),b""):h.update(chunk)
    return h.hexdigest()
def writejson(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(".writing.tmp")
    temp.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding="utf-8")
    temp.replace(path)
def publish(path):
    remote="safe-bim-mailbox/gpt-live/results/apa-bdd-apa-north-windows-%s-%s.json"%(
      datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),uuid.uuid4().hex[:8])
    payload=path.with_suffix(".github-upload.tmp.json")
    try:
        writejson(payload,{"branch":"main",
            "message":"APA native north facade two Windows via shared SceneWriter",
            "content":base64.b64encode(path.read_bytes()).decode("ascii")})
        cp=subprocess.run(["gh","api","--method","PUT",
            "repos/dvikt33-ux/safe-bim-bridge/contents/"+remote,
            "--input",str(payload)],capture_output=True,text=True,timeout=150)
        if cp.returncode:raise RuntimeError("GITHUB_REPORT_UPLOAD_FAILED: "+cp.stderr[-400:])
    finally:payload.unlink(missing_ok=True)
    return "https://github.com/dvikt33-ux/safe-bim-bridge/blob/main/"+remote

def all_ids(api):
    rows=api("GetAllElements",{}).get("elements")
    if not isinstance(rows,list):raise ValueError("NATIVE_INVENTORY_UNAVAILABLE")
    result={}
    for item in rows:
        guid=item.get("elementId",{}).get("guid")
        if not isinstance(guid,str) or not guid or guid.lower() in result:
            raise ValueError("NATIVE_DUPLICATE_OR_MISSING_GUID")
        result[guid.lower()]=guid
    return result
def native_detail(api,guid):
    rows=api("GetDetailsOfElements",{
      "elements":[{"elementId":{"guid":guid}}]}).get("detailsOfElements")
    if not isinstance(rows,list) or len(rows)!=1 or not isinstance(rows[0],dict):
        raise ValueError("NATIVE_ELEMENT_DETAILS_MISSING")
    return rows[0]
def same(x,y):
    return isinstance(x,(int,float)) and math.isfinite(x) and abs(x-y)<.0001
def check_host(row):
    d=row.get("details") or {}
    if row.get("type")!="Wall" or row.get("floorIndex")!=0:
        raise ValueError("NORTH_WALL_NATIVE_TYPE_OR_STORY_CHANGED")
    for key,expected in [("height",3),("begThickness",.25),
                         ("endThickness",.25),("zCoordinate",-.1)]:
        if not same(d.get(key),expected):
            raise ValueError("NORTH_WALL_DIMENSION_CHANGED_"+key)
    for key,xy in [("begCoordinate",(14.28,9.38)),
                   ("endCoordinate",(0,9.38))]:
        val=d.get(key) or {}
        if not same(val.get("x"),xy[0]) or not same(val.get("y"),xy[1]):
            raise ValueError("NORTH_WALL_REFERENCE_LINE_CHANGED_"+key)
def check_window(row,expected,host):
    d=row.get("details") or {}
    if row.get("type")!="Window" or row.get("floorIndex")!=0 or (
      d.get("ownerElementId",{}).get("guid","").lower()!=host):
        raise ValueError("WINDOW_TYPE_STORY_OR_OWNER_NOT_VERIFIED")
    for key in ("width","height","sillHeight","centerOffset"):
        if not same(d.get(key),expected[key]):
            raise ValueError("WINDOW_NATIVE_DIMENSION_MISMATCH_"+key)
def baseline(binding):
    roles=binding["roles"]
    groups=[
      {g.lower() for g in roles["originalGuids"]},
      {g.lower() for s in roles["parent"] for g in s["physicalGuids"]},
      {g.lower() for g in roles["automaticChildGuids"]}]
    if tuple(map(len,groups))!=(21,125,115) or len(set.union(*groups))!=261:
        raise ValueError("SOURCE_261_GUID_ROLE_MISMATCH")
    known=set.union(*groups)
    if PREVIOUS in known or HOST not in groups[1]:
        raise ValueError("SOURCE_SAVED_BASELINE_INCONSISTENT")
    return known|{PREVIOUS}
def check_previous_ledger():
    if not LEDGER.exists():
        raise ValueError("FIRST_WINDOW_SCENE_WRITER_LEDGER_NOT_FOUND")
    with sqlite3.connect("file:"+LEDGER.as_posix()+"?mode=ro",uri=True) as db:
        row=db.execute("SELECT state FROM scenes WHERE scene_id=?",
                       (PREVIOUS_SCENE,)).fetchone()
        if row!=("PASS",):
            raise ValueError("FIRST_WINDOW_HAS_NO_SQLITE_PASS_RECORD")
        for stage in STAGES:
            if db.execute("SELECT state FROM scenes WHERE scene_id=?",
                          (stage["sceneId"],)).fetchone():
                raise ValueError("NEW_WINDOW_SCENE_ALREADY_RESERVED_NO_RETRY")
def stage_params(row):
    return {"ownerWallId":{"guid":HOST},
            "centerOffset":row["centerOffset"],
            "sillHeight":row["sillHeight"],
            "width":row["width"],"height":row["height"]}
def source_verify(doc):
    if doc.get("status")!="PDF_VECTOR_DIMENSION_CHAIN_PLAN_CORRELATED__NATIVE_WRITE_NOT_YET_RUN":
        raise ValueError("NORTH_WINDOW_SOURCE_STATUS_CHANGED")
    src=doc["openings"]
    if len(src)!=2:raise ValueError("SOURCE_REQUIRES_EXACTLY_TWO_WINDOWS")
    for s,c in zip(src,STAGES):
        d=s["nativeParameters"]
        if s["kind"]!="Window" or d!=stage_params(c) or not (
          s["frameEndSourceChainMm"]-s["frameBeginSourceChainMm"]==
          s["clearWidthMm"]+100):
            raise ValueError("SOURCE_CHAIN_OR_NATIVE_PARAMETERS_CHANGED")
        source_center=(s["frameBeginSourceChainMm"]+s["frameEndSourceChainMm"])/2
        if not same((source_center-50)/1000,14.28-c["centerOffset"]):
            raise ValueError("SOURCE_TO_NATIVE_REFERENCE_LINE_NOT_VALIDATED")

def task_for(params):
    return {"schemaVersion":"apa-native-task/1",
      "request":"BDD 2022 KR12 north wall 1.7 exact native opening hosted in saved Wall",
      "graph":{"operations":[
        {"id":"read-north-parent","command":"GetDetailsOfElements",
         "params":{"elements":[{"elementId":{"guid":HOST}}]}},
        {"id":"create-approved-north-window","command":"CreateWindows",
         "params":{"windowsData":[params]},
         "after":["read-north-parent"]}]}}

def main(args):
    if REPORT.exists():
        raise ValueError("NORTH_WINDOW_JOURNAL_ALREADY_EXISTS_NEVER_RERUN")
    binding=json.loads(BASE.read_text(encoding="utf-8"))
    doc=json.loads(SOURCE.read_text(encoding="utf-8"))
    source_verify(doc)
    active_path=Path(binding["target"]["workingPLN"])
    original_path=Path(binding["target"]["sourcePLN"])
    if not active_path.is_file() or not original_path.is_file():
        raise ValueError("SOURCE_OR_WORKING_PLN_FILE_MISSING")
    if hashfile(original_path)!=binding["target"]["sourceBaselineSha256"]:
        raise ValueError("ORIGINAL_PLN_CHANGED")
    if active_path.stat().st_mtime<=PREVIOUS_PASS_TIME:
        raise ValueError("SAVE_PREVIOUS_WINDOW_IN_WORKING_PLN_BEFORE_CONTINUING")
    backup=active_path.with_name(active_path.stem+".before-KR12-north-windows.pln")
    if backup.exists():
        raise ValueError("PRIOR_NORTH_WINDOWS_BACKUP_EXISTS_NEVER_RERUN")
    check_previous_ledger()
    before_disk=hashfile(active_path)
    RUN.bind_authorized_saved_copy(PORT,str(active_path),
        active_path.stem,before_disk,"BDD_20261016_2_NORTH_SOURCE_WINDOWS")
    from archicad import ACConnection
    conn=ACConnection.connect(PORT)
    if conn is None:raise ValueError("ARCHICAD_19727_CONNECTION_UNAVAILABLE")
    p=conn.commands.GetProductInfo()
    if int(p[0])!=29 or int(p[1])!=5101:
        raise ValueError("WRONG_ARCHICAD_MAJOR_OR_BUILD")
    EVIDENCE.mkdir(parents=True,exist_ok=False)
    api=APA.EvidenceAPI(APA.native_transport,EVIDENCE,execute=args.apply)
    current=all_ids(api)
    approved=baseline(binding)
    if len(current)!=262 or set(current)!=approved:
        raise ValueError("NEED_EXACTLY_262_KNOWN_NATIVE_GUIDS_IN_ACTIVE_PLN")
    check_host(native_detail(api,current[HOST]))
    check_window(native_detail(api,current[PREVIOUS]),
       {"width":1.5,"height":.9,"sillHeight":1.1,"centerOffset":5.01},PREVIOUS_HOST)
    proj=RUN.guarded_project_for_read(api)
    if proj["activeViewStoryIndex"] not in (-1,0):
        raise ValueError("WINDOW_WRITES_REQUIRE_3D_OR_FIRST_FLOOR_ACTIVE")
    router=APA.native_command_router(SCHEMA,include_functional_modules=False)
    for cmd,effect,impact in [("GetDetailsOfElements","READ_ONLY","READ_ONLY"),
                              ("CreateWindows","CREATE","MODEL")]:
        router.review_policy(cmd,effect,impact,{
          "source":"Pinned Tapir 1.5.10 native Windows and Details provider",
          "sha256":router.contract_hash(cmd)})
    for row in STAGES:
        plan=APA.prepare_native_task(router,task_for(stage_params(row)))
        if len(plan["workflow"]["graph"]["operations"])!=2:
            raise ValueError("APA_GRAPH_NOT_COMPILED")
    result={"schema":"apa.bdd.kr12.two-north-windows-execute.v1",
       "startedAtUTC":utc(),"status":"PREFLIGHT_PASS",
       "targetWorkingPLN":str(active_path),
       "prewriteSHA256":before_disk,"originalUnchanged":True,
       "initialGUIDCount":262,
       "expectedFinalGUIDCount":264,
       "westPreviousWindowGuid":PREVIOUS,
       "hostGuid":HOST,
       "nativeWriteCount":0,
       "completedStages":[],"pending":len(STAGES),"saveRequired":False,
       "builtThrough":"EXISTING_APA_DYNAMIC_COMMANDS_SCENE_WRITER_SQLITE"}
    if not args.apply:
        writejson(REPORT,result)
        print("DRY RUN: 262 GUIDs; previous window present; 2 source-bound windows verified",flush=True)
        if args.publish:print("PRIVATE GITHUB NORTH WINDOWS PREFLIGHT:",publish(REPORT),flush=True)
        return 0
    shutil.copy2(active_path,backup)
    if hashfile(backup)!=before_disk:
        raise ValueError("WORKING_PLN_BACKUP_CHECKSUM_FAILED_NO_WRITES")
    result["backupPath"]=str(backup)
    result["status"]="BACKED_UP_NATIVE_WRITES_START"
    writejson(REPORT,result)
    writer=RUN.SceneWriter(api,LEDGER,schema_path=SCHEMA,
                           allow_3d_view_for_write=True)
    for stage in STAGES:
        params=stage_params(stage)
        scene_id=stage["sceneId"]
        # Recheck byte baseline and exact current in-memory model at each step.
        if hashfile(active_path)!=before_disk or all_ids(api)!=current:
            raise ValueError("NATIVE_MODEL_OR_SAVED_PLN_CHANGED_BETWEEN_STAGES")
        before_host=native_detail(api,current[HOST])
        check_host(before_host)
        task=task_for(params)
        plan=APA.prepare_native_task(router,task)
        ticket=router.prepare("CreateWindows",{"windowsData":[params]})
        retained=set(current)-{HOST}
        native=D.capture_full_model(api,sorted(retained))
        signatures=C.retained_geometry_signatures(native,sorted(retained))
        if set(signatures)!=retained:
            raise ValueError("FULL_NATIVE_RETAINED_SIGNATURES_INCOMPLETE")
        host_body=next((x for x in native["elements"]
                        if x["guid"].lower()==HOST),None)
        if not host_body or not host_body.get("bodies"):
            raise ValueError("NATIVE_HOST_WALL_BREP_MISSING")
        geom_before=RUN.digest(C.ROOF.geometry_signature(host_body))
        if all_ids(api)!=current:
            raise ValueError("GUID_DRIFT_AFTER_NATIVE_BREP_READ")
        new_guid=[None]
        def before(native_api):
            if set(all_ids(native_api))!=set(current):
                raise ValueError("MODEL_CHANGED_IMMEDIATELY_BEFORE_WINDOW")
            check_host(native_detail(native_api,current[HOST]))
            return {"status":"SOURCE_HOST_WALL_AND_262_PLUS_NATIVE_GUIDS_PASS",
                "source":"KR-12 2022 block1.7", "offsetMeters":params["centerOffset"]}
        def after(reply,prior):
            rows=reply.get("elements")
            if not isinstance(rows,list) or len(rows)!=1:
                raise ValueError("WINDOW_RESPONSE_UNEXPECTED")
            g=rows[0].get("elementId",{}).get("guid")
            if not isinstance(g,str) or not g:
                raise ValueError("WINDOW_NATIVE_GUID_NOT_RETURNED")
            new_guid[0]=g.lower()
            check_window(native_detail(api,g),params,HOST)
            actual=all_ids(api)
            if set(actual)!=set(current)|{g.lower()}:
                raise ValueError("WINDOW_GUID_DELTA_NOT_EXACTLY_ONE")
            after_dump=D.capture_full_model(api,[HOST])
            host_after=next((x for x in after_dump["elements"]
                             if x["guid"].lower()==HOST),None)
            if not host_after or not host_after.get("bodies"):
                raise ValueError("AFTER_CREATE_HOST_BREP_NOT_READ")
            if geom_before==RUN.digest(C.ROOF.geometry_signature(host_after)):
                raise ValueError("HOST_BREP_NOT_CHANGED_BY_NEW_WINDOW")
            return {"status":"ONE_NATIVE_WINDOW_SOURCE_AND_HOST_BREP_PASS",
                "windowGuid":g,"hostGuid":HOST,
                "parameters":params,"modelGUIDCount":len(actual)}
        state=router.execute(writer,scene_id,ticket,[HOST],
            signatures,before_disk,
            "USER_AUTHORIZED_KR12_NORTH_TWO_WINDOWS_20261016",
            "MODEL",after,verify_before=before)
        result["lastSceneId"]=scene_id
        result["lastSceneResult"]=state
        if state["status"]!="PASS":
            result["status"]="PARTIAL_OR_UNKNOWN_OUTCOME_DO_NOT_RETRY"
            writejson(REPORT,result)
            raise ValueError("SceneWriter failed; do not rerun: "+state["status"])
        result["completedStages"].append({
            "name":stage["name"],"sceneId":scene_id,"guid":new_guid[0],
            "hostGuid":HOST,"params":params,"nativeReceipt":state["readback"]})
        result["nativeWriteCount"]+=1
        result["pending"]=len(STAGES)-len(result["completedStages"])
        result["status"]="PARTIAL_NATIVE_PASS_UNSAVED" if result["pending"] else "TWO_NATIVE_NORTH_WINDOWS_PASS_UNSAVED"
        result["saveRequired"]=True
        writejson(REPORT,result)
        current=all_ids(api)
        print("NATIVE WINDOW PASS",stage["name"],new_guid[0],flush=True)
    if len(current)!=264 or hashfile(original_path)!=binding["target"]["sourceBaselineSha256"]:
        raise ValueError("FINAL_INVENTORY_OR_ORIGINAL_SHA_MISMATCH")
    result["finishedAtUTC"]=utc()
    result["finalGUIDCount"]=264
    result["originalUnchanged"]=True
    writejson(REPORT,result)
    if args.publish:print("PRIVATE GITHUB TWO NORTH WINDOWS:",publish(REPORT),flush=True)
    print("TWO NATIVE WINDOWS PASS; SAVE THE WORKING PLN NOW (Ctrl+S)",flush=True)
    return 0

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply",action="store_true")
    parser.add_argument("--publish",action="store_true")
    args=parser.parse_args()
    try:
        sys.exit(main(args))
    except Exception as exc:
        print("APA NORTH WINDOWS BLOCKED:",type(exc).__name__,str(exc),file=sys.stderr,flush=True)
        if args.publish:
            try:
                state=json.loads(REPORT.read_text(encoding="utf-8")) if REPORT.exists() else {
                    "schema":"apa.bdd.kr12.two-north-windows-execute.v1",
                    "status":"PREFLIGHT_BLOCKED_NO_WRITES_PROVEN"}
                state.update(errorType=type(exc).__name__,error=str(exc)[:900],
                            errorAtUTC=utc(),
                            retry="NEVER_WITHOUT_RECONCILIATION",
                            recommendedAction="Do not close Archicad or rerun; inspect SQLite journal and live model")
                if state.get("status") not in ("PREFLIGHT_BLOCKED_NO_WRITES_PROVEN",):
                    state["status"]="BLOCKED_POSSIBLE_PARTIAL_NATIVE_WRITE"
                writejson(REPORT,state)
                print("PRIVATE GITHUB NORTH WINDOW FAILURE:",publish(REPORT),flush=True)
            except Exception as report_error:
                print("GITHUB_REPORT_FAILURE:",str(report_error)[:250],file=sys.stderr,flush=True)
        sys.exit(2)
