"""Forensic AC29 SceneWriter attempt #01: READ-ONLY, no model changes.

PROVES ONLY that the journaled APA attempt did not dispatch CloneNativeGroup
on the existing 19724 disposable scratch PLN, and that the complete native
model readback still matches the last pre-dispatch captured BREP. Independent
unlogged third-party/user changes cannot be excluded by telemetry alone.

Use only after DYNAMIC_PROVIDER_VERSION_DRIFT and BEFORE any new attempt.
No copy/open, native Create/Clone/Move/Ungroup/Save, retry, or SQL writes.
"""
from __future__ import annotations

from datetime import datetime, timezone
import base64
import json
from pathlib import Path
import sqlite3
import sys

import archicad_scene_run as RUN
import archicad_batch_contracts as CONTRACTS
import archicad_connected_components as C
import archicad_project_accelerator as APA
import apa_ac29_group_acceptance_mailbox as LIVE
import apa_ac29_apx_build_mailbox as MAILBOX
import apa_ac29_group_scenewriter_live as PREVIOUS

STATE = PREVIOUS.STATE
REPORT = STATE / "scene-writer-01-readonly-reconciliation.json"
REMOTE = ("safe-bim-mailbox/apa-ac29-group-acceptance/results/"
          "group-scenewriter-native-clone-20261018-01-readonly-reconciliation.json")
EXPECTED_STOP = "ValueError: DYNAMIC_PROVIDER_VERSION_DRIFT"
WRITE = "AddOn.TapirCommand.CloneNativeGroupV1"


def need(ok, code):
    if not ok:
        raise RuntimeError(code)


def records(path):
    need(path.is_file(), "SCENEWRITER_EVIDENCE_TRACE_MISSING:" + str(path))
    lines = path.read_text(encoding="utf8").splitlines()
    need(bool(lines), "SCENEWRITER_EVIDENCE_TRACE_EMPTY")
    values = []
    for index, line in enumerate(lines):
        try:
            row = json.loads(line)
        except ValueError as error:
            raise RuntimeError("SCENEWRITER_TRACE_RECORD_INVALID:" + str(index)) from error
        need(isinstance(row, dict) and isinstance(row.get("command"), str),
             "SCENEWRITER_TRACE_MISSING_COMMAND:" + str(index))
        values.append(row)
    return values


def provenance():
    receipt = PREVIOUS.read_json(STATE / "result.json")
    failed = receipt.get("result", {})
    need(receipt.get("schema") == "APA_AC29_GROUP_SCENEWRITER_ACCEPTANCE_V1"
         and failed.get("status") ==
         "STOPPED_NO_AUTOMATIC_RETRY_MANUAL_RECONCILIATION"
         and failed.get("error") == EXPECTED_STOP
         and receipt.get("scenario") == PREVIOUS.SCENE
         and failed.get("scratchPath", "").lower() ==
         str(PREVIOUS.SCRATCH).lower(), "DIFFERENT_STOPPED_WRITER_ATTEMPT")
    intent = PREVIOUS.read_json(STATE / "before-native-dispatch.json")
    copied = PREVIOUS.read_json(STATE / "copied.json")
    started = PREVIOUS.read_json(STATE / "attempted.json")
    require_same = lambda x, name: need(
        x.lower() == str(PREVIOUS.SCRATCH).lower(),
        "SCENEWRITER_PINNED_SCOPE_DRIFT:" + name)
    require_same(copied["newScratchPath"], "copied")
    require_same(intent["scratchPath"], "intent")
    require_same(started["destinationProject"], "attempt")
    need(intent["sceneId"] == PREVIOUS.SCENE
         and intent["command"] == WRITE
         and intent.get("automaticRetry") is False,
         "DIFFERENT_NATIVE_WRITE_INTENT")
    old_sha = PREVIOUS.read_json(PREVIOUS.HISTORY / "preflight.json")["sourceSha256"]
    need(copied["sourceSavedSha256"] == started["sourceSha256"]
         and intent["originalAcceptedSourceSha256"] == copied["sourceSavedSha256"]
         and intent["sourceFunctionalTestSha256"] == old_sha,
         "PREVIOUS_ORIGINAL_SOURCE_RECEIPTS_NOT_BOUND")
    need(LIVE.digest(PREVIOUS.SOURCE) == copied["sourceSavedSha256"]
         and LIVE.digest(PREVIOUS.SCRATCH) == copied["sourceSavedSha256"]
         and LIVE.digest(LIVE.SOURCE_PATH) == old_sha,
         "SOURCE_OR_SAVED_SCRATCH_SHA_DRIFT")
    LIVE.guard(PREVIOUS.SCRATCH, old_sha)
    return intent, copied, old_sha


def native_signatures(document, guids):
    normalized = C.G.normalize_dump(document)
    elements = {row["guid"].lower(): row for row in normalized["elements"]}
    need(set(elements) == set(guids) and len(normalized["elements"]) == len(guids),
         "PREVIOUS_OR_CURRENT_BREP_GUID_INVENTORY_INCOMPLETE")
    return C.retained_geometry_signatures(normalized, sorted(guids))


def run():
    need(not REPORT.exists(), "RECONCILIATION_RECEIPT_ALREADY_EXISTS_NO_RECHECK")
    intent, copied, old_sha = provenance()
    sqlite_file = STATE / "original-scenewriter.sqlite"
    need(sqlite_file.is_file(), "ORIGINAL_SCENEWRITER_JOURNAL_MISSING")
    with sqlite3.connect(
        f"file:{sqlite_file.as_posix()}?mode=ro", uri=True
    ) as db:
        scene_rows = db.execute("SELECT scene_id, state FROM scenes").fetchall()
        step_rows = db.execute("SELECT scene_id, step_id, state FROM steps").fetchall()
    need(not scene_rows and not step_rows,
         "SQLITE_ATTEMPT_WAS_ENTERED_CANNOT_DECLARE_NO_WRITE")
    dispatches = records(STATE / "trace" / "dispatch.jsonl")
    returns = records(STATE / "trace" / "raw.jsonl")
    mutating = [row["command"] for row in dispatches
                if row["command"] == WRITE
                or row["command"] in {
                    "SaveProject", "OpenProject", "MoveElements", "CreateColumns",
                    "CreateNativeGroupV1", "MoveNativeGroupV1", "UngroupNativeGroupV1",
                    "API.ExecuteAddOnCommand"
                } or row["command"].startswith("AddOn.")]
    need(not mutating, "NATIVE_WRITER_MUTATION_DISPATCH_ALREADY_RECORDED")
    expected_reads = [row for row in returns
                      if row["command"] == "GetModelDumpV1"
                      and isinstance(row.get("response"), dict)
                      and "error" not in row["response"]]
    need(bool(expected_reads), "PREWRITE_MODEL_DUMP_EVIDENCE_NOT_RECORDED")
    inventory = APA.inventory_guids(lambda name, params: LIVE.request(name, params,
                    addon=(name == "GetModelDumpV1")))
    need(len(inventory) == 44,
         "SAVED_SCRATCH_LIVE_GUID_COUNT_DIFFERS_FROM_ACCEPTED_44")
    last_capture = expected_reads[-1]["response"]
    baseline = native_signatures(last_capture, inventory)
    current = LIVE.request("GetModelDumpV1", {}, addon=True, timeout=180)
    after = native_signatures(current, inventory)
    need(baseline == after,
         "NATIVE_BREP_OR_RELATIONSHIPS_CHANGED_AFTER_FAILED_WRITER")
    initial = PREVIOUS.read_json(
        PREVIOUS.HISTORY / "group-autoselect-real-model-readonly-20261018-01.json")
    group = initial["verifiedSourceGroupId"]
    members = {v.lower() for v in LIVE.elements_of_group(group)}
    require_members = {v.lower() for v in
                       PREVIOUS.read_json(PREVIOUS.HISTORY / "preflight.json")["sourceColumnGuids"]}
    need(members == require_members and len(members) == 2,
         "ACCEPTED_GROUP_MEMBERSHIP_DRIFT")
    version = LIVE.request("GetAddOnVersion", {}).get("version")
    old_catalog = CONTRACTS.load_catalog(
        PREVIOUS.ROOT / "tapir-1.5.8.json")
    need(version == RUN.EXPECTED_TAPIR == "1.5.10"
         and CONTRACTS.source_version(old_catalog) == "1.5.8",
         "VERSION_MISMATCH_CAUSE_NOT_REPRODUCED_READ_ONLY")
    need(LIVE.digest(PREVIOUS.SCRATCH) == copied["sourceSavedSha256"],
         "TEST_SCRATCH_SAVED_FILE_CHANGED_DURING_READS")
    return {
        "schema": "APA_AC29_GROUP_SCENEWRITER_NO_WRITE_RECONCILIATION_V1",
        "status": "WRITER_PRE_DISPATCH_STOP_AND_LIVE_NATIVE_BASELINE_PASS",
        "at": datetime.now(timezone.utc).isoformat(),
        "priorScenario": PREVIOUS.SCENE,
        "priorError": EXPECTED_STOP,
        "currentProject": str(PREVIOUS.SCRATCH),
        "port": LIVE.PORT,
        "sqliteSceneEntries": len(scene_rows),
        "sqliteStepEntries": len(step_rows),
        "writerNativeMutationDispatches": len(mutating),
        "traceReadEntries": len(returns),
        "acceptedGuidCount": len(inventory),
        "nativeBrepSignaturesMatchPreWriteTrace": True,
        "sourceGroupMembersRetained": sorted(members),
        "savedScratchSourceSha256": copied["sourceSavedSha256"],
        "originalFunctionalTestPlnUnchanged": True,
        "savedScratchUnchanged": True,
        "originalRouterProviderVersion": "1.5.8",
        "liveTapirProviderVersion": version,
        "nativeModelWritesFromThisStoppedWriter": 0,
        "diagnosticNativeWrites": 0,
        "diagnosticSaveCalls": 0,
        "modelWriteReplayAuthorized": False,
        "otherActorsNotCovered": True,
        "automaticRetry": False
    }


def publish(report):
    raw = (json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2)
           + "\n").encode("utf8")
    if REPORT.is_file():
        need(json.loads(REPORT.read_text(encoding="utf8")) == report,
             "RECONCILIATION_LOCAL_RECEIPT_IMMUTABLE")
    else:
        MAILBOX.save(REPORT, report)
    try:
        previous, _ = MAILBOX.read_file(REMOTE)
    except Exception as exc:
        if "404" not in str(exc) and "Not Found" not in str(exc):
            raise
    else:
        need(previous == report, "GITHUB_FORENSIC_RECEIPT_DIFFERENT")
        return "ALREADY_PUBLISHED"
    response = MAILBOX.gh(
        f"repos/{LIVE.BRIDGE}/contents/{REMOTE}", put={
            "message": "AC29 group SceneWriter 01 read-only pre-dispatch forensic proof",
            "branch": LIVE.MAILBOX_BRANCH,
            "content": base64.b64encode(raw).decode("ascii")
        })
    need(response.get("content", {}).get("sha") == MAILBOX.git_blob(raw),
         "FORENSIC_GITHUB_RECEIPT_NOT_VERIFIED")
    return "PUBLISHED"


if __name__ == "__main__":
    try:
        if REPORT.is_file():
            print("APA_GROUP_SCENEWRITER_PREVIOUS_FORENSIC_RESULT:",
                  PREVIOUS.read_json(REPORT).get("status"), flush=True)
        else:
            result = run()
            print("APA_GROUP_SCENEWRITER_FORENSIC:", result["status"],
                  flush=True)
            print("NATIVE_MODEL_WRITES:", result["nativeModelWritesFromThisStoppedWriter"],
                  flush=True)
            print("GITHUB_RECEIPT:", publish(result), flush=True)
    except Exception as exc:
        print("APA_GROUP_SCENEWRITER_FORENSIC_STOPPED:",
              type(exc).__name__, str(exc)[-1500:], flush=True)
        sys.exit(2)
