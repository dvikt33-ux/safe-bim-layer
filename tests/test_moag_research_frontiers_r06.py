"""R06 review queue must preserve unresolved isolation rather than fabricate doors."""
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/moag_topology"))
import research_frontiers_r06 as research


class UnresolvedSpatialResearch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = research.assemble_review()

    def test_source_linked_fixed_object_queue_and_narrative_gaps(self):
        r = self.r
        self.assertEqual(r["fixed_infrastructure_isolation_count"], 12)
        self.assertEqual(r["total_route_gaps"], 18)
        self.assertEqual(len(r["isolated_fixed_infrastructure"]), 12)
        self.assertEqual(len(r["narrative_route_gaps"]), 18)
        self.assertTrue(all(not x["no_automatic_link"]
                            for x in r["isolated_fixed_infrastructure"]))
        self.assertTrue(all(not x["link_automatically"]
                            for x in r["narrative_route_gaps"]))
        self.assertFalse(r["archicad_write"])

    def test_source_ids_are_traceable_to_reviewed_book_pages(self):
        r = self.r
        self.assertTrue(all(x["all_cited_pages_in_ledger"]
                            for x in r["isolated_fixed_infrastructure"]))
        self.assertTrue(all(x["all_boundary_pages_reviewed"]
                            for x in r["narrative_route_gaps"]))
        self.assertTrue(all(p["url"].startswith("https://loveread.ec/")
                            for x in r["isolated_fixed_infrastructure"]
                            for p in x["sources"]))
        self.assertEqual(len({x["index_id"] for x in r["isolated_fixed_infrastructure"]}), 12)

    def test_unproven_relationship_remains_nonconnecting(self):
        r = self.r
        for x in r["isolated_fixed_infrastructure"]:
            self.assertTrue(x["no_geometric_extent_proven"])
            for edge in x["unaccepted_neighbor_hypotheses"]:
                self.assertTrue(edge["not_an_approved_spatial_connection"])
        self.assertEqual(r["still_unverified_station_candidates"], 3)


if __name__ == "__main__":
    unittest.main()
