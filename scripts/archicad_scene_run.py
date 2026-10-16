"""Guarded one-shot native Archicad scene writer: 12 related BIM elements.

DELIBERATELY NOT a Mailbox recipe; no daemon and no remote activation.
Default is a read-only preflight. --execute requires a matching plan hash
printed by preflight and a unique scene ID. Exactly ONE local saved test PLN.
NO save, switch, retry, delete or rollback. Partial scenes require inspection.
"""
from __future__ import annotations

import argparse
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path, PureWindowsPath
import re
import sqlite3
import sys
import traceback

from archicad_guarded_wall_probe import tapir
import archicad_scene_v1 as SCENE

PORT = 19723
EXPECTED_NAME = "Тест MER "
EXPECTED_PATH = r"C:\LocalAI\SafeBIM_Global_Library_Test_Projects\Тест MER .pln"
EXPECTED_TAPIR = "1.5.10"

# Narrowly approved throwaway project. NEVER apply CLI target override to any
# other PLN, including protected APA_Pavilion_MVP_SUCCESS.pln and SyncGuids.
APPROVED_SCRATCH_PATH = r"C:\LocalAI\APA_Test_House_01.pln"
APPROVED_ISOLATED_WRITER_PATH = r"C:\LocalAI\APA_Isolated_Writer_Test_01.pln"
_SAVED_COPY_AUTHORIZATION = None


def bind_isolated_writer_pln(port, path=APPROVED_ISOLATED_WRITER_PATH):
    """Bind the user-authorized isolated writer test; no arbitrary path override."""
    global PORT, EXPECTED_NAME, EXPECTED_PATH, _SAVED_COPY_AUTHORIZATION
    if type(port) is not int or not 1 <= port <= 65535:
        raise ValueError("INVALID_TEST_PORT")
    if path != APPROVED_ISOLATED_WRITER_PATH:
        raise ValueError("ISOLATED_WRITER_PLN_NOT_APPROVED")
    PORT = port
    EXPECTED_PATH = APPROVED_ISOLATED_WRITER_PATH
    EXPECTED_NAME = "APA_Isolated_Writer_Test_01"
    _SAVED_COPY_AUTHORIZATION = None


def bind_authorized_saved_copy(port, path, name, saved_sha256, authorization_ref):
    """Bind an explicitly authorized renamed test copy, never a CLI override.

    The caller supplies the current human authorization reference and exact
    saved-file hash. Identity and accepted GUID/body checks still run before
    every native mutation through the existing SceneWriter.
    """
    global PORT, EXPECTED_NAME, EXPECTED_PATH, _SAVED_COPY_AUTHORIZATION
    if type(port) is not int or not 1 <= port <= 65535:
        raise ValueError('INVALID_TEST_PORT')
    if (not isinstance(path,str) or not PureWindowsPath(path).is_absolute() or
            PureWindowsPath(path).suffix.casefold()!='.pln' or
            not isinstance(name,str) or name!=PureWindowsPath(path).stem or
            not isinstance(authorization_ref,str) or not authorization_ref.strip() or
            not isinstance(saved_sha256,str) or not re.fullmatch('[0-9a-f]{64}',saved_sha256)):
        raise ValueError('EXPLICIT_SAVED_COPY_AUTHORIZATION_REQUIRED')
    if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=saved_sha256:
        raise ValueError('AUTHORIZED_SAVED_COPY_HASH_MISMATCH')
    PORT,EXPECTED_PATH,EXPECTED_NAME=port,path,name
    _SAVED_COPY_AUTHORIZATION = {'path': path, 'sha256': saved_sha256,
                                'authorizationRef': authorization_ref}


def authorized_authored_target(path):
    """Pure preview eligibility, not an execution grant or arbitrary override."""
    if path in (APPROVED_SCRATCH_PATH, APPROVED_ISOLATED_WRITER_PATH):
        return True
    record = _SAVED_COPY_AUTHORIZATION
    return bool(record and path == EXPECTED_PATH == record['path'] and
        hashlib.sha256(Path(path).read_bytes()).hexdigest() == record['sha256'])


def bind_approved_scratch_pln(port, path=APPROVED_SCRATCH_PATH):
    """Configure only the expressly designated disposable PLN; fail closed."""
    global PORT, EXPECTED_NAME, EXPECTED_PATH
    if type(port) is not int or port < 1 or port > 65535:
        raise ValueError("INVALID_TEST_PORT")
    if not isinstance(path, str) or path.casefold() != APPROVED_SCRATCH_PATH.casefold():
        raise ValueError("TEST_PLN_NOT_APPROVED")
    PORT = port
    EXPECTED_PATH = APPROVED_SCRATCH_PATH
    EXPECTED_NAME = "APA_Test_House_01"

DEFAULT_SCENE_SCHEMA = Path(__file__).resolve().parents[1] / "schemas/tapir-live-1.5.10/tapir-scene-live.json"
ALLOWED_WRITES = frozenset(("CreateWalls", "CreateSlabs", "CreateColumns",
                           "CreateWindows", "CreateDoors", "CreateObjects"))
# Opt-in typed adapters reuse this journal; a command name alone never enables it.
EXTENDED_WRITES = frozenset({'CreateRoofs','CreateBeams','CreateMorphs','CreateMEPRoutingElements','CreateMEPElements'})
_GUID = re.compile(r"^[0-9a-fA-F]{8}(-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}$")
_SCENE_ID = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{3,79}$")
_NONSPATIAL_TYPES = frozenset({
    "Dimension", "RadialDimension", "LevelDimension", "AngleDimension",
    "Text", "Label", "Hatch", "Line", "PolyLine", "Arc", "Circle",
    "Spline", "Hotspot", "CutPlane", "Camera", "CamSet", "Group",
    "SectElem", "Drawing", "Picture", "Detail", "Elevation",
    "InteriorElevation", "Worksheet", "ChangeMarker",
})



def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def native_plan_hash(preview, graph_hash):
    binding={'graphHash':graph_hash, 'schemaSha256':preview['schemaSha256'],
        'slabBasicMaterialName':preview.get('slabBasicMaterialName'),
        'slabBasicMaterialGuid':preview.get('slabBasicMaterialGuid'),
        'slabLevelConvention':preview.get('slabLevelConvention','LEGACY_RELATIVE')}
    if preview.get('nativeAttributeExpectations'):
        binding['nativeAttributeExpectations']=preview['nativeAttributeExpectations']
    if preview.get('nativeLibraryExpectations'):
        binding['nativeLibraryExpectations']=preview['nativeLibraryExpectations']
    if preview.get('integrationBindings'):
        binding['integrationBindings']=preview['integrationBindings']
    return digest(binding)


def close(a, b, tolerance=1e-5):
    return (type(a) in (int, float) and type(b) in (int, float)
            and math.isfinite(a) and math.isfinite(b)
            and abs(a-b) <= tolerance)


def guarded_project(api, required_story=None):
    info = api("GetProjectInfo", {})
    if (not isinstance(info, dict) or info.get("projectName") != EXPECTED_NAME
            or info.get("projectPath") != EXPECTED_PATH
            or info.get("isUntitled") is not False
            or info.get("isTeamwork") is not False):
        raise ValueError("WRONG_PROJECT: exact test PLN (including trailing space) required")
    stories = api("GetStories", {})
    if required_story is None:
        native_index, floor_id, level, label = 0, 1, 0.0, None
    else:
        native_index = required_story["nativeIndex"]
        floor_id = required_story["floorId"]
        level = required_story["level"]
        label = required_story["label"]
    floor = next((x for x in stories.get("stories", [])
                  if x.get("index") == native_index), None)
    if (stories.get("actStory") != native_index or not isinstance(floor, dict)
            or floor.get("floorId") != floor_id or not close(floor.get("level"), level)):
        raise ValueError("STORY_MISMATCH: active story must match pinned binding")
    if label is not None and (floor.get("name") or floor.get("uName") or "") != label:
        raise ValueError("STORY_LABEL_MISMATCH_OR_MISSING")
    version = api("GetAddOnVersion", {}).get("version")
    if version != EXPECTED_TAPIR:
        raise ValueError(f"TAPIR_VERSION_MISMATCH: {version!r} != {EXPECTED_TAPIR}")
    return {"path": info["projectPath"], "name": info["projectName"],
            "port": PORT, "tapirVersion": version, "storyIndex": native_index}


def guarded_project_for_read(api):
    """Exactly bound PLN + verified native story topology, independent of UI view.

    READ-ONLY guard for DynamicCommands.read(): the active Archicad view may
    be 3D (actStory=-1) or a legitimate upper story. It is not an element
    home-story and must not be a precondition for Get* operations.

    SceneWriter.guarded_binding() continues to call guarded_project() above.
    Never reuse this relaxed *view* guard as a write authorization.
    """
    info = api("GetProjectInfo", {})
    if (not isinstance(info, dict) or info.get("projectName") != EXPECTED_NAME
            or info.get("projectPath") != EXPECTED_PATH
            or info.get("isUntitled") is not False
            or info.get("isTeamwork") is not False):
        raise ValueError("WRONG_PROJECT: exact saved PLN required for native read")
    native = api("GetStories", {})
    if not isinstance(native, dict) or not isinstance(native.get("stories"), list):
        raise ValueError("READONLY_NATIVE_STORY_MAP_UNAVAILABLE")
    stories = native["stories"]
    indices = [s.get("index") for s in stories if isinstance(s, dict)]
    if (len(stories) != len(indices) or not all(type(i) is int for i in indices)
            or len(indices) != len(set(indices))):
        raise ValueError("READONLY_NATIVE_STORY_MAP_INVALID")
    first = next((s for s in stories if s["index"] == 0), None)
    if (not isinstance(first, dict) or first.get("floorId") != 1
            or not close(first.get("level"), 0.0)):
        raise ValueError("READONLY_PINNED_FIRST_STORY_MISMATCH")
    if any(not type(s.get("floorId")) is int or
           not type(s.get("level")) in (int, float) or
           not math.isfinite(s["level"]) for s in stories):
        raise ValueError("READONLY_NATIVE_STORY_TOPOLOGY_INVALID")
    active = native.get("actStory")
    if type(active) is not int:
        raise ValueError("READONLY_ACTIVE_VIEW_INDEX_MISSING")
    version = api("GetAddOnVersion", {}).get("version")
    if version != EXPECTED_TAPIR:
        raise ValueError(f"TAPIR_VERSION_MISMATCH: {version!r} != {EXPECTED_TAPIR}")
    return {"path": info["projectPath"], "name": info["projectName"],
            "port": PORT, "tapirVersion": version, "storyIndex": 0,
            "activeViewStoryIndex": active,
            "storyTopology": [
                {"index": s["index"], "floorId": s["floorId"],
                 "level": s["level"], "label": s.get("name") or s.get("uName") or ""}
                for s in sorted(stories, key=lambda s: s["index"])
            ]}


def scan_for_existing_geometry(api, anchor_x, anchor_y, envelope=None):
    """Conservatively refuse if an existing 3D body touches the scene envelope.

    Every existing element is scanned, not just selected Walls. Malformed,
    unsupported or incomplete API responses block all scene writes.
    """
    all_elements = api("GetAllElements", {})
    elements = all_elements.get("elements") if isinstance(all_elements, dict) else None
    if not isinstance(elements, list) or len(elements) > 50000:
        raise ValueError("SPATIAL_SCAN_UNAVAILABLE: missing/oversized native inventory")
    if envelope is None:
        lowx, highx = anchor_x-.35, anchor_x+SCENE.WIDTH+.35
        lowy, highy = anchor_y-.35, anchor_y+SCENE.DEPTH+.35
        lowz, highz = -SCENE.SLAB_THICKNESS-.1, SCENE.HEIGHT+.1
    else:
        if (not isinstance(envelope, dict) or set(envelope) !=
                {"xMin", "xMax", "yMin", "yMax", "zMin", "zMax"}):
            raise ValueError("INVALID_SCENE_ENVELOPE")
        coordinates = [envelope[k] for k in
                       ("xMin", "xMax", "yMin", "yMax", "zMin", "zMax")]
        if any(type(n) not in (float, int) or not math.isfinite(n)
               for n in coordinates):
            raise ValueError("INVALID_SCENE_ENVELOPE")
        if any(coordinates[i] >= coordinates[i+1] for i in (0, 2, 4)):
            raise ValueError("INVERTED_SCENE_ENVELOPE")
        lowx, highx, lowy, highy, lowz, highz = (
            envelope["xMin"]-.35, envelope["xMax"]+.35,
            envelope["yMin"]-.35, envelope["yMax"]+.35,
            envelope["zMin"]-.1, envelope["zMax"]+.1)
    checked = 0
    nonspatial = 0
    native_dump = None
    native_elements = None
    resultant_fallbacks = []
    bodyless_external = []
    bodyless_stair_parts = []
    stair_members = {}
    # Batch modestly; do not hold a massive JSON response in memory.
    for i in range(0, len(elements), 100):
        batch = elements[i:i+100]
        if any(not isinstance(v, dict) or not _GUID.fullmatch(str(
               v.get("elementId", {}).get("guid", ""))) for v in batch):
            raise ValueError("SPATIAL_SCAN_UNAVAILABLE: invalid element GUID row")
        boxes = api("Get3DBoundingBoxes", {"elements": batch})
        rows = boxes.get("boundingBoxes3D") if isinstance(boxes, dict) else None
        if not isinstance(rows, list) or len(rows) != len(batch):
            raise ValueError("SPATIAL_SCAN_UNAVAILABLE: incomplete 3D boxes")
        # Some plan annotations have no 3D body. Their explicit native
        # geometry errors can be ignored ONLY after typed native classification;
        # unsupported 3D objects or unknown failures still stop all writes.
        unavailable = []
        keys = ("xMin", "xMax", "yMin", "yMax", "zMin", "zMax")
        for index, item in enumerate(rows):
            b = item.get("boundingBox3D") if isinstance(item, dict) else None
            if b is None and isinstance(item, dict) and "error" in item:
                unavailable.append(batch[index])
                continue
            if (not isinstance(b, dict) or not all(
                    type(b.get(k)) in (int, float) and math.isfinite(b[k])
                    for k in keys)):
                raise ValueError("SPATIAL_SCAN_UNAVAILABLE: invalid 3D bbox")
            if (b["xMin"] > b["xMax"] or b["yMin"] > b["yMax"]
                    or b["zMin"] > b["zMax"]):
                # The installed universal API returns empty sentinel XY extents
                # for real Beam/Column segments. Use actual resultant bodies,
                # not an invented box or a rewritten provider field.
                if native_dump is None:
                    native_dump = api('GetModelDumpV1', {})
                    slots = native_dump.get('nativeBodySlots')
                    body_ids = [v.get('nativeBodyIndex') for v in native_dump.get('bodies', [])]
                    deleted = native_dump.get('deletedBodySlots', [])
                    if (type(slots) is not int or native_dump.get('regenerated3D') is not True or
                            native_dump.get('coordinateSystem') != 'ABSOLUTE_PROJECT_XYZ' or
                            len(body_ids + deleted) != len(set(body_ids + deleted)) or
                            set(body_ids + deleted) != set(range(1, slots + 1))):
                        raise ValueError('SPATIAL_SCAN_UNAVAILABLE: incomplete native body slots')
                    import archicad_authored_geometry as GEOMETRY
                    native_elements = {e['guid'].lower(): e for e in
                        GEOMETRY.normalize_dump(native_dump)['elements']}
                guid = batch[index]['elementId']['guid'].lower()
                element = native_elements.get(guid)
                if not element:raise ValueError('SPATIAL_SCAN_UNAVAILABLE: missing native identity')
                vertices = [v for body in element['bodies'] for v in body['vertices']]
                if vertices:
                    b = {axis + bound: fn(v[k] for v in vertices)
                        for k, axis in enumerate(('x', 'y', 'z'))
                        for bound, fn in [('Min', min), ('Max', max)]}
                    resultant_fallbacks.append(guid)
                elif (element.get('nativeTypeId') == 150 and
                        all(b[a+'Min'] == 1e35 and b[a+'Max'] == -1e35 for a in ('x','y'))):
                    # No semantic MEP/analytical classification is inferred.
                    # Slot-complete native model and empty universal extent both
                    # establish no available volumetric body. Preserve the GUID
                    # and explicitly retain the native view/filter scope below.
                    bodyless_external.append(guid)
                    nonspatial += 1
                    continue
                elif (element.get('type') in {'Riser','Tread'} and element.get('nativeTypeId') in {48,49}
                        and all(b[a+'Min']==1e35 and b[a+'Max']==-1e35 for a in ('x','y'))):
                    parent=element.get('relationships',{}).get('hostGuid','').lower()
                    if native_elements.get(parent,{}).get('type')!='Stair':raise ValueError('SPATIAL_SCAN_UNAVAILABLE: stair child owner unverified')
                    if parent not in stair_members:
                        parts=api('GetSubelementsOfHierarchicalElements',{'elements':[{'elementId':{'guid':parent}}]})['subelements']
                        if len(parts)!=1:raise ValueError('SPATIAL_SCAN_UNAVAILABLE: stair membership incomplete')
                        stair_members[parent]={r.get('elementId',{}).get('guid','').lower() for values in parts[0].values() if isinstance(values,list) for r in values}
                    if guid not in stair_members[parent]:raise ValueError('SPATIAL_SCAN_UNAVAILABLE: stair child membership mismatch')
                    bodyless_stair_parts.append(guid);nonspatial+=1;continue
                else:raise ValueError('SPATIAL_SCAN_UNAVAILABLE: inverted 3D bbox')
            if (b["xMin"] <= highx and b["xMax"] >= lowx
                    and b["yMin"] <= highy and b["yMax"] >= lowy
                    and b["zMin"] <= highz and b["zMax"] >= lowz):
                raise ValueError("SPATIAL_COLLISION: existing element inside scene envelope")
            checked += 1
        if unavailable:
            classified = api("GetDetailsOfElements", {"elements": unavailable})
            types = classified.get("detailsOfElements") if isinstance(classified, dict) else None
            if (not isinstance(types, list) or len(types) != len(unavailable)
                    or any(not isinstance(t, dict)
                           or t.get("type") not in _NONSPATIAL_TYPES for t in types)):
                raise ValueError("SPATIAL_SCAN_UNAVAILABLE: unbounded 3D/unknown element")
            nonspatial += len(unavailable)
    return {"nativeElementsInspected": checked+nonspatial,
            "volumetricBodiesChecked": checked,
            "nonSpatialElementsVerified": nonspatial - len(bodyless_external)-len(bodyless_stair_parts),
            "bodylessNativeStairChildren": bodyless_stair_parts,
            "resultantBodyBoundsFallbackGuids": resultant_fallbacks,
            "bodylessExternalGuids": bodyless_external,
            "bodylessExternalSemantics": 'NOT_VERIFIED_NO_TYPE_INFERENCE',
            "geometryScope": native_dump.get('geometryScope') if native_dump else 'UNIVERSAL_NATIVE_BOUNDS'}


def requested_details(api, guid):
    output = api("GetDetailsOfElements", {
        "elements": [{"elementId": {"guid": guid}}]})
    rows = output.get("detailsOfElements") if isinstance(output, dict) else None
    if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict):
        raise ValueError("NATIVE_READBACK: expected one typed detail row")
    return rows[0]


def resolve_params(step, created):
    """Replace ONLY generated parent Wall GUID for Windows or Doors."""
    command = step["command"]
    key = command[6:].lower()+"Data"
    # CreateWalls -> wallsData, CreateWindows -> windowsData, etc.
    params = json.loads(canonical(step["params"]))
    data = params[key]
    if not isinstance(data, list) or len(data) != 1:
        raise ValueError("only one element per native mutation supported")
    item = data[0]
    if command in ("CreateWindows", "CreateDoors"):
        owner = item.get("ownerWallId")
        ref = owner.get("guid") if isinstance(owner, dict) else None
        if not isinstance(ref, dict) or set(ref) != {"$createdGuid"}:
            raise ValueError("hosted opening must reference a generated Wall")
        sid = ref["$createdGuid"]
        if sid not in created or created[sid]["kind"] != "Wall":
            raise ValueError("hosted opening missing verified parent Wall GUID")
        item["ownerWallId"] = {"guid": created[sid]["guid"]}
    return params


def compare_polygon(expected, actual):
    if not isinstance(actual, list) or len(actual) not in (len(expected), len(expected)+1):
        return False
    actual = list(actual)
    if len(actual) == len(expected)+1:
        if not (close(actual[-1].get("x"), actual[0].get("x"))
                and close(actual[-1].get("y"), actual[0].get("y"))):
            return False
        actual.pop()
    want = [(p["x"], p["y"]) for p in expected]
    got = [(p.get("x"), p.get("y")) for p in actual]
    n = len(want)
    return any(all(close(got[(start + direction*i) % n][0], want[i][0])
                   and close(got[(start + direction*i) % n][1], want[i][1])
                   for i in range(n))
               for start in range(n) for direction in (-1, 1))


def story_level_for_floor(story_bindings, native_index):
    """Resolve absolute story elevation by native index, never by ordinal guess."""
    if not story_bindings:
        if native_index != 0:
            raise ValueError("NONZERO_STORY_WITHOUT_PINNED_ELEVATION")
        return 0.0
    matched = [s for s in story_bindings if s.get("nativeIndex") == native_index]
    if len(matched) != 1 or not isinstance(matched[0].get("level"), (int, float)):
        raise ValueError("STORY_ELEVATION_NOT_UNIQUELY_PINNED")
    level = matched[0]["level"]
    if not math.isfinite(level):
        raise ValueError("STORY_ELEVATION_NOT_FINITE")
    return level


def verify_readback(command, params, row, owner_guid=None, expected_floor=0,
                    expected_slab_material_guid=None, allow_slab_thickness_mismatch=False,
                    expected_story_level=0.0, slab_level_is_absolute=False):
    kind = command[6:-1]  # CreateWalls -> Wall, CreateDoors -> Door
    if row.get("type") != kind or row.get("floorIndex") != expected_floor:
        raise ValueError(f"READBACK_TYPE_OR_STORY: expected {kind} on native story {expected_floor}")
    details = row.get("details")
    if not isinstance(details, dict):
        raise ValueError("READBACK_DETAILS_MISSING")
    k = command[6:].lower()+"Data"
    expected = params[k][0]
    if command == "CreateWalls":
        # Reuse the proven wall's core geometry/type checks.
        for key in ("begCoordinate", "endCoordinate"):
            if any(not close(details.get(key, {}).get(axis), expected[key][axis])
                   for axis in ("x", "y")):
                raise ValueError("WALL_POSITION_READBACK_MISMATCH")
        for source, target in (("height", "height"), ("thickness", "begThickness"),
                               ("thickness", "endThickness"), ("offset", "offset"),
                               ("arcAngle", "arcAngle")):
            wanted = expected.get(source, 0.0) if source in ('offset', 'arcAngle') else expected[source]
            if not close(details.get(target), wanted):
                raise ValueError("WALL_SIZE_READBACK_MISMATCH: " + target)
        # CreateWalls zCoordinate is a floor-local offset in the pinned graph;
        # native GetDetailsOfElements returns absolute project Z in observed
        # Archicad 29: story 1 at +3m => requested 0m, readback +3m.
        if not close(details.get("zCoordinate"),
                     expected_story_level + expected["zCoordinate"]):
            raise ValueError("WALL_STORY_Z_READBACK_MISMATCH")
        if any(details.get(k) != v for k, v in (
            ("structureType", expected.get("structureType", "Basic")), ("referenceLineLocation", "Center"),
            ("geometryType", "Straight"))):
            raise ValueError("WALL_TYPE_READBACK_MISMATCH")
        if "buildingMaterialId" in expected and (
                str(details.get("buildingMaterialId",{}).get("guid","")).casefold()!=
                expected["buildingMaterialId"]["guid"].casefold()):
            raise ValueError("WALL_MATERIAL_READBACK_MISMATCH")
        if expected.get('structureType') == 'Composite' and (
                str(details.get('compositeId',{}).get('guid','')).casefold()!=
                expected['compositeId']['guid'].casefold()):
            raise ValueError('WALL_COMPOSITE_READBACK_MISMATCH')
        for face in ('referenceMaterial','oppositeMaterial','sideMaterial'):
            if face in expected:
                actual=details.get(face,{})
                wanted=expected[face]
                if actual.get('overridden') != wanted['overridden'] or (
                        wanted['overridden'] and
                        str(actual.get('attributeId',{}).get('guid','')).casefold()!=
                        wanted['attributeId']['guid'].casefold()):
                    raise ValueError('WALL_SURFACE_OVERRIDE_READBACK_MISMATCH')
    elif command == "CreateSlabs":
        if 'holes' in expected:
            holes=details.get('holes',[])
            wanted=expected['holes']
            if len(holes)!=len(wanted):raise ValueError('SLAB_HOLE_READBACK_COUNT_MISMATCH')
            unused=list(holes)
            for hole in wanted:
                match=next((i for i,q in enumerate(unused) if compare_polygon(hole['polygonCoordinates'],q.get('polygonOutline',q.get('polygonCoordinates')))),None)
                if match is None:raise ValueError('SLAB_HOLE_READBACK_GEOMETRY_MISMATCH')
                unused.pop(match)
        # CreateSlabs may inherit Composite from the current defaults. Allow an
        # intermediate thickness mismatch ONLY before an explicitly journaled
        # ModifySlabs; still prove story, type, level and polygon first.
        relative_level = (expected["level"] - expected_story_level
                          if slab_level_is_absolute else expected["level"])
        if (not close(details.get("level"), relative_level)
                or (slab_level_is_absolute
                    and not close(details.get("zCoordinate"), expected["level"]))
                or not compare_polygon(expected["polygonCoordinates"],
                                       details.get("polygonOutline"))
                or (not allow_slab_thickness_mismatch
                    and not close(details.get("thickness"), expected["thickness"]))):
            raise ValueError("SLAB_READBACK_MISMATCH")
        if allow_slab_thickness_mismatch and (
                details.get("structureType") not in ("Basic", "Composite")
                or type(details.get("thickness")) not in (int, float)
                or not math.isfinite(details["thickness"]) or details["thickness"] <= 0):
            raise ValueError("SLAB_INTERMEDIATE_STRUCTURE_UNVERIFIED")
        if expected_slab_material_guid is not None:
            material = details.get("buildingMaterialId")
            actual_guid = material.get("guid") if isinstance(material, dict) else None
            if (details.get("structureType") != "Basic"
                    or not isinstance(actual_guid, str)
                    or actual_guid.lower() != expected_slab_material_guid.lower()):
                raise ValueError("BASIC_SLAB_MATERIAL_READBACK_MISMATCH")
    elif command == "CreateColumns":
        point = expected["coordinates"]
        origin = details.get("origin", {})
        if (not all(close(origin.get(axis), point[axis]) for axis in ("x", "y"))
                or not all(close(details.get(key), value) for key, value in (
                    ("zCoordinate", point["z"]), ("height", expected["height"]),
                    ("width", expected["width"]), ("depth", expected["depth"])))):
            raise ValueError("COLUMN_READBACK_MISMATCH")
        if 'buildingMaterialId' in expected and (
                str(details.get('buildingMaterialId',{}).get('guid','')).casefold()!=
                expected['buildingMaterialId']['guid'].casefold()):
            raise ValueError('COLUMN_MATERIAL_READBACK_MISMATCH')
        if 'profileId' in expected and (
                str(details.get('profileId',{}).get('guid','')).casefold()!=
                expected['profileId']['guid'].casefold()):
            raise ValueError('COLUMN_PROFILE_READBACK_MISMATCH')
    elif command == "CreateObjects":
        if details.get('libPart', {}).get('name') != expected['libraryPartName']:
            raise ValueError('OBJECT_LIBRARY_NAME_READBACK_MISMATCH')
        if not all(close(details.get('origin', {}).get(axis), expected['coordinates'][axis])
                   for axis in ('x','y','z')):
            raise ValueError('OBJECT_POSITION_READBACK_MISMATCH')
        if 'dimensions' in expected and not all(
                close(details.get('dimensions',{}).get(axis), expected['dimensions'][axis])
                for axis in ('x','y','z')):
            raise ValueError('OBJECT_DIMENSIONS_READBACK_MISMATCH')
        if 'angle' in expected and not close(details.get('angle'),expected['angle']):
            raise ValueError('OBJECT_ROTATION_READBACK_MISMATCH')
    else:
        owner = details.get("ownerElementId")
        actual_guid = owner.get("guid") if isinstance(owner, dict) else None
        if not isinstance(actual_guid, str) or actual_guid.lower() != owner_guid.lower():
            raise ValueError("HOST_GUID_READBACK_MISMATCH")
        if details.get("ownerElementType") not in (None, "Wall"):
            raise ValueError("HOST_TYPE_READBACK_MISMATCH")
        for field in ("width", "height", "sillHeight", "centerOffset"):
            if not close(details.get(field), expected[field]):
                raise ValueError(f"OPENING_READBACK_MISMATCH: {field}")
    return kind


def created_guid(raw):
    rows = raw.get("elements") if isinstance(raw, dict) else None
    if not isinstance(rows, list) or len(rows) != 1:
        raise ValueError("AMBIGUOUS_CREATE_RESULT: expected one element")
    entry = rows[0]
    guid = entry.get("elementId", {}).get("guid") if isinstance(entry, dict) else None
    if not isinstance(guid, str) or not _GUID.fullmatch(guid):
        raise ValueError("INVALID_CREATED_GUID")
    return guid


def check_previous_wall(api, graph_step, created, story_bindings=None):
    key = graph_step["params"]
    data = list(key.values())[0][0]
    wallid = data["ownerWallId"]["guid"]["$createdGuid"]
    parent = created.get(wallid)
    if not parent or parent["kind"] != "Wall":
        raise ValueError("MISSING_APPROVED_PARENT_WALL")
    previous_step = next((s for s in created["__plan__"]["operations"]
                          if s["id"] == wallid), None)
    if previous_step is None:
        raise ValueError("PARENT_PLAN_ROW_MISSING")
    row = requested_details(api, parent["guid"])
    parent_floor = previous_step["params"]["wallsData"][0]["floorIndex"]
    verify_readback(
        "CreateWalls", previous_step["params"], row,
        expected_floor=parent_floor,
        expected_story_level=story_level_for_floor(story_bindings, parent_floor))
    return parent["guid"]


def resolve_basic_slab_material(api, name):
    """Resolve exactly one approved Building Material in the sole active PLN."""
    data = api("GetAttributesByType", {"attributeType": "BuildingMaterial"})
    headers = data.get("attributes") if isinstance(data, dict) else None
    if not isinstance(headers, list):
        raise ValueError("BUILDING_MATERIAL_INVENTORY_UNAVAILABLE")
    matches = [row for row in headers if isinstance(row, dict) and row.get("name") == name]
    if len(matches) != 1:
        raise ValueError("BASIC_SLAB_MATERIAL_MISSING_OR_AMBIGUOUS")
    attr = matches[0].get("attributeId")
    guid = attr.get("guid") if isinstance(attr, dict) else None
    if not isinstance(guid, str) or not _GUID.fullmatch(guid):
        raise ValueError("BASIC_SLAB_MATERIAL_GUID_UNVERIFIED")
    return guid


class SceneWriter:
    def __init__(self, api, journal_path, schema_path=None, preview_factory=None,
                 adapters=None, allow_3d_view_for_write=False):
        self.api = api
        # Explicit opt-in only for an already SHA-authorized saved copy.
        # The default writer keeps the original active-story=0 guard.
        if type(allow_3d_view_for_write) is not bool:
            raise ValueError('3D_NATIVE_WRITE_OPTIN_MUST_BE_BOOLEAN')
        self.allow_3d_view_for_write = allow_3d_view_for_write
        self.journal_path = Path(journal_path)
        self.schema_path = Path(schema_path) if schema_path is not None else DEFAULT_SCENE_SCHEMA
        self.preview_factory = preview_factory
        self.required_story = None
        self.adapters = dict(adapters or {})
        if set(self.adapters) - EXTENDED_WRITES:
            raise ValueError('UNSUPPORTED_NATIVE_ADAPTER')
        self.allowed_writes = ALLOWED_WRITES | self.adapters.keys()

    def modify_morph_body(self, preflight, scene_id, parameters, expected_hash,
                          verify_after):
        """One explicit in-place repair through the same durable writer ledger.

        A failed create is reconciled externally first. This is a new, hashed
        Modify intent, never a retry of CreateMorphs or an automatic rollback.
        """
        if ('CreateMorphs' not in self.adapters or
                not _SCENE_ID.fullmatch(scene_id) or not callable(verify_after)):
            raise ValueError('MORPH_CHANGE_REQUIRES_TYPED_ADAPTER_AND_READBACK')
        command='ModifyMorphs'
        intent={'sceneId':scene_id,'sourcePlanHash':preflight['sourcePlanHash'],
            'command':command,'parameters':parameters,'target':preflight['binding']}
        if digest(intent)!=expected_hash:
            raise ValueError('MORPH_CHANGE_INTENT_HASH_MISMATCH')
        rows=parameters.get('morphsWithDetails',[])
        if len(rows)!=1 or set(rows[0])!={'elementId','body'}:
            raise ValueError('ONLY_ONE_EXPLICIT_MORPH_BODY_REPAIR')
        checked=SCENE.GRAPH.CONTRACTS.compile_batch(
            SCENE.GRAPH.CONTRACTS.load_catalog(self.schema_path),
            {'requests':[{'id':'repair','command':command,'params':parameters}]},
            runtime_version=EXPECTED_TAPIR)
        if checked['status']!='SCHEMA_VALID':
            raise ValueError('MORPH_CHANGE_SCHEMA_INVALID')
        from archicad_native_beam_details import require_morph_last_resort
        require_morph_last_resort(preflight.get('integrationBindings',{}).get('dependencies',{}))
        result={'status':'BLOCKED','automaticRetry':False,'sceneId':scene_id,
            'operationHash':expected_hash,'command':command,'nativeCreates':0}
        with closing(sqlite3.connect(self.journal_path)) as db:
            db.execute('PRAGMA synchronous=FULL');db.execute('BEGIN IMMEDIATE')
            if db.execute('SELECT 1 FROM scenes WHERE scene_id=? OR plan_hash=?',(scene_id,expected_hash)).fetchone():
                raise ValueError('MORPH_CHANGE_ALREADY_RESERVED_NEVER_RETRY')
            db.execute('INSERT INTO scenes VALUES(?,?,?,?)',(scene_id,expected_hash,'STARTED',canonical(result)))
            db.execute('INSERT INTO steps VALUES(?,?,?,?,?)',(scene_id,'repair','ATTEMPTED',rows[0]['elementId']['guid'],canonical(intent)))
            db.commit()
            try:
                if self.guarded_binding()!=preflight['binding']:
                    raise ValueError('MORPH_CHANGE_PROJECT_DRIFT')
                reply=self.api(command,parameters)
                if reply.get('executionResults')!=[{'success':True}]:
                    raise ValueError('MORPH_CHANGE_NOT_CONFIRMED')
                if self.guarded_binding()!=preflight['binding']:
                    raise ValueError('MORPH_CHANGE_TARGET_CHANGED_AFTER_WRITE')
                result['readback']=verify_after()
                result['status']='EXISTING_MORPH_BODY_READBACK_PASS'
                db.execute("UPDATE steps SET state='PASS',output=? WHERE scene_id=? AND step_id='repair'",(canonical(result),scene_id))
            except Exception as exc:
                result.update(status='PARTIAL_OR_UNKNOWN_OUTCOME',reason=type(exc).__name__+': '+str(exc),manualReconciliationRequired=True)
            db.execute('UPDATE scenes SET state=?,result=? WHERE scene_id=?',(result['status'],canonical(result),scene_id));db.commit()
        return result

    def guarded_binding(self):
        if not self.allow_3d_view_for_write:
            return guarded_project(self.api, self.required_story)
        # A native BREP dump regenerates the 3D view (actStory=-1). Under
        # an EXACTLY hashed, explicitly authorized saved copy, permit only
        # view 3D or the pinned first floor, not some other active story.
        # This does not permit arbitrary PLN writes or bypass story topology.
        if (self.required_story is not None or
                _SAVED_COPY_AUTHORIZATION is None or
                not authorized_authored_target(EXPECTED_PATH)):
            raise ValueError('3D_WRITER_REQUIRES_EXACT_SAVED_COPY_AUTHORIZATION')
        b = guarded_project_for_read(self.api)
        if b['activeViewStoryIndex'] not in (0, -1):
            raise ValueError('3D_WRITER_REQUIRES_3D_OR_STORY_ZERO')
        return {'path':b['path'], 'name':b['name'],
                'port':b['port'], 'tapirVersion':b['tapirVersion'],
                'storyIndex':0}

    def verify_source_bindings(self,preflight):
        binding=preflight.get('integrationBindings',{}).get('dependencies',{}).get('sourceRoofTrimBinding')
        if binding is not None:
            from archicad_native_operations import verify_roof_trim_source
            verify_roof_trim_source(self.api,binding)
        repair=preflight.get('integrationBindings',{}).get('dependencies',{}).get('wallRoofRepair')
        if repair is not None:
            from archicad_native_operations import verify_roof_trim_source
            verify_roof_trim_source(self.api,{'sourceBodies':[repair['nativeBindings'][1]]})

    def execute_bound_operation(self, preflight, scene_id, command, parameters,
                                expected_hash, verify_before, verify_after):
        """Opt-in non-create adapters use this same SceneWriter/SQLite ledger.

        Callbacks prove current ownership/geometry before the durable intent
        and independently read the resulting native relations after one call.
        No replay, second executor or automatic rollback.
        """
        documentation=preflight.get('integrationBindings',{}).get('dependencies',{}).get('documentationOperation')
        model_scope=preflight.get('integrationBindings',{}).get('dependencies',{}).get('modelOperation')
        spatial_scope=preflight.get('integrationBindings',{}).get('dependencies',{}).get('spatialOperation')
        dynamic_scope=preflight.get('integrationBindings',{}).get('dependencies',{}).get('dynamicOperation')
        if sum(x is not None for x in (documentation,model_scope,spatial_scope,dynamic_scope))>1:
            raise ValueError('EXACTLY_ONE_BOUNDED_OPERATION_SCOPE_REQUIRED')
        dynamic_command=dynamic_scope is not None
        if dynamic_command:
            router=getattr(self.api,'dynamic_commands',None)
            if router is None:raise ValueError('DYNAMIC_COMMAND_ROUTER_NOT_BOUND')
            router.qualify_scope(dynamic_scope,command,parameters,preflight['sourcePlanHash'])
            if dynamic_scope['binding']!=preflight['binding']:raise ValueError('DYNAMIC_PROJECT_BINDING_DRIFT')
        spatial_command=False
        if spatial_scope is not None:
            from archicad_native_spatial_structure import qualify_spatial_operation
            qualify_spatial_operation(spatial_scope,command,parameters,preflight['sourcePlanHash'])
            spatial_command=True
        model_command=False
        if model_scope is not None:
            from archicad_authored_extension import qualify_model_operation
            qualify_model_operation(model_scope,command,parameters,preflight['sourcePlanHash'])
            model_command=True
        document_command=False
        if documentation is not None:
            from archicad_bim_documentation import qualify_operation, DOCUMENT_COMMANDS
            qualify_operation(documentation,command,parameters,preflight['sourcePlanHash'])
            document_command=command in DOCUMENT_COMMANDS
        if (not dynamic_command and not document_command and not model_command and not spatial_command and command not in {'ConnectMEPElements','ModifyMEPRoutingElements',
                            'CreateOpenings','CreateSolidElementLinks','RemoveSolidElementLinks','ModifyMorphs','ModifyBeams','ModifyWalls','SetClassificationsOfElements','TrimElements'}
                or not _SCENE_ID.fullmatch(scene_id) or not callable(verify_before) or not callable(verify_after)):
            raise ValueError('BOUNDED_OPERATION_ADAPTER_REQUIRED')
        intent={'sceneId':scene_id,'sourcePlanHash':preflight['sourcePlanHash'],
                'command':command,'parameters':parameters,'target':preflight['binding']}
        if digest(intent)!=expected_hash:raise ValueError('BOUNDED_OPERATION_HASH_MISMATCH')
        slots={'ConnectMEPElements':'connectionsData','ModifyMEPRoutingElements':'routingElementsData',
               'CreateOpenings':'openingsData','CreateSolidElementLinks':'solidLinks','RemoveSolidElementLinks':'solidLinks','ModifyMorphs':'morphsWithDetails',
               'SetClassificationsOfElements':'elementClassifications','ModifyBeams':'beamsWithDetails','ModifyWalls':'wallsWithDetails','TrimElements':'elements'}
        rows=parameters.get(slots.get(command))
        if not dynamic_command and not document_command and not model_command and not spatial_command and (not isinstance(rows,list) or len(rows)!=1):raise ValueError('BOUNDED_OPERATION_REQUIRES_SINGLE_NATIVE_TARGET')
        if not dynamic_command and command=='ModifyWalls' and documentation is None and model_scope is None:
            repair=preflight.get('integrationBindings',{}).get('dependencies',{}).get('wallRoofRepair',{})
            candidates=repair.get('operationCandidates',[])
            if (repair.get('status')!='APPLICABLE_NOT_EXECUTED' or not repair.get('executionAllowed') or
                    repair.get('assessmentHash')!=digest({k:v for k,v in repair.items() if k!='assessmentHash'}) or
                    len(candidates)!=2 or parameters!=candidates[0].get('params') or
                    set(parameters)!={'wallsWithDetails'} or set(rows[0])!={'elementId','height'}):
                raise ValueError('BOUNDED_WALL_HEIGHT_REQUIRES_QUALIFIED_EXACT_JUNCTION_PLAN')
        if not dynamic_command and command=='ModifyBeams' and ('CreateBeams' not in self.adapters or set(rows[0])!={'elementId','profileAngle'}):
            raise ValueError('BOUNDED_BEAM_PROFILE_REQUIRES_TYPED_ADAPTER_AND_EXPLICIT_ANGLE')
        if not dynamic_command and command=='TrimElements' and ('CreateRoofs' not in self.adapters or
                set(parameters)!={'elements','trimmingElement','trimType'} or parameters['trimType']!='KeepInside'):
            raise ValueError('BOUNDED_ROOF_TRIM_REQUIRES_TYPED_ROOF_AND_EXPLICIT_INSIDE')
        if not dynamic_command and command=='ModifyMorphs' and ('CreateMorphs' not in self.adapters or
                set(rows[0]) not in ({'elementId','xAxis','yAxis','zAxis'},{'elementId','translation'})):
            raise ValueError('BOUNDED_MORPH_PLACEMENT_REQUIRES_TYPED_ADAPTER_AND_EXPLICIT_TRANSFORM')
        if command=='ModifyMorphs' or dynamic_command and 'Morph' in command:
            from archicad_native_beam_details import require_morph_last_resort
            require_morph_last_resort(preflight.get('integrationBindings',{}).get('dependencies',{}))
        if not dynamic_command and command=='SetClassificationsOfElements' and ('CreateMorphs' not in self.adapters or
                set(rows[0])!={'elementId','classificationId'} or
                set(rows[0].get('classificationId',{}))!={'classificationSystemId','classificationItemId'}):
            raise ValueError('BOUNDED_CLASSIFICATION_REQUIRES_TYPED_NEW_MEMBER_AND_EXPLICIT_ITEM')
        if dynamic_command:
            if command=='OpenProject' and parameters!={'projectFilePath':preflight['binding']['path']}:raise ValueError('DYNAMIC_OPEN_FOREIGN_PROJECT_DENIED')
            router.validate(dynamic_scope['ticket']);checked={'status':'SCHEMA_VALID'}
        elif document_command and command in {'SaveProject','OpenProject','PublishPublisherSet'}:
            # SPECIAL_REVIEW stays unexecutable in ordinary writer operations;
            # only this explicit, bound documentation persistence opts in.
            if command=='OpenProject' and parameters!={'projectFilePath':preflight['binding']['path']}:
                raise ValueError('DOCUMENTATION_OPEN_FOREIGN_PROJECT_DENIED')
            catalog=SCENE.GRAPH.CONTRACTS.load_catalog(self.schema_path)
            checked={'status':'SCHEMA_VALID' if SCENE.GRAPH.CONTRACTS.source_version(catalog)==EXPECTED_TAPIR and
                not list(SCENE.GRAPH.CONTRACTS._validator(catalog,command).iter_errors(parameters)) else 'INVALID'}
        else:
            checked=SCENE.GRAPH.CONTRACTS.compile_batch(SCENE.GRAPH.CONTRACTS.load_catalog(self.schema_path),
                {'requests':[{'id':'operation','command':command,'params':parameters}]},runtime_version=EXPECTED_TAPIR)
        if checked['status']!='SCHEMA_VALID':raise ValueError('BOUNDED_OPERATION_SCHEMA_INVALID')
        if self.guarded_binding()!=preflight['binding']:raise ValueError('BOUNDED_OPERATION_TARGET_DRIFT')
        self.verify_source_bindings(preflight)
        before=verify_before()
        result={'status':'BLOCKED','automaticRetry':False,'sceneId':scene_id,'command':command,'operationHash':expected_hash,'intent':intent}
        with closing(sqlite3.connect(self.journal_path)) as db:
            db.execute('PRAGMA synchronous=FULL')
            db.execute('CREATE TABLE IF NOT EXISTS scenes (scene_id TEXT PRIMARY KEY, plan_hash TEXT NOT NULL, state TEXT NOT NULL, result TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS steps (scene_id TEXT NOT NULL, step_id TEXT NOT NULL, state TEXT NOT NULL, guid TEXT, output TEXT NOT NULL, PRIMARY KEY(scene_id,step_id))')
            db.commit();db.execute('BEGIN IMMEDIATE')
            if db.execute('SELECT 1 FROM scenes WHERE scene_id=? OR plan_hash=?',(scene_id,expected_hash)).fetchone():
                raise ValueError('BOUNDED_OPERATION_RESERVED_NEVER_RETRY')
            db.execute('INSERT INTO scenes VALUES(?,?,?,?)',(scene_id,expected_hash,'STARTED',canonical(result)))
            db.execute('INSERT INTO steps VALUES(?,?,?,?,?)',(scene_id,'operation','ATTEMPTED',None,canonical({'intent':intent,'before':before})));db.commit()
            try:
                if self.guarded_binding()!=preflight['binding']:raise ValueError('BOUNDED_OPERATION_TARGET_DRIFT')
                if dynamic_command:
                    with self.api.dynamic_call(dynamic_scope['ticket'],journal_scope=dynamic_scope):reply=self.api(command,parameters)
                else:reply=self.api(command,parameters)
                result['nativeResponse']=reply
                if dynamic_command:
                    router.validate_result(command,reply)
                elif spatial_command:
                    if reply!={'success':True}:raise ValueError('SPATIAL_NATIVE_SUCCESS_NOT_CONFIRMED')
                elif document_command:
                    from archicad_bim_documentation import native_response
                    guid=native_response(command,reply)
                    if guid:
                        result['createdGuid']=guid
                        db.execute("UPDATE steps SET state='CREATED_UNVERIFIED',guid=? WHERE scene_id=? AND step_id='operation'",(guid,scene_id));db.commit()
                elif command in {'CreateRoofs','CreateStairs','CreateNativeGridElementsV1','CreateExactStairsV1'} and model_command:
                    result['createdGuid']=created_guid(reply)
                    db.execute("UPDATE steps SET state='CREATED_UNVERIFIED',guid=? WHERE scene_id=? AND step_id='operation'",(result['createdGuid'],scene_id));db.commit()
                elif command=='ModifyRoofs' and model_command:
                    rows=reply.get('executionResults')
                    if not isinstance(rows,list) or len(rows)!=len(parameters['roofsWithDetails']) or any(row!={'success':True} for row in rows):
                        raise ValueError('BOUNDED_ROOF_BATCH_PARTIAL_OR_UNKNOWN')
                elif command=='TrimElements':
                    if reply!={'success':True}:raise ValueError('BOUNDED_TRIM_NATIVE_SUCCESS_NOT_CONFIRMED')
                elif command != 'CreateOpenings':
                    key = 'connectionResults' if command == 'ConnectMEPElements' else 'executionResults'
                    rows = reply.get(key)
                    if not isinstance(rows, list) or len(rows) != 1 or any('error' in r for r in rows):
                        raise ValueError('BOUNDED_OPERATION_NATIVE_RESPONSE_REJECTED')
                    if command != 'ConnectMEPElements' and rows[0].get('success') is not True:
                        raise ValueError('BOUNDED_OPERATION_NATIVE_SUCCESS_NOT_CONFIRMED')
                if command=='CreateOpenings' and not dynamic_command:
                    result['createdGuid']=created_guid(reply)
                    db.execute("UPDATE steps SET state='CREATED_UNVERIFIED',guid=? WHERE scene_id=? AND step_id='operation'",(result['createdGuid'],scene_id));db.commit()
                if self.guarded_binding()!=preflight['binding']:raise ValueError('BOUNDED_OPERATION_AFTER_TARGET_DRIFT')
                result['readback']=verify_after(reply,before)
                if not isinstance(result['readback'],dict) or not str(result['readback'].get('status','')).endswith('PASS'):
                    raise ValueError('BOUNDED_OPERATION_INDEPENDENT_READBACK_NOT_CONFIRMED')
                result['status']='PASS'
                db.execute("UPDATE steps SET state='PASS',output=? WHERE scene_id=? AND step_id='operation'",(canonical(result),scene_id))
            except Exception as exc:
                result.update(status='PARTIAL_OR_UNKNOWN_OUTCOME',reason=type(exc).__name__+': '+str(exc),manualReconciliationRequired=True)
                db.execute("UPDATE steps SET state='UNKNOWN_OUTCOME',output=? WHERE scene_id=? AND step_id='operation'",(canonical(result),scene_id))
            db.execute('UPDATE scenes SET state=?,result=? WHERE scene_id=?',(result['status'],canonical(result),scene_id));db.commit()
        return result

    def preflight(self, x, y):
        preview = (self.preview_factory(x, y, self.schema_path)
                   if self.preview_factory is not None
                   else SCENE.prepare(x, y, self.schema_path))
        bindings = preview.get("storyBindings")
        self.required_story = bindings[0] if bindings else None
        binding = self.guarded_binding()
        target = preview.get("nativeTargetProjectPath")
        if target is not None and target != binding["path"]:
            raise ValueError("AUTHORED_TARGET_DIFFERS_FROM_WRITER_BINDING")
        if bindings:
            stories = self.api("GetStories", {}).get("stories")
            if not isinstance(stories, list):
                raise ValueError("STORY_MAP_UNAVAILABLE")
            for binding_row in bindings:
                actual = next((r for r in stories if
                               r.get("index") == binding_row["nativeIndex"]), None)
                if (not actual or actual.get("floorId") != binding_row["floorId"]
                        or not close(actual.get("level"), binding_row["level"])
                        or (actual.get("name") or actual.get("uName") or "") != binding_row["label"]):
                    raise ValueError("UNVERIFIED_NAMED_STORY: " + binding_row["label"])
        if preview["schemaVersion"] != binding["tapirVersion"]:
            raise ValueError("TAPIR_SCHEMA_VERSION_MISMATCH")
        basic_name = preview.get("slabBasicMaterialName")
        material_guid = (resolve_basic_slab_material(self.api, basic_name)
                         if basic_name is not None else None)
        pinned_material = preview.get("expectedPreflightSlabMaterialGuid")
        if pinned_material is not None and (
                not isinstance(material_guid, str)
                or material_guid.casefold() != pinned_material.casefold()):
            raise ValueError("AUTHORED_SLAB_MATERIAL_CHANGED_BEFORE_PREFLIGHT")
        preview["slabBasicMaterialGuid"] = material_guid
        preview["sourcePlanHash"] = native_plan_hash(preview,preview["sourcePlanHash"])
        scan_report = scan_for_existing_geometry(self.api, x, y, preview.get("envelope"))
        if self.guarded_binding() != binding:
            raise ValueError("project binding changed during read-only preflight")
        return {**preview, "status": "READY_FOR_EXPLICIT_TEST_RUN",
                "binding": binding, **scan_report,
                "liveWriteAuthorized": False, "plnChanged": False}

    def execute(self, x, y, scene_id, expected_hash):
        if not isinstance(scene_id, str) or not _SCENE_ID.fullmatch(scene_id):
            raise ValueError("invalid durable scene ID")
        preflight = self.preflight(x, y)
        if preflight["sourcePlanHash"] != expected_hash:
            raise ValueError("PLAN_HASH_MISMATCH: get hash from same-anchor dry-run")
        return self._execute_verified_plan(preflight, scene_id, expected_hash)

    def _execute_verified_plan(self, preflight, scene_id, expected_hash,
                               seeded_created=None, approval_source=None,
                               on_before_complete=None):
        """Same existing one-shot SceneWriter, with externally verified prefix.

        Only recovery after exact immutable old-ledger + current-native matching
        can supply a nonempty prefix. Never invokes preflight's spatial collision
        scanner for a scene that legitimately already contains its first steps.
        """
        seeded_created = dict(seeded_created or {})
        if (not isinstance(scene_id, str) or not _SCENE_ID.fullmatch(scene_id)
                or preflight["sourcePlanHash"] != expected_hash):
            raise ValueError("RESUME_PLAN_OR_ID_MISMATCH")
        if not self.journal_path.parent.exists():
            raise ValueError("journal state directory must already exist")
        result = {
            "sceneId": scene_id, "planHash": expected_hash, "status": "BLOCKED",
            "plnSaved": False, "automaticRetry": False, "steps": {},
            "sceneDimensions": preflight["metrics"]["dimensionsMeters"],
            "reusedCount": len(seeded_created),
        }
        with closing(sqlite3.connect(str(self.journal_path))) as db:
            db.execute("PRAGMA synchronous=FULL")
            db.execute("CREATE TABLE IF NOT EXISTS scenes (scene_id TEXT PRIMARY KEY, plan_hash TEXT NOT NULL, state TEXT NOT NULL, result TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS steps (scene_id TEXT NOT NULL, step_id TEXT NOT NULL, state TEXT NOT NULL, guid TEXT, output TEXT NOT NULL, PRIMARY KEY(scene_id,step_id))")
            db.commit()
            db.execute("BEGIN IMMEDIATE")
            if db.execute("SELECT 1 FROM scenes WHERE scene_id=? OR plan_hash=?",
                          (scene_id, expected_hash)).fetchone():
                raise ValueError("SCENE_ALREADY_RESERVED: never replay ambiguous write")
            db.execute("INSERT INTO scenes VALUES (?,?,?,?)",
                       (scene_id, expected_hash, "STARTED", canonical(result)))
            db.commit()
            created = {"__plan__": preflight["graph"], **seeded_created}
            for sid, prior in seeded_created.items():
                result["steps"][sid] = {
                    "status": "REUSED_VERIFIED", "guid": prior["guid"],
                    "kind": prior["kind"], "floorIndex": prior["floorIndex"]}
            for step_id in preflight["executionOrder"]:
                if step_id in seeded_created:
                    continue
                step = next(s for s in preflight["graph"]["operations"] if s["id"] == step_id)
                command = step["command"]
                if command not in self.allowed_writes:
                    raise ValueError("UNSUPPORTED_WRITE_RECIPE")
                try:
                    # The FULL project identity is freshly checked at every step.
                    if self.guarded_binding() != preflight["binding"]:
                        raise ValueError("PROJECT_SWITCHED_DURING_SCENE")
                    parent_guid = None
                    if command in ("CreateWindows", "CreateDoors"):
                        parent_guid = check_previous_wall(
                            self.api, step, created, preflight.get("storyBindings"))
                    adapter = self.adapters.get(command)
                    if adapter is not None:
                        params = adapter.resolve(step, created, preflight)
                        # Compile against the same installed schema immediately
                        # before durable reservation; no unchecked plug-in payload.
                        catalog = SCENE.GRAPH.CONTRACTS.load_catalog(self.schema_path)
                        validated = SCENE.GRAPH.CONTRACTS.compile_batch(catalog,
                            {'requests':[{'id':step_id,'command':command,'params':params}]},
                            runtime_version=EXPECTED_TAPIR)
                        if validated['status'] != 'SCHEMA_VALID':
                            raise ValueError('ADAPTER_PARAMETERS_INVALID')
                        if callable(getattr(adapter,'before_write',None)):
                            adapter.before_write(self.api,params,preflight)
                    else:
                        params = resolve_params(step, created)
                    self.verify_source_bindings(preflight)
                    # Bind each operation to its exact resolved (including GUID)
                    # parameters, approved local test scope, source scene and target.
                    intent = {"sceneId": scene_id, "planHash": expected_hash,
                              "stepId": step_id, "command": command,
                              "parameters": params, "target": preflight["binding"]}
                    approval_record = {
                        "operationHash": digest(intent),
                        "permission": command,
                        "scope": EXPECTED_PATH,
                        "approvedBy": "local-explicit--execute-with-matching-plan-hash",
                        "approvedAt": datetime.now(timezone.utc).isoformat(),
                        "approvalSource": approval_source or "standing-test-PLN-permission",
                    }
                    if approval_record["permission"] not in self.allowed_writes:
                        raise ValueError("UNREVIEWED_WRITE_SCOPE")
                    db.execute("BEGIN IMMEDIATE")
                    db.execute("INSERT INTO steps VALUES (?,?,?,?,?)",
                               (scene_id, step_id, "ATTEMPTED", None, canonical({
                                   "intent": intent, "localApproval": approval_record
                               })))
                    db.commit()  # Durable per-operation approval and intent BEFORE write.
                    if (self.guarded_binding() != intent["target"]
                            or digest(intent) != approval_record["operationHash"]
                            or approval_record["scope"] != EXPECTED_PATH):
                        raise ValueError("OPERATION_BOUNDARY_APPROVAL_MISMATCH")
                    raw = self.api(command, params)
                    guid = created_guid(raw)
                    db.execute("UPDATE steps SET state='CREATED_UNVERIFIED',guid=? WHERE scene_id=? AND step_id=?",
                               (guid, scene_id, step_id))
                    db.commit()
                    if self.guarded_binding() != preflight["binding"]:
                        raise ValueError("PROJECT_CHANGED_AFTER_WRITE")
                    basic_guid = preflight.get("slabBasicMaterialGuid")
                    if command == "CreateSlabs" and basic_guid:
                        # Read the newly created element BEFORE attempting the
                        # second native mutation. The first GUID is never replayed.
                        intermediate = requested_details(self.api, guid)
                        floor = params["slabsData"][0]["floorIndex"]
                        verify_readback(command, params, intermediate,
                                        expected_floor=floor,
                                        expected_story_level=story_level_for_floor(
                                            preflight.get("storyBindings"),floor),
                                        slab_level_is_absolute=(preflight.get("slabLevelConvention")=="PROJECT_ABSOLUTE"),
                                        allow_slab_thickness_mismatch=True)
                        modify = {"slabsWithDetails": [{
                            "elementId": {"guid": guid},
                            "structureType": "Basic",
                            "thickness": params["slabsData"][0]["thickness"],
                            "buildingMaterialId": {"guid": basic_guid},
                        }]}
                        modify_intent = {
                            "sceneId": scene_id, "planHash": expected_hash,
                            "stepId": step_id, "command": "ModifySlabs",
                            "parameters": modify, "target": preflight["binding"],
                            "createdGuid": guid,
                            "approval": approval_record,
                        }
                        db.execute("UPDATE steps SET state=?,output=? "
                                   "WHERE scene_id=? AND step_id=?",
                                   ("BASIC_MODIFY_ATTEMPTED", canonical(modify_intent),
                                    scene_id, step_id))
                        db.commit()  # Crash-safe BEFORE ModifySlabs native call.
                        if self.guarded_binding() != preflight["binding"]:
                            raise ValueError("PROJECT_CHANGED_BEFORE_SLAB_MODIFY")
                        modified = self.api("ModifySlabs", modify)
                        responses = (modified.get("executionResults")
                                     if isinstance(modified, dict) else None)
                        if (not isinstance(responses, list) or len(responses) != 1
                                or responses[0].get("success") is not True):
                            raise ValueError("BASIC_SLAB_MODIFY_NOT_CONFIRMED")
                    row = requested_details(self.api, guid)
                    if command in ("CreateWindows", "CreateDoors"):
                        owner_ref = step["params"][command[6:].lower()+"Data"][0]["ownerWallId"]["guid"]["$createdGuid"]
                        floor_index = created[owner_ref]["floorIndex"]
                    elif adapter is not None:
                        floor_index = adapter.floor(params, preflight)
                    else:
                        floor_index = next(iter(params.values()))[0]["floorIndex"]
                    if adapter is not None:
                        kind = adapter.verify(self.api, guid, params, row, floor_index,
                            story_level_for_floor(preflight.get('storyBindings'),floor_index))
                    else:
                        kind = verify_readback(
                            command, params, row, parent_guid,
                            expected_floor=floor_index,
                            expected_story_level=story_level_for_floor(
                                preflight.get("storyBindings"), floor_index),
                            expected_slab_material_guid=(
                                preflight.get("slabBasicMaterialGuid")
                                if command == "CreateSlabs" else None),
                            slab_level_is_absolute=(preflight.get("slabLevelConvention")=="PROJECT_ABSOLUTE"))
                    created[step_id] = {"guid": guid, "kind": kind, "floorIndex": floor_index}
                    result["steps"][step_id] = {"status": "PASS", "guid": guid, "kind": kind}
                    db.execute("UPDATE steps SET state='PASS',output=? WHERE scene_id=? AND step_id=?",
                               (canonical(result["steps"][step_id]), scene_id, step_id))
                    db.commit()
                except Exception as exc:
                    # A native call can succeed and then time out or read back poorly.
                    # Always stop and never retry, undo, or erase the step ledger.
                    result["status"] = "PARTIAL_OR_UNKNOWN_OUTCOME"
                    result["failedStep"] = step_id
                    result["reason"] = type(exc).__name__ + ": " + str(exc)
                    result["manualReconciliationRequired"] = True
                    db.execute("UPDATE scenes SET state=?,result=? WHERE scene_id=?",
                               (result["status"], canonical(result), scene_id))
                    db.commit()
                    return result
            if on_before_complete is not None:
                try:
                    on_before_complete(preflight, created)
                except Exception as exc:
                    result["status"] = "PARTIAL_OR_UNKNOWN_OUTCOME"
                    result["failedStep"] = "FINAL_READBACK"
                    result["reason"] = type(exc).__name__ + ": " + str(exc)
                    result["manualReconciliationRequired"] = True
                    db.execute("UPDATE scenes SET state=?,result=? WHERE scene_id=?",
                               (result["status"], canonical(result), scene_id))
                    db.commit()
                    return result
            result["status"] = "COMPLETE_UNSAVED"
            result["createdCount"] = len(result["steps"])
            result["newCreatedCount"] = len(result["steps"]) - len(seeded_created)
            result["allGuidsReadback"] = True
            db.execute("UPDATE scenes SET state=?,result=? WHERE scene_id=?",
                       (result["status"], canonical(result), scene_id))
            db.commit()
            return result


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--anchor-x", type=float, required=True)
    p.add_argument("--anchor-y", type=float, required=True)
    p.add_argument("--data-dir", type=Path, required=True,
                   help="existing local state directory; separate scene journal is added")
    p.add_argument("--summary", action="store_true",
                   help="short read-only preflight report without entire 12-step graph")
    p.add_argument("--schema", type=Path, default=DEFAULT_SCENE_SCHEMA,
                   help="actual Tapir snapshot; defaults to tapir-scene-live.json beside this script")
    p.add_argument("--execute", action="store_true",
                   help="actually create scene once inside exact pinned test PLN")
    p.add_argument("--scene-id", help="durable unique name, NEVER reuse")
    p.add_argument("--confirm-plan-hash", help="hash printed by read-only preflight")
    args = p.parse_args(argv)
    try:
        api = lambda command, params: tapir(PORT, command, params)
        runner = SceneWriter(api, args.data_dir / "scene-v1-attempts.sqlite3", args.schema)
        if args.execute:
            if not args.scene_id or not args.confirm_plan_hash:
                raise ValueError("--execute requires --scene-id and --confirm-plan-hash")
            out = runner.execute(args.anchor_x, args.anchor_y,
                                 args.scene_id, args.confirm_plan_hash)
        else:
            out = runner.preflight(args.anchor_x, args.anchor_y)
        if args.summary and not args.execute:
            keys = ("status", "sourcePlanHash", "binding", "metrics",
                    "schemaPath", "schemaVersion", "schemaSha256",
                    "nativeElementsInspected", "volumetricBodiesChecked",
                    "nonSpatialElementsVerified", "liveWriteAuthorized",
                    "plnChanged")
            out = {key: out[key] for key in keys if key in out}
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0 if out["status"] in ("READY_FOR_EXPLICIT_TEST_RUN", "COMPLETE_UNSAVED") else 2
    except Exception as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc),
                          "automaticRetry": False, "plnSaved": False},
                         ensure_ascii=False))
        return 2


if __name__ == "__main__":
    sys.exit(main())
