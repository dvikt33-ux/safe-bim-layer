"""TRC-SAD geometry -> existing APA BIM Graph; strictly OFFLINE / zero native writes.

The design is a coordinated shell/atrium and program-area preview, NOT room walls,
stair engineering, shelter approval, native Fill/Zone or a construction drawing.
Do not route this output to SceneWriter until separate story/material/load/
evacuation/opening gates are implemented and expressly approved.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path

import archicad_bim_graph as GRAPH
import archicad_building_shell as BUILD
import archicad_scene_run as RUN

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SPEC = ROOT / "data" / "trc_sad_concept_v1.json"
EXPECTED_SHELL = ((0, 21), (42, 0), (142.8, 0), (184.8, 21),
                  (184.8, 142.8), (0, 142.8))
EXPECTED_ATRIUM = ((79.8, 37.8), (105, 37.8), (113.4, 50.4),
                   (113.4, 75.6), (105, 88.2), (79.8, 88.2),
                   (71.4, 75.6), (71.4, 50.4))
ABOVE_STORIES = ("1", "2", "3")
BLOCKERS = (
    "Basement area and separate exits not designed; no basement native operations",
    "No accepted structural load path, support grid or slab material selected",
    "Core footprints are RESERVED only: no real stairs, doors or fire compartments",
    "Main entrance gap is conceptual; glazed wall/doors not authored",
    "No verified protected corridor, smoke management or shelter access",
    "Fill, Zone, annotation and dimension native writers not accepted in APA",
    "No BIM/PLN execution authority, no automatic save, no project switching",
)


def _num(v, name):
    if type(v) not in (float, int) or not math.isfinite(v):
        raise ValueError("NONFINITE_" + name)
    return float(v)


def polygon_area(points):
    pts = [(float(x), float(y)) for x, y in points]
    if len(pts) < 3:
        raise ValueError("DEGENERATE_POLYGON")
    return sum(x * pts[(i + 1) % len(pts)][1]
               - pts[(i + 1) % len(pts)][0] * y
               for i, (x, y) in enumerate(pts)) / 2


def _v(a):
    return tuple((_num(a[0], "X"), _num(a[1], "Y")))


def _ring(value, expected, name):
    if not isinstance(value, list) or tuple(map(_v, value)) != tuple(map(_v, expected)):
        raise ValueError("UNAPPROVED_" + name + "_GEOMETRY")
    if polygon_area(value) <= 0:
        raise ValueError("NON_CCW_" + name)
    return [tuple(map(float, p)) for p in value]


def slab_regions(shell, atrium, floor):
    """Known four-part, nonoverlapping decomposition of the octagonal atrium.

    No fictitious hole syntax is passed to the installed CreateSlabs contract.
    1st-floor slab is whole; 2nd/3rd floor slabs have an actual open void.
    """
    if floor == "1":
        return [shell]
    return [
        [(0, 21), (42, 0), (142.8, 0), (184.8, 21),
         (184.8, 37.8), (0, 37.8)],
        [(0, 37.8), (79.8, 37.8), (71.4, 50.4),
         (71.4, 75.6), (79.8, 88.2), (0, 88.2)],
        [(105, 37.8), (184.8, 37.8), (184.8, 88.2),
         (105, 88.2), (113.4, 75.6), (113.4, 50.4)],
        [(0, 88.2), (184.8, 88.2),
         (184.8, 142.8), (0, 142.8)],
    ]


def _cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


def inset_axes(shell, half_thickness):
    """Return reference-line corners inside the exterior bounding polygon."""
    lines = []
    for i, a in enumerate(shell):
        b = shell[(i + 1) % len(shell)]
        delta = (b[0] - a[0], b[1] - a[1])
        norm = math.hypot(*delta)
        if norm < 0.01:
            raise ValueError("TOO_SHORT_SHELL_EDGE")
        normal = (-delta[1] / norm, delta[0] / norm)
        lines.append(((a[0] + half_thickness * normal[0],
                       a[1] + half_thickness * normal[1]), delta))
    axes = []
    for i in range(len(shell)):
        prev, r = lines[(i - 1) % len(lines)]
        curr, s = lines[i]
        divisor = _cross(r, s)
        if abs(divisor) < 1e-9:
            raise ValueError("OFFSET_AXES_PARALLEL")
        diff = (curr[0] - prev[0], curr[1] - prev[1])
        t = _cross(diff, s) / divisor
        axes.append((round(prev[0] + r[0] * t, 6),
                     round(prev[1] + r[1] * t, 6)))
    return axes


def validate_spec(spec):
    if not isinstance(spec, dict) or spec.get("schemaVersion") != "trc-sad-plan/1":
        raise ValueError("TRC_SAD_SCHEMA_REQUIRED")
    if spec.get("unit") != "m" or spec.get("projectId") != "trc-sad":
        raise ValueError("TRC_SAD_UNIT_OR_PROJECT_MISMATCH")
    shell = _ring(spec.get("shell"), EXPECTED_SHELL, "SHELL")
    atrium = _ring(spec.get("atrium"), EXPECTED_ATRIUM, "ATRIUM")
    floors = spec.get("floors")
    if not isinstance(floors, list) or [r.get("id") for r in floors] != ["-1", "1", "2", "3"]:
        raise ValueError("FOUR_FIXED_STORY_LABELS_REQUIRED")
    z = [-4.5, 0.0, 6.3, 12.6]
    height = [None, 6.3, 6.3, 5.4]
    for i, floor in enumerate(floors):
        if abs(_num(floor.get("elevation"), "Z") - z[i]) > 1e-7:
            raise ValueError("STORY_LEVEL_MISMATCH")
        if i and abs(_num(floor.get("height"), "H") - height[i]) > 1e-7:
            raise ValueError("STORY_HEIGHT_MISMATCH")
    if floors[0].get("status") != "BASEMENT_EXTENT_UNRESOLVED":
        raise ValueError("BASEMENT_FOOTPRINT_HAS_NOT_BEEN_ACCEPTED")
    wall_t = _num(spec.get("exteriorWallThickness"), "WALL_T")
    slab_t = _num(spec.get("slabThickness"), "SLAB_T")
    if wall_t != 0.3 or slab_t != 0.22:
        raise ValueError("STRUCTURAL_PREVIEW_THICKNESS_CHANGED")
    if spec.get("entranceClearGap") != [79.8, 105.0]:
        raise ValueError("ENTRANCE_GAP_CHANGED")
    cores = spec.get("reservedCores", [])
    if (not isinstance(cores, list) or [c.get("id") for c in cores]
            != ["REAR_L", "REAR_R", "FRONT_L", "FRONT_R"]):
        raise ValueError("COORDINATED_CORE_RESERVES_REQUIRED")
    for c in cores:
        if not isinstance(c.get("rect"), list) or len(c["rect"]) != 4:
            raise ValueError("INVALID_CORE_FOOTPRINT")
    programs = spec.get("program")
    if not isinstance(programs, list):
        raise ValueError("PROGRAM_LIST_REQUIRED")
    ids = set()
    for p in programs:
        if (not isinstance(p, dict) or p.get("floor") not in ABOVE_STORIES
                or not isinstance(p.get("id"), str) or p["id"] in ids):
            raise ValueError("DUPLICATE_OR_UNKNOWN_PROGRAM_ZONE")
        ids.add(p["id"])
        rect = p.get("rect")
        if not isinstance(rect, list) or len(rect) != 4:
            raise ValueError("INVALID_FUNCTION_RECT")
        x0, y0, x1, y1 = [_num(v, "ZONE") for v in rect]
        if not (0 <= x0 < x1 <= 184.8 and 0 <= y0 < y1 <= 142.8):
            raise ValueError("PROGRAM_OUTSIDE_BUILDING_BOUNDS")
    areas = {}
    gross = polygon_area(shell)
    hole = polygon_area(atrium)
    for sid in ABOVE_STORIES:
        regions = slab_regions(shell, atrium, sid)
        actual = sum(polygon_area(r) for r in regions)
        expected = gross if sid == "1" else gross - hole
        if any(polygon_area(r) <= 0 for r in regions) or abs(actual - expected) > 1e-6:
            raise ValueError("SLAB_REGION_AREA_MISMATCH_" + sid)
        areas[sid] = round(actual, 6)
    if abs(gross - 25507.44) > 1e-6 or abs(hole - 1905.12) > 1e-6:
        raise ValueError("PREVIOUS_PLAN_GEOMETRY_RECONCILIATION_FAILED")
    return shell, atrium, areas


def _binding(stories):
    """An external actual GetStories mapping is required even for offline DAG.

    Supplying a mapping is NOT a native readback, write approval or PLN identity.
    """
    if stories is None:
        return None
    if not isinstance(stories, dict) or set(stories) != set(ABOVE_STORIES):
        raise ValueError("EXACT_NATIVE_STORY_BINDINGS_REQUIRED")
    mapped = {}
    expected = {"1": 0.0, "2": 6.3, "3": 12.6}
    for sid in ABOVE_STORIES:
        row = stories[sid]
        if not isinstance(row, dict) or set(row) != {"nativeIndex", "elevation"}:
            raise ValueError("NATIVE_STORY_BINDING_FIELDS")
        index = row["nativeIndex"]
        if type(index) is not int or abs(index) > 100:
            raise ValueError("INVALID_NATIVE_STORY_INDEX")
        if abs(_num(row["elevation"], "STORY_Z") - expected[sid]) > 1e-6:
            raise ValueError("NATIVE_STORY_ELEVATION_MISMATCH")
        mapped[sid] = index
    if len(set(mapped.values())) != 3:
        raise ValueError("DUPLICATE_NATIVE_STORY_INDEX")
    return mapped


def prepare(spec, native_story_bindings=None, schema_path=None):
    """Pure offline preview. Never call SceneWriter or Archicad transport."""
    shell, atrium, floor_areas = validate_spec(spec)
    mapped = _binding(native_story_bindings)
    zones = [dict(id=p["id"], floor=p["floor"], label=p["label"],
                  reservedAreaSquareMeters=round(
                      (p["rect"][2] - p["rect"][0]) *
                      (p["rect"][3] - p["rect"][1]), 4),
                  polygon=[[p["rect"][0], p["rect"][1]],
                           [p["rect"][2], p["rect"][1]],
                           [p["rect"][2], p["rect"][3]],
                           [p["rect"][0], p["rect"][3]]],
                  status="UNVERIFIED_PROGRAM_RESERVATION_NOT_NATIVE_ZONE")
             for p in spec["program"]]
    result = {
        "status": "GEOMETRY_PREVIEW_OFFLINE",
        "geometrySource": "data/trc_sad_concept_v1.json",
        "modelRevision": hashlib.sha256(
            json.dumps(spec, sort_keys=True, ensure_ascii=False,
                       separators=(",", ":")).encode("utf8")).hexdigest(),
        "dimensionsMeters": {"x": 184.8, "y": 142.8},
        "shellGrossSquareMeters": 25507.44,
        "atriumVoidSquareMeters": 1905.12,
        "floorSlabAreasSquareMeters": floor_areas,
        "aboveGroundSlabAreaSquareMeters": round(sum(floor_areas.values()), 4),
        "basementAreaSquareMeters": None,
        "reservedCores": copy.deepcopy(spec["reservedCores"]),
        "programReservations": zones,
        "nativeGraph": None,
        "blockingConditions": list(BLOCKERS),
        "normativeApproval": "NOT_VERIFIED",
        "nativeWrites": 0,
        "liveWriteAuthorized": False,
        "plnChanged": False,
    }
    if mapped is None:
        result["nativeGraphStatus"] = "BLOCKED_MISSING_VERIFIED_GETSTORIES_BINDINGS"
        return result

    axes = inset_axes(shell, .15)
    operations = []
    for sid in ABOVE_STORIES:
        idx = mapped[sid]
        h = next(s["height"] for s in spec["floors"] if s["id"] == sid)
        for i, a in enumerate(axes):
            b = axes[(i + 1) % len(axes)]
            segments = [(a, b)]
            if i == 1:  # South entrance: 25.2 m gap, not a 25.2 m Door
                segments = [(a, (79.8, a[1])), ((105., a[1]), b)]
            for j, (start, end) in enumerate(segments):
                step_id = "trc-s" + sid + "-w" + str(i) + "-" + str(j)
                operations.append(BUILD.step(
                    step_id, "CreateWalls",
                    BUILD.wall(BUILD.xy(*start), BUILD.xy(*end),
                               idx, float(h), .30)))
        for i, shape in enumerate(slab_regions(shell, atrium, sid)):
            operations.append(BUILD.step(
                "trc-s" + sid + "-slab-" + str(i), "CreateSlabs",
                {"level": next(x["elevation"] for x in spec["floors"] if x["id"] == sid),
                 "floorIndex": idx, "thickness": .22,
                 "referencePlaneLocation": "Top",
                 "polygonCoordinates": [BUILD.xy(*p) for p in shape]}))
    if len(operations) > GRAPH.CONTRACTS.MAX_REQUESTS:
        raise ValueError("EXISTING_BIM_GRAPH_OPERATION_LIMIT")
    catalog = GRAPH.CONTRACTS.load_catalog(Path(schema_path or RUN.DEFAULT_SCENE_SCHEMA))
    check = GRAPH.compile_graph(catalog, {"operations": operations},
                                runtime_version=RUN.EXPECTED_TAPIR)
    if check["status"] != "PLAN_VALIDATED_OFFLINE":
        raise ValueError("EXISTING_APA_GRAPH_REJECTED: " +
                         json.dumps([r for r in check["operations"]
                                     if r["status"] == "INVALID"][:3]))
    result.update(
        status="NATIVE_DAG_PREVIEW_OFFLINE_NOT_AUTHORIZED",
        nativeGraphStatus="SCHEMA_VALID_NOT_EXECUTION_AUTHORIZED",
        nativeGraph={"operations": operations},
        sourcePlanHash=check["sourcePlanHash"],
        executionOrder=check["executionOrder"],
        nativeCommandCount=len(operations),
        nativeKinds={"Wall": 24, "Slab": 9},
    )
    if len(operations) != 33:
        raise ValueError("UNEXPECTED_OPERATION_CARDINALITY")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, default=DEFAULT_SPEC)
    parser.add_argument("--stories", type=Path,
                        help="JSON mapping read from actual GetStories; optional")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("OUTPUT_MUST_BE_NEW")
    spec = json.loads(args.spec.read_text(encoding="utf8"))
    stories = json.loads(args.stories.read_text(encoding="utf8")) if args.stories else None
    preview = prepare(spec, stories)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(preview, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf8")
    print(preview["status"], "nativeWrites=0")


if __name__ == "__main__":
    main()
