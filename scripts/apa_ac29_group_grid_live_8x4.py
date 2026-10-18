"""Isolated AC29 8x4 native-group grid: STAGE -> CHECK -> ONE-SHOT EXECUTE.

STAGE: disk-only creates a never-before-used saved copy of accepted 44-GUID PLN.
CHECK: READ-ONLY preview and full native BREP collision preflight in a NEW,
       separately opened Archicad 29 instance (auto-find ONLY ports 19727..35).
EXECUTE: only after CHECK, current project/port/source hashes pinned, one
         CloneNativeGroupV1 through ORIGINAL APA/DynamicCommands/SceneWriter.
No project switching or SaveProject in ANY phase. Never touch the unsaved
previous #02 on 19724, hotlink work on 19726, BDD or main. No auto-retry.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sys
import time

import apa_ac29_group_acceptance_mailbox as LIVE
import apa_ac29_apx_build_mailbox as MAILBOX
import apa_ac29_group_scenewriter_live as ORIGINAL
import apa_ac29_native_group_grid as GRID
import apa_ac29_native_group_clone_verifier as VERIFIER
import archicad_scene_run as RUN
import archicad_project_accelerator as APA
import archicad_dynamic_commands as DYNAMIC
import archicad_bim_documentation as DOC

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ORIGINAL.SOURCE
PRIOR_SCRATCH = ORIGINAL.SCRATCH
SCRATCH = Path(r"C:\LocalAI\APA_Group_Acceptance\group-ac29-grid-8x4-20261018-01.pln")
STATE = Path(r"C:\LocalAI\APA_AC29_Group_Grid_State\group-grid-8x4-20261018-01")
BRANCH = "feature/apa-ac29-group-grid-live-20261018"
SCENE = "GroupGrid8x4Writer29_20261018_01"
SOURCE_REF = "https://github.com/dvikt33-ux/safe-bim-layer/pull/172"
AUTH_REF = "USER_APPROVED_AC29_GROUP_GRID_8X4_TEST_20261018"
REMOTE = ("safe-bim-mailbox/apa-ac29-group-acceptance/results/"
          "group-grid-8x4-scenewriter-20261018-01.json")
PRIOR_REMOTE = ("safe-bim-mailbox/apa-ac29-group-acceptance/results/"
                "group-scenewriter-native-clone-20261018-02-sqlite-audit.json")
GRID_RECIPE = dict(schema=GRID.SCHEMA, columns=8, rows=4, stepX=25,
                   stepY=8, startDx=25, startDy=0)
SHIFTS = GRID.grid_offsets(GRID_RECIPE)
PORT_RANGE = tuple(range(19727, 19736))
OLD_VERIFIED_GROUP = "40D5303F-18CA-4117-9DE0-E06BFD8E64B9"
EXPECTED_BASE_GUIDS = 44
EXPECTED_POST_GUIDS = 172


def require(ok, reason):
    if not ok:
        raise RuntimeError(reason)


def read(path):
    require(path.is_file(), "GROUP_GRID_REQUIRED_RECEIPT_MISSING:" + str(path))
    return json.loads(path.read_text(encoding="utf8"))


def previous_proof():
    """Past model is NEVER used as live input; merely prove accepted source."""
    receipt, _ = MAILBOX.read_file(PRIOR_REMOTE)
    require(receipt.get("status") ==
            "SCENEWRITER_SQLITE_INDEPENDENT_AUDIT_PASS"
            and receipt.get("acceptance", {}).get("nativeMutationDispatches") == 1
            and receipt["acceptance"]["nativeGuidCountBefore"] == 44
            and receipt["acceptance"]["nativeGuidCountAfter"] == 52
            and receipt.get("sourceRevision") ==
            "b921b205354fff609c62020a46d1edf1e46f1cb2"
            and receipt.get("saveCalls") == 0
            and receipt.get("archicadCalls") == 0,
            "GROUP_GRID_PARENT_SCENEWRITER_ACCEPTANCE_NOT_GITHUB_PROVEN")
    local_audit = read(Path(r"C:\LocalAI\APA_AC29_Group_SceneWriter_State"
                            r"\scene-writer-20261018-02\sqlite-independent-audit.json"))
    require(local_audit == receipt,
            "GROUP_GRID_PARENT_LOCAL_AND_GITHUB_AUDIT_DIFFER")
    history = read(ORIGINAL.HISTORY /
                   "group-autoselect-real-model-readonly-20261018-01.json")
    require(history.get("status") ==
            "LIVE_READONLY_GROUP_STRATEGY_SELECTED_PASS"
            and history.get("verifiedSourceGroupId", "").lower() ==
            OLD_VERIFIED_GROUP.lower()
            and history.get("modelGuidCount") == 44,
            "GROUP_GRID_SOURCE_GROUP_NOT_PREVIOUSLY_ACCEPTED")
    functional_sha = read(ORIGINAL.HISTORY / "preflight.json")["sourceSha256"]
    source_sha = LIVE.digest(SOURCE)
    require(LIVE.digest(LIVE.SOURCE_PATH) == functional_sha,
            "GROUP_GRID_PROTECTED_BDD_ORIGINAL_CHANGED")
    require(LIVE.digest(PRIOR_SCRATCH) == source_sha,
            "GROUP_GRID_PREVIOUS_WRITER_SAVED_SOURCE_DRIFT")
    # ORIGINAL.SCRATCH on importing V1 points to #01, saved and unchanged.
    require(len(source_sha) == 64, "GROUP_GRID_SOURCE_SHA_INVALID")
    return dict(functionalSha256=functional_sha,
                sourceSavedSha256=source_sha,
                sourceGroupId=OLD_VERIFIED_GROUP,
                priorSQLiteAuditSha256=receipt["sqliteSHA256"])


def configure_reused_writer():
    """Only runtime local constants for an entirely new disposable one-shot."""
    ORIGINAL.SCRATCH = SCRATCH
    ORIGINAL.STATE = STATE
    ORIGINAL.SCENE = SCENE
    ORIGINAL.BRANCH = BRANCH
    ORIGINAL.SOURCE_REF = SOURCE_REF
    ORIGINAL.AUTH_REF = AUTH_REF
    ORIGINAL.REMOTE = REMOTE
    ORIGINAL.OFFSET = tuple(SHIFTS)


def stage():
    revision = ORIGINAL.require_local_branch()
    require(not STATE.exists() and not SCRATCH.exists(),
            "GRID_STAGE_ALREADY_EXISTS_NO_OVERWRITE")
    require(SOURCE.is_file() and SOURCE != SCRATCH,
            "GRID_SOURCE_NOT_SAVED_OR_SAME_DESTINATION")
    past = previous_proof()
    STATE.mkdir(parents=True, exist_ok=False)
    try:
        SCRATCH.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(SOURCE, SCRATCH)
        require(LIVE.digest(SCRATCH) == past["sourceSavedSha256"],
                "GRID_NEW_SAVED_COPY_BYTES_NOT_IDENTICAL")
        MAILBOX.save(STATE / "stage.json", {
            "schema": "APA_AC29_GROUP_GRID_STAGE_V1",
            "status": "STAGED_SAVED_COPY_ONLY_NO_ARCHICAD_CALLS",
            "at": datetime.now(timezone.utc).isoformat(),
            "sourceRevision": revision,
            "sourceProject": str(SOURCE),
            "scratchProject": str(SCRATCH),
            "scene": SCENE,
            "grid": GRID_RECIPE,
            "shifts": SHIFTS,
            "expectedOriginalGuids": EXPECTED_BASE_GUIDS,
            "expectedPostGuids": EXPECTED_POST_GUIDS,
            "archicadCalls": 0, "nativeModelWrites": 0,
            "saveCalls": 0, "automaticRetry": False,
            **past
        })
    except Exception:
        # Fail-closed stage: never delete an ambiguous scratch or state.
        raise
    print("APA_GRID_STAGE: SAVED_COPY_ONLY_PASS", flush=True)
    print("OPEN_IN_NEW_ARCHICAD29_INSTANCE:", SCRATCH, flush=True)
    print("PROTECTED_PORTS: 19723..19726 (never used)", flush=True)
    print("NEXT: --check (read-only) after opening staged PLN", flush=True)


def staged():
    require(STATE.is_dir() and SCRATCH.is_file(),
            "GROUP_GRID_STAGE_REQUIRED_BEFORE_EXECUTION")
    stage_receipt = read(STATE / "stage.json")
    require(stage_receipt.get("schema") == "APA_AC29_GROUP_GRID_STAGE_V1"
            and stage_receipt.get("status") ==
            "STAGED_SAVED_COPY_ONLY_NO_ARCHICAD_CALLS"
            and stage_receipt.get("scratchProject") == str(SCRATCH)
            and stage_receipt.get("sourceProject") == str(SOURCE)
            and stage_receipt.get("grid") == GRID_RECIPE
            and stage_receipt.get("shifts") == SHIFTS
            and stage_receipt.get("scene") == SCENE
            and stage_receipt.get("expectedOriginalGuids") == 44
            and stage_receipt.get("expectedPostGuids") == 172,
            "GRID_STAGE_IMMUTABLE_SOURCE_OR_RECIPE_DRIFT")
    past = previous_proof()
    require(all(stage_receipt[k] == past[k] for k in past)
            and LIVE.digest(SCRATCH) == past["sourceSavedSha256"]
            and LIVE.digest(SOURCE) == past["sourceSavedSha256"],
            "GRID_STAGED_SAVED_PROJECT_SHA_DRIFT")
    return stage_receipt


def discover_dedicated_instance():
    """Only read identity; NEVER OpenProject or touch protected 19723–19726."""
    found = []
    original_port = LIVE.PORT
    try:
        for port in PORT_RANGE:
            LIVE.PORT = port
            try:
                info = LIVE.request("GetProjectInfo", {}, addon=True,
                                    timeout=2)
            except Exception:
                continue
            if (info.get("isUntitled") is False and
                    info.get("isTeamwork") is False and
                    LIVE.canonical_path(info.get("projectPath", "")) ==
                    LIVE.canonical_path(SCRATCH)):
                found.append((port, info))
        require(len(found) == 1,
                "GRID_EXACTLY_ONE_DEDICATED_INSTANCE_MUST_OPEN_STAGED_PLN:"
                + str(len(found)))
        port, info = found[0]
        require(port not in (19723, 19724, 19725, 19726),
                "GRID_PROTECTED_ARCHICAD_INSTANCE_DENIED")
        LIVE.PORT = port
        return port, info
    finally:
        if len(found) != 1:
            LIVE.PORT = original_port


def intent_factory(native_intent):
    """Replace only target expansion with the pure reviewed 8x4 grid."""
    base = native_intent["assemblyGroups"]
    require(len(base) == 1
            and len(base[0]["memberGuids"]) == 2
            and base[0]["existingGroupGuid"].lower() ==
            OLD_VERIFIED_GROUP.lower(),
            "GRID_ORIGINAL_NATIVE_SOURCE_GROUP_CHANGED")
    converted = GRID.build_group_grid_intent(
        native_intent["existing"], base[0], GRID_RECIPE,
        "One verified native group x 32 placements, original SceneWriter")
    require(converted["assemblyGroups"][0]["placements"] == SHIFTS
            and len(converted["targets"]) == 64,
            "GRID_TARGET_EXPANSION_NOT_EXACT")
    return converted


def read_only_check(*, require_new=True):
    stage_receipt = staged()
    port, info = discover_dedicated_instance()
    prior_functional_hash = stage_receipt["functionalSha256"]
    LIVE.guard(SCRATCH, prior_functional_hash)
    require(LIVE.request("GetAddOnVersion", {}, addon=True).get("version")
            == "1.5.10", "GRID_TAPIR_VERSION_NOT_ACCEPTED_1_5_10")
    RUN.bind_authorized_saved_copy(port, str(SCRATCH), SCRATCH.stem,
                                   stage_receipt["sourceSavedSha256"],
                                   AUTH_REF)
    if require_new:
        require(not (STATE / "attempted.json").exists()
                and not (STATE / "original-scenewriter.sqlite").exists()
                and not (STATE / "result.json").exists(),
                "GRID_NATIVE_ATTEMPT_ALREADY_EXISTS_NEVER_RETRY")
    router = DYNAMIC.DynamicCommands(APA.catalog_with_provenance(
        ROOT / "schemas/tapir-live-1.5.10/tapir-scene-live.json"))
    APA.connect_functional_modules(router)
    folder = STATE / "preflight-trace"
    folder.mkdir(parents=True, exist_ok=True)
    api = APA.EvidenceAPI(APA.native_transport, folder, execute=False)
    writer = RUN.SceneWriter(
        api, journal_path=STATE / "original-scenewriter.sqlite",
        allow_3d_view_for_write=True
    )
    bound = writer.guarded_binding()
    require(bound["port"] == port
            and LIVE.canonical_path(bound["path"]) ==
                LIVE.canonical_path(SCRATCH),
            "GRID_ORIGINAL_WRITER_NOT_BOUND_TO_DEDICATED_PLN")
    selected = read(ORIGINAL.HISTORY /
                    "group-autoselect-real-model-readonly-20261018-01.json")
    native_intent, native, original_guids = ORIGINAL.native_intent(
        api, router, selected["verifiedSourceGroupId"],
        stage_receipt["sourceSavedSha256"])
    require(len(original_guids) == 44, "GRID_NATIVE_44_GUID_BASELINE_DRIFT")
    intent = intent_factory(native_intent)
    checked = APA.prepare_current_runtime_group_native_task(
        router, writer, intent)
    plan = checked["preview"]
    require(plan["status"] == "ONE_SOURCE_QUALIFIED_STRATEGY_PREPARED"
            and plan["nativeWritePermission"] is False
            and plan["groupedTargetCount"] == 64
            and plan["individuallyRoutedTargetCount"] == 0
            and plan["nativeCallCountIfAuthorized"] == 1,
            "GRID_EXISTING_APA_AUTO_ROUTER_NOT_ONE_GROUP_CALL")
    operations = plan["selectedNativeTaskPreview"]["workflow"]["graph"]["operations"]
    require(len(operations) == 1
            and operations[0]["command"] == VERIFIER.CMD
            and operations[0]["params"]["translations"] == SHIFTS
            and operations[0]["params"]["groupId"]["guid"].lower() ==
                OLD_VERIFIED_GROUP.lower(),
            "GRID_ORIGINAL_APA_NATIVE_COMMAND_OR_SOURCE_DRIFT")
    proof = VERIFIER.verify_before(
        api=api, command=VERIFIER.CMD,
        parameters=operations[0]["params"], affected=[],
        native_before=native)
    require(proof["status"] ==
            "GROUP_CLONE_SOURCE_OWNED_NATIVE_BREP_AND_LAYOUT_PASS"
            and len(proof["offsets"]) == 32
            and api.write_attempts == 0,
            "GRID_32_NATIVE_BREP_COLLISION_PREFLIGHT_NOT_CLEARED")
    require(LIVE.digest(SCRATCH) == stage_receipt["sourceSavedSha256"]
            and LIVE.digest(SOURCE) == stage_receipt["sourceSavedSha256"],
            "GRID_FILE_SHA_CHANGED_DURING_READONLY_CHECK")
    return {
        "schema": "APA_AC29_GROUP_GRID_PREFLIGHT_V1",
        "status": "GRID_8X4_NATIVE_BREP_AND_RUNTIME_PREFLIGHT_PASS",
        "sourceRevision": stage_receipt["sourceRevision"],
        "scene": SCENE,
        "scratchPath": str(SCRATCH), "port": port,
        "originalSourceGuidCount": 44,
        "expectedGuidCountAfter": 172,
        "expectedRootCount": 64, "expectedGroupCount": 32,
        "nativeCallCountIfAuthorized": 1,
        "nativeReadbackStatus": proof["status"],
        "grid": GRID_RECIPE, "shifts": SHIFTS,
        "sourcePlnSha256": stage_receipt["sourceSavedSha256"],
        "sourceGroupId": OLD_VERIFIED_GROUP,
        "sourcePlanHash": plan["selectedNativeTaskPreview"]["workflow"]["sourcePlanHash"],
        "archicadWrites": 0, "saveCalls": 0,
        "automaticRetry": False
    }


def check():
    require(not (STATE / "preflight.json").exists(),
            "GRID_PREFLIGHT_ALREADY_RECORDED")
    report = read_only_check()
    MAILBOX.save(STATE / "preflight.json", report)
    print("APA_GRID_PREFLIGHT:", report["status"], flush=True)
    print("DEDICATED_PORT:", report["port"], flush=True)
    print("LIVE_NATIVE_WRITES: 0", flush=True)
    print("NEXT: --execute (one-shot only)", flush=True)


def execute():
    revision = ORIGINAL.require_local_branch()
    stage_receipt = staged()
    pinned = read(STATE / "preflight.json")
    require(pinned.get("status") ==
            "GRID_8X4_NATIVE_BREP_AND_RUNTIME_PREFLIGHT_PASS"
            and pinned.get("scene") == SCENE
            and pinned.get("sourceRevision") == revision
            and pinned.get("sourcePlnSha256") ==
                stage_receipt["sourceSavedSha256"],
            "GRID_MATCHING_SUCCESSFUL_READ_ONLY_PREFLIGHT_REQUIRED")
    require(not (STATE / "attempted.json").exists()
            and not (STATE / "result.json").exists()
            and not (STATE / "before-native-dispatch.json").exists()
            and not (STATE / "original-scenewriter.sqlite").exists(),
            "GRID_PREVIOUS_MUTATION_ATTEMPT_NEVER_REPLAY")
    live = read_only_check()
    require(live == pinned, "GRID_CURRENT_READONLY_PREFLIGHT_DRIFT")
    port = live["port"]
    previous_return = (ORIGINAL.execute_once, ORIGINAL.native_intent)
    # Safe runtime parameters: SOURCE/ORIGINAL/BDD identities are UNCHANGED.
    # We change only per-process copies of dedicated one-shot state constants.
    configure_reused_writer()
    original_native_intent = ORIGINAL.native_intent
    def reviewed_intent(api, router, group, sha):
        intent, native, ids = original_native_intent(api, router, group, sha)
        return intent_factory(intent), native, ids
    ORIGINAL.native_intent = reviewed_intent
    started = datetime.now(timezone.utc).isoformat()
    MAILBOX.save(STATE / "attempted.json", {
        "sourceRevision": revision, "sourceProject": str(SOURCE),
        "destinationProject": str(SCRATCH),
        "sourceSha256": stage_receipt["sourceSavedSha256"],
        "scene": SCENE, "port": port,
        "approvedOffsets": SHIFTS,
        "at": started, "automaticRetry": False
    })
    timer = time.perf_counter()
    try:
        selected = read(ORIGINAL.HISTORY /
                        "group-autoselect-real-model-readonly-20261018-01.json")
        report = ORIGINAL.execute_once(
            revision, selected, stage_receipt["functionalSha256"])
        report["fullWorkflowElapsedSeconds"] = round(time.perf_counter()-timer, 6)
        report["grid"] = GRID_RECIPE
        report["expectedGridPositions"] = 32
        report["expectedNewNativeGuids"] = 128
        raw = STATE / "trace" / "raw.jsonl"
        records = [json.loads(line) for line in raw.read_text(
            encoding="utf8").splitlines()]
        writes = [x for x in records if x.get("command") == VERIFIER.CMD]
        require(len(writes) == 1 and
                type(writes[0].get("elapsedSeconds")) in (int, float),
                "GRID_BENCHMARK_EXACTLY_ONE_NATIVE_LATENCY_MISSING")
        report["nativeRoundTripElapsedSeconds"] = writes[0]["elapsedSeconds"]
        require(report["postGuidCount"] == EXPECTED_POST_GUIDS
                and report["createdRootCount"] == 64
                and report["createdGroupCount"] == 32
                and report["nativeModelWritesFromAddOn"] == 64
                and report["nativeMutationCalls"] == 1
                and report["saveCalls"] == 0,
                "GRID_SCENEWRITER_NATIVE_32_GROUP_RESULT_INVALID")
        report["status"] = "LIVE_GRID_8X4_SCENEWRITER_NATIVE_GROUP_PASS"
    except Exception as exc:
        report = {
            "status": "GRID_STOPPED_UNKNOWN_OR_PARTIAL_OUTCOME_NO_RETRY",
            "error": type(exc).__name__ + ": " + str(exc)[-1400:],
            "modelWritesMayHaveOccurred":
                (STATE / "before-native-dispatch.json").exists(),
            "scene": SCENE, "port": port,
            "scratchProject": str(SCRATCH),
            "fullWorkflowElapsedSeconds": round(time.perf_counter()-timer, 6),
            "automaticRetry": False, "nativeCommandNeverRetried": True,
            "savedPlnNotWrittenByRunner": True
        }
    finally:
        ORIGINAL.native_intent = previous_return[1]
    ORIGINAL.immutable_report({
        "schema": "APA_AC29_GROUP_GRID_SCENEWRITER_V1",
        "scenario": SCENE,
        "at": datetime.now(timezone.utc).isoformat(),
        "result": report
    })
    print("APA_AC29_GROUP_GRID:", report["status"], flush=True)
    print("GITHUB_RECEIPT:", ORIGINAL.publish_existing(), flush=True)
    return 0 if report["status"] == \
        "LIVE_GRID_8X4_SCENEWRITER_NATIVE_GROUP_PASS" else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    opts = parser.add_mutually_exclusive_group(required=True)
    opts.add_argument("--stage", action="store_true")
    opts.add_argument("--check", action="store_true")
    opts.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    configure_reused_writer()
    if args.stage:
        return stage()
    if args.check:
        return check()
    return execute()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print("APA_GROUP_GRID_STOPPED:", type(exc).__name__,
              str(exc)[-1000:], flush=True)
        sys.exit(2)
