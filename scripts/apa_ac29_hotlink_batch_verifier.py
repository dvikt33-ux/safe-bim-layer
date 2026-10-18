"""Code-owned proof for one bounded CreateHotlinkInstances native batch.

Reuses original DynamicCommands/SceneWriter scoped verifier protocol.
One existing node, many new instances, exactly ONE native model-write call.
No second router, no native add-on, no per-instance re-dispatch or replay.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import re

import apa_ac29_hotlink_batch_geometry as G
from apa_ac29_dynamic_write_scopes import NativeVerifier
from apa_ac29_hotlink_native_verifiers import (
    need, digest, flatten_hotlinks, canonical_location, verify_instance_root,
)


def batch_parameters(node_guid, origins, native_settings):
    need(isinstance(origins, list) and 1 <= len(origins) <= G.MAX_INSTANCES,
         "HOTLINK_BATCH_BOUNDED_INSTANCE_COUNT_REQUIRED")
    flags = {"skipNested", "suspendFixAngle", "ignoreTopFloorLinks",
             "relinkWallOpenings", "adjustLevelDiffs"}
    need(isinstance(native_settings, dict) and
         set(native_settings) == flags | {"floorDifference"} and
         native_settings["floorDifference"] == 0 and
         all(type(native_settings[k]) is bool for k in flags),
         "HOTLINK_BATCH_EXACT_PROTOTYPE_MODULE_SETTINGS_REQUIRED")
    return {"hotlinkInstances": [{
        "hotlinkNodeId": {"guid": node_guid.lower()},
        "origin": dict(origin),
        "rotationAngle": 0.0,
        "mirrored": False,
        "floorIndex": 0,
        **native_settings,
    } for origin in origins]}


def parse_batch_response(response, count, previous):
    rows = response.get("elements") if isinstance(response, dict) else None
    need(isinstance(rows, list) and len(rows) == count,
         "HOTLINK_BATCH_NATIVE_RESPONSE_CARDINALITY")
    result = []
    for item in rows:
        node = (item.get("elementId") or {}) if isinstance(item, dict) else {}
        guid = node.get("guid")
        need(isinstance(guid, str) and
             re.fullmatch(r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}", guid) and
             guid.lower() not in previous and guid.lower() not in result,
             "HOTLINK_BATCH_NEW_NATIVE_ROOT_IDS_REQUIRED")
        result.append(guid.lower())
    return result


def installed_batch_verifier(module_path, module_sha, node_guid,
                             prototype_guid, prototype_origin,
                             count, gap, approved_plan):
    module = Path(module_path).resolve()
    need(module.is_file() and digest(module) == module_sha,
         "HOTLINK_BATCH_MODULE_IMMUTABLE_SHA_REQUIRED")
    location = canonical_location(str(module))
    node_guid, prototype_guid = node_guid.lower(), prototype_guid.lower()
    origins = approved_plan.get("origins")
    expected_params = batch_parameters(node_guid, origins,
                                       approved_plan["prototypeSettings"])
    need(approved_plan.get("nodeGuid") == node_guid and
         approved_plan.get("prototypeGuid") == prototype_guid and
         approved_plan.get("count") == count and
         approved_plan.get("gapMeters") == gap,
         "HOTLINK_BATCH_APPROVED_PLAN_DRIFT")

    def source_proof(api, native):
        need(digest(module) == module_sha,
             "HOTLINK_BATCH_MODULE_SOURCE_SHA_CHANGED")
        pairs = flatten_hotlinks(api("GetHotlinks", {}))
        need(pairs.count((location, node_guid)) == 1,
             "HOTLINK_BATCH_ONLY_EXISTING_PLACED_NODE_ALLOWED")
        proof = G.placed_prototype(
            api, native, node_guid, prototype_guid, prototype_origin)
        plan = G.planned_batch(proof, count, gap)
        need({key: plan[key] for key in approved_plan} == approved_plan,
             "HOTLINK_BATCH_RECOMPUTED_NATIVE_BREP_PLAN_CHANGED")
        return proof, plan

    def before(*, api, command, parameters, affected, native_before):
        need(command == "CreateHotlinkInstances" and not affected and
             parameters == expected_params,
             "HOTLINK_BATCH_ONE_EXACT_NATIVE_CALL_REQUIRED")
        proof, plan = source_proof(api, native_before)
        return {"status": "HOTLINK_BATCH_NATIVE_SOURCE_AND_BREP_PASS",
                "nodeGuid": node_guid, "prototypeGuid": prototype_guid,
                "moduleSHA256": module_sha, "sourceOwnedCount": proof["ownedCount"],
                "sourceTypeHistogram": proof["typeHistogram"],
                "plan": plan}

    def after(*, api, command, parameters, native_response,
              before_guids, after_guids, affected, native_before,
              native_after, source_proof):
        need(command == "CreateHotlinkInstances" and
             parameters == expected_params and not affected and
             digest(module) == module_sha,
             "HOTLINK_BATCH_NATIVE_SOURCE_CHANGED_AFTER_WRITE")
        roots = parse_batch_response(native_response, count, before_guids)
        added = set(after_guids) - set(before_guids)
        per_instance = source_proof["sourceOwnedCount"]
        need(len(added) == count * (per_instance + 1) and
             set(roots) <= added and not (set(before_guids) - set(after_guids)),
             "HOTLINK_BATCH_UNEXPECTED_GUID_DELTA")
        need((location, node_guid) in
             flatten_hotlinks(api("GetHotlinks", {})),
             "HOTLINK_BATCH_PLACED_NODE_RELATION_MISSING")

        new_children = sorted(added - set(roots))
        rows = api("GetDetailsOfElements", {
            "elements": [{"elementId": {"guid": g}} for g in new_children],
            "fields": ["type", "hotlinkId", "floorIndex", "details"],
        }).get("detailsOfElements")
        need(isinstance(rows, list) and len(rows) == len(new_children),
             "HOTLINK_BATCH_NATIVE_CHILD_DETAILS_MISSING")
        groups = {root: [] for root in roots}
        kinds = {root: Counter() for root in roots}
        for guid, row in zip(new_children, rows):
            owner = (row.get("hotlinkId") or {}).get("guid", "").lower()
            need(owner in groups and row.get("floorIndex") == 0 and
                 isinstance(row.get("type"), str),
                 "HOTLINK_BATCH_ORPHANED_OR_WRONG_FLOOR_CHILD")
            groups[owner].append(guid)
            kinds[owner][row["type"]] += 1

        nodes = {row["guid"].lower(): row for row in native_after["elements"]}
        need(set(nodes) == set(after_guids),
             "HOTLINK_BATCH_COMPLETE_NATIVE_POST_BREP_REQUIRED")
        expected = source_proof["plan"]
        for index, root in enumerate(roots):
            need(len(groups[root]) == per_instance and
                 dict(kinds[root]) == source_proof["sourceTypeHistogram"],
                 "HOTLINK_BATCH_INSTANCE_MEMBER_COUNT_OR_TYPES_DRIFT")
            native_root = verify_instance_root(
                api, node_guid, root, expected["origins"][index])
            root_settings = native_root["details"]
            need(all(root_settings.get(k) == v and
                     type(root_settings.get(k)) is type(v)
                     for k, v in expected["prototypeSettings"].items()),
                 "HOTLINK_BATCH_NATIVE_INSTANCE_PLACEMENT_FLAGS_DRIFT")
            child_boxes = G.world_boxes({"elements":
                                          [nodes[g] for g in groups[root]]})
            actual = G.union(list(child_boxes.values()))
            need(G.box_close(actual, expected["expectedBounds"][index]),
                 "HOTLINK_BATCH_NATIVE_WORLD_BREP_COORDINATES_DRIFT")
        return {"status": "HOTLINK_BATCH_ALL_INSTANCES_NATIVE_BREP_PASS",
                "instanceGuids": roots, "newGuidCount": len(added),
                "childrenPerInstance": per_instance,
                "verifiedOwners": len(new_children),
                "nativeBatchWrites": 1, "expectedOrigins": expected["origins"],
                "moduleSHA256": module_sha}

    return {"VerifiedHotlinkBatchReuseV1": NativeVerifier(
        verifier_id="VerifiedHotlinkBatchReuseV1",
        command="CreateHotlinkInstances", effect="CREATE",
        before=before, after=after)}
