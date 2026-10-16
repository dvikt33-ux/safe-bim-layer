"""Fast Downward planner integration: source-qualified alternatives, NO writes.

Tests actual FD solve when installed and host-side fail-closed validation.
These example prices are synthetic TEST FIXTURES, never LIVE measurements.
"""
from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import archicad_execution_optimizer as optimizer
import archicad_project_accelerator as apa


class FakeRouter:
    def __init__(self):
        self.calls = []

    def operation_kind(self, command):
        return {"MoveElements": "CREATE", "CreateColumns": "CREATE",
                "CreateBeams": "CREATE", "UnknownUnreviewed": "UNKNOWN"}.get(
                    command, "UNKNOWN")

    def prepare_workflow(self, graph):
        if not isinstance(graph, dict) or set(graph) != {"operations"}:
            raise ValueError("EXISTING_BIM_GRAPH_FORMAT_REQUIRED")
        if not graph["operations"]:
            raise ValueError("EMPTY_GRAPH")
        if any("command" not in op or "params" not in op or "id" not in op
               for op in graph["operations"]):
            raise ValueError("INVALID_TYPED_OPERATION")
        self.calls.append(graph)
        return {"schema": "APA_DYNAMIC_BIM_WORKFLOW_V1",
                "sourcePlanHash": apa.RUN.digest(graph),
                "graph": graph}

    def run_workflow(self, api, plan, writer, scopes, checkpoint):
        return {"status": "MOCK_SCENEWRITER_PATH",
                "graph": plan["graph"]}


def strategy(name, command, price, calls, source="verified-benchmark-receipt-fixture"):
    return {
        "id": name,
        "estimatedCostMs": price,
        "nativeCallCount": calls,
        "costEvidenceRef": source,
        "graph": {"operations": [{
            "id": "native_step",
            "command": command,
            "params": {"sourceQualified": True},
            "after": []
        }]}
    }


class PlannerTests(unittest.TestCase):
    def setUp(self):
        self.router = FakeRouter()

    def test_bulk_strategy_wins_by_measured_cost_not_first_list_position(self):
        # Strictly synthetic cost fixtures (not an Archicad performance claim).
        strategies = [
            strategy("individual_100_creates", "CreateColumns", 50000, 100),
            strategy("batch_100_copies", "MoveElements", 1300, 1),
            strategy("other_native_recipe", "CreateBeams", 5000, 2),
        ]
        intent = {"schemaVersion": "apa-native-optimizer/1",
                  "request": "Source-qualified wall frame 100 repeated studs",
                  "strategies": strategies}
        preview = apa.prepare_optimized_native_task(self.router, intent)
        self.assertEqual(preview["selectedStrategyId"], "batch_100_copies")
        self.assertEqual(preview["engine"], "fast-downward-opt")
        self.assertEqual(preview["alternativesExamined"], 3)
        self.assertEqual(preview["estimatedCostMs"], 1300)
        self.assertEqual(preview["nativeWritePermission"], False)
        self.assertEqual(preview["automaticNativeExecution"], False)
        self.assertEqual(preview["executor"], "EXISTING_APA_SCENEWRITER_ONLY")
        chosen = preview["selectedNativeTaskPreview"]
        self.assertEqual(chosen["schema"], "APA_NATIVE_TASK_PREVIEW_V1")
        self.assertEqual(chosen["workflow"]["graph"]["operations"][0]["command"],
                         "MoveElements")
        self.assertEqual(len(self.router.calls), 4)  # 3 checked + selected recompiled

    def test_engine_chooses_best_cost_not_just_fewest_calls(self):
        preview = optimizer.prepare_optimized_native_task(
            self.router, "Use cheapest source-verified native plan", [
                strategy("one_slow_native_call", "MoveElements", 8000, 1),
                strategy("two_quick_native_calls", "CreateColumns", 2500, 2),
            ])
        self.assertEqual(preview["selectedStrategyId"], "two_quick_native_calls")

    def test_rejects_unreviewed_command_even_if_cheap(self):
        with self.assertRaisesRegex(ValueError, "UNREVIEWED_COMMAND_EFFECT"):
            optimizer.prepare_optimized_native_task(
                self.router, "frame", [
                    strategy("unreviewed", "UnknownUnreviewed", 1, 1),
                    strategy("verified", "MoveElements", 2000, 1),
                ])

    def test_rejects_missing_cost_evidence_and_invalid_data(self):
        a = strategy("a", "MoveElements", 100, 1)
        b = strategy("b", "CreateColumns", 1000, 2)
        for field, invalid, reason in [
            ("costEvidenceRef", "", "COST_EVIDENCE"),
            ("estimatedCostMs", 0, "POSITIVE_COST"),
            ("estimatedCostMs", False, "POSITIVE_COST"),
            ("nativeCallCount", -1, "NATIVE_CALL_COUNT"),
        ]:
            modified = dict(a, **{field: invalid})
            with self.subTest(field=field):
                with self.assertRaisesRegex(ValueError, reason):
                    optimizer.prepare_optimized_native_task(
                        self.router, "frame", [modified, b])
        with self.assertRaisesRegex(ValueError, "UNIQUE_SAFE_STRATEGY_ID"):
            optimizer.prepare_optimized_native_task(
                self.router, "frame", [a, dict(b, id=a["id"])])

    def test_no_solver_fallback_when_environment_missing(self):
        with self.assertRaisesRegex(ValueError, "ENV_NOT_INSTALLED"):
            optimizer.prepare_optimized_native_task(
                self.router, "frame", [
                    strategy("a", "MoveElements", 100, 1),
                    strategy("b", "CreateColumns", 1000, 2),
                ], planner_python=ROOT / "absent-fast-downward-runtime.exe")

    def test_run_preserves_original_apa_run_native_task(self):
        strategies = [
            strategy("fast", "MoveElements", 1100, 1),
            strategy("slow", "CreateColumns", 7000, 100),
        ]
        preview = optimizer.prepare_optimized_native_task(
            self.router, "frame", strategies)
        outcome = apa.run_optimized_native_task(
            self.router, object(), preview, object(), {"foo": "bar"})
        self.assertEqual(outcome["status"], "MOCK_SCENEWRITER_PATH")
        self.assertEqual(outcome["graph"]["operations"][0]["command"], "MoveElements")

    def test_rejects_preview_permission_tampering(self):
        strategies = [
            strategy("fast", "MoveElements", 1100, 1),
            strategy("slow", "CreateColumns", 7000, 100),
        ]
        preview = optimizer.prepare_optimized_native_task(
            self.router, "frame", strategies)
        preview["nativeWritePermission"] = True
        with self.assertRaisesRegex(ValueError, "INVALID_PREVIEW"):
            apa.run_optimized_native_task(
                self.router, object(), preview, object(), {})
        self.assertEqual(preview["selectedNativeTaskPreview"]["executionPermission"], False)


if __name__ == "__main__":
    unittest.main()
