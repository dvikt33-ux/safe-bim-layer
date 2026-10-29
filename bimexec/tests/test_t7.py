"""Focused deterministic regressions for the canonical T7 F2 audit."""
from __future__ import annotations

import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "probes"))
sys.path.insert(0, os.path.join(ROOT, "reference"))
from probe_t7 import PAUSED_VERIFY_UNAVAILABLE, T7Stop, result_for, run_t7, write_report_once
from bimexec.adapters import Faults
from bimexec.states import JobState, OpState


TESTS = []
def test(fn): TESTS.append((fn.__name__, fn)); return fn


@test
def unavailable_after_known_apply_pauses_and_blocks_dependents():
    with tempfile.TemporaryDirectory() as d:
        executor, adapter = run_t7(d)
        result = result_for(executor, adapter)
    assert result["job_state"] == JobState.PAUSED.value
    assert result["pause_reason"] == "VERIFY_UNAVAILABLE"
    assert result["primary_op_state"] == OpState.UNAVAILABLE.value
    assert result["primary_dispatch_count"] == 1
    assert result["dependent_dispatch_count"] == 0
    assert result["retry_count"] == 0


@test
def unavailable_does_not_automatically_retry():
    with tempfile.TemporaryDirectory() as d:
        executor, adapter = run_t7(d)
        result = result_for(executor, adapter)
    assert adapter.calls.count("create_wall") == 1
    assert result["retry_count"] == 0


@test
def ordinary_geometry_mismatch_is_verify_failed():
    from tests.test_p0 import make, plan
    executor, _, _ = make(Faults(wrong_geometry=True))
    executor.submit(plan())
    assert executor.run() is JobState.PAUSED
    assert executor.job.ops["PKG01/W_F1_EXT_001"].state is OpState.VERIFIED_FAILED
    assert executor.paused_reason == "VERIFIED_FAILED"
    assert executor.paused_reason != "VERIFY_UNAVAILABLE"


@test
def pre_dispatch_and_backend_failures_are_not_unavailable():
    from tests.test_p0 import make, plan
    executor, archicad, _ = make()
    archicad.layer_state["locked"].add("A-WALL")
    executor.submit(plan())
    assert executor.run() is JobState.PAUSED
    assert executor.paused_reason.startswith("PRECONDITION_FAILED")
    assert executor.paused_reason != "VERIFY_UNAVAILABLE"
    assert executor.adapter.calls.count("create_wall") == 0


@test
def evidence_is_durable_and_not_overwritten():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "t7-report.json")
        report = {"probe": "T7", "result": {"status": PAUSED_VERIFY_UNAVAILABLE}}
        write_report_once(path, report)
        try:
            write_report_once(path, {"replacement": True})
        except T7Stop:
            pass
        else:
            raise AssertionError("T7 evidence must not be overwritten")
        with open(path, encoding="utf-8") as fh:
            assert json.load(fh) == report
