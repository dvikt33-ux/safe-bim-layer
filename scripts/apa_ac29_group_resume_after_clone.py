"""Resume ONLY remaining MOVE + UNGROUP on exact unsaved AC29 scratch PLN.

This is a manual one-shot continuation, NOT a replay of Create/Clone.
Before any modification the immutable original forensic read receipt must
exactly match a new live read, including all native hierarchy GUIDs and bounds.
Never operate on BDD, original test PLN, or any unexpected project.
"""
from __future__ import annotations

from datetime import datetime, timezone
import base64
import json
from pathlib import Path
import sys

import apa_ac29_apx_build_mailbox as MAILBOX
import apa_ac29_group_acceptance_mailbox as ACCEPTANCE
import apa_ac29_group_reconcile_readonly as FORENSIC

ROOT = FORENSIC.ROOT
JOB = FORENSIC.JOB
SCRATCH = FORENSIC.SCOPE
STARTED = ROOT / "resume-started.json"
REPORT = ROOT / "resume-result.json"
REMOTE = (ACCEPTANCE.OUTBOX + "/" + JOB + "-resume.json")

# Distinct from the read-only report's timestamp; all status-critical
# values must remain precisely the same on a second native read.
EVIDENCE_FIELDS = (
    "jobId", "schema", "port", "activeScratchProject",
    "originalSourceSha256Verified", "baselineGuidCount", "currentGuidCount",
    "clonedParentGuidCount", "naiveExpectedGuidCount",
    "unexpectedGuidDelta", "copiedParentTypes", "liveTypeCounts",
    "sourceGroupAndCopiedGroups", "childrenOfCopiedParents",
    "uniqueCopiedChildCount", "allCopiedChildrenPresentInInventory",
    "allCopiedParentsPresentInInventory", "nativeGroupMembershipVerified",
    "copiedGroupParentGeometry", "modelWritesInThisDiagnostic",
    "reopenedOrSavedProject"
)


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def clean_ids(values):
    ids = set()
    for item in values:
        value = str(item).lower()
        ACCEPTANCE.need(ACCEPTANCE.GUID.fullmatch(value or "") and value not in ids,
                        "RESUME_INVALID_OR_DUPLICATE_GUID")
        ids.add(value)
    return ids


def verified_preflight():
    ACCEPTANCE.need(not STARTED.exists(), "RESUME_ALREADY_ATTEMPTED_NO_RETRY")
    ACCEPTANCE.need(not REPORT.exists(), "RESUME_RESULT_EXISTS_NO_RETRY")
    ACCEPTANCE.need(ROOT.is_dir(), "ORIGINAL_JOB_STATE_MISSING")
    initial_receipt = FORENSIC.load("reconciliation-readonly.json")
    ACCEPTANCE.need(initial_receipt.get("status") ==
                    "INVENTORY_EXTRA_CONSISTENT_WITH_NATIVE_CHILDREN",
                    "PREVIOUS_RECONCILIATION_NOT_PASS")
    current = FORENSIC.read_only()  # exact project, source hash, groups, native children
    for key in EVIDENCE_FIELDS:
        ACCEPTANCE.need(current.get(key) == initial_receipt.get(key),
                        "FORENSIC_DRIFT:" + key)
    ACCEPTANCE.need(current.get("status") == initial_receipt.get("status"),
                    "FORENSIC_STATUS_CHANGED")
    ACCEPTANCE.need(current["baselineGuidCount"] == 36
                    and current["currentGuidCount"] == 44
                    and current["unexpectedGuidDelta"] == 4
                    and current["uniqueCopiedChildCount"] == 4
                    and current["nativeGroupMembershipVerified"] is True
                    and current["allCopiedParentsPresentInInventory"] is True
                    and current["allCopiedChildrenPresentInInventory"] is True
                    and len(current["sourceGroupAndCopiedGroups"]) == 3
                    and all(row.get("expectedParentGeometryMatches") is True
                            for row in current["copiedGroupParentGeometry"]),
                    "EXACT_CLONED_SCENE_NOT_RECONFIRMED")
    before = FORENSIC.load("preflight.json")
    clone = FORENSIC.load("after-clone.json")
    parents = clean_ids(
        row["elementId"]["guid"] for row in clone["createdElements"]
    )
    hierarchy = current["childrenOfCopiedParents"]
    ACCEPTANCE.need(len(hierarchy) == 4, "COPY_CHILD_HIERARCHY_INCOMPLETE")
    children = clean_ids(child["guid"] for row in hierarchy
                         for child in row.get("children", []))
    ACCEPTANCE.need(len(children) == 4, "COPIED_CHILD_GUID_COUNT_DIFF")
    complete_before = clean_ids(ACCEPTANCE.read_elements())
    baseline = complete_before - parents - children
    ACCEPTANCE.need(len(complete_before) == 44 and len(baseline) == 36
                    and len(complete_before) == len(baseline | parents | children),
                    "LIVE_MODEL_BASELINE_NOT_CONSISTENT")
    ids_from_report = {
        child["guid"].lower() for row in hierarchy for child in row["children"]
    }
    ACCEPTANCE.need(ids_from_report == children, "FORENSIC_CHILDREN_ID_MISMATCH")
    copied = current["sourceGroupAndCopiedGroups"][1:]
    source = current["sourceGroupAndCopiedGroups"][0]
    ACCEPTANCE.need(set(source["members"]) ==
                    clean_ids(before["sourceColumnGuids"]),
                    "SOURCE_COLUMN_MEMBERS_CHANGED")
    for row in copied:
        ACCEPTANCE.need(len(row["members"]) == 2
                        and clean_ids(row["members"]).issubset(parents),
                        "COPIED_GROUP_MEMBERS_CHANGED")
    ACCEPTANCE.need(
        clean_ids(v["guid"] for v in clone["newGroupIds"]) ==
        clean_ids(row["group"] for row in copied),
        "COPIED_GROUP_IDENTITY_CHANGED"
    )
    return {
        "before": before, "clone": clone, "forensic": current,
        "originalSha": before["sourceSha256"],
        "baseline": baseline,
        "parents": parents,
        "children": children,
        "complete": complete_before,
        "copied": copied,
        "source": source,
        "target": copied[0]["group"],
        "target_members": clean_ids(copied[0]["members"]),
        "other": copied[1]["group"]
    }


def require_unchanged_inventory(state):
    ids = clean_ids(ACCEPTANCE.read_elements())
    ACCEPTANCE.need(ids == state["complete"],
                    "LIVE_MODEL_GUID_SET_CHANGED_DURING_RESUME")
    mapping, children = ACCEPTANCE.native_owned_children(
        sorted(state["parents"]), state["baseline"])
    ACCEPTANCE.need(children == state["children"],
                    "NATIVE_CHILDREN_CHANGED_DURING_RESUME")
    expected_map = {row["parentGuid"].lower():
                    [child["guid"].lower() for child in row["children"]]
                    for row in state["forensic"]["childrenOfCopiedParents"]}
    ACCEPTANCE.need(mapping == expected_map,
                    "NATIVE_PARENT_CHILD_RELATION_CHANGED_DURING_RESUME")


def command_once(state, stage, name, params):
    ACCEPTANCE.guard(SCRATCH, state["originalSha"])
    ACCEPTANCE.need(STARTED.exists(), "RESUME_INTENT_NOT_DURABLE")
    stage_file = ROOT / ("resume-before-" + stage + ".json")
    ACCEPTANCE.need(not stage_file.exists(), "STAGE_ALREADY_DISPATCHED_NO_RETRY")
    MAILBOX.save(stage_file, {
        "stage": stage, "command": name, "parameters": params,
        "scope": str(SCRATCH), "at": timestamp(), "autoRetry": False
    })
    result = ACCEPTANCE.request(name, params, addon=True, timeout=90)
    MAILBOX.save(ROOT / ("resume-after-" + stage + ".json"), result)
    return result


def run():
    state = verified_preflight()
    parent_members = sorted(state["target_members"])
    before_boxes = ACCEPTANCE.boxes(parent_members)
    ACCEPTANCE.need(all(b is not None for b in before_boxes),
                    "MOVE_BASELINE_PARENT_GEOMETRY_MISSING")
    clone_offsets = state["before"]["translations"]
    ACCEPTANCE.need(len(clone_offsets) == 2 and clone_offsets[0] ==
                    state["forensic"]["copiedGroupParentGeometry"][0]["translation"],
                    "ORIGINAL_CLONE_PLACEMENT_IDENTITY_CHANGED")
    delta = state["before"]["moveTranslation"]
    ACCEPTANCE.need(set(delta) == {"dx", "dy", "dz"},
                    "PREFLIGHT_TRANSLATION_INCOMPLETE")
    ACCEPTANCE.need(delta["dx"] == 0.0 and delta["dy"] == 15.0
                    and delta["dz"] == 0.0,
                    "UNEXPECTED_MOVE_REQUEST")
    expected_after = [
        ACCEPTANCE.shift(box, delta["dx"], delta["dy"], delta["dz"])
        for box in before_boxes
    ]
    require_unchanged_inventory(state)
    ACCEPTANCE.need(clean_ids(ACCEPTANCE.elements_of_group(state["target"])) ==
                    state["target_members"],
                    "TARGET_GROUP_CHANGED_IMMEDIATELY_BEFORE_WRITE")
    MAILBOX.save(STARTED, {
        "schema": "APA_AC29_GROUP_RESUME_ONE_SHOT_V1",
        "scratchPath": str(SCRATCH),
        "originalSha256": state["originalSha"],
        "group": state["target"],
        "modelGuidsBefore": sorted(state["complete"]),
        "sourceForensicStatus": state["forensic"]["status"],
        "at": timestamp(), "autoRetry": False
    })
    source_ref = "APA_GROUP_ACCEPTANCE:" + state["originalSha"][:24]
    moved = command_once(state, "move", "MoveNativeGroupV1", {
        "groupId": {"guid": state["target"]},
        "sourceRef": source_ref,
        "translation": delta
    })
    moved_members = clean_ids(
        v.get("guid", "") for v in moved.get("movedMembers", []))
    ACCEPTANCE.need(moved_members == state["target_members"],
                    "NATIVE_MOVE_RESULT_MEMBER_GUIDS_MISMATCH")
    ACCEPTANCE.need(clean_ids(ACCEPTANCE.elements_of_group(state["target"])) ==
                    state["target_members"], "NATIVE_MOVE_GROUP_CHANGED")
    ACCEPTANCE.exact_bbox(parent_members, expected_after)
    require_unchanged_inventory(state)
    ACCEPTANCE.need(
        clean_ids(ACCEPTANCE.elements_of_group(state["other"])) ==
        clean_ids(state["copied"][1]["members"]),
        "NATIVE_MOVE_DAMAGED_OTHER_GROUP"
    )
    released = command_once(state, "ungroup", "UngroupNativeGroupV1", {
        "groupId": {"guid": state["target"]}, "sourceRef": source_ref
    })
    released_members = clean_ids(
        v.get("guid", "") for v in released.get("releasedMembers", []))
    ACCEPTANCE.need(released_members == state["target_members"],
                    "NATIVE_UNGROUP_RELEASED_WRONG_MEMBERS")
    roots = ACCEPTANCE.group_roots(parent_members)
    ACCEPTANCE.need(
        all(isinstance(v, dict) and "error" not in v
            and ACCEPTANCE.null_group(v.get("groupId"))
            and ACCEPTANCE.null_group(v.get("rootGroupId"))
            for v in roots),
        "NATIVE_UNGROUP_MEMBERS_STILL_GROUPED"
    )
    ACCEPTANCE.exact_bbox(parent_members, expected_after)
    require_unchanged_inventory(state)
    ACCEPTANCE.need(
        clean_ids(ACCEPTANCE.elements_of_group(state["other"])) ==
        clean_ids(state["copied"][1]["members"]),
        "NATIVE_UNGROUP_DAMAGED_OTHER_GROUP"
    )
    ACCEPTANCE.need(
        clean_ids(ACCEPTANCE.elements_of_group(state["source"]["group"])) ==
        clean_ids(state["source"]["members"]),
        "NATIVE_UNGROUP_DAMAGED_SOURCE_GROUP"
    )
    ACCEPTANCE.guard(SCRATCH, state["originalSha"])
    save_stage = ROOT / "resume-before-save.json"
    ACCEPTANCE.need(not save_stage.exists(), "SAVE_ALREADY_ATTEMPTED")
    MAILBOX.save(save_stage, {
        "at": timestamp(), "scratchPath": str(SCRATCH),
        "autoRetry": False, "command": "SaveProject"
    })
    save = ACCEPTANCE.request("SaveProject", {}, addon=True, timeout=90)
    MAILBOX.save(ROOT / "resume-after-save.json", save)
    ACCEPTANCE.need(save.get("success") is True,
                    "SCRATCH_SAVE_NOT_CONFIRMED")
    ACCEPTANCE.need(ACCEPTANCE.digest(ACCEPTANCE.SOURCE_PATH) ==
                    state["originalSha"], "ORIGINAL_PLN_DISK_CHANGED")
    return {
        "status": "LIVE_GROUP_CHAIN_COMPLETED_AFTER_READONLY_RECONCILIATION",
        "sourceJobId": JOB, "port": ACCEPTANCE.PORT,
        "scratchProject": str(SCRATCH),
        "saveConfirmed": True,
        "originalSourceSha256Unchanged": True,
        "createdParentCount": len(state["parents"]),
        "createdNativeChildCount": len(state["children"]),
        "sourceAndCopiedGroupsInitiallyVerified": 3,
        "move": "NATIVE_MOVE_AND_BBOX_PASS",
        "ungroup": "NATIVE_UNGROUP_AND_GUID_PASS",
        "unchangedInventoryGuidCount": len(state["complete"]),
        "autoRetry": False
    }


def publish_result():
    data = REPORT.read_bytes()
    path = REMOTE
    try:
        existing, _ = MAILBOX.read_file(path)
    except Exception as exc:
        if "404" not in str(exc) and "Not Found" not in str(exc):
            raise
    else:
        ACCEPTANCE.need(existing == json.loads(data),
                        "RESUME_REMOTE_REPORT_CANNOT_OVERWRITE")
        return
    answer = MAILBOX.gh(
        f"repos/{ACCEPTANCE.BRIDGE}/contents/{path}",
        put={
            "message": "AC29 group copy reconciliation: resume remaining native operations",
            "branch": ACCEPTANCE.MAILBOX_BRANCH,
            "content": base64.b64encode(data).decode("ascii")
        }
    )
    ACCEPTANCE.need(answer.get("content", {}).get("sha") ==
                    MAILBOX.git_blob(data),
                    "RESUME_REMOTE_PUBLICATION_NOT_VERIFIED")


if __name__ == "__main__":
    try:
        if REPORT.exists():
            previous = json.loads(REPORT.read_text(encoding="utf8"))
            publish_result()
            print("APA_AC29_GROUP_RESUME_PREVIOUS_RESULT_REPUBLISHED:",
                  previous["result"]["status"], flush=True)
            raise SystemExit(
                0 if previous["result"]["status"] ==
                "LIVE_GROUP_CHAIN_COMPLETED_AFTER_READONLY_RECONCILIATION"
                else 2)
        try:
            status = run()
        except Exception as exc:
            status = {
                "status": "RESUME_STOPPED_NO_AUTOMATIC_RETRY",
                "error": type(exc).__name__ + ": " + str(exc)[-1200:],
                "someNativeWritesMayHaveOccurred": STARTED.exists(),
                "scratchMayHaveUnsavedChanges": STARTED.exists(),
                "sourceJobId": JOB, "autoRetry": False
            }
        MAILBOX.save(REPORT, {
            "schema": "APA_AC29_GROUP_RESUME_RESULT_V1",
            "jobId": JOB, "capturedAt": timestamp(),
            "result": status
        })
        publish_result()
        print("APA_AC29_GROUP_RESUME:", status["status"], flush=True)
        if status["status"] != "LIVE_GROUP_CHAIN_COMPLETED_AFTER_READONLY_RECONCILIATION":
            raise SystemExit(2)
    except Exception as exc:
        print("APA_AC29_GROUP_RESUME_FATAL:",
              type(exc).__name__, str(exc), flush=True)
        raise SystemExit(2)
