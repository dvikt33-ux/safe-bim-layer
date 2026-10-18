"""APA stage-2 repeated opening mark selection, no model execution/writes."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import apa_ap2_massops_preflight as P

class TestAP2MassOps(unittest.TestCase):
    def fixture(self, root):
        import pymupdf
        pdf = root / "stage2.pdf"
        doc = pymupdf.open()
        page = doc.new_page(width=1190, height=842)
        # Two model marks, one unique. Legend outside selected floorplan clip.
        page.insert_text((200, 200), "OK-3", fontsize=9)
        page.insert_text((400, 280), "OK-3", fontsize=9)
        page.insert_text((500, 450), "D-1", fontsize=9)
        page.insert_text((920, 475), "OK-3", fontsize=9)
        doc.save(str(pdf))
        doc.close()
        sha = P.digest(pdf)
        result = root / "plan"
        result.mkdir()
        (result / "floorplan.png").write_bytes(b"mock-png")
        evidence = {
            "schema": "APA_PDF_LAYERED_FLOORPLAN_EVIDENCE_V1",
            "sourceSHA256": sha,
            "pdfPage": 16,
            "pdfPointsClip": [125., 95., 685., 595.],
            "nativeCalls": 0, "modelWrites": 0,
            "rasterSHA256": P.digest(result / "floorplan.png"),
            "rasterPixelSize": [1120, 1000],
        }
        (result / "evidence.json").write_text(
            json.dumps(evidence), encoding="utf-8")
        return pdf, result, sha

    def test_repeat_from_true_floorplan_crop_excludes_legend(self):
        with tempfile.TemporaryDirectory() as td:
            pdf, folder, sha = self.fixture(Path(td))
            report = P.inspect(pdf, folder / "evidence.json",
                               expected_source_hash=sha)
            self.assertEqual(report["markCounts"], {"Д-1": 1, "ОК-3": 2})
            self.assertEqual(report["markPlacementCount"], 3)
            self.assertEqual(report["repeatGroups"], 1)
            self.assertEqual(report["repeatPlacementCount"], 2)
            self.assertIsNone(report["candidateBatches"][1]
                              ["nativeOperationChosen"])
            self.assertFalse(report["readyForModelWrite"])
            self.assertEqual(report["nativeCalls"], 0)
            self.assertEqual(report["modelWrites"], 0)

    def test_wrong_model_report_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            pdf, folder, sha = self.fixture(Path(td))
            false = folder / "fake-openbim.json"
            false.write_text(json.dumps({
                "schema": "APA_SEMANTIC_SOURCE_EVIDENCE_V1",
                "action": "openbim",
                "nativeCalls": 0, "modelWrites": 0,
                "sourceNotModified": True,
                "sources": [{"sha256": "0"*64}],
                "result": {"classPixelCounts": {
                    "wall": 1, "window": 1, "door": 1, "background": 1}}
            }), encoding="utf-8")
            with self.assertRaisesRegex(ValueError,
                                        "NOT_FOR_THIS_RASTER"):
                P.inspect(pdf, folder / "evidence.json",
                          false, expected_source_hash=sha)

    def test_genuine_model_provenance_not_bim_acceptance(self):
        with tempfile.TemporaryDirectory() as td:
            pdf, folder, sha = self.fixture(Path(td))
            model = folder / "openbim.json"
            model.write_text(json.dumps({
                "schema": "APA_SEMANTIC_SOURCE_EVIDENCE_V1",
                "action": "openbim",
                "nativeCalls": 0, "modelWrites": 0,
                "sourceNotModified": True,
                "sources": [{"sha256": P.digest(folder / "floorplan.png")}],
                "result": {
                    "imageSizePx": [1024, 1024],
                    "classPixelCounts": {
                        "wall": 10, "window": 8, "door": 0,
                        "background": 1048558},
                },
            }), encoding="utf-8")
            report = P.inspect(pdf, folder / "evidence.json",
                               model, expected_source_hash=sha)
            self.assertTrue(report["semantic"]["evidenceAccepted"])
            self.assertFalse(report["semantic"]["maskAndRasterPixelsComparable"])
            self.assertFalse(report["readyForModelWrite"])
            self.assertEqual(report["copiedGroupsConfirmed"], 0)

    def test_document_sha_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            pdf, folder, sha = self.fixture(Path(td))
            with self.assertRaisesRegex(ValueError, "SOURCE_PDF_SHA_MISMATCH"):
                P.inspect(pdf, folder / "evidence.json",
                          expected_source_hash="f"*64)

if __name__ == "__main__":
    unittest.main()
