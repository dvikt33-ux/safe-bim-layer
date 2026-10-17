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
            self.assertEqual(W.read_verified_ml_model(cfg, "openbim")[2], model)
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

if __name__ == "__main__":
    main()
