"""Read-only forensic receipt for stopped AC29 native group cloning attempt 04.

Does not call OpenProject, SaveProject, Create*, Clone*, Move*, Ungroup* or
any Archicad write command. Leaves the currently open scratch PLN untouched.
Uses immutable local receipts, existing Tapir reads, and GitHub for a report.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import base64
import json
from pathlib import Path

import apa_ac29_apx_build_mailbox as MAILBOX
import apa_ac29_group_acceptance_mailbox as ACCEPTANCE

JOB = "group-ac29-assembly-20261018-04"
ROOT = Path(r"C:\LocalAI\APA_AC29_Group_Acceptance_State") / JOB
SCOPE = Path(r"C:\LocalAI\APA_Group_Acceptance") / (JOB + ".pln")
BRIDGE_RESULT = (
    "safe-bim-mailbox/apa-ac29-group-acceptance/results/"
    + JOB + "-reconciliation.json"
)


def load(file):
    path = ROOT / file
    ACCEPTANCE.need(path.is_file(), "LOCAL_RECEIPT_NOT_FOUND:" + str(path))
    return json.loads(path.read_text(encoding="utf8"))


def gid(entry):
    if isinstance(entry, dict):
        return str(entry.get("guid", "")).lower()
    return ""


def guids(entries):
    return [gid(x) for x in entries]


def read_only():
    """Verify exact approved scratch path before native queries."""
    ACCEPTANCE.need(ROOT.is_dir(), "NO_PREVIOUS_ATTEMPT_STATE")
    preflight = load("preflight.json")
    clone = load("after-clone.json")
    create = load("after-create.json")
    stopped = load("result.json")
    ACCEPTANCE.need(
        stopped.get("result", {}).get("error", "").endswith("GROUP_CLONE_INVENTORY_DIFF"),
        "WRONG_STOPPED_ATTEMPT_FOR_RECONCILIATION"
    )
    source_hash = preflight.get("sourceSha256")
    ACCEPTANCE.need(isinstance(source_hash, str) and len(source_hash) == 64,
                    "PREFLIGHT_SOURCE_HASH_MISSING")
    ACCEPTANCE.need(
        ACCEPTANCE.canonical_path(preflight.get("scratchPath", "")) ==
        ACCEPTANCE.canonical_path(SCOPE),
        "SCRATCH_PATH_NOT_MATCHING_PINNED_JOB"
    )
    ACCEPTANCE.need(
        ACCEPTANCE.request("API.GetProductInfo", {}).get("version") == 29,
        "NOT_ARCHICAD29_ON_APPROVED_PORT"
    )
    active = ACCEPTANCE.guard(SCOPE, source_hash)
    source_group = gid(create.get("groupId"))
    copied_groups = guids(clone.get("newGroupIds", []))
    copied_ids = guids(
        [v.get("elementId", {}) for v in clone.get("createdElements", [])]
    )
    ACCEPTANCE.need(
        ACCEPTANCE.GUID.fullmatch(source_group or "")
        and len(copied_groups) == 2
        and len(set(copied_groups)) == 2
        and len(copied_ids) == 4
        and len(set(copied_ids)) == 4
        and all(ACCEPTANCE.GUID.fullmatch(x or "")
                for x in copied_groups + copied_ids),
        "CLONE_RECEIPT_GUIDS_INVALID"
    )
    live_guids = ACCEPTANCE.read_elements()
    originals = [str(x).lower() for x in preflight.get("sourceColumnGuids", [])]
    ACCEPTANCE.need(
        len(originals) == 2 and all(ACCEPTANCE.GUID.fullmatch(x) for x in originals),
        "SOURCE_COLUMNS_NOT_PINNED"
    )
    element_details = ACCEPTANCE.batched(
        "GetDetailsOfElements", live_guids, "detailsOfElements"
    )
    kinds = {}
    for guid, row in zip(live_guids, element_details):
        kinds[guid.lower()] = row.get("type", "UNRESOLVED") if isinstance(row, dict) else "ERROR"
    parent_details = ACCEPTANCE.batched(
        "GetDetailsOfElements", copied_ids, "detailsOfElements"
    )
    group_ids = [source_group] + copied_groups
    group_results = []
    for group_id in group_ids:
        try:
            members = ACCEPTANCE.elements_of_group(group_id)
            group_results.append({
                "group": group_id,
                "members": [m.lower() for m in members],
                "types": [kinds.get(m.lower(), "UNRESOLVED") for m in members]
            })
        except Exception as error:
            group_results.append({
                "group": group_id,
                "readError": type(error).__name__ + ": " + str(error)
            })
    hierarchy = []
    new_child_ids = set()
    for parent_id in copied_ids:
        result = {"parentGuid": parent_id,
                  "parentType": kinds.get(parent_id, "UNKNOWN")}
        try:
            response = ACCEPTANCE.request(
                "GetSubelementsOfHierarchicalElements",
                {"elements": [{"elementId": {"guid": parent_id}}]},
                addon=True
            ).get("subelements")
            ACCEPTANCE.need(
                isinstance(response, list)
                and len(response) == 1
                and isinstance(response[0], dict),
                "NATIVE_SUBELEMENT_READBACK_INVALID"
            )
            record = response[0]
            found = []
            for slot, arr in record.items():
                if isinstance(arr, list):
                    for item in arr:
                        if isinstance(item, dict):
                            child = gid(item.get("elementId"))
                            if ACCEPTANCE.GUID.fullmatch(child or ""):
                                found.append({"slot": slot, "guid": child,
                                              "type": kinds.get(child, "UNRESOLVED")})
                                new_child_ids.add(child)
            result["children"] = found
            result["returnedSlots"] = list(record)
        except Exception as error:
            result["readError"] = type(error).__name__ + ": " + str(error)
        hierarchy.append(result)

    geometry = []
    source_boxes = ACCEPTANCE.boxes(originals)
    for group_id, offset in zip(copied_groups, preflight.get("translations", [])):
        item = {"group": group_id, "translation": offset}
        associated = next((g for g in group_results if g["group"] == group_id), {})
        member_ids = associated.get("members", [])
        if len(member_ids) == 2 and all(isinstance(v, dict) for v in source_boxes):
            actual_boxes = ACCEPTANCE.boxes(member_ids)
            expected_boxes = [ACCEPTANCE.shift(
                box, offset["dx"], offset["dy"], offset["dz"]
            ) for box in source_boxes]
            item["sourceBoundsAvailable"] = True
            item["clonedParentBoundsAvailable"] = all(
                isinstance(b, dict) for b in actual_boxes
            )
            item["expectedParentGeometryMatches"] = (
                all(isinstance(b, dict) for b in actual_boxes)
                and ACCEPTANCE.signatures(actual_boxes) ==
                ACCEPTANCE.signatures(expected_boxes)
            )
        geometry.append(item)

    actual_count = len(live_guids)
    baseline_count = preflight["baselineGuids"]
    naive_expected = baseline_count + len(copied_ids)
    child_count = len(new_child_ids)
    extra_count = actual_count - naive_expected
    all_children_present = new_child_ids.issubset(set(g.lower() for g in live_guids))
    every_copied_parent_present = set(copied_ids).issubset(
        set(g.lower() for g in live_guids)
    )
    full_native_membership = (
        len(group_results) == 3
        and all("members" in g and len(g["members"]) == 2 for g in group_results)
        and set(group_results[0]["members"]) == set(originals)
        and all(set(g["members"]).issubset(set(copied_ids))
                for g in group_results[1:])
        and len(set(m for g in group_results[1:] for m in g["members"])) == 4
    )
    status = (
        "INVENTORY_EXTRA_CONSISTENT_WITH_NATIVE_CHILDREN"
        if extra_count > 0 and extra_count == child_count
        and all_children_present and every_copied_parent_present
        and full_native_membership
        else "INVENTORY_DISCREPANCY_NEEDS_ANALYSIS"
    )
    return {
        "schema": "APA_AC29_GROUP_READONLY_RECONCILIATION_V1",
        "jobId": JOB,
        "status": status,
        "capturedAt": datetime.now(timezone.utc).isoformat(),
        "modelWritesInThisDiagnostic": 0,
        "reopenedOrSavedProject": False,
        "port": ACCEPTANCE.PORT,
        "activeScratchProject": active.get("projectPath"),
        "originalSourceSha256Verified": source_hash,
        "baselineGuidCount": baseline_count,
        "currentGuidCount": actual_count,
        "clonedParentGuidCount": len(copied_ids),
        "naiveExpectedGuidCount": naive_expected,
        "unexpectedGuidDelta": extra_count,
        "copiedParentTypes": [row.get("type", "UNRESOLVED")
                              if isinstance(row, dict) else "ERROR"
                              for row in parent_details],
        "liveTypeCounts": dict(Counter(kinds.values())),
        "sourceGroupAndCopiedGroups": group_results,
        "childrenOfCopiedParents": hierarchy,
        "uniqueCopiedChildCount": child_count,
        "allCopiedChildrenPresentInInventory": all_children_present,
        "allCopiedParentsPresentInInventory": every_copied_parent_present,
        "nativeGroupMembershipVerified": full_native_membership,
        "copiedGroupParentGeometry": geometry,
        "note": ("Matching counts are consistent with auto-generated native "
                 "ColumnSegment/BeamSegment children; they do not prove no "
                 "other concurrent or hidden changes.")
    }


def publish(report):
    payload = (json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2)
               + "\n").encode("utf8")
    local = ROOT / "reconciliation-readonly.json"
    if local.is_file():
        previous = json.loads(local.read_text(encoding="utf8"))
        ACCEPTANCE.need(previous == report,
                        "EXISTING_RECONCILIATION_RECEIPT_CANNOT_OVERWRITE")
    else:
        local.write_bytes(payload)
    try:
        existing, _ = MAILBOX.read_file(BRIDGE_RESULT)
    except Exception as error:
        if "404" not in str(error) and "Not Found" not in str(error):
            raise
    else:
        ACCEPTANCE.need(existing == report,
                        "REMOTE_RECONCILIATION_RECEIPT_CANNOT_OVERWRITE")
        return "ALREADY_PUBLISHED"
    content = base64.b64encode(payload).decode("ascii")
    answer = MAILBOX.gh(
        f"repos/{ACCEPTANCE.BRIDGE}/contents/{BRIDGE_RESULT}",
        put={
            "message": "Read-only AC29 group cloning reconciliation 04",
            "branch": ACCEPTANCE.MAILBOX_BRANCH,
            "content": content
        }
    )
    ACCEPTANCE.need(
        answer.get("content", {}).get("sha") == MAILBOX.git_blob(payload),
        "FORENSIC_REPORT_GITHUB_UPLOAD_NOT_VERIFIED"
    )
    return "PUBLISHED"


if __name__ == "__main__":
    try:
        result = read_only()
        print("APA_AC29_READ_ONLY_RECONCILIATION:", result["status"], flush=True)
        print("LIVE_ELEMENT_COUNT:", result["currentGuidCount"], flush=True)
        print("EXPECTED_WITHOUT_SUBELEMENTS:", result["naiveExpectedGuidCount"], flush=True)
        print("NEW_NATIVE_CHILDREN:", result["uniqueCopiedChildCount"], flush=True)
        print("REPORT:", publish(result), flush=True)
    except Exception as exc:
        print("APA_AC29_RECONCILIATION_STOPPED:",
              type(exc).__name__, str(exc), flush=True)
        raise SystemExit(2)
