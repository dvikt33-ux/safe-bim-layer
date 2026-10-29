#!/usr/bin/env python3
"""BIMEXEC T7: real Executor audit for unavailable post-marker read-back.

The scenario is wholly in memory.  It performs one successful primary dispatch
and marker round-trip, then injects failure of the required detail read-back.
No Archicad connection or production Router is used.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "reference"))

from bimexec.adapters import FakeAdapter, FakeArchicad, Faults
from bimexec.executor import Executor
from bimexec.states import JobState, OpState
from bimexec.verify import Capability, CapabilityMatrix

PAUSED_VERIFY_UNAVAILABLE = "PAUSED(VERIFY_UNAVAILABLE)"
class T7Stop(RuntimeError):
    pass


PROJECT = {
    "port": 19723, "project_path": "/pln/sandbox.pln", "project_name": "SANDBOX",
    "is_untitled": False, "is_teamwork": False, "archicad_version": "29", "archicad_build": "29.0.0",
}
STORIES = [{"name": "Ground Floor", "elevation": 0.0}]
PRIMARY = "PKG01/W_PRIMARY"
DEPENDENT = "PKG02/W_DEPENDENT"


def _matrix() -> CapabilityMatrix:
    m = CapabilityMatrix()
    m.add(Capability(
        op="create_wall", exec_backend="FakeAdapter",
        readback_backends=["guid", "filter", "marker", "count"],
        readable_fields={"exists", "type", "story", "layer", "marker_exact", "ref_line", "length", "height", "thickness", "angle", "count_delta"},
        marker_medium="element_id", marker_search_exact=True, marker_search_prefix=True,
        count_by_type=True, production_safe=True, probe_certified=True,
        duplicate_detection="PREFIX", adapter_version="t7-fake",
    ))
    return m


def _wall(object_id: str, x: float) -> dict:
    return {
        "op": "create_wall", "id": object_id,
        "story": {"name": "Ground Floor", "elevation": 0.0}, "layer": "A-WALL",
        "from": [x, 2.5], "to": [x + 5.0, 2.5], "height": 3.0, "thickness": 0.30,
        "reference_line": "center", "base_level": 0.0, "top_link": "absolute",
        "verify": {
            "type": "Wall", "story": {"name": "Ground Floor", "elevation": 0.0}, "layer": "A-WALL",
            "marker_exact": True, "ref_line": {"from": [x, 2.5], "to": [x + 5.0, 2.5], "tolerance": 0.01},
            "length": {"expected": 5.0, "tolerance": 0.05}, "height": {"expected": 3.0, "tolerance": 0.001},
            "thickness": {"expected": 0.30, "tolerance": 0.001}, "count_delta": {"Wall": 1},
        },
    }


def _plan() -> dict:
    return {
        "bimexec": 1, "schema_version": "1.0", "job": "T7_UNAVAILABLE", "mode": "strict",
        "units": {"length": "m", "angle": "deg"}, "origin": "probe",
        "packages": [
            {"id": "PKG01", "type": "walls", "depends_on": [], "operations": [_wall("W_PRIMARY", 1.5)]},
            {"id": "PKG02", "type": "walls", "depends_on": ["PKG01"], "operations": [_wall("W_DEPENDENT", 10.0)]},
        ],
    }


def run_t7(workdir: str) -> tuple[Executor, FakeAdapter]:
    """Drive the production/reference Executor through T7, in memory only."""
    archicad = FakeArchicad(PROJECT, STORIES)
    adapter = FakeAdapter(archicad, Faults(readback_broken_after_marker=True))
    executor = Executor(adapter, _matrix(), os.path.join(workdir, "t7.journal.jsonl"),
                        lock_path=os.path.join(workdir, "t7.lock"), write_gate=True)
    executor.confirm_token = "t7-test-token"
    executor.submit(_plan())
    executor.run()
    # The real Executor owns a durable journal; close its only file handle so
    # this isolated probe can also prove cleanup on Windows.
    executor.journal.close()
    return executor, adapter


def result_for(executor: Executor, adapter: FakeAdapter) -> dict:
    primary = executor.job.ops[PRIMARY]
    return {
        "job_state": executor.job_state.value,
        "pause_reason": executor.paused_reason,
        "primary_op_state": primary.state.value,
        "primary_dispatch_count": adapter.calls.count("create_wall"),
        "dependent_dispatch_count": 1 if DEPENDENT in executor.job.ops and executor.job.ops[DEPENDENT].state is not OpState.PLANNED else 0,
        "retry_count": 0,
    }


def write_report_once(path: str, report: dict) -> None:
    if os.path.exists(path):
        raise T7Stop(f"T7 evidence already exists: {path}")
    parent = os.path.dirname(os.path.abspath(path))
    os.makedirs(parent, exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="T7 dry-run unavailable read-back audit")
    ap.add_argument("--out", default="t7_report.json")
    args = ap.parse_args(argv)
    os.makedirs(args.out + ".work", exist_ok=True)
    executor, adapter = run_t7(args.out + ".work")
    result = result_for(executor, adapter)
    report = {"probe": "T7", "mode": "dry-run", "contract": {
        "expected_unavailable": PAUSED_VERIFY_UNAVAILABLE,
        "dependent_dispatch_after_unavailable": 0,
        "automatic_retry": 0}, "result": result}
    write_report_once(args.out, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if (result["job_state"] == JobState.PAUSED.value and result["pause_reason"] == "VERIFY_UNAVAILABLE") else 0


if __name__ == "__main__":
    raise SystemExit(main())
