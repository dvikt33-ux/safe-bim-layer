"""Remove ONLY rejected APA TRC-SAD 2D elements by provenance GUID.

No undo, no model reset, no project switch and no automatic Save.
The owner must first SAVE AS a protected backup and then SAVE AS a separate
working copy, preserving all unrelated prior unsaved changes.

The default invocation is read-only and prints a one-time confirmation hash.
--execute requires an unchanged matching preflight and explicit hash.
Partial/unknown prior attempts, journal mismatches, changed project,
mismatching native types/stories, and missing GUIDs fail closed.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import re
from pathlib import Path
import sys

from archicad_guarded_wall_probe import tapir

PORT = 19727
ROOT_DIR = Path(r"C:\LocalAI\SafeBIM_Global_Library_Test_Projects")
BACKUP = ROOT_DIR / "ТРЦ с GP - BEFORE_CLEANUP.pln"
WORKING = ROOT_DIR / "ТРЦ с GP - CLEANUP_WORKING.pln"
ORIGINAL = ROOT_DIR / "ТРЦ с GP.pln"
PLAN_LOG = "trc-sad-2d-19727-attempt.jsonl"
GRID_LOG = "trc-sad-grid-19727-attempt.jsonl"
APPROVAL_REPORT = "trc-sad-cleanup-preflight.json"
ATTEMPT_LOG = "trc-sad-cleanup-attempt.jsonl"
KINDS = {
    "CreateHatches": "Hatch", "CreatePolylines": "PolyLine",
    "CreateTexts": "Text", "CreateCircles": "Circle",
}
GUID = re.compile(r"(?i)^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$")
READS = frozenset({"GetProjectInfo", "GetAddOnVersion", "GetStories",
                   "GetAllElements", "GetDetailsOfElements"})


def _canon(v):
    return json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _write_log(path, value):
    with path.open("a", encoding="utf-8") as f:
        f.write(_canon(value) + "\n")
        f.flush()


def _digest(value):
    return hashlib.sha256(_canon(value).encode("utf-8")).hexdigest()


def _parse_log(path, kind):
    if not path.is_file() or path.stat().st_size > 4_000_000:
        raise ValueError("MISSING_OR_OVERSIZED_SOURCE_JOURNAL_" + kind)
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(rows) < 3:
        raise ValueError("INCOMPLETE_OR_INVALID_SOURCE_JOURNAL_" + kind)
    if kind == "floor":
        if rows[0].get("state") != "BEGIN" or rows[-1].get("state") != "COMPLETE_UNSAVED":
            raise ValueError("2D_DRAW_NOT_FULLY_ACKNOWLEDGED")
        if rows[0].get("binding", {}).get("projectPath") != str(ORIGINAL):
            raise ValueError("2D_DRAW_JOURNAL_WRONG_ORIGINAL_PLN")
        start, dispatched, acknowledged, finish = "BEGIN", "ABOUT_TO_WRITE", "WRITE_ACKNOWLEDGED", "COMPLETE_UNSAVED"
        actual_totals = rows[-1].get("totals")
        required = {"CreateHatches": 27, "CreatePolylines": 51, "CreateTexts": 46}
    elif kind == "grid":
        if rows[0].get("status") != "GRID_WRITE_BEGIN" or rows[-1].get("status") != "GRID_DRAWN_UNSAVED":
            raise ValueError("GRID_DRAW_NOT_FULLY_ACKNOWLEDGED")
        if rows[0].get("project", {}).get("projectPath") != str(ORIGINAL):
            raise ValueError("GRID_JOURNAL_WRONG_ORIGINAL_PLN")
        start, dispatched, acknowledged, finish = "GRID_WRITE_BEGIN", "ABOUT_TO_DISPATCH", "READBACK_RESPONSE_GUIDS", "GRID_DRAWN_UNSAVED"
        actual_totals = rows[-1].get("counts")
        required = None
    else:
        raise ValueError("INVALID_PROVENANCE_KIND")

    pending = []
    entries = []
    totals = {}
    for row in rows[1:-1]:
        state = row.get("state") if kind == "floor" else row.get("status")
        if state == dispatched:
            command = row.get("command")
            if command not in KINDS or (kind == "floor" and command == "CreateCircles"):
                raise ValueError("UNEXPECTED_MUTATION_COMMAND")
            pending.append((row.get("floor"), command, row.get("count")))
        elif state == acknowledged:
            command = row.get("command")
            floor = row.get("floor")
            ids = row.get("guids")
            if (not pending or not isinstance(ids, list) or
                    pending.pop(0) != (floor, command, len(ids))):
                raise ValueError("DISPATCH_ACK_MISMATCH")
            if (floor not in ("1", "2", "3", 1, 2, 3) or
                    not isinstance(command, str) or command not in KINDS):
                raise ValueError("UNKNOWN_SOURCE_FLOOR_OR_COMMAND")
            for guid in ids:
                if not isinstance(guid, str) or not GUID.fullmatch(guid):
                    raise ValueError("INVALID_JOURNAL_GUID")
                entries.append({
                    "guid": guid.lower(), "type": KINDS[command],
                    "floorIndex": int(floor) - 1, "from": kind,
                })
            totals[command] = totals.get(command, 0) + len(ids)
        else:
            raise ValueError("UNRECOGNIZED_OR_ERROR_JOURNAL_STATE")
    if pending or totals != actual_totals or (required and totals != required):
        raise ValueError("UNACKNOWLEDGED_OR_INCONSISTENT_SOURCE_WRITES")
    if len(entries) != len(set(x["guid"] for x in entries)):
        raise ValueError("DUPLICATE_PROVENANCE_GUID")
    return entries


def provenance(folder):
    if not folder.is_dir():
        raise ValueError("JOURNAL_DIRECTORY_MISSING")
    entries = _parse_log(folder / PLAN_LOG, "floor")
    grid = folder / GRID_LOG
    if grid.exists():
        entries.extend(_parse_log(grid, "grid"))
    if len(entries) != len({x["guid"] for x in entries}):
        raise ValueError("CROSS_JOURNAL_DUPLICATE_GUID")
    return sorted(entries, key=lambda a: a["guid"])


def read_only_transport(port=PORT):
    if port != PORT:
        raise ValueError("PORT_19727_ONLY")
    def call(command, params=None):
        if command not in READS:
            raise ValueError("MUTATION_DENIED_IN_READ_ONLY_TRANSPORT")
        return tapir(port, command, params or {}, timeout=25)
    return call


def live_guard(reader):
    info = reader("GetProjectInfo", {})
    if (info.get("projectPath") != str(WORKING) or
            info.get("projectName") != WORKING.stem or
            info.get("isUntitled") or info.get("isTeamwork")):
        raise ValueError("EXACT_SAVED_CLEANUP_WORKING_PLN_REQUIRED")
    ver = reader("GetAddOnVersion", {})
    if ver.get("version") != "1.5.10":
        raise ValueError("TAPIR_VERSION_MISMATCH")
    st = reader("GetStories", {}).get("stories")
    if (not isinstance(st, list) or len(st) != 3 or
            [(s.get("index"), float(s.get("level")), float(s.get("height")))
             for s in st] != [(0, 0.0, 3.0), (1, 3.0, 3.0), (2, 6.0, 3.0)]):
        raise ValueError("EXISTING_STORIES_CHANGED")
    if reader("GetProjectInfo", {}) != info:
        raise ValueError("PROJECT_CHANGED_DURING_GUARD")
    return {"projectPath": info["projectPath"], "projectName": info["projectName"]}


def inventory(reader):
    response = reader("GetAllElements", {})
    rows = response.get("elements") if isinstance(response, dict) else None
    if not isinstance(rows, list):
        raise ValueError("ARCHICAD_INVENTORY_UNAVAILABLE")
    guids = []
    for row in rows:
        g = row.get("elementId", {}).get("guid") if isinstance(row, dict) else None
        if not isinstance(g, str) or not GUID.fullmatch(g):
            raise ValueError("NON_GUID_IN_NATIVE_INVENTORY")
        guids.append(g.lower())
    if len(guids) != len(set(guids)):
        raise ValueError("DUPLICATE_NATIVE_INVENTORY")
    return frozenset(guids)


def verify_native_elements(reader, entries, current_inventory):
    expected = {v["guid"] for v in entries}
    if not expected.issubset(current_inventory):
        raise ValueError("JOURNAL_ELEMENTS_MISSING_FROM_OPEN_PLN")
    # Chunk requests; type and home-story must be checked against GUID order.
    for pos in range(0, len(entries), 40):
        batch = entries[pos:pos+40]
        native = reader("GetDetailsOfElements", {
            "elements": [{"elementId": {"guid": x["guid"]}} for x in batch],
            "fields": ["type", "id", "floorIndex", "layerIndex", "drawIndex", "details"],
        })
        rows = native.get("detailsOfElements")
        if not isinstance(rows, list) or len(rows) != len(batch):
            raise ValueError("NATIVE_DETAILS_COUNT_MISMATCH")
        for expected_row, actual in zip(batch, rows):
            if not isinstance(actual, dict) or (
                    actual.get("type") != expected_row["type"] or
                    actual.get("floorIndex") != expected_row["floorIndex"]):
                raise ValueError("NATIVE_ELEMENT_TYPE_OR_FLOOR_MISMATCH")
    return True


def make_preview(reader, entries):
    binding = live_guard(reader)
    before = inventory(reader)
    verify_native_elements(reader, entries, before)
    by_type = {}
    for row in entries:
        by_type[row["type"]] = by_type.get(row["type"], 0) + 1
    snapshot = {
        "status": "READ_ONLY_CLEANUP_PREFLIGHT",
        "port": PORT, "project": binding,
        "expectedBackup": str(BACKUP),
        "deleteGuids": [x["guid"] for x in entries],
        "verifiedEntries": entries,
        "types": by_type, "total": len(entries),
        "inventorySha256": _digest(sorted(before)),
        "allOtherElementsPreserved": True,
        "writes": 0, "saveProjectCalled": False,
    }
    snapshot["approvalHash"] = _digest(snapshot)
    return snapshot


def execute(reader, writer, evidence, approval, attempt):
    if attempt.exists():
        raise FileExistsError("EXISTING_CLEANUP_ATTEMPT_INSPECT_BEFORE_RETRY")
    if not BACKUP.is_file() or not WORKING.is_file():
        raise ValueError("SAVE_AS_BACKUP_AND_DISTINCT_WORKING_COPY_FIRST")
    original_entries = provenance(evidence)
    current = make_preview(reader, original_entries)
    if approval != current or approval.get("approvalHash") != _digest(
            {k:v for k,v in approval.items() if k!="approvalHash"}):
        raise ValueError("CURRENT_MODEL_OR_PROVENANCE_DRIFT_REQUIRES_NEW_PREFLIGHT")
    binding = current["project"]
    before = inventory(reader)
    _write_log(attempt, {"status": "BEGIN", "time": datetime.now(timezone.utc).isoformat(),
                         "hash": approval["approvalHash"], "total": approval["total"],
                         "project": binding})
    try:
        remaining = set(before)
        for idx in range(0, len(original_entries), 30):
            chunk = original_entries[idx:idx+30]
            if live_guard(reader) != binding or inventory(reader) != frozenset(remaining):
                raise ValueError("TARGET_OR_INVENTORY_CHANGED_DURING_CLEANUP")
            payload = {"elements": [{"elementId": {"guid": x["guid"]}} for x in chunk]}
            _write_log(attempt, {"status": "ABOUT_TO_DELETE",
                                 "batch": idx//30, "guids": [x["guid"] for x in chunk]})
            response = writer("DeleteElements", payload)
            responses = response.get("executionResults") if isinstance(response, dict) else None
            if (not isinstance(responses, list) or len(responses) != len(chunk) or
                    any(r.get("success") is not True for r in responses if isinstance(r, dict)) or
                    any(not isinstance(r, dict) for r in responses)):
                raise ValueError("NATIVE_DELETE_UNVERIFIED_NO_RETRY")
            remaining.difference_update({x["guid"] for x in chunk})
            if inventory(reader) != frozenset(remaining):
                raise ValueError("POST_DELETE_INVENTORY_NOT_EXACTLY_EXPECTED")
            _write_log(attempt, {"status": "BATCH_VERIFIED", "batch": idx//30,
                                 "removedCount": len(chunk)})
        _write_log(attempt, {"status": "COMPLETE_UNSAVED", "removedCount": len(original_entries),
                             "preservedUnrelatedCount": len(remaining)})
    except Exception as exc:
        _write_log(attempt, {"status": "PARTIAL_OR_UNKNOWN_DO_NOT_RETRY",
                             "error": type(exc).__name__ + ": " + str(exc)})
        raise
    return {"status": "EXACT_GUID_CLEANUP_COMPLETE_UNSAVED",
            "removed": len(original_entries),
            "preservedUnrelated": len(remaining), "plnSaved": False}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--port", type=int, default=PORT)
    p.add_argument("--execute", action="store_true")
    p.add_argument("--approve-hash")
    p.add_argument("--journal-dir", type=Path, default=Path.cwd())
    args = p.parse_args(argv)
    if args.port != PORT:
        raise ValueError("ONLY_ARCHICAD_PORT_19727")
    if not BACKUP.is_file() or not WORKING.is_file():
        raise ValueError("SAVE_AS_BACKUP_AND_WORKING_PLN_BEFORE_CLEANUP")
    evidence = args.journal_dir
    preview_file = evidence / APPROVAL_REPORT
    attempt_file = evidence / ATTEMPT_LOG
    reader = read_only_transport(PORT)
    if not args.execute:
        if preview_file.exists():
            raise FileExistsError("PREFLIGHT_EXISTS_USE_REVIEW_AND_EXECUTE_OR_ARCHIVE_OLD_REPORT")
        report = make_preview(reader, provenance(evidence))
        preview_file.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                                encoding="utf-8")
        print(json.dumps({"status": report["status"], "total": report["total"],
                          "types": report["types"], "approvalHash": report["approvalHash"],
                          "evidence": str(preview_file), "writeCommands": 0},
                         ensure_ascii=True, indent=2))
        return 0
    if not isinstance(args.approve_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", args.approve_hash):
        raise ValueError("EXPLICIT_APPROVAL_HASH_REQUIRED")
    if not preview_file.is_file() or not (evidence / PLAN_LOG).is_file():
        raise ValueError("PREFLIGHT_OR_SOURCE_LOG_MISSING")
    saved = json.loads(preview_file.read_text(encoding="utf-8"))
    if saved.get("approvalHash") != args.approve_hash:
        raise ValueError("APPROVAL_HASH_DOES_NOT_MATCH_REVIEWED_PREFLIGHT")
    result = execute(
        reader, lambda c, v: tapir(PORT, c, v, timeout=30),
        evidence, saved, attempt_file)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
