"""Strictly READ-ONLY fourth-suffix timeout investigation.

Always read immutable prior evidence and SQLite journal in mode=ro BEFORE
attempting optional native reads. --journal-only never contacts Archicad.
--with-native performs only allowlisted native GET calls; no Save/Create/Modify.
A missing or ATTEMPTED journal GUID NEVER licenses a replay.
"""
from __future__ import annotations

import argparse
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import sys

import archicad_scene_run as RUN
import repair_apa_partial_slab as REPAIR
import continue_apa_partial_scene as SECOND
import continue_apa_after_story_z as THIRD
import repair_apa_suffix3_slab as SLAB2
import continue_apa_after_s2_slab as FOURTH

SAFE_READ_COMMANDS = frozenset({
    "GetProjectInfo", "GetStories", "GetAddOnVersion",
    "GetAllElements", "GetDetailsOfElements",
})


def read_journal():
    SECOND.verify_evidence_manifest(REPAIR.EVIDENCE)
    historical, plan, initial20, journal = REPAIR.read_evidence(REPAIR.EVIDENCE)
    if len(plan["executionOrder"]) != 25 or len(initial20) != 20:
        raise ValueError("NOT_THE_HISTORICAL_25_STEP_PLAN")
    known_steps = [op["id"] for op in plan["graph"]["operations"]]
    if (len(set(known_steps)) != 25 or set(plan["executionOrder"]) != set(known_steps)):
        raise ValueError("INVALID_ORIGINAL_STEP_SET")
    read_only_uri = journal.resolve().as_uri() + "?mode=ro"
    with closing(sqlite3.connect(read_only_uri, uri=True)) as db:
        db.execute("PRAGMA query_only=ON")
        prior = []
        for sid in (historical["sceneId"], SECOND.SUFFIX_ID, THIRD.THIRD_SCENE_ID):
            row = db.execute(
                "SELECT scene_id,state FROM scenes WHERE scene_id=?", (sid,)).fetchone()
            if not row or row[1] != "PARTIAL_OR_UNKNOWN_OUTCOME":
                raise ValueError("PREVIOUS_SCENE_STATUS_CHANGED: " + sid)
            records = db.execute(
                "SELECT step_id,state,guid FROM steps WHERE scene_id=? ORDER BY rowid",
                (sid,)).fetchall()
            prior.append(records)
        r1 = db.execute("SELECT state,slab_guid FROM apa_partial_slab_repairs "
                        "WHERE scene_id=?", (historical["sceneId"],)).fetchone()
        r2 = db.execute("SELECT state,guid FROM apa_suffix3_slab_repairs "
                        "WHERE scene_id=?", (THIRD.THIRD_SCENE_ID,)).fetchone()
        fourth = db.execute(
            "SELECT state,plan_hash,result FROM scenes WHERE scene_id=?",
            (FOURTH.FOURTH_SCENE_ID,)).fetchone()
        suffix = db.execute(
            "SELECT step_id,state,guid,output FROM steps WHERE scene_id=? ORDER BY rowid",
            (FOURTH.FOURTH_SCENE_ID,)).fetchall()
    if (len(prior[0]) != 5 or len(prior[1]) != 3 or len(prior[2]) != 4
            or [q[0] for batch in prior for q in batch] != plan["executionOrder"][:12]):
        raise ValueError("FIRST_12_JOURNAL_PREFIX_CHANGED")
    expected_states = ["PASS"]*4+["CREATED_UNVERIFIED"]+["PASS"]*2+[
        "CREATED_UNVERIFIED"]+["PASS"]*3+["CREATED_UNVERIFIED"]
    if [q[1] for batch in prior for q in batch] != expected_states:
        raise ValueError("HISTORICAL_JOURNAL_STATES_CHANGED")
    if (r1 != ("READBACK_PASS", REPAIR.SLAB_GUID)
            or r2 != ("READBACK_PASS", SLAB2.TARGET_GUID)):
        raise ValueError("VERIFIED_SLAB_REPAIR_ROWS_CHANGED")
    first_guids = [str(x).lower() for x in initial20]
    previous_guids = [g.lower() for batch in prior for _, _, g in batch
                      if isinstance(g, str)]
    if (len(previous_guids) != 12 or len(set(previous_guids)) != 12
            or len(set(first_guids)) != 20
            or set(previous_guids) & set(first_guids)):
        raise ValueError("ORIGINAL_32_GUIDS_NOT_UNIQUE")
    prior32 = sorted([*first_guids, *previous_guids])
    if fourth is None and suffix:
        raise ValueError("FOURTH_SCENE_ROWS_WITHOUT_SCENE_RESERVATION")
    expected_order = plan["executionOrder"][12:]
    suffix_ids = [sid for sid, _, _, _ in suffix]
    if (suffix_ids != expected_order[:len(suffix_ids)]
            or len(suffix) > 13 or len(set(suffix_ids)) != len(suffix_ids)):
        raise ValueError("FOURTH_SCENE_NOT_A_PREFIX_OF_HISTORICAL_REMAINDER")
    journaled_new = {g.lower() for _, _, g, _ in suffix if isinstance(g, str)}
    report = {
        "status": "READ_ONLY_FOURTH_SUFFIX_JOURNAL",
        "sceneId": FOURTH.FOURTH_SCENE_ID,
        "journalPath": str(journal),
        "fourthSceneReserved": fourth is not None,
        "fourthSceneState": fourth[0] if fourth else None,
        "fourthScenePlanHash": fourth[1] if fourth else None,
        "fourthSceneLastResult": (
            json.loads(fourth[2]) if fourth is not None else None),
        "previousBaselineGuids": prior32,
        "previousBaselineCount": len(prior32),
        "plannedRemainingStepIds": expected_order,
        "fourthJournal": [
            {"step": sid, "state": state, "guid": guid}
            for sid, state, guid, _ in suffix
        ],
        "journaledNewGuids": sorted(journaled_new),
        "journaledNewCount": len(journaled_new),
        "ambiguousWithoutGuid": [
            sid for sid, state, guid, _ in suffix
            if state in ("ATTEMPTED", "CREATED_UNVERIFIED",
                         "BASIC_MODIFY_ATTEMPTED") and not guid
        ],
        "readOnly": True,
        "nativeWriteCalls": 0,
        "automaticReplayAllowed": False,
    }
    return report, plan


def read_native(api, report, plan):
    def get(cmd, params):
        if cmd not in SAFE_READ_COMMANDS:
            raise ValueError("NON_READ_ONLY_COMMAND_BLOCKED: " + cmd)
        return api(cmd, params)
    # No need for an active story match: a user may change the UI after timeout.
    info = get("GetProjectInfo", {})
    if (info.get("projectName") != "APA_Test_House_01"
            or info.get("projectPath") != RUN.APPROVED_SCRATCH_PATH
            or info.get("isUntitled") is not False
            or info.get("isTeamwork") is not False):
        raise ValueError("NOT_THE_APPROVED_SCRATCH_PROJECT")
    version = get("GetAddOnVersion", {}).get("version")
    if version != RUN.EXPECTED_TAPIR:
        raise ValueError("WRONG_NATIVE_ADDON_VERSION")
    stories = get("GetStories", {})
    report["activeStoryIndex"] = stories.get("actStory")
    for expected in plan["storyBindings"]:
        matching = [row for row in stories.get("stories", [])
                    if row.get("index") == expected["nativeIndex"]]
        if (len(matching) != 1 or matching[0].get("floorId") != expected["floorId"]
                or not RUN.close(matching[0].get("level"), expected["level"])):
            raise ValueError("PINNED_STORY_MAPPING_CHANGED")
    native = [row["elementId"]["guid"].lower()
              for row in get("GetAllElements", {}).get("elements", [])]
    if (len(set(native)) != len(native)
            or any(not RUN._GUID.fullmatch(g) for g in native)):
        raise ValueError("INVALID_NATIVE_INVENTORY")
    before = set(report["previousBaselineGuids"])
    actual = set(native)
    recorded = set(report["journaledNewGuids"])
    missing = sorted(before - actual)
    fresh = sorted(actual - before)
    report["native"] = {
        "status": "READ_ONLY_NATIVE_INVENTORY",
        "total": len(native),
        "presentOriginal32": len(before & actual),
        "missingOriginal32": missing,
        "newGuids": fresh,
        "newGuidCount": len(fresh),
        "newGuidsNotInFourthJournal": sorted(set(fresh) - recorded),
        "fourthJournalGuidsMissingFromModel": sorted(recorded - actual),
        "modelMatchesRecordedGuids": (
            not missing and set(fresh) == recorded),
    }
    return report


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--port", type=int, default=19726)
    p.add_argument("--journal-only", action="store_true",
                   help="Zero network/native calls; SQLite mode=ro only (default)")
    p.add_argument("--with-native", action="store_true",
                   help="Also GET exact test PLN identity, stories and live GUID inventory")
    args = p.parse_args(argv)
    if args.journal_only and args.with_native:
        p.error("Choose either --journal-only or --with-native, not both")
    try:
        report, plan = read_journal()
    except Exception as exc:
        print(json.dumps({
            "status": "BLOCKED_READ_ONLY_JOURNAL",
            "reason": type(exc).__name__ + ": " + str(exc),
            "nativeWriteCalls": 0,
            "automaticReplayAllowed": False,
        }, ensure_ascii=False, indent=2))
        return 2
    if args.with_native:
        try:
            RUN.bind_approved_scratch_pln(args.port)
            read_native(lambda cmd, prm: RUN.tapir(args.port, cmd, prm), report, plan)
        except Exception as exc:
            report["native"] = {
                "status": "UNAVAILABLE_OR_BLOCKED",
                "reason": type(exc).__name__ + ": " + str(exc),
                "outcomeUnknown": True,
            }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
