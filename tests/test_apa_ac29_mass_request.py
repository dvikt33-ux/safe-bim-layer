"""Offline source/graph tests. Mocked dispatch is not native LIVE evidence."""
from pathlib import Path
import copy
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import apa_ac29_mass_request as M
import archicad_project_accelerator as A
from archicad_dynamic_commands import DynamicCommands
from archicad_batch_contracts import load_catalog
from test_apa_ac29_native_group_grid import input_source


def request(grouped=True, mode="GRID"):
    existing, assembly = input_source()
    return dict(schemaVersion=M.SCHEMA,
                request="Replicate group in a grid" if grouped else "Copy elements along a line",
                sourceRef=assembly["sourceRef"], existing=existing if grouped else existing[:1],
                assembly=assembly if grouped else None,
                placements=(dict(mode="GRID", columns=8, rows=4, stepX=25, stepY=8,
                                 startDx=25, startDy=0) if mode == "GRID" else
                            dict(mode="LINEAR", count=3, start=dict(dx=10, dy=0, dz=0),
                                 step=dict(dx=10, dy=0, dz=0))))


def router(registered=True):
    root = Path(__file__).resolve().parents[1]
    r = DynamicCommands(load_catalog(root / "tapir-1.5.8.json"))
    A.connect_functional_modules(r)
    if registered:
        r.register_availability("AddOn.TapirCommand.CloneNativeGroupV1", True)
        r.register_availability("MoveElements", True)
    return r


class MassRequestTests(unittest.TestCase):
    def test_grid_uses_existing_entrypoint_one_native_clone_no_create(self):
        task = request()
        original = copy.deepcopy(task)
        result = A.prepare_auto_optimized_native_task(router(), task)
        self.assertEqual(result["status"], "ONE_SOURCE_QUALIFIED_STRATEGY_PREPARED")
        self.assertEqual(result["requiredRuntimeCommands"], ["AddOn.TapirCommand.CloneNativeGroupV1"])
        self.assertEqual(result["groupedTargetCount"], 64)
        self.assertEqual(result["nativeCallCountIfAuthorized"], 1)
        self.assertEqual(result["optimality"], "UNCALIBRATED_NO_SPEED_CLAIM")
        self.assertFalse(result["nativeWritePermission"])
        self.assertEqual(task, original)

    def test_ungrouped_linear_uses_single_existing_move_copy_batch(self):
        result = A.prepare_auto_optimized_native_task(router(), request(False, "LINEAR"))
        self.assertEqual(result["requiredRuntimeCommands"], ["MoveElements"])
        ops = result["selectedNativeTaskPreview"]["workflow"]["graph"]["operations"]
        rows = ops[0]["params"]["elementsWithMoveVectors"]
        self.assertEqual(len(ops), 1)
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(row["copy"] is True for row in rows))

    def test_source_only_runtime_is_not_dispatchable(self):
        preview = A.prepare_auto_optimized_native_task(router(False), request())
        self.assertIsNone(preview["selectedNativeTaskPreview"])
        with self.assertRaisesRegex(ValueError, "NOT_READY"):
            A.run_auto_optimized_native_task(router(), object(), preview, object(), object())

    def test_axes_keep_nonuniform_source_coordinates(self):
        task = request(False)
        task["request"] = "Распределить копии по осям"
        task["placements"] = dict(mode="AXIS_INTERSECTIONS", sourceRef=task["sourceRef"],
            X=[dict(id="1", coordinate=10), dict(id="2", coordinate=23)],
            Y=[dict(id="A", coordinate=0), dict(id="B", coordinate=8)],
            reference=dict(x=0,y=0,z=0), requiresNativeAxisObjects=False)
        intent = M.normalize_mass_request(task)
        self.assertEqual([r["anchor"]["x"] for r in intent["targets"]], [10,23,10,23])
        task["placements"]["requiresNativeAxisObjects"] = True
        with self.assertRaisesRegex(ValueError, "OWN_VERIFIER"):
            M.normalize_mass_request(task)

    def test_unknown_boolean_or_unproven_groups_fail_before_router(self):
        for text in ("boolean union bodies", "Слить тела", "Something unrelated"):
            task = request(); task["request"] = text
            with self.subTest(text=text), self.assertRaises(ValueError):
                M.normalize_mass_request(task)
        task = request(); task["assembly"]["groupReadbackVerified"] = False
        with self.assertRaisesRegex(ValueError, "VERIFIED_TWO_COLUMN"):
            M.normalize_mass_request(task)

    def test_bad_inputs_and_unsupported_group_family_fail_closed(self):
        for mutate in (lambda t: t["existing"][0].update(nativeReadbackVerified=False),
                       lambda t: t["existing"][0].update(type="Beam"),
                       lambda t: t["placements"].update(columns=33),
                       lambda t: t["placements"].update(stepX=float("nan"))):
            task = request(); mutate(task)
            with self.assertRaises(ValueError): M.normalize_mass_request(task)

    def test_zero_and_duplicate_offsets_rejected(self):
        for values in ([dict(dx=0,dy=0,dz=0)], [dict(dx=10,dy=0,dz=0)] * 2):
            with self.assertRaisesRegex(ValueError, "DUPLICATE_ZERO"):
                M.placement_offsets(dict(mode="TRANSLATIONS", values=values))

    def test_selected_request_delegates_to_original_graph_executor(self):
        r = router(); selected = A.prepare_auto_optimized_native_task(r, request())
        with patch.object(A, "run_native_task", return_value={"status":"OFFLINE_DISPATCH_SENTINEL"}) as run:
            result = A.run_auto_optimized_native_task(r, "api", selected, "writer", "scopes")
            self.assertEqual(result["status"], "OFFLINE_DISPATCH_SENTINEL")
            self.assertEqual(run.call_args.args[:2], (r, "api"))
            self.assertEqual(run.call_args.args[3:5], ("writer", "scopes"))


if __name__ == "__main__":
    unittest.main()
