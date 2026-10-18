"""One high-level AC29 native-group acceptance job, using the existing Tapir commands.

Never modify the source PLN/BDD. Copy a pinned local test PLN, OpenProject on
the approved Archicad instance, choose 2 ungrouped columns, group/clone/move/
ungroup with independent GUID and geometry readback, save only the scratch PLN.
No remote shell commands; no auto-retries after a partially attempted job.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
import msvcrt
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
import urllib.request

import apa_ac29_apx_build_mailbox as mailbox

BRIDGE = "dvikt33-ux/safe-bim-bridge"
MAILBOX_BRANCH = "feature/apa-ac29-apx-build-mailbox-20261018"
INBOX = "safe-bim-mailbox/apa-ac29-group-acceptance/jobs"
OUTBOX = "safe-bim-mailbox/apa-ac29-group-acceptance/results"
SOURCE_REPO = "dvikt33-ux/safe-bim-layer"
SOURCE_PATH = Path(r"C:\LocalAI\APA_Functional_Test_House_01.pln")
PORT = 19724
SCHEMA = "APA_AC29_GROUP_ACCEPTANCE_V1"
JOB_ID = re.compile(r"^group-[a-z0-9-]{8,55}$")
HEX = re.compile(r"^[a-f0-9]{40}$")
GUID = re.compile(r"^[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}$")
COORDS = ("xMin", "xMax", "yMin", "yMax", "zMin", "zMax")
# Reuse the conservative typed nonspatial classification from the existing
# SceneWriter collision preflight; never ignore an unknown 3D member.
NONSPATIAL_TYPES = frozenset({
    "Dimension", "RadialDimension", "LevelDimension", "AngleDimension",
    "Text", "Label", "Hatch", "Line", "PolyLine", "Arc", "Circle",
    "Spline", "Hotspot", "CutPlane", "Camera", "CamSet", "Group",
    "SectElem", "Drawing", "Picture", "Detail", "Elevation",
    "InteriorElevation", "Worksheet", "ChangeMarker",
})



def need(condition, reason):
    if not condition:
        raise RuntimeError(reason)


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1048576), b""):
            h.update(block)
    return h.hexdigest()


def canonical_path(path):
    return os.path.normcase(os.path.abspath(str(path)))


def request(command, params, *, addon=False, timeout=30):
    if addon:
        payload = {
            "command": "API.ExecuteAddOnCommand",
            "parameters": {
                "addOnCommandId": {
                    "commandNamespace": "TapirCommand",
                    "commandName": command
                },
                "addOnCommandParameters": params
            }
        }
    else:
        payload = {"command": command, "parameters": params}
    query = urllib.request.Request(
        f"http://127.0.0.1:{PORT}",
        data=json.dumps(payload, ensure_ascii=False).encode("utf8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(query, timeout=timeout) as response:
        reply = json.loads(response.read().decode("utf8"))
    need(reply.get("succeeded") is True, f"ARCHICAD_CALL_FAILED:{command}:"
         + repr(reply.get("error"))[:400])
    value = reply.get("result", {})
    if addon:
        value = value.get("addOnCommandResponse")
    need(isinstance(value, dict), "ARCHICAD_RESPONSE_NOT_OBJECT:" + command)
    need("error" not in value, "NATIVE_COMMAND_FAILED:" + command + ":" + repr(value.get("error")))
    return value


def project():
    return request("GetProjectInfo", {}, addon=True)


def guard(expected, original_hash):
    info = project()
    need(info.get("isUntitled") is False and info.get("isTeamwork") is False,
         "UNSAVED_OR_TEAMWORK_PROJECT_BLOCKED")
    need(canonical_path(info.get("projectPath", "")) == canonical_path(expected),
         "PROJECT_SWITCH_DETECTED:" + repr(info.get("projectPath")))
    need(SOURCE_PATH.is_file() and digest(SOURCE_PATH) == original_hash,
         "ORIGINAL_TEST_PLN_DISK_CHANGED")
    return info


def read_elements():
    data = request("GetAllElements", {}, addon=True)
    rows = data.get("elements", [])
    need(isinstance(rows, list) and 6 <= len(rows) <= 5000, "UNEXPECTED_INVENTORY_SIZE")
    ids = [row.get("elementId", {}).get("guid", "") for row in rows]
    need(all(GUID.fullmatch(x) for x in ids) and len(set(ids)) == len(ids),
         "INVALID_OR_DUPLICATE_INVENTORY_GUIDS")
    return ids


def batched(command, guids, key, size=40):
    result = []
    for i in range(0, len(guids), size):
        batch = [{"elementId": {"guid": x}} for x in guids[i:i + size]]
        received = request(command, {"elements": batch}, addon=True).get(key, [])
        need(isinstance(received, list) and len(received) == len(batch),
             command + "_INCOMPLETE_READBACK")
        result.extend(received)
    return result


def boxes(guids):
    rows = batched("Get3DBoundingBoxes", guids, "boundingBoxes3D")
    converted = []
    for row in rows:
        box = row.get("boundingBox3D") if isinstance(row, dict) else None
        if isinstance(box, dict) and all(
            type(box.get(k)) in (int, float) and math.isfinite(box[k]) for k in COORDS
        ) and all(box[a] <= box[b] for a, b in [("xMin", "xMax"), ("yMin", "yMax"), ("zMin", "zMax")]):
            converted.append(box)
        else:
            converted.append(None)
    return converted


def group_roots(guids):
    return batched("GetNativeGroupRootsV1", guids, "groups")


def null_group(value):
    guid = (value or {}).get("guid", "") if isinstance(value, dict) else ""
    return isinstance(guid, str) and guid.replace("-", "").strip("0") == ""


def elements_of_group(group_id):
    result = request("GetNativeGroupMembersV1", {"groupId": {"guid": group_id}}, addon=True)
    need(result.get("nativeModelWrites") == 0, "GROUP_READ_UNEXPECTED_WRITE")
    elements = [v.get("guid", "") for v in result.get("memberIds", [])]
    need(all(GUID.fullmatch(v) for v in elements), "INVALID_GROUP_MEMBER_GUID")
    return elements


def native_owned_children(parent_ids, preexisting_ids):
    """Read complete typed child inventory for explicitly copied native parents.

    A Column/Beam created by ACAPI_Element_Edit can own newly created
    ColumnSegment/BeamSegment GUIDs that GetAllElements reports independently.
    Never accept the extra GUIDs by arithmetic alone; obtain each parent-child
    relation from the existing native hierarchical subelement API.
    """
    need(len(parent_ids) == len(set(g.lower() for g in parent_ids)),
         "DUPLICATE_COPIED_PARENT_IDS")
    need(all(GUID.fullmatch(x or "") for x in parent_ids),
         "INVALID_COPIED_PARENT_ID")
    details = batched("GetDetailsOfElements", parent_ids, "detailsOfElements")
    response = batched(
        "GetSubelementsOfHierarchicalElements", parent_ids, "subelements"
    )
    seen = set()
    by_parent = {}
    pairs = []
    for parent, detail, row in zip(parent_ids, details, response):
        kind = detail.get("type") if isinstance(detail, dict) else None
        slot, child_type = {
            "Column": ("columnSegments", "ColumnSegment"),
            "Beam": ("beamSegments", "BeamSegment"),
        }.get(kind, (None, None))
        need(slot is not None and isinstance(row, dict),
             "COPIED_PARENT_NOT_SUPPORTED_STRUCTURAL_TYPE:" + str(kind))
        children = row.get(slot)
        need(isinstance(children, list) and len(children) > 0
             and set(row.keys()) == {slot},
             "COPIED_PARENT_NATIVE_SEGMENT_HIERARCHY_UNVERIFIED:" + parent)
        ids = []
        for child in children:
            value = child.get("elementId", {}).get("guid") if isinstance(child, dict) else None
            need(isinstance(value, str) and GUID.fullmatch(value),
                 "COPIED_CHILD_GUID_INVALID:" + parent)
            value = value.lower()
            need(value not in seen and value not in preexisting_ids
                 and value not in {x.lower() for x in parent_ids},
                 "COPIED_CHILD_ID_COLLIDES_WITH_OTHER_ELEMENT:" + value)
            seen.add(value)
            ids.append(value)
            pairs.append((value, child_type))
        by_parent[parent.lower()] = ids
    types = batched("GetDetailsOfElements",
                    [value for value, _ in pairs], "detailsOfElements")
    for (value, expected), row in zip(pairs, types):
        need(isinstance(row, dict) and row.get("type") == expected,
             "COPIED_CHILD_NATIVE_TYPE_MISMATCH:" + value)
    return by_parent, seen


def choose_pair(guids):
    details = batched("GetDetailsOfElements", guids, "detailsOfElements")
    columns = [guid for guid, row in zip(guids, details)
               if isinstance(row, dict) and row.get("type") == "Column"]
    need(len(columns) >= 2, "AT_LEAST_TWO_COLUMNS_REQUIRED")
    candidates = columns[:40]
    roots = group_roots(candidates)
    col_boxes = boxes(candidates)
    available = [(guid, bbox) for guid, root, bbox in zip(candidates, roots, col_boxes)
                 if isinstance(root, dict) and "error" not in root
                 and null_group(root.get("groupId"))
                 and null_group(root.get("rootGroupId"))
                 and bbox is not None]
    need(len(available) >= 2, "TWO_INDEPENDENT_UNGROUPED_COLUMNS_REQUIRED")
    pairs = []
    for i, (a, x) in enumerate(available):
        for b, y in available[i + 1:]:
            same_height = abs(x["zMin"] - y["zMin"]) < 0.002 and abs(x["zMax"] - y["zMax"]) < 0.002
            distance = abs(x["xMin"] - y["xMin"]) + abs(x["yMin"] - y["yMin"])
            if same_height and 0.2 < distance < 12:
                pairs.append((round(distance, 5), a, b))
    need(pairs, "NO_SAFE_SAME_STORY_COLUMN_PAIR")
    _, left, right = sorted(pairs)[0]
    return [left, right]


def intersects(a, b):
    return all(a[lo] < b[hi] - 0.001 and a[hi] > b[lo] + 0.001
               for lo, hi in (("xMin", "xMax"), ("yMin", "yMax"), ("zMin", "zMax")))


def shift(box, dx=0.0, dy=0.0, dz=0.0):
    return {k: round(box[k] + {"x": dx, "y": dy, "z": dz}[k[0]], 6) for k in COORDS}


def signatures(bbox_list):
    return Counter(tuple(round(b[k], 4) for k in COORDS) for b in bbox_list)



def native_model_bounds_for_unresolved(all_guids, universal_bounds, structural):
    """Reuse the existing GetModelDumpV1 native BREP: no synthetic coordinates.

    Some hierarchical ColumnSegment / BeamSegment elements have unusable generic
    Get3DBoundingBoxes but geometry is owned by their parent. In that case
    require native owner GUID, matching parent type, explicit Tapir hierarchy
    membership AND parent-owned actual BREP vertices; overbound with the parent
    universal bounds rather than treating segments as invisible 2D members.
    """
    native = request("GetModelDumpV1", {}, addon=True, timeout=180)
    slots = native.get("nativeBodySlots")
    bodies = native.get("bodies")
    deleted = native.get("deletedBodySlots")
    need(type(slots) is int and slots > 0
         and native.get("regenerated3D") is True
         and native.get("coordinateSystem") == "ABSOLUTE_PROJECT_XYZ"
         and isinstance(bodies, list) and isinstance(deleted, list),
         "NATIVE_BREP_NOT_ABSOLUTE_OR_COMPLETE")
    indices = [b.get("nativeBodyIndex") for b in bodies]
    need(all(type(i) is int for i in indices + deleted)
         and len(set(indices + deleted)) == len(indices) + len(deleted)
         and set(indices + deleted) == set(range(1, slots + 1)),
         "NATIVE_BREP_SLOTS_NOT_COMPLETE")
    native_rows = native.get("elements")
    need(isinstance(native_rows, list), "NATIVE_BREP_ELEMENTS_MISSING")
    elems = {}
    for e in native_rows:
        k = e.get("guid", "").lower() if isinstance(e, dict) else ""
        need(bool(GUID.fullmatch(k)) and k not in elems,
             "NATIVE_BREP_ELEMENT_IDENTITY_INVALID")
        elems[k] = e
    bodypoints = {}
    for body in bodies:
        owner = body.get("parentGuid", "").lower()
        need(owner in elems, "NATIVE_BREP_UNKNOWN_BODY_OWNER")
        vertices = body.get("vertices", [])
        need(isinstance(vertices, list), "NATIVE_BREP_INVALID_VERTICES")
        for vertex in vertices:
            need(isinstance(vertex, dict)
                 and all(type(vertex.get(k)) in (int, float)
                         and math.isfinite(vertex[k]) for k in ("x", "y", "z")),
                 "NATIVE_BREP_NONFINITE_VERTEX")
            bodypoints.setdefault(owner, []).append(vertex)
    by_guid = {guid.lower(): bbox for guid, bbox in zip(all_guids, universal_bounds)}
    def bounds(points):
        return {axis + bound: fn(p[axis] for p in points)
                for axis in ("x", "y", "z")
                for bound, fn in (("Min", min), ("Max", max))}
    hierarchy = {}
    output = []
    for guid, kind in structural:
        node = elems.get(guid.lower())
        need(isinstance(node, dict) and node.get("type") == kind,
             "NATIVE_BREP_GUID_OR_TYPE_MISMATCH:" + guid)
        points = bodypoints.get(guid.lower(), [])
        if points:
            output.append({"guid": guid, "type": kind, "bounds": bounds(points),
                           "authority": "EXACT_NATIVE_BREP_MEMBER_VERTICES"})
            continue
        parent_type = {"ColumnSegment": "Column", "BeamSegment": "Beam"}.get(kind)
        need(parent_type is not None,
             "MISSING_SPATIAL_BREP_NOT_HIERARCHICAL:" + guid + ":" + kind)
        parent = node.get("relationships", {}).get("hostGuid", "").lower()
        owner = elems.get(parent)
        need(bool(GUID.fullmatch(parent)) and isinstance(owner, dict)
             and owner.get("type") == parent_type,
             "NATIVE_SEGMENT_PARENT_NOT_VERIFIED:" + guid)
        need(parent in by_guid and isinstance(by_guid[parent], dict),
             "NATIVE_SEGMENT_PARENT_UNBOUNDED:" + guid)
        need(bodypoints.get(parent),
             "NATIVE_SEGMENT_PARENT_BREP_MISSING:" + guid)
        if parent not in hierarchy:
            response = request("GetSubelementsOfHierarchicalElements", {
                "elements": [{"elementId": {"guid": parent}}]
            }, addon=True).get("subelements")
            need(isinstance(response, list) and len(response) == 1
                 and isinstance(response[0], dict),
                 "NATIVE_SEGMENT_HIERARCHY_NOT_AVAILABLE:" + parent)
            slot = "columnSegments" if kind == "ColumnSegment" else "beamSegments"
            children = response[0].get(slot)
            need(isinstance(children, list) and children,
                 "NATIVE_SEGMENT_HIERARCHY_EMPTY:" + parent)
            ids = [x.get("elementId", {}).get("guid", "").lower()
                   for x in children if isinstance(x, dict)]
            need(len(ids) == len(children) and all(GUID.fullmatch(x) for x in ids)
                 and len(set(ids)) == len(ids),
                 "NATIVE_SEGMENT_HIERARCHY_BAD_IDS:" + parent)
            hierarchy[parent] = set(ids)
        need(guid.lower() in hierarchy[parent],
             "NATIVE_SEGMENT_NOT_IN_PARENT_HIERARCHY:" + guid)
        parent_box = by_guid[parent]
        source_box = bounds(bodypoints[parent])
        upper = {k: (min(parent_box[k], source_box[k])
                     if k.endswith("Min")
                     else max(parent_box[k], source_box[k])) for k in COORDS}
        output.append({"guid": guid, "type": kind, "bounds": upper,
                       "authority": "PROVEN_HIERARCHICAL_PARENT_BREP_ENVELOPE",
                       "parentGuid": parent})
    return output


def classify_collision_obstacles(guids, values):
    """Use existing native BREP for structural elements with unusable bounds.

    Fail closed for unknown 3D geometry. Only verified bodyless annotations
    may be excluded. Never silently skip column / beam segments.
    """
    need(len(guids) == len(values), "COLLISION_INVENTORY_ALIGNMENT_FAILED")
    unresolved = [(guid, i) for i, (guid, value) in enumerate(zip(guids, values))
                  if value is None]
    verified_2d, structural = [], []
    if unresolved:
        descriptions = batched("GetDetailsOfElements",
                               [guid for guid, _ in unresolved],
                               "detailsOfElements")
        for (guid, _), row in zip(unresolved, descriptions):
            kind = row.get("type") if isinstance(row, dict) else None
            if kind in NONSPATIAL_TYPES:
                verified_2d.append({"guid": guid, "type": kind})
            else:
                need(kind in {"ColumnSegment", "BeamSegment"},
                     "UNBOUNDED_SPATIAL_MEMBER_BLOCKED:guid=" + guid
                     + " type=" + repr(kind))
                structural.append((guid, kind))
    restored = native_model_bounds_for_unresolved(guids, values, structural) if structural else []
    obstacles = [v for v in values if v is not None] + [r["bounds"] for r in restored]
    need(len(obstacles) + len(verified_2d) == len(guids),
         "INCOMPLETE_COLLISION_CLASSIFICATION")
    return obstacles, verified_2d, [{k: v for k, v in r.items() if k != "bounds"}
                                   for r in restored]


def offsets_for_pair(chosen_boxes, existing):
    # Prefer two destinations, each containing the whole verified assembly.
    # Reject any placement intersecting known saved geometry or each other.
    need(all(isinstance(b, dict) for b in existing),
         "COLLISION_OBSTACLES_NOT_CLASSIFIED")
    for delta in (15.0, 25.0, 40.0, 70.0, 110.0, 180.0):
        translations = [{"dx": delta, "dy": 0.0, "dz": 0.0},
                        {"dx": 2 * delta, "dy": 0.0, "dz": 0.0}]
        moved = [shift(b, t["dx"]) for t in translations for b in chosen_boxes]
        if any(intersects(a, b) for a in moved for b in existing):
            continue
        if any(intersects(a, b) for i, a in enumerate(moved) for b in moved[i + 1:]):
            continue
        after_move = [shift(b, delta, delta) for b in chosen_boxes]
        if any(intersects(a, b) for a in after_move for b in existing + moved[2:]):
            continue
        return translations, {"dx": 0.0, "dy": delta, "dz": 0.0}
    raise RuntimeError("NO_COLLISION_FREE_TEST_PLACEMENTS")


def exact_bbox(guids, expected):
    current = boxes(guids)
    need(all(b is not None for b in current)
         and signatures(current) == signatures(expected), "BBOX_READBACK_DIFF")
    return True


def run_acceptance(name, folder):
    need(SOURCE_PATH.is_file() and SOURCE_PATH.suffix.lower() == ".pln",
         "TEST_PLN_NOT_FOUND")
    source_hash = digest(SOURCE_PATH)
    need(request("API.GetProductInfo", {}).get("version") == 29, "NOT_ARCHICAD29")
    guard(SOURCE_PATH, source_hash)
    native_commands = ("GetNativeGroupMembersV1", "CreateNativeGroupV1",
                       "CloneNativeGroupV1", "MoveNativeGroupV1", "UngroupNativeGroupV1")
    for command in native_commands:
        check = request("API.IsAddOnCommandAvailable", {
            "addOnCommandId": {
                "commandNamespace": "TapirCommand", "commandName": command
            }
        })
        need(check.get("available") is True, "NATIVE_GROUP_COMMAND_MISSING:" + command)

    existing = read_elements()
    pair = choose_pair(existing)
    existing_boxes = boxes(existing)
    chosen_boxes = [existing_boxes[existing.index(g)] for g in pair]
    need(all(b is not None for b in chosen_boxes), "SOURCE_COLUMNS_MISSING_GEOMETRY")
    collision_obstacles, excluded_annotations, native_reconstructed = (
        classify_collision_obstacles(existing, existing_boxes))
    translations, move = offsets_for_pair(chosen_boxes, collision_obstacles)
    scratch = Path(r"C:\LocalAI\APA_Group_Acceptance") / (name + ".pln")
    need(not scratch.exists(), "SCRATCH_PLN_ALREADY_EXISTS")
    scratch.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE_PATH, scratch)
    need(digest(scratch) == source_hash, "SCRATCH_COPY_NOT_IDENTICAL")
    mailbox.save(folder / "preflight.json", {
        "sourcePath": str(SOURCE_PATH), "sourceSha256": source_hash,
        "scratchPath": str(scratch), "sourceColumnGuids": pair,
        "translations": translations, "moveTranslation": move,
        "baselineGuids": len(existing),
        "collisionObstacles3D": len(collision_obstacles),
        "excludedTypedNonspatialAnnotations": excluded_annotations,
        "nativeBoundsReconstructed": native_reconstructed,
        "status": "SOURCE_READBACK_AND_SNAPSHOT_PASS"
    })

    # OpenProject may prompt on unsaved local edits. In that case stop: NEVER
    # fall through to native mutations on the original/open wrong project.
    try:
        response = request("OpenProject", {"projectFilePath": str(scratch)},
                           addon=True, timeout=90)
        need(response.get("success") is True, "ARCHICAD_OPEN_SCRATCH_REJECTED")
    except Exception:
        # Transport may close while changing PLN; only exact new path is trusted.
        pass
    deadline = time.monotonic() + 90
    while True:
        try:
            guard(scratch, source_hash)
            break
        except Exception:
            if time.monotonic() > deadline:
                raise RuntimeError("OPEN_SCRATCH_DID_NOT_CONFIRM_EXACT_NEW_PROJECT")
            time.sleep(2)
    need(set(read_elements()) == set(existing), "COPIED_PROJECT_GUID_SET_DRIFT")
    exact_bbox(pair, chosen_boxes)

    source_ref = "APA_GROUP_ACCEPTANCE:" + source_hash[:24]
    def mutating(command, params, stage):
        guard(scratch, source_hash)
        mailbox.save(folder / ("before-" + stage + ".json"), {
            "command": command, "parameters": params,
            "status": "DURABLE_INTENT_NO_RETRY", "at": datetime.now(timezone.utc).isoformat()
        })
        result = request(command, params, addon=True, timeout=90)
        mailbox.save(folder / ("after-" + stage + ".json"), result)
        return result

    created = mutating("CreateNativeGroupV1", {
        "memberIds": [{"guid": g} for g in pair], "sourceRef": source_ref
    }, "create")
    source_group = created.get("groupId", {}).get("guid")
    need(GUID.fullmatch(source_group or "") and created.get("memberCount") == 2,
         "GROUP_CREATE_MALFORMED_RESPONSE")
    need(set(elements_of_group(source_group)) == set(pair), "SOURCE_GROUP_READBACK_FAILED")
    need(set(read_elements()) == set(existing), "GROUP_CREATE_CHANGED_INVENTORY")
    exact_bbox(pair, chosen_boxes)

    cloned = mutating("CloneNativeGroupV1", {
        "groupId": {"guid": source_group}, "sourceRef": source_ref,
        "translations": translations
    }, "clone")
    new_groups = [x.get("guid") for x in cloned.get("newGroupIds", [])]
    new_ids = [v.get("elementId", {}).get("guid") for v in cloned.get("createdElements", [])]
    need(len(new_groups) == 2 and len(set(new_groups)) == 2
         and all(GUID.fullmatch(v or "") for v in new_groups)
         and len(new_ids) == 4 and len(set(new_ids)) == 4
         and not (set(new_ids) & set(existing)), "NATIVE_GROUP_CLONE_GUIDS_INVALID")
    existing_set = {x.lower() for x in existing}
    copied_parents = {x.lower() for x in new_ids}
    cloned_hierarchy, cloned_child_ids = native_owned_children(
        new_ids, existing_set)
    expected_after_clone = existing_set | copied_parents | cloned_child_ids
    need({x.lower() for x in read_elements()} == expected_after_clone,
         "GROUP_CLONE_INVENTORY_DIFF")
    for group_id, translation in zip(new_groups, translations):
        member_ids = elements_of_group(group_id)
        need(len(member_ids) == 2 and set(member_ids) <= set(new_ids),
             "COPIED_GROUP_MEMBERSHIP_MISMATCH")
        exact_bbox(member_ids, [shift(b, translation["dx"],
                                      translation["dy"], translation["dz"]) for b in chosen_boxes])
    exact_bbox(pair, chosen_boxes)

    moved_group = new_groups[0]
    moved_ids = elements_of_group(moved_group)
    moved_boxes = boxes(moved_ids)
    moved = mutating("MoveNativeGroupV1", {
        "groupId": {"guid": moved_group}, "sourceRef": source_ref, "translation": move
    }, "move")
    need(set(x.get("guid") for x in moved.get("movedMembers", [])) == set(moved_ids),
         "MOVE_RESULT_MEMBERS_DIFF")
    need(set(elements_of_group(moved_group)) == set(moved_ids), "MOVE_CHANGED_GROUP_GUIDS")
    exact_bbox(moved_ids, [shift(b, move["dx"], move["dy"], move["dz"]) for b in moved_boxes])
    exact_bbox(pair, chosen_boxes)

    released = mutating("UngroupNativeGroupV1", {
        "groupId": {"guid": moved_group}, "sourceRef": source_ref
    }, "ungroup")
    need(set(x.get("guid") for x in released.get("releasedMembers", [])) == set(moved_ids),
         "UNGROUP_MEMBER_SET_DIFF")
    roots = group_roots(moved_ids)
    need(all(null_group(x.get("groupId")) and null_group(x.get("rootGroupId"))
             for x in roots), "UNGROUP_READBACK_STILL_GROUPED")
    current_hierarchy, current_children = native_owned_children(
        new_ids, existing_set)
    need(current_hierarchy == cloned_hierarchy and
         current_children == cloned_child_ids,
         "NATIVE_CHILD_HIERARCHY_CHANGED_DURING_MOVE_OR_UNGROUP")
    need({x.lower() for x in read_elements()} == expected_after_clone,
         "FINAL_GUID_INVENTORY_CHANGED")
    exact_bbox(moved_ids, [shift(b, move["dx"], move["dy"], move["dz"]) for b in moved_boxes])
    exact_bbox(pair, chosen_boxes)

    # Save only the scratch project. Original test PLN remains byte-identical.
    guard(scratch, source_hash)
    saved = request("SaveProject", {}, addon=True, timeout=90)
    need(saved.get("success") is True, "SCRATCH_SAVE_NOT_CONFIRMED")
    need(digest(SOURCE_PATH) == source_hash, "ORIGINAL_CHANGED_AFTER_TEST")
    return {
        "status": "LIVE_GROUP_FULL_CHAIN_PASS", "port": PORT,
        "scratchPln": str(scratch), "scratchSaved": True,
        "sourcePlnUnchanged": True, "sourceSha256": source_hash,
        "sourceGroupId": source_group, "newGroupIds": new_groups,
        "sourceMembers": pair, "createdElementGuids": new_ids,
        "createdNativeChildGuids": sorted(cloned_child_ids),
        "createdNativeChildrenByParent": cloned_hierarchy,
        "operations": ["CreateNativeGroupV1", "CloneNativeGroupV1",
                       "MoveNativeGroupV1", "UngroupNativeGroupV1"],
        "readback": "EXACT_GUID_AND_3D_BOUNDING_BOX_MATCH",
        "modelWrites": "ONLY_IN_SEPARATE_TEST_PLN", "bddUntouched": True
    }


def validate_job(job, name, approved_sha):
    need(isinstance(job, dict) and set(job) ==
         {"schema", "jobId", "action", "repo", "commit", "port",
          "projectPath", "createdAt", "expiresAt"}, "UNEXPECTED_JOB_FIELDS")
    need(job["schema"] == SCHEMA and job["jobId"] == name
         and JOB_ID.fullmatch(name), "BAD_JOB_SCHEMA")
    need(job["action"] == "RUN_GROUP_ACCEPTANCE_ONLY"
         and job["repo"] == SOURCE_REPO
         and job["port"] == PORT
         and canonical_path(job["projectPath"]) == canonical_path(SOURCE_PATH)
         and job["commit"] == approved_sha and HEX.fullmatch(approved_sha),
         "JOB_NOT_EXACT_LOCALLY_APPROVED_SCOPE")
    created, expires = mailbox.utc(job["createdAt"]), mailbox.utc(job["expiresAt"])
    now = datetime.now(timezone.utc)
    need(created <= now < expires <= created + timedelta(days=2),
         "JOB_TIMESTAMP_OUT_OF_RANGE")


def publish(name, folder):
    marker = folder / "published.json"
    if marker.is_file():
        return
    data = (folder / "result.json").read_bytes()
    remote_path = f"{OUTBOX}/{name}.json"
    # Refuse overwrite; a published result is immutable.
    try:
        old, _ = mailbox.read_file(remote_path)
    except Exception as error:
        if "404" not in str(error) and "Not Found" not in str(error):
            raise
    else:
        need(old == json.loads(data), "REMOTE_RESULT_COLLISION")
        mailbox.save(marker, {"status": "IDENTICAL_REMOTE_RESULT_ALREADY_EXISTS"})
        return
    answer = mailbox.gh(f"repos/{BRIDGE}/contents/{remote_path}", put={
        "message": "APA AC29 live group acceptance receipt " + name,
        "branch": MAILBOX_BRANCH,
        "content": __import__("base64").b64encode(data).decode("ascii")
    })
    need(answer.get("content", {}).get("sha") == mailbox.git_blob(data),
         "RESULT_PUBLICATION_VERIFY_FAILED")
    mailbox.save(marker, {"status": "PUBLISHED"})


def run_job(name, state, approved_sha):
    folder = state / name
    if (folder / "result.json").exists():
        publish(name, folder)
        return "EXISTING_RESULT"
    if folder.exists():
        return "PREVIOUS_ATTEMPT_MANUAL_RECONCILIATION_REQUIRED"
    payload, blob_sha = mailbox.read_file(f"{INBOX}/{name}.json")
    validate_job(payload, name, approved_sha)
    folder.mkdir(parents=True, exist_ok=False)
    mailbox.save(folder / "attempted.json", {
        "jobId": name, "commit": approved_sha, "sourceBlob": blob_sha,
        "automaticRetry": False, "at": datetime.now(timezone.utc).isoformat()
    })
    try:
        result = run_acceptance(name, folder)
    except Exception as error:
        result = {
            "status": "STOPPED_REQUIRES_MANUAL_RECONCILIATION_NO_AUTORETRY",
            "error": type(error).__name__ + ": " + str(error)[-1200:],
            "scratchMayContainUnsavedChanges": (folder / "before-create.json").exists(),
            "originalSourcePlnSaveNotRequested": True,
            "modelWritesToBDD": False
        }
    mailbox.save(folder / "result.json", {
        "schema": "APA_AC29_GROUP_ACCEPTANCE_RESULT_V1",
        "jobId": name, "sourceBlob": blob_sha, "approvedRevision": approved_sha,
        "automaticRetry": False, "result": result
    })
    publish(name, folder)
    return result["status"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-repo", type=Path,
                        default=Path(r"C:\LocalAI\APA_AC29_Build_Source"))
    parser.add_argument("--approved-sha", required=True)
    parser.add_argument("--state", type=Path,
                        default=Path(r"C:\LocalAI\APA_AC29_Group_Acceptance_State"))
    parser.add_argument("--loop", action="store_true")
    parser.add_argument("--interval", type=int, default=30)
    parser.add_argument("--healthcheck", action="store_true")
    args = parser.parse_args()
    need(HEX.fullmatch(args.approved_sha or ""), "APPROVED_SHA_REQUIRED")
    need(10 <= args.interval <= 3600, "BAD_POLL_INTERVAL")
    mailbox.approve_repository(args.source_repo)
    observed = subprocess.run(
        ["git", "-C", str(args.source_repo), "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True
    ).stdout.strip()
    need(observed == args.approved_sha, "LOCAL_EXECUTOR_COMMIT_NOT_PINNED")
    mailbox.call(["gh", "auth", "status"])
    if args.healthcheck:
        need(SOURCE_PATH.is_file(), "LOCAL_TEST_PLN_NOT_FOUND")
        need(request("API.GetProductInfo", {}).get("version") == 29,
             "ARCHICAD29_NOT_AVAILABLE_ON_APPROVED_PORT")
        info = project()
        need(canonical_path(info.get("projectPath", "")) == canonical_path(SOURCE_PATH),
             "WRONG_OPEN_PROJECT_FOR_TEST")
        print("APA_GROUP_MAILBOX_HEALTHCHECK_PASS_NO_NATIVE_MODEL_WRITES", flush=True)
        return
    args.state.mkdir(parents=True, exist_ok=True)
    lock = (args.state / ".single-instance.lock").open("a+b")
    lock.seek(0)
    lock.write(b"\0")
    lock.flush()
    lock.seek(0)
    msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
    try:
        while True:
            items = mailbox.gh(
                f"repos/{BRIDGE}/contents/{INBOX}?ref={MAILBOX_BRANCH}"
            )
            need(isinstance(items, list) and len(items) <= 100,
                 "GROUP_MAILBOX_NOT_BOUNDED")
            ids = sorted(v["name"][:-5] for v in items if v.get("type") == "file"
                         and v["name"].endswith(".json")
                         and JOB_ID.fullmatch(v["name"][:-5]))
            for name in ids:
                try:
                    print(name, run_job(name, args.state, args.approved_sha), flush=True)
                except Exception as error:
                    print(name, "DENIED", type(error).__name__, str(error)[-500:], flush=True)
            if not args.loop:
                break
            time.sleep(args.interval)
    finally:
        lock.close()


if __name__ == "__main__":
    main()
