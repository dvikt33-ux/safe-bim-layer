#!/usr/bin/env python3
"""Read-only reconciliation for an audit T3 run stopped at OPENING_READBACK.

This probe NEVER creates, edits, tags, deletes, moves or retries anything.
It adopts no model state by mutation. It only proves whether the already-created
Opening recorded in the immutable T3 receipt is hosted by the already-confirmed
T3 wall via Tapir GetConnectedElements.

Why this exists:
Tapir 1.5.9 can create generic Opening elements, but GetDetailsOfElements returns
"Not yet supported element type" for their type-specific details. The original
T3 runner therefore correctly stopped with VERIFY_UNAVAILABLE instead of
pretending owner/size read-back succeeded. GetConnectedElements is an independent
read-only relation query and can still prove the dependency binding.
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
import probe_t3_dependency_v13 as t3
import probe_t2_connections_v13 as t2c

VER = "1.0"


class ReconcileError(RuntimeError):
    pass


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def read_json(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        obj = json.load(f)
    if not isinstance(obj, dict):
        raise ReconcileError("receipt must be a JSON object")
    return obj


def project_ok(info: dict[str, Any], expected: str) -> bool:
    path = info.get("project_path") or ""
    return (
        os.path.normcase(path) == os.path.normcase(expected)
        and not info.get("is_untitled")
        and not info.get("is_teamwork")
    )


def receipt_origin(receipt: dict[str, Any]) -> tuple[float, float]:
    for st in receipt.get("stages") or []:
        if st.get("stage") == "PRECHECK":
            origin = st.get("origin")
            if isinstance(origin, list) and len(origin) == 2:
                return float(origin[0]), float(origin[1])
    raise ReconcileError("PRECHECK origin missing from receipt")


def receipt_guids(receipt: dict[str, Any]) -> tuple[str, str]:
    wall = ((receipt.get("mapping") or {}).get("host_wall") or {}).get("guid")
    opening = None
    for artifact in receipt.get("artifacts") or []:
        if artifact.get("kind") == "Opening" and artifact.get("guid"):
            opening = artifact.get("guid")
            break
    if not wall or not opening:
        raise ReconcileError("receipt does not contain both host wall and Opening GUIDs")
    return str(wall), str(opening)


def connected_openings(b: TapirBackendV13, wall_guid: str) -> list[str]:
    res = b.raw_call("GetConnectedElements", {
        "elements": [{"elementId": {"guid": wall_guid}}],
        "connectedElementType": "Opening",
    })
    d = base._to_dict(res)
    wrappers = base._as_list(d.get("connectedElements") or [])
    out: list[str] = []
    for wrapper in wrappers:
        wd = base._to_dict(wrapper)
        for item in base._as_list(wd.get("elements") or []):
            g = base._guid(item)
            if g:
                out.append(str(g))
    return sorted(set(out))


def opening_bbox(b: TapirBackendV13, wall_guid: str, opening_guid: str) -> dict[str, Any]:
    res = b.raw_call("Get3DBoundingBoxes", {
        "elements": [
            {"elementId": {"guid": wall_guid}},
            {"elementId": {"guid": opening_guid}},
        ]
    })
    return base._to_dict(res)


def reconcile(b: TapirBackendV13, receipt: dict[str, Any], expected_project: str) -> dict[str, Any]:
    if receipt.get("probe") != "AUDIT_T3_DEPENDENCY":
        raise ReconcileError(f"wrong receipt probe: {receipt.get('probe')!r}")
    if receipt.get("status") != "VERIFY_UNAVAILABLE" or receipt.get("stopped_at_stage") != "OPENING_READBACK":
        raise ReconcileError(
            "reconcile is only valid for VERIFY_UNAVAILABLE at OPENING_READBACK; "
            f"got status={receipt.get('status')!r} stage={receipt.get('stopped_at_stage')!r}"
        )

    packages = receipt.get("packages") or {}
    expected_pkg = {t3.PKG01: "COMPLETED", t3.PKG02: "COMPLETED", t3.PKG04: "RUNNING"}
    if packages != expected_pkg:
        raise ReconcileError(f"unexpected package states: {packages!r}")

    wall_guid, opening_guid = receipt_guids(receipt)
    origin = receipt_origin(receipt)

    ok, why = b.available()
    if not ok:
        raise ReconcileError(f"backend unavailable: {why}")
    if b.addon_version() != t3.ADDON:
        raise ReconcileError(f"Tapir version {b.addon_version()!r} != {t3.ADDON!r}")

    info = b.project_info()
    if not project_ok(info, expected_project):
        raise ReconcileError(f"project mismatch: {info!r}")

    walls = set(b.elements_by_type("Wall") or [])
    openings = set(b.elements_by_type("Opening") or [])
    if wall_guid not in walls:
        raise ReconcileError(f"host wall no longer exists: {wall_guid}")
    if opening_guid not in openings:
        raise ReconcileError(f"Opening no longer exists: {opening_guid}")

    # Re-check the confirmed host wall before trusting any relation result.
    stories = b.stories()
    wall_obs = t2c.observe(b, wall_guid, stories)
    wall_checks = t2c.geometry_checks(wall_obs, t3.wall_segment(origin))
    if not all(wall_checks.values()):
        raise ReconcileError(f"host wall drifted: checks={wall_checks}; obs={wall_obs}")

    connected = connected_openings(b, wall_guid)
    if connected != [opening_guid]:
        raise ReconcileError(
            f"owner relation mismatch/ambiguous: expected only {opening_guid}, got {connected}"
        )

    bbox = opening_bbox(b, wall_guid, opening_guid)

    return {
        "probe": "AUDIT_T3_DEPENDENCY_RECONCILE",
        "version": VER,
        "generated_at": now(),
        "source_receipt_status": receipt.get("status"),
        "source_stopped_at_stage": receipt.get("stopped_at_stage"),
        "archicad": info,
        "origin": list(origin),
        "artifacts": {
            "host_wall_guid": wall_guid,
            "opening_guid": opening_guid,
        },
        "results": {
            "host_wall_exists": True,
            "opening_exists": True,
            "host_wall_geometry_stable": True,
            "host_wall_checks": wall_checks,
            "connected_openings_from_host_wall": connected,
            "opening_bound_to_confirmed_wall": True,
            "dependency_order_preserved_from_source_receipt": True,
            "bbox_observation_advisory_only": bbox,
            "mutations": 0,
        },
        "limitations": {
            "opening_type_specific_details": "UNAVAILABLE in Tapir 1.5.9 GetDetailsOfElements: Not yet supported element type",
            "opening_size_machine_certified": False,
            "opening_base_point_machine_certified": False,
            "note": "T3 dependency/owner binding is reconciled. Opening geometry still requires visual confirmation or a future independent read-back capability.",
        },
        "verdicts": {
            "audit_t3_dependency_machine_go": True,
            "owner_binding_reconciled": True,
            "manual_visual_check_required": True,
            "create_opening_production_safe": False,
            "production_integration_ready": False,
        },
        "blocked_by": [
            "manual_visual_check_pending",
            "opening_geometry_readback_unavailable",
            "live_T4_T7_not_run",
        ],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--expect-project", required=True)
    ap.add_argument("--port", type=int, default=19723)
    ap.add_argument("--receipt", required=True)
    ap.add_argument("--report", required=True)
    a = ap.parse_args()

    if os.path.exists(a.report):
        print(f"STOP: reconcile report already exists: {a.report}", file=sys.stderr)
        return 1

    try:
        receipt = read_json(a.receipt)
        report = reconcile(TapirBackendV13(port=a.port), receipt, a.expect_project)
        base.write_json_atomic(a.report, report)
        print("AUDIT T3 DEPENDENCY RECONCILED")
        print("host wall GUID     :", report["artifacts"]["host_wall_guid"])
        print("opening GUID       :", report["artifacts"]["opening_guid"])
        print("OWNER BINDING      : OK via GetConnectedElements")
        print("DEPENDENCY ORDER   : preserved")
        print("MUTATIONS          : 0")
        print("OPENING GEOMETRY   : visual check still required")
        print("report             :", a.report)
        return 0
    except Exception as e:
        print(f"RECONCILE STOP: {type(e).__name__}: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
