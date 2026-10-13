"""Offline proof of correct bounded GPT gateway and negative trust/ACL tests."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gateway import (retrieve, compact_fit, artifact_source_path, stable_relative)
from graph import build_index, canonical
from sections import build

CODE = Path(__file__).resolve().parents[1] / "gateway.py"


class GatewayTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "repo"
        self.control = self.root / "docs/research/apa-results/control"
        self.runs = self.root / "docs/research/apa-results/runs/2026-10-13"
        self.control.mkdir(parents=True)
        self.runs.mkdir(parents=True)
        self.a = self.control / "NORMATIVE_NOT_OFFICIAL.md"
        self.b = self.runs / "RESEARCH_NOT_PRIMARY.md"
        self.c = self.control / "WINDOW.md"
        self.a.write_text("# Кровли и расчёт\nКровли требуют точной проверки уклона и длины ската.\n", encoding="utf-8")
        self.b.write_text("# Исследование кровли\nКровли подробно обсуждались в исследовании.\n", encoding="utf-8")
        self.c.write_text("# Кровли и окно\nПримыкания кровли к окну описаны.\n", encoding="utf-8")
        def t(id, status, ids, deps=(), owner=None):
            return {"id": id, "title": "Task " + id, "status": status,
                    "priority": 1, "depends_on": list(deps), "related": [],
                    "inputs": ids, "evidence": [], "owner": owner, "claim_ref": None,
                    "requires_approval": False}
        self.plan = {
            "revision": 2,
            "tasks": {
                "APA-P50.A01.S01": t("APA-P50.A01.S01", "DONE_PUBLISHED", ["ART-CONTROL"]),
                "APA-P50.A01.S02": t("APA-P50.A01.S02", "READY", ["ART-CONTROL"], ["APA-P50.A01.S01"]),
                "APA-P50.A01.S03": t("APA-P50.A01.S03", "IN_PROGRESS", ["ART-RESEARCH"], owner="someone"),
                "APA-P50.A01.S04": t("APA-P50.A01.S04", "BLOCKED", ["ART-WINDOW"]),
            },
            "artifacts": {
                "ART-CONTROL": {"id": "ART-CONTROL", "kind": "DOCUMENT",
                                "verification": "READBACK_VERIFIED", "uri": self.a.relative_to(self.root).as_posix()},
                "ART-RESEARCH": {"id": "ART-RESEARCH", "kind": "DOCUMENT",
                                 "verification": "SOURCE_RESEARCH", "uri": self.b.relative_to(self.root).as_posix()},
                "ART-WINDOW": {"id": "ART-WINDOW", "kind": "DOCUMENT",
                               "verification": "NOT_VERIFIED", "uri": self.c.relative_to(self.root).as_posix()},
            }
        }
        self.index = build_index(self.plan)
        self.db = Path(self.tmp.name)/"sections.sqlite"
        build([self.root / "docs"], self.db)

    def call(self, q, mode="research", limit=4, budget=2600, source_class=None, ix=None, plan=None):
        return retrieve(ix or self.index, plan or self.plan, self.db, self.root,
                        "dvikt33-ux/safe-bim-layer", q, mode=mode, limit=limit,
                        max_chars=budget, source_class=source_class)

    def test_exact_task_uses_zero_documents_and_includes_status(self):
        r = self.call("APA-P50.A01.S02")
        self.assertEqual(r["retrieval"], "EXACT_TASK")
        self.assertEqual(r["items"][0]["status"], "READY")
        self.assertEqual(r["items"][0]["artifact_count"], 1)
        self.assertNotIn("excerpt", r["items"][0])

    def test_exact_artifact_is_reference_only(self):
        r = self.call("ART-CONTROL")
        self.assertEqual(r["retrieval"], "EXACT_ARTIFACT")
        self.assertEqual(r["items"][0]["task_reference_count"], 2)
        self.assertEqual(r["items"][0]["relation"], "REFERENCE_ONLY")

    def test_two_artifact_join_returns_shared_task_without_semantic_promotion(self):
        p = copy.deepcopy(self.plan)
        p["tasks"]["APA-P50.A01.S01"]["inputs"].append("ART-RESEARCH")
        ix = build_index(p)
        r = self.call("ART-CONTROL ART-RESEARCH", ix=ix, plan=p)
        self.assertEqual(r["retrieval"], "MULTI_ARTIFACT_GRAPH")
        self.assertEqual(r["task_refs_all"], 1)
        matches = [x for x in r["items"] if x.get("task_id") == "APA-P50.A01.S01"]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["relation"], "COMMON_TASK_REFERENCE_NOT_SEMANTIC_DEPENDENCY")
        self.assertEqual(r["unpinned_source_count"], 2)
        self.assertLessEqual(len(canonical(r)), 2600)
        small = self.call("ART-CONTROL ART-RESEARCH", ix=ix, plan=p, budget=1200)
        self.assertEqual(small["status"], "OK")
        self.assertTrue(any(item.get("task_id") == "APA-P50.A01.S01" for item in small["items"]),
                        "Must never omit the central cross-document relation just to show full URLs")
        self.assertTrue(all("uri" not in item for item in small["items"]))


    def test_multi_artifact_unknown_fails_closed(self):
        r = self.call("ART-CONTROL ART-NONEXISTENT")
        self.assertEqual(r["status"], "NOT_FOUND")
        self.assertEqual(r["retrieval"], "MULTI_ARTIFACT_GRAPH")

    def test_source_based_research_returns_bounded_multiple_docs(self):
        r = self.call("кровли", limit=4)
        self.assertEqual(r["retrieval"], "SECTION_SEARCH_PLUS_TASK_GRAPH")
        self.assertGreaterEqual(len(r["items"]), 2)
        self.assertEqual(len({c["source"] for c in r["items"]}), len(r["items"]))
        self.assertTrue(all(c["relationship"] == "LEXICAL_AND_EXPLICIT_REFERENCES_ONLY" for c in r["items"]))
        self.assertTrue(all(len(c["sha256"]) == 64 for c in r["items"]))
        self.assertTrue(all(not c["source"].startswith("/") for c in r["items"]))
        self.assertLessEqual(len(canonical(r)), 2600)

    def test_source_class_research_separated_from_project_control(self):
        r = self.call("кровли", source_class="PROJECT_CONTROL")
        self.assertTrue(r["items"])
        self.assertEqual({x["class"] for x in r["items"]}, {"PROJECT_CONTROL"})
        self.assertFalse(any("RESEARCH_NOT_PRIMARY" in x["source"] for x in r["items"]))

    def test_normative_mode_must_never_mark_official(self):
        r = self.call("кровли", mode="normative")
        self.assertEqual(r["status"], "NOT_VERIFIED_OFFICIAL_SOURCE")
        self.assertFalse(r["normative_authority"])
        self.assertTrue(all(x["source_legal_authority"] == "NOT_VERIFIED" for x in r["items"]))
        self.assertFalse(any(x["class"] == "RESEARCH_RUN" for x in r["items"]))

    def test_next_mode_only_suggests_existing_unclaimed_ready(self):
        r = self.call("кровли", mode="next", limit=4)
        cards = [x for x in r["items"] if x["artifact_ids"]]
        self.assertTrue(any("APA-P50.A01.S02" in x.get("eligible_tasks_not_claimed", []) for x in cards))
        self.assertFalse(any("APA-P50.A01.S03" in x.get("eligible_tasks_not_claimed", []) for x in cards))
        self.assertFalse(any("APA-P50.A01.S04" in x.get("eligible_tasks_not_claimed", []) for x in cards))

    def test_new_plan_invalidates_caches(self):
        modified = copy.deepcopy(self.plan)
        modified["tasks"]["APA-P50.A01.S02"]["status"] = "IN_PROGRESS"
        with self.assertRaisesRegex(ValueError, "STALE_INDEX"):
            self.call("кровли", plan=modified)

    def test_budget_fits_or_honestly_errors(self):
        r = self.call("кровли", limit=4, budget=780)
        self.assertLessEqual(len(canonical(r)), 780)
        self.assertIn(r["status"], ("OK", "BUDGET_TOO_SMALL"))
        if r["status"] == "OK":
            self.assertGreaterEqual(r["omitted"], 1)
        else:
            self.assertEqual(r["items"], [])

    def test_query_rejects_unbounded_budget(self):
        with self.assertRaisesRegex(ValueError, "max_chars"):
            self.call("кровли", budget=50000)

    def test_hostile_queries_are_data_not_executable(self):
        r = self.call('"; DROP TABLE sections; --')
        self.assertEqual(r["status"], "OK")
        self.assertEqual(r["items"], [])

    def test_git_url_pinning_does_not_guess_branch_slash(self):
        path, label = artifact_source_path(
            "https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/a/dir.md",
            "dvikt33-ux/safe-bim-layer")
        self.assertIsNone(path)
        self.assertEqual(label, "MOVING_OR_UNRESOLVED_REF")
        stable = "a"*40
        path,label = artifact_source_path(
            "https://github.com/dvikt33-ux/safe-bim-layer/blob/"+stable+"/docs/a.md",
            "dvikt33-ux/safe-bim-layer")
        self.assertEqual((path,label), ("docs/a.md", "COMMIT_PINNED_URI"))

    def test_repository_boundary_blocks_leak(self):
        external = Path(self.tmp.name)/"private.txt"
        external.write_text("secret")
        with self.assertRaisesRegex(ValueError, "SOURCE_PATH_OUTSIDE"):
            stable_relative(self.root, external)

    def test_source_mutation_aborts_not_returns_outdated_excerpts(self):
        self.a.write_text(self.a.read_text() + "\nChanged content.", encoding="utf-8")
        r = self.call("кровли", limit=4)
        self.assertEqual(r["status"], "STALE_INDEX")
        self.assertEqual(r["items"], [])

    def test_cli_roundtrip_compact(self):
        idxp = Path(self.tmp.name)/"index.json"
        pp = Path(self.tmp.name)/"plan.json"
        idxp.write_text(json.dumps(self.index), encoding="utf-8")
        pp.write_text(json.dumps(self.plan), encoding="utf-8")
        proc = subprocess.run([sys.executable, str(CODE),
            "--index", str(idxp), "--plan", str(pp),
            "--query", "APA-P50.A01.S02", "--max-chars", "800"],
            text=True,capture_output=True,check=True)
        self.assertEqual(json.loads(proc.stdout)["retrieval"], "EXACT_TASK")


if __name__ == "__main__":
    unittest.main()
