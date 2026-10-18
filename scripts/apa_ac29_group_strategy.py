"""AC29 verified native assembly precedence for existing APA strategy selection.

This module is a pure planner. It reuses the installed DynamicCommands,
BIM Graph and SceneWriter; it neither creates an Archicad command nor writes
to a PLN. An assembly is selected automatically only when every source member
maps to an exact source-qualified target in every translated placement.
"""
from __future__ import annotations

from collections import defaultdict
import math
import re

from apa_ac29_assembly_operations import plan_assemblies

GUID = re.compile(r"^[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}$")
COPYABLE = frozenset({"Column", "Beam", "Object"})
CREATE = {"Column": ("CreateColumns", "columnsData"),
          "Beam": ("CreateBeams", "beamsData")}
SCHEMA = "APA_AC29_GROUP_FIRST_STRATEGY_V1"


def need(condition, reason):
    if not condition:
        raise ValueError(reason)


def finite(value):
    return type(value) in (int, float) and math.isfinite(value) and abs(value) <= 100000


def key(row):
    need(isinstance(row, dict) and row.get("type") in COPYABLE
         and isinstance(row.get("familySignature"), str)
         and len(row["familySignature"]) >= 16
         and type(row.get("storyIndex")) is int
         and isinstance(row.get("anchor"), dict)
         and set(row["anchor"]) == {"x", "y", "z"}
         and all(finite(row["anchor"][k]) for k in ("x", "y", "z")),
         "GROUP_SELECTOR_EXACT_BIM_IDENTITY_AND_ANCHOR_REQUIRED")
    return (row["type"], row["familySignature"], row["storyIndex"],
            *(round(row["anchor"][k], 6) for k in ("x", "y", "z")))


def route(existing, targets, assembly_groups=None):
    """Choose whole groups before the ordinary per-element copy planner.

    Absence of an assembly is NOT evidence that existing elements form a
    group. Explicit assemblies require verified source members, home story,
    native group membership (or verified ungrouped members), no dependencies
    outside the assembly, and exact target anchors/family signatures.
    Fail closed instead of silently re-copying member objects individually.
    """
    if assembly_groups is None:
        return {"schema": SCHEMA, "assemblies": [], "coveredTargetIndices": [],
                "nativeCallsIfAuthorized": 0, "nativeModelWrites": 0}
    need(isinstance(assembly_groups, list), "GROUP_SELECTOR_LIST_REQUIRED")
    need(isinstance(existing, list) and isinstance(targets, list),
         "GROUP_SELECTOR_BIM_ROWS_REQUIRED")
    basic = plan_assemblies(existing, assembly_groups)
    indexed = {}
    for row in existing:
        guid = row.get("guid") if isinstance(row, dict) else None
        if not isinstance(guid, str):
            continue
        need(bool(GUID.fullmatch(guid)), "GROUP_SELECTOR_INVALID_EXISTING_GUID")
        need(guid.lower() not in indexed, "GROUP_SELECTOR_EXISTING_GUID_DUPLICATED")
        indexed[guid.lower()] = row

    # The exact typed target identity uniquely resolves each placement. The
    # source already existing at the original anchor is never a new copy.
    target_ids = defaultdict(list)
    for index, target in enumerate(targets):
        if target.get("type") in COPYABLE:
            target_ids[key(target)].append(index)
    for group in target_ids.values():
        need(len(group) == 1, "GROUP_SELECTOR_DUPLICATED_TARGET_IDENTITY")

    selected, covered, involved_sources = [], set(), set()
    for index, (raw, planned) in enumerate(zip(assembly_groups, basic)):
        members = raw["memberGuids"]
        need(2 <= len(members) <= 128, "GROUP_SELECTOR_GROUP_MEMBERS_OUT_OF_BOUNDS")
        need(len(planned["relativePlacements"]) <= 32 and
             len(members) * len(planned["relativePlacements"]) <= 200,
             "GROUP_SELECTOR_NATIVE_CLONE_CAPACITY_EXCEEDED")
        need(raw.get("dependenciesVerified") is True,
             "GROUP_SELECTOR_DEPENDENCIES_NOT_INDEPENDENTLY_VERIFIED")
        old_group = raw.get("existingGroupGuid")
        if old_group:
            need(bool(GUID.fullmatch(old_group)) and
                 raw.get("groupReadbackVerified") is True,
                 "GROUP_SELECTOR_EXISTING_NATIVE_GROUP_NOT_READBACK_VERIFIED")
        else:
            need(raw.get("ungroupedReadbackVerified") is True,
                 "GROUP_SELECTOR_UNGROUPED_SOURCE_MEMBERS_NOT_PROVEN")
        source_rows = []
        for guid in members:
            need(isinstance(guid, str) and GUID.fullmatch(guid),
                 "GROUP_SELECTOR_INVALID_MEMBER_GUID")
            lower = guid.lower()
            need(lower in indexed and lower not in involved_sources,
                 "GROUP_SELECTOR_SOURCE_MISSING_OR_REUSED_ACROSS_GROUPS")
            source = indexed[lower]
            need(source.get("nativeReadbackVerified") is True
                 and source.get("type") in COPYABLE,
                 "GROUP_SELECTOR_SOURCE_MEMBER_NOT_SAFE_TO_COPY")
            key(source)
            involved_sources.add(lower)
            source_rows.append(source)

        hits = []
        for position in planned["relativePlacements"]:
            delta = dict(zip(("x", "y", "z"), position))
            for source in source_rows:
                source_key = key(source)
                translated = (source_key[0], source_key[1], source_key[2],
                              *(round(source_key[3+i] + delta[axis], 6)
                                for i, axis in enumerate(("x", "y", "z"))))
                matched = target_ids.get(translated, [])
                need(len(matched) == 1, "GROUP_SELECTOR_TARGET_ASSEMBLY_NOT_EXACT")
                hit = matched[0]
                need(hit not in covered and hit not in hits,
                     "GROUP_SELECTOR_TARGET_ALREADY_COVERED")
                need(targets[hit].get("sourceRef") == raw["sourceRef"],
                     "GROUP_SELECTOR_TARGET_PROVENANCE_DIFFERS_FROM_ASSEMBLY")
                hits.append(hit)

        covered.update(hits)
        selected.append({
            **planned,
            "status": "VERIFIED_GROUP_FIRST_PREVIEW_SCOPE_AND_RUNTIME_REQUIRED",
            "strategy": "NATIVE_GROUP_REPLICATION" if old_group else
                        "NATIVE_GROUP_THEN_REPLICATION",
            "routeCommands": (["CloneNativeGroupV1"] if old_group else
                              ["CreateNativeGroupV1", "CloneNativeGroupV1"]),
            "coveredTargetIndices": sorted(hits),
            "assemblyIndex": index,
            "groupReadbackVerified": bool(old_group),
            "nativeCallsIfAuthorized": 1 if old_group else 2,
            "nativeModelWrites": 0
        })
    return {
        "schema": SCHEMA,
        "assemblies": selected,
        "coveredTargetIndices": sorted(covered),
        "nativeCallsIfAuthorized": sum(s["nativeCallsIfAuthorized"] for s in selected),
        "nativeModelWrites": 0
    }


def command_name(router, bare):
    """Resolve existing command name, never create a provider or schema."""
    commands = getattr(router, "catalog", {}).get("commands", {})
    direct = bare if bare in commands else "AddOn.TapirCommand." + bare
    need(direct in commands, "GROUP_SELECTOR_NATIVE_COMMAND_NOT_IN_APA_CATALOG:" + bare)
    need(router.operation_kind(direct) == "CREATE",
         "GROUP_SELECTOR_NATIVE_CREATE_POLICY_NOT_REVIEWED:" + direct)
    return direct


def workflow_for_selected(router, request, existing, targets, chosen):
    """Produce one existing BIM Graph, never an alternate executor.

    Strategy precedence: grouped assembly -> remaining prototype copies in
    one MoveElements batch -> remaining typed create operations if complete.
    Every graph command is checked by the original schema/graph compiler.
    All writes still require per-step local SceneWriter authorization.
    """
    need(isinstance(request, str) and request.strip(),
         "GROUP_SELECTOR_REQUEST_REQUIRED")
    need(isinstance(chosen, dict) and chosen.get("schema") == SCHEMA,
         "GROUP_SELECTOR_INVALID_SELECTION")
    covered = set(chosen["coveredTargetIndices"])
    need(all(type(i) is int and 0 <= i < len(targets) for i in covered),
         "GROUP_SELECTOR_COVERED_TARGET_OUTSIDE_INPUT")
    operations = []
    for i, assembly in enumerate(chosen["assemblies"]):
        source_ref = assembly["sourceRef"]
        translations = [{"dx": x, "dy": y, "dz": z}
                        for x, y, z in assembly["relativePlacements"]]
        if assembly["groupGuid"]:
            ref = {"guid": assembly["groupGuid"]}
        else:
            create_id = "assembly_" + str(i) + "_group"
            operations.append({
                "id": create_id,
                "command": command_name(router, "CreateNativeGroupV1"),
                "params": {"memberIds": [{"guid": v} for v in assembly["memberGuids"]],
                           "sourceRef": source_ref},
                "after": []
            })
            ref = {"$result": {"step": create_id, "pointer": "/groupId"}}
        operations.append({
            "id": "assembly_" + str(i) + "_clone",
            "command": command_name(router, "CloneNativeGroupV1"),
            "params": {"groupId": ref, "sourceRef": source_ref,
                       "translations": translations},
            "after": []
        })

    remainder = [row for i, row in enumerate(targets) if i not in covered]
    # This is the existing, proven copy-first router, not a new copy strategy.
    from archicad_dynamic_commands import DynamicCommands
    copy_targets = [x for x in remainder if x.get("type") in COPYABLE]
    copy_sources = [x for x in existing if x.get("type") in COPYABLE]
    plan = DynamicCommands.plan_reuse_existing(copy_sources, copy_targets) if copy_targets else {
        "copyGroups": [], "unmatchedTargetsPendingPrototype": [],
        "existingElementGuids": []}
    if plan["copyGroups"]:
        rows = [
            {"elementId": {"guid": group["prototypeGuid"]},
             "moveVector": shift, "copy": True}
            for group in plan["copyGroups"] for shift in group["displacements"]
        ]
        need(0 < len(rows) <= 200, "GROUP_SELECTOR_ELEMENT_BATCH_CAPACITY")
        operations.append({
            "id": "ungrouped_prototype_copy",
            "command": command_name(router, "MoveElements"),
            "params": {"elementsWithMoveVectors": rows},
            "after": []
        })
    pending = plan["unmatchedTargetsPendingPrototype"]
    missing = [*pending, *(x for x in remainder if x.get("type") not in COPYABLE)]
    by_command = defaultdict(list)
    for row in missing:
        kind = row.get("type")
        need(kind in CREATE and
             isinstance(row.get("nativeCreateData"), dict) and
             bool(row["nativeCreateData"]),
             "GROUP_SELECTOR_REMAINDER_REQUIRES_VERIFIED_NATIVE_CREATE_DATA")
        # Do not allow opaque unsupported command defaults or hosted elements.
        command, slot = CREATE[kind]
        by_command[(command, slot)].append(row["nativeCreateData"])
    for i, ((command, slot), entries) in enumerate(sorted(by_command.items())):
        operations.append({
            "id": "remaining_create_" + str(i),
            "command": command_name(router, command),
            "params": {slot: entries},
            "after": []
        })
    need(bool(operations), "GROUP_SELECTOR_NO_MODEL_ACTION_REQUIRED")
    # Dependency from new group creation to Clone is expressed by $result.
    # Existing APA handles result binding, serialization and per-step ledger.
    from archicad_project_accelerator import prepare_native_task
    prepared = prepare_native_task(router, {
        "schemaVersion": "apa-native-task/1",
        "request": request,
        "graph": {"operations": operations}
    })
    commands = [row["command"] for row in operations]
    all_registered = all(
        getattr(router, "registration", {}).get(command) is True
        for command in set(commands)
    )
    return {
        "schema": "APA_AUTO_NATIVE_TASK_V1",
        "adapterVersion": "AC29_GROUP_FIRST_V1",
        "status": ("ONE_SOURCE_QUALIFIED_STRATEGY_PREPARED" if all_registered
                   else "GROUP_WORKFLOW_REQUIRES_FRESH_RUNTIME_REGISTRATION"),
        "sourceStrategy": SCHEMA,
        "strategyOrder": [
            "VERIFIED_NATIVE_GROUPS", "EXISTING_BATCH_COPY",
            "EXISTING_TYPED_BATCH_CREATE"
        ],
        "selectedNativeTaskPreview": prepared if all_registered else None,
        "candidateNativeTaskPreview": prepared,
        "requiredRuntimeCommands": sorted(set(commands)),
        "unprobedCommands": sorted(c for c in set(commands)
                                  if getattr(router, "registration", {}).get(c) is not True),
        "groupedSourceMembers": sum(a["memberCount"] for a in chosen["assemblies"]),
        "groupedTargetCount": len(covered),
        "individuallyRoutedTargetCount": len(remainder),
        "groupNativeCallsIfAuthorized": chosen["nativeCallsIfAuthorized"],
        "nativeCallCountIfAuthorized": len(operations),
        "nativeWritePermission": False,
        "automaticNativeExecution": False,
        "nativeModelWrites": 0,
        "executor": "EXISTING_APA_SCENEWRITER_ONLY"
    }
