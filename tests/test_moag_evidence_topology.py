"""Offline safety gates for MOAG evidence graph. No Archicad access required."""
from __future__ import annotations
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE_FILE = ROOT / "tools/moag_topology/validate.py"
SPEC = importlib.util.spec_from_file_location("moag_topology_validate", MODULE_FILE)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
SOURCE = ROOT / "docs/research/apa-results/moag/v1/evidence_graph.json"

class MOAGTopologyTests(unittest.TestCase):
    def setUp(self):
        self.g = json.loads(SOURCE.read_text(encoding="utf-8"))

    def test_source_linked_seed_passes(self):
        result=MODULE.validate(self.g)
        self.assertTrue(result["validated"])
        self.assertGreaterEqual(result["nodes"],40)
        self.assertGreaterEqual(result["edges"],40)
        self.assertFalse(result["geometry_ready"])

    def test_no_executable_writes_in_export(self):
        export=MODULE.export_topology(self.g)
        self.assertFalse(export["gates"]["apa_native_execute"])
        self.assertFalse(export["gates"]["scene_writer_write"])
        self.assertEqual(export["status"],"GRAPH_ONLY_NO_COORDINATES")
        self.assertNotIn("operations",export)
        self.assertEqual(export["construction_dag"][2]["depends_on"],["P1_topology"])

    def test_reject_unknown_source(self):
        self.g["edges"][0]["source_ids"]=["fabricated"]
        with self.assertRaisesRegex(MODULE.ModelError,"missing source"):
            MODULE.validate(self.g)

    def test_reject_unapproved_coordinates(self):
        self.g["nodes"][0]["position"]["x"]=100
        with self.assertRaisesRegex(MODULE.ModelError,"unapproved spatial"):
            MODULE.validate(self.g)

    def test_reject_dangling_edge(self):
        self.g["edges"][0]["to"]="not-a-room"
        with self.assertRaisesRegex(MODULE.ModelError,"dangling"):
            MODULE.validate(self.g)

    def test_reject_containment_cycles(self):
        self.g["edges"].append({"id":"CYCLE-TEST","from":"L1-INNER","to":"L1",
          "type":"contains","source_ids":["B1-06"],"state":"TEXT_DIRECT",
          "claim":"synthetic invalid cycle","metric":None})
        with self.assertRaisesRegex(MODULE.ModelError,"containment cycle"):
            MODULE.validate(self.g)

    def test_reject_false_exhaustiveness(self):
        self.g["corpus"]["books_exhaustively_checked"]=4
        with self.assertRaisesRegex(MODULE.ModelError,"exhaustive"):
            MODULE.validate(self.g)

    def test_semantic_gates_must_be_explicit(self):
        self.g["nodes"][0]["state"]="RECHECK_REQUIRED"
        self.g["nodes"][0]["geometry_gate"]="APPROVED"
        with self.assertRaisesRegex(MODULE.ModelError,"unverified"):
            MODULE.validate(self.g)

if __name__=="__main__":
    unittest.main()
