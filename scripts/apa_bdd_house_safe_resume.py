#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Safely resume interrupted native BDD house BUILD after first 16 columns.

This script is a one-time reconciliation: original 21 GUIDs + 16 Columns +
16 automatically generated ColumnSegments, all cross-checked against the
previous published diagnostic. Subsequent phases record primary element IDs
and Archicad-owned subcomponent IDs separately.

WRITE TARGET IS THE EXISTING WORKING COPY, NEVER THE ORIGINAL PLN.
Do not rerun after any failure until an independent read-only reconciliation.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import sys

import apa_bdd_house_native_builder as B

DIAG_PARENT_GUIDS = set(["19fab51b-9095-4ff8-b11d-c2aeeeb63c15","1f795816-fb0e-4a7b-b0bb-6abc0fa312f9","31951fb1-b938-40ce-ad02-032402f705aa","379633e4-ea4f-4664-83d6-065a1ddfd697","4917c196-800e-4cda-8abe-55763858ea52","49b811ac-1215-4bb7-9804-3d5762a32800","4c9ac78b-62dc-4466-a241-3a550b6bd493","569436af-bbab-4583-81f2-06cc3f40d1ec","a58cc9ba-b5ad-4e2d-9273-caad919a6dfd","ac946863-93d7-4be6-99c5-7f66cb126733","af7a6ca7-43c3-4e73-adcd-ccb0e5a96aa0","b8680229-b547-4dea-9a29-2682a74e93ac","c5e038ce-5c29-4f89-9e11-5e6d7ca53775","cfbfc98b-a463-44df-b2af-1340f42ff46e","dc2376fc-e239-4875-ab88-fdc121f3f01b","f8da84af-2bef-4008-a0a0-1e0e56987107"])
DIAG_SEGMENT_GUIDS = set(["06a75ea5-2a39-4a03-a98f-316a618b37d0","12af2075-5e13-4305-a709-7ddde0b5b8ce","213aac51-caf1-4989-bf9d-203a263d677b","22dd7d09-9317-49f4-bf97-6064a625fdcd","54ee7f43-dbdf-49eb-8a93-4bdbb8482024","8f54e76f-45ad-4014-8471-711272893f5a","a1a5396b-047b-4d0f-8e46-e56331966e95","a31a3bc0-898a-4abc-a459-17230fcf4408","a77fdbfd-f692-4f60-b678-06a419d6fd38","bf1886e8-379e-4d4e-b75e-06c1dc90b14b","bfa49910-e3d6-4d1d-82f9-44b8c75d6361","c6d45039-7b78-4a3a-a676-87686a57fc04","d61063e1-4000-4b67-affc-ffa9266717b0","e5036072-966c-4bc7-862d-1f096a5d9d3b","e7911aa8-b2ff-4a3f-a404-70ba2e0eac00","e81d7abd-0036-495e-83d2-c2dd95e9c641"])
STAGE_FILE = B.EVIDENCE_DIR / "house_native_manifest.json"

AUTO_CHILD = {
    "CreateColumns": {"ColumnSegment"},
    "CreateBeams": {"BeamSegment"},
    "CreateWalls": set(),
    "CreateSlabs": set(),
    "CreateRoofs": {"RoofSegment", "RoofPlane"},
}
PARENT_TYPE = {
    "CreateColumns": "Column",
    "CreateBeams": "Beam",
    "CreateWalls": "Wall",
    "CreateSlabs": "Slab",
    "CreateRoofs": "Roof",
}

def utcnow():
    return datetime.now(timezone.utc).isoformat()


def write_checkpoint(manifest):
    B.atomic_json(STAGE_FILE, manifest)


def native_details(guids):
    ids=sorted(guids)
    out={}
    for begin in range(0,len(ids),24):
        group=ids[begin:begin+24]
        r=B.api("GetDetailsOfElements",{
            "elements":[{"elementId":{"guid":g}} for g in group]
        }).get("detailsOfElements")
        if not isinstance(r,list) or len(r)!=len(group):
            raise RuntimeError("Native details missing/length mismatch")
        for k,v in zip(group,r):
            if not isinstance(v,dict) or not isinstance(v.get("type"),str):
                raise RuntimeError("Invalid detail for %s" % k)
            out[k.lower()]=v
    return out


def initial_reconcile(manifest):
    if manifest.get("stages") or manifest.get("inFlight"):
        raise RuntimeError("Unexpected prior journal entries or in-flight call; manual reconciliation required")
    if manifest.get("status") != "BUILDING":
        raise RuntimeError("Unexpected prior manifest status "+str(manifest.get("status")))
    B.assert_archicad29()
    B.project(B.WORKING)
    if B.hashfile(B.ORIGINAL)!=manifest.get("sourcePLNSHA256"):
        raise RuntimeError("Original PLN hash changed; refuse to resume")
    baseline=set(x.lower() for x in manifest.get("initialGUIDs",[]))
    if len(baseline)!=21 or B.BASELINE_GUID.lower() not in baseline:
        raise RuntimeError("Missing original 21 GUID evidence")

    live=B.guids()
    new=live-baseline
    if not baseline.issubset(live) or len(live)!=53 or len(new)!=32:
        raise RuntimeError("Model no longer matches the recorded 53 GUID failure state")
    d=native_details(new)
    parent=set(k for k,v in d.items() if v["type"]=="Column")
    children=set(k for k,v in d.items() if v["type"]=="ColumnSegment")
    if parent!=DIAG_PARENT_GUIDS or children!=DIAG_SEGMENT_GUIDS:
        raise RuntimeError("Current model GUIDs do not match previous live diagnosis")
    desired=set((round(float(x),3),round(float(y),3))
                for x,y in B.PILES[:16])
    got=set()
    for guid in sorted(parent):
        det=d[guid]["details"]
        xy=det.get("origin",{})
        pos=(round(float(xy.get("x")),3),round(float(xy.get("y")),3))
        got.add(pos)
        for field,target in [("height",2.4),("width",0.3),
                             ("depth",0.3),("zCoordinate",-3.0)]:
            if not math.isclose(float(det[field]),target,abs_tol=0.0001):
                raise RuntimeError("Pile geometry mismatch %s %s" % (guid,field))
        if det.get("circleBased") is not True:
            raise RuntimeError("Pile is not circular: "+guid)
    if got!=desired or len(got)!=16:
        raise RuntimeError("Pile coordinate mismatch; expected=%r got=%r"%(desired,got))
    manifest["stages"].append({
        "phase":"49 bored piles (recovered first 16)",
        "command":"CreateColumns",
        "primaryGuids":sorted(parent),
        "autoChildGuids":sorted(children),
        "reconciledAtUTC":utcnow(),
        "source":"GitHub live diagnostic 20261016T140357Z, exact GUID and parameter match",
    })
    manifest["lastCount"]=len(live)
    manifest["status"]="RECOVERED_16_COLUMNS_AND_CHILDREN"
    write_checkpoint(manifest)
    # First save the 16 original new Columns in the WORKING copy so
    # partial unsaved changes do not disappear on an Archicad crash.
    B.api("SaveProject",{})
    B.project(B.WORKING)
    if not baseline.issubset(B.guids()):
        raise RuntimeError("Baseline changed after saving working copy")
    print("RECOVERED 16 PILES + 16 NATIVE SEGMENTS; working copy saved",flush=True)
    return baseline


def record_native_batch(manifest, original_guids, phase, command, param_key,
                        items, offset=0, batch_size=12):
    for start in range(0,len(items),batch_size):
        batch=items[start:start+batch_size]
        B.project(B.WORKING)
        before=B.guids()
        if not original_guids.issubset(before):
            raise RuntimeError("Original 21 GUIDs missing before "+phase)
        manifest["inFlight"]={
            "phase":phase,"command":command,"offset":offset+start,
            "expectedParents":len(batch),"beforeCount":len(before),
            "atUTC":utcnow(),
        }
        write_checkpoint(manifest)
        # No retry of a failed add-on call, because the call may have
        # committed elements even when it returns a transport error.
        reply=B.api(command,{param_key:batch})
        after=B.guids()
        created=after-before
        returned=B.item_ids(reply,len(batch))
        primary={g.lower() for g in returned}
        other=created-primary
        diagnostic={
            "phase":phase,"command":command,"offset":offset+start,
            "returnedPrimary":returned,"allCreated":sorted(created),
            "autoChildren":sorted(other),"beforeCount":len(before),
            "afterCount":len(after),"atUTC":utcnow(),
        }
        # Persist this evidence *before* asserting model semantics.
        manifest["lastAttempt"]=diagnostic
        write_checkpoint(manifest)
        if not before.issubset(after) or not primary.issubset(created):
            raise RuntimeError("Unexplained removal or primary GUID mismatch in "+phase)
        if not original_guids.issubset(after):
            raise RuntimeError("The original 21 elements have been modified or deleted")
        details=native_details(created)
        actual_parent={k for k in primary
                       if details[k].get("type")==PARENT_TYPE[command]}
        if actual_parent!=primary:
            raise RuntimeError("Unexpected primary element type in "+phase)
        child_types=Counter(details[k].get("type") for k in other)
        if any(t not in AUTO_CHILD[command] for t in child_types):
            raise RuntimeError("Unexpected additional child types %r in %s" %
                               (dict(child_types),phase))
        if len(other)>len(primary)*8:
            raise RuntimeError("Excessive unexpected native child entities in "+phase)
        manifest["stages"].append({
            "phase":phase,"command":command,
            "primaryGuids":sorted(primary),
            "autoChildGuids":sorted(other),
            "extraTypes":dict(child_types),
            "atUTC":utcnow(),
        })
        manifest["lastCount"]=len(after)
        manifest["inFlight"]=None
        write_checkpoint(manifest)
        print("VERIFIED",phase,offset+start+len(batch),
              "new primary GUIDs; children",dict(child_types),
              "model total",len(after),flush=True)


def run(args):
    if not args.apply:
        print("Only explicit --apply performs write continuation; no action")
        return 0
    manifest=json.loads(STAGE_FILE.read_text(encoding="utf-8"))
    baseline=initial_reconcile(manifest)
    source=B.plan()
    stages=[
        ("49 bored piles (remaining 33)","CreateColumns","columnsData",source["piles"][16:],16),
        ("400 mm RC grillage","CreateBeams","beamsData",source["grillage"],0),
        ("Outer timber walls","CreateWalls","wallsData",source["exteriorWalls"],0),
        ("Timber joists nominal @ 600 mm","CreateBeams","beamsData",source["floorJoists"],0),
        ("Floor sheathing","CreateSlabs","slabsData",source["floorPanels"],0),
        ("Terrace platforms","CreateSlabs","slabsData",source["terracePlatforms"],0),
        ("Roof temporary pitched envelope","CreateRoofs","roofsData",source["roofEnvelope"],0),
    ]
    for phase,command,key,items,offset in stages:
        record_native_batch(manifest,baseline,phase,command,key,items,offset)
        # Incremental save only to verified working copy.
        B.project(B.WORKING)
        B.api("SaveProject",{})
        print("WORKING PLN SAVED after",phase,flush=True)

    B.project(B.WORKING)
    model=B.guids()
    roots={x for stage in manifest["stages"]
           for x in stage.get("primaryGuids",[])}
    children={x for stage in manifest["stages"]
              for x in stage.get("autoChildGuids",[])}
    if len(roots)!=125:
        raise RuntimeError("Expected 125 primary BIM entities; have %d"%len(roots))
    expected=baseline|set(roots)|set(children)
    if model!=expected:
        raise RuntimeError("Final GUID readback disagrees with manifest")
    types=native_details(set(roots))
    counts=dict(Counter(x["type"] for x in types.values()))
    if counts!={"Column":49,"Beam":66,"Wall":6,"Slab":3,"Roof":1}:
        raise RuntimeError("Unexpected physical types at final readback "+repr(counts))
    manifest["status"]="NATIVE_STRUCTURAL_CORE_SAVED__ROOF_AND_OPENINGS_PROVISIONAL"
    manifest["finishedAtUTC"]=utcnow()
    manifest["primaryElementCounts"]=counts
    manifest["totalPrimaryCreated"]=len(roots)
    manifest["nativeChildCount"]=len(children)
    manifest["finalGUIDCount"]=len(model)
    manifest["sourcePLNUnmodifiedOnDisk"]=(B.hashfile(B.ORIGINAL)==manifest.get("sourcePLNSHA256"))
    write_checkpoint(manifest)
    print("NATIVE CORE VERIFIED:",counts,flush=True)
    print("PARENT ELEMENTS: 125; AUXILIARY:",len(children),flush=True)
    print("WORKING PLN:",B.WORKING,flush=True)
    print("SOURCE FILE UNCHANGED:",manifest["sourcePLNUnmodifiedOnDisk"],flush=True)
    if args.publish:
        print("PRIVATE GITHUB BUILD REPORT:",B.publish_manifest(STAGE_FILE),flush=True)
    return 0


if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply",action="store_true",
                        help="Resume native BIM writes into exact verified working PLN")
    parser.add_argument("--publish",action="store_true",
                        help="Upload final manifest to private GitHub mailbox")
    args=parser.parse_args()
    try:
        sys.exit(run(args))
    except Exception as exc:
        print("RESUME BLOCKED:",type(exc).__name__,str(exc),file=sys.stderr,flush=True)
        print("Do not rerun: live PLN may contain partially saved elements;"
              " inspect inFlight/lastAttempt journal first.",file=sys.stderr,flush=True)
        sys.exit(2)
