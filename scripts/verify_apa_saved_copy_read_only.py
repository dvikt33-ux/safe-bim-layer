"""Independent READ-ONLY Archicad 29 saved-copy audit after MANUAL reopen.

This verifies only the exact owner-named saved copy, not the writable
original. Does not open/switch projects, save, create, modify, delete,
repair, retry prior scenes, or write any SQLite/local file. User MUST
manually reopen the copy first: Tapir cannot prove a reopen happened.
"""
from __future__ import annotations

import argparse
from contextlib import closing
from collections import Counter
import hashlib
import json
import os
from pathlib import PureWindowsPath
import sqlite3
import sys
import unicodedata

import archicad_scene_run as RUN
import archicad_building_shell as BUILD
import repair_apa_partial_slab as REPAIR
import continue_apa_partial_scene as SECOND
import continue_apa_after_s2_slab as FOURTH
import continue_apa_after_orphan_partition as FIFTH
import diagnose_apa_suffix4_timeout as TIMEOUT

COPY_PATH = "C:\\институт проект\\Улучшенная копия APA_Test_House_01.pln"
EXPECTED_COPY_NAME = PureWindowsPath(COPY_PATH).stem
EXPECTED_TOTAL = 45
EXPECTED_BUILT = 25
EXPECTED_FIFTH_NEW = 12

ALLOWED_READS = frozenset({
    "GetProjectInfo", "GetAddOnVersion", "GetStories",
    "GetAllElements", "GetDetailsOfElements",
})


def copy_identity(api):
    info = api("GetProjectInfo", {})
    if not isinstance(info, dict):
        raise ValueError("COPY_PROJECT_INFO_MISSING")
    path = info.get("projectPath")
    def normalized(text):
        return unicodedata.normalize("NFC", text).casefold() if isinstance(text, str) else None
    if (normalized(path) != normalized(COPY_PATH)
            or normalized(info.get("projectName")) != normalized(EXPECTED_COPY_NAME)
            or info.get("isUntitled") is not False
            or info.get("isTeamwork") is not False):
        raise ValueError("WRONG_OPEN_PROJECT_EXPECT_EXACT_SAVED_COPY: " + str(path))
    if api("GetAddOnVersion", {}).get("version") != RUN.EXPECTED_TAPIR:
        raise ValueError("COPY_TAPIR_VERSION_MISMATCH")
    return {"path": path, "name": info["projectName"],
            "tapirVersion": RUN.EXPECTED_TAPIR}


def saved_provenance():
    """Read only historical evidence and durable final journal; never mutate."""
    SECOND.verify_evidence_manifest(REPAIR.EVIDENCE)
    original, plan, first20, journal = REPAIR.read_evidence(REPAIR.EVIDENCE)
    schema = RUN.DEFAULT_SCENE_SCHEMA
    if (plan.get("schemaVersion") != RUN.EXPECTED_TAPIR
            or plan.get("schemaSha256") != hashlib.sha256(schema.read_bytes()).hexdigest()):
        raise ValueError("PINNED_SOURCE_SCHEMA_CHANGED")
    spec = json.loads(SECOND.ORIGINAL_INTENT.read_text(encoding="utf-8"))
    rebuilt = BUILD.prepare(spec["components"][0], schema)
    if (rebuilt["graph"] != plan["graph"]
            or rebuilt["executionOrder"] != plan["executionOrder"]
            or rebuilt["storyBindings"] != plan["storyBindings"]
            or len(plan["executionOrder"]) != EXPECTED_BUILT):
        raise ValueError("PINNED_25_STEP_GRAPH_CHANGED")
    fourth, _ = TIMEOUT.read_journal()
    if (fourth["fourthScenePlanHash"] != FIFTH.APPROVED_FOURTH_PLAN_HASH
            or fourth["fourthSceneState"] != "PARTIAL_OR_UNKNOWN_OUTCOME"
            or len(fourth["fourthJournal"]) != 1
            or fourth["fourthJournal"][0] != {
                "step": FIFTH.ORPHAN_STEP,
                "state": "ATTEMPTED", "guid": None}):
        raise ValueError("INTERRUPTED_FOURTH_JOURNAL_CHANGED")
    with closing(sqlite3.connect(journal.resolve().as_uri()+"?mode=ro",uri=True)) as db:
        db.execute("PRAGMA query_only=ON")
        old_rows = []
        for scene_id in (original["sceneId"],SECOND.SUFFIX_ID,
                         "apa-suffix3-20261011-031123-7181b47c"):
            old_rows.extend(db.execute(
                "SELECT step_id,guid FROM steps WHERE scene_id=? ORDER BY rowid",
                (scene_id,)).fetchall())
        fifth = db.execute(
            "SELECT state,plan_hash,result FROM scenes WHERE scene_id=?",
            (FIFTH.FIFTH_SCENE_ID,)).fetchone()
        new_rows = db.execute(
            "SELECT step_id,state,guid FROM steps WHERE scene_id=? ORDER BY rowid",
            (FIFTH.FIFTH_SCENE_ID,)).fetchall()
        repairs = [db.execute(
            "SELECT state,token,intent_json,result_json FROM "+table+
            " WHERE scene_id=?", (sid,)).fetchone() for table,sid in (
                ("apa_partial_slab_repairs",original["sceneId"]),
                ("apa_suffix3_slab_repairs","apa-suffix3-20261011-031123-7181b47c"))]
    if (not fifth or fifth[0] != "COMPLETE_UNSAVED"
            or not isinstance(fifth[1],str) or len(fifth[1])!=64):
        raise ValueError("FIFTH_SCENE_NOT_DURABLY_COMPLETE_UNSAVED")
    result = json.loads(fifth[2])
    if (result.get("status") != "COMPLETE_UNSAVED"
            or result.get("sceneId") != FIFTH.FIFTH_SCENE_ID
            or result.get("planHash") != fifth[1]
            or result.get("reusedCount") != 13
            or result.get("newCreatedCount") != EXPECTED_FIFTH_NEW
            or result.get("allGuidsReadback") is not True
            or result.get("plnSaved") is not False):
        raise ValueError("FIFTH_COMPLETION_RESULT_NOT_EXACT")
    if (len(old_rows)!=12
            or tuple(sid for sid,_ in old_rows)!=tuple(plan["executionOrder"][:12])
            or len(new_rows)!=EXPECTED_FIFTH_NEW
            or tuple(sid for sid,_,_ in new_rows)!=tuple(plan["executionOrder"][13:])
            or any(state!="PASS" for _,state,_ in new_rows)):
        raise ValueError("FIFTH_PREFIX_OR_TWELVE_STEP_JOURNAL_MISMATCH")
    for repair in repairs:
        if (not repair or repair[0]!="READBACK_PASS"
                or RUN.digest(json.loads(repair[2]))!=repair[1]):
            raise ValueError("SINGLE_SLAB_REPAIR_NOT_DURABLY_VERIFIED")
    material_guids = [json.loads(repair[2]).get("materialGuid","").lower()
                      for repair in repairs]
    if (len(set(material_guids))!=1
            or not RUN._GUID.fullmatch(material_guids[0])):
        raise ValueError("REPAIRED_BUILDING_MATERIAL_NOT_UNIQUE")
    mapping = dict(old_rows)
    mapping[FIFTH.ORPHAN_STEP] = FIFTH.VERIFIED_ORPHAN_GUID
    mapping.update({sid:guid for sid,_,guid in new_rows})
    if (len(mapping)!=EXPECTED_BUILT
            or set(mapping)!=set(plan["executionOrder"])
            or any(not isinstance(guid,str) or not RUN._GUID.fullmatch(guid)
                   for guid in mapping.values())
            or len(set(g.lower() for g in mapping.values()))!=EXPECTED_BUILT):
        raise ValueError("DURABLE_25_GUID_MAP_MISSING_OR_DUPLICATED")
    original_ids = [str(x).lower() for x in first20]
    if (len(original_ids)!=20 or len(set(original_ids))!=20
            or set(original_ids)&{x.lower() for x in mapping.values()}):
        raise ValueError("ORIGINAL_20_GUID_BASELINE_INVALID")
    return {
        "plan":plan,"expectedGuids":sorted(original_ids+
            [g.lower() for g in mapping.values()]),
        "mapping":mapping,"materialGuid":material_guids[0],
        "journal":str(journal),
        "fifthHash":fifth[1],
    }


def verify_copy(api, *, check_local_file=True):
    if check_local_file:
        if not os.path.isfile(COPY_PATH):
            raise ValueError("SAVED_COPY_FILE_NOT_FOUND_AT_EXACT_PATH")
        if os.path.getsize(COPY_PATH)<=0:
            raise ValueError("SAVED_COPY_FILE_EMPTY")
    historical = saved_provenance()
    identity = copy_identity(api)
    plan = historical["plan"]
    SECOND.verify_live_story_map(api,plan["storyBindings"])
    native_before=REPAIR.all_guids(api)
    if (len(native_before)!=EXPECTED_TOTAL
            or native_before!=historical["expectedGuids"]):
        raise ValueError("SAVED_COPY_45_GUIDS_DO_NOT_MATCH_HISTORICAL_PLAN")
    operations={x["id"]:x for x in plan["graph"]["operations"]}
    created={"__plan__":plan["graph"]}
    for sid in plan["executionOrder"]:
        cmd=operations[sid]["command"]
        floor=(operations[sid]["params"]["wallsData"][0]["floorIndex"]
               if cmd=="CreateWalls" else
               operations[sid]["params"]["slabsData"][0]["floorIndex"]
               if cmd=="CreateSlabs" else None)
        created[sid]={
            "guid":historical["mapping"][sid],
            "kind":cmd[6:-1],
            "floorIndex":floor,
        }
    counts=Counter()
    per_story=Counter()
    for sid in plan["executionOrder"]:
        step=operations[sid]
        command=step["command"]
        params=RUN.resolve_params(step,created)
        host=None
        if command in ("CreateWindows","CreateDoors"):
            parent_sid=step["params"][command[6:].lower()+"Data"][0]["ownerWallId"]["guid"]["$createdGuid"]
            host=created[parent_sid]["guid"]
            floor=created[parent_sid]["floorIndex"]
        else:
            floor=created[sid]["floorIndex"]
        row=RUN.requested_details(api,created[sid]["guid"])
        result=RUN.verify_readback(
            command,params,row,host,
            expected_floor=floor,
            expected_story_level=RUN.story_level_for_floor(plan["storyBindings"],floor),
            expected_slab_material_guid=(
                historical["materialGuid"] if command=="CreateSlabs" else None))
        if result!=created[sid]["kind"]:
            raise ValueError("SAVED_COPY_NATIVE_BIM_KIND_DRIFT")
        if command=="CreateSlabs":
            actual=row["details"]
            elevation=RUN.story_level_for_floor(plan["storyBindings"],floor)
            if (not RUN.close(actual.get("zCoordinate"),elevation)
                    or not RUN.close(actual.get("level"),0.0)):
                raise ValueError("SAVED_COPY_SLAB_ABSOLUTE_STORY_Z_MISMATCH")
        counts[result]+=1
        per_story[str(floor)]+=1
    if (copy_identity(api)!=identity
            or REPAIR.all_guids(api)!=native_before):
        raise ValueError("SAVED_COPY_CHANGED_DURING_READ_ONLY_VERIFICATION")
    return {
        "status":"OPEN_SAVED_COPY_TYPED_READBACK_PASS",
        "copyPath":COPY_PATH,
        "tapirVersion":identity["tapirVersion"],
        "expectedTotalGuids":EXPECTED_TOTAL,
        "actualTotalGuids":len(native_before),
        "plannedBuildingElementsVerified":len(plan["executionOrder"]),
        "plannedBuildingKinds":dict(sorted(counts.items())),
        "plannedElementsByNativeStory":dict(sorted(per_story.items())),
        "slabBuildingMaterialGuid":historical["materialGuid"],
        "crossStoryBindingsVerified":True,
        "hostedOpeningGuidsVerified":True,
        "allPlannedGuidsPreserved":True,
        "original20GuidsPreserved":True,
        "originalJournalChanged":False,
        "nativeWriteCalls":0,
        "savedCopyWasManuallyReopened":"USER_CONFIRMATION_REQUIRED",
        "note":"Native API cannot prove a close/reopen took place; user must reopen the copy before running.",
    }


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port",type=int,default=19726)
    args=parser.parse_args(argv)
    try:
        if type(args.port)!=int or args.port<1 or args.port>65535:
            raise ValueError("INVALID_TAPIR_PORT")
        def api(cmd,params):
            if cmd not in ALLOWED_READS:
                raise ValueError("READ_ONLY_COMMAND_BLOCKED: "+cmd)
            return RUN.tapir(args.port,cmd,params,timeout=15)
        out=verify_copy(api)
        print(json.dumps(out,ensure_ascii=False,indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({
            "status":"BLOCKED_READ_ONLY_SAVED_COPY",
            "reason":type(exc).__name__+": "+str(exc),
            "nativeWriteCalls":0,
            "noAutomaticRetry":True,
        },ensure_ascii=False,indent=2))
        return 2


if __name__=="__main__":
    sys.exit(main())
