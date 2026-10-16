#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ONE-SHOT LIVE STRESS: 100 native Column copies in a 10x10 grid and
50 uniformly distributed Columns in a line, in free space beside the house.

One existing APA -> DynamicCommands.copy_existing_many -> SceneWriter SQLite
-> one MoveElements(copy=true) native call. NO CreateColumns, no new PLN,
no SaveProject, no retry and no automatic recovery. Uses exact saved 290-GUID
working BDD PLN, protected source hash and original timber Column GUID.

Preflight reads actual full BREP and refuses any occupied destination.
Postflight requires 150 new root Columns AND their 150 ColumnSegments,
correct native XYZ/material, source and all old geometry unchanged, and
the exact GUID delta 290 -> 590. The source PLN is never written.
--apply is explicitly needed for the ONE real Archicad batch.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import sqlite3
import sys
import time
import traceback

import archicad_project_accelerator as APA
import archicad_scene_run as RUN
import archicad_connected_components as C
import archicad_bim_documentation as D

WORKING=Path(r"C:\LocalAI\SafeBIM_Global_Library_Test_Projects\BDD дом - по чертежам 2022.pln")
ORIGINAL=Path(r"C:\LocalAI\SafeBIM_Global_Library_Test_Projects\BDD дом .pln")
WORKING_SHA="e91d5670f20202c269d442bafc6e66a4cb13d223344122243b7237047a9ff3aa"
ORIGINAL_SHA="33b96850ad07547a9b12524de8bc46479fd98fbbce6772436d388be679836d66"
PROTOTYPE="b8d528f0-ab6a-4ece-a62d-74e3a0d7c46c"
SOURCE_XY=(3.53,9.255)
WOOD="e7ef3819-b3e8-419f-b313-5172e6b0412c"
GRID_COUNT=(10,10)
GRID_STEP=.8
GRID_ORIGIN=(22.,0.)
LINE_COUNT=50
LINE_ORIGIN=(22.,11.)
LINE_STEP=.8
SCENE="BDD_BULK150_GRID_AND_LINE_20261016"
PORT=19727
LEDGER=Path(os.environ.get("LOCALAPPDATA",str(Path.home())))/"APA_BDD_Window1p8"/"apa_scene_writer.sqlite"
OUT=Path(os.environ.get("LOCALAPPDATA",str(Path.home())))/"APA_BDD_Bulk150_NearHouse"
SCHEMA=Path(APA.__file__).resolve().parents[1]/"schemas/tapir-live-1.5.10/tapir-scene-live.json"
TOL=0.0004

def require(ok,reason):
    if not ok:
        raise ValueError(reason)

def same(a,b):
    return type(a) in (int,float) and math.isfinite(a) and abs(a-b)<TOL

def digest_file(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def record(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(".writing")
    tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False),encoding="utf-8")
    tmp.replace(path)

def inventory(api):
    rows=api("GetAllElements",{}).get("elements")
    require(isinstance(rows,list),"GET_ALL_ELEMENTS_MISSING")
    d={}
    for row in rows:
        g=(row.get("elementId") or {}).get("guid")
        require(isinstance(g,str) and g.lower() not in d,"INVALID_OR_DUPLICATE_NATIVE_GUID")
        d[g.lower()]=row
    return d

def details(api,guids):
    result=api("GetDetailsOfElements",{"elements":[{"elementId":{"guid":g}} for g in guids]})
    rows=result.get("detailsOfElements")
    require(isinstance(rows,list) and len(rows)==len(guids),"GET_DETAILS_INCOMPLETE")
    require(all(isinstance(r,dict) and "error" not in r for r in rows),"GET_DETAILS_NATIVE_ERROR")
    return dict(zip(guids,rows))

def normalized_map(dump):
    return {r["guid"].lower():r for r in dump["elements"]}

def native_box(element):
    verts=[v for body in element.get("bodies",[]) for v in body["vertices"]]
    return tuple((min(v[i] for v in verts),max(v[i] for v in verts)) for i in range(3)) if verts else None

def segments_for(native,parent):
    return [e for e in native.values() if e.get("type")=="ColumnSegment"
            and e.get("relationships",{}).get("hostGuid","").lower()==parent]

def segment(native,parent):
    rows=segments_for(native,parent)
    require(len(rows)==1,"EXPECTED_ONE_NATIVE_COLUMN_SEGMENT:"+parent)
    require(native_box(rows[0]) is not None,"COLUMN_SEGMENT_WITHOUT_BREP:"+parent)
    return rows[0]

def material(seg):
    return (seg.get("materialBindings",{}).get("buildingMaterial",{})
            .get("guid","").lower())

def expected_positions():
    grid=[(round(GRID_ORIGIN[0]+i*GRID_STEP,6),
           round(GRID_ORIGIN[1]+j*GRID_STEP,6))
          for i in range(GRID_COUNT[0]) for j in range(GRID_COUNT[1])]
    line=[(round(LINE_ORIGIN[0]+i*LINE_STEP,6),LINE_ORIGIN[1])
          for i in range(LINE_COUNT)]
    points=grid+line
    require(len(grid)==100 and len(line)==50 and len(points)==150,"PLAN_COUNT_NOT_150")
    require(len(set(points))==150,"DUPLICATE_TARGET_COORDINATES")
    require(all(x>20 and -1<y<12 for x,y in points),"TEST_TARGET_OUTSIDE_AUTHORIZED_EAST_ZONE")
    return points

def segment_geometry(seg, xy):
    require(seg["type"]=="ColumnSegment" and material(seg)==WOOD,
            "WOOD_OR_COLUMN_SEGMENT_MATERIAL_CHANGED")
    box=native_box(seg)
    require(box is not None,"COLUMN_SEGMENT_GEOMETRY_MISSING")
    for i,center,size in ((0,xy[0],.1),(1,xy[1],.05),(2,1.45,2.9)):
        require(same(box[i][0],center-size/2) and same(box[i][1],center+size/2),
                "NATIVE_SEGMENT_BREP_POSITION_OR_SECTION_MISMATCH:"+str(i))

def verify_source_detail(row):
    d=row.get("details") or {}
    origin=d.get("origin") or {}
    require(row.get("type")=="Column" and row.get("floorIndex")==0,
            "TEST_SOURCE_NOT_FIRST_FLOOR_COLUMN")
    for axis, expected in zip(("x","y"),SOURCE_XY):
        require(same(origin.get(axis),expected),"TEST_SOURCE_POSITION_CHANGED:"+axis)
    for key,expected in (("width",.1),("depth",.05),("height",2.9)):
        require(same(d.get(key),expected),"TEST_SOURCE_SECTION_OR_LENGTH_CHANGED:"+key)

def preflight_clearance(native,points):
    # Check the complete in-memory native physical BREP, not just facade bounds.
    occupied=[(guid,native_box(row)) for guid,row in native.items()]
    for x,y in points:
        target=((x-.3,x+.3),(y-.3,y+.3),(-.3,3.2))
        for guid,box in occupied:
            if box is not None and all(box[i][0]<target[i][1]
                                       and target[i][0]<box[i][1] for i in range(3)):
                raise ValueError("TEST_TARGET_COLLIDES_WITH_EXISTING_NATIVE_BODY:"+guid)
    # Assert target-to-target clearance (including across grid/line families).
    require(all((points[i][0]-points[j][0])**2+(points[i][1]-points[j][1])**2>=.6**2
                for i in range(len(points)) for j in range(i+1,len(points))),
            "COPY_DISTRIBUTION_HAS_SELF_COLLISIONS")

def run(apply):
    require(WORKING.exists() and ORIGINAL.exists(),"BDD_PLN_FILES_MISSING")
    require(digest_file(WORKING)==WORKING_SHA,"SAVED_WORKING_PLN_NOT_PINNED_290_GUID_VERSION")
    require(digest_file(ORIGINAL)==ORIGINAL_SHA,"PROTECTED_ORIGINAL_CHANGED")
    require(SCHEMA.is_file() and LEDGER.is_file(),"APA_SCHEMA_OR_ORIGINAL_SCENEWRITER_LEDGER_MISSING")
    require(not (OUT/"attempted.json").exists(),"MASS_COPY_PREVIOUSLY_ATTEMPTED_NEVER_RETRY")
    with sqlite3.connect(LEDGER) as db:
        require(db.execute("SELECT 1 FROM scenes WHERE scene_id=?",(SCENE,)).fetchone() is None,
                "MASS_COPY_SCENE_ALREADY_RESERVED")
        require(all(x[0]=="PASS" for x in db.execute("SELECT state FROM scenes")),
                "SCENEWRITER_LEDGER_HAS_UNRECONCILED_SCENE")
    RUN.bind_authorized_saved_copy(PORT,str(WORKING),WORKING.stem,WORKING_SHA,
          "USER_APPROVED_150_NATIVE_COPIES_GRID_AND_LINE_BESIDE_BDD_HOUSE")
    from archicad import ACConnection
    conn=ACConnection.connect(PORT)
    require(conn is not None,"ARCHICAD_19727_UNAVAILABLE")
    version=conn.commands.GetProductInfo()
    require(int(version[0])==29 and int(version[1])==5101,
            "ARCHICAD_29_BUILD_5101_REQUIRED")

    raw=OUT/"raw"
    raw.mkdir(parents=True,exist_ok=True)
    stats={"nativeMoveCalls":0,"nativeMoveTransportSeconds":None}
    def measured(command,params):
        if command in APA.NATIVE_MUTATIONS:
            require(command=="MoveElements","UNAUTHORIZED_NATIVE_WRITE_BLOCKED:"+command)
            require(stats["nativeMoveCalls"]==0,"MULTIPLE_NATIVE_MOVE_DISPATCH_DENIED")
            stats["nativeMoveCalls"]+=1
            started=time.perf_counter()
            try:
                return APA.native_transport(command,params)
            finally:
                stats["nativeMoveTransportSeconds"]=round(time.perf_counter()-started,5)
        return APA.native_transport(command,params)

    api=APA.EvidenceAPI(measured,raw,execute=apply)
    binding=RUN.guarded_project_for_read(api)
    require(binding["activeViewStoryIndex"] in (0,-1),"FIRST_FLOOR_OR_3D_VIEW_REQUIRED")
    old=inventory(api)
    require(len(old)==290 and PROTOTYPE in old,"EXACT_290_GUID_MODEL_AND_SOURCE_REQUIRED")
    native=D.capture_full_model(api,sorted(old))
    model=normalized_map(native)
    require(set(old)<=set(model),"INITIAL_3D_BREP_DUMP_INCOMPLETE")
    source_details=details(api,[PROTOTYPE])[PROTOTYPE]
    verify_source_detail(source_details)
    source_seg=segment(model,PROTOTYPE)
    segment_geometry(source_seg,SOURCE_XY)
    points=expected_positions()
    preflight_clearance(model,points)
    require(set(inventory(api))==set(old),"MODEL_CHANGED_WHILE_PREFLIGHT_READING")
    source_sig=RUN.digest({"detail":source_details,
                            "root":C.ROOF.geometry_signature(model[PROTOTYPE]),
                            "segment":C.ROOF.geometry_signature(source_seg)})
    retained=sorted(set(old)-{PROTOTYPE})
    signatures=C.retained_geometry_signatures(native,retained)
    require(set(signatures)==set(retained),"RETAINED_MODEL_SIGNATURES_INCOMPLETE")
    vectors=[{"x":round(x-SOURCE_XY[0],6),
              "y":round(y-SOURCE_XY[1],6),"z":0.} for x,y in points]
    router=APA.native_command_router(SCHEMA,include_functional_modules=False)
    router.review_policy("MoveElements","CREATE","MODEL",
        {"source":"Exact Tapir 1.5.10 MoveElements copy=true; user-approved 100-grid + 50-line source Column",
         "sha256":router.contract_hash("MoveElements")})
    ticket=router.prepare("MoveElements",{"elementsWithMoveVectors":[
        {"elementId":{"guid":PROTOTYPE},"moveVector":v,"copy":True} for v in vectors]})
    require(ticket["effect"]=="CREATE","MOVE_ELEMENTS_NOT_REVIEWED_AS_CREATE")
    preview={"schema":"apa.bdd.bulk-grid-and-line.v1",
             "status":"MASS_GRID_AND_DISTRIBUTION_PREFLIGHT_PASS",
             "grid":{"rows":10,"columns":10,"pitchMeters":.8,"origin":GRID_ORIGIN},
             "line":{"count":50,"pitchMeters":.8,"origin":LINE_ORIGIN},
             "copyCount":150,"nativeCallCountExpected":1,
             "existingGuidCount":290,"expectedGuidCount":590,
             "sourcePrototypeGuid":PROTOTYPE,"savedPlnSha256":WORKING_SHA,
             "sourcePlnProtected":True,"actualModelWrites":0}
    record(OUT/"preflight.json",preview)
    print(json.dumps(preview,ensure_ascii=False,indent=2),flush=True)
    if not apply:
        print("READ_ONLY_PASS; no native write. --apply required exactly once.",flush=True)
        return 0

    record(OUT/"attempted.json",{"sceneId":SCENE,
        "utc":datetime.now(timezone.utc).isoformat(),"state":"ONE_SHOT_ARMED_NO_RETRY"})
    writer=RUN.SceneWriter(api,LEDGER,schema_path=SCHEMA,allow_3d_view_for_write=True)

    def verify_before(native_api):
        require(set(inventory(native_api))==set(old),"MODEL_CHANGED_BEFORE_MASS_COPY")
        verify_source_detail(details(native_api,[PROTOTYPE])[PROTOTYPE])
        return {"status":"NATIVE_290_GUID_AND_SOURCE_VERIFIED_PASS"}

    def verify_after(reply,prior):
        now=inventory(api)
        added=set(now)-set(old)
        require(set(old)<=set(now) and len(now)==590 and len(added)==300,
                "MASS_COPY_GUID_DELTA_NOT_EXACTLY_150_ROOTS_PLUS_150_CHILDREN")
        parents=sorted(g for g in added if now[g].get("type")=="Column")
        children={g for g in added if now[g].get("type")=="ColumnSegment"}
        require(len(parents)==len(children)==150 and added==set(parents)|children,
                "MASS_COPY_UNEXPECTED_NATIVE_ELEMENT_TYPES")
        post=D.capture_full_model(api,sorted(now))
        bodies=normalized_map(post)
        require(set(now)<=set(bodies),"MASS_COPY_BREP_DUMP_INCOMPLETE")
        detail_rows=details(api,parents)
        actual={}
        for parent in parents:
            d=detail_rows[parent]
            require(d.get("type")=="Column" and d.get("floorIndex")==0,
                    "MASS_COPY_PARENT_STORY_OR_TYPE_WRONG")
            origin=(d.get("details") or {}).get("origin") or {}
            xy=(origin.get("x"),origin.get("y"))
            require(all(type(v) in (int,float) and math.isfinite(v) for v in xy),
                    "MASS_COPY_PARENT_ANCHOR_MISSING")
            key=(round(xy[0],5),round(xy[1],5))
            require(key not in actual,"MASS_COPY_DUPLICATE_RESULT_POSITION")
            actual[key]=parent
            seg=segment(bodies,parent)
            require(seg["guid"].lower() in children,"MASS_COPY_SEGMENT_NOT_NEW")
            segment_geometry(seg,xy)
        require(set(actual)==set(points),"MASS_COPY_GRID_OR_LINE_PLACEMENT_INCORRECT")
        after_source=details(api,[PROTOTYPE])[PROTOTYPE]
        verify_source_detail(after_source)
        seg=segment(bodies,PROTOTYPE)
        require(RUN.digest({"detail":after_source,
                            "root":C.ROOF.geometry_signature(bodies[PROTOTYPE]),
                            "segment":C.ROOF.geometry_signature(seg)})==source_sig,
                "MASS_COPY_ORIGINAL_COLUMN_OR_CHILD_CHANGED")
        require(digest_file(WORKING)==WORKING_SHA and digest_file(ORIGINAL)==ORIGINAL_SHA,
                "PLN_BYTES_CHANGED_WITHOUT_APPROVED_SAVE")
        require(stats["nativeMoveCalls"]==1,"MASS_COPY_NOT_EXACTLY_ONE_NATIVE_CALL")
        return {"status":"MASS150_COLUMNS_SEGMENTS_MATERIALS_POSITIONS_PASS",
                "newPhysicalCopyCount":150,"prototypeGuidUnchanged":True,
                "newColumnGuids":parents,"newColumnSegmentCount":len(children),
                "nativeCallSeconds":stats["nativeMoveTransportSeconds"],
                "initialGuidCount":290,"finalGuidCount":590,
                "gridCount":100,"lineCount":50,"saved":False}

    result=router.copy_existing_many(writer,SCENE,PROTOTYPE,"Column",
        vectors,signatures,WORKING_SHA,
        "USER_APPROVED_MASS_GRID_AND_UNIFORM_LINE_DISTRIBUTION_BDD_20261016",
        verify_before,verify_after)
    receipt=dict(preview,status=result["status"],
                 nativeMoveCalls=stats["nativeMoveCalls"],
                 nativeMoveTransportSeconds=stats["nativeMoveTransportSeconds"],
                 sceneWriter=result,nativeSave=False)
    record(OUT/"result.json",receipt)
    require(result["status"]=="PASS","NATIVE_MASS_COPY_UNKNOWN_OUTCOME_DO_NOT_RETRY")
    print("MASS_COPY_LIVE_PASS: 100 GRID + 50 LINE, 150 Columns + 150 ColumnSegments, one native call.",flush=True)
    print("NATIVE_MOVE_TRANSPORT_SECONDS:",stats["nativeMoveTransportSeconds"],flush=True)
    print("Native saved PLN remains unchanged. Inspect all 150 copies and working house before Ctrl+S.",flush=True)
    return 0

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--apply",action="store_true",help="one native 150-item batch, never retry")
    args=p.parse_args()
    try:
        sys.exit(run(args.apply))
    except Exception as ex:
        print("MASS_COPY_BLOCKED_OR_UNKNOWN:",type(ex).__name__,str(ex),file=sys.stderr,flush=True)
        traceback.print_exc(limit=4)
        if (OUT/"attempted.json").exists():
            record(OUT/"failure.json",{"status":"UNKNOWN_OUTCOME_NO_RETRY",
                   "reason":str(ex),"at":datetime.now(timezone.utc).isoformat()})
            print("DO NOT REPEAT OR SAVE: native write may have executed. Inspect journal and PLN.",file=sys.stderr,flush=True)
        sys.exit(2)
