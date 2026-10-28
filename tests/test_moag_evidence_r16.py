"""R16: classification never authorizes geometry, fork comparison is real solver work."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"tools/moag_topology"))
import evidence_triage_r16 as r16
import integrated_spatial_r15 as r15
import solver_r11 as r11


class R16EvidenceAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m, cls.audit = r16.build()

    def test_353_stages_and_review_queue_no_automatic_rooms(self):
        d = self.audit["review_queue"]
        self.assertEqual(len(d), 353)
        self.assertEqual(sum(bool(x["index_anchor"]) for x in d), 189)
        self.assertEqual(sum(x["index_anchor"] is None for x in d), 164)
        self.assertEqual(sum(x["global_block_domain"] == [1] for x in d), 112)
        self.assertTrue(all(not x["new_physical_entity_authorized"] and
                            not x["placement_approved"] and
                            not x["metric_area_authorized"] for x in d))
        self.assertEqual(self.audit["R09_fingerprint"], r11.digest(r11.inputs()[-1]))
        self.assertTrue(r16.validate(self.m, self.audit))

    def test_aggregate_is_not_auto_room_and_original_stage_is_not_lost(self):
        x = {x["id"]:x for x in self.audit["review_queue"]}
        self.assertEqual(x["RT001-L"]["index_kind"], "zone")
        self.assertEqual(x["RT001-L"]["review_class"],
                         "INDEXED_AGGREGATE_OR_SYSTEM_REQUIRES_DOMAIN_NOT_ROOM")
        self.assertEqual(x["RT007-H"]["review_class"],
                         "UNINDEXED_MOVEMENT_OR_FEATURE_REVIEW_NOT_NEW_ROOM")
        self.assertEqual(x["RT014-B"]["review_class"],
                         "UNLOCATED_NARRATIVE_GAP_NO_SHAFT_OR_ROOM_AUTHORIZED")
        self.assertFalse(x["RT014-B"]["new_physical_entity_authorized"])
        self.assertEqual(len(self.m["r14"]["steps"]), 378)
        self.assertEqual(len(self.m["r13"]["volumes"]), 12)
        self.assertEqual(len(self.m["unbound_route_steps"]), 353)

    def test_four_missing_observation_links_found_in_preexisting_page_ledger(self):
        overlay = {x["page_id"]:x for x in self.audit["source_url_overlay"]}
        self.assertEqual(set(overlay), {"B1-061","B1-063","B1-064","B1-065"})
        for page, record in overlay.items():
            self.assertIn("loveread.ec/read_book.php", record["url"])
            self.assertTrue(record["route_stages_with_page"])
            self.assertFalse(record["primary_text_reaudited_in_R16"])
            self.assertFalse(record["R14_source_record_rewritten"])
            self.assertEqual(record["source_of_url"], "EXISTING_B1_PAGE_LEDGER_NOT_PAGE_OBSERVATION")

    def test_fork_attached_to_existing_index_not_new_path_geometry(self):
        f=self.audit["fork_comparison"]
        self.assertEqual(f["fork_index"],"MOAG-G-0100")
        self.assertEqual(f["observed_long_branch_stage"],"RT014-E")
        self.assertEqual(f["source_page"],"B1-065")
        self.assertEqual(f["kind"],"QUALITATIVE_RELATIVE_PATH_LENGTH_ONLY")
        self.assertFalse(f["metric_distance_measured"])
        self.assertFalse(f["physical_door_proven"])
        self.assertFalse(f["both_branches_new_physical_nodes"])
        self.assertFalse(f["junction_xy_proven"])

    def test_source_promotion_and_geometry_are_rejected(self):
        a=deepcopy(self.audit)
        a["review_queue"][0]["placement_approved"]=True
        with self.assertRaisesRegex(ValueError,"REVIEW_PROMOTED_TO_PHYSICAL_ROOM"):
            r16.validate(self.m,a)
        a=deepcopy(self.audit)
        a["fork_comparison"]["metric_distance_measured"]=True
        with self.assertRaisesRegex(ValueError,"QUALITATIVE_PATH_LENGTH_PROMOTED_TO_METRES"):
            r16.validate(self.m,a)
        m=deepcopy(self.m)
        c=next(c for c in m["constraints"] if c["id"]=="R16-FORK-B1-065-LONGER-THAN-SHORTER")
        c["rows"][0]["rhs"]=0
        with self.assertRaisesRegex(ValueError,"FORK_CONSTRAINT_MISSING_OR_INVERTED"):
            r16.validate(m,self.audit)


@unittest.skipUnless(importlib.util.find_spec("ortools"), "Install R11 solver requirements")
class R16RealSolverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m,cls.audit=r16.build()

    def test_full_r15_with_r16_fork_is_sat(self):
        a=r15.cp_solve(self.m)
        self.assertEqual(a["status"],"SAT")
        self.assertTrue(r15.verify(self.m,a["witness"]))
        v=a["witness"]["values"]
        self.assertGreater(v[self.audit["fork_long_rank_var"]],
                           v[self.audit["fork_short_rank_var"]])

    def test_missing_fork_relation_provably_expands_qualitative_domain(self):
        vi=self.audit["fork_long_rank_var"]
        before=r15.cp_solve(self.m,exclude_families=("r16_branch_choice",),
                            objective=(vi,"min"))
        after=r15.cp_solve(self.m,objective=(vi,"min"))
        self.assertEqual(before["solver_status"],"OPTIMAL")
        self.assertEqual(after["solver_status"],"OPTIMAL")
        self.assertEqual(before["objective"],0)
        self.assertEqual(after["objective"],1)

    def test_inverse_source_fork_is_explained_unsat(self):
        a=self.audit
        inverse=r15.probe("TEST-INVERSE-R16-FORK",
                          [r15.row([(a["fork_short_rank_var"],1),
                                    (a["fork_long_rank_var"],-1)],0)])
        result=r15.cp_solve(self.m,[inverse])
        self.assertEqual(result["status"],"INFEASIBLE")
        core={x["id"] for x in result["unsat_core"]}
        self.assertIn(inverse["id"],core)
        self.assertIn(a["fork_comparison"]["id"],core)
        self.assertTrue(any("B1-065" in str(s) for c in result["unsat_core"]
                            for s in c.get("sources", [])))

if __name__=="__main__":
    unittest.main()
