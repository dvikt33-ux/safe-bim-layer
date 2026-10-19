"""Character route audit: no invented floor/metric and no unverified identity merges."""
from pathlib import Path
import importlib.util
import json
import unittest

ROOT=Path(__file__).resolve().parents[1]
M=ROOT/"tools/moag_topology/routes_audit.py"
S=importlib.util.spec_from_file_location("moag_routes_audit",M)
module=importlib.util.module_from_spec(S)
S.loader.exec_module(module)

class RoutesTests(unittest.TestCase):
    def test_all_routes_refer_to_fully_reviewed_pages(self):
        out=module.check()
        self.assertGreaterEqual(out["routes"],5)
        self.assertGreaterEqual(out["anchors"],30)
        self.assertGreaterEqual(out["vertical_movements"],8)
        self.assertFalse(out["geometry_approved"])
        self.assertFalse(out["write_authorized"])

    def test_no_automatic_identification_of_sealed_rooms(self):
        d=module.load(module.BASE/"v2/character_routes.json")
        r=next(x for x in d["routes"] if x["id"]=="RT-001")
        for h in r["identity_hypotheses"]:
            self.assertTrue(h["status"].startswith("UNVERIFIED"))

    def test_observed_return_is_ascent_from_below_basement(self):
        d=module.load(module.BASE/"v2/character_routes.json")
        r=next(x for x in d["routes"] if x["id"]=="RT-001")
        steps=[x["movement_method"] for x in r["nodes"]]
        self.assertLess(steps.index("DROP_DOWN"),steps.index("CLIMB_UP"))
        self.assertLess(steps.index("CLIMB_UP"),steps.index("TURN_AND_CRAWL"))

    def test_routes_do_not_guess_unnamed_stories(self):
        d=module.load(module.BASE/"v2/character_routes.json")
        self.assertTrue(all(s["global_level"] in (None,1,2,3) for r in d["routes"] for s in r["nodes"]))
        self.assertTrue(all(s["absolute_z_m"] is None for r in d["routes"] for s in r["nodes"]))

if __name__=="__main__":
    unittest.main()
