"""Source-only regression tests for APA semantic provider, no PLN or live AC."""
from __future__ import annotations
import json
from pathlib import Path
import sys
import tempfile
from unittest import TestCase, main, mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import apa_semantic_readonly as W
import apa_semantic_catalog as C
import configure_apa_semantic_models as M

class SemanticReadOnlyTests(TestCase):
    def test_pdf_groups_layers_and_one_page_raster_without_bim_guessing(self):
        import pymupdf
        with tempfile.TemporaryDirectory(prefix="apa-semantic-") as d:
            directory = Path(d)
            pdf = directory / "source.pdf"
            doc = pymupdf.open()
            p = doc.new_page(width=400, height=300)
            p.draw_line((10, 10), (60, 60))
            p.draw_rect(pymupdf.Rect(100, 20, 220, 70))
            doc.save(str(pdf))
            doc.close()
            before = W.digest(pdf)
            result = W.pdf_paths(pdf, 1)
            self.assertEqual(result["pageCount"], 1)
            self.assertGreaterEqual(result["pathCount"], 2)
            self.assertEqual(result["pathCount"], len(result["paths"]))
            self.assertFalse(result["clustersAreBIMElements"])
            self.assertFalse(result["truncated"])
            self.assertEqual(result["coordinateSystem"],
                             "PDF_POINTS_TOP_LEFT_NOT_BIM_METRES")
            dest = directory / "page.json"
            png = W.pdf_raster(pdf, 1, dest)
            self.assertTrue(Path(png["imageFile"]).is_file())
            self.assertTrue(png["imageSHA256"])
            self.assertEqual(png["imageSizePx"], [800, 600])
            self.assertEqual(png["pointsToPixels"], 2)
            self.assertEqual(W.digest(pdf), before)

    def test_no_overwrite_and_no_fake_units(self):
        import pymupdf
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            pdf = root / "a.pdf"
            doc = pymupdf.open()
            doc.new_page()
            doc.save(str(pdf))
            doc.close()
            with self.assertRaisesRegex(ValueError, "PDF_PAGE_NOT_FOUND"):
                W.pdf_paths(pdf, 2)
            report = root / "result.json"
            png = report.with_suffix(".png")
            png.write_bytes(b"occupied")
            with self.assertRaisesRegex(ValueError, "ALREADY_EXISTS"):
                W.pdf_raster(pdf, 1, report)
            self.assertEqual(png.read_bytes(), b"occupied")

    def test_api_plain_geometry_and_bad_type(self):
        class FakePoint:
            x = 9
            y = 10
        class Unrecognized:
            pass
        self.assertEqual(W.plain(FakePoint()), [9., 10.])
        with self.assertRaisesRegex(TypeError, "UNSUPPORTED_PYMUPDF"):
            W.plain(Unrecognized())

    def test_vendor_weight_sha_config_required(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            exe = root / "python.exe"
            exe.write_bytes(b"python")
            model = root / "weights.pt"
            model.write_bytes(b"weights")
            cfg = root / "models.json"
            cfg.write_text(json.dumps({
                "schema": "APA_SEMANTIC_ML_VENDOR_CONFIG_V1",
                "openbim": {
                    "python": str(exe), "root": str(root),
                    "model": str(model), "modelSHA256": W.digest(model)
                }
            }), encoding="utf-8")
            self.assertEqual(W.read_verified_ml_model(cfg, "openbim")[2], model.resolve())
            model.write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "MODEL_HASH_MISMATCH"):
                W.read_verified_ml_model(cfg, "openbim")

    def test_new_four_only_registered_to_original_router(self):
        class DummyRouter:
            def __init__(self):
                self.registered = {}
                self.policies = []
            def add_local_provider(self, namespace, contracts, handlers, source, deps):
                self.registered.update(contracts)
                self.handlers = handlers
            def contract_hash(self, key):
                return key
            def review_policy(self, *args):
                self.policies.append(args)
        router = DummyRouter()
        with mock.patch.object(C, "installed", return_value=("python", "script")):
            result = C.register(router)
        self.assertEqual(len(result["registered"]), 4)
        self.assertEqual(len(router.registered), 4)
        self.assertEqual(len(router.policies), 4)
        self.assertEqual(router.registered["PDFPaths"]["parameters"]
                         ["properties"]["page"]["type"], "integer")
        self.assertTrue(all(p[1:3] == ("READ_ONLY", "READ_ONLY")
                            for p in router.policies))


    def test_ml_config_append_requires_explicit_owner_trust_and_sha(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            side = root / "semantic"
            side.mkdir()
            (side / "installation.json").write_text("{}", encoding="utf-8")
            exe = root / "python.exe"
            exe.write_bytes(b"python")
            vendor = root / "vendor"
            vendor.mkdir()
            (vendor / "inference_api.py").write_text("# vendor", encoding="utf-8")
            weights = vendor / "weights.pt"
            weights.write_bytes(b"weights")
            with mock.patch.object(M, "SIDE", side), (
                 mock.patch.object(M, "TARGET", side / "models.json")):
                with self.assertRaisesRegex(ValueError, "EXPLICIT_TRUST"):
                    M.configure("openbim", exe, vendor, weights, False)
                self.assertFalse((side / "models.json").exists())
                report = M.configure("openbim", exe, vendor, weights, True)
                self.assertEqual(report["configured"], ["openbim"])
                with self.assertRaisesRegex(ValueError, "ALREADY_EXISTS"):
                    M.configure("openbim", exe, vendor, weights, True)


    def test_real_dynamiccommands_register_prepare_read(self):
        from archicad_dynamic_commands import DynamicCommands
        router = DynamicCommands({"commands": {}, "common_schemas": {}})
        with mock.patch.object(C, "installed", return_value=("python", "script")):
            receipt = C.register(router)
        self.assertEqual(len(receipt["registered"]), 4)
        key = "AddOn.APASemantic.PDFPaths"
        params = {"a": "C:/fixture.pdf", "page": 1,
                  "output": "C:/new-semantic-report.json"}
        ticket = router.prepare(key, params)
        self.assertEqual(ticket["effect"], "READ_ONLY")
        self.assertFalse(ticket["nativeWritePermission"])
        fake = {
            "schema": "APA_SEMANTIC_SOURCE_EVIDENCE_V1",
            "action": "pdf-paths",
            "status": "SOURCE_ONLY_NOT_BIM_ACCEPTANCE",
            "result": {"pathCount": 1},
            "sources": [],
            "nativeCalls": 0, "modelWrites": 0,
            "sourceNotModified": True,
        }
        with mock.patch.object(C, "run", return_value=fake) as vendor:
            actual = router.read(None, ticket, reviewed_read_only=True)
        self.assertEqual(actual, fake)
        vendor.assert_called_once_with("pdf-paths", params)
        with self.assertRaises(ValueError):
            router.read(None, ticket, reviewed_read_only=False)


    def test_real_dynamic_router_vendor_subprocess_pdf_paths(self):
        import pymupdf
        from archicad_dynamic_commands import DynamicCommands
        with tempfile.TemporaryDirectory(prefix="apa-router-semantic-") as d:
            base = Path(d)
            pdf = base / "source.pdf"
            doc = pymupdf.open()
            page = doc.new_page(width=300, height=200)
            page.draw_rect(pymupdf.Rect(10, 10, 100, 50))
            doc.save(str(pdf))
            doc.close()
            out = base / "new-report.json"
            original_sha = W.digest(pdf)
            router = DynamicCommands({"commands": {}, "common_schemas": {}})
            with mock.patch.object(C, "installed",
                                   return_value=(Path(sys.executable),
                                                 Path(W.__file__).resolve())):
                C.register(router)
                ticket = router.prepare("AddOn.APASemantic.PDFPaths",
                                        {"a": str(pdf), "page": 1,
                                         "output": str(out)})
                result = router.read(None, ticket, reviewed_read_only=True)
            self.assertEqual(result["schema"],
                             "APA_SEMANTIC_SOURCE_EVIDENCE_V1")
            self.assertEqual(result["result"]["page"], 1)
            self.assertGreaterEqual(result["result"]["pathCount"], 1)
            self.assertFalse(result["result"]["clustersAreBIMElements"])
            self.assertEqual(result["modelWrites"], 0)
            self.assertEqual(result["nativeCalls"], 0)
            self.assertTrue(out.is_file())
            self.assertEqual(W.digest(pdf), original_sha)

if __name__ == "__main__":
    main()
