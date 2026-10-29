#!/usr/bin/env python3
"""Audit T5: hard-kill a standalone probe process after dispatch and before verify.

This is a disposable MCP_TEST.pln probe. It does NOT kill Archicad and does NOT
kill or modify the production Router.

Safety contract:
- dry-run only locates a clean scratch area and prints the exact wall payload;
- live run requires explicit origin + both write flags;
- parent/controller performs read-only prechecks, then launches a child worker;
- child fsyncs DISPATCHED/attempt=1 before the only CreateWalls mutation;
- after CreateWalls returns, the child writes a TEST-HARNESS killpoint sidecar
  (never used by recovery) and parks without read-back/marker/verify;
- parent observes that killpoint and hard-kills ONLY the child probe process;
- source receipt is intentionally left at RUNNING/DISPATCHED with no outcome;
- parent never reads Archicad after the dispatch; a separate restart/reconcile
  process must infer PAUSED(OP_UNKNOWN) from INTENT-without-OUTCOME;
- no retry, delete, undo, move, rotate, marker write, or second mutation.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
import time
from typing import Any

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import backends as base
from backends_v13 import TapirBackendV13
import probe_t2_connections_v13 as t2c
import probe_t3_dependency_v13 as t3

VER = "1.0"
ADDON = "1.5.9"
EXPECTED_KILL_EXIT = 5


class Stop(Exception):
    def __init__(self, stage: str, reason: str):
        super().__init__(reason)
        self.stage = stage
        self.reason = reason


class KillPointReached(RuntimeError):
    """Test-only control flow used when park=False; never used in live worker."""


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def jwrite(path: str, obj: Any) -> None:
    base.write_json_atomic(path, obj)


def load_json(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _setrec(path: str, **kw: Any) -> dict[str, Any]:
    rec = load_json(path)
    rec.update(kw)
    jwrite(path, rec)
    return rec


def _stage(path: str, name: str, **kw: Any) -> dict[str, Any]:
    rec = load_json(path)
    rec.setdefault("stages", []).append({"stage": name, "at": now(), **kw})
    jwrite(path, rec)
    return rec


def _prepare_receipt(
    b: Any,
    *,
    expect_project: str,
    out: str,
    origin: tuple[float, float] | None,
) -> tuple[tuple[float, float], dict[str, Any]]:
    ok, why = b.available()
    if not ok:
        raise Stop("BACKEND", why)
    addon = b.addon_version()
    if addon != ADDON:
        raise Stop("BACKEND", f"Tapir {addon!r} != {ADDON!r}")

    try:
        info, stories = t2c.project_recheck(b, expect_project)
        comp = t2c.witness_composite(b)
    except t2c.Stop as e:
        raise Stop(e.stage, e.reason) from e

    before_all = set(b.all_elements() or [])
    before_walls = set(b.elements_by_type("Wall") or [])
    before_counts = b.count_by_type()
    leftovers = t2c.scan_prefix(b, before_all, "BX:")
    if leftovers:
        raise Stop("PRECHECK_MARKERS", f"existing BX markers: {leftovers}")

    if origin is None:
        chosen = t3.choose_free_origin(b, before_all)
    else:
        chosen = (float(origin[0]), float(origin[1]))
        t3.assert_area_clean(b, before_all, chosen)

    wall_plan = t3.wall_payload(chosen, comp)
    seg = t3.wall_segment(chosen)
    rec: dict[str, Any] = {
        "probe": "AUDIT_T5_PROCESS_KILL_AFTER_DISPATCH",
        "version": VER,
        "host": f"{platform.system()} {platform.release()}",
        "started_at": now(),
        "job_state": "PREPARED",
        "paused_reason": None,
        "op_state": "PLANNED",
        "dispatch_attempts": 0,
        "stages": [],
        "baseline_guids": sorted(before_all),
        "baseline_walls": sorted(before_walls),
        "baseline_counts": before_counts,
        "origin": list(chosen),
        "payload": wall_plan,
        "project": info,
        "adapter_version": addon,
        "protection_box": t3.protection_box(chosen),
        "intended": {
            "kind": "Wall",
            "story_index": t2c.FLOOR,
            "story_name": t2c.STORY,
            "from": list(seg["from_abs"]),
            "to": list(seg["to_abs"]),
            "length": seg["length"],
            "height": t2c.HEIGHT,
            "thickness": t2c.THICK,
            "referenceLineLocation": t2c.REFLINE,
            "offset": t2c.OFFSET,
            "arcAngle": t2c.ARC,
            "structureType": "Composite",
            "compositeId": comp,
        },
        "recovery_contract": {
            "intent_without_outcome_means": "OP_UNKNOWN",
            "automatic_retry_allowed": False,
            "automatic_adopt_allowed": False,
            "reconcile_must_be_separate_process": True,
        },
    }
    jwrite(out, rec)
    _stage(
        out,
        "PRECHECK",
        project=info,
        addon=addon,
        origin=list(chosen),
        protection_box=t3.protection_box(chosen),
        scratch="FREE",
        before_all=len(before_all),
        before_walls=len(before_walls),
        before_counts=before_counts,
        payload=wall_plan,
    )
    return chosen, wall_plan


def worker_dispatch_until_killpoint(
    b: Any,
    *,
    expect_project: str,
    receipt: str,
    killpoint: str,
    park: bool = True,
) -> None:
    """One mutation. After success, signal the harness and never verify/read back."""
    src = load_json(receipt)
    if src.get("probe") != "AUDIT_T5_PROCESS_KILL_AFTER_DISPATCH":
        raise RuntimeError("wrong T5 source receipt")
    if src.get("job_state") != "PREPARED" or src.get("op_state") != "PLANNED":
        raise RuntimeError("T5 worker source state is not PREPARED/PLANNED")
    if int(src.get("dispatch_attempts", 0)) != 0:
        raise RuntimeError("T5 worker refuses a second dispatch attempt")

    origin_raw = src.get("origin") or []
    if len(origin_raw) != 2:
        raise RuntimeError("T5 receipt has no valid origin")
    origin = (float(origin_raw[0]), float(origin_raw[1]))

    # Revalidate immediately before the only mutation.
    try:
        t2c.project_recheck(b, expect_project)
    except t2c.Stop as e:
        raise RuntimeError(f"binding recheck failed: {e.reason}") from e
    t3.assert_area_clean(b, set(b.all_elements() or []), origin)

    _setrec(
        receipt,
        job_state="RUNNING",
        op_state="DISPATCHED",
        dispatch_attempts=1,
    )
    _stage(
        receipt,
        "DISPATCH_INTENT",
        attempt=1,
        payload=src.get("payload"),
        note="durable intent fsynced before the only CreateWalls dispatch",
    )

    # Exactly one permitted mutation. Returned GUID(s) are deliberately ignored
    # and never written to the source receipt.
    t2c.create_once(b, src["payload"])

    # Test-harness side channel ONLY. Recovery is forbidden from using this file
    # as model evidence; it only lets the parent kill at the required boundary.
    jwrite(
        killpoint,
        {
            "probe": "AUDIT_T5_KILLPOINT",
            "reached_at": now(),
            "pid": os.getpid(),
            "point": "after_CreateWalls_return_before_outcome_or_verify",
            "model_readback_after_dispatch": 0,
        },
    )

    if not park:
        raise KillPointReached("T5 test killpoint reached")

    # Live child parks forever; parent must hard-kill it. No backend calls below.
    while True:
        time.sleep(60.0)


def _worker_main(a: argparse.Namespace) -> int:
    try:
        b = TapirBackendV13(port=a.port)
        worker_dispatch_until_killpoint(
            b,
            expect_project=a.expect_project,
            receipt=a.out,
            killpoint=a.killpoint,
            park=True,
        )
        return 99  # unreachable
    except Exception as e:
        # A failure before the controlled killpoint is NOT a passing T5 run.
        # Preserve UNKNOWN/no-retry semantics because dispatch may have applied.
        if os.path.exists(a.out):
            try:
                _setrec(
                    a.out,
                    job_state="PAUSED",
                    paused_reason="OP_UNKNOWN",
                    op_state="UNKNOWN",
                    worker_error=f"{type(e).__name__}: {e}",
                    finished_at=now(),
                )
            except Exception:
                pass
        print(f"T5 WORKER ERROR: {type(e).__name__}: {e}", file=sys.stderr)
        return 3


def _controller_live(a: argparse.Namespace) -> int:
    if os.path.exists(a.controller_report):
        print(f"STOP: controller report already exists: {a.controller_report}", file=sys.stderr)
        return 1
    if os.path.exists(a.killpoint):
        print(f"STOP: stale killpoint already exists: {a.killpoint}", file=sys.stderr)
        return 1

    cmd = [
        sys.executable,
        os.path.abspath(__file__),
        "--worker",
        "--expect-project", a.expect_project,
        "--port", str(a.port),
        "--out", a.out,
        "--killpoint", a.killpoint,
    ]
    proc = subprocess.Popen(cmd)
    started = time.monotonic()
    observed = False
    outcome = "UNKNOWN"

    try:
        while time.monotonic() - started < a.killpoint_timeout:
            if os.path.exists(a.killpoint):
                observed = True
                break
            rc = proc.poll()
            if rc is not None:
                outcome = "CHILD_EXIT_BEFORE_KILLPOINT"
                break
            time.sleep(0.05)

        if observed:
            # The audited failure: hard kill the standalone child probe process.
            proc.kill()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=10)
            outcome = "HARD_KILL_CONFIRMED"
        elif proc.poll() is None:
            # Kill only to avoid a stranded worker. This is NOT a passing T5 run
            # because the exact after-apply killpoint was not observed.
            proc.kill()
            proc.wait(timeout=10)
            outcome = "KILLPOINT_TIMEOUT_CHILD_KILLED"
    finally:
        controller = {
            "probe": "AUDIT_T5_PROCESS_KILL_CONTROLLER",
            "version": VER,
            "generated_at": now(),
            "source_receipt": a.out,
            "child_pid": proc.pid,
            "killpoint_observed": observed,
            "controller_outcome": outcome,
            "child_exit_code": proc.poll(),
            "hard_killed_process_scope": "standalone T5 child probe only",
            "archicad_process_killed": False,
            "production_router_killed": False,
            "post_dispatch_model_readback_by_controller": 0,
            "automatic_retry_allowed": False,
            "automatic_adopt_performed": False,
        }
        jwrite(a.controller_report, controller)

    if outcome == "HARD_KILL_CONFIRMED":
        print("AUDIT T5 HARD PROCESS KILL INJECTED")
        print("CHILD KILLPOINT      : after CreateWalls return / before outcome+verify")
        print("SOURCE RECEIPT       : RUNNING / DISPATCHED / attempts=1")
        print("CHILD HARD-KILLED    : YES")
        print("ARCHICAD KILLED      : NO")
        print("PRODUCTION ROUTER    : UNTOUCHED")
        print("POST-DISPATCH READBACK: 0")
        print("AUTO RETRY           : FORBIDDEN")
        print("NEXT                 : separate restart/read-only reconcile")
        print("receipt              :", a.out)
        print("controller report    :", a.controller_report)
        return EXPECTED_KILL_EXIT

    print(f"AUDIT T5 DID NOT REACH CONTROLLED KILLPOINT: {outcome}", file=sys.stderr)
    print("DO NOT RETRY; inspect receipt/controller first", file=sys.stderr)
    return 3


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--expect-project", required=True)
    ap.add_argument("--port", type=int, default=19723)
    ap.add_argument("--origin-x", type=float, default=None)
    ap.add_argument("--origin-y", type=float, default=None)
    ap.add_argument("--out", default="t5_kill_receipt_live_v13.json")
    ap.add_argument("--controller-report", default="t5_kill_controller_live_v13.json")
    ap.add_argument("--killpoint", default="t5_killpoint_live_v13.json")
    ap.add_argument("--killpoint-timeout", type=float, default=30.0)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--allow-write", action="store_true")
    ap.add_argument("--i-understand-this-writes-to-archicad", action="store_true")
    ap.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    a = ap.parse_args()

    if a.worker:
        return _worker_main(a)

    if a.allow_write != a.i_understand_this_writes_to_archicad:
        print("STOP: нужны оба write-флага одновременно", file=sys.stderr)
        return 1
    write_enabled = bool(a.allow_write and a.i_understand_this_writes_to_archicad)
    if write_enabled and (a.origin_x is None or a.origin_y is None):
        print("STOP: live T5 requires explicit --origin-x and --origin-y from prior dry-run", file=sys.stderr)
        return 1
    if (a.origin_x is None) != (a.origin_y is None):
        print("STOP: origin requires both --origin-x and --origin-y", file=sys.stderr)
        return 1
    if os.path.exists(a.out):
        print(f"STOP: receipt already exists: {a.out}", file=sys.stderr)
        return 1

    try:
        b = TapirBackendV13(port=a.port)
        origin = None if a.origin_x is None else (float(a.origin_x), float(a.origin_y))
        chosen, wall_plan = _prepare_receipt(
            b,
            expect_project=a.expect_project,
            out=a.out,
            origin=origin,
        )
    except Stop as e:
        print(f"STOP at {e.stage}: {e.reason}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"STOP: {type(e).__name__}: {e}", file=sys.stderr)
        return 1

    if a.dry_run or not write_enabled:
        _setrec(a.out, job_state="DRY_RUN_OK", op_state="PLANNED", finished_at=now())
        print("AUDIT T5 PROCESS-KILL DRY-RUN OK")
        print("MUTATIONS: 0")
        print(f"SUGGESTED ORIGIN: --origin-x {chosen[0]} --origin-y {chosen[1]}")
        print("FAULT PLAN: child fsync DISPATCHED -> one CreateWalls -> hard kill before outcome/verify")
        print("TARGET PROCESS: standalone T5 child probe ONLY (not Archicad, not production Router)")
        print(json.dumps(wall_plan, ensure_ascii=False, indent=2))
        return 0

    return _controller_live(a)


if __name__ == "__main__":
    raise SystemExit(main())
