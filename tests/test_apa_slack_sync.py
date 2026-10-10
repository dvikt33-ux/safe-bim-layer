"""Offline tests for the APA Slack event ledger and work-step contract.

Run: python -m unittest -v tests.test_apa_slack_sync
No network, tokens, live Slack, Archicad or PLN required.
"""
import json
import tempfile
import threading
import time
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch
from urllib.request import urlopen

from scripts.apa_sync.coordinator import (
    EventStore, InvalidEvent, format_event, make_server, parse_event,
)
from scripts.apa_sync.step_sync import after_step, before_step
from scripts.apa_sync.socket_mode import bootstrap_channel


def event(**changes):
    value = {
        "event_id": uuid.uuid4().hex,
        "task_id": "TN-GDL-CREATE-01",
        "status": "BLOCKED",
        "phase": "BUILD",
        "source": "chatgpt:research",
        "summary": "Native diagnostic build remains unverified",
        "evidence_urls": ["https://github.com/dvikt33-ux/safe-bim-layer/pull/20"],
    }
    value.update(changes)
    return value


class EventFormatTests(unittest.TestCase):
    def test_round_trip_including_cyrillic(self):
        value = event(summary="Нативный APX пока не собран")
        self.assertEqual(parse_event(format_event(value))["summary"], value["summary"])

    def test_slack_compacted_json_fence(self):
        value = event(summary="Slack may collapse fenced JSON lines")
        original = format_event(value)
        compacted = original.replace("```json\n", "```").replace("\n```", "```")
        self.assertEqual(parse_event(compacted)["event_id"], value["event_id"])

    def test_live_chat_schema_discriminator(self):
        # Live APA chats already emit optional schema and pretty JSON.
        sample = event(
            schema="APA_EVENT_V1",
            event_id="apa-20261010-taskproposal-audit-plan-1418",
            task_id="APA-P60.A02.S04",
            phase="OFFLINE",
            status="INFO",
            source="chatgpt:apa-controller-setup",
            summary="PROJECT_PLAN task proposal checked; pending independent audit",
        )
        message = "APA_EVENT_V1\\n```" + json.dumps(
            sample, ensure_ascii=False, indent=2
        ) + "```"
        parsed = parse_event(message)
        self.assertEqual(parsed["task_id"], "APA-P60.A02.S04")
        self.assertEqual(parsed["schema"], "APA_EVENT_V1")

    def test_invalid_schema_discriminator_rejected(self):
        with self.assertRaises(InvalidEvent):
            parse_event(format_event(event(schema="SOME_OTHER_PROTOCOL")))

    def test_ignore_freeform_messages(self):
        self.assertIsNone(parse_event("APA report: anything"))
        self.assertIsNone(parse_event("Random message"))

    def test_fail_closed_malformed(self):
        with self.assertRaises(InvalidEvent):
            parse_event("APA_EVENT_V1\nnot-json")
        with self.assertRaises(InvalidEvent):
            parse_event(format_event(event(status="PASS", evidence_urls=[])))
        with self.assertRaises(InvalidEvent):
            parse_event(format_event(event(phase="UNVERIFIED")))
        with self.assertRaises(InvalidEvent):
            parse_event(format_event(event(evidence_urls=["http://example.com"])))
        with self.assertRaises(InvalidEvent):
            parse_event(format_event(event(extra_key="surprise")))

    def test_before_step_pages_history_and_tracks_non_event_ts(self):
        older = event(summary="Historical report")
        newer = event(summary="More recent report")

        class Client:
            def conversations_history(self, **kwargs):
                if not kwargs.get("cursor"):
                    return {
                        "messages": [
                            {"ts": "102.1", "text": "ordinary human conversation"},
                            {"ts": "101.1", "text": format_event(newer)},
                        ],
                        "response_metadata": {"next_cursor": "page-2"},
                    }
                return {
                    "messages": [{"ts": "100.1", "text": format_event(older)}],
                    "response_metadata": {"next_cursor": ""},
                }

        with patch("scripts.apa_sync.step_sync._client", return_value=Client()):
            output = before_step("C0C886E1PGR", limit=3)
        self.assertEqual(len(output["events"]), 2)
        self.assertEqual(output["newest_ts"], "102.1")
        self.assertFalse(output["truncated"])

    def test_preview_only_by_default(self):
        output = after_step("C0C886E1PGR", event(), publish=False)
        self.assertTrue(output["dry_run"])
        self.assertIn("APA_EVENT_V1", output["message"])


class EventStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = EventStore(Path(self.temp.name) / "state.sqlite3")

    def tearDown(self):
        self.temp.cleanup()

    def _ingest(self, e, ts):
        return self.store.ingest(format_event(e), slack_channel="C0C886E1PGR", slack_ts=ts)

    def test_dedupe_on_delivery_retry(self):
        e = event()
        result = self._ingest(e, "100.1")
        self.assertTrue(result["accepted"])
        result2 = self._ingest(e, "100.1")
        self.assertEqual(result2["reason"], "duplicate")
        self.assertEqual(len(self.store.changes()["changes"]), 1)

    def test_other_messages_cannot_enter_ledger(self):
        result = self.store.ingest("Other chat discussion", slack_channel="C0C886E1PGR", slack_ts="99.1")
        self.assertFalse(result["accepted"])
        self.assertEqual(len(self.store.changes()["changes"]), 0)

    def test_conflicting_evidence_is_not_silently_accepted(self):
        initial = event()
        next_one = event(status="PASS", summary="Claimed live completion", phase="BUILD")
        self._ingest(initial, "100.1")
        result = self._ingest(next_one, "101.1")
        self.assertTrue(result["conflict"])
        state = self.store.latest_states()["state"]["TN-GDL-CREATE-01:BUILD"]
        self.assertEqual(state["effective_status"], "CONFLICT")

    def test_conflict_sticks_until_explicit_supersession(self):
        initial = event()
        disputed = event(status="PASS", summary="Unreviewed reversal")
        repeated = event(status="PASS", summary="Another unreviewed claim")
        self._ingest(initial, "100.1")
        self._ingest(disputed, "101.1")
        status = self._ingest(repeated, "102.1")
        self.assertTrue(status["conflict"])
        self.assertEqual(
            self.store.latest_states()["state"]["TN-GDL-CREATE-01:BUILD"]["effective_status"],
            "CONFLICT",
        )

    def test_same_id_different_payload_is_rejected(self):
        first = event()
        self._ingest(first, "100.1")
        tampered = dict(first, summary="Conflicting reused identity")
        with self.assertRaises(InvalidEvent):
            self._ingest(tampered, "102.1")

    def test_supersession_resolves_prior_status(self):
        initial = event()
        second = event(
            status="PASS", summary="Build evidence exists",
            supersedes=initial["event_id"],
        )
        self._ingest(initial, "100.1")
        result = self._ingest(second, "101.1")
        self.assertFalse(result["conflict"])
        state = self.store.latest_states()["state"]["TN-GDL-CREATE-01:BUILD"]
        self.assertEqual(state["effective_status"], "PASS")

    def test_invalid_supersedes_is_rejected(self):
        with self.assertRaises(InvalidEvent):
            self._ingest(event(supersedes="arbitrary-123"), "101.1")

    def test_sequence_and_cursor(self):
        self._ingest(event(), "100.1")
        self._ingest(event(), "101.1")
        first = self.store.changes(after=0, limit=1)
        second = self.store.changes(after=first["next_cursor"])
        self.assertEqual(len(first["changes"]), 1)
        self.assertEqual(len(second["changes"]), 1)
        self.assertLess(first["next_cursor"], second["next_cursor"])

    def test_wait_wakes_after_insert(self):
        output = []
        thread = threading.Thread(
            target=lambda: output.append(self.store.wait_changes(after=0, timeout=2)),
            daemon=True,
        )
        thread.start()
        time.sleep(0.03)
        self._ingest(event(), "104.1")
        thread.join(timeout=3)
        self.assertFalse(thread.is_alive())
        self.assertEqual(len(output[0]["changes"]), 1)

    def test_bootstrap_recent_history_and_dedupe(self):
        first = event()
        second = event(summary="Other chat reached another checkpoint")
        class Client:
            def conversations_history(self, **kwargs):
                return {
                    "messages": [
                        {"ts": "101.1", "text": format_event(second), "subtype": "bot_message"},
                        {"ts": "100.1", "text": format_event(first)},
                    ],
                    "response_metadata": {"next_cursor": ""},
                }
        client = Client()
        info = bootstrap_channel(self.store, client, "C0C886E1PGR")
        self.assertEqual(info["accepted"], 2)
        self.assertEqual(bootstrap_channel(self.store, client, "C0C886E1PGR")["accepted"], 0)
        self.assertEqual(len(self.store.changes()["changes"]), 2)

    def test_http_read_only_loopback(self):
        server = make_server(self.store, port=0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            base = f"http://127.0.0.1:{server.server_port}"
            with urlopen(base + "/health", timeout=3) as response:
                self.assertTrue(json.load(response)["ok"])
            with urlopen(base + "/v1/changes?after=0", timeout=3) as response:
                self.assertEqual(json.load(response)["changes"], [])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)

    def test_server_wont_bind_public_interface(self):
        with self.assertRaises(ValueError):
            make_server(self.store, host="0.0.0.0", port=0)


if __name__ == "__main__":
    unittest.main()
