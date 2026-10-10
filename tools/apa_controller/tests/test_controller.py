"""Offline regression tests for the authoritative APA project manager."""
import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import controller as c

SOURCE_PLAN = (Path(__file__).resolve().parents[3] /
               "docs/research/apa-results/control/PROJECT_PLAN.json")


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.original_cwd = Path.cwd()
        os.chdir(self.temp.name)
        self.root = Path("docs/research/apa-results")
        self.plan_path = self.root / "control/PROJECT_PLAN.json"
        self.plan_path.parent.mkdir(parents=True)
        self.plan_path.write_bytes(SOURCE_PLAN.read_bytes())
        self.patcher = patch.multiple(
            c, ROOT=self.root, PLAN=self.plan_path,
            GENERATED=self.root / "control/generated",
            RUNS=self.root / "runs", RECEIPTS=self.root / "receipts",
            INBOX=self.root / "inbox", PENDING=Path(".apa-controller-pending.json"))
        self.patcher.start()
        self.plan = c.load()

    def tearDown(self):
        self.patcher.stop()
        os.chdir(self.original_cwd)
        self.temp.cleanup()

    def test_all_real_plan_tasks_valid(self):
        self.assertGreaterEqual(len(self.plan["tasks"]), 50)
        self.assertGreaterEqual(len(self.plan["plans"]), 7)
        self.assertGreaterEqual(len(self.plan["artifacts"]), 24)
        self.assertGreaterEqual(len(self.plan["topics"]), 15)

    def test_dispatch_and_generated_state_idempotent(self):
        state = c.build(self.plan)
        self.assertGreater(state["counts"]["DISPATCHABLE_NOW"], 0)
        self.assertIn("APA-P10.A01.S01", state["dispatchable"]["RESEARCH"])
        self.assertNotIn("APA-P40.A01.S04", sum(state["dispatchable"].values(), []))
        self.assertEqual(state["research_runner_24h"], "NOT_RUNNING")
        first = {p.name: p.read_bytes() for p in c.GENERATED.iterdir()}
        second = c.build(self.plan)
        self.assertEqual(state, second)
        self.assertEqual(first, {p.name: p.read_bytes() for p in c.GENERATED.iterdir()})

    def test_development_board_and_aggregate_progress(self):
        state = c.build(self.plan)
        self.assertEqual(state["development"]["plan_id"], "APA-P70")
        self.assertEqual(state["development"]["total"], 23)
        self.assertEqual(state["development"]["done"], 0)
        self.assertEqual(state["development"]["next_eligible"], "APA-P70.A01.S01")
        board = (c.GENERATED / "DEVELOPMENT_BOARD.md").read_text(encoding="utf-8")
        handoff = (c.GENERATED / "HANDOFF.md").read_text(encoding="utf-8")
        self.assertIn("APA-P70.A01 —", board)
        self.assertIn("APA-P70.A08.S03", board)
        self.assertIn("DEVELOPMENT_BOARD.md", handoff)
        self.assertNotEqual(state["development"]["status"], "DONE_PUBLISHED")
        all_done = copy.deepcopy(self.plan)
        for task in all_done["tasks"].values():
            if task["plan_id"] == "APA-P70":
                task["status"] = "DONE_PUBLISHED"
                task["evidence"] = ["ART-APA-FULL-CYCLE"]
        c.validate(all_done)
        finished = c.build(all_done)
        self.assertEqual(finished["development"]["status"], "DONE_PUBLISHED")
        self.assertEqual(finished["development"]["done"], 23)
        self.assertTrue(all(a["status"] == "DONE_PUBLISHED"
                            for a in finished["development"]["actions"]))

    def test_approval_required_is_not_dispatchable(self):
        plan = copy.deepcopy(self.plan)
        t = plan["tasks"]["APA-P70.A03.S02"]
        t["depends_on"] = []
        self.assertTrue(t["requires_approval"])
        c.validate(plan)
        self.assertFalse(c.eligible(t, plan))
        t["requires_approval"] = False
        self.assertTrue(c.eligible(t, plan))

    def test_research_routes_link_every_product_task(self):
        self.assertEqual(len(self.plan["research_routes"]), 23)
        self.assertEqual(set(self.plan["research_routes"]),
                         {sid for sid, t in self.plan["tasks"].items()
                          if t["plan_id"] == "APA-P70"})
        state = c.build(self.plan)
        self.assertEqual(state["research_lookahead"]["linked_product_substeps"], 23)
        self.assertIsNotNone(state["research_lookahead"]["next_target"])
        self.assertTrue(state["research_lookahead"]["next_eligible_research"])
        board = (c.GENERATED / "RESEARCH_LOOKAHEAD.md").read_text(encoding="utf-8")
        self.assertIn("APA-P70.A08.S03", board)
        self.assertIn("ART-APA-FULL-CYCLE", board)
        dev_board = (c.GENERATED / "DEVELOPMENT_BOARD.md").read_text(encoding="utf-8")
        self.assertIn("Источники/ветки:", dev_board)

    def test_research_routes_reject_orphans_and_false_sufficient(self):
        plan = copy.deepcopy(self.plan)
        del plan["research_routes"]["APA-P70.A01.S01"]
        with self.assertRaisesRegex(c.ControllerError, "UNMAPPED_PRODUCT_RESEARCH"):
            c.validate(plan)
        plan = copy.deepcopy(self.plan)
        route = plan["research_routes"]["APA-P70.A01.S01"]
        route["readiness"] = "SUFFICIENT"
        with self.assertRaisesRegex(c.ControllerError, "UNPROVEN_RESEARCH_SUFFICIENT"):
            c.validate(plan)
        route["readiness_evidence_ids"] = ["ART-APA-FULL-CYCLE"]
        c.validate(plan)
        plan = copy.deepcopy(self.plan)
        plan["research_routes"]["APA-P70.A01.S01"]["research_task_ids"] = ["APA-P99.A99.S99"]
        with self.assertRaisesRegex(c.ControllerError, "UNKNOWN_RESEARCH_TASK"):
            c.validate(plan)

    def test_cycle_rejected(self):
        plan = copy.deepcopy(self.plan)
        plan["tasks"]["APA-P00.A02.S02"]["depends_on"] = ["APA-P60.A01.S01"]
        with self.assertRaisesRegex(c.ControllerError, "DEPENDENCY_CYCLE"):
            c.validate(plan)

    def test_duplicate_topic_membership_rejected(self):
        plan = copy.deepcopy(self.plan)
        plan["topics"]["SDK_NATIVE"]["task_ids"].append("APA-P10.A02.S01")
        with self.assertRaisesRegex(c.ControllerError, "DUPLICATE_TOPIC_MEMBERSHIP"):
            c.validate(plan)

    def test_unmapped_topic_task_rejected(self):
        plan = copy.deepcopy(self.plan)
        plan["topics"]["SDK_NATIVE"]["task_ids"].remove("APA-P10.A01.S01")
        with self.assertRaisesRegex(c.ControllerError, "UNMAPPED_TASK_TOPIC"):
            c.validate(plan)

    def test_duplicate_work_key_rejected(self):
        plan = copy.deepcopy(self.plan)
        plan["tasks"]["APA-P10.A02.S01"]["work_key"] = \
            plan["tasks"]["APA-P10.A01.S01"]["work_key"]
        with self.assertRaisesRegex(c.ControllerError, "DUPLICATE_WORK_KEY"):
            c.validate(plan)

    def test_claim_and_expired_lease(self):
        plan = copy.deepcopy(self.plan)
        task = plan["tasks"]["APA-P10.A01.S02"]
        task.update(status="CLAIMED", owner="chatgpt-worker-1",
                    lease_until="2020-01-01T00:00:00Z",
                    claim_ref="https://github.com/dvikt33-ux/safe-bim-layer/commit/" + "a" * 40)
        c.validate(plan)
        state = c.build(plan)
        self.assertIn(task["id"], state["expired_leases"])
        self.assertNotIn(task["id"], state["dispatchable"]["RESEARCH"])

    def test_unclaimed_active_rejected(self):
        plan = copy.deepcopy(self.plan)
        plan["tasks"]["APA-P10.A02.S01"]["status"] = "CLAIMED"
        with self.assertRaisesRegex(c.ControllerError, "UNCLAIMED_ACTIVE"):
            c.validate(plan)

    def test_unknown_inbox_task_rejected(self):
        c.INBOX.mkdir(parents=True)
        path = c.INBOX / "APA-RUN-20261010-104437Z-invalid.json"
        path.write_text(json.dumps({"substep_id": "APA-P99.A99.S99",
                                    "run_id": "APA-RUN-20261010-104437Z-invalid"}))
        with self.assertRaisesRegex(c.ControllerError, "ORPHAN_INBOX_TASK"):
            c.verify_inbox(self.plan)

    def test_new_inbox_must_be_claimed_and_owned(self):
        c.INBOX.mkdir(parents=True)
        run_id = "APA-RUN-20261010-104437Z-new-unclaimed"
        path = c.INBOX / (run_id + ".json")
        payload = {"run_id": run_id, "substep_id": "APA-P10.A02.S01",
                   "plan_id": "APA-P10", "action_id": "APA-P10.A02",
                   "executor": "chatgpt-worker-1", "phase": "SOURCE"}
        path.write_text(json.dumps(payload))
        with self.assertRaisesRegex(c.ControllerError, "NOT_IN_PROGRESS"):
            c.verify_inbox(self.plan)
        plan = copy.deepcopy(self.plan)
        plan["tasks"]["APA-P10.A02.S01"].update(
            status="CLAIMED", owner="chatgpt-worker-1",
            lease_until="2099-01-01T00:00:00Z", claim_ref="scheduled-run-1")
        c.validate(plan)
        with self.assertRaisesRegex(c.ControllerError, "NOT_IN_PROGRESS"):
            c.verify_inbox(plan)
        plan["tasks"]["APA-P10.A02.S01"]["status"] = "IN_PROGRESS"
        payload["executor_run_id"] = "scheduled-run-1"
        path.write_text(json.dumps(payload))
        c.validate(plan)
        c.verify_inbox(plan)
        payload["executor"] = "wrong-worker"
        path.write_text(json.dumps(payload))
        with self.assertRaisesRegex(c.ControllerError, "CLAIM_OWNER_MISMATCH"):
            c.verify_inbox(plan)
        payload["executor"] = "chatgpt-worker-1"
        payload["executor_run_id"] = "wrong-run"
        path.write_text(json.dumps(payload))
        with self.assertRaisesRegex(c.ControllerError, "RUN_ID_MISMATCH"):
            c.verify_inbox(plan)

    def test_expired_run_cannot_publish(self):
        c.INBOX.mkdir(parents=True)
        rid = "APA-RUN-20261010-104437Z-expired"
        sid = "APA-P10.A02.S01"
        (c.INBOX / (rid + ".json")).write_text(json.dumps(
            {"run_id": rid, "substep_id": sid, "plan_id": "APA-P10",
             "action_id": "APA-P10.A02", "executor": "worker-1",
             "executor_run_id": "scheduled-expired", "phase": "SOURCE"}))
        plan = copy.deepcopy(self.plan)
        plan["tasks"][sid].update(
            status="IN_PROGRESS", owner="worker-1",
            lease_until="2020-01-01T00:00:00Z", claim_ref="scheduled-expired")
        c.validate(plan)
        with self.assertRaisesRegex(c.ControllerError, "CLAIM_LEASE_EXPIRED"):
            c.verify_inbox(plan)

    def test_duplicate_active_execution_id_rejected(self):
        plan = copy.deepcopy(self.plan)
        for sid in ("APA-P10.A01.S01", "APA-P10.A02.S01"):
            plan["tasks"][sid].update(
                status="IN_PROGRESS", owner="worker-1",
                lease_until="2099-01-01T00:00:00Z", claim_ref="same-scheduled-run")
        with self.assertRaisesRegex(c.ControllerError, "DUPLICATE_ACTIVE_RUN"):
            c.validate(plan)

    def test_unfinished_dependency_blocks_new_run(self):
        c.INBOX.mkdir(parents=True)
        rid = "APA-RUN-20261010-104437Z-dependency"
        sid = "APA-P10.A03.S01"
        (c.INBOX / (rid + ".json")).write_text(json.dumps(
            {"run_id": rid, "substep_id": sid, "plan_id": "APA-P10",
             "action_id": "APA-P10.A03", "executor": "worker-1",
             "executor_run_id": "scheduled-dependency", "phase": "SOURCE"}))
        plan = copy.deepcopy(self.plan)
        plan["tasks"][sid].update(
            status="IN_PROGRESS", owner="worker-1",
            lease_until="2099-01-01T00:00:00Z", claim_ref="scheduled-dependency")
        c.validate(plan)
        with self.assertRaisesRegex(c.ControllerError, "CLAIM_DEPENDENCY_NOT_DONE"):
            c.verify_inbox(plan)

    def test_existing_published_inbox_is_allowed_after_completion(self):
        c.INBOX.mkdir(parents=True)
        run_id = "APA-RUN-20261010-104437Z-publisher-integration-smoke"
        payload = {"run_id": run_id, "substep_id": "APA-P00.A03.S04",
                   "plan_id": "APA-P00", "action_id": "APA-P00.A03"}
        (c.INBOX / (run_id + ".json")).write_text(json.dumps(payload))
        folder = c.RUNS / "2026-10-10" / run_id
        folder.mkdir(parents=True)
        (folder / "manifest.json").write_text(json.dumps(
            {"schema": "APA_RUN_EVENT_V2", "run_id": run_id,
             "substep_id": "APA-P00.A03.S04"}))
        c.verify_inbox(self.plan)
        receipt_path = c.RECEIPTS / (run_id + ".json")
        receipt_path.parent.mkdir(parents=True)
        receipt_path.write_text(json.dumps(
            {"run_id": run_id, "status": "DONE_PUBLISHED",
             "readback_verified": True, "indexed": True}))
        state = c.build(self.plan)
        self.assertEqual(state["known_published_v2_runs"], 1)

    def test_blocked_never_dispatches(self):
        plan = copy.deepcopy(self.plan)
        task = plan["tasks"]["APA-P40.A01.S01"]
        task["depends_on"] = []
        c.validate(plan)
        self.assertFalse(c.eligible(task, plan))


if __name__ == "__main__":
    unittest.main()
