"""Focused regressions for audit T4 timeout-after-apply. No Archicad connection."""
from __future__ import annotations

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PROBES = os.path.join(ROOT, "probes")
sys.path.insert(0, PROBES)

import probe_t4_timeout_v13 as t4
import reconcile_t4_timeout_v13 as r4
import probe_t2_connections_v13 as t2c
import probe_t3_dependency_v13 as t3
from tests.test_t3_dependency import FakeT3Backend, _apply_wall

TESTS: list[tuple[str, object]] = []


def test(fn):
    TESTS.append((fn.__name__, fn))
    return fn


def _argv_probe(out: str, *, with_origin: bool = True) -> list[str]:
    args = [
        "probe_t4_timeout_v13.py",
        "--expect-project", r"C:\Users\Admin\Downloads\MCP_TEST.pln",
        "--port", "19723",
        "--out", out,
        "--allow-write",
        "--i-understand-this-writes-to-archicad",
    ]
    if with_origin:
        args += ["--origin-x", "20.0", "--origin-y", "20.0"]
    return args


def _source_receipt(path: str, backend: FakeT3Backend, *, valid: bool = True) -> None:
    intended_comp = "COMP-T3-FAKE"
    src = {
        "probe": "AUDIT_T4_TIMEOUT_AFTER_APPLY",
        "version": "1.0",
        "job_state": "PAUSED" if valid else "RUNNING",
        "paused_reason": "OP_UNKNOWN",
        "op_state": "UNKNOWN",
        "dispatch_attempts": 1,
        "baseline_guids": [t2c.WITNESS],
        "baseline_walls": [t2c.WITNESS],
        "baseline_counts": {"Wall": 1, "Opening": 0},
        "origin": [backend.origin[0], backend.origin[1]],
        "intended": {
            "kind": "Wall",
            "story_index": t2c.FLOOR,
            "story_name": t2c.STORY,
            "from": [backend.origin[0], backend.origin[1]],
            "to": [backend.origin[0] + t3.WALL_LENGTH, backend.origin[1]],
            "length": t3.WALL_LENGTH,
            "height": t2c.HEIGHT,
            "thickness": t2c.THICK,
            "referenceLineLocation": t2c.REFLINE,
            "offset": t2c.OFFSET,
            "arcAngle": t2c.ARC,
            "structureType": "Composite",
            "compositeId": intended_comp,
        },
        "injected_fault": {
            "kind": "synthetic_transport_timeout",
            "point": "after_CreateWalls_return_before_outcome_record",
            "mutation_call_returned_to_injector": True,
            "returned_guid_deliberately_not_persisted": True,
        },
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(src, f)


def _run_reconcile(backend: FakeT3Backend, receipt: str, report: str) -> int:
    old_backend = r4.TapirBackendV13
    old_argv = sys.argv[:]
    try:
        r4.TapirBackendV13 = lambda port=19723: backend
        sys.argv = [
            "reconcile_t4_timeout_v13.py",
            "--expect-project", r"C:\Users\Admin\Downloads\MCP_TEST.pln",
            "--port", "19723",
            "--receipt", receipt,
            "--report", report,
        ]
        return r4.main()
    finally:
        r4.TapirBackendV13 = old_backend
        sys.argv = old_argv


@test
def audit_t4_timeout_after_apply_pauses_unknown_once_no_retry():
    backend = FakeT3Backend()
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, "receipt.json")
        old_backend = t4.TapirBackendV13
        old_create = t4.t2c.create_once
        old_argv = sys.argv[:]
        try:
            t4.TapirBackendV13 = lambda port=19723: backend
            t4.t2c.create_once = lambda b, p: [_apply_wall(b, p)]
            sys.argv = _argv_probe(out)
            rc = t4.main()
        finally:
            t4.TapirBackendV13 = old_backend
            t4.t2c.create_once = old_create
            sys.argv = old_argv

        assert rc == 2
        assert backend.wall_calls == 1
        assert len(backend.walls) == 2  # witness + exactly one new wall
        with open(out, "r", encoding="utf-8") as f:
            rec = json.load(f)
        assert rec["job_state"] == "PAUSED"
        assert rec["paused_reason"] == "OP_UNKNOWN"
        assert rec["op_state"] == "UNKNOWN"
        assert rec["dispatch_attempts"] == 1
        assert rec["injected_fault"]["mutation_call_returned_to_injector"] is True
        assert rec["cleanup"]["automatic_retry_allowed"] is False
        assert "candidate_guid" not in rec


@test
def audit_t4_reconcile_offers_adopt_for_one_unique_anchor_readonly():
    backend = FakeT3Backend()
    backend.origin = (20.0, 20.0)
    _apply_wall(backend, t3.wall_payload(backend.origin, "COMP-T3-FAKE"))
    with tempfile.TemporaryDirectory() as d:
        receipt = os.path.join(d, "receipt.json")
        report = os.path.join(d, "report.json")
        _source_receipt(receipt, backend)
        rc = _run_reconcile(backend, receipt, report)
        assert rc == 0
        with open(report, "r", encoding="utf-8") as f:
            rep = json.load(f)
        assert rep["classification"] == "APPLIED_ADOPTABLE_BY_ANCHOR"
        assert rep["recommended_human_decision"] == "ADOPT"
        assert rep["automatic_retry_allowed"] is False
        assert rep["automatic_adopt_performed"] is False
        assert rep["mutations"] == 0
        assert rep["observations"]["wall_count_delta"] == 1


@test
def audit_t4_reconcile_rejects_ambiguous_two_new_walls():
    backend = FakeT3Backend()
    backend.origin = (20.0, 20.0)
    _apply_wall(backend, t3.wall_payload(backend.origin, "COMP-T3-FAKE"))
    # Add a second fresh wall without invoking a second dispatch in the probe under test.
    g2 = "T4-SECOND-FRESH-WALL"
    backend.guids.append(g2)
    backend.walls.add(g2)
    backend.layer_index[g2] = 1
    backend.layer_name[g2] = "Default Layer"
    backend.element_id[g2] = "W-T4-2"
    with tempfile.TemporaryDirectory() as d:
        receipt = os.path.join(d, "receipt.json")
        report = os.path.join(d, "report.json")
        _source_receipt(receipt, backend)
        rc = _run_reconcile(backend, receipt, report)
        assert rc == 2
        with open(report, "r", encoding="utf-8") as f:
            rep = json.load(f)
        assert rep["classification"] == "AMBIGUOUS"
        assert rep["recommended_human_decision"] != "ADOPT"


@test
def audit_t4_reconcile_reports_not_applied_without_candidate():
    backend = FakeT3Backend()
    backend.origin = (20.0, 20.0)
    with tempfile.TemporaryDirectory() as d:
        receipt = os.path.join(d, "receipt.json")
        report = os.path.join(d, "report.json")
        _source_receipt(receipt, backend)
        rc = _run_reconcile(backend, receipt, report)
        assert rc == 2
        with open(report, "r", encoding="utf-8") as f:
            rep = json.load(f)
        assert rep["classification"] == "NOT_APPLIED"
        assert rep["recommended_human_decision"] == "NOT_APPLIED"


@test
def audit_t4_reconcile_refuses_non_unknown_source_before_backend():
    backend = FakeT3Backend()
    with tempfile.TemporaryDirectory() as d:
        receipt = os.path.join(d, "receipt.json")
        report = os.path.join(d, "report.json")
        _source_receipt(receipt, backend, valid=False)
        old_backend = r4.TapirBackendV13
        old_argv = sys.argv[:]
        try:
            r4.TapirBackendV13 = lambda port=19723: (_ for _ in ()).throw(AssertionError("backend must not be constructed"))
            sys.argv = [
                "reconcile_t4_timeout_v13.py",
                "--expect-project", r"C:\Users\Admin\Downloads\MCP_TEST.pln",
                "--receipt", receipt,
                "--report", report,
            ]
            rc = r4.main()
        finally:
            r4.TapirBackendV13 = old_backend
            sys.argv = old_argv
        assert rc == 1
        assert not os.path.exists(report)


@test
def audit_t4_live_requires_explicit_origin_before_backend():
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, "receipt.json")
        old_backend = t4.TapirBackendV13
        old_argv = sys.argv[:]
        try:
            t4.TapirBackendV13 = lambda port=19723: (_ for _ in ()).throw(AssertionError("backend must not be constructed"))
            sys.argv = _argv_probe(out, with_origin=False)
            rc = t4.main()
        finally:
            t4.TapirBackendV13 = old_backend
            sys.argv = old_argv
        assert rc == 1
        assert not os.path.exists(out)
