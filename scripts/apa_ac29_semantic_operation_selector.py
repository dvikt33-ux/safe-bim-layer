"""APA AC29 semantic topology and native operation choice. READ-ONLY preview.

Uses the ORIGINAL DynamicCommands.plan_reuse_existing for prototype matching.
Does not infer dimensions, construct native GridElements, claim cost optimality,
write to SceneWriter, or change the user's BDD PLN. It distinguishes a
RECTANGULAR ARRAY of objects from independent architectural AXIS GRID intent.
"""
from __future__ import annotations

from collections import defaultdict
import math

from archicad_dynamic_commands import DynamicCommands
from apa_ac29_assembly_operations import plan_assemblies

TOL = 1e-6
COPYABLE = frozenset({"Column", "Beam", "Object"})
CREATABLE = {
    "Column": "CreateColumns", "Beam": "CreateBeams",
    "Wall": "CreateWalls", "Roof": "CreateRoofs",
    "Slab": "CreateSlabs", "Window": "CreateWindows",
    "Door": "CreateDoors",
}
HOSTED = frozenset({"Window", "Door"})
SCHEMA = "APA_AC29_SEMANTIC_NATIVE_CHOICE_V1"


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def q(x):
    need(type(x) in (int, float) and math.isfinite(x) and abs(x) < 100000,
         "SEMANTIC_SELECTOR_FINITE_COORDINATE_REQUIRED")
    return round(x, 6)


def xyz(target):
    p = target["anchor"]
    return tuple(q(p[k]) for k in ("x", "y", "z"))


def _regular(values):
    return len(values) < 3 or all(
        abs((values[i+1]-values[i])-(values[1]-values[0])) <= TOL
        for i in range(1,len(values)-1)
    )


def _parallel_linear_runs(points):
    """Find complete, equidistant parallel rows without filling gaps.

    Returns run decomposition only if EVERY exact target belongs to a
    homogeneous row with >=3 items and verified constant pitch. A Cartesian
    complete rectangle is classified earlier as RECTANGULAR_ARRAY.
    """
    for direction in ("X","Y"):
        by_line=defaultdict(list)
        for x,y,z in points:
            line=(q(y),q(z)) if direction=="X" else (q(x),q(z))
            by_line[line].append(x if direction=="X" else y)
        if len(by_line)<2:
            continue
        parts=[]
        valid=True
        for (fixed,z),values in sorted(by_line.items()):
            coords=sorted(values)
            if len(coords)<3 or not _regular(coords) or abs(coords[-1]-coords[0])<=TOL:
                valid=False
                break
            step=coords[1]-coords[0]
            if step<=TOL:
                valid=False
                break
            parts.append({"direction":direction,"fixedCoordinate":fixed,
                          "z":z,"count":len(coords),"start":coords[0],
                          "step":round(step,6)})
        if valid:
            return parts
    return None


def _on_segment(p, a, b):
    v = tuple(b[i]-a[i] for i in range(3))
    v2 = sum(x*x for x in v)
    need(v2 > TOL*TOL, "SEMANTIC_SELECTOR_ZERO_PATH_SEGMENT")
    t = sum((p[i]-a[i])*v[i] for i in range(3))/v2
    dist = math.sqrt(sum((p[i]-a[i]-t*v[i])**2 for i in range(3)))
    return t, dist, math.sqrt(v2)


def _polyline_arclengths(points, path):
    route = [xyz({"anchor":p}) for p in path]
    need(len(route)>=2 and len(set(route))==len(route),
         "SEMANTIC_SELECTOR_PATH_REQUIRES_DISTINCT_VERTICES")
    lengths = []
    for a,b in zip(route,route[1:]):
        length = math.dist(a,b)
        need(length > TOL, "SEMANTIC_SELECTOR_ZERO_PATH_SEGMENT")
        lengths.append(length)
    result = []
    for p in points:
        candidates=[]
        offset=0.
        for a,b,lg in zip(route,route[1:],lengths):
            t,dist,_ = _on_segment(p,a,b)
            if -TOL <= t <= 1+TOL and dist <= TOL:
                candidates.append(offset+min(1,max(0,t))*lg)
            offset+=lg
        need(candidates, "SEMANTIC_SELECTOR_POINT_NOT_ON_SOURCE_PATH")
        result.append(min(candidates))
    return sorted(result), sum(lengths), route


def topology(points, rule=None):
    """Classify actual points; never insert missing positions or infer axes."""
    need(isinstance(points,list) and bool(points),
         "SEMANTIC_SELECTOR_NONEMPTY_TARGET_SET_REQUIRED")
    p = sorted(points)
    need(len(set(p))==len(p),
         "SEMANTIC_SELECTOR_DUPLICATE_TARGET_POSITION")
    if len(p)==1:
        need(rule is None,"SEMANTIC_SELECTOR_SINGLE_HAS_NO_DISTRIBUTION_RULE")
        return {"pattern":"SINGLE","count":1,"step":None}
    if rule is not None:
        need(isinstance(rule,dict) and set(rule)=={"mode","sourceRef","path"} and
             rule["mode"] in {"EVEN_BETWEEN","ALONG_POLYLINE"} and
             isinstance(rule["sourceRef"],str) and len(rule["sourceRef"])>7 and
             isinstance(rule["path"],list),
             "SEMANTIC_SELECTOR_DISTRIBUTION_REQUIRES_REVIEWED_PATH")
        distances,total,route=_polyline_arclengths(p,rule["path"])
        need(len(p)>=2 and abs(distances[0])<=TOL and
             abs(distances[-1]-total)<=TOL and
             all(abs(x-total*i/(len(p)-1))<=TOL
                 for i,x in enumerate(distances)),
             "SEMANTIC_SELECTOR_DISTRIBUTION_MUST_PRESERVE_ALL_EXACT_POINTS")
        if rule["mode"]=="EVEN_BETWEEN":
            need(len(route)==2,
                 "SEMANTIC_SELECTOR_BETWEEN_REQUIRES_ONE_STRAIGHT_SEGMENT")
            return {"pattern":"EVEN_DISTRIBUTION","count":len(p),
                    "step":round(total/(len(p)-1),6)}
        return {"pattern":"POLYLINE_DISTRIBUTION","count":len(p),
                "step":round(total/(len(p)-1),6)}
    zz={p0[2] for p0 in p}
    xs=sorted({p0[0] for p0 in p})
    ys=sorted({p0[1] for p0 in p})
    if (len(zz)==1 and len(xs)>1 and len(ys)>1 and
            len(xs)*len(ys)==len(p) and
            {(x,y,next(iter(zz))) for x in xs for y in ys}==set(p) and
            _regular(xs) and _regular(ys)):
        return {"pattern":"RECTANGULAR_ARRAY","count":len(p),
                "gridShape":[len(xs),len(ys)],
                "step":[round(xs[1]-xs[0],6),round(ys[1]-ys[0],6)]}
    runs=_parallel_linear_runs(p)
    if runs:
        return {"pattern":"PARALLEL_LINEAR_RUNS","count":len(p),
                "runCount":len(runs),"runs":runs}
    origin=p[0]
    vector=tuple(p[-1][i]-origin[i] for i in range(3))
    span=sum(v*v for v in vector)
    if span>TOL*TOL:
        projections=sorted(sum((x[i]-origin[i])*vector[i] for i in range(3))/span
                           for x in p)
        if all(math.dist(x,tuple(origin[i]+t*vector[i] for i in range(3)))<=TOL
               for x,t in zip(p,[
                   sum((z[i]-origin[i])*vector[i] for i in range(3))/span for z in p
               ])):
            if _regular(projections):
                return {"pattern":"LINEAR_ARRAY","count":len(p),
                        "step":round(math.sqrt(span)/(len(p)-1),6)}
    return {"pattern":"EXPLICIT_POSITIONS","count":len(p),"step":None}


def axes_review(axes, points):
    if axes is None:
        return {"status":"NO_SOURCE_QUALIFIED_AXIS_GRID_REQUEST",
                "nativeAxisCallsAuthorized":False}
    need(isinstance(axes,dict) and set(axes)=={
        "status","sourceRef","X","Y","requiresNativeAxisObjects"} and
        axes["status"]=="SOURCE_VERIFIED" and
        isinstance(axes["sourceRef"],str) and len(axes["sourceRef"])>=8 and
        type(axes["requiresNativeAxisObjects"]) is bool,
        "SEMANTIC_SELECTOR_AXIS_SOURCE_NOT_VERIFIED")
    for direction in ("X","Y"):
        rows=axes[direction]
        need(isinstance(rows,list) and rows and all(
            isinstance(row,dict) and set(row)=={"id","coordinate"} and
            isinstance(row["id"],str) and row["id"].strip() and
            type(row["coordinate"]) in (int,float) and
            math.isfinite(row["coordinate"]) for row in rows) and
            len({row["id"] for row in rows})==len(rows) and
            len({q(row["coordinate"]) for row in rows})==len(rows),
            "SEMANTIC_SELECTOR_DUPLICATED_OR_INVALID_SOURCE_AXES")
    xs={q(row["coordinate"]) for row in axes["X"]}
    ys={q(row["coordinate"]) for row in axes["Y"]}
    need(all(x in xs and y in ys for x,y,_ in points),
         "SEMANTIC_SELECTOR_ELEMENT_NOT_AT_SOURCE_AXIS_INTERSECTION")
    return {"status":("NATIVE_GRID_ELEMENTS_REQUIRE_INDEPENDENT_RUNTIME_AND_LIBRARY_PROOF"
                      if axes["requiresNativeAxisObjects"] else
                      "SOURCE_AXES_REFERENCED_NO_NATIVE_GRID_ELEMENTS_REQUESTED"),
            "sourceAxesX":len(xs),"sourceAxesY":len(ys),
            "occupiedIntersections":len({(x,y) for x,y,_ in points}),
            "sourceRef":axes["sourceRef"],"nativeAxisCallsAuthorized":False}


def analyze(existing, targets, *, source_axes=None, distribution_rules=None, assembly_groups=None):
    """Read-only answer on exact supplied construction/placements.

    Source-qualified rows must have real familySignature, typed coordinates
    and original sourceRef. A copy suggestion only uses an existing verified
    native prototype and original planner. Mixed copyable prototypes pack into
    one MoveElements batch; incompatible create families remain separate.
    """
    need(isinstance(distribution_rules,(dict,type(None))),
         "SEMANTIC_SELECTOR_RULES_MAP_REQUIRED")
    distribution_rules=distribution_rules or {}
    need(isinstance(existing,list) and isinstance(targets,list) and bool(targets),
         "SEMANTIC_SELECTOR_NONEMPTY_TYPED_TASK_REQUIRED")
    for row in targets:
        need(isinstance(row,dict) and row.get("type") in (set(CREATABLE)|{"Object"}) and
             isinstance(row.get("sourceRef"),str) and len(row["sourceRef"])>=8 and
             isinstance(row.get("familySignature"),str) and
             len(row["familySignature"])>=16 and
             type(row.get("storyIndex")) is int and
             isinstance(row.get("anchor"),dict) and
             set(row["anchor"])=={"x","y","z"},
             "SEMANTIC_SELECTOR_SOURCE_TYPED_TARGET_REQUIRED")
        xyz(row)
    need(set(distribution_rules)<={
        (r["type"],r["familySignature"],r["storyIndex"]) for r in targets},
         "SEMANTIC_SELECTOR_UNUSED_DISTRIBUTION_RULE")
    # The original copy-first planner supports native Column/Beam/Object
    # prototypes. Roofs and hosted/structural dependent families are still
    # accounted for, but must not be fed into unsupported copy recipes.
    safe_existing=[row for row in existing if row.get("type") in COPYABLE]
    safe_targets=[row for row in targets if row["type"] in COPYABLE]
    plan=(DynamicCommands.plan_reuse_existing(safe_existing,safe_targets)
          if safe_targets else {
              "copyGroups":[],"unmatchedTargetsPendingPrototype":[],
              "existingElementGuids":[]})
    # Independent existing elements of non-copyable kinds can satisfy an exact
    # identity/location, but cannot be translated as detached copies.
    fulfilled_other=[]
    create_other=[]
    for target in targets:
        if target["type"] in COPYABLE:
            continue
        matching=[src for src in existing
            if src.get("nativeReadbackVerified") is True and
               src.get("type")==target["type"] and
               src.get("familySignature")==target["familySignature"] and
               src.get("storyIndex")==target["storyIndex"] and
               isinstance(src.get("anchor"),dict) and
               xyz(src)==xyz(target) and
               (target["type"] not in HOSTED or
                (src.get("ownerWallGuid") and
                 src.get("ownerWallGuid")==
                 target.get("nativeCreateData",{}).get(
                     "ownerWallId",{}).get("guid")))]
        if matching:
            fulfilled_other.append(matching[0].get("guid"))
        else:
            create_other.append(target)
    copy_groups=[]
    planned_guids={x["guid"].lower():x for x in existing}
    for group in plan["copyGroups"]:
        parent=planned_guids[group["prototypeGuid"].lower()]
        need(group["prototypeType"] in COPYABLE,
             "SEMANTIC_SELECTOR_DEPENDENT_OR_HOSTED_COPY_NOT_REVIEWED")
        copied=[tuple(q(parent["anchor"][k]+shift[k])
                      for k in ("x","y","z")) for shift in group["displacements"]]
        key=(parent["type"],parent["familySignature"],parent["storyIndex"])
        # When the source prototype itself occupies an approved target,
        # it counts for pattern inference (but must NEVER be copied again).
        source_point=xyz(parent)
        source_is_target=any(
            (r["type"],r["familySignature"],r["storyIndex"])==key and
            xyz(r)==source_point for r in targets)
        layout=copied+([source_point] if source_is_target else [])
        report=topology(layout,distribution_rules.get(key))
        copy_groups.append({"prototypeGuid":group["prototypeGuid"],
                            "familyType":group["prototypeType"],
                            "count":len(copied),
                            "layoutTargetCount":len(layout),
                            "prototypeAlreadyOccupiesTarget":source_is_target,
                            "arrangement":report,
                            "method":"NATIVE_COPY_SINGLE" if len(copied)==1
                                else "NATIVE_COPY_BULK",
                            "nativeCommand":"MoveElements",
                            "sourceRef":group["sourceRef"]})
    remaining=defaultdict(list)
    for row in [*plan["unmatchedTargetsPendingPrototype"],*create_other]:
        remaining[(row["type"],row["familySignature"],row["storyIndex"])].append(row)
    creates=[]
    for key,rows in sorted(remaining.items()):
        points=[xyz(x) for x in rows]
        rpt=topology(points,distribution_rules.get(key))
        command=CREATABLE.get(key[0])
        # A native creation strategy cannot be authorized from coordinates
        # alone: complete nativeCreateData is mandatory for each element.
        complete=all(isinstance(x.get("nativeCreateData"),dict) and
                     bool(x["nativeCreateData"]) for x in rows)
        creates.append({"familyType":key[0],"count":len(rows),
                        "arrangement":rpt,
                        "method":"NATIVE_CREATE_SINGLE" if len(rows)==1
                            else "NATIVE_CREATE_BATCH",
                        "nativeCommand":command,
                        "state":("BLOCKED_OBJECT_CREATE_REQUIRES_VERIFIED_LIBRARY_PART"
                                 if command is None else
                                 "SOURCE_DATA_READY_FOR_NATIVE_SCHEMA_REVIEW"
                                 if complete else "BLOCKED_NATIVE_SOURCE_DATA_MISSING")})
    # Axis definitions are separate construction resources. Do not invent them
    # from a Cartesian array, and do not claim NativeGrid runtime support.
    requested=[xyz(row) for row in targets]
    axis_report=axes_review(source_axes,requested)
    copy_calls=int(bool(copy_groups))
    # For create calls, one per command family is a possible packing plan
    # only after each source row has passed the real runtime catalog/schema.
    create_commands=sorted({x["nativeCommand"] for x in creates
                            if x["nativeCommand"] is not None})
    return {
        "schema":SCHEMA,
        "status":"READ_ONLY_SEMANTIC_OPERATION_PLAN_PREPARED",
        "requestedTargets":len(targets),
        "alreadyPresent":len(plan["existingElementGuids"])+len(fulfilled_other),
        "copies":copy_groups,"creates":creates,
        "assemblies":plan_assemblies(existing, assembly_groups),
        "copyMethod":("ONE_NATIVE_MULTI_PROTOTYPE_COPY_CALL"
                      if len(copy_groups)>1 else
                      "ONE_NATIVE_BATCH_COPY_CALL"
                      if copy_calls and copy_groups[0]["count"]>1 else
                      "ONE_NATIVE_COPY_CALL" if copy_calls else "NONE"),
        "copyNativeCallsIfIndependentlyAuthorized":copy_calls,
        "createCommandFamilies":create_commands,
        "sourceAxes":axis_report,
        "requiresMeasuredCostForSpeedRanking":bool(copy_groups and creates),
        "nativeModelWrites":0,"nativeSaveCalls":0,
        "automaticNativeExecution":False,
        "nativeWritePermission":False,
        "sourceDataIndependentLiveVerification":False,
        "note":"Placement-pattern classification is NOT native-runtime availability, cost optimization, or project authorization."
    }
