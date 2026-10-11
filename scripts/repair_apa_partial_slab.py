"""One-off reconciliation of the known 2026-10-11 APA scratch slab incident.

DEFAULT IS READ ONLY. --confirm-token authorizes at most ONE ModifySlabs call
after full native preflight, matched exact historical evidence and durable
SQLite reservation. The interrupted Create-scene is never replayed or saved.
This is a narrow recovery utility built on the EXISTING SceneWriter helpers,
not a second general-purpose scene writer.
"""
from __future__ import annotations

import argparse
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import sys

import archicad_scene_run as RUN

EVIDENCE = Path(r"C:\LocalAI\APA_Trial_Evidence\20261011-031123-7181b47c")
SLAB_GUID = "BB516C6F-587B-4F51-AFCC-180291542687"
EXPECTED_OLD_THICKNESS = .30
WALL_IDS = ("s1-wall-south", "s1-wall-east", "s1-wall-north", "s1-wall-west")
FAILED_STEP = "s1-slab"
REPAIR_TABLE = "apa_partial_slab_repairs"


def read_evidence(directory):
    result = json.loads((directory / "execute" / "result.json").read_text(encoding="utf-8"))
    plan = json.loads((directory / "execute" / "plan.json").read_text(encoding="utf-8"))
    before = json.loads((directory / "execute" / "inventory-before.json").read_text(encoding="utf-8"))
    if not isinstance(before, list) or len(before) != 20:
        raise ValueError("EXPECTED_BASELINE_20_ELEMENTS")
    scene = result.get("scene", {})
    if (result.get("status") != "PARTIAL_OR_UNKNOWN_OUTCOME"
            or scene.get("failedStep") != FAILED_STEP
            or not isinstance(scene.get("sceneId"), str)
            or not isinstance(scene.get("planHash"), str)):
        raise ValueError("INCORRECT_HISTORICAL_SCENE")
    journal = directory.parent / "persistent-ledger" / "scene-v1-attempts.sqlite3"
    if not journal.is_file():
        raise ValueError("ORIGINAL_DURABLE_JOURNAL_MISSING")
    return scene, plan, before, journal


def journal_view(journal, scene):
    # Reading the original ledger must not create or modify any journal file.
    with closing(sqlite3.connect(journal.resolve().as_uri() + "?mode=ro", uri=True)) as db:
        parent = db.execute("SELECT plan_hash,state FROM scenes WHERE scene_id=?",
                            (scene["sceneId"],)).fetchone()
        rows = db.execute(
            "SELECT step_id,state,guid FROM steps WHERE scene_id=?",
            (scene["sceneId"],)).fetchall()
        already = False
        table = db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (REPAIR_TABLE,)).fetchone()
        if table:
            already = db.execute(
                "SELECT 1 FROM apa_partial_slab_repairs WHERE scene_id=?",
                (scene["sceneId"],)).fetchone() is not None
    if (not parent or parent != (scene["planHash"], "PARTIAL_OR_UNKNOWN_OUTCOME")
            or len(rows) != 5 or len({x[0] for x in rows}) != 5):
        raise ValueError("HISTORICAL_JOURNAL_NOT_EXACT_FIVE_STEP_PARTIAL")
    by_id = {sid: {"state": state, "guid": guid} for sid, state, guid in rows}
    if set(by_id) != set(WALL_IDS) | {FAILED_STEP}:
        raise ValueError("UNEXPECTED_JOURNAL_STEPS")
    if any(by_id[s]["state"] != "PASS" for s in WALL_IDS):
        raise ValueError("PREVIOUS_WALLS_NOT_JOURNAL_PASS")
    slab = by_id[FAILED_STEP]
    if slab["state"] != "CREATED_UNVERIFIED" or slab["guid"].lower() != SLAB_GUID.lower():
        raise ValueError("WRONG_FAILED_SLAB_GUID_OR_STATE")
    if already:
        raise ValueError("SLAB_REPAIR_ALREADY_RESERVED_DO_NOT_RETRY")
    return by_id


def all_guids(api):
    rows = api("GetAllElements", {}).get("elements")
    if not isinstance(rows, list):
        raise ValueError("NATIVE_INVENTORY_MISSING")
    ids = [x["elementId"]["guid"].lower() for x in rows]
    if any(not RUN._GUID.fullmatch(g) for g in ids) or len(ids) != len(set(ids)):
        raise ValueError("INVALID_NATIVE_INVENTORY")
    return sorted(ids)


def exact_plan_steps(plan):
    ops = plan.get("graph", {}).get("operations")
    if not isinstance(ops, list):
        raise ValueError("HISTORICAL_PLAN_MISSING")
    steps = {s.get("id"): s for s in ops}
    if not set((*WALL_IDS, FAILED_STEP)) <= set(steps):
        raise ValueError("HISTORICAL_WALL_AND_SLAB_PLANS_MISSING")
    return steps


def preflight(api, directory, material_name):
    if (not isinstance(material_name, str) or not material_name
            or material_name != material_name.strip()):
        raise ValueError("EXPLICIT_MATERIAL_NAME_REQUIRED")
    scene, plan, baseline, journal = read_evidence(directory)
    steps = exact_plan_steps(plan)
    binding_rows = plan.get("storyBindings")
    if not isinstance(binding_rows, list) or not binding_rows:
        raise ValueError("HISTORICAL_STORY_BINDING_MISSING")
    binding = RUN.guarded_project(api, binding_rows[0])
    recorded = journal_view(journal, scene)
    before = {g.lower() for g in baseline}
    added = {row["guid"].lower() for row in recorded.values()}
    current = all_guids(api)
    if (len(current) != 25 or len(before) != 20 or len(added) != 5
            or set(current) != before | added or before & added):
        raise ValueError("ORIGINAL_25_ELEMENT_INVENTORY_CHANGED")
    # Re-verify the four real native walls, not merely the old PASS journal.
    for sid in WALL_IDS:
        params = steps[sid]["params"]
        row = RUN.requested_details(api, recorded[sid]["guid"])
        RUN.verify_readback("CreateWalls", params, row,
                            expected_floor=params["wallsData"][0]["floorIndex"])
    slab_step = steps[FAILED_STEP]
    params = slab_step["params"]
    expected = params["slabsData"][0]
    row = RUN.requested_details(api, SLAB_GUID)
    RUN.verify_readback("CreateSlabs", params, row,
                        expected_floor=expected["floorIndex"],
                        allow_slab_thickness_mismatch=True)
    details = row["details"]
    if (details.get("structureType") != "Composite"
            or not RUN.close(details.get("thickness"), EXPECTED_OLD_THICKNESS)
            or not RUN.close(expected["thickness"], .20)):
        raise ValueError("ACTUAL_SLAB_NO_LONGER_MATCHES_HISTORICAL_MISMATCH")
    material_guid = RUN.resolve_basic_slab_material(api, material_name)
    modify = {"slabsWithDetails": [{
        "elementId": {"guid": SLAB_GUID},
        "structureType": "Basic",
        "thickness": expected["thickness"],
        "buildingMaterialId": {"guid": material_guid},
    }]}
    intent = {"operation": "RECOVER_ONE_EXISTING_SLAB_MODIFY_ONLY",
              "sceneId": scene["sceneId"], "planHash": scene["planHash"],
              "project": binding, "evidence": str(directory), "slabGuid": SLAB_GUID,
              "materialName": material_name, "materialGuid": material_guid,
              "baselineGuids": current, "requestedNativeParams": modify}
    # No state mutation during preflight; read original live inventory twice.
    if RUN.guarded_project(api, binding_rows[0]) != binding or all_guids(api) != current:
        raise ValueError("PROJECT_CHANGED_DURING_PREFLIGHT")
    return {"status": "READY_FOR_EXPLICIT_SINGLE_SLAB_REPAIR",
            "token": RUN.digest(intent), "sceneId": scene["sceneId"],
            "slabGuid": SLAB_GUID, "project": binding,
            "expectedThickness": .20, "currentThickness": .30,
            "material": material_name, "materialGuid": material_guid,
            "modelWriteAttempts": 0, "repairIntent": intent,
            "journalPath": str(journal),
            "projectStory": binding_rows[0],
            "expectedSlabPolygon": expected["polygonCoordinates"]}


def repair(api, directory, material, confirm_token):
    ticket = preflight(api, directory, material)
    if not isinstance(confirm_token, str) or confirm_token != ticket["token"]:
        raise ValueError("EXPLICIT_REPAIR_CONFIRMATION_TOKEN_MISMATCH")
    journal = Path(ticket["journalPath"])
    params = ticket["repairIntent"]["requestedNativeParams"]
    scene_id = ticket["sceneId"]
    with closing(sqlite3.connect(str(journal), timeout=15)) as db:
        db.execute("PRAGMA synchronous=FULL")
        db.execute(
            "CREATE TABLE IF NOT EXISTS apa_partial_slab_repairs "
            "(scene_id TEXT NOT NULL,slab_guid TEXT NOT NULL,token TEXT NOT NULL,"
            "state TEXT NOT NULL,intent_json TEXT NOT NULL,result_json TEXT NOT NULL,"
            "PRIMARY KEY(scene_id,slab_guid))")
        db.commit()
        db.execute("BEGIN IMMEDIATE")
        if db.execute("SELECT 1 FROM apa_partial_slab_repairs WHERE scene_id=?",
                      (scene_id,)).fetchone():
            db.rollback()
            raise ValueError("SLAB_REPAIR_ALREADY_RESERVED_DO_NOT_RETRY")
        db.execute("INSERT INTO apa_partial_slab_repairs VALUES (?,?,?,?,?,?)",
                   (scene_id, SLAB_GUID, ticket["token"], "ATTEMPTED",
                    RUN.canonical(ticket["repairIntent"]), "{}"))
        db.commit()  # durable reservation before the single native mutation
        try:
            # Guard AGAIN at the mutation boundary, including the exact target.
            if RUN.guarded_project(api, ticket["projectStory"]) != ticket["project"]:
                raise ValueError("PROJECT_SWITCHED_BEFORE_REPAIR")
            reply = api("ModifySlabs", params)
            results = reply.get("executionResults") if isinstance(reply, dict) else None
            if (not isinstance(results, list) or len(results) != 1
                    or not isinstance(results[0], dict)
                    or results[0].get("success") is not True):
                raise ValueError("NATIVE_MODIFY_SLAB_NOT_CONFIRMED")
            row = RUN.requested_details(api, SLAB_GUID)
            if row.get("floorIndex") != 0 or row.get("type") != "Slab":
                raise ValueError("SLAB_CHANGED_STORY_OR_TYPE")
            details = row.get("details", {})
            if (not RUN.close(details.get("thickness"), .20)
                    or details.get("structureType") != "Basic"
                    or details.get("buildingMaterialId", {}).get("guid", "").lower()
                       != ticket["materialGuid"].lower()):
                raise ValueError("SLAB_REPAIR_TYPED_READBACK_MISMATCH")
            expected_polygon = ticket["expectedSlabPolygon"]
            if not RUN.compare_polygon(expected_polygon, details.get("polygonOutline")):
                raise ValueError("SLAB_POLYGON_CHANGED_AFTER_MODIFY")
            if RUN.guarded_project(api, ticket["projectStory"]) != ticket["project"]:
                raise ValueError("PROJECT_SWITCHED_AFTER_REPAIR")
            if all_guids(api) != ticket["repairIntent"]["baselineGuids"]:
                raise ValueError("GUID_INVENTORY_CHANGED_AFTER_MODIFY")
            outcome = {"status": "SINGLE_SLAB_REPAIR_VERIFIED_UNSAVED",
                       "guid": SLAB_GUID, "structureType": "Basic",
                       "thickness": .20, "materialGuid": ticket["materialGuid"],
                       "plnSaved": False, "createCalls": 0, "modifyCalls": 1,
                       "remainingSceneOperations": "NOT_EXECUTED"}
            db.execute("UPDATE apa_partial_slab_repairs SET state=?,result_json=? "
                       "WHERE scene_id=? AND slab_guid=?",
                       ("READBACK_PASS", RUN.canonical(outcome), scene_id, SLAB_GUID))
            db.commit()
            return outcome
        except Exception as exc:
            # A native mutation may have happened before timeout/failed readback.
            db.execute("UPDATE apa_partial_slab_repairs SET state=?,result_json=? "
                       "WHERE scene_id=? AND slab_guid=?",
                       ("UNKNOWN_NEEDS_MANUAL_INSPECTION",
                        RUN.canonical({"error": type(exc).__name__ + ": " + str(exc)}),
                        scene_id, SLAB_GUID))
            db.commit()
            return {"status": "REPAIR_OUTCOME_UNCERTAIN_NO_RETRY",
                    "error": type(exc).__name__ + ": " + str(exc),
                    "slabGuid": SLAB_GUID, "plnSaved": False}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--port", type=int, default=19726)
    p.add_argument("--material", required=True,
                   help="Exact material name returned by GetAttributesByType")
    p.add_argument("--confirm-token", help="Read-only preflight token; omit for zero writes")
    args = p.parse_args(argv)
    RUN.bind_approved_scratch_pln(args.port)
    api = lambda command, params: RUN.tapir(args.port, command, params)
    if args.confirm_token:
        output = repair(api, EVIDENCE, args.material, args.confirm_token)
    else:
        ticket = preflight(api, EVIDENCE, args.material)
        output = {k: v for k, v in ticket.items()
                  if k not in ("repairIntent", "expectedSlabPolygon")}
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if output["status"] in (
        "READY_FOR_EXPLICIT_SINGLE_SLAB_REPAIR",
        "SINGLE_SLAB_REPAIR_VERIFIED_UNSAVED") else 2


if __name__ == "__main__":
    sys.exit(main())
