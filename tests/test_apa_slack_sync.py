"""Offline tests for the APA Slack event ledger and work-step contract.

Run: python -m unittest -v tests.test_apa_slack_sync
No network, tokens, live Slack, Archicad or PLN required.
"""
import json
import tempfile
import threading
import unittest
import uuid
from pathlib import Path
from urllib.request import urlopen

from scripts.apa_sync.coordinator import (
    EventStore, InvalidEvent, format_event, make_server, parse_event,
)
from scripts.apa_sync.step_sync import after_step


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
