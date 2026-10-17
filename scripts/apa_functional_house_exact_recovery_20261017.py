"""Recover the exact 2026-10-17 APA_Functional_Test_House_01 partial scene.

Default: read-only provenance reconciliation. --execute requires matching token.
The original 5 operations are NEVER replayed. One reserved ModifySlabs,
then up to 7 remaining one-shot native creates via EXISTING SceneWriter.
No SaveProject, DeleteElements, project switch, or automatic retry.
Do not run this on BDD. Port and PLN identity are fixed.
"""
from __future__ import annotations

import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import time

import archicad_scene_run as RUN
import archicad_scene_v1 as SCENE

ROOT = Path(r"C:\LocalAI\APA_AC29_Stable")
PLN = Path(r"C:\LocalAI\APA_Functional_Test_House_01.pln")
LEDGER = Path(r"C:\LocalAI\APA_Functional_Test_House_01_ledger\scene-v1-attempts.sqlite3")
SCHEMA = ROOT / "external-tools/apa-readonly-v1/session-factory-v1/tapir-scene-live.json"
PORT = 19726
PLN_SHA = "1efc00a776217723510c8ed5467469b2b4ef4642ba78b5423f6f95c6b9db14f3"
ORIGIN = "apa_functional_house_01_first_build"
SUFFIX = "apa_functional_house_01_verified_suffix_20261017"
REPAIR_TABLE = "apa_functional_house_slab_repair_v1"
WALL_IDS = ("wall-south", "wall-east", "wall-north", "wall-west")
WALL_GUIDS = (
    "8BCC2A69-43D7-472A-BA2B-97BD9599D25E",
    "462BC642-A5FA-431F-B728-F5A25ECBFA64",
    "CF1853A5-D3CF-40D5-9E06-00BED7219E6E",
    "293D0F57-7B5F-488C-BBD9-9216B318CBC5",
)
SLAB_GUID = "2A50ACD3-1EB9-4CD9-A584-E96A2F3343F7"
PREFIX_IDS = (*WALL_IDS, "slab")


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def native_ids(api):
    rows = api("GetAllElements", {}).get("elements")
    require(isinstance(rows, list), "NATIVE_INVENTORY_MISSING")
    guids = [r["elementId"]["guid"].lower() for r in rows]
    require(len(guids) == len(set(guids))
            and all(RUN._GUID.fullmatch(g) for g in guids), "NATIVE_INVENTORY_INVALID")
    return sorted(guids)


def read_journal():
    require(LEDGER.is_file(), "ORIGINAL_JOURNAL_NOT_FOUND")
    with closing(sqlite3.connect(LEDGER.resolve().as_uri() + "?mode=ro", uri=True)) as db:
        origin = db.execute("SELECT plan_hash,state,result FROM scenes WHERE scene_id=?",
                            (ORIGIN,)).fetchone()
        rows = db.execute(
            "SELECT step_id,state,guid FROM steps WHERE scene_id=? ORDER BY rowid",
            (ORIGIN,)).fetchall()
        suffix = db.execute("SELECT 1 FROM scenes WHERE scene_id=?", (SUFFIX,)).fetchone()
        table = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                           (REPAIR_TABLE,)).fetchone()
        repair = db.execute(
            "SELECT token,state,intent_json,result_json FROM " + REPAIR_TABLE
            + " WHERE scene_id=?", (ORIGIN,)).fetchone() if table else None
    return origin, rows, suffix, repair


def context():
    require(PLN.is_file() and SCHEMA.is_file(), "SOURCE_PLN_OR_SCHEMA_MISSING")
    require(sha(PLN) == PLN_SHA, "SAVED_TEST_PLN_SHA_DRIFT")
    RUN.bind_authorized_saved_copy(
        PORT, str(PLN), PLN.stem, PLN_SHA,
        "2026-10-17: user approved building independent APA functional test house")
    api = lambda command, params: RUN.tapir(PORT, command, params)
    writer = RUN.SceneWriter(api, LEDGER, SCHEMA, allow_3d_view_for_write=True)
    binding = writer.guarded_binding()
    preview = SCENE.prepare(300., 300., SCHEMA)
    plan_hash = RUN.native_plan_hash(preview, preview["sourcePlanHash"])
    require(preview["executionOrder"][:5] == list(PREFIX_IDS)
            and len(preview["executionOrder"]) == 12
            and preview["metrics"]["elementCount"] == 12,
            "EXACT_12_ELEMENT_GRAPH_REQUIRED")
    origin, rows, suffix, repair = read_journal()
    require(origin is not None
            and origin[0] == plan_hash
            and origin[1] == "PARTIAL_OR_UNKNOWN_OUTCOME"
            and json.loads(origin[2]).get("failedStep") == "slab",
            "ORIGINAL_PARTIAL_SCENE_NOT_PROVEN")
    require(len(rows) == 5
            and [r[0] for r in rows] == list(PREFIX_IDS)
            and [r[1] for r in rows] == ["PASS"] * 4 + ["CREATED_UNVERIFIED"]
            and [r[2].lower() for r in rows]
               == [g.lower() for g in (*WALL_GUIDS, SLAB_GUID)],
            "EXACT_ORIGINAL_5_GUID_JOURNAL_MISMATCH")
    require(suffix is None, "CONTINUATION_ALREADY_RESERVED_DO_NOT_REPLAY")
    found = native_ids(api)
    required = {g.lower() for g in (*WALL_GUIDS, SLAB_GUID)}
    require(len(found) == 25 and required <= set(found), "NATIVE_25_GUID_SNAPSHOT_DRIFT")
    steps = {s["id"]: s for s in preview["graph"]["operations"]}
    prefix = {}
    for sid, guid in zip(WALL_IDS, WALL_GUIDS):
        row = RUN.requested_details(api, guid)
        kind = RUN.verify_readback("CreateWalls", steps[sid]["params"], row,
                                   expected_floor=0)
        prefix[sid] = {"guid": guid, "kind": kind, "floorIndex": 0}
    slab = RUN.requested_details(api, SLAB_GUID)
    require(slab.get("type") == "Slab" and slab.get("floorIndex") == 0,
            "SLAB_NATIVE_TYPE_OR_STORY_CHANGED")
    details = slab["details"]
    RUN.verify_readback("CreateSlabs", steps["slab"]["params"], slab,
                        expected_floor=0, allow_slab_thickness_mismatch=True)
    south_mat = RUN.requested_details(api, WALL_GUIDS[0])["details"].get("buildingMaterialId")
    require(isinstance(south_mat, dict)
            and RUN._GUID.fullmatch(str(south_mat.get("guid", ""))),
            "SOUTH_WALL_BUILDING_MATERIAL_NOT_AVAILABLE")
    material_guid = south_mat["guid"]
    attributes = api("GetAttributesByType", {"attributeType": "BuildingMaterial"}).get("attributes")
    require(isinstance(attributes, list), "BUILDING_MATERIALS_NOT_AVAILABLE")
    named = [a["name"] for a in attributes
             if a.get("attributeId", {}).get("guid", "").lower() == material_guid.lower()]
    require(len(named) == 1, "WALL_MATERIAL_NOT_UNIQUE_IN_NATIVE_CATALOG")
    # The existing valid BuildingMaterial from the test wall is reused,
    # not a newly invented or absent material.
    request = {
        "schema": "APA_FUNCTIONAL_HOUSE_EXACT_RECOVERY_V1",
        "sourcePlnSHA": PLN_SHA,
        "originalScene": ORIGIN, "originalPlanHash": plan_hash,
        "target": binding, "schemaSHA": preview["schemaSha256"],
        "reused": prefix, "slabGuid": SLAB_GUID,
        "oldSlab": {"level": details.get("level"),
                    "thickness": details.get("thickness"),
                    "structureType": details.get("structureType"),
                    "polygon": details.get("polygonOutline")},
        "newSlab": {"thickness": .2, "structureType": "Basic",
                    "materialGuid": material_guid},
        "before": found,
        "nextScene": SUFFIX,
        "remaining": preview["executionOrder"][5:],
    }
    token = RUN.digest(request)
    return dict(api=api, writer=writer, binding=binding, preview=preview,
                steps=steps, prefix=prefix, slab=slab, material=material_guid,
                material_name=named[0], before=found,
                repair=repair, request=request, token=token)


def check_repair(ctx):
    repair = ctx["repair"]
    if repair is None:
        d = ctx["slab"]["details"]
        require(d.get("structureType") == "Composite"
                and RUN.close(d.get("thickness"), .3)
                and RUN.close(d.get("level"), 0.),
                "EXACT_300MM_COMPOSITE_INCIDENT_NO_LONGER_PRESENT")
        return "NOT_ATTEMPTED"
    token, state, intent, result = repair
    require(state == "READBACK_PASS"
            and token == RUN.digest(json.loads(intent))
            and json.loads(intent).get("sourceToken") == ctx["token"],
            "REPAIR_JOURNAL_NOT_VERIFIED_OR_DIFFERENT")
    RUN.verify_readback("CreateSlabs", ctx["steps"]["slab"]["params"],
                        ctx["slab"], expected_floor=0,
                        expected_slab_material_guid=ctx["material"])
    require(json.loads(result).get("status") == "SLAB_REPAIR_VERIFIED_UNSAVED",
            "REPAIR_RESULT_INCOMPLETE")
    return "READBACK_PASS"


def repair_once(ctx):
    require(ctx["repair"] is None, "REPAIR_ALREADY_RESERVED_NEVER_RETRY")
    require(check_repair(ctx) == "NOT_ATTEMPTED", "SLAB_NOT_ELIGIBLE_FOR_REPAIR")
    api = ctx["api"]
    params = {"slabsWithDetails": [{
        "elementId": {"guid": SLAB_GUID},
        "structureType": "Basic", "thickness": .2,
        "buildingMaterialId": {"guid": ctx["material"]},
    }]}
    intent = {"sourceToken": ctx["token"], "nativeCommand": "ModifySlabs",
              "nativeParameters": params, "target": ctx["binding"],
              "before": ctx["before"], "slabGuid": SLAB_GUID}
    token = RUN.digest(intent)
    with closing(sqlite3.connect(LEDGER)) as db:
        db.execute("PRAGMA synchronous=FULL")
        db.execute("CREATE TABLE IF NOT EXISTS " + REPAIR_TABLE + " ("
                   "scene_id TEXT PRIMARY KEY, token TEXT NOT NULL, state TEXT NOT NULL,"
                   "intent_json TEXT NOT NULL, result_json TEXT NOT NULL)")
        db.commit()
        db.execute("BEGIN IMMEDIATE")
        require(not db.execute("SELECT 1 FROM " + REPAIR_TABLE
                               + " WHERE scene_id=?", (ORIGIN,)).fetchone(),
                "REPAIR_ALREADY_RESERVED")
        require(ctx["writer"].guarded_binding() == ctx["binding"]
                and native_ids(api) == ctx["before"], "REPAIR_PREWRITE_DRIFT")
        db.execute("INSERT INTO " + REPAIR_TABLE + " VALUES (?,?,?,?,?)",
                   (ORIGIN, token, "ATTEMPTED", RUN.canonical(intent), "{}"))
        db.commit()  # Durable intent BEFORE exactly one native mutation.
        try:
            require(ctx["writer"].guarded_binding() == ctx["binding"],
                    "REPAIR_PROJECT_SWITCHED")
            raw = api("ModifySlabs", params)
            require(raw.get("executionResults") == [{"success": True}],
                    "SLAB_NATIVE_MODIFY_NOT_CONFIRMED")
            row = RUN.requested_details(api, SLAB_GUID)
            RUN.verify_readback("CreateSlabs", ctx["steps"]["slab"]["params"],
                                row, expected_floor=0,
                                expected_slab_material_guid=ctx["material"])
            require(native_ids(api) == ctx["before"]
                    and ctx["writer"].guarded_binding() == ctx["binding"]
                    and sha(PLN) == PLN_SHA, "SLAB_REPAIR_POSTWRITE_DRIFT")
            result = {"status": "SLAB_REPAIR_VERIFIED_UNSAVED",
                      "slabGuid": SLAB_GUID, "modifyCalls": 1,
                      "createCalls": 0, "plnSaved": False}
            db.execute("UPDATE " + REPAIR_TABLE
                       + " SET state=?,result_json=? WHERE scene_id=?",
                       ("READBACK_PASS", RUN.canonical(result), ORIGIN))
            db.commit()
            return result
        except Exception as exc:
            result = {"status": "REPAIR_OUTCOME_UNKNOWN_NO_RETRY",
                      "reason": type(exc).__name__ + ": " + str(exc)}
            db.execute("UPDATE " + REPAIR_TABLE
                       + " SET state=?,result_json=? WHERE scene_id=?",
                       ("UNKNOWN_OUTCOME", RUN.canonical(result), ORIGIN))
            db.commit()
            return result


def continue_once(ctx):
    require(check_repair(ctx) == "READBACK_PASS", "REPAIRED_SLAB_NOT_VERIFIED")
    api, writer = ctx["api"], ctx["writer"]
    require(writer.guarded_binding() == ctx["binding"]
            and native_ids(api) == ctx["before"]
            and sha(PLN) == PLN_SHA, "CONTINUATION_BOUNDARY_DRIFT")
    preview = ctx["preview"]
    seeded = {**ctx["prefix"],
              "slab": {"guid": SLAB_GUID, "kind": "Slab", "floorIndex": 0}}
    remaining = preview["executionOrder"][5:]
    ticket = {
        **preview, "status": "READY_FOR_EXPLICIT_TEST_RUN",
        "sourcePlanHash": RUN.digest({
            "recovery": ctx["token"],
            "repair": json.loads(ctx["repair"][2]),
            "suffix": SUFFIX, "remaining": remaining,
            "inventory": ctx["before"]}),
        "binding": ctx["binding"], "slabBasicMaterialGuid": ctx["material"],
    }

    def verify_all(plan, created):
        require(set(created) == set(preview["executionOrder"]) | {"__plan__"},
                "FINAL_GRAPH_NOT_12_ELEMENTS")
        new_guids = [created[sid]["guid"].lower() for sid in remaining]
        require(len(new_guids) == 7 and len(set(new_guids)) == 7
                and not set(new_guids) & set(ctx["before"])
                and native_ids(api) == sorted(ctx["before"] + new_guids),
                "FINAL_INVENTORY_NOT_BASE25_PLUS7")
        for sid in preview["executionOrder"]:
            step = ctx["steps"][sid]
            params = RUN.resolve_params(step, created)
            parent = (RUN.check_previous_wall(api, step, created)
                      if step["command"] in ("CreateDoors", "CreateWindows")
                      else None)
            RUN.verify_readback(step["command"], params,
                                RUN.requested_details(api, created[sid]["guid"]),
                                parent, expected_floor=0,
                                expected_slab_material_guid=(
                                    ctx["material"] if sid == "slab" else None))
        require(writer.guarded_binding() == ctx["binding"]
                and sha(PLN) == PLN_SHA, "FINAL_TARGET_OR_SAVED_PLN_CHANGED")

    return writer._execute_verified_plan(
        ticket, SUFFIX, ticket["sourcePlanHash"], seeded_created=seeded,
        approval_source="user-authorized-isolated-functional-house-continuation",
        on_before_complete=verify_all)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true",
                        help="one-time single-slab repair, followed by max 7 remaining creates")
    parser.add_argument("--token", help="exact token from current read-only preflight")
    args = parser.parse_args()
    try:
        start = time.perf_counter()
        ctx = context()
        state = check_repair(ctx)
        if not args.execute:
            result = {
                "status": "READY_FOR_EXACT_RECOVERY" if state == "NOT_ATTEMPTED"
                          else "REPAIR_ALREADY_VERIFIED_INSPECT_ONLY",
                "token": ctx["token"], "target": str(PLN),
                "port": PORT, "firstFourWallGuids": list(WALL_GUIDS),
                "slabGuid": SLAB_GUID,
                "slabExistingThickness": ctx["slab"]["details"]["thickness"],
                "materialReuse": ctx["material_name"],
                "materialGuid": ctx["material"],
                "repairState": state, "remainingCreates": 7,
                "nativeWrites": 0, "plnWrites": 0,
            }
        else:
            require(args.token == ctx["token"], "EXECUTION_TOKEN_DRIFT")
            # Never skip a previously attempted incomplete repair.
            if state == "NOT_ATTEMPTED":
                repaired = repair_once(ctx)
                if repaired["status"] != "SLAB_REPAIR_VERIFIED_UNSAVED":
                    raise RuntimeError("REPAIR_STOPPED: " + RUN.canonical(repaired))
                ctx = context()  # fresh independent native reconciliation
            require(check_repair(ctx) == "READBACK_PASS",
                    "REPAIR_READBACK_NOT_PASS")
            result = continue_once(ctx)
            result = {
                "status": result["status"],
                "createdCount": result.get("createdCount"),
                "newCreatedCount": result.get("newCreatedCount"),
                "reusedCount": result.get("reusedCount"),
                "failedStep": result.get("failedStep"),
                "reason": result.get("reason"),
                "plnSaved": result.get("plnSaved"),
                "automaticRetry": False,
                "slabGuid": SLAB_GUID, "port": PORT,
            }
        result["durationSeconds"] = round(time.perf_counter() - start, 3)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["status"] in ("READY_FOR_EXACT_RECOVERY",
                                         "REPAIR_ALREADY_VERIFIED_INSPECT_ONLY",
                                         "COMPLETE_UNSAVED") else 2
    except Exception as exc:
        print(json.dumps({"status": "BLOCKED_OR_UNKNOWN_NO_RETRY",
                          "reason": type(exc).__name__ + ": " + str(exc),
                          "automaticRetry": False, "port": PORT},
                         ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
