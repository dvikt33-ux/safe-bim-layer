"""Offline test suite: read-only APA graph, anti-false-impact and compact retrieval."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from graph import (build_index, task_card, artifact_impact, field_impact, task_descendants,
                   validate_lineage, fingerprint, validate_plan)

SCRIPT = Path(__file__).resolve().parents[1] / "graph.py"
REAL_PLAN = Path(__file__).resolve().parents[3] / "docs/research/apa-results/control/PROJECT_PLAN.json"


def task(sid, status, deps=(), inputs=(), priority=1, owner=None):
    return {"id": sid, "title": "Test " + sid, "status": status, "priority": priority,
            "depends_on": list(deps), "related": [], "inputs": list(inputs),
            "evidence": [], "owner": owner, "claim_ref": None, "requires_approval": False}


def plan():
    return {
        "revision": 12,
        "tasks": {
            "S1": task("S1", "DONE_PUBLISHED", inputs=["A1"]),
            "S2": task("S2", "READY", deps=["S1"], inputs=["A1"]),
            "S3": task("S3", "READY", deps=["S2"], inputs=["A2"]),
            "S4": task("S4", "READY", deps=["S1"], inputs=["A3"]),
            "S5": task("S5", "IN_PROGRESS", deps=["S1"], owner="other-agent", inputs=["A1"]),
        },
        "artifacts": {k: {"id": k, "uri": "path/" + k, "kind": "DOCUMENT",
                          "verification": "READBACK_VERIFIED"} for k in ("A1", "A2", "A3")},
    }


def fields():
    return {
        "schema": "APA_FIELD_LINEAGE_V1",
        "fields": {
            "area": {"project_class": "IZHS"},
            "calc": {"project_class": "IZHS", "task_id": "S2"},
            "check": {"project_class": "IZHS", "task_id": "S3"},
            "other": {"project_class": "IZHS", "task_id": "S4"},
        },
        "edges": [
            {"from": "area", "to": "calc", "kind": "USES_PARAMETER",
             "verification": "SOURCE_VERIFIED", "project_class": "IZHS",
             "source_revision": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "evidence_uri": "file#area"},
            {"from": "calc", "to": "check", "kind": "DERIVED_FROM",
             "verification": "SOURCE_VERIFIED", "project_class": "IZHS",
             "source_revision": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "evidence_uri": "file#check"},
            {"from": "area", "to": "other", "kind": "REFERENCES",
             "verification": "SOURCE_VERIFIED", "project_class": "IZHS",
             "source_revision": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "evidence_uri": "file#mention"},
        ]
    }


class GraphTest(unittest.TestCase):
    def setUp(self):
        self.source = plan()
        self.before = copy.deepcopy(self.source)
        self.index = build_index(self.source)

    def test_exact_and_small_card(self):
        card = task_card(self.index, "S2")
        self.assertEqual(card["status"], "READY")
        self.assertEqual(card["artifact_count"], 1)
        self.assertLess(len(json.dumps(card)), len(json.dumps(self.source)))
        self.assertNotIn("artifacts", card)

    def test_unknown_identifier(self):
        self.assertEqual(task_card(self.index, "MISSING")["status"], "NOT_FOUND")
        self.assertEqual(artifact_impact(self.index, "MISSING")["status"], "NOT_FOUND")

    def test_artifact_ref_is_not_verified_impact(self):
        r = artifact_impact(self.index, "A1")
        self.assertEqual(r["total_candidates"], 3)
        self.assertEqual({x["impact"] for x in r["results"]}, {"POSSIBLE_IMPACT"})
        self.assertEqual(r["field_lineage_coverage"], "UNKNOWN")

    def test_bounded_limit_reports_omitted(self):
        r = artifact_impact(self.index, "A1", limit=1)
        self.assertEqual(len(r["results"]), 1)
        self.assertEqual(r["omitted"], 2)

    def test_scheduling_edges_not_field_impacts(self):
        r = task_descendants(self.index, "S1")
        self.assertEqual({x["id"] for x in r["results"]}, {"S2", "S3", "S4", "S5"})
        self.assertEqual(r["relation_kind"], "SCHEDULING_ONLY_NOT_PROVEN_DATA_IMPACT")

    def test_explicit_verified_field_lineage_only(self):
        result = field_impact(self.index, fields(),
                              {"field_id": "area", "project_class": "IZHS", "before": 35, "after": 42})
        self.assertEqual({x["field_id"] for x in result["verified_impacts"]}, {"calc", "check"})
        self.assertEqual({x["field_id"] for x in result["review_required"]}, {"other"})
        self.assertEqual(result["potential_next_tasks_not_claimed"], ["S2"])
        self.assertFalse(result["no_impact_proven"])

    def test_no_change_no_propagation(self):
        result = field_impact(self.index, fields(),
                              {"field_id": "area", "project_class": "IZHS", "before": 42, "after": 42})
        self.assertEqual(result["status"], "NO_VALUE_CHANGE")

    def test_cross_class_cannot_propagate(self):
        lineage = fields()
        lineage["fields"]["other"]["project_class"] = "MKD"
        with self.assertRaisesRegex(ValueError, "Cross-class"):
            field_impact(self.index, lineage,
                          {"field_id": "area", "project_class": "IZHS", "before": 1, "after": 2})
        self.assertEqual(field_impact(self.index, fields(),
                            {"field_id": "area", "project_class": "TRC", "before": 1, "after": 2})["status"],
                            "SCOPE_MISMATCH")

    def test_proposed_edge_never_proves_downstream(self):
        lineage = fields()
        lineage["edges"][0]["verification"] = "PROPOSED"
        result = field_impact(self.index, lineage,
                              {"field_id": "area", "project_class": "IZHS", "before": 1, "after": 2})
        self.assertEqual(result["verified_relation_count"], 0)
        self.assertEqual(result["review_required_count"], 2)

    def test_verified_edge_must_have_evidence(self):
        lineage = fields()
        del lineage["edges"][0]["evidence_uri"]
        with self.assertRaisesRegex(ValueError, "source_revision and evidence_uri"):
            validate_lineage(lineage, self.index)

    def test_cycle_terminates(self):
        lineage = fields()
        lineage["edges"].append({"from": "check", "to": "area", "kind": "DERIVED_FROM",
                                "verification": "SOURCE_VERIFIED", "project_class": "IZHS",
                                "source_revision": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "evidence_uri": "file#cycle"})
        r = field_impact(self.index, lineage, {"field_id": "area", "project_class": "IZHS",
                                                "before": 1, "after": 2})
        self.assertEqual(r["verified_relation_count"], 2)

    def test_reject_dangling_plan_ids(self):
        broken = plan()
        broken["tasks"]["S2"]["inputs"].append("MISSING")
        with self.assertRaisesRegex(ValueError, "Dangling artifact"):
            validate_plan(broken)

    def test_input_plan_is_never_mutated(self):
        field_impact(self.index, fields(),
                     {"field_id": "area", "project_class": "IZHS", "before": 1, "after": 2})
        self.assertEqual(self.source, self.before)
        self.assertEqual(self.index, build_index(self.source))

    def test_rebuild_is_deterministic_and_fingerprint_changes(self):
        self.assertEqual(fingerprint(self.index), fingerprint(build_index(plan())))
        changed = plan()
        changed["tasks"]["S2"]["title"] = "Changed title"
        self.assertNotEqual(build_index(changed)["plan_sha256"], self.index["plan_sha256"])

    def test_cli_roundtrip_without_plan_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            src, idx = Path(d) / "plan.json", Path(d) / "index.json"
            src.write_text(json.dumps(self.source), encoding="utf-8")
            original = src.read_bytes()
            cmd = [sys.executable, str(SCRIPT), "build", "--plan", str(src), "--out", str(idx)]
            proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
            self.assertIn("DERIVED_INDEX_WRITTEN", proc.stdout)
            self.assertEqual(src.read_bytes(), original)
            q = subprocess.run([sys.executable, str(SCRIPT), "artifact", "--index", str(idx),
                                "--id", "A1", "--limit", "2"],
                               capture_output=True, text=True, check=True)
            self.assertEqual(json.loads(q.stdout)["omitted"], 1)

    def test_cli_refuses_overwriting_authoritative_plan(self):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "plan.json"
            src.write_text(json.dumps(self.source), encoding="utf-8")
            proc = subprocess.run([sys.executable, str(SCRIPT), "build", "--plan", str(src),
                                    "--out", str(src)], capture_output=True, text=True)
            self.assertNotEqual(proc.returncode, 0)
            self.assertEqual(json.loads(src.read_text()), self.source)

    @unittest.skipUnless(REAL_PLAN.is_file(), "Current APA canonical plan not in local checkout")
    def test_real_plan_regression(self):
        real = json.loads(REAL_PLAN.read_text(encoding="utf-8"))
        index = build_index(real)
        self.assertGreaterEqual(len(index["tasks"]), 91)
        self.assertGreaterEqual(len(index["artifacts"]), 166)
        if real.get("revision") == 125:
            self.assertEqual(len(index["artifact_to_tasks"]["ART-APA-RU-JUNCTION-NORMS"]), 15)
            self.assertEqual(task_card(index, "APA-P70.A11.S03")["status"], "PARTIAL")
        self.assertEqual(index["authority"], "DERIVED_READ_ONLY")


if __name__ == "__main__":
    unittest.main()
