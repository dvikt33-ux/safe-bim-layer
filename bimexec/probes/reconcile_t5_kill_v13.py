#!/usr/bin/env python3
"""Read-only restart/reconcile for audit T5 hard process kill.

The source receipt is expected to end durably at RUNNING/DISPATCHED with exactly
one attempt and no recorded outcome because the worker process was hard-killed.
This separate process interprets INTENT-without-OUTCOME as OP_UNKNOWN, performs
read-only model reconciliation, and may only OFFER ADOPT. It never retries or
mutates Archicad.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import Any

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import backends as base
from backends_v13 import TapirBackendV13
import probe_t2_connections_v13 as t2c
import probe_t3_dependency_v13 as t3

VER = "1.0"
ADDON = "1.5.9"


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def load_json(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str, obj: Any) -> None:
    base.write_json_atomic(path, obj)


def comp_guid(raw: dict[str, Any]) -> str | None:
    det = raw.get("details") if isinstance(raw.get("details"), dict) else {}
    c = base._to_dict(det.get("compositeId"))
    return str(c.get("guid")) if c.get("guid") else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--expect-project", required=True)
    ap.add_argument("--port", type=int, default=19723)
    ap.add_argument("--receipt", required=True)
    ap.add_argument("--controller-report", required=True)
    ap.add_argument("--report", default="t5_kill_reconcile_live_v13.json")
    a = ap.parse_args()

    if os.path.exists(a.report):
        print(f"STOP: reconcile report already exists: {a.report}", file=sys.stderr)
        return 1
    if not os.path.exists(a.receipt):
        print(f"STOP: source receipt missing: {a.receipt}", file=sys.stderr)
        return 1
    if not os.path.exists(a.controller_report):
        print(f"STOP: controller report missing: {a.controller_report}", file=sys.stderr)
        return 1

    src = load_json(a.receipt)
    ctl = load_json(a.controller_report)

    stages = src.get("stages") or []
    last_stage = stages[-1].get("stage") if stages else None
    source_ok = (
        src.get("probe") == "AUDIT_T5_PROCESS_KILL_AFTER_DISPATCH"
        and src.get("job_state") == "RUNNING"
        and src.get("op_state") == "DISPATCHED"
        and int(src.get("dispatch_attempts", 0)) == 1
        and last_stage == "DISPATCH_INTENT"
        and not src.get("candidate_guid")
        and not src.get("outcome")
        and not src.get("finished_at")
    )
    if not source_ok:
        print("STOP: source receipt is not the expected T5 INTENT-without-OUTCOME state", file=sys.stderr)
        return 1

    controller_ok = (
        ctl.get("probe") == "AUDIT_T5_PROCESS_KILL_CONTROLLER"
        and ctl.get("controller_outcome") == "HARD_KILL_CONFIRMED"
        and ctl.get("killpoint_observed") is True
        and ctl.get("archicad_process_killed") is False
        and ctl.get("production_router_killed") is False
        and int(ctl.get("post_dispatch_model_readback_by_controller", -1)) == 0
    )
    if not controller_ok:
        print("STOP: controller does not prove the intended hard-kill boundary", file=sys.stderr)
        return 1

    origin_raw = src.get("origin") or []
    if len(origin_raw) != 2:
        print("STOP: source receipt has no valid origin", file=sys.stderr)
        return 1
    origin = (float(origin_raw[0]), float(origin_raw[1]))

    baseline_guids = set(src.get("baseline_guids") or [])
    baseline_walls = set(src.get("baseline_walls") or [])
    baseline_counts = src.get("baseline_counts") or {}
    intended = src.get("intended") or {}

    b = TapirBackendV13(port=a.port)
    ok, why = b.available()
    if not ok:
        print(f"STOP: backend unavailable: {why}", file=sys.stderr)
        return 1
    addon = b.addon_version()
    if addon != ADDON:
        print(f"STOP: Tapir {addon!r} != {ADDON!r}", file=sys.stderr)
        return 1

    try:
        info, stories = t2c.project_recheck(b, a.expect_project)
    except t2c.Stop as e:
        print(f"STOP: project binding mismatch: {e.reason}", file=sys.stderr)
        return 1

    current_all = set(b.all_elements() or [])
    current_walls = set(b.elements_by_type("Wall") or [])
    current_counts = b.count_by_type()
    fresh_all = sorted(current_all - baseline_guids)
    fresh_walls = sorted(current_walls - baseline_walls)
    wall_delta = int(current_counts.get("Wall", 0)) - int(baseline_counts.get("Wall", 0))

    report: dict[str, Any] = {
        "probe": "AUDIT_T5_PROCESS_KILL_RESTART_RECONCILE",
        "version": VER,
        "generated_at": now(),
        "source_receipt": a.receipt,
        "controller_report": a.controller_report,
        "crash_recovery_inference": {
            "durable_source_state": "RUNNING/DISPATCHED",
            "missing_outcome": True,
            "recovered_job_state": "PAUSED",
            "recovered_pause_reason": "OP_UNKNOWN",
            "recovered_op_state": "UNKNOWN",
            "reason": "durable mutation intent exists but no durable outcome after hard process kill",
        },
        "archicad": info,
        "adapter_version": addon,
        "origin": list(origin),
        "read_only": True,
        "mutations": 0,
        "observations": {
            "fresh_all_guids": fresh_all,
            "fresh_wall_guids": fresh_walls,
            "wall_count_delta": wall_delta,
        },
        "classification": None,
        "candidate_guid": None,
        "anchor_checks": None,
        "recommended_human_decision": None,
        "automatic_retry_allowed": False,
        "automatic_adopt_performed": False,
    }

    if wall_delta == 0 and not fresh_walls:
        report["classification"] = "NOT_APPLIED"
        report["recommended_human_decision"] = "NOT_APPLIED"
    elif wall_delta != 1 or len(fresh_walls) != 1:
        report["classification"] = "AMBIGUOUS"
        report["recommended_human_decision"] = "QUARANTINE_OR_MANUAL_REVIEW"
    elif len(fresh_all) != 1 or fresh_all[0] != fresh_walls[0]:
        report["classification"] = "AMBIENT_MODEL_CHANGE"
        report["candidate_guid"] = fresh_walls[0]
        report["recommended_human_decision"] = "MANUAL_REVIEW"
    else:
        guid = fresh_walls[0]
        seg = t3.wall_segment(origin)
        obs = t2c.observe(b, guid, stories)
        checks = t2c.geometry_checks(obs, seg)
        # Process dies immediately after CreateWalls and before any layer/details write.
        checks.pop("layer", None)
        raw = b.details_raw(guid) or {}
        det = raw.get("details") if isinstance(raw.get("details"), dict) else {}
        checks["structureType"] = det.get("structureType") == intended.get("structureType") == "Composite"
        checks["compositeId"] = comp_guid(raw) == str(intended.get("compositeId"))
        checks["story_index"] = raw.get("floorIndex") == intended.get("story_index")

        report["candidate_guid"] = guid
        report["anchor_checks"] = checks
        report["candidate_observation"] = obs
        report["candidate_raw_structure"] = {
            "structureType": det.get("structureType"),
            "compositeId": comp_guid(raw),
            "floorIndex": raw.get("floorIndex"),
            "layerIndex": raw.get("layerIndex"),
        }
        if all(checks.values()):
            report["classification"] = "APPLIED_ADOPTABLE_BY_ANCHOR"
            report["recommended_human_decision"] = "ADOPT"
        else:
            report["classification"] = "APPLIED_BUT_ANCHOR_MISMATCH"
            report["recommended_human_decision"] = "MANUAL_REVIEW"

    write_json(a.report, report)

    print("AUDIT T5 RESTART / READ-ONLY RECONCILE")
    print("DURABLE SOURCE       : RUNNING/DISPATCHED, no outcome")
    print("RECOVERED STATE      : PAUSED(OP_UNKNOWN)")
    print("DISPATCH ATTEMPTS    :", src.get("dispatch_attempts"))
    print("FRESH WALLS          :", fresh_walls)
    print("WALL COUNT DELTA     :", wall_delta)
    print("CLASSIFICATION       :", report["classification"])
    print("CANDIDATE GUID       :", report.get("candidate_guid"))
    print("HUMAN DECISION OFFER :", report["recommended_human_decision"])
    print("AUTO RETRY           : FORBIDDEN")
    print("AUTO ADOPT           : NOT PERFORMED")
    print("MUTATIONS            : 0")
    print("report               :", a.report)

    return 0 if report["classification"] == "APPLIED_ADOPTABLE_BY_ANCHOR" else 2


if __name__ == "__main__":
    raise SystemExit(main())
