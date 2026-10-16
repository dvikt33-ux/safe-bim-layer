"""V1 catalog auto-discovery: real Fast Downward, no native model writes.

Benchmark prices are synthetic test fixtures. Real production selection
requires end-to-end benchmark data for the exact batch/workload and same
reviewed command contract. User input supplies approved geometry/signature.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from archicad_dynamic_commands import DynamicCommands
from archicad_strategy_discovery import discover_native_execution_plan as plan
import archicad_project_accelerator as APA


STUD="WOOD_STUD_SECTION_100x50x2900_MATERIAL_A"
SOURCE="11111111-1111-4111-8111-111111111111"


class FakeExistingRouter:
    catalog = {"commands": {
        "MoveElements": {"availability":"LIVE_EXPORT_REGISTERED"},
        "CreateColumns": {"availability":"LIVE_EXPORT_REGISTERED"},
        "GetAllElements": {"availability":"LIVE_EXPORT_REGISTERED"},
        "UnknownTool": {"availability":"NOT_EXPOSED"},
    }}
    plan_reuse_existing = staticmethod(DynamicCommands.plan_reuse_existing)

    def __init__(self, copy="CREATE", create="CREATE"):
        self.kinds={"MoveElements":copy, "CreateColumns":create}

    def operation_kind(self, command):
        return self.kinds.get(command,"UNKNOWN")

    def contract_hash(self, command):
        return "test-native-contract-v1/" + command

    def prepare_workflow(self, graph):
        assert set(graph)=={"operations"}
        assert len(graph["operations"])==1
        step=graph["operations"][0]
        assert "command" in step and "id" in step and "params" in step
        if step["command"]=="MoveElements":
            rows=step["params"]["elementsWithMoveVectors"]
            assert all(row["copy"] is True for row in rows)
        if step["command"]=="CreateColumns":
            rows=step["params"]["columnsData"]
            assert all("buildingMaterialId" in row for row in rows)
        return {"schema": "APA_DYNAMIC_BIM_WORKFLOW_V1",
                "sourcePlanHash": APA.RUN.digest(graph), "graph": graph,
                "executionPermission":False}


def source():
    return {"guid": SOURCE,"type":"Column", "familySignature":STUD,
            "storyIndex":0,"anchor":{"x":0.0,"y":0.0,"z":0.0},
            "nativeReadbackVerified":True}


def targets(n=30, native=True):
    result=[]
    for i in range(n):
        x=1+i*.8
        row={"type":"Column","familySignature":STUD,"storyIndex":0,
             "anchor":{"x":x,"y":0.0,"z":0.0},"sourceRef":"KR-10"}
        if native:
            row["nativeCreateData"]={
                "coordinates":{"x":x,"y":0.0,"z":0.0},
                "width":.1,"depth":.05,"height":2.9,
                "floorIndex":0,
                "buildingMaterialId":{"guid":"22222222-2222-4222-8222-222222222222"},
            }
        result.append(row)
    return result


def intent(rows, costs=None, existing=None):
    return {"schemaVersion":"apa-native-auto/1",
            "request":"Place source-qualified timber frame",
            "existing":[source()] if existing is None else existing,
            "targets":rows,"benchmarks":costs or {}}


def prices(router, n=30, copy_time=1300, create_time=4400):
    return {
        "MoveElements": {
            "batchSize":n,"endToEndMs":copy_time,
            "evidenceRef":"SYNTHETIC_TEST_FIXTURE_COPY_BATCH",
            "contractHash":router.contract_hash("MoveElements")},
        "CreateColumns": {
            "batchSize":n,"endToEndMs":create_time,
            "evidenceRef":"SYNTHETIC_TEST_FIXTURE_CREATE_BATCH",
            "contractHash":router.contract_hash("CreateColumns")}
    }


class AutoDiscoveryTests(unittest.TestCase):
    def test_real_solver_auto_discovers_30_copy_vs_30_create(self):
        r=FakeExistingRouter()
        output=plan(r,intent(targets(30),prices(r)))
        self.assertEqual(output["status"],"COST_OPTIMAL_SOURCE_QUALIFIED_STRATEGY_PREPARED")
        self.assertEqual(output["selectedStrategyId"],"native_copy_existing_batch")
        self.assertEqual(output["discovery"]["catalogCommandCount"],4)
        self.assertEqual(output["discovery"]["qualifiedStrategies"],2)
        self.assertEqual(output["discovery"]["pendingUnmatchedTargets"],0)
        self.assertFalse(output["nativeWritePermission"])
        self.assertFalse(output["automaticNativeExecution"])
        action=output["selectedNativeTaskPreview"]["workflow"]["graph"]["operations"][0]
        self.assertEqual(action["command"],"MoveElements")
        copy_rows=action["params"]["elementsWithMoveVectors"]
        self.assertEqual(len(copy_rows),30)
        self.assertTrue(all(item["copy"] for item in copy_rows))
        self.assertTrue(all(item["elementId"]["guid"]==SOURCE for item in copy_rows))

    def test_real_solver_can_choose_batch_create_when_faster(self):
        r=FakeExistingRouter()
        output=plan(r,intent(targets(30),prices(r,copy_time=9000,create_time=1000)))
        self.assertEqual(output["selectedStrategyId"],"native_create_columns_batch")
        op=output["selectedNativeTaskPreview"]["workflow"]["graph"]["operations"][0]
        self.assertEqual(op["command"],"CreateColumns")
        self.assertEqual(len(op["params"]["columnsData"]),30)

    def test_without_verified_cost_comparison_do_not_claim_optimality(self):
        r=FakeExistingRouter()
        no_cost=plan(r,intent(targets(30)))
        self.assertEqual(no_cost["status"],"COST_COMPARISON_BLOCKED_UNCALIBRATED_ALTERNATIVES")
        self.assertIsNone(no_cost["selectedNativeTaskPreview"])
        self.assertEqual(set(no_cost["unmeasuredCommands"]),{"MoveElements","CreateColumns"})
        one_cost=plan(r,intent(targets(30),{"MoveElements":prices(r)["MoveElements"]}))
        self.assertEqual(one_cost["unmeasuredCommands"],["CreateColumns"])
        self.assertFalse(one_cost["nativeWritePermission"])

    def test_single_discovered_copy_does_not_pretend_solver_optimized(self):
        r=FakeExistingRouter()
        output=plan(r,intent(targets(30,native=False)))
        self.assertEqual(output["status"],"ONE_SOURCE_QUALIFIED_STRATEGY_PREPARED")
        self.assertEqual(output["selectedStrategyId"],"native_copy_existing_batch")
        self.assertEqual(output["selectionMethod"],"SOLE_FEASIBLE_TYPED_OPTION_NOT_COST_OPTIMIZATION")
        self.assertEqual(output["discovery"]["qualifiedStrategies"],1)

    def test_no_changes_when_every_target_already_exists(self):
        r=FakeExistingRouter()
        row={"type":"Column","familySignature":STUD,"storyIndex":0,
             "anchor":{"x":0,"y":0,"z":0},"sourceRef":"KR-10"}
        result=plan(r,intent([row]))
        self.assertEqual(result["status"],"NO_CHANGES_REQUIRED")
        self.assertIsNone(result["selectedNativeTaskPreview"])

    def test_unmatched_family_never_silently_partial_copies(self):
        r=FakeExistingRouter()
        rows=targets(3,native=False)
        rows[1]["familySignature"]="DIFFERENT_UNVERIFIED_FAMILY_555555"
        with self.assertRaisesRegex(ValueError,"NO_COMPLETE_QUALIFIED_STRATEGY"):
            plan(r,intent(rows))

    def test_create_only_when_source_verified_native_data_exists(self):
        r=FakeExistingRouter()
        rows=targets(4)
        # Different source signature -> can't copy, but exact source-created
        # Column data is present, so create-only is safe as *preview*.
        for item in rows:
            item["familySignature"]="BRAND_NEW_COLUMN_SECTION_200x100x2900"
        out=plan(r,intent(rows))
        self.assertEqual(out["status"],"ONE_SOURCE_QUALIFIED_STRATEGY_PREPARED")
        self.assertEqual(out["selectedStrategyId"],"native_create_columns_batch")
        self.assertEqual(out["discovery"]["pendingUnmatchedTargets"],4)

    def test_invalid_material_or_wrong_coordinate_blocks_create_strategy(self):
        r=FakeExistingRouter(copy="UNKNOWN")
        rows=targets(2)
        rows[0]["nativeCreateData"]["coordinates"]["x"]=999.
        with self.assertRaisesRegex(ValueError,"NO_COMPLETE_QUALIFIED_STRATEGY"):
            plan(r,intent(rows))
        rows=targets(2)
        del rows[0]["nativeCreateData"]["buildingMaterialId"]
        with self.assertRaisesRegex(ValueError,"NO_COMPLETE_QUALIFIED_STRATEGY"):
            plan(r,intent(rows))

    def test_catalog_policy_blocks_unreviewed_native_methods(self):
        r=FakeExistingRouter(copy="UNKNOWN",create="UNKNOWN")
        with self.assertRaisesRegex(ValueError,"NO_COMPLETE_QUALIFIED_STRATEGY"):
            plan(r,intent(targets(5,native=False)))

    def test_no_auto_creation_for_beams_without_exact_native_rows(self):
        r=FakeExistingRouter()
        beam={"type":"Beam","familySignature":"BEAM_SECTION_200x100_4000M_123",
              "storyIndex":0,"anchor":{"x":12,"y":3,"z":2.9},
              "sourceRef":"KR-13"}
        with self.assertRaisesRegex(ValueError,"NO_COMPLETE_QUALIFIED_STRATEGY"):
            plan(r,intent([beam]))

    def test_duplicate_destination_and_unverified_existing_source_block(self):
        r=FakeExistingRouter()
        row=targets(1)[0]
        with self.assertRaisesRegex(ValueError,"TARGET_POSITION_DUPLICATED"):
            plan(r,intent([row,row]))
        bad=source();bad["nativeReadbackVerified"]=False
        with self.assertRaisesRegex(ValueError,"LIVE_EXISTING_PROTOTYPE"):
            plan(r,intent(targets(2),existing=[bad]))

    def test_benchmark_drift_or_wrong_batch_count_blocks(self):
        r=FakeExistingRouter()
        cost=prices(r)
        cost["MoveElements"]["batchSize"]=15
        with self.assertRaisesRegex(ValueError,"BENCHMARK_WORKLOAD_MISMATCH"):
            plan(r,intent(targets(30),cost))
        cost=prices(r)
        cost["CreateColumns"]["contractHash"]="old-revision"
        with self.assertRaisesRegex(ValueError,"BENCHMARK_COMMAND_CONTRACT_DRIFT"):
            plan(r,intent(targets(30),cost))

    def test_all_native_operations_remain_prepared_without_execution(self):
        r=FakeExistingRouter()
        output=plan(r,intent(targets(30),prices(r)))
        self.assertFalse(output["selectedNativeTaskPreview"]["executionPermission"])
        self.assertEqual(output["selectedNativeTaskPreview"]["executor"],"SceneWriter")


if __name__=="__main__":
    unittest.main()
