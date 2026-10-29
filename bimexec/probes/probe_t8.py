#!/usr/bin/env python3
"""BIMEXEC T8: durable triple-delivery audit at the reference Executor boundary.

This is not an HTTP transport test: the repository has no HTTP service.  It
tests the submission boundary directly with the real reference Executor and an
in-memory FakeAdapter; neither live Archicad nor the production Router is used.
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "reference"))

from bimexec.adapters import FakeAdapter, FakeArchicad, Faults
from bimexec.executor import Executor
from bimexec.states import JobState
from bimexec.verify import Capability, CapabilityMatrix


class T8Stop(RuntimeError):
    pass


PROJECT = {
    "port": 19723, "project_path": "/pln/sandbox.pln", "project_name": "SANDBOX",
    "is_untitled": False, "is_teamwork": False, "archicad_version": "29", "archicad_build": "29.0.0",
}
STORIES = [{"name": "Ground Floor", "elevation": 0.0}]


def matrix() -> CapabilityMatrix:
    capabilities = CapabilityMatrix()
    capabilities.add(Capability(
        op="create_wall", exec_backend="FakeAdapter",
        readback_backends=["guid", "filter", "marker", "count"],
        readable_fields={"exists", "type", "story", "layer", "marker_exact", "ref_line", "length", "height", "thickness", "angle", "count_delta"},
        marker_medium="element_id", marker_search_exact=True, marker_search_prefix=True,
        count_by_type=True, production_safe=True, probe_certified=True,
        duplicate_detection="PREFIX", adapter_version="t8-fake",
    ))
    return capabilities


def plan(*, x: float = 1.5) -> dict:
    return {
        "bimexec": 1, "schema_version": "1.0", "job": "T8_TRIPLE_DELIVERY", "mode": "strict",
        "units": {"length": "m", "angle": "deg"}, "origin": "probe",
        "packages": [{"id": "PKG01", "type": "walls", "depends_on": [], "operations": [{
            "op": "create_wall", "id": "W_PRIMARY",
            "story": {"name": "Ground Floor", "elevation": 0.0}, "layer": "A-WALL",
            "from": [x, 2.5], "to": [x + 5.0, 2.5], "height": 3.0, "thickness": 0.30,
            "reference_line": "center", "base_level": 0.0, "top_link": "absolute",
            "verify": {
                "type": "Wall", "story": {"name": "Ground Floor", "elevation": 0.0}, "layer": "A-WALL",
                "marker_exact": True, "ref_line": {"from": [x, 2.5], "to": [x + 5.0, 2.5], "tolerance": 0.01},
                "length": {"expected": 5.0, "tolerance": 0.05}, "height": {"expected": 3.0, "tolerance": 0.001},
                "thickness": {"expected": 0.30, "tolerance": 0.001}, "count_delta": {"Wall": 1},
            },
        }]}],
    }


def executor_for(workdir: str, archicad: FakeArchicad, *, faults: Faults | None = None) -> tuple[Executor, FakeAdapter]:
    adapter = FakeAdapter(archicad, faults or Faults())
    executor = Executor(adapter, matrix(), os.path.join(workdir, "t8.journal.jsonl"),
                        lock_path=os.path.join(workdir, "t8.lock"), write_gate=True)
    executor.confirm_token = "t8-test-token"
    return executor, adapter


def triple_delivery(workdir: str) -> dict:
    """Delivery #1 runs; #2 and #3 only submit against the durable journal."""
    archicad = FakeArchicad(PROJECT, STORIES)
    first, first_adapter = executor_for(workdir, archicad)
    first_job = first.submit(plan())
    first_status = first.run()
    first.journal.close()

    second, second_adapter = executor_for(workdir, archicad)
    second_job = second.submit(plan())
    second_status = second.job_state
    second.journal.close()

    third, third_adapter = executor_for(workdir, archicad)
    third_job = third.submit(plan())
    third_status = third.job_state
    third.journal.close()

    return {
        "job_ids": [first_job.job_id, second_job.job_id, third_job.job_id],
        "statuses": [first_status.value, second_status.value, third_status.value],
        "create_wall_dispatches": sum(adapter.calls.count("create_wall") for adapter in (first_adapter, second_adapter, third_adapter)),
        "elements": len(archicad.elements),
        "second_submit_called_run": False,
        "third_submit_called_run": False,
    }


def write_report_once(path: str, report: dict) -> None:
    if os.path.exists(path):
        raise T8Stop(f"T8 evidence already exists: {path}")
    parent = os.path.dirname(os.path.abspath(path))
    os.makedirs(parent, exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="T8 reference-Executor triple-delivery audit")
    parser.add_argument("--out", default="t8_report.json")
    args = parser.parse_args(argv)
    workdir = args.out + ".work"
    os.makedirs(workdir, exist_ok=True)
    result = triple_delivery(workdir)
    report = {
        "probe": "T8", "boundary": "reference_executor_submission_not_http_transport",
        "contract": {"deliveries": 3, "dispatches": 1, "duplicate_submit_runs": 0}, "result": result,
    }
    write_report_once(args.out, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if (result["statuses"] == [JobState.COMPLETED.value] * 3 and result["create_wall_dispatches"] == 1 and result["elements"] == 1) else 1


if __name__ == "__main__":
    raise SystemExit(main())
