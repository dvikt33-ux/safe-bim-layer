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

import archicad_semantic_spatial as SPATIAL
import archicad_semantic_brief as BRIEF
import archicad_building_shell as BUILD
import archicad_bim_graph as GRAPH
import archicad_scene_run as RUN

READS=frozenset({"GetProjectInfo","GetStories","GetAttributesByType"})


def compile_candidate(brief,pack,layout,heights,read_api,*,schema_path=None):
    """Native-schema validated single DAG, but never executable by this adapter."""
    if not callable(read_api):
        raise ValueError("EXPLICIT_READ_ONLY_NATIVE_SOURCE_REQUIRED")
    def api(cmd,params):
        if cmd not in READS:
            raise ValueError("READ_ONLY_API_COMMAND_DENIED")
        return read_api(cmd,params)
    geometry=SPATIAL.compile_spatial(brief,pack,layout)
    doc=BRIEF.normalize(brief)
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
    if geometry["missingSlabCseStoryIds"]:
        raise ValueError("FLOOR_SLAB_CSE_REQUIRED_ALL_STORIES")
    material_name=slab["native"]["name"]
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
    bounds=geometry["outline"]
    polygon=[
        BUILD.xy(bounds["xMin"],bounds["yMin"]),
        BUILD.xy(bounds["xMax"],bounds["yMin"]),
        BUILD.xy(bounds["xMax"],bounds["yMax"]),
        BUILD.xy(bounds["xMin"],bounds["yMax"]),
    ]
    for s in doc["stories"]:
        sid=s["id"]
        native=story_map[sid]["nativeIndex"]
        # One authored footprint slab per storey; no guessed room partitions.
        step_id="native-slab-"+sid
        ops.append(BUILD.step(step_id,"CreateSlabs",{
            "level":0.0,"floorIndex":native,
            "thickness":slab["thicknessMeters"],
            "referencePlaneLocation":"Top",
            "polygonCoordinates":polygon
        }))
        walls=sorted((m for m in geometry["bearingLines"]
                      if m["storyId"]==sid),key=lambda v:v["id"])
        for wall in walls:
            if wall["direction"]=="X":
                p1=BUILD.xy(wall["constantCoordinate"],wall["fromCoordinate"])
                p2=BUILD.xy(wall["constantCoordinate"],wall["toCoordinate"])
            else:
                p1=BUILD.xy(wall["fromCoordinate"],wall["constantCoordinate"])
                p2=BUILD.xy(wall["toCoordinate"],wall["constantCoordinate"])
            ops.append(BUILD.step("native-"+wall["id"],"CreateWalls",
                BUILD.wall(p1,p2,native,heights[sid],wall["thicknessMeters"])))
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
    return {
        "status":"OFFLINE_EXISTING_BIM_GRAPH_COMPILED_NOT_AUTHORIZED",
        "projectId":doc["projectId"],"nativeTargetProjectPath":doc["targetProjectPath"],
        "sourceLayoutStatus":geometry["status"],
        "sourcePackStatus":pack["status"],
        "authoredOutline":geometry["outline"],
        "authoredStoryHeightsMeters":{k:float(v) for k,v in heights.items()},
        "slabBasicMaterialName":material_name,
        "graph":graph,"executionOrder":checked["executionOrder"],
        "sourcePlanHash":checked["sourcePlanHash"],
        "schemaVersion":checked["schemaVersion"],
        "schemaSha256":hashlib.sha256(schema.read_bytes()).hexdigest(),
        "provisionalBasicSlabMaterialGuid":actual_guid,
        "storyBindings":known,
        "authoredRoomIds":[r["id"] for r in geometry["rooms"]],
        "plannedNativeCommands":dict(Counter(x["command"] for x in ops)),
        "unresolved":unresolved,
        "operationCount":len(ops),
        "graphValidator":"EXISTING_ARCHICAD_BIM_GRAPH_COMPILE_GRAPH",
        "nativeWriter":"EXISTING_SCENE_WRITER_NOT_CALLED",
        "liveWriteAuthorized":False,
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
    if candidate.get("nativeTargetProjectPath") not in (
            RUN.APPROVED_SCRATCH_PATH, RUN.APPROVED_ISOLATED_WRITER_PATH):
        raise ValueError("WRITER_PREVIEW_ONLY_FOR_EXISTING_APPROVED_SCRATCH_PLN")
    schema=RUN.DEFAULT_SCENE_SCHEMA
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
