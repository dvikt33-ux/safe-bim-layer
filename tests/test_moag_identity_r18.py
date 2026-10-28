"""МОАГ R18: test proof strength, transitive same identity, unresolved countermodels."""
import importlib.util
import sys
import unittest
from copy import deepcopy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools/moag_topology"))
import identity_alternatives_r18 as r18
import integrated_spatial_r15 as r15
import solver_r11 as r11


class SourceIntegrityR18(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m,cls.audit=r18.build()

    def test_source_identity_counts_and_master_fingerprint(self):
        self.assertEqual(len(self.audit["tokens"]),15)
        self.assertEqual(len(self.audit["proven_same"]),4)
        self.assertEqual(len(self.audit["proven_different"]),1)
        self.assertEqual(len(self.audit["not_yet_decidable"]),6)
        self.assertEqual(self.audit["R09_fingerprint"],r11.digest(r11.inputs()[-1]))
        self.assertEqual(self.audit["r15_bound_visits"],25)
        self.assertEqual(self.audit["r15_unbound_visits"],353)
        self.assertEqual(len(self.m["r14"]["steps"]),378)
        self.assertTrue(r18.validate(self.m,self.audit))

    def test_same_source_not_from_shared_legacy_label(self):
        same={(x["a"],x["b"]):x["source_observation_id"]
              for x in self.audit["proven_same"]}
        self.assertEqual(same[("RT024-J","RT024-G")],"P-317")
        self.assertEqual(same[("RT015-J","M-L1-CH-ST-001")],"P-220")
        self.assertEqual(same[("RT024-G","M-L1-AH-OLD-ST-001")],"P-313")
        self.assertEqual(same[("RT030-G","M-L1-FH-001-ST")],"P-365")
        self.assertNotIn(("RT015-J","RT024-G"),same)
        self.assertFalse(self.audit["full_3d_geometry_proven"])

    def test_neighboring_boat_hangars_distinct_despite_operator_connection(self):
        diff=self.audit["proven_different"]
        self.assertEqual(len(diff),1)
        self.assertEqual({diff[0]["a"],diff[0]["b"]},
                         {"M-L1-FH-001","M-L1-FH-002"})
        self.assertEqual(diff[0]["source_observation_id"],"P-367")
        self.assertEqual(diff[0]["additional_source_observation_id"],"P-368")
        self.assertFalse(diff[0]["metric_xyz_implied"])

    def test_old_cargo_hangar_not_forcibly_merged_with_sleeper_or_raised_controller(self):
        v={frozenset((x["a"],x["b"])) for x in self.audit["not_yet_decidable"]}
        self.assertIn(frozenset(("M-L1-CG-001","M-L1-AH-OLD-001")),v)
        self.assertIn(frozenset(("MOAG-G-0057","M-L1-AH-OLD-001")),v)
        self.assertIn(frozenset(("MOAG-G-0053","M-L1-CG-001")),v)
        self.assertTrue(all(not x["hard_identity_added"] and
                            not x["hard_distinctness_added"]
                            for x in self.audit["not_yet_decidable"]))

    def test_fail_closed_cannot_rewrite_book_identity_and_geometry(self):
        a=deepcopy(self.audit)
        a["not_yet_decidable"][0]["hard_identity_added"]=True
        with self.assertRaisesRegex(ValueError,"R18_UNSUPPORTED_IDENTITY_PROMOTED"):
            r18.validate(self.m,a)
        a=deepcopy(self.audit)
        a["full_3d_geometry_proven"]=True
        with self.assertRaisesRegex(ValueError,"R18_GEOMETRY_OR_SOURCE_PROMOTION"):
            r18.validate(self.m,a)
        m=deepcopy(self.m)
        cid="R18-SAME::RT024-J::RT024-G"
        c=next(x for x in m["constraints"] if x["id"]==cid)
        c["rows"][0]["rhs"]=1
        with self.assertRaisesRegex(ValueError,"R18_SOURCED_SAME_DROPPED"):
            r18.validate(m,self.audit)


@unittest.skipUnless(importlib.util.find_spec("ortools"),"Requires official OR-Tools")
class CPIdentityR18(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m,cls.audit=r18.build()

    def test_real_joint_sat_and_identity_token_semantics(self):
        p=r15.cp_solve(self.m)
        self.assertEqual(p["status"],"SAT")
        self.assertTrue(r15.verify(self.m,p["witness"]))
        v=p["witness"]["values"];t=self.audit["tokens"]
        self.assertEqual(v[t["RT024-G"]],v[t["RT024-J"]])
        self.assertEqual(v[t["RT024-G"]],v[t["M-L1-AH-OLD-ST-001"]])
        self.assertNotEqual(v[t["M-L1-FH-001"]],v[t["M-L1-FH-002"]])

    def test_both_unproven_stair_identity_outcomes_satisfiable(self):
        a,b="RT015-J","RT024-G"
        for kind in ("same","different"):
            p=r18.query(self.audit,a,b,kind)
            z=r15.cp_solve(self.m,[p])
            self.assertEqual(z["status"],"SAT",kind)

    def test_both_unproven_old_hangar_identity_outcomes_satisfiable(self):
        a,b="M-L1-CG-001","M-L1-AH-OLD-001"
        for kind in ("same","different"):
            p=r18.query(self.audit,a,b,kind)
            self.assertEqual(r15.cp_solve(self.m,[p])["status"],"SAT")

    def test_reversing_confirmed_same_stair_is_unsat_with_source(self):
        q=r18.query(self.audit,"RT024-G","RT024-J","different",
                    "TEST-R18-FALSE-TWO-STAIRS")
        cp=r15.cp_solve(self.m,[q])
        self.assertEqual(cp["status"],"INFEASIBLE")
        ids={c["id"] for c in cp["unsat_core"]}
        self.assertIn(q["id"],ids)
        self.assertIn("R18-SAME::RT024-J::RT024-G",ids)
        self.assertTrue(any(x["id"]=="P-317" for c in cp["unsat_core"]
                            for x in c.get("sources",[])))

    def test_merging_distinct_hangars_unsat_without_fabricated_metric_distance(self):
        q=r18.query(self.audit,"M-L1-FH-001","M-L1-FH-002","same",
                    "TEST-R18-COLLAPSE-NEIGHBOR-HANGARS")
        cp=r15.cp_solve(self.m,[q])
        self.assertEqual(cp["status"],"INFEASIBLE")
        ids={c["id"] for c in cp["unsat_core"]}
        self.assertIn(q["id"],ids)
        self.assertIn("R18-DIFFERENT::M-L1-FH-001::M-L1-FH-002",ids)

if __name__=="__main__":unittest.main()
