"""APA independent advanced offline matrix, continuation after PR #90.

288 NEW uniquely seeded test IDs; does not import or discover older suites.
Exercises the actual DynamicCommands router, BIM Graph execution, and
IfcOpenShell-backed APA adapters. This is not an Archicad LIVE test.
"""
from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import archicad_local_modules as L
from archicad_dynamic_commands import DynamicCommands

EVIDENCE = {"source": "Synthetic QA-only reviewed handlers", "sha256": "4" * 64}


def case_id(cls, category, n, function):
    setattr(cls, f"test_advanced_{category}_{n:03d}", function)


def empty_router():
    return DynamicCommands({
        "common_schemas": {},
        "commands": {},
        "_metadata": {"provider_version": "1.5.10"},
    })


def contract(params, returns):
    return {
        "version": "1", "category": "Synthetic offline QA",
        "parameters": params, "returns": returns,
    }


class AdvancedIndependentMatrix(unittest.TestCase):
    """All scenarios are deterministic and isolated from native model writes."""


def nested_reference_case(seed):
    def test(self):
        router = empty_router()
        refs = {
            "Leaf": {
                "type": "object", "required": ["n"],
                "properties": {"n": {"type": "integer", "minimum": 0, "maximum": 10000}},
                "additionalProperties": False,
            },
            "Bucket": {
                "type": "object", "required": ["entries"],
                "properties": {"entries": {
                    "type": "array", "minItems": 1,
                    "items": {"$ref": "#/Leaf"},
                }},
                "additionalProperties": False,
            },
            "Envelope": {
                "type": "object", "required": ["data"],
                "properties": {"data": {"$ref": "#/Bucket"}},
                "additionalProperties": False,
            },
        }
        namespace = f"Nested{seed}"
        key = f"AddOn.{namespace}.Process"
        router.add_provider(namespace, {
            "Process": contract({"$ref": "#/Envelope"}, {"type": "object"}),
        }, "QA contract only", refs)
        value = (seed * 157) % 10001
        valid = {"data": {"entries": [{"n": value}]}}
        ticket = router.prepare(key, valid)
        self.assertEqual(ticket["parameters"], valid)
        self.assertFalse(ticket["nativeWritePermission"])
        self.assertEqual(router.select(key)["runtimeRegistered"], None)
        invalid = copy.deepcopy(valid)
        mode = seed % 4
        if mode == 0:
            invalid["data"]["entries"][0]["n"] = "number"
        elif mode == 1:
            invalid["data"]["entries"] = []
        elif mode == 2:
            invalid["data"]["entries"][0]["unlisted"] = seed
        else:
            invalid["data"].pop("entries")
        with self.assertRaises(Exception):
            router.prepare(key, invalid)
        self.assertEqual(router.validate(ticket)["hash"], ticket["hash"])
    return test


for n in range(64):
    case_id(AdvancedIndependentMatrix, "nested_ref_contract", n, nested_reference_case(n))


def escaped_pointer_case(seed):
    def test(self):
        router = empty_router()
        router.catalog["common_schemas"]["Leaf"] = {
            "type": "object", "required": ["n"],
            "properties": {"n": {"type": "integer"}},
        }
        schema = {
            "type": "object",
            "properties": {
                "a/b": {"type": "array", "items": {"$ref": "#/Leaf"}},
                "m~n": {"type": "array", "items": {"type": "integer"}},
                "plain": {"type": "array", "items": {
                    "type": "object", "properties": {"nested": {"type": "string"}},
                }},
            },
        }
        payload = {
            "a/b": [{"n": seed + 11}],
            "m~n": [seed * 2 + 3],
            "plain": [{"nested": "tag-" + str(seed)}],
        }
        mode = seed % 4
        pointer, expected_type, expected = [
            ("/a~1b/0/n", "integer", seed + 11),
            ("/m~0n/0", "integer", seed * 2 + 3),
            ("/plain/0/nested", "string", "tag-" + str(seed)),
            ("/a~1b/0", None, {"n": seed + 11}),
        ][mode]
        target_schema = router._schema_at(schema, pointer)
        if expected_type is not None:
            self.assertEqual(target_schema["type"], expected_type)
        else:
            self.assertEqual(router._schema_example(target_schema), {"n": 1})
        value = router._result_at(payload, pointer)
        self.assertEqual(value, expected)
        if isinstance(value, dict):
            value["n"] = -1
            self.assertEqual(payload["a/b"][0]["n"], seed + 11)
    return test


for n in range(48):
    case_id(AdvancedIndependentMatrix, "escaped_pointer_schema_value", n, escaped_pointer_case(n))


def local_pipeline_router(bad_source=None, trace=None):
    router = empty_router()
    int_schema = {"type": "integer"}
    result_schema = {
        "type": "object", "required": ["value"],
        "properties": {"value": int_schema}, "additionalProperties": False,
    }
    definitions = {
        "Source": contract({
            "type": "object", "required": ["start"],
            "properties": {"start": int_schema}, "additionalProperties": False,
        }, result_schema),
        "Middle": contract({
            "type": "object", "required": ["value", "offset"],
            "properties": {"value": int_schema, "offset": int_schema},
            "additionalProperties": False,
        }, result_schema),
        "Final": contract({
            "type": "object", "required": ["value", "factor"],
            "properties": {"value": int_schema, "factor": int_schema},
            "additionalProperties": False,
        }, result_schema),
    }
    def source(start):
        if trace is not None:
            trace.append("source")
        return {"value": start} if bad_source is None else {"value": bad_source}
    def middle(value, offset):
        if trace is not None:
            trace.append("middle")
        return {"value": value + offset}
    def final(value, factor):
        if trace is not None:
            trace.append("final")
        return {"value": value * factor}
    names = {"Source": source, "Middle": middle, "Final": final}
    router.add_local_provider("QALocal", definitions, names, "QA non-native handlers",
                              {k: [] for k in names})
    for name in names:
        router.review_policy("AddOn.QALocal." + name, "READ_ONLY", "READ_ONLY", EVIDENCE)
    return router


def pipeline_graph(start, offset, factor):
    source = "AddOn.QALocal."
    return {"operations": [
        {"id": "first", "command": source + "Source", "params": {"start": start}},
        {"id": "second", "command": source + "Middle",
         "params": {"value": {"$result": {"step": "first", "pointer": "/value"}},
                    "offset": offset}},
        {"id": "third", "command": source + "Final",
         "params": {"value": {"$result": {"step": "second", "pointer": "/value"}},
                    "factor": factor}},
    ]}


def workflow_pipeline_case(seed):
    def test(self):
        router = local_pipeline_router()
        start, offset, factor = seed + 2, seed % 13 - 6, seed % 7 + 1
        graph = pipeline_graph(start, offset, factor)
        plan = router.prepare_workflow(graph)
        self.assertEqual(plan["executionOrder"], ["first", "second", "third"])
        self.assertEqual(plan["dependencies"]["second"], ["first"])
        self.assertEqual(plan["dependencies"]["third"], ["second"])
        self.assertIs(plan["executionPermission"], False)
        output = router.run_workflow(None, plan)
        self.assertEqual(output["status"], "WORKFLOW_CALLABLE_VERIFIED")
        self.assertEqual(output["results"]["third"]["value"], (start + offset) * factor)
        self.assertEqual(len(output["trace"]), 3)
        self.assertEqual(len(router.local_events), 3)
        self.assertTrue(all(entry["nativeWrites"] == 0 for entry in router.local_events))
        self.assertFalse(output["automaticRetry"])
    return test


for n in range(48):
    case_id(AdvancedIndependentMatrix, "three_step_result_pipeline", n, workflow_pipeline_case(n))


def independent_namespace_case(seed):
    def test(self):
        router = empty_router()
        left = f"StrictLeft{seed}"
        right = f"StrictRight{seed}"
        key_a, key_b = f"AddOn.{left}.Echo", f"AddOn.{right}.Echo"
        router.add_provider(left, {
            "Echo": contract({"$ref": "#/Payload"}, {"type": "object"}),
        }, "independent source A", {"Payload": {
            "type": "object", "properties": {"value": {"type": "integer"}},
            "required": ["value"], "additionalProperties": False,
        }})
        first_hash = router.contract_hash(key_a)
        router.add_provider(right, {
            "Echo": contract({"$ref": "#/Payload"}, {"type": "object"}),
        }, "independent source B", {"Payload": {
            "type": "object", "properties": {"value": {"type": "string"}},
            "required": ["value"], "additionalProperties": False,
        }})
        self.assertEqual(router.contract_hash(key_a), first_hash)
        self.assertEqual(router.prepare(key_a, {"value": seed})["command"], key_a)
        self.assertEqual(router.prepare(key_b, {"value": str(seed)})["command"], key_b)
        with self.assertRaises(Exception):
            router.prepare(key_a, {"value": str(seed)})
        with self.assertRaises(Exception):
            router.prepare(key_b, {"value": seed})
        self.assertEqual(router.select(key_a)["runtimeRegistered"], None)
        self.assertEqual(router.select(key_b)["runtimeRegistered"], None)
    return test


for n in range(48):
    case_id(AdvancedIndependentMatrix, "independent_apx_provider_contract", n,
            independent_namespace_case(n))


def ifc_structure_case(seed):
    def test(self):
        import ifcopenshell
        mode = seed % 3
        with tempfile.TemporaryDirectory(prefix="apa_ifc_qa_") as directory:
            path = Path(directory) / f"qa-{seed}.ifc"
            if mode == 2:
                invalid_path = Path(directory) / f"qa-{seed}.txt"
                invalid_path.write_text("not an IFC", encoding="utf8")
                with self.assertRaises(ValueError):
                    L.ifc_select(str(invalid_path), "IfcWall")
                with self.assertRaises(ValueError):
                    L.ifc_select(str(path), "IfcWall")
                return
            model = ifcopenshell.file(schema="IFC4")
            wall_a = model.create_entity("IfcWall", GlobalId=ifcopenshell.guid.new(),
                                         Name=f"Wall_{seed}_A")
            wall_b = model.create_entity("IfcWall", GlobalId=ifcopenshell.guid.new(),
                                         Name=f"Wall_{seed}_B")
            model.create_entity("IfcDoor", GlobalId=ifcopenshell.guid.new(),
                                Name=f"Door_{seed}")
            model.write(str(path))
            selected = L.ifc_select(str(path), "IfcWall")
            self.assertEqual(selected["schema"], "IFC4")
            self.assertEqual(len(selected["elements"]), 2)
            self.assertEqual({r["name"] for r in selected["elements"]},
                             {f"Wall_{seed}_A", f"Wall_{seed}_B"})
            self.assertEqual({r["ifcId"] for r in selected["elements"]},
                             {wall_a.GlobalId, wall_b.GlobalId})
            self.assertEqual({r["type"] for r in selected["elements"]}, {"IfcWall"})
            self.assertEqual(selected["semanticCompatibility"], "NOT_VERIFIED")
            if mode == 1:
                result = L.ifc_geometry(str(path), [wall_a.GlobalId, wall_b.GlobalId])
                self.assertEqual(result["engineering"], "NOT_VERIFIED")
                self.assertEqual([r["ifcId"] for r in result["elements"]],
                                 [wall_a.GlobalId, wall_b.GlobalId])
                self.assertTrue(all(row["status"] == "IFC_GEOMETRY_NOT_AVAILABLE"
                                    for row in result["elements"]))
    return test


for n in range(48):
    case_id(AdvancedIndependentMatrix, "synthetic_ifc_structure", n, ifc_structure_case(n))


def no_downstream_after_bad_result_case(seed):
    def test(self):
        trace = []
        failures = ["wrong-" + str(seed), [seed], {"wrong": seed}, None, True]
        bad = failures[seed % len(failures)]
        # None would collide with the success sentinel; use string instead.
        if bad is None:
            bad = "null-value-" + str(seed)
        router = local_pipeline_router(bad_source=bad, trace=trace)
        graph = pipeline_graph(seed + 1, 2, 3)
        plan = router.prepare_workflow(graph)
        with self.assertRaises(Exception):
            router.run_workflow(None, plan)
        self.assertEqual(trace, ["source"])
        self.assertEqual(router.local_events, [])
        self.assertEqual(router.callable, {})
        self.assertIs(plan["executionPermission"], False)
    return test


for n in range(32):
    case_id(AdvancedIndependentMatrix, "invalid_source_blocks_downstream", n,
            no_downstream_after_bad_result_case(n))


EXPECTED_CASES = 64 + 48 + 48 + 48 + 48 + 32
assert len(unittest.defaultTestLoader.loadTestsFromTestCase(
    AdvancedIndependentMatrix)._tests) == EXPECTED_CASES, "ADVANCED_TEST_DISCOVERY_MISMATCH"

if __name__ == "__main__":
    unittest.main()
