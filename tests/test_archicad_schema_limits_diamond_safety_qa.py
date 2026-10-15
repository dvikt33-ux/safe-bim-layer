"""384 fresh independent APA tests after PR91: boundaries, union replies,
source snapshots, diamond BIM Graph flows, nonrectangular geometry and plan drift.

Imported production functions are tested. Fixtures do not touch Archicad,
installed APX, user project or the network. Not an Archicad LIVE test.
"""
from __future__ import annotations

import copy
import math
import sys
import unittest

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from archicad_dynamic_commands import DynamicCommands
import archicad_local_modules as LOCAL

REVIEW = {"source": "Self-contained QA handler, not an Archicad add-on",
          "sha256": "8" * 64}


def router():
    return DynamicCommands({
        "common_schemas": {},
        "commands": {},
        "_metadata": {"provider_version": "1.5.10"},
    })


def contract(parameters, returns):
    return {"version": "1", "category": "Independent synthetic QA",
            "parameters": parameters, "returns": returns}


def add_test(group, seed, fn):
    setattr(IndependentBoundaryMatrix, f"test_fresh_{group}_{seed:03d}", fn)


class IndependentBoundaryMatrix(unittest.TestCase):
    pass


def bounded_contract_case(seed):
    def test(self):
        r = router()
        key = f"AddOn.Bounded{seed}.Calculate"
        schema = {
            "type": "object",
            "required": ["items", "mode"],
            "additionalProperties": False,
            "properties": {
                "items": {"type": "array", "minItems": 2, "maxItems": 4,
                          "uniqueItems": True,
                          "items": {"type": "integer", "minimum": 0, "maximum": 100}},
                "mode": {"type": "string", "enum": ["fast", "slow"]},
                "code": {"type": "string", "pattern": "^AA-[0-9]{3}$"},
            },
        }
        r.add_provider(f"Bounded{seed}",
                       {"Calculate": contract(schema, {"type": "object"})},
                       "Bounded QA source")
        value = seed % 40
        valid = {"items": [value, value + 1],
                 "mode": "fast" if seed % 2 else "slow",
                 "code": f"AA-{seed:03d}"}
        t = r.prepare(key, valid)
        self.assertEqual(t["parameters"], valid)
        self.assertFalse(t["nativeWritePermission"])
        invalid = copy.deepcopy(valid)
        mode = seed % 10
        if mode == 0:
            invalid["items"] = [value]
        elif mode == 1:
            invalid["items"] = list(range(5))
        elif mode == 2:
            invalid["items"] = [value, value]
        elif mode == 3:
            invalid["items"][0] = "integer"
        elif mode == 4:
            invalid["items"] = [-1, value]
        elif mode == 5:
            invalid["items"] = [101, value]
        elif mode == 6:
            invalid["mode"] = "unsafe"
        elif mode == 7:
            invalid["code"] = "AA-XYZ"
        elif mode == 8:
            invalid["unknown"] = seed
        else:
            invalid.pop("mode")
        with self.assertRaises(Exception):
            r.prepare(key, invalid)
        self.assertEqual(r.validate(t), t)
        self.assertIsNone(r.select(key)["runtimeRegistered"])
    return test


for seed in range(80):
    add_test("schema_bounded_inputs", seed, bounded_contract_case(seed))


def disjoint_union_case(seed):
    def test(self):
        r = router()
        result_schema = {
            "oneOf": [
                {"type": "object", "required": ["kind", "payload"],
                 "properties": {"kind": {"const": "integer"},
                                "payload": {"type": "integer"}},
                 "additionalProperties": False},
                {"type": "object", "required": ["kind", "payload"],
                 "properties": {"kind": {"const": "text"},
                                "payload": {"type": "string"}},
                 "additionalProperties": False},
            ],
        }
        namespace = f"ReturnUnion{seed}"
        key = f"AddOn.{namespace}.Inspect"
        r.add_provider(namespace,
                       {"Inspect": contract({"type": "object", "maxProperties": 0},
                                            result_schema)},
                       "Union results QA")
        valid = ({"kind": "integer", "payload": seed - 20} if seed % 2
                 else {"kind": "text", "payload": f"reply_{seed}"})
        self.assertEqual(r.validate_result(key, valid), valid)
        invalid = copy.deepcopy(valid)
        mode = seed % 4
        if mode == 0:
            invalid["payload"] = None
        elif mode == 1:
            del invalid["payload"]
        elif mode == 2:
            invalid["additional"] = 1
        else:
            invalid["kind"] = "third_variant"
        with self.assertRaises(Exception):
            r.validate_result(key, invalid)
        self.assertIsNone(r.select(key)["runtimeRegistered"])
        self.assertNotIn(key, r.live)
    return test


for seed in range(64):
    add_test("oneof_return_validation", seed, disjoint_union_case(seed))


def snapshot_stability_case(seed):
    def test(self):
        r = router()
        label = f"ExternalSnapshot{seed}"
        command = f"SourceOnly_{seed:03d}"
        snapshot = {
            "common_schemas": {
                "Payload": {
                    "type": "object", "required": ["value"],
                    "properties": {"value": {"type": "integer",
                                             "minimum": 0, "maximum": 1000}},
                    "additionalProperties": False,
                },
            },
            "commands": {
                command: contract({"$ref": "#/Payload"},
                                  {"type": "object", "properties": {
                                      "ok": {"type": "boolean"}}}),
            },
        }
        original = copy.deepcopy(snapshot)
        self.assertEqual(r.include_source_snapshot(snapshot, label), [command])
        self.assertEqual(snapshot, original)
        before = r.fingerprint
        before_contract = r.contract_hash(command)
        self.assertEqual(r.include_source_snapshot(snapshot, label), [])
        self.assertEqual(r.fingerprint, before)
        self.assertEqual(r.contract_hash(command), before_contract)
        snapshot["common_schemas"]["Payload"]["properties"]["value"]["type"] = "string"
        self.assertEqual(r.prepare(command, {"value": seed % 1000})["command"], command)
        with self.assertRaises(Exception):
            r.prepare(command, {"value": str(seed)})
        row = r.select(command)
        self.assertEqual(row["availability"], "SOURCE_SNAPSHOT_NOT_RUNTIME_PROBED")
        self.assertIsNone(row["runtimeRegistered"])
        self.assertNotEqual(row["status"], "LIVE_VERIFIED")
    return test


for seed in range(64):
    add_test("snapshot_hash_stability", seed, snapshot_stability_case(seed))


def diamond_router():
    r = router()
    numeric = {"type": "integer"}
    result = {"type": "object", "required": ["value"],
              "properties": {"value": numeric}, "additionalProperties": False}

    def function_start(start):
        return {"value": start}

    def function_left(value, delta):
        return {"value": value + delta}

    def function_right(value, multiplier):
        return {"value": value * multiplier}

    def function_join(left, right):
        return {"value": left - right}

    contracts = {
        "Start": contract({"type": "object", "required": ["start"],
                            "properties": {"start": numeric},
                            "additionalProperties": False}, result),
        "Left": contract({"type": "object", "required": ["value", "delta"],
                           "properties": {"value": numeric, "delta": numeric},
                           "additionalProperties": False}, result),
        "Right": contract({"type": "object", "required": ["value", "multiplier"],
                            "properties": {"value": numeric, "multiplier": numeric},
                            "additionalProperties": False}, result),
        "Join": contract({"type": "object", "required": ["left", "right"],
                           "properties": {"left": numeric, "right": numeric},
                           "additionalProperties": False}, result),
    }
    handlers = {"Start": function_start, "Left": function_left,
                "Right": function_right, "Join": function_join}
    r.add_local_provider("DiamondQA", contracts, handlers, "QA-only local dataflow",
                         {k: [] for k in contracts})
    for name in contracts:
        r.review_policy("AddOn.DiamondQA." + name, "READ_ONLY", "READ_ONLY", REVIEW)
    return r


def diamond_graph(seed):
    start, delta, mult = seed + 1, seed % 9 - 4, seed % 5 + 1
    ref = lambda step: {"$result": {"step": step, "pointer": "/value"}}
    prefix = "AddOn.DiamondQA."
    graph = {"operations": [
        {"id": "origin", "command": prefix + "Start", "params": {"start": start}},
        {"id": "arm_a", "command": prefix + "Left",
         "params": {"value": ref("origin"), "delta": delta}},
        {"id": "arm_b", "command": prefix + "Right",
         "params": {"value": ref("origin"), "multiplier": mult}},
        {"id": "join", "command": prefix + "Join",
         "after": ["arm_a"], "params": {
             "left": ref("arm_a"), "right": ref("arm_b")}},
    ]}
    return graph, (start + delta) - start * mult


def diamond_fanin_case(seed):
    def test(self):
        r = diamond_router()
        graph, oracle = diamond_graph(seed)
        plan = r.prepare_workflow(graph)
        self.assertEqual(plan["executionOrder"],
                         ["origin", "arm_a", "arm_b", "join"])
        self.assertEqual(plan["dependencies"]["arm_a"], ["origin"])
        self.assertEqual(plan["dependencies"]["arm_b"], ["origin"])
        self.assertEqual(plan["dependencies"]["join"], ["arm_a", "arm_b"])
        snapshots = []
        result = r.run_workflow(None, plan, checkpoint=snapshots.append)
        self.assertEqual(result["status"], "WORKFLOW_CALLABLE_VERIFIED")
        self.assertEqual(result["results"]["join"]["value"], oracle)
        self.assertEqual(len(result["trace"]), 4)
        self.assertEqual(len(snapshots), 4)
        self.assertEqual([s["status"] for s in snapshots],
                         ["WORKFLOW_CHECKPOINT"] * 4)
        self.assertEqual(len(r.local_events), 4)
        self.assertTrue(all(row["nativeWrites"] == 0 for row in r.local_events))
        self.assertFalse(result["automaticRetry"])
        self.assertFalse(plan["executionPermission"])
    return test


for seed in range(64):
    add_test("diamond_fanout_fanin", seed, diamond_fanin_case(seed))


def diamond_points(x, r):
    return [[x, r], [x + r, 0], [x, -r], [x - r, 0]]


def oblique_polygon_case(seed):
    def test(self):
        radius = 2 + seed % 7
        mode = seed % 4
        d = (2 * radius - 1 if mode == 0
             else 2 * radius if mode == 1
             else 2 * radius + (0.5 if mode == 2 else 0.25))
        tol = 0.5 if mode == 3 else 0
        output = LOCAL.polygon_relations([
            {"id": "diamond-a", "outline": diamond_points(0, radius)},
            {"id": "diamond-b", "outline": diamond_points(d, radius)},
        ], tolerance=tol)
        self.assertEqual(len(output["polygons"]), 2)
        for polygon in output["polygons"]:
            self.assertAlmostEqual(polygon["area"], 2 * radius * radius)
            self.assertAlmostEqual(polygon["perimeter"],
                                   4 * radius * math.sqrt(2))
        self.assertEqual(output["engineering"], "NOT_VERIFIED")
        self.assertEqual(output["scope"], "2D_SOURCE_POLYGONS_NOT_3D_NATIVE_COLLISION")
        if mode == 2:
            self.assertEqual(output["relations"], [])
            return
        self.assertEqual(len(output["relations"]), 1)
        relation = output["relations"][0]
        self.assertEqual((relation["first"], relation["second"]),
                         ("diamond-a", "diamond-b"))
        self.assertAlmostEqual(relation["intersectionArea"],
                               0.5 if mode == 0 else 0.0, places=6)
        self.assertEqual(relation["intersects"], mode in (0, 1))
        self.assertEqual(relation["touches"], mode == 1)
        self.assertAlmostEqual(relation["distance"],
                               0.25 if mode == 3 else 0.0, places=6)
    return test


for seed in range(64):
    add_test("nonrectangular_tolerance", seed, oblique_polygon_case(seed))


def tampered_plan_case(seed):
    def test(self):
        r = diamond_router()
        graph, _ = diamond_graph(seed)
        plan = r.prepare_workflow(graph)
        tampered = copy.deepcopy(plan)
        mode = seed % 6
        if mode == 0:
            tampered["executionPermission"] = True
        elif mode == 1:
            tampered["graph"]["operations"][0]["params"]["start"] += 1
        elif mode == 2:
            tampered["catalogHash"] = "0" * 64
        elif mode == 3:
            tampered["sourcePlanHash"] = "0" * 64
        elif mode == 4:
            tampered["executionOrder"] = list(reversed(tampered["executionOrder"]))
        else:
            tampered["dependencies"]["join"] = []
        with self.assertRaises(ValueError):
            r.run_workflow(None, tampered)
        self.assertEqual(r.local_events, [])
        self.assertEqual(r.callable, {})
        self.assertFalse(plan["executionPermission"])
    return test


for seed in range(48):
    add_test("plan_integrity_rejection", seed, tampered_plan_case(seed))


EXPECTED = 80 + 64 + 64 + 64 + 64 + 48
assert len(unittest.defaultTestLoader.loadTestsFromTestCase(
    IndependentBoundaryMatrix)._tests) == EXPECTED, "QA_TEST_COUNT_MISMATCH"

if __name__ == "__main__":
    unittest.main()
