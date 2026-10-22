"""Адресные тесты нового шлюза, без Opera, Automa, GitHub и Archicad."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import bureau_chat_activation_gateway as gateway


def event(name, target="D-03", action="ACTIVATE_ONLY"):
    now = datetime.now(timezone.utc)
    stamp = lambda dt: dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "schema": gateway.SCHEMA,
        "jobId": name,
        "eventType": "TRIGGER_PROBE",
        "targetChat": target,
        "action": action,
        "createdAt": stamp(now - timedelta(minutes=1)),
        "expiresAt": stamp(now + timedelta(hours=1)),
        "sourceRef": None,
    }


class GatewayTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.opera = self.folder / "opera.exe"
        self.opera.touch()
        self.db = gateway.database(self.folder / "state.sqlite")
        self.addCleanup(self.db.close)
        self.config = {
            "operaExe": str(self.opera),
            "extensionId": "a" * 32,
            "targets": {
                "D-03": {"workflowId": "workflow_d03"},
                "D-04": {"workflowId": "workflow_d04"},
            },
        }

    def push(self, name, target="D-03"):
        value = event(name, target)
        return gateway.ingest(
            self.db, value, gateway.git_blob_sha(str(value).encode()),
            self.config["targets"]
        )

    def test_strict_envelope_rejects_remote_message_injection(self):
        value = event("activation-01")
        value["message"] = "Send this to ChatGPT"
        with self.assertRaisesRegex(ValueError, "EVENT_FIELDS_INVALID"):
            gateway.validate(value, value["jobId"], self.config["targets"])

    def test_send_and_unknown_target_are_blocked(self):
        with self.assertRaisesRegex(ValueError, "SEND_AND_WRITE_NOT_AUTHORIZED"):
            gateway.validate(event("activation-02", action="SEND"),
                             "activation-02", self.config["targets"])
        with self.assertRaisesRegex(ValueError, "CHAT_NOT_IN_LOCAL_ALLOWLIST"):
            gateway.validate(event("activation-03", target="D-99"),
                             "activation-03", self.config["targets"])

    def test_immutable_id_deduplicates_and_detects_rewrite(self):
        value = event("activation-04")
        sha = gateway.git_blob_sha(b"original")
        self.assertEqual(gateway.ingest(
            self.db, value, sha, self.config["targets"]), "QUEUED")
        self.assertEqual(gateway.ingest(
            self.db, value, sha, self.config["targets"]), "DUPLICATE_IGNORED")
        with self.assertRaisesRegex(ValueError, "IMMUTABLE_EVENT_REWRITTEN"):
            gateway.ingest(self.db, value, gateway.git_blob_sha(b"changed"),
                           self.config["targets"])
        self.assertEqual(self.db.execute("SELECT count(*) FROM jobs").fetchone()[0], 1)

    def test_two_events_for_same_chat_wait_in_fifo(self):
        self.push("activation-05")
        self.push("activation-06")
        started = []
        self.assertEqual(gateway.dispatch_one(
            self.db, self.config, lambda exe, url: started.append(url)),
            "AWAIT_TAB_PROOF:activation-05")
        self.assertEqual(gateway.dispatch_one(
            self.db, self.config, lambda exe, url: started.append(url)),
            "NO_ELIGIBLE_JOBS")
        self.assertEqual(len(started), 1)
        gateway.confirm_tab(self.db, "activation-05", "Manual tab inspection")
        self.assertEqual(gateway.dispatch_one(
            self.db, self.config, lambda exe, url: started.append(url)),
            "AWAIT_TAB_PROOF:activation-06")

    def test_browser_ui_is_serialized_even_across_independent_chats(self):
        self.push("activation-07", "D-03")
        self.push("activation-08", "D-04")
        self.assertTrue(gateway.dispatch_one(
            self.db, self.config, lambda exe, url: None).startswith("AWAIT_TAB_PROOF"))
        self.assertEqual(gateway.dispatch_one(
            self.db, self.config, lambda exe, url: None), "NO_ELIGIBLE_JOBS")
        gateway.confirm_tab(self.db, "activation-07", "D-03 switched")
        self.assertEqual(gateway.dispatch_one(
            self.db, self.config, lambda exe, url: None),
            "AWAIT_TAB_PROOF:activation-08")

    def test_url_opens_automa_only_and_never_claims_chat_success(self):
        self.push("activation-09")
        launches = []
        gateway.dispatch_one(self.db, self.config,
                             lambda exe, url: launches.append((exe, url)))
        self.assertEqual(len(launches), 1)
        self.assertIn("chrome-extension://" + "a" * 32 + "/execute.html#/",
                      launches[0][1])
        self.assertIn("jobId=activation-09", launches[0][1])
        self.assertNotIn("chatgpt.com", launches[0][1])
        self.assertEqual(
            self.db.execute("SELECT status FROM jobs WHERE job_id='activation-09'").fetchone()[0],
            "AWAIT_TAB_PROOF"
        )

    def test_failure_after_journal_blocks_reexecution(self):
        self.push("activation-10")
        def fail(exe, url):
            raise OSError("Opera unavailable")
        self.assertEqual(gateway.dispatch_one(self.db, self.config, fail),
                         "BLOCKED_NEEDS_RECONCILE:activation-10")
        self.assertEqual(gateway.dispatch_one(self.db, self.config, fail),
                         "NO_ELIGIBLE_JOBS")

    def test_fetch_does_not_retrieve_already_seen_blob(self):
        known = {"activation-11": "7" * 40}
        records = [{"type": "file", "name": "activation-11.json", "sha": "7" * 40}]
        with patch.object(gateway, "gh_api", return_value=records) as call:
            self.assertEqual(list(gateway.fetch_events(known)), [])
            self.assertEqual(call.call_count, 1)
        records[0]["sha"] = "8" * 40
        with patch.object(gateway, "gh_api", return_value=records):
            with self.assertRaisesRegex(ValueError, "IMMUTABLE_EVENT_REWRITTEN"):
                list(gateway.fetch_events(known))


    def test_expired_event_cannot_launch_after_waiting_in_queue(self):
        self.push("activation-12")
        after_expiry = datetime.now(timezone.utc) + timedelta(days=2)
        with patch.object(gateway, "utc_now", return_value=after_expiry):
            self.assertEqual(gateway.claim(self.db), None)
        self.assertEqual(
            self.db.execute(
                "SELECT status FROM jobs WHERE job_id='activation-12'"
            ).fetchone()[0],
            "EXPIRED"
        )

    def test_blocked_launch_needs_explicit_reconciliation(self):
        self.push("activation-13")
        self.push("activation-14")
        def fail(exe, url):
            raise OSError("Cannot open Opera")
        self.assertEqual(gateway.dispatch_one(self.db, self.config, fail),
                         "BLOCKED_NEEDS_RECONCILE:activation-13")
        with self.assertRaisesRegex(ValueError, "JOB_NOT_WAITING"):
            gateway.confirm_tab(self.db, "activation-13", "No tab was opened")
        self.assertEqual(gateway.dispatch_one(
            self.db, self.config, lambda exe, url: None), "NO_ELIGIBLE_JOBS")
        gateway.cancel_blocked(self.db, "activation-13",
                               "Inspected Opera and confirmed no pending job")
        self.assertEqual(gateway.dispatch_one(
            self.db, self.config, lambda exe, url: None),
            "AWAIT_TAB_PROOF:activation-14")


if __name__ == "__main__":
    unittest.main()
