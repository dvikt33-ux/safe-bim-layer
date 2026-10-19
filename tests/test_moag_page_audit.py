"""Verify no false claim of full-book coverage or visual-derived geometry."""
from pathlib import Path
import importlib.util
import unittest

ROOT=Path(__file__).resolve().parents[1]
MODULE=ROOT/"tools/moag_topology/page_audit.py"
SPEC=importlib.util.spec_from_file_location("moag_page_audit",MODULE)
m=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)
def deep(x):
    import copy
    return copy.deepcopy(x)

class TestPageAudit(unittest.TestCase):
    def test_expected_412_pages_and_twenty_five_read(self):
        d=m.check()
        self.assertEqual(d["total_indexed_pages"],412)
        self.assertEqual(d["coverage"]["REVIEWED_FULL_PAGE"],25)
        self.assertEqual(d["coverage"]["NOT_REVIEWED"],387)
        self.assertEqual(d["observations"],110)
        self.assertFalse(d["full_corpus_claim"])
        self.assertFalse(d["geometry_authorized"])

    def test_other_station_excluded(self):
        data=m.load(m.ROOT/"page_observations.json")
        d=[x for x in data["observations"] if x["page_id"]=="B4-001"]
        self.assertTrue(d)
        self.assertTrue(all(x["station_id"]=="THIRD_STATION_NOT_MOAG" and x["evidence_class"]=="EXCLUSION_EVIDENCE" for x in d))

    def test_hypotheses_cannot_be_geometry(self):
        v=m.load(m.ROOT/"visual_hypotheses.json")
        self.assertTrue(v["hypotheses"])
        self.assertTrue(all(x["adopt_as_geometry"] is False for x in v["hypotheses"]))

    def test_middle_level_has_no_claim_of_full_extra_floor(self):
        v=m.load(m.ROOT/"visual_hypotheses.json")
        h=next(x for x in v["hypotheses"] if x["id"]=="VH-004")
        self.assertEqual(h["status"],"INSUFFICIENT_EVIDENCE")

if __name__=="__main__":
    unittest.main()
