"""TRC-SAD planning AXIS/DIMENSION 2D overlay for Archicad 29, no BIM/3D.

Design grid: X=0..184.8 at 8.4 m (axes 1..23), Y=0..142.8 at 8.4 m
(axes А..Ф); every other bay indicates a possible 16.8 m planning module.
NOT engineering-approved supports. Native 2D Polyline/Circle/Text; dimension
chains use explicit computed values, NOT misleading associative Dimensions.
Uses existing project/port/three-story guard and UTF-8 Tapir transport.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

from archicad_guarded_wall_probe import tapir
from trc_sad_draw_2d import (
    PORT, PROJECT_PATH, guarded_live, element_ids, _log,
)
import trc_sad_plan as PLAN

GRID_STEP = 8.4
WIDTH = 184.8
DEPTH = 142.8
X_COUNT = 23
Y_COUNT = 18
Y_LABELS = tuple("АБВГДЕЖИКЛМНПРСТУФ")
PEN_AXES = 7
PEN_DIM = 1
PEN_PRIMARY = 4
DEFAULT_JOURNAL = Path("trc-sad-grid-19727-attempt.jsonl")
WRITE_COMMANDS = ("CreatePolylines", "CreateCircles", "CreateTexts")


def geometry(spec):
    PLAN.validate_spec(spec)
    xs = [round(i * GRID_STEP, 6) for i in range(X_COUNT)]
    ys = [round(i * GRID_STEP, 6) for i in range(Y_COUNT)]
    if abs(xs[-1] - WIDTH) > 1e-6 or abs(ys[-1] - DEPTH) > 1e-6:
        raise ValueError("GRID_DOES_NOT_DIVIDE_OUTLINE")
    if len(Y_LABELS) != len(ys) or len(set(Y_LABELS)) != len(Y_LABELS):
        raise ValueError("INVALID_RUSSIAN_AXES")
    atrium = spec["atrium"]
    ext = [min(p[0] for p in atrium), min(p[1] for p in atrium),
           max(p[0] for p in atrium), max(p[1] for p in atrium)]
    if [round(v, 1) for v in ext] != [71.4, 37.8, 113.4, 88.2]:
        raise ValueError("ATRIUM_DIMENSION_MISMATCH")
    return {
        "x": xs, "y": ys, "atriumBounds": ext,
        "totalWidthMm": int(round(WIDTH * 1000)),
        "totalDepthMm": int(round(DEPTH * 1000)),
        "primaryModuleMm": 16800,
        "subModuleMm": 8400,
        "notAColumnLayout": True,
    }


def build_floor(spec, floor):
    if floor not in (1, 2, 3):
        raise ValueError("ONLY_EXISTING_FLOORS_1_2_3")
    grid = geometry(spec)
    index = floor - 1
    level = (0.0, 3.0, 6.0)[index]
    polylines = []
    circles = []
    texts = []

    def p(x, y):
        return {"x": round(float(x), 6), "y": round(float(y), 6)}

    def poly(points, pen=PEN_DIM):
        polylines.append({
            "floorInd": index, "linePenIndex": pen,
            "coordinates": [p(x, y) for x, y in points]})

    def circ(x, y):
        circles.append({
            "floorInd": index, "linePenIndex": PEN_DIM,
            "origin": p(x, y), "radius": 2.0})

    def label(x, y, val, height=2.3):
        texts.append({
            "floorIndex": index, "coordinate": {"x": float(x), "y": float(y), "z": level},
            "text": str(val), "height": height, "pen": PEN_DIM,
            "justification": "Center"})

    xs, ys = grid["x"], grid["y"]
    # Axes extend beyond the approved building footprint: purely datum/grid.
    # Primary every 16.8 m; secondary every 8.4 m.
    for i, x in enumerate(xs):
        poly([(x, -1), (x, DEPTH + 1)],
             PEN_PRIMARY if i % 2 == 0 else PEN_AXES)
        circ(x, -5.0)
        circ(x, DEPTH + 5.0)
        label(x, -5.0, i + 1)
        label(x, DEPTH + 5.0, i + 1)

    for i, y in enumerate(ys):
        poly([(-1, y), (WIDTH + 1, y)],
             PEN_PRIMARY if i % 2 == 0 else PEN_AXES)
        circ(-5.0, y)
        circ(WIDTH + 5.0, y)
        label(-5.0, y, Y_LABELS[i])
        label(WIDTH + 5.0, y, Y_LABELS[i])

    # Two measured, NON-ASSOCIATIVE dimension chains on bottom:
    # actual consecutive 8400 widths, plus overall 184800.
    def tick(x, y):
        poly([(x - .8, y - .8), (x + .8, y + .8)], PEN_DIM)

    def v_tick(x, y):
        poly([(x - .8, y - .8), (x + .8, y + .8)], PEN_DIM)

    y_chain, y_total = -12.0, -19.0
    poly([(xs[0], y_chain), (xs[-1], y_chain)])
    for x in xs:
        poly([(x, -9.0), (x, y_chain - 1.7)])
        tick(x, y_chain)
    for a, b in zip(xs, xs[1:]):
        label((a + b) / 2, y_chain - 2.8, round((b - a) * 1000), 2.1)
    poly([(xs[0], y_total), (xs[-1], y_total)])
    for x in (xs[0], xs[-1]):
        poly([(x, y_chain - 1.5), (x, y_total - 1.7)])
        tick(x, y_total)
    label(WIDTH / 2, y_total - 2.7, grid["totalWidthMm"], 2.6)

    # Matching Y dimensions on the left.
    x_chain, x_total = -12.0, -19.0
    poly([(x_chain, ys[0]), (x_chain, ys[-1])])
    for y in ys:
        poly([(-9.0, y), (x_chain - 1.7, y)])
        v_tick(x_chain, y)
    for a, b in zip(ys, ys[1:]):
        label(x_chain - 3.3, (a + b) / 2, round((b - a) * 1000), 2.1)
    poly([(x_total, ys[0]), (x_total, ys[-1])])
    for y in (ys[0], ys[-1]):
        poly([(x_chain - 1.5, y), (x_total - 1.7, y)])
        v_tick(x_total, y)
    label(x_total - 4.0, DEPTH / 2, grid["totalDepthMm"], 2.6)

    # Atrium bounding offsets shown as 2D measured guide annotation,
    # not as fictional structural columns.
    x0, y0, x1, y1 = grid["atriumBounds"]
    label((x0 + x1) / 2, (y0 + y1) / 2 - 3.0,
          "АТРИУМ: " + str(round((x1 - x0) * 1000)) +
          " x " + str(round((y1 - y0) * 1000)) + " мм", 2.3)
    label((x0 + x1) / 2, (y0 + y1) / 2 + 3.0,
          "РЕЗЕРВ ПО ОГИБАЮЩЕМУ КОНТУРУ", 2.0)

    # Same front corner cuts: x cut=42m, y cut=21m.
    label(21.0, 22.0, "СКОС: 42000 / 21000 мм", 2.1)
    label(WIDTH - 21.0, 22.0, "СКОС: 42000 / 21000 мм", 2.1)
    label(WIDTH / 2, -25.5,
          "РАЗМЕРЫ В ММ. СЕТКА 8400; УКРУПНЕННЫЙ МОДУЛЬ 16800.", 2.4)
    label(WIDTH / 2, -29.5,
          "ОСИ ПЛАНИРОВОЧНЫЕ, НЕ МЕСТА КОЛОНН. РАЗМЕРЫ 2D, НЕ АССОЦИАТИВНЫЕ.", 2.1)

    return {
        "floor": floor, "nativeFloorIndex": index, "grid": grid,
        "commands": [
            ("CreatePolylines", {"polylinesData": polylines}),
            ("CreateCircles", {"circlesData": circles}),
            ("CreateTexts", {"textsData": texts}),
        ],
        "counts": {
            "polylines": len(polylines), "circles": len(circles),
            "texts": len(texts)},
        "native3DOperations": 0,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--floor", choices=["1", "2", "3", "all"], default="all")
    parser.add_argument("--draw", action="store_true",
                        help="Add native 2D axes/dimensions to already opened target PLN, unsaved")
    parser.add_argument("--journal", type=Path, default=DEFAULT_JOURNAL)
    args = parser.parse_args(argv)
    if args.port != PORT:
        raise ValueError("PORT_19727_ONLY")
    spec = json.loads(PLAN.DEFAULT_SPEC.read_text(encoding="utf-8"))
    floors = [1, 2, 3] if args.floor == "all" else [int(args.floor)]
    plans = [build_floor(spec, floor) for floor in floors]
    summary = {
        "status": "GRID_2D_OFFLINE_PREVIEW", "port": PORT, "floors": floors,
        "grid": plans[0]["grid"], "counts": {p["floor"]: p["counts"] for p in plans},
        "noNative3D": True, "plnSaved": False,
        "modelSha256": hashlib.sha256(PLAN.DEFAULT_SPEC.read_bytes()).hexdigest(),
    }
    if not args.draw:
        print(json.dumps(summary, ensure_ascii=True, indent=2))
        return 0
    if args.journal.exists():
        raise FileExistsError("PREVIOUS_GRID_ATTEMPT_EXISTS_INSPECT_MODEL_DO_NOT_DUPLICATE")
    transport = lambda cmd, params: tapir(PORT, cmd, params, timeout=25)
    bound = guarded_live(transport)  # read only
    _log(args.journal, {
        **summary, "status": "GRID_WRITE_BEGIN",
        "project": bound, "time": datetime.now(timezone.utc).isoformat()})
    totals = {k: 0 for k in WRITE_COMMANDS}
    try:
        for plan in plans:
            for cmd, payload in plan["commands"]:
                if cmd not in WRITE_COMMANDS:
                    raise ValueError("NON_2D_COMMAND_REFUSED")
                if guarded_live(transport) != bound:
                    raise ValueError("ACTIVE_PROJECT_OR_STORIES_CHANGED")
                rows = next(iter(payload.values()))
                _log(args.journal, {"status": "ABOUT_TO_DISPATCH",
                                    "floor": plan["floor"],
                                    "command": cmd, "count": len(rows)})
                response = transport(cmd, payload)
                guids = element_ids(response, len(rows))
                totals[cmd] += len(guids)
                _log(args.journal, {"status": "READBACK_RESPONSE_GUIDS",
                                    "floor": plan["floor"],
                                    "command": cmd, "guids": guids})
    except Exception as exc:
        _log(args.journal, {
            "status": "PARTIAL_OR_UNKNOWN_OUTCOME",
            "error": type(exc).__name__ + ": " + str(exc),
            "action": "DO_NOT_RETRY; inspect current Archicad elements and this journal"})
        raise
    _log(args.journal, {"status": "GRID_DRAWN_UNSAVED", "counts": totals})
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    print(json.dumps({
        "status": "GRID_DRAWN_UNSAVED",
        "port": PORT, "floors": floors, "created2D": totals,
        "created3D": 0, "saveProjectCalled": False,
        "journal": str(args.journal)
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
