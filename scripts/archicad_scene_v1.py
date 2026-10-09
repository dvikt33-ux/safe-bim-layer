"""Single-source geometric BIM scene: 4 m x 3 m test pavilion (12 elements).

Creates a declarative, schema-verifiable GRAPH, not Archicad elements.
All lengths, placements, wall openings, areas and volume are derived from the
same dimensions; NEVER hand-enter inconsistent room-area / volume labels.
The graph can be consumed later by an explicitly guarded native executor.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys

GRAPH_FILE = Path(__file__).with_name("archicad_bim_graph.py")
_S = importlib.util.spec_from_file_location("archicad_bim_graph_scene", GRAPH_FILE)
GRAPH = importlib.util.module_from_spec(_S)
_S.loader.exec_module(GRAPH)

WIDTH = 4.0
DEPTH = 3.0
HEIGHT = 3.0
WALL_THICKNESS = 0.20
SLAB_THICKNESS = 0.20
COLUMN_SIZE = 0.25
WINDOW_WIDTH = 0.80
WINDOW_HEIGHT = 1.20
WINDOW_SILL = 0.90
DOOR_WIDTH = 0.90
DOOR_HEIGHT = 2.10
DOOR_CENTER = 1.40
NORTH_WINDOW_CENTERS = (0.90, 3.10)
SCENE_ELEMENT_COUNT = 12


def xy(x, y):
    return {"x": float(x), "y": float(y)}


def _finite_anchor(x, y):
    if any(type(v) not in (int, float) or not math.isfinite(v)
           or abs(v) > 1_000_000 for v in (x, y)):
        raise ValueError("finite meter coordinates are required")
    return float(x), float(y)


def wall(start, end):
    return {
        "begCoordinate": start, "endCoordinate": end,
        "floorIndex": 0, "zCoordinate": 0.0,
        "height": HEIGHT, "thickness": WALL_THICKNESS,
        "offset": 0.0, "arcAngle": 0.0,
        "referenceLineLocation": "Center", "structureType": "Basic",
    }


def step(sid, command, key, data, *, after=None):
    node = {"id": sid, "command": command, "params": {key: [data]}}
    if after:
        node["after"] = after
    return node


def host_wall(wall_id):
    return {"ownerWallId": {"guid": {"$createdGuid": wall_id}}}


def graph(anchor_x: float, anchor_y: float):
    """12 coordinated elements: 4 walls, slab, 4 columns, 2 windows, door.

    North wall is drawn East->West. Its offsets and the corresponding
    horizontal window positions are therefore measured FROM the east corner.
    """
    x, y = _finite_anchor(anchor_x, anchor_y)
    # The 4 x 3 m dimensions are the EXTERIOR bounding footprint.
    # Wall reference lines are centered one half-thickness in from its edge.
    # Slab remains the actual 4 x 3 m exterior footprint.
    sw, se = xy(x, y), xy(x+WIDTH, y)
    ne, nw = xy(x+WIDTH, y+DEPTH), xy(x, y+DEPTH)
    t = WALL_THICKNESS / 2
    axis_sw, axis_se = xy(x+t, y+t), xy(x+WIDTH-t, y+t)
    axis_ne, axis_nw = xy(x+WIDTH-t, y+DEPTH-t), xy(x+t, y+DEPTH-t)
    data = [
        step("wall-south", "CreateWalls", "wallsData", wall(axis_sw, axis_se)),
        step("wall-east", "CreateWalls", "wallsData", wall(axis_se, axis_ne)),
        step("wall-north", "CreateWalls", "wallsData", wall(axis_ne, axis_nw)),
        step("wall-west", "CreateWalls", "wallsData", wall(axis_nw, axis_sw)),
        step("slab", "CreateSlabs", "slabsData", {
            "level": 0.0, "floorIndex": 0, "thickness": SLAB_THICKNESS,
            "referencePlaneLocation": "Top",
            "polygonCoordinates": [sw, se, ne, nw],
        }),
    ]
    # Interior corner columns; centers are derived from the same origin.
    for name, dx, dy in (
        ("sw", .35, .35), ("se", WIDTH-.35, .35),
        ("ne", WIDTH-.35, DEPTH-.35), ("nw", .35, DEPTH-.35)
    ):
        data.append(step("column-"+name, "CreateColumns", "columnsData", {
            "coordinates": {"x": x+dx, "y": y+dy, "z": 0.0},
            "floorIndex": 0, "height": HEIGHT,
            "width": COLUMN_SIZE, "depth": COLUMN_SIZE,
            "circleBased": False, "coreAnchor": "Center",
            "isWidthAndHeightLinked": False,
        }))
    data.append(step("door-south", "CreateDoors", "doorsData", {
        **host_wall("wall-south"), "centerOffset": DOOR_CENTER,
        "sillHeight": 0.0, "width": DOOR_WIDTH, "height": DOOR_HEIGHT,
    }))
    for i, center in enumerate(NORTH_WINDOW_CENTERS, 1):
        data.append(step(f"window-north-{i}", "CreateWindows", "windowsData", {
            **host_wall("wall-north"), "centerOffset": center,
            "sillHeight": WINDOW_SILL,
            "width": WINDOW_WIDTH, "height": WINDOW_HEIGHT,
        }))
    assert len(data) == SCENE_ELEMENT_COUNT
    return {"operations": data}


def metrics():
    gross_floor_area = WIDTH*DEPTH  # exact exterior wall-face footprint
    clear_floor_area = (WIDTH-2*WALL_THICKNESS)*(DEPTH-2*WALL_THICKNESS)
    gross_wall_area = 2*(WIDTH+DEPTH)*HEIGHT
    opening_area = DOOR_WIDTH*DOOR_HEIGHT + 2*WINDOW_WIDTH*WINDOW_HEIGHT
    return {
        "dimensionsMeters": {"width": WIDTH, "depth": DEPTH, "height": HEIGHT},
        "slabTopElevationMeters": 0.0,
        "firstStoryIndexInAPI": 0,
        "grossFootprintSquareMeters": round(gross_floor_area, 6),
        "interiorClearAreaSquareMeters": round(clear_floor_area, 6),
        "wallReferenceLineLengthsMeters": {"long": WIDTH-WALL_THICKNESS,
                                           "short": DEPTH-WALL_THICKNESS},
        "perimeterMeters": 2*(WIDTH+DEPTH),
        "grossVolumeCubicMeters": round(gross_floor_area*HEIGHT, 6),
        "wallSurfaceGrossSquareMeters": round(gross_wall_area, 6),
        "openingAreaSquareMeters": round(opening_area, 6),
        "wallSurfaceNetMinusOpeningsSquareMeters": round(gross_wall_area-opening_area, 6),
        "elementCount": SCENE_ELEMENT_COUNT,
        "elementKinds": {"Wall": 4, "Slab": 1, "Column": 4,
                         "Window": 2, "Door": 1},
        "note": "Footprint and prism volume measured at exterior wall faces; interior clear area excludes wall thickness, but not columns. Structural design not verified.",
    }


def prepare(x, y, schema_path=None):
    data = graph(x, y)
    selected_schema = Path(schema_path) if schema_path is not None else Path(__file__).resolve().parents[1] / "schemas/tapir-live-1.5.10/tapir-scene-live.json"
    selected_schema = selected_schema.resolve()
    if not selected_schema.is_file():
        raise ValueError(f"SCHEMA_NOT_FOUND: {selected_schema}; select the actual Tapir snapshot with --schema")
    catalog = GRAPH.CONTRACTS.load_catalog(selected_schema)
    verification = GRAPH.compile_graph(catalog, data)
    if verification["status"] != "PLAN_VALIDATED_OFFLINE":
        raise ValueError("scene did not pass pinned Tapir graph contract: "
                         + json.dumps(verification["operations"], ensure_ascii=False))
    return {
        "status": "SCENE_PREVIEW_OFFLINE",
        "sourcePlanHash": verification["sourcePlanHash"],
        "graph": data,
        "metrics": metrics(),
        "executionOrder": verification["executionOrder"],
        "schemaVersion": verification["schemaVersion"],
        "schemaPath": str(selected_schema),
        "schemaSha256": hashlib.sha256(selected_schema.read_bytes()).hexdigest(),
        "liveWriteAuthorized": False,
        "plnChanged": False,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--anchor-x", type=float, required=True,
                    help="Coordinate in meters: no automatic empty-site guess")
    ap.add_argument("--anchor-y", type=float, required=True)
    ap.add_argument("--output", type=Path)
    ap.add_argument("--schema", type=Path, default=Path(__file__).resolve().parents[1] / "schemas/tapir-live-1.5.10/tapir-scene-live.json")
    args = ap.parse_args(argv)
    report = prepare(args.anchor_x, args.anchor_y, args.schema)
    output = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    print(output, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
