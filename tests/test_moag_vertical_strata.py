"""Contract tests for local multi-level lower block; no invented floor coordinates."""
import json
from pathlib import Path
import unittest

BASE=Path(__file__).resolve().parents[1]/"docs/research/apa-results/moag/v1"

class LowerStrataTests(unittest.TestCase):
    def test_every_height_claim_has_source_and_known_nodes(self):
        graph=json.loads((BASE/"evidence_graph.json").read_text(encoding="utf-8"))
        d=json.loads((BASE/"vertical_strata.json").read_text(encoding="utf-8"))
        nodes={x["id"] for x in graph["nodes"]}
        sources={x["id"] for x in graph["sources"]}
        self.assertFalse(d["geometry_write_authorized"])
        self.assertIsNone(d["global_level_hierarchy"]["absolute_datum_m"])
        self.assertEqual(d["global_level_hierarchy"]["known_global_levels"],[1,2,3])
        self.assertTrue(d["global_level_hierarchy"]["nested_local_strata_not_extra_global_levels"])
        for x in d["inequalities"]:
            self.assertIn(x["higher"],nodes)
            self.assertIn(x["lower"],nodes)
            self.assertTrue(set(x["source_ids"]) <= sources)
            self.assertIsNone(x["numeric_delta_m"])
            self.assertTrue(x["proof"])
        for x in d["zones"]:
            self.assertTrue(set(x["node_refs"]) <= nodes)
            self.assertIsNone(x["deck_index"])
            self.assertIsNone(x["claimed_footprint_rank"])
        self.assertIsNone(next(z for z in d["zones"] if z["id"]=="S-L1-2")["global_level"])

if __name__=="__main__":
    unittest.main()
