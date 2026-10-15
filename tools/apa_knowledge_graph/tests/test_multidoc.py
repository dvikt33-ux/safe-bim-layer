"""Tests for bounded evidence joins across multiple actual APA artifact identities."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from graph import build_index
from multidoc import document_bundle

SCRIPT = Path(__file__).resolve().parents[1] / "multidoc.py"
REAL_PLAN = Path(__file__).resolve().parents[3] / "docs/research/apa-results/control/PROJECT_PLAN.json"


class MultiDocTest(unittest.TestCase):
    def setUp(self):
        plan = {
            "tasks": {
                "S1": {"id":"S1", "status":"DONE_PUBLISHED", "title":"S1", "inputs":["A1","A2"],
                       "evidence":[], "depends_on":[], "related":[]},
                "S2": {"id":"S2", "status":"READY", "title":"S2", "inputs":["A1"],
                       "evidence":[], "depends_on":[], "related":[]},
                "S3": {"id":"S3", "status":"READY", "title":"S3", "inputs":["A3"],
                       "evidence":[], "depends_on":[], "related":[]},
            },
            "artifacts": {
                "A1":{"id":"A1", "uri":"docs/a1.md", "verification":"READBACK_VERIFIED"},
                "A2":{"id":"A2", "uri":"docs/a2.md", "verification":"NOT_VERIFIED"},
                "A3":{"id":"A3", "uri":"docs/a3.md", "verification":"NOT_VERIFIED"},
            },
            "revision": 10,
        }
        self.index = build_index(plan)

    def test_join_dedup_and_shared(self):
        result = document_bundle(self.index, ["A1", "A2", "A1"])
        self.assertEqual(result["tasks_with_any_reference"], 2)
        self.assertEqual(result["tasks_referencing_all"], 1)
        self.assertEqual(result["tasks"][0]["task_id"], "S1")
        self.assertEqual(result["tasks"][0]["shared_artifact_count"], 2)
        self.assertEqual(result["verification"], "REFERENCES_ONLY_NOT_FIELD_LINEAGE")

    def test_join_unrelated_sources(self):
        result = document_bundle(self.index, ["A1", "A3"])
        self.assertEqual(result["tasks_referencing_all"], 0)
        self.assertEqual(result["tasks_with_any_reference"], 3)

    def test_missing_artifact_fails_closed(self):
        result = document_bundle(self.index, ["A1", "MISSING"])
        self.assertEqual(result["status"], "NOT_FOUND")

    def test_max_tasks_is_bounded_and_reports_omitted(self):
        result = document_bundle(self.index, ["A1", "A2"], max_tasks=1)
        self.assertEqual(len(result["tasks"]), 1)
        self.assertEqual(result["omitted_task_count"], 1)

    def test_unpinned_sources_never_claim_sha_proof(self):
        result = document_bundle(self.index, ["A1", "A2"])
        self.assertEqual(result["source_revision_warnings"], ["A1", "A2"])
        self.assertTrue(all(x["revision"] == "UNPINNED_OR_UNVERIFIED_URI" for x in result["source_artifacts"]))

    def test_cli_works_on_small_index(self):
        with tempfile.TemporaryDirectory() as d:
            fp = Path(d) / "index.json"
            fp.write_text(json.dumps(self.index), encoding="utf-8")
            proc = subprocess.run([sys.executable, str(SCRIPT), "--index", str(fp),
                                    "--artifacts", "A1", "A2", "--max-tasks", "1"],
                                   check=True, capture_output=True, text=True)
            self.assertEqual(json.loads(proc.stdout)["omitted_task_count"], 1)

    @unittest.skipUnless(REAL_PLAN.exists(), "Canonical plan missing from checkout")
    def test_real_apa_two_artifact_join(self):
        p = json.loads(REAL_PLAN.read_text(encoding="utf-8"))
        idx = build_index(p)
        result = document_bundle(idx, ["ART-APA-RU-JUNCTION-NORMS",
                                       "ART-APA-CSE-RESEARCH"], max_tasks=5)
        self.assertEqual(result["status"], "OK")
        self.assertGreater(result["tasks_with_any_reference"], 0)
        self.assertLessEqual(len(result["tasks"]), 5)


if __name__ == "__main__":
    unittest.main()
