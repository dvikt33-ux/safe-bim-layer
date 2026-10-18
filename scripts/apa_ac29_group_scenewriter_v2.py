"""One-shot V2 of APA AC29 SceneWriter group acceptance after independent forensic.

The original failed attempt #01 is IMMUTABLE and never retried. All V2 model
writes go to a distinct disposable PLN, distinct SQLite scene and journal.
The previous failure must be independently reconciled with an immutable
local AND GitHub receipt and fresh live BREP before any project switch.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import apa_ac29_group_scenewriter_live as ORIGINAL
import apa_ac29_group_scenewriter_reconcile_readonly as FORENSIC
import apa_ac29_group_acceptance_mailbox as LIVE
import apa_ac29_apx_build_mailbox as MAILBOX
import archicad_project_accelerator as APA
import archicad_dynamic_commands as DYNAMIC
import apa_ac29_native_group_clone_verifier as VERIFIER

ORIGINAL_SCENE = ORIGINAL.SCENE
ORIGINAL_STATE = ORIGINAL.STATE
ORIGINAL_SCRATCH = ORIGINAL.SCRATCH
ORIGINAL_REMOTE = ORIGINAL.REMOTE
V2_SCENE = "GroupCloneWriter29_20261018_02"
V2_STATE = Path(r"C:\LocalAI\APA_AC29_Group_SceneWriter_State\scene-writer-20261018-02")
V2_SCRATCH = Path(r"C:\LocalAI\APA_Group_Acceptance\group-ac29-scene-writer-20261018-02.pln")
V2_REMOTE = ("safe-bim-mailbox/apa-ac29-group-acceptance/results/"
             "group-scenewriter-native-clone-20261018-02.json")
V2_AUTHORIZATION = "USER_APPROVED_AC29_GROUP_SCENEWRITER_NEW_SCRATCH_20261018_02"

EXPECTED_FORENSIC = "WRITER_PRE_DISPATCH_STOP_AND_LIVE_NATIVE_BASELINE_PASS"


def require(ok, reason):
    if not ok:
        raise RuntimeError(reason)


def prove_prior_no_write():
    """Read-only gate; does not open/modify/save any project."""
    require(ORIGINAL_SCENE != V2_SCENE and
            ORIGINAL_SCRATCH != V2_SCRATCH and
            ORIGINAL_STATE != V2_STATE and
            ORIGINAL_REMOTE != V2_REMOTE,
            "V2_REQUIRES_FRESH_SCENE_PLN_LEDGER_AND_RECEIPT")
    require(not V2_SCRATCH.exists() and not V2_STATE.exists(),
            "V2_PREVIOUS_ATTEMPT_MUST_NEVER_REPLAY")
    prior_failed = ORIGINAL.read_json(ORIGINAL_STATE / "result.json")
    require(prior_failed.get("result", {}).get("error") ==
            "ValueError: DYNAMIC_PROVIDER_VERSION_DRIFT" and
            prior_failed.get("scenario") == ORIGINAL_SCENE,
            "V1_DIFFERENT_FAILURE_OR_OUTCOME")
    local = ORIGINAL.read_json(FORENSIC.REPORT)
    remote, _ = MAILBOX.read_file(FORENSIC.REMOTE)
    require(remote == local and
            local.get("schema") ==
            "APA_AC29_GROUP_SCENEWRITER_NO_WRITE_RECONCILIATION_V1" and
            local.get("status") == EXPECTED_FORENSIC and
            local.get("priorScenario") == ORIGINAL_SCENE and
            local.get("acceptedGuidCount") == 44 and
            local.get("writerNativeMutationDispatches") == 0 and
            local.get("sqliteSceneEntries") == 0 and
            local.get("sqliteStepEntries") == 0 and
            local.get("nativeModelWritesFromThisStoppedWriter") == 0 and
            local.get("nativeBrepSignaturesMatchPreWriteTrace") is True and
            local.get("savedScratchUnchanged") is True and
            local.get("originalFunctionalTestPlnUnchanged") is True,
            "NO_WRITE_FORENSIC_GITHUB_AND_LOCAL_RECEIPTS_NOT_IDENTICAL_PASS")
    require(local.get("currentProject", "").lower() ==
            str(ORIGINAL_SCRATCH).lower() and
            local.get("port") == LIVE.PORT and
            local.get("modelWriteReplayAuthorized") is False,
            "HISTORICAL_RECONCILIATION_SCOPE_OR_PERMISSION_DRIFT")
    copied = ORIGINAL.read_json(ORIGINAL_STATE / "copied.json")
    original_functional_sha = ORIGINAL.read_json(
        ORIGINAL.HISTORY / "preflight.json")["sourceSha256"]
    require(local["savedScratchSourceSha256"] ==
            copied["sourceSavedSha256"] and
            LIVE.digest(ORIGINAL.SOURCE) == copied["sourceSavedSha256"] and
            LIVE.digest(ORIGINAL_SCRATCH) == copied["sourceSavedSha256"] and
            LIVE.digest(LIVE.SOURCE_PATH) == original_functional_sha,
            "ACCEPTED_ORIGINAL_FILES_CHANGED_AFTER_FORENSIC")
    LIVE.guard(ORIGINAL_SCRATCH, original_functional_sha)
    current = sorted(x.lower() for x in LIVE.read_elements())
    require(len(current) == 44 and len(set(current)) == 44,
            "LIVE_PREVIOUS_SCENE_INVENTORY_CHANGED")
    saved_traces = FORENSIC.records(
        ORIGINAL_STATE / "trace" / "raw.jsonl")
    native = [
        item["response"] for item in saved_traces
        if item["command"] == "GetModelDumpV1"
        and isinstance(item.get("response"), dict)
        and "error" not in item["response"]
    ]
    require(bool(native), "V1_PRE_WRITE_BREP_NOT_RECORDED")
    before = FORENSIC.native_signatures(native[-1], current)
    after = FORENSIC.native_signatures(
        LIVE.request("GetModelDumpV1", {}, addon=True, timeout=180),
        current)
    require(before == after, "NATIVE_BREP_CHANGED_SINCE_PRIOR_FORENSIC")
    group = ORIGINAL.read_json(
        ORIGINAL.HISTORY / "group-autoselect-real-model-readonly-20261018-01.json"
    )["verifiedSourceGroupId"]
    member_ids = {x.lower() for x in LIVE.elements_of_group(group)}
    require(member_ids == set(local["sourceGroupMembersRetained"]),
            "PREVIOUS_NATIVE_SOURCE_GROUP_CHANGED")
    require(LIVE.request("GetAddOnVersion", {}, addon=True).get("version") ==
            "1.5.10", "CURRENT_TAPIR_VERSION_CHANGED")
    return {
        "previousScene": ORIGINAL_SCENE,
        "previousNativeGuidCount": 44,
        "previousNativeWrites": 0,
        "previousReconciliationStatus": EXPECTED_FORENSIC,
        "v2Target": str(V2_SCRATCH),
        "v2Scene": V2_SCENE,
        "v2WritesAlreadyPerformed": 0
    }


def verify_complete_native_preflight_against_old_scratch():
    """Run the entire group-specific BREP/collision preflight read-only.

    This is deliberately BEFORE opening a new scratch PLN or creating its
    one-shot state. All command calls are hard-denied unless read-only.
    """
    class ReadOnlyApi:
        allowed = {"API.GetProductInfo", "API.IsAddOnCommandAvailable",
                   "GetAllElements", "GetDetailsOfElements",
                   "GetModelDumpV1", "GetAddOnVersion", "GetProjectInfo",
                   "GetStories", "GetNativeGroupMembersV1"}

        def __call__(self, command, params):
            require(command in self.allowed,
                    "GROUP_V2_PREFLIGHT_FORBIDS_NATIVE_MUTATION:" + command)
            return LIVE.request(command, params,
                                addon=not command.startswith("API."),
                                timeout=180)

    api = ReadOnlyApi()
    source_sha = LIVE.digest(ORIGINAL.SOURCE)
    original_sha = ORIGINAL.read_json(
        ORIGINAL.HISTORY / "preflight.json")["sourceSha256"]
    router = DYNAMIC.DynamicCommands(APA.catalog_with_provenance(
        ORIGINAL.ROOT / "schemas/tapir-live-1.5.10/tapir-scene-live.json"))
    APA.connect_functional_modules(router)
    group = ORIGINAL.read_json(
        ORIGINAL.HISTORY /
        "group-autoselect-real-model-readonly-20261018-01.json"
    )["verifiedSourceGroupId"]
    intent, native, before_ids = ORIGINAL.native_intent(
        api, router, group, source_sha)
    require(len(before_ids) == 44, "V2_FULL_NATIVE_SOURCE_COUNT_CHANGED")
    class GuardedReadOnlyBinding:
        def __init__(self):
            self.api = api

        def guarded_binding(self):
            info = LIVE.guard(ORIGINAL_SCRATCH, original_sha)
            require(api("GetAddOnVersion", {}).get("version") == "1.5.10",
                    "V2_RUNTIME_TAPIR_VERSION_CHANGED")
            return {"path": info["projectPath"],
                    "name": info["projectName"],
                    "port": LIVE.PORT,
                    "tapirVersion": "1.5.10",
                    "storyIndex": 0}
    prepared = APA.prepare_current_runtime_group_native_task(
        router, GuardedReadOnlyBinding(), intent)
    plan = prepared["preview"]
    require(plan.get("status") == "ONE_SOURCE_QUALIFIED_STRATEGY_PREPARED"
            and plan.get("groupedTargetCount") == 4
            and plan.get("individuallyRoutedTargetCount") == 0
            and plan.get("nativeWritePermission") is False,
            "V2_NATIVE_GROUP_AUTOMATIC_PLAN_NOT_VERIFIED")
    steps = plan["selectedNativeTaskPreview"]["workflow"]["graph"]["operations"]
    require(len(steps) == 1 and
            steps[0]["command"] == VERIFIER.CMD and
            steps[0]["params"]["groupId"]["guid"].lower() == group.lower() and
            steps[0]["params"]["translations"] == list(ORIGINAL.OFFSET),
            "V2_GROUP_PLAN_COMMAND_OR_OFFSETS_CHANGED")
    proof = VERIFIER.verify_before(
        api=api, command=steps[0]["command"],
        parameters=steps[0]["params"],
        affected=[], native_before=native)
    require(proof.get("status") ==
            "GROUP_CLONE_SOURCE_OWNED_NATIVE_BREP_AND_LAYOUT_PASS",
            "V2_SOURCE_SPECIFIC_FULL_BREP_COLLISION_PREFLIGHT_NOT_PASS")
    require(LIVE.digest(ORIGINAL_SCRATCH) == source_sha and
            LIVE.digest(ORIGINAL.SOURCE) == source_sha and
            LIVE.digest(LIVE.SOURCE_PATH) == original_sha,
            "V2_PREVIEW_CHANGED_ANY_SAVED_SOURCE")
    return {"nativeGuidCount": len(before_ids),
            "sourceGroup": group,
            "liveNativeCommand": steps[0]["command"],
            "cloneTranslations": steps[0]["params"]["translations"],
            "sourceReadback": proof["status"],
            "nativeWrites": 0,
            "sourcePlnUnchanged": True}


def configure_original_one_shot_to_new_scope():
    """Only reuse the established code-owned original SceneWriter ROUTE."""
    ORIGINAL.SCENE = V2_SCENE
    ORIGINAL.STATE = V2_STATE
    ORIGINAL.SCRATCH = V2_SCRATCH
    ORIGINAL.REMOTE = V2_REMOTE
    ORIGINAL.AUTH_REF = V2_AUTHORIZATION


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    require(args.execute, "V2_REQUIRES_SEPARATE_EXPLICIT_EXECUTE")
    ORIGINAL.require_local_branch()
    proof = prove_prior_no_write()
    verified = verify_complete_native_preflight_against_old_scratch()
    print("APA_GROUP_SCENEWRITER_V2_SOURCE_PREFLIGHT:",
          verified["sourceReadback"], "0 NATIVE WRITES", flush=True)
    print("APA_GROUP_SCENEWRITER_V2_GUARD:", proof["previousReconciliationStatus"],
          "44 GUID, 0 PRIOR WRITES", flush=True)
    configure_original_one_shot_to_new_scope()
    # The original code creates STATE via mkdir(exist_ok=False) and refuses
    # any existing receipt or scratch file; it cannot replay this attempt.
    return ORIGINAL.main()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print("APA_GROUP_SCENEWRITER_V2_STOPPED_BEFORE_CREATE_OR_WRITE:",
              type(exc).__name__, str(exc)[-1000:], flush=True)
        sys.exit(2)
