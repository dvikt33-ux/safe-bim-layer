"""One-shot AC29 APA group clone through ORIGINAL SceneWriter, isolated PLN.

Scope is pinned: existing accepted source scratch PLN on port 19724, new
disposable distinct scratch path, one native CloneNativeGroupV1 execution,
the existing APA DynamicCommands, NativeVerifier, dynamic scope builder,
SQLite SceneWriter ledger and full BREP readback.

Never writes to BDD, main, source scratch or original functional test PLN.
Never automatically retries a native command, switches source projects
without exact identity proof, or saves the clone without a separate approval.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import base64
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import time

import archicad_scene_run as RUN
import archicad_project_accelerator as APA
import archicad_dynamic_commands as DYNAMIC
import archicad_batch_contracts as CONTRACTS
import archicad_bim_documentation as DOC
import archicad_connected_components as C
import apa_ac29_multi_prototype_native_copy as M
import apa_ac29_group_acceptance_mailbox as LIVE
import apa_ac29_apx_build_mailbox as MAILBOX
from apa_ac29_dynamic_native_verifiers import installed_verifiers
from apa_ac29_dynamic_write_scopes import build_existing_workflow_scopes

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(r"C:\LocalAI\APA_Group_Acceptance\group-ac29-assembly-20261018-04.pln")
SCRATCH = Path(r"C:\LocalAI\APA_Group_Acceptance\group-ac29-scene-writer-20261018-01.pln")
HISTORY = Path(r"C:\LocalAI\APA_AC29_Group_Acceptance_State\group-ac29-assembly-20261018-04")
STATE = Path(r"C:\LocalAI\APA_AC29_Group_SceneWriter_State\scene-writer-20261018-01")
BRANCH = "feature/apa-ac29-group-scenewriter-live-20261018"
SCENE = "GroupCloneWriter29_20261018_01"
SOURCE_REF = "https://github.com/dvikt33-ux/safe-bim-layer/pull/162"
AUTH_REF = "USER_APPROVED_AC29_GROUP_SCENEWRITER_TEST_20261018"
OFFSET = ({"dx": 25, "dy": 0, "dz": 0}, {"dx": 50, "dy": 0, "dz": 0})
REMOTE = (
    "safe-bim-mailbox/apa-ac29-group-acceptance/results/"
    "group-scenewriter-native-clone-20261018-01.json"
)


def need(ok, why):
    if not ok:
        raise RuntimeError(why)


def read_json(path):
    need(path.is_file(), "REQUIRED_PRIOR_RECEIPT_NOT_FOUND:" + str(path))
    return json.loads(path.read_text(encoding="utf8"))


def immutable_report(report):
    STATE.mkdir(parents=True, exist_ok=True)
    destination = STATE / "result.json"
    if destination.is_file():
        need(read_json(destination) == report,
             "LOCAL_FINAL_RECEIPT_CANNOT_BE_REPLACED")
    else:
        MAILBOX.save(destination, report)


def publish_existing():
    report = read_json(STATE / "result.json")
    raw = (json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2)
           + "\n").encode("utf8")
    try:
        previous, _ = MAILBOX.read_file(REMOTE)
    except Exception as exc:
        if "404" not in str(exc) and "Not Found" not in str(exc):
            raise
    else:
        need(previous == report, "REMOTE_RECEIPT_DIFFERENT_BLOCKED")
        return "EXISTING_GITHUB_RECEIPT"
    response = MAILBOX.gh(
        f"repos/{LIVE.BRIDGE}/contents/{REMOTE}",
        put={
            "message": "AC29 original SceneWriter native group clone acceptance 01",
            "branch": LIVE.MAILBOX_BRANCH,
            "content": base64.b64encode(raw).decode("ascii")
        }
    )
    need(response.get("content", {}).get("sha") == MAILBOX.git_blob(raw),
         "GITHUB_SCENEWRITER_RECEIPT_PUBLICATION_NOT_VERIFIED")
    return "PUBLISHED"


def verify_previous():
    completion = read_json(HISTORY / "resume-v2-result.json").get("result", {})
    success = "LIVE_GROUP_CHAIN_COMPLETED_AFTER_READONLY_RECONCILIATION"
    need(completion.get("status") == success
         and completion.get("saveConfirmed") is True
         and completion.get("originalSourceSha256Unchanged") is True
         and completion.get("scratchProject", "").lower() == str(SOURCE).lower(),
         "PREVIOUS_NATIVE_ACCEPTANCE_SUCCESS_RECEIPT_MISSING")
    selected = read_json(HISTORY / "group-autoselect-real-model-readonly-20261018-01.json")
    need(selected.get("status") == "LIVE_READONLY_GROUP_STRATEGY_SELECTED_PASS"
         and selected.get("sourcePlnUnchanged") is True
         and selected.get("scratchSavedPlnUnchanged") is True
         and selected.get("modelWrites") == 0
         and selected.get("saveCalls") == 0
         and selected.get("selectedCommand") == "AddOn.TapirCommand.CloneNativeGroupV1"
         and selected.get("selectedOffsets") == list(OFFSET)
         and selected.get("modelGuidCount") == 44,
         "PREVIOUS_AUTOSELECT_NATIVE_ACCEPTANCE_MISSING")
    original_sha = read_json(HISTORY / "preflight.json")["sourceSha256"]
    LIVE.guard(SOURCE, original_sha)
    need(LIVE.digest(LIVE.SOURCE_PATH) == original_sha,
         "PROTECTED_TEST_ORIGINAL_HASH_CHANGED")
    need(LIVE.digest(SOURCE), "PROTECTED_SAVED_ACCEPTED_SCRATCH_MISSING")
    return selected, original_sha


def require_local_branch():
    branch = subprocess.run(
        ["git", "-C", str(ROOT), "branch", "--show-current"],
        check=True, capture_output=True, text=True
    ).stdout.strip()
    need(branch == BRANCH, "GROUP_WRITER_DIFFERENT_LOCAL_BRANCH")
    revision = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True
    ).stdout.strip()
    changes = subprocess.run(
        ["git", "-C", str(ROOT), "status", "--porcelain"],
        check=True, capture_output=True, text=True
    ).stdout.strip()
    need(len(revision) == 40 and not changes, "GROUP_WRITER_UNPINNED_LOCAL_WORKTREE")
    return revision


def create_and_open_copy(source_sha, original_sha):
    need(not SCRATCH.exists(), "TEST_CLONE_PLN_ALREADY_EXISTS_NO_RETRY")
    shutil.copy2(SOURCE, SCRATCH)
    need(LIVE.digest(SCRATCH) == source_sha, "NEW_SCRATCH_BYTES_DIFFER")
    MAILBOX.save(STATE / "copied.json", {
        "at": datetime.now(timezone.utc).isoformat(),
        "sourceSavedSha256": source_sha,
        "newScratchPath": str(SCRATCH),
        "automaticRetry": False
    })
    # Project switching is never model mutation, but may trigger a user UI
    # prompt for unsaved edits. Only exact new identity authorizes writes.
    try:
        reply = LIVE.request("OpenProject", {"projectFilePath": str(SCRATCH)},
                             addon=True, timeout=90)
        need(reply.get("success") is True, "SCRATCH_OPEN_NATIVE_REJECTED")
    except Exception:
        pass
    for _ in range(20):
        try:
            LIVE.guard(SCRATCH, original_sha)
            return
        except Exception:
            time.sleep(2)
    raise RuntimeError("OPENED_PROJECT_NOT_EXACT_NEW_SCRATCH_NO_MODEL_WRITES")


def native_intent(api, router, group, source_sha):
    members = [g.lower() for g in LIVE.elements_of_group(group)]
    need(len(members) == 2 and len(set(g.lower() for g in members)) == 2,
         "GROUP_WRITER_SOURCE_NATIVE_GROUP_CHANGED")
    ids = APA.inventory_guids(api)
    need(len(ids) == 44, "GROUP_WRITER_SOURCE_GUID_INVENTORY_NOT_44")
    native = DOC.capture_full_model(api, ids)
    nodes = {row["guid"].lower(): row for row in native["elements"]}
    need(set(nodes) == set(ids), "GROUP_WRITER_FULL_NATIVE_BASELINE_MISSING")
    details = M.SINGLE.column_details(api, members)
    sources, targets = [], []
    for guid in members:
        guid = guid.lower()
        row = details[guid]
        part = row["details"]
        anchor = {"x": part["origin"]["x"],
                  "y": part["origin"]["y"],
                  "z": part["zCoordinate"]}
        children = M.owned_children(nodes, guid, "Column")
        need(row.get("floorIndex") == 0 and nodes[guid].get("homeStory") == 0,
             "GROUP_WRITER_HOME_STORY_UNVERIFIED")
        family = APA.RUN.digest({
            "typed": M.source_detail_fingerprint(row, "Column", anchor),
            "native": M.solid_fingerprint(
                nodes[guid], children, anchor, parent_guid=guid)
        })
        sources.append({
            "guid": guid, "type": "Column",
            "familySignature": family, "storyIndex": 0,
            "anchor": anchor, "nativeReadbackVerified": True
        })
        for translation in OFFSET:
            targets.append({
                "type": "Column", "familySignature": family,
                "storyIndex": 0,
                "anchor": {
                    axis: round(anchor[axis] + translation["d" + axis], 6)
                    for axis in ("x", "y", "z")
                },
                "sourceRef": SOURCE_REF
            })
    intent = {
        "schemaVersion": "apa-native-group-auto/1",
        "request": "Copy exactly one proven original native group on isolated writer PLN",
        "existing": sources, "targets": targets,
        "assemblyGroups": [{
            "sourceRef": SOURCE_REF,
            "memberGuids": sorted(g.lower() for g in members),
            "placements": list(OFFSET),
            "sameStory": True,
            "dependenciesVerified": True,
            "existingGroupGuid": group,
            "groupReadbackVerified": True
        }]
    }
    need(LIVE.digest(SCRATCH) == source_sha,
         "GROUP_WRITER_TEST_SCRATCH_FILE_CHANGED_BEFORE_PLAN")
    return intent, native, ids


def execute_once(revision, selected, original_sha):
    import hashlib
    need(LIVE.canonical_path(LIVE.project()["projectPath"]) ==
         LIVE.canonical_path(SCRATCH), "SCRATCH_SWITCHED_BEFORE_WRITE")
    source_sha = read_json(STATE / "copied.json")["sourceSavedSha256"]
    RUN.bind_authorized_saved_copy(
        LIVE.PORT, str(SCRATCH), SCRATCH.stem, source_sha, AUTH_REF
    )
    folder = STATE / "trace"
    folder.mkdir(exist_ok=True, parents=True)
    api = APA.EvidenceAPI(APA.native_transport, folder, execute=False)
    writer = RUN.SceneWriter(
        api, journal_path=STATE / "original-scenewriter.sqlite",
        allow_3d_view_for_write=True
    )
    router = DYNAMIC.DynamicCommands(
        CONTRACTS.load_catalog(ROOT / "tapir-1.5.8.json"))
    APA.connect_functional_modules(router)
    binding = writer.guarded_binding()
    need(LIVE.canonical_path(binding["path"]) ==
         LIVE.canonical_path(SCRATCH),
         "SCENEWRITER_NOT_BOUND_TO_DISPOSABLE_PLN")
    intent, baseline_native, ids = native_intent(
        api, router, selected["verifiedSourceGroupId"], source_sha
    )
    live = APA.prepare_current_runtime_group_native_task(router, writer, intent)
    preview = live["preview"]
    graph = preview["selectedNativeTaskPreview"]["workflow"]
    commands = graph["graph"]["operations"]
    need(len(commands) == 1
         and commands[0]["command"] == "AddOn.TapirCommand.CloneNativeGroupV1"
         and commands[0]["params"]["translations"] == list(OFFSET)
         and commands[0]["params"]["groupId"]["guid"].lower() ==
         selected["verifiedSourceGroupId"].lower()
         and len(ids) == 44
         and preview["groupedTargetCount"] == 4
         and preview["individuallyRoutedTargetCount"] == 0,
         "APA_SOURCE_QUALIFIED_AUTO_GROUP_PLAN_DRIFT")
    registry = installed_verifiers()
    need("VerifiedNativeGroupClone" in registry,
         "SCENEWRITER_CODE_OWNED_GROUP_VERIFIER_NOT_INSTALLED")
    model = DOC.capture_full_model(api, ids)
    actual = {r["guid"].lower(): r for r in model["elements"]}
    need(set(actual) == set(ids), "SCOPE_MODEL_GUID_SET_INCOMPLETE")
    source_snapshot = {
        g: C.ROOF.geometry_signature(actual[g]) for g in sorted(ids)
    }
    need(
        APA.RUN.digest(source_snapshot) ==
        APA.RUN.digest({g: C.ROOF.geometry_signature(
            {r["guid"].lower(): r for r in baseline_native["elements"]}[g])
                        for g in sorted(ids)}),
        "SCENEWRITER_BREP_CHANGED_DURING_PREVIEW"
    )
    spec = {
        "schemaVersion": "apa-ac29-dynamic-mutation-scope/1",
        "projectSha256": source_sha,
        "sourcePlanHash": graph["sourcePlanHash"],
        "authorizationRef": AUTH_REF,
        "sourceEvidenceRef": SOURCE_REF,
        "sceneId": SCENE,
        "stepId": commands[0]["id"],
        "command": commands[0]["command"],
        "effect": "CREATE", "impact": "MODEL",
        "commandContractHash": router.contract_hash(commands[0]["command"]),
        "parametersHash": APA.RUN.digest(commands[0]["params"]),
        "expectedBeforeGuidSetHash": APA.RUN.digest(sorted(ids)),
        "expectedBeforeNativeBrepHash": APA.RUN.digest(source_snapshot),
        "affectedGuids": [],
        "retainedGuids": sorted(ids),
        "verifierId": "VerifiedNativeGroupClone"
    }
    journal = writer.journal_path
    # Existing SceneWriter writes its real ledger; create the two tables only
    # so the existing scoped-workflow ledger checker can read empty history.
    need(not journal.exists(), "SCENEWRITER_JOURNAL_ALREADY_EXISTS_NO_RETRY")
    with sqlite3.connect(journal) as db:
        db.execute(
            "CREATE TABLE scenes (scene_id TEXT PRIMARY KEY,"
            "plan_hash TEXT NOT NULL, state TEXT NOT NULL, result TEXT NOT NULL)"
        )
        db.execute(
            "CREATE TABLE steps (scene_id TEXT NOT NULL, step_id TEXT NOT NULL,"
            "state TEXT NOT NULL, guid TEXT, output TEXT NOT NULL,"
            "PRIMARY KEY(scene_id,step_id))"
        )
        db.commit()
    scopes = build_existing_workflow_scopes(
        spec=spec, plan=graph, router=router, registry=registry,
        writer=writer, api=api,
        capture_model=DOC.capture_full_model,
        guid_inventory=APA.inventory_guids,
        current_project_sha=lambda: LIVE.digest(SCRATCH),
        approved_project_sha=source_sha,
        local_authorization=AUTH_REF
    )
    # Durable intent exists before the first native model write. No retry even
    # on transport timeout, SQLite failure or false readback.
    MAILBOX.save(STATE / "before-native-dispatch.json", {
        "sceneId": SCENE,
        "scratchPath": str(SCRATCH),
        "originalAcceptedSourceSha256": source_sha,
        "sourceFunctionalTestSha256": original_sha,
        "exactWorkflowSourceHash": graph["sourcePlanHash"],
        "command": commands[0]["command"],
        "parameters": commands[0]["params"],
        "authorization": AUTH_REF,
        "repositoryRevision": revision,
        "automaticRetry": False,
        "at": datetime.now(timezone.utc).isoformat()
    })
    result = APA.run_auto_optimized_native_task(
        router, api, preview, writer, scopes
    )
    need(result.get("status") == "WORKFLOW_CALLABLE_VERIFIED"
         and len(result.get("trace", [])) == 1,
         "SCENEWRITER_GROUP_WORKFLOW_NOT_FULLY_VERIFIED")
    entry = result["results"][commands[0]["id"]]
    need(len(entry["newGroupIds"]) == 2
         and len(entry["createdElements"]) == 4,
         "SCENEWRITER_GROUP_NATIVE_RESPONSE_NOT_EXACT")
    need(LIVE.digest(SCRATCH) == source_sha,
         "SAVED_SCRATCH_DISK_CHANGED_DURING_UNSAVED_NATIVE_CLONE")
    need(LIVE.digest(SOURCE) == read_json(STATE / "copied.json")["sourceSavedSha256"],
         "PROTECTED_SOURCE_SCRATCH_DISK_CHANGED")
    need(LIVE.digest(LIVE.SOURCE_PATH) == original_sha,
         "PROTECTED_FUNCTIONAL_TEST_SOURCE_DISK_CHANGED")
    ids_after = APA.inventory_guids(api)
    need(len(ids_after) == 52, "GROUP_SCENEWRITER_44_PLUS_EIGHT_INVENTORY_REQUIRED")
    need(api.write_attempts == 1,
         "GROUP_WRITER_EXPECTED_EXACTLY_ONE_NATIVE_MUTATION")
    return {
        "status": "LIVE_SCENEWRITER_NATIVE_GROUP_CLONE_PASS",
        "sourceRevision": revision,
        "port": LIVE.PORT, "scratchProject": str(SCRATCH),
        "baseGuidCount": 44, "postGuidCount": 52,
        "nativeModelWrites": 1, "saveCalls": 0,
        "originalSourcePlnUnchanged": True,
        "previousAcceptedScratchUnchanged": True,
        "scratchSavedFileUnchangedUnsavedModel": True,
        "sourceGroupId": selected["verifiedSourceGroupId"],
        "createdRootCount": len(entry["createdElements"]),
        "createdGroupCount": len(entry["newGroupIds"]),
        "sceneWriterOriginalSqliteJournal": str(journal),
        "sceneWriterOriginalWorkflow": "WORKFLOW_CALLABLE_VERIFIED",
        "verifierId": "VerifiedNativeGroupClone",
        "automaticRetry": False,
        "uncommittedScratchPlnChanges": True,
        "note": "Native grouped copy verified through original SceneWriter; "
                "test PLN has unsaved changes and was NOT saved."
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--execute", action="store_true")
    args = p.parse_args()
    need(args.execute, "MUTATION_REQUIRES_EXPLICIT_EXECUTE_FLAG")
    revision = require_local_branch()
    # A previous uncertain attempt must NEVER be repeated or overwritten.
    if (STATE / "result.json").exists():
        need(False, "PREVIOUS_RESULT_ALREADY_EXISTS_NO_MODEL_RETRY")
    need(not STATE.exists() and not SCRATCH.exists(),
         "PREVIOUS_ATTEMPT_OR_DISPOSABLE_PLN_ALREADY_EXISTS_NO_RETRY")
    _, original_sha = verify_previous()
    source_sha = LIVE.digest(SOURCE)
    STATE.mkdir(parents=True, exist_ok=False)
    MAILBOX.save(STATE / "attempted.json", {
        "sourceRevision": revision,
        "sourceProject": str(SOURCE),
        "destinationProject": str(SCRATCH),
        "sourceSha256": source_sha,
        "at": datetime.now(timezone.utc).isoformat(),
        "automaticRetry": False
    })
    try:
        create_and_open_copy(source_sha, original_sha)
        selected = read_json(
            HISTORY / "group-autoselect-real-model-readonly-20261018-01.json"
        )
        report = execute_once(revision, selected, original_sha)
    except Exception as exc:
        report = {
            "status": "STOPPED_NO_AUTOMATIC_RETRY_MANUAL_RECONCILIATION",
            "error": type(exc).__name__ + ": " + str(exc)[-1400:],
            "modelWritesMayHaveOccurred": (
                (STATE / "before-native-dispatch.json").exists()
            ),
            "openedScratchProjectMayHaveUnsavedChanges": (
                (STATE / "before-native-dispatch.json").exists()
            ),
            "nativeCommandNeverRetried": True,
            "scratchPath": str(SCRATCH),
            "originalAcceptedSourcePlnSaveNotRequested": True
        }
    immutable_report({
        "schema": "APA_AC29_GROUP_SCENEWRITER_ACCEPTANCE_V1",
        "scenario": SCENE,
        "at": datetime.now(timezone.utc).isoformat(),
        "result": report
    })
    print("APA_AC29_SCENEWRITER_GROUP:", report["status"], flush=True)
    print("GITHUB_RECEIPT:", publish_existing(), flush=True)
    return 0 if report["status"] == "LIVE_SCENEWRITER_NATIVE_GROUP_CLONE_PASS" else 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print("APA_AC29_SCENEWRITER_FATAL:",
              type(exc).__name__, str(exc), flush=True)
        sys.exit(2)
