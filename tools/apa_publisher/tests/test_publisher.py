"""Offline, no-network regression tests for APA Research OS publisher."""
import base64
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import publisher as p


def request(run_id="APA-RUN-20261010-181500Z-publisher-smoke"):
    return {
        "schema": "APA_PUBLISH_REQUEST_V1",
        "run_id": run_id,
        "plan_id": "APA-P00",
        "action_id": "APA-P00.A03",
        "substep_id": "APA-P00.A03.S03",
        "executor": "github-actions",
        "executor_run_id": "synthetic-test-1",
        "phase": "SYNTHETIC",
        "started_at": "2026-10-10T18:15:00Z",
        "finished_at": "2026-10-10T18:15:01Z",
        "scope": {"repository": p.REPO, "archicad": None},
        "source_revisions": [],
        "inputs": [],
        "claims": [{
            "claim_id": "APA-CLAIM-PUBLISHER-SMOKE",
            "statement": "Synthetic publisher pipeline test, not an Archicad live test",
            "status": "NOT_VERIFIED", "evidence_ids": ["E1"]
        }],
        "evidence": [{
            "evidence_id": "E1", "uri": "https://github.com/dvikt33-ux/safe-bim-layer",
            "kind": "OTHER", "verification": "REPORTED",
            "sha256": None, "source_revision": None
        }],
        "report_markdown": "# Synthetic publisher smoke test\n\nNo PLN/APX/Archicad operation occurred.",
        "next_substep": "APA-P00.A03.S04",
        "safety": {key: False for key in p.SAFETY},
    }


class PublisherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old_cwd = Path.cwd()
        os.chdir(self.temp.name)
        self.root = Path("docs/research/apa-results")
        self.overrides = patch.multiple(
            p, ROOT=self.root, RUNS=self.root / "runs", INBOX=self.root / "inbox",
            RECEIPTS=self.root / "receipts", GENERATED=self.root / "generated",
            PENDING=Path(".apa-publisher-pending.json"))
        self.overrides.start()

    def tearDown(self):
        self.overrides.stop()
        os.chdir(self.old_cwd)
        self.temp.cleanup()

    def test_idempotent_run_and_projection(self):
        r = request()
        p.validate(r)
        a = p.create_run(r)
        b = p.create_run(r)
        self.assertEqual(a, b)
        paths = p.rebuild_indexes()
        state = p.read_json(Path(paths[1]))
        self.assertEqual(state["run_count"], 1)
        self.assertEqual(state["runs"][0]["run_id"], r["run_id"])
        old = Path(paths[0]).read_bytes()
        p.rebuild_indexes()
        self.assertEqual(Path(paths[0]).read_bytes(), old)

    def test_prepare_then_receipt_recovery(self):
        r = request()
        p.INBOX.mkdir(parents=True)
        (p.INBOX / (r["run_id"] + ".json")).write_bytes(p.encoded(r))
        p.prepare()
        self.assertEqual(len(p.read_json(p.PENDING)["entries"]), 1)
        commit = "a" * 40
        p.receipt(commit)
        receipt_path = p.RECEIPTS / (r["run_id"] + ".json")
        first = receipt_path.read_bytes()
        p.receipt("b" * 40)
        self.assertEqual(receipt_path.read_bytes(), first)
        self.assertEqual(p.read_json(receipt_path)["report_commit_sha"], commit)

    def test_immutable_conflict_rejected(self):
        r = request()
        p.create_run(r)
        changed = copy.deepcopy(r)
        changed["report_markdown"] = "# Changed report\n\nA different report must be rejected."
        with self.assertRaisesRegex(p.PublishError, "IMMUTABLE_CONFLICT"):
            p.create_run(changed)
        self.assertIn(b"Synthetic publisher", (p.run_path(r["run_id"]) / "REPORT.md").read_bytes())

    def test_reject_unsafe_request(self):
        cases = []
        r = request()
        r["run_id"] = "../../main"
        cases.append(r)
        r = request()
        r["safety"]["main_modified"] = True
        cases.append(r)
        r = request()
        r["scope"]["repository"] = "attacker/repo"
        cases.append(r)
        r = request()
        r["claims"][0]["status"] = "LIVE_PASS"
        cases.append(r)
        r = request()
        r["claims"][0]["evidence_ids"] = ["unknown"]
        cases.append(r)
        for bad in cases:
            with self.subTest(bad=bad):
                with self.assertRaises(p.PublishError):
                    p.validate(bad)

    def test_duplicate_json_keys_rejected(self):
        path = Path("duplicate.json")
        path.write_text('{"schema":"one","schema":"two"}')
        with self.assertRaisesRegex(p.PublishError, "Duplicate JSON"):
            p.read_json(path)

    def test_github_rest_blob_readback(self):
        raw = b"report content\n"
        sha = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        body = json.dumps({"encoding": "base64", "content": base64.b64encode(raw).decode(),
                           "sha": sha}).encode()
        class Response:
            def __enter__(self):
                return self
            def __exit__(self, *_):
                return False
            def read(self):
                return body
        with patch.dict(os.environ, {"GITHUB_TOKEN": "fake-token"}):
            with patch.object(p, "urlopen", return_value=Response()) as fetch:
                p.api_readback({"docs/research/apa-results/runs/report.md": p.digest(raw)},
                               "a" * 40)
                self.assertEqual(fetch.call_count, 1)
                with self.assertRaisesRegex(p.PublishError, "READBACK_HASH_MISMATCH"):
                    p.api_readback({"docs/research/apa-results/runs/report.md": "0" * 64},
                                   "a" * 40)


if __name__ == "__main__":
    unittest.main()
