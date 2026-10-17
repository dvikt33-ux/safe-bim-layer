"""AC29 code-owned CREATE adapters, reusing the already-tested native verifiers.

This module does NOT create a second writer. The original DynamicCommands
run_workflow -> SceneWriter provides the single durable native call; these
callbacks bind existing NativeAdapter.verify / SceneWriter.verify_readback to
an exact one-element, story-zero, basic construction source.
Unsupported geometry and source/host junctions stop before dispatch.
"""
from __future__ import annotations

import math

from apa_ac29_dynamic_write_scopes import NativeVerifier


SLOTS = {
    "CreateBeams": ("beamsData", "Beam", "BeamSegment"),
    "CreateWalls": ("wallsData", "Wall", None),
    "CreateSlabs": ("slabsData", "Slab", None),
}
BEAM_KEYS = frozenset({
    "begCoordinate", "endCoordinate", "zCoordinate", "floorIndex",
    "offset", "slantAngle", "isSlanted", "profileAngle", "arcAngle",
    "verticalCurveHeight", "width", "height", "anchorPoint",
    "circleBased", "isWidthAndHeightLinked", "buildingMaterialId",
})
WALL_REQUIRED = frozenset({
    "begCoordinate", "endCoordinate", "zCoordinate", "floorIndex",
    "height", "thickness", "structureType", "buildingMaterialId",
})
WALL_ALLOWED = WALL_REQUIRED | {"offset", "arcAngle"}
SLAB_REQUIRED = frozenset({
    "polygonCoordinates", "level", "thickness", "floorIndex",
    "structureType", "buildingMaterialId",
})


def need(ok, code):
    if not ok:
        raise ValueError(code)


def finite(v):
    return type(v) in (int, float) and math.isfinite(v)


def same(a, b, tolerance=1e-5):
    return finite(a) and finite(b) and abs(a-b) <= tolerance


def point2(value):
    need(isinstance(value, dict) and
         all(finite(value.get(k)) and abs(value[k]) <= 10000
             for k in ("x", "y")),
         "APA_SCOPED_CREATE_EXACT_FINITE_XY_REQUIRED")
    return (value["x"], value["y"])


def checked_source(command, parameters):
    """One source-qualified native body. Router checks the FULL live schema."""
    need(command in SLOTS and isinstance(parameters, dict),
         "APA_SCOPED_CREATE_UNSUPPORTED_COMMAND")
    slot, kind, _ = SLOTS[command]
    need(set(parameters) == {slot} and
         isinstance(parameters[slot], list) and len(parameters[slot]) == 1 and
         isinstance(parameters[slot][0], dict),
         "APA_SCOPED_CREATE_EXACT_SINGLE_NATIVE_ELEMENT_REQUIRED")
    source = parameters[slot][0]
    need(type(source.get("floorIndex")) is int and
         source["floorIndex"] == 0 and
         isinstance(source.get("buildingMaterialId"), dict) and
         isinstance(source["buildingMaterialId"].get("guid"), str) and
         len(source["buildingMaterialId"]["guid"]) == 36,
         "APA_SCOPED_CREATE_STORY0_EXPLICIT_MATERIAL_REQUIRED")

    if command == "CreateBeams":
        # NativeAdapter.resolve already documents this complete profile.
        need(set(source) == BEAM_KEYS and
             source["anchorPoint"] == "Center" and
             source["circleBased"] is False and
             source["isWidthAndHeightLinked"] is False and
             source["isSlanted"] is False and
             all(finite(source.get(k)) for k in (
                 "zCoordinate", "offset", "slantAngle", "profileAngle",
                 "arcAngle", "verticalCurveHeight", "width", "height")) and
             all(same(source[k], 0) for k in (
                 "offset", "slantAngle", "profileAngle",
                 "arcAngle", "verticalCurveHeight")) and
             0 < source["width"] <= 5 and 0 < source["height"] <= 5,
             "APA_SCOPED_CREATE_ONLY_BASIC_HORIZONTAL_BEAM")
        start, finish = point2(source["begCoordinate"]), point2(source["endCoordinate"])
        need((same(start[0], finish[0]) != same(start[1], finish[1])) and
             max(abs(start[0]-finish[0]), abs(start[1]-finish[1])) > 0.01,
             "APA_SCOPED_CREATE_BEAM_MUST_BE_AXIS_ALIGNED_NONZERO")
        pad = max(source["width"], source["height"])
        # Oversized conservative envelope: never mistake it for a precise BREP.
        xy = [(min(start[i], finish[i])-pad,
               max(start[i], finish[i])+pad) for i in (0, 1)]
        z = (source["zCoordinate"]-pad, source["zCoordinate"]+pad)
    elif command == "CreateWalls":
        need(WALL_REQUIRED <= set(source) <= WALL_ALLOWED and
             source["structureType"] == "Basic" and
             all(finite(source.get(k)) for k in (
                 "height", "thickness", "zCoordinate")) and
             0 < source["height"] <= 30 and 0 < source["thickness"] <= 5 and
             same(source.get("arcAngle", 0), 0) and
             same(source.get("offset", 0), 0),
             "APA_SCOPED_CREATE_ONLY_BASIC_STRAIGHT_WALL")
        start, finish = point2(source["begCoordinate"]), point2(source["endCoordinate"])
        need((same(start[0], finish[0]) != same(start[1], finish[1])) and
             max(abs(start[0]-finish[0]), abs(start[1]-finish[1])) > 0.01,
             "APA_SCOPED_CREATE_WALL_MUST_BE_AXIS_ALIGNED_NONZERO")
        pad = source["thickness"]
        xy = [(min(start[i], finish[i])-pad, max(start[i], finish[i])+pad)
              for i in (0, 1)]
        z = (source["zCoordinate"]-1e-4,
             source["zCoordinate"]+source["height"]+1e-4)
    else:
        need(set(source) == SLAB_REQUIRED and
             source["structureType"] == "Basic" and
             finite(source.get("level")) and
             finite(source.get("thickness")) and
             0 < source["thickness"] <= 3 and
             isinstance(source.get("polygonCoordinates"), list) and
             len(source["polygonCoordinates"]) >= 3,
             "APA_SCOPED_CREATE_ONLY_EXPLICIT_BASIC_SLAB")
        positions = [point2(p) for p in source["polygonCoordinates"]]
        need(len(set(positions)) >= 3,
             "APA_SCOPED_CREATE_NONDEGENERATE_SLAB_POLYGON_REQUIRED")
        xy = [(min(p[i] for p in positions), max(p[i] for p in positions))
              for i in (0, 1)]
        # Conservative envelope accommodates both top-reference variants.
        z = (source["level"]-source["thickness"]-1e-4,
             source["level"]+source["thickness"]+1e-4)
    need(all(finite(lo) and finite(hi) and lo < hi and
             abs(lo) <= 10000 and abs(hi) <= 10000
             for lo, hi in [*xy, z]),
         "APA_SCOPED_CREATE_NATIVE_ENVELOPE_INVALID")
    return source, (xy[0], xy[1], z)


def current_model(native):
    import archicad_connected_components as C
    if (isinstance(native, dict) and
            isinstance(native.get("elements"), list) and
            all(isinstance(r, dict) and "guid" in r and "type" in r
                for r in native["elements"])):
        return native
    return C.G.normalize_dump(native)


def boxes_of(native):
    from apa_ac29_reusable_native_copy import native_aabb_overlaps
    rows = current_model(native)["elements"]
    boxes = []
    for row in rows:
        for body in row.get("bodies", []):
            vertices = body.get("vertices", [])
            if vertices:
                need(all(isinstance(v, (list, tuple)) and len(v) == 3 and
                         all(finite(i) for i in v) for v in vertices),
                     "APA_SCOPED_CREATE_EXISTING_BREP_INVALID")
                box = tuple((min(v[i] for v in vertices),
                             max(v[i] for v in vertices)) for i in range(3))
                boxes.append((row["guid"].lower(), box))
    return boxes


def verify_existing_create_before(*, api, command, parameters, affected,
                                  native_before):
    from apa_ac29_reusable_native_copy import native_aabb_overlaps
    need(not affected, "APA_SCOPED_CREATE_CANNOT_AFFECT_EXISTING_GUIDS")
    item, candidate = checked_source(command, parameters)
    original = current_model(native_before)
    need(original.get("elements"),
         "APA_SCOPED_CREATE_PREVIOUS_NATIVE_MODEL_MISSING")
    collisions = [guid for guid, existing in boxes_of(original)
                  if native_aabb_overlaps(candidate, existing)]
    need(not collisions,
         "APA_SCOPED_CREATE_EXISTING_BREP_JUNCTION_NOT_SOURCE_QUALIFIED")
    return {"status": "APA_EXISTING_NATIVE_CREATE_PREFLIGHT_PASS",
            "command": command,
            "expectedEnvelope": candidate,
            "expectedMaterial": item["buildingMaterialId"]["guid"].lower()}


def verify_existing_create_after(*, api, command, parameters, native_response,
                                 before_guids, after_guids, affected,
                                 native_before, native_after, source_proof):
    from archicad_scene_run import created_guid, requested_details, verify_readback
    from archicad_connected_components import NativeAdapter
    _, kind, child_type = SLOTS[command]
    item, envelope = checked_source(command, parameters)
    need(not affected and source_proof.get("command") == command and
         source_proof.get("expectedMaterial") ==
         item["buildingMaterialId"]["guid"].lower(),
         "APA_SCOPED_CREATE_SOURCE_PROFILE_CHANGED")
    guid = created_guid(native_response).lower()
    new = after_guids - before_guids
    need(before_guids <= after_guids and guid in new and
         len(new) == (2 if child_type else 1),
         "APA_SCOPED_CREATE_GUID_DELTA_INVALID")
    native = current_model(native_after)
    rows = {row["guid"].lower(): row for row in native["elements"]}
    need(set(rows) == after_guids and rows[guid]["type"] == kind,
         "APA_SCOPED_CREATE_NATIVE_ROOT_TYPE_OR_INVENTORY_MISMATCH")
    detail = requested_details(api, guid)
    if command == "CreateBeams":
        # Reuse existing native typed geometry/segment/material acceptance.
        import archicad_connected_components as C
        adapter = NativeAdapter(command)
        adapter.resolve({"params": parameters}, {}, {})
        adapter.verify(api, guid, parameters, detail, 0, 0.0)
    else:
        verify_readback(
            command, parameters, detail,
            expected_floor=0, expected_story_level=0.,
            expected_slab_material_guid=(
                item["buildingMaterialId"]["guid"]
                if command == "CreateSlabs" else None),
            slab_level_is_absolute=command == "CreateSlabs")
    related = [(g, row) for g, row in rows.items() if
               (row.get("relationships", {}).get("hostGuid") or "").lower()
               == guid]
    if child_type:
        need(len(related) == 1 and related[0][1]["type"] == child_type and
             related[0][0] in new,
             "APA_SCOPED_CREATE_OWNED_BEAM_SEGMENT_REQUIRED")
        bodies = related[0][1].get("bodies") or []
        material_row = related[0][1].get("materialBindings", {})
    else:
        need(not related, "APA_SCOPED_CREATE_UNEXPECTED_NATIVE_CHILD")
        bodies = rows[guid].get("bodies") or []
        material_row = rows[guid].get("materialBindings", {})
    need(bodies and all(body.get("closed") is True for body in bodies),
         "APA_SCOPED_CREATE_PHYSICAL_CLOSED_BREP_REQUIRED")
    need(material_row.get("buildingMaterial", {}).get("guid", "").lower()
         == item["buildingMaterialId"]["guid"].lower(),
         "APA_SCOPED_CREATE_NATIVE_BREP_MATERIAL_CHANGED")
    verts = [v for b in bodies for v in b.get("vertices", [])]
    need(verts and all(isinstance(v, (list, tuple)) and len(v) == 3 and
                       all(finite(n) for n in v) for v in verts),
         "APA_SCOPED_CREATE_NATIVE_BREP_VERTICES_MISSING")
    need(all(envelope[i][0]-1e-4 <= v[i] <= envelope[i][1]+1e-4
             for v in verts for i in range(3)),
         "APA_SCOPED_CREATE_PHYSICAL_SOLID_OUTSIDE_APPROVED_ENVELOPE")
    need(set(new) == {guid} | {g for g, _ in related},
         "APA_SCOPED_CREATE_UNEXPECTED_NEW_NATIVE_ELEMENTS")
    return {"status": "APA_EXISTING_NATIVE_CREATE_TYPED_BREP_PASS",
            "command": command, "rootGuid": guid,
            "childGuids": [g for g, _ in related],
            "nativeCreatedGuidCount": len(new)}


def extended_verifiers():
    return {
        "VerifiedNativeBasicBeam": NativeVerifier(
            verifier_id="VerifiedNativeBasicBeam",
            command="CreateBeams", effect="CREATE",
            before=verify_existing_create_before,
            after=verify_existing_create_after),
        "VerifiedNativeBasicWall": NativeVerifier(
            verifier_id="VerifiedNativeBasicWall",
            command="CreateWalls", effect="CREATE",
            before=verify_existing_create_before,
            after=verify_existing_create_after),
        "VerifiedNativeBasicSlab": NativeVerifier(
            verifier_id="VerifiedNativeBasicSlab",
            command="CreateSlabs", effect="CREATE",
            before=verify_existing_create_before,
            after=verify_existing_create_after),
    }
