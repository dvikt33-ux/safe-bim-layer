"""P70.A03.S01: authored room/axis/support constraints feeding the EXISTING BIM DAG.

No synthetic wall selection, no new BIM graph, no geometry mutation. This
projects a typed, explicit layout into candidate *source constraints*, not
into executable CreateWalls. S02 must resolve wall systems, project-native
story indices, and feed existing archicad_bim_graph.compile_graph/SceneWriter.
"""
from __future__ import annotations

from collections import Counter
import copy
import math

import archicad_semantic_brief as BRIEF

SCHEMA="apa-authored-spatial-layout/1"
EPS=1e-6


def number(value, field):
    if type(value) not in (int,float) or not math.isfinite(value):
        raise ValueError("INVALID_"+field)
    return float(value)


def rectangle(value, field):
    if not isinstance(value,dict) or set(value)!={"xMin","xMax","yMin","yMax"}:
        raise ValueError("INVALID_"+field+"_RECT")
    rect={key:number(value[key],field+"_"+key) for key in sorted(value)}
    if rect["xMax"]-rect["xMin"] < .6 or rect["yMax"]-rect["yMin"] < .6:
        raise ValueError("NONPOSITIVE_OR_TINY_"+field)
    return rect


def contains(outer,inner):
    return (outer["xMin"]-EPS<=inner["xMin"] and
            inner["xMax"]<=outer["xMax"]+EPS and
            outer["yMin"]-EPS<=inner["yMin"] and
            inner["yMax"]<=outer["yMax"]+EPS)


def overlap_area(a,b):
    return max(0,min(a["xMax"],b["xMax"])-max(a["xMin"],b["xMin"]))*max(
        0,min(a["yMax"],b["yMax"])-max(a["yMin"],b["yMin"]))


def compile_spatial(brief,pack,layout):
    """Return proof-carrying spatial facts; ALWAYS no-native-writes and not engineered."""
    doc=BRIEF.normalize(brief)
    if (not isinstance(pack,dict) or
            pack.get("schemaVersion")!="apa-project-library-pack/1"
            or pack.get("projectId")!=doc["projectId"] or
            pack.get("projectMode")!=doc["mode"]
            or pack.get("targetProjectPath")!=doc["targetProjectPath"]):
        raise ValueError("PROJECT_PACK_AND_BRIEF_IDENTITY_MISMATCH")
    candidates=pack.get("selectedCseCandidates")
    if not isinstance(candidates,list) or not candidates:
        raise ValueError("CSE_PACK_EMPTY")
    slab=[c for c in candidates if isinstance(c,dict) and c.get("role")=="floor-slab"]
    if len(slab)!=1 or not isinstance(slab[0].get("native"),dict):
        raise ValueError("EXACT_ONE_PROVISIONAL_SLAB_CSE_REQUIRED")
    slab=slab[0]
    if (slab.get("engineeringApproved") is not False or
            slab.get("detailApproved") is not False):
        raise ValueError("UNTRUSTED_SELF_APPROVED_CSE")
    if (not isinstance(layout,dict) or set(layout)!={
            "schemaVersion","outline","rooms","axes","bearingLines","loadPaths"} or
            layout["schemaVersion"]!=SCHEMA):
        raise ValueError("SPATIAL_LAYOUT_SCHEMA_MISMATCH")
    outline=rectangle(layout["outline"],"OUTLINE")
    if any(abs(x)>1e6 for x in outline.values()):
        raise ValueError("COORDINATES_OUT_OF_BOUNDS")
    story_ids={s["id"] for s in doc["stories"]}
    room_ids={r["id"]:r for r in doc["rooms"]}
    given_rooms=layout["rooms"]
    if not isinstance(given_rooms,list) or len(given_rooms)!=len(room_ids):
        raise ValueError("EVERY_BRIEF_ROOM_REQUIRES_AUTHORED_RECT")
    rooms={}
    for x in given_rooms:
        if not isinstance(x,dict) or set(x)!={"roomId","storyId","rectangle"}:
            raise ValueError("ROOM_LOCATION_SCHEMA")
        rid=x["roomId"]
        if rid not in room_ids or rid in rooms or x["storyId"]!=room_ids[rid]["storyId"]:
            raise ValueError("ROOM_ID_OR_STORY_MISMATCH")
        rect=rectangle(x["rectangle"],"ROOM")
        if not contains(outline,rect):
            raise ValueError("ROOM_OUTSIDE_APPROVED_OUTLINE")
        area=(rect["xMax"]-rect["xMin"])*(rect["yMax"]-rect["yMin"])
        if area+EPS<room_ids[rid]["minAreaM2"]:
            raise ValueError("ROOM_MINIMUM_AREA_VIOLATION")
        rooms[rid]={"id":rid,"storyId":x["storyId"],"rectangle":rect,
                    "areaM2":round(area,4)}
    if set(rooms)!=set(room_ids):
        raise ValueError("NOT_ALL_ROOMS_LOCATED")
    vals=list(rooms.values())
    for i,a in enumerate(vals):
        for q in vals[i+1:]:
            if (a["storyId"]==q["storyId"] and
                    overlap_area(a["rectangle"],q["rectangle"])>EPS):
                raise ValueError("ROOM_POLYGONS_OVERLAP_SAME_STOREY")

    axes=layout["axes"]
    if not isinstance(axes,list) or not 1<=len(axes)<=100:
        raise ValueError("AXES_REQUIRED")
    by_axis={}
    for a in axes:
        if not isinstance(a,dict) or set(a)!={"id","direction","coordinate"}:
            raise ValueError("AXIS_SCHEMA")
        aid=BRIEF._id(a["id"],"AXIS_ID")
        if aid in by_axis or a["direction"] not in ("X","Y"):
            raise ValueError("DUPLICATE_OR_BAD_AXIS")
        coord=number(a["coordinate"],"AXIS_COORDINATE")
        lower=outline["xMin" if a["direction"]=="X" else "yMin"]
        upper=outline["xMax" if a["direction"]=="X" else "yMax"]
        if not lower-EPS<=coord<=upper+EPS:
            raise ValueError("AXIS_OUTSIDE_OUTLINE")
        by_axis[aid]={"id":aid,"direction":a["direction"],"coordinate":coord}
    lines=layout["bearingLines"]
    if not isinstance(lines,list) or not lines or len(lines)>150:
        raise ValueError("AUTHORED_BEARING_LINES_REQUIRED")
    members={}
    for line in lines:
        if not isinstance(line,dict) or set(line)!={
                "id","storyId","axisId","fromCoordinate","toCoordinate",
                "wallThicknessMeters","cseCandidateId"}:
            raise ValueError("BEARING_LINE_SCHEMA")
        mid=BRIEF._id(line["id"],"BEARING_LINE_ID")
        sid=line["storyId"]
        axis=by_axis.get(line["axisId"])
        if mid in members or sid not in story_ids or axis is None:
            raise ValueError("UNKNOWN_OR_DUPLICATE_BEARING_LINE")
        start=number(line["fromCoordinate"],"BEARING_START")
        end=number(line["toCoordinate"],"BEARING_END")
        thick=number(line["wallThicknessMeters"],"WALL_THICKNESS")
        if not .15<=thick<=.6 or end-start<1.0:
            raise ValueError("INVALID_AUTHORED_WALL_ENVELOPE")
        lower=outline["yMin" if axis["direction"]=="X" else "xMin"]
        upper=outline["yMax" if axis["direction"]=="X" else "xMax"]
        if start<lower-EPS or end>upper+EPS:
            raise ValueError("BEARING_LINE_OUTSIDE_OUTLINE")
        # Avoid arbitrarily drawn supports: a real room edge must coincide.
        if not any(r["storyId"]==sid and (
            abs(axis["coordinate"]-r["rectangle"][
                "xMin" if axis["direction"]=="X" else "yMin"])<EPS or
            abs(axis["coordinate"]-r["rectangle"][
                "xMax" if axis["direction"]=="X" else "yMax"])<EPS)
            and start<r["rectangle"][
                "yMax" if axis["direction"]=="X" else "xMax"]-EPS
            and end>r["rectangle"][
                "yMin" if axis["direction"]=="X" else "xMin"]+EPS
            for r in rooms.values()):
            raise ValueError("BEARING_LINE_NOT_ON_AUTHORED_ROOM_BOUNDARY")
        wall_cse=line["cseCandidateId"]
        if wall_cse is not None:
            matching=[c for c in candidates if isinstance(c,dict) and
                      c.get("id")==wall_cse and c.get("role") in {
                          "external-wall","internal-partition"}]
            if len(matching)!=1:
                raise ValueError("BEARING_WALL_CSE_ROLE_NOT_MATCHED")
        members[mid]={"id":mid,"storyId":sid,"axisId":axis["id"],
                      "direction":axis["direction"],
                      "constantCoordinate":axis["coordinate"],
                      "fromCoordinate":start,"toCoordinate":end,
                      "thicknessMeters":thick,
                      "wallCseCandidateId":wall_cse,
                      "structuralApproval":"UNVERIFIED"}
    # Overlapping collinear native walls are not a valid plan.
    seq=list(members.values())
    for i,a in enumerate(seq):
        for q in seq[i+1:]:
            if (a["storyId"]==q["storyId"] and
                    a["direction"]==q["direction"] and
                    abs(a["constantCoordinate"]-q["constantCoordinate"])<EPS and
                    min(a["toCoordinate"],q["toCoordinate"])-
                    max(a["fromCoordinate"],q["fromCoordinate"])>EPS):
                raise ValueError("DUPLICATE_COLLINEAR_BEARING_WALL")
    paths=layout["loadPaths"]
    if not isinstance(paths,list):
        raise ValueError("LOAD_PATHS_REQUIRED_LIST")
    mapping={s["id"]:i for i,s in enumerate(doc["stories"])}
    visited=set()
    links=[]
    for link in paths:
        if not isinstance(link,dict) or set(link)!={"upperMemberId","lowerMemberId"}:
            raise ValueError("LOAD_PATH_SCHEMA")
        upper=members.get(link["upperMemberId"])
        lower=members.get(link["lowerMemberId"])
        if upper is None or lower is None or upper["id"]==lower["id"]:
            raise ValueError("LOAD_PATH_UNKNOWN_SUPPORT")
        pair=(upper["id"],lower["id"])
        if pair in visited:
            raise ValueError("DUPLICATE_LOAD_PATH")
        visited.add(pair)
        if mapping[upper["storyId"]]!=mapping[lower["storyId"]]+1:
            raise ValueError("LOAD_PATH_MUST_REACH_ADJACENT_LOWER_STORY")
        if (upper["direction"]!=lower["direction"] or
                abs(upper["constantCoordinate"]-lower["constantCoordinate"])>EPS or
                min(upper["toCoordinate"],lower["toCoordinate"])-
                max(upper["fromCoordinate"],lower["fromCoordinate"])<1.0):
            raise ValueError("LOAD_PATH_GEOMETRIC_SUPPORT_NOT_ALIGNED")
        links.append({"upperMemberId":upper["id"],
                      "lowerMemberId":lower["id"],
                      "geometryAligned":True,
                      "forceTransferProved":False})
    unlinked=[x["id"] for x in members.values()
              if mapping[x["storyId"]]>0 and
              not any(z["upperMemberId"]==x["id"] for z in links)]
    cse_missing=[x["id"] for x in members.values() if x["wallCseCandidateId"] is None]
    unresolved=pack.get("missingCriticalConditionIds",[])
    if not isinstance(unresolved,list):
        raise ValueError("CSE_UNRESOLVED_CONDITIONS_UNAVAILABLE")
    slab_stories=set(slab.get("storyIds",[]))
    missing_slabs=sorted(story_ids-slab_stories)
    return {
        "status":"AUTHORED_SPATIAL_GEOMETRY_CHECKED_ENGINEERING_PENDING",
        "schemaVersion":SCHEMA,"projectId":doc["projectId"],
        "sourcePackStatus":pack["status"],
        "outline":outline,
        "rooms":vals,"axes":list(by_axis.values()),
        "bearingLines":seq,"loadPaths":links,
        "floorSlabCseCandidateId":slab["id"],
        "floorSlabCandidateStoryIds":sorted(slab_stories),
        "unresolvedWallCseMemberIds":cse_missing,
        "upperMembersWithoutLoadPath":unlinked,
        "missingSlabCseStoryIds":missing_slabs,
        "unresolvedJunctionConditions":list(unresolved),
        "nativeBimGraph":"EXISTING_ARCHICAD_BIM_GRAPH_ONLY",
        "bimEmissionAuthorized":False,
        "engineeringApproved":False,"normativeApproved":False,
        "nativeWriteCalls":0,
        "summary":{"roomCount":len(vals),"authoredBearingLineCount":len(seq),
                   "alignedCandidateLoadPathCount":len(links),
                   "perStoryRoomCount":dict(Counter(x["storyId"] for x in vals))}
    }


def relocate_authored_xy(layout, dx, dy):
    """Pure *explicit* authored-layout translation; no geometry inferred.

    Shift whole BIM layout (outline, rooms, axes, continuous bearing lines)
    in world XY. Leaves structural links and story identity unchanged. This
    is NOT an automatic place-picker and does not grant Create/Modify.
    The result still needs compile_spatial and native read-only collision scan.
    """
    delta_x=number(dx,"TRANSLATION_X")
    delta_y=number(dy,"TRANSLATION_Y")
    if not isinstance(layout,dict) or set(layout)!={
            "schemaVersion","outline","rooms","axes","bearingLines","loadPaths"
            } or layout["schemaVersion"]!=SCHEMA:
        raise ValueError("AUTHORED_LAYOUT_REQUIRED_FOR_TRANSLATION")
    copied=copy.deepcopy(layout)
    def add(obj,key,delta):
        obj[key]=number(obj[key],"SOURCE_"+key)+delta
        if not math.isfinite(obj[key]) or abs(obj[key])>1e6:
            raise ValueError("TRANSLATED_COORDINATE_OUT_OF_RANGE")
    for key in ("xMin","xMax"):
        add(copied["outline"],key,delta_x)
    for key in ("yMin","yMax"):
        add(copied["outline"],key,delta_y)
    for room in copied["rooms"]:
        rect=room["rectangle"]
        for key in ("xMin","xMax"):
            add(rect,key,delta_x)
        for key in ("yMin","yMax"):
            add(rect,key,delta_y)
    axis_directions={}
    for axis in copied["axes"]:
        direction=axis["direction"]
        if direction not in ("X","Y") or axis["id"] in axis_directions:
            raise ValueError("INVALID_SOURCE_AXIS_FOR_TRANSLATION")
        axis_directions[axis["id"]]=direction
        add(axis,"coordinate",delta_x if direction=="X" else delta_y)
    for line in copied["bearingLines"]:
        direction=axis_directions.get(line["axisId"])
        if direction is None:
            raise ValueError("TRANSLATION_UNKNOWN_BEARING_AXIS")
        # X-axis constant coordinate is world X, so the span is world Y.
        # Y-axis constant coordinate is world Y, so the span is world X.
        delta=delta_y if direction=="X" else delta_x
        add(line,"fromCoordinate",delta)
        add(line,"toCoordinate",delta)
    return copied
