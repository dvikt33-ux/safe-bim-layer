"""P70.A03.S02 source-only authored line/slab -> existing BIM Graph adapter.

No new graph engine or SceneWriter, no native writes, no PLN project opening,
no automatic executor authorization. Only created from explicitly authored
bearing lines, actual GetStories bindings and exact single Building Material.
"""
from __future__ import annotations

from collections import Counter
import copy
import hashlib
import math
from pathlib import Path
import re

import archicad_semantic_spatial as SPATIAL
import archicad_semantic_brief as BRIEF
import archicad_building_shell as BUILD
import archicad_bim_graph as GRAPH
import archicad_scene_run as RUN

READS=frozenset({"GetProjectInfo","GetStories","GetAttributesByType"})


def _compile_stair_links(links, doc, geometry, floors, operations):
    """Plan straight +Y flights with an explicit left baseline and two landings."""
    from shapely.geometry import Polygon, box

    checks = {row["id"]: row for row in geometry["requirements"]
              if row.get("criterion", {}).get("kind") == "STAIR_LINK"}
    if not isinstance(links, list) or len(links) > len(checks):
        raise ValueError("STAIR_LINKS_REQUIRE_DISTINCT_BRIEF_CRITERIA")
    if links and not floors:
        raise ValueError("STAIR_LINK_REQUIRES_AUTHORED_FLOOR_PLANS")
    stories = {row["id"]: (ordinal, row["level"]) for ordinal, row in enumerate(doc["stories"])}
    fields = {"requirementId", "start", "stepCount", "widthM", "goingM", "favoriteName",
              "source", "lowerLandingDepthM", "upperLandingDepthM"}
    links_by_requirement, occupied_holes, reservations = {}, set(), []
    eps = SPATIAL.EPS
    for link in links:
        if not isinstance(link, dict) or set(link) != fields:
            raise ValueError("STAIR_LINK_INPUT_FIELDS_REQUIRED")
        rid = BRIEF._id(link["requirementId"], "STAIR_REQUIREMENT_ID")
        if rid not in checks or rid in links_by_requirement:
            raise ValueError("STAIR_LINKS_REQUIRE_DISTINCT_BRIEF_CRITERIA")
        source = link["source"]
        if (not isinstance(source, dict) or set(source) != {"ref", "sha256"}
                or not isinstance(source["ref"], str) or not source["ref"].strip()
                or not isinstance(source["sha256"], str) or not re.fullmatch(r"[a-f0-9]{64}", source["sha256"])):
            raise ValueError("STAIR_SOURCE_REFERENCE_AND_SHA256_REQUIRED")
        name = BRIEF._name(link["favoriteName"], "STAIR_FAVORITE_NAME")
        count, start = link["stepCount"], link["start"]
        if type(count) is not int or not 2 <= count <= 200 or not isinstance(start, dict) or set(start) != {"x", "y"}:
            raise ValueError("STAIR_FAVORITE_START_AND_STEP_COUNT_REQUIRED")
        width, going, lower_depth, upper_depth = (SPATIAL.number(link[key], key) for key in
            ("widthM", "goingM", "lowerLandingDepthM", "upperLandingDepthM"))
        if min(width, going, lower_depth, upper_depth) <= eps:
            raise ValueError("STAIR_FLIGHT_AND_LANDINGS_REQUIRE_POSITIVE_DIMENSIONS")
        x, y = (SPATIAL.number(start[key], "STAIR_START_" + key) for key in ("x", "y"))
        right, end = x + width, y + count * going
        bounds = geometry["outline"]
        if not (bounds["xMin"] <= x < right <= bounds["xMax"]
                and bounds["yMin"] <= y - lower_depth < y < end < end + upper_depth <= bounds["yMax"]):
            raise ValueError("STAIR_FLIGHT_OR_LANDING_OUTSIDE_LAYOUT")
        criterion = checks[rid]["criterion"]
        lower, upper = criterion["lowerStoryId"], criterion["upperStoryId"]
        index, level = stories[lower]
        height = stories[upper][1] - level
        lower_landing, upper_landing = box(x, y - lower_depth, right, y), box(x, end, right, end + upper_depth)
        if not floors[lower].buffer(eps).covers(lower_landing):
            raise ValueError("STAIR_LOWER_LANDING_REQUIRES_SOLID_SLAB")
        if not floors[upper].buffer(eps).covers(upper_landing):
            raise ValueError("STAIR_UPPER_LANDING_REQUIRES_SOLID_SLAB")
        flight = box(x, y, right, end)
        hole_index = next((i for i, ring in enumerate(floors[upper].interiors)
                           if Polygon(ring).buffer(eps).covers(flight)), None)
        if hole_index is None:
            raise ValueError("STAIR_FLIGHT_REQUIRES_MATCHING_UPPER_SLAB_VOID")
        hole_key = upper, hole_index
        if hole_key in occupied_holes:
            raise ValueError("STAIR_UPPER_SLAB_VOID_ALREADY_ASSIGNED")
        reserves = {lower: box(x, y - lower_depth, right, end), upper: box(x, y, right, end + upper_depth)}
        if any(shape.intersection(prior[story]).area > eps ** 2
               for prior in reservations for story, shape in reserves.items() if story in prior):
            raise ValueError("STAIR_FLIGHT_OR_LANDING_INTERSECTS_ANOTHER_STAIR")
        for wall in geometry["bearingLines"]:
            reserve = reserves.get(wall["storyId"])
            if reserve is None:
                continue
            c, a, b = wall["constantCoordinate"], wall["fromCoordinate"], wall["toCoordinate"]
            half = wall["thicknessMeters"] / 2
            footprint = box(c - half, a, c + half, b) if wall["direction"] == "X" else box(a, c - half, b, c + half)
            if footprint.intersection(reserve).area > eps ** 2:
                raise ValueError("STAIR_FLIGHT_OR_LANDING_INTERSECTS_WALL: " + wall["id"])
        occupied_holes.add(hole_key)
        reservations.append(reserves)

        sid = "native-stair-" + rid
        if len(sid) > 64:
            sid = "native-stair-" + hashlib.sha256(rid.encode("ascii")).hexdigest()[:40]
        slabs = ["native-slab-" + story for story in (lower, upper)]
        operation = BUILD.step(sid, "CreateStairs", dict(favoriteName=name, floorIndex=index,
            zCoordinate=level, totalHeight=height, baseLinePoints=[dict(x=x, y=y), dict(x=x, y=end)],
            flightWidth=width, stepNum=count, riserHeight=height / count, treadDepth=going, finishVisible=False))
        operation["after"] = slabs
        operations.append(operation)
        links_by_requirement[rid] = dict(requirementId=rid, stairOperationId=sid,
            lowerSlabOperationId=slabs[0], upperSlabOperationId=slabs[1], upperSlabHoleIndex=hole_index,
            source=copy.deepcopy(source), sourceStatus="DECLARED", flightLengthM=count * going,
            lowerLandingDepthM=lower_depth, upperLandingDepthM=upper_depth,
            nativeConnection="NOT_TESTED", headroom="UNVERIFIED", engineeringApproval="UNVERIFIED")
    return links_by_requirement


def compile_candidate(brief,pack,layout,heights,read_api,*,schema_path=None,junction_policy=None,
                      floor_plans=None,stair_links=None,design_only=False):
    """Native-schema validated single DAG, but never executable by this adapter."""
    if not design_only and not callable(read_api):
        raise ValueError("EXPLICIT_READ_ONLY_NATIVE_SOURCE_REQUIRED")
    if stair_links is not None and not design_only:
        raise ValueError("STAIR_LINK_NATIVE_BINDING_AND_READBACK_REQUIRED")
    def api(cmd,params):
        if cmd not in READS:
            raise ValueError("READ_ONLY_API_COMMAND_DENIED")
        return read_api(cmd,params)
    geometry=SPATIAL.compile_spatial(brief,pack,layout)
    doc=BRIEF.normalize(brief)
    if floor_plans is not None and (not isinstance(floor_plans,dict) or set(floor_plans)!={s['id'] for s in doc['stories']}):
        raise ValueError('SOURCE_FLOOR_PLAN_REQUIRED_EVERY_STORY')
    if not isinstance(heights,dict) or set(heights)!={x["id"] for x in doc["stories"]}:
        raise ValueError("STORY_HEIGHTS_MUST_BE_AUTHORED")
    for i,story in enumerate(doc["stories"]):
        h=heights[story["id"]]
        if type(h) not in (int,float) or not math.isfinite(h) or not 2.4<=h<=4.5:
            raise ValueError("UNSUPPORTED_AUTHORED_STORY_HEIGHT")
        if i+1<len(doc["stories"]):
            next_level=doc["stories"][i+1]["level"]
            if abs(story["level"]+h-next_level)>1e-5:
                raise ValueError("STORY_HEIGHT_INCONSISTENT_WITH_LEVELS")

    known=[]
    if not design_only:
        if pack.get("status")!="PROJECT_NATIVE_MATERIAL_RESOLVED_NOT_ENGINEER_APPROVED":
            raise ValueError("PROJECT_NATIVE_CSE_BINDING_NOT_ESTABLISHED")
        known=pack.get("nativeStoryBindings")
        resolved=BRIEF.resolve_stories(doc,api)
        if resolved["nativeResolution"]!="READY_FOR_ATTRIBUTE_RESOLUTION":
            raise ValueError("REAL_STORY_MAP_UNRESOLVED")
        if known!=resolved["nativeStoryBindings"]:
            raise ValueError("PROJECT_STORY_MAPPING_CHANGED_SINCE_CSE_READ")
    candidates=pack["selectedCseCandidates"]
    slab=next(x for x in candidates if x.get("role")=="floor-slab")
    if junction_policy is not None and junction_policy != {
            'schema': 'apa-native-junction-policy/1',
            'slabFootprint': 'OUTER_WALL_FACE',
            'intermediateWallTop': 'SLAB_UNDERSIDE'}:
        raise ValueError('UNSUPPORTED_AUTHORED_JUNCTION_POLICY')
    if geometry["missingSlabCseStoryIds"]:
        raise ValueError("FLOOR_SLAB_CSE_REQUIRED_ALL_STORIES")
    material_name=slab["native"]["name"]
    actual_guid=None
    if not design_only:
        before=api("GetProjectInfo",{})
        actual_guid=RUN.resolve_basic_slab_material(api,material_name)
        after=api("GetProjectInfo",{})
        if before!=after:
            raise ValueError("ACTIVE_PROJECT_IDENTITY_CHANGED")
        expected_guid=slab["native"].get("guid")
        if (not isinstance(expected_guid,str)
                or actual_guid.casefold()!=expected_guid.casefold()):
            raise ValueError("PROJECT_SLAB_MATERIAL_CHANGED_AFTER_PACK_BINDING")

    story_map={b["architecturalStoryId"]:b for b in known}
    ops=[]
    floor_shapes = {}
    bounds=geometry["outline"]
    polygon=[
        BUILD.xy(bounds["xMin"],bounds["yMin"]),
        BUILD.xy(bounds["xMax"],bounds["yMin"]),
        BUILD.xy(bounds["xMax"],bounds["yMax"]),
        BUILD.xy(bounds["xMin"],bounds["yMax"]),
    ]
    for story_number,s in enumerate(doc["stories"]):
        sid=s["id"]
        native=story_number if design_only else story_map[sid]["nativeIndex"]
        # One authored footprint slab per storey; no guessed room partitions.
        step_id="native-slab-"+sid
        walls=sorted((m for m in geometry["bearingLines"]
                      if m["storyId"]==sid),key=lambda v:v["id"])
        footprint=copy.deepcopy(bounds)
        wall_height=heights[sid]
        if junction_policy:
            for field,direction in [('xMin','X'),('xMax','X'),('yMin','Y'),('yMax','Y')]:
                boundary=[w for w in walls if w['direction']==direction and
                    abs(w['constantCoordinate']-bounds[field])<1e-6]
                if not boundary:raise ValueError('JUNCTION_POLICY_REQUIRES_RECTANGULAR_PERIMETER_WALLS')
                margin=max(w['thicknessMeters']/2 for w in boundary)
                footprint[field] += margin * (-1 if field.endswith('Min') else 1)
            if story_number+1<len(doc['stories']):
                wall_height-=slab['thicknessMeters']
                if wall_height<=0:raise ValueError('SLAB_LEAVES_NO_CLEAR_WALL_HEIGHT')
        slab_polygon=[BUILD.xy(footprint['xMin'],footprint['yMin']),
            BUILD.xy(footprint['xMax'],footprint['yMin']),
            BUILD.xy(footprint['xMax'],footprint['yMax']),
            BUILD.xy(footprint['xMin'],footprint['yMax'])] if junction_policy else polygon
        authored_floor=None
        if floor_plans is not None:
            from shapely.geometry import LineString,box
            authored_floor,shape=BUILD.source_floor_polygon(floor_plans[sid])
            floor_shapes[sid] = shape
            envelope=box(bounds['xMin'],bounds['yMin'],bounds['xMax'],bounds['yMax']).buffer(.6)
            if not envelope.covers(shape):raise ValueError('SOURCE_FLOOR_OUTSIDE_DECLARED_ENVELOPE')
            for member in walls:
                c=member['constantCoordinate'];a=member['fromCoordinate'];b=member['toCoordinate']
                points=[(c,a),(c,b)] if member['direction']=='X' else [(a,c),(b,c)]
                if not shape.buffer(1e-6).covers(LineString(points)):raise ValueError('SOURCE_WALL_OVER_FLOOR_VOID_OR_OUTSIDE_CONTOUR')
            for room in geometry['rooms']:
                if room['storyId']==sid:
                    q=room['rectangle'];room_polygon=box(q['xMin'],q['yMin'],q['xMax'],q['yMax'])
                    if not shape.buffer(1e-6).covers(room_polygon):raise ValueError('SOURCE_ROOM_OVER_FLOOR_VOID')
            slab_polygon=authored_floor['polygonCoordinates']
        ops.append(BUILD.step(step_id,"CreateSlabs",{
            # Tapir CreateSlabs level is absolute project Z; native details
            # return level relative to the home story and zCoordinate absolute.
            "level":float(s["level"]),"floorIndex":native,
            "thickness":slab["thicknessMeters"],
            "referencePlaneLocation":"Top",
            "polygonCoordinates":slab_polygon,
            **({'holes':authored_floor['holes']} if authored_floor is not None else {})
        }))
        for wall in walls:
            if wall["direction"]=="X":
                p1=BUILD.xy(wall["constantCoordinate"],wall["fromCoordinate"])
                p2=BUILD.xy(wall["constantCoordinate"],wall["toCoordinate"])
            else:
                p1=BUILD.xy(wall["fromCoordinate"],wall["constantCoordinate"])
                p2=BUILD.xy(wall["toCoordinate"],wall["constantCoordinate"])
            ops.append(BUILD.step("native-"+wall["id"],"CreateWalls",
                BUILD.wall(p1,p2,native,wall_height,wall["thicknessMeters"])))
    for opening in geometry["openings"]:
        kind = "CreateDoors" if opening["kind"] == "DOOR" else "CreateWindows"
        if opening["sillHeight"] + opening["height"] > float(heights[opening["storyId"]]) + SPATIAL.EPS:
            raise ValueError("PASSAGE_EXCEEDS_STORY_HEIGHT")
        ops.append(BUILD.step("native-opening-" + opening["id"], kind,
            BUILD.opening("native-" + opening["hostMemberId"], opening["centerOffset"],
                          opening["width"], opening["height"], opening["sillHeight"])))
    stairs = _compile_stair_links(stair_links, doc, geometry, floor_shapes, ops) if stair_links is not None else {}
    schema=Path(schema_path or RUN.DEFAULT_SCENE_SCHEMA)
    if not schema.is_file():
        raise ValueError("NATIVE_TAPIR_SCHEMA_MISSING")
    catalog=GRAPH.CONTRACTS.load_catalog(schema)
    graph={"operations":ops}
    checked=GRAPH.compile_graph(catalog,graph,
                                 runtime_version=RUN.EXPECTED_TAPIR)
    if checked["status"]!="PLAN_VALIDATED_OFFLINE":
        raise ValueError("EXISTING_BIM_GRAPH_REFUSED: "+checked["status"])
    # The app can inspect/preview; no nonreviewed engineering facts become
    # native write authorization just because JSON schema is valid.
    unresolved={
        "wallCse":list(geometry["unresolvedWallCseMemberIds"]),
        "loadPath":list(geometry["upperMembersWithoutLoadPath"]),
        "junctions":list(geometry["unresolvedJunctionConditions"]),
        "engineeringChecks":["STRUCTURAL_LOAD_PATH_UNVERIFIED",
                             "BUILDING_CODE_APPLICABILITY_UNVERIFIED"]
    }
    requirements = copy.deepcopy(geometry["requirements"])
    for row in requirements:
        if row.get("criterion", {}).get("kind") in ("ENTRANCE", "ROOM_CONNECTION", "ACCESS_PATH"):
            row["bimOperationIds"] = ["native-opening-" + oid for oid in row["designObjectIds"]]
        if row["id"] in stairs:
            connection = stairs[row["id"]]
            row.update(status="PARTIAL", reason="FLIGHT_VOID_AND_LANDINGS_PLANNED_NATIVE_READBACK_PENDING",
                       bimOperationIds=[connection[key] for key in (
                           "stairOperationId", "lowerSlabOperationId", "upperSlabOperationId")])
    requirements_pending = [row["id"] for row in requirements
                            if row.get("priority") == "REQUIRED" and row["status"] != "DESIGN_CHECKED"]
    return {
        "status":("BIM_GRAPH_PREVIEW_NEEDS_NATIVE_BINDINGS" if design_only
                  else "OFFLINE_EXISTING_BIM_GRAPH_COMPILED_NOT_AUTHORIZED"),
        "floorIndexBasis": "SEMANTIC_STORY_ORDINAL_PREVIEW_ONLY" if design_only else "NATIVE_STORY_READBACK",
        "projectId":doc["projectId"],"nativeTargetProjectPath":doc["targetProjectPath"],
        "sourceLayoutStatus":geometry["status"],
        "sourcePackStatus":pack["status"],
        "authoredOutline":geometry["outline"],
        "authoredStoryHeightsMeters":{k:float(v) for k,v in heights.items()},
        "authoredFloorPlans":copy.deepcopy(floor_plans),
        **({"stairConnections": list(stairs.values())} if stairs else {}),
        "slabBasicMaterialName":material_name,
        "graph":graph,"executionOrder":checked["executionOrder"],
        "sourcePlanHash":checked["sourcePlanHash"],
        "schemaVersion":checked["schemaVersion"],
        "schemaSha256":hashlib.sha256(schema.read_bytes()).hexdigest(),
        "schemaPath":str(schema.resolve()),
        "provisionalBasicSlabMaterialGuid":actual_guid,
        "storyBindings":known,
        "authoredRoomIds":[r["id"] for r in geometry["rooms"]],
        "requirements": requirements,
        "requiredOpenIds": requirements_pending,
        "areaMeasures": geometry["areaMeasures"],
        "areaBalance": geometry["areaBalance"],
        "plannedNativeCommands":dict(Counter(x["command"] for x in ops)),
        "unresolved":unresolved,
        "operationCount":len(ops),
        "graphValidator":"EXISTING_ARCHICAD_BIM_GRAPH_COMPILE_GRAPH",
        "nativeWriter":"EXISTING_SCENE_WRITER_NOT_CALLED",
        "liveWriteAuthorized":False,
        "engineeringApproved":False,
        "normativeApproved":False,
        "sceneReservationCreated":False,
        "plnChanged":False,
        "nativeWriteCalls":0
    }


def as_existing_scene_writer_preview(candidate):
    """Adapt validated authored DAG to pre-existing SceneWriter preview format.

    This is PURE: no native calls, file writes or reservations. Only the
    specifically already-approved throwaway scratch PLN is ever eligible for
    that writer. Other PLN paths are blocked, NOT silently added to a grant.
    """
    if (not isinstance(candidate,dict) or
            candidate.get("status")!="OFFLINE_EXISTING_BIM_GRAPH_COMPILED_NOT_AUTHORIZED"
            or candidate.get("liveWriteAuthorized") is not False
            or candidate.get("nativeWriteCalls")!=0):
        raise ValueError("UNTRUSTED_OR_AUTHORIZED_SOURCE_CANDIDATE")
    if not RUN.authorized_authored_target(candidate.get("nativeTargetProjectPath")):
        raise ValueError("WRITER_PREVIEW_ONLY_FOR_EXISTING_APPROVED_SCRATCH_PLN")
    schema=Path(candidate.get('schemaPath',RUN.DEFAULT_SCENE_SCHEMA))
    if (not schema.is_file() or
            hashlib.sha256(schema.read_bytes()).hexdigest()!=candidate.get("schemaSha256")):
        raise ValueError("PINNED_SCHEMA_CHANGED_SINCE_NATIVE_COMPILE")
    graph=candidate.get("graph")
    checked=GRAPH.compile_graph(GRAPH.CONTRACTS.load_catalog(schema),graph,
                                 runtime_version=RUN.EXPECTED_TAPIR)
    if (checked["status"]!="PLAN_VALIDATED_OFFLINE"
            or checked["sourcePlanHash"]!=candidate.get("sourcePlanHash")
            or checked["executionOrder"]!=candidate.get("executionOrder")):
        raise ValueError("AUTHORED_OPERATION_GRAPH_DRIFT")
    stories=candidate.get("storyBindings")
    if not isinstance(stories,list) or not stories:
        raise ValueError("STORY_BINDINGS_REQUIRED")
    native=[]
    for row in stories:
        if not isinstance(row,dict) or set(row)!={
                "architecturalStoryId","label","nativeIndex","floorId",
                "nativeLabel","level"}:
            raise ValueError("AUTHOR_TO_NATIVE_STORY_MAP_CHANGED")
        native.append({"label":row["nativeLabel"],"nativeIndex":row["nativeIndex"],
                       "floorId":row["floorId"],"level":row["level"]})
    heights=candidate.get("authoredStoryHeightsMeters")
    outline=candidate.get("authoredOutline")
    if (not isinstance(heights,dict) or
            not isinstance(outline,dict) or
            set(outline)!={"xMin","xMax","yMin","yMax"}):
        raise ValueError("AUTHORED_ENVELOPE_MISSING")
    last=stories[-1]
    final_height=heights.get(last["architecturalStoryId"])
    if type(final_height) not in (float,int) or not math.isfinite(final_height):
        raise ValueError("AUTHOR_LAST_STORY_HEIGHT_MISSING")
    if not isinstance(candidate.get("slabBasicMaterialName"),str):
        raise ValueError("EXPLICIT_BASIC_SLAB_MATERIAL_NAME_MISSING")
    counts=dict(Counter(x["command"] for x in graph["operations"]))
    if counts!=candidate.get("plannedNativeCommands"):
        raise ValueError("GRAPH_NATIVE_COMMAND_COUNTS_DRIFT")
    dimensions={
        "width":outline["xMax"]-outline["xMin"],
        "depth":outline["yMax"]-outline["yMin"],
        "height":last["level"]+final_height-stories[0]["level"],
    }
    if any(type(v) not in (int,float) or not math.isfinite(v) or v<=0
           for v in dimensions.values()):
        raise ValueError("INVALID_AUTHORED_SCENE_DIMENSIONS")
    return {
        "status":"SCENE_PREVIEW_OFFLINE",
        "nativeTargetProjectPath":candidate["nativeTargetProjectPath"],
        "sourcePlanHash":checked["sourcePlanHash"],
        "graph":graph,
        "executionOrder":checked["executionOrder"],
        "schemaVersion":checked["schemaVersion"],
        "schemaPath":str(schema),
        "schemaSha256":candidate["schemaSha256"],
        "storyBindings":native,
        "slabBasicMaterialName":candidate["slabBasicMaterialName"],
        "expectedPreflightSlabMaterialGuid":candidate["provisionalBasicSlabMaterialGuid"],
        "slabLevelConvention":"PROJECT_ABSOLUTE",
        "envelope":{**outline,
                    "zMin":stories[0]["level"]-.3,
                    "zMax":last["level"]+final_height+.3},
        "metrics":{"dimensionsMeters":dimensions,
                   "elementCount":candidate["operationCount"],
                   "nativeCommands":counts,
                   "authoredRooms":len(candidate["authoredRoomIds"]),
                   "structuralVerified":False,"normativeVerified":False},
        "limitations":["PROVISIONAL_AUTHORED_GEOMETRY_NOT_STRUCTURAL_ACCEPTANCE",
                       "NO_EXECUTION_GRANT_OR_NATIVE_WRITES",
                       "MISSING_PROVEN_WALL_CSE_AND_JUNCTIONS"],
        "liveWriteAuthorized":False,"plnChanged":False,
    }


def make_read_only_scene_writer_preview_factory(candidate):
    """Existing SceneWriter.preview_factory contract; only pure and immutable.

    This object cannot invoke the writer, set a port, create a journal, or
    grant permission. Requires caller's anchors to equal authored XY minima
    instead of ignoring coordinates and silently planning somewhere else.
    Each request revalidates the source schema/hash and yields a deep copy.
    """
    frozen=copy.deepcopy(candidate)
    preview=as_existing_scene_writer_preview(frozen)
    outline=preview["envelope"]
    def factory(x, y, schema_path):
        if (type(x) not in (int,float) or type(y) not in (int,float)
                or not math.isfinite(x) or not math.isfinite(y)
                or abs(x-outline["xMin"])>1e-6
                or abs(y-outline["yMin"])>1e-6):
            raise ValueError("SCENE_ANCHOR_DIFFERS_FROM_AUTHORED_OUTLINE")
        expected=Path(preview["schemaPath"]).resolve()
        if Path(schema_path).resolve()!=expected:
            raise ValueError("WRITER_SCHEMA_PATH_CHANGED_FROM_AUTHORED_PLAN")
        fresh=as_existing_scene_writer_preview(frozen)
        if fresh["sourcePlanHash"]!=preview["sourcePlanHash"]:
            raise ValueError("AUTHORED_PREVIEW_SOURCE_HASH_CHANGED")
        return copy.deepcopy(fresh)
    return factory
