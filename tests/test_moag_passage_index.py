"""Traceability tests for MOAG exact scene/dialogue locator index."""
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs/research/apa-results/moag/v1"

class PassageIndexTests(unittest.TestCase):
    def setUp(self):
        self.graph=json.loads((BASE/"evidence_graph.json").read_text(encoding="utf-8"))
        self.index=json.loads((BASE/"passage_index.json").read_text(encoding="utf-8"))

    def test_claims_resolve_all_identifiers(self):
        self.assertEqual(self.index["schema"],"APA-MOAG-PASSAGE-INDEX/0.1")
        sources={s["id"] for s in self.graph["sources"]}
        nodes={n["id"] for n in self.graph["nodes"]}
        edges={e["id"] for e in self.graph["edges"]}
        ids=set()
        for p in self.index["passages"]:
            self.assertNotIn(p["id"],ids)
            ids.add(p["id"])
            self.assertIn(p["source_id"],sources)
            self.assertTrue(p["locator_hint"])
            self.assertTrue(p["paraphrase"])
            self.assertFalse(p["absolute_coordinates"])
            self.assertTrue(set(p["node_refs"]) <= nodes)
            self.assertTrue(set(p["edge_refs"]) <= edges)
        self.assertGreaterEqual(len(ids),15)

    def test_locator_not_artificial_metric(self):
        for p in self.index["passages"]:
            self.assertNotIn("x_m",p)
            self.assertNotIn("y_m",p)
            self.assertNotIn("scale",p)


    def test_published_snapshot_matches_exact_source_blob(self):
        content=(BASE/"evidence_graph.json").read_bytes()
        canonical_sha=hashlib.sha1(b"blob "+str(len(content)).encode("ascii")+bytes([0])+content).hexdigest()
        snapshot=json.loads((BASE/"topology_snapshot.json").read_text(encoding="utf-8"))
        self.assertEqual(snapshot["source_blob_sha"],canonical_sha)
        self.assertEqual({x["id"] for x in snapshot["space_refs"]},
                         {x["id"] for x in self.graph["nodes"]})
        self.assertEqual({x["id"] for x in snapshot["relationships"]},
                         {x["id"] for x in self.graph["edges"]})
        self.assertFalse(snapshot["gates"]["apa_native_execute"])

if __name__=="__main__":
    unittest.main()
