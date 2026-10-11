"""Read-only exact failure audit for 2026-10-11 APA second-storey south wall.

No native Create/Modify/Delete, PLN save, journal update, or retry. Prints the
native actual-vs-requested values for the recorded failed GUID, plus the exact
suffix ledger and inventory delta. Preserves evidence of ambiguous writes.
"""
from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import sys

import archicad_scene_run as RUN
import repair_apa_partial_slab as REPAIR
import continue_apa_partial_scene as CONT

FAILED_STEP = "s2-wall-south"
WALL_FIELDS = (
    ("height", "height"), ("thickness", "begThickness"),
    ("thickness", "endThickness"), ("offset", "offset"),
    ("zCoordinate", "zCoordinate"), ("arcAngle", "arcAngle"),
)
BASE = ("begCoordinate", "endCoordinate")
SAFE_READS = frozenset({
    "GetProjectInfo", "GetStories", "GetAddOnVersion",
    "GetAllElements", "GetDetailsOfElements",
})


def collect(api):
    scene, plan, before, journal = REPAIR.read_evidence(REPAIR.EVIDENCE)
    stories = plan["storyBindings"]
    binding = RUN.guarded_project(api, stories[0])
    CONT.verify_live_story_map(api, stories)
    operations = {step["id"]: step for step in plan["graph"]["operations"]}
    order = plan["executionOrder"]
    if FAILED_STEP not in operations or FAILED_STEP not in order:
        raise ValueError("FAILED_WALL_NOT_IN_ORIGINAL_PLAN")
    # Do not run continuation preflight: 25-GUID baseline no longer applies.
    uri = journal.resolve().as_uri() + "?mode=ro"
    with sqlite3.connect(uri, uri=True) as db:
        scene_row = db.execute(
            "SELECT state,plan_hash,result FROM scenes WHERE scene_id=?",
            (CONT.SUFFIX_ID,)).fetchone()
        step_rows = db.execute(
            "SELECT step_id,state,guid,output FROM steps WHERE scene_id=? ORDER BY rowid",
            (CONT.SUFFIX_ID,)).fetchall()
        orig_rows = db.execute(
            "SELECT step_id,state,guid FROM steps WHERE scene_id=?",
            (scene["sceneId"],)).fetchall()
        repair_row = db.execute(
            "SELECT state,slab_guid FROM apa_partial_slab_repairs WHERE scene_id=?",
            (scene["sceneId"],)).fetchone()
    if not scene_row:
        raise ValueError("SUFFIX_SCENE_NOT_IN_LEDGER")
    if scene_row[0] != "PARTIAL_OR_UNKNOWN_OUTCOME":
        raise ValueError("SUFFIX_SCENE_STATE_NOT_PARTIAL")
    summary = json.loads(scene_row[2])
    if summary.get("failedStep") != FAILED_STEP:
        raise ValueError("SUFFIX_FAILURE_STEP_CHANGED")
    if len(step_rows) != len({row[0] for row in step_rows}):
        raise ValueError("DUPLICATE_SUFFIX_STEP_ROWS")
    if not step_rows or step_rows[-1][0] != FAILED_STEP:
        raise ValueError("FAILED_STEP_NOT_LAST_LOGGED_OPERATION")
    if step_rows[-1][1] not in (
            "CREATED_UNVERIFIED", "ATTEMPTED", "BASIC_MODIFY_ATTEMPTED"):
        raise ValueError("FAILED_STEP_STATE_UNEXPECTED")
    rows = [{"stepId": sid, "state": state, "guid": guid}
            for sid, state, guid, _ in step_rows]
    prefix_ids = {guid.lower() for _, state, guid in orig_rows if guid}
    if len(prefix_ids) != 5 or repair_row != ("READBACK_PASS", REPAIR.SLAB_GUID):
        raise ValueError("ORIGINAL_FIVE_OR_SLAB_REPAIR_LEDGER_MISMATCH")
    native_ids = REPAIR.all_guids(api)
    prior = {str(x).lower() for x in before}
    new = set(native_ids) - prior - prefix_ids
    vanished = (prior | prefix_ids) - set(native_ids)
    logged = {guid.lower() for _, _, guid, _ in step_rows if guid}
    unrecorded = sorted(new - logged)
    output = {
        "status": "READ_ONLY_SUFFIX_DIAGNOSIS",
        "project": binding,
        "suffixScene": CONT.SUFFIX_ID,
        "suffixState": scene_row[0],
        "failure": summary.get("reason"),
        "failedStep": FAILED_STEP,
        "journal": str(journal),
        "nativeInventory": {
            "original20": len(prior),
            "repairedOriginal5": len(prefix_ids),
            "totalNow": len(native_ids),
            "suffixNewGuids": sorted(new),
            "suffixGuidCount": len(new),
            "missingFromOriginal25": sorted(vanished),
            "nativeGuidsAbsentFromSuffixJournal": unrecorded,
        },
        "suffixJournal": rows,
        "plnSavedByScript": False,
        "nativeWriteCalls": 0,
    }
    failed = step_rows[-1]
    if failed[2]:
        expected = operations[FAILED_STEP]["params"]["wallsData"][0]
        real = RUN.requested_details(api, failed[2])
        details = real.get("details")
        if not isinstance(details, dict):
            raise ValueError("FAILED_WALL_NATIVE_DETAILS_MISSING")
        differences = {}
        for requested, actual in WALL_FIELDS:
            want, got = expected.get(requested), details.get(actual)
            differences[actual] = {
                "requested": want, "native": got, "matches": RUN.close(want, got),
            }
        for key in BASE:
            v1, v2 = expected.get(key, {}), details.get(key, {})
            differences[key] = {
                axis: {
                    "requested": v1.get(axis), "native": v2.get(axis),
                    "matches": RUN.close(v1.get(axis), v2.get(axis)),
                } for axis in ("x", "y")
            }
        output["failedWall"] = {
            "guid": failed[2],
            "journalState": failed[1],
            "plannedFloorIndex": expected["floorIndex"],
            "nativeFloorIndex": real.get("floorIndex"),
            "nativeType": real.get("type"),
            "plannedReferenceStructure": expected.get("structureType"),
            "nativeStructureType": details.get("structureType"),
            "fieldComparison": differences,
            "nativeDetail": details,
            "originOperationIntent": json.loads(failed[3]).get("intent", {}),
        }
    else:
        output["failedWall"] = {
            "guid": None, "journalState": failed[1],
            "note": "No returned GUID. No retry is safe without native spatial reconciliation",
        }
    if RUN.guarded_project(api, stories[0]) != binding or REPAIR.all_guids(api) != native_ids:
        raise ValueError("PROJECT_OR_INVENTORY_CHANGED_DURING_DIAGNOSIS")
    return output


def main(argv=None):
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--port", type=int, default=19726)
    args = p.parse_args(argv)
    try:
        RUN.bind_approved_scratch_pln(args.port)
        def read_only_api(command, params):
            if command not in SAFE_READS:
                raise RuntimeError("DIAGNOSTIC_REFUSED_NON_READ_COMMAND: " + command)
            return RUN.tapir(args.port, command, params)
        data = collect(read_only_api)
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"status": "BLOCKED_READ_ONLY",
                          "reason": type(exc).__name__ + ": " + str(exc),
                          "nativeWriteCalls": 0},
                         ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    sys.exit(main())
