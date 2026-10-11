"""Resume 13 remaining exact historical APA building-shell creates.

STRICT read-only by default. Existing 20 + 12 native GUIDs (three journals,
two one-shot slab repairs) are verified without replaying any prior scene.
Explicit token permits one new 13-create SceneWriter scene only on the pinned
open scratch PLN. No Save, Delete, undo, retry or project switching.
"""
from __future__ import annotations

import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

import archicad_scene_run as RUN
import archicad_building_shell as BUILD
import repair_apa_partial_slab as REPAIR1
import continue_apa_partial_scene as SECOND
import continue_apa_after_story_z as THIRD
import repair_apa_suffix3_slab as REPAIR2

FOURTH_SCENE_ID = "apa-suffix4-20261011-031123-7181b47c"
SECOND_STEP_IDS = ("s1-partition-1", "s1-partition-2", "s2-wall-south")
THIRD_STEP_IDS = ("s2-wall-east", "s2-wall-north", "s2-wall-west", "s2-slab")


def _rows(db, scene_id):
    scene = db.execute("SELECT plan_hash,state,result FROM scenes WHERE scene_id=?",
                       (scene_id,)).fetchone()
    steps = db.execute("SELECT step_id,state,guid FROM steps WHERE scene_id=? ORDER BY rowid",
                       (scene_id,)).fetchall()
    return scene, steps


def _checked_rows(rows, ids, states):
    if (tuple(r[0] for r in rows) != ids
            or tuple(r[1] for r in rows) != states
            or any(not isinstance(r[2], str) or not RUN._GUID.fullmatch(r[2])
                   for r in rows)):
        raise ValueError("RECOVERY_JOURNAL_PREFIX_CHANGED")


def _check_all_native_elements(api, plan, prefix, material_guid):
    mapped = {op["id"]: op for op in plan["graph"]["operations"]}
    created = {}
    for sid in plan["executionOrder"][:12]:
        step = mapped[sid]
        guid = prefix[sid]
        if step["command"] not in ("CreateWalls", "CreateSlabs"):
            raise ValueError("UNSUPPORTED_EXISTING_PREFIX_TYPE")
        params = step["params"]
        floor = next(iter(params.values()))[0]["floorIndex"]
        row = RUN.requested_details(api, guid)
        kind = RUN.verify_readback(
            step["command"], params, row,
            expected_floor=floor,
            expected_story_level=RUN.story_level_for_floor(
                plan["storyBindings"], floor),
            expected_slab_material_guid=(
                material_guid if step["command"] == "CreateSlabs" else None))
        if step["command"] == "CreateSlabs":
            expected_absolute = RUN.story_level_for_floor(plan["storyBindings"], floor)
            details = row.get("details", {})
            if (not RUN.close(details.get("zCoordinate"), expected_absolute)
                    or not RUN.close(details.get("level"), 0.0)):
                raise ValueError("REPAIRED_SLAB_GLOBAL_Z_OR_LEVEL_DRIFT")
        created[sid] = {"guid": guid, "kind": kind, "floorIndex": floor}
    return created


def proof(api, material):
    if not isinstance(material, str) or not material or material.strip() != material:
        raise ValueError("EXACT_MATERIAL_NAME_REQUIRED")
    SECOND.verify_evidence_manifest(REPAIR1.EVIDENCE)
    origin, plan, baseline20, journal = REPAIR1.read_evidence(REPAIR1.EVIDENCE)
    schema = RUN.DEFAULT_SCENE_SCHEMA
    if (plan.get("schemaVersion") != RUN.EXPECTED_TAPIR
            or plan.get("schemaSha256") != hashlib.sha256(schema.read_bytes()).hexdigest()):
        raise ValueError("ORIGINAL_SCHEMA_CHANGED")
    historical_intent = json.loads(SECOND.ORIGINAL_INTENT.read_text(encoding="utf-8"))
    rebuilt = BUILD.prepare(historical_intent["components"][0], schema)
    if (rebuilt["graph"] != plan["graph"]
            or rebuilt["executionOrder"] != plan["executionOrder"]
            or rebuilt["storyBindings"] != plan["storyBindings"]
            or len(plan["executionOrder"]) != 25
            or tuple(plan["executionOrder"][:5]) != SECOND.FIRST
            or tuple(plan["executionOrder"][5:8]) != SECOND_STEP_IDS
            or tuple(plan["executionOrder"][8:12]) != THIRD_STEP_IDS):
        raise ValueError("HISTORICAL_GRAPH_OR_ORDER_CHANGED")
    binding = RUN.guarded_project(api, plan["storyBindings"][0])
    SECOND.verify_live_story_map(api, plan["storyBindings"])
    material_guid = RUN.resolve_basic_slab_material(api, material)
    with closing(sqlite3.connect(journal.resolve().as_uri()+"?mode=ro", uri=True)) as db:
        original, row_a = _rows(db, origin["sceneId"])
        second, row_b = _rows(db, SECOND.SUFFIX_ID)
        third, row_c = _rows(db, THIRD.THIRD_SCENE_ID)
        existing_fourth = db.execute(
            "SELECT 1 FROM scenes WHERE scene_id=?", (FOURTH_SCENE_ID,)).fetchone()
        first_repair = db.execute(
            "SELECT slab_guid,token,state,intent_json,result_json "
            "FROM apa_partial_slab_repairs WHERE scene_id=?",
            (origin["sceneId"],)).fetchone()
        second_repair = db.execute(
            "SELECT guid,token,state,intent_json,result_json "
            "FROM apa_suffix3_slab_repairs WHERE scene_id=?",
            (THIRD.THIRD_SCENE_ID,)).fetchone()
    if existing_fourth:
        raise ValueError("FOURTH_SCENE_ALREADY_RESERVED_NEVER_REPLAY")
    if (not original or original[:2] != (origin["planHash"], "PARTIAL_OR_UNKNOWN_OUTCOME")
            or not second or second[1] != "PARTIAL_OR_UNKNOWN_OUTCOME"
            or not third or third[1] != "PARTIAL_OR_UNKNOWN_OUTCOME"
            or json.loads(second[2]).get("failedStep") != "s2-wall-south"
            or json.loads(third[2]).get("failedStep") != "s2-slab"):
        raise ValueError("PREVIOUS_SCENE_STATES_CHANGED")
    _checked_rows(row_a, SECOND.FIRST,
                  ("PASS","PASS","PASS","PASS","CREATED_UNVERIFIED"))
    _checked_rows(row_b, SECOND_STEP_IDS, ("PASS","PASS","CREATED_UNVERIFIED"))
    _checked_rows(row_c, THIRD_STEP_IDS,
                  ("PASS","PASS","PASS","CREATED_UNVERIFIED"))
    if (not first_repair or first_repair[0].lower()!=REPAIR1.SLAB_GUID.lower()
            or first_repair[2]!="READBACK_PASS"
            or not second_repair or second_repair[0].lower()!=REPAIR2.TARGET_GUID.lower()
            or second_repair[2]!="READBACK_PASS"):
        raise ValueError("SLAB_REPAIR_LEDGER_NOT_BOTH_PASS")
    r1intent, r1result = json.loads(first_repair[3]), json.loads(first_repair[4])
    r2intent, r2result = json.loads(second_repair[3]), json.loads(second_repair[4])
    if (RUN.digest(r1intent) != first_repair[1]
            or RUN.digest(r2intent) != second_repair[1]
            or r1intent.get("project") != binding
            or r2intent.get("scope") != binding
            or r1intent.get("materialName") != material
            or r2intent.get("materialName") != material
            or r1intent.get("materialGuid","").lower()!=material_guid.lower()
            or r2intent.get("materialGuid","").lower()!=material_guid.lower()
            or r1result.get("status")!="SINGLE_SLAB_REPAIR_VERIFIED_UNSAVED"
            or r2result.get("status")!="S2_SLAB_REPAIRED_VERIFIED_UNSAVED"
            or not RUN.close(r2result.get("zCoordinate"),3.0)
            or not RUN.close(r2result.get("localLevel"),0.0)
            or not RUN.close(r2result.get("thickness"),.2)
            or r2result.get("createCalls")!=0
            or r2result.get("modifyCalls")!=1):
        raise ValueError("SLAB_REPAIR_INTENT_OR_RESULT_CHANGED")
    prefix = {sid: guid for sid, _, guid in row_a + row_b + row_c}
    native = REPAIR1.all_guids(api)
    first20 = [str(g).lower() for g in baseline20]
    prefix_guids = [g.lower() for g in prefix.values()]
    if (len(first20)!=20 or len(prefix_guids)!=12 or len(set(prefix_guids))!=12
            or len(native)!=32
            or native!=sorted([*first20,*prefix_guids])):
        raise ValueError("NATIVE_32_GUIDS_NOT_EXACT_HISTORY")
    # First-suffix plan hash is reconstructed, not blindly trusted.
    old5 = _check_all_native_elements(
        api, plan, {sid:prefix[sid] for sid in plan["executionOrder"][:12]},
        material_guid)
    five = {sid: old5[sid] for sid in SECOND.FIRST}
    prior25 = sorted([*first20,*[prefix[sid].lower() for sid in SECOND.FIRST]])
    token_second = RUN.digest({
        "continuationSceneId": SECOND.SUFFIX_ID, "originSceneId": origin["sceneId"],
        "originPlanHash":origin["planHash"],
        "repairedSlabGuid": REPAIR1.SLAB_GUID, "repairToken":RUN.digest(r1intent),
        "schemaSha256":plan["schemaSha256"],"project":binding,
        "material":material,"materialGuid":material_guid,
        "reusedGuids":five,"nativeInventory":prior25,
        "remainingStepIds":plan["executionOrder"][5:],
        "graphHash":RUN.digest(plan["graph"]),
    })
    eight = {sid:old5[sid] for sid in plan["executionOrder"][:8]}
    old28 = sorted([*prior25,*[prefix[sid].lower() for sid in SECOND_STEP_IDS]])
    token_third = RUN.digest({
        "operation":"CONTINUE_ONLY_VERIFIED_SEVENTEEN",
        "thirdSceneId":THIRD.THIRD_SCENE_ID,"previousSuffix":SECOND.SUFFIX_ID,
        "previousSuffixToken":token_second,
        "originalSceneId":origin["sceneId"],"originalPlanHash":origin["planHash"],
        "schemaSha256":plan["schemaSha256"],
        "graphHash":RUN.digest(plan["graph"]),"project":binding,
        "materialName":material,"materialGuid":material_guid,
        "seeded":eight,"nativeInventory":old28,
        "remainingStepIds":plan["executionOrder"][8:],
    })
    if second[0]!=token_second or third[0]!=token_third or r2intent.get("thirdPlanHash")!=token_third:
        raise ValueError("SUFFIX_APPROVAL_HASH_CHAIN_CHANGED")
    if (RUN.guarded_project(api, plan["storyBindings"][0]) != binding
            or REPAIR1.all_guids(api) != native):
        raise ValueError("PROJECT_OR_INVENTORY_CHANGED_DURING_PREFLIGHT")
    remaining = plan["executionOrder"][12:]
    request = {
        "operation": "CONTINUE_EXACT_REPAIRED_THIRTEEN",
        "sceneId": FOURTH_SCENE_ID, "originalSceneId":origin["sceneId"],
        "previousSuffix":THIRD.THIRD_SCENE_ID,
        "previousSuffixPlanHash":token_third,
        "repairToken":RUN.digest(r2intent), "graphHash":RUN.digest(plan["graph"]),
        "schemaSha256":plan["schemaSha256"],"binding":binding,
        "materialName":material,"materialGuid":material_guid,
        "seeded":old5,"nativeInventory":native,"newStepIds":remaining,
    }
    token = RUN.digest(request)
    return {
        "status":"READY_FOR_EXPLICIT_THIRTEEN_STEP_CONTINUATION",
        "token":token,"binding":binding,"sourcePlanHash":token,
        "sceneId":FOURTH_SCENE_ID,"graph":plan["graph"],
        "executionOrder":plan["executionOrder"],"metrics":plan["metrics"],
        "storyBindings":plan["storyBindings"],
        "slabBasicMaterialGuid":material_guid,
        "newStepIds":remaining,"reused":old5,"reusedCount":12,
        "remainingCount":13,"modelWriteAttempts":0,
        "before":native,"journal":str(journal),
    }


def _final_verify(api, ticket, plan, created):
    SECOND.finish_verify(api, ticket, plan, created)
    for sid in ("s1-slab", "s2-slab"):
        floor = created[sid]["floorIndex"]
        details = RUN.requested_details(api,created[sid]["guid"])["details"]
        z = RUN.story_level_for_floor(ticket["storyBindings"],floor)
        if (not RUN.close(details.get("zCoordinate"),z)
                or not RUN.close(details.get("level"),0.0)):
            raise ValueError("FINAL_SLAB_ABSOLUTE_Z_MISMATCH")


def execute(api, material, token):
    ticket=proof(api,material)
    if not isinstance(token,str) or token!=ticket["token"]:
        raise ValueError("EXPLICIT_THIRTEEN_STEP_TOKEN_MISMATCH")
    writer=RUN.SceneWriter(api,Path(ticket["journal"]))
    writer.required_story=ticket["storyBindings"][0]
    return writer._execute_verified_plan(
        ticket,FOURTH_SCENE_ID,ticket["token"],
        seeded_created=ticket["reused"],
        approval_source="owner-explicit-exact-13-final-suffix",
        on_before_complete=lambda p,c:_final_verify(api,ticket,p,c))


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--port",type=int,default=19726)
    p.add_argument("--material",required=True)
    p.add_argument("--confirm-token")
    args=p.parse_args(argv)
    try:
        RUN.bind_approved_scratch_pln(args.port)
        api=lambda cmd,params: RUN.tapir(args.port,cmd,params)
        if args.confirm_token:
            out=execute(api,args.material,args.confirm_token)
            public={
                "status":out["status"],"sceneId":out["sceneId"],
                "reusedCount":out["reusedCount"],
                "newCreatedCount":out.get("newCreatedCount"),
                "allGuidsReadback":out.get("allGuidsReadback",False),
                "failedStep":out.get("failedStep"),
                "reason":out.get("reason"),
                "plnSaved":False,
            }
        else:
            out=proof(api,args.material)
            public={k:out[k] for k in (
                "status","token","binding","sceneId","reusedCount",
                "remainingCount","modelWriteAttempts")}
        print(json.dumps(public,ensure_ascii=False,indent=2))
        return 0 if public["status"] in (
            "READY_FOR_EXPLICIT_THIRTEEN_STEP_CONTINUATION","COMPLETE_UNSAVED") else 2
    except Exception as exc:
        # Exceptions can also escape from a post-write native read/SQLite commit.
        # Never report a fabricated zero native write count on a timeout.
        print(json.dumps({
            "status": "OUTCOME_UNKNOWN_NEEDS_JOURNAL_RECONCILIATION",
            "reason": type(exc).__name__ + ": " + str(exc),
            "modelWriteAttempts": None,
            "automaticReplayAllowed": False,
            "journalOnlyDiagnostic": "diagnose_apa_suffix4_timeout.py --journal-only",
        }, ensure_ascii=False, indent=2))
        return 2


if __name__=="__main__":
    sys.exit(main())
