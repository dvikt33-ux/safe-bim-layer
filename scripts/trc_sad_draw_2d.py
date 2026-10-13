"""Fast *2D only* TRC-SAD floor plans via existing APA Tapir transport.

Creates native Archicad Polylines, Hatches and Texts on current stories
0, 1, 2; never creates Walls/Slabs/Columns/Stories/3D geometry.
Does not save, open or switch a PLN. Uses one-shot durable local attempt
record (a failed/partial write MUST NOT be automatically repeated).
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PureWindowsPath
import re
import sys

from archicad_guarded_wall_probe import tapir
import trc_sad_plan as PLAN

PORT = 19727
PROJECT_PATH = r"C:\LocalAI\SafeBIM_Global_Library_Test_Projects\ТРЦ с GP.pln"
PROJECT_NAME = "ТРЦ с GP"
EXPECTED_STORIES = {0: (0.0, 3.0), 1: (3.0, 3.0), 2: (6.0, 3.0)}
APPROVED_DRAWS = frozenset({"CreatePolylines", "CreateHatches", "CreateTexts"})
APPROVED_READS = frozenset({"GetProjectInfo", "GetStories", "GetAddOnVersion", "GetAllElements"})
DATA = PLAN.DEFAULT_SPEC
TITLE = {"1": "ПЛАН 1 ЭТАЖА", "2": "ПЛАН 2 ЭТАЖА", "3": "ПЛАН 3 ЭТАЖА"}
Z_TARGET = {"1": "±0,000", "2": "+6,300", "3": "+12,600"}
CORE_NAMES = {
    "REAR_L": "ЛК - РЕЗЕРВ", "REAR_R": "ЛК - РЕЗЕРВ",
    "FRONT_L": "ЛК - РЕЗЕРВ", "FRONT_R": "ЛК - РЕЗЕРВ",
    "ATR_LIFT": "ЛИФТ (РЕЗЕРВ)", "ATR_STAIR": "ЛЕСТН. (РЕЗЕРВ)",
}


def _log(fp, item):
    with fp.open("a", encoding="utf-8") as f:
        f.write(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n")
        f.flush()


def _xy(p):
    return {"x": float(p[0]), "y": float(p[1])}


def _rect(r):
    x0, y0, x1, y1 = r
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def _area(r):
    return round((r[2] - r[0]) * (r[3] - r[1]), 4)


def _nonoverlap(rect, obstructions):
    """Subtract axis-aligned reserved cores; hatches never cover their footprint."""
    pieces = [tuple(map(float, rect))]
    for block in obstructions:
        bx0, by0, bx1, by1 = block
        new = []
        for x0, y0, x1, y1 in pieces:
            a, b = max(x0, bx0), max(y0, by0)
            c, d = min(x1, bx1), min(y1, by1)
            if a >= c or b >= d:
                new.append((x0, y0, x1, y1))
                continue
            possible = (
                (x0, y0, a, y1),
                (c, y0, x1, y1),
                (a, y0, c, b),
                (a, d, c, y1),
            )
            new.extend(r for r in possible if r[2] - r[0] > 1e-6 and r[3] - r[1] > 1e-6)
        pieces = new
    return pieces


def plan_floor(spec, floor):
    """Pure recipe generation. No Archicad commands are executed here."""
    if floor not in ("1", "2", "3"):
        raise ValueError("ONLY_EXISTING_THREE_STORIES")
    PLAN.validate_spec(spec)
    fi = int(floor) - 1
    native_z = EXPECTED_STORIES[fi][0]
    shell = [tuple(p) for p in spec["shell"]]
    atrium = [tuple(p) for p in spec["atrium"]]
    gallery = [(77.2, 31.8), (107.6, 31.8), (119.4, 47.8),
               (119.4, 78.2), (107.6, 94.2), (77.2, 94.2),
               (65.4, 78.2), (65.4, 47.8)]
    core = [(row["id"], row["rect"]) for row in spec["reservedCores"]]
    core += [("ATR_LIFT", [76, 96, 88, 112]),
             ("ATR_STAIR", [100, 96, 112, 112])]
    polys, hatches, texts = [], [], []

    def boundary(name, pts, pen=1):
        p = list(pts)
        polys.append({"floorInd": fi, "linePenIndex": pen,
                      "coordinates": [_xy(x) for x in p + [p[0]]]})

    def hatch(pts, pen):
        hatches.append({"floorInd": fi, "coordinates": [_xy(p) for p in pts],
                        "contourPenIndex": 1, "fillPenIndex": pen,
                        "fillBackgroundPenIndex": 0, "showArea": False})

    def note(label, x, y, size=2.5):
        texts.append({"floorIndex": fi,
                      "coordinate": {"x": float(x), "y": float(y), "z": native_z},
                      "height": size, "pen": 1, "text": label})

    boundary("shell", shell, 1)
    boundary("atrium", atrium, 3)
    boundary("gallery", gallery, 4)
    # A few true common-route outlines, not additional speculative rooms.
    for a, b in [((58, 28), (127, 28)), ((58, 123), (127, 123)),
                 ((62, 30), (62, 121)), ((123, 30), (123, 121))]:
        polys.append({"floorInd": fi, "linePenIndex": 4,
                      "coordinates": [_xy(a), _xy(b)]})

    if floor == "1":
        # Garden at ground level, atrium is an OPEN VOID only on upper floors.
        hatch(atrium, 33)
        note("САД / АТРИУМ", 82, 63, 3.0)
    else:
        note("ОТКРЫТЫЙ АТРИУМ", 76, 63, 3.0)
    notes = []
    pen_cycle = {"1": 19, "2": 63, "3": 73}
    obstacles = [r for _name, r in core]
    for z in (q for q in spec["program"] if q["floor"] == floor):
        rect = z["rect"]
        pieces = _nonoverlap(rect, obstacles)
        if not pieces:
            raise ValueError("ZONE_COMPLETELY_INSIDE_RESERVED_CORE_" + z["id"])
        for patch in pieces:
            hatch(_rect(patch), pen_cycle[floor])
        boundary("zone_" + z["id"], _rect(rect), 7)
        # Labels are program placeholders, not computed native Zone entities.
        note(z["label"], rect[0] + 1.5, rect[1] + 2.2, 2.3)
        notes.append({"id": z["id"], "grossReservationSquareMeters": _area(rect),
                      "netAfterCoreReserveSquareMeters": round(sum(_area(r) for r in pieces), 4),
                      "status": "2D_PROGRAM_ONLY_UNVERIFIED"})
    for name, rect in core:
        boundary("core_" + name, _rect(rect), 5)
        cx = (rect[0] + rect[2]) / 2
        cy = (rect[1] + rect[3]) / 2
        note(CORE_NAMES[name], cx - 6, cy, 1.9)
    # Show future protected stairs as reservations only. NO stair treads/doors
    # because their actual geometries and evacuation design are not verified.
    note(TITLE[floor] + " / ЭСКИЗ 2D", 4, 149, 3.7)
    note("Проектная отметка " + Z_TARGET[floor] +
         " (в PLN отметка +" + str(native_z).replace(".", ",") + " м)", 4, 155, 2.6)
    note("Габарит 184800 x 142800 мм; площади помещений НЕ утверждены", 4, 161, 2.5)
    note("2D: линии + штриховки + подписи. Элементов 3D: 0", 4, 167, 2.5)
    if floor == "3":
        note("ПИТАНИЕ → ОТДЫХ → КОВОРКИНГ → БИБЛИОТЕКА", 91, 131, 3)
    return {"floor": floor, "nativeFloorIndex": fi,
            "commands": [
                ("CreateHatches", {"hatchesData": hatches}),
                ("CreatePolylines", {"polylinesData": polys}),
                ("CreateTexts", {"textsData": texts}),
            ],
            "programAreaAudit": notes,
            "counts": {"hatches": len(hatches), "polylines": len(polys), "texts": len(texts)}}


def guarded_live(read):
    """No guessed project path, version or story heights."""
    info = read("GetProjectInfo", {})
    if (not isinstance(info, dict)
            or info.get("projectName") != PROJECT_NAME
            or info.get("projectPath") != PROJECT_PATH
            or info.get("isUntitled") or info.get("isTeamwork")):
        raise ValueError("WRONG_ACTIVE_TRC_PLN")
    ver = read("GetAddOnVersion", {})
    if ver.get("version") != "1.5.10":
        raise ValueError("UNQUALIFIED_TAPIR_VERSION")
    stories = read("GetStories", {})
    rows = stories.get("stories")
    if not isinstance(rows, list) or len(rows) != 3:
        raise ValueError("THREE_EXISTING_STORIES_REQUIRED")
    by_index = {r["index"]: r for r in rows}
    if set(by_index) != {0, 1, 2}:
        raise ValueError("UNEXPECTED_STORY_INDICES")
    for idx, (level, height) in EXPECTED_STORIES.items():
        native = by_index[idx]
        if abs(float(native["level"]) - level) > 1e-6 or abs(float(native["height"]) - height) > 1e-6:
            raise ValueError("STORY_STRUCTURE_CHANGED")
    after = read("GetProjectInfo", {})
    if info != after:
        raise ValueError("PROJECT_CHANGED_DURING_READ")
    return {"projectPath": info["projectPath"], "projectName": info["projectName"],
            "storyLevels": [by_index[i]["level"] for i in range(3)]}


def element_ids(result, expected):
    rows = result.get("elements")
    if not isinstance(rows, list) or len(rows) != expected:
        raise ValueError("NATIVE_CREATE_RESPONSE_CARDINALITY_UNKNOWN_NO_RETRY")
    guids = []
    for r in rows:
        if not isinstance(r, dict):
            raise ValueError("NATIVE_CREATE_RETURNED_ERROR_NO_RETRY")
        guid = r.get("elementId", {}).get("guid")
        if not isinstance(guid, str) or not re.fullmatch(
                r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}", guid):
            raise ValueError("NATIVE_CREATED_ELEMENT_GUID_UNVERIFIED_NO_RETRY")
        guids.append(guid)
    if len(set(guids)) != len(guids):
        raise ValueError("DUPLICATE_NATIVE_GUID_NO_RETRY")
    return guids


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--port", type=int, default=PORT)
    ap.add_argument("--floor", choices=["1", "2", "3", "all"], default="all")
    ap.add_argument("--draw", action="store_true",
                    help="Write 2D native elements UNSAVED to the exact open PLN")
    ap.add_argument("--evidence", type=Path,
                    default=Path("trc-sad-2d-19727-attempt.jsonl"))
    args = ap.parse_args(argv)
    if args.port != PORT:
        raise ValueError("ONLY_APPROVED_PORT_19727")
    spec = json.loads(DATA.read_text(encoding="utf-8"))
    floors = ["1", "2", "3"] if args.floor == "all" else [args.floor]
    plans = [plan_floor(spec, sid) for sid in floors]
    source_hash = hashlib.sha256(DATA.read_bytes()).hexdigest()
    preview = {"status": "2D_PLAN_READY_NO_WRITES",
               "port": args.port, "floors": [p["floor"] for p in plans],
               "sourceSha256": source_hash,
               "counts": {p["floor"]: p["counts"] for p in plans},
               "native3DOperations": 0, "changesSavedToPLN": False}
    if not args.draw:
        print(json.dumps(preview, indent=2, ensure_ascii=True))
        return 0
    if args.evidence.exists():
        raise FileExistsError("PRIOR_ATTEMPT_EXISTS_DO_NOT_RETRY_OR_DUPLICATE")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    read = lambda c, p: tapir(args.port, c, p, timeout=20)
    bound = guarded_live(read)
    # A marker is persisted BEFORE any BIM/2D create, so failed/partial
    # outcomes never lead to an automatic retry.
    _log(args.evidence, {"state": "BEGIN", **preview, "binding": bound,
                        "time": datetime.now(timezone.utc).isoformat()})
    totals = {"CreateHatches": 0, "CreatePolylines": 0, "CreateTexts": 0}
    try:
        for p in plans:
            for command, params in p["commands"]:
                if command not in APPROVED_DRAWS or set(params) != {
                        {"CreateHatches": "hatchesData",
                         "CreatePolylines": "polylinesData",
                         "CreateTexts": "textsData"}[command]}:
                    raise ValueError("2D_COMMAND_OR_PARAMETER_NOT_ALLOWLISTED")
                # Guard identity+levels before each group; no window/project switch.
                if guarded_live(read) != bound:
                    raise ValueError("LIVE_BINDING_CHANGED")
                expected = len(next(iter(params.values())))
                _log(args.evidence, {"state": "ABOUT_TO_WRITE", "floor": p["floor"],
                                     "command": command, "count": expected})
                response = read(command, params)
                guids = element_ids(response, expected)
                totals[command] += len(guids)
                _log(args.evidence, {"state": "WRITE_ACKNOWLEDGED",
                                     "floor": p["floor"], "command": command,
                                     "guids": guids})
    except Exception as exc:
        _log(args.evidence, {"state": "PARTIAL_OR_UNKNOWN_OUTCOME",
                             "error": type(exc).__name__ + ": " + str(exc),
                             "warning": "DO NOT RETRY: inspect Archicad/current plan first"})
        raise
    _log(args.evidence, {"state": "COMPLETE_UNSAVED", "totals": totals,
                         "warning": "Review drawing in Archicad; SAVE MANUALLY ONLY IF APPROVED"})
    print(json.dumps({"status": "2D_DRAW_COMPLETE_UNSAVED", "port": args.port,
                      "native3DOperations": 0, "native2DElements": totals,
                      "journal": str(args.evidence),
                      "saveProjectCalled": False}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
