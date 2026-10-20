"""Objective MOAG R06 readiness counters must not claim plan/BIM completion."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/moag_topology"))
import audit_readiness_r06 as report


class ReadinessAuditR06(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.value = report.audit()

    def test_corpus_statuses_count_actual_manifest_not_previous_summary(self):
        r = self.value["source_reading"]
        self.assertEqual(r["total_corpus_pages"], 412)
        self.assertEqual(r["first_pass_fully_reviewed_pages"],
                         sum(r["by_book"].values()))
        self.assertGreater(r["first_pass_fully_reviewed_pages"], 200)
        self.assertLess(r["first_pass_fully_reviewed_pages"], 412)
        self.assertEqual(r["indexed_spatial_observations"], 690)
        self.assertFalse(r["independent_textological_audit_completed"])

    def test_no_confusion_of_graph_and_access_completeness(self):
        r = self.value
        self.assertEqual(r["graph_structure"]["indexed_physical_and_conceptual_candidates"], 197)
        self.assertGreater(r["graph_structure"]["direct_access_components"],
                           r["graph_structure"]["qualitative_components"])
        self.assertGreater(r["graph_structure"]["fully_isolated_indices"], 0)
        self.assertGreater(r["graph_structure"]["semantic_review_links_excluded_from_connectivity"], 0)
        self.assertEqual(r["routes"]["recorded_steps"], 378)
        self.assertLessEqual(r["routes"]["steps_with_accepted_source_index_link"],
                             r["routes"]["steps_with_existing_index_reference"])

    def test_project_metric_intervals_cannot_be_reported_as_book_measurements(self):
        r = self.value
        self.assertEqual(r["area_volume"]["applicable_project_interval_profiles"], 157)
        self.assertEqual(r["area_volume"]["non_area_indices"], 40)
        self.assertEqual(r["area_volume"]["book_metric_footprint_profiles"], 0)
        self.assertGreaterEqual(
            r["area_volume"]["local_upper_floor_double_count_review_cases"], 5)
        self.assertEqual(r["levels_and_geometry"]["physically_confirmed_xy_index_count"], 0)
        self.assertFalse(r["gates"]["BIM_release_ready"])
        self.assertFalse(r["gates"]["readiness_percentage_can_be_interpreted_as_project_completion"])


if __name__ == "__main__":
    unittest.main()
