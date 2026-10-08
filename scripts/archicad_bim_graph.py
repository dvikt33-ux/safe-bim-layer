"""Offline BIM operation dependency planner, built on Tapir JSON contracts.

Turns a declarative list of API operations into a validated dependency graph.
Supports references to GUIDs returned by prior *single-element create* steps.
No project access, no mailbox publishing, no write permission, no live execution.
"""
from __future__ import annotations

import argparse
from collections import deque
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "archicad_batch_contracts", Path(__file__).with_name("archicad_batch_contracts.py"))
CONTRACTS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CONTRACTS)

_REF_KEY = "$createdGuid"
_DUMMY_GUID = "00000000-0000-4000-8000-000000000000"
_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")
# Only commands with a single returned GUID and a known element kind can be
# referenced by another step. Actual cardinality must be verified at runtime.
CREATES = {
    "CreateWalls": "Wall", "CreateColumns": "Column",
    "CreateBeams": "Beam", "CreateSlabs": "Slab",
    "CreateWindows": "Window", "CreateDoors": "Door",
    "CreateRoofs": "Roof", "CreateMorphs": "Morph",
    "CreateStairs": "Stair", "CreateZones": "Zone",
    "CreateOpenings": "Opening",
}
# Schema alone does not establish semantic ownership.
HOST_REFERENCE_KEYS = {"ownerWallId": "Wall"}


def _collect_refs(node, path="$", found=None):
    """Return a copy safe for *offline* schema validation, plus typed references.

    Sentinel substitution is never returned as executable command parameters.
    """
    if found is None:
        found = []
    if isinstance(node, dict):
        if _REF_KEY in node:
            if set(node) != {_REF_KEY} or not isinstance(node[_REF_KEY], str):
                raise ValueError(f"{path}: {_REF_KEY} reference must be a single string field")
            name = node[_REF_KEY]
            if not _ID_RE.fullmatch(name):
                raise ValueError(f"{path}: malformed referenced operation ID")
            found.append((path, name))
            return _DUMMY_GUID
        return {key: _collect_refs(value, path + "." + key, found)
                for key, value in node.items()}
    if isinstance(node, list):
        return [_collect_refs(value, f"{path}[{i}]", found)
                for i, value in enumerate(node)]
    return node


def _topo(node_ids, edges):
    """Stable Kahn sort; IDs are emitted in their input order when unconstrained."""
    indegree = {key: len(edges[key]) for key in node_ids}
    children = {key: [] for key in node_ids}
    for key in node_ids:
        for dependency in edges[key]:
            children[dependency].append(key)
    ready = deque(key for key in node_ids if indegree[key] == 0)
    order = []
    while ready:
        key = ready.popleft()
        order.append(key)
        for child in children[key]:
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.append(child)
    return order if len(order) == len(node_ids) else None


def compile_graph(catalog: dict, value: dict, runtime_version: str | None = None) -> dict:
    if not isinstance(value, dict) or set(value) != {"operations"}:
        raise ValueError("plan must contain only the 'operations' array")
    operations = value["operations"]
    if not isinstance(operations, list) or not (1 <= len(operations) <= CONTRACTS.MAX_REQUESTS):
        raise ValueError(f"operations must contain 1..{CONTRACTS.MAX_REQUESTS} steps")
    by_id = {}
    for index, item in enumerate(operations):
        if not isinstance(item, dict) or not (
            {"id", "command", "params"} <= set(item) <=
            {"id", "command", "params", "after"}
        ):
            raise ValueError(f"operations[{index}]: expected id, command, params, optional after")
        name = item["id"]
        if not isinstance(name, str) or not _ID_RE.fullmatch(name) or name in by_id:
            raise ValueError(f"operations[{index}]: invalid or duplicate operation ID")
        by_id[name] = item

    reports, dependencies = [], {}
    for index, item in enumerate(operations):
        name = item["id"]
        command = item["command"]
        errors = []
        refs = []
        normalized = None
        if not isinstance(command, str) or command not in catalog["commands"]:
            errors.append("command not found in pinned schema")
        if not isinstance(item["params"], dict):
            errors.append("params must be an object")
        else:
            try:
                normalized = _collect_refs(item["params"], found=refs)
            except ValueError as exc:
                errors.append(str(exc))
        after = item.get("after", [])
        if (not isinstance(after, list) or
                any(not isinstance(dep, str) or not _ID_RE.fullmatch(dep) for dep in after)):
            errors.append("after must be an array of operation IDs")
            after = []
        elif len(after) != len(set(after)):
            errors.append("duplicate after dependency")
        explicit = list(after)
        all_deps = list(dict.fromkeys([*explicit, *(dep for _, dep in refs)]))
        for dep in all_deps:
            if dep == name:
                errors.append("operation cannot depend on itself")
            elif dep not in by_id:
                errors.append(f"unknown dependency: {dep}")
        for path, dep in refs:
            producer = by_id.get(dep)
            if not path.endswith(".guid"):
                errors.append(f"{path}: generated GUID references are allowed only in .guid fields")
            if producer:
                producer_command = producer.get("command")
                if producer_command not in CREATES:
                    errors.append(f"{path}: {dep} is not a known single-element create recipe")
                else:
                    # The batch may contain many create steps, but a referenced
                    # producer must return exactly one GUID, not a GUID array.
                    payload_key = producer_command[len("Create"):].lower() + "Data"
                    rows = producer.get("params", {}).get(payload_key)
                    if not isinstance(rows, list) or len(rows) != 1:
                        errors.append(f"{path}: {dep} must create exactly one element")
            expected = next((kind for field, kind in HOST_REFERENCE_KEYS.items()
                             if path.endswith("." + field + ".guid")), None)
            if expected and producer and CREATES.get(producer.get("command")) != expected:
                errors.append(f"{path}: host must be {expected} (not {producer.get('command')})")
        if command in catalog["commands"] and isinstance(normalized, dict):
            try:
                validator = CONTRACTS._validator(catalog, command)
                for error in sorted(validator.iter_errors(normalized), key=lambda e: str(e.path)):
                    at = ".".join(map(str, error.absolute_path)) or "$"
                    errors.append(f"{at}: {error.message}")
                    if len(errors) >= 20:
                        break
            except Exception as exc:
                errors.append("schema validation unavailable: " + str(exc))
        dependencies[name] = [dep for dep in all_deps if dep in by_id and dep != name]
        reports.append({
            "id": name, "index": index, "command": command,
            "status": "SCHEMA_VALID" if not errors else "INVALID",
            "dependsOn": all_deps,
            "references": [{"parameterPath": path, "producerId": dep} for path, dep in refs],
            "disposition": CONTRACTS.disposition(command) if isinstance(command, str) else None,
            "errors": errors[:20],
        })

    order = _topo(list(by_id), dependencies)
    if order is None:
        for report in reports:
            report["errors"].append("dependency cycle detected")
            report["status"] = "INVALID"
    mismatch = runtime_version is not None and runtime_version != CONTRACTS.source_version(catalog)
    invalid = any(x["status"] != "SCHEMA_VALID" for x in reports)
    # Hash the untouched intent, not the schema-only placeholders.
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                           allow_nan=False).encode("utf-8")
    return {
        "status": "INVALID" if invalid else (
            "REQUIRES_UPDATED_SCHEMA" if mismatch else "PLAN_VALIDATED_OFFLINE"),
        "schemaVersion": CONTRACTS.source_version(catalog),
        "runtimeVersion": runtime_version,
        "runtimeSchemaMatch": (not mismatch) if runtime_version else None,
        "operationCount": len(operations),
        "sourcePlanHash": hashlib.sha256(canonical).hexdigest(),
        "executionOrder": order if not invalid else None,
        "operations": reports,
        "liveCommandsVerified": 0, "executionSupported": False,
        "jobPublished": False, "plnChanged": False,
        "note": "No host binding, collision, geometry or actual runtime GUID verified.",
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("plan", type=Path, help="declarative BIM operations JSON file")
    p.add_argument("--schema", type=Path, default=CONTRACTS.DEFAULT_SCHEMA)
    p.add_argument("--runtime-version", default=None)
    p.add_argument("--output", type=Path)
    args = p.parse_args(argv)
    try:
        catalog = CONTRACTS.load_catalog(args.schema)
        value = json.loads(args.plan.read_text(encoding="utf-8-sig"))
        result = compile_graph(catalog, value, args.runtime_version)
        rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
        print(rendered, end="")
        return 0 if result["status"] == "PLAN_VALIDATED_OFFLINE" else 2
    except Exception as exc:
        print(json.dumps({"status": "ERROR", "error": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    sys.exit(main())
