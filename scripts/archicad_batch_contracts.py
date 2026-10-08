"""Offline, schema-driven preparation for batches of Archicad/Tapir commands.

No network, Archicad access, Mailbox publishing, or project writes occur here.
Schema-valid does NOT imply a command is supported by the running add-on,
geometrically valid, authorized, or safe to execute.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys

DEFAULT_SCHEMA = Path(__file__).resolve().parents[1] / "tapir-1.5.8.json"
MAX_REQUESTS = 100
_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")
# Explicitly denied even for offline dispatch planning: these may close,
# save, or alter external state and must never be treated as normal BIM writes.
SPECIAL_REVIEW = frozenset({
    "QuitArchicad", "SaveProject", "OpenProject", "PublishPublisherSet",
    "SendTeamworkChanges", "ReceiveTeamworkChanges", "ReserveElements",
    "ReleaseElements", "DeleteElements", "DeleteNavigatorItems",
})
# Schema coverage is NOT executable permissions.
BIM_RECIPE_CANDIDATES = frozenset({
    "CreateWalls", "CreateColumns", "CreateBeams", "CreateSlabs",
    "CreateWindows", "CreateDoors", "CreateRoofs", "CreateMorphs",
    "CreateZones", "CreateOpenings", "CreateStairs", "CreateMEPElements",
    "CreateMEPRoutingElements", "ModifyWalls", "ModifySlabs",
    "ModifyColumns", "ModifyBeams", "ModifyRoofs", "ModifyMorphs",
    "ModifyWindows", "ModifyDoors",
})


def load_catalog(path: Path) -> dict:
    doc = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(doc, dict) or not isinstance(doc.get("commands"), dict):
        raise ValueError("not a Tapir command snapshot (missing commands object)")
    if not isinstance(doc.get("common_schemas"), dict):
        raise ValueError("Tapir snapshot has no common_schemas")
    return doc


def source_version(catalog: dict) -> str:
    return str(catalog.get("_metadata", {}).get("provider_version", "unknown"))


def disposition(command: str) -> str:
    """Planning labels only, NEVER authorization to invoke a command."""
    if command in SPECIAL_REVIEW:
        return "SPECIAL_REVIEW"
    if command.startswith(("Get", "Is")):
        return "READ_CANDIDATE"
    if command in BIM_RECIPE_CANDIDATES:
        return "TYPED_RECIPE_REQUIRED"
    return "UNREVIEWED_COMMAND"


def _refs(obj):
    if isinstance(obj, dict):
        if "$ref" in obj:
            yield obj["$ref"]
        for item in obj.values():
            yield from _refs(item)
    elif isinstance(obj, list):
        for item in obj:
            yield from _refs(item)


def audit(catalog: dict, runtime_version: str | None = None) -> dict:
    common = catalog["common_schemas"]
    commands = catalog["commands"]
    missing = []
    for name, definition in sorted(commands.items()):
        for ref in _refs(definition):
            if not isinstance(ref, str) or not ref.startswith("#/") or (
                len(ref.split("/")) != 2
            ) or (ref.split("/", 1)[1] not in common):
                missing.append({"command": name, "ref": ref})
    counts = Counter(disposition(name) for name in commands)
    categories = Counter(str(x.get("category", "Uncategorized")) for x in commands.values())
    version = source_version(catalog)
    return {
        "status": "SCHEMA_AUDIT",
        "schemaVersion": version,
        "runtimeVersion": runtime_version,
        "runtimeSchemaMatch": (version == runtime_version) if runtime_version else None,
        "documentedCommandCount": len(commands),
        "categories": dict(sorted(categories.items())),
        "dispositions": dict(sorted(counts.items())),
        "unresolvedCommandRefs": missing[:30],
        "unresolvedCommandRefCount": len(missing),
        "liveCommandsVerified": 0,
        "executionSupported": False,
    }


def _validator(catalog: dict, command: str):
    try:
        from jsonschema import Draft7Validator
    except ImportError as exc:
        raise RuntimeError(
            "Install JSON Schema validation first: python -m pip install jsonschema>=4,<5"
        ) from exc
    definition = catalog["commands"][command]
    params = definition.get("parameters")
    if params is None:
        params = {"type": "object", "maxProperties": 0}
    if not isinstance(params, dict):
        raise ValueError(f"{command}: malformed parameter contract")
    # Tapir uses refs like '#/Coordinate2D'. Place its shared schemas at
    # the same document root so standard jsonschema resolves them verbatim.
    document = {**catalog["common_schemas"], "__input__": params,
                "$ref": "#/__input__"}
    Draft7Validator.check_schema(document)
    return Draft7Validator(document)


def compile_batch(catalog: dict, batch: dict, runtime_version: str | None = None) -> dict:
    if not isinstance(batch, dict) or set(batch) != {"requests"}:
        raise ValueError("batch must be an object containing only 'requests'")
    requests = batch["requests"]
    if not isinstance(requests, list) or not 1 <= len(requests) <= MAX_REQUESTS:
        raise ValueError(f"requests must contain 1..{MAX_REQUESTS} items")
    results, ids = [], set()
    for index, request in enumerate(requests):
        errors = []
        request_id = request.get("id") if isinstance(request, dict) else None
        command = request.get("command") if isinstance(request, dict) else None
        params = request.get("params") if isinstance(request, dict) else None
        if not isinstance(request, dict) or set(request) != {"id", "command", "params"}:
            errors.append("request must contain exactly id, command, params")
        if not isinstance(request_id, str) or not _ID.fullmatch(request_id):
            errors.append("invalid request id (1..64 ASCII-safe characters)")
        elif request_id in ids:
            errors.append("duplicate request id")
        else:
            ids.add(request_id)
        if not isinstance(command, str) or command not in catalog["commands"]:
            errors.append("command absent from pinned schema")
        if not isinstance(params, dict):
            errors.append("params must be a JSON object")
        if not errors:
            try:
                validator = _validator(catalog, command)
                for error in sorted(validator.iter_errors(params), key=lambda e: str(e.path)):
                    path = ".".join(map(str, error.absolute_path)) or "$"
                    errors.append(f"{path}: {error.message}")
                    if len(errors) >= 20:
                        break
            except Exception as exc:
                errors.append("schema validation unavailable: " + str(exc))
        results.append({
            "index": index,
            "id": request_id,
            "command": command,
            "disposition": disposition(command) if isinstance(command, str) else None,
            "status": "SCHEMA_VALID" if not errors else "INVALID",
            "errors": errors,
        })
    version = source_version(catalog)
    mismatch = runtime_version is not None and version != runtime_version
    return {
        "status": "INVALID" if any(r["errors"] for r in results) else (
            "REQUIRES_UPDATED_SCHEMA" if mismatch else "SCHEMA_VALID"
        ),
        "schemaVersion": version,
        "runtimeVersion": runtime_version,
        "runtimeSchemaMatch": (not mismatch) if runtime_version else None,
        "batchSize": len(requests),
        "validCount": sum(r["status"] == "SCHEMA_VALID" for r in results),
        "invalidCount": sum(r["status"] != "SCHEMA_VALID" for r in results),
        "results": results,
        "executionSupported": False,
        "jobPublished": False,
        "modelChanged": False,
        "note": "Offline contract check only. Runtime, identity, geometric and write-policy gates are separate.",
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    p.add_argument("--batch", type=Path, help="optional JSON batch (never executed)")
    p.add_argument("--runtime-version", help="e.g. 1.5.10, to flag outdated snapshots")
    p.add_argument("--output", type=Path, help="optional output JSON file")
    args = p.parse_args(argv)
    try:
        catalog = load_catalog(args.schema)
        result = compile_batch(
            catalog, json.loads(args.batch.read_text(encoding="utf-8-sig")),
            args.runtime_version,
        ) if args.batch else audit(catalog, args.runtime_version)
        rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
        print(rendered, end="")
        return 0 if result["status"] in ("SCHEMA_AUDIT", "SCHEMA_VALID") else 2
    except Exception as exc:
        print(json.dumps({"status": "ERROR", "error": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    sys.exit(main())
