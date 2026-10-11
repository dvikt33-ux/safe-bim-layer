"""Read-only by default: reconcile false second-story Z mismatch, then optionally
create ONLY the 17 missing operations using the EXISTING journaled SceneWriter.

Exact 2026-10-11 disposable PLN and immutable 20→25→28 provenance only.
Never retry the reserved 20-step suffix. NEVER auto-save, undo or delete.
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
import continue_apa_partial_scene as CONT

THIRD_SCENE_ID = "apa-suffix3-20261011-031123-7181b47c"
FAILED_STEP = "s2-wall-south"
EXPECTED_PREVIOUS = ("s1-partition-1", "s1-partition-2", FAILED_STEP)


def proof(api, material):
    """Prove original, first repair, 3 recorded suffix GUIDs and all 28 live IDs."""
    if not isinstance(material, str) or not material or material.strip() != material:
        raise ValueError("EXACT_MATERIAL_NAME_REQUIRED")
    CONT.verify_evidence_manifest(REPAIR.EVIDENCE)
    original_scene, original_plan, original20, journal = REPAIR.read_evidence(
        REPAIR.EVIDENCE)
    bound_stories = original_plan["storyBindings"]
    schema = RUN.DEFAULT_SCENE_SCHEMA
    if (original_plan.get("schemaVersion") != RUN.EXPECTED_TAPIR
            or original_plan.get("schemaSha256") != hashlib.sha256(
                schema.read_bytes()).hexdigest()):
        raise ValueError("ORIGINAL_SCHEMA_REVISION_CHANGED")
    initial_intent = json.loads(CONT.ORIGINAL_INTENT.read_text(encoding="utf-8"))
    rebuilt = BUILD.prepare(initial_intent["components"][0], schema)
    if (original_plan["graph"] != rebuilt["graph"]
            or original_plan["executionOrder"] != rebuilt["executionOrder"]
            or bound_stories != rebuilt["storyBindings"]
            or len(rebuilt["executionOrder"]) != 25
            or original_plan["executionOrder"][:5] != list(CONT.FIRST)
            or original_plan["executionOrder"][5:8] != list(EXPECTED_PREVIOUS)):
        raise ValueError("ORIGINAL_GRAPH_OR_EXECUTION_ORDER_MISMATCH")
    old_prefix, repair_intent, repair_result = CONT.read_repaired_ledger(
        journal, original_scene, allow_existing_suffix=True)
    binding = RUN.guarded_project(api, bound_stories[0])
    CONT.verify_live_story_map(api, bound_stories)
    material_guid = RUN.resolve_basic_slab_material(api, material)
    if (repair_intent.get("project") != binding
            or material != repair_intent.get("materialName")
            or material_guid.lower() != repair_intent.get("materialGuid", "").lower()
            or material_guid.lower() != repair_result.get("materialGuid", "").lower()):
        raise ValueError("SLAB_REPAIR_BINDING_DRIFT")
    seeded_five = CONT.inspect_live_prefix(api, original_plan, old_prefix, material_guid)
    first_25_guids = sorted([
        *[str(g).lower() for g in original20],
        *[x["guid"].lower() for x in seeded_five.values()],
    ])
    if len(first_25_guids) != 25 or len(set(first_25_guids)) != 25:
        raise ValueError("ORIGINAL_25_NOT_UNIQUE")
    prior_request = {
        "continuationSceneId": CONT.SUFFIX_ID,
        "originSceneId": original_scene["sceneId"],
        "originPlanHash": original_scene["planHash"],
        "repairedSlabGuid": REPAIR.SLAB_GUID,
        "repairToken": RUN.digest(repair_intent),
        "schemaSha256": original_plan["schemaSha256"],
        "project": binding,
        "material": material, "materialGuid": material_guid,
        "reusedGuids": seeded_five,
        "nativeInventory": first_25_guids,
        "remainingStepIds": original_plan["executionOrder"][5:],
        "graphHash": RUN.digest(original_plan["graph"]),
    }
    first_suffix_token = RUN.digest(prior_request)
    with closing(sqlite3.connect(journal.resolve().as_uri() + "?mode=ro", uri=True)) as db:
        sc = db.execute(
            "SELECT plan_hash,state,result FROM scenes WHERE scene_id=?",
            (CONT.SUFFIX_ID,)).fetchone()
        rows = db.execute(
            "SELECT step_id,state,guid FROM steps WHERE scene_id=? ORDER BY rowid",
            (CONT.SUFFIX_ID,)).fetchall()
        next_exists = db.execute(
            "SELECT 1 FROM scenes WHERE scene_id=?", (THIRD_SCENE_ID,)).fetchone()
    if next_exists:
        raise ValueError("THIRD_SCENE_ALREADY_RESERVED_NO_RETRY")
    if (not sc or sc[0] != first_suffix_token
            or sc[1] != "PARTIAL_OR_UNKNOWN_OUTCOME"):
        raise ValueError("FIRST_SUFFIX_DURABLE_HASH_OR_STATE_MISMATCH")
    prior_result = json.loads(sc[2])
    if prior_result.get("failedStep") != FAILED_STEP:
        raise ValueError("FIRST_SUFFIX_FAILED_STEP_CHANGED")
    if (len(rows) != 3 or tuple(x[0] for x in rows) != EXPECTED_PREVIOUS
            or [x[1] for x in rows] != [
                "PASS", "PASS", "CREATED_UNVERIFIED"]):
        raise ValueError("FIRST_SUFFIX_THREE_STEP_JOURNAL_MISMATCH")
    if any(not isinstance(x[2], str) or not RUN._GUID.fullmatch(x[2]) for x in rows):
        raise ValueError("FIRST_SUFFIX_GUID_MISSING")
    current = REPAIR.all_guids(api)
    extra = [guid.lower() for _, _, guid in rows]
    if (len(current) != 28 or len(set(extra)) != 3
            or set(extra) & set(first_25_guids)
            or current != sorted([*first_25_guids, *extra])):
        raise ValueError("CURRENT_28_GUID_INVENTORY_DRIFT")
    all_steps = {x["id"]: x for x in original_plan["graph"]["operations"]}
    seeded = dict(seeded_five)
    for sid, _, guid in rows:
        step = all_steps[sid]
        params = step["params"]
        floor = next(iter(params.values()))[0]["floorIndex"]
        kind = RUN.verify_readback(
            step["command"], params, RUN.requested_details(api, guid),
            expected_floor=floor,
            expected_story_level=RUN.story_level_for_floor(bound_stories, floor))
        seeded[sid] = {"guid": guid, "kind": kind, "floorIndex": floor}
    if len(seeded) != 8 or set(seeded) != set(original_plan["executionOrder"][:8]):
        raise ValueError("EIGHT_VERIFIED_PREFIX_ELEMENTS_REQUIRED")
    if RUN.guarded_project(api, bound_stories[0]) != binding or REPAIR.all_guids(api) != current:
        raise ValueError("PROJECT_CHANGED_DURING_READ_ONLY_RECONCILIATION")
    remaining = original_plan["executionOrder"][8:]
    request = {
        "operation": "CONTINUE_ONLY_VERIFIED_SEVENTEEN",
        "thirdSceneId": THIRD_SCENE_ID,
        "previousSuffix": CONT.SUFFIX_ID,
        "previousSuffixToken": first_suffix_token,
        "originalSceneId": original_scene["sceneId"],
        "originalPlanHash": original_scene["planHash"],
        "schemaSha256": original_plan["schemaSha256"],
        "graphHash": RUN.digest(original_plan["graph"]),
        "project": binding,
        "materialName": material, "materialGuid": material_guid,
        "seeded": seeded,
        "nativeInventory": current,
        "remainingStepIds": remaining,
    }
    token = RUN.digest(request)
    return {
        "status": "READY_FOR_EXPLICIT_SEVENTEEN_STEP_CONTINUATION",
        "token": token,
        "binding": binding,
        "sourcePlanHash": token,
        "sceneId": THIRD_SCENE_ID,
        "graph": original_plan["graph"],
        "executionOrder": original_plan["executionOrder"],
        "metrics": original_plan["metrics"],
        "slabBasicMaterialGuid": material_guid,
        "storyBindings": bound_stories,
        "newStepIds": remaining,
        "reusedCount": len(seeded),
        "remainingCount": len(remaining),
        "modelWriteAttempts": 0,
        "reused": seeded,
        "before": current,
        "journal": str(journal),
    }


def execute(api, material, token):
    ticket = proof(api, material)
    if not isinstance(token, str) or token != ticket["token"]:
        raise ValueError("EXPLICIT_SEVENTEEN_STEP_APPROVAL_TOKEN_MISMATCH")
    writer = RUN.SceneWriter(api, Path(ticket["journal"]))
    writer.required_story = ticket["storyBindings"][0]
    return writer._execute_verified_plan(
        ticket, THIRD_SCENE_ID, ticket["token"],
        seeded_created=ticket["reused"],
        approval_source="owner-confirmed-verified-third-suffix-only-17",
        on_before_complete=lambda pre, created: CONT.finish_verify(api, ticket, pre, created))


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--port", type=int, default=19726)
    p.add_argument("--material", required=True)
    p.add_argument("--confirm-token",
                   help="Explicitly approve only the 17 missing Create calls on the exact scratch PLN")
    args = p.parse_args(argv)
    try:
        RUN.bind_approved_scratch_pln(args.port)
        api = lambda command, params: RUN.tapir(args.port, command, params)
        if args.confirm_token:
            out = execute(api, args.material, args.confirm_token)
            public = {
                "status": out["status"],
                "sceneId": out["sceneId"],
                "reusedCount": out["reusedCount"],
                "newCreatedCount": out.get("newCreatedCount"),
                "allGuidsReadback": out.get("allGuidsReadback", False),
                "failedStep": out.get("failedStep"),
                "reason": out.get("reason"),
                "plnSaved": False,
            }
        else:
            out = proof(api, args.material)
            public = {k: out[k] for k in ("status", "token", "binding",
                "sceneId", "reusedCount", "remainingCount", "modelWriteAttempts")}
        print(json.dumps(public, ensure_ascii=False, indent=2))
        return 0 if public["status"] in (
            "READY_FOR_EXPLICIT_SEVENTEEN_STEP_CONTINUATION", "COMPLETE_UNSAVED") else 2
    except Exception as exc:
        print(json.dumps({"status": "BLOCKED",
                          "reason": type(exc).__name__ + ": " + str(exc),
                          "automaticRetry": False,
                          "plnSaved": False}, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    sys.exit(main())
