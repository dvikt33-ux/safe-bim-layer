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
import math
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


def _hosted_fit_errors(step, steps):
    """Offline-only linear fit. Does not check libraries, materials or openings.

    The Tapir centerOffset is treated as a location along the parent wall
    reference segment. For a curved wall, static host fit is not inferred.
    A live parent GUID also needs a fresh native read before actual creation.
    """
    command = step.get("command")
    if command not in ("CreateWindows", "CreateDoors"):
        return []
    params = step.get("params")
    field = "windowsData" if command == "CreateWindows" else "doorsData"
    entries = params.get(field) if isinstance(params, dict) else None
    if not isinstance(entries, list):
        return []
    errors = []
    for i, entry in enumerate(entries):
        if not isinstance(entry, dict):
            continue
        owner = entry.get("ownerWallId")
        guid = owner.get("guid") if isinstance(owner, dict) else None
        if (not isinstance(guid, dict) or set(guid) != {_REF_KEY}
                or not isinstance(guid[_REF_KEY], str)):
            continue  # Malformed refs are diagnosed by the reference validator.
        source = steps.get(guid[_REF_KEY])
        if not isinstance(source, dict) or source.get("command") != "CreateWalls":
            continue  # The typed-reference validator reports the error.
        source_params = source.get("params")
        walls = source_params.get("wallsData") if isinstance(source_params, dict) else None
        if not isinstance(walls, list) or len(walls) != 1 or not isinstance(walls[0], dict):
            continue
        wall = walls[0]
        if wall.get("arcAngle", 0) != 0:
            continue  # Curved geometry requires native host interpretation.
        a, b = wall.get("begCoordinate"), wall.get("endCoordinate")
        if not isinstance(a, dict) or not isinstance(b, dict):
            continue
        try:
            xy = (a["x"], a["y"], b["x"], b["y"])
            if any(type(v) not in (int, float) or not math.isfinite(v) for v in xy):
                continue
            length = math.hypot(b["x"]-a["x"], b["y"]-a["y"])
            offset, width = entry.get("centerOffset"), entry.get("width")
            if type(offset) not in (int, float) or not math.isfinite(offset):
                continue  # JSON Schema validator separately checks numeric type.
            if offset > length + 1e-9:
                errors.append(f"{field}[{i}]: centerOffset exceeds straight host wall length")
            if type(width) in (int, float) and math.isfinite(width):
                if offset - width / 2 < -1e-9 or offset + width / 2 > length + 1e-9:
                    errors.append(f"{field}[{i}]: opening width exceeds straight host wall segment")
            # Never assume defaults inherited from Archicad Favorites.
            sill, opening_height, wall_height = (entry.get("sillHeight"),
                                                  entry.get("height"), wall.get("height"))
            if all(type(v) in (int, float) and math.isfinite(v)
                   for v in (sill, opening_height, wall_height)):
                if sill < -1e-9 or sill + opening_height > wall_height + 1e-9:
                    errors.append(f"{field}[{i}]: opening height exceeds straight host wall vertical extent")
        except (KeyError, TypeError):
            continue
    return errors


def _hosted_overlap_errors(operations):
    """Reject overlapping openings on the SAME planned, generated straight Wall.

    Uses only explicit widths and offsets. Never guesses Favorite dimensions.
    Existing host GUIDs and curved walls need native readback before clearance.
    """
    walls = {step["id"]: step for step in operations
             if step.get("command") == "CreateWalls"}
    spans, errors = {}, {}
    for step in operations:
        field = {"CreateWindows": "windowsData",
                 "CreateDoors": "doorsData"}.get(step.get("command"))
        if not field or not isinstance(step.get("params"), dict):
            continue
        rows = step["params"].get(field)
        if not isinstance(rows, list):
            continue
        for i, row in enumerate(rows):
            if not isinstance(row, dict):
                continue
            owner = row.get("ownerWallId")
            guid = owner.get("guid") if isinstance(owner, dict) else None
            if not isinstance(guid, dict) or set(guid) != {_REF_KEY}:
                continue
            parent = guid[_REF_KEY]
            if not isinstance(parent, str) or parent not in walls:
                continue
            parent_data = walls[parent].get("params")
            wall_rows = parent_data.get("wallsData") if isinstance(parent_data, dict) else None
            if (not isinstance(wall_rows, list) or len(wall_rows) != 1
                    or not isinstance(wall_rows[0], dict)
                    or wall_rows[0].get("arcAngle", 0) != 0):
                continue
            center, width = row.get("centerOffset"), row.get("width")
            if (not all(type(v) in (float, int) and math.isfinite(v)
                        for v in (center, width)) or width <= 0):
                continue
            start, end = center - width / 2, center + width / 2
            for prior_start, prior_end, prev_id, prev_row in spans.get(parent, []):
                if min(end, prior_end) - max(start, prior_start) > 1e-9:
                    errors.setdefault(step["id"], []).append(
                        f"{field}[{i}]: opening overlaps with "
                        f"{prev_id}[{prev_row}] on generated Wall {parent}")
            spans.setdefault(parent, []).append((start, end, step["id"], i))
    return errors


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
                if not isinstance(producer_command, str) or producer_command not in CREATES:
                    errors.append(f"{path}: {dep} is not a known single-element create recipe")
                else:
                    # The batch may contain many create steps, but a referenced
                    # producer must return exactly one GUID, not a GUID array.
                    payload_key = producer_command[len("Create"):].lower() + "Data"
                    producer_params = producer.get("params")
                    rows = producer_params.get(payload_key) if isinstance(producer_params, dict) else None
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
        errors.extend(_hosted_fit_errors(item, by_id))
        dependencies[name] = [dep for dep in all_deps if dep in by_id and dep != name]
        reports.append({
            "id": name, "index": index, "command": command,
            "status": "SCHEMA_VALID" if not errors else "INVALID",
            "dependsOn": all_deps,
            "references": [{"parameterPath": path, "producerId": dep} for path, dep in refs],
            "disposition": CONTRACTS.disposition(command) if isinstance(command, str) else None,
            "errors": errors[:20],
        })

    # Cross-step overlaps can involve references to later-listed openings.
    overlaps = _hosted_overlap_errors(operations)
    for report in reports:
        if report["id"] in overlaps:
            report["errors"].extend(overlaps[report["id"]])
            report["status"] = "INVALID"

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
        "note": "Only offline straight-wall opening fit/overlap was checked; no native collision, host binding, favorites, clearance or actual GUID verified.",
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
