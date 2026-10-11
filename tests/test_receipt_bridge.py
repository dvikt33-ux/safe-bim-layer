"""No network, no Slack tokens, no GitHub writes, no user project dependencies."""
import hashlib
import json
import pathlib
import sys
import types
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.apa_sync import receipt_bridge as b

TASK = "APA-P70.A01.S01"
COMMIT = "a" * 40
REPORT_COMMIT = "b" * 40
REPORT_PATH = "docs/research/apa-results/runs/2026-10-11/test/REPORT.md"
RECEIPT_PATH = "docs/research/apa-results/receipts/APA-RUN-test12345678.json"
REPORT = f"# {TASK}\nThis is an immutable test report\n".encode()
ART = "ART-P70-RECEIPT-TEST"


def fixture():
    receipt = {
        "schema": "APA_PUBLISH_RECEIPT_V1", "status": "DONE_PUBLISHED",
        "run_id": "APA-RUN-test12345678", "indexed": True, "readback_verified": True,
        "report_path": REPORT_PATH, "report_commit_sha": REPORT_COMMIT,
        "report_sha256": hashlib.sha256(REPORT).hexdigest(),
        "idempotency_key": "sha256:" + "d" * 64,
    }
    plan = {
        "schema": "APA_PROJECT_PLAN_V1", "repository": b.REPO,
        "canonical_branch": b.BRANCH,
        "tasks": {TASK: {"id": TASK, "status": "PARTIAL", "evidence": [ART]}},
        "artifacts": {ART: {"id": ART, "uri": RECEIPT_PATH, "kind": "RECEIPT"}},
    }
    files = {
        (b.PLAN_PATH, COMMIT): json.dumps(plan).encode(),
        (RECEIPT_PATH, COMMIT): json.dumps(receipt).encode(),
        (REPORT_PATH, REPORT_COMMIT): REPORT,
    }
    return files, plan, receipt


class FakeReader:
    def __init__(self, files):
        self.files = files
        self.read_calls = []

    def read(self, path, ref):
        self.read_calls.append((path, ref))
        return self.files[path, ref]


class BridgeTests(unittest.TestCase):
    def test_good_receipt_is_info_even_if_task_partial(self):
        files, _, _ = fixture()
        proof = b.verify_receipt(FakeReader(files), COMMIT, TASK, RECEIPT_PATH)
        ev = b.notification(proof)
        self.assertEqual((ev["status"], ev["phase"]), ("INFO", "SOURCE"))
        self.assertEqual(ev["task_id"], TASK)
        self.assertIn("PARTIAL", ev["summary"])
        self.assertEqual(len(ev["evidence_urls"]), 2)
        self.assertEqual(ev["event_id"], b.notification(proof)["event_id"])
        self.assertTrue(ev["evidence_urls"][0].startswith(f"https://github.com/{b.REPO}/blob/{COMMIT}/"))

    def test_mismatch_report_hash_rejected(self):
        files, _, _ = fixture()
        files[(REPORT_PATH, REPORT_COMMIT)] += b"TAMPER"
        with self.assertRaisesRegex(b.BridgeError, "SHA256"):
            b.verify_receipt(FakeReader(files), COMMIT, TASK, RECEIPT_PATH)

    def test_fake_done_without_readback_rejected(self):
        files, _, receipt = fixture()
        receipt["readback_verified"] = False
        files[(RECEIPT_PATH, COMMIT)] = json.dumps(receipt).encode()
        with self.assertRaisesRegex(b.BridgeError, "readback"):
            b.verify_receipt(FakeReader(files), COMMIT, TASK, RECEIPT_PATH)

    def test_unregistered_receipt_rejected(self):
        files, plan, _ = fixture()
        plan["tasks"][TASK]["evidence"] = []
        files[(b.PLAN_PATH, COMMIT)] = json.dumps(plan).encode()
        with self.assertRaisesRegex(b.BridgeError, "not registered"):
            b.verify_receipt(FakeReader(files), COMMIT, TASK, RECEIPT_PATH)

    def test_different_task_cannot_claim_another_receipt(self):
        files, plan, _ = fixture()
        other = "APA-P00.A02.S04"
        plan["tasks"][other] = {"id": other, "status": "PARTIAL", "evidence": [ART]}
        files[(b.PLAN_PATH, COMMIT)] = json.dumps(plan).encode()
        with self.assertRaisesRegex(b.BridgeError, "report does not bind"):
            b.verify_receipt(FakeReader(files), COMMIT, other, RECEIPT_PATH)

    def test_unpinned_commit_and_traversal_blocked(self):
        files, _, _ = fixture()
        for bad_sha in ("main", "a" * 39, "A" * 40, "../" + "a" * 40):
            with self.subTest(bad_sha=bad_sha), self.assertRaises(b.BridgeError):
                b.verify_receipt(FakeReader(files), bad_sha, TASK, RECEIPT_PATH)
        for bad_path in ("docs/research/apa-results/receipts/../bad.json",
                         "docs/research/apa-results/receipts/%2E%2E/bad.json",
                         "https://evil.com/receipts/a.json", "docs/research/apa-results/receipts/f.txt"):
            with self.subTest(bad_path=bad_path), self.assertRaises(b.BridgeError):
                b.verify_receipt(FakeReader(files), COMMIT, TASK, bad_path)

    def test_different_github_host_unmatched(self):
        bad = "https://evil.example/dvikt33-ux/safe-bim-layer/blob/" + b.BRANCH + "/" + RECEIPT_PATH
        self.assertIsNone(b.artifact_path(bad))
        self.assertEqual(b.artifact_path(RECEIPT_PATH), RECEIPT_PATH)

    def test_receipt_path_must_match_run_id(self):
        files, _, receipt = fixture()
        receipt["run_id"] = "APA-RUN-wrong1234567"
        files[(RECEIPT_PATH, COMMIT)] = json.dumps(receipt).encode()
        with self.assertRaisesRegex(b.BridgeError, "run ID"):
            b.verify_receipt(FakeReader(files), COMMIT, TASK, RECEIPT_PATH)

    def test_missing_receipt_idempotency_key_rejected(self):
        files, _, receipt = fixture()
        receipt.pop("idempotency_key")
        files[(RECEIPT_PATH, COMMIT)] = json.dumps(receipt).encode()
        with self.assertRaisesRegex(b.BridgeError, "idempotency key"):
            b.verify_receipt(FakeReader(files), COMMIT, TASK, RECEIPT_PATH)

    def test_duplicate_slack_notification_not_resent(self):
        files, _, _ = fixture()
        event = b.notification(b.verify_receipt(FakeReader(files), COMMIT, TASK, RECEIPT_PATH))
        calls = []
        class FakeSlack:
            def conversations_history(self, **kwargs):
                calls.append("history")
                return {"messages": [{"text": "DUMMY EVENT"}], "response_metadata": {}}
        coordinator = types.ModuleType("scripts.apa_sync.coordinator")
        coordinator.parse_event = lambda t: event if t == "DUMMY EVENT" else None
        step_sync = types.ModuleType("scripts.apa_sync.step_sync")
        step_sync._client = lambda: FakeSlack()
        step_sync.after_step = lambda *args, **kwargs: calls.append("POST")
        with patch.dict(sys.modules, {"scripts.apa_sync.coordinator": coordinator,
                                      "scripts.apa_sync.step_sync": step_sync}):
            outcome = b.send_notification(event)
        self.assertEqual(outcome, {"published": False, "already_present": True})
        self.assertEqual(calls, ["history"])

    def test_slack_notification_send_only_on_explicit_call(self):
        files, _, _ = fixture()
        event = b.notification(b.verify_receipt(FakeReader(files), COMMIT, TASK, RECEIPT_PATH))
        calls = []
        class FakeSlack:
            def conversations_history(self, **kwargs):
                calls.append("history")
                return {"messages": [], "response_metadata": {}}
        coordinator = types.ModuleType("scripts.apa_sync.coordinator")
        coordinator.parse_event = lambda t: None
        step_sync = types.ModuleType("scripts.apa_sync.step_sync")
        step_sync._client = lambda: FakeSlack()
        step_sync.after_step = lambda channel, event, publish: calls.append("POST") or {"published": True}
        with patch.dict(sys.modules, {"scripts.apa_sync.coordinator": coordinator,
                                      "scripts.apa_sync.step_sync": step_sync}):
            outcome = b.send_notification(event)
        self.assertEqual(outcome, {"published": True})
        self.assertEqual(calls, ["history", "POST"])

    def test_local_scan_only_reports_candidates(self):
        _, plan, _ = fixture()
        row = {"seq": 22, "event_id": "apa-test-22", "task_id": TASK, "conflict": False,
               "payload": {"event_id": "apa-test-22", "evidence_urls": [RECEIPT_PATH, "https://evil.example/fake"]}}
        def api(url):
            self.assertTrue(url.startswith("http://127.0.0.1:8765/"))
            return {"changes": [row], "next_cursor": 22}
        result = b.summarize_changes(api, plan, after=21)
        self.assertEqual(result["next_cursor"], 22)
        self.assertEqual(result["registered_evidence_matches"], 1)
        self.assertEqual(result["unmatched_evidence"], 1)
        self.assertEqual(result["authority"], "READ_ONLY_CANDIDATES_NOT_TASK_STATUS")
        self.assertEqual(plan["tasks"][TASK]["status"], "PARTIAL")

    def test_local_scan_rejects_reused_cursor(self):
        _, plan, _ = fixture()
        with self.assertRaisesRegex(b.BridgeError, "seq"):
            b.summarize_changes(lambda _: {"changes": [{"seq": 21}], "next_cursor": 21}, plan, after=21)

    def test_local_scan_rejects_mismatched_payload(self):
        _, plan, _ = fixture()
        row = {"seq": 22, "event_id": "one", "task_id": TASK,
               "payload": {"event_id": "two", "evidence_urls": []}}
        with self.assertRaisesRegex(b.BridgeError, "mismatch"):
            b.summarize_changes(lambda _: {"changes": [row], "next_cursor": 22}, plan, after=21)

    def test_notify_restricts_channel_without_side_effect(self):
        with self.assertRaisesRegex(b.BridgeError, "restricted"):
            b.send_notification({"event_id": "any"}, channel="OTHER")

    def test_reader_endpoint_cannot_be_injected(self):
        fake = lambda url, **kwargs: {"type": "file", "encoding": "base64", "content": "YWJj"}
        with patch.object(b, "http_json", side_effect=fake) as mocked:
            val = b.GitHubReader().read(b.PLAN_PATH, COMMIT)
            self.assertEqual(val, b"abc")
            self.assertEqual(mocked.call_args.args[0], b.API + b.PLAN_PATH + "?ref=" + COMMIT)
        with self.assertRaises(b.BridgeError):
            b.GitHubReader().read("https://evil.example/a", COMMIT)


if __name__ == "__main__":
    unittest.main()
