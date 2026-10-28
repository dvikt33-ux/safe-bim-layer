"""R12 contracts: no geometric promotion and genuine interval-envelope SAT/UNSAT."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools/moag_topology"))
import solver_r11 as r11
import spatial_constraints_r12 as r12


class SourceAndScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lower=r12.build(1)
        cls.second=r12.build(2)
        cls.third=r12.build(3)

    def test_r09_unchanged_and_no_geometry(self):
        self.assertEqual(self.lower["r11"]["R09_quantities"]["total_vertices"],593)
        self.assertEqual(self.lower["r11"]["R09_quantities"]["total_typed_edges"],845)
        self.assertEqual(self.lower["R09_fingerprint"],r11.digest(r11.inputs()[-1]))
        self.assertTrue(self.lower["immutable_R09"])
        self.assertFalse(self.lower["geometry_approved"])
        self.assertFalse(self.lower["archicad_write"])
        self.assertTrue(r12.validate(self.lower))

    def test_raised_within_halls_does_not_create_full_floors(self):
        pairs={(e["container"],e["upper"]) for e in self.lower["envelopes"]}
        self.assertIn(("M-L1-FH-001","M-L1-FH-001-CTRL"),pairs)
        self.assertIn(("M-L1-FH-002","M-L1-FH-002-CTRL"),pairs)
        self.assertIn(("M-L1-CH-001","M-L1-CH-GAL-001"),pairs)
        self.assertIn(("MOAG-G-0055","MOAG-G-0058"),pairs)
        self.assertEqual(len(self.lower["envelopes"]),7)
        self.assertTrue(all(not e["full_upper_floor_inferred"]
                            and not e["floor_plan_geometry_proven"]
                            for e in self.lower["envelopes"]))
        self.assertEqual(len(self.second["envelopes"]),1)
        self.assertEqual(len(self.third["envelopes"]),1)
        self.assertIn(("MOAG-G-0036","MOAG-G-0095"),
                      {(e["container"],e["upper"]) for e in self.third["envelopes"]})

    def test_indirect_base_routes_not_direct_access_or_metrics(self):
        links=self.lower["source_backed_routes_not_solver_constraints"]
        self.assertEqual({x["source"]["id"] for x in links},{"P-024","P-305"})
        self.assertTrue(all(x["from"]=="MOAG-G-0008" and x["to"]=="MOAG-G-0009"
                            and not x["direct_access_claim"]
                            and x["numerical_length_m"] is None for x in links))
        self.assertEqual(self.second["source_backed_routes_not_solver_constraints"],[])

    def test_corrupt_plan_and_vertical_proof_rejected(self):
        p=deepcopy(self.lower)
        p["envelopes"][0]["full_upper_floor_inferred"]=True
        with self.assertRaisesRegex(ValueError,"GEOMETRIC_PROMOTION"):
            r12.validate(p)
        p=deepcopy(self.lower)
        p["source_backed_routes_not_solver_constraints"][0]["direct_access_claim"]=True
        with self.assertRaisesRegex(ValueError,"INDIRECT_ROUTE_PROMOTED"):
            r12.validate(p)
        p=deepcopy(self.lower)
        p["r11"]["constraints"][0]["a"]="MOAG-G-0091"
        with self.assertRaisesRegex(ValueError,"R11_PROVEN_CONSTRAINT_CHANGED"):
            r12.validate(p)

    def test_areas_unknown_and_absent_hull_or_metric_claims(self):
        self.assertFalse(self.lower["r11"]["metric_area_constraints_enabled"])
        self.assertFalse(self.lower["r11"]["full_floor_decks_inferred"])
        self.assertEqual(self.lower["r11"]["hypothesis_edges_used_as_hard_constraints"],0)
        for e in self.lower["envelopes"]:
            self.assertFalse(e["metric_height_proven"])
            self.assertFalse(e["two_legacy_names_merged"])
            self.assertTrue(e["sources"])
            self.assertTrue(all(s.get("url") for s in e["sources"]))

    def test_r03_hall_not_merged_with_conceptual_hall(self):
        pairs={(e["container"],e["upper"]) for e in self.lower["envelopes"]}
        self.assertIn(("M-L1-CH-001","M-L1-CH-GAL-001"),pairs)
        self.assertIn(("MOAG-G-0055","MOAG-G-0058"),pairs)
        self.assertFalse(self.lower["r11"]["R09_mutated"])


@unittest.skipUnless(importlib.util.find_spec("ortools"),"Install requirements-r11.txt")
class RealR12SolverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lower=r12.build(1)
        cls.second=r12.build(2)

    def test_real_satisfiability_three_scopes(self):
        for p in (self.lower,self.second,self.third):
            r=r12.cp_solve(p)
            self.assertEqual(r["status"],"SAT")
            self.assertTrue(r12.verify(p,r["witness"]))

    def test_synthetic_ceiling_inversion_explained(self):
        source=next(x for x in self.lower["envelopes"] if x["id"]=="MOAG-R3-RC-016")
        inverse={"id":"R12-SYNTHETIC-TEST-HEIGHT",
                 "type":"SYNTHETIC_CEILING_BELOW_UPPER",
                 "container":source["container"],"upper":source["upper"]}
        result=r12.cp_solve(self.lower,inverse)
        self.assertEqual(result["status"],"INFEASIBLE")
        ids={x["id"] for x in result["unsat_core"]}
        self.assertIn(inverse["id"],ids)
        self.assertIn(source["id"],ids)
        self.assertTrue(any("p=14" in s["url"] for x in result["unsat_core"]
                            for s in x.get("sources",[])))

    def test_corrupt_envelope_witness_rejected(self):
        p=self.lower
        witness=deepcopy(r12.cp_solve(p)["witness"])
        source=p["envelopes"][0]
        ids={e["id"]:i for i,e in enumerate(p["r11"]["entities"])}
        witness["top"][ids[source["container"]]]=0
        with self.assertRaisesRegex(ValueError,"VERTICAL_ENVELOPE_CONTRADICTION"):
            r12.verify(p,witness)

if __name__=="__main__":
    unittest.main()
