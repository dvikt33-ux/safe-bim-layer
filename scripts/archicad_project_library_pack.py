"""P70.A02.S03: small, source-linked per-project CSE candidate pack.

Pure/read-only adapter. Reuses archicad_semantic_brief and the EXISTING
SceneWriter material resolver; does not create a materials registry,
import GDL/PLA, modify PLN, instantiate objects, or approve details.
"""
from __future__ import annotations

import math
import re
import archicad_semantic_brief as BRIEF
import archicad_scene_run as RUN

SCHEMA = "apa-project-library-pack/1"
_SHA1 = re.compile(r"^[a-f0-9]{40}$")
_SHA256 = re.compile(r"^[a-f0-9]{64}$")
_GUID = re.compile(r"^[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}$")
ROLES = frozenset({"floor-slab", "external-wall", "internal-partition",
                    "roof", "foundation", "opening-interface"})
RIGHTS = frozenset({"LINK_ONLY_RIGHTS_UNVERIFIED"})
SOURCE_STATES = frozenset({"PROJECT_NATIVE_READBACK", "TECHNICAL_REFERENCE",
                           "UNREVIEWED"})
DETAIL_STATES = frozenset({"UNVERIFIED", "BLOCKED"})
READS = frozenset({"GetProjectInfo","GetStories","GetAttributesByType"})


def _text(v, field):
    if not isinstance(v,str) or not v or len(v)>256 or v!=v.strip():
        raise ValueError("INVALID_"+field)
    return v


def _id(v, field):
    if (not isinstance(v,str) or len(v)>80
            or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{2,79}",v)):
        raise ValueError("INVALID_"+field)
    return v


def compile_pack(brief, candidate, *, api=None):
    """Build a minimal source-anchored pack, never certify project adequacy.

    The candidate is one actual geometry-enabling CSE candidate; additional
    structural systems remain deliberately unselected until source-backed.
    No user-provided SOURCE_VERIFIED flag can make details APPROVED.
    """
    doc = BRIEF.normalize(brief)
    if not isinstance(candidate,dict) or set(candidate)!={
            "candidateId","systemFamily","role","source","native",
            "thicknessMeters","storyIds","requiredInterfaceConditions",
            "selectedDetailIds"}:
        raise ValueError("CSE_CANDIDATE_CONTRACT_MISMATCH")
    candidate_id=_id(candidate["candidateId"],"CANDIDATE_ID")
    family=_id(candidate["systemFamily"],"SYSTEM_FAMILY")
    role=candidate["role"]
    if role not in ROLES:
        raise ValueError("UNSUPPORTED_CSE_ROLE")
    source=candidate["source"]
    if not isinstance(source,dict) or set(source)!={
            "sourceId","uri","gitBlobSha","publisher","rights",
            "status","licenseEvidenceUri","applicabilityNote"}:
        raise ValueError("CSE_SOURCE_FIELDS_REQUIRED")
    source_id=_id(source["sourceId"],"SOURCE_ID")
    uri=_text(source["uri"],"SOURCE_URI")
    if not (uri.startswith("https://github.com/dvikt33-ux/safe-bim-layer/")
            and "/blob/" in uri):
        raise ValueError("UNPINNED_OR_EXTERNAL_CSE_SOURCE")
    sha=source["gitBlobSha"]
    if not isinstance(sha,str) or not _SHA1.fullmatch(sha):
        raise ValueError("SOURCE_BLOB_SHA_REQUIRED")
    if source["rights"] not in RIGHTS or source["status"] not in SOURCE_STATES:
        raise ValueError("CSE_LICENSE_OR_EVIDENCE_STATUS_INVALID")
    license_uri=source["licenseEvidenceUri"]
    # A self-declared URL must never upgrade rights to verified.
    if license_uri is not None:
        _text(license_uri,"LICENSE_EVIDENCE_URI")
    _text(source["publisher"],"SOURCE_PUBLISHER")
    _text(source["applicabilityNote"],"SOURCE_APPLICABILITY")
    native=candidate["native"]
    if not isinstance(native,dict) or set(native)!={
            "attributeType","name","expectedProjectGuid"}:
        raise ValueError("CSE_NATIVE_BINDING_FIELDS_REQUIRED")
    if native["attributeType"]!="BuildingMaterial":
        raise ValueError("NO_VERIFIED_RESOLVER_FOR_THIS_NATIVE_ATTRIBUTE")
    material_name=_text(native["name"],"BUILDING_MATERIAL")
    expected=native["expectedProjectGuid"]
    if expected is not None and (not isinstance(expected,str) or not _GUID.fullmatch(expected)):
        raise ValueError("INVALID_EXPECTED_PROJECT_MATERIAL_GUID")
    thickness=candidate["thicknessMeters"]
    if (type(thickness) not in (int,float) or not math.isfinite(thickness)
            or not .05<=thickness<=1.5):
        raise ValueError("CSE_THICKNESS_MUST_BE_EXPLICIT_SI")
    valid_stories={x["id"] for x in doc["stories"]}
    requested=candidate["storyIds"]
    if (not isinstance(requested,list) or not requested
            or len(set(requested))!=len(requested)
            or not set(requested)<=valid_stories):
        raise ValueError("CSE_STORY_SCOPE_NOT_IN_BRIEF")
    required=candidate["requiredInterfaceConditions"]
    if (not isinstance(required,list) or not required
            or len(set(required))!=len(required)
            or any(not isinstance(x,str) or not x.strip() for x in required)):
        raise ValueError("CSE_REQUIRED_INTERFACE_CONDITIONS_INVALID")
    details=candidate["selectedDetailIds"]
    if details != []:
        # Details v2.12 are indexed references, NOT approved construction nodes.
        raise ValueError("DETAIL_BINDINGS_REQUIRE_INDEPENDENT_APPLICABILITY_AUDIT")
    scope={
        "schemaVersion":SCHEMA,"projectId":doc["projectId"],
        "projectMode":doc["mode"],"site":doc["site"],
        "targetProjectPath":doc["targetProjectPath"],
        "sourceLinksAndGitBlobHashes":[{
            "id":source_id,"uri":uri,"gitBlobSha":sha,
            "publisher":source["publisher"],"rights":source["rights"],
            "licenseEvidenceUri":license_uri,"sourceTruthLevel":source["status"],
            "applicabilityNote":source["applicabilityNote"]
        }],
        "selectedCseCandidates":[{
            "id":candidate_id,"systemFamily":family,"role":role,
            "storyIds":list(requested),"thicknessMeters":float(thickness),
            "native":{"attributeType":"BuildingMaterial","name":material_name,
                      "guid":None},"sourceId":source_id,
            "sourceTruthLevel":source["status"],"engineeringApproved":False,
            "detailApproved":False,
        }],
        "requiredJunctionConditions":[{"id":x,"status":"UNVERIFIED",
                                        "selectedDetailIds":[]} for x in required],
        "missingCriticalConditionIds":list(required),
        "importedLibraryObjects":[],
        "projectNativeFavoritesCompositesProfiles":[],
        "licenseAndStoragePermission":"NO_EXTERNAL_FILES_IMPORTED",
        "normativePackDigest":None,
        "sourceRegistryRevision":sha,
        "status":"PROVISIONAL_CSE_AWAITING_NATIVE_BINDING",
        "nativeWriteCalls":0,
    }
    if api is None:
        return scope
    def safe(cmd,params):
        if cmd not in READS:
            raise ValueError("NATIVE_MUTATION_BLOCKED")
        return api(cmd,params)
    mapped=BRIEF.resolve_stories(doc,safe)
    if mapped["nativeResolution"]!="READY_FOR_ATTRIBUTE_RESOLUTION":
        return {**scope,"status":mapped["nativeResolution"]}
    before=safe("GetProjectInfo",{})
    guid=RUN.resolve_basic_slab_material(safe,material_name)
    after=safe("GetProjectInfo",{})
    if before!=after:
        raise ValueError("PROJECT_IDENTITY_CHANGED_DURING_ATTRIBUTE_READ")
    if expected is not None and guid.casefold()!=expected.casefold():
        raise ValueError("PROJECT_BUILDING_MATERIAL_GUID_CHANGED")
    scope["selectedCseCandidates"][0]["native"]["guid"]=guid
    scope["nativeStoryBindings"]=mapped["nativeStoryBindings"]
    scope["status"]="PROJECT_NATIVE_MATERIAL_RESOLVED_NOT_ENGINEER_APPROVED"
    return scope
