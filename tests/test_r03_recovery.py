import base64
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import apa_ac29_autonomous_job_bridge as bridge
from apa_ac29_save_isolation import reservation_owner_exited


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.state = Path(self.tmp.name)
        self.name = "r03-isolated-test"
        self.job = self.state / self.name
        self.job.mkdir()

    def remote_file(self, data):
        return {"type": "file", "sha": bridge.git_sha(data), "encoding": "base64",
                "content": base64.b64encode(data).decode("ascii"), "html_url": "fixture"}

    def test_recovery_cannot_take_over_live_writer(self):
        self.assertFalse(reservation_owner_exited(os.getpid()))

    def test_lost_put_reply_is_reconciled_without_second_put(self):
        report = self.job / "result.json"
        report.write_bytes(b"{}\n")
        stored = None
        put_count = 0

        def contents(endpoint, *, body=None, allow_missing=False):
            nonlocal put_count, stored
            if body is None:
                self.assertTrue(allow_missing)
                self.assertTrue(endpoint.endswith("?ref=main"))
                return stored
            payload = json.loads(body.read_text(encoding="utf-8"))
            self.assertNotIn("sha", payload)
            put_count += 1
            stored = self.remote_file(base64.b64decode(payload["content"]))
            raise subprocess.TimeoutExpired("fixture: lost response", 1)

        with patch.object(bridge, "gh_api", contents):
            bridge.upload_result(self.name, self.job)
            bridge.upload_result(self.name, self.job)
        marker = json.loads((self.job / "published.json").read_text(encoding="utf-8"))
        self.assertEqual(marker["sha"], bridge.git_sha(report.read_bytes()))
        self.assertTrue(marker["verifiedBytes"])
        self.assertEqual(put_count, 1)

    def test_existing_remote_conflict_prevents_put(self):
        (self.job / "result.json").write_bytes(b"{}\n")
        with patch.object(bridge, "gh_api", return_value=self.remote_file(b'{"other":true}')) as api:
            with self.assertRaisesRegex(ValueError, "REMOTE_RESULT_CONFLICT"):
                bridge.upload_result(self.name, self.job)
        self.assertEqual(api.call_count, 1)
        self.assertTrue(api.call_args.kwargs["allow_missing"])
        self.assertFalse((self.job / "published.json").exists())

    def test_durable_attempt_after_restart_yields_unknown_without_running_job(self):
        attempt = self.job / "attempted.json"
        bridge.durable_write(attempt, {"job": self.name, "action": "APPROVED_SCOPED_NATIVE_MUTATION",
                                      "sourceBlob": "a" * 40, "currentProject": str(bridge.WORKING)})
        prior = attempt.read_bytes()
        with (patch.object(bridge, "STATE", self.state),
              patch.object(bridge, "capture_approved_scoped_native_mutation") as execute,
              patch.object(bridge, "remote_json") as read_inbox,
              patch.object(bridge, "upload_result") as publish):
            bridge.process_job(self.name)
            first = (self.job / "result.json").read_bytes()
            bridge.process_job(self.name)
        self.assertEqual(attempt.read_bytes(), prior)
        self.assertEqual((self.job / "result.json").read_bytes(), first)
        outcome = json.loads(first)["result"]
        self.assertEqual(outcome["nativeOutcome"], "UNKNOWN")
        self.assertFalse(outcome["nativeReplayAttempted"])
        self.assertEqual(publish.call_count, 2)
        execute.assert_not_called()
        read_inbox.assert_not_called()

    def test_missing_intent_requires_inspection(self):
        with (patch.object(bridge, "STATE", self.state),
              patch.object(bridge, "upload_result") as publish):
            with self.assertRaisesRegex(ValueError, "WITHOUT_DURABLE_INTENT"):
                bridge.process_job(self.name)
        self.assertFalse((self.job / "result.json").exists())
        publish.assert_not_called()
