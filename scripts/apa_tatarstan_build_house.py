#!/usr/bin/env python3
"""Build one native BIM shell NEXT TO the old Tatarstan test house.

One-shot write to the ONE already-open saved Archicad 29 PLN; no switching,
no Morph, no deletes. Uses the project's existing pinned read-only adapter.
Only --build authorizes a write. Every native create is followed by readback,
one persistent journal, a backup of saved PLN, and no automatic retry.

This creates a geometric test shell, NOT engineered construction documents.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import re
import shutil
import sys
import urllib.request
import uuid

import apa_tatarstan_readonly_snapshot as R

PORT = 19724
OLD_WALL = "0ca6a748-e5e1-41d4-aae6-778ace39d960"
OLD_SLAB = "2a99cbab-342d-4f04-a382-2a669d8f5149"
OLD_ROOF = "9a0a855b-b705-4f66-b4d4-032d649be66b"
WRITES = frozenset({"CreateWalls", "CreateSlabs", "ModifySlabs",
                    "CreateRoofs", "SaveProject"})
TOL = 0.003
X0, X1, XC = 112.0, 122.0, 117.0
Y0, Y1 = 39.0, 51.0
WALL_T, SLAB_T, ROOF_T = 0.38, 0.20, 0.25
STORY_H = 3.0
PITCH = math.radians(35)
ENVELOPE = (110.0, 124.0, 37.0, 53.0, -1.0, 11.0)


def xy(x, y):
    return {"x": round(float(x), 7), "y": round(float(y), 7)}


def same(a, b):
    return (type(a) in (float, int) and math.isfinite(a)
            and abs(a - b) <= TOL)


def assert_response_success(result, command):
    if result != {"success": True}:
        raise RuntimeError(f"WRITE_RESULT_NOT_SUCCESS: {command}: {result!r}")


def assert_modify_success(result):
    rows = result.get("executionResults")
    if not isinstance(rows, list) or rows != [{"success": True}]:
        raise RuntimeError(f"SLAB_MODIFY_NOT_SUCCESS: {result!r}")


def call(command, params=None, *, port=PORT, timeout=600):
    if command in R.READ_COMMANDS:
        return R.tapir(command, params, port=port, timeout=timeout)
    if command not in WRITES:
        raise RuntimeError("UNAUTHORIZED_TAPIR_COMMAND: " + command)
    payload = json.dumps({
        "command": "API.ExecuteAddOnCommand",
        "parameters": {
            "addOnCommandId": {
                "commandNamespace": "TapirCommand", "commandName": command,
            },
            "addOnCommandParameters": params if params is not None else {},
        },
    }, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}/", data=payload, method="POST",
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as stream:
        response = json.load(stream)
    if response.get("succeeded") is not True:
        raise RuntimeError(f"WRITE_ENVELOPE_FAILURE: {command}: {response.get('error')!r}")
    data = response.get("result", {}).get("addOnCommandResponse")
    if not isinstance(data, dict) or "error" in data:
        raise RuntimeError(f"WRITE_RESPONSE_INVALID: {command}: {data!r}")
    return data


def api_factory(port):
    return lambda name, data=None, timeout=600: call(
        name, data, port=port, timeout=timeout)


def details(api, guid):
    result = api("GetDetailsOfElements", {
        "elements": [{"elementId": {"guid": guid}}],
        "fields": ["type", "id", "floorIndex", "details"],
    })
    rows = result.get("detailsOfElements")
    if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict):
        raise RuntimeError("TYPED_ELEMENT_READBACK_MISSING: " + guid)
    return rows[0]


def src_material(api):
    """Reuse real native building-material identity already present in this PLN."""
    w = details(api, OLD_WALL)
    s = details(api, OLD_SLAB)
    r = details(api, OLD_ROOF)
    if (w.get("type") != "Wall" or w.get("floorIndex") != 0
            or s.get("type") != "Slab" or s.get("floorIndex") != 0
            or r.get("type") != "Roof" or r.get("details", {}).get("roofClass") != "SinglePlane"):
        raise RuntimeError("SOURCE_ELEMENTS_CHANGED")
    wall = w["details"]
    slab = s["details"]
    roof = r["details"]
    if (wall.get("structureType") != "Basic"
            or slab.get("structureType") != "Basic"
            or roof.get("structureType") != "Basic"):
        raise RuntimeError("SOURCE_BASIC_MATERIAL_BINDING_MISSING")
    refs = [x.get("buildingMaterialId", {}).get("guid", "").lower()
            for x in (wall, slab, roof)]
    if (not all(R.GUID_PATTERN.fullmatch(g) for g in refs)
            or len(set(refs)) != 1):
        raise RuntimeError("SOURCE_MATERIAL_GUIDS_NOT_COHERENT")
    if (not same(wall["begCoordinate"]["x"], 50)
            or not same(wall["begCoordinate"]["y"], 40)
            or not same(slab.get("thickness"), .20)):
        raise RuntimeError("SOURCE_GEOMETRY_CHANGED")
    return refs[0]


def wall(a, b, floor, material_guid):
    return {
        "begCoordinate": a, "endCoordinate": b,
        "floorIndex": floor, "zCoordinate": 0.0,
        "height": STORY_H, "thickness": WALL_T, "offset": 0.0,
        "arcAngle": 0.0, "referenceLineLocation": "Center",
        "structureType": "Basic",
        "buildingMaterialId": {"guid": material_guid},
    }


def rectangle():
    return [xy(X0, Y0), xy(X1, Y0), xy(X1, Y1), xy(X0, Y1)]


def make_plan(material_guid):
    ops = []
    inset = WALL_T / 2
    for floor in (0, 1):
        corners = [
            xy(X0 + inset, Y0 + inset),
            xy(X1 - inset, Y0 + inset),
            xy(X1 - inset, Y1 - inset),
            xy(X0 + inset, Y1 - inset),
        ]
        paths = [(corners[i], corners[(i+1) % 4], side)
                 for i, side in enumerate(("south", "east", "north", "west"))]
        paths.append((
            xy(XC, Y0+inset), xy(XC, Y1-inset), "center",
        ))
        for a, b, name in paths:
            ops.append({
                "id": f"wall{floor}-{name}", "type": "Wall", "floor": floor,
                "command": "CreateWalls",
                "params": {"wallsData": [wall(a, b, floor, material_guid)]},
            })
        # CreateSlabs takes ABSOLUTE Z even with floorIndex (confirmed by
        # prior APA S02 repair). Native defaults may inherit Composite;
        # we journal an explicit ModifySlabs to enforce Basic below.
        slab = {
            "level": floor * STORY_H, "floorIndex": floor,
            "thickness": SLAB_T, "referencePlaneLocation": "Top",
            "polygonCoordinates": rectangle(),
        }
        ops.append({
            "id": f"slab{floor}", "type": "Slab", "floor": floor,
            "command": "CreateSlabs", "params": {"slabsData": [slab]},
        })

    roofs = (
        ("west", [xy(X0, Y0), xy(XC, Y0), xy(XC, Y1), xy(X0, Y1)],
         xy(X0, Y1), xy(X0, Y0)),
        ("east", [xy(XC, Y0), xy(X1, Y0), xy(X1, Y1), xy(XC, Y1)],
         xy(X1, Y0), xy(X1, Y1)),
    )
    for name, polygon, pivot_a, pivot_b in roofs:
        data = {
            "level": 6.0, "floorIndex": 2, "thickness": ROOF_T,
            "polygonCoordinates": polygon,
            "pivotLine": {"begCoordinate": pivot_a, "endCoordinate": pivot_b},
            "angle": PITCH, "structureType": "Basic",
            "buildingMaterialId": {"guid": material_guid},
        }
        ops.append({
            "id": f"roof-{name}", "type": "Roof", "floor": 2,
            "command": "CreateRoofs", "params": {"roofsData": [data]},
        })
    if Counter(x["type"] for x in ops) != {
            "Wall": 10, "Slab": 2, "Roof": 2}:
        raise AssertionError("BAD_HOUSE_PLAN")
    return ops


def aabb_overlap(box, envelope=ENVELOPE):
    x0, x1, y0, y1, z0, z1 = envelope
    return (box["xMax"] >= x0 and box["xMin"] <= x1
            and box["yMax"] >= y0 and box["yMin"] <= y1
            and box["zMax"] >= z0 and box["zMin"] <= z1)


def check_native_clearance(native):
    """Test actual supplied native 3D body vertices, not invalid +/-1e35 AABBs."""
    if not isinstance(native.get("bodies"), list) or not native["bodies"]:
        raise RuntimeError("NATIVE_BREP_NOT_AVAILABLE")
    counted = 0
    for body in native["bodies"]:
        pts = body.get("vertices", [])
        if not pts:
            continue  # Some zero-body owner slots have no geometry.
        if not all(
            isinstance(p, dict) and all(
                isinstance(p.get(axis), (float, int))
                and math.isfinite(p[axis]) and abs(p[axis]) < 1e30
                for axis in "xyz"
            ) for p in pts
        ):
            raise RuntimeError("UNVERIFIABLE_NATIVE_BODY_VERTICES")
        bounds = {
            "xMin": min(p["x"] for p in pts), "xMax": max(p["x"] for p in pts),
            "yMin": min(p["y"] for p in pts), "yMax": max(p["y"] for p in pts),
            "zMin": min(p["z"] for p in pts), "zMax": max(p["z"] for p in pts),
        }
        if aabb_overlap(bounds):
            raise RuntimeError("NEW_HOUSE_SITE_INTERSECTS_NATIVE_BODY")
        counted += 1
    if counted == 0:
        raise RuntimeError("NATIVE_DUMP_CONTAINS_NO_USABLE_BODIES")
    return counted


def polygon_match(actual, expected):
    """Allow Archicad's closed final point and cyclic/reversed reordering."""
    if not isinstance(actual, list):
        return False
    points = [(p.get("x"), p.get("y")) for p in actual if isinstance(p, dict)]
    if len(points) != len(actual):
        return False
    if len(points) == 5 and all(same(a, b) for a, b in zip(points[0], points[-1])):
        points.pop()
    return len(points) == len(expected) and all(
        sum(all(same(a, b) for a, b in zip(p, (q["x"], q["y"])))
            for p in points) == 1 for q in expected
    )


def verify_element(api, operation, guid, material_guid):
    kind, floor = operation["type"], operation["floor"]
    data = next(iter(operation["params"].values()))[0]
    row = details(api, guid)
    if row.get("type") != kind or row.get("floorIndex") != floor:
        raise RuntimeError(f"NEW_ELEMENT_TYPE_STORY_MISMATCH: {operation['id']}")
    d = row.get("details")
    if not isinstance(d, dict):
        raise RuntimeError("NEW_TYPED_DETAILS_MISSING")
    if d.get("structureType") != "Basic":
        raise RuntimeError(f"NEW_ELEMENT_NOT_NATIVE_BASIC: {operation['id']}")
    if d.get("buildingMaterialId", {}).get("guid", "").lower() != material_guid:
        raise RuntimeError(f"NEW_ELEMENT_MATERIAL_MISMATCH: {operation['id']}")
    if kind == "Wall":
        for k in ("begCoordinate", "endCoordinate"):
            for dim in ("x", "y"):
                if not same(d.get(k, {}).get(dim), data[k][dim]):
                    raise RuntimeError("WALL_XY_READBACK_MISMATCH")
        if not (same(d.get("height"), STORY_H)
                and same(d.get("begThickness"), WALL_T)
                and same(d.get("endThickness"), WALL_T)
                and same(d.get("zCoordinate"), floor * STORY_H)):
            raise RuntimeError("WALL_DIMENSION_READBACK_MISMATCH")
    elif kind == "Slab":
        if not (same(d.get("thickness"), SLAB_T)
                and same(d.get("zCoordinate"), floor * STORY_H)
                and d.get("referencePlaneLocation") == "Top"
                and polygon_match(d.get("polygonOutline"), data["polygonCoordinates"])):
            raise RuntimeError("SLAB_GEOMETRY_READBACK_MISMATCH")
    elif kind == "Roof":
        if not (d.get("roofClass") == "SinglePlane"
                and same(d.get("thickness"), ROOF_T)
                and same(d.get("angle"), PITCH)
                and same(d.get("zCoordinate"), 6.0)
                and polygon_match(d.get("polygonOutline"), data["polygonCoordinates"])):
            raise RuntimeError("ROOF_GEOMETRY_READBACK_MISMATCH")
        pivot = d.get("pivotLine", {})
        for api_key, expected_key in (("begin", "begCoordinate"),
                                       ("end", "endCoordinate")):
            for axis in ("x", "y"):
                if not same(pivot.get(api_key, {}).get(axis),
                            data["pivotLine"][expected_key][axis]):
                    raise RuntimeError("ROOF_PIVOT_READBACK_MISMATCH")
    result = api("Get3DBoundingBoxes", {
        "elements": [{"elementId": {"guid": guid}}],
    })
    items = result.get("boundingBoxes3D")
    if not isinstance(items, list) or len(items) != 1:
        raise RuntimeError("NEW_ELEMENT_BBOX_COUNT_MISMATCH")
    b = items[0].get("boundingBox3D")
    if not isinstance(b, dict) or not all(
        type(b.get(key)) in (int, float) and math.isfinite(b[key])
        and abs(b[key]) < 1e30 for key in (
            "xMin", "xMax", "yMin", "yMax", "zMin", "zMax"
        )):
        raise RuntimeError("NEW_ELEMENT_BBOX_INVALID")
    if (b["xMin"] < X0 - TOL or b["xMax"] > X1 + TOL
            or b["yMin"] < Y0 - TOL or b["yMax"] > Y1 + TOL
            or b["zMin"] < -SLAB_T - TOL or b["zMax"] > 9.85):
        raise RuntimeError("NEW_ELEMENT_OUT_OF_SITE_ENVELOPE")
    return b


def prepare(api):
    R.assert_project(api)
    version = api("GetAddOnVersion", {}).get("version")
    if version != R.EXPECTED_VERSION:
        raise RuntimeError("WRONG_TAPIR_VERSION: " + repr(version))
    stories = api("GetStories", {}).get("stories")
    if not isinstance(stories, list):
        raise RuntimeError("NO_NATIVE_STORIES")
    for index, expected in ((0, 0.0), (1, 3.0), (2, 6.0)):
        if sum(x.get("index") == index and same(x.get("level"), expected)
               for x in stories) != 1:
            raise RuntimeError(f"STORY_LEVEL_MISMATCH: {index}")
    baseline = R.inventory(api)
    if len(baseline) != 107:
        raise RuntimeError(f"MODEL_COUNT_CHANGED_SINCE_SNAPSHOT: {len(baseline)} != 107")
    for guid in (OLD_WALL, OLD_SLAB, OLD_ROOF):
        if guid not in baseline:
            raise RuntimeError("BASELINE_SOURCE_GUID_MISSING: " + guid)
    material = src_material(api)
    native = api("GetModelDumpV1", {}, timeout=600)
    bodies = check_native_clearance(native)
    if R.inventory(api) != baseline:
        raise RuntimeError("MODEL_CHANGED_DURING_PREPARE")
    R.assert_project(api)
    return {"baseline": baseline, "material_guid": material,
            "existing_native_bodies_inspected": bodies,
            "operations": make_plan(material)}


def write_json(path, payload):
    path.write_text(json.dumps(
        payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def execute(api, *, out_dir, source_pln):
    """A single permanent journal; if an outcome is unknown, never replay."""
    if source_pln != R.EXPECTED_PATH:
        raise RuntimeError("SOURCE_PLN_PATH_NOT_THE_APPROVED_TATARSTAN_PROJECT")
    marker = out_dir / "write_started.json"
    if marker.exists():
        raise RuntimeError("ALREADY_ATTEMPTED_S03_DO_NOT_REPLAY")
    plan = prepare(api)
    out_dir.mkdir(parents=True, exist_ok=True)
    plan_path = out_dir / "plan.json"
    write_json(plan_path, {
        "project": source_pln,
        "material_guid": plan["material_guid"],
        "before_guids": plan["baseline"],
        "existing_bodies_inspected": plan["existing_native_bodies_inspected"],
        "operations": plan["operations"], "status": "PREPARED",
    })
    if not Path(source_pln).is_file():
        raise RuntimeError("SAVED_PLN_NOT_PRESENT")
    backup = out_dir / "before_S03.pln"
    if backup.exists():
        raise RuntimeError("BACKUP_PATH_ALREADY_EXISTS; DO_NOT_OVERWRITE")
    shutil.copy2(source_pln, backup)
    if backup.stat().st_size != Path(source_pln).stat().st_size:
        raise RuntimeError("PLN_BACKUP_SIZE_MISMATCH")
    if R.inventory(api) != plan["baseline"]:
        raise RuntimeError("MODEL_CHANGED_BEFORE_BUILD")
    R.assert_project(api)

    # File is created atomically and exclusively; no automatic retries.
    with marker.open("x", encoding="utf-8") as f:
        json.dump({"status": "WRITE_STARTED_NO_REPLAY", "created_utc":
                   datetime.now(timezone.utc).isoformat(),
                   "project": source_pln, "run_id": uuid.uuid4().hex}, f)
    log = out_dir / "operations.jsonl"
    expected = list(plan["baseline"])
    made = []
    def journal(item):
        with log.open("a", encoding="utf-8") as f:
            f.write(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n")
            f.flush()
            os.fsync(f.fileno())
    try:
        for op in plan["operations"]:
            R.assert_project(api)
            if R.inventory(api) != sorted(expected):
                raise RuntimeError("MODEL_INVENTORY_CHANGED_OUTSIDE_WRITER")
            journal({"op": op["id"], "command": op["command"], "state": "SENT"})
            result = api(op["command"], op["params"])
            rows = result.get("elements")
            if (not isinstance(rows, list) or len(rows) != 1
                    or not isinstance(rows[0], dict)):
                raise RuntimeError("CREATE_RESPONSE_UNVERIFIED: " + op["id"])
            guid = rows[0].get("elementId", {}).get("guid", "").lower()
            if not R.GUID_PATTERN.fullmatch(guid) or guid in expected:
                raise RuntimeError("CREATE_GUID_INVALID_OR_DUPLICATE: " + op["id"])
            expected.append(guid)
            journal({"op": op["id"], "state": "CREATED_UNVERIFIED", "guid": guid})
            if op["type"] == "Slab":
                # Pin Basic type, absolute z and real structural material.
                # Native CreateSlabs may inherit a Composite default and
                # ignore the requested thickness before ModifySlabs.
                journal({"op": op["id"], "state": "MODIFY_SLAB_SENT", "guid": guid})
                result = api("ModifySlabs", {
                    "slabsWithDetails": [{
                        "elementId": {"guid": guid}, "zCoordinate": op["floor"] * STORY_H,
                        "thickness": SLAB_T, "structureType": "Basic",
                        "buildingMaterialId": {"guid": plan["material_guid"]},
                        "referencePlaneLocation": "Top",
                    }],
                })
                assert_modify_success(result)
                journal({"op": op["id"], "state": "SLAB_FIXED", "guid": guid})
            bbox = verify_element(api, op, guid, plan["material_guid"])
            journal({"op": op["id"], "state": "PASS_TYPED_GEOMETRY",
                     "guid": guid, "bbox": bbox})
            made.append({"op": op["id"], "type": op["type"],
                         "guid": guid, "story": op["floor"]})
            print(f"PASS {op['id']}: {guid}", flush=True)

        final = R.inventory(api)
        if final != sorted(expected) or len(made) != 14 or len(final) != 121:
            raise RuntimeError("FINAL_GUID_INVENTORY_MISMATCH")
        R.assert_project(api)
        # Verify no new actual body occupies the old building.
        post = api("GetModelDumpV1", {}, timeout=600)
        bodies = post.get("bodies")
        if not isinstance(bodies, list) or not bodies:
            raise RuntimeError("AFTER_DUMP_UNAVAILABLE")
        new_set = {item["guid"] for item in made}
        parent_set = {str(b.get("parentGuid", "")).lower() for b in bodies}
        missing = new_set - parent_set
        if missing:
            raise RuntimeError("NEW_NATIVE_BODIES_MISSING: " + repr(sorted(missing)))
        # The old set is retained as GUID identities and remains geographically
        # separate; this is not a construction/fastener/structural audit.
        journal({"state": "BEFORE_SAVE_VALIDATED", "new_guid_count": len(made)})
        save_result = api("SaveProject", {})
        assert_response_success(save_result, "SaveProject")
        R.assert_project(api)
        if R.inventory(api) != sorted(expected):
            raise RuntimeError("AFTER_SAVE_GUID_INVENTORY_MISMATCH")
        journal({"state": "SAVED_AND_READBACK_PASS", "guid_count": len(final)})
        write_json(out_dir / "created.json", {
            "status": "SAVED_AND_READBACK_PASS",
            "baseline_guids_preserved": len(plan["baseline"]),
            "new_elements": made,
            "new_guid_count": len(made),
            "native_body_ownership_check": "PARENT_GUID_PRESENT",
            "geometry_scope": "TYPED_READBACK_AND_NATIVE_BODIES; NOT_ENGINEERED",
            "no_morph": True,
        })
        print("SUCCESS: BUILT AND SAVED 10 Wall + 2 Slab + 2 Roof")
        print("BEFORE GUIDS:", len(plan["baseline"]), "AFTER GUIDS:", len(final))
        print("OLD BUILDING: PRESERVED; NEW HOUSE: X112..122 Y39..51")
        print("EVIDENCE:", out_dir)
    except Exception:
        journal({"state": "PARTIAL_OR_UNKNOWN_OUTCOME_NO_REPLAY"})
        print("STOP: POSSIBLE PARTIAL MODEL. DO NOT RUN AGAIN.", file=sys.stderr)
        print("EVIDENCE:", out_dir, file=sys.stderr)
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", action="store_true",
                        help="explicitly authorize ONE native build and save")
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--out-dir", type=Path,
                        default=Path.home() / "Desktop" / "APA_Tatarstan_House_S03")
    args = parser.parse_args(argv)
    if args.port != PORT:
        parser.error("This scene is pinned to the confirmed port 19724")
    api = api_factory(args.port)
    if not args.build:
        plan = prepare(api)
        print("READ ONLY PLAN:", Counter(x["type"] for x in plan["operations"]))
        print("ORIGINAL GUIDS:", len(plan["baseline"]))
        print("NATIVE BODIES CHECKED:", plan["existing_native_bodies_inspected"])
        print("NO WRITE. Use --build to construct on the approved PLN.")
        return 0
    execute(api, out_dir=args.out_dir, source_pln=R.EXPECTED_PATH)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print("APA_HOUSE_STOPPED:", str(exc), file=sys.stderr)
        sys.exit(1)
