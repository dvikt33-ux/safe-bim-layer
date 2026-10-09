"""Project intent -> existing BIM graph -> guarded native writer -> evidence.

Only pavilion-frame-v1 is executable. Floor and MEP adapters are deliberately
UNSUPPORTED. Default mode is offline. No daemon, save, deletion, or retry.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
import time
import urllib.request

import archicad_scene_run as RUN
import archicad_scene_v1 as SCENE

READS = frozenset({"GetProjectInfo", "GetStories", "GetAddOnVersion",
                  "GetAllElements", "Get3DBoundingBoxes", "GetDetailsOfElements", "API.GetProductInfo"})
PRIMITIVES = {
    "pavilion-frame-v1": {"status": "EXECUTABLE_PENDING_LIVE_ACCEPTANCE",
                          "executor": "SceneWriter", "elementCount": 12},
    "typical-floor-v1": {"status": "UNSUPPORTED", "reason": "no accepted floor executor"},
    "mep-network-v1": {"status": "UNSUPPORTED", "reason": "native routing/license/readback unverified"},
}
ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{3,79}$")


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2,
                                    allow_nan=False) + "\n", encoding="utf-8")


def native_transport(command, params):
    if command != "API.GetProductInfo":
        return RUN.tapir(RUN.PORT, command, params)
    request = urllib.request.Request(f"http://127.0.0.1:{RUN.PORT}",
        data=json.dumps({"command": command, "parameters": params}).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(request, timeout=15) as response:
        result = json.loads(response.read().decode("utf-8"))
    if result.get("succeeded") is not True or not isinstance(result.get("result"), dict):
        raise ValueError("ARCHICAD_PRODUCT_INFO_UNAVAILABLE")
    return result["result"]


def archicad29(api):
    product = api("API.GetProductInfo", {})
    if product.get("version") != 29:
        raise ValueError("ARCHICAD_29_REQUIRED")
    return product


def catalog_with_provenance(path):
    """Require the modified live export, including untouched source JS hashes."""
    path = Path(path)
    doc = SCENE.GRAPH.CONTRACTS.load_catalog(path)
    meta = doc.get("_metadata", {})
    if (meta.get("origin") != "live TapirCommand.GenerateDocumentation"
            or meta.get("provider_version") != RUN.EXPECTED_TAPIR):
        raise ValueError("CURRENT_MODIFIED_TAPIR_EXPORT_REQUIRED")
    for name in ("command_definitions.js", "common_schema_definitions.js"):
        raw = (path.parent / name).read_bytes()
        if hashlib.sha256(raw).hexdigest() != meta.get("inputs", {}).get(name):
            raise ValueError("SCHEMA_SOURCE_HASH_MISMATCH: " + name)
    # Hashes alone do not bind a potentially edited JSON to its source values.
    expected = parse_documentation(path.parent, meta["binding"])
    if doc != expected:
        raise ValueError("SCHEMA_EXPORT_CONTENT_MISMATCH")
    return doc


def parse_documentation(folder, binding):
    folder = Path(folder)
    def read(name, prefix):
        raw = (folder / name).read_bytes()
        value = raw.decode("utf-8").strip()
        if not value.startswith(prefix) or not value.endswith(";"):
            raise ValueError("UNEXPECTED_DOCUMENTATION_FORMAT: " + name)
        return json.loads(value[len(prefix):-1]), hashlib.sha256(raw).hexdigest()
    groups, ch = read("command_definitions.js", "var gCommands = ")
    common, sh = read("common_schema_definitions.js", "var gSchemaDefinitions = ")
    commands = {}
    for group in groups:
        for c in group["commands"]:
            if c["name"] in commands:
                raise ValueError("DUPLICATE_DOCUMENTED_COMMAND")
            commands[c["name"]] = dict(category=group["name"], description=c["description"],
                                       version=c["version"], parameters=c["inputScheme"],
                                       returns=c["outputScheme"], api="tapir", name=c["name"])
    return dict(commands=commands, common_schemas=common,
                element_types=common["ElementType"]["enum"],
                _metadata=dict(format="archicad-mcp.tapir-snapshot/1", provider="tapir",
                               provider_version=binding["tapirVersion"],
                               origin="live TapirCommand.GenerateDocumentation", binding=binding,
                               inputs={"command_definitions.js": ch, "common_schema_definitions.js": sh}))


def compile_intent(intent, schema_path):
    if (not isinstance(intent, dict) or set(intent) != {"schemaVersion", "projectId", "units", "components"}
            or intent["schemaVersion"] != "archicad-project-intent/1"
            or intent["units"] != "meters" or not isinstance(intent["projectId"], str)
            or not ID.fullmatch(intent["projectId"])):
        raise ValueError("INVALID_PROJECT_INTENT")
    parts = intent["components"]
    if not isinstance(parts, list) or len(parts) != 1:
        raise ValueError("MVP_REQUIRES_ONE_WHOLE_PAVILION: multiple components unsupported")
    part = parts[0]
    if (not isinstance(part, dict) or set(part) != {"id", "primitive", "anchor"}
            or not isinstance(part["id"], str) or not ID.fullmatch(part["id"])):
        raise ValueError("INVALID_COMPONENT")
    primitive = part["primitive"]
    if not isinstance(primitive, str) or primitive != "pavilion-frame-v1":
        raise ValueError("UNSUPPORTED_PRIMITIVE: " + str(primitive))
    anchor = part["anchor"]
    if not isinstance(anchor, dict) or set(anchor) != {"x", "y"}:
        raise ValueError("INVALID_ANCHOR")
    catalog_with_provenance(schema_path)
    preview = SCENE.prepare(anchor["x"], anchor["y"], schema_path)
    routes = {s["id"]: {"executor": "SceneWriter", "command": s["command"],
                         "readback": "GetDetailsOfElements"} for s in preview["graph"]["operations"]}
    if any(s["command"] not in RUN.ALLOWED_WRITES for s in preview["graph"]["operations"]):
        raise ValueError("UNSUPPORTED_EXECUTOR_ROUTE")
    return {**preview, "status": "ACCELERATOR_COMPILED_OFFLINE", "intent": intent,
            "intentHash": RUN.digest(intent), "routes": routes,
            "bimIntent": {"componentId": part["id"], "primitive": primitive,
                          "entities": [{"id": s["id"], "kind": SCENE.GRAPH.CREATES[s["command"]],
                                        "sourceComponent": part["id"]} for s in preview["graph"]["operations"]]},
            "primitiveRegistry": PRIMITIVES,
            "limitations": ["Pavilion frame only: no roof, zones, finishes or documentation",
                            "Metrics are intent geometry, not structural or normative acceptance",
                            "Typical floor and MEP blocked until independent live acceptance"]}


class EvidenceAPI:
    def __init__(self, transport, folder, execute=False, export=False):
        self.transport, self.folder = transport, Path(folder)
        self.allowed = READS | (RUN.ALLOWED_WRITES if execute else frozenset())
        if export:
            self.allowed = self.allowed | {"GenerateDocumentation"}
        self.calls = Counter()
        self.write_attempts = 0

    def __call__(self, command, params):
        if command not in self.allowed:
            raise ValueError("ROUTER_REFUSED: " + command)
        record = {"at": datetime.now(timezone.utc).isoformat(), "command": command, "parameters": params}
        # Persist dispatch intent BEFORE transport, including uncertain writes.
        with (self.folder / "dispatch.jsonl").open("a", encoding="utf-8") as f:
            f.write(RUN.canonical(record) + "\n")
        self.calls[command] += 1
        self.write_attempts += int(command in RUN.ALLOWED_WRITES)
        start = time.perf_counter()
        try:
            record["response"] = self.transport(command, params)
            return record["response"]
        except Exception as exc:
            record["error"] = type(exc).__name__ + ": " + str(exc)
            raise
        finally:
            record["elapsedSeconds"] = time.perf_counter() - start
            with (self.folder / "raw.jsonl").open("a", encoding="utf-8") as f:
                f.write(RUN.canonical(record) + "\n")


def inventory_guids(api):
    rows = api("GetAllElements", {}).get("elements")
    if not isinstance(rows, list):
        raise ValueError("INVALID_INVENTORY")
    guids = [r.get("elementId", {}).get("guid") for r in rows]
    if any(not isinstance(g, str) or not RUN._GUID.fullmatch(g) for g in guids):
        raise ValueError("INVALID_INVENTORY_GUID")
    guids = sorted(g.lower() for g in guids)
    if len(guids) != len(set(guids)):
        raise ValueError("DUPLICATE_INVENTORY_GUID")
    return guids


def approval_hash(compiled, preflight):
    return RUN.digest({"intentHash": compiled["intentHash"],
                       "routes": compiled["routes"], "binding": preflight["binding"],
                       "scenePlanHash": preflight["sourcePlanHash"]})


def run_project(intent, schema, folder, state_dir, mode="offline", transport=None,
                run_id=None, confirm_hash=None):
    """All evidence stays local. Execute requires an exact preflight approval hash."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=False)
    start = time.perf_counter()
    api = None
    result = {"status": "BLOCKED", "evidenceKind": "OFFLINE" if mode == "offline" else
              "LIVE" if transport is native_transport else "SYNTHETIC",
              "automaticRetry": False, "plnSaved": False}
    try:
        compiled = compile_intent(intent, schema)
        write_json(folder / "plan.json", compiled)
        result.update(intentHash=compiled["intentHash"], metrics=compiled["metrics"])
        if mode == "offline":
            result["status"] = compiled["status"]
            return result
        if mode not in {"preflight", "execute"}:
            raise ValueError("INVALID_MODE")
        api = EvidenceAPI(transport, folder, execute=mode == "execute")
        binding = RUN.guarded_project(api)  # Identity before inventory or follow-ons.
        result["archicadProduct"] = archicad29(api)
        before = inventory_guids(api)
        write_json(folder / "inventory-before.json", before)
        ledger_dir = Path(state_dir) if state_dir is not None else folder.parent / "accelerator-state"
        writer = RUN.SceneWriter(api, ledger_dir / "scene-v1-attempts.sqlite3", schema)
        anchor = intent["components"][0]["anchor"]
        ticket = writer.preflight(anchor["x"], anchor["y"])
        if ticket["binding"] != binding or ticket["graph"] != compiled["graph"]:
            raise ValueError("PLAN_OR_BINDING_CHANGED")
        token = approval_hash(compiled, ticket)
        write_json(folder / "preflight.json", ticket)
        result.update(status=ticket["status"], confirmPlanHash=token, binding=binding,
                      nativeElementsInspected=ticket["nativeElementsInspected"])
        if mode == "execute":
            if not run_id or not confirm_hash or token != confirm_hash:
                raise ValueError("EXPLICIT_EXECUTE_REQUIRES_RUN_ID_AND_MATCHING_CONFIRM_PLAN_HASH")
            # Reuse the original one-shot reservation/host/readback implementation.
            result["scene"] = writer.execute(anchor["x"], anchor["y"], run_id, ticket["sourcePlanHash"])
            result["status"] = result["scene"]["status"]
        after = inventory_guids(api)
        write_json(folder / "inventory-after.json", after)
        if RUN.guarded_project(api) != binding:
            raise ValueError("PROJECT_CHANGED_AFTER_RUN")
        added, removed = sorted(set(after)-set(before)), sorted(set(before)-set(after))
        result.update(addedGuids=added, removedGuids=removed, inventoryUnchanged=before == after)
        if mode == "preflight" and before != after:
            raise ValueError("INVENTORY_CHANGED_DURING_READ_ONLY_PREFLIGHT")
        if result["status"] == "COMPLETE_UNSAVED":
            expected = sorted(s["guid"].lower() for s in result["scene"]["steps"].values())
            if added != expected or removed:
                raise ValueError("FINAL_INVENTORY_DIFF_MISMATCH")
            # Verify every element again after the complete assembly, not just its creation.
            created = {"__plan__": compiled["graph"], **{k: {"guid": v["guid"], "kind": v["kind"]}
                       for k, v in result["scene"]["steps"].items()}}
            for step in compiled["graph"]["operations"]:
                RUN.guarded_project(api)
                params = RUN.resolve_params(step, created)
                host = RUN.check_previous_wall(api, step, created) if step["command"] in {"CreateDoors", "CreateWindows"} else None
                RUN.verify_readback(step["command"], params, RUN.requested_details(api, created[step["id"]]["guid"]), host)
            if RUN.guarded_project(api) != binding:
                raise ValueError("PROJECT_CHANGED_DURING_WHOLE_ASSEMBLY_READBACK")
            result["wholeAssemblyReadback"] = True
    except Exception as exc:
        result.update(status="PARTIAL_OR_UNKNOWN_OUTCOME" if api and api.write_attempts else "BLOCKED",
                      reason=type(exc).__name__ + ": " + str(exc))
        if api and api.write_attempts:
            result["manualReconciliationRequired"] = True
    finally:
        result.update(elapsedSeconds=round(time.perf_counter()-start, 6),
                      commandCounts=dict(api.calls) if api else {},
                      modelWriteAttempts=api.write_attempts if api else 0)
        write_json(folder / "result.json", result)
        manifest = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.iterdir() if p.is_file()}
        write_json(folder / "SHA256.json", manifest)
    return result


def export_schema(folder, transport):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=False)
    api = EvidenceAPI(transport, folder, export=True)
    before = RUN.guarded_project(api)
    product = archicad29(api)
    guids = inventory_guids(api)
    response = api("GenerateDocumentation", {"destinationFolder": str(folder.resolve())})
    if response.get("success") is not True:
        raise ValueError("DOCUMENTATION_EXPORT_FAILED")
    after = RUN.guarded_project(api)
    if before != after or inventory_guids(api) != guids:
        raise ValueError("PROJECT_OR_INVENTORY_CHANGED_DURING_EXPORT")
    doc = parse_documentation(folder, before)
    write_json(folder / "tapir-scene-live.json", doc)
    write_json(folder / "tapir-export-evidence.json", {
        "before": before, "after": after, "exportResponse": response,
        "archicadProduct": product,
        "inventoryUnchanged": True, "modelWriteCommands": 0, "plnSaved": False})
    return {"status": "LIVE_SCHEMA_EXPORTED", "schema": str(folder / "tapir-scene-live.json"),
            "commands": len(doc["commands"]), "modelDumpDocumented": "GetModelDumpV1" in doc["commands"],
            "mepCommands": [c for c in doc["commands"] if "MEP" in c]}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--intent", type=Path)
    p.add_argument("--schema", type=Path, default=RUN.DEFAULT_SCENE_SCHEMA)
    p.add_argument("--output", type=Path, required=True, help="new evidence directory")
    p.add_argument("--data-dir", type=Path, help="stable local ledger directory; never replace to retry")
    group = p.add_mutually_exclusive_group()
    group.add_argument("--preflight", action="store_true")
    group.add_argument("--execute", action="store_true")
    group.add_argument("--refresh-schema", action="store_true")
    p.add_argument("--run-id")
    p.add_argument("--confirm-plan-hash")
    args = p.parse_args(argv)
    try:
        transport = native_transport
        if args.refresh_schema:
            result = export_schema(args.output, transport)
        else:
            if not args.intent:
                raise ValueError("--intent required")
            if args.execute and (not args.run_id or not args.confirm_plan_hash or not args.data_dir):
                raise ValueError("--execute requires --run-id, --confirm-plan-hash and stable --data-dir")
            intent = json.loads(args.intent.read_text(encoding="utf-8-sig"))
            result = run_project(intent, args.schema, args.output, args.data_dir,
                                 "execute" if args.execute else "preflight" if args.preflight else "offline",
                                 transport, args.run_id, args.confirm_plan_hash)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["status"] in {"LIVE_SCHEMA_EXPORTED", "ACCELERATOR_COMPILED_OFFLINE", "READY_FOR_EXPLICIT_TEST_RUN", "COMPLETE_UNSAVED"} else 2
    except Exception as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    sys.exit(main())
