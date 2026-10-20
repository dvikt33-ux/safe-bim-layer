"""Проверки единой очереди, независимости чатов и квитанций без реальной Opera."""
import base64
from datetime import datetime, timedelta, timezone
from pathlib import Path
import hashlib
import json
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import bureau_unified_service as service


def stamp(value):
    return value.strftime("%Y-%m-%dT%H:%M:%SZ")


def event(name, target="D-03", typ="ASSIGN_TASK"):
    current = datetime.now(timezone.utc)
    return {
        "schema": "BUREAU_JOB_V2", "jobId": name, "eventType": typ,
        "targetChat": target, "action": "DELIVER_TASK",
        "createdAt": stamp(current - timedelta(minutes=2)),
        "expiresAt": stamp(current + timedelta(days=2)),
        "taskRef": {
            "path": f"safe-bim-mailbox/bureau/tasks/{name}.json",
            "blobSha": "a" * 40
        },
        "parentJobId": None
    }


class UnifiedServiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        path = Path(self.tmp.name)
        self.opera = path / "opera.exe"
        self.opera.touch()
        self.config = {
            "operaExe": str(self.opera),
            "extensionId": "a" * 32,
            "pollSeconds": 5, "callbackPort": 18765,
            "targets": {
                "D-03": {"workflowId": "workflow_d03"},
                "D-04": {"workflowId": "workflow_d04"},
                "DIR-03": {"workflowId": "workflow_dir03"},
                "SECRETARIAT": {"workflowId": "workflow_secretary"},
                "HQ": {"workflowId": "workflow_headquarters"}
            },
            "routes": {
                "D-03": {"REPORT_READY": "DIR-03"},
                "DIR-03": {"DEPARTMENT_REPORT_READY": "SECRETARIAT"},
                "SECRETARIAT": {"HQ_BRIEF_READY": "HQ"}
            },
            "apaEnabled": False, "apaBridgePath": "",
            "apaBridgeSha256": ""
        }
        self.db = service.open_db(path / "queue.sqlite")
        self.addCleanup(self.db.close)
        self.opened = []
        self.c = service.Coordinator(
            self.config, self.db,
            lambda exe, url: self.opened.append(url)
        )

    def enqueue(self, job_id, target="D-03", event_type="ASSIGN_TASK"):
        current = datetime.now(timezone.utc)
        self.c.record({
            "id": job_id, "target": target, "event_type": event_type,
            "action": "DELIVER_TASK",
            "task": {"schema": "BUREAU_TASK_V1", "jobId": job_id,
                     "instruction": "Проведи исследование по заданию."},
            "parent": None,
            "created": (current-timedelta(minutes=1)).isoformat(),
            "expires": (current+timedelta(days=2)).isoformat()
        }, hashlib.sha1(job_id.encode()).hexdigest())

    def launch(self):
        return self.c.launch_one()

    def token(self, job_id):
        return self.db.execute(
            "SELECT nonce FROM jobs WHERE id=?", (job_id,)
        ).fetchone()[0]

    def test_v2_contract_rejects_remote_text_and_wrong_target(self):
        ev = event("assign-001")
        ev["instruction"] = "Remote injected instruction"
        with self.assertRaisesRegex(ValueError, "JOB_V2_NOT_AUTHORIZED"):
            service.validate_event(ev, ev["jobId"], self.config)
        ev.pop("instruction")
        ev["targetChat"] = "D-99"
        with self.assertRaisesRegex(ValueError, "JOB_V2_NOT_AUTHORIZED"):
            service.validate_event(ev, ev["jobId"], self.config)

    def test_source_task_is_sha_pinned(self):
        ev = event("assign-002")
        content = {"schema": "BUREAU_TASK_V1", "jobId": "assign-002",
                   "instruction": "Проведи независимое исследование."}
        with patch.object(service, "checked_remote", return_value=content) as fetch:
            validated = service.validate_event(ev, "assign-002", self.config)
            self.assertEqual(validated["task"], content)
            fetch.assert_called_once_with(ev["taskRef"]["path"], "a"*40)

    def test_dedup_and_immutable_job(self):
        self.enqueue("assign-003")
        ev = {
            "id": "assign-003", "target": "D-03", "event_type": "ASSIGN_TASK",
            "action": "DELIVER_TASK", "task": {}, "parent": None,
            "created": service.now_iso(), "expires": service.now_iso()
        }
        old = self.db.execute(
            "SELECT blob_sha FROM jobs WHERE id='assign-003'"
        ).fetchone()[0]
        self.assertEqual(self.c.record(ev, old), "DUPLICATE")
        with self.assertRaisesRegex(ValueError, "IMMUTABLE_JOB_REWRITTEN"):
            self.c.record(ev, "b"*40)

    def test_serialized_opera_with_concurrent_chat_work(self):
        self.enqueue("assign-004", "D-03")
        self.enqueue("assign-005", "D-04")
        self.assertEqual(self.launch(), "WAIT_TAB:assign-004")
        self.assertEqual(self.launch(), "NO_ELIGIBLE_WORK")
        nonce = self.token("assign-004")
        self.assertEqual(self.c.ack("assign-004", nonce, "TAB_SELECTED", "Tab exists"),
                         "WAIT_SUBMIT")
        self.assertEqual(self.launch(), "NO_ELIGIBLE_WORK")
        self.assertEqual(self.c.ack("assign-004", nonce, "MESSAGE_SUBMITTED",
                                    "Input and send verified"), "WAIT_RESULT")
        self.assertEqual(self.launch(), "WAIT_TAB:assign-005")
        self.assertEqual(len(self.opened), 2)

    def test_per_chat_busy_until_result_published(self):
        self.enqueue("assign-006", "D-03")
        self.enqueue("assign-007", "D-03")
        self.assertEqual(self.launch(), "WAIT_TAB:assign-006")
        token = self.token("assign-006")
        self.c.ack("assign-006", token, "TAB_SELECTED", "Tab verified")
        self.c.ack("assign-006", token, "MESSAGE_SUBMITTED", "Sent verified")
        self.assertEqual(self.launch(), "NO_ELIGIBLE_WORK")
        self.assertEqual(
            self.db.execute("SELECT status FROM jobs WHERE id='assign-007'")
            .fetchone()[0], "QUEUED")

    def test_token_and_stage_protect_ack(self):
        self.enqueue("assign-008")
        self.launch()
        with self.assertRaisesRegex(ValueError, "ACK_NOT_AUTHENTICATED"):
            self.c.ack("assign-008", "wrong-token", "TAB_SELECTED", "anything")
        with self.assertRaisesRegex(ValueError, "ACK_STAGE_OUT_OF_ORDER"):
            self.c.ack("assign-008", self.token("assign-008"),
                       "MESSAGE_SUBMITTED", "Cannot send yet")

    def test_receipt_advances_d03_to_director_without_skipping_review(self):
        self.enqueue("assign-009", "D-03")
        self.launch()
        nonce = self.token("assign-009")
        self.c.ack("assign-009", nonce, "TAB_SELECTED", "Tab chosen")
        self.c.ack("assign-009", nonce, "MESSAGE_SUBMITTED", "User request sent")
        receipt = {
            "schema": "BUREAU_RECEIPT_V1", "jobId": "assign-009",
            "status": "REPORT_PUBLISHED",
            "documentUrl": "https://docs.google.com/document/d/example/edit",
            "summary": "Исследователь опубликовал результаты для проверки"
        }
        with patch.object(service, "checked_remote", return_value=receipt):
            status = self.c.ack("assign-009", nonce, "RESULT_PUBLISHED",
                                "Receipt publication verified", "c"*40)
        self.assertEqual(status, "COMPLETE_REPORTED")
        derived = self.db.execute(
            "SELECT target,event_type,status,parent FROM jobs WHERE parent='assign-009'"
        ).fetchone()
        self.assertEqual(derived, ("DIR-03", "REPORT_READY", "QUEUED", "assign-009"))

    def test_refuse_invalid_receipt_and_fake_result(self):
        self.enqueue("assign-010")
        self.launch()
        nonce = self.token("assign-010")
        self.c.ack("assign-010", nonce, "TAB_SELECTED", "Switched")
        self.c.ack("assign-010", nonce, "MESSAGE_SUBMITTED", "Submitted")
        with patch.object(service, "checked_remote", return_value={
            "schema": "BUREAU_RECEIPT_V1", "jobId": "other-job",
            "status": "REPORT_PUBLISHED", "documentUrl": "https://evil.example",
            "summary": ""
        }):
            with self.assertRaisesRegex(ValueError, "RECEIPT_NOT_VERIFIED"):
                self.c.ack("assign-010", nonce, "RESULT_PUBLISHED",
                           "Forged result", "e"*40)
        self.assertEqual(
            self.db.execute("SELECT status FROM jobs WHERE id='assign-010'")
            .fetchone()[0], "WAIT_RESULT"
        )

    def test_failure_in_research_does_not_block_other_chats(self):
        self.enqueue("assign-011", "D-03")
        self.enqueue("assign-012", "D-04")
        self.launch()
        token = self.token("assign-011")
        self.c.ack("assign-011", token, "TAB_SELECTED", "Tab chosen")
        self.c.ack("assign-011", token, "MESSAGE_SUBMITTED", "Sent")
        self.assertEqual(self.c.ack("assign-011", token, "FAILED",
                                    "Research failed"), "BLOCKED_CHAT")
        self.assertEqual(self.launch(), "WAIT_TAB:assign-012")
        self.c.recover("assign-011", "User reviewed failed job and cancelled it")

    def test_expired_queued_not_launched(self):
        self.enqueue("assign-013")
        self.db.execute("UPDATE jobs SET expires=? WHERE id='assign-013'",
                        ("2020-01-01T00:00:00+00:00",))
        self.assertEqual(self.launch(), "NO_ELIGIBLE_WORK")
        self.assertEqual(
            self.db.execute("SELECT status FROM jobs WHERE id='assign-013'")
            .fetchone()[0], "EXPIRED")

    def test_crashed_browser_is_not_retried(self):
        self.c.opener = lambda exe, url: (_ for _ in ()).throw(OSError("Cannot open"))
        self.enqueue("assign-014")
        self.assertEqual(self.launch(), "BLOCKED_UI")
        self.assertEqual(self.launch(), "NO_ELIGIBLE_WORK")
        self.c.recover("assign-014", "Reviewed browser state no message sent")
        self.assertEqual(
            self.db.execute("SELECT status FROM jobs WHERE id='assign-014'")
            .fetchone()[0], "CANCELLED_AFTER_REVIEW")

    def test_no_internet_or_archicad_needed_for_startup_disabled_apa(self):
        self.assertEqual(self.c.enable_apa(), "APA_DISABLED_BY_LOCAL_CONFIG")
        self.assertIsNone(self.c.apa)


if __name__ == "__main__":
    unittest.main()
