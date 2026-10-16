"""APA catalog-driven execution-strategy discovery (PREVIEW ONLY).

Converts *source-qualified, typed* building intent to available Archicad
strategies. All candidate commands must already be in the deployed dynamic
catalog with reviewed CREATE effect. Discovery reuses existing
DynamicCommands.plan_reuse_existing -> BIM Graph schema validation -> Fast
Downward cost selector -> APA native-task preview -> existing SceneWriter.

No natural-language geometry guesses, execution, retries, model saves, new
writer or alternate transport. Unsupported element families fail closed.
Benchmark costs must be end-to-end and exact-batch-size, with contract hashes.
Uncalibrated competing strategies are exposed but NEVER ranked as fastest.

V2 adds homogeneous Wall/Slab create/copy/modify batches and Window/Door create
batches on verified existing straight Wall hosts. It preserves V1 structural
recipes. Scanning the catalog does not imply a typed adapter or live acceptance.
"""
from __future__ import annotations

import json
import math
import hashlib
from jsonschema.exceptions import ValidationError, SchemaError

from archicad_execution_optimizer import prepare_optimized_native_task


COPY_NAME = "native_copy_existing_batch"
CREATE_NAME = "native_create_columns_batch"
BEAM_CREATE_NAME = "native_create_beams_batch"
CAPABILITY = {
    "MoveElements": {
        "strategy": COPY_NAME,
        "requirements": "source-verified geometry family/anchor + native copy policy",
    },
    "CreateColumns": {
        "strategy": CREATE_NAME,
        "requirements": "source-verified complete target column creation rows",
    },
    "CreateBeams": {
        "strategy": BEAM_CREATE_NAME,
        "requirements": "source-verified complete target beam creation rows on story zero",
    },
}
# Typed recipes refer to the existing catalog; these are not command schemas
# or effect policies. All parameters are still validated by DynamicCommands.
for _command, _effect in {
    "CreateWalls": "CREATE", "CreateSlabs": "CREATE",
    "CreateWindows": "CREATE", "CreateDoors": "CREATE",
    "ModifyWalls": "MODIFY", "ModifySlabs": "MODIFY",
}.items():
    CAPABILITY[_command] = {"effect": _effect,
                            "requirements": "V2 source-qualified exact BIM data"}

CREATE_SLOTS = {"Column": ("CreateColumns", "columnsData"),
                "Beam": ("CreateBeams", "beamsData"),
                "Wall": ("CreateWalls", "wallsData"),
                "Slab": ("CreateSlabs", "slabsData"),
                "Window": ("CreateWindows", "windowsData"),
                "Door": ("CreateDoors", "doorsData")}


def source_data_hash(target):
    """Bind the complete prepared BIM record, including host/story/settings."""
    value = {k: v for k, v in target.items() if k != "sourceVerification"}
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True,
                     allow_nan=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _v2_sources(targets):
    require(isinstance(targets, list) and 1 <= len(targets) <= 200,
            "AUTO_DISCOVERY_V2_REQUIRES_1_TO_200_TARGETS")
    for target in targets:
        require(isinstance(target, dict), "AUTO_DISCOVERY_V2_TYPED_TARGET_REQUIRED")
        proof = target.get("sourceVerification", {})
        require(isinstance(proof, dict) and proof.get("status") == "SOURCE_VERIFIED"
                and proof.get("dataHash") == source_data_hash(target)
                and isinstance(proof.get("evidenceRef"), str)
                and len(proof["evidenceRef"].strip()) >= 8,
                "AUTO_DISCOVERY_V2_SOURCE_DATA_PROVENANCE_OR_HASH_REQUIRED")
    require(len({t.get("type") for t in targets}) == 1
            and len({t.get("operation", "CREATE") for t in targets}) == 1,
            "AUTO_DISCOVERY_V2_HOMOGENEOUS_COMPLETE_BATCH_REQUIRED")


def _finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def _v2_polygon(row, outline):
    require(row.get("polygonArcs") == [],
            "AUTO_DISCOVERY_V2_CURVED_SLAB_REQUIRES_ANALYTIC_GEOMETRY_QUALIFIER")
    from archicad_building_shell import source_floor_polygon
    # Validate the original shape without replacing it with an approximation
    # or silently applying the helper's winding normalization to source data.
    source_floor_polygon({"polygonCoordinates": row[outline], "holes": row["holes"]})


def _v2_modify_targets(targets, existing):
    kind = targets[0]["type"]
    require(kind in {"Wall", "Slab"}, "AUTO_DISCOVERY_V2_NO_TYPED_MODIFY_ADAPTER")
    command, field = ("ModifyWalls", "wallsWithDetails") if kind == "Wall" else (
        "ModifySlabs", "slabsWithDetails")
    baseline = {s["guid"].lower(): s for s in existing}
    rows, used = [], set()
    for target in targets:
        row = target.get("nativeModifyData", {})
        guid = row.get("elementId", {}).get("guid", "").lower()
        source = baseline.get(guid, {})
        require(guid and guid not in used and len(row) > 1
                and source.get("type") == kind
                and source.get("nativeReadbackVerified") is True
                and source.get("storyIndex") == target["storyIndex"]
                and source.get("nativeDependenciesVerified") is True
                and source.get("dependentElementGuids") == []
                and isinstance(source.get("nativeSignatureSHA256"), str)
                and len(source["nativeSignatureSHA256"]) == 64
                and target.get("baselineSignatureSHA256") == source["nativeSignatureSHA256"],
                "AUTO_DISCOVERY_V2_MODIFY_EXACT_INDEPENDENT_BASELINE_REQUIRED")
        if kind == "Slab" and "polygonOutline" in row:
            require("holes" in row and "polygonArcs" in row,
                    "AUTO_DISCOVERY_V2_REPLACED_SLAB_MUST_PRESERVE_EXPLICIT_HOLES_AND_ARCS")
            _v2_polygon(row, "polygonOutline")
        elif kind == "Slab" and ("holes" in row or "polygonArcs" in row):
            raise ValueError("AUTO_DISCOVERY_V2_SLAB_HOLE_EDIT_REQUIRES_COMPLETE_OUTLINE")
        if kind == "Wall":
            require(not ({"height", "relativeTopStory"} <= set(row)),
                    "AUTO_DISCOVERY_V2_CONFLICTING_WALL_TOP_SETTINGS")
            if "begCoordinate" in row or "endCoordinate" in row:
                require({"begCoordinate", "endCoordinate", "arcAngle"} <= set(row)
                        and row["begCoordinate"] != row["endCoordinate"],
                        "AUTO_DISCOVERY_V2_COMPLETE_WALL_REFERENCE_SEGMENT_REQUIRED")
        used.add(guid)
        rows.append(immutable(row))
    return command, field, rows


def _v2_host_batch(targets):
    hosts, spans = {}, {}
    for target in targets:
        host, row = target["hostContext"], target["nativeCreateData"]
        guid = host["guid"].lower()
        require(guid not in hosts or hosts[guid] == host,
                "AUTO_DISCOVERY_V2_INCONSISTENT_HOST_CONTEXT")
        hosts[guid] = host
        lo, hi = row["centerOffset"]-row["width"]/2, row["centerOffset"]+row["width"]/2
        require(all(min(hi, end)-max(lo, start) <= 1e-7
                    for start, end in spans.get(guid, [])),
                "AUTO_DISCOVERY_V2_BATCH_HOST_OPENING_COLLISION")
        spans.setdefault(guid, []).append((lo, hi))


def _v2_create_row(target):
    kind, row, anchor = target["type"], target.get("nativeCreateData"), target["anchor"]
    require(isinstance(row, dict), "AUTO_DISCOVERY_V2_EXACT_NATIVE_DATA_REQUIRED")
    require(type(target.get("storyIndex")) is int
            and _finite(target.get("storyElevation")),
            "AUTO_DISCOVERY_V2_SOURCE_STORY_ELEVATION_REQUIRED")
    if kind in {"Wall", "Slab"}:
        require(row.get("floorIndex") == target["storyIndex"],
                "AUTO_DISCOVERY_V2_HOME_STORY_MISMATCH")
    if kind == "Wall":
        require(all(k in row for k in ("begCoordinate", "endCoordinate", "height",
                    "thickness", "zCoordinate", "offset", "arcAngle",
                    "referenceLineLocation", "structureType")),
                "AUTO_DISCOVERY_V2_COMPLETE_WALL_SETTINGS_REQUIRED")
        a, b = row["begCoordinate"], row["endCoordinate"]
        require(a != b and all(abs(a[k]-anchor[k]) < 1e-7 for k in ("x", "y"))
                and abs(target["storyElevation"]+row["zCoordinate"]-anchor["z"]) < 1e-7,
                "AUTO_DISCOVERY_V2_WALL_ANCHOR_OR_STORY_OFFSET_MISMATCH")
        attribute = {"Basic": "buildingMaterialId", "Composite": "compositeId",
                     "Profile": "profileId"}.get(row["structureType"])
        require(attribute in row if attribute else False,
                "AUTO_DISCOVERY_V2_EXACT_WALL_ATTRIBUTE_REQUIRED")
    elif kind == "Slab":
        require(all(k in row for k in ("level", "thickness", "referencePlaneLocation",
                                      "polygonCoordinates", "holes", "polygonArcs",
                                      "favoriteName")),
                "AUTO_DISCOVERY_V2_COMPLETE_SLAB_SETTINGS_REQUIRED")
        # This pinned CreateSlabs contract has NO material/structure parameter.
        # Those must come from an exact, independently qualified Favorite.
        settings = target.get("settingsQualification", {})
        require(settings.get("status") == "SOURCE_VERIFIED"
                and settings.get("favoriteName") == row["favoriteName"]
                and isinstance(settings.get("settingsHash"), str)
                and len(settings["settingsHash"]) == 64
                and settings.get("attributesVerified") is True,
                "AUTO_DISCOVERY_V2_SLAB_FAVORITE_ATTRIBUTES_NOT_QUALIFIED")
        p = row["polygonCoordinates"][0]
        require(all(abs(p[k]-anchor[k]) < 1e-7 for k in ("x", "y"))
                and abs(row["level"]-anchor["z"]) < 1e-7,
                "AUTO_DISCOVERY_V2_SLAB_ANCHOR_MISMATCH")
        require(row["referencePlaneLocation"] in {"Top", "Bottom"}
                or settings.get("structureType") == "Composite",
                "AUTO_DISCOVERY_V2_SLAB_REFERENCE_PLANE_INCOMPATIBLE")
        _v2_polygon(row, "polygonCoordinates")
    elif kind in {"Window", "Door"}:
        require(all(k in row for k in ("ownerWallId", "centerOffset", "width", "height",
                                      "sillHeight", "reflected", "refSide", "oSide"))
                and bool(row.get("favoriteName") or row.get("libraryPartName")),
                "AUTO_DISCOVERY_V2_COMPLETE_HOSTED_SETTINGS_REQUIRED")
        host = target.get("hostContext", {})
        require(host.get("type") == "Wall" and host.get("nativeReadbackVerified") is True
                and host.get("relationshipsComplete") is True
                and host.get("guid") == row["ownerWallId"].get("guid")
                and host.get("storyIndex") == target["storyIndex"]
                and isinstance(host.get("existingOpenings"), list),
                "AUTO_DISCOVERY_V2_VERIFIED_EXISTING_WALL_HOST_REQUIRED")
        wall = host.get("wallData", {})
        require(wall.get("arcAngle") == 0
                and all(k in wall for k in ("begCoordinate", "endCoordinate", "height")),
                "AUTO_DISCOVERY_V2_STRAIGHT_HOST_GEOMETRY_REQUIRED")
        library = target.get("libraryQualification", {})
        require(library.get("status") == "SOURCE_VERIFIED"
                and library.get("libraryPartName") == row.get("libraryPartName")
                and library.get("favoriteName") == row.get("favoriteName")
                and isinstance(library.get("settingsHash"), str)
                and len(library["settingsHash"]) == 64,
                "AUTO_DISCOVERY_V2_HOSTED_LIBRARY_QUALIFICATION_REQUIRED")
        a, b = wall["begCoordinate"], wall["endCoordinate"]
        length = math.hypot(b["x"]-a["x"], b["y"]-a["y"])
        require(length > 1e-7 and _finite(wall.get("zCoordinate")),
                "AUTO_DISCOVERY_V2_NONZERO_HOST_AND_EXACT_BASE_REQUIRED")
        expected = {k: a[k]+(b[k]-a[k])*row["centerOffset"]/length for k in ("x", "y")}
        expected["z"] = target["storyElevation"]+wall["zCoordinate"]+row["sillHeight"]
        require(all(abs(expected[k]-anchor[k]) <= 1e-7 for k in ("x", "y", "z")),
                "AUTO_DISCOVERY_V2_HOSTED_ANCHOR_MISMATCH")
        import archicad_bim_graph as G
        field = CREATE_SLOTS[kind][1]
        check_row = immutable(row)
        check_row["ownerWallId"] = {"guid": {"$createdGuid": "host"}}
        step = {"id": "child", "command": CREATE_SLOTS[kind][0],
                "params": {field: [check_row]}}
        require(not G._hosted_fit_errors(step, {"host": {
            "command": "CreateWalls", "params": {"wallsData": [wall]}}}),
            "AUTO_DISCOVERY_V2_HOSTED_ELEMENT_OUTSIDE_HOST")
        lo, hi = row["centerOffset"]-row["width"]/2, row["centerOffset"]+row["width"]/2
        for old in host["existingOpenings"]:
            require(all(_finite(old.get(k)) for k in ("start", "end"))
                    and old["start"] < old["end"],
                    "AUTO_DISCOVERY_V2_EXISTING_OPENING_EXTENT_REQUIRED")
            require(min(hi, old["end"])-max(lo, old["start"]) <= 1e-7,
                    "AUTO_DISCOVERY_V2_EXISTING_HOST_OPENING_COLLISION")
    else:
        raise ValueError("AUTO_DISCOVERY_V2_NO_TYPED_CREATE_ADAPTER:" + kind)
    return immutable(row)


def require(test, reason):
    if not test:
        raise ValueError(reason)


def immutable(value):
    return json.loads(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                 allow_nan=False))


def _catalog_find(router):
    catalog = getattr(router, "catalog", {})
    commands = catalog.get("commands", {}) if isinstance(catalog, dict) else {}
    require(isinstance(commands, dict), "AUTO_DISCOVERY_INVALID_APA_COMMAND_CATALOG")
    discovered = []
    ineligible = []
    for command, contract in commands.items():
        if command not in CAPABILITY:
            continue
        if not isinstance(contract, dict):
            ineligible.append({"command": command, "reason": "MALFORMED_CONTRACT"})
            continue
        if contract.get("executionBlocker"):
            ineligible.append({"command": command, "reason": "EXISTING_CONTRACT_EXECUTION_BLOCKER",
                               "detail": contract["executionBlocker"]})
            continue
        if router.operation_kind(command) != CAPABILITY[command].get("effect", "CREATE"):
            ineligible.append({"command": command, "reason": "NO_REVIEWED_OPERATION_POLICY"})
            continue
        if contract.get("availability") in {
                "NOT_EXPOSED", "SOURCE_CONTRACT_NOT_RUNTIME_PROBED",
                "LOCAL_DEPENDENCIES_NOT_CHECKED", "UNAVAILABLE", "NOT_TESTED",
                "SOURCE_SNAPSHOT_NOT_RUNTIME_PROBED"} or getattr(router, "registration", {}).get(command) is False:
            ineligible.append({"command": command,
                               "reason": "NOT_RUNTIME_QUALIFIED_FOR_LIVE"})
            continue
        discovered.append(command)
    return discovered, ineligible, len(commands)


def _presence_key(row):
    family = (row["type"], row["familySignature"], row["storyIndex"])
    key = (family, *(round(row["anchor"][k], 7) for k in ("x", "y", "z")))
    if row["type"] in {"Window", "Door"}:
        owner = row.get("ownerWallGuid") or row.get("nativeCreateData", {}).get("ownerWallId", {}).get("guid")
        key += (owner,)
    return key


def _native_create_targets(targets, present, v2=False):
    """Find complete typed create families WITHOUT inventing profile or stories.

    V1 prepares exactly one homogeneous family per create alternative.
    Beams require start and end endpoints, nonzero span, exact source
    elevation and first-story origin 0. Higher story beams require a separate
    story-level qualifier and are therefore excluded.
    """
    rows = []
    created_types = set()
    for target in targets:
        a = target["anchor"]
        key = _presence_key(target)
        if key in present:
            continue
        kind = target["type"]
        if kind not in CREATE_SLOTS:
            return None
        if kind not in {"Column", "Beam"}:
            if not v2:
                return None
            rows.append(_v2_create_row(target))
            created_types.add(kind)
            continue
        native = target.get("nativeCreateData")
        if not isinstance(native, dict):
            return None
        native = immutable(native)
        created_types.add(kind)
        if ("buildingMaterialId" not in native or "width" not in native
                or "height" not in native):
            return None
        if "floorIndex" not in native or native["floorIndex"] != target["storyIndex"]:
            return None
        if kind == "Column":
            xyz = native.get("coordinates")
            if (not isinstance(xyz, dict) or set(xyz) != {"x", "y", "z"}
                    or "depth" not in native):
                return None
            if any(type(xyz[k]) not in (int, float) or not math.isfinite(xyz[k])
                   or abs(xyz[k]-a[k]) > 1e-7 for k in ("x", "y", "z")):
                return None
        else:
            begin = native.get("begCoordinate")
            end = native.get("endCoordinate")
            if (not isinstance(begin, dict) or set(begin) != {"x", "y"}
                    or not isinstance(end, dict) or set(end) != {"x", "y"}):
                return None
            if (any(type(v) not in (int, float) or not math.isfinite(v)
                    for v in (*begin.values(), *end.values()))
                    or not all(abs(begin[k]-a[k]) <= 1e-7 for k in ("x", "y"))
                    or all(abs(begin[k]-end[k]) < 1e-7 for k in ("x", "y"))):
                return None
            if (target["storyIndex"] != 0
                    or type(native.get("zCoordinate")) not in (int, float)
                    or not math.isfinite(native["zCoordinate"])
                    or abs(native["zCoordinate"] - a["z"]) > 1e-7):
                return None
        rows.append(native)
    if len(created_types) != 1:
        return None
    kind = next(iter(created_types))
    return CREATE_SLOTS[kind][0], rows


def _calibrate(router, command, count, benchmarks, workload_hash=None):
    row = benchmarks.get(command)
    if row is None:
        return None
    fields = {"batchSize", "endToEndMs", "evidenceRef", "contractHash"}
    if workload_hash is not None:
        fields |= {"workloadHash", "measurementKind"}
    require(isinstance(row, dict) and set(row) == fields,
            "AUTO_DISCOVERY_EXACT_BENCHMARK_FIELDS_REQUIRED:" + command)
    if workload_hash is not None:
        require(row["workloadHash"] == workload_hash
                and row["measurementKind"] == "NATIVE_END_TO_END",
                "AUTO_DISCOVERY_V2_COMPARABLE_NATIVE_END_TO_END_EVIDENCE_REQUIRED")
    require(type(row["batchSize"]) is int and row["batchSize"] == count,
            "AUTO_DISCOVERY_BENCHMARK_WORKLOAD_MISMATCH:" + command)
    require(type(row["endToEndMs"]) is int and 1 <= row["endToEndMs"] <= 10_000_000,
            "AUTO_DISCOVERY_END_TO_END_MEASURED_MS_REQUIRED:" + command)
    require(isinstance(row["evidenceRef"], str) and len(row["evidenceRef"].strip()) >= 8,
            "AUTO_DISCOVERY_BENCHMARK_PROVENANCE_REQUIRED:" + command)
    require(isinstance(row["contractHash"], str)
            and row["contractHash"] == router.contract_hash(command),
            "AUTO_DISCOVERY_BENCHMARK_COMMAND_CONTRACT_DRIFT:" + command)
    return {"estimatedCostMs": row["endToEndMs"],
            "costEvidenceRef": row["evidenceRef"]}


def _workflow(command, params, name):
    return {"operations": [{
        "id": name, "command": command, "params": immutable(params),
        "after": []
    }]}


def discover_native_execution_plan(router, intent, planner_python=None):
    """Discover feasible native strategies from catalog and choose when costed.

    Input schema apa-native-auto/1: request, existing, targets, benchmarks.
    Existing/target rows follow DynamicCommands.plan_reuse_existing verified
    structural family contracts. Targets may include *fully source-verified*
    nativeCreateData; no API defaults are assumed to be correct for BIM.

    Return either chosen APA_NATIVE_TASK_PREVIEW_V1 (no execution permission)
    or a shortlist requiring real, comparable benchmarks. Never modify PLN.
    """
    require(isinstance(intent, dict) and set(intent) == {
        "schemaVersion", "request", "existing", "targets", "benchmarks"
    } and intent.get("schemaVersion") in {"apa-native-auto/1", "apa-native-auto/2"},
            "AUTO_DISCOVERY_EXACT_INTENT_SCHEMA_REQUIRED")
    require(isinstance(intent["request"], str) and intent["request"].strip(),
            "AUTO_DISCOVERY_NONEMPTY_USER_TASK_REQUIRED")
    require(isinstance(intent["benchmarks"], dict),
            "AUTO_DISCOVERY_BENCHMARK_RECORDS_OBJECT_REQUIRED")
    existing = immutable(intent["existing"])
    targets = immutable(intent["targets"])
    v2 = intent["schemaVersion"] == "apa-native-auto/2"
    if v2:
        _v2_sources(targets)
        require(all(t.get("operation", "CREATE") in {"CREATE", "MODIFY"} for t in targets),
                "AUTO_DISCOVERY_V2_UNSUPPORTED_OPERATION")
    else:
        require(all(t.get("type") in {"Column", "Beam", "Object"}
                    for t in [*existing, *targets]),
                "AUTO_DISCOVERY_NEW_ELEMENT_TYPES_REQUIRE_V2_SOURCE_QUALIFICATION")
    modifying = v2 and targets[0].get("operation", "CREATE") == "MODIFY"

    # Uses already-tested source/anchor/family verification, detects duplicate
    # target anchors and never invents or writes unmatched elements.
    require(hasattr(router, "plan_reuse_existing"),
            "AUTO_DISCOVERY_REQUIRES_INSTALLED_COPY_FIRST_ROUTER")
    copy_plan = router.plan_reuse_existing(existing, targets)
    qualified, ineligible, catalog_count = _catalog_find(router)
    strategies = []
    rejected = []

    def accept(id_, command, params, count):
        # Reuse APA's typed command validation, reviewed-effect policy and BIM
        # graph compiler. Never write a new native command validator here.
        graph = _workflow(command, params, id_)
        try:
            router.prepare_workflow(graph)
        except (ValueError, KeyError, TypeError, RuntimeError, ValidationError, SchemaError) as exc:
            rejected.append({"id": id_, "command": command,
                             "reason": "BIM_GRAPH_OR_NATIVE_SCHEMA_BLOCKED",
                             "detail": type(exc).__name__ + ":" + str(exc)[:400]})
            return
        strategies.append({
            "id": id_, "command": command,
            "graph": graph,
            "nativeCallCount": 1, "itemCount": count,
        })

    # Source-qualified copy-first is complete only if all targets match a
    # verified prototype or are already fulfilled in the live model.
    pending = copy_plan["unmatchedTargetsPendingPrototype"]
    groups = copy_plan["copyGroups"]
    if not modifying and "MoveElements" in qualified and not pending and groups:
        rows = []
        for group in groups:
            for vector in group["displacements"]:
                rows.append({
                    "elementId": {"guid": group["prototypeGuid"]},
                    "moveVector": immutable(vector), "copy": True,
                })
        require(len(rows) == copy_plan["newCopyCount"]
                and 0 < len(rows) <= 200,
                "AUTO_DISCOVERY_NATIVE_COPY_BATCH_EXCEEDS_APPROVED_CAPACITY")
        accept(COPY_NAME, "MoveElements",
               {"elementsWithMoveVectors": rows}, len(rows))
    elif groups or pending:
        rejected.append({"id": COPY_NAME, "command": "MoveElements",
                         "reason": "UNMATCHED_FAMILY_OR_NO_APPROVED_COPY_POLICY"
                                   if pending or "MoveElements" not in qualified
                                   else "NO_COPIES_NEEDED"})

    present = set()
    for source in existing:
        require(source.get("nativeReadbackVerified") is True,
                "AUTO_DISCOVERY_SOURCE_UNVERIFIED")
        present.add(_presence_key(source))
    if modifying:
        command, field, rows = _v2_modify_targets(targets, existing)
        if command in qualified:
            accept("native_" + command.lower() + "_batch", command, {field: rows}, len(rows))
        else:
            rejected.append({"command": command, "reason": "NO_REVIEWED_OPERATION_POLICY"})
    try:
        missing_create = None if modifying else _native_create_targets(targets, present, v2)
    except (ValueError, KeyError, TypeError, IndexError, ImportError) as exc:
        missing_create = None
        rejected.append({"id": "native_create_batch", "reason": str(exc)[:400]})
    if missing_create:
        create_command, create_rows = missing_create
        if create_command in qualified:
            kind = next(k for k, spec in CREATE_SLOTS.items() if spec[0] == create_command)
            create_name = {"Column": CREATE_NAME, "Beam": BEAM_CREATE_NAME}.get(
                kind, "native_create_" + kind.lower() + "s_batch")
            data_field = CREATE_SLOTS[kind][1]
            if kind in {"Window", "Door"}:
                _v2_host_batch(targets)
            accept(create_name, create_command,
                   {data_field: create_rows}, len(create_rows))
        else:
            rejected.append({
                "id": create_command, "command": create_command,
                "reason": "CREATE_POLICY_NOT_REVIEWED_OR_RUNTIME_QUALIFIED",
            })
    elif not modifying:
        rejected.append({
            "id": "native_create_batch", "command": "CreateColumns/CreateBeams",
            "reason": "NO_COMPLETE_HOMOGENEOUS_SOURCE_QUALIFIED_NATIVE_DATA",
        })

    discovery = {
        "schema": "APA_CATALOG_AUTO_DISCOVERY_V1",
        "status": "CATALOG_SCANNED_AND_TYPED_NATIVE_CANDIDATES_VALIDATED",
        "catalogCommandCount": catalog_count,
        "recognizedRecipeCommands": sorted(CAPABILITY),
        "eligibleCommands": sorted(qualified),
        "ineligibleCommands": ineligible,
        "copyFirstStatus": copy_plan["status"],
        "pendingUnmatchedTargets": len(pending),
        "alreadyPresent": len(copy_plan["existingElementGuids"]),
        "qualifiedStrategies": len(strategies),
        "rejectedStrategies": rejected,
        "newNativeModelWrites": 0,
        "automaticNativeExecution": False,
        "nativeWritePermission": False,
        "sourceQualification": "CALLER_SUPPLIED_NATIVE_READBACK_AND_DOCUMENT_REF_NOT_REVALIDATED_LIVE",
        "adapterVersion": 2 if v2 else 1,
        "benchmarkWorkloadHash": source_data_hash({"existing": existing, "targets": targets}) if v2 else None,
        "verificationRequirements": ["EXACT_PROJECT_MODEL_GUID_AND_SAVED_FILE_HASH",
            "FRESH_OPERATION_SPECIFIC_BASELINE_AND_HOSTS", "COMPLETE_GUID_INVENTORY",
            "RETAINED_NATIVE_BREP_AND_ATTRIBUTES", "INDEPENDENT_CREATED_OR_MODIFIED_GUID_READBACK",
            "SOURCE_STORY_MATERIAL_FAVORITE_LIBRARY_AND_GEOMETRY_READBACK"],
    }
    if not strategies:
        # Zero-work outcome is valid ONLY when every requested target is
        # demonstrably already present; missing creation data must not be
        # interpreted as completed construction.
        if v2 and (modifying or pending or groups):
            return {"schema": "APA_AUTO_NATIVE_TASK_V1",
                    "status": "BLOCKED_NO_COMPLETE_QUALIFIED_STRATEGY",
                    "discovery": discovery, "selectedNativeTaskPreview": None,
                    "nativeWritePermission": False, "automaticNativeExecution": False}
        require(not modifying and not pending and not groups
                and len(copy_plan["existingElementGuids"]) == len(targets),
                "AUTO_DISCOVERY_NO_COMPLETE_QUALIFIED_STRATEGY")
        return {
            "schema": "APA_AUTO_NATIVE_TASK_V1",
            "status": "NO_CHANGES_REQUIRED",
            "discovery": discovery,
            "selectedNativeTaskPreview": None,
            "nativeWritePermission": False,
        }

    measured = []
    for strategy in strategies:
        candidate = dict(strategy)
        price = _calibrate(router, strategy["command"],
                           strategy["itemCount"], intent["benchmarks"],
                           source_data_hash({"existing": existing, "targets": targets}) if v2 else None)
        if price is not None:
            candidate.update(price)
        measured.append(candidate)

    if len(strategies) == 1:
        import archicad_project_accelerator as APA
        single = measured[0]
        child = APA.prepare_native_task(router, {
            "schemaVersion": "apa-native-task/1", "request": intent["request"],
            "graph": single["graph"],
        })
        return {
            "schema": "APA_AUTO_NATIVE_TASK_V1",
            "status": "ONE_SOURCE_QUALIFIED_STRATEGY_PREPARED",
            "selectedStrategyId": single["id"],
            "selectedNativeTaskPreview": child,
            "selectionMethod": "SOLE_FEASIBLE_TYPED_OPTION_NOT_COST_OPTIMIZATION",
            "calibrationStatus": "MEASURED" if "estimatedCostMs" in single else "UNCALIBRATED",
            "discovery": discovery,
            "nativeWritePermission": False,
            "automaticNativeExecution": False,
        }

    missing = [row["command"] for row in measured if "estimatedCostMs" not in row]
    if missing:
        return {
            "schema": "APA_AUTO_NATIVE_TASK_V1",
            "status": "COST_COMPARISON_BLOCKED_UNCALIBRATED_ALTERNATIVES",
            "selectedNativeTaskPreview": None,
            "unmeasuredCommands": sorted(set(missing)),
            "candidateSummaries": [
                {"id": row["id"], "command": row["command"],
                 "nativeCallCount": row["nativeCallCount"],
                 "itemCount": row["itemCount"],
                 "estimatedCostMs": row.get("estimatedCostMs"),
                 "costEvidenceRef": row.get("costEvidenceRef")}
                for row in measured
            ],
            "discovery": discovery,
            "nativeWritePermission": False,
            "automaticNativeExecution": False,
        }

    winner = prepare_optimized_native_task(router, intent["request"], [
        {key: row[key] for key in (
            "id", "graph", "nativeCallCount", "estimatedCostMs", "costEvidenceRef"
        )} for row in measured
    ], planner_python)
    require(winner["nativeWritePermission"] is False
            and winner["automaticNativeExecution"] is False,
            "AUTO_DISCOVERY_SOLVER_GRANTED_NATIVE_WRITE")
    return {
        "schema": "APA_AUTO_NATIVE_TASK_V1",
        "status": "COST_OPTIMAL_SOURCE_QUALIFIED_STRATEGY_PREPARED",
        "selectedStrategyId": winner["selectedStrategyId"],
        "selectedNativeTaskPreview": winner["selectedNativeTaskPreview"],
        "selectionMethod": "UNIFIED_PLANNING_FAST_DOWNWARD_VERIFIED_COSTED_ALTERNATIVES",
        "estimatedCostMs": winner["estimatedCostMs"],
        "costEvidenceRef": winner["costEvidenceRef"],
        "discovery": discovery,
        "compared": winner["compared"],
        "nativeWritePermission": False,
        "automaticNativeExecution": False,
    }


def main():
    """Offline preview CLI over the SAME router, policies, graph and APA API."""
    import argparse
    from pathlib import Path
    import archicad_project_accelerator as APA
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--intent", required=True)
    parser.add_argument("--schema", required=True,
                        help="Existing pinned provider schema; never queries Archicad")
    parser.add_argument("--reviewed-policies", required=True,
                        help="JSON command -> existing reviewed kind/impact/evidence records")
    parser.add_argument("--planner-python")
    args = parser.parse_args()
    router = APA.native_command_router(Path(args.schema))
    policies = json.loads(Path(args.reviewed_policies).read_text(encoding="utf-8-sig"))
    for name, policy in policies.items():
        require(policy["evidence"]["sha256"] == router.contract_hash(name),
                "AUTO_DISCOVERY_REVIEWED_POLICY_CONTRACT_DRIFT:" + name)
        router.review_policy(name, policy["kind"], policy["impact"], policy["evidence"])
    result = discover_native_execution_plan(router,
        json.loads(Path(args.intent).read_text(encoding="utf-8-sig")), args.planner_python)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 2 if result["status"].startswith("BLOCKED_") else 0


if __name__ == "__main__":
    raise SystemExit(main())
