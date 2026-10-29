"""R22 real identities, evidence incidence corrections and no invented access."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools/moag_topology"))
import physical_connectivity_r22 as r22
import integrated_spatial_r15 as r15
import solver_r11 as r11
import contextual_crosswalk_r21 as r21


class EvidenceConnectivityR22(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m, cls.a = r22.build()
        cls.rows = {x["stage_id"]: x for x in cls.a["all_30_uses"]}

    def test_593_nodes_845_edges_and_378_occurrences_preserved(self):
        self.assertEqual(len(self.a["original_nodes"]), 593)
        self.assertEqual(len(self.a["original_edges"]), 845)
        self.assertEqual(len(self.m["r14"]["steps"]), 378)
        self.assertEqual(len(self.m["unbound_route_steps"]), 353)
        self.assertEqual(self.a["R09_fingerprint"], r11.digest(r11.inputs()[-1]))

    def test_all_30_and_dependent_31st_context(self):
        self.assertEqual(len(self.rows), 30)
        self.assertTrue(all(x["source_review"] for x in self.rows.values()))
        self.assertEqual(self.a["dependent_occurrence"]["stage_id"], "RT031-G")

    def test_source_qualified_repairs_do_not_downgrade_existing_r09_corrections(self):
        self.assertEqual(self.rows["RT015-G"]["effective_specific_referent"], "MOAG-G-0057")
        self.assertEqual(self.rows["RT024-F"]["effective_specific_referent"], "M-L1-AH-OLD-001")
        for sid, index in (("RT015-L", "M-L1-CH-CTRL-001"), ("RT024-H", "M-L1-AH-OLD-CTRL-001"),
                           ("RT015-J", "M-L1-CH-ST-001"), ("RT024-G", "M-L1-AH-OLD-ST-001")):
            self.assertEqual(self.rows[sid]["effective_specific_referent"], index)
        self.assertIsNone(self.rows["RT023-A"]["effective_specific_referent"])

    def test_sectors_and_corridors_never_assert_shared_room_identity(self):
        scoped = [x for x in self.rows.values() if x["original_legacy_alias"] in r22.SCOPES]
        self.assertEqual(len(scoped), 19)
        self.assertTrue(all(x["effective_specific_referent"] is None for x in scoped))
        self.assertEqual(len(self.a["uncertainty"]["gate_alternatives"]["objects"]), 11)

    def test_episode_hangar_f_and_g_cannot_join_first_boat_hangar_by_legacy_anchor(self):
        changed = [x for x in self.a["edge_dispositions"] if x["action"].startswith("LEGACY_CONTEXT")]
        self.assertEqual({x["edge_id"].split("::")[-1] for x in changed}, {"RT031-F", "RT031-G"})
        self.assertTrue(all(not x["qualified"]["joins_approved_evidence_component"] for x in changed))

    def test_direct_access_unchanged_and_not_added_by_identity(self):
        original = [e for e in self.a["original_edges"] if e.get("proves_direct_access")]
        projected = [x["qualified"] for x in self.a["edge_dispositions"]
                     if x["qualified"].get("proves_direct_access")]
        self.assertEqual(len(original), 25)
        self.assertEqual(original, projected)
        self.assertEqual([x["original"] for x in self.a["edge_dispositions"]
                          if x["edge_id"].startswith("STEP::")],
                         [x["qualified"] for x in self.a["edge_dispositions"]
                          if x["edge_id"].startswith("STEP::")])

    def test_reproducible_three_component_projections(self):
        expected = [("baseline_R21_raw", 197, [173, 48, 39]),
                    ("R21_source_qualified", 197, [173, 48, 39]),
                    ("R22_source_qualified_identity_quotient", 196, [172, 47, 39])]
        for key, classes, components in expected:
            self.assertEqual(self.a[key]["physical_identity_classes"], classes)
            self.assertEqual([v["components"] for v in self.a[key]["projections"].values()], components)
            self.assertTrue(all(sum(map(len, v["physical_index_memberships"])) == 197
                                for v in self.a[key]["projections"].values()))

    def test_one_new_source_union_without_stair_or_control_merges(self):
        unions = self.a["new_confirmed_physical_unions"]
        self.assertEqual(len(unions), 1)
        self.assertEqual((unions[0]["a"], unions[0]["b"]), r22.HALLS)
        self.assertEqual(unions[0]["source"]["id"], "R22-B1-110-EMMA-RECOLLECTION")
        multiple = [g for g in self.a["R22_source_qualified_identity_quotient"]["identity_classes"] if len(g) > 1]
        self.assertEqual(multiple, [sorted(r22.HALLS)])

    def test_all_known_hypotheses_gaps_and_unlocated_intervals_retained(self):
        u = self.a["uncertainty"]
        self.assertEqual(len(u["hypothetical_edges"]), 84)
        self.assertEqual(len(u["documented_gaps"]), 18)
        self.assertEqual(len(u["unlocated_intervals"]), 306)
        self.assertEqual(len(u["unlocated_fixed_elements"]), 12)
        self.assertEqual(len(u["identity_candidate_rows"]), 9)
        self.assertEqual(len(u["unresolved_identity_pairs"]), 7)
        self.assertTrue(all(x["alternatives"] and x["confirm_if"] and x["refute_if"]
                            for x in u["hypothetical_edges"] + u["identity_candidate_rows"]))

    def test_no_metric_global_level_or_profile_rewrite(self):
        p = self.a["geometry_policy"]
        self.assertEqual(p["global_levels"], [1, 2, 3])
        self.assertEqual(p["new_metric_constraints"], 0)
        self.assertEqual(p["scenario_volumes"], 12)
        self.assertEqual(self.a["protected_model"]["R05_profiles"], r11.digest(r11.inputs()[2]))

    def test_all_previous_variables_and_constraints_preserved_exactly(self):
        base, _, _, _ = r21.build()
        self.assertEqual(self.m["variables"][:-1], base["variables"])
        self.assertEqual(self.m["constraints"][:-2], base["constraints"])
        self.assertEqual(self.m["r13"], base["r13"])
        self.assertEqual(self.m["r14"], base["r14"])

    def test_forged_door_and_component_merge_fail_validation(self):
        for mutation in ("door", "component", "identity"):
            a = deepcopy(self.a)
            if mutation == "door":
                a["edge_dispositions"][0]["qualified"]["proves_direct_access"] = True
            elif mutation == "component":
                a["R22_source_qualified_identity_quotient"]["projections"]["route_evidence"]["components"] -= 1
            else:
                a["R22_source_qualified_identity_quotient"]["identity_classes"][0].append("M-L1-FH-001")
            with self.assertRaisesRegex(ValueError, "R22_UNSOURCED"):
                r22.validate(self.m, a)


@unittest.skipUnless(importlib.util.find_spec("ortools"), "Official OR-Tools required")
class RealIdentityR22(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m, cls.a = r22.build()

    def test_joint_model_sat(self):
        z = r15.cp_solve(self.m)
        self.assertEqual(z["status"], "SAT")
        self.assertTrue(r15.verify(self.m, z["witness"]))

    def test_new_identity_is_source_causal_and_source_core_replays(self):
        q = r22.query(self.a, *r22.HALLS, "different", "TEST-R22-SPLIT")
        self.assertEqual(r15.cp_solve(self.m, [q], exclude_families=("r22_cross_episode_identity",))["status"], "SAT")
        z = r15.cp_solve(self.m, [q])
        self.assertEqual(z["status"], "INFEASIBLE")
        ids = {c["id"] for c in z["unsat_core"]}
        self.assertIn("R22-SAME-ROUND-AND-OLD-HALL", ids)
        self.assertEqual(r15.cp_solve(self.m, [q], active=ids)["status"], "INFEASIBLE")

    def test_sleeping_hall_and_independent_boat_hangars_not_merged(self):
        for left, right in ((r22.HALLS[1], "MOAG-G-0057"), ("M-L1-FH-001", "M-L1-FH-002")):
            q = r22.query(self.a, left, right, "same", "TEST-R22-MERGE")
            self.assertEqual(r15.cp_solve(self.m, [q])["status"], "INFEASIBLE")

    def test_seven_unknown_pairs_each_allow_same_and_different(self):
        for p in self.a["uncertainty"]["unresolved_identity_pairs"]:
            for kind in ("same", "different"):
                q = r22.query(self.a, p["a"], p["b"], kind, "TEST-R22-OPEN")
                self.assertEqual(r15.cp_solve(self.m, [q])["status"], "SAT")


if __name__ == "__main__":
    unittest.main()
