#!/usr/bin/env python3
"""Audit T4: injected transport timeout after a wall mutation has applied.

Standalone live probe for disposable MCP_TEST.pln. NOT production Router.

Safety contract:
- dry-run only locates a clean scratch area and prints the exact payload;
- live run requires an explicit origin from the dry-run and both write flags;
- exactly one CreateWalls dispatch is allowed;
- the receipt is fsynced with DISPATCHED before the mutation;
- after CreateWalls returns successfully, this probe deliberately discards the
  response and injects a synthetic TimeoutError to emulate a lost transport
  response after the server-side mutation has applied;
- after the injection point, NO read-back, marker write, retry, layer write,
  delete, undo, move, or second mutation is allowed;
- the durable result is PAUSED(OP_UNKNOWN), op_state=UNKNOWN, attempts=1;
- a separate process, reconcile_t4_timeout_v13.py, must inspect the model and
  may only OFFER ADOPT. This probe never auto-adopts.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
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


class Stop(Exception):
    def __init__(self, stage: str, reason: str, status: str = "NO_GO"):
        super().__init__(reason)
        self.stage = stage
        self.reason = reason
        self.status = status


class InjectedTimeoutAfterApply(TimeoutError):
    pass


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def jwrite(path: str, obj: Any) -> None:
    base.write_json_atomic(path, obj)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--expect-project", required=True)
    ap.add_argument("--port", type=int, default=19723)
    ap.add_argument("--origin-x", type=float, default=None)
    ap.add_argument("--origin-y", type=float, default=None)
    ap.add_argument("--out", default="t4_timeout_receipt_live_v13.json")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--allow-write", action="store_true")
    ap.add_argument("--i-understand-this-writes-to-archicad", action="store_true")
    a = ap.parse_args()

    if a.allow_write != a.i_understand_this_writes_to_archicad:
        print("STOP: нужны оба write-флага одновременно", file=sys.stderr)
        return 1
    write_enabled = bool(a.allow_write and a.i_understand_this_writes_to_archicad)
    if write_enabled and (a.origin_x is None or a.origin_y is None):
        print("STOP: live T4 requires explicit --origin-x and --origin-y from prior dry-run", file=sys.stderr)
        return 1
    if (a.origin_x is None) != (a.origin_y is None):
        print("STOP: origin requires both --origin-x and --origin-y", file=sys.stderr)
        return 1
    if os.path.exists(a.out):
        print(f"STOP: receipt already exists: {a.out}", file=sys.stderr)
        return 1

    rec: dict[str, Any] = {
        "probe": "AUDIT_T4_TIMEOUT_AFTER_APPLY",
        "version": VER,
        "host": f"{platform.system()} {platform.release()}",
        "started_at": now(),
        "job_state": "RUNNING",
        "paused_reason": None,
        "op_state": "PLANNED",
        "dispatch_attempts": 0,
        "stages": [],
        "baseline_guids": [],
        "baseline_walls": [],
        "baseline_counts": {},
        "origin": None,
        "payload": None,
        "injected_fault": None,
        "cleanup": None,
    }
    jwrite(a.out, rec)

    def stage(name: str, **kw: Any) -> None:
        rec["stages"].append({"stage": name, "at": now(), **kw})
        jwrite(a.out, rec)

    def setrec(**kw: Any) -> None:
        rec.update(kw)
        jwrite(a.out, rec)

    lock = a.out + ".lock"
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.close(fd)
    except FileExistsError:
        setrec(job_state="PAUSED", paused_reason="CONCURRENT_PROBE", op_state="PLANNED")
        print(f"STOP: concurrent probe lock exists: {lock}", file=sys.stderr)
        return 1

    try:
        b = TapirBackendV13(port=a.port)
        ok, why = b.available()
        if not ok:
            raise Stop("BACKEND", why)
        addon = b.addon_version()
        if addon != ADDON:
            raise Stop("BACKEND", f"Tapir {addon!r} != {ADDON!r}")

        try:
            info, stories = t2c.project_recheck(b, a.expect_project)
            comp = t2c.witness_composite(b)
        except t2c.Stop as e:
            raise Stop(e.stage, e.reason, e.status) from e

        before_all = set(b.all_elements() or [])
        before_walls = set(b.elements_by_type("Wall") or [])
        before_counts = b.count_by_type()
        leftovers = t2c.scan_prefix(b, before_all, "BX:")
        if leftovers:
            raise Stop("PRECHECK_MARKERS", f"existing BX markers: {leftovers}")

        if a.origin_x is None:
            origin = t3.choose_free_origin(b, before_all)
        else:
            origin = (float(a.origin_x), float(a.origin_y))
            t3.assert_area_clean(b, before_all, origin)

        wall_plan = t3.wall_payload(origin, comp)
        seg = t3.wall_segment(origin)
        setrec(
            project=info,
            adapter_version=addon,
            origin=list(origin),
            protection_box=t3.protection_box(origin),
            baseline_guids=sorted(before_all),
            baseline_walls=sorted(before_walls),
            baseline_counts=before_counts,
            payload=wall_plan,
            intended={
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
        )
        stage(
            "PRECHECK",
            project=info,
            addon=addon,
            origin=list(origin),
            protection_box=t3.protection_box(origin),
            scratch="FREE",
            before_all=len(before_all),
            before_walls=len(before_walls),
            before_counts=before_counts,
            payload=wall_plan,
        )

        if a.dry_run or not write_enabled:
            setrec(job_state="DRY_RUN_OK", op_state="PLANNED", finished_at=now())
            print("AUDIT T4 TIMEOUT DRY-RUN OK")
            print("MUTATIONS: 0")
            print(f"SUGGESTED ORIGIN: --origin-x {origin[0]} --origin-y {origin[1]}")
            print("FAULT PLAN: one CreateWalls -> synthetic timeout after apply -> PAUSED(OP_UNKNOWN)")
            print(json.dumps(wall_plan, ensure_ascii=False, indent=2))
            return 0

        # Revalidate identity immediately before the one permitted mutation.
        try:
            t2c.project_recheck(b, a.expect_project)
        except t2c.Stop as e:
            raise Stop("BINDING", e.reason, "UNKNOWN") from e
        t3.assert_area_clean(b, set(b.all_elements() or []), origin)

        setrec(op_state="DISPATCHED", dispatch_attempts=1)
        stage(
            "DISPATCH_INTENT",
            attempt=1,
            payload=wall_plan,
            note="receipt fsynced before the only CreateWalls dispatch",
        )

        try:
            # Controlled fault injection. The actual server-side mutation is allowed to
            # complete once. The returned GUID(s) are deliberately discarded to emulate
            # a response lost by the transport after apply.
            t2c.create_once(b, wall_plan)
            setrec(
                injected_fault={
                    "kind": "synthetic_transport_timeout",
                    "point": "after_CreateWalls_return_before_outcome_record",
                    "mutation_call_returned_to_injector": True,
                    "returned_guid_deliberately_not_persisted": True,
                }
            )
            raise InjectedTimeoutAfterApply("simulated transport timeout after mutation applied")
        except InjectedTimeoutAfterApply as e:
            # CRITICAL: from here on we do not call the backend again. The process must
            # preserve UNKNOWN and leave reconciliation to a separate invocation.
            setrec(
                job_state="PAUSED",
                paused_reason="OP_UNKNOWN",
                op_state="UNKNOWN",
                dispatch_attempts=1,
                stopped_at_stage="DISPATCH_UNKNOWN",
                reason=str(e),
                cleanup={
                    "action": "DO NOT RETRY; DO NOT DELETE/UNDO; run separate read-only reconcile",
                    "automatic_retry_allowed": False,
                    "automatic_adopt_allowed": False,
                },
                finished_at=now(),
            )
            print("AUDIT T4 INJECTED TIMEOUT AFTER APPLY")
            print("JOB STATE          : PAUSED")
            print("PAUSE REASON       : OP_UNKNOWN")
            print("OP STATE           : UNKNOWN")
            print("DISPATCH ATTEMPTS  : 1")
            print("AUTO RETRY         : FORBIDDEN")
            print("POST-FAULT READBACK: 0")
            print("NEXT               : separate read-only reconcile process")
            print("receipt            :", a.out)
            return 2
        except Exception as e:
            # A real dispatch failure is also UNKNOWN. No retry and no post-failure read.
            setrec(
                job_state="PAUSED",
                paused_reason="OP_UNKNOWN",
                op_state="UNKNOWN",
                dispatch_attempts=1,
                stopped_at_stage="DISPATCH_UNKNOWN",
                reason=f"{type(e).__name__}: {e}",
                injected_fault={
                    "kind": "not_reached",
                    "point": "CreateWalls raised before controlled timeout injection",
                    "mutation_call_returned_to_injector": False,
                },
                cleanup={
                    "action": "DO NOT RETRY; reconcile actual model state",
                    "automatic_retry_allowed": False,
                    "automatic_adopt_allowed": False,
                },
                finished_at=now(),
            )
            print(f"AUDIT T4 REAL DISPATCH ERROR -> OP_UNKNOWN: {type(e).__name__}: {e}", file=sys.stderr)
            print("receipt:", a.out, file=sys.stderr)
            return 3

    except Stop as s:
        setrec(
            job_state="PAUSED" if s.status == "UNKNOWN" else "STOP",
            paused_reason="OP_UNKNOWN" if s.status == "UNKNOWN" else s.status,
            stopped_at_stage=s.stage,
            reason=s.reason,
            finished_at=now(),
        )
        print(f"STOP at {s.stage}: {s.reason}", file=sys.stderr)
        print("receipt:", a.out, file=sys.stderr)
        return 1
    except Exception as e:
        setrec(
            job_state="PAUSED",
            paused_reason="OP_UNKNOWN",
            op_state="UNKNOWN",
            reason=f"{type(e).__name__}: {e}",
            finished_at=now(),
        )
        print(f"UNKNOWN: {type(e).__name__}: {e}", file=sys.stderr)
        print("receipt:", a.out, file=sys.stderr)
        return 1
    finally:
        try:
            os.unlink(lock)
        except OSError:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
