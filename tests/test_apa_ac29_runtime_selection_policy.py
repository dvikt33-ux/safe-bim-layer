"""Focused regression of read-only runtime-selection policy; no Archicad calls."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from archicad_strategy_discovery import select_uniquely_registered_read_alternative


def fixture(kind="READ_ONLY", duplicate=False):
    class Router:
        def operation_kind(self, command):
            return kind

    def option(id_, commands):
        return {
            "id": id_,
            "commands": commands,
            "executionBlockers": [],
            "graph": {"operations": [
                {"command": name, "id": str(index), "params": {}}
                for index, name in enumerate(commands)
            ]},
            "nativeTaskPreview": {"id": id_, "executionPermission": False},
        }
    options = [
        option("native", ["GetDetailsOfElements", "Get3DBoundingBoxes"]),
        option("official", ["GetDetailsOfElements", "API.Get3DBoundingBoxes"]),
    ]
    if duplicate:
        options[1] = option("equally-registered", ["GetDetailsOfElements", "GetSomeOtherBounds"])
    preview = {
        "schema": "APA_AUTO_NATIVE_TASK_V1",
        "status": "QUALIFIED_CATALOG_ALTERNATIVES_UNCALIBRATED",
        "nativeWritePermission": False,
        "automaticNativeExecution": False,
        "selectedNativeTaskPreview": None,
        "alternatives": options,
    }
    return Router(), preview


class RuntimeSelectionPolicy(unittest.TestCase):
    def test_read_only_native_registered_is_selected_over_client_only(self):
        router, preview = fixture()
        selected, reason = select_uniquely_registered_read_alternative(router, preview, [
            {"command": "GetDetailsOfElements", "status": "RUNTIME_AVAILABLE"},
            {"command": "Get3DBoundingBoxes", "status": "RUNTIME_AVAILABLE"},
            {"command": "API.Get3DBoundingBoxes", "status":
                "CLIENT_PRODUCT_MATCH_NOT_PER_METHOD_REGISTRATION"},
        ])
        self.assertEqual(reason, "AUTO_SELECTED_READ_ONLY_BY_RUNTIME_REGISTRATION")
        self.assertEqual(selected["selectedStrategyId"], "native")
        self.assertEqual(selected["calibrationStatus"], "UNCALIBRATED")
        self.assertFalse(selected["nativeWritePermission"])
        self.assertFalse(selected["automaticNativeExecution"])
        self.assertIn("NOT_COST_OPTIMAL", selected["selectionMethod"])

    def test_equal_registration_does_not_guess_fastest(self):
        router, preview = fixture(duplicate=True)
        output, reason = select_uniquely_registered_read_alternative(router, preview, [
            {"command": command, "status": "RUNTIME_AVAILABLE"}
            for command in ["GetDetailsOfElements", "Get3DBoundingBoxes", "GetSomeOtherBounds"]
        ])
        self.assertEqual(reason, "EQUAL_REGISTRATION_CONFIDENCE_KEEP_ALTERNATIVES")
        self.assertIsNone(output["selectedNativeTaskPreview"])

    def test_write_tasks_do_not_use_registration_tiebreak(self):
        router, preview = fixture(kind="CREATE")
        output, reason = select_uniquely_registered_read_alternative(router, preview, [
            {"command": command, "status": "RUNTIME_AVAILABLE"}
            for command in ["GetDetailsOfElements", "Get3DBoundingBoxes"]
        ])
        self.assertEqual(reason, "WRITE_OR_UNREVIEWED_EFFECT_NOT_AUTO_SELECTED")
        self.assertIsNone(output["selectedNativeTaskPreview"])

    def test_unprobed_provider_is_not_assumed_registered(self):
        router, preview = fixture()
        output, reason = select_uniquely_registered_read_alternative(router, preview, [
            {"command": "GetDetailsOfElements", "status": "RUNTIME_AVAILABLE"},
            {"command": "Get3DBoundingBoxes", "status": "RUNTIME_AVAILABLE"},
        ])
        self.assertEqual(
            reason, "INSUFFICIENT_TASK_SCOPED_NATIVE_REGISTRATION_EVIDENCE"
        )
        self.assertIsNone(output["selectedNativeTaskPreview"])

    def test_source_only_option_not_promoted(self):
        router, preview = fixture()
        preview["alternatives"][1]["executionBlockers"] = ["SOURCE_ONLY"]
        output, reason = select_uniquely_registered_read_alternative(router, preview, [
            {"command": "GetDetailsOfElements", "status": "RUNTIME_AVAILABLE"},
            {"command": "Get3DBoundingBoxes", "status": "RUNTIME_AVAILABLE"},
        ])
        self.assertEqual(reason, "NO_MULTIPLE_ELIGIBLE_OPTIONS")
        self.assertIsNone(output["selectedNativeTaskPreview"])


if __name__ == "__main__":
    unittest.main()
