"""Focused safety checks for newly added APA external read-only bridge."""
import contextlib
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import apa_external_readonly as A


class ExternalReadonlyTests(unittest.TestCase):
    def test_source_extension_enforced_before_vendor_call(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "unexpected.txt"
            p.write_text("not an IFC")
            with self.assertRaisesRegex(ValueError, "SOURCE_TYPE_MISMATCH"):
                A.source(p, "ifc")

    def test_ifc_diff_uses_registered_upstream_module_and_semantic_relations(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            left, right = p / "before.ifc", p / "after.ifc"
            left.write_text("old"); right.write_text("new")
            with mock.patch.object(A, "invoke_module", return_value={"ok": True}) as invoke:
                result, paths = A.ifc_diff(type("Args", (), {
                    "a": str(left), "b": str(right), "output": str(p / "result.json")
                })())
            self.assertEqual(result, {"ok": True})
            self.assertEqual(paths, [left, right])
            self.assertEqual(invoke.call_args.args[0], "ifcdiff")
            self.assertEqual(invoke.call_args.args[1][2], "-r")

    def test_clash_set_is_source_pinned_and_has_no_shell_dispatch(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "model.ifc"
            path.write_text("IFC")
            def inspect(module, arguments, output):
                self.assertEqual(module, "ifcclash")
                import json
                cfg = json.loads(Path(arguments[0]).read_text())
                self.assertEqual(cfg[0]["a"][0]["file"], str(path))
                self.assertNotIn("b", cfg[0])
                return {"ok": True}
            with mock.patch.object(A, "invoke_module", side_effect=inspect):
                report, files = A.ifc_clash(type("Args", (), {
                    "a": str(path), "b": None, "output": str(path.parent / "out.json")
                })())
            self.assertEqual(files, [path])
            self.assertEqual(report["ok"], True)

    def test_output_already_exists_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            inp = p / "source.pdf"; inp.write_text("%PDF-1.4")
            out = p / "existing.json"; out.write_text("KEEP")
            with mock.patch.object(A, "check_environment", return_value={"status": "READY"}):
                with mock.patch.dict(A.OPERATIONS, {"pdf-vectors": lambda args:
                        ({"mock": True}, [inp])}):
                    with self.assertRaisesRegex(ValueError, "OUTPUT_ALREADY_EXISTS"):
                        A.main(["pdf-vectors", "--a", str(inp), "--output", str(out)])
            self.assertEqual(out.read_text(), "KEEP")

    def test_explicit_output_is_provenance_tagged(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            inp = p / "source.dxf"; inp.write_text("DXF")
            out = p / "new.json"
            with mock.patch.object(A, "check_environment", return_value={"status": "READY"}):
                with mock.patch.dict(A.OPERATIONS, {"dxf-vectors": lambda args:
                        ({"facts": []}, [inp])}):
                    with contextlib.redirect_stdout(io.StringIO()):
                        self.assertEqual(A.main(["dxf-vectors", "--a", str(inp),
                                                 "--output", str(out)]), 0)
            import json
            proof = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(proof["nativeCalls"], 0)
            self.assertEqual(proof["modelWrites"], 0)
            self.assertEqual(proof["sources"][0]["sha256"], A.sha256(inp))
            self.assertEqual(proof["action"], "dxf-vectors")


if __name__ == "__main__":
    unittest.main()
