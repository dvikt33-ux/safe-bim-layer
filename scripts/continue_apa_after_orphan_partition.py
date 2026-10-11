"""Fifth, one-shot continuation: reuse 13 verified GUIDs, create only 12.

Read-only default. Exact pinned 2026-10-11 disposable PLN + immutable history;
three old suffixes and interrupted fourth may NEVER be replayed.
--confirm-token requires fresh verified geometry and explicit user approval.
Create requests are allotted up to 120 seconds to allow an Archicad
modal prompt to be acknowledged manually. No auto-click, auto-save, retry,
rollback, prior journal rewrite, or UI manipulation is attempted.
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
import repair_apa_partial_slab as REPAIR
import continue_apa_partial_scene as SECOND
import continue_apa_after_s2_slab as FOURTH
import diagnose_apa_suffix4_timeout as TIMEOUT
import inspect_apa_orphan_s2_partition as ORPHAN

FIFTH_SCENE_ID = "apa-suffix5-20261011-031123-7181b47c"
APPROVED_FOURTH_PLAN_HASH = "f426fb1f7c8363850440226ad949aab39729dd5927a63bf0854cb043e8874b75"
VERIFIED_ORPHAN_GUID = "bcfc99f0-50d2-4cd5-bf27-8f436c21683a"
ORPHAN_STEP = "s2-partition-1"
CREATE_TIMEOUT_SECONDS = 120


def proof(api, material):
    if not isinstance(material, str) or not material or material != material.strip():
        raise ValueError("EXACT_BUILDING_MATERIAL_NAME_REQUIRED")
    SECOND.verify_evidence_manifest(REPAIR.EVIDENCE)
    original, plan, original20, journal = REPAIR.read_evidence(REPAIR.EVIDENCE)
    schema = RUN.DEFAULT_SCENE_SCHEMA
    if (plan.get("schemaVersion") != RUN.EXPECTED_TAPIR
            or plan.get("schemaSha256") != hashlib.sha256(
                schema.read_bytes()).hexdigest()):
        raise ValueError("PINNED_TAPIR_SCHEMA_CHANGED")
    source = json.loads(SECOND.ORIGINAL_INTENT.read_text(encoding="utf-8"))
    regenerated = BUILD.prepare(source["components"][0], schema)
    if (regenerated["graph"] != plan["graph"]
            or regenerated["executionOrder"] != plan["executionOrder"]
            or regenerated["storyBindings"] != plan["storyBindings"]
            or len(plan["executionOrder"]) != 25
            or plan["executionOrder"][12] != ORPHAN_STEP):
        raise ValueError("IMMUTABLE_25_STEP_GRAPH_CHANGED")
    binding = RUN.guarded_project(api, plan["storyBindings"][0])
    SECOND.verify_live_story_map(api, plan["storyBindings"])
    material_guid = RUN.resolve_basic_slab_material(api, material)
    report, _ = TIMEOUT.read_journal()
    if (not report["fourthSceneReserved"]
            or report["fourthScenePlanHash"] != APPROVED_FOURTH_PLAN_HASH
            or report["fourthSceneState"] != "PARTIAL_OR_UNKNOWN_OUTCOME"
            or report["fourthSceneLastResult"].get("failedStep") != ORPHAN_STEP
            or len(report["fourthJournal"]) != 1
            or report["fourthJournal"][0] != {
                "step":ORPHAN_STEP, "state":"ATTEMPTED", "guid":None}
            or report["journaledNewCount"] != 0):
        raise ValueError("PREVIOUS_TIMEOUT_JOURNAL_CHANGED")
    # Check reservation before live reconciliation: after a previous attempt
    # the inventory is expected to differ from 33, but retries must always
    # fail with the durable scene reservation, not an incidental count error.
    with closing(sqlite3.connect(journal.resolve().as_uri()+"?mode=ro",uri=True)) as db:
        db.execute("PRAGMA query_only=ON")
        if db.execute("SELECT 1 FROM scenes WHERE scene_id=?",
                      (FIFTH_SCENE_ID,)).fetchone():
            raise ValueError("FIFTH_SCENE_ALREADY_RESERVED_NO_REPLAY")
    verified_orphan = ORPHAN.reconcile(api)
    if (verified_orphan["status"] != "READ_ONLY_ORPHAN_S2_PARTITION_VERIFIED"
            or verified_orphan["guid"].lower() != VERIFIED_ORPHAN_GUID
            or verified_orphan["plannedElementsVerified"] != 13
            or verified_orphan["totalModelElements"] != 33
            or verified_orphan["remainingPlannedCreates"] != 12):
        raise ValueError("ORPHAN_NOT_THE_EXACT_VERIFIED_WALL")
    with closing(sqlite3.connect(journal.resolve().as_uri()+"?mode=ro",uri=True)) as db:
        db.execute("PRAGMA query_only=ON")
        fifth_exists = db.execute(
            "SELECT 1 FROM scenes WHERE scene_id=?",(FIFTH_SCENE_ID,)).fetchone()
        previous_ids = []
        for scene_id in (original["sceneId"],
                         SECOND.SUFFIX_ID,
                         "apa-suffix3-20261011-031123-7181b47c"):
            previous_ids.extend(db.execute(
                "SELECT step_id,guid FROM steps WHERE scene_id=? ORDER BY rowid",
                (scene_id,)).fetchall())
        repaired = db.execute(
            "SELECT state,token,intent_json,result_json FROM apa_suffix3_slab_repairs "
            "WHERE scene_id=?",("apa-suffix3-20261011-031123-7181b47c",)).fetchone()
        first_repaired = db.execute(
            "SELECT state,token,intent_json,result_json FROM apa_partial_slab_repairs "
            "WHERE scene_id=?", (original["sceneId"],)).fetchone()
    if fifth_exists:
        raise ValueError("FIFTH_SCENE_ALREADY_RESERVED_NO_REPLAY")
    if len(previous_ids) != 12 or tuple(x[0] for x in previous_ids) != tuple(plan["executionOrder"][:12]):
        raise ValueError("HISTORICAL_FIRST_12_JOURNAL_STEP_ORDER_DRIFT")
    if (not repaired or repaired[0] != "READBACK_PASS"
            or not first_repaired or first_repaired[0] != "READBACK_PASS"):
        raise ValueError("BOTH_SLAB_REPAIRS_NOT_DURABLE_PASS")
    for record in (repaired,first_repaired):
        if RUN.digest(json.loads(record[2])) != record[1]:
            raise ValueError("SINGLE_SLAB_REPAIR_INTENT_HASH_DRIFT")
    if (json.loads(repaired[3]).get("status") != "S2_SLAB_REPAIRED_VERIFIED_UNSAVED"
            or json.loads(first_repaired[3]).get("status") != "SINGLE_SLAB_REPAIR_VERIFIED_UNSAVED"
            or json.loads(repaired[2]).get("materialGuid","").lower() != material_guid.lower()
            or json.loads(first_repaired[2]).get("materialGuid","").lower() != material_guid.lower()):
        raise ValueError("SINGLE_SLAB_REPAIR_MATERIAL_OR_RESULT_DRIFT")
    guid_map = {sid:guid for sid,guid in previous_ids}
    previously = FOURTH._check_all_native_elements(
        api,plan,guid_map,material_guid)
    for sid in ("s1-slab","s2-slab"):
        floor=previously[sid]["floorIndex"]
        row=RUN.requested_details(api,previously[sid]["guid"])
        absolute=RUN.story_level_for_floor(plan["storyBindings"],floor)
        if (not RUN.close(row["details"].get("zCoordinate"),absolute)
                or not RUN.close(row["details"].get("level"),0.0)):
            raise ValueError("REPAIRED_SLAB_NATIVE_Z_DRIFT")
    orphan_params=next(x for x in plan["graph"]["operations"]
                       if x["id"]==ORPHAN_STEP)["params"]
    orphan_kind=RUN.verify_readback(
        "CreateWalls",orphan_params,
        RUN.requested_details(api,VERIFIED_ORPHAN_GUID),
        expected_floor=1,
        expected_story_level=RUN.story_level_for_floor(plan["storyBindings"],1))
    if orphan_kind!="Wall":
        raise ValueError("ORPHAN_WALL_TYPE_DRIFT")
    seeded={**previously,ORPHAN_STEP:{
        "guid":VERIFIED_ORPHAN_GUID,
        "kind":"Wall", "floorIndex":1}}
    if set(seeded)!=set(plan["executionOrder"][:13]):
        raise ValueError("REUSED_THIRTEEN_PREFIX_STEP_IDS_CHANGED")
    before=REPAIR.all_guids(api)
    original32=report["previousBaselineGuids"]
    if (len(before)!=33 or
            before!=sorted([*original32,VERIFIED_ORPHAN_GUID])):
        raise ValueError("LIVE_33_GUID_INVENTORY_CHANGED")
    if (RUN.guarded_project(api,plan["storyBindings"][0])!=binding
            or REPAIR.all_guids(api)!=before):
        raise ValueError("PROJECT_OR_INVENTORY_CHANGED_DURING_PREFLIGHT")
    remaining=plan["executionOrder"][13:]
    if len(remaining)!=12:
        raise ValueError("REMAINING_TWELVE_STEPS_MISSING")
    request={
        "operation":"EXACT_FIFTH_SUFFIX_REUSE_THIRTEEN_CREATE_TWELVE",
        "fifthSceneId":FIFTH_SCENE_ID,
        "originPlanHash":original["planHash"],
        "previousFourthPlanHash":APPROVED_FOURTH_PLAN_HASH,
        "sourceGraphHash":RUN.digest(plan["graph"]),
        "schemaSha256":plan["schemaSha256"],
        "binding":binding,
        "slabMaterialGuid":material_guid,
        "material":material,
        "seeded":seeded,
        "before":before,
        "remainingStepIds":remaining,
        "maxCreateTimeoutSeconds":CREATE_TIMEOUT_SECONDS,
    }
    token=RUN.digest(request)
    return {
        "status":"READY_FOR_EXPLICIT_TWELVE_STEP_CONTINUATION",
        "token":token,"sourcePlanHash":token,
        "sceneId":FIFTH_SCENE_ID,
        "binding":binding,
        "graph":plan["graph"],
        "executionOrder":plan["executionOrder"],
        "storyBindings":plan["storyBindings"],
        "metrics":plan["metrics"],
        "slabBasicMaterialGuid":material_guid,
        "reused":seeded,
        "reusedCount":13,
        "remainingCount":12,
        "newStepIds":remaining,
        "before":before,
        "journal":str(journal),
        "maxCreateTimeoutSeconds":CREATE_TIMEOUT_SECONDS,
        "modelWriteAttempts":0,
    }


def execute(api,material,token):
    ticket=proof(api,material)
    if not isinstance(token,str) or token!=ticket["token"]:
        raise ValueError("EXPLICIT_TWELVE_STEP_TOKEN_MISMATCH")
    writer=RUN.SceneWriter(api,Path(ticket["journal"]))
    writer.required_story=ticket["storyBindings"][0]
    return writer._execute_verified_plan(
        ticket,FIFTH_SCENE_ID,ticket["token"],
        seeded_created=ticket["reused"],
        approval_source="owner-explicit-exact-reconciled-12-only",
        on_before_complete=lambda pre,created:
            FOURTH._final_verify(api,ticket,pre,created))


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--port",type=int,default=19726)
    p.add_argument("--material",required=True)
    p.add_argument("--confirm-token")
    opts=p.parse_args(argv)
    try:
        RUN.bind_approved_scratch_pln(opts.port)
        def api(cmd,params):
            # The 15s default remains for read-only GET calls; only potential
            # Create calls have longer one-shot HTTP waiting. No retries.
            seconds=CREATE_TIMEOUT_SECONDS if cmd in RUN.ALLOWED_WRITES else 15
            return RUN.tapir(opts.port,cmd,params,timeout=seconds)
        if opts.confirm_token:
            out=execute(api,opts.material,opts.confirm_token)
            public={k:out.get(k) for k in (
                "status","sceneId","reusedCount","newCreatedCount",
                "allGuidsReadback","failedStep","reason","plnSaved")}
            if "automaticRetry" in out:
                public["automaticRetry"]=out["automaticRetry"]
        else:
            out=proof(api,opts.material)
            public={k:out[k] for k in (
                "status","token","sceneId","binding","reusedCount",
                "remainingCount","modelWriteAttempts","maxCreateTimeoutSeconds")}
        print(json.dumps(public,ensure_ascii=False,indent=2))
        return 0 if public["status"] in (
            "READY_FOR_EXPLICIT_TWELVE_STEP_CONTINUATION",
            "COMPLETE_UNSAVED") else 2
    except Exception as exc:
        print(json.dumps({
            "status":"OUTCOME_UNKNOWN_NEEDS_JOURNAL_RECONCILIATION",
            "reason":type(exc).__name__+": "+str(exc),
            "modelWriteAttempts":None,
            "automaticReplayAllowed":False,
        },ensure_ascii=False,indent=2))
        return 2


if __name__=="__main__":
    sys.exit(main())
