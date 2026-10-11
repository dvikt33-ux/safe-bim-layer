"""STRICT READ ONLY: diagnose the third APA scratch scene stopped at s2-slab.

Inspects the original, first suffix and third suffix journals without writing;
checks exact current Archicad 29 / Tapir 1.5.10 test PLN, GetStories, complete
GUID inventory and actual Slab details. No Create/Modify/Delete/Save or retries.
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

FAILED_STEP = "s2-slab"
READS = frozenset({"GetProjectInfo", "GetStories", "GetAddOnVersion",
                   "GetAllElements", "GetDetailsOfElements"})


def journal_rows(db, scene_id):
    scene = db.execute(
        "SELECT plan_hash,state,result FROM scenes WHERE scene_id=?",
        (scene_id,)).fetchone()
    rows = db.execute(
        "SELECT step_id,state,guid,output FROM steps WHERE scene_id=? ORDER BY rowid",
        (scene_id,)).fetchall()
    return scene, rows


def collect(api):
    historical, plan, baseline, journal = REPAIR.read_evidence(REPAIR.EVIDENCE)
    stories = plan["storyBindings"]
    binding = RUN.guarded_project(api, stories[0])
    CONT.verify_live_story_map(api, stories)
    if len(baseline) != 20 or len(plan["graph"]["operations"]) != 25:
        raise ValueError("HISTORICAL_PLAN_OR_BASELINE_CHANGED")
    with closing(sqlite3.connect(journal.resolve().as_uri() + "?mode=ro", uri=True)) as db:
        old, original_rows = journal_rows(db, historical["sceneId"])
        prev, previous_rows = journal_rows(db, CONT.SUFFIX_ID)
        third, third_rows = journal_rows(db, THIRD.THIRD_SCENE_ID)
        repair = db.execute(
            "SELECT state,slab_guid FROM apa_partial_slab_repairs WHERE scene_id=?",
            (historical["sceneId"],)).fetchone()
    if (not old or old[:2] != (historical["planHash"], "PARTIAL_OR_UNKNOWN_OUTCOME")
            or repair != ("READBACK_PASS", REPAIR.SLAB_GUID)):
        raise ValueError("ORIGINAL_SCENE_OR_REPAIR_STATE_CHANGED")
    if (len(original_rows) != 5 or len(previous_rows) != 3
            or len(third_rows) == 0):
        raise ValueError("HISTORICAL_SCENE_ROWS_CHANGED")
    if [r[0] for r in previous_rows] != [
            "s1-partition-1", "s1-partition-2", "s2-wall-south"]:
        raise ValueError("PREVIOUS_SUFFIX_NOT_THE_VERIFIED_THREE")
    if (not prev or prev[1] != "PARTIAL_OR_UNKNOWN_OUTCOME"
            or not third or third[1] != "PARTIAL_OR_UNKNOWN_OUTCOME"):
        raise ValueError("SUFFIX_STATES_NOT_PARTIAL")
    summary = json.loads(third[2])
    if (summary.get("failedStep") != FAILED_STEP
            or not isinstance(summary.get("reason"), str)):
        raise ValueError("THIRD_SUFFIX_NOT_FAILED_ON_S2_SLAB")
    planned_ids = plan["executionOrder"][8:]
    logged_ids = [sid for sid, _, _, _ in third_rows]
    if (logged_ids != planned_ids[:len(logged_ids)]
            or logged_ids[-1] != FAILED_STEP
            or len(set(logged_ids)) != len(logged_ids)):
        raise ValueError("THIRD_SUFFIX_NOT_ORDERED_PREFIX")
    if third_rows[-1][1] not in (
            "ATTEMPTED", "CREATED_UNVERIFIED", "BASIC_MODIFY_ATTEMPTED"):
        raise ValueError("FAILED_SLAB_JOURNAL_STATE_NOT_RECONCILABLE")
    preserved = sorted(set(str(g).lower() for g in baseline)
                       | {r[2].lower() for r in original_rows + previous_rows
                          if isinstance(r[2], str)})
    if len(preserved) != 28:
        raise ValueError("FIRST_28_GUIDS_NOT_UNIQUE")
    present = REPAIR.all_guids(api)
    lost = sorted(set(preserved) - set(present))
    after = sorted(set(present) - set(preserved))
    registered = {r[2].lower() for r in third_rows if isinstance(r[2], str)}
    missing_logged = sorted(registered - set(present))
    unlogged = sorted(set(after) - registered)
    report = {
        "status": "READ_ONLY_THIRD_SUFFIX_SLAB_DIAGNOSIS",
        "binding": binding,
        "sceneId": THIRD.THIRD_SCENE_ID,
        "sceneStatus": third[1],
        "failedStep": FAILED_STEP,
        "failure": summary["reason"],
        "journalPath": str(journal),
        "inventory": {
            "baselinePreserved": len(preserved),
            "nativeTotal": len(present),
            "newElementsAfter28": len(after),
            "newGuidsAfter28": after,
            "missingPreviouslyVerifiedGuids": lost,
            "journaledGuidsAbsentFromModel": missing_logged,
            "nativeGuidsNotInThirdJournal": unlogged,
        },
        "thirdSceneJournal": [
            {"step": sid, "state": state, "guid": guid}
            for sid, state, guid, _ in third_rows
        ],
        "nativeWriteCalls": 0,
        "plnSavedByDiagnostic": False,
        "rerunPermitted": False,
    }
    failed = third_rows[-1]
    if failed[2]:
        if failed[2].lower() not in present:
            report["failedSlab"] = {
                "guid": failed[2], "journalState": failed[1],
                "status": "GUID_NOT_IN_CURRENT_MODEL"}
        else:
            row = RUN.requested_details(api, failed[2])
            details = row.get("details")
            if not isinstance(details, dict):
                raise ValueError("NATIVE_SLAB_DETAILS_MISSING")
            operations = {op["id"]: op for op in plan["graph"]["operations"]}
            want = operations[FAILED_STEP]["params"]["slabsData"][0]
            floor_level = RUN.story_level_for_floor(stories, want["floorIndex"])
            expected_guid = None
            material = details.get("buildingMaterialId")
            if isinstance(material, dict):
                expected_guid = material.get("guid")
            actual_polys = details.get("polygonOutline")
            polygon_ok = (RUN.compare_polygon(
                want["polygonCoordinates"], actual_polys)
                if isinstance(actual_polys, list) else False)
            report["failedSlab"] = {
                "guid": failed[2], "journalState": failed[1],
                "nativeType": row.get("type"),
                "nativeStoryIndex": row.get("floorIndex"),
                "plannedStoryIndex": want["floorIndex"],
                "storyAbsoluteLevel": floor_level,
                "nativeStructureType": details.get("structureType"),
                "nativeMaterialGuid": expected_guid,
                "fieldComparison": {
                    "level": {
                        "requestedLocal": want["level"],
                        "requestedPlusStory": want["level"] + floor_level,
                        "native": details.get("level"),
                        "matchesLocal": RUN.close(want["level"], details.get("level")),
                        "matchesAbsolute": RUN.close(
                            want["level"] + floor_level, details.get("level")),
                    },
                    "zCoordinate": {
                        "native": details.get("zCoordinate"),
                        "expectedStoryPlusLocal": floor_level + want["level"],
                        "matchesAbsolute": RUN.close(
                            details.get("zCoordinate"), floor_level + want["level"]),
                    },
                    "thickness": {
                        "requested": want["thickness"],
                        "native": details.get("thickness"),
                        "matches": RUN.close(want["thickness"], details.get("thickness")),
                    },
                    "referencePlaneLocation": {
                        "requested": want.get("referencePlaneLocation"),
                        "native": details.get("referencePlaneLocation"),
                    },
                    "polygon": {"matches": polygon_ok},
                },
                "nativeDetails": details,
            }
    else:
        report["failedSlab"] = {
            "guid": None, "journalState": failed[1],
            "status": "NATIVE_CALL_OUTCOME_UNKNOWN_NO_GUID",
        }
    if RUN.guarded_project(api, stories[0]) != binding or REPAIR.all_guids(api) != present:
        raise ValueError("PROJECT_OR_INVENTORY_CHANGED_DURING_READ_ONLY_DIAGNOSIS")
    return report


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--port", type=int, default=19726)
    opts = p.parse_args(argv)
    try:
        RUN.bind_approved_scratch_pln(opts.port)
        def api(command, parameters):
            if command not in READS:
                raise ValueError("DIAGNOSIS_REFUSED_WRITE_OR_UNREVIEWED_READ")
            return RUN.tapir(opts.port, command, parameters)
        result = collect(api)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({
            "status": "BLOCKED_READ_ONLY",
            "reason": type(exc).__name__ + ": " + str(exc),
            "nativeWriteCalls": 0,
        }, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    sys.exit(main())
