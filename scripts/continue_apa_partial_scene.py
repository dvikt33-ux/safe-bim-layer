"""Continue exactly the 20 unfinished steps of a verified, repaired APA test scene.

Read-only by default. Requires original on-disk SHA256 evidence, immutable
create ledger, exact native 25-GUID inventory, readback of four original walls
and repaired slab, and separate explicit confirmation for new Create operations.
Reuses SceneWriter._execute_verified_plan; NEVER reruns the original 25 steps.
No Save, no project switch, no automatic retry.
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

SUFFIX_ID = "apa-suffix-20261011-031123-7181b47c"
FIRST = (*REPAIR.WALL_IDS, REPAIR.FAILED_STEP)
ORIGINAL_INTENT = Path(__file__).resolve().parents[1] / (
    "examples/accelerator/apa-test-house-01.intent.json")


def verify_evidence_manifest(folder):
    record = json.loads((folder / "execute" / "SHA256.json").read_text(encoding="utf-8"))
    for name in ("plan.json", "result.json", "inventory-before.json"):
        expected = record.get(name)
        data = (folder / "execute" / name).read_bytes()
        if (not isinstance(expected, str) or len(expected) != 64
                or hashlib.sha256(data).hexdigest() != expected):
            raise ValueError("HISTORICAL_EVIDENCE_SHA256_MISMATCH: " + name)


def read_repaired_ledger(journal, scene):
    # Existing incomplete creation is preserved verbatim. The one-shot slab
    # repair has a separate durable row, checked without changing either.
    with closing(sqlite3.connect(journal.resolve().as_uri() + "?mode=ro", uri=True)) as db:
        parent = db.execute(
            "SELECT plan_hash,state FROM scenes WHERE scene_id=?",
            (scene["sceneId"],)).fetchone()
        rows = db.execute(
            "SELECT step_id,state,guid FROM steps WHERE scene_id=?",
            (scene["sceneId"],)).fetchall()
        exists = db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (REPAIR.REPAIR_TABLE,)).fetchone()
        repaired = (db.execute(
            "SELECT slab_guid,token,state,intent_json,result_json "
            "FROM apa_partial_slab_repairs WHERE scene_id=?",
            (scene["sceneId"],)).fetchone() if exists else None)
        existing_suffix = db.execute(
            "SELECT 1 FROM scenes WHERE scene_id=?", (SUFFIX_ID,)).fetchone()
    if existing_suffix:
        raise ValueError("SUFFIX_ALREADY_RESERVED_DO_NOT_REPLAY")
    if parent != (scene["planHash"], "PARTIAL_OR_UNKNOWN_OUTCOME"):
        raise ValueError("ORIGINAL_SCENE_NOT_PARTIAL")
    if len(rows) != 5 or len({row[0] for row in rows}) != 5:
        raise ValueError("ORIGINAL_FIVE_JOURNAL_ROWS_REQUIRED")
    prefix = {sid: {"state": state, "guid": guid} for sid, state, guid in rows}
    if set(prefix) != set(FIRST):
        raise ValueError("ORIGINAL_JOURNAL_PREFIX_MISMATCH")
    if any(prefix[sid]["state"] != "PASS" for sid in REPAIR.WALL_IDS):
        raise ValueError("PREVIOUS_WALL_NOT_VERIFIED")
    if (prefix[REPAIR.FAILED_STEP]["state"] != "CREATED_UNVERIFIED"
            or prefix[REPAIR.FAILED_STEP]["guid"].lower() != REPAIR.SLAB_GUID.lower()):
        raise ValueError("ORIGINAL_SLAB_GUID_MISMATCH")
    if not repaired or repaired[0].lower() != REPAIR.SLAB_GUID.lower() or repaired[2] != "READBACK_PASS":
        raise ValueError("SLAB_REPAIR_NOT_VERIFIED_IN_DURABLE_JOURNAL")
    intent, result = json.loads(repaired[3]), json.loads(repaired[4])
    if (RUN.digest(intent) != repaired[1]
            or intent.get("sceneId") != scene["sceneId"]
            or intent.get("slabGuid", "").lower() != REPAIR.SLAB_GUID.lower()
            or result.get("status") != "SINGLE_SLAB_REPAIR_VERIFIED_UNSAVED"
            or result.get("createCalls") != 0 or result.get("modifyCalls") != 1):
        raise ValueError("REPAIR_DURABLE_INTENT_OR_RESULT_MISMATCH")
    return prefix, intent, result


def verify_live_story_map(api, expected):
    response = api("GetStories", {})
    entries = response.get("stories") if isinstance(response, dict) else None
    if not isinstance(entries, list) or not isinstance(expected, list) or len(expected) != 2:
        raise ValueError("EXPECTED_TWO_STORIES")
    for story in expected:
        row = next((a for a in entries if a.get("index") == story["nativeIndex"]), None)
        if (row is None or row.get("floorId") != story["floorId"]
                or not RUN.close(row.get("level"), story["level"])
                or (row.get("name") or row.get("uName") or "") != story["label"]):
            raise ValueError("SECONDARY_STORY_BINDING_CHANGED")


def inspect_live_prefix(api, plan, prefix, material_guid):
    steps = {s["id"]: s for s in plan["graph"]["operations"]}
    seeded = {}
    for sid in FIRST:
        step = steps[sid]
        guid = prefix[sid]["guid"]
        params = step["params"]
        expected_floor = next(iter(params.values()))[0]["floorIndex"]
        row = RUN.requested_details(api, guid)
        kind = RUN.verify_readback(
            step["command"], params, row, expected_floor=expected_floor,
            expected_story_level=RUN.story_level_for_floor(
                plan["storyBindings"], expected_floor),
            expected_slab_material_guid=(
                material_guid if sid == REPAIR.FAILED_STEP else None))
        seeded[sid] = {"guid": guid, "kind": kind, "floorIndex": expected_floor}
    return seeded


def proof(api, material):
    if not isinstance(material, str) or not material.strip() or material != material.strip():
        raise ValueError("MATERIAL_NAME_REQUIRED")
    verify_evidence_manifest(REPAIR.EVIDENCE)
    scene, plan, baseline, journal = REPAIR.read_evidence(REPAIR.EVIDENCE)
    current_schema = RUN.DEFAULT_SCENE_SCHEMA
    if (plan.get("schemaSha256") != hashlib.sha256(current_schema.read_bytes()).hexdigest()
            or plan.get("schemaVersion") != RUN.EXPECTED_TAPIR):
        raise ValueError("PINNED_SCHEMA_OR_VERSION_MISMATCH")
    original_intent = json.loads(ORIGINAL_INTENT.read_text(encoding="utf-8"))
    original = BUILD.prepare(original_intent["components"][0], current_schema)
    if (plan.get("graph") != original["graph"]
            or plan.get("executionOrder") != original["executionOrder"]
            or plan.get("storyBindings") != original["storyBindings"]
            or len(plan["executionOrder"]) != 25
            or plan["executionOrder"][:5] != list(FIRST)):
        raise ValueError("ORIGINAL_PLAN_DOES_NOT_MATCH_REVIEWED_SOURCE")
    prefix, repair_intent, repair_result = read_repaired_ledger(journal, scene)
    binding = RUN.guarded_project(api, plan["storyBindings"][0])
    verify_live_story_map(api, plan["storyBindings"])
    if repair_intent.get("project") != binding:
        raise ValueError("REPAIR_PROJECT_IDENTITY_CHANGED")
    material_guid = RUN.resolve_basic_slab_material(api, material)
    if (material != repair_intent.get("materialName")
            or material_guid.lower() != repair_intent.get("materialGuid", "").lower()
            or material_guid.lower() != repair_result.get("materialGuid", "").lower()):
        raise ValueError("REPAIR_MATERIAL_BINDING_CHANGED")
    before = sorted(x.lower() for x in baseline)
    prefix_guids = sorted(row["guid"].lower() for row in prefix.values())
    native_guids = REPAIR.all_guids(api)
    if (len(before) != 20 or len(prefix_guids) != 5
            or len(native_guids) != 25
            or native_guids != sorted([*before, *prefix_guids])):
        raise ValueError("PROJECT_25_ELEMENT_BASELINE_DRIFT")
    seeded = inspect_live_prefix(api, plan, prefix, material_guid)
    if (RUN.guarded_project(api, plan["storyBindings"][0]) != binding
            or REPAIR.all_guids(api) != native_guids):
        raise ValueError("NATIVE_STATE_CHANGED_DURING_CONTINUATION_PREFLIGHT")
    request = {
        "continuationSceneId": SUFFIX_ID,
        "originSceneId": scene["sceneId"],
        "originPlanHash": scene["planHash"],
        "repairedSlabGuid": REPAIR.SLAB_GUID,
        "repairToken": RUN.digest(repair_intent),
        "schemaSha256": plan["schemaSha256"],
        "project": binding,
        "material": material, "materialGuid": material_guid,
        "reusedGuids": seeded,
        "nativeInventory": native_guids,
        "remainingStepIds": plan["executionOrder"][5:],
        "graphHash": RUN.digest(plan["graph"]),
    }
    token = RUN.digest(request)
    ticket = {
        "status": "READY_FOR_EXPLICIT_TWENTY_STEP_CONTINUATION",
        "token": token,
        "binding": binding,
        "sourcePlanHash": token,
        "graph": plan["graph"],
        "executionOrder": plan["executionOrder"],
        "slabBasicMaterialGuid": material_guid,
        "metrics": plan["metrics"],
        "sceneId": SUFFIX_ID,
        "reusedCount": 5,
        "remainingCount": 20,
        "modelWriteAttempts": 0,
        "reused": seeded,
        "before": native_guids,
        "storyBindings": plan["storyBindings"],
        "journal": str(journal),
    }
    return ticket


def finish_verify(api, ticket, preflight, created):
    if RUN.guarded_project(api, ticket["storyBindings"][0]) != ticket["binding"]:
        raise ValueError("FINAL_PROJECT_CHANGED")
    verify_live_story_map(api, ticket["storyBindings"])
    if set(created) - {"__plan__"} != set(ticket["executionOrder"]):
        raise ValueError("FINAL_GRAPH_HAS_MISSING_ELEMENTS")
    expected_new = sorted(
        created[sid]["guid"].lower() for sid in ticket["executionOrder"][5:])
    existing = set(ticket["before"])
    actual = REPAIR.all_guids(api)
    if (len(expected_new) != 20 or set(expected_new) & existing
            or actual != sorted([*existing, *expected_new]) or len(actual) != 45):
        raise ValueError("FINAL_NATIVE_GUID_INVENTORY_MISMATCH")
    for sid in ticket["executionOrder"]:
        step = next(x for x in ticket["graph"]["operations"] if x["id"] == sid)
        params = RUN.resolve_params(step, created)
        host = (RUN.check_previous_wall(api, step, created,
                                        ticket["storyBindings"])
                if step["command"] in ("CreateWindows", "CreateDoors") else None)
        floor = created[sid]["floorIndex"]
        RUN.verify_readback(
            step["command"], params,
            RUN.requested_details(api, created[sid]["guid"]),
            host, expected_floor=floor,
            expected_story_level=RUN.story_level_for_floor(
                ticket["storyBindings"], floor),
            expected_slab_material_guid=(
                preflight["slabBasicMaterialGuid"]
                if step["command"] == "CreateSlabs" else None))
    if (RUN.guarded_project(api, ticket["storyBindings"][0]) != ticket["binding"]
            or REPAIR.all_guids(api) != actual):
        raise ValueError("FINAL_BINDING_OR_INVENTORY_DRIFT")


def continue_scene(api, material, token):
    ticket = proof(api, material)
    if not isinstance(token, str) or token != ticket["token"]:
        raise ValueError("EXPLICIT_TWENTY_STEP_CONFIRMATION_TOKEN_MISMATCH")
    writer = RUN.SceneWriter(api, Path(ticket["journal"]))
    writer.required_story = ticket["storyBindings"][0]
    out = writer._execute_verified_plan(
        ticket, SUFFIX_ID, ticket["token"],
        seeded_created=ticket["reused"],
        approval_source="owner-confirmed-one-shot-twenty-op-remainder",
        on_before_complete=lambda pre, created: finish_verify(api, ticket, pre, created))
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=19726)
    parser.add_argument("--material", required=True)
    parser.add_argument("--confirm-token",
                        help="Run EXACT 20 remaining native creates only with separate owner approval")
    args = parser.parse_args(argv)
    try:
        RUN.bind_approved_scratch_pln(args.port)
        api = lambda command, params: RUN.tapir(args.port, command, params)
        if args.confirm_token is None:
            out = proof(api, args.material)
            out = {key: out[key] for key in (
                "status", "token", "binding", "sceneId",
                "reusedCount", "remainingCount", "modelWriteAttempts")}
        else:
            out = continue_scene(api, args.material, args.confirm_token)
            out = {
                "status": out["status"],
                "sceneId": out["sceneId"],
                "newCreatedCount": out.get("newCreatedCount"),
                "reusedCount": out["reusedCount"],
                "plnSaved": out["plnSaved"],
                "allGuidsReadback": out.get("allGuidsReadback", False),
                "reason": out.get("reason"),
                "failedStep": out.get("failedStep"),
                "manualReconciliationRequired": out.get("manualReconciliationRequired", False),
            }
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0 if out["status"] in (
            "READY_FOR_EXPLICIT_TWENTY_STEP_CONTINUATION", "COMPLETE_UNSAVED") else 2
    except Exception as exc:
        print(json.dumps({"status": "BLOCKED",
                          "reason": type(exc).__name__ + ": " + str(exc),
                          "automaticRetry": False,
                          "plnSaved": False}, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    sys.exit(main())
