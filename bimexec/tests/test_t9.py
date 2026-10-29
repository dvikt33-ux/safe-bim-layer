"""Canonical T9 production-verifier negative-control regressions."""
from __future__ import annotations

import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "probes"))

from probe_t9 import T9Stop, run_t9, write_report_once


TESTS = []
def test(fn): TESTS.append((fn.__name__, fn)); return fn


@test
def correct_spec_passes_with_production_evaluate():
    assert run_t9()["correct_verdict"] == "OK"


@test
def wrong_height_fails_with_production_evaluate():
    result = run_t9()
    assert result["wrong_height_verdict"] == "FAILED"
    assert result["result"] == "VERIFY_FAILED"


@test
def wrong_ref_line_fails_with_production_evaluate():
    assert run_t9()["wrong_ref_line_verdict"] == "FAILED"


@test
def failed_negative_control_is_not_unavailable_or_inconclusive():
    result = run_t9()
    for verdict in (result["wrong_height_verdict"], result["wrong_ref_line_verdict"]):
        assert verdict == "FAILED"
        assert verdict not in {"UNAVAILABLE", "INCONCLUSIVE"}
    assert result["retry_count"] == 0
    assert result["dependent_dispatch_count"] == 0
    assert result["adapter_mutation_calls"] == []
    assert result["elements_after_verify"] == 1


@test
def evidence_is_durable_and_not_overwritten():
    with tempfile.TemporaryDirectory() as workdir:
        path = os.path.join(workdir, "t9-report.json")
        report = {"probe": "T9", "result": {"status": "VERIFY_FAILED"}}
        write_report_once(path, report)
        try:
            write_report_once(path, {"replacement": True})
        except T9Stop:
            pass
        else:
            raise AssertionError("T9 evidence must not be overwritten")
        with open(path, encoding="utf-8") as handle:
            assert json.load(handle) == report
