"""Dependency-free CI guards; real vendors tested separately by B1 suite."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import apa_ifc_reports_b1 as B
import apa_external_catalog as V1
from archicad_dynamic_commands import DynamicCommands


class Contracts(unittest.TestCase):
    def test_preserves_all_eighteen_contracts(self):
        router = DynamicCommands({"common_schemas": {}, "commands": {}})
        with mock.patch.object(V1, "verified_environment", return_value=(Path(sys.executable), Path(V1.__file__))):
            V1.register(router)
        with mock.patch.object(B.V2, "verified_python", return_value=Path(sys.executable)):
            B.V2.register(router)
            before = copy.deepcopy(router.catalog["commands"])
            self.assertEqual(len(before), 18)
            B.register(router)
        self.assertEqual(len(router.catalog["commands"]), 21)
        for key, value in before.items():
            self.assertEqual(value, router.catalog["commands"][key])

    def test_unknown_action(self):
        with self.assertRaisesRegex(ValueError, "UNKNOWN_ACTION"):
            B.inputs("unknown", {})

    def test_missing_parameters(self):
        with self.assertRaisesRegex(ValueError, "INVALID_PARAMETERS"):
            B.inputs("select", {})

    def test_unpinned_vendor_rejected(self):
        with mock.patch.object(B.importlib.metadata, "version", return_value="9"):
            with self.assertRaisesRegex(ValueError, "VERSION_DRIFT"):
                B.versions("validate")

    def test_forged_source_receipt_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source.ifc"
            source.write_text("fixture")
            out = root / "output"
            def fake_run(*args, **kwargs):
                out.mkdir()
                (out / "report.json").write_text(json.dumps({"schema": B.SCHEMA}))
                return mock.Mock(returncode=0, stderr="")
            with mock.patch.object(B.V2, "verified_python", return_value=Path(sys.executable)):
                with mock.patch.object(B.subprocess, "run", side_effect=fake_run):
                    with self.assertRaisesRegex(ValueError, "EVIDENCE_MISMATCH"):
                        B.call("validate", {"a": str(source), "output": str(out)})

    def test_json_is_not_ods(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "fake.ods"
            path.write_text("{}")
            with self.assertRaises(B.zipfile.BadZipFile):
                B.ods_readback(path)


if __name__ == "__main__":
    unittest.main()
