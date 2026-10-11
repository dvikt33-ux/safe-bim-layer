"""STRICT READ ONLY — reconcile timed-out s2-partition-1 native GUID.

Never modifies the BIM or SQLite. Requires exactly one unjournaled new GUID,
exact fourth suffix original ATTEMPTED write intent and durable partial state,
exact disposable PLN identity, pinned stories, and full native Wall typed
geometry/readback at second storey (+3 m). No replay/repair authorization.
"""
from __future__ import annotations

import argparse
from contextlib import closing
import json
import sqlite3
import sys

import archicad_scene_run as RUN
import diagnose_apa_suffix4_timeout as TIMEOUT
import continue_apa_partial_scene as SECOND
import repair_apa_partial_slab as REPAIR
import continue_apa_after_s2_slab as FOURTH

FAILED_STEP = "s2-partition-1"
READ_ONLY = frozenset({
    "GetProjectInfo", "GetAddOnVersion", "GetStories",
    "GetAllElements", "GetDetailsOfElements",
})


def reconcile(api):
    report, plan = TIMEOUT.read_journal()
    scene = report["fourthSceneLastResult"]
    rows = report["fourthJournal"]
    if (not report["fourthSceneReserved"]
            or report["fourthSceneState"] != "PARTIAL_OR_UNKNOWN_OUTCOME"
            or not isinstance(scene, dict)
            or scene.get("failedStep") != FAILED_STEP
            or "TimeoutError" not in scene.get("reason", "")
            or len(rows) != 1 or rows[0]["step"] != FAILED_STEP
            or rows[0]["state"] != "ATTEMPTED" or rows[0]["guid"] is not None
            or report["journaledNewCount"] != 0):
        raise ValueError("NOT_EXACT_ONE_ATTEMPTED_S2_PARTITION_TIMEOUT")
    step = next((s for s in plan["graph"]["operations"]
                 if s.get("id") == FAILED_STEP), None)
    if step is None or step["command"] != "CreateWalls":
        raise ValueError("EXPECTED_S2_PARTITION_WALL_PLAN_MISSING")
    intended = step["params"]["wallsData"][0]
    if (intended["floorIndex"] != 1
            or RUN.story_level_for_floor(plan["storyBindings"], 1) != 3):
        raise ValueError("S2_PARTITION_PLAN_OR_STORY_LEVEL_CHANGED")
    journal = REPAIR.read_evidence(REPAIR.EVIDENCE)[3]
    with closing(sqlite3.connect(journal.resolve().as_uri()+"?mode=ro",uri=True)) as db:
        db.execute("PRAGMA query_only=ON")
        row = db.execute(
            "SELECT output FROM steps WHERE scene_id=? AND step_id=?",
            (FOURTH.FOURTH_SCENE_ID, FAILED_STEP)).fetchone()
    if not row:
        raise ValueError("DURABLE_UNACKNOWLEDGED_WRITE_INTENT_MISSING")
    recorded = json.loads(row[0])
    intent = recorded.get("intent")
    approval = recorded.get("localApproval")
    expected_intent = {
        "sceneId": FOURTH.FOURTH_SCENE_ID,
        "planHash": report["fourthScenePlanHash"],
        "stepId": FAILED_STEP, "command": "CreateWalls",
        "parameters": step["params"],
        "target": {
            "path": RUN.APPROVED_SCRATCH_PATH, "name": "APA_Test_House_01",
            "port": RUN.PORT, "tapirVersion": RUN.EXPECTED_TAPIR,
            "storyIndex": 0,
        }
    }
    if (intent != expected_intent or not isinstance(approval, dict)
            or approval.get("operationHash") != RUN.digest(expected_intent)
            or approval.get("permission") != "CreateWalls"
            or approval.get("scope") != RUN.APPROVED_SCRATCH_PATH):
        raise ValueError("RECORDED_NATIVE_INTENT_NOT_EXACT_APPROVED_OPERATION")
    def read(cmd, params):
        if cmd not in READ_ONLY:
            raise ValueError("READ_ONLY_BOUNDARY_REJECTED: "+cmd)
        return api(cmd, params)
    TIMEOUT.read_native(read, report, plan)
    live = report["native"]
    if (live["status"] != "READ_ONLY_NATIVE_INVENTORY"
            or live["presentOriginal32"] != 32 or live["missingOriginal32"]
            or live["newGuidCount"] != 1
            or len(live["newGuidsNotInFourthJournal"]) != 1):
        raise ValueError("NATIVE_NOT_EXACTLY_32_PLUS_ONE_UNJOURNALED")
    guid = live["newGuidsNotInFourthJournal"][0]
    actual = RUN.requested_details(read, guid)
    if (actual.get("type") != "Wall" or actual.get("floorIndex") != 1):
        raise ValueError("NEW_GUID_NOT_SECOND_STORY_WALL")
    kind = RUN.verify_readback(
        "CreateWalls", step["params"], actual,
        expected_floor=1,
        expected_story_level=RUN.story_level_for_floor(
            plan["storyBindings"], 1))
    if kind != "Wall":
        raise ValueError("UNEXPECTED_NEW_NATIVE_ELEMENT_TYPE")
    # Fresh final identity/inventory read makes a mid-audit change visible.
    check_info = read("GetProjectInfo", {})
    check_guids = read("GetAllElements", {}).get("elements")
    last = sorted(x["elementId"]["guid"].lower() for x in check_guids)
    if (check_info.get("projectPath") != RUN.APPROVED_SCRATCH_PATH
            or last != sorted([*report["previousBaselineGuids"], guid])):
        raise ValueError("NATIVE_IDENTITY_OR_INVENTORY_CHANGED_DURING_READBACK")
    return {
        "status": "READ_ONLY_ORPHAN_S2_PARTITION_VERIFIED",
        "sceneId": FOURTH.FOURTH_SCENE_ID,
        "operation": FAILED_STEP,
        "guid": guid,
        "journalState": rows[0]["state"],
        "nativeType": actual["type"],
        "nativeFloorIndex": actual["floorIndex"],
        "expectedAbsoluteZ": 3.0,
        "nativeAbsoluteZ": actual["details"].get("zCoordinate"),
        "plannedElementsVerified": 13,
        "totalModelElements": 33,
        "remainingPlannedCreates": 12,
        "journalRewritten": False,
        "modelWriteCalls": 0,
        "replayOfFourthSceneAllowed": False,
        "outcome": "RECONCILED_IN_NATIVE_NOT_IN_ORIGINAL_CREATE_LEDGER",
    }


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--port",type=int,default=19726)
    args=p.parse_args(argv)
    try:
        RUN.bind_approved_scratch_pln(args.port)
        def api(cmd,params):
            if cmd not in READ_ONLY:
                raise ValueError("FORBIDDEN_WRITE_COMMAND: "+cmd)
            return RUN.tapir(args.port,cmd,params)
        result=reconcile(api)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({
            "status":"BLOCKED_READ_ONLY_ORPHAN_RECONCILIATION",
            "reason":type(exc).__name__+": "+str(exc),
            "modelWriteCalls":0,
            "automaticReplayAllowed":False,
        },ensure_ascii=False,indent=2))
        return 2


if __name__=="__main__":
    sys.exit(main())
