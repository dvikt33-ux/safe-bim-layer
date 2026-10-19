"""Code-owned AC29 native group clone verifier for the original SceneWriter.

A single source-qualified native group of two complete columns (each one
ColumnSegment) can be cloned at 1..32 distinct, BREP-cleared horizontal
offsets in ONE existing native group operation (max 64 new Column roots).
The 2-placement live acceptance remains a strict subset of this extension. This module does not execute any commands;
it supplies independent native pre- and post-readback callbacks to the
EXISTING APA Dynamic Mutation Scopes and SQLite SceneWriter.
"""
from __future__ import annotations

import math
import re
import json

import apa_ac29_multi_prototype_native_copy as M
from apa_ac29_dynamic_write_scopes import NativeVerifier

CMD = "AddOn.TapirCommand.CloneNativeGroupV1"
GROUP_GUID = re.compile(r"^[a-fA-F0-9]{8}(?:-[a-fA-F0-9]{4}){3}-[a-fA-F0-9]{12}$")


def require(ok, msg):
    if not ok:
        raise ValueError(msg)


def same_native_fact(current, pinned):
    """Exact JSON-contract comparison, including persisted tuple geometry."""
    def canonical(value):
        return json.dumps(value, sort_keys=True, ensure_ascii=False,
                          separators=(",", ":"), allow_nan=False)
    return canonical(current) == canonical(pinned)


def group_member_ids(api, group_id):
    reply = api("GetNativeGroupMembersV1", {"groupId": {"guid": group_id}})
    require(isinstance(reply, dict) and reply.get("nativeModelWrites") == 0,
            "GROUP_WRITER_NATIVE_GROUP_READ_ONLY_RESPONSE_REQUIRED")
    values = reply.get("memberIds")
    require(isinstance(values, list) and len(values) == 2,
            "GROUP_WRITER_EXACT_TWO_NATIVE_MEMBERS_REQUIRED")
    ids = [item.get("guid", "").lower() for item in values
           if isinstance(item, dict)]
    require(len(ids) == 2 and len(set(ids)) == 2
            and all(GROUP_GUID.fullmatch(v) for v in ids),
            "GROUP_WRITER_NATIVE_GROUP_MEMBER_IDS_INVALID")
    return set(ids)


def column_facts(api, nodes, members):
    """Existing native BREP and native typed details prove each whole column."""
    require(all(nodes.get(g, {}).get("type") == "Column" for g in members),
            "GROUP_WRITER_SOURCE_NOT_TWO_COLUMNS")
    details = M.SINGLE.column_details(api, sorted(members))
    sources = {}
    for guid in sorted(members):
        row = details[guid]
        value = row["details"]
        origin = value["origin"]
        point = {
            "x": origin["x"], "y": origin["y"],
            "z": value["zCoordinate"]
        }
        M.vector(point)
        require(row.get("floorIndex") == 0
                and nodes[guid].get("homeStory") == 0,
                "GROUP_WRITER_COLUMN_NATIVE_STORY_DRIFT")
        children = M.owned_children(nodes, guid, "Column")
        require(len(children) == 1, "GROUP_WRITER_ONE_COLUMN_SEGMENT_REQUIRED")
        typed = M.source_detail_fingerprint(row, "Column", point)
        solid = M.solid_fingerprint(
            nodes[guid], children, point, parent_guid=guid
        )
        sources[guid] = {
            "anchor": point, "typed": typed, "solid": solid,
            "source": (nodes[guid], children)
        }
    return sources


def verify_before(*, api, command, parameters, affected, native_before):
    require(command == CMD and not affected,
            "GROUP_WRITER_ONLY_CREATE_EXACT_NATIVE_GROUP_CLONE")
    require(isinstance(parameters, dict)
            and set(parameters) == {"groupId", "sourceRef", "translations"}
            and isinstance(parameters["sourceRef"], str)
            and len(parameters["sourceRef"]) >= 8,
            "GROUP_WRITER_SOURCE_PROVENANCE_REQUIRED")
    group = parameters["groupId"].get("guid")
    require(isinstance(group, str) and GROUP_GUID.fullmatch(group),
            "GROUP_WRITER_GROUP_GUID_REQUIRED")
    shifts = parameters["translations"]
    require(isinstance(shifts, list) and 1 <= len(shifts) <= 32,
            "GROUP_WRITER_NATIVE_ONE_TO_32_GROUP_COPIES")
    seen = set()
    for offset in shifts:
        require(isinstance(offset, dict)
                and set(offset) == {"dx", "dy", "dz"}
                and all(type(n) in (int, float) and math.isfinite(n)
                        and abs(n) <= 10000 for n in offset.values())
                and offset["dz"] == 0
                and (offset["dx"] != 0 or offset["dy"] != 0),
                "GROUP_WRITER_HORIZONTAL_NONZERO_EXACT_SHIFT_REQUIRED")
        point = tuple(round(offset[k], 6) for k in ("dx", "dy", "dz"))
        require(point not in seen, "GROUP_WRITER_DUPLICATE_GROUP_SHIFT")
        seen.add(point)
    rows = native_before.get("elements") if isinstance(native_before, dict) else None
    require(isinstance(rows, list) and len(rows) >= 6,
            "GROUP_WRITER_NATIVE_BASELINE_MISSING")
    nodes = {r["guid"].lower(): r for r in rows}
    require(len(nodes) == len(rows), "GROUP_WRITER_BASELINE_GUID_COLLISION")
    members = group_member_ids(api, group)
    require(members <= set(nodes), "GROUP_WRITER_SOURCE_NOT_IN_SAVED_MODEL")
    sources = column_facts(api, nodes, members)
    # The existing native all-solids layout verifier checks complete actual
    # source BREP against ALL existing geometry and both incoming placements.
    layouts = []
    source_elements = {}
    targets = {}
    for guid in sorted(members):
        src = sources[guid]
        layouts.append({"prototypeGuid": guid,
                        "prototypeType": "Column",
                        "sourceAnchor": src["anchor"]})
        source_elements[guid] = src["source"]
        targets[guid] = [
            {axis: src["anchor"][axis] + shift["d" + axis]
             for axis in ("x", "y", "z")}
            for shift in shifts
        ]
    clearance = M.verify_batch_layout(layouts, source_elements, nodes, targets)
    require(clearance.get("status") ==
            "MULTI_COPY_ALL_NATIVE_BREP_AABB_CLEAR_PASS",
            "GROUP_WRITER_NATIVE_LAYOUT_COLLISION_NOT_CLEARED")
    return {
        "status": "GROUP_CLONE_SOURCE_OWNED_NATIVE_BREP_AND_LAYOUT_PASS",
        "group": group.lower(),
        "members": sorted(members),
        "offsets": shifts,
        "sourceFacts": {
            k: {"anchor": v["anchor"], "typed": v["typed"],
                "solid": v["solid"]} for k, v in sources.items()
        },
        "sourceNativeGuidCount": len(nodes),
        "collisionProof": clearance
    }


def verify_after(*, api, command, parameters, native_response, before_guids,
                 after_guids, affected, native_before, native_after, source_proof):
    require(command == CMD and not affected
            and source_proof.get("group") ==
            parameters["groupId"]["guid"].lower()
            and source_proof.get("offsets") == parameters.get("translations")
            and source_proof.get("status") ==
            "GROUP_CLONE_SOURCE_OWNED_NATIVE_BREP_AND_LAYOUT_PASS"
            and source_proof.get("sourceNativeGuidCount") == len(before_guids),
            "GROUP_WRITER_POST_READBACK_SOURCE_DRIFT")
    number_of_groups = len(source_proof["offsets"])
    require(1 <= number_of_groups <= 32
            and len(source_proof.get("members", [])) == 2,
            "GROUP_WRITER_POST_READBACK_COUNT_OUTSIDE_SDK_CAPACITY")
    expected_roots = 2 * number_of_groups
    expected_new_guids = 2 * expected_roots
    require(isinstance(native_response, dict)
            and isinstance(native_after, dict)
            and isinstance(native_after.get("elements"), list),
            "GROUP_WRITER_NATIVE_RESPONSE_OR_MODEL_DUMP_MISSING")
    newgroups = native_response.get("newGroupIds")
    outputs = native_response.get("createdElements")
    require(isinstance(newgroups, list) and
            len(newgroups) == number_of_groups
            and isinstance(outputs, list) and len(outputs) == expected_roots
            and native_response.get("nativeModelWrites") == expected_roots
            and native_response.get("sourceGroupId", {}).get("guid", "").lower()
            == source_proof["group"],
            "GROUP_WRITER_NATIVE_RESPONSE_GROUP_ROOT_COUNT_MISMATCH")
    source_groups = [
        row.get("guid", "").lower() for row in newgroups if isinstance(row, dict)
    ]
    roots = [
        row.get("elementId", {}).get("guid", "").lower()
        for row in outputs if isinstance(row, dict)
    ]
    require(len(source_groups) == number_of_groups
            and len(set(source_groups)) == number_of_groups
            and all(GROUP_GUID.fullmatch(g) for g in source_groups)
            and len(roots) == expected_roots
            and len(set(roots)) == expected_roots
            and all(GROUP_GUID.fullmatch(g) for g in roots),
            "GROUP_WRITER_GROUP_OR_PARENT_IDS_INVALID")
    nodes = {r["guid"].lower(): r for r in native_after["elements"]}
    require(len(nodes) == len(native_after["elements"])
            and set(nodes) == after_guids
            and before_guids <= after_guids
            and len(after_guids - before_guids) == expected_new_guids,
            "GROUP_WRITER_COMPLETE_NATIVE_ROOT_AND_SEGMENT_GUIDS_REQUIRED")
    new = after_guids - before_guids
    require(set(roots) <= new and set(roots).isdisjoint(before_guids),
            "GROUP_WRITER_COPIED_ROOT_NOT_NEW")
    require(group_member_ids(api, source_proof["group"]) ==
            set(source_proof["members"]),
            "GROUP_WRITER_ORIGINAL_GROUP_CHANGED")
    seen_roots, seen_children = set(), set()
    for copy_group, shift in zip(source_groups, source_proof["offsets"]):
        members = group_member_ids(api, copy_group)
        require(members <= set(roots)
                and members.isdisjoint(seen_roots),
                "GROUP_WRITER_CLONE_GROUP_MEMBERS_INVALID")
        seen_roots.update(members)
        current = column_facts(api, nodes, members)
        matched = set()
        for original in source_proof["members"]:
            source = source_proof["sourceFacts"][original]
            point = {
                axis: source["anchor"][axis] + shift["d" + axis]
                for axis in ("x", "y", "z")
            }
            candidates = [
                guid for guid in members
                if all(M.SINGLE.almost(current[guid]["anchor"][k], point[k])
                       for k in ("x", "y", "z"))
                and same_native_fact(current[guid]["typed"], source["typed"])
                and same_native_fact(current[guid]["solid"], source["solid"])
            ]
            require(len(candidates) == 1 and candidates[0] not in matched,
                    "GROUP_WRITER_TRANSLATED_BREP_OR_ATTRIBUTES_MISMATCH")
            matched.add(candidates[0])
            children = current[candidates[0]]["source"][1]
            require(len(children) == 1 and children[0][0] in new
                    and children[0][0] not in seen_children,
                    "GROUP_WRITER_NATIVE_SEGMENT_MISSING_OR_DUPLICATED")
            seen_children.add(children[0][0])
        require(matched == members,
                "GROUP_WRITER_NATIVE_MEMBER_GEOMETRY_SET_MISMATCH")
    require(seen_roots == set(roots) and
            seen_roots | seen_children == new
            and len(seen_children) == expected_roots,
            "GROUP_WRITER_ALL_NATIVE_GROUP_GUIDS_NOT_EXACTLY_ACCOUNTED")
    return {
        "status": "GROUP_CLONE_SCENEWRITER_NATIVE_BREP_GUID_READBACK_PASS",
        "originalNativeGuidCount": len(before_guids),
        "finalNativeGuidCount": len(after_guids),
        "newRootGuids": sorted(seen_roots),
        "newSegmentGuids": sorted(seen_children),
        "newGroupGuids": source_groups,
        "groupCopyCount": number_of_groups,
        "originalGroupUnchanged": True,
        "allNativeRootsAndChildrenVerified": True
    }


def installed_group_clone_verifiers():
    return {
        "VerifiedNativeGroupClone": NativeVerifier(
            verifier_id="VerifiedNativeGroupClone",
            command=CMD, effect="CREATE",
            before=verify_before, after=verify_after
        )
    }
