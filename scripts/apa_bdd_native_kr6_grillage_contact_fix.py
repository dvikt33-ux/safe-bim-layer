#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fix the *existing* 18 BDD grillage beams to KR-6 section elevations.

Source section: 2022 BDD structural PDF, sheet KR-6, PDF page 8.
+0.000 finished floor; joist bottom -0.300; concrete grillage top
-0.300; grillage height 0.300; grillage bottom/pile top -0.600.
Width 0.400. No other BIM elements are modified.

Only works against the exact 261-GUID Archicad 29 working copy after
successful KR-6 floor repair. Performs no delete/create and refuses repeat.
Requires explicit --apply. --publish uploads a unique JSON report to private
GitHub on both success and failure. The original PLN is never modified.
"""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import uuid

PORT=19727
SOURCE=Path("C:/LocalAI/SafeBIM_Global_Library_Test_Projects/BDD \u0434\u043e\u043c .pln")
TARGET=SOURCE.with_name("BDD \u0434\u043e\u043c - \u043f\u043e \u0447\u0435\u0440\u0442\u0435\u0436\u0430\u043c 2022.pln")
ROOT=Path(tempfile.gettempdir())/"APA_BDD_House_Construction"
BUILD=ROOT/"house_native_manifest.json"
FLOOR=ROOT/"kr6_floor_correction.json"
LOG=ROOT/"kr6_grillage_correction.json"
BACKUP=TARGET.with_suffix(".before-KR6-grillage-correction.pln")
READ=frozenset({"GetProjectInfo","GetAllElements","GetDetailsOfElements",
                "Get3DBoundingBoxes"})
WRITE=frozenset({"ModifyBeams","SaveProject"})

def utc():
    return datetime.now(timezone.utc).isoformat()

def close(x,y,tol=0.006):
    return isinstance(x,(int,float)) and math.isfinite(x) and abs(x-y)<=tol

def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as s:
        for chunk in iter(lambda:s.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def store(path,body):
    path.parent.mkdir(parents=True,exist_ok=True)
    t=path.with_suffix(".writing.tmp")
    t.write_text(json.dumps(body,ensure_ascii=False,indent=2),encoding="utf8")
    t.replace(path)

def tapir(command,params=None,allow_write=False):
    if command not in (WRITE if allow_write else READ):
        raise RuntimeError("COMMAND NOT ALLOWED: %s/%r"%(command,allow_write))
    payload={"command":"API.ExecuteAddOnCommand",
             "parameters":{"addOnCommandId":{"commandNamespace":"TapirCommand",
                                              "commandName":command},
                           "addOnCommandParameters":params or {}}}
    req=urllib.request.Request("http://127.0.0.1:%d"%PORT,
        json.dumps(payload,ensure_ascii=False).encode("utf8"),
        {"Content-Type":"application/json"},method="POST")
    with urllib.request.urlopen(req,timeout=120) as response:
        outer=json.load(response)
    if outer.get("succeeded") is not True:
        raise RuntimeError("Tapir transport failed on "+command)
    out=outer.get("result",{}).get("addOnCommandResponse",{})
    if not isinstance(out,dict) or out.get("error") is not None:
        raise RuntimeError("Tapir command failed on "+command)
    return out

def target():
    from archicad import ACConnection
    c=ACConnection.connect(PORT)
    if c is None:
        raise RuntimeError("Archicad not accessible on port 19727")
    info=c.commands.GetProductInfo()
    if int(info[0])!=29 or int(info[1])!=5101:
        raise RuntimeError("WRONG ARCHICAD PRODUCT: "+str(info))
    p=tapir("GetProjectInfo")
    active=p.get("projectPath") or p.get("projectLocation") or ""
    if (active.casefold()!=str(TARGET).casefold()
            or p.get("isUntitled") or p.get("isTeamwork")):
        raise RuntimeError("WRONG ACTIVE PLN: "+repr(active))
    return p

def model():
    elements=tapir("GetAllElements").get("elements")
    if not isinstance(elements,list):
        raise RuntimeError("GetAllElements missing array")
    result={}
    for row in elements:
        g=(row.get("elementId") or {}).get("guid") or row.get("guid")
        if not isinstance(g,str) or not g or g.lower() in result:
            raise RuntimeError("Duplicate/missing GUID")
        result[g.lower()]=g
    return result

def selected_readback(ids):
    result={}
    for k in range(0,len(ids),12):
        part=ids[k:k+12]
        data={"elements":[{"elementId":{"guid":g}} for g in part]}
        detail=tapir("GetDetailsOfElements",data).get("detailsOfElements")
        boxes=tapir("Get3DBoundingBoxes",data).get("boundingBoxes3D")
        if (not isinstance(detail,list) or not isinstance(boxes,list)
            or len(detail)!=len(part) or len(boxes)!=len(part)):
            raise RuntimeError("Native readback response alignment error")
        for guid,d,b in zip(part,detail,boxes):
            if not isinstance(d,dict) or not isinstance(d.get("details"),dict):
                raise RuntimeError("Missing native detail for "+guid)
            box=b.get("boundingBox3D") if isinstance(b,dict) else None
            if not isinstance(box,dict) or not all(
                 math.isfinite(box.get(x,float("nan"))) and abs(box[x])<100000
                 for x in ("xMin","xMax","yMin","yMax","zMin","zMax")):
                raise RuntimeError("Missing native bounding box for "+guid)
            result[guid.lower()]={"type":d.get("type"),"data":d["details"],
                                  "bbox":box}
    return result

def read_guards():
    target()
    if not (SOURCE.is_file() and TARGET.is_file() and BUILD.is_file()
            and FLOOR.is_file()):
        raise RuntimeError("Missing source, working copy, or completed stage journals")
    bm=json.loads(BUILD.read_text(encoding="utf8"))
    fm=json.loads(FLOOR.read_text(encoding="utf8"))
    if bm.get("status")!="NATIVE_STRUCTURAL_CORE_SAVED__ROOF_AND_OPENINGS_PROVISIONAL":
        raise RuntimeError("Unexpected original builder status")
    if fm.get("status")!="KR6_FLOOR_CORE_GEOMETRY_CORRECTED__LAYERS_AND_MATERIALS_PENDING":
        raise RuntimeError("KR6 floor repair has not been completed")
    if fm.get("inFlight") is not None or bm.get("inFlight") is not None:
        raise RuntimeError("In-flight changes from earlier stage")
    if sha(SOURCE)!=bm.get("sourcePLNSHA256"):
        raise RuntimeError("Source PLN checksum does not match baseline")
    orig={g.lower() for g in bm["initialGUIDs"]}
    parent={g.lower() for s in bm["stages"] for g in s.get("primaryGuids",[])}
    child={g.lower() for s in bm["stages"] for g in s.get("autoChildGuids",[])}
    if tuple(map(len,(orig,parent,child)))!=(21,125,115):
        raise RuntimeError("Unexpected core GUID group sizes")
    current=model()
    if len(current)!=261 or set(current)!=orig|parent|child:
        raise RuntimeError("Live model GUIDs do not match 261-GUID approved core")
    grillage=[
        g.lower() for stage in bm["stages"]
        if stage.get("phase")=="400 mm RC grillage"
        for g in stage.get("primaryGuids",[])
    ]
    joists=[
        g.lower() for stage in bm["stages"]
        if stage.get("phase")=="Timber joists nominal @ 600 mm"
        for g in stage.get("primaryGuids",[])
    ]
    piles=[
        g.lower() for stage in bm["stages"]
        if stage.get("phase","").startswith("49 bored piles")
        for g in stage.get("primaryGuids",[])
    ]
    if (len(grillage),len(joists),len(piles))!=(18,48,49):
        raise RuntimeError("Unexpected source group sizes")
    # Verify all native vertical ties before touching any beam.
    read=selected_readback([current[g] for g in grillage+joists+piles])
    for g in grillage:
        item=read[g]
        d,b=item["data"],item["bbox"]
        if item["type"]!="Beam" or not all(close(d.get(k),value) for k,value in
                     (("width",.4),("height",.5),("level",-.6))):
            raise RuntimeError("Grillage modified since geometry audit: "+g)
        if not close(b["zMin"],-1.1) or not close(b["zMax"],-.6):
            raise RuntimeError("Grillage vertical envelope changed: "+g)
    for g in joists:
        b=read[g]["bbox"]
        if read[g]["type"]!="Beam" or not close(b["zMin"],-.3) or not close(b["zMax"],-.1):
            raise RuntimeError("KR6 joist height changed since floor repair: "+g)
    for g in piles:
        b=read[g]["bbox"]
        if read[g]["type"]!="Column" or not close(b["zMax"],-.6):
            raise RuntimeError("Pile top is not -0.600 m: "+g)
    if model()!=current:
        raise RuntimeError("Model changed during verification")
    return bm,current,grillage

def publish(path):
    fname=("apa-bdd-kr6-grillage-%s-%s.json" %
          (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
           uuid.uuid4().hex[:8]))
    remote="safe-bim-mailbox/gpt-live/results/"+fname
    upload=path.with_suffix(".gh-upload.tmp.json")
    try:
        store(upload,{
            "branch":"main",
            "message":"BDD KR6 source-correct native grillage position and section",
            "content":base64.b64encode(path.read_bytes()).decode("ascii")})
        s=subprocess.run(["gh","api","--method","PUT",
          "repos/dvikt33-ux/safe-bim-bridge/contents/"+remote,
          "--input",str(upload)],capture_output=True,text=True,timeout=180)
        if s.returncode:
            raise RuntimeError("Private GitHub upload failed: "+s.stderr[-400:])
    finally:
        upload.unlink(missing_ok=True)
    return "https://github.com/dvikt33-ux/safe-bim-bridge/blob/main/"+remote

def run(args):
    bm,before,grillage=read_guards()
    print("PREFLIGHT PASS: 261 GUIDs, 18 grillage, 49 piles, 48 repaired joists",
          flush=True)
    print("SOURCE KR-6: grillage WIDTH 400mm, HEIGHT 300mm, "
          "top -0.300m, bottom -0.600m",flush=True)
    if not args.apply:
        print("DRY RUN ONLY: existing PLN remains unchanged",flush=True)
        return 0
    if BACKUP.exists() or LOG.exists():
        raise RuntimeError("Existing backup or in-flight journal. Never run twice!")
    disk_hash=sha(TARGET)
    shutil.copy2(TARGET,BACKUP)
    if sha(BACKUP)!=disk_hash:
        raise RuntimeError("Working PLN backup checksum mismatch; no writes")
    state={"schema":"apa.bdd.kr6.grillage-correction.v1",
           "status":"IN_PROGRESS","startedAtUTC":utc(),"project":str(TARGET),
           "sourcePLN":str(SOURCE),"initialGUIDs":261,
           "backupFile":str(BACKUP),"backupSHA256":disk_hash,
           "stages":[],"inFlight":None,
           "sourceSheet":"3_этап_КП_КОМФОРТ_без_замазок.pdf, page 8, KR-6",
           "expected":{"width":.4,"height":.3,"topZ":-.3,"bottomZ":-.6}}
    store(LOG,state)
    # Stage changes in small batches, with exact write journal before each call.
    for start in range(0,len(grillage),6):
        subset=grillage[start:start+6]
        target()
        current=model()
        if current!=before:
            raise RuntimeError("Foreign model GUID mutation before batch")
        items=[{"elementId":{"guid":before[g]},"level":-.3,
                "height":.3,"isWidthAndHeightLinked":False}
               for g in subset]
        state["inFlight"]={"phase":"ModifyBeams","atUTC":utc(),
                           "guids":subset,"start":start}
        store(LOG,state)
        reply=tapir("ModifyBeams",{"beamsWithDetails":items},allow_write=True)
        outcome=reply.get("executionResults")
        state["lastReply"]=outcome
        store(LOG,state)
        if (not isinstance(outcome,list) or len(outcome)!=len(items)
                or any(not isinstance(o,dict) or o.get("success") is not True
                       for o in outcome)):
            raise RuntimeError("Per-element ModifyBeams returned a failure")
        if model()!=before:
            raise RuntimeError("Native GUID set changed during grillage edit")
        after=selected_readback([before[g] for g in subset])
        for g in subset:
            d=after[g]["data"]; b=after[g]["bbox"]
            if (after[g]["type"]!="Beam" or not close(d.get("width"),.4)
                    or not close(d.get("height"),.3)
                    or not close(d.get("level"),-.3)
                    or not close(b.get("zMin"),-.6)
                    or not close(b.get("zMax"),-.3)):
                raise RuntimeError("Post-modify geometry mismatch for "+g)
        state["stages"].append({"completedAtUTC":utc(),"beamGUIDs":subset})
        state["inFlight"]=None
        store(LOG,state)
        print("VERIFIED GRILLAGE:",min(start+6,len(grillage)),"/ 18",flush=True)
    if model()!=before:
        raise RuntimeError("Unexpected GUID change at end of correction")
    target()
    state["inFlight"]={"phase":"SaveProject","atUTC":utc()}
    store(LOG,state)
    tapir("SaveProject",{},allow_write=True)
    target()
    state["inFlight"]=None
    state["status"]="KR6_GRILLAGE_CONTACT_SAVED__OTHER_HOUSE_WORK_PENDING"
    state["finishedAtUTC"]=utc()
    state["finalGUIDCount"]=len(model())
    state["sourcePLNUnmodifiedOnDisk"]=(sha(SOURCE)==bm["sourcePLNSHA256"])
    store(LOG,state)
    print("KR6 GRILLAGE SAVED: 18 beams corrected, 261 GUIDs preserved",flush=True)
    print("SOURCE PLN UNCHANGED:",state["sourcePLNUnmodifiedOnDisk"],flush=True)
    if args.publish:
        print("PRIVATE GITHUB GRILLAGE REPORT:",publish(LOG),flush=True)
    return 0

if __name__=="__main__":
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply",action="store_true")
    ap.add_argument("--publish",action="store_true")
    args=ap.parse_args()
    try:
        sys.exit(run(args))
    except Exception as exc:
        print("GRILLAGE FIX BLOCKED:",type(exc).__name__,str(exc),
              file=sys.stderr,flush=True)
        if args.publish:
            try:
                state=json.loads(LOG.read_text(encoding="utf8")) if LOG.exists() else {
                    "schema":"apa.bdd.kr6.grillage-correction.v1",
                    "status":"PREFLIGHT_BLOCKED","project":str(TARGET)}
                state["error"]={"type":type(exc).__name__,
                                 "detail":str(exc)[:600],"utc":utc()}
                state["status"]="BLOCKED_REQUIRES_MANUAL_RECONCILIATION"
                store(LOG,state)
                print("PRIVATE GITHUB GRILLAGE FAILURE:",publish(LOG),flush=True)
            except Exception as pub_error:
                print("GITHUB REPORT ERROR:",str(pub_error)[:200],
                      file=sys.stderr,flush=True)
        print("Do not rerun after a failed write; inspect the live model and journal.",
              file=sys.stderr)
        sys.exit(2)
