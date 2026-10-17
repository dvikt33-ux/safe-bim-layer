"""High-level native assembly/group choice for APA AC29.

Source: Graphisoft ACAPI_ElementGroup_Create and ACAPI_ElementGroup_GetAllGroupedElems.
Planning only. Does not claim the existing Tapir/APA runtime exports group writing.
"""
from __future__ import annotations
from math import isfinite

def plan_assemblies(existing, assemblies):
    """Plan reuse of a whole verified composition, never individual element copies.

    Each assembly: sourceRef, memberGuids, placements [{dx,dy,dz}],
    existingGroupGuid (optional), sameStory (boolean), dependenciesVerified
    (boolean). Every displacement is an exact destination relative to source.
    """
    if assemblies is None:
        return []
    if not isinstance(assemblies, list):
        raise ValueError("ASSEMBLIES_LIST_REQUIRED")
    indexed = {row.get("guid", "").lower(): row for row in existing
               if isinstance(row, dict) and isinstance(row.get("guid"), str)}
    result = []
    for a in assemblies:
        if not isinstance(a, dict) or not isinstance(a.get("sourceRef"), str) or len(a["sourceRef"]) < 8:
            raise ValueError("ASSEMBLY_SOURCE_REQUIRED")
        guids = a.get("memberGuids")
        if not isinstance(guids, list) or len(guids) < 2 or any(not isinstance(g, str) for g in guids):
            raise ValueError("ASSEMBLY_MEMBERS_REQUIRED")
        if len(set(g.lower() for g in guids)) != len(guids):
            raise ValueError("ASSEMBLY_DUPLICATE_MEMBERS")
        if any(g.lower() not in indexed or indexed[g.lower()].get("nativeReadbackVerified") is not True for g in guids):
            raise ValueError("ASSEMBLY_MEMBERS_NOT_VERIFIED")
        stories = {indexed[g.lower()].get("storyIndex") for g in guids}
        if len(stories) != 1 or a.get("sameStory") is not True:
            raise ValueError("ASSEMBLY_GROUP_AC29_SAME_STORY_REQUIRED")
        placements = a.get("placements")
        if not isinstance(placements, list) or not placements:
            raise ValueError("ASSEMBLY_PLACEMENTS_REQUIRED")
        shifts = []
        for p in placements:
            if not isinstance(p, dict) or set(p) != {"dx", "dy", "dz"} or any(
                type(v) not in (float, int) or not isfinite(v) for v in p.values()
            ):
                raise ValueError("ASSEMBLY_FINITE_SHIFT_REQUIRED")
            xyz = tuple(round(p[k], 6) for k in ("dx", "dy", "dz"))
            if xyz == (0, 0, 0):
                raise ValueError("ASSEMBLY_ZERO_SHIFT_COPIES_SOURCE")
            shifts.append(xyz)
        if len(set(shifts)) != len(shifts):
            raise ValueError("ASSEMBLY_DUPLICATE_PLACEMENT")
        verified_group = isinstance(a.get("existingGroupGuid"), str) and bool(a["existingGroupGuid"])
        ready = a.get("dependenciesVerified") is True and verified_group
        result.append({
            "sourceRef": a["sourceRef"],
            "memberCount": len(guids),
            "copies": len(shifts),
            "groupGuid": a.get("existingGroupGuid") if verified_group else None,
            "memberGuids": guids,
            "relativePlacements": shifts,
            "strategy": "NATIVE_GROUP_REPLICATION" if verified_group else "NATIVE_GROUP_THEN_REPLICATION",
            "groupCreationSDK": None if verified_group else "ACAPI_ElementGroup_Create",
            "groupReadbackSDK": "ACAPI_ElementGroup_GetAllGroupedElems",
            "status": "REQUIRES_NATIVE_GROUP_AND_COPY_RUNTIME_BINDING" if ready
                      else "BLOCKED_VERIFY_GROUP_DEPENDENCIES_AND_RUNTIME",
            "nativeModelWrites": 0,
            "estimatedCalls": None,
            "disbandAfterCopy": False,
        })
    return result
