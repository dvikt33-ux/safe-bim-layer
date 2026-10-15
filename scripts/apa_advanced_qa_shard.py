"""Ten-way deterministic Windows QA sharder: ONLY the 288 new advanced tests."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import sys
import unittest
from pathlib import Path

PATTERN = "test_archicad_advanced_ref_workflow_ifc_qa.py"
EXPECTED = 288


def flatten(suite):
    for value in suite:
        if isinstance(value, unittest.TestSuite):
            yield from flatten(value)
        else:
            yield value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--shard", type=int, required=True)
    parser.add_argument("--shards", type=int, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.shards < 1 or args.shard not in range(args.shards):
        parser.error("invalid shard")
    os.environ["APA_OFFLINE_ONLY"] = "1"
    discovery = list(flatten(unittest.TestLoader().discover(
        start_dir="tests", pattern=PATTERN)))
    ids = [test.id() for test in discovery]
    unique = set(ids)
    if len(ids) != EXPECTED or len(unique) != EXPECTED:
        print(f"FAIL: expected {EXPECTED} unique new tests, got "
              f"{len(ids)} discovered / {len(unique)} unique", file=sys.stderr)
        return 2

    def bucket(name):
        return int(hashlib.sha256(name.encode("utf8")).hexdigest()[:16], 16) % args.shards

    selected = [test for test in discovery if bucket(test.id()) == args.shard]
    digest = hashlib.sha256("\n".join(sorted(ids)).encode("utf8")).hexdigest()
    print(f"APA_ADVANCED_SHARD {args.shard + 1}/{args.shards} "
          f"DISCOVERED={len(ids)} ASSIGNED={len(selected)} SHA256={digest}", flush=True)
    result = unittest.TextTestRunner(verbosity=1).run(unittest.TestSuite(selected))
    payload = {
        "schema": "APA_PARALLEL_OFFLINE_SHARD_V1",
        "shard": args.shard,
        "shards": args.shards,
        "totalDiscovered": len(ids),
        "discoveredOccurrences": len(ids),
        "duplicateIdsCollapsed": 0,
        "suiteSHA256": digest,
        "assigned": len(selected),
        "assignedTestIDs": [test.id() for test in selected],
        "testsRun": result.testsRun,
        "failures": [{"test": test.id(), "trace": tb[-9000:]}
                     for test, tb in result.failures],
        "errors": [{"test": test.id(), "trace": tb[-9000:]}
                   for test, tb in result.errors],
        "skipped": [{"test": test.id(), "reason": reason}
                    for test, reason in result.skipped],
        "expectedFailures": [{"test": test.id(), "trace": tb[-4000:]}
                             for test, tb in result.expectedFailures],
        "unexpectedSuccesses": [test.id() for test in result.unexpectedSuccesses],
        "successful": result.wasSuccessful(),
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf8")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
