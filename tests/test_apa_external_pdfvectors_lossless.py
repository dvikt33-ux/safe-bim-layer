"""Focused lossless PDFVectors regressions, vendor-backed and high-density mock.

These tests do not contact Archicad, touch a PLN or register any writer.
"""
from __future__ import annotations

from pathlib import Path
import tempfile
import sys
import unittest
from unittest import mock
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import apa_external_readonly as A
import apa_external_router_activation as R


class PDFLosslessTests(unittest.TestCase):
    def test_cyrillic_recovery_preserves_original(self):
        raw = "Ñõåìà ñòðîïèëüíîé ñèñòåìû"
        text, status = A._pdf_recover_cyrillic(raw)
        self.assertEqual(text, "Схема стропильной системы")
        self.assertEqual(status, "LATIN1_CP1251_REVERSIBLE_RECOVERY")
        self.assertEqual(A._pdf_recover_cyrillic("GSPublisherVersion 0.24")[0],
                         "GSPublisherVersion 0.24")

    def test_cubic_bezier_keeps_three_control_and_endpoint_points(self):
        path = [
            ("m", (10., 20.)),
            ("c", (20., 30.), (40., 45.), (50., 60.)),
            ("h",),
        ]
        ops = A._pdf_path_ops(path, 100.)
        self.assertEqual(ops, [
            {"op": "m", "pointsPt": [[10., 20.]]},
            {"op": "c", "pointsPt": [[20., 30.], [40., 45.], [50., 60.]]},
            {"op": "h", "pointsPt": []},
        ])
        with self.assertRaisesRegex(ValueError, "UNSUPPORTED_PDF_VECTOR"):
            A._pdf_path_ops([("n",)], 100.)

    def test_vendor_real_tiny_vector_pdf(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "fixture.pdf"
            R.make_pdf(p)
            result, sources = A.pdf_vectors(SimpleNamespace(a=str(p)))
            self.assertEqual(sources, [p.resolve()])
            self.assertTrue(result["vectorGeometryComplete"])
            self.assertFalse(result["truncated"])
            self.assertGreaterEqual(result["totals"]["lines"], 1)
            self.assertEqual(result["pages"][0]["lineCount"],
                             len(result["pages"][0]["lines"]))

    def test_more_than_20000_realized_without_slice(self):
        line = {
            "x0": 0., "x1": 1., "top": 10., "bottom": 10.,
            "pts": ((0., 10.), (1., 10.)),
            "path": [("m", (0., 10.)), ("l", (1., 10.))],
            "linewidth": .1, "stroke": True,
            "fill": False, "evenodd": False,
        }
        curve = {
            "x0": 1., "x1": 5., "top": 20., "bottom": 40.,
            "pts": ((1., 20.), (5., 40.)),
            "path": [("m", (1., 80.)),
                     ("c", (2., 70.), (3., 60.), (5., 60.))],
            "linewidth": .1, "stroke": True,
            "fill": False, "evenodd": False,
        }
        page = SimpleNamespace(
            width=200., height=100.,
            lines=[line] * 20001, curves=[curve] * 201,
            rects=[], images=[],
            extract_text=lambda: "Ñõåìà ñòðîïèëüíîé ñèñòåìû")
        fake_pdf = SimpleNamespace(pages=[page])
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "valid.pdf"
            source.write_bytes(b"%PDF-minimal-content-not-parsed-due-to-mock")
            with mock.patch("pdfplumber.open") as opening:
                opening.return_value.__enter__.return_value = fake_pdf
                result, _ = A.pdf_vectors(SimpleNamespace(a=str(source)))
        self.assertEqual(len(result["pages"][0]["lines"]), 20001)
        self.assertEqual(len(result["pages"][0]["curves"]), 201)
        self.assertEqual(result["pages"][0]["curveCountNotExtracted"], 0)
        self.assertEqual(result["totals"]["lines"], 20001)
        self.assertFalse(result["pages"][0]["truncated"])
        self.assertEqual(result["pages"][0]["text"],
                         "Схема стропильной системы")
        self.assertEqual(result["pages"][0]["curves"][0]["path"][1]["op"], "c")
        self.assertEqual(result["pages"][0]["lines"][0]["startPt"],
                         result["pages"][0]["lines"][0]["path"][0]["pointsPt"][0])


if __name__ == "__main__":
    unittest.main()
