"""Build the first live Series 178-07sm.86 typical-floor skeleton in the open Archicad project.

Safety/operating rules:
- never opens, switches, saves or closes a PLN;
- always reads a fresh Model Dump before writing;
- dry-run is default; --execute is required for writes;
- refuses a missing target story or pre-existing matching skeleton;
- writes only the provisional structural skeleton from the checked-in JSON spec;
- reads every created GUID back before reporting PASS.

This is intentionally the fast MVP skeleton. Panel marks, exact openings, room
partitions and stair geometry remain a later refinement pass.
"""
from __future__ import annotations

import argparse
import contextlib
import importlib.util
import io
import json
import math
import os
import sys
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SPEC = ROOT / "examples" / "series178_typical_floor_v0.1.json"
DUMP_CLIENT = ROOT / "archicad-addon" / "Examples" / "model_dump_v1.py"
EVIDENCE = Path(os.environ.get(
    "SAFE_BIM_MVP_EVIDENCE",
    Path(tempfile.gettempdir()) / "safe-bim-mvp-evidence"
)) / "series178-typical-floor"
DEFAULT_PORT = 19723
TOL = 0.002


def write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def fresh_dump(port: int, stem: str):
    spec = importlib.util.spec_from_file_location("model_dump_v1", DUMP_CLIENT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with contextlib.redirect_stdout(io.StringIO()):
        data, metrics = module.dump(EVIDENCE / f"{stem}.json", port)
    return data, metrics


def api_call(port: int, command: str, parameters: dict, stem: str):
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    request = {
        "command": "API.ExecuteAddOnCommand",
        "parameters": {
            "addOnCommandId": {
                "commandNamespace": "TapirCommand",
                "commandName": command,
            },
            "addOnCommandParameters": parameters,
        },
    }
    payload = json.dumps(request, ensure_ascii=False).encode("utf-8")
    (EVIDENCE / f"{stem}.request.json").write_bytes(payload)
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}",
        payload,
        {"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=180) as response:
        raw = response.read()
    (EVIDENCE / f"{stem}.response.json").write_bytes(raw)
    envelope = json.loads(raw)
    if not envelope.get("succeeded"):
        raise RuntimeError(f"{command} transport failed: {envelope}")
    result = envelope.get("result", {}).get("addOnCommandResponse", {})
    if isinstance(result, dict) and "error" in result:
        raise RuntimeError(f"{command} failed: {result}")
    return result


def created_guids(result: dict, expected: int):
    rows = result.get("elements", [])
    guids = []
    errors = []
    for row in rows:
        guid = row.get("elementId", {}).get("guid")
        if guid:
            guids.append(guid)
        else:
            errors.append(row)
    if errors or len(guids) != expected:
        raise RuntimeError(
            f"Expected {expected} created GUIDs, got {len(guids)}; "
            f"errors={errors[:4]}"
        )
    return guids


def e_map(data: dict):
    return {e["guid"].lower(): e for e in data.get("elements", [])}


def wall_ref(element: dict):
    if element.get("type") != "Wall":
        return None
    ref = element.get("placement", {}).get("referenceGeometry", {})
    if ref.get("kind") != "WallReferenceLine" or ref.get("arcAngle") not in (0, 0.0):
        return None
    if not ref.get("begin") or not ref.get("end"):
        return None
    return ref


def pt(p, ox, oy):
    return {"x": float(p[0]) + ox, "y": float(p[1]) + oy}


def point_dist(a, b):
    return math.hypot(float(a["x"]) - float(b["x"]), float(a["y"]) - float(b["y"]))


def wall_matches(element: dict, wall: dict, construction: dict, story_index: int, ox: float, oy: float):
    ref = wall_ref(element)
    if ref is None or element.get("homeStory") != story_index:
        return False
    a = pt(wall["a"], ox, oy)
    b = pt(wall["b"], ox, oy)
    ea, eb = ref["begin"], ref["end"]
    same = point_dist(a, ea) <= TOL and point_dist(b, eb) <= TOL
    reverse = point_dist(a, eb) <= TOL and point_dist(b, ea) <= TOL
    expected_t = (
        construction["externalPanelThickness"]
        if wall["role"] == "external"
        else construction["internalBearingPanelThickness"]
    )
    return (
        (same or reverse)
        and abs(float(ref.get("thickness", -999)) - float(expected_t)) <= TOL
        and abs(float(ref.get("height", -999)) - float(construction["wallClearHeight"])) <= TOL
    )


def body_bounds(element: dict):
    pts = [p for b in element.get("bodies", []) for p in b.get("vertices", [])]
    if not pts:
        return None
    return tuple(
        (min(float(p[i]) for p in pts), max(float(p[i]) for p in pts))
        for i in range(3)
    )


def story_or_block(data: dict, story_index: int):
    matches = [s for s in data.get("stories", []) if int(s["index"]) == story_index]
    if len(matches) != 1:
        raise RuntimeError(
            f"Target story index {story_index} is absent or ambiguous. "
            f"Available={[s.get('index') for s in data.get('stories', [])]}"
        )
    return matches[0]


def make_plan(spec: dict, story_index: int, ox: float, oy: float):
    c = spec["provisionalConstruction"]
    walls = []
    for item in spec["walls"]:
        thickness = (
            c["externalPanelThickness"]
            if item["role"] == "external"
            else c["internalBearingPanelThickness"]
        )
        walls.append({
            "id": item["id"],
            "role": item["role"],
            "begCoordinate": pt(item["a"], ox, oy),
            "endCoordinate": pt(item["b"], ox, oy),
            "floorIndex": story_index,
            "zCoordinate": 0.0,
            "height": c["wallClearHeight"],
            "thickness": thickness,
            "offset": 0.0,
            "arcAngle": 0.0,
            "referenceLineLocation": "Center",
            "structureType": "Basic",
        })
    slabs = []
    for item in spec["slabs"]:
        slabs.append({
            "id": item["id"],
            "floorIndex": story_index,
            "thickness": item["thickness"],
            "referencePlaneLocation": item["referencePlaneLocation"],
            "polygonCoordinates": [pt(p, ox, oy) for p in item["polygon"]],
        })
    return walls, slabs


def duplicate_guard(data: dict, spec: dict, story_index: int, ox: float, oy: float):
    existing = []
    for expected in spec["walls"]:
        for element in data.get("elements", []):
            if wall_matches(
                element, expected, spec["provisionalConstruction"],
                story_index, ox, oy
            ):
                existing.append({
                    "specId": expected["id"],
                    "guid": element["guid"],
                })
                break
    if existing:
        raise RuntimeError(
            "Refusing to overlap an existing matching Series 178 skeleton; "
            f"matches={existing[:8]}"
        )


def verify_wall_batch(after: dict, guids: list[str], spec: dict, story_index: int, ox: float, oy: float):
    amap = e_map(after)
    out = []
    for guid, expected in zip(guids, spec["walls"]):
        element = amap.get(guid.lower())
        ok = bool(element and wall_matches(
            element, expected, spec["provisionalConstruction"],
            story_index, ox, oy
        ))
        out.append({
            "id": expected["id"],
            "guid": guid,
            "pass": ok,
            "type": element.get("type") if element else None,
            "homeStory": element.get("homeStory") if element else None,
        })
    return out


def verify_slab(after: dict, guid: str, spec: dict, story_index: int, ox: float, oy: float):
    element = e_map(after).get(guid.lower())
    if not element or element.get("type") != "Slab" or element.get("homeStory") != story_index:
        return {"guid": guid, "pass": False, "reason": "Slab missing/type/story mismatch"}
    bb = body_bounds(element)
    if bb is None:
        return {"guid": guid, "pass": False, "reason": "Slab has no body"}
    overall = spec["grid"]["overall"]
    expected = (
        (ox, ox + float(overall["x"])),
        (oy, oy + float(overall["y"])),
    )
    xy_ok = all(
        abs(bb[i][0] - expected[i][0]) <= TOL
        and abs(bb[i][1] - expected[i][1]) <= TOL
        for i in (0, 1)
    )
    z_span = bb[2][1] - bb[2][0]
    thick_ok = abs(z_span - float(spec["provisionalConstruction"]["slabThickness"])) <= TOL
    return {
        "guid": guid,
        "pass": bool(xy_ok and thick_ok),
        "bounds": bb,
        "expectedXY": expected,
        "thickness": z_span,
    }


def run(args):
    spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    story_index = args.story_index
    if story_index is None:
        story_index = int(spec["defaultStoryIndex"])

    before, before_metrics = fresh_dump(args.port, "before")
    story = story_or_block(before, story_index)
    duplicate_guard(before, spec, story_index, args.origin_x, args.origin_y)
    walls, slabs = make_plan(spec, story_index, args.origin_x, args.origin_y)

    plan = {
        "status": "DRY_RUN" if not args.execute else "PLANNED",
        "projectRule": "current open project only; no open/switch/save/close",
        "spec": str(Path(args.spec).resolve()),
        "storyIndex": story_index,
        "storyElevation": story["elevation"],
        "origin": {"x": args.origin_x, "y": args.origin_y},
        "provisional": True,
        "wallCount": len(walls),
        "slabCount": len(slabs),
        "walls": walls,
        "slabs": slabs,
        "beforeElementCount": len(before.get("elements", [])),
        "beforeDumpCounts": before.get("counts"),
        "beforeMetrics": before_metrics,
    }
    write_json(EVIDENCE / "plan.json", plan)
    if not args.execute:
        return plan

    slab_payload = []
    for item in slabs:
        row = {k: v for k, v in item.items() if k != "id"}
        row["level"] = float(story["elevation"])
        slab_payload.append(row)
    slab_result = api_call(
        args.port, "CreateSlabs", {"slabsData": slab_payload}, "create-slabs"
    )
    slab_guids = created_guids(slab_result, len(slabs))
    after_slab, _ = fresh_dump(args.port, "after-slab")
    slab_checks = [
        verify_slab(
            after_slab, guid, spec, story_index, args.origin_x, args.origin_y
        )
        for guid in slab_guids
    ]
    if not all(x["pass"] for x in slab_checks):
        return {
            "status": "BLOCKED",
            "stage": "slab-readback",
            "slabs": slab_checks,
            "retainedGuids": slab_guids,
            "note": "Created elements are retained for inspection; project was not saved.",
        }

    wall_payload = [{k: v for k, v in item.items() if k not in ("id", "role")} for item in walls]
    wall_result = api_call(
        args.port, "CreateWalls", {"wallsData": wall_payload}, "create-walls"
    )
    wall_guids = created_guids(wall_result, len(walls))
    after, after_metrics = fresh_dump(args.port, "after")
    wall_checks = verify_wall_batch(
        after, wall_guids, spec, story_index, args.origin_x, args.origin_y
    )

    result = {
        "status": "PASS" if all(x["pass"] for x in wall_checks) else "BLOCKED",
        "stage": "skeleton-readback",
        "specStatus": spec["source"]["status"],
        "storyIndex": story_index,
        "storyElevation": story["elevation"],
        "origin": {"x": args.origin_x, "y": args.origin_y},
        "slabs": slab_checks,
        "walls": wall_checks,
        "createdSlabGuids": slab_guids,
        "createdWallGuids": wall_guids,
        "elementCountBefore": len(before.get("elements", [])),
        "elementCountAfter": len(after.get("elements", [])),
        "afterDumpCounts": after.get("counts"),
        "afterMetrics": after_metrics,
        "retained": True,
        "savedProject": False,
        "nextPhase": (
            "visual compare -> targeted partitions/openings/stair/balconies"
            if all(x["pass"] for x in wall_checks)
            else "inspect read-back mismatch before any further geometry"
        ),
    }
    write_json(EVIDENCE / "result.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", default=str(DEFAULT_SPEC))
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--story-index", type=int, default=None)
    parser.add_argument("--origin-x", type=float, default=0.0)
    parser.add_argument("--origin-y", type=float, default=0.0)
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually create the provisional skeleton in the currently open Archicad project.",
    )
    args = parser.parse_args()
    try:
        result = run(args)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if result.get("status") == "BLOCKED":
            raise SystemExit(2)
    except Exception as exc:
        print(json.dumps({"status": "BLOCKED", "error": str(exc)}, ensure_ascii=False, indent=2))
        raise SystemExit(2)


if __name__ == "__main__":
    main()
