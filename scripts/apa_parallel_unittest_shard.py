"""Deterministic read-only sharding of repository offline unittest cases.

Each discovered test ID is assigned to exactly one shard via stable SHA-256.
This avoids running the full suite redundantly on parallel Windows runners.
The CI matrix provides 8 independent shards; results retain exact test IDs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import unittest
from pathlib import Path


def cases(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from cases(item)
        else:
            yield item


def target(test_id: str, shards: int) -> int:
    return int(hashlib.sha256(test_id.encode("utf-8")).hexdigest()[:16], 16) % shards


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--shard", type=int, required=True)
    parser.add_argument("--shards", type=int, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.shards < 1 or args.shard not in range(args.shards):
        parser.error("shard must be 0 <= shard < shards")
    os.environ["APA_OFFLINE_ONLY"] = "1"
    # We deliberately discover all tracked top-level tests, not just
    # test_archicad_*.py, and report import errors as real errors.
    suite = unittest.TestLoader().discover(start_dir="tests", pattern="test_*.py")
    discovered = list(cases(suite))
    identifiers = [t.id() for t in discovered]
    duplicates = len(identifiers) - len(set(identifiers))
    selected = [t for t in discovered if target(t.id(), args.shards) == args.shard]
    unique_assignments = all(sum(target(k, args.shards) == s for s in range(args.shards)) == 1 for k in identifiers)
    if duplicates or not unique_assignments:
        print(f"ERROR: duplicate IDs={duplicates} unique assignments={unique_assignments}", file=sys.stderr)
        return 2
    ordered_digest = hashlib.sha256("\n".join(sorted(identifiers)).encode()).hexdigest()
    print(f"OFFLINE_SHARD {args.shard + 1}/{args.shards}; DISCOVERED={len(discovered)}; ASSIGNED={len(selected)}; DISCOVERY_SHA={ordered_digest}", flush=True)
    runner = unittest.TextTestRunner(verbosity=1, failfast=False)
    result = runner.run(unittest.TestSuite(selected))
    payload = {
        "schema": "APA_PARALLEL_OFFLINE_SHARD_V1",
        "shard": args.shard,
        "shards": args.shards,
        "totalDiscovered": len(discovered),
        "assigned": len(selected),
        "suiteSHA256": ordered_digest,
        "testsRun": result.testsRun,
        "failures": [{"test": t.id(), "trace": traceback[-9000:]} for t, traceback in result.failures],
        "errors": [{"test": t.id(), "trace": traceback[-9000:]} for t, traceback in result.errors],
        "skipped": [{"test": t.id(), "reason": reason} for t, reason in result.skipped],
        "expectedFailures": [{"test": t.id(), "trace": traceback[-4000:]} for t, traceback in result.expectedFailures],
        "unexpectedSuccesses": [t.id() for t in result.unexpectedSuccesses],
        "successful": result.wasSuccessful(),
        "assignedTestIDs": [t.id() for t in selected],
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf8")
    print("OFFLINE_SHARD_RESULT " + json.dumps({k: v for k, v in payload.items() if k not in {"failures","errors","skipped","expectedFailures","unexpectedSuccesses","assignedTestIDs"}}), flush=True)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
