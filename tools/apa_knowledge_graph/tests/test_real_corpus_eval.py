"""Deterministic exact-ID structural retrieval census over real APA plan.

This is a source-derived oracle NOT human-adjudicated semantic-RAG gold set.
It verifies that every registered task and artifact can be resolved with a
bounded response, without reading the whole plan into model-visible context.
"""
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from graph import build_index, canonical
from gateway import retrieve

REAL_PLAN = Path(__file__).resolve().parents[3] / "docs/research/apa-results/control/PROJECT_PLAN.json"
REPO = "dvikt33-ux/safe-bim-layer"


@unittest.skipUnless(REAL_PLAN.exists(), "Only runs in full GitHub checkout")
class RealRegistryRetrievalCensus(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = json.loads(REAL_PLAN.read_text(encoding="utf-8"))
        cls.index = build_index(cls.plan)

    def query(self, expression, budget=12000):
        return retrieve(self.index, self.plan, None, None, REPO,
                        expression, max_chars=budget, limit=10)

    def test_entire_registered_task_set_exact_lookup(self):
        failures = []
        total = 0
        for task_id, row in sorted(self.plan["tasks"].items()):
            result = self.query(task_id)
            total += 1
            if (result.get("status") != "OK" or
                    result.get("retrieval") != "EXACT_TASK" or
                    len(result["items"]) != 1 or
                    result["items"][0].get("id") != task_id or
                    result["items"][0].get("status") != row["status"]):
                failures.append(task_id)
        self.assertEqual(failures, [])
        self.assertGreaterEqual(total, 91)
        print("REAL_CENSUS_EXACT_TASKS", total, "failures", len(failures))

    def test_entire_registered_artifact_set_exact_lookup(self):
        failures = []
        for art_id, row in sorted(self.plan["artifacts"].items()):
            result = self.query(art_id)
            if (result.get("status") != "OK" or
                    result.get("retrieval") != "EXACT_ARTIFACT" or
                    len(result["items"]) != 1 or
                    result["items"][0].get("id") != art_id or
                    result["items"][0].get("task_reference_count") !=
                    len(self.index["artifact_to_tasks"].get(art_id, []))):
                failures.append(art_id)
        self.assertEqual(failures, [])
        self.assertGreaterEqual(len(self.plan["artifacts"]), 166)
        print("REAL_CENSUS_EXACT_ARTIFACTS", len(self.plan["artifacts"]), "failures", len(failures))

    def test_shared_artifact_pairs_under_fixed_budget(self):
        candidates = []
        for task_id, task in sorted(self.plan["tasks"].items()):
            ids = sorted(set(task.get("inputs", [])) | set(task.get("evidence", [])))
            for j in range(min(len(ids) - 1, 3)):
                pair = (ids[j], ids[j+1])
                if pair not in candidates:
                    candidates.append(pair)
        count = 0
        failures = []
        for a,b in candidates[:40]:
            result = self.query(a + " " + b, budget=2000)
            count += 1
            # Each pair has a shared task by independent registered PLAN data.
            if (result.get("status") != "OK" or
                    result.get("retrieval") != "MULTI_ARTIFACT_GRAPH" or
                    result.get("task_refs_all", 0) < 1 or
                    not any(item.get("task_id") for item in result["items"])):
                failures.append((a,b,result.get("status")))
        self.assertEqual(failures, [])
        self.assertGreaterEqual(count, 20)
        print("REAL_CENSUS_SHARED_ARTIFACT_PAIRS", count, "failures", len(failures))

    def test_plan_next_actions_never_claim_and_no_fulltext(self):
        result = retrieve(self.index, self.plan, None, None, REPO,
                          "что делать дальше", mode="plan", limit=5, max_chars=2500)
        self.assertEqual(result["retrieval"], "DETERMINISTIC_PLAN_CANDIDATES")
        self.assertEqual(result["task_claim"], "NEVER_AUTOMATIC")
        self.assertTrue(all(item["requires_claim"] for item in result["items"]))
        self.assertLessEqual(len(canonical(result)), 2500)
        expected = sum(1 for tid,item in self.index["tasks"].items()
                       if item["status"] in ("READY", "PARTIAL")
                       and not (item["owner"] or item["claim_ref"] or item.get("lease_until")
                                or item["requires_approval"])
                       and all(self.index["tasks"][d]["status"] == "DONE_PUBLISHED"
                               for d in item["depends_on"]))
        self.assertEqual(result["total_eligible_tasks"], expected)
        self.assertGreaterEqual(result["total_eligible_tasks"], len(result["items"]))
        print("REAL_CENSUS_NEXT_TASKS", len(result["items"]),
              "total_eligible", result["total_eligible_tasks"])


if __name__ == "__main__":
    unittest.main()
