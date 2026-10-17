"""Source-only layer-aware raster benchmark test using a real PyMuPDF PDF."""
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import apa_arch_plan_benchmark as B

class TestLayeredPlan(unittest.TestCase):
    def test_creates_cropped_png_and_stable_source_evidence(self):
        import pymupdf
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            pdf=root/"original.pdf"
            doc=pymupdf.open()
            page=doc.new_page(width=300,height=200)
            page.draw_rect(pymupdf.Rect(15,30,140,170))
            doc.save(str(pdf))
            doc.close()
            before=B.sha256(pdf)
            out=root/"outputs"
            report=B.extract(pdf,1,(10,20,180,180),out,144)
            self.assertEqual(report["schema"],"APA_PDF_LAYERED_FLOORPLAN_EVIDENCE_V1")
            self.assertEqual(report["sourceSHA256"],before)
            self.assertEqual(B.sha256(pdf),before)
            self.assertEqual(report["rasterPixelSize"],[340,320])
            self.assertEqual(report["modelWrites"],0)
            self.assertEqual(report["nativeCalls"],0)
            self.assertFalse(report["rasterLayerFilterApplied"])
            self.assertTrue(report["pathCountsAreNotBIMElementCounts"])
            self.assertTrue((out/"evidence.json").is_file())
            self.assertTrue((out/"floorplan.png").is_file())
            with self.assertRaisesRegex(ValueError,"RESULT_FOLDER_ALREADY_EXISTS"):
                B.extract(pdf,1,(10,20,180,180),out,144)

    def test_fails_on_invalid_page_and_clip_without_output(self):
        import pymupdf
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            pdf=root/"source.pdf"
            doc=pymupdf.open()
            doc.new_page()
            doc.save(str(pdf))
            doc.close()
            dest=root/"do_not_create"
            with self.assertRaisesRegex(ValueError,"CLIP_OUTSIDE_PDF_PAGE"):
                B.extract(pdf,1,(0,0,4000,4000),dest)
            self.assertFalse(dest.exists())
            with self.assertRaisesRegex(ValueError,"PAGE_NOT_FOUND"):
                B.extract(pdf,3,(0,0,100,100),dest)
            self.assertFalse(dest.exists())

    def test_classification_does_not_invent_bim(self):
        self.assertEqual(B.classify_layer("Конструктив - Стены Несущие"),
                         "wall_or_partition_graphics")
        self.assertEqual(B.classify_layer("$_12 - Перегородки"),
                         "wall_or_partition_graphics")
        self.assertEqual(B.classify_layer("Интерьер - Мебель"),
                         "furniture_graphics")
        self.assertEqual(B.classify_layer("Элемент Модели - Зона"),
                         "zone_graphics")

if __name__=="__main__":
    unittest.main()
