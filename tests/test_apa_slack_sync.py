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
from scripts.apa_sync.socket_mode import bootstrap_channel, rejected_message_shape
from scripts.apa_sync.inspect_raw_envelopes import summarize, characterize, safe_slack_error_summary


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
        message = "APA_EVENT_V1\n```" + json.dumps(
            sample, ensure_ascii=False, indent=2
        ) + "```"
        parsed = parse_event(message)
        self.assertEqual(parsed["task_id"], "APA-P60.A02.S04")
        self.assertEqual(parsed["schema"], "APA_EVENT_V1")

    def test_exact_chatgpt_slack_footer_after_json_fence(self):
        sample = event(
            schema="APA_EVENT_V1",
            event_id="apa-source-attribution-20261011-001",
            phase="SOURCE", status="INFO",
            summary="Source-only research, BUILD and LIVE not verified",
        )
        footer = "\n*Sent using* <@U0C90JE4WAC|ChatGPT>"
        variants = [
            format_event(sample) + footer,
            "APA_EVENT_V1\n```" + json.dumps(sample) + "```" + footer,
            "APA_EVENT_V1\nResearch summary\n```json\n" + json.dumps(
                sample, ensure_ascii=False, indent=2,
            ) + "\n```" + footer,
        ]
        for message in variants:
            with self.subTest(message_prefix=message[:35]):
                parsed = parse_event(message)
                self.assertEqual(parsed["event_id"], sample["event_id"])
                self.assertEqual(parsed["phase"], "SOURCE")
                self.assertEqual(parsed["status"], "INFO")

    def test_raw_slack_chatgpt_mention_without_display_label(self):
        # Slack's raw Web API text uses a bare mention; the separate
        # ChatGPT connector may render this with a |ChatGPT display label.
        sample = event(
            schema="APA_EVENT_V1",
            event_id="apa-native-slack-20261011-test",
            task_id="APA-P10.A01.S01",
            phase="SOURCE", status="INFO",
            source="chatgpt:raw-slack",
        )
        trailer = "\n*Sent using* <@U0C90JE4WAC>"
        for envelope in (
            format_event(sample),
            "APA_EVENT_V1\n```" + json.dumps(sample, ensure_ascii=False) + "```",
            "APA_EVENT_V1\n```{\n" + json.dumps(
                sample, ensure_ascii=False, indent=2,
            ) + "\n}```",
        ):
            with self.subTest(envelope=envelope[:32]):
                parsed = parse_event(envelope + trailer)
                self.assertEqual(parsed["event_id"], sample["event_id"])
                self.assertEqual(parsed["phase"], "SOURCE")
                self.assertEqual(parsed["status"], "INFO")

    def test_raw_footer_rejects_unknown_sender_and_attached_content(self):
        full = format_event(event())
        for extra in (
            "\n*Sent using* <@U0C90JE4WAD>",
            "\n*Sent using* <@U0C90JE4WAC|Other>",
            "\n*Sent using* <@U0C90JE4WAC> approved",
            "\n*Sent using* <@U0C90JE4WAC>\nBUILD PASS",
            "\n*Sent using* <@U0C90JE4WAC|ChatGPT> extra",
            "\n*Sent using* <@U0C90JE4WAC",
            "\n*Sent using* <@U0C90JE4WAC>>",
        ):
            with self.subTest(suffix=extra):
                with self.assertRaises(InvalidEvent):
                    parse_event(full + extra)
        with self.assertRaises(InvalidEvent):
            parse_event(format_event(event(status="PASS", evidence_urls=[])) +
                        "\n*Sent using* <@U0C90JE4WAC>")

    def test_chatgpt_footer_rejects_noncanonical_or_extra_text(self):
        clean = format_event(event())
        invalid = [
            clean + "\nSent using ChatGPT",
            clean + "\n*Sent using* <@U0C90JE4WAC|Other>",
            clean + "\n*Sent using* <@U0123456789|ChatGPT>",
            clean + "\n*Sent using* <@U0C90JE4WAC|ChatGPT>\nUNVERIFIED EXTRA",
            clean + "\nthis event is now LIVE PASS",
            clean.replace("\n```", "") + "\n*Sent using* <@U0C90JE4WAC|ChatGPT>",
        ]
        for message in invalid:
            with self.subTest(last_chars=message[-50:]):
                with self.assertRaises(InvalidEvent):
                    parse_event(message)

    def test_attribution_does_not_bypass_strict_status_and_evidence(self):
        footer = "\n*Sent using* <@U0C90JE4WAC|ChatGPT>"
        with self.assertRaises(InvalidEvent):
            parse_event(format_event(event(status="PASS", evidence_urls=[])) + footer)
        with self.assertRaises(InvalidEvent):
            parse_event(format_event(event(phase="UNSAFE", status="PASS")) + footer)

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

    def test_bootstrap_reports_safe_rejection_counts(self):
        fresh = event(task_id="APA-SYNC-BOOTSTRAP-TEST", phase="LIVE", status="INFO")

        class Client:
            def conversations_history(self, **kwargs):
                return {
                    "messages": [
                        {"ts": "105.1", "text": "ordinary channel message"},
                        {"ts": "104.1", "text": "APA_EVENT_V1\nmissing JSON fence"},
                        {"ts": "103.1", "text": "secret should never be shown", "subtype": "channel_join"},
                        {"ts": "102.1", "text": format_event(fresh)},
                    ],
                    "response_metadata": {"next_cursor": ""},
                }

        client = Client()
        first = bootstrap_channel(self.store, client, "C0C886E1PGR")
        self.assertEqual(first["scanned"], 4)
        self.assertEqual(first["accepted"], 1)
        self.assertEqual(first["duplicates"], 0)
        self.assertEqual(first["not_apa_events"], 1)
        self.assertEqual(first["ignored_subtype"], 1)
        self.assertEqual(first["rejected"], {
            "Expected APA_EVENT_V1 and one JSON code fence": 1,
        })
        # Running the bootstrap again must not re-insert the event.
        second = bootstrap_channel(self.store, client, "C0C886E1PGR")
        self.assertEqual(second["accepted"], 0)
        self.assertEqual(second["duplicates"], 1)
        self.assertEqual(self.store.changes()["next_cursor"], 1)
        self.assertNotIn("secret", str(second))

    def test_rejected_event_envelope_shape_has_fixed_safe_labels(self):
        sample = "APA_EVENT_V1\n" + "Some header\n" + '{"event_id":"secret-value","url":"https://secret.example/path"}'
        shape = rejected_message_shape(sample)
        self.assertEqual(shape, "fences=none;begins=header;ends=object;object=yes")
        self.assertNotIn("secret", shape)
        self.assertNotIn("https", shape)
        self.assertEqual(
            rejected_message_shape("APA_EVENT_V1\n```json\n{}"),
            "fences=one;begins=fence;ends=object;object=yes",
        )
        self.assertEqual(
            rejected_message_shape("APA_EVENT_V1\n```json\n{}\n``` suffix"),
            "fences=two;begins=fence;ends=other;object=yes",
        )

    def test_bootstrap_reports_rejected_shape_counts(self):
        class Client:
            def conversations_history(self, **kwargs):
                return {
                    "messages": [
                        {"ts": "211.1", "text": "APA_EVENT_V1\n" + '{"event_id":"private-marker"}'},
                        {"ts": "210.1", "text": "APA_EVENT_V1\n```json\n{}"},
                    ],
                    "response_metadata": {"next_cursor": ""},
                }
        stats = bootstrap_channel(self.store, Client(), "C0C886E1PGR")
        self.assertEqual(stats["scanned"], 2)
        self.assertEqual(stats["accepted"], 0)
        self.assertEqual(sum(stats["rejection_shapes"].values()), 2)
        self.assertIn("fences=none;begins=object;ends=object;object=yes",
                      stats["rejection_shapes"])
        self.assertIn("fences=one;begins=fence;ends=object;object=yes",
                      stats["rejection_shapes"])
        self.assertNotIn("private-marker", str(stats))

    def test_bootstrap_chatgpt_footer_and_duplicate(self):
        first = event(event_id="apa-legacy-source-20261010-001",
                      task_id="APA-P10.A01.S01", status="INFO", phase="SOURCE")
        second = event(event_id="apa-legacy-offline-20261010-002",
                       task_id="APA-SYNC-01", status="PASS", phase="OFFLINE")
        footer = "\n*Sent using* <@U0C90JE4WAC|ChatGPT>"
        class Client:
            def conversations_history(self, **kwargs):
                return {
                    "messages": [
                        {"ts": "201.1", "text": format_event(second) + footer},
                        {"ts": "200.1", "text": format_event(first) + footer},
                        {"ts": "199.1", "text": "APA_EVENT_V1\n```json\n{}\n"},  # invalid fence
                    ],
                    "response_metadata": {"next_cursor": ""},
                }
        client = Client()
        result = bootstrap_channel(self.store, client, "C0C886E1PGR")
        self.assertEqual(result["scanned"], 3)
        self.assertEqual(result["accepted"], 2)
        self.assertEqual(result["rejected"], {
            "Expected APA_EVENT_V1 and one JSON code fence": 1,
        })
        self.assertEqual(result["conflicts"], 0)
        again = bootstrap_channel(self.store, client, "C0C886E1PGR")
        self.assertEqual(again["accepted"], 0)
        self.assertEqual(again["duplicates"], 2)
        self.assertEqual(self.store.changes()["next_cursor"], 2)
        self.assertEqual(
            self.store.latest_states()["state"]["APA-P10.A01.S01:SOURCE"]["effective_status"],
            "INFO",
        )

    def test_bootstrap_raw_unlabelled_sender_replay_is_idempotent(self):
        old = event(
            event_id="apa-historical-source-20261011-a",
            task_id="APA-P10.A01.S01",
            status="INFO", phase="SOURCE",
        )
        footer = "\n*Sent using* <@U0C90JE4WAC>"

        class Client:
            def conversations_history(self, **kwargs):
                return {
                    "messages": [
                        {"ts": "402.1", "text": format_event(old) + footer},
                        {"ts": "401.1", "text": "APA_EVENT_V1\n```json\n{}"},
                    ],
                    "response_metadata": {"next_cursor": ""},
                }

        client = Client()
        first = bootstrap_channel(self.store, client, "C0C886E1PGR")
        self.assertEqual(first["accepted"], 1)
        self.assertEqual(first["conflicts"], 0)
        self.assertEqual(first["rejected"], {
            "Expected APA_EVENT_V1 and one JSON code fence": 1,
        })
        second = bootstrap_channel(self.store, client, "C0C886E1PGR")
        self.assertEqual(second["accepted"], 0)
        self.assertEqual(second["duplicates"], 1)
        self.assertEqual(self.store.changes()["next_cursor"], 1)

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


class RawSlackProbeTests(unittest.TestCase):
    def test_safe_footer_and_unknown_suffix_categories(self):
        self.assertEqual(
            characterize("APA_EVENT_V1\n```json\n{}\n```\n*Sent using* <@U0C90JE4WAC|ChatGPT>"),
            "fences=two;tail=exact_known_footer;tail_len=1-64;cr=no;invisible=no",
        )
        unknown = characterize("APA_EVENT_V1\n```json\n{}\n```\nconfidential private-data")
        self.assertIn("tail=other_suffix", unknown)
        self.assertNotIn("confidential", unknown)
        self.assertNotIn("private-data", unknown)

    def test_safe_slack_error_allows_only_whitelisted_code_and_numeric_hints(self):
        class Response(dict):
            def __init__(self, code, status, headers=None):
                super().__init__({"error": code, "extra": "private-slack-payload"})
                self.status_code = status
                self.headers = headers or {}

        self.assertEqual(
            safe_slack_error_summary(
                Response("ratelimited", 429, {"Retry-After": "60"})
            ),
            {"error_code": "ratelimited", "http_status": 429,
             "retry_after_seconds": 60},
        )
        self.assertEqual(
            safe_slack_error_summary(Response("invalid_auth", 200)),
            {"error_code": "invalid_auth", "http_status": 200},
        )
        self.assertEqual(
            safe_slack_error_summary(Response("missing_scope", 200)),
            {"error_code": "missing_scope", "http_status": 200},
        )

    def test_safe_slack_error_redacts_unknown_text_and_invalid_retry_header(self):
        class Response(dict):
            status_code = 900
            headers = {"Retry-After": "sensitive-value"}
        response = Response(
            error="private-xoxb-token-do-not-log",
            body="private Slack conversation content",
        )
        result = safe_slack_error_summary(response)
        self.assertEqual(result, {"error_code": "other_slack_error"})
        output = json.dumps(result)
        for sensitive in ("xoxb", "sensitive", "conversation", "private"):
            self.assertNotIn(sensitive, output)

    def test_probe_does_not_emit_any_slack_message_contents(self):
        valid = format_event(event(event_id="probe-valid-event")) + (
            "\n*Sent using* <@U0C90JE4WAC|ChatGPT>"
        )
        bad = "APA_EVENT_V1\n```json\n{}" + "must-remain-secret"
        results = summarize([
            {"text": valid, "ts": "900.1", "user": "sensitive-user"},
            {"text": bad, "ts": "901.1", "user": "another-user"},
            {"text": "irrelevant private text", "ts": "902.1"},
            {"subtype": "channel_join", "text": "hello", "ts": "903.1"},
        ])
        self.assertEqual(results["counts"]["scanned"], 4)
        self.assertEqual(results["counts"]["parse_valid"], 1)
        self.assertEqual(results["counts"]["fence_envelope_rejected"], 1)
        self.assertEqual(results["counts"]["non_event"], 1)
        self.assertEqual(results["counts"]["ignored_subtype"], 1)
        out = json.dumps(results)
        for secret in ("must-remain-secret", "probe-valid-event", "900.1",
                       "901.1", "sensitive-user", "another-user", "irrelevant private text"):
            self.assertNotIn(secret, out)


if __name__ == "__main__":
    unittest.main()
