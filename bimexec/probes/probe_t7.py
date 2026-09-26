#!/usr/bin/env python3
"""BIMEXEC T7: fail-closed unavailable read-back audit.

This is a deterministic, dry-run harness for the F2 condition.  It models the
post-dispatch path only; no Archicad connection or production Router is used.
"""
from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from typing import Callable

PAUSED_VERIFY_UNAVAILABLE = "PAUSED(VERIFY_UNAVAILABLE)"
VERIFY_FAILED = "VERIFY_FAILED"
OP_UNKNOWN = "OP_UNKNOWN"


class T7Stop(RuntimeError):
    pass


@dataclass
class T7Harness:
    readback: str = "ok"  # ok, unavailable, mismatch
    pre_dispatch_failure: str | None = None
    dispatch_count: int = 0
    retry_count: int = 0

    def run(self, dependent_dispatch: Callable[[], None] | None = None) -> dict:
        """Run one known-applied operation and gate all continuation on verify."""
        if self.pre_dispatch_failure:
            return {"status": self.pre_dispatch_failure,
                    "dependent_dispatch_count": 0, "retry_count": 0}

        # The mutation is already known applied in this audit scenario.
        self.dispatch_count += 1
        if self.readback == "unavailable":
            status = PAUSED_VERIFY_UNAVAILABLE
        elif self.readback == "mismatch":
            status = VERIFY_FAILED
        elif self.readback == "ok":
            status = "VERIFIED_OK"
        else:
            raise T7Stop(f"unknown read-back mode: {self.readback}")

        if status != "VERIFIED_OK":
            # Fail closed: no retry and no dependent/next mutation dispatch.
            return {"status": status, "dependent_dispatch_count": 0,
                    "retry_count": self.retry_count,
                    "dispatch_count": self.dispatch_count}
        if dependent_dispatch is not None:
            dependent_dispatch()
        return {"status": status,
                "dependent_dispatch_count": 1 if dependent_dispatch else 0,
                "retry_count": self.retry_count,
                "dispatch_count": self.dispatch_count}


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
    ap.add_argument("--readback", choices=("ok", "unavailable", "mismatch"), default="unavailable")
    ap.add_argument("--out", default="t7_report.json")
    args = ap.parse_args(argv)
    result = T7Harness(readback=args.readback).run()
    report = {"probe": "T7", "mode": "dry-run", "contract": {
        "expected_unavailable": PAUSED_VERIFY_UNAVAILABLE,
        "dependent_dispatch_after_unavailable": 0,
        "automatic_retry": 0}, "result": result}
    write_report_once(args.out, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if result["status"] == PAUSED_VERIFY_UNAVAILABLE else 0


if __name__ == "__main__":
    raise SystemExit(main())
