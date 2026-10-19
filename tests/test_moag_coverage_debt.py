"""Regression coverage: mark read != proof of page-to-evidence extraction."""
import importlib.util
from pathlib import Path
import unittest

MODULE = Path(__file__).resolve().parents[1] / "tools/moag_topology/coverage_debt.py"
spec = importlib.util.spec_from_file_location("moag_coverage_debt", MODULE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class EvidenceCoverageTests(unittest.TestCase):
    def test_production_data_reports_honestly_without_geometry(self):
        report = mod.check()
        self.assertEqual(report["indexed_pages"], 412)
        self.assertLess(report["reviewed_pages"], 412)
        self.assertFalse(report["textual_corpus_complete"])
        self.assertFalse(report["metric_geometry_approved"])
        self.assertFalse(report["archicad_native_write_authorized"])

    def test_detects_read_page_with_unindexed_hints(self):
        pages = [
            {"id": "B1-001", "status": "REVIEWED_FULL_PAGE", "recorded_spatial_hints": 3},
            {"id": "B1-002", "status": "REVIEWED_FULL_PAGE", "recorded_spatial_hints": 0},
            {"id": "B1-003", "status": "NOT_REVIEWED", "recorded_spatial_hints": None},
        ]
        out = mod.evaluate(pages, [])
        self.assertEqual(out["read_pages_with_positive_hints_but_no_observations"], ["B1-001"])
        self.assertEqual(out["valid_zero_hint_read_pages_without_observations"], ["B1-002"])
        self.assertFalse(out["page_to_evidence_gap_free"])

    def test_observation_closes_gap(self):
        p = [{"id": "B1-061", "status": "REVIEWED_FULL_PAGE", "recorded_spatial_hints": 8}]
        ob = [{"id": "P-1000", "page_id": "B1-061"}]
        result = mod.evaluate(p, ob)
        self.assertTrue(result["page_to_evidence_gap_free"])
        self.assertTrue(result["textual_corpus_complete"])

    def test_unread_page_cannot_contain_evidence(self):
        p = [{"id": "B1-077", "status": "NOT_REVIEWED", "recorded_spatial_hints": None}]
        with self.assertRaises(ValueError):
            mod.evaluate(p, [{"id": "P-001", "page_id": "B1-077"}])


if __name__ == "__main__":
    unittest.main()
