"""Regression checks for the template live-launcher status contract.

These tests are offline and NEVER connect to Archicad or write a PLN.
"""
import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "archicad_template_builder.py"
SPEC = importlib.util.spec_from_file_location("archicad_template_builder_under_test", SCRIPT)
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


class FakeTapir:
    def __init__(self, attribute_error=False, geo_error=False):
        self.attribute_error = attribute_error
        self.geo_error = geo_error

    def call(self, command, parameters=None):
        if command == "GetProjectInfo":
            return {
                "isUntitled": False,
                "projectName": "CANDIDATE",
                "projectPath": "C:\\candidate\\template.pln",
            }
        if command == "GetProjectInfoFields":
            return {"fields": []}
        if command == "GetAllElements":
            return {"elements": []}
        if command == "GetAttributesByType":
            if self.attribute_error and parameters["attributeType"] == "Fill":
                raise RuntimeError("Fill enumeration unavailable")
            return {"attributes": []}
        if command == "GetModelViewOptions":
            return {"modelViewOptions": []}
        if command == "GetCalculationUnits":
            return {"length": {"unit": "Millimeter"}}
        if command == "GetGeoLocation":
            if self.geo_error:
                raise RuntimeError("Coordinate query failed")
            return {"surveyPoint": {}}
        if command == "GetStories":
            return {"stories": []}
        raise AssertionError(f"Unexpected fake Tapir command: {command}")


class TemplateStatusContractTests(unittest.TestCase):
    def test_successful_inspect_is_explicit_pass(self):
        result = builder.live_inventory(FakeTapir())
        self.assertEqual(result["status"], "PASS")
        self.assertFalse(result["writePerformed"])
        self.assertEqual(result["readErrors"], {})

    def test_attribute_read_error_blocks_inspect(self):
        result = builder.live_inventory(FakeTapir(attribute_error=True))
        self.assertEqual(result["status"], "BLOCKED_INVENTORY")
        self.assertIn("attribute:Fill", result["readErrors"])

    def test_geolocation_read_error_blocks_inspect(self):
        result = builder.live_inventory(FakeTapir(geo_error=True))
        self.assertEqual(result["status"], "BLOCKED_INVENTORY")
        self.assertIn("geoLocation", result["readErrors"])

    def test_successful_plan_is_explicit_pass(self):
        inventory = builder.live_inventory(FakeTapir())
        with patch.object(builder, "validate_specs", return_value={"status": "PASS"}):
            result = builder.plan_summary(inventory)
        self.assertEqual(result["status"], "PASS")
        self.assertFalse(result["writePerformed"])

    def test_failed_inventory_cannot_become_passing_plan(self):
        inventory = builder.live_inventory(FakeTapir(attribute_error=True))
        with patch.object(builder, "validate_specs", return_value={"status": "PASS"}):
            result = builder.plan_summary(inventory)
        self.assertEqual(result["status"], "BLOCKED_INVENTORY")

    def test_validation_failure_blocks_plan(self):
        inventory = builder.live_inventory(FakeTapir())
        with patch.object(builder, "validate_specs", return_value={"status": "FAIL"}):
            result = builder.plan_summary(inventory)
        self.assertEqual(result["status"], "FAIL")

    def test_blocked_cli_returns_nonzero_even_with_json(self):
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder) / "result.json"
            with patch.object(builder, "EVIDENCE_ROOT", Path(folder) / "evidence"):
                with patch.object(
                    builder, "check_windows_fonts",
                    return_value={"status": "BLOCKED_FONT_MISSING", "requiredMissing": ["Test"]},
                ):
                    with patch.object(
                        sys, "argv", ["builder", "font-preflight", "--out", str(destination)]
                    ):
                        with contextlib.redirect_stdout(io.StringIO()):
                            with self.assertRaises(SystemExit) as ctx:
                                builder.main()
            self.assertEqual(ctx.exception.code, 2)
            self.assertEqual(json.loads(destination.read_text(encoding="utf-8"))["status"],
                             "BLOCKED_FONT_MISSING")

    def test_passing_cli_returns_normally(self):
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder) / "result.json"
            with patch.object(builder, "EVIDENCE_ROOT", Path(folder) / "evidence"):
                with patch.object(builder, "check_windows_fonts", return_value={"status": "PASS"}):
                    with patch.object(sys, "argv", ["builder", "font-preflight", "--out", str(destination)]):
                        with contextlib.redirect_stdout(io.StringIO()):
                            builder.main()
            self.assertEqual(json.loads(destination.read_text(encoding="utf-8"))["status"], "PASS")



    def test_apply_core_pass_only_after_successful_live_readback(self):
        # Stub all mutations; the test exercises the returned contract only.
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.object(builder, "validate_specs", return_value={"status": "PASS"}))
            for name in (
                "create_project_info_fields",
                "create_layers",
                "create_pen_tables",
                "create_line_types",
                "create_layer_combinations",
            ):
                stack.enter_context(patch.object(builder, name, return_value={}))
            stack.enter_context(patch.object(
                builder, "live_inventory",
                return_value={
                    "status": "PASS",
                    "elementCount": 0,
                    "attributes": {},
                    "projectInfoFields": [
                        {"projectInfoName": key, "projectInfoValue": val}
                        for key, val in builder.project_info_targets().items()
                    ],
                },
            ))
            result = builder.apply_safe_core(FakeTapir())
        self.assertEqual(result["status"], "PASS")
        self.assertTrue(result["postconditions"]["geometryCountUnchanged"])
        self.assertEqual(
            result["postconditions"]["projectInfoFields"],
            builder.project_info_targets(),
        )

    def test_apply_core_never_returns_pass_on_incomplete_readback(self):
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.object(builder, "validate_specs", return_value={"status": "PASS"}))
            for name in (
                "create_project_info_fields",
                "create_layers",
                "create_pen_tables",
                "create_line_types",
                "create_layer_combinations",
            ):
                stack.enter_context(patch.object(builder, name, return_value={}))
            stack.enter_context(patch.object(
                builder, "live_inventory",
                return_value={"status": "BLOCKED_INVENTORY", "readErrors": {"geoLocation": "offline test"}},
            ))
            with self.assertRaisesRegex(RuntimeError, "read-back inventory is incomplete"):
                builder.apply_safe_core(FakeTapir())

    def test_apply_core_blocks_missing_project_info_in_readback(self):
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.object(builder, "validate_specs", return_value={"status": "PASS"}))
            for name in (
                "create_project_info_fields",
                "create_layers",
                "create_pen_tables",
                "create_line_types",
                "create_layer_combinations",
            ):
                stack.enter_context(patch.object(builder, name, return_value={}))
            with self.assertRaisesRegex(RuntimeError, "Project Info read-back mismatch"):
                builder.apply_safe_core(FakeTapir())

    def test_apply_cli_without_expected_project_path_blocks_before_write(self):
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder) / "blocked.json"
            with contextlib.ExitStack() as stack:
                stack.enter_context(patch.object(builder, "Tapir", return_value=FakeTapir()))
                stack.enter_context(patch.object(builder, "EVIDENCE_ROOT", Path(folder) / "evidence"))
                apply = stack.enter_context(patch.object(builder, "apply_safe_core"))
                stack.enter_context(patch.object(
                    sys, "argv", ["builder", "apply-core", "--out", str(destination)]
                ))
                with contextlib.redirect_stdout(io.StringIO()):
                    with self.assertRaises(SystemExit) as ctx:
                        builder.main()
            self.assertEqual(ctx.exception.code, 2)
            self.assertEqual(json.loads(destination.read_text(encoding="utf-8"))["status"],
                             "BLOCKED_PROJECT_CONFIRMATION")
            apply.assert_not_called()

    def test_apply_cli_mismatched_project_path_blocks_before_write(self):
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder) / "blocked.json"
            with contextlib.ExitStack() as stack:
                stack.enter_context(patch.object(builder, "Tapir", return_value=FakeTapir()))
                stack.enter_context(patch.object(builder, "EVIDENCE_ROOT", Path(folder) / "evidence"))
                apply = stack.enter_context(patch.object(builder, "apply_safe_core"))
                stack.enter_context(patch.object(
                    sys, "argv", [
                        "builder", "apply-core", "--expected-project-path", "C:\\other.pln",
                        "--out", str(destination),
                    ]
                ))
                with contextlib.redirect_stdout(io.StringIO()):
                    with self.assertRaises(SystemExit) as ctx:
                        builder.main()
            self.assertEqual(ctx.exception.code, 2)
            self.assertEqual(json.loads(destination.read_text(encoding="utf-8"))["status"],
                             "BLOCKED_ACTIVE_PROJECT_CHANGED")
            apply.assert_not_called()

    def test_apply_cli_exact_project_path_accepts_guarded_stage(self):
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder) / "passed.json"
            with contextlib.ExitStack() as stack:
                stack.enter_context(patch.object(builder, "Tapir", return_value=FakeTapir()))
                stack.enter_context(patch.object(builder, "EVIDENCE_ROOT", Path(folder) / "evidence"))
                apply = stack.enter_context(patch.object(
                    builder, "apply_safe_core", return_value={"status": "PASS"}
                ))
                stack.enter_context(patch.object(
                    sys, "argv", [
                        "builder", "apply-core", "--expected-project-path",
                        "C:\\candidate\\template.pln", "--out", str(destination),
                    ]
                ))
                with contextlib.redirect_stdout(io.StringIO()):
                    builder.main()
            self.assertEqual(json.loads(destination.read_text(encoding="utf-8"))["status"],
                             "PASS")
            apply.assert_called_once()

if __name__ == "__main__":
    unittest.main()
