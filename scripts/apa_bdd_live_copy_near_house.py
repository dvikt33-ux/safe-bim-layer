#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One-shot LIVE native duplicate smoke NEXT TO the saved BDD working house.

Uses only deployed APA.DynamicCommands.copy_existing_many() and the EXISTING
SceneWriter SQLite. Exactly ONE MoveElements(copy=True) native call requesting
TWO timber studs. Physical copy results require new Column + ColumnSegment
native GUIDs, preserved source, unchanged rest of the 290-GUID model and
native BREP bounds/materials. No SaveProject, new PLN, retry or fallback.

On an ambiguous result, DO NOT rerun. Inspect the open Archicad model and
the existing SceneWriter journal. --apply is the opt-in native mutation.
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
import traceback

import archicad_project_accelerator as APA
import archicad_scene_run as RUN
import archicad_connected_components as C
import archicad_bim_documentation as D

WORKING = Path(r"C:\LocalAI\SafeBIM_Global_Library_Test_Projects\BDD дом - по чертежам 2022.pln")
PROTECTED = Path(r"C:\LocalAI\SafeBIM_Global_Library_Test_Projects\BDD дом .pln")
EXPECTED_WORKING = "e91d5670f20202c269d442bafc6e66a4cb13d223344122243b7237047a9ff3aa"
EXPECTED_PROTECTED = "33b96850ad07547a9b12524de8bc46479fd98fbbce6772436d388be679836d66"
LEDGER = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "APA_BDD_Window1p8" / "apa_scene_writer.sqlite"
EVIDENCE = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "APA_BDD_CopyFirst_NearHouse"
SCENE = "BDD_COPY_FIRST_NEAR_HOUSE_TWO_STUDS_20261016"
SRC_XY = (3.53, 9.255)
TARGETS = [(22.0, 6.4), (22.8, 6.4)]
TOL = 0.0003
WOOD = "e7ef3819-b3e8-419f-b313-5172e6b0412c"
PORT = 19727
SCHEMA = Path(APA.__file__).resolve().parents[1] / "schemas/tapir-live-1.5.10/tapir-scene-live.json"


def need(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()


def eq(a, b):
    return isinstance(a, (int,float)) and math.isfinite(a) and abs(a-b)<TOL


def record(path, data):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(".writing")
    tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False),encoding="utf8")
    tmp.replace(path)


def inventory(api):
    result=api("GetAllElements",{}).get("elements")
    need(isinstance(result,list),"NATIVE_INVENTORY_MISSING")
    rows={}
    for el in result:
        g=(el.get("elementId") or {}).get("guid")
        need(isinstance(g,str) and g.lower() not in rows,"NATIVE_INVALID_OR_DUPLICATE_GUID")
        rows[g.lower()]=el
    return rows


def detail(api, guid):
    rows=api("GetDetailsOfElements",{"elements":[{"elementId":{"guid":guid}}]}).get("detailsOfElements")
    need(isinstance(rows,list) and len(rows)==1 and "error" not in rows[0],"NATIVE_COLUMN_DETAIL_MISSING")
    return rows[0]


def native_elements(dump):
    return {e["guid"].lower():e for e in dump["elements"]}


def bounds(row):
    verts=[v for body in row.get("bodies",[]) for v in body["vertices"]]
    if not verts:
        return None
    return tuple((min(v[i] for v in verts),max(v[i] for v in verts)) for i in range(3))


def segment_for(native, parent):
    matches=[e for e in native.values() if e["type"]=="ColumnSegment"
             and e.get("relationships",{}).get("hostGuid","").lower()==parent.lower()]
    need(len(matches)==1,"COPY_SOURCE_OR_CHILD_SEGMENT_COUNT_NOT_ONE:"+parent)
    seg=matches[0]
    need(bounds(seg) is not None,"COLUMN_PHYSICAL_SEGMENT_BREP_MISSING")
    return seg


def material(segment):
    return segment.get("materialBindings",{}).get("buildingMaterial",{}).get("guid","").lower()


def target_is_clear(native):
    # Physical BREP collision guard, including all existing roots and children.
    # Fixed source-grounded zone 7.7 metres east of the known 14.28m facade.
    need(min(t[0] for t in TARGETS)>14.28+5,"NOT_EAST_OF_KNOWN_HOUSE")
    box=((21.5,23.3),(5.9,6.9),(-0.3,3.2))
    for g,row in native.items():
        b=bounds(row)
        if b and all(b[i][0] < box[i][1] and box[i][0] < b[i][1] for i in range(3)):
            raise ValueError("LIVE_TEST_ZONE_OCCUPIED_BY_NATIVE_BREP:"+g)


def check_source(row):
    need(row.get("type")=="Column" and row.get("floorIndex")==0,"TEST_PROTOTYPE_NOT_FIRST_FLOOR_COLUMN")
    d=row.get("details") or {}
    org=d.get("origin") or {}
    for axis,val in zip(("x","y"),SRC_XY):
        need(eq(org.get(axis),val),"SOURCE_COLUMN_ORIGIN_DRIFT:"+axis)
    for k,val in (("height",2.9),("width",.1),("depth",.05)):
        need(eq(d.get(k),val),"SOURCE_COLUMN_DIMENSION_DRIFT:"+k)


def check_segment(seg, target_xy):
    need(seg["type"]=="ColumnSegment" and material(seg)==WOOD,"COPY_SEGMENT_MATERIAL_OR_TYPE_DRIFT")
    b=bounds(seg)
    need(b is not None,"COPY_SEGMENT_MISSING_PHYSICAL_BREP")
    for i,(center,size) in enumerate(((target_xy[0],.1),(target_xy[1],.05),(1.45,2.9))):
        lo,hi=b[i]
        need(eq(lo,center-size/2) and eq(hi,center+size/2),
             "COPY_SEGMENT_GEOMETRY_OR_POSITION_MISMATCH:"+str(i))


def main(apply):
    # Fail closed: the first attempted SceneWriter intent is never replayed.
    need(sha(WORKING)==EXPECTED_WORKING,"WORKING_PLN_SAVED_BASELINE_CHANGED")
    need(sha(PROTECTED)==EXPECTED_PROTECTED,"PROTECTED_ORIGINAL_CHANGED")
    need(SCHEMA.is_file() and LEDGER.is_file(),"INSTALLED_APA_SCHEMA_OR_EXISTING_LEDGER_MISSING")
    need(not (EVIDENCE/"attempted.json").exists(),"PREVIOUS_LIVE_COPY_ATTEMPT_NEVER_RETRY")
    with sqlite3.connect(LEDGER) as db:
        need(db.execute("SELECT 1 FROM scenes WHERE scene_id=?",(SCENE,)).fetchone() is None,
             "SCENE_ALREADY_RESERVED_NEVER_RETRY")
        need(all(r[0]=="PASS" for r in db.execute("SELECT state FROM scenes")),
             "PREVIOUS_SCENE_NOT_RECONCILED")

    RUN.bind_authorized_saved_copy(PORT,str(WORKING),WORKING.stem,
        EXPECTED_WORKING,"USER_AUTHORIZED_TWO_NATIVE_STUD_COPY_EAST_OF_BDD_HOUSE_20261016")
    from archicad import ACConnection
    conn=ACConnection.connect(PORT)
    need(conn is not None,"ARCHICAD_19727_NOT_CONNECTED")
    product=conn.commands.GetProductInfo()
    need(int(product[0])==29 and int(product[1])==5101,"ARCHICAD_PRODUCT_BUILD_CHANGED")

    raw=EVIDENCE/"raw"
    raw.mkdir(parents=True,exist_ok=True)
    api=APA.EvidenceAPI(APA.native_transport,raw,execute=apply)
    binding=RUN.guarded_project_for_read(api)
    need(binding["activeViewStoryIndex"] in (0,-1),"OPEN_FIRST_STORY_OR_3D")
    old=inventory(api)
    need(len(old)==290,"BASELINE_REQUIRES_EXACTLY_290_NATIVE_GUIDS")
    ids=[row["elementId"]["guid"] for row in old.values() if row.get("type")=="Column"]
    need(bool(ids),"NATIVE_COLUMNS_NOT_FOUND")
    details=api("GetDetailsOfElements",{"elements":[{"elementId":{"guid":g}} for g in ids]}).get("detailsOfElements")
    need(isinstance(details,list) and len(details)==len(ids),"SOURCE_COLUMN_DETAILS_INCOMPLETE")
    candidates=[g.lower() for g,d in zip(ids,details) if
                d.get("type")=="Column" and d.get("floorIndex")==0 and
                eq((d.get("details") or {}).get("origin",{}).get("x"),SRC_XY[0]) and
                eq((d.get("details") or {}).get("origin",{}).get("y"),SRC_XY[1]) and
                eq((d.get("details") or {}).get("height"),2.9)]
    need(len(candidates)==1,"SOURCE_COLUMN_NOT_UNIQUELY_IDENTIFIED")
    guid=candidates[0]
    source_details=detail(api,guid)
    check_source(source_details)
    old_dump=D.capture_full_model(api,sorted(old))
    native=native_elements(old_dump)
    need(set(old)<=set(native),"MODEL_DUMP_NOT_COMPLETE")
    src_segment=segment_for(native,guid)
    check_segment(src_segment,SRC_XY)
    target_is_clear(native)
    source_geometry=RUN.digest({"root":C.ROOF.geometry_signature(native[guid]),
                               "segment":C.ROOF.geometry_signature(src_segment),
                               "rootDetails":source_details})
    vectors=[dict(x=round(x-SRC_XY[0],6),y=round(y-SRC_XY[1],6),z=0.) for x,y in TARGETS]
    retained=sorted(set(old)-{guid})
    signatures=C.retained_geometry_signatures(old_dump,retained)
    need(set(signatures)==set(retained),"RETAINED_BREP_SIGNATURES_INCOMPLETE")
    router=APA.native_command_router(SCHEMA,include_functional_modules=False)
    router.review_policy("MoveElements","CREATE","MODEL",{
        "source":"Tapir 1.5.10 MoveElements(copy=true), two free-standing timber stud copies, east of BDD working house",
        "sha256":router.contract_hash("MoveElements")})
    # Native schema and reviewed CREATE effect must pass even for dry run.
    preview=router.prepare("MoveElements",{"elementsWithMoveVectors":[{
        "elementId":{"guid":guid},"moveVector":v,"copy":True} for v in vectors]})
    need(preview["effect"]=="CREATE","NATIVE_COPY_CREATE_POLICY_NOT_QUALIFIED")
    baseline={"schema":"apa.bdd.native-copy-smoke.v1","status":"PREFLIGHT_PASS",
        "savedPlnSha256":EXPECTED_WORKING,"originalSha256":EXPECTED_PROTECTED,
        "initialGuidCount":290,"prototypeGuid":guid,"prototypeSegmentGuid":src_segment["guid"],
        "sourceXY":SRC_XY,"copyXY":TARGETS,"displacements":vectors,
        "modelWrites":0,"nativeSave":False,
        "nativeRoute":"DynamicCommands.copy_existing_many -> SceneWriter -> SQLite"}
    record(EVIDENCE/"preflight.json",baseline)
    print(json.dumps(baseline,ensure_ascii=False,indent=2),flush=True)
    if not apply:
        print("DRY_RUN_ONLY: to write once run --apply; NO native mutation yet",flush=True)
        return 0

    record(EVIDENCE/"attempted.json",{"scene":SCENE,"status":"NATIVE_ATTEMPT_ARMED",
                                     "at":datetime.now(timezone.utc).isoformat()})
    writer=RUN.SceneWriter(api,LEDGER,schema_path=SCHEMA,allow_3d_view_for_write=True)

    def verify_before(native_api):
        need(set(inventory(native_api))==set(old),"MODEL_CHANGED_BEFORE_NATIVE_COPY")
        check_source(detail(native_api,guid))
        return {"status":"VERIFIED_SOURCE_AND_EMPTY_EAST_ZONE_PASS"}

    def verify_after(reply, prior):
        now=inventory(api)
        added=set(now)-set(old)
        need(set(old)<=set(now) and len(added)==4 and len(now)==294,
             "COPY_ADDED_GUIDS_NOT_EXACTLY_TWO_COLUMNS_AND_TWO_SEGMENTS")
        parent_guids=[g for g in added if now[g].get("type")=="Column"]
        need(len(parent_guids)==2,"COPY_NEW_COLUMN_PARENTS_NOT_EXACTLY_TWO")
        post=D.capture_full_model(api,sorted(now))
        native_after=native_elements(post)
        need(set(now)<=set(native_after),"COPY_POST_NATIVE_BREP_INCOMPLETE")
        new_segment_guids=[]
        remaining=set(parent_guids)
        for xy in TARGETS:
            found=[]
            for parent in remaining:
                row=detail(api,parent)
                check_source_type=row.get("type")=="Column" and row.get("floorIndex")==0
                point=(row.get("details") or {}).get("origin") or {}
                if check_source_type and eq(point.get("x"),xy[0]) and eq(point.get("y"),xy[1]):
                    found.append(parent)
            need(len(found)==1,"COPY_COLUMN_ANCHOR_NOT_EXACTLY_AT_REQUESTED_POSITION")
            parent=found[0]
            remaining.remove(parent)
            seg=segment_for(native_after,parent)
            need(seg["guid"].lower() in added,"COPY_SEGMENT_GUID_NOT_NEW")
            check_segment(seg,xy)
            new_segment_guids.append(seg["guid"].lower())
        need(added==set(parent_guids)|set(new_segment_guids),"UNEXPECTED_NEW_NATIVE_GUID_TYPES")
        original_segment=segment_for(native_after,guid)
        root=detail(api,guid)
        check_source(root)
        after_signature=RUN.digest({"root":C.ROOF.geometry_signature(native_after[guid]),
                                    "segment":C.ROOF.geometry_signature(original_segment),
                                    "rootDetails":root})
        need(after_signature==source_geometry,"SOURCE_PROTOTYPE_CHANGED_DURING_COPY")
        need(sha(WORKING)==EXPECTED_WORKING and sha(PROTECTED)==EXPECTED_PROTECTED,
             "SAVED_WORKING_OR_PROTECTED_SOURCE_CHANGED_DURING_COPY")
        return {"status":"TWO_NATIVE_COLUMN_AND_SEGMENT_BREP_PASS",
                "newPhysicalCopyCount":2,"prototypeGuidUnchanged":True,
                "newColumnGuids":sorted(parent_guids),
                "newSegmentGuids":sorted(new_segment_guids),
                "finalGuidCount":len(now),"saveRequired":True}

    outcome=router.copy_existing_many(
        writer, SCENE, guid, "Column", vectors, signatures,
        EXPECTED_WORKING, "USER_AUTHORIZED_NATIVE_TEST_EAST_OF_BDD_HOUSE",
        verify_before, verify_after)
    result=dict(baseline,status=outcome["status"],modelWrites=1,nativeSave=False,
                nativeResult=outcome)
    record(EVIDENCE/"result.json",result)
    need(outcome["status"]=="PASS","NATIVE_RESULT_PARTIAL_OR_UNKNOWN_DO_NOT_RETRY")
    print("NATIVE_COPY_LIVE_PASS: 2 native Columns + 2 native ColumnSegments.",flush=True)
    print("Saved PLN unchanged. Review both studs at X=22.0 and X=22.8, Y=6.4.",flush=True)
    print("After visual verification press Ctrl+S in WORKING BDD PLN. DO NOT SAVE the protected original.",flush=True)
    return 0


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--apply",action="store_true",help="ONE native copy; never automatic retry")
    args=p.parse_args()
    try:
        sys.exit(main(args.apply))
    except Exception as e:
        print("COPY_SMOKE_BLOCKED_OR_UNKNOWN:",type(e).__name__,str(e),file=sys.stderr,flush=True)
        traceback.print_exc(limit=4)
        if (EVIDENCE/"attempted.json").exists():
            record(EVIDENCE/"failure.json",{"status":"UNKNOWN_OUTCOME_DO_NOT_RETRY",
                   "error":type(e).__name__+": "+str(e)})
            print("DO NOT RERUN. Native operation may have executed. Do not save PLN until reconciled.",file=sys.stderr)
        sys.exit(2)
