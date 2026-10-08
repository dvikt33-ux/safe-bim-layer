"""One CLI offline system/metrics pass for the 12-element scene and typical floor.

Every "API" response here comes from the existing FakeNative test double.
Never imports a live Archicad connection, never invokes --execute against PLN.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sqlite3
from statistics import median
import sys
import tempfile
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))

import archicad_scene_run as RUN
import archicad_typical_floor_graph as FLOOR
from test_archicad_scene_run import FakeNative


class MeteredFake:
    def __init__(self, fake=None):
        self.fake = fake or FakeNative()
        self.calls = []

    def __call__(self, command, params):
        request_size = len(json.dumps({"command": command, "params": params},
                                      ensure_ascii=False).encode("utf-8"))
        start = perf_counter()
        outcome = "PASS"
        try:
            result = self.fake(command, params)
            response_size = len(json.dumps(result, ensure_ascii=False).encode("utf-8"))
            return result
        except Exception:
            outcome = "ERROR"
            response_size = 0
            raise
        finally:
            self.calls.append({"command": command, "status": outcome,
                               "durationMs": round((perf_counter()-start)*1000, 5),
                               "requestBytes": request_size,
                               "responseBytes": response_size})

    def metrics(self):
        return {
            "apiCallCount": len(self.calls),
            "apiCallKinds": dict(Counter(x["command"] for x in self.calls)),
            "failedApiCalls": sum(x["status"] == "ERROR" for x in self.calls),
            "requestBytes": sum(x["requestBytes"] for x in self.calls),
            "responseBytes": sum(x["responseBytes"] for x in self.calls),
            "mockApiWallTimeMs": round(sum(x["durationMs"] for x in self.calls), 4),
            "readbackApiCallCount": sum(x["command"] == "GetDetailsOfElements"
                                        for x in self.calls),
            "readbackApiWallTimeMs": round(sum(x["durationMs"]
                        for x in self.calls if x["command"] == "GetDetailsOfElements"), 4),
        }


def timed_pavilion():
    api = MeteredFake()
    with tempfile.TemporaryDirectory() as d:
        writer = RUN.SceneWriter(api, Path(d) / "journal.sqlite3")
        start = perf_counter()
        preflight = writer.preflight(200, 200)
        preflight_ms = round((perf_counter()-start)*1000, 4)
        if preflight["status"] != "READY_FOR_EXPLICIT_TEST_RUN":
            raise AssertionError("mock preflight mismatch")
        begin = perf_counter()
        result = writer.execute(200, 200, "scene-offline-metrics-001",
                                preflight["sourcePlanHash"])
        duration_ms = round((perf_counter()-begin)*1000, 4)
        if result["status"] != "COMPLETE_UNSAVED" or result["createdCount"] != 12:
            raise AssertionError("mock pavilion was incomplete")
        with sqlite3.connect(writer.journal_path) as db:
            states = dict(db.execute("SELECT state,COUNT(*) FROM steps GROUP BY state"))
            if states != {"PASS": 12}:
                raise AssertionError("journal has unverified state: " + str(states))
        count_before_retry = len(api.fake.writes)
        try:
            writer.execute(200, 200, "scene-offline-metrics-002",
                           preflight["sourcePlanHash"])
            raise AssertionError("duplicate scene should be blocked")
        except ValueError as exc:
            if "SCENE_ALREADY_RESERVED" not in str(exc):
                raise
        if len(api.fake.writes) != count_before_retry:
            raise AssertionError("duplicate generated another native write")
        return {"status": "OFFLINE_MOCK_PAVILION_PASS", "elementsVerified": 12,
                "readOnlyPreflightDurationMs": preflight_ms,
                "mockExecutionDurationMs": duration_ms,
                "journalStates": states, "duplicateBlocked": True, **api.metrics()}


def timed_partial_failure():
    fake = FakeNative()
    fake.fail_at = "CreateSlabs"
    api = MeteredFake(fake)
    with tempfile.TemporaryDirectory() as d:
        writer = RUN.SceneWriter(api, Path(d) / "journal.sqlite3")
        preflight = writer.preflight(200, 200)
        result = writer.execute(200, 200, "scene-offline-failure-001",
                                preflight["sourcePlanHash"])
        if result["status"] != "PARTIAL_OR_UNKNOWN_OUTCOME":
            raise AssertionError("unknown outcome not retained")
        with sqlite3.connect(writer.journal_path) as db:
            states = dict(db.execute("SELECT state,COUNT(*) FROM steps GROUP BY state"))
            if states.get("ATTEMPTED") != 1 or states.get("PASS") != 4:
                raise AssertionError("partial ledger mismatch")
        writes = len(fake.writes)
        try:
            writer.execute(200, 200, "scene-offline-failure-001",
                           preflight["sourcePlanHash"])
            raise AssertionError("ambiguous replay accepted")
        except ValueError as exc:
            if "SCENE_ALREADY_RESERVED" not in str(exc):
                raise
        if len(fake.writes) != writes:
            raise AssertionError("unknown operation was replayed")
        return {"status": "OFFLINE_MOCK_PARTIAL_PASS",
                "failedStep": result["failedStep"],
                "journalStates": states, "replayBlocked": True, **api.metrics()}


def timed_floor():
    start = perf_counter()
    preview = FLOOR.prepare()
    compilation_ms = round((perf_counter()-start)*1000, 4)
    catalog_start = perf_counter()
    cached_catalog = FLOOR.GRAPH.CONTRACTS.load_catalog(
        FLOOR.GRAPH.CONTRACTS.DEFAULT_SCHEMA)
    catalog_load_ms = round((perf_counter()-catalog_start)*1000, 4)
    cached_trials = []
    for _ in range(5):
        trial_start = perf_counter()
        replay = FLOOR.prepare(catalog=cached_catalog)
        cached_trials.append((perf_counter()-trial_start)*1000)
        if (replay["sourcePlanHash"] != preview["sourcePlanHash"] or
                replay["executionOrder"] != preview["executionOrder"]):
            raise AssertionError("cached schema changed the graph/plan hash")
    fake = MeteredFake()
    created = {"__plan__": preview["graph"]}
    by_id = {s["id"]: s for s in preview["graph"]["operations"]}
    start = perf_counter()
    for sid in preview["executionOrder"]:
        step = by_id[sid]
        command = step["command"]
        if command not in FLOOR.SUPPORTED:
            raise AssertionError("unsupported native step in offline graph")
        owner_guid = (RUN.check_previous_wall(fake, step, created)
                      if command in ("CreateWindows", "CreateDoors") else None)
        resolved = RUN.resolve_params(step, created)
        guid = RUN.created_guid(fake(command, resolved))
        row = RUN.requested_details(fake, guid)
        kind = RUN.verify_readback(command, resolved, row, owner_guid)
        created[sid] = {"guid": guid, "kind": kind}
    duration_ms = round((perf_counter()-start)*1000, 4)
    if len(created)-1 != preview["metrics"]["elementCount"]:
        raise AssertionError("not every GUID was confirmed in fake readback")
    return {"status": "OFFLINE_MOCK_FLOOR_PASS",
            "elementsVerified": len(created)-1,
            "mockGraphCompileDurationMs": compilation_ms,
            "cachedCatalogLoadDurationMs": catalog_load_ms,
            "cachedCatalogGraphCompileMedianMs": round(median(cached_trials), 4),
            "cachedCatalogReusesPreservePlanHash": True,
            "mockExecutionDurationMs": duration_ms,
            "sourcePlanHash": preview["sourcePlanHash"],
            **fake.metrics()}


def report():
    return {
        "status": "OFFLINE_FAKE_NATIVE_ONLY",
        "notClaims": ["real Archicad creation", "real API performance",
                      "live PLN mutation", "real material assignment",
                      "batch optimization validated"],
        "pavilion": timed_pavilion(),
        "partialFailure": timed_partial_failure(),
        "typicalFloor": timed_floor(),
        "optimization": "NOT_MEASURED_ON_NATIVE; do not enable write batching",
        "plnSaved": False,
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path)
    args = p.parse_args(argv)
    try:
        output = report()
        data = json.dumps(output, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(data, encoding="utf-8")
        print(data, end="")
        return 0
    except Exception as exc:
        print(json.dumps({"status": "OFFLINE_FAILURE", "error": str(exc)},
                         ensure_ascii=False))
        return 2


if __name__ == "__main__":
    sys.exit(main())
