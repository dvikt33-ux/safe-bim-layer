"""Source-qualified mass requests -> existing APA group/copy discovery.

No router, executor, dimensions inferred from prose, installation or write
permission. Placement coordinates are explicit SI model meters. Native
execution remains run_auto_optimized_native_task with code-owned scopes.
"""
from __future__ import annotations

import copy
import math
import re

import apa_ac29_group_strategy as GROUP

SCHEMA = "apa-native-mass-request/1"


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def vector(value):
    need(isinstance(value, dict) and set(value) == {"dx", "dy", "dz"} and
         all(type(n) in (int, float) and math.isfinite(n) and abs(n) <= 10000
             for n in value.values()), "MASS_EXPLICIT_FINITE_METERS_REQUIRED")
    return {key: round(value[key], 6) for key in ("dx", "dy", "dz")}


def recognize_request(request):
    """Bounded intent hints only; prose cannot supply coordinates or consent."""
    need(isinstance(request, str) and bool(request.strip()), "MASS_REQUEST_REQUIRED")
    text = request.casefold()
    need(not re.search(r"булев|boolean|\bunion\b|сплав|слить.*тел", text),
         "MASS_BOOLEAN_UNION_HAS_NO_VERIFIED_NATIVE_ADAPTER")
    flags = {
        "replicate": bool(re.search(r"копир|клонир|тираж|размнож|распредел|расстав|массив|copy|clone|multiply|distribut|array|replicat", text)),
        "groups": bool(re.search(r"групп|композиц|group|assembl", text)),
        "grid": bool(re.search(r"сетк|grid|массив|array", text)),
        "axes": bool(re.search(r"осям|оси|осей|\baxes\b|\baxis\b", text)),
    }
    need(flags["replicate"], "MASS_REQUEST_INTENT_NOT_SUPPORTED_REQUIRES_EXPLICIT_COPY_TASK")
    return flags


def axis_intersections(layout):
    """Explicit orthogonal axes only; preserve labels and caller's pair order."""
    fields={"mode", "sourceRef", "X", "Y", "reference", "requiresNativeAxisObjects"}
    need(set(layout) in (fields, fields | {"selectedIntersections"}) and
         isinstance(layout["sourceRef"], str) and len(layout["sourceRef"]) >= 8 and
         layout["requiresNativeAxisObjects"] is False,
         "MASS_AXIS_PLACEMENTS_ONLY_NATIVE_GRID_CREATION_NEEDS_OWN_VERIFIER")
    reference=layout["reference"]
    need(isinstance(reference,dict) and set(reference)=={"x","y","z"} and
         all(type(n) in (int,float) and math.isfinite(n) for n in reference.values()),
         "MASS_AXIS_EXPLICIT_SOURCE_REFERENCE_REQUIRED")
    axes={}
    for name in ("X","Y"):
        rows=layout[name]
        need(isinstance(rows,list) and 1<=len(rows)<=32 and
             all(isinstance(r,dict) and set(r)=={"id","coordinate"} and
                 isinstance(r["id"],str) and bool(r["id"].strip()) and r["id"]==r["id"].strip() and
                 type(r["coordinate"]) in (int,float) and math.isfinite(r["coordinate"])
                 for r in rows) and len({r["id"] for r in rows})==len(rows) and
             len({round(r["coordinate"],6) for r in rows})==len(rows),
             "MASS_AXES_IDENTIFIERS_AND_COORDINATES_MUST_BE_UNIQUE")
        axes[name]={r["id"]:r["coordinate"] for r in rows}
    pairs=layout.get("selectedIntersections")
    if "selectedIntersections" not in layout:
        need(len(axes["X"])*len(axes["Y"])<=32,"MASS_AXIS_PLACEMENT_CAPACITY_EXCEEDED")
        pairs=[dict(X=x,Y=y) for y in axes["Y"] for x in axes["X"]]
    need(isinstance(pairs,list) and 1<=len(pairs)<=32 and
         all(isinstance(r,dict) and set(r)=={"X","Y"} and
             all(isinstance(r[k],str) and r[k] in axes[k] for k in ("X","Y")) for r in pairs),
         "MASS_SELECTED_AXIS_PAIRS_MUST_REFERENCE_KNOWN_IDENTIFIERS")
    need(len({(r["X"],r["Y"]) for r in pairs})==len(pairs),"MASS_DUPLICATE_SELECTED_AXIS_PAIR")
    return [dict(X=r["X"],Y=r["Y"],x=axes["X"][r["X"]],y=axes["Y"][r["Y"]],z=reference["z"])
            for r in pairs]


def placement_offsets(layout):
    need(isinstance(layout, dict), "MASS_PLACEMENT_RECIPE_REQUIRED")
    mode = layout.get("mode")
    if mode == "TRANSLATIONS":
        need(set(layout) == {"mode", "values"} and isinstance(layout["values"], list),
             "MASS_EXACT_TRANSLATIONS_REQUIRED")
        offsets = [vector(v) for v in layout["values"]]
    elif mode == "LINEAR":
        need(set(layout) == {"mode", "count", "start", "step"} and
             type(layout["count"]) is int and 1 <= layout["count"] <= 200,
             "MASS_LINEAR_EXPLICIT_COUNT_START_STEP_REQUIRED")
        start, step = vector(layout["start"]), vector(layout["step"])
        offsets = [vector({k: start[k] + i * step[k] for k in start})
                   for i in range(layout["count"])]
    elif mode == "LINE_SEGMENT":
        # Positions include both explicit endpoints. Count means new copies;
        # the retained prototype is not silently included in that count.
        need(set(layout) == {"mode", "count", "start", "end", "reference"} and
             type(layout["count"]) is int and 2 <= layout["count"] <= 200,
             "MASS_SEGMENT_EXPLICIT_ENDPOINTS_REFERENCE_AND_COPY_COUNT_REQUIRED")
        points = {}
        for name in ("start", "end", "reference"):
            point = layout[name]
            need(isinstance(point, dict) and set(point) == {"x", "y", "z"} and
                 all(type(n) in (int, float) and math.isfinite(n) and abs(n) <= 10000
                     for n in point.values()), "MASS_SEGMENT_FINITE_MODEL_METERS_REQUIRED")
            points[name] = point
        start, end, reference = (points[k] for k in ("start", "end", "reference"))
        need(start["z"] == end["z"] == reference["z"],
             "MASS_SEGMENT_HORIZONTAL_SOURCE_STORY_ONLY")
        need(math.hypot(end["x"] - start["x"], end["y"] - start["y"]) >= 1e-6,
             "MASS_SEGMENT_DISTINCT_ENDPOINTS_REQUIRED")
        offsets = [vector({"d" + k: start[k] + (end[k] - start[k]) * i /
                           (layout["count"] - 1) - reference[k] for k in ("x", "y", "z")})
                   for i in range(layout["count"])]
    elif mode == "GRID":
        from apa_ac29_native_group_grid import grid_offsets, SCHEMA as GRID_SCHEMA
        need(set(layout) == {"mode", "columns", "rows", "stepX", "stepY", "startDx", "startDy"},
             "MASS_GRID_EXPLICIT_COUNTS_PITCH_AND_START_REQUIRED")
        offsets = grid_offsets({"schema": GRID_SCHEMA,
                                **{k: v for k, v in layout.items() if k != "mode"}})
    elif mode == "AXIS_INTERSECTIONS":
        positions=axis_intersections(layout);reference=layout["reference"]
        offsets=[vector({"dx":r["x"]-reference["x"],"dy":r["y"]-reference["y"],"dz":0})
                 for r in positions]
    else:
        raise ValueError("MASS_UNSUPPORTED_PLACEMENT_MODE")
    unique = {tuple(row[k] for k in ("dx", "dy", "dz")) for row in offsets}
    need(1 <= len(offsets) <= 200 and len(unique) == len(offsets) and
         (0, 0, 0) not in unique, "MASS_DUPLICATE_ZERO_OR_UNBOUNDED_PLACEMENTS")
    return offsets


def normalize_mass_request(task):
    need(isinstance(task, dict) and set(task) == {
        "schemaVersion", "request", "sourceRef", "existing", "assembly", "placements"}
         and task["schemaVersion"] == SCHEMA and isinstance(task["sourceRef"], str)
         and len(task["sourceRef"]) >= 8 and isinstance(task["existing"], list)
         and bool(task["existing"]), "MASS_EXACT_SOURCE_QUALIFIED_TASK_REQUIRED")
    hints = recognize_request(task["request"])
    shifts = placement_offsets(task["placements"])
    existing = copy.deepcopy(task["existing"])
    need(all(isinstance(r, dict) and r.get("nativeReadbackVerified") is True and
             isinstance(r.get("guid"), str) and GROUP.GUID.fullmatch(r["guid"])
             for r in existing) and
         len({r["guid"].lower() for r in existing}) == len(existing),
         "MASS_FRESH_NATIVE_SOURCE_GUIDS_REQUIRED")
    for row in existing:
        GROUP.key(row)
    if task["placements"]["mode"] in {"AXIS_INTERSECTIONS", "LINE_SEGMENT"}:
        need((task["placements"]["mode"] != "AXIS_INTERSECTIONS" or
              task["placements"]["sourceRef"] == task["sourceRef"]) and
             all(abs(task["placements"]["reference"][k] - existing[0]["anchor"][k]) <= 1e-6
                 for k in ("x", "y", "z")),
             "MASS_PLACEMENT_REFERENCE_MUST_MATCH_FIRST_VERIFIED_SOURCE_ANCHOR")
    assembly = copy.deepcopy(task["assembly"])
    if assembly is not None:
        # Use only the currently code-owned clone verifier's actual domain.
        need(isinstance(assembly, dict) and assembly.get("existingGroupGuid") and
             assembly.get("groupReadbackVerified") is True and
             assembly.get("dependenciesVerified") is True and assembly.get("sameStory") is True
             and assembly.get("sourceRef") == task["sourceRef"] and
             len(existing) == 2 and all(r["type"] == "Column" and r["storyIndex"] == 0 for r in existing)
             and {r["guid"].lower() for r in existing} ==
                 {g.lower() for g in assembly.get("memberGuids", [])} and len(shifts) <= 32,
             "MASS_GROUP_REQUIRES_EXISTING_VERIFIED_TWO_COLUMN_CONTRACT")
        assembly["placements"] = shifts
    else:
        need(not hints["groups"], "MASS_GROUP_REQUEST_REQUIRES_VERIFIED_NATIVE_GROUP")
    need(len(existing) * len(shifts) <= 200, "MASS_NATIVE_BATCH_200_ROOT_LIMIT")
    targets = []
    for shift in shifts:
        for row in existing:
            point = {axis: round(row["anchor"][axis] + shift["d" + axis], 6)
                     for axis in ("x", "y", "z")}
            need(all(GROUP.finite(n) for n in point.values()), "MASS_TARGET_OUTSIDE_MODEL_BOUNDS")
            targets.append({"type": row["type"], "familySignature": row["familySignature"],
                            "storyIndex": row["storyIndex"], "anchor": point,
                            "sourceRef": task["sourceRef"]})
    return {"schemaVersion": "apa-native-group-auto/1", "request": task["request"],
            "existing": existing, "targets": targets,
            "assemblyGroups": [assembly] if assembly is not None else []}


def prepare_mass_request(router, task):
    from archicad_project_accelerator import prepare_auto_optimized_native_task
    normalized = normalize_mass_request(task)
    result = prepare_auto_optimized_native_task(router, normalized)
    prepared=dict(result, massRequestSchema=SCHEMA,
                recognizedIntent=recognize_request(task["request"]),
                placementMode=task["placements"]["mode"],
                qualification="SOURCE_PREVIEW_REQUIRES_FRESH_NATIVE_SCOPE_AND_READBACK",
                optimality="UNCALIBRATED_NO_SPEED_CLAIM")
    if task["placements"]["mode"]=="AXIS_INTERSECTIONS":
        prepared["placementReferences"]=dict(sourceRef=task["placements"]["sourceRef"],
            coordinateFrame="EXPLICIT_MODEL_METERS_ORTHOGONAL_AXES",nativeAxisObjectsCreated=False,
            intersections=axis_intersections(task["placements"]))
    return prepared
