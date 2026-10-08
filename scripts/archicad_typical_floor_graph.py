"""Parametric single-storey BIM floor plan. OFFLINE ONLY: no Archicad writes.

Uses the existing pavilion operation shapes and BIM graph compiler, rather
than a second geometry writer. Stair/lift/MEP/Zone nodes remain semantic
placeholders until a native recipe has been verified for each kind.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import sys

import archicad_scene_v1 as SCENE

GRAPH = SCENE.GRAPH
SUPPORTED = frozenset(("CreateWalls", "CreateSlabs", "CreateColumns",
                       "CreateWindows", "CreateDoors"))


@dataclass(frozen=True)
class FloorParameters:
    anchor_x: float = 200.0
    anchor_y: float = 200.0
    length: float = 36.0
    depth: float = 18.0
    height: float = 3.0
    bays: int = 6
    corridor_width: float = 2.4
    outer_wall: float = 0.30
    inner_wall: float = 0.15
    slab_thickness: float = 0.20
    column_size: float = 0.30
    door_width: float = 0.90
    door_height: float = 2.10
    window_width: float = 1.20
    window_height: float = 1.20
    window_sill: float = 0.90
    story_index: int = 0
    story_level: float = 0.0

    def validate(self):
        numbers = vars(self)
        for name, val in numbers.items():
            if name in ("bays", "story_index"):
                if type(val) is not int:
                    raise ValueError(name + " must be an integer")
            elif type(val) not in (int, float) or not math.isfinite(val):
                raise ValueError(name + " must be finite numeric")
        if self.story_index != 0 or self.story_level != 0:
            raise ValueError("UNSUPPORTED_STORY: this offline recipe is pinned to first story (API index 0)")
        if not 2 <= self.bays <= 20:
            raise ValueError("bays must be 2..20")
        if (self.length <= 0 or self.depth <= 0 or self.height <= 0
                or self.outer_wall <= 0 or self.inner_wall <= 0
                or self.slab_thickness <= 0 or self.column_size <= 0):
            raise ValueError("all geometric dimensions must be positive")
        if (self.length / self.bays < 4.5
                or self.depth < self.corridor_width + 2 * (self.outer_wall + self.inner_wall + 2.5)
                or self.corridor_width <= self.inner_wall + 1.3):
            raise ValueError("floor bays, rooms or clear corridor too small")
        if not (0 < self.door_width < self.length/self.bays - 2*self.inner_wall
                and 0 < self.door_height <= self.height
                and 0 < self.window_width < 0.3 * (self.length/self.bays - self.outer_wall)
                and 0 < self.window_height
                and 0 <= self.window_sill
                and self.window_sill + self.window_height <= self.height):
            raise ValueError("opening geometry invalid or conflicts with the module")
        if max(abs(self.anchor_x), abs(self.anchor_y)) > 100000:
            raise ValueError("anchor outside approved offline coordinate range")


def _xy(x, y):
    return SCENE.xy(x, y)


def _wall(p: FloorParameters, x0, y0, x1, y1, thickness):
    if math.hypot(x1-x0, y1-y0) < 0.2:
        raise ValueError("zero/short wall")
    return {
        "begCoordinate": _xy(x0, y0),
        "endCoordinate": _xy(x1, y1),
        "floorIndex": p.story_index,
        "zCoordinate": p.story_level,
        "height": p.height, "thickness": thickness,
        "offset": 0.0, "arcAngle": 0.0,
        "referenceLineLocation": "Center", "structureType": "Basic",
    }


def graph_and_semantics(p: FloorParameters):
    p.validate()
    x, y, length, depth = p.anchor_x, p.anchor_y, p.length, p.depth
    half = p.outer_wall / 2
    bay = length / p.bays
    cuts = [x + i*bay for i in range(p.bays+1)]
    cuts[0], cuts[-1] = x+half, x+length-half
    y_south, y_north = y+half, y+depth-half
    corridor_lo = y + (depth-p.corridor_width)/2
    corridor_hi = corridor_lo + p.corridor_width
    ops = []
    rooms = []
    cores = []

    def add_wall(sid, x0, y0, x1, y1, thick):
        ops.append(SCENE.step(sid, "CreateWalls", "wallsData",
                              _wall(p, x0, y0, x1, y1, thick)))

    # Six module-aligned facade walls per long side. The north reference
    # lines run east -> west, so north window offsets are also measured eastward.
    for i in range(p.bays):
        a, b = cuts[i], cuts[i+1]
        add_wall(f"facade-s-{i+1:02}", a, y_south, b, y_south, p.outer_wall)
        add_wall(f"facade-n-{i+1:02}", b, y_north, a, y_north, p.outer_wall)
        add_wall(f"corridor-s-{i+1:02}", a, corridor_lo, b, corridor_lo, p.inner_wall)
        add_wall(f"corridor-n-{i+1:02}", a, corridor_hi, b, corridor_hi, p.inner_wall)
    add_wall("facade-east", x+length-half, y_south, x+length-half, y_north,
             p.outer_wall)
    add_wall("facade-west", x+half, y_north, x+half, y_south, p.outer_wall)

    for i in range(1, p.bays):
        split = x + i*bay
        add_wall(f"partition-s-{i:02}", split, y+ p.outer_wall,
                 split, corridor_lo, p.inner_wall)
        add_wall(f"partition-n-{i:02}", split, corridor_hi,
                 split, y+depth-p.outer_wall, p.inner_wall)

    # Slab outline uses external wall faces, not wall reference lines.
    ops.append(SCENE.step("floor-slab", "CreateSlabs", "slabsData", {
        "level": p.story_level, "floorIndex": p.story_index,
        "thickness": p.slab_thickness,
        "referencePlaneLocation": "Top",
        "polygonCoordinates": [_xy(x,y), _xy(x+length,y),
                               _xy(x+length,y+depth), _xy(x,y+depth)]
    }))

    # Single grid definition controls all column coordinates.
    grid_x = [x+half] + [x+i*bay for i in range(1, p.bays)] + [x+length-half]
    grid_y = [y+half, y+depth/3, y+2*depth/3, y+depth-half]
    for ci, cx in enumerate(grid_x):
        for ri, cy in enumerate(grid_y):
            ops.append(SCENE.step(f"column-{ci:02}-{ri:02}", "CreateColumns",
                                  "columnsData", {
                "coordinates": {"x": cx, "y": cy, "z": p.story_level},
                "floorIndex": p.story_index, "height": p.height,
                "width": p.column_size, "depth": p.column_size,
                "circleBased": False, "coreAnchor": "Center",
                "isWidthAndHeightLinked": False,
            }))

    for i in range(p.bays):
        facade_s = f"facade-s-{i+1:02}"
        facade_n = f"facade-n-{i+1:02}"
        corridor_s = f"corridor-s-{i+1:02}"
        corridor_n = f"corridor-n-{i+1:02}"
        span = cuts[i+1] - cuts[i]
        for suffix, host in (("s", facade_s), ("n", facade_n)):
            for w_idx, fraction in enumerate((0.30, 0.70), start=1):
                ops.append(SCENE.step(f"window-{suffix}-{i+1:02}-{w_idx}",
                                      "CreateWindows", "windowsData", {
                    **SCENE.host_wall(host),
                    "centerOffset": span*fraction,
                    "sillHeight": p.window_sill,
                    "width": p.window_width, "height": p.window_height,
                }))
        for suffix, host in (("s", corridor_s), ("n", corridor_n)):
            ops.append(SCENE.step(f"door-{suffix}-{i+1:02}",
                                  "CreateDoors", "doorsData", {
                **SCENE.host_wall(host), "centerOffset": span/2,
                "sillHeight": 0.0, "width": p.door_width,
                "height": p.door_height,
            }))
            left = x + i*bay + (p.outer_wall if i == 0 else p.inner_wall/2)
            right = x + (i+1)*bay - (p.outer_wall if i == p.bays-1 else p.inner_wall/2)
            low_y = y+p.outer_wall if suffix == "s" else corridor_hi+p.inner_wall/2
            high_y = corridor_lo-p.inner_wall/2 if suffix == "s" else y+depth-p.outer_wall
            rooms.append({"id": f"room-{suffix}-{i+1:02}",
                          "bboxMeters": [left, low_y, right, high_y],
                          "clearAreaSquareMeters": round((right-left)*(high_y-low_y), 5),
                          "status": "SEMANTIC_ONLY",
                          "nativeZone": "UNSUPPORTED"})

    for core_type, room_id in (
        ("STAIR_CORE", "room-s-01"),
        ("LIFT_CORE", f"room-n-{p.bays:02}"),
        ("MEP_CORE", f"room-n-{p.bays//2+1:02}"),
    ):
        selected = next(room for room in rooms if room["id"] == room_id)
        cores.append({"type": core_type, "roomId": room_id,
                      "bboxMeters": selected["bboxMeters"],
                      "nativeImplementation": "UNSUPPORTED",
                      "note": "Reserved footprint only; not a stair, lift or MEP object"})

    semantic = {
        "rooms": rooms, "cores": cores,
        "corridor": {"bboxMeters": [x+p.outer_wall,
                      corridor_lo+p.inner_wall/2,
                      x+length-p.outer_wall, corridor_hi-p.inner_wall/2],
                     "nativeZone": "UNSUPPORTED"},
        "grid": {"xMeters": grid_x, "yMeters": grid_y},
        "materials": {"externalWalls": "UNSUPPORTED",
                      "internalWalls": "UNSUPPORTED",
                      "slab": "UNSUPPORTED", "columns": "UNSUPPORTED"},
        "physicalJunctionsAndClashes": "NOT_VERIFIED",
    }
    return {"operations": ops}, semantic


def prepare(p: FloorParameters = FloorParameters(), catalog=None):
    graph, semantic = graph_and_semantics(p)
    if catalog is None:
        catalog = GRAPH.CONTRACTS.load_catalog(GRAPH.CONTRACTS.DEFAULT_SCHEMA)
    audit = GRAPH.compile_graph(catalog, graph)
    if audit["status"] != "PLAN_VALIDATED_OFFLINE":
        failures = [r for r in audit["operations"] if r["status"] != "SCHEMA_VALID"]
        raise ValueError("FLOOR_GRAPH_INVALID: " + json.dumps(failures[:5], ensure_ascii=False))
    counts = Counter(op["command"].replace("Create", "")[:-1]
                     for op in graph["operations"])
    return {
        "status": "FLOOR_PREVIEW_OFFLINE",
        "graph": graph, "executionOrder": audit["executionOrder"],
        "sourcePlanHash": audit["sourcePlanHash"],
        "schemaVersion": audit["schemaVersion"],
        "metrics": {"grossFootprintSquareMeters": round(p.length*p.depth, 5),
                    "grossVolumeCubicMeters": round(p.length*p.depth*p.height, 5),
                    "elementCount": len(graph["operations"]),
                    "elementKinds": dict(counts),
                    "roomCount": len(semantic["rooms"]),
                    "bayCount": p.bays, "firstStoryIndexInAPI": 0},
        "semantic": semantic,
        "liveWriteAuthorized": False, "modelChanged": False,
        "nativeOperationsVerified": 0,
        "note": "Offline schema/graph only. Tapir 1.5.8 snapshot; live 1.5.10 differs.",
    }


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--anchor-x", type=float, default=200)
    ap.add_argument("--anchor-y", type=float, default=200)
    ap.add_argument("--length", type=float, default=36)
    ap.add_argument("--depth", type=float, default=18)
    ap.add_argument("--bays", type=int, default=6)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args(argv)
    try:
        p = FloorParameters(anchor_x=args.anchor_x, anchor_y=args.anchor_y,
                            length=args.length, depth=args.depth, bays=args.bays)
        rendered = json.dumps(prepare(p), ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
        print(rendered, end="")
        return 0
    except Exception as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    sys.exit(main())
