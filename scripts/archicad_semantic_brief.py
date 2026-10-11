"""P70.A02.S01: typed project brief + strict GetStories resolution.

Pure/read-only adapter for THE existing Project Accelerator. Not a separate
graph, writer, general planner, or live project creation interface.
Both supported modes use user-visible architectural storey labels, not
guessed Tapir floorIndex. GENERATE_FROM_ZERO describes the requested stories
but does not create a new file or any Archicad story.
"""
from __future__ import annotations

import math
from pathlib import PureWindowsPath
import re

SCHEMA = "apa-semantic-project-brief/1"
MODES = frozenset({"GENERATE_FROM_ZERO", "ADAPT_EXISTING"})
_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{2,79}$")


def _name(value, field):
    if (not isinstance(value,str) or not 1<=len(value)<=160
            or value!=value.strip()):
        raise ValueError("INVALID_" + field)
    return value


def _nonneg(value, field):
    if type(value) not in (float,int) or not math.isfinite(value):
        raise ValueError("INVALID_" + field)
    return float(value)


def _id(value, field):
    if not isinstance(value,str) or not _ID.fullmatch(value):
        raise ValueError("INVALID_" + field)
    return value


def normalize(doc):
    """Validate user brief; never assign a native story index or BIM GUID."""
    fields={"schemaVersion","projectId","mode","units","site",
            "stories","rooms","constraints"}
    if not isinstance(doc,dict) or not fields<=set(doc) or set(doc)-fields-{"targetProjectPath"}:
        raise ValueError("INVALID_SEMANTIC_BRIEF_FIELDS")
    if doc["schemaVersion"]!=SCHEMA or doc["units"]!="meters" or doc["mode"] not in MODES:
        raise ValueError("UNSUPPORTED_BRIEF_SCHEMA_MODE_OR_UNITS")
    project=_id(doc["projectId"],"PROJECT_ID")
    target=doc.get("targetProjectPath")
    if target is not None:
        if (not isinstance(target,str) or
                len(target)>260 or target!=target.strip() or
                not PureWindowsPath(target).drive or
                PureWindowsPath(target).suffix.casefold()!=".pln"):
            raise ValueError("EXACT_WINDOWS_PLN_TARGET_REQUIRED")
    if doc["mode"]=="ADAPT_EXISTING" and target is None:
        raise ValueError("EXISTING_MODE_NEEDS_EXACT_PLN_PATH")
    site=doc["site"]
    if (not isinstance(site,dict) or set(site)!={"siteId","region"}):
        raise ValueError("SITE_FIELDS_REQUIRED")
    _id(site["siteId"],"SITE_ID")
    if site["region"] is not None:
        _name(site["region"],"REGION")

    stories=doc["stories"]
    if not isinstance(stories,list) or not 1<=len(stories)<=20:
        raise ValueError("STORIES_REQUIRED")
    seen_ids=set(); seen_labels=set(); normalized=[]; last=None
    for i,row in enumerate(stories):
        if (not isinstance(row,dict) or
                set(row)-{"id","label","level","existingNativeLabel"} or
                not {"id","label","level"}<=set(row)):
            raise ValueError("STORY_FIELDS_REQUIRED")
        sid=_id(row["id"],"STORY_ID")
        label=_name(row["label"],"STORY_LABEL")
        level=_nonneg(row["level"],"STORY_LEVEL")
        existing=row.get("existingNativeLabel",label)
        _name(existing,"EXISTING_STORY_LABEL")
        if (sid in seen_ids or label in seen_labels
                or (last is not None and level<=last)):
            raise ValueError("DUPLICATE_OR_UNORDERED_STORY")
        if i==0 and (label!="1 этаж" or abs(level)>1e-6):
            raise ValueError("FIRST_ARCHITECTURAL_STORY_MUST_BE_1_AT_ZERO")
        seen_ids.add(sid);seen_labels.add(label);last=level
        normalized.append({"id":sid,"label":label,"level":level,
                           "existingNativeLabel":existing})
    if len({s["existingNativeLabel"] for s in normalized})!=len(normalized):
        raise ValueError("DUPLICATE_EXISTING_STORY_LABEL")

    rooms=doc["rooms"]
    if not isinstance(rooms,list) or len(rooms)>100:
        raise ValueError("INVALID_ROOM_LIST")
    used_rooms=set();accepted=[]
    for room in rooms:
        if (not isinstance(room,dict) or
                set(room)!={"id","name","storyId","minAreaM2"}):
            raise ValueError("INVALID_ROOM_FIELDS")
        rid=_id(room["id"],"ROOM_ID")
        if rid in used_rooms:
            raise ValueError("DUPLICATE_ROOM_ID")
        if room["storyId"] not in seen_ids:
            raise ValueError("ROOM_HAS_UNKNOWN_STORY")
        area=_nonneg(room["minAreaM2"],"ROOM_AREA")
        if not .5<=area<=10000:
            raise ValueError("ROOM_AREA_OUTSIDE_SUPPORTED_RANGE")
        used_rooms.add(rid)
        accepted.append({"id":rid,"name":_name(room["name"],"ROOM_NAME"),
                         "storyId":room["storyId"],"minAreaM2":area})
    constraints=doc["constraints"]
    if not isinstance(constraints,list) or len(constraints)>100:
        raise ValueError("INVALID_CONSTRAINT_LIST")
    seen_cons=set(); checked_cons=[]
    for row in constraints:
        if not isinstance(row,dict) or set(row)!={"id","text","evidenceStatus"}:
            raise ValueError("INVALID_CONSTRAINT_FIELDS")
        cid=_id(row["id"],"CONSTRAINT_ID")
        if cid in seen_cons or row["evidenceStatus"] not in {"UNVERIFIED","SOURCE_VERIFIED"}:
            raise ValueError("DUPLICATE_OR_FALSE_VERIFIED_CONSTRAINT")
        seen_cons.add(cid)
        checked_cons.append({"id":cid,"text":_name(row["text"],"CONSTRAINT_TEXT"),
                             "evidenceStatus":row["evidenceStatus"]})
    return {"schemaVersion":SCHEMA,"projectId":project,
            "mode":doc["mode"],"units":"meters",
            "site":dict(site),"stories":normalized,"rooms":accepted,
            "constraints":checked_cons,"targetProjectPath":target,
            "nativeStoryBindings":[],"nativeResolution":"NOT_ATTEMPTED",
            "nativeWriteCalls":0}


def resolve_stories(normalized, api):
    """Only GET current project/stories; exact matching, no silent renumber.

    None of these lookups selects, opens, switches, creates or renames a PLN.
    """
    if not isinstance(normalized,dict) or normalized.get("schemaVersion")!=SCHEMA:
        raise ValueError("NORMALIZED_BRIEF_REQUIRED")
    target=normalized["targetProjectPath"]
    if target is None:
        return {**normalized,"nativeResolution":"NEEDS_NEW_PROJECT_SETUP"}
    allowed=frozenset({"GetProjectInfo","GetStories"})
    def read(cmd):
        if cmd not in allowed:
            raise ValueError("READ_ONLY_COMMAND_BLOCKED")
        return api(cmd,{})
    project=read("GetProjectInfo")
    def norm(x):
        return x.casefold() if isinstance(x,str) else None
    if (not isinstance(project,dict) or
            norm(project.get("projectPath"))!=norm(target)
            or project.get("isUntitled") is not False or
            project.get("isTeamwork") is not False):
        raise ValueError("WRONG_ACTIVE_SINGLE_PLN")
    state=read("GetStories")
    current=state.get("stories") if isinstance(state,dict) else None
    if not isinstance(current,list):
        raise ValueError("NATIVE_STORY_INVENTORY_UNAVAILABLE")
    bindings=[]
    for story in normalized["stories"]:
        matches=[s for s in current if isinstance(s,dict)
                 and (s.get("name") or s.get("uName") or "")==story["existingNativeLabel"]
                 and isinstance(s.get("index"),int)
                 and isinstance(s.get("floorId"),int)
                 and type(s.get("level")) in (int,float)
                 and math.isfinite(s["level"])
                 and abs(s["level"]-story["level"])<=1e-5]
        if len(matches)!=1:
            return {**normalized,"nativeResolution":"NEEDS_STORY_RESOLUTION",
                    "unresolvedArchitecturalStoryId":story["id"]}
        hit=matches[0]
        bindings.append({"architecturalStoryId":story["id"],"label":story["label"],
                         "nativeIndex":hit["index"],"floorId":hit["floorId"],
                         "nativeLabel":story["existingNativeLabel"],"level":hit["level"]})
    if (len({v["nativeIndex"] for v in bindings})!=len(bindings)
            or len({v["floorId"] for v in bindings})!=len(bindings)):
        return {**normalized,"nativeResolution":"NEEDS_STORY_RESOLUTION",
                "unresolvedArchitecturalStoryId":"AMBIGUOUS_NATIVE_BINDINGS"}
    return {**normalized,"nativeResolution":"READY_FOR_ATTRIBUTE_RESOLUTION",
            "nativeStoryBindings":bindings}
