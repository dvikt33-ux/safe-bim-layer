"""Read-only reconciliation of an interrupted APA SceneWriter trial.

Never replays a Create command, never alters PLN, never modifies SQLite ledger.
Reads pinned journal + evidence from the user's Windows scratch trial.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sqlite3
import sys

import archicad_scene_run as RUN


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True,
                        help="C:/LocalAI/APA_Trial_Evidence/<run-folder>")
    parser.add_argument("--port", type=int, default=19726)
    args = parser.parse_args(argv)
    RUN.bind_approved_scratch_pln(args.port)
    directory = args.evidence.resolve()
    result = json.loads((directory / "execute" / "result.json").read_text(encoding="utf-8"))
    plan = json.loads((directory / "execute" / "plan.json").read_text(encoding="utf-8"))
    original = json.loads((directory / "execute" / "inventory-before.json").read_text(encoding="utf-8"))
    failed_step = result.get("scene", {}).get("failedStep")
    scene_id = result.get("scene", {}).get("sceneId")
    if (result.get("status") != "PARTIAL_OR_UNKNOWN_OUTCOME"
            or not isinstance(scene_id, str) or not isinstance(failed_step, str)
            or failed_step != "s1-slab"):
        raise RuntimeError("NOT_THE_EXPECTED_PARTIAL_SLAB_SCENE")
    db_path = directory.parent / "persistent-ledger" / "scene-v1-attempts.sqlite3"
    if not db_path.is_file():
        raise RuntimeError("LEDGER_MISSING: STOP; no rerun")
    uri = db_path.resolve().as_uri() + "?mode=ro"
    with sqlite3.connect(uri, uri=True) as conn:
        record = conn.execute("SELECT state,plan_hash FROM scenes WHERE scene_id=?",
                              (scene_id,)).fetchone()
        steps = list(conn.execute(
            "SELECT step_id,state,guid FROM steps WHERE scene_id=? ORDER BY rowid",
            (scene_id,)))
    if not record or record[0] != "PARTIAL_OR_UNKNOWN_OUTCOME":
        raise RuntimeError("LEDGER_SCENE_STATE_UNEXPECTED")
    if record[1] != result["scene"]["planHash"]:
        raise RuntimeError("LEDGER_PLAN_HASH_MISMATCH")
    api = lambda command, params: RUN.tapir(args.port, command, params)
    story = plan["storyBindings"][0]
    binding = RUN.guarded_project(api, story)
    print("=== TARGET VERIFIED (READ ONLY) ===")
    print(json.dumps(binding, ensure_ascii=False))
    inventory = api("GetAllElements", {}).get("elements")
    if not isinstance(inventory, list):
        raise RuntimeError("INVENTORY_UNAVAILABLE")
    current = {e["elementId"]["guid"].lower() for e in inventory}
    before = {x.lower() for x in original}
    added = sorted(current - before)
    removed = sorted(before - current)
    print("=== INVENTORY DIFF ===")
    print(json.dumps({"before": len(before), "now": len(current),
                      "addedGuids": added, "removedGuids": removed}, indent=2))
    print("=== DURABLE JOURNAL ===")
    print(json.dumps([{"step": step, "state": state, "guid": guid}
                     for step, state, guid in steps], indent=2))
    if removed:
        print("STOP: INVENTORY_REMOVED_UNEXPECTEDLY")
        return 2
    failed = next((x for x in steps if x[0] == failed_step), None)
    if not failed or not failed[2]:
        print("STOP: SLAB_GUID_NOT_IN_LEDGER")
        return 2
    slab_guid = failed[2]
    if slab_guid.lower() not in current:
        print("STOP: SLAB_GUID_NOT_PRESENT_IN_LIVE_PROJECT")
        return 2
    if binding != RUN.guarded_project(api, story):
        raise RuntimeError("PROJECT_CHANGED_DURING_RECONCILIATION")
    slab_step = next(s for s in plan["graph"]["operations"] if s["id"] == failed_step)
    want = slab_step["params"]["slabsData"][0]
    row = RUN.requested_details(api, slab_guid)
    actual = row.get("details", {})
    if not isinstance(actual, dict):
        print("STOP: LIVE_SLAB_DETAILS_MISSING")
        return 2
    try:
        polygon_matches = RUN.compare_polygon(want["polygonCoordinates"],
                                              actual.get("polygonOutline"))
    except (ValueError, KeyError, TypeError, AttributeError) as exc:
        polygon_matches = "UNREADABLE: " + str(exc)
    comparison = {
        "type": row.get("type"),
        "storyIndex": row.get("floorIndex"),
        "thicknessEqual": RUN.close(want["thickness"], actual.get("thickness")),
        "levelEqual": RUN.close(want["level"], actual.get("level")),
        "polygonEqual": polygon_matches,
        "expected": want,
        "actualDetails": actual,
    }
    print("=== FAILED SLAB: EXPECTED vs NATIVE READBACK ===")
    print(json.dumps(comparison, ensure_ascii=False, indent=2))
    if binding != RUN.guarded_project(api, story):
        raise RuntimeError("PROJECT_CHANGED_DURING_RECONCILIATION")
    print("APA_DIAGNOSTIC_READ_ONLY_COMPLETE: no Create/Modify/Delete/Save calls")
    print("DO NOT RE-RUN ORIGINAL SCENE; preserve source PLN and journal")
    return 0


if __name__ == "__main__":
    sys.exit(main())
