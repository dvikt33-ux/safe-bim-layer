#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archicad 29 native structural house builder from BDD 2022 KR drawings.

Creates a DISTINCT working PLN copy, then populates it with editable native
Archicad Walls, Slabs, Beams, Columns and a provisional Roof.
The input PLN is never the active write target. Does not delete elements.
Only --apply permits BIM mutation. No changes to GitHub or main.
Readback + append-only local manifest after each operation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import sys
import tempfile
from datetime import datetime, timezone
import urllib.request

PORT = 19727
ORIGINAL = Path("C:/LocalAI/SafeBIM_Global_Library_Test_Projects/BDD \u0434\u043e\u043c .pln")
WORKING = ORIGINAL.with_name("BDD \u0434\u043e\u043c - \u043f\u043e \u0447\u0435\u0440\u0442\u0435\u0436\u0430\u043c 2022.pln")
BASELINE_GUID = "744A9A2E-985A-434F-B6EA-851A42E6075B"
EVIDENCE_DIR = Path(tempfile.gettempdir()) / "APA_BDD_House_Construction"
EXPECTED_BEFORE_COUNT = 21
# Raster-independent PDF vector circle extraction; individual pile IDs in
# source legend are not assigned to these rows. Local grid axes, metres.
PILES = [
    (0,9.38),(0,0),(5.34,0),(5.34,1.54),(6.959,1.315),
    (14.255,1.09),(14.28,9.38),(1.587,9.38),(3.174,9.38),
    (4.761,9.38),(6.348,9.38),(7.935,9.38),(9.522,9.38),
    (11.109,9.38),(12.696,9.38),(14.28,7.722),
    (14.28,6.064),(14.28,4.406),(14.28,2.748),
    (12.791,1.09),(11.327,1.09),(9.863,1.09),(8.399,1.09),
    (4.005,0),(2.67,0),(1.335,0),(0,1.563),(0,3.126),
    (0,4.689),(0,6.252),(0,7.815),(2.38,5.235),
    (4.76,5.235),(7.14,5.235),(9.52,5.235),(11.9,5.235),
    (0,10.58),(3.08,10.58),(0,-3),(6.58,-3),(6.58,-0.91),
    (8.7,-0.91),(8.7,-2),(14.28,-2),(2.193,-3),
    (4.386,-3),(14.28,-0.455),(11.49,-2),(0,-1.5)
]
assert len(PILES) == 49

# Reference-line polygon read from structural wall binding sheet KR-9.
# L-shaped main heated block; porches/terraces are separate.
MAIN = [
    (0,0),(5.34,0),(5.34,1.09),
    (14.28,1.09),(14.28,9.38),(0,9.38)
]
# Source-prompt ambiguities retained in manifest: horizontal axes 14.18/14.28,
# vertical axes 9.28/9.38. Repeated dimension chains are 14.28 and 9.38.
DIMENSION_CHECK = {"xChain":[5.34,1.43,1.93,5.58],
                   "yChain":[1.09,8.29],
                   "xSum":14.28,"ySum":9.38,
                   "generalNotesConflict":[14.18,9.28]}
# Grillage centerline schematic from KR-4; segment labels are descriptive.
GRILLAGE = [
    ((0,9.38),(14.28,9.38)),
    ((0,9.38),(0,0)),
    ((14.28,9.38),(14.28,-2)),
    ((0,5.235),(14.28,5.235)),
    ((0,0),(5.34,0)),
    ((5.34,0),(5.34,1.54)),
    ((5.34,1.54),(6.959,1.315)),
    ((6.959,1.09),(14.28,1.09)),
    ((0,9.38),(0,10.58)),
    ((0,10.58),(3.08,10.58)),
    ((3.08,10.58),(3.08,9.38)),
    ((0,0),(0,-3)),
    ((0,-3),(6.58,-3)),
    ((6.58,-3),(6.58,-0.91)),
    ((6.58,-0.91),(8.7,-0.91)),
    ((8.7,-0.91),(8.7,-2)),
    ((8.7,-2),(14.28,-2)),
]
# Important: internal partitions and actual door/window openings MUST be
# transcribed from KR wall elevations before final architectural release.
NOT_IMPLEMENTED = [
    "exact internal partition endpoints (wall elevation sheets KR-11..KR-15)",
    "exact window and door jamb/sill/head coordinates from wall elevations",
    "pitched porch and crossing gable/valley roof geometry",
    "actual thermal-envelope material assembly attributes and multilayer templates",
    "individual joist and truss connections, foundation elevations verified by section",
    "editable native grid axes (not emulated by text or 2D lines)",
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    tmp.replace(path)


def hashfile(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(2**20), b""):
            h.update(block)
    return h.hexdigest()


def c2(xy) -> dict:
    return {"x": round(float(xy[0]), 5), "y": round(float(xy[1]), 5)}


def c3(x,y,z) -> dict:
    return {"x":round(float(x),5),"y":round(float(y),5),"z":round(float(z),5)}


def api(cmd: str, params=None, port: int=PORT) -> dict:
    if port != PORT:
        raise RuntimeError("Refuse unexpected Archicad port")
    # The hard-fenced local BIM executor is separate from sync_bridge.
    allowed = {
        "GetProjectInfo","GetAddOnVersion","GetAllElements","GetStories",
        "GetDetailsOfElements","OpenProject","SaveProject",
        "CreateColumns","CreateBeams","CreateWalls","CreateSlabs","CreateRoofs",
    }
    if cmd not in allowed:
        raise RuntimeError("Command not allowlisted: " + cmd)
    request = {"command":"API.ExecuteAddOnCommand","parameters":{
        "addOnCommandId":{"commandNamespace":"TapirCommand","commandName":cmd},
        "addOnCommandParameters":params or {}}}
    payload=json.dumps(request,ensure_ascii=False).encode("utf-8")
    req=urllib.request.Request(
        "http://127.0.0.1:%d" % port,payload,
        {"Content-Type":"application/json"},method="POST")
    with urllib.request.urlopen(req,timeout=180) as response:
        obj=json.load(response)
    if obj.get("succeeded") is not True:
        raise RuntimeError("%s transport error %s" % (cmd,str(obj.get("error","?"))[:240]))
    result=obj.get("result",{}).get("addOnCommandResponse",{})
    if not isinstance(result,dict) or result.get("error") is not None:
        raise RuntimeError("%s returned %s" % (cmd,str(result)[:300]))
    return result


def project(path: Path) -> dict:
    p=api("GetProjectInfo")
    name=p.get("projectName")
    actual=Path(p.get("projectPath") or p.get("projectLocation") or "")
    if str(actual).casefold()!=str(path).casefold():
        raise RuntimeError("PROJECT MISMATCH: expected %r got %r" % (str(path),str(actual)))
    if p.get("isUntitled") or p.get("isTeamwork"):
        raise RuntimeError("Unsupported unsaved/Teamwork project")
    return p


def guids() -> set[str]:
    rows=api("GetAllElements").get("elements")
    if not isinstance(rows,list):
        raise RuntimeError("GetAllElements missing rows")
    out=set()
    for row in rows:
        g=(row.get("elementId") or {}).get("guid") or row.get("guid")
        if not g:
            raise RuntimeError("Missing GUID in existing element")
        out.add(g.lower())
    if len(out)!=len(rows):
        raise RuntimeError("Duplicate GUID detected")
    return out


def item_ids(result: dict, expected: int) -> list[str]:
    rows=result.get("elements")
    if not isinstance(rows,list) or len(rows)!=expected:
        raise RuntimeError("Expected %d elements in response; got %r" %
                           (expected,result))
    output=[]
    for item in rows:
        g=((item.get("elementId") or {}).get("guid")
           or item.get("guid")) if isinstance(item,dict) else None
        if not isinstance(g,str) or not g:
            raise RuntimeError("Partial creation / per-element error: %r" % item)
        output.append(g)
    if len(set(g.lower() for g in output))!=expected:
        raise RuntimeError("Duplicate returned GUID")
    return output


def record_stage(manifest, title: str, cmd: str, key: str,
                 items: list[dict], chunk=16):
    expected_path=WORKING
    prior=guids()
    print("BUILD",title,"items",len(items),flush=True)
    for start in range(0,len(items),chunk):
        batch=items[start:start+chunk]
        project(expected_path)
        response=api(cmd,{key:batch})
        identifiers=item_ids(response,len(batch))
        after=guids()
        created={x.lower() for x in identifiers}
        if not created.issubset(after) or not prior.issubset(after):
            raise RuntimeError("Post-write GUID guard failed in %s" % title)
        if len(after-prior)!=len(batch):
            raise RuntimeError("Unexpected element count or foreign write during %s" % title)
        manifest["stages"].append({
            "phase":title,"command":cmd,
            "guid":identifiers,"atUTC":now()
        })
        manifest["lastCount"]=len(after)
        atomic_json(EVIDENCE_DIR/"house_native_manifest.json",manifest)
        prior=after
        print("  verified",min(start+len(batch),len(items)),"/",len(items),
              "model total",len(after),flush=True)


def plan():
    # Native roof parameters are a provisional envelope, not exact valleys.
    level=3.33
    angle=math.atan2(6.295-level,9.38/2)
    # KR-6 floor framing: 100x200 joists at 600 mm nominal spacing.
    # Exact bay ends remain provisional until every joist is individually traced.
    floor_joists=[]
    x=0.15
    while x<14.2:
        low_y=0.15 if x<=5.34 else 1.24
        for a,b in ((low_y,5.235),(5.235,9.23)):
            if b-a>0.1:
                floor_joists.append({
                    'begCoordinate':c2((x,a)),
                    'endCoordinate':c2((x,b)),
                    'floorIndex':0,'zCoordinate':-0.30,
                    'width':0.1,'height':0.2,
                    'isWidthAndHeightLinked':False,
                })
        x+=0.6
    return {
        "floorJoists":floor_joists,
        "piles":[{"coordinates":c3(x,y,-3.0),"height":2.4,
                  "width":0.30,"depth":0.30,
                  "circleBased":True,"floorIndex":0}
                 for x,y in PILES],
        "grillage":[{"begCoordinate":c2(a),"endCoordinate":c2(b),
                    "zCoordinate":-0.60,"floorIndex":0,
                    "width":0.40,"height":0.50,
                    "isWidthAndHeightLinked":False}
                   for a,b in GRILLAGE],
        "exteriorWalls":[{
            "begCoordinate":c2(MAIN[i]),
            "endCoordinate":c2(MAIN[(i+1)%len(MAIN)]),
            "floorIndex":0,"zCoordinate":-0.10,
            "height":3.0,"thickness":0.25,
            "referenceLineLocation":"Center","structureType":"Basic"}
            for i in range(len(MAIN))],
        "floorPanels":[{
            "level":0.0, "thickness":0.042,
            "referencePlaneLocation":"Top",
            "polygonCoordinates":[c2(p) for p in MAIN],
            "floorIndex":0}],
        "terracePlatforms":[{
            "level":-0.05,"thickness":0.05,
            "referencePlaneLocation":"Top",
            "polygonCoordinates":[c2(p) for p in points],
            "floorIndex":0}
            for points in [
                [(0,-3),(6.58,-3),(6.58,0),(0,0)],
                [(8.7,-2),(14.28,-2),(14.28,1.09),(8.7,1.09)]
            ]],
        "roofEnvelope":[{
            "level":level,
            "polygonCoordinates":[c2(p) for p in MAIN],
            "floorIndex":1,
            "thickness":0.15,
            "eavesOverhang":0.84,
            "levels":[{"levelHeight":0.0,"levelAngle":angle}],
            "structureType":"Basic"
        }]
    }


def assert_archicad29():
    from archicad import ACConnection
    c=ACConnection.connect(PORT)
    if c is None:
        raise RuntimeError('Archicad 29 is not reachable on port 19727')
    product=c.commands.GetProductInfo()
    if int(product[0])!=29 or int(product[1])!=5101:
        raise RuntimeError('WRONG ARCHICAD VERSION/BUILD: %r' % (product,))
    return product


def run(args):
    if args.port!=PORT:
        raise RuntimeError("Port must be 19727, no automatic discovery")
    if not ORIGINAL.is_file():
        raise RuntimeError("Source PLN not found: %s" % ORIGINAL)
    assert_archicad29()
    live=project(ORIGINAL)
    product=api("GetAddOnVersion")
    if not str(product.get("version","")).startswith("1.5."):
        raise RuntimeError("Unexpected Tapir version: %r" % product)
    baseline=guids()
    if len(baseline)!=EXPECTED_BEFORE_COUNT or BASELINE_GUID.lower() not in baseline:
        raise RuntimeError("Baseline not 21 expected GUIDs; stop instead of editing")
    stories=api("GetStories").get("stories",[])
    if not any(x.get("index")==0 and x.get("level")==0 for x in stories):
        raise RuntimeError("First floor 0.000 not found")
    components=plan()
    print("PREFLIGHT OK: 29, 19727, BDD original, existing GUIDs",len(baseline))
    for name,items in components.items():
        print("PLAN",name,len(items))
    print("LIMITATIONS:",*NOT_IMPLEMENTED,sep="\n - ")
    if not args.apply:
        print("DRY_RUN_ONLY: source PLN untouched")
        return 0
    if WORKING.exists():
        raise RuntimeError("Working PLN already exists; refusing to overwrite: %s" % WORKING)
    EVIDENCE_DIR.mkdir(parents=True,exist_ok=True)
    manifest_path=EVIDENCE_DIR/"house_native_manifest.json"
    if manifest_path.exists():
        raise RuntimeError("Previous write manifest exists; refusing duplicate run")

    # Only the source *on disk* is copied; user must save any unsaved changes
    # before running this script. No source PLN write command is executed.
    shutil.copy2(ORIGINAL,WORKING)
    src_hash=hashfile(ORIGINAL)
    if hashfile(WORKING)!=src_hash:
        raise RuntimeError("Copy hash mismatch")
    manifest={
        "schema":"apa.bdd.native-house-build.v1",
        "startedAtUTC":now(),
        "sourcePLN":str(ORIGINAL),
        "sourcePLNSHA256":src_hash,
        "workingPLN":str(WORKING),
        "port":PORT,
        "initialGUIDs":sorted(baseline),
        "sourceDrawing":"3_этап_КП_КОМФОРТ_без_замазок.pdf",
        "dimensionDecision":DIMENSION_CHECK,
        "sourceTraceStatus":"KR pile field PDF vector-derived",
        "roofStatus":"PROVISIONAL; slopes/valleys not yet accurately reconstructed",
        "materialStatus":"UNVERIFIED Archicad default; thermal layers pending",
        "interiorAndOpeningsStatus":"NOT_BUILT; detailed KR wall elevation digitization pending",
        "levelsStatus":"Foundation absolute elevations preliminary; see PDF section",
        "stages":[],
        "status":"CREATED_WORKING_COPY",
    }
    atomic_json(manifest_path,manifest)
    print("COPY VERIFIED:",WORKING,flush=True)

    # Switch the Archicad 29 instance from original to the WORKING COPY;
    # opening a project can prompt to save unsaved changes in Archicad.
    api("OpenProject",{"projectFilePath":str(WORKING)})
    project(WORKING)
    assert_archicad29()
    current=guids()
    if current!=baseline:
        raise RuntimeError("Working PLN baseline differs; stop")
    manifest["status"]="BUILDING"
    atomic_json(manifest_path,manifest)

    stages=[
        ("49 bored piles", "CreateColumns","columnsData",components["piles"]),
        ("400 mm RC grillage preliminary Z", "CreateBeams","beamsData",components["grillage"]),
        ("L-shaped exterior frame envelope","CreateWalls","wallsData",components["exteriorWalls"]),
        ("100x200 timber floor joists @ 600 mm","CreateBeams","beamsData",components["floorJoists"]),
        ("timber floor sheathing as native slab","CreateSlabs","slabsData",components["floorPanels"]),
        ("terrace timber platforms as native slabs","CreateSlabs","slabsData",components["terracePlatforms"]),
        ("provisional pitched multi-plane roof","CreateRoofs","roofsData",components["roofEnvelope"]),
    ]
    for label,command,key,items in stages:
        record_stage(manifest,label,command,key,items)
    project(WORKING)
    end=guids()
    all_created={g.lower() for stage in manifest["stages"] for g in stage["guid"]}
    if len(end)!=len(baseline)+len(all_created):
        raise RuntimeError("Final GUID quantity verification failed")
    if end-baseline!=all_created:
        raise RuntimeError("Foreign GUID changes detected")

    # Save the WORKING copy only, never original.
    api("SaveProject",{})
    project(WORKING)
    manifest["status"]="NATIVE_CORE_CREATED_AND_SAVED__INTERIOR_OPENINGS_PENDING"
    manifest["finishedAtUTC"]=now()
    manifest["finalGUIDs"]=sorted(end)
    manifest["createdElementCount"]=len(all_created)
    manifest["workingPLNSizeBytes"]=WORKING.stat().st_size if WORKING.exists() else None
    manifest["originalPLNUnmodifiedOnDisk"]=(hashfile(ORIGINAL)==src_hash)
    atomic_json(manifest_path,manifest)
    print("NATIVE CORE SAVED:",WORKING,flush=True)
    print("NEW NATIVE ELEMENTS:",len(all_created),flush=True)
    print("ORIGINAL PRESERVED:",manifest["originalPLNUnmodifiedOnDisk"],flush=True)
    print("LOCAL MANIFEST:",manifest_path,flush=True)
    print("STATUS:",manifest["status"],flush=True)
    return 0


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port",type=int,default=PORT)
    parser.add_argument("--apply",action="store_true",
                        help="Create a distinct working PLN and write native BIM elements")
    args=parser.parse_args()
    try:
        sys.exit(run(args))
    except Exception as exc:
        print("BUILD_BLOCKED:",type(exc).__name__,str(exc),file=sys.stderr)
        print("If writes started, inspect the working PLN and local manifest;"
              " do not rerun blindly.",file=sys.stderr)
        sys.exit(2)
