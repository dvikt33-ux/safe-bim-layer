import tempfile
import threading
import unittest
import json
import urllib.request
from pathlib import Path

from safe_bim_runtime import (
    JobStatus, ProjectMismatch, ResumableExecutor, SQLiteCheckpointStore, StepSpec,
)
from safe_bim_ipc import PaletteHTTPServer


PROJECT = r"C:\Users\Admin\Downloads\Test_House.pln"


class FakeOperations:
    def __init__(self):
        self.calls = 0
        self.project = PROJECT
        self.mode = "pass"
        self.reconciliation = {"classification": "APPLIED", "status": "PASS",
                               "readback": [{"guid": "wall-1"}]}

    def execute(self, operation, params):
        self.calls += 1
        if self.mode == "timeout":
            raise TimeoutError("applied but response blocked")
        if self.mode == "unknown":
            return {"status": "UNKNOWN_OUTCOME"}
        return {"status": "PASS", "readback": [{"operation": operation}]}

    def reconcile(self, operation, params, previous):
        return dict(self.reconciliation)


class ResumableExecutorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "runtime.sqlite3"
        self.ops = FakeOperations()
        self.store = SQLiteCheckpointStore(self.db)
        self.executor = ResumableExecutor(
            self.store, self.ops.execute, self.ops.reconcile, lambda: self.ops.project)

    def tearDown(self):
        self.tmp.cleanup()

    def create_job(self, job_id="job-1", count=1):
        self.store.create_job(job_id, "Тестовый дом", PROJECT, [
            StepSpec(f"Стена {i + 1}", "create_wall", {"n": i}, floor_index=1)
            for i in range(count)
        ])
        return job_id

    def test_active_selection_prefers_running_then_pending_then_history(self):
        self.create_job("old-done")
        self.executor.run("old-done")
        self.create_job("pending")
        self.create_job("running")
        self.store.set_job("running", JobStatus.RUNNING)
        self.assertEqual(self.executor.resolve_job_id("active"), "running")
        self.store.set_job("running", JobStatus.DONE)
        self.assertEqual(self.executor.resolve_job_id("active"), "pending")

    def test_palette_terminal_controls_and_history_fallback(self):
        self.create_job("done-job")
        self.executor.run("done-job")
        state = self.executor.palette_state("done-job")
        self.assertEqual(state["selection"], "history")
        self.assertFalse(state["controls"]["continue"])
        self.assertFalse(state["controls"]["pause"])
        self.assertFalse(state["controls"]["stop"])
        self.assertTrue(any(row["job_id"] == "done-job" for row in state["history"]))

    def test_persistence_survives_store_reopen(self):
        job_id = self.create_job()
        self.assertEqual(self.executor.run(job_id), JobStatus.DONE)
        reopened = SQLiteCheckpointStore(self.db).job(job_id)
        self.assertEqual(reopened["status"], "DONE")
        self.assertEqual(reopened["steps"][0]["status"], "DONE")
        self.assertEqual(reopened["steps"][0]["attempts"], 1)
        self.assertEqual(reopened["steps"][0]["checkpoint"]["phase"], "BEFORE_WRITE")

    def test_timeout_is_unknown_and_has_no_blind_retry(self):
        job_id = self.create_job()
        self.ops.mode = "timeout"
        self.assertEqual(self.executor.run(job_id), JobStatus.UNKNOWN_OUTCOME)
        self.assertEqual(self.ops.calls, 1)
        row = self.store.job(job_id)["steps"][0]
        self.assertEqual(row["attempts"], 1)
        self.assertFalse(row["result"]["retryAllowed"])

    def test_modal_state_waits_for_user_without_retry(self):
        job_id = self.create_job()
        class ModalError(RuntimeError):
            retry_allowed = False
        self.ops.execute = lambda *_: (_ for _ in ()).throw(ModalError("modal"))
        executor = ResumableExecutor(
            self.store, self.ops.execute, self.ops.reconcile, lambda: self.ops.project)
        self.assertEqual(executor.run(job_id), JobStatus.WAITING_USER)
        row = self.store.job(job_id)["steps"][0]
        self.assertEqual(row["status"], "WAITING_USER")
        self.assertFalse(row["result"]["retryAllowed"])

    def test_resume_reconciles_applied_without_redispatch(self):
        job_id = self.create_job()
        self.ops.mode = "timeout"
        self.executor.run(job_id)
        self.ops.mode = "pass"
        self.assertEqual(self.executor.resume(job_id), JobStatus.DONE)
        self.assertEqual(self.ops.calls, 1)

    def test_crash_after_checkpoint_reconciles_without_blind_retry(self):
        job_id = self.create_job()
        self.store.checkpoint_before_write(job_id, 0, {
            "operation": "create_wall", "params": {"n": 0}, "floorIndex": 1})
        reopened = ResumableExecutor(
            SQLiteCheckpointStore(self.db), self.ops.execute,
            self.ops.reconcile, lambda: PROJECT)
        self.assertEqual(reopened.resume(job_id), JobStatus.DONE)
        self.assertEqual(self.ops.calls, 0)

    def test_resume_retries_only_when_reconciliation_proves_not_applied(self):
        job_id = self.create_job()
        self.ops.mode = "timeout"
        self.executor.run(job_id)
        self.ops.mode = "pass"
        self.ops.reconciliation = {"classification": "NOT_APPLIED"}
        self.assertEqual(self.executor.resume(job_id), JobStatus.DONE)
        self.assertEqual(self.ops.calls, 2)

    def test_ambiguous_reconciliation_waits_for_user(self):
        job_id = self.create_job()
        self.ops.mode = "timeout"
        self.executor.run(job_id)
        self.ops.reconciliation = {"classification": "AMBIGUOUS"}
        self.assertEqual(self.executor.resume(job_id), JobStatus.WAITING_USER)
        self.assertEqual(self.ops.calls, 1)

    def test_pause_and_continue_at_safe_boundary(self):
        job_id = self.create_job()
        self.assertEqual(self.executor.pause(job_id), JobStatus.PAUSED)
        self.assertEqual(self.ops.calls, 0)
        self.assertEqual(self.executor.resume(job_id), JobStatus.DONE)
        self.assertEqual(self.ops.calls, 1)

    def test_stop_is_persistent_and_not_resumable(self):
        job_id = self.create_job()
        self.assertEqual(self.executor.stop(job_id), JobStatus.CANCELLED)
        reopened_executor = ResumableExecutor(
            SQLiteCheckpointStore(self.db), self.ops.execute,
            self.ops.reconcile, lambda: PROJECT)
        self.assertEqual(reopened_executor.resume(job_id), JobStatus.CANCELLED)
        self.assertEqual(self.ops.calls, 0)

    def test_project_identity_checked_before_run_and_resume(self):
        job_id = self.create_job()
        self.ops.project = r"C:\Other\Wrong.pln"
        with self.assertRaises(ProjectMismatch):
            self.executor.run(job_id)
        self.assertEqual(self.ops.calls, 0)
        self.ops.project = PROJECT
        self.ops.mode = "timeout"
        self.executor.run(job_id)
        self.ops.project = r"C:\Other\Wrong.pln"
        with self.assertRaises(ProjectMismatch):
            self.executor.resume(job_id)
        self.assertEqual(self.ops.calls, 1)

    def test_done_requires_readback(self):
        job_id = self.create_job()
        self.ops.execute = lambda *_: {"status": "PASS", "readback": []}
        executor = ResumableExecutor(
            self.store, self.ops.execute, self.ops.reconcile, lambda: PROJECT)
        self.assertEqual(executor.run(job_id), JobStatus.FAILED)

    def test_palette_active_alias_resolves_latest_job(self):
        job_id = self.create_job()
        state = self.executor.palette_state("active")
        self.assertEqual(state["job_id"], job_id)
        self.assertEqual(state["status"], "PENDING")

    def test_localhost_ipc_reports_state_and_pauses(self):
        job_id = self.create_job()
        server = PaletteHTTPServer(("127.0.0.1", 0), self.executor)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            port = server.server_address[1]
            with urllib.request.urlopen(
                    f"http://127.0.0.1:{port}/state?job_id=active", timeout=3) as response:
                state = json.loads(response.read().decode("utf-8"))
            self.assertEqual(state["job_id"], job_id)
            request = urllib.request.Request(
                f"http://127.0.0.1:{port}/jobs/active/pause", data=b"", method="POST")
            with urllib.request.urlopen(request, timeout=3) as response:
                result = json.loads(response.read().decode("utf-8"))
            self.assertEqual(result["status"], "PAUSED")
            self.assertEqual(self.store.job(job_id)["status"], "PAUSED")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
