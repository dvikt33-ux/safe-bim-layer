"""Repair ONLY the created s2-slab in the 2026-10-11 exact scratch PLN.

Default: READ ONLY. A separate owner-provided confirmation token authorizes at
most ONE journaled ModifySlabs. Previous Create scenes remain immutable and
cannot be replayed. Zero automatic retry, save, delete or rollback.
"""
from __future__ import annotations

import argparse
from contextlib import closing
import json
import sqlite3
import sys

import archicad_scene_run as RUN
import repair_apa_partial_slab as REPAIR
import continue_apa_partial_scene as CONT
import continue_apa_after_story_z as THIRD

REPAIR_TABLE = "apa_suffix3_slab_repairs"
FAILED = "s2-slab"
PREVIOUS = ("s2-wall-east", "s2-wall-north", "s2-wall-west")
TARGET_GUID = "1020BDF5-AFEC-455E-BAB9-D17999AC1567"


def view(db, scene_id):
    return (
        db.execute("SELECT plan_hash,state,result FROM scenes WHERE scene_id=?",
                   (scene_id,)).fetchone(),
        db.execute("SELECT step_id,state,guid FROM steps WHERE scene_id=? ORDER BY rowid",
                   (scene_id,)).fetchall(),
    )


def preflight(api, material_name):
    if not isinstance(material_name, str) or not material_name or material_name.strip() != material_name:
        raise ValueError("EXPLICIT_PROJECT_MATERIAL_REQUIRED")
    CONT.verify_evidence_manifest(REPAIR.EVIDENCE)
    historical, plan, prior20, journal = REPAIR.read_evidence(REPAIR.EVIDENCE)
    story_rows = plan["storyBindings"]
    binding = RUN.guarded_project(api, story_rows[0])
    CONT.verify_live_story_map(api, story_rows)
    if len(prior20) != 20 or len(plan["graph"]["operations"]) != 25:
        raise ValueError("ORIGINAL_SCENE_EVIDENCE_NOT_EXACT")
    with closing(sqlite3.connect(journal.resolve().as_uri() + "?mode=ro", uri=True)) as db:
        original, initial = view(db, historical["sceneId"])
        second, second_rows = view(db, CONT.SUFFIX_ID)
        third, third_rows = view(db, THIRD.THIRD_SCENE_ID)
        existing = db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (REPAIR_TABLE,)).fetchone()
        taken = (db.execute(
            "SELECT 1 FROM apa_suffix3_slab_repairs WHERE scene_id=?",
            (THIRD.THIRD_SCENE_ID,)).fetchone() if existing else None)
        first_repair = db.execute(
            "SELECT state,slab_guid,intent_json,result_json FROM apa_partial_slab_repairs "
            "WHERE scene_id=?", (historical["sceneId"],)).fetchone()
    if taken:
        raise ValueError("SUFFIX3_SLAB_REPAIR_ALREADY_RESERVED_NEVER_RETRY")
    if (not original or original[:2] != (
            historical["planHash"], "PARTIAL_OR_UNKNOWN_OUTCOME")
            or not second or second[1] != "PARTIAL_OR_UNKNOWN_OUTCOME"
            or not third or third[1] != "PARTIAL_OR_UNKNOWN_OUTCOME"):
        raise ValueError("HISTORIC_EXECUTION_JOURNALS_NOT_PARTIAL")
    third_summary = json.loads(third[2])
    if third_summary.get("failedStep") != FAILED:
        raise ValueError("THIRD_SCENE_FAILURE_STEP_CHANGED")
    if (len(initial) != 5 or len(second_rows) != 3
            or tuple(x[0] for x in second_rows) != (
                "s1-partition-1", "s1-partition-2", "s2-wall-south")
            or len(third_rows) != 4
            or tuple(x[0] for x in third_rows) != (*PREVIOUS, FAILED)
            or tuple(x[1] for x in third_rows) != (
                "PASS", "PASS", "PASS", "CREATED_UNVERIFIED")
            or not third_rows[-1][2]
            or third_rows[-1][2].lower() != TARGET_GUID.lower()):
        raise ValueError("THIRD_SCENE_JOURNAL_NOT_EXACT_3_WALLS_1_SLAB: " + RUN.canonical([(sid, state) for sid, state, _ in third_rows]))
    if (not first_repair or first_repair[0] != "READBACK_PASS"
            or first_repair[1].lower() != REPAIR.SLAB_GUID.lower()
            or json.loads(first_repair[3]).get("status") !=
            "SINGLE_SLAB_REPAIR_VERIFIED_UNSAVED"):
        raise ValueError("FIRST_SLAB_REPAIR_NOT_VERIFIED")
    ids = [x[2].lower() for x in (*initial, *second_rows, *third_rows)
           if isinstance(x[2], str)]
    before = [g.lower() for g in prior20]
    native = REPAIR.all_guids(api)
    if (len(ids) != 12 or len(before) != 20 or len(native) != 32
            or len(set(ids)) != 12 or native != sorted([*before, *ids])):
        raise ValueError("CURRENT_32_ELEMENT_GUIDS_NOT_EXACT_JOURNAL")
    # Verify every pre-existing wall before allowing one write. No geometry
    # change, recalculation, moving or deletion of those walls is permitted.
    ops = {x["id"]: x for x in plan["graph"]["operations"]}
    for sid, state, guid in (*initial, *second_rows, *third_rows):
        if sid == FAILED:
            continue
        step = ops[sid]
        if step["command"] == "CreateWalls":
            floor = step["params"]["wallsData"][0]["floorIndex"]
            RUN.verify_readback(
                "CreateWalls", step["params"], RUN.requested_details(api, guid),
                expected_floor=floor,
                expected_story_level=RUN.story_level_for_floor(story_rows, floor))
        elif sid == "s1-slab":
            RUN.verify_readback(
                "CreateSlabs", step["params"], RUN.requested_details(api, guid),
                expected_floor=0,
                expected_slab_material_guid=RUN.resolve_basic_slab_material(
                    api, material_name))
    target = ops[FAILED]["params"]["slabsData"][0]
    live = RUN.requested_details(api, TARGET_GUID)
    actual = live.get("details")
    floor_z = RUN.story_level_for_floor(story_rows, 1)
    if (live.get("type") != "Slab" or live.get("floorIndex") != 1
            or not isinstance(actual, dict)
            or not RUN.close(floor_z, 3.0)
            or not RUN.close(target["thickness"], .20)
            or actual.get("structureType") != "Composite"
            or not RUN.close(actual.get("thickness"), .30)
            or not RUN.close(actual.get("level"), -3.0)
            or not RUN.close(actual.get("zCoordinate"), 0.0)
            or not RUN.compare_polygon(
                target["polygonCoordinates"], actual.get("polygonOutline"))):
        raise ValueError("SUFFIX3_SLAB_CURRENT_GEOMETRY_NOT_EXACT_EXPECTED_MISMATCH")
    material_guid = RUN.resolve_basic_slab_material(api, material_name)
    first_intent = json.loads(first_repair[2])
    if (first_intent.get("materialName") != material_name
            or first_intent.get("materialGuid", "").lower() != material_guid.lower()):
        raise ValueError("BUILDING_MATERIAL_DIFFERENT_FROM_VERIFIED_FLOOR1")
    modifier = {"slabsWithDetails": [{
        "elementId": {"guid": TARGET_GUID},
        "structureType": "Basic",
        "zCoordinate": floor_z,
        "thickness": .20,
        "buildingMaterialId": {"guid": material_guid},
    }]}
    intent = {
        "command": "ModifySlabs",
        "scope": binding,
        "sceneId": THIRD.THIRD_SCENE_ID,
        "failedStep": FAILED, "createdGuid": TARGET_GUID,
        "requested": modifier,
        "materialName": material_name,
        "materialGuid": material_guid,
        "nativeInventoryBefore": native,
        "originalEvidence": str(REPAIR.EVIDENCE),
        "journal": str(journal),
        "originalPlanHash": historical["planHash"],
        "thirdPlanHash": third[0],
        "storyBindings": story_rows,
    }
    if (RUN.guarded_project(api, story_rows[0]) != binding
            or REPAIR.all_guids(api) != native):
        raise ValueError("PREWRITE_NATIVE_IDENTITY_OR_INVENTORY_DRIFT")
    return {
        "status": "READY_FOR_EXPLICIT_SINGLE_S2_SLAB_REPAIR",
        "token": RUN.digest(intent),
        "guid": TARGET_GUID, "targetStoryLevel": floor_z,
        "nativeCurrentZ": 0.0, "desiredStructureType": "Basic",
        "desiredThickness": .20, "material": material_name,
        "binding": binding, "journal": str(journal), "intent": intent,
        "modelWriteAttempts": 0,
        "polygon": target["polygonCoordinates"],
    }


def execute(api, material_name, token):
    ticket = preflight(api, material_name)
    if not isinstance(token, str) or token != ticket["token"]:
        raise ValueError("EXPLICIT_REPAIR_TOKEN_REQUIRED")
    intent = ticket["intent"]
    with closing(sqlite3.connect(ticket["journal"], timeout=15)) as db:
        db.execute("PRAGMA synchronous=FULL")
        db.execute(
            "CREATE TABLE IF NOT EXISTS apa_suffix3_slab_repairs ("
            "scene_id TEXT PRIMARY KEY,guid TEXT NOT NULL,token TEXT NOT NULL,"
            "state TEXT NOT NULL,intent_json TEXT NOT NULL,result_json TEXT NOT NULL)")
        db.commit()
        db.execute("BEGIN IMMEDIATE")
        if db.execute(
            "SELECT 1 FROM apa_suffix3_slab_repairs WHERE scene_id=?",
            (THIRD.THIRD_SCENE_ID,)).fetchone():
            db.rollback()
            raise ValueError("SUFFIX3_REPAIR_ALREADY_RESERVED")
        db.execute("INSERT INTO apa_suffix3_slab_repairs VALUES (?,?,?,?,?,?)",
                   (THIRD.THIRD_SCENE_ID, TARGET_GUID, ticket["token"],
                    "ATTEMPTED", RUN.canonical(intent), "{}"))
        db.commit()  # reserved BEFORE native write
        try:
            if RUN.guarded_project(api, intent["storyBindings"][0]) != ticket["binding"]:
                raise ValueError("PROJECT_CHANGED_BEFORE_SLAB_MUTATION")
            native_result = api("ModifySlabs", intent["requested"])
            rows = (native_result.get("executionResults")
                    if isinstance(native_result, dict) else None)
            if (not isinstance(rows, list) or len(rows) != 1
                    or not isinstance(rows[0], dict)
                    or rows[0].get("success") is not True):
                raise ValueError("SUFFIX3_NATIVE_MODIFY_RETURNED_FAILURE")
            after = RUN.requested_details(api, TARGET_GUID)
            details = after.get("details")
            if (after.get("type") != "Slab" or after.get("floorIndex") != 1
                    or not isinstance(details, dict)
                    or details.get("structureType") != "Basic"
                    or not RUN.close(details.get("thickness"), .20)
                    or not RUN.close(details.get("zCoordinate"), ticket["targetStoryLevel"])
                    or not RUN.close(details.get("level"), 0.0)
                    or details.get("buildingMaterialId", {}).get("guid", "").lower()
                       != intent["materialGuid"].lower()
                    or not RUN.compare_polygon(ticket["polygon"],
                                               details.get("polygonOutline"))):
                raise ValueError("SUFFIX3_SLAB_FINAL_TYPED_READBACK_MISMATCH")
            if (RUN.guarded_project(api, intent["storyBindings"][0]) != ticket["binding"]
                    or REPAIR.all_guids(api) != intent["nativeInventoryBefore"]):
                raise ValueError("POSTWRITE_PROJECT_OR_INVENTORY_DRIFT")
            out = {
                "status": "S2_SLAB_REPAIRED_VERIFIED_UNSAVED",
                "guid": TARGET_GUID, "floorIndex": 1,
                "zCoordinate": ticket["targetStoryLevel"],
                "localLevel": 0.0, "thickness": .20,
                "structureType": "Basic",
                "buildingMaterialId": intent["materialGuid"],
                "createCalls": 0, "modifyCalls": 1,
                "plnSaved": False,
            }
            db.execute(
                "UPDATE apa_suffix3_slab_repairs SET state=?,result_json=? "
                "WHERE scene_id=?",
                ("READBACK_PASS", RUN.canonical(out), THIRD.THIRD_SCENE_ID))
            db.commit()
            return out
        except Exception as exc:
            out = {"status": "SUFFIX3_REPAIR_UNKNOWN_NO_RETRY",
                   "reason": type(exc).__name__ + ": " + str(exc),
                   "guid": TARGET_GUID, "plnSaved": False}
            db.execute(
                "UPDATE apa_suffix3_slab_repairs SET state=?,result_json=? "
                "WHERE scene_id=?",
                ("UNKNOWN_NEEDS_INSPECTION", RUN.canonical(out), THIRD.THIRD_SCENE_ID))
            db.commit()
            return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=19726)
    parser.add_argument("--material", required=True)
    parser.add_argument("--confirm-token")
    args = parser.parse_args(argv)
    try:
        RUN.bind_approved_scratch_pln(args.port)
        api = lambda command, params: RUN.tapir(args.port, command, params)
        if args.confirm_token:
            result = execute(api, args.material, args.confirm_token)
        else:
            ticket = preflight(api, args.material)
            result = {k: ticket[k] for k in (
                "status", "token", "guid", "targetStoryLevel",
                "nativeCurrentZ", "desiredStructureType",
                "desiredThickness", "material", "binding", "modelWriteAttempts")}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["status"] in (
            "READY_FOR_EXPLICIT_SINGLE_S2_SLAB_REPAIR",
            "S2_SLAB_REPAIRED_VERIFIED_UNSAVED") else 2
    except Exception as exc:
        print(json.dumps({"status": "BLOCKED",
                          "reason": type(exc).__name__ + ": " + str(exc),
                          "modelWriteAttempts": 0}, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    sys.exit(main())
