"""Offline tests. No Archicad connection and no changes to any PLN."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "archicad_batch_contracts.py"
spec = importlib.util.spec_from_file_location("archicad_batch_contracts", MODULE)
contracts = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contracts)


def wall():
    return {
        "begCoordinate": {"x": 23.0, "y": 20.0},
        "endCoordinate": {"x": 24.0, "y": 20.0},
        "floorIndex": 0, "height": 3.0, "thickness": 0.2,
        "zCoordinate": 0.0, "referenceLineLocation": "Center",
        "structureType": "Basic",
    }


def request(name, command, params):
    return {"id": name, "command": command, "params": params}


class BatchContractsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = contracts.load_catalog(ROOT / "tapir-1.5.8.json")

    def compile(self, *requests, runtime_version=None):
        return contracts.compile_batch(
            self.catalog, {"requests": list(requests)}, runtime_version)

    def test_all_command_references_resolve_without_live_api(self):
        report = contracts.audit(self.catalog)
        self.assertEqual(report["documentedCommandCount"], 236)
        self.assertEqual(report["unresolvedCommandRefCount"], 0)
        self.assertFalse(report["executionSupported"])

    def test_one_valid_wall_plan_never_executes(self):
        result = self.compile(request("a", "CreateWalls", {"wallsData": [wall()]}))
        self.assertEqual(result["status"], "SCHEMA_VALID")
        self.assertFalse(result["executionSupported"])
        self.assertFalse(result["jobPublished"])
        self.assertFalse(result["modelChanged"])
        self.assertEqual(result["results"][0]["disposition"], "TYPED_RECIPE_REQUIRED")

    def test_batch_three_distinct_command_families(self):
        result = self.compile(
            request("one", "CreateWalls", {"wallsData": [wall()]}),
            request("two", "GetStories", {}),
            request("three", "CreateMEPElements", {
                "elementsData": [{"type": "Terminal", "domain": "Piping",
                                  "position": {"x": 1, "y": 2, "z": 0}}],
            }),
        )
        self.assertEqual(result["validCount"], 3)
        self.assertEqual(result["invalidCount"], 0)

    def test_reject_invalid_geometry_by_schema(self):
        bad = wall()
        bad["height"] = -1
        result = self.compile(request("x", "CreateWalls", {"wallsData": [bad]}))
        self.assertEqual(result["status"], "INVALID")
        self.assertIn("height", str(result["results"][0]["errors"]))

    def test_reject_unknown_field_and_unsupported_command(self):
        bad = wall()
        bad["secretExtra"] = 999
        result = self.compile(
            request("a", "CreateWalls", {"wallsData": [bad]}),
            request("b", "ExecuteAnyTapirCommand", {}),
        )
        self.assertEqual(result["invalidCount"], 2)

    def test_reject_duplicate_id_even_across_valid_requests(self):
        result = self.compile(request("same", "GetStories", {}),
                              request("same", "GetProjectInfo", {}))
        self.assertEqual(result["invalidCount"], 1)
        self.assertIn("duplicate", " ".join(result["results"][1]["errors"]))

    def test_schema_version_mismatch_is_not_live_supported(self):
        result = self.compile(request("a", "CreateWalls", {"wallsData": [wall()]}),
                              runtime_version="1.5.10")
        self.assertEqual(result["status"], "REQUIRES_UPDATED_SCHEMA")
        self.assertFalse(result["runtimeSchemaMatch"])

    def test_special_review_commands_are_never_executable(self):
        result = self.compile(request("a", "QuitArchicad", {}))
        self.assertEqual(result["results"][0]["disposition"], "SPECIAL_REVIEW")
        self.assertFalse(result["executionSupported"])

    def test_empty_and_oversized_batches_fail(self):
        with self.assertRaises(ValueError):
            contracts.compile_batch(self.catalog, {"requests": []})
        with self.assertRaises(ValueError):
            contracts.compile_batch(self.catalog, {
                "requests": [request(str(i), "GetStories", {}) for i in range(101)]
            })


if __name__ == "__main__":
    unittest.main()
