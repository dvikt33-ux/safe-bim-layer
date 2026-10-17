"""Read-only final inventory audit of APA Functional Test House, 2026-10-17.

Never creates/modifies/deletes/saves Archicad elements or touches journal bytes.
Reads the original 25-GUID snapshot from the durably committed repair intent,
then compares the seven journaled suffix GUIDs to current native inventory.
"""
from __future__ import annotations

from collections import Counter
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

ROOT = Path(r"C:\LocalAI\APA_AC29_Stable")
PLN = Path(r"C:\LocalAI\APA_Functional_Test_House_01.pln")
LEDGER = Path(r"C:\LocalAI\APA_Functional_Test_House_01_ledger\scene-v1-attempts.sqlite3")
PORT = 19726
SHA = "1efc00a776217723510c8ed5467469b2b4ef4642ba78b5423f6f95c6b9db14f3"
ORIGIN = "apa_functional_house_01_first_build"
SUFFIX = "apa_functional_house_01_verified_suffix_20261017"
REPAIR_TABLE = "apa_functional_house_slab_repair_v1"
sys.path.insert(0, str(ROOT / "scripts"))
import archicad_scene_run as RUN
import archicad_scene_v1 as SCENE

ALLOWED_READS = {
    "GetProjectInfo", "GetAllElements", "GetDetailsOfElements",
    "GetStories", "GetAddOnVersion"
}

def read(command, params=None):
    if command not in ALLOWED_READS:
        raise RuntimeError("READ_ONLY_ALLOWLIST_REFUSED: " + command)
    return RUN.tapir(PORT, command, params or {})

def die(why):
    raise RuntimeError(why)

def main():
    if not LEDGER.is_file() or not PLN.is_file():
        die("TEST_LEDGER_OR_PLN_MISSING")
    digest = hashlib.sha256(PLN.read_bytes()).hexdigest()
    if digest != SHA:
        die("SAVED_PLN_DRIFT")
    info = read("GetProjectInfo")
    if (info.get("projectPath") != str(PLN)
            or info.get("projectName") != PLN.stem
            or info.get("isUntitled") is not False):
        die("WRONG_NATIVE_PROJECT")
    with closing(sqlite3.connect(LEDGER.resolve().as_uri() + "?mode=ro", uri=True)) as db:
        before = db.execute(
            "SELECT state,result FROM scenes WHERE scene_id=?", (ORIGIN,)
        ).fetchone()
        later = db.execute(
            "SELECT state,result FROM scenes WHERE scene_id=?", (SUFFIX,)
        ).fetchone()
        repair_row = db.execute(
            "SELECT state,intent_json,result_json FROM " + REPAIR_TABLE
            + " WHERE scene_id=?", (ORIGIN,)
        ).fetchone()
        first = db.execute(
            "SELECT step_id,state,guid FROM steps WHERE scene_id=? ORDER BY rowid",
            (ORIGIN,)
        ).fetchall()
        last = db.execute(
            "SELECT step_id,state,guid FROM steps WHERE scene_id=? ORDER BY rowid",
            (SUFFIX,)
        ).fetchall()
    if before is None or later is None or repair_row is None:
        die("INCOMPLETE_ORIGINAL_REPAIR_OR_SUFFIX_LEDGER")
    if before[0] != "PARTIAL_OR_UNKNOWN_OUTCOME":
        die("ORIGINAL_SCENE_STATE_UNEXPECTED")
    intent = json.loads(repair_row[1])
    original_guids = [x.lower() for x in intent["before"]]
    if (len(original_guids) != 25 or len(set(original_guids)) != 25
            or repair_row[0] != "READBACK_PASS"):
        die("REPAIRED_ORIGINAL_25_SNAPSHOT_NOT_VERIFIED")
    if len(first) != 5 or len(last) != 12:
        die("EXPECTED_ORIGINAL_FIVE_AND_SUFFIX_TWELVE_ROWS")
    final_result = json.loads(later[1])
    native = read("GetAllElements").get("elements")
    if not isinstance(native, list):
        die("NATIVE_INVENTORY_UNAVAILABLE")
    current = [r["elementId"]["guid"].lower() for r in native]
    if len(current) != len(set(current)):
        die("DUPLICATE_NATIVE_GUIDS")
    suffix_new = [(sid, guid.lower(), state)
                  for sid, state, guid in last if sid not in
                  ("wall-south", "wall-east", "wall-north", "wall-west", "slab")
                  and guid]
    if len(suffix_new) != 7:
        die("NOT_EXACTLY_SEVEN_SUFFIX_NEW_GUIDS")
    expected = set(original_guids) | {guid for _, guid, _ in suffix_new}
    current_set = set(current)
    extra = sorted(current_set - expected)
    missing = sorted(expected - current_set)
    preview = SCENE.graph(300., 300.)
    plan = {step["id"]:step for step in preview["operations"]}
    mapped = {sid:{"guid":guid, "kind":kind, "floorIndex":0}
              for (sid,_,guid),kind in zip(first, ("Wall","Wall","Wall","Wall","Slab"))}
    mapped.update({sid:{"guid":guid, "kind":plan[sid]["command"][6:-1], "floorIndex":0}
                   for sid,guid,state in suffix_new})
    mapped["__plan__"] = preview
    detail_checks = []
    for sid in [s["id"] for s in preview["operations"]]:
        guid = mapped[sid]["guid"]
        try:
            step = plan[sid]
            params = RUN.resolve_params(step, mapped)
            row = RUN.requested_details(read, guid)
            owner = RUN.check_previous_wall(read, step, mapped) if step["command"] in (
                "CreateWindows", "CreateDoors") else None
            kind = RUN.verify_readback(step["command"], params, row, owner,
                                       expected_floor=0)
            detail_checks.append({"step": sid, "status": "PASS",
                                  "kind": kind, "guid": guid})
        except Exception as exc:
            detail_checks.append({"step": sid, "status": "MISMATCH",
                                  "guid": guid, "reason": str(exc)})
    extras = []
    for guid in extra[:40]:
        try:
            row = RUN.requested_details(read, guid)
            extras.append({"guid": guid, "type": row.get("type"),
                           "floorIndex": row.get("floorIndex")})
        except Exception as exc:
            extras.append({"guid": guid, "readbackError": str(exc)})
    report = {
        "status": "READ_ONLY_FINAL_INVENTORY_AUDIT",
        "sourceSavedPlnUnchanged": True,
        "project": str(PLN),
        "port": PORT,
        "originalSceneState": before[0],
        "repairState": repair_row[0],
        "suffixSceneState": later[0],
        "suffixFailedStep": final_result.get("failedStep"),
        "suffixJournalSteps": [{"id":sid,"status":st,"guid":guid}
                              for sid,st,guid in last],
        "originalInventoryCount": len(original_guids),
        "newSuffixCount": len(suffix_new),
        "nativeInventoryCount": len(current),
        "expectedNativeCount": len(expected),
        "missingExpectedGuids": missing,
        "unexpectedGuids": extra,
        "unexpectedElementDetails": extras,
        "nativeTypeCheck": detail_checks,
        "journalPassCount": sum(st=="PASS" for _,st,_ in last),
        "nativeReadbackPassCount": sum(x["status"]=="PASS" for x in detail_checks),
        "nativeWrites": 0,
        "plnWrites": 0,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"status":"READ_ONLY_AUDIT_BLOCKED",
                          "reason":type(exc).__name__+": "+str(exc),
                          "nativeWrites":0,"plnWrites":0},ensure_ascii=False))
        raise SystemExit(2)
