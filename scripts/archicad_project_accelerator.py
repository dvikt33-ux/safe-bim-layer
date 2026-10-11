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
import math
from pathlib import Path
import re
import sys
import time
import urllib.request

import archicad_scene_run as RUN
import archicad_scene_v1 as SCENE
import archicad_building_shell as BUILD
import archicad_semantic_brief as BRIEF
import archicad_project_library_pack as PACK
import archicad_semantic_spatial as SPATIAL
import archicad_authored_native_plan as AUTHORED_NATIVE

READS = frozenset({"GetProjectInfo", "GetStories", "GetAddOnVersion",
                  "GetAllElements", "Get3DBoundingBoxes", "GetDetailsOfElements",
                  "GetAttributesByType", "GetSubelementsOfHierarchicalElements", "API.GetProductInfo"})
NATIVE_MUTATIONS = RUN.ALLOWED_WRITES | frozenset({"ModifySlabs"})
PRIMITIVES = {
    "pavilion-frame-v1": {"status": "EXECUTABLE_PENDING_LIVE_ACCEPTANCE",
                          "executor": "SceneWriter", "elementCount": 12},
    "building-shell-v1": {"status": "COMPILES_TO_GUARDED_SCENE_WRITER",
                          "executor": "SceneWriter",
                          "structuralVerification": "NOT_VERIFIED"},
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


def compile_project_brief(brief, read_api=None):
    """Semantic contract entry for future project compiler stages (zero writes).

    This deliberately does NOT route to SceneWriter or create projects;
    current compile_intent()/run_project() behavior is unchanged.
    P70.A02.S02/S03 will supply evidence-backed attributes and systems.
    """
    contract = BRIEF.normalize(brief)
    if read_api is None:
        contract["nativeResolution"] = ("NEEDS_NEW_PROJECT_SETUP"
                                        if contract["mode"] == "GENERATE_FROM_ZERO"
                                        else "NEEDS_STORY_RESOLUTION")
        return contract
    return BRIEF.resolve_stories(contract, read_api)


def compile_project_library_pack(brief, cse_candidate, read_api=None):
    """Read-only project-local CSE/attribute slice for the current single PLN.

    Source rights/detail engineering status remain explicit; reuse the existing
    material resolver. No additional executor or geometry creation.
    """
    return PACK.compile_pack(brief, cse_candidate, api=read_api)


def compile_project_spatial_plan(brief, project_pack, authored_layout):
    """Plan authored rooms/axes/load paths in the existing accelerator.

    Does not fabricate walls or modify PLN. The sole BIM DAG compiler remains
    archicad_bim_graph.compile_graph, used in the later S02 emission gate.
    """
    return SPATIAL.compile_spatial(brief, project_pack, authored_layout)


def compile_authored_native_candidate(brief, project_pack, authored_layout,
                                      authored_story_heights, read_api,
                                      schema_path=RUN.DEFAULT_SCENE_SCHEMA):
    """Read-only existing BIM DAG compiler, no SceneWriter.execute.

    Never exposes a native mutation token; no authority to write follows from
    a valid offline command graph or from prior successful scratch evidence.
    """
    catalog_with_provenance(schema_path)
    return AUTHORED_NATIVE.compile_candidate(
        brief,project_pack,authored_layout,authored_story_heights,
        read_api,schema_path=schema_path)


def compile_intent(intent, schema_path):
    if (not isinstance(intent, dict) or set(intent) !=
            {"schemaVersion", "projectId", "units", "components"}
            or intent["schemaVersion"] != "archicad-project-intent/1"
            or intent["units"] != "meters" or not isinstance(intent["projectId"], str)
            or not ID.fullmatch(intent["projectId"])):
        raise ValueError("INVALID_PROJECT_INTENT")
    parts = intent["components"]
    if not isinstance(parts, list) or len(parts) != 1:
        raise ValueError("ONLY_ONE_COORDINATED_BUILDING_COMPONENT_SUPPORTED")
    part = parts[0]
    if not isinstance(part, dict) or part.get("primitive") not in {
            "pavilion-frame-v1", "building-shell-v1"}:
        raise ValueError("UNSUPPORTED_PRIMITIVE: " + str(part.get("primitive") if isinstance(part, dict) else part))
    if not isinstance(part.get("id"), str) or not ID.fullmatch(part["id"]):
        raise ValueError("INVALID_COMPONENT_ID")
    primitive = part["primitive"]
    catalog_with_provenance(schema_path)
    if primitive == "building-shell-v1":
        preview = BUILD.prepare(part, schema_path)
    else:
        if set(part) != {"id", "primitive", "anchor"}:
            raise ValueError("INVALID_PAVILION_COMPONENT")
        anchor = part["anchor"]
        if not isinstance(anchor, dict) or set(anchor) != {"x", "y"}:
            raise ValueError("INVALID_ANCHOR")
        preview = SCENE.prepare(anchor["x"], anchor["y"], schema_path)
    routes = {step["id"]: {"executor": "SceneWriter", "command": step["command"],
                           "readback": "GetDetailsOfElements"}
              for step in preview["graph"]["operations"]}
    if any(step["command"] not in RUN.ALLOWED_WRITES
           for step in preview["graph"]["operations"]):
        raise ValueError("UNSUPPORTED_EXECUTOR_ROUTE")
    return {**preview, "status": "ACCELERATOR_COMPILED_OFFLINE", "intent": intent,
            "intentHash": RUN.digest(intent), "routes": routes,
            "bimIntent": {
                "componentId": part["id"], "primitive": primitive,
                "entities": [{"id": step["id"], "kind": SCENE.GRAPH.CREATES[step["command"]],
                              "sourceComponent": part["id"]}
                             for step in preview["graph"]["operations"]]},
            "primitiveRegistry": PRIMITIVES,
            "limitations": preview.get("limitations", [
                "Pavilion only: no roof, zones, finishes or documentation",
                "Metrics are geometry, not structural/normative acceptance",
                "Typical floor and MEP require independent live acceptance"])}


def compile_authored_intent(intent, schema_path, read_api):
    """Join authored brief/PLP/geometry to the same existing native execution path."""
    required = {
            "schemaVersion", "projectId", "units", "brief", "cseCandidate",
            "layout", "storyHeights"}
    if (not isinstance(intent, dict) or not required <= set(intent)
            or set(intent)-required-{"wallBasicMaterialName","nativeComponents"}
            or intent["schemaVersion"] != "apa-authored-project/1"
            or intent["units"] != "meters"
            or not isinstance(intent["projectId"], str)
            or not ID.fullmatch(intent["projectId"])
            or intent["brief"].get("projectId") != intent["projectId"]
            or intent["brief"].get("targetProjectPath") != RUN.EXPECTED_PATH):
        raise ValueError("INVALID_AUTHORED_PROJECT_OR_WRITER_TARGET")
    catalog_with_provenance(schema_path)
    pack = compile_project_library_pack(intent["brief"], intent["cseCandidate"], read_api)
    candidate = compile_authored_native_candidate(
        intent["brief"], pack, intent["layout"], intent["storyHeights"],
        read_api, schema_path=schema_path)
    if "wallBasicMaterialName" in intent:
        wall_guid = RUN.resolve_basic_slab_material(read_api,intent["wallBasicMaterialName"])
        for step in candidate["graph"]["operations"]:
            if step["command"] == "CreateWalls":
                step["params"]["wallsData"][0]["buildingMaterialId"]={"guid":wall_guid}
    additions = intent.get("nativeComponents", [])
    if not isinstance(additions,list) or len(additions)>100:
        raise ValueError("INVALID_AUTHORED_NATIVE_COMPONENTS")
    story_indices={b["nativeIndex"] for b in candidate["storyBindings"]}
    outline=candidate["authoredOutline"]
    for step in additions:
        if not isinstance(step,dict) or step.get("command") not in {
                "CreateColumns","CreateDoors","CreateWindows"}:
            raise ValueError("UNSUPPORTED_AUTHORED_NATIVE_COMPONENT")
        if step["command"]=="CreateColumns":
            columns=step.get("params",{}).get("columnsData",[])
            if len(columns)!=1 or columns[0].get("floorIndex") not in story_indices:
                raise ValueError("AUTHORED_COLUMN_STORY_REQUIRED")
            point=columns[0].get("coordinates",{})
            if not all(type(point.get(k)) in (int,float) and math.isfinite(point[k]) for k in ("x","y","z")):
                raise ValueError("AUTHORED_COLUMN_COORDINATES_REQUIRED")
            if not (outline["xMin"]<=point["x"]<=outline["xMax"] and
                    outline["yMin"]<=point["y"]<=outline["yMax"]):
                raise ValueError("AUTHORED_COLUMN_OUTSIDE_BUILDING")
    if additions or "wallBasicMaterialName" in intent:
        candidate["graph"]["operations"].extend(json.loads(RUN.canonical(additions)))
        checked=SCENE.GRAPH.compile_graph(catalog_with_provenance(schema_path),candidate["graph"],runtime_version=RUN.EXPECTED_TAPIR)
        if checked["status"]!="PLAN_VALIDATED_OFFLINE":
            raise ValueError("AUTHORED_COMPONENT_GRAPH_REFUSED: "+checked["status"])
        candidate.update(sourcePlanHash=checked["sourcePlanHash"],executionOrder=checked["executionOrder"],
            operationCount=len(candidate["graph"]["operations"]),
            plannedNativeCommands=dict(Counter(s["command"] for s in candidate["graph"]["operations"])))
    preview = AUTHORED_NATIVE.as_existing_scene_writer_preview(candidate)
    return {**preview, "status": "ACCELERATOR_COMPILED_OFFLINE",
            "intent": intent, "intentHash": RUN.digest(intent),
            "authoredCandidate": candidate,
            "routes": {s["id"]: {"executor": "SceneWriter", "command": s["command"],
                                    "readback": "GetDetailsOfElements"}
                       for s in preview["graph"]["operations"]}}


class EvidenceAPI:
    def __init__(self, transport, folder, execute=False, export=False):
        self.transport, self.folder = transport, Path(folder)
        self.allowed = READS | (NATIVE_MUTATIONS if execute else frozenset())
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
        self.write_attempts += int(command in NATIVE_MUTATIONS)
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


def column_subelements(api, created):
    columns = [v['guid'] for v in created.values() if v.get('kind')=='Column']
    if not columns:
        return {}
    rows = api('GetSubelementsOfHierarchicalElements',
        {'elements':[{'elementId':{'guid':g}} for g in columns]}).get('subelements')
    if not isinstance(rows,list) or len(rows)!=len(columns):
        raise ValueError('COLUMN_HIERARCHY_READBACK_MISMATCH')
    mapping = {}
    seen = {v['guid'].lower() for v in created.values()}
    for parent, row in zip(columns,rows):
        if not isinstance(row,dict) or set(row)-{'columnSegments'}:
            raise ValueError('UNEXPECTED_COLUMN_SUBELEMENT_TYPE')
        children = row.get('columnSegments')
        if not isinstance(children,list) or not children:
            raise ValueError('COLUMN_SEGMENTS_NOT_PROVEN')
        guids=[]
        for child in children:
            guid=child.get('elementId',{}).get('guid')
            if not isinstance(guid,str) or not RUN._GUID.fullmatch(guid) or guid.lower() in seen:
                raise ValueError('INVALID_OR_DUPLICATED_COLUMN_SEGMENT_GUID')
            seen.add(guid.lower());guids.append(guid.lower())
        mapping[parent.lower()] = sorted(guids)
    return mapping


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
        authored = isinstance(intent, dict) and intent.get("schemaVersion") == "apa-authored-project/1"
        if authored:
            if mode not in {"preflight", "execute"} or not callable(transport):
                raise ValueError("AUTHORED_NATIVE_REQUIRES_EXPLICIT_READ_ONLY_PREFLIGHT")
            # Exact identity is checked before resolving any authored native data.
            api = EvidenceAPI(transport, folder, execute=mode == "execute")
            RUN.guarded_project(api)
            compiled = compile_authored_intent(intent, schema, api)
        else:
            compiled = compile_intent(intent, schema)
        write_json(folder / "plan.json", compiled)
        result.update(intentHash=compiled["intentHash"], metrics=compiled["metrics"])
        if mode == "offline":
            result["status"] = compiled["status"]
            return result
        if mode not in {"preflight", "execute"}:
            raise ValueError("INVALID_MODE")
        if api is None:
            api = EvidenceAPI(transport, folder, execute=mode == "execute")
        required_story = (compiled.get("storyBindings") or [None])[0]
        binding = RUN.guarded_project(api, required_story)  # Identity before inventory.
        result["archicadProduct"] = archicad29(api)
        before = inventory_guids(api)
        write_json(folder / "inventory-before.json", before)
        ledger_dir = Path(state_dir) if state_dir is not None else folder.parent / "accelerator-state"
        writer = RUN.SceneWriter(api, ledger_dir / "scene-v1-attempts.sqlite3", schema,
                                 preview_factory=(
                                     AUTHORED_NATIVE.make_read_only_scene_writer_preview_factory(
                                         compiled["authoredCandidate"]) if authored else
                                     (lambda x, y, path: BUILD.prepare(intent["components"][0], path))
                                     if required_story is not None else None))
        anchor = ({"x": compiled["envelope"]["xMin"], "y": compiled["envelope"]["yMin"]}
                  if authored else intent["components"][0]["anchor"])
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
        if RUN.guarded_project(api, required_story) != binding:
            raise ValueError("PROJECT_CHANGED_AFTER_RUN")
        added, removed = sorted(set(after)-set(before)), sorted(set(before)-set(after))
        result.update(addedGuids=added, removedGuids=removed, inventoryUnchanged=before == after)
        if mode == "preflight" and before != after:
            raise ValueError("INVENTORY_CHANGED_DURING_READ_ONLY_PREFLIGHT")
        if result["status"] == "COMPLETE_UNSAVED":
            expected = sorted(s["guid"].lower() for s in result["scene"]["steps"].values())
            if authored:
                children=column_subelements(api,result['scene']['steps'])
                expected=sorted(expected+[g for group in children.values() for g in group])
                result['ownedColumnSegments']=children
            if added != expected or removed:
                raise ValueError("FINAL_INVENTORY_DIFF_MISMATCH")
            # Verify every element again after the complete assembly, not just its creation.
            created = {"__plan__": compiled["graph"], **{k: {"guid": v["guid"], "kind": v["kind"]}
                       for k, v in result["scene"]["steps"].items()}}
            for step in compiled["graph"]["operations"]:
                RUN.guarded_project(api, required_story)
                params = RUN.resolve_params(step, created)
                host = (RUN.check_previous_wall(
                            api, step, created, ticket.get("storyBindings"))
                        if step["command"] in {"CreateDoors", "CreateWindows"} else None)
                if host:
                    parent_id = next(iter(step["params"].values()))[0]["ownerWallId"]["guid"]["$createdGuid"]
                    parent_step = next(s for s in compiled["graph"]["operations"]
                                       if s["id"] == parent_id)
                    expected_floor = parent_step["params"]["wallsData"][0]["floorIndex"]
                else:
                    expected_floor = next(iter(params.values()))[0]["floorIndex"]
                RUN.verify_readback(
                    step["command"], params,
                    RUN.requested_details(api, created[step["id"]]["guid"]),
                    host, expected_floor=expected_floor,
                    expected_story_level=RUN.story_level_for_floor(
                        ticket.get("storyBindings"), expected_floor),
                    expected_slab_material_guid=(
                        ticket.get("slabBasicMaterialGuid")
                        if step["command"] == "CreateSlabs" else None),
                    slab_level_is_absolute=(ticket.get("slabLevelConvention")=="PROJECT_ABSOLUTE"))
            if RUN.guarded_project(api, required_story) != binding:
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
    p.add_argument("--scratch-port", type=int,
                   help="Use only the approved disposable C:\\LocalAI\\APA_Test_House_01.pln on this port")
    p.add_argument("--isolated-port", type=int,
                   help="Use only user-authorized C:\\LocalAI\\APA_Isolated_Writer_Test_01.pln")
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
            if args.scratch_port is not None and args.isolated_port is not None:
                raise ValueError("ONLY_ONE_EXPLICIT_NATIVE_TARGET")
            if args.isolated_port is not None:
                RUN.bind_isolated_writer_pln(args.isolated_port)
            elif args.scratch_port is not None:
                RUN.bind_approved_scratch_pln(args.scratch_port)
            elif (args.preflight or args.execute) and any(
                    c.get("primitive") == "building-shell-v1"
                    for c in intent.get("components", []) if isinstance(c, dict)):
                raise ValueError("BUILDING_LIVE_REQUIRES_EXPLICIT_APPROVED_SCRATCH_PORT")
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
