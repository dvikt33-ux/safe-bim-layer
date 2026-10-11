"""Isolated regression tests for crash-safe opt-in Slack notification persistence."""
from pathlib import Path
import sqlite3
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.apa_sync import receipt_bridge as b
from scripts.apa_sync.notification_outbox import NotificationOutbox, OutboxError

EVENT = {
    "schema": "APA_EVENT_V1",
    "event_id": "apa-gh-receipt-1234567890abcdef12345678",
    "task_id": "APA-P70.A01.S01",
    "status": "INFO",
    "phase": "SOURCE",
    "source": "apa:receipt-bridge:git-verified",
    "summary": "Verified immutable publisher receipt (test)",
    "evidence_urls": ["https://github.com/dvikt33-ux/safe-bim-layer/blob/" + "b" * 40 +
                      "/docs/research/apa-results/runs/test/REPORT.md"]
}


def fake_step(send):
    m = types.ModuleType("scripts.apa_sync.step_sync")
    m.after_step = send
    return m


class OutboxTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name) / "isolated.sqlite3"

    def tearDown(self):
        self.directory.cleanup()

    def test_reservation_survives_reopen(self):
        a = NotificationOutbox(self.path)
        self.assertEqual(a.reserve(EVENT), "RESERVED")
        self.assertEqual(NotificationOutbox(self.path).reserve(EVENT), "RESERVED")
        self.assertEqual(a.status(EVENT["event_id"])["status"], "RESERVED")

    def test_conflicting_payload_refused(self):
        a = NotificationOutbox(self.path)
        a.reserve(EVENT)
        other = {**EVENT, "summary": "changed status masquerading as same ID"}
        with self.assertRaisesRegex(OutboxError, "different payload"):
            a.reserve(other)

    def test_concurrent_second_sender_refused(self):
        a = NotificationOutbox(self.path)
        a.reserve(EVENT)
        a.begin_send(EVENT["event_id"])
        other = NotificationOutbox(self.path)
        self.assertEqual(other.reserve(EVENT), "IN_FLIGHT")
        with self.assertRaisesRegex(OutboxError, "already in flight"):
            other.begin_send(EVENT["event_id"])

    def test_uncertain_delivery_is_persistent(self):
        a = NotificationOutbox(self.path)
        a.reserve(EVENT)
        a.begin_send(EVENT["event_id"])
        a.mark_uncertain(EVENT["event_id"])
        self.assertEqual(NotificationOutbox(self.path).reserve(EVENT), "UNCERTAIN")

    def test_sent_record_is_persistent(self):
        a = NotificationOutbox(self.path)
        a.reserve(EVENT)
        a.begin_send(EVENT["event_id"])
        a.mark_sent(EVENT["event_id"], "1791721617.730099")
        self.assertEqual(NotificationOutbox(self.path).status(EVENT["event_id"])["slack_ts"],
                         "1791721617.730099")
        self.assertEqual(NotificationOutbox(self.path).reserve(EVENT), "SENT")

    def test_send_once_then_durable_duplicate(self):
        calls = []
        def send(channel, event, publish=False):
            calls.append(("send", channel, publish))
            return {"published": True, "slack_ts": "1791721617.730099"}
        with patch.object(b, "find_notification", return_value=None) as probe:
            with patch.dict(sys.modules, {"scripts.apa_sync.step_sync": fake_step(send)}):
                first = b.publish_with_outbox(EVENT, outbox_path=self.path)
                second = b.publish_with_outbox(EVENT, outbox_path=self.path)
        self.assertTrue(first["published"])
        self.assertEqual(second, {"published": False, "already_recorded": True,
                                  "event_id": EVENT["event_id"]})
        self.assertEqual(calls, [("send", b.CHANNEL, True)])
        self.assertEqual(probe.call_count, 1)
        self.assertEqual(NotificationOutbox(self.path).status(EVENT["event_id"])["status"], "SENT")

    def test_exception_leaves_uncertain_no_blind_retry(self):
        calls = []
        def send(channel, event, publish=False):
            calls.append("send")
            raise RuntimeError("network timed out after possible Slack acceptance")
        with patch.object(b, "find_notification", return_value=None):
            with patch.dict(sys.modules, {"scripts.apa_sync.step_sync": fake_step(send)}):
                with self.assertRaisesRegex(b.BridgeError, "delivery uncertain"):
                    b.publish_with_outbox(EVENT, outbox_path=self.path)
                with self.assertRaisesRegex(b.BridgeError, "manual review"):
                    b.publish_with_outbox(EVENT, outbox_path=self.path)
        self.assertEqual(calls, ["send"])
        self.assertEqual(NotificationOutbox(self.path).reserve(EVENT), "UNCERTAIN")

    def test_restart_can_reconcile_present_slack_message(self):
        a = NotificationOutbox(self.path)
        a.reserve(EVENT)
        a.begin_send(EVENT["event_id"])
        with patch.object(b, "find_notification",
                          return_value={"slack_ts": "1791721617.730099", "channel_id": b.CHANNEL}):
            with patch.dict(sys.modules, {"scripts.apa_sync.step_sync": fake_step(
                    lambda *args, **kwargs: self.fail("should not post"))}):
                result = b.publish_with_outbox(EVENT, outbox_path=self.path)
        self.assertTrue(result["already_present"])
        self.assertEqual(NotificationOutbox(self.path).reserve(EVENT), "SENT")

    def test_unresolved_crash_never_resends(self):
        a = NotificationOutbox(self.path)
        a.reserve(EVENT)
        a.begin_send(EVENT["event_id"])
        with patch.object(b, "find_notification", return_value=None):
            with self.assertRaisesRegex(b.BridgeError, "manual review"):
                b.publish_with_outbox(EVENT, outbox_path=self.path)
        self.assertEqual(NotificationOutbox(self.path).reserve(EVENT), "IN_FLIGHT")

    def test_slack_same_id_different_proof_fails_closed(self):
        changed = {**EVENT, "evidence_urls": ["https://github.com/other/repo"]}
        m = types.ModuleType("scripts.apa_sync.coordinator")
        m.parse_event = lambda _: changed
        client = types.SimpleNamespace(conversations_history=lambda **kwargs: {
            "messages": [{"text": "existing", "ts": "1791721617.730099"}],
            "response_metadata": {}
        })
        s = types.ModuleType("scripts.apa_sync.step_sync")
        s._client = lambda: client
        with patch.dict(sys.modules, {"scripts.apa_sync.coordinator": m,
                                      "scripts.apa_sync.step_sync": s}):
            with self.assertRaisesRegex(b.BridgeError, "conflicting payload"):
                b.find_notification(EVENT)

    def test_slack_pagination_incomplete_fails_closed(self):
        m = types.ModuleType("scripts.apa_sync.coordinator")
        m.parse_event = lambda _: None
        client = types.SimpleNamespace(conversations_history=lambda **kwargs: {
            "messages": [], "response_metadata": {"next_cursor": "more"}
        })
        s = types.ModuleType("scripts.apa_sync.step_sync")
        s._client = lambda: client
        with patch.dict(sys.modules, {"scripts.apa_sync.coordinator": m,
                                      "scripts.apa_sync.step_sync": s}):
            with self.assertRaisesRegex(b.BridgeError, "scan incomplete"):
                b.find_notification(EVENT)


if __name__ == "__main__":
    unittest.main()
