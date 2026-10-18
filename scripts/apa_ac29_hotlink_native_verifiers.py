"""Two CODE-OWNED single-write Hotlink verifiers for existing APA SceneWriter.

One node and one instance; no new router, command, native transport or
model writer. This module performs only validations and native readbacks.
"""
from __future__ import annotations

import hashlib
import math
from pathlib import Path, PureWindowsPath
import re

from apa_ac29_dynamic_write_scopes import NativeVerifier

_GUID = re.compile(r"^[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}$")
NODE = "CreateHotlinkNodes"
INSTANCE = "CreateHotlinkInstances"


def need(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical_location(value):
    need(isinstance(value, str) and bool(value), "HOTLINK_SOURCE_LOCATION_REQUIRED")
    # Windows TemporaryDirectory may expose an 8.3 short path; compare the
    # resolved filesystem identity, not two different spellings of one file.
    try:
        normalized = str(Path(value).resolve(strict=False))
    except (OSError, ValueError):
        normalized = value
    return PureWindowsPath(normalized).as_posix().casefold()


def flatten_hotlinks(response):
    need(isinstance(response, dict) and isinstance(response.get("hotlinks"), list),
         "HOTLINK_READBACK_MISSING")
    nodes = []
    def visit(items, depth=0):
        need(depth <= 24, "HOTLINK_NESTING_TOO_DEEP")
        for item in items:
            need(isinstance(item, dict), "HOTLINK_NODE_INVALID")
            if item.get("hotlinkNodeId"):
                guid = (item["hotlinkNodeId"] or {}).get("guid")
                need(isinstance(guid, str) and _GUID.fullmatch(guid.lower()),
                     "HOTLINK_NODE_INVALID_GUID")
                nodes.append((canonical_location(item["location"]), guid.lower()))
            visit(item.get("children") or [], depth + 1)
    visit(response["hotlinks"])
    need(len(nodes) == len(set(nodes)), "HOTLINK_DUPLICATE_NODE_IN_READBACK")
    return nodes


def node_parameters(module_path):
    module = Path(module_path).resolve()
    need(module.is_file() and module.suffix.lower() in {".pln", ".mod"},
         "HOTLINK_REQUIRE_EXISTING_PLN_OR_MOD_MODULE")
    return {"hotlinkNodes": [{"sourceLocation": str(module),
                                "name": "APA_Hotlink_OneShot",
                                "storyRangeType": "AllStories"}]}


def instance_parameters(node_guid, origin):
    need(isinstance(node_guid, str) and _GUID.fullmatch(node_guid.lower()),
         "HOTLINK_VERIFIED_NODE_GUID_REQUIRED")
    need(isinstance(origin, dict) and set(origin) == {"x", "y", "z"} and
         all(type(v) in (int, float) and math.isfinite(v) and
             abs(v) <= 100000 for v in origin.values()),
         "HOTLINK_EXACT_FINITE_ORIGIN_REQUIRED")
    return {"hotlinkInstances": [{
        "hotlinkNodeId": {"guid": node_guid.lower()},
        "origin": dict(origin),
        "rotationAngle": 0.0,
        "mirrored": False,
        "floorIndex": 0
    }]}


def parse_node_reply(response):
    rows = response.get("hotlinkNodes") if isinstance(response, dict) else None
    need(isinstance(rows, list) and len(rows) == 1, "HOTLINK_NODE_RESPONSE_CARDINALITY")
    row = rows[0]
    need(isinstance(row, dict) and row.get("existing") is False,
         "HOTLINK_NODE_WAS_NOT_NEW")
    node = (row.get("hotlinkNodeId") or {}).get("guid")
    need(isinstance(node, str) and _GUID.fullmatch(node.lower()),
         "HOTLINK_NODE_RESPONSE_GUID_REQUIRED")
    return node.lower()


def parse_instance_reply(response):
    rows = response.get("elements") if isinstance(response, dict) else None
    need(isinstance(rows, list) and len(rows) == 1, "HOTLINK_INSTANCE_RESPONSE_CARDINALITY")
    row = rows[0]
    ident = (row.get("elementId") or {}).get("guid") if isinstance(row, dict) else None
    need(isinstance(ident, str) and _GUID.fullmatch(ident.lower()),
         "HOTLINK_INSTANCE_RESPONSE_GUID_REQUIRED")
    return ident.lower()


def installed_hotlink_verifiers(module_path, expected_sha, exact_origin,
                                verified_node_guid=None):
    """Explicit local closures bound to a SHA-verified source module.

    The registry is passed to the EXISTING build_existing_workflow_scopes().
    It never modifies installed_verifiers(), and grants no blanket native write.
    """
    module = Path(module_path).resolve()
    need(module.is_file() and digest(module) == expected_sha,
         "HOTLINK_MODULE_SHA_DRIFT")
    source_location = canonical_location(str(module))
    node_params = node_parameters(module)
    selected_node = (verified_node_guid or "").lower()

    def read_nodes(api):
        return flatten_hotlinks(api("GetHotlinks", {}))

    def check_source():
        need(digest(module) == expected_sha, "HOTLINK_MODULE_CHANGED")

    def before_node(*, api, command, parameters, affected, native_before):
        check_source()
        need(command == NODE and parameters == node_params and affected == [],
             "HOTLINK_NODE_SINGLE_EXACT_CREATE_REQUIRED")
        nodes = read_nodes(api)
        need(not any(location == source_location for location, _ in nodes),
             "HOTLINK_SOURCE_ALREADY_HAS_NODE")
        need(native_before.get("elements"), "HOTLINK_SCRATCH_NATIVE_BASELINE_REQUIRED")
        return {"status": "HOTLINK_NODE_SOURCE_EXCLUSIVE_PASS", "existing": nodes}

    def after_node(*, api, command, parameters, native_response,
                   before_guids, after_guids, affected, native_before,
                   native_after, source_proof):
        check_source()
        need(command == NODE and before_guids == after_guids,
             "HOTLINK_NODE_CHANGED_MODEL_GUID_SET")
        node = parse_node_reply(native_response)
        before = source_proof["existing"]
        after = read_nodes(api)
        need(sorted(after) == sorted(before + [(source_location, node)]),
             "HOTLINK_NODE_INDEPENDENT_READBACK_DIFFERENT")
        return {"status": "HOTLINK_NODE_NATIVE_READBACK_PASS", "nodeGuid": node,
                "moduleSHA256": expected_sha}

    def before_instance(*, api, command, parameters, affected, native_before):
        check_source()
        need(bool(selected_node) and command == INSTANCE and not affected and
             parameters == instance_parameters(selected_node, exact_origin),
             "HOTLINK_INSTANCE_ONE_EXACT_PLACEMENT_REQUIRED")
        pairs = read_nodes(api)
        need(pairs.count((source_location, selected_node)) == 1,
             "HOTLINK_INSTANCE_VERIFIED_NODE_NOT_FOUND")
        need(native_before.get("elements"), "HOTLINK_INSTANCE_NATIVE_BASELINE_MISSING")
        return {"status": "HOTLINK_INSTANCE_NODE_AND_MODULE_PASS",
                "nodeGuid": selected_node, "moduleSHA256": expected_sha}

    def after_instance(*, api, command, parameters, native_response,
                       before_guids, after_guids, affected, native_before,
                       native_after, source_proof):
        check_source()
        instance = parse_instance_reply(native_response)
        new_guids = sorted(after_guids - before_guids)
        need(command == INSTANCE and source_proof["nodeGuid"] == selected_node and
             instance not in before_guids and new_guids,
             "HOTLINK_INSTANCE_NEW_MODEL_ELEMENTS_NOT_READ_BACK")
        need((source_location, selected_node) in read_nodes(api),
             "HOTLINK_INSTANCE_NODE_RELATION_LOST")
        # Require at least one real element owned by the placed instance.
        # The native instance GUID itself may or may not appear as a model
        # element; require explicit hotlinkId for every imported child.
        rows = api("GetDetailsOfElements", {
            "elements": [{"elementId": {"guid": g}} for g in new_guids if g != instance]
        }).get("detailsOfElements")
        need(isinstance(rows, list) and len(rows) == len([g for g in new_guids if g != instance])
             and rows, "HOTLINK_INSTANCE_IMPORTED_ELEMENT_READBACK_MISSING")
        owners = [(row.get("hotlinkId") or {}).get("guid", "").lower()
                  for row in rows if isinstance(row, dict)]
        need(len(owners) == len(rows) and all(x == instance for x in owners),
             "HOTLINK_INSTANCE_IMPORTED_ELEMENTS_NOT_OWNED")
        return {"status": "HOTLINK_INSTANCE_NATIVE_OWNERSHIP_READBACK_PASS",
                "instanceGuid": instance, "nodeGuid": selected_node,
                "importedElementCount": len(rows),
                "importedGuids": new_guids, "moduleSHA256": expected_sha}

    return {
        "VerifiedHotlinkNodeOneShot": NativeVerifier(
            verifier_id="VerifiedHotlinkNodeOneShot", command=NODE,
            effect="CREATE", before=before_node, after=after_node),
        "VerifiedHotlinkInstanceOneShot": NativeVerifier(
            verifier_id="VerifiedHotlinkInstanceOneShot", command=INSTANCE,
            effect="CREATE", before=before_instance, after=after_instance),
    }
