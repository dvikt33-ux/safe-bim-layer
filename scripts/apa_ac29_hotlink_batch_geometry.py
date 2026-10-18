"""READ_ONLY APA29 Hotlink geometry: local origin correction and bounded batch.

Only supports 0 rotation, non-mirrored, same story/floor. Native world BREP
of the previously accepted, placed Hotlink prototype is the source of truth.
No geometry is reconstructed from a file name, rough component widths, or UI.
"""
from __future__ import annotations

from collections import Counter
import math

from apa_ac29_hotlink_native_verifiers import need, verify_instance_root

MAX_INSTANCES = 32
TOLERANCE = 0.002


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def check_box(box):
    need(isinstance(box, dict) and set(box) == {"x", "y", "z"} and
         all(isinstance(box[a], (tuple, list)) and len(box[a]) == 2 and
             all(finite(v) for v in box[a]) and box[a][0] <= box[a][1]
             for a in ("x", "y", "z")), "HOTLINK_FINITE_NATIVE_AABB_REQUIRED")
    return box


def bounds(points):
    need(isinstance(points, list) and points and
         all(isinstance(v, (list, tuple)) and len(v) == 3 and
             all(finite(x) for x in v) for v in points),
         "HOTLINK_NONEMPTY_FINITE_3D_BREP_VERTICES_REQUIRED")
    return {axis: [min(v[i] for v in points), max(v[i] for v in points)]
            for i, axis in enumerate("xyz")}


def body_vertices(element):
    points = []
    for body in element.get("bodies", []):
        need(isinstance(body, dict) and isinstance(body.get("vertices"), list),
             "HOTLINK_NATIVE_BREP_INVALID_BODY")
        points += body["vertices"]
    return points


def world_boxes(native):
    need(isinstance(native, dict) and isinstance(native.get("elements"), list),
         "HOTLINK_NATIVE_BREP_DUMP_REQUIRED")
    result = {}
    for row in native["elements"]:
        guid = row.get("guid", "").lower()
        need(guid and guid not in result and isinstance(row.get("bodies"), list),
             "HOTLINK_NATIVE_BREP_GUID_OR_BODY_INVALID")
        points = body_vertices(row)
        result[guid] = bounds(points) if points else None
    need(result and any(v is not None for v in result.values()),
         "HOTLINK_NATIVE_MODEL_HAS_NO_SPATIAL_BREP")
    return result


def union(boxes):
    active = [check_box(box) for box in boxes if box is not None]
    need(active, "HOTLINK_SPATIAL_AABB_UNAVAILABLE")
    return {axis: [min(b[axis][0] for b in active),
                   max(b[axis][1] for b in active)] for axis in "xyz"}


def translate(box, offset):
    check_box(box)
    need(isinstance(offset, dict) and set(offset) == {"x", "y", "z"} and
         all(finite(v) for v in offset.values()),
         "HOTLINK_FINITE_TRANSLATION_REQUIRED")
    return {axis: [box[axis][k] + offset[axis] for k in (0, 1)]
            for axis in "xyz"}


def subtract_origin(box, origin):
    return translate(box, {k: -origin[k] for k in "xyz"})


def clash(first, second, tolerance=1e-5):
    check_box(first)
    check_box(second)
    return all(first[axis][0] < second[axis][1] - tolerance and
               first[axis][1] > second[axis][0] + tolerance
               for axis in "xyz")


def box_close(actual, target, tolerance=TOLERANCE):
    check_box(actual)
    check_box(target)
    return all(abs(actual[axis][k] - target[axis][k]) <= tolerance
               for axis in "xyz" for k in (0, 1))


def batch_origins(local_bounds, occupied, prototype_origin, gap, count):
    """Position modules beyond occupied native BREP, with exact X clearance.

    The world transform for zero-rotation/non-mirror is:
      world_point = original_module_point + hotlink_origin.
    Hence target_origin_x = rightmost_existing_world_x + gap - local_min_x.
    """
    check_box(local_bounds)
    need(isinstance(occupied, list) and occupied and
         all(box is None or check_box(box) for box in occupied),
         "HOTLINK_OCCUPIED_NATIVE_BREP_BOXES_REQUIRED")
    need(isinstance(prototype_origin, dict) and
         set(prototype_origin) == {"x", "y", "z"} and
         all(finite(x) for x in prototype_origin.values()) and
         type(count) is int and 1 <= count <= MAX_INSTANCES and
         finite(gap) and 0.1 <= gap <= 100,
         "HOTLINK_BOUNDED_BATCH_AND_GAP_REQUIRED")
    original = [box for box in occupied if box is not None]
    right = union(original)["x"][1]
    origins, predicted, in_use = [], [], list(original)
    for index in range(count):
        x = round(right + gap - local_bounds["x"][0], 6)
        origin = {"x": x, "y": prototype_origin["y"], "z": prototype_origin["z"]}
        target = translate(local_bounds, origin)
        need(target["x"][0] + TOLERANCE >= right + gap and
             all(not clash(target, previous) for previous in in_use),
             "HOTLINK_BATCH_COLLISION_OR_TARGET_GAP_INVALID")
        origins.append(origin)
        predicted.append(target)
        in_use.append(target)
        right = target["x"][1]
    return origins, predicted


def placed_prototype(api, native, node_guid, prototype_guid, actual_origin):
    """Recover source local BREP from a previously placed, SHA-bound module.

    Imported elements must be *owned* by the requested native Hotlink root.
    We do not equate standalone similar solids with a reusable module.
    """
    node_guid, prototype_guid = node_guid.lower(), prototype_guid.lower()
    nodes = {row["guid"].lower(): row for row in native["elements"]}
    need(prototype_guid in nodes and nodes[prototype_guid]["type"] == "Hotlink",
         "HOTLINK_EXISTING_NATIVE_ROOT_REQUIRED")
    verify_instance_root(api, node_guid, prototype_guid, actual_origin)
    guids = sorted(g for g in nodes if g != prototype_guid)
    rows = api("GetDetailsOfElements", {
        "elements": [{"elementId": {"guid": g}} for g in guids],
        "fields": ["type", "hotlinkId", "floorIndex", "details"]
    }).get("detailsOfElements")
    need(isinstance(rows, list) and len(rows) == len(guids),
         "HOTLINK_NATIVE_EXISTING_OWNER_READBACK_INCOMPLETE")
    owned, types = [], Counter()
    for guid, row in zip(guids, rows):
        need(isinstance(row, dict), "HOTLINK_INVALID_NATIVE_DETAIL")
        owner = (row.get("hotlinkId") or {}).get("guid", "").lower()
        if owner == prototype_guid:
            need(row.get("type") != "Hotlink" and row.get("floorIndex") == 0,
                 "HOTLINK_NESTED_OR_OTHER_STORY_NOT_APPROVED")
            owned.append(guid)
            types[row["type"]] += 1
    need(1 <= len(owned) <= 500 and owned and
         all(nodes[g].get("type") == kind
             for g, kind in zip(owned, [nodes[g].get("type") for g in owned])),
         "HOTLINK_EXISTING_OWNED_ELEMENTS_MISSING")
    boxes = world_boxes(native)
    placed = union([boxes[g] for g in owned if boxes[g] is not None])
    local = subtract_origin(placed, actual_origin)
    need(box_close(translate(local, actual_origin), placed),
         "HOTLINK_NATIVE_WORLD_LOCAL_TRANSFORM_DRIFT")
    return {"nodeGuid": node_guid, "prototypeGuid": prototype_guid,
            "prototypeOrigin": actual_origin, "ownedGuids": owned,
            "ownedCount": len(owned), "typeHistogram": dict(types),
            "sourceLocalBounds": local, "existingWorldBounds": placed,
            "allBoxes": boxes}


def planned_batch(prototype, count, gap):
    occupied = list(prototype["allBoxes"].values())
    origins, predicted = batch_origins(
        prototype["sourceLocalBounds"], occupied, prototype["prototypeOrigin"],
        gap, count)
    return {"schema": "APA_HOTLINK_BATCH_GEOMETRY_V1",
            "status": "SOURCE_BREP_COORDINATE_PLAN_PASS_NO_WRITES",
            "nodeGuid": prototype["nodeGuid"],
            "prototypeGuid": prototype["prototypeGuid"],
            "sourceLocalBounds": prototype["sourceLocalBounds"],
            "prototypeOrigin": prototype["prototypeOrigin"],
            "sourceOwnedCount": prototype["ownedCount"],
            "sourceTypeHistogram": prototype["typeHistogram"],
            "count": count, "gapMeters": gap,
            "origins": origins, "expectedBounds": predicted,
            "modelWrites": 0, "singleBatchCall": True}


def published_one_shot_coordinate_proof():
    """Reproduce PR #171 evidence exactly; no user Windows read/write."""
    origin = 346.475
    new_min = 646.474975586
    actual_clearance = 315.999975586
    source_local_min = new_min - origin
    host_right = new_min - actual_clearance
    expected_origin = host_right + 10.0 - source_local_min
    return {"sourceLocalMinX": source_local_min,
            "hostMaxX": host_right,
            "previousOriginX": origin,
            "previousClearanceMeters": actual_clearance,
            "forTenMeterGapOriginX": expected_origin,
            "predictedNewMinX": source_local_min + expected_origin,
            "predictedClearanceMeters": source_local_min + expected_origin - host_right,
            "status": "PUBLISHED_BREP_ARITHMETIC_VERIFIED_NOT_SECOND_LIVE_RUN"}
