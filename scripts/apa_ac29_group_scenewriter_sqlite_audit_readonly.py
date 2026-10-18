"""Independent read-only SQLite/transport audit of ACCEPTED AC29 SceneWriter V2.

No Archicad connection, no SDK/native operation, no SaveProject/OpenProject,
no replay, no SQL writes. Reads existing SQLite via mode=ro, existing
EvidenceAPI trace, immutable local/remote acceptance receipt and disk hashes.
Publishes ONLY an audit JSON on its own fresh GitHub mailbox path.
"""
from __future__ import annotations

from datetime import datetime, timezone
from contextlib import closing
import base64
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

import apa_ac29_apx_build_mailbox as MAILBOX

SCENE = "GroupCloneWriter29_20261018_02"
COMMAND = "AddOn.TapirCommand.CloneNativeGroupV1"
ROOT = Path(r"C:\LocalAI\APA_AC29_Group_SceneWriter_State\scene-writer-20261018-02")
SCRATCH = Path(r"C:\LocalAI\APA_Group_Acceptance\group-ac29-scene-writer-20261018-02.pln")
SOURCE = Path(r"C:\LocalAI\APA_Group_Acceptance\group-ac29-assembly-20261018-04.pln")
ORIGINAL = Path(r"C:\LocalAI\APA_Functional_Test_House_01.pln")
RECEIPT_REMOTE = (
    "safe-bim-mailbox/apa-ac29-group-acceptance/results/"
    "group-scenewriter-native-clone-20261018-02.json"
)
AUDIT_REMOTE = (
    "safe-bim-mailbox/apa-ac29-group-acceptance/results/"
    "group-scenewriter-native-clone-20261018-02-sqlite-audit.json"
)
AUDIT_LOCAL = ROOT / "sqlite-independent-audit.json"
READS = frozenset({
    "GetProjectInfo", "GetStories", "GetAddOnVersion", "GetAllElements",
    "Get3DBoundingBoxes", "GetDetailsOfElements", "GetModelDumpV1",
    "GetNativeGroupMembersV1", "GetNativeGroupRootsV1",
    "GetSubelementsOfHierarchicalElements", "GetAPARuntimeInfoV1",
    "API.IsAddOnCommandAvailable", "API.GetProductInfo",
    "GetAttributesByType", "GetCurrentWindowType", "GetNavigatorItemTree"
})


def require(condition, reason):
    if not condition:
        raise RuntimeError(reason)


def read_json(path):
    require(path.is_file(), "AUDIT_REQUIRED_LOCAL_RECORD_MISSING:" + str(path))
    return json.loads(path.read_text(encoding="utf8"))


def file_hash(path):
    require(path.is_file(), "AUDIT_SAVED_FILE_MISSING:" + str(path))
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            h.update(block)
    return h.hexdigest()


def jsonl(path):
    require(path.is_file(), "AUDIT_DISPATCH_TRACE_MISSING:" + str(path))
    rows = []
    for i, line in enumerate(path.read_text(encoding="utf8").splitlines()):
        require(bool(line.strip()), "AUDIT_BLANK_TRACE_ROW:" + str(i))
        value = json.loads(line)
        require(isinstance(value, dict) and
                isinstance(value.get("command"), str),
                "AUDIT_TRACE_RECORD_NOT_VALID:" + str(i))
        rows.append(value)
    require(bool(rows), "AUDIT_TRACE_EMPTY")
    return rows


def sqlite_rows(path):
    require(path.is_file(), "AUDIT_ORIGINAL_SCENEWRITER_SQLITE_MISSING")
    # URI mode=ro: independent readers never create, delete or alter the
    # existing SQLite schema, rows, WAL or transaction state.
    with closing(sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)) as db:
        db.execute("PRAGMA query_only = ON")
        require(db.execute("PRAGMA quick_check").fetchone()[0] == "ok",
                "AUDIT_SQLITE_INTEGRITY_FAILED")
        names = {
            row[0] for row in db.execute(
                "SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        }
        require({"scenes", "steps"} <= names,
                "AUDIT_SCENEWRITER_TABLES_MISSING")
        scenes = db.execute(
            "SELECT scene_id,plan_hash,state,result FROM scenes"
        ).fetchall()
        steps = db.execute(
            "SELECT scene_id,step_id,state,guid,output FROM steps"
        ).fetchall()
    return scenes, steps


def unique_guids(raw, expected):
    require(isinstance(raw, list) and len(raw) == expected,
            "AUDIT_EXPECTED_GUID_LIST_COUNT_MISMATCH")
    require(all(isinstance(x, str) and len(x) == 36 for x in raw),
            "AUDIT_INVALID_GUID_FORMAT")
    values = [x.lower() for x in raw]
    require(len(set(values)) == expected, "AUDIT_DUPLICATE_GUIDS")
    return set(values)


def verify_evidence(receipt, before, scenes, steps, dispatch, trace):
    """Pure validation: usable in CI without local files or Archicad."""
    require(receipt.get("schema") == "APA_AC29_GROUP_SCENEWRITER_ACCEPTANCE_V1"
            and receipt.get("scenario") == SCENE,
            "AUDIT_WRONG_RECEIPT_SCENARIO")
    done = receipt.get("result")
    require(isinstance(done, dict)
            and done.get("status") == "LIVE_SCENEWRITER_NATIVE_GROUP_CLONE_PASS"
            and done.get("scratchProject", "").lower() == str(SCRATCH).lower()
            and done.get("baseGuidCount") == 44
            and done.get("postGuidCount") == 52
            and done.get("nativeMutationCalls") == 1
            and done.get("nativeModelWritesFromAddOn") == 4
            and done.get("createdGroupCount") == 2
            and done.get("createdRootCount") == 4
            and done.get("sceneWriterOriginalWorkflow") ==
            "WORKFLOW_CALLABLE_VERIFIED"
            and done.get("verifierId") == "VerifiedNativeGroupClone"
            and done.get("saveCalls") == 0
            and done.get("automaticRetry") is False
            and done.get("uncommittedScratchPlnChanges") is True,
            "AUDIT_ACCEPTED_RECEIPT_NOT_EXACT_GROUP_CLONE")
    require(isinstance(before, dict)
            and before.get("sceneId") == SCENE
            and before.get("command") == COMMAND
            and before.get("scratchPath", "").lower() == str(SCRATCH).lower()
            and before.get("automaticRetry") is False
            and before.get("repositoryRevision") == done.get("sourceRevision"),
            "AUDIT_PRE_DISPATCH_INTENT_NOT_BOUND")
    parameters = before.get("parameters")
    require(isinstance(parameters, dict) and
            parameters.get("groupId", {}).get("guid", "").lower() ==
            done["sourceGroupId"].lower() and
            parameters.get("translations") ==
            [{"dx": 25, "dy": 0, "dz": 0}, {"dx": 50, "dy": 0, "dz": 0}],
            "AUDIT_NATIVE_GROUP_OR_OFFSETS_DRIFT")
    require(len(scenes) == 1 and len(steps) == 1,
            "AUDIT_SQLITE_EXACT_ONE_SCENE_AND_ONE_STEP_REQUIRED")
    sid, plan_hash, status, raw = scenes[0]
    ssid, step_id, state, step_guid, step_raw = steps[0]
    require(sid == ssid == SCENE and
            status == state == "PASS" and step_id == "operation" and
            step_guid is None,
            "AUDIT_SQLITE_SCENE_AND_OPERATION_NOT_PASS")
    result = json.loads(raw)
    step = json.loads(step_raw)
    require(result == step and
            result.get("status") == "PASS" and
            result.get("sceneId") == SCENE and
            result.get("command") == COMMAND and
            result.get("operationHash") == plan_hash and
            result.get("automaticRetry") is False,
            "AUDIT_SQLITE_SCENE_RESULT_STEP_OR_HASH_MISMATCH")
    intent = result.get("intent")
    require(isinstance(intent, dict) and
            intent.get("sceneId") == SCENE and
            intent.get("command") == COMMAND and
            intent.get("parameters") == parameters and
            intent.get("target", {}).get("path", "").lower() ==
            str(SCRATCH).lower() and
            intent.get("target", {}).get("port") == 19724,
            "AUDIT_SQLITE_INTENT_TARGET_NOT_PINNED")
    require(isinstance(dispatch, list) and isinstance(trace, list)
            and len(dispatch) == len(trace),
            "AUDIT_TRACE_DISPATCH_AND_RESPONSE_COUNT_MISMATCH")
    require(all(a.get("command") == b.get("command") and
                a.get("parameters") == b.get("parameters")
                for a, b in zip(dispatch, trace)),
            "AUDIT_TRACE_COMMAND_OR_PARAMETERS_DRIFT")
    unknown = [r["command"] for r in dispatch
               if r.get("command") not in READS | {COMMAND}]
    require(not unknown, "AUDIT_UNAPPROVED_NATIVE_DISPATCH:" + str(unknown))
    writes = [row for row in trace if row["command"] == COMMAND]
    require(len(writes) == 1
            and "error" not in writes[0]
            and isinstance(writes[0].get("response"), dict),
            "AUDIT_EXACTLY_ONE_SUCCESSFUL_GROUP_NATIVE_DISPATCH_REQUIRED")
    native = result.get("nativeResponse")
    require(native == writes[0]["response"] and
            native.get("nativeModelWrites") == 4 and
            native.get("sourceGroupId", {}).get("guid", "").lower() ==
            done["sourceGroupId"].lower(),
            "AUDIT_SQLITE_NATIVE_RESPONSE_NOT_EQUAL_TRANSPORT_TRACE")
    group_ids = unique_guids(
        [x["guid"] for x in native.get("newGroupIds", [])], 2)
    root_ids = unique_guids(
        [x["elementId"]["guid"] for x in native.get("createdElements", [])], 4)
    independent = result.get("readback")
    require(isinstance(independent, dict) and
            independent.get("status") ==
            "GROUP_CLONE_SCENEWRITER_NATIVE_BREP_GUID_READBACK_PASS" and
            independent.get("originalNativeGuidCount") == 44 and
            independent.get("finalNativeGuidCount") == 52 and
            independent.get("originalGroupUnchanged") is True and
            independent.get("allNativeRootsAndChildrenVerified") is True,
            "AUDIT_SQLITE_INDEPENDENT_NATIVE_BREP_READBACK_NOT_PASS")
    checked_roots = unique_guids(independent.get("newRootGuids"), 4)
    segments = unique_guids(independent.get("newSegmentGuids"), 4)
    checked_groups = unique_guids(independent.get("newGroupGuids"), 2)
    require(checked_roots == root_ids and
            checked_groups == group_ids and
            not checked_roots.intersection(segments),
            "AUDIT_NEW_NATIVE_GROUP_PARENT_SEGMENT_OWNERSHIP_DRIFT")
    return {
        "scene": SCENE, "sqlSceneState": status,
        "sqlStepState": state,
        "sqlJournalRows": len(scenes) + len(steps),
        "transportTraceRows": len(trace),
        "nativeMutationDispatches": len(writes),
        "createdRootCount": len(root_ids),
        "createdSegmentCount": len(segments),
        "createdNativeGroups": len(group_ids),
        "nativeGuidCountBefore": 44, "nativeGuidCountAfter": 52,
        "verifierReadbackStatus": independent["status"],
        "nativeResponseMatchesLoggedTransport": True
    }


def audit():
    require(not AUDIT_LOCAL.exists(), "AUDIT_RECEIPT_ALREADY_EXISTS_DO_NOT_OVERWRITE")
    receipt = read_json(ROOT / "result.json")
    remote, _ = MAILBOX.read_file(RECEIPT_REMOTE)
    require(receipt == remote, "AUDIT_LOCAL_AND_GITHUB_ACCEPTANCE_RECEIPTS_DIFFER")
    before = read_json(ROOT / "before-native-dispatch.json")
    copied = read_json(ROOT / "copied.json")
    require(before["originalAcceptedSourceSha256"] ==
            copied["sourceSavedSha256"] ==
            file_hash(SOURCE) == file_hash(SCRATCH),
            "AUDIT_TEST_PLN_SOURCE_OR_SCRATCH_SAVED_BYTES_CHANGED")
    require(before["sourceFunctionalTestSha256"] == file_hash(ORIGINAL),
            "AUDIT_FUNCTIONAL_SOURCE_PLN_CHANGED")
    dbfile = ROOT / "original-scenewriter.sqlite"
    before_sql_hash = file_hash(dbfile)
    scenes, steps = sqlite_rows(dbfile)
    recorded = verify_evidence(
        receipt, before, scenes, steps,
        jsonl(ROOT / "trace" / "dispatch.jsonl"),
        jsonl(ROOT / "trace" / "raw.jsonl"))
    require(file_hash(dbfile) == before_sql_hash,
            "AUDIT_SQLITE_CHANGED_WHILE_BEING_READ")
    return {
        "schema": "APA_AC29_GROUP_SCENEWRITER_SQLITE_AUDIT_V1",
        "status": "SCENEWRITER_SQLITE_INDEPENDENT_AUDIT_PASS",
        "at": datetime.now(timezone.utc).isoformat(),
        "acceptance": recorded,
        "sqliteSHA256": before_sql_hash,
        "sourceRevision": remote["result"]["sourceRevision"],
        "testScratchSavedFileUnchanged": True,
        "originalFunctionalTestPlnUnchanged": True,
        "savedAcceptedSourcePlnUnchanged": True,
        "sqliteMode": "READ_ONLY",
        "archicadCalls": 0,
        "nativeModelWrites": 0,
        "saveCalls": 0,
        "previousNativeMutationNeverRetried": True
    }


def publish(report):
    require(not AUDIT_LOCAL.exists(), "AUDIT_IMMUTABLE_LOCAL_REPORT_ALREADY_EXISTS")
    # Fail closed on an already published remote. This is a one-time audit.
    try:
        prior, _ = MAILBOX.read_file(AUDIT_REMOTE)
    except Exception as exc:
        require("404" in str(exc) or "Not Found" in str(exc),
                "AUDIT_REMOTE_RECEIPT_LOOKUP_FAILED")
    else:
        raise RuntimeError("AUDIT_GITHUB_RECEIPT_ALREADY_EXISTS:" +
                           str(prior.get("status")))
    MAILBOX.save(AUDIT_LOCAL, report)
    raw = (json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2)
           + "\n").encode("utf8")
    received = MAILBOX.gh(
        f"repos/{MAILBOX.BRIDGE}/contents/{AUDIT_REMOTE}",
        put={"message": "APA AC29 V2 independent read-only original SQLite acceptance",
             "branch": MAILBOX.BRANCH,
             "content": base64.b64encode(raw).decode("ascii")}
    )
    require(received.get("content", {}).get("sha") == MAILBOX.git_blob(raw),
            "AUDIT_GITHUB_RECEIPT_PUBLICATION_NOT_VERIFIED")
    return "PUBLISHED"


def main():
    try:
        result = audit()
        print("APA_SCENEWRITER_SQLITE:", result["status"], flush=True)
        print("SQL_ROWS:", result["acceptance"]["sqlJournalRows"],
              "NATIVE_DISPATCHES:", result["acceptance"]["nativeMutationDispatches"],
              "NEW_GUIDS:", result["acceptance"]["nativeGuidCountAfter"] -
                           result["acceptance"]["nativeGuidCountBefore"], flush=True)
        print("GITHUB_RECEIPT:", publish(result), flush=True)
    except Exception as exc:
        print("APA_SCENEWRITER_SQLITE_AUDIT_STOPPED:",
              type(exc).__name__, str(exc)[-1200:], flush=True)
        sys.exit(2)


if __name__ == "__main__":
    main()
