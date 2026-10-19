"""MOAG R06: verify physical-access graph and area/volume evidence views."""
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/moag_topology"))
BASE = ROOT / "docs/research/apa-results/moag"
spec = importlib.util.spec_from_file_location(
    "moag_structural_views", ROOT / "tools/moag_topology/inspect_graph_structure_r06.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
import assemble_evidence_graph_r06 as build


class MOAGStructuralProjections(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        read = lambda relative: json.loads((BASE / relative).read_text(encoding="utf-8"))
        cls.g = read("synthesis/full_indexed_parametric_graph_r04.json")
        cls.f = read("synthesis/progressive_fragments_r05.json")
        cls.a = read("synthesis/area_volume_bounds_r05.json")
        cls.r = read("v2/character_routes.json")
        cls.graph = build.assemble(cls.g, cls.f, cls.r, cls.a)
        cls.structure = module.project(cls.g, cls.f, cls.a, cls.graph)

    def test_evidence_views_preserve_full_inventory(self):
        s = self.structure
        self.assertEqual(s["physical_index_count"], 197)
        self.assertEqual(len(s["spatial_area_volume_profiles"]), 197)
        self.assertFalse(s["gates"]["geometry_approved"])
        self.assertFalse(s["gates"]["walking_route_proven_for_entire_station"])
        self.assertGreater(s["direct_access_graph"]["component_count"],
                           self.graph["counts"]["after_routes_physical_components"])
        self.assertTrue(all(not e["metric_geometry_proven"]
                            for e in s["evidence_relations"]))

    def test_direct_passage_is_not_reduced_to_proximity(self):
        s = self.structure
        edge_types = {x["edge_id"]:x for x in s["evidence_relations"]}
        self.assertTrue(edge_types["MOAG-R3-RC-013"]["physically_traversable_connection_asserted"])
        self.assertTrue(edge_types["MOAG-R3-RC-020"]["physically_traversable_connection_asserted"])
        self.assertFalse(edge_types["MOAG-R3-RC-024"]["physically_traversable_connection_asserted"])
        self.assertFalse(edge_types["MOAG-R3-RC-022"]["physically_traversable_connection_asserted"])
        self.assertFalse(edge_types["MOAG-R3-RC-004"]["physically_traversable_connection_asserted"])
        self.assertEqual(edge_types["MOAG-R3-RC-004"]["relation_class"],
                         "INTERLEVEL_SPAN_NOT_ACCESS")
        self.assertEqual(len(s["interlevel_span_without_access"]), 3)

    def test_direct_room_path_requires_actual_access_evidence(self):
        s = self.structure
        r = module.trace_direct_access(
            s, "M-L1-FH-001-CTRL", "M-L1-FH-002-CTRL")
        self.assertEqual(r["status"],
                         "EXPLICIT_ACCESS_CHAIN_WITHOUT_METRIC_GEOMETRY")
        self.assertIn("MOAG-R3-RC-020",
                      {x["edge_id"] for x in r["edge_chain"]})
        no = module.trace_direct_access(
            s, "M-L1-WASTE-001", "M-L1-WASTE-FURNACE-001")
        self.assertEqual(no["status"], "NO_PROVEN_DIRECT_ACCESS_CHAIN")
        with self.assertRaisesRegex(ValueError, "UNKNOWN_ACCESS_INDEX"):
            module.trace_direct_access(s, "NOT-IN-GRAPH", "M-L1-FH-001-CTRL")

    def test_areas_are_not_blindly_summed_as_three_floors(self):
        p = {x["physical_index_id"]:x
             for x in self.structure["spatial_area_volume_profiles"]}
        hall = p["M-L1-CH-001"]
        mezz = p["M-L1-CH-GAL-001"]
        env = p["M-STA-L1-001"]
        self.assertEqual(hall["global_level_domain"], [1])
        self.assertEqual(mezz["global_level_domain"], [1])
        self.assertEqual(env["global_level_domain"], [1])
        self.assertIsNotNone(hall["footprint_range_m2"])
        self.assertIsNotNone(hall["clear_volume_bounding_prism_range_m3"])
        self.assertIsNone(env["usable_floor_area_range_m2"])
        self.assertTrue(env["not_additive_by_default"])
        self.assertTrue(hall["scenario_not_text_measurement"])
        self.assertEqual(self.structure["area_and_volume_accounting"]["area_bearing"], 157)


if __name__ == "__main__":
    unittest.main()
