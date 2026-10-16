#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BDD house first exact native window, using installed APA DynamicCommands AND SceneWriter.

ONE existing west wall is host, no walls are created/deleted/modified directly.
Uses Archicad 29 on port 19727, existing 261-GUID working PLN, 2022 KR-10/12
source (block 1.8). Native CreateWindows is permitted ONLY via:
  archicad_project_accelerator.native_command_router()
  archicad_project_accelerator.prepare_native_task()
  archicad_dynamic_commands.DynamicCommands.execute()
  archicad_scene_run.SceneWriter.execute_bound_operation()  # SQLite intent
No own transport, writer, routing, or retry loop.

--apply is required to issue the ONE native CreateWindows command.
The working PLN is backed up byte-for-byte BEFORE the write. No source PLN
modification, no automatic replay of uncertain results. Does not call SaveProject:
the user MUST save the working PLN once the verified window appears.
--publish stores success/error to the private GitHub mailbox.
"""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

import archicad_project_accelerator as APA
import archicad_scene_run as RUN
import archicad_connected_components as C
import archicad_bim_documentation as D

ROOT=Path(__file__).resolve().parents[1]
BINDING=ROOT/"docs/research/apa-results/bdd-house/APA_EXISTING_SCENE_WRITER_BASELINE_20261016.json"
SOURCE_INTENT=ROOT/"docs/research/apa-results/bdd-house/APA_KR12_BLOCK_1P8_FIRST_WINDOW_INTENT.json"
SCHEMA=ROOT/"schemas/tapir-live-1.5.10/tapir-scene-live.json"
PORT=19727
WALL_GUID="323703e9-2bf2-4488-a24d-0ba20760400d"
OP={"ownerWallId":{"guid":WALL_GUID},"centerOffset":5.01,
    "sillHeight":1.1,"width":1.5,"height":0.9}
STORY=0
SCENE_ID="BDD_KR12_W1P8_20261016_FIRST_NATIVE_WINDOW"
LOCAL=Path(os.environ.get("LOCALAPPDATA",str(Path.home()))) / "APA_BDD_Window1p8"
LEDGER=LOCAL/"apa_scene_writer.sqlite"
REPORT=LOCAL/"window_1p8_report.json"
BEFORE=LOCAL/"approved_before_window.pln"
READ_CMDS={"GetProjectInfo","GetStories","GetAllElements","GetDetailsOfElements",
           "Get3DBoundingBoxes","GetAddOnVersion","GetModelDumpV1"}

def utc():
    return datetime.now(timezone.utc).isoformat()

def checksum(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for c in iter(lambda:f.read(2**20),b""):h.update(c)
    return h.hexdigest()

def save(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    p=path.with_suffix(".writing.tmp")
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf8")
    p.replace(path)

def publish(path):
    p=Path(path)
    dest="safe-bim-mailbox/gpt-live/results/apa-bdd-scene-writer-window-1p8-%s-%s.json"%(
       datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),uuid.uuid4().hex[:7])
    payload=p.with_suffix(".github.tmp.json")
    try:
        save(payload,{"branch":"main","message":"BDD APA native Window 1.8 source-grounded write report",
                      "content":base64.b64encode(p.read_bytes()).decode("ascii")})
        cp=subprocess.run(["gh","api","--method","PUT",
                           "repos/dvikt33-ux/safe-bim-bridge/contents/"+dest,
                           "--input",str(payload)],capture_output=True,text=True,timeout=150)
        if cp.returncode:raise RuntimeError(cp.stderr[-650:])
    finally:payload.unlink(missing_ok=True)
    return "https://github.com/dvikt33-ux/safe-bim-bridge/blob/main/"+dest

def ids(api):
    res=api("GetAllElements",{}).get("elements")
    if not isinstance(res,list):raise ValueError("NATIVE_ALL_ELEMENTS_UNAVAILABLE")
    out={}
    for x in res:
        g=x.get("elementId",{}).get("guid")
        if not isinstance(g,str) or not g or g.lower() in out:
            raise ValueError("NATIVE_DUPLICATE_OR_MISSING_GUID")
        out[g.lower()]=g
    return out

def single_detail(api,guid):
    res=api("GetDetailsOfElements",
            {"elements":[{"elementId":{"guid":guid}}]}).get("detailsOfElements")
    if not isinstance(res,list) or len(res)!=1 or not isinstance(res[0],dict):
        raise ValueError("WINDOW_OR_HOST_DETAIL_UNAVAILABLE")
    return res[0]

def pin_story_for_write(api):
    # BDD script uses the narrowly opt-in SceneWriter guard allowing 3D
    # after a SHA-pinned exact-copy authorization. Upper-story views are
    # still rejected; project topology/first-floor Z remain verified.
    b=RUN.guarded_project_for_read(api)
    if b.get("storyIndex")!=0 or b.get("activeViewStoryIndex") not in (0,-1):
        raise ValueError("WRITE_REQUIRES_PINNED_FIRST_STORY_OR_3D")
    if not RUN.authorized_authored_target(RUN.EXPECTED_PATH):
        raise ValueError("WRITER_SAVED_SHA_AUTHORIZATION_NOT_VALID")
    return b

def verify_unchanged_host(row):
    d=row.get("details") or {}
    if row.get("type")!="Wall" or row.get("floorIndex")!=0:
        raise ValueError("WRONG_EXISTING_HOST_WALL_TYPE")
    for field,expected in (
        ("height",3.0),("begThickness",.25),("zCoordinate",-.1)
    ):
        if not isinstance(d.get(field),(int,float)) or abs(d[field]-expected)>0.00001:
            raise ValueError("EXISTING_WALL_GEOMETRY_CHANGED:"+field)
    for key,xy in (("begCoordinate",{"x":0,"y":9.38}),
                   ("endCoordinate",{"x":0,"y":0})):
        if not all(abs(d.get(key,{}).get(k,1e10)-v)<1e-6 for k,v in xy.items()):
            raise ValueError("EXISTING_HOST_DIRECTION_CHANGED:"+key)
    return True

def approved_guids(binding):
    roles=binding["roles"]
    ids0={g.lower() for g in roles["originalGuids"]}
    ids1={g.lower() for s in roles["parent"] for g in s["physicalGuids"]}
    ids2={g.lower() for g in roles["automaticChildGuids"]}
    if tuple(map(len,(ids0,ids1,ids2)))!=(21,125,115) or len(ids0|ids1|ids2)!=261:
        raise ValueError("261_GUID_BASELINE_MISMATCH")
    return ids0|ids1|ids2

def create_task():
    # Standard APA BIM Graph: native read of existing host precedes hosted CREATE.
    return {"schemaVersion":"apa-native-task/1",
      "request":"2022 KR-12 1.8 block single west facade window, 1500x900mm, sill +1.100, existing host GUID",
      "graph":{"operations":[
         {"id":"west-host-preflight","command":"GetDetailsOfElements",
          "params":{"elements":[{"elementId":{"guid":WALL_GUID}}]}},
         {"id":"west-window-1p8","command":"CreateWindows",
          "params":{"windowsData":[OP]},"after":["west-host-preflight"]}
       ]}}

def run(args):
    LOCAL.mkdir(parents=True,exist_ok=True)
    source=json.loads(SOURCE_INTENT.read_text(encoding="utf8"))
    binding=json.loads(BINDING.read_text(encoding="utf8"))
    target=Path(binding["target"]["workingPLN"])
    original=Path(binding["target"]["sourcePLN"])
    if not target.is_file() or not original.is_file():
        raise ValueError("APPROVED_PLN_PATH_MISSING")
    if checksum(original)!=binding["target"]["sourceBaselineSha256"]:
        raise ValueError("PROTECTED_ORIGINAL_CHANGED")
    if source["nativeWindowIntent"]["element"]!=OP or source["nativeHost"]["guid"].lower()!=WALL_GUID:
        raise ValueError("SOURCE_BOUND_WINDOW_INTENT_CHANGED")
    baseline=approved_guids(binding)
    if WALL_GUID not in baseline:raise ValueError("HOST_NOT_IN_SAVED_BASELINE")
    saved_sha=checksum(target)
    RUN.bind_authorized_saved_copy(PORT,str(target),target.stem,saved_sha,
        "USER_APPROVED_BDD_SINGLE_SOURCE_WINDOW_KR12_20261016")
    from archicad import ACConnection
    conn=ACConnection.connect(PORT)
    if conn is None:raise ValueError("EXPECTED_ARCHICAD_PORT_19727_NOT_CONNECTED")
    product=conn.commands.GetProductInfo()
    if int(product[0])!=29 or int(product[1])!=5101:
        raise ValueError("EXPECTED_ARCHICAD29_BUILD5101_REQUIRED")
    # Existing code-owned API/transport, not a parallel Tapir client.
    evidence=LOCAL/("evidence-"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    evidence.mkdir(parents=True,exist_ok=False)
    api=APA.EvidenceAPI(APA.native_transport,evidence,execute=args.apply)
    current=ids(api)
    if set(current)!=baseline:raise ValueError("261_GUID_MODEL_DRIFT_NO_NEW_WRITES")
    # Native writes from 3D are allowed only by the exact-copy opt-in
    # SceneWriter binding, never by merely omitting the active-story check.
    identity=pin_story_for_write(api)
    host_before=single_detail(api,current[WALL_GUID])
    verify_unchanged_host(host_before)

    router=APA.native_command_router(SCHEMA,include_functional_modules=False)
    for cmd in ("GetDetailsOfElements","CreateWindows"):
        router.review_policy(cmd,"READ_ONLY" if cmd.startswith("Get") else "CREATE",
          "READ_ONLY" if cmd.startswith("Get") else "MODEL",
          {"source":"Tapir 1.5.10 provider source-reviewed native command contract",
           "sha256":router.contract_hash(cmd)})
    task=create_task()
    preview=APA.prepare_native_task(router,task)
    window_ticket=router.prepare("CreateWindows",{"windowsData":[OP]})
    if window_ticket["effect"]!="CREATE" or len(preview["workflow"]["graph"]["operations"])!=2:
        raise ValueError("APA_BIM_GRAPH_WINDOW_INTENT_NOT_QUALIFIED")
    # Read project documentation via the existing router, not a separate API.
    readticket=router.prepare("GetDetailsOfElements",
                             {"elements":[{"elementId":{"guid":WALL_GUID}}]})
    nativehost=router.read(api,readticket,reviewed_read_only=True)
    verify_unchanged_host(nativehost["detailsOfElements"][0])

    report={"schema":"apa.bdd.first-native-window-execution.v1",
       "atUTC":utc(),"modelOriginalGuidCount":261,
       "sourcePDF":"2022 KR-10 plan / KR-12 block 1.8 wall elevation",
       "sourceMeasuredOpening":{"width":1.5,"height":.9,"sill":1.1},
       "nativeHostGuid":WALL_GUID,"nativeCenterOffsetM":5.01,
       "worldCenter":{"x":0,"y":4.37},
       "planHash":preview["sourcePlanHash"],
       "dynamicCommandHash":window_ticket["hash"],
       "targetPath":str(target),"targetSavedSHA256Before":saved_sha,
       "sourceOriginalSHA256":binding["target"]["sourceBaselineSha256"],
       "apaModules":["archicad_project_accelerator","archicad_dynamic_commands",
                     "archicad_bim_graph","archicad_scene_run.SceneWriter"],
       "result":"DRY_RUN_NO_WRITES" if not args.apply else "PREPARED_NOT_EXECUTED"}
    save(REPORT,report)
    if not args.apply:
        print("APA BIM GRAPH & HOST PREFLIGHT PASS: NO BIM WRITES",flush=True)
        if args.publish:print("PRIVATE GITHUB APA WINDOW DRY:",publish(REPORT),flush=True)
        return 0

    # One-shot durable barrier; refused on any rerun. Even a failed native
    # response may have already modified the in-memory model.
    if LEDGER.exists() or BEFORE.exists():
        raise ValueError("PREVIOUS_SCENE_OR_BACKUP_EXISTS_NEVER_REPLAY")
    shutil.copy2(target,BEFORE)
    if checksum(BEFORE)!=saved_sha:
        raise ValueError("BACKUP_BYTES_FAILED_BEFORE_NATIVE_WRITE")

    retained=baseline-{WALL_GUID}
    native=D.capture_full_model(api,sorted(retained))
    signatures=C.retained_geometry_signatures(native,sorted(retained))
    if set(signatures)!=retained:
        raise ValueError("NATIVE_RETAINED_SIGNATURES_NOT_COMPLETE")
    # The native dump may activate 3D view. The narrowly approved writer
    # validates the same exact PLN/SHA/story topology without a UI switch.
    pin_story_for_write(api)
    if ids(api)!=current:raise ValueError("MODEL_DRIFT_AFTER_NATIVE_DUMP")
    host_body_before=next((e for e in native["elements"]
                           if e["guid"].lower()==WALL_GUID),None)
    if not host_body_before or not host_body_before.get("bodies"):
        raise ValueError("HOST_WALL_NATIVE_BODY_UNAVAILABLE")
    host_geom_before=RUN.digest(C.ROOF.geometry_signature(host_body_before))
    writer=RUN.SceneWriter(api,LEDGER,schema_path=SCHEMA,
                           allow_3d_view_for_write=True)
    state={"createdGuid":None}

    def before(api_):
        verify_unchanged_host(single_detail(api_,current[WALL_GUID]))
        if set(ids(api_))!=baseline:
            raise ValueError("PRE_WRITE_261_GUID_DRIFT")
        return {"status":"KR12_HOST_WALL_SOURCE_GEOMETRY_PASS",
                "hostGUID":WALL_GUID,"sourceOpeningCenterOffsetM":5.01}

    def after(native_reply,prior):
        rows=native_reply.get("elements")
        if not isinstance(rows,list) or len(rows)!=1:
            raise ValueError("CREATE_WINDOW_AMBIGUOUS_RESPONSE")
        new=rows[0].get("elementId",{}).get("guid")
        if not isinstance(new,str):raise ValueError("NEW_WINDOW_GUID_MISSING")
        state["createdGuid"]=new
        row=single_detail(api,new)
        d=row.get("details") or {}
        if (row.get("type")!="Window" or row.get("floorIndex")!=0 or
            d.get("ownerElementId",{}).get("guid","").lower()!=WALL_GUID):
            raise ValueError("WINDOW_NATIVE_HOST_LINK_MISMATCH")
        for k,v in (("width",1.5),("height",.9),
                    ("sillHeight",1.1),("centerOffset",5.01)):
            if not isinstance(d.get(k),(float,int)) or not math.isclose(d[k],v,abs_tol=1e-5):
                raise ValueError("WINDOW_NATIVE_DIMENSION_MISMATCH:"+k)
        after_ids=set(ids(api))
        if after_ids!=baseline|{new.lower()}:
            raise ValueError("UNEXPECTED_NATIVE_GUID_DELTA_AFTER_WINDOW")
        after_dump=D.capture_full_model(api,[WALL_GUID])
        other=next((e for e in after_dump["elements"]
                    if e["guid"].lower()==WALL_GUID),None)
        if not other or not other.get("bodies"):
            raise ValueError("AFTER_WINDOW_NATIVE_HOST_BODY_MISSING")
        host_geom_after=RUN.digest(C.ROOF.geometry_signature(other))
        if host_geom_after==host_geom_before:
            raise ValueError("WINDOW_DID_NOT_CHANGE_NATIVE_HOST_BREP")
        return {"status":"BDD_KR12_NATIVE_WINDOW_AND_HOST_BREP_PASS",
                "windowGuid":new,"hostGuid":WALL_GUID,
                "nativeDetails":d,
                "hostBREPChanged":True,
                "newGUIDCount":1}

    # ONLY native mutation, delegated to the existing durable APA writer.
    result=router.execute(writer,SCENE_ID,window_ticket,[WALL_GUID],
        signatures,saved_sha,
        "USER_APPROVED_BDD_SINGLE_WINDOW_KR12_20261016","MODEL",
        after,verify_before=before)
    report["sceneWriterResult"]=result
    report["createdWindowGuid"]=state["createdGuid"]
    report["inMemoryGUIDCount"]=len(ids(api))
    report["sourceOriginalUnchanged"]=(
        checksum(original)==binding["target"]["sourceBaselineSha256"])
    report["savedToPLN"]=False
    report["status"]="NATIVE_WINDOW_CREATED_UNSAVED_USER_SAVE_REQUIRED" if result["status"]=="PASS" \
        else "PARTIAL_OR_UNKNOWN_OUTCOME_NO_RETRY"
    save(REPORT,report)
    if args.publish:print("PRIVATE GITHUB APA NATIVE WINDOW:",publish(REPORT),flush=True)
    if result["status"]!="PASS":
        raise RuntimeError("SceneWriter returned "+result["status"]+"; do not rerun")
    print("NATIVE WINDOW LIVE PASS",state["createdGuid"],flush=True)
    print("SAVE THE WORKING PLN in Archicad now (Ctrl+S), DO NOT rerun",flush=True)
    return 0

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--apply",action="store_true")
    p.add_argument("--publish",action="store_true")
    args=p.parse_args()
    try:sys.exit(run(args))
    except Exception as e:
        print("APA FIRST WINDOW BLOCKED:",type(e).__name__,str(e),file=sys.stderr,flush=True)
        if args.publish:
            try:
                state=json.loads(REPORT.read_text(encoding="utf8")) if REPORT.exists() else {
                    "schema":"apa.bdd.first-native-window-execution.v1"}
                state.update(status="BLOCKED_CHECK_SQLITE_AND_NATIVE_MODEL_BEFORE_ANY_RETRY",
                             failedAtUTC=utc(),error=type(e).__name__+": "+str(e)[:900],
                             saveState="UNKNOWN_IF_ERROR_OCCURRED_AFTER_CREATE")
                save(REPORT,state)
                print("PRIVATE GITHUB APA WINDOW ERROR:",publish(REPORT),flush=True)
            except Exception as ep:
                print("REPORT PUBLISH ERROR:",str(ep)[:250],file=sys.stderr)
        sys.exit(2)
