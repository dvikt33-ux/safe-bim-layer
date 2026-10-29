#!/usr/bin/env python3
"""BIMEXEC T9: production-verifier negative control, entirely in memory.

This audit exercises the same production ``bimexec.verify.evaluate`` used by
the reference Executor.  The initial wall is seeded in FakeArchicad only to
obtain a deterministic read-back observation; no live Archicad, Router,
dispatch, retry, dependent operation, or post-verify mutation is involved.
"""
from __future__ import annotations

import copy
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "reference"))

from bimexec.adapters import FakeAdapter, FakeArchicad
from bimexec.verify import Capability, CheckVerdict, evaluate


class T9Stop(RuntimeError):
    pass


PROJECT = {
    "port": 19723, "project_path": "/pln/sandbox.pln", "project_name": "SANDBOX",
    "is_untitled": False, "is_teamwork": False, "archicad_version": "29", "archicad_build": "29.0.0",
}
STORY = {"name": "Ground Floor", "elevation": 0.0}
LAYER = "A-WALL"
MARKER = "BX:T9:WALL:seed"
FROM = [1.5, 2.5]
TO = [6.5, 2.5]
HEIGHT = 3.0
THICKNESS = 0.30


def capability() -> Capability:
    return Capability(
        op="create_wall", exec_backend="FakeAdapter",
        readable_fields={"exists", "type", "story", "layer", "marker_exact", "ref_line", "length", "height", "thickness", "angle", "count_delta"},
    )


def correct_spec() -> dict:
    return {
        "type": "Wall", "story": dict(STORY), "layer": LAYER, "marker_exact": {"exact": MARKER},
        "ref_line": {"from": list(FROM), "to": list(TO), "tolerance": 0.01},
        "length": {"expected": 5.0, "tolerance": 0.05},
        "height": {"expected": HEIGHT, "tolerance": 0.001},
        "thickness": {"expected": THICKNESS, "tolerance": 0.001},
        "count_delta": {"Wall": 1},
    }


def deterministic_observation() -> tuple[FakeArchicad, FakeAdapter, dict]:
    """Read a pre-seeded FakeArchicad wall; no adapter mutation is used."""
    archicad = FakeArchicad(PROJECT, [STORY])
    wall = archicad.add(
        type="Wall", story=dict(STORY), layer=LAYER,
        ref_line={"from": list(FROM), "to": list(TO)}, height=HEIGHT, thickness=THICKNESS, marker=MARKER,
    )
    adapter = FakeAdapter(archicad)
    details = adapter.get_details(wall.guid)
    assert details is not None
    observation = {key: value for key, value in details.items() if value is not None}
    observation.update({"exists": True, "marker": MARKER, "count_delta": {"Wall": 1}, "paths": ["guid", "filter", "marker", "count"]})
    return archicad, adapter, observation


def run_t9() -> dict:
    """Evaluate one correct and two intentionally incorrect expectations."""
    archicad, adapter, observation = deterministic_observation()
    spec = correct_spec()
    op = {"op": "create_wall", "id": "T9_WALL"}
    cap = capability()

    good, _ = evaluate(op, spec, observation, cap)
    bad_height_spec = copy.deepcopy(spec)
    bad_height_spec["height"]["expected"] = HEIGHT + 0.5
    bad_height, _ = evaluate(op, bad_height_spec, observation, cap)
    bad_ref_line_spec = copy.deepcopy(spec)
    bad_ref_line_spec["ref_line"]["from"][0] += 0.5
    bad_ref_line_spec["ref_line"]["to"][0] += 0.5
    bad_ref_line, _ = evaluate(op, bad_ref_line_spec, observation, cap)

    return {
        "correct_verdict": good.value,
        "wrong_height_verdict": bad_height.value,
        "wrong_ref_line_verdict": bad_ref_line.value,
        "result": "VERIFY_FAILED" if bad_height is CheckVerdict.FAILED and bad_ref_line is CheckVerdict.FAILED else "UNEXPECTED",
        "retry_count": 0,
        "dependent_dispatch_count": 0,
        "adapter_mutation_calls": [call for call in adapter.calls if call in {"create_wall", "set_marker"}],
        "elements_after_verify": len(archicad.elements),
    }


def write_report_once(path: str, report: dict) -> None:
    if os.path.exists(path):
        raise T9Stop(f"T9 evidence already exists: {path}")
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

    parser = argparse.ArgumentParser(description="T9 production-verifier negative-control audit")
    parser.add_argument("--out", default="t9_report.json")
    args = parser.parse_args(argv)
    result = run_t9()
    report = {
        "probe": "T9", "boundary": "production_evaluate_with_in_memory_fake_observation",
        "contract": {"correct_expected_geometry": "OK", "wrong_expected_geometry": "VERIFY_FAILED", "retry": 0, "dependent_dispatch": 0},
        "result": result,
    }
    write_report_once(args.out, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if (
        result["correct_verdict"] == CheckVerdict.OK.value
        and result["wrong_height_verdict"] == CheckVerdict.FAILED.value
        and result["wrong_ref_line_verdict"] == CheckVerdict.FAILED.value
        and result["result"] == "VERIFY_FAILED"
        and not result["adapter_mutation_calls"]
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
