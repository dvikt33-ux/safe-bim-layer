"""Focused deterministic regressions for the canonical T7 F2 audit."""
from __future__ import annotations

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "probes"))
from probe_t7 import (OP_UNKNOWN, PAUSED_VERIFY_UNAVAILABLE, T7Harness, T7Stop,
                      VERIFY_FAILED, write_report_once)


TESTS = []
def test(fn): TESTS.append((fn.__name__, fn)); return fn


@test
def unavailable_after_known_apply_pauses_and_blocks_dependents():
    calls = []
    result = T7Harness(readback="unavailable").run(lambda: calls.append("next"))
    assert result["status"] == PAUSED_VERIFY_UNAVAILABLE
    assert result["dependent_dispatch_count"] == 0
    assert result["retry_count"] == 0
    assert calls == []


@test
def unavailable_does_not_automatically_retry():
    h = T7Harness(readback="unavailable")
    result = h.run()
    assert result["dispatch_count"] == 1
    assert result["retry_count"] == 0


@test
def ordinary_geometry_mismatch_is_verify_failed():
    result = T7Harness(readback="mismatch").run()
    assert result["status"] == VERIFY_FAILED
    assert result["status"] != PAUSED_VERIFY_UNAVAILABLE


@test
def pre_dispatch_and_backend_failures_are_not_unavailable():
    for reason in ("PRE_DISPATCH_FAILED", "BACKEND_UNAVAILABLE", OP_UNKNOWN):
        result = T7Harness(pre_dispatch_failure=reason).run()
        assert result["status"] == reason
        assert result["status"] != PAUSED_VERIFY_UNAVAILABLE
        assert result["dependent_dispatch_count"] == 0


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
