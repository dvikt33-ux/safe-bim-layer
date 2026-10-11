"""Parametric whole-building BIM graph compiled into the EXISTING Tapir scene writer.

This is a geometrical integration milestone, NOT a designed/certified dwelling.
No live write or project switch occurs here. Explicit story mappings come from
the open project and must be verified again in a live guarded preflight.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
import math
from pathlib import Path

import archicad_bim_graph as GRAPH

ID = __import__("re").compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")
TAPIR_SCHEMA = Path(__file__).resolve().parents[1] / "schemas/tapir-live-1.5.10/tapir-scene-live.json"
WRITES = frozenset(("CreateWalls", "CreateSlabs", "CreateDoors", "CreateWindows"))


def finite(value, label):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError("INVALID_NUMERIC_" + label)
    return float(value)


def xy(x, y):
    return {"x": round(x, 6), "y": round(y, 6)}


def step(sid, command, payload):
    key = command[6:].lower() + "Data"
    return {"id": sid, "command": command, "params": {key: [payload]}}


def wall(a, b, index, height, thickness):
    return {"begCoordinate": a, "endCoordinate": b,
            "floorIndex": index, "zCoordinate": 0.0,
            "height": height, "thickness": thickness,
            "offset": 0.0, "arcAngle": 0.0,
            "referenceLineLocation": "Center", "structureType": "Basic"}


def opening(host_id, offset, width, height, sill=0.0):
    return {"ownerWallId": {"guid": {"$createdGuid": host_id}},
            "centerOffset": round(offset, 6),
            "sillHeight": sill, "width": width, "height": height}


def validate_spec(spec, anchor):
    if not isinstance(spec, dict) or set(spec) != {
            "width", "depth", "storyHeight", "wallThickness",
            "roomBays", "stories"}:
        raise ValueError("BUILDING_SPEC_FIELDS_REQUIRED")
    ax, ay = finite(anchor["x"], "anchor_x"), finite(anchor["y"], "anchor_y")
    width, depth = finite(spec["width"], "width"), finite(spec["depth"], "depth")
    height = finite(spec["storyHeight"], "story_height")
    thick = finite(spec["wallThickness"], "wall_thickness")
    bays = spec["roomBays"]
    if not (6 <= width <= 30 and 6 <= depth <= 30 and
            2.4 <= height <= 4.5 and 0.15 <= thick <= 0.6):
        raise ValueError("BUILDING_ENVELOPE_OUT_OF_RANGE")
    if type(bays) is not int or not (2 <= bays <= 4) or (width - thick) / bays < 2.25:
        raise ValueError("ROOM_BAYS_NOT_FIT")
    stories = spec["stories"]
    if not isinstance(stories, list) or not (1 <= len(stories) <= 3):
        raise ValueError("STORIES_REQUIRED_1_TO_3")
    seen = set()
    for i, item in enumerate(stories):
        if not isinstance(item, dict) or set(item) != {"label", "nativeIndex", "floorId", "level"}:
            raise ValueError("STORY_BINDING_FIELDS_REQUIRED")
        if (not isinstance(item["label"], str)
                or type(item["nativeIndex"]) is not int
                or type(item["floorId"]) is not int
                or item["nativeIndex"] in seen):
            raise ValueError("INVALID_STORY_BINDING")
        seen.add(item["nativeIndex"])
        level = finite(item["level"], "story_level")
        if abs(level - (finite(stories[0]["level"], "base_level") + i * height)) > 1e-5:
            raise ValueError("STORY_LEVELS_DO_NOT_MATCH_HEIGHT")
    if abs(ax) > 1e6 or abs(ay) > 1e6:
        raise ValueError("ANCHOR_OUT_OF_RANGE")
    return ax, ay, width, depth, height, thick, bays, stories


def prepare(part, schema_path=None):
    if not isinstance(part, dict) or set(part) != {"id", "primitive", "anchor", "specification"}:
        raise ValueError("INVALID_BUILDING_COMPONENT")
    if part["primitive"] != "building-shell-v1" or not isinstance(part["id"], str) or not ID.fullmatch(part["id"]):
        raise ValueError("UNSUPPORTED_BUILDING_COMPONENT")
    anchor = part["anchor"]
    if not isinstance(anchor, dict) or set(anchor) != {"x", "y"}:
        raise ValueError("INVALID_ANCHOR")
    x, y, width, depth, height, thick, bays, stories = validate_spec(part["specification"], anchor)
    t = thick / 2.0
    corner = [
        xy(x+t, y+t), xy(x+width-t, y+t),
        xy(x+width-t, y+depth-t), xy(x+t, y+depth-t)
    ]
    slab_corners = [xy(x, y), xy(x+width, y),
                    xy(x+width, y+depth), xy(x, y+depth)]
    operations = []
    # One native Wall per continuous edge and storey, NOT separate pieces at openings.
    for floor, story in enumerate(stories):
        prefix = "s" + str(floor+1)
        idx = story["nativeIndex"]
        for side, a, b in (
            ("south", corner[0], corner[1]), ("east", corner[1], corner[2]),
            ("north", corner[2], corner[3]), ("west", corner[3], corner[0])):
            operations.append(step(prefix+"-wall-"+side, "CreateWalls",
                                   wall(a, b, idx, height, thick)))
        operations.append(step(prefix+"-slab", "CreateSlabs", {
            "level": 0.0, "floorIndex": idx, "thickness": 0.2,
            "referencePlaneLocation": "Top", "polygonCoordinates": slab_corners}))
        for bay in range(1, bays):
            split_x = x + thick/2 + (width-thick)*bay/bays
            sid = prefix+"-partition-"+str(bay)
            operations.append(step(sid, "CreateWalls",
                                   wall(xy(split_x, y+t), xy(split_x, y+depth-t),
                                        idx, height, thick)))
            operations.append(step(prefix+"-interior-door-"+str(bay), "CreateDoors",
                                   opening(sid, (depth-thick)/2.0, .8, 2.0)))
        window_span = min(1.2, (width-thick)/bays - 1.0)
        for bay in range(bays):
            operations.append(step(prefix+"-window-"+str(bay+1), "CreateWindows",
                                   opening(prefix+"-wall-north",
                                           (width-thick)*(bay+.5)/bays,
                                           window_span, 1.25, .9)))
        if floor == 0:
            operations.append(step(prefix+"-entrance", "CreateDoors",
                                   opening(prefix+"-wall-south",
                                           (width-thick)*(.5/bays), .9, 2.1)))
    graph = {"operations": operations}
    schema = Path(schema_path or TAPIR_SCHEMA).resolve()
    if not schema.is_file():
        raise ValueError("PINNED_TAPIR_SCHEMA_MISSING")
    result = GRAPH.compile_graph(GRAPH.CONTRACTS.load_catalog(schema), graph)
    if result["status"] != "PLAN_VALIDATED_OFFLINE":
        invalid = [r for r in result["operations"] if r["status"] == "INVALID"]
        raise ValueError("BUILDING_GRAPH_INVALID: " + json.dumps(invalid[:5], ensure_ascii=False))
    if any(op["command"] not in WRITES for op in operations):
        raise ValueError("UNAPPROVED_BUILDING_MUTATION")
    counts = dict(Counter(GRAPH.CREATES[op["command"]] for op in operations))
    base_level = stories[0]["level"]
    return {
        "status": "SCENE_PREVIEW_OFFLINE", "sourcePlanHash": result["sourcePlanHash"],
        "graph": graph, "executionOrder": result["executionOrder"],
        "schemaVersion": result["schemaVersion"], "schemaPath": str(schema),
        "schemaSha256": hashlib.sha256(schema.read_bytes()).hexdigest(),
        "metrics": {
            "dimensionsMeters": {"width": width, "depth": depth,
                                "height": height*len(stories)},
            "grossFloorAreaSquareMeters": round(width*depth*len(stories), 4),
            "roomBaysPerStorey": bays, "storeyCount": len(stories),
            "elementCount": len(operations), "elementKinds": counts,
            "structuralVerified": False, "normativeVerified": False,
        },
        "envelope": {"xMin": x, "xMax": x+width, "yMin": y,
                     "yMax": y+depth, "zMin": base_level-.3,
                     "zMax": base_level+height*len(stories)+.3},
        "storyBindings": stories,
        "limitations": [
            "NOT_FOR_CONSTRUCTION: no engineered load-path, strength or ground verification",
            "No verified roof/structural joints/foundation/MEP/documentation",
            "Walls are native Basic until composite/CSE adapter is accepted",
            "No automatic PLN save, no automatic retry or rollback",
        ],
        "liveWriteAuthorized": False, "plnChanged": False}
