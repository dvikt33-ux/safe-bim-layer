#!/usr/bin/env python3
"""BIMEXEC T6: durable, read-only manual model-drift probe.

Run ``preflight`` before manually moving the source wall.  It writes the
baseline once.  After the manual move, run ``verify`` against that evidence.
The second read-back returns ``PAUSED(MODEL_DRIFT)`` before a dependent
operation can be dispatched.  This probe deliberately has no mutation API.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import sys
from typing import Any, Callable

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from backends import Backend, write_json_atomic  # noqa: E402
from backends_v13 import TapirBackendV13, build_backends_v13  # noqa: E402
import probe_t2_connections_v13 as t2c  # noqa: E402

PROBE_VERSION = "1.1"
PAUSED_MODEL_DRIFT = "PAUSED(MODEL_DRIFT)"


class T6Stop(RuntimeError):
    """Fail-closed preflight or evidence error."""


def _project_path(project: dict[str, Any]) -> str:
    return str(project.get("project_path") or project.get("path") or "")


def _geometry(details: dict[str, Any]) -> dict[str, Any]:
    """Keep only geometry material to the T6 wall comparison."""
    line = details.get("ref_line") or {}
    start, end = line.get("from"), line.get("to")
    if not isinstance(start, list) or not isinstance(end, list):
        raise T6Stop("baseline/read-back has no wall ref_line geometry")
    return {"ref_line": {"from": start, "to": end},
            "height": details.get("height"), "thickness": details.get("thickness")}


def _snapshot(backend: Backend, guid: str, stories: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    # Tapir must use the proven v1.3 details payload and normalization.  The
    # legacy backend returns no usable ref_line on AC29/Tapir 1.5.9.
    if isinstance(backend, TapirBackendV13):
        if stories is None:
            stories = backend.stories()
        details = t2c.observe(backend, guid, stories)
    else:
        details = backend.details(guid)
    if not details:
        raise T6Stop(f"details unavailable for {guid}")
    return {"guid": guid, "details": details, "geometry": _geometry(details)}


def _validate_binding(backend: Backend, source_guid: str, dependent_guid: str,
                      expect_project: str) -> dict[str, Any]:
    ok, reason = backend.available()
    if not ok:
        raise T6Stop(f"backend unavailable: {reason}")
    project = backend.project_info()
    actual = _project_path(project)
    if not actual or os.path.normcase(actual) != os.path.normcase(expect_project):
        raise T6Stop(f"project mismatch: expected {expect_project!r}, got {actual!r}")
    missing = [g for g in (source_guid, dependent_guid) if g not in set(backend.all_elements())]
    if missing:
        raise T6Stop(f"GUID not found: {', '.join(missing)}")
    return project


def preflight(backend: Backend, source_guid: str, dependent_guid: str,
              expect_project: str) -> dict[str, Any]:
    """Create a durable baseline payload; performs no model mutation."""
    project = _validate_binding(backend, source_guid, dependent_guid, expect_project)
    stories = backend.stories() if isinstance(backend, TapirBackendV13) else None
    return {
        "probe": "T6", "version": PROBE_VERSION, "mode": "preflight-read-only",
        "host": f"{platform.system()} {platform.release()}", "project": project,
        "source": _snapshot(backend, source_guid, stories),
        "dependent": {"guid": dependent_guid},
        "contract": {"manual_action": "move source wall geometry between operations",
                     "expected_pause": PAUSED_MODEL_DRIFT,
                     "dependent_mutation_allowed_after_drift": False},
    }


def write_baseline_once(path: str, receipt: dict[str, Any]) -> None:
    if os.path.exists(path):
        raise T6Stop(f"baseline evidence already exists: {path}")
    write_json_atomic(path, receipt)


def read_baseline(path: str) -> dict[str, Any]:
    try:
        with open(path, encoding="utf-8") as fh:
            receipt = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        raise T6Stop(f"baseline evidence unavailable: {exc}") from exc
    try:
        if receipt["probe"] != "T6" or not receipt["source"]["guid"] or not receipt["dependent"]["guid"]:
            raise KeyError("invalid T6 fields")
        _geometry(receipt["source"]["details"])
        if not _project_path(receipt["project"]):
            raise KeyError("project")
    except (KeyError, TypeError, T6Stop) as exc:
        raise T6Stop("baseline evidence is invalid") from exc
    return receipt


def verify_after_manual_move(backend: Backend, baseline: dict[str, Any],
                             dependent_dispatch: Callable[[], None] | None = None) -> dict[str, Any]:
    """Second read-back; dispatcher exists only for offline ordering tests."""
    source_guid = baseline["source"]["guid"]
    dependent_guid = baseline["dependent"]["guid"]
    _validate_binding(backend, source_guid, dependent_guid, _project_path(baseline["project"]))
    stories = backend.stories() if isinstance(backend, TapirBackendV13) else None
    current = _snapshot(backend, source_guid, stories)
    expected = baseline["source"]["geometry"]
    if current["geometry"] != expected:
        return {"probe": "T6", "status": PAUSED_MODEL_DRIFT,
                "source_guid": source_guid, "dependent_guid": dependent_guid,
                "baseline_geometry": expected, "current_geometry": current["geometry"],
                "dependent_dispatch_count": 0}
    if dependent_dispatch is not None:
        dependent_dispatch()
    return {"probe": "T6", "status": "UNCHANGED_GEOMETRY",
            "source_guid": source_guid, "dependent_guid": dependent_guid,
            "dependent_dispatch_count": 1 if dependent_dispatch else 0}


def _backend(args: argparse.Namespace) -> Backend:
    errors = []
    for backend in build_backends_v13(args.backend_order, args.port, args.mcp_url, args.backend_module):
        ok, reason = backend.available()
        if ok:
            return backend
        errors.append(f"{backend.name}: {reason}")
    raise T6Stop("no available backend: " + " | ".join(errors))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="T6 durable read-only drift probe")
    sub = ap.add_subparsers(dest="command", required=True)
    pre = sub.add_parser("preflight", help="write baseline before manual wall move")
    pre.add_argument("--source-guid", required=True)
    pre.add_argument("--dependent-guid", required=True)
    pre.add_argument("--expect-project", required=True)
    pre.add_argument("--out", default="t6_baseline.json")
    verify = sub.add_parser("verify", help="compare second read-back with baseline")
    verify.add_argument("--baseline", required=True)
    for parser in (pre, verify):
        parser.add_argument("--backend-order", default="tapir,mcp")
        parser.add_argument("--backend-module", default=None)
        parser.add_argument("--port", type=int, default=None)
        parser.add_argument("--mcp-url", default="http://127.0.0.1:8001/mcp")
    args = ap.parse_args(argv)
    try:
        backend = _backend(args)
        if args.command == "preflight":
            write_baseline_once(args.out, preflight(backend, args.source_guid, args.dependent_guid, args.expect_project))
            print("T6 PREFLIGHT OK: durable baseline written; no mutation attempted.")
            return 0
        result = verify_after_manual_move(backend, read_baseline(args.baseline))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if result["status"] == PAUSED_MODEL_DRIFT else 0
    except T6Stop as exc:
        print(f"T6 STOP: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
