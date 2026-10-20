"""МОАГ R10: frontier priority is NOT a geometry or adjacency solver."""
from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/moag_topology"))
import reconcile_uncertainty_r09 as r09
import review_frontiers_r10 as r10


class SourceFrontiersR10(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph = r10.read(r10.SYNTH / "full_indexed_parametric_graph_r04.json")
        cls.fragments = r10.read(r10.SYNTH / "progressive_fragments_r05.json")
        cls.bounds = r10.read(r10.SYNTH / "area_volume_bounds_r05.json")
        cls.routes = r10.read(r10.BASE / "v2/character_routes.json")
        cls.left = r09.r08a.build(cls.graph, cls.fragments, cls.bounds, cls.routes)
        cls.master = r09.build(cls.graph, cls.fragments, cls.bounds,
                               cls.routes, left=cls.left)
        cls.output = r10.build(cls.graph, cls.fragments, cls.bounds,
                               cls.routes, left=cls.left, master=cls.master)

    def run_mutant(self, data=None, identity_register=None):
        return r10.build(
            self.graph, self.fragments, self.bounds, self.routes,
            left=self.left, master=data if data is not None else self.master,
            identity_register=identity_register)

    def test_all_open_questions_survive_without_master_mutations(self):
        q = self.output["quantities"]
        self.assertEqual(q["fixed_isolates"], 12)
        self.assertEqual(q["candidate_options"], 24)
        self.assertEqual(q["narrative_gaps"], 18)
        self.assertEqual(q["witnessed_intervals"], 306)
        self.assertEqual(q["global_identity_questions"], 5)
        self.assertEqual(self.output["immutable_graph_quantities"]["proven_nodes"], 575)
        self.assertEqual(self.output["immutable_graph_quantities"]["proven_edges"], 761)
        self.assertEqual(self.output["immutable_graph_quantities"]["proven_components"], 39)
        self.assertEqual(self.output["immutable_graph_quantities"]["approved_direct_access"], 25)
        self.assertFalse(any(self.output["gates"].values()))
        self.assertEqual(len(self.master["nodes"]), 593)
        self.assertEqual(len(self.master["edges"]), 845)

    def test_fixed_options_are_alternatives_not_physical_access(self):
        groups = self.output["fixed_isolates"]
        self.assertEqual(len({x["target_index_id"] for x in groups}), 12)
        for group in groups:
            self.assertTrue(group["may_remain_unlocated"])
            self.assertEqual(len(group["possible_options"]), 2)
            for option in group["possible_options"]:
                self.assertFalse(option["approved_as_link"])
                self.assertTrue(option["candidate_anchors_not_proven_neighbors"])
                self.assertTrue(all(
                    "anchor_proven_component" in x and
                    "different_components_if_later_proven" in x
                    for x in option["candidate_anchors_not_proven_neighbors"]))

    def test_page_triage_never_claims_connectivity(self):
        queue = self.output["source_page_review_queue"]
        self.assertEqual(len({x["page_id"] for x in queue}), len(queue))
        self.assertTrue(queue)
        self.assertTrue(all(not x["can_merge_components"]
                            and x["cooccurrence_is_only_a_review_hint"]
                            and x["url"].startswith("http")
                            for x in queue))
        self.assertEqual(queue, sorted(
            queue, key=lambda x: (-x["priority_score_not_confidence"],
                                  x["already_marked_full_page_reviewed"],
                                  x["page_id"])))
        self.assertTrue(all(
            x["not_proof_of_immediate_access"] and
            x["unknown_number_of_intervening_elements"]
            for x in self.output["witnessed_intervals_without_direct_geometry"]))
        self.assertTrue(all(x["no_direct_link_or_new_corridor_proven"]
                            for x in self.output["narrative_route_gaps"]))

    def test_cannot_drop_an_isolated_fixed_group(self):
        data = copy.deepcopy(self.master)
        data["unlocated_fixed_element_options"].pop()
        with self.assertRaisesRegex(ValueError, "R10_FIXED_GROUP_LOST"):
            self.run_mutant(data=data)

    def test_cannot_drop_a_route_gap_or_interval(self):
        data = copy.deepcopy(self.master)
        data["gap_placeholders"].pop()
        with self.assertRaisesRegex(ValueError, "R10_GAP_COUNT_CHANGED"):
            self.run_mutant(data=data)
        data = copy.deepcopy(self.master)
        data["witnessed_route_steps_with_unresolved_intermediate_geometry"].pop()
        with self.assertRaisesRegex(ValueError, "R10_WITNESSED_INTERVAL_COUNT_CHANGED"):
            self.run_mutant(data=data)

    def test_cannot_promote_soft_option_to_access(self):
        data = copy.deepcopy(self.master)
        target_id = data["unlocated_fixed_element_options"][0]["canonical_edge_ids"][0][0]
        e = next(x for x in data["edges"] if x["id"] == target_id)
        e["proves_direct_access"] = True
        with self.assertRaisesRegex(ValueError, "R10_OPTION_PROMOTED_OR_MISSING"):
            self.run_mutant(data=data)

    def test_cannot_declare_old_identity_question_solved(self):
        identities = r10.read(r10.IDENTITIES)
        identities["review_items"][0]["global_identity_approved"] = True
        with self.assertRaisesRegex(ValueError, "R10_UNREVIEWED_IDENTITY_WAS_PROMOTED"):
            self.run_mutant(identity_register=identities)


if __name__ == "__main__":
    unittest.main()
