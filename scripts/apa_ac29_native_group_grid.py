"""AC29 native-group grid recipe -> EXISTING APA group-first BIM Graph.

Pure read-only preparation, no new native commands, no model/PLN mutations,
no automatic authorization or execution. The actual command remains
AddOn.TapirCommand.CloneNativeGroupV1 in DynamicCommands -> SceneWriter.

The source must be exactly a previously readback-verified native group of
two independent, single-segment columns. Generalized object/group semantics
require separate verifier acceptance. Positions are in model meters.
"""
from __future__ import annotations

import copy
import math

import apa_ac29_group_strategy as GROUP

SCHEMA = "APA_AC29_NATIVE_GROUP_GRID_V1"
INTENT = "apa-native-group-auto/1"
AXES = ("dx", "dy", "dz")
GRID_KEYS = frozenset({"schema", "columns", "rows", "stepX",
                       "stepY", "startDx", "startDy"})
MAX_PLACEMENTS = 32
MAX_ROOTS = 200
MAX_HORIZONTAL_DISTANCE = 10000.0


def require(ok, message):
    if not ok:
        raise ValueError(message)


def number(value):
    return type(value) in (float, int) and math.isfinite(value)


def grid_offsets(grid):
    """Expand an explicitly dimensioned rectangular grid to clone translations.

    startDx/startDy locate the first NEW group relative to the old source.
    In particular, the original group at offset (0,0,0) is NEVER cloned.
    A row-major, unique, hash-stable list is passed unchanged to the
    original group-first selection and native schema. No dimension guessed.
    """
    require(isinstance(grid, dict) and set(grid) == GRID_KEYS
            and grid.get("schema") == SCHEMA,
            "GRID_EXACT_TYPED_RECIPE_REQUIRED")
    columns, rows = grid["columns"], grid["rows"]
    require(type(columns) is int and type(rows) is int
            and 1 <= columns <= MAX_PLACEMENTS
            and 1 <= rows <= MAX_PLACEMENTS
            and columns * rows <= MAX_PLACEMENTS,
            "GRID_NATIVE_MAX_32_PLACEMENTS")
    for name in ("stepX", "stepY", "startDx", "startDy"):
        require(number(grid[name]) and abs(grid[name]) <= MAX_HORIZONTAL_DISTANCE,
                "GRID_FINITE_BOUNDED_METERS_REQUIRED:" + name)
    require(columns == 1 or round(grid["stepX"], 6) != 0,
            "GRID_REPEATED_COLUMNS_REQUIRE_NONZERO_STEP_X")
    require(rows == 1 or round(grid["stepY"], 6) != 0,
            "GRID_REPEATED_ROWS_REQUIRE_NONZERO_STEP_Y")
    shifts, unique = [], set()
    for iy in range(rows):
        for ix in range(columns):
            dx = round(grid["startDx"] + ix * grid["stepX"], 6)
            dy = round(grid["startDy"] + iy * grid["stepY"], 6)
            require(math.isfinite(dx) and math.isfinite(dy)
                    and abs(dx) <= MAX_HORIZONTAL_DISTANCE
                    and abs(dy) <= MAX_HORIZONTAL_DISTANCE
                    and (dx != 0 or dy != 0),
                    "GRID_OUTSIDE_BOUNDS_OR_COPIES_ORIGINAL_GROUP")
            xy = (dx, dy)
            require(xy not in unique, "GRID_DUPLICATE_NATIVE_PLACEMENT")
            unique.add(xy)
            shifts.append({"dx": dx, "dy": dy, "dz": 0})
    return shifts


def build_group_grid_intent(existing, assembly, grid, request):
    """Produce the *existing* APA group-intent type and exact typed targets.

    This function cannot assert native group presence by itself: the source
    group member IDs and all member signatures MUST arrive from trusted
    native readback. Existing APA route() re-checks group provenance, story,
    typed family identity, full target coverage and duplicate targets.
    Full BREP collision check occurs in the independent SceneWriter verifier,
    not in this pure grid-preview adapter.
    """
    require(isinstance(existing, list) and isinstance(assembly, dict)
            and isinstance(request, str) and request.strip(),
            "GRID_EXPLICIT_VERIFIED_SOURCE_AND_REQUEST_REQUIRED")
    require(assembly.get("existingGroupGuid")
            and assembly.get("groupReadbackVerified") is True
            and assembly.get("dependenciesVerified") is True
            and assembly.get("sameStory") is True
            and isinstance(assembly.get("memberGuids"), list)
            and len(assembly["memberGuids"]) == 2,
            "GRID_EXACT_TWO_VERIFIED_NATIVE_COLUMN_MEMBERS_REQUIRED")
    members = [value.lower() for value in assembly["memberGuids"]
               if isinstance(value, str)]
    require(len(members) == 2 and len(set(members)) == 2,
            "GRID_SOURCE_GROUP_MEMBER_GUID_DUPLICATION")
    sources = []
    for row in existing:
        if isinstance(row, dict) and isinstance(row.get("guid"), str):
            if row["guid"].lower() in members:
                GROUP.key(row)
                require(row.get("nativeReadbackVerified") is True
                        and row["type"] == "Column",
                        "GRID_SOURCE_GROUP_MUST_BE_NATIVE_VERIFIED_COLUMNS")
                sources.append(row)
    require(len(sources) == 2 and
            {x["guid"].lower() for x in sources} == set(members),
            "GRID_SOURCE_GROUP_COLUMN_IDENTITIES_INCOMPLETE")
    require(sources[0]["storyIndex"] == sources[1]["storyIndex"],
            "GRID_SOURCE_GROUP_STORY_DRIFT")
    translations = grid_offsets(grid)
    require(len(sources) * len(translations) <= MAX_ROOTS,
            "GRID_NATIVE_200_ROOT_CAPACITY_EXCEEDED")
    source_ref = assembly.get("sourceRef")
    require(isinstance(source_ref, str) and len(source_ref) >= 8,
            "GRID_SOURCE_PROVENANCE_REQUIRED")
    # Explicit row-major groups: each existing member is replicated once
    # into each placement, never inferred as an independent new family.
    targets = []
    for shift in translations:
        for member in sources:
            old = member["anchor"]
            point = {axis: round(old[axis] + shift["d" + axis], 6)
                     for axis in ("x", "y", "z")}
            require(all(GROUP.finite(v) for v in point.values()),
                    "GRID_TRANSLATED_NATIVE_ANCHOR_OUTSIDE_BOUNDS")
            targets.append({
                "type": member["type"],
                "familySignature": member["familySignature"],
                "storyIndex": member["storyIndex"],
                "anchor": point,
                "sourceRef": source_ref
            })
    candidate = copy.deepcopy(assembly)
    candidate["placements"] = translations
    # Validate against existing GROUP.route instead of designing another
    # selector or trusting that the generated array is a native write permit.
    selected = GROUP.route(existing, targets, [candidate])
    require(selected.get("coveredTargetIndices") == list(range(len(targets)))
            and selected.get("nativeCallsIfAuthorized") == 1,
            "GRID_EXISTING_APA_GROUP_FIRST_SELECTOR_NOT_EXACTLY_ONE_CLONE")
    return {
        "schemaVersion": INTENT,
        "request": request,
        "existing": copy.deepcopy(existing),
        "targets": targets,
        "assemblyGroups": [candidate]
    }


def prepare_group_grid_preview(router, existing, assembly, grid, request):
    """Compile grid using ORIGINAL APA dynamic router and BIM Graph only."""
    from archicad_project_accelerator import prepare_auto_optimized_native_task
    intent = build_group_grid_intent(existing, assembly, grid, request)
    chosen = prepare_auto_optimized_native_task(router, intent)
    require(chosen.get("nativeWritePermission") is False
            and chosen.get("automaticNativeExecution") is False
            and chosen.get("nativeModelWrites") == 0
            and chosen.get("groupedTargetCount") == len(intent["targets"])
            and chosen.get("individuallyRoutedTargetCount") == 0
            and chosen.get("groupNativeCallsIfAuthorized") == 1
            and chosen.get("requiredRuntimeCommands") ==
            ["AddOn.TapirCommand.CloneNativeGroupV1"],
            "GRID_MUST_REUSE_SINGLE_EXISTING_APA_SCENEWRITER_ROUTE")
    return {"intent": intent, "preview": chosen,
            "schema": SCHEMA, "modelWrites": 0,
            "executionPermission": False,
            "requiresNativeBREPCollisionVerifier": True}
