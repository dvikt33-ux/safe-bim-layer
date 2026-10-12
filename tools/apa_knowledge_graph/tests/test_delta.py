"""Incremental value-level delta: false-negative safeguards and bounded results."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from graph import build_index
from delta import compare_plans, compare_field_snapshots


def sample():
    return {"revision":1,
            "artifacts":{"A1":{"id":"A1", "uri":"docs/input.md", "verification":"READBACK_VERIFIED"},
                         "A2":{"id":"A2", "uri":"docs/unused.md", "verification":"READBACK_VERIFIED"}},
            "tasks":{"S1":{"id":"S1", "title":"S1", "status":"DONE_PUBLISHED",
                           "depends_on":[], "related":[], "inputs":["A1"], "evidence":[]},
                     "S2":{"id":"S2", "title":"S2", "status":"READY",
                           "depends_on":["S1"], "related":[], "inputs":["A1"], "evidence":[]},
                     "S3":{"id":"S3", "title":"S3", "status":"READY",
                           "depends_on":[], "related":[], "inputs":["A2"], "evidence":[]}}}


def lineage():
    return {"schema":"APA_FIELD_LINEAGE_V1",
            "fields":{"source":{"project_class":"IZHS"},
                      "derived":{"project_class":"IZHS", "task_id":"S2"},
                      "irrelevant":{"project_class":"IZHS", "task_id":"S3"}},
            "edges":[{"from":"source", "to":"derived", "kind":"DERIVED_FROM",
                      "verification":"SOURCE_VERIFIED", "project_class":"IZHS",
                      "source_revision":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", "evidence_uri":"docs/field-ref"}]}


class DeltaTest(unittest.TestCase):
    def setUp(self):
        self.p = sample()
        self.ix = build_index(self.p)

    def test_same_plan_no_change(self):
        self.assertEqual(compare_plans(self.p, copy.deepcopy(self.p))["status"], "UNCHANGED")

    def test_exact_artifact_update_does_not_mark_all_tasks_affected(self):
        nxt = copy.deepcopy(self.p)
        nxt["artifacts"]["A1"]["uri"] = "docs/input-v2.md"
        nxt["revision"] += 1
        r = compare_plans(self.p, nxt)
        self.assertEqual(r["total_changed_records"], 1)
        self.assertEqual(r["changes"][0]["possibly_affected_tasks"], ["S1", "S2"])
        self.assertNotIn("S3", r["changes"][0]["possibly_affected_tasks"])
        self.assertEqual(r["changes"][0]["impact_kind"], "REFERENCE_CANDIDATES_NOT_PROVEN")

    def test_task_status_changes_only_scheduling(self):
        nxt = copy.deepcopy(self.p)
        nxt["tasks"]["S1"]["status"] = "PARTIAL"
        r = compare_plans(self.p, nxt)
        s = r["changes"][0]
        self.assertEqual(s["scheduling_dependents"], ["S2"])
        self.assertEqual(s["impact_kind"], "SCHEDULING_ONLY_NOT_SEMANTIC_IMPACT")

    def test_changed_field_affects_only_confirmed_downstream(self):
        before = {"schema":"APA_FIELD_VALUES_V1", "values":{"source":100, "derived":150, "irrelevant":5}}
        after = {"schema":"APA_FIELD_VALUES_V1", "values":{"source":101, "derived":150, "irrelevant":5}}
        r = compare_field_snapshots(self.ix, lineage(), before, after)
        self.assertEqual(r["total_changed_fields"], 1)
        impact = r["impacts"][0]["impact"]
        self.assertEqual([x["field_id"] for x in impact["verified_impacts"]], ["derived"])
        self.assertNotIn("irrelevant", [x["field_id"] for x in impact["verified_impacts"]])

    def test_missing_value_does_not_claim_unaffected(self):
        a = {"schema":"APA_FIELD_VALUES_V1", "values":{"source":1}}
        b = {"schema":"APA_FIELD_VALUES_V1", "values":{"source":1, "new":2}}
        r = compare_field_snapshots(self.ix, lineage(), a, b)
        self.assertEqual(r["status"], "COVERAGE_CHANGED")
        self.assertEqual(r["missing_in_before"], ["new"])

    def test_unknown_field_is_reported_not_ignored(self):
        a = {"schema":"APA_FIELD_VALUES_V1", "values":{"unknown":1}}
        b = {"schema":"APA_FIELD_VALUES_V1", "values":{"unknown":2}}
        r = compare_field_snapshots(self.ix, lineage(), a, b)
        self.assertEqual(r["impacts"][0]["status"], "FIELD_NOT_IN_LINEAGE")

    def test_changed_value_output_has_hard_cap(self):
        a = {"schema":"APA_FIELD_VALUES_V1", "values":{"source":"x"*500, "derived":1, "irrelevant":1}}
        b = {"schema":"APA_FIELD_VALUES_V1", "values":{"source":"y"*500, "derived":1, "irrelevant":1}}
        r = compare_field_snapshots(self.ix, lineage(), a, b, limit=1)
        self.assertEqual(r["impacts"][0]["before"]["value"], "TOO_LONG")

    def test_delta_cli_plan_mode(self):
        with tempfile.TemporaryDirectory() as d:
            old, new = Path(d)/"old.json", Path(d)/"new.json"
            old.write_text(json.dumps(self.p), encoding="utf-8")
            nxt = copy.deepcopy(self.p)
            nxt["artifacts"]["A1"]["uri"] = "docs/new.md"
            new.write_text(json.dumps(nxt), encoding="utf-8")
            proc = subprocess.run([sys.executable, str(Path(__file__).resolve().parents[1]/"delta.py"),
                                   "plan", "--before",str(old),"--after",str(new)],
                                  check=True, text=True, capture_output=True)
            self.assertEqual(json.loads(proc.stdout)["total_changed_records"], 1)


if __name__ == "__main__":
    unittest.main()
