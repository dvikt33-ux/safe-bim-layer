"""AC29 live, READ-ONLY proof of APA group-first automatic strategy selection.

Runs on the existing saved, disposable acceptance scratch PLN on port 19724.
No OpenProject/SaveProject/Create*/Clone*/Move*/Ungroup* or SceneWriter writes.
Exactly the existing APA native router, source-owned group commands, BIM Graph,
schema validation and runtime availability probes are exercised.

This is a planning/route acceptance, NOT authorization to clone more geometry.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import apa_ac29_group_acceptance_mailbox as LIVE
import apa_ac29_apx_build_mailbox as MAILBOX
import archicad_batch_contracts as CONTRACTS
import archicad_dynamic_commands as ROUTER
import archicad_project_accelerator as APA

ROOT = Path(__file__).resolve().parents[1]
BRANCH = "feature/apa-ac29-automatic-group-routing-20261018"
SCOPE = Path(r"C:\LocalAI\APA_Group_Acceptance\group-ac29-assembly-20261018-04.pln")
HISTORY = Path(r"C:\LocalAI\APA_AC29_Group_Acceptance_State\group-ac29-assembly-20261018-04")
READONLY_REPORT = (
    "safe-bim-mailbox/apa-ac29-group-acceptance/results/"
    "group-autoselect-real-model-readonly-20261018-01.json"
)
REPORT_LOCAL = HISTORY / "group-autoselect-real-model-readonly-20261018-01.json"
READ_COMMANDS = frozenset({
    "API.GetProductInfo", "API.IsAddOnCommandAvailable", "GetProjectInfo",
    "GetAddOnVersion", "GetAllElements", "GetDetailsOfElements",
    "Get3DBoundingBoxes", "GetNativeGroupMembersV1", "GetModelDumpV1",
    "GetSubelementsOfHierarchicalElements"
})


def require(ok, code):
    if not ok:
        raise RuntimeError(code)


def json_receipt(filename):
    path = HISTORY / filename
    require(path.is_file(), "PREVIOUS_NATIVE_ACCEPTANCE_EVIDENCE_NOT_FOUND:" + filename)
    return json.loads(path.read_text(encoding="utf8"))


def result_identity():
    preflight = json_receipt("preflight.json")
    create = json_receipt("after-create.json")
    completion = json_receipt("resume-v2-result.json")
    final = completion.get("result", {})
    require(final.get("status") ==
            "LIVE_GROUP_CHAIN_COMPLETED_AFTER_READONLY_RECONCILIATION"
            and final.get("saveConfirmed") is True
            and final.get("originalSourceSha256Unchanged") is True
            and final.get("unchangedInventoryGuidCount") == 44
            and final.get("port") == LIVE.PORT,
            "PREVIOUS_NATIVE_CHAIN_NOT_FULLY_VERIFIED")
    require(LIVE.canonical_path(preflight.get("scratchPath", "")) ==
            LIVE.canonical_path(SCOPE)
            and LIVE.canonical_path(final.get("scratchProject", "")) ==
            LIVE.canonical_path(SCOPE),
            "HISTORICAL_SCRATCH_SCOPE_NOT_MATCHING")
    source_hash = preflight.get("sourceSha256")
    require(isinstance(source_hash, str) and len(source_hash) == 64,
            "ORIGINAL_SOURCE_HASH_NOT_PINNED")
    live_project = LIVE.guard(SCOPE, source_hash)
    require(SCOPE.is_file(), "SAVED_SCRATCH_PLN_NOT_FOUND")
    group = create.get("groupId", {}).get("guid", "")
    members = preflight.get("sourceColumnGuids")
    require(bool(LIVE.GUID.fullmatch(group)) and isinstance(members, list)
            and len(members) == 2 and
            all(LIVE.GUID.fullmatch(x) for x in members),
            "SOURCE_NATIVE_GROUP_RECEIPT_INCOMPLETE")
    return preflight, final, live_project, group, members, source_hash


class ReadOnlyApi:
    def __init__(self):
        self.allowed = set(READ_COMMANDS)
        self.calls = []

    def __call__(self, command, params):
        require(command in READ_COMMANDS,
                "LIVE_READONLY_TRANSPORT_FORBIDS_COMMAND:" + str(command))
        require(isinstance(params, dict), "LIVE_READONLY_TYPED_PARAMS_REQUIRED")
        self.calls.append(command)
        return LIVE.request(command, params, addon=not command.startswith("API."))


class ReadOnlyBinding:
    """Provides ONLY the project identity interface, never SceneWriter writes."""

    def __init__(self, api, expected_sha):
        self.api = api
        self.expected_sha = expected_sha

    def guarded_binding(self):
        original = LIVE.guard(SCOPE, self.expected_sha)
        version = self.api("GetAddOnVersion", {}).get("version")
        require(version == APA.RUN.EXPECTED_TAPIR,
                "LIVE_READONLY_TAPIR_VERSION_UNEXPECTED")
        return {
            "path": original["projectPath"],
            "name": original["projectName"],
            "port": LIVE.PORT,
            "tapirVersion": version,
            "storyIndex": 0
        }


def source_members_and_story(api, group, claimed, inventory):
    member_ids = LIVE.elements_of_group(group)
    lower = lambda vals: {x.lower() for x in vals}
    require(lower(member_ids) == lower(claimed) and len(set(lower(member_ids))) == 2,
            "LIVE_SOURCE_NATIVE_GROUP_MEMBERSHIP_CHANGED")
    require(lower(member_ids).issubset(lower(inventory)),
            "LIVE_SOURCE_GROUP_MEMBERS_NOT_IN_SAVED_PLN")
    rows = LIVE.batched("GetDetailsOfElements", claimed, "detailsOfElements")
    require(all(isinstance(x, dict) and x.get("type") == "Column" for x in rows),
            "LIVE_GROUP_SOURCE_IS_NOT_EXACT_TWO_COLUMNS")
    originals = LIVE.batched("GetSubelementsOfHierarchicalElements",
                             claimed, "subelements")
    child_ids = []
    require(len(originals) == 2, "NATIVE_HIERARCHY_ROW_COUNT_MISMATCH")
    for row in originals:
        require(isinstance(row, dict) and set(row) == {"columnSegments"},
                "LIVE_GROUP_HAS_UNQUALIFIED_STRUCTURAL_DEPENDENCIES")
        children = row["columnSegments"]
        require(isinstance(children, list) and len(children) == 1,
                "LIVE_SOURCE_NATIVE_COLUMN_SEGMENT_MISSING")
        child = children[0].get("elementId", {}).get("guid")
        require(isinstance(child, str) and LIVE.GUID.fullmatch(child),
                "LIVE_NATIVE_CHILD_GUID_NOT_READABLE")
        child_ids.append(child)
    require(len(lower(child_ids)) == 2 and lower(child_ids).issubset(lower(inventory)),
            "LIVE_NATIVE_CHILDREN_DUPLICATED_OR_MISSING")
    child_rows = LIVE.batched("GetDetailsOfElements", child_ids, "detailsOfElements")
    require(all(isinstance(x, dict) and x.get("type") == "ColumnSegment"
                for x in child_rows), "LIVE_NATIVE_CHILD_TYPE_UNVERIFIED")

    # Home story is taken from the actual installed native ModelDump V1,
    # never guessed from the current open view's actStory index.
    dump = api("GetModelDumpV1", {})
    require(dump.get("regenerated3D") is True
            and dump.get("coordinateSystem") == "ABSOLUTE_PROJECT_XYZ",
            "LIVE_NATIVE_BREP_NOT_REGENERATED_ABSOLUTE")
    elems = {
        x["guid"].lower(): x for x in dump.get("elements", [])
        if isinstance(x, dict) and isinstance(x.get("guid"), str)
    }
    kinds = []
    for guid in claimed:
        entry = elems.get(guid.lower())
        require(isinstance(entry, dict) and entry.get("type") == "Column"
                and type(entry.get("homeStory")) is int,
                "LIVE_NATIVE_GROUP_STORY_NOT_VERIFIED:" + guid)
        kinds.append(entry["homeStory"])
    require(len(set(kinds)) == 1 and kinds[0] == 0,
            "LIVE_NATIVE_SOURCE_STORY_CHANGED_FROM_TEST")
    for child, parent in zip(child_ids, claimed):
        entry = elems.get(child.lower())
        require(isinstance(entry, dict) and entry.get("type") == "ColumnSegment"
                and entry.get("relationships", {}).get("hostGuid", "").lower() ==
                parent.lower(), "NATIVE_CHILD_OWNER_NOT_VERIFIED:" + child)
    return kinds[0], child_ids


def publish(report):
    raw = (json.dumps(report, sort_keys=True, ensure_ascii=False, indent=2)
           + "\n").encode("utf8")
    # One immutable independent report; do not replay any native calls to
    # force a desired outcome after an unexpected result.
    if REPORT_LOCAL.is_file():
        saved = REPORT_LOCAL.read_bytes()
        require(json.loads(saved) == report, "EXISTING_LOCAL_REPORT_CANNOT_BE_REPLACED")
    else:
        REPORT_LOCAL.write_bytes(raw)
    try:
        old, _ = MAILBOX.read_file(READONLY_REPORT)
    except Exception as exc:
        if "404" not in str(exc) and "Not Found" not in str(exc):
            raise
    else:
        require(old == report, "GITHUB_REPORT_ALREADY_EXISTS_DIFFERENT_CONTENT")
        return "EXISTING_GITHUB_RECEIPT"
    import base64
    response = MAILBOX.gh(
        f"repos/{LIVE.BRIDGE}/contents/{READONLY_REPORT}",
        put={
            "message": "AC29 native group-first automatic real model read-only check",
            "branch": LIVE.MAILBOX_BRANCH,
            "content": base64.b64encode(raw).decode("ascii")
        }
    )
    require(response.get("content", {}).get("sha") == MAILBOX.git_blob(raw),
            "GITHUB_REPORT_PUBLICATION_NOT_VERIFIED")
    return "PUBLISHED"


def run():
    require(not REPORT_LOCAL.is_file(),
            "REPORT_ALREADY_EXISTS_NO_REPEATED_LIVE_ACCEPTANCE")
    branch = subprocess.run(
        ["git", "-C", str(ROOT), "branch", "--show-current"],
        check=True, capture_output=True, text=True
    ).stdout.strip()
    require(branch == BRANCH, "LOCAL_APA_ROUTER_BRANCH_NOT_INSTALLED")
    dirty = subprocess.run(
        ["git", "-C", str(ROOT), "status", "--porcelain"],
        check=True, capture_output=True, text=True
    ).stdout.strip()
    require(not dirty, "LOCAL_APA_ROUTER_WORKTREE_DIRTY")
    original, previous, project, group, members, original_sha = result_identity()
    scratch_hash_before = LIVE.digest(SCOPE)
    api = ReadOnlyApi()
    product = api("API.GetProductInfo", {})
    require(product.get("version") == 29, "ARCHICAD_29_PORT_CHANGED")
    ids = LIVE.read_elements()
    require(len(ids) == 44, "LIVE_SCRATCH_MODEL_GUID_COUNT_CHANGED")
    story, native_children = source_members_and_story(api, group, members, ids)
    member_bounds = LIVE.boxes(members)
    require(len(member_bounds) == 2 and all(isinstance(x, dict) for x in member_bounds),
            "LIVE_NATIVE_SOURCE_COLUMNS_UNBOUNDED")
    existing_bounds = LIVE.boxes(ids)
    obstacles, excluded, restored = LIVE.classify_collision_obstacles(ids, existing_bounds)
    translations, unused_move = LIVE.offsets_for_pair(member_bounds, obstacles)
    source_ref = "APA_AC29_ACCEPTED_NATIVE_SOURCE_" + original_sha[:24]
    existing, targets = [], []
    for member, bbox in zip(members, member_bounds):
        family_signature = "EXACT_COPY_OF_NATIVE_GUID_" + member.lower()
        anchor = {k: bbox[k + "Min"] for k in ("x", "y", "z")}
        existing.append({
            "guid": member,
            "type": "Column",
            "familySignature": family_signature,
            "storyIndex": story,
            "anchor": anchor,
            "nativeReadbackVerified": True,
        })
        for offset in translations:
            targets.append({
                "type": "Column", "familySignature": family_signature,
                "storyIndex": story,
                "anchor": {k: round(anchor[k] + offset["d" + k], 6)
                           for k in ("x", "y", "z")},
                "sourceRef": source_ref,
            })
    intent = {
        "schemaVersion": "apa-native-group-auto/1",
        "request": "Read-only automatic group-first choice for saved scratch AC29 columns",
        "existing": existing, "targets": targets,
        "assemblyGroups": [{
            "sourceRef": source_ref,
            "memberGuids": members,
            "placements": translations,
            "sameStory": True,
            "dependenciesVerified": True,
            "existingGroupGuid": group,
            "groupReadbackVerified": True
        }]
    }
    router = ROUTER.DynamicCommands(CONTRACTS.load_catalog(ROOT / "tapir-1.5.8.json"))
    APA.connect_functional_modules(router)  # existing code-owned SDK contracts
    checked = APA.prepare_current_runtime_group_native_task(
        router, ReadOnlyBinding(api, original_sha), intent)
    plan = checked["preview"]
    steps = plan["selectedNativeTaskPreview"]["workflow"]["graph"]["operations"]
    require(plan["status"] == "ONE_SOURCE_QUALIFIED_STRATEGY_PREPARED"
            and plan["groupedTargetCount"] == 4
            and plan["individuallyRoutedTargetCount"] == 0
            and plan["nativeWritePermission"] is False
            and plan["automaticNativeExecution"] is False
            and len(steps) == 1
            and steps[0]["command"].endswith("CloneNativeGroupV1")
            and steps[0]["params"]["groupId"]["guid"].lower() == group.lower()
            and steps[0]["params"]["translations"] == translations
            and checked["runtimeRegisteredCommands"] == [steps[0]["command"]],
            "APA_REAL_NATIVE_GROUP_NOT_SELECTED_WITH_ZERO_WRITES")
    require(LIVE.canonical_path(LIVE.project()["projectPath"]) ==
            LIVE.canonical_path(SCOPE), "PROJECT_IDENTITY_CHANGED_DURING_READ")
    require(LIVE.digest(SCOPE) == scratch_hash_before,
            "SAVED_TEST_PLN_CHANGED_DURING_READONLY_SELECTION")
    require(LIVE.digest(LIVE.SOURCE_PATH) == original_sha,
            "ORIGINAL_TEST_PLN_CHANGED_DURING_READONLY_SELECTION")
    return {
        "schema": "APA_AC29_GROUP_REAL_MODEL_AUTOSELECT_READONLY_V1",
        "status": "LIVE_READONLY_GROUP_STRATEGY_SELECTED_PASS",
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "sourceGitRevision": subprocess.run(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"], check=True,
            capture_output=True, text=True
        ).stdout.strip(),
        "port": LIVE.PORT,
        "projectPath": project["projectPath"],
        "verifiedSourceGroupId": group,
        "sourceNativeColumns": 2,
        "sourceNativeColumnSegments": len(native_children),
        "modelGuidCount": len(ids),
        "selectionMethod": "GROUP_FIRST_FULL_ASSEMBLY",
        "selectedCommand": steps[0]["command"],
        "selectedOffsets": translations,
        "targetNativeColumns": len(targets),
        "selectedNativeCallsIfAuthorized": plan["nativeCallCountIfAuthorized"],
        "individualElementCopiesSelected": plan["individuallyRoutedTargetCount"],
        "currentRuntimeProbes": checked["runtimeRegisteredCommands"],
        "native3DBodiesChecked": len(obstacles),
        "verifiedNonspatialElementsExcluded": len(excluded),
        "hierarchicalNativeBoundsReconstructed": len(restored),
        "sourcePlnUnchanged": True,
        "scratchSavedPlnUnchanged": True,
        "modelWrites": 0,
        "saveCalls": 0,
        "writeAuthorization": False,
        "executionPreparedButNotPerformed": True,
        "actualSourceFamilyEquivalence": "EXACT_SAME_SOURCE_GUID_NATIVE_COPY",
        "sceneWriterMutationRoute": "NOT_EXERCISED",
        "speedRanking": "NOT_MEASURED"
    }


if __name__ == "__main__":
    try:
        report = run()
        print("APA_AC29_LIVE_GROUP_AUTOSELECT:", report["status"], flush=True)
        print("CURRENT_RUNTIME:", report["currentRuntimeProbes"], flush=True)
        print("CHOSEN:", report["selectedCommand"], flush=True)
        print("GROUP_COPY_COUNT:", report["targetNativeColumns"], flush=True)
        print("NEW_NATIVE_WRITES: 0, SAVE_CALLS: 0", flush=True)
        print("GITHUB_RECEIPT:", publish(report), flush=True)
    except Exception as error:
        print("APA_AC29_GROUP_AUTOSELECT_STOPPED:",
              type(error).__name__, str(error)[-1000:], flush=True)
        sys.exit(2)
