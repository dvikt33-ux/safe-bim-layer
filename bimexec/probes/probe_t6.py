#!/usr/bin/env python3
"""BIMEXEC T6: read-only preflight for the manual model-drift test.

The actual live mutation is intentionally not performed by the default mode.
The preflight binds to the expected project, resolves one source wall and one
dependent operation target, and records their read-back snapshots.  An
operator can then use this receipt to perform the canonical manual move
between operations; the dependent mutation must not be dispatched after the
next read-back reports ``PAUSED(MODEL_DRIFT)``.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import sys
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from backends import Backend, build_backends, write_json_atomic  # noqa: E402

PROBE_VERSION = "1.0"


def _snapshot(backend: Backend, guid: str) -> dict[str, Any]:
    details = backend.details(guid)
    if not details:
        raise RuntimeError(f"details unavailable for {guid}")
    return {"guid": guid, "details": details}


def preflight(backend: Backend, source_guid: str, dependent_guid: str,
              expect_project: str) -> dict[str, Any]:
    """Perform only read-only checks and return a durable T6 receipt."""
    ok, reason = backend.available()
    if not ok:
        raise RuntimeError(f"backend unavailable: {reason}")
    project = backend.project_info()
    actual = str(project.get("project_path") or project.get("path") or "")
    if os.path.normcase(actual) != os.path.normcase(expect_project):
        raise RuntimeError(f"project mismatch: expected {expect_project!r}, got {actual!r}")
    guids = set(backend.all_elements())
    missing = [g for g in (source_guid, dependent_guid) if g not in guids]
    if missing:
        raise RuntimeError(f"GUID not found: {', '.join(missing)}")
    return {
        "probe": "T6",
        "version": PROBE_VERSION,
        "mode": "preflight-read-only",
        "host": f"{platform.system()} {platform.release()}",
        "project": project,
        "source": _snapshot(backend, source_guid),
        "dependent": {"guid": dependent_guid},
        "contract": {
            "manual_action": "move source geometry between operations",
            "expected_pause": "PAUSED(MODEL_DRIFT)",
            "dependent_mutation_allowed_after_drift": False,
        },
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="T6 read-only live preflight")
    ap.add_argument("--source-guid", required=True)
    ap.add_argument("--dependent-guid", required=True,
                    help="GUID reserved for the dependent operation; never written in preflight")
    ap.add_argument("--expect-project", required=True)
    ap.add_argument("--out", default="t6_preflight.json")
    ap.add_argument("--backend-order", default="tapir,mcp")
    ap.add_argument("--backend-module", default=None)
    ap.add_argument("--port", type=int, default=None)
    ap.add_argument("--mcp-url", default="http://127.0.0.1:8001/mcp")
    args = ap.parse_args(argv)
    if os.path.exists(args.out):
        print(f"STOP: receipt already exists: {args.out}", file=sys.stderr)
        return 1
    errors: list[str] = []
    for backend in build_backends(args.backend_order, args.port, args.mcp_url,
                                  args.backend_module):
        try:
            receipt = preflight(backend, args.source_guid, args.dependent_guid,
                                args.expect_project)
            write_json_atomic(args.out, receipt)
            print(json.dumps(receipt, ensure_ascii=False, indent=2))
            print("T6 PREFLIGHT OK: read-only; no live mutation was attempted.")
            return 0
        except Exception as exc:
            errors.append(f"{backend.name}: {type(exc).__name__}: {exc}")
    print("T6 PREFLIGHT STOP: " + " | ".join(errors), file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
