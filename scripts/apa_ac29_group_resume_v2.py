"""Safely continue stopped AC29 group acceptance 04 after a read-only preflight.

Attempt V1 stopped BEFORE any write due to case-sensitive GUID comparison.
This is an explicitly new, one-shot V2 with its own start and result receipts.
No repeat of group creation or group copying. Scope: only existing scratch PLN
on Archicad 29 port 19724. No automatic retry after any uncertainty.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

import apa_ac29_group_resume_after_clone as RESUME

ROOT = RESUME.ROOT
PRIOR_RESULT = ROOT / "resume-result.json"
PRIOR_STARTED = ROOT / "resume-started.json"
V2_STARTED = ROOT / "resume-v2-started.json"
V2_RESULT = ROOT / "resume-v2-result.json"
V2_REMOTE = RESUME.ACCEPTANCE.OUTBOX + "/" + RESUME.JOB + "-resume-v2.json"
V1_STAGE_FILES = (
    "resume-before-move.json", "resume-after-move.json",
    "resume-before-ungroup.json", "resume-after-ungroup.json",
    "resume-before-save.json", "resume-after-save.json",
)


def require_v1_readonly_stop():
    """Only this exact known case-mismatch failure authorizes V2 preflight."""
    need = RESUME.ACCEPTANCE.need
    need(PRIOR_RESULT.is_file(), "V1_RESULT_RECEIPT_NOT_PRESENT")
    previous = json.loads(PRIOR_RESULT.read_text(encoding="utf8"))
    result = previous.get("result", {})
    need(previous.get("schema") == "APA_AC29_GROUP_RESUME_RESULT_V1"
         and previous.get("jobId") == RESUME.JOB
         and result.get("status") == "RESUME_STOPPED_NO_AUTOMATIC_RETRY"
         and result.get("error") ==
         "RuntimeError: TARGET_GROUP_CHANGED_IMMEDIATELY_BEFORE_WRITE"
         and result.get("someNativeWritesMayHaveOccurred") is False
         and result.get("scratchMayHaveUnsavedChanges") is False,
         "V1_FAILED_SAFELY_BEFORE_WRITE_NOT_PROVEN")
    need(not PRIOR_STARTED.exists(),
         "V1_START_MARKER_PRESENT_MUST_RECONCILE_FIRST")
    need(not any((ROOT / name).exists() for name in V1_STAGE_FILES),
         "V1_MUTATING_STAGE_MAY_HAVE_BEEN_DISPATCHED")
    # No shell commands, no path switches, no model writes in this guard.


def offline_case_regression():
    """Five formerly broken comparisons all use canonical GUID case."""
    s = Path(RESUME.__file__).read_text(encoding="utf8")
    need = RESUME.ACCEPTANCE.need
    need("set(ACCEPTANCE.elements_of_group(" not in s,
         "REGRESSION_UNNORMALIZED_NATIVE_MEMBERSHIP_COMPARE")
    need(s.count("clean_ids(ACCEPTANCE.elements_of_group(") == 5,
         "REGRESSION_NOT_ALL_FIVE_MEMBERSHIP_CHECKS_CANONICAL")
    mixed = [
        "0A17FB15-3639-4DFA-AB01-CD910AE112B0",
        "CCC099EA-DA0F-4A5D-AEC4-75EA5B792C3C",
    ]
    low = {x.lower() for x in mixed}
    need(RESUME.clean_ids(mixed) == low
         and RESUME.clean_ids(x.lower() for x in mixed) == low,
         "REGRESSION_GUID_CASE_NORMALIZATION_FAILED")


def configure_v2():
    RESUME.STARTED = V2_STARTED
    RESUME.REPORT = V2_RESULT
    RESUME.REMOTE = V2_REMOTE


def main():
    # Even a second invocation may ONLY re-publish an existing V2 receipt,
    # never re-run a mutation or override that receipt.
    configure_v2()
    if V2_RESULT.is_file():
        old = json.loads(V2_RESULT.read_text(encoding="utf8"))
        RESUME.publish_result()
        status = old.get("result", {}).get("status", "")
        print("APA_AC29_GROUP_RESUME_V2_PREVIOUS_RECEIPT:", status,
              flush=True)
        return 0 if status == \
            "LIVE_GROUP_CHAIN_COMPLETED_AFTER_READONLY_RECONCILIATION" else 2

    try:
        require_v1_readonly_stop()
        offline_case_regression()
        # Requires exact project + forensic GUID/hierarchy/geometry matches.
        # All V2 mutation intents are written durably before native calls.
        result = RESUME.run()
    except Exception as exc:
        result = {
            "status": "RESUME_V2_STOPPED_NO_AUTOMATIC_RETRY",
            "error": type(exc).__name__ + ": " + str(exc)[-1200:],
            "someNativeWritesMayHaveOccurred": V2_STARTED.exists(),
            "scratchMayHaveUnsavedChanges": V2_STARTED.exists(),
            "sourceJobId": RESUME.JOB,
            "autoRetry": False
        }
    RESUME.MAILBOX.save(V2_RESULT, {
        "schema": "APA_AC29_GROUP_RESUME_RESULT_V2",
        "jobId": RESUME.JOB,
        "capturedAt": RESUME.timestamp(),
        "sourceV1Result": str(PRIOR_RESULT),
        "result": result
    })
    RESUME.publish_result()
    print("APA_AC29_GROUP_RESUME_V2:", result["status"], flush=True)
    return 0 if result["status"] == \
        "LIVE_GROUP_CHAIN_COMPLETED_AFTER_READONLY_RECONCILIATION" else 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print("APA_AC29_GROUP_RESUME_V2_FATAL:",
              type(exc).__name__, str(exc), flush=True)
        sys.exit(2)
