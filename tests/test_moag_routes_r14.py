"""MOAG R14: route-step preservation is not evidence of direct door adjacency."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools/moag_topology"))
import route_constraints_r14 as r14
import solver_r11 as r11


class R14SourceSemantics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m=r14.build()

    def test_all_source_routes_and_vertical_notes_present(self):
        m=self.m
        self.assertEqual(len(m["routes"]),52)
        self.assertEqual(len(m["steps"]),378)
        self.assertEqual(len(m["observed_order_not_direct_access"]),326)
        self.assertEqual(len(m["strict_local_or_global_relative_z"]),32)
        self.assertEqual(len(m["non_strict_route_flags"]),1)
        self.assertEqual(m["R09_fingerprint"],r11.digest(r11.inputs()[-1]))
        self.assertTrue(r14.validate(m))

    def test_going_to_wild_base_is_not_one_direct_segment(self):
        m=self.m
        r=next(r for r in m["routes"] if r["id"]=="RT-006")
        self.assertEqual(len(r["step_ids"]),7)
        self.assertEqual(r["minimum_recorded_intermediate_stages"],5)
        ids={s["id"]:s for s in m["steps"]}
        self.assertEqual(ids[r["step_ids"][0]]["stable_graph_anchor"],"MOAG-G-0008")
        self.assertEqual(ids[r["step_ids"][-1]]["stable_graph_anchor"],"MOAG-G-0010")
        vertical=[e for e in m["strict_local_or_global_relative_z"] if e["route"]=="RT-006"]
        self.assertEqual([(e["higher"],e["lower"]) for e in vertical],[("RT006-D","RT006-E")])
        self.assertTrue(all(not x["direct_door_asserted"] for x in m["observed_order_not_direct_access"]))

    def test_two_descent_observations_in_dark_to_cargo_route(self):
        vertical=[x for x in self.m["strict_local_or_global_relative_z"] if x["route"]=="RT-007"]
        self.assertEqual({(c["higher"],c["lower"]) for c in vertical},
                        {("RT007-A","RT007-B"),("RT007-C","RT007-D")})
        matched=self.m["candidate_only_step_index_matches"]
        self.assertEqual(len(matched),1)
        self.assertEqual(matched[0]["step_id"],"RT007-H")
        self.assertEqual(matched[0]["candidate_index"],"MOAG-G-0080")
        self.assertFalse(matched[0]["becomes_hard_geometry_anchor"])

    def test_oval_dark_descriptions_tied_to_both_bases(self):
        routes=self.m["author_attached_base_route_overlays"]
        self.assertEqual({x["source"]["id"] for x in routes},{"P-024","P-305"})
        self.assertTrue(all({x["from"],x["to"]}=={"MOAG-G-0008","MOAG-G-0009"}
                            for x in routes))
        self.assertTrue(all(not x["unplaced_free_floating_corridor_allowed"]
                            and not x["segments_are_direct_doors"]
                            and x["corridor_xy_m"] is None for x in routes))

    def test_route_stages_are_not_new_physical_rooms(self):
        for s in self.m["steps"]:
            self.assertFalse(s["new_physical_node_created"])
            self.assertIsNone(s["xy_m"])
            self.assertIsNone(s["z_m"])
        self.assertEqual(self.m["unverified_page_cross_references"],
                         ["B1-061","B1-063","B1-064","B1-065"])
        self.assertFalse(self.m["geometry_approved"])
        self.assertFalse(self.m["archicad_write"])

    def test_mutations_do_not_pass_semantic_checks(self):
        m=deepcopy(self.m)
        m["author_attached_base_route_overlays"][0]["to"]="MOAG-G-0080"
        with self.assertRaisesRegex(ValueError,"BASE_ROUTE_DISCONNECTED"):
            r14.validate(m)
        m=deepcopy(self.m)
        m["observed_order_not_direct_access"][0]["direct_door_asserted"]=True
        with self.assertRaisesRegex(ValueError,"ROUTE_ORDER_BECAME_GEOMETRIC_ACCESS"):
            r14.validate(m)
        m=deepcopy(self.m)
        r=next(x for x in m["routes"] if x["id"]=="RT-006")
        r["step_ids"].pop(3)
        with self.assertRaisesRegex(ValueError,"ROUTE_STAGES_DROPPED"):
            r14.validate(m)
        m=deepcopy(self.m)
        m["candidate_only_step_index_matches"][0]["becomes_hard_geometry_anchor"]=True
        with self.assertRaisesRegex(ValueError,"UNAPPROVED_CARGO_REFERENT_MERGE"):
            r14.validate(m)


@unittest.skipUnless(importlib.util.find_spec("ortools"),"Install requirements-r11.txt")
class R14RealSolver(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m=r14.build()

    def test_32_vertical_orders_really_satisfiable(self):
        result=r14.cp_solve(self.m)
        self.assertEqual(result["status"],"SAT")
        self.assertTrue(r14.verify(self.m,result["witness"]))

    def test_book_vertical_constraint_inverse_is_unsat(self):
        source=next(x for x in self.m["strict_local_or_global_relative_z"]
                    if (x["higher"],x["lower"])==("RT006-D","RT006-E"))
        test={"id":"TEST-REVERSE-RT006","type":"REVERSED_RECORDED_HEIGHT",
              "reverse_id":source["id"]}
        bad=r14.cp_solve(self.m,inject=test)
        self.assertEqual(bad["status"],"INFEASIBLE")
        core={x["id"] for x in bad["unsat_core"]}
        self.assertIn(test["id"],core)
        self.assertIn(source["id"],core)
        self.assertTrue(any("B1-043" in x.get("source_page_id","")
                            for x in bad["unsat_core"]))

    def test_wild_base_detour_cannot_be_compressed_to_one_recorded_hop(self):
        test={"id":"TEST-DIRECT-SKIP-RT006","type":"COMPRESSED_ROUTE_SHORTCUT","route":"RT-006"}
        bad=r14.cp_solve(self.m,inject=test)
        self.assertEqual(bad["status"],"INFEASIBLE")
        core={x["id"] for x in bad["unsat_core"]}
        self.assertIn(test["id"],core)
        self.assertTrue(any(i.startswith("R14-SEQ-RT-006") for i in core))

    def test_fake_z_order_witness_rejected(self):
        m=self.m
        w=deepcopy(r14.cp_solve(m)["witness"])
        ids={s["id"]:i for i,s in enumerate(m["steps"])}
        w["z"][ids["RT006-D"]]=w["z"][ids["RT006-E"]]
        with self.assertRaisesRegex(ValueError,"SOURCE_VERTICAL_ORDER_CONTRADICTION"):
            r14.verify(m,w)

if __name__=="__main__":
    unittest.main()
