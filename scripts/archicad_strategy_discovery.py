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

V1 supports repetitive structural Columns with available complete native
CreateColumns data, and reuse of source-verified Column/Beam/Object families
via MoveElements(copy=true). Extensibility comes from approved typed recipe
adapters; scanning the full catalog does NOT imply every command can construct
these particular targets.
"""
from __future__ import annotations

import copy
import json
import math

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
        if router.operation_kind(command) != "CREATE":
            ineligible.append({"command": command, "reason": "NO_REVIEWED_CREATE_POLICY"})
            continue
        if contract.get("availability") in {
                "NOT_EXPOSED", "SOURCE_CONTRACT_NOT_RUNTIME_PROBED",
                "LOCAL_DEPENDENCIES_NOT_CHECKED", "UNAVAILABLE", "NOT_TESTED"}:
            ineligible.append({"command": command,
                               "reason": "NOT_RUNTIME_QUALIFIED_FOR_LIVE"})
            continue
        discovered.append(command)
    return discovered, ineligible, len(commands)


def _native_create_targets(targets, present):
    """Find complete typed create families WITHOUT inventing profile or stories.

    V1 prepares exactly one homogeneous family per create alternative.
    Beams require start and end endpoints, nonzero span, exact source
    elevation and first-story origin 0. Higher story beams require a separate
    story-level qualifier and are therefore excluded.
    """
    rows = []
    created_types = set()
    for target in targets:
        f = (target["type"], target["familySignature"], target["storyIndex"])
        a = target["anchor"]
        key = (f, *(round(a[k], 7) for k in ("x", "y", "z")))
        if key in present:
            continue
        kind = target["type"]
        if kind not in {"Column", "Beam"}:
            return None
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
    return ("CreateColumns", rows) if kind == "Column" else ("CreateBeams", rows)


def _calibrate(router, command, count, benchmarks):
    row = benchmarks.get(command)
    if row is None:
        return None
    require(isinstance(row, dict) and set(row) == {
                "batchSize", "endToEndMs", "evidenceRef", "contractHash"},
            "AUTO_DISCOVERY_EXACT_BENCHMARK_FIELDS_REQUIRED:" + command)
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
    } and intent.get("schemaVersion") == "apa-native-auto/1",
            "AUTO_DISCOVERY_EXACT_INTENT_SCHEMA_REQUIRED")
    require(isinstance(intent["request"], str) and intent["request"].strip(),
            "AUTO_DISCOVERY_NONEMPTY_USER_TASK_REQUIRED")
    require(isinstance(intent["benchmarks"], dict),
            "AUTO_DISCOVERY_BENCHMARK_RECORDS_OBJECT_REQUIRED")
    existing = immutable(intent["existing"])
    targets = immutable(intent["targets"])

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
        except (ValueError, KeyError, TypeError, RuntimeError) as exc:
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
    if "MoveElements" in qualified and not pending and groups:
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
        a = source["anchor"]
        present.add(((source["type"], source["familySignature"],
                      source["storyIndex"]),
                     *(round(a[k], 7) for k in ("x", "y", "z"))))
    missing_create = _native_create_targets(targets, present)
    if missing_create:
        create_command, create_rows = missing_create
        if create_command in qualified:
            create_name = CREATE_NAME if create_command == "CreateColumns" else BEAM_CREATE_NAME
            data_field = "columnsData" if create_command == "CreateColumns" else "beamsData"
            accept(create_name, create_command,
                   {data_field: create_rows}, len(create_rows))
        else:
            rejected.append({
                "id": create_command, "command": create_command,
                "reason": "CREATE_POLICY_NOT_REVIEWED_OR_RUNTIME_QUALIFIED",
            })
    else:
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
    }
    if not strategies:
        # Zero-work outcome is valid ONLY when every requested target is
        # demonstrably already present; missing creation data must not be
        # interpreted as completed construction.
        require(not pending and not groups
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
                           strategy["itemCount"], intent["benchmarks"])
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
