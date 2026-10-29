"""Focused regressions for audit T5 hard process-kill recovery. No Archicad connection."""
from __future__ import annotations

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PROBES = os.path.join(ROOT, "probes")
sys.path.insert(0, PROBES)

import probe_t5_kill_v13 as t5
import reconcile_t5_kill_v13 as r5
import probe_t2_connections_v13 as t2c
import probe_t3_dependency_v13 as t3
from tests.test_t3_dependency import FakeT3Backend, _apply_wall

TESTS: list[tuple[str, object]] = []


def test(fn):
    TESTS.append((fn.__name__, fn))
    return fn


def _controller(path: str, *, valid: bool = True) -> None:
    obj = {
        "probe": "AUDIT_T5_PROCESS_KILL_CONTROLLER",
        "version": "1.0",
        "killpoint_observed": True,
        "controller_outcome": "HARD_KILL_CONFIRMED" if valid else "CHILD_EXIT_BEFORE_KILLPOINT",
        "child_exit_code": -9,
        "hard_killed_process_scope": "standalone T5 child probe only",
        "archicad_process_killed": False,
        "production_router_killed": False,
        "post_dispatch_model_readback_by_controller": 0,
        "automatic_retry_allowed": False,
        "automatic_adopt_performed": False,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f)


def _source_receipt(path: str, backend: FakeT3Backend, *, valid: bool = True) -> None:
    ox, oy = backend.origin
    src = {
        "probe": "AUDIT_T5_PROCESS_KILL_AFTER_DISPATCH",
        "version": "1.0",
        "job_state": "RUNNING" if valid else "PREPARED",
        "paused_reason": None,
        "op_state": "DISPATCHED" if valid else "PLANNED",
        "dispatch_attempts": 1 if valid else 0,
        "stages": [
            {"stage": "PRECHECK"},
            {"stage": "DISPATCH_INTENT", "attempt": 1},
        ] if valid else [{"stage": "PRECHECK"}],
        "baseline_guids": [t2c.WITNESS],
        "baseline_walls": [t2c.WITNESS],
        "baseline_counts": {"Wall": 1, "Opening": 0},
        "origin": [ox, oy],
        "intended": {
            "kind": "Wall",
            "story_index": t2c.FLOOR,
            "story_name": t2c.STORY,
            "from": [ox, oy],
            "to": [ox + t3.WALL_LENGTH, oy],
            "length": t3.WALL_LENGTH,
            "height": t2c.HEIGHT,
            "thickness": t2c.THICK,
            "referenceLineLocation": t2c.REFLINE,
            "offset": t2c.OFFSET,
            "arcAngle": t2c.ARC,
            "structureType": "Composite",
            "compositeId": "COMP-T3-FAKE",
        },
        "recovery_contract": {
            "intent_without_outcome_means": "OP_UNKNOWN",
            "automatic_retry_allowed": False,
            "automatic_adopt_allowed": False,
        },
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(src, f)


def _run_reconcile(backend: FakeT3Backend, receipt: str, controller: str, report: str) -> int:
    old_backend = r5.TapirBackendV13
    old_argv = sys.argv[:]
    try:
        r5.TapirBackendV13 = lambda port=19723: backend
        sys.argv = [
            "reconcile_t5_kill_v13.py",
            "--expect-project", r"C:\Users\Admin\Downloads\MCP_TEST.pln",
            "--port", "19723",
            "--receipt", receipt,
            "--controller-report", controller,
            "--report", report,
        ]
        return r5.main()
    finally:
        r5.TapirBackendV13 = old_backend
        sys.argv = old_argv


@test
def audit_t5_worker_leaves_durable_intent_without_outcome_at_killpoint():
    backend = FakeT3Backend()
    with tempfile.TemporaryDirectory() as d:
        receipt = os.path.join(d, "receipt.json")
        killpoint = os.path.join(d, "killpoint.json")
        old_create = t5.t2c.create_once
        try:
            t5._prepare_receipt(
                backend,
                expect_project=r"C:\Users\Admin\Downloads\MCP_TEST.pln",
                out=receipt,
                origin=backend.origin,
            )
            t5.t2c.create_once = lambda b, p: [_apply_wall(b, p)]
            try:
                t5.worker_dispatch_until_killpoint(
                    backend,
                    expect_project=r"C:\Users\Admin\Downloads\MCP_TEST.pln",
                    receipt=receipt,
                    killpoint=killpoint,
                    park=False,
                )
                raise AssertionError("killpoint control flow was not reached")
            except t5.KillPointReached:
                pass
        finally:
            t5.t2c.create_once = old_create

        assert backend.wall_calls == 1
        assert os.path.exists(killpoint)
        with open(receipt, "r", encoding="utf-8") as f:
            rec = json.load(f)
        assert rec["job_state"] == "RUNNING"
        assert rec["op_state"] == "DISPATCHED"
        assert rec["dispatch_attempts"] == 1
        assert rec["stages"][-1]["stage"] == "DISPATCH_INTENT"
        assert "candidate_guid" not in rec
        assert "outcome" not in rec
        assert "finished_at" not in rec


@test
def audit_t5_restart_infers_unknown_and_offers_adopt_for_unique_anchor():
    backend = FakeT3Backend()
    backend.origin = (20.0, 20.0)
    _apply_wall(backend, t3.wall_payload(backend.origin, "COMP-T3-FAKE"))
    with tempfile.TemporaryDirectory() as d:
        receipt = os.path.join(d, "receipt.json")
        controller = os.path.join(d, "controller.json")
        report = os.path.join(d, "report.json")
        _source_receipt(receipt, backend)
        _controller(controller)
        rc = _run_reconcile(backend, receipt, controller, report)
        assert rc == 0
        with open(report, "r", encoding="utf-8") as f:
            rep = json.load(f)
        inf = rep["crash_recovery_inference"]
        assert inf["recovered_job_state"] == "PAUSED"
        assert inf["recovered_pause_reason"] == "OP_UNKNOWN"
        assert inf["recovered_op_state"] == "UNKNOWN"
        assert rep["classification"] == "APPLIED_ADOPTABLE_BY_ANCHOR"
        assert rep["recommended_human_decision"] == "ADOPT"
        assert rep["automatic_retry_allowed"] is False
        assert rep["automatic_adopt_performed"] is False
        assert rep["mutations"] == 0
        assert rep["observations"]["wall_count_delta"] == 1


@test
def audit_t5_restart_rejects_ambiguous_two_new_walls():
    backend = FakeT3Backend()
    backend.origin = (20.0, 20.0)
    _apply_wall(backend, t3.wall_payload(backend.origin, "COMP-T3-FAKE"))
    g2 = "T5-SECOND-FRESH-WALL"
    backend.guids.append(g2)
    backend.walls.add(g2)
    backend.layer_index[g2] = 1
    backend.layer_name[g2] = "Default Layer"
    backend.element_id[g2] = "W-T5-2"
    with tempfile.TemporaryDirectory() as d:
        receipt = os.path.join(d, "receipt.json")
        controller = os.path.join(d, "controller.json")
        report = os.path.join(d, "report.json")
        _source_receipt(receipt, backend)
        _controller(controller)
        rc = _run_reconcile(backend, receipt, controller, report)
        assert rc == 2
        with open(report, "r", encoding="utf-8") as f:
            rep = json.load(f)
        assert rep["classification"] == "AMBIGUOUS"
        assert rep["recommended_human_decision"] != "ADOPT"


@test
def audit_t5_restart_reports_not_applied_without_candidate():
    backend = FakeT3Backend()
    backend.origin = (20.0, 20.0)
    with tempfile.TemporaryDirectory() as d:
        receipt = os.path.join(d, "receipt.json")
        controller = os.path.join(d, "controller.json")
        report = os.path.join(d, "report.json")
        _source_receipt(receipt, backend)
        _controller(controller)
        rc = _run_reconcile(backend, receipt, controller, report)
        assert rc == 2
        with open(report, "r", encoding="utf-8") as f:
            rep = json.load(f)
        assert rep["classification"] == "NOT_APPLIED"
        assert rep["recommended_human_decision"] == "NOT_APPLIED"


@test
def audit_t5_restart_refuses_invalid_crash_evidence_before_backend():
    backend = FakeT3Backend()
    with tempfile.TemporaryDirectory() as d:
        receipt = os.path.join(d, "receipt.json")
        controller = os.path.join(d, "controller.json")
        report = os.path.join(d, "report.json")
        _source_receipt(receipt, backend, valid=False)
        _controller(controller)
        old_backend = r5.TapirBackendV13
        old_argv = sys.argv[:]
        try:
            r5.TapirBackendV13 = lambda port=19723: (_ for _ in ()).throw(AssertionError("backend must not be constructed"))
            sys.argv = [
                "reconcile_t5_kill_v13.py",
                "--expect-project", r"C:\Users\Admin\Downloads\MCP_TEST.pln",
                "--receipt", receipt,
                "--controller-report", controller,
                "--report", report,
            ]
            rc = r5.main()
        finally:
            r5.TapirBackendV13 = old_backend
            sys.argv = old_argv
        assert rc == 1
        assert not os.path.exists(report)


@test
def audit_t5_restart_refuses_unproven_kill_boundary_before_backend():
    backend = FakeT3Backend()
    with tempfile.TemporaryDirectory() as d:
        receipt = os.path.join(d, "receipt.json")
        controller = os.path.join(d, "controller.json")
        report = os.path.join(d, "report.json")
        _source_receipt(receipt, backend)
        _controller(controller, valid=False)
        old_backend = r5.TapirBackendV13
        old_argv = sys.argv[:]
        try:
            r5.TapirBackendV13 = lambda port=19723: (_ for _ in ()).throw(AssertionError("backend must not be constructed"))
            sys.argv = [
                "reconcile_t5_kill_v13.py",
                "--expect-project", r"C:\Users\Admin\Downloads\MCP_TEST.pln",
                "--receipt", receipt,
                "--controller-report", controller,
                "--report", report,
            ]
            rc = r5.main()
        finally:
            r5.TapirBackendV13 = old_backend
            sys.argv = old_argv
        assert rc == 1
        assert not os.path.exists(report)


@test
def audit_t5_live_requires_explicit_origin_before_backend():
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, "receipt.json")
        old_backend = t5.TapirBackendV13
        old_argv = sys.argv[:]
        try:
            t5.TapirBackendV13 = lambda port=19723: (_ for _ in ()).throw(AssertionError("backend must not be constructed"))
            sys.argv = [
                "probe_t5_kill_v13.py",
                "--expect-project", r"C:\Users\Admin\Downloads\MCP_TEST.pln",
                "--port", "19723",
                "--out", out,
                "--allow-write",
                "--i-understand-this-writes-to-archicad",
            ]
            rc = t5.main()
        finally:
            t5.TapirBackendV13 = old_backend
            sys.argv = old_argv
        assert rc == 1
        assert not os.path.exists(out)
