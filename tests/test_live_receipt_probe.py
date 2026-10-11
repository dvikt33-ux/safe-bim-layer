"""One-shot live probe contracts. Entire suite is offline and token-free."""
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.apa_sync import live_receipt_probe as probe
from scripts.apa_sync import receipt_bridge as bridge

TASK = "APA-P70.A01.S01"
NOTICE = "APA-RECEIPT-EVENT-APA-P70-A01-S01"
EVENT = {"event_id": "apa-notice-test-0001", "task_id": NOTICE,
         "source": "apa:receipt-bridge:git-verified", "status": "INFO",
         "phase": "SOURCE", "summary": "Verified receipt for " + TASK,
         "evidence_urls": ["https://github.com/dvikt33-ux/safe-bim-layer/blob/" +
                           "a" * 40 + "/docs/research/apa-results/receipts/a.json"]}
TS = "1791721617.730099"


def row(seq=23, *, conflict=False):
    return {"seq": seq, "event_id": EVENT["event_id"],
            "slack_ts": TS, "task_id": NOTICE, "conflict": conflict,
            "payload": dict(EVENT)}


def response(*, changes, cursor):
    return {"changes": changes, "next_cursor": cursor}


def local_api(url):
    if url == "/health":
        return {"ok": True, "mode": "read_only_local"}
    if url.startswith("/v1/changes?after=0"):
        return response(changes=[{"seq": 22, "event_id": "old-event"}], cursor=22)
    if url.startswith("/v1/wait?after=22"):
        return response(changes=[row()], cursor=23)
    raise AssertionError("Unexpected local API " + url)


class LiveProbeTests(unittest.TestCase):
    def test_health_pass(self):
        probe.healthy(lambda _: {"ok": True, "mode": "read_only_local"})

    def test_health_false_blocks(self):
        with self.assertRaisesRegex(bridge.BridgeError, "not healthy"):
            probe.healthy(lambda _: {"ok": False, "mode": "read_only_local"})

    def test_health_wrong_mode_blocks(self):
        with self.assertRaisesRegex(bridge.BridgeError, "not healthy"):
            probe.healthy(lambda _: {"ok": True, "mode": "writable"})

    def test_change_page_valid(self):
        out = probe.read_changes(21, lambda _: response(changes=[row(22)], cursor=22))
        self.assertEqual(out["next_cursor"], 22)

    def test_nonmonotonic_seq_rejected(self):
        with self.assertRaisesRegex(bridge.BridgeError, "nonmonotonic"):
            probe.read_changes(22, lambda _: response(changes=[row(22)], cursor=22))

    def test_cursor_mismatch_rejected(self):
        with self.assertRaisesRegex(bridge.BridgeError, "cursor"):
            probe.read_changes(21, lambda _: response(changes=[row(22)], cursor=23))

    def test_scan_ledger_finds_existing_delivery(self):
        last, matches = probe.scan_ledger(EVENT["event_id"], lambda _: response(
            changes=[row(23)], cursor=23))
        self.assertEqual(last, 23)
        self.assertEqual(len(matches), 1)

    def test_scan_ledger_paginates_and_preserves_cursor(self):
        calls = []
        def get(url):
            calls.append(url)
            if "after=0" in url:
                return response(changes=[{"seq": i, "event_id": "other"}
                                         for i in range(1, 201)], cursor=200)
            return response(changes=[row(201)], cursor=201)
        cursor, matches = probe.scan_ledger(EVENT["event_id"], get)
        self.assertEqual(cursor, 201)
        self.assertEqual(len(matches), 1)
        self.assertEqual(len(calls), 2)

    def test_validate_fresh_row_pass(self):
        probe.validate_row(row(), EVENT, TS)

    def test_validate_conflict_blocks(self):
        with self.assertRaisesRegex(bridge.BridgeError, "conflict"):
            probe.validate_row(row(conflict=True), EVENT, TS)

    def test_validate_slack_timestamp_mismatch_blocks(self):
        with self.assertRaisesRegex(bridge.BridgeError, "Slack readback"):
            probe.validate_row(row(), EVENT, "wrong-ts")

    def test_validate_payload_mismatch_blocks(self):
        changed = row()
        changed["payload"]["summary"] = "tampered"
        with self.assertRaisesRegex(bridge.BridgeError, "payload mismatch"):
            probe.validate_row(changed, EVENT, TS)

    def test_wait_for_new_delivery_pass(self):
        result = probe.wait_for_fresh(EVENT, 22, TS, local_api, max_waits=1)
        self.assertEqual(result, {"seq": 23, "cursor": 23, "conflict": False})

    def test_wait_without_event_fails_closed(self):
        with self.assertRaisesRegex(bridge.BridgeError, "not observed"):
            probe.wait_for_fresh(EVENT, 22, TS, lambda _: response(
                changes=[], cursor=22), max_waits=1)

    def test_preflight_never_sends(self):
        with patch.object(probe.bridge, "verify_receipt", return_value={}):
            with patch.object(probe.bridge, "notification", return_value=EVENT):
                with patch.object(probe.bridge, "publish_with_outbox",
                                  side_effect=AssertionError("Unexpected Slack send")):
                    result = probe.run("a" * 40, TASK, "anything", publish=False, get=local_api)
        self.assertEqual(result["status"], "PREFLIGHT_PASS_NO_POST")
        self.assertEqual(result["baseline_cursor"], 22)

    def test_publish_correlates_one_fresh_delivery(self):
        with patch.object(probe.bridge, "verify_receipt", return_value={}):
            with patch.object(probe.bridge, "notification", return_value=EVENT):
                with patch.object(probe.bridge, "publish_with_outbox",
                                  return_value={"published": True, "slack_ts": TS}) as send:
                    with patch.object(probe.bridge, "find_notification",
                                      return_value={"slack_ts": TS, "channel_id": bridge.CHANNEL}):
                        with patch.dict(os.environ, {"SLACK_BOT_TOKEN": "xoxb-fake-offline"}):
                            result = probe.run("a" * 40, TASK, "anything", publish=True,
                                               get=local_api)
        self.assertEqual(result["status"], "FRESH_LIVE_PASS")
        self.assertEqual((result["seq"], result["cursor"]), (23, 23))
        send.assert_called_once()

    def test_prior_delivery_prevents_second_post(self):
        def api(url):
            if url == "/health":
                return {"ok": True, "mode": "read_only_local"}
            return response(changes=[row(23)], cursor=23)
        with patch.object(probe.bridge, "verify_receipt", return_value={}):
            with patch.object(probe.bridge, "notification", return_value=EVENT):
                with patch.object(probe.bridge, "publish_with_outbox",
                                  side_effect=AssertionError("Not expected")):
                    with self.assertRaisesRegex(bridge.BridgeError, "already present"):
                        probe.run("a" * 40, TASK, "anything", publish=True, get=api)

    def test_missing_bot_token_refuses_noninteractive(self):
        with patch.object(probe.bridge, "verify_receipt", return_value={}):
            with patch.object(probe.bridge, "notification", return_value=EVENT):
                with patch.dict(os.environ, {"SLACK_BOT_TOKEN": ""}):
                    with patch.object(probe.os, "isatty", return_value=False):
                        with self.assertRaisesRegex(bridge.BridgeError, "token unavailable"):
                            probe.run("a" * 40, TASK, "anything", publish=True, get=local_api)

    def test_nonfresh_ack_is_not_live_pass(self):
        with patch.object(probe.bridge, "verify_receipt", return_value={}):
            with patch.object(probe.bridge, "notification", return_value=EVENT):
                with patch.object(probe.bridge, "publish_with_outbox",
                                  return_value={"published": False, "already_recorded": True}):
                    with patch.object(probe.bridge, "find_notification",
                                      return_value={"slack_ts": TS}):
                        with patch.dict(os.environ, {"SLACK_BOT_TOKEN": "xoxb-fake-offline"}):
                            with self.assertRaisesRegex(bridge.BridgeError, "cannot claim fresh"):
                                probe.run("a" * 40, TASK, "anything", publish=True,
                                          get=local_api)


if __name__ == "__main__":
    unittest.main()
