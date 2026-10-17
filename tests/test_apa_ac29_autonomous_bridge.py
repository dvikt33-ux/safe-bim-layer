"""Only new GitHub bridge authorization, deduplication and ingress checks."""
from datetime import datetime, timedelta, timezone
import sys
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import apa_ac29_autonomous_job_bridge as bridge


def sample(action="BDD114_ROOF_FINALIZE", name="bdd114-roof-20261017"):
    now = datetime.now(timezone.utc)
    stamp = lambda value: value.strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "schema": "APA_AC29_AUTONOMOUS_JOB_V1",
        "jobId": name,
        "action": action,
        "createdAt": stamp(now-timedelta(seconds=30)),
        "expiresAt": stamp(now+timedelta(hours=2)),
        "projectSha256": bridge.BASE_SHA,
        "sourceTask": None,
    }


class GateTests(TestCase):
    def test_source_review_only_job_is_accepted(self):
        m = sample()
        self.assertEqual(bridge.validate_job(m, m["jobId"])["action"],
                         "BDD114_ROOF_FINALIZE")

    def test_no_unreviewed_write_action(self):
        m = sample()
        m["action"] = "CREATE_COLUMNS"
        with self.assertRaisesRegex(ValueError, "JOB_ACTION_OR_TARGET_NOT_ALLOWED"):
            bridge.validate_job(m, m["jobId"])

    def test_no_foreign_pln_hash(self):
        m = sample()
        m["projectSha256"] = "0"*64
        with self.assertRaisesRegex(ValueError, "JOB_ACTION_OR_TARGET_NOT_ALLOWED"):
            bridge.validate_job(m, m["jobId"])

    def test_no_unpinned_source_task(self):
        m = sample("SOURCE_QUALIFIED_NATIVE_READ")
        m["sourceTask"] = {"repo": "dvikt33-ux/safe-bim-layer",
                           "ref": "main",
                           "path": "examples/accelerator/bdd-house.json",
                           "blobSha1": "a"*40}
        with self.assertRaisesRegex(ValueError, "READ_TASK_NOT_PINNED"):
            bridge.validate_job(m, m["jobId"])

    def test_no_replay_when_attempt_exists(self):
        with unittest.mock.patch.object(bridge, "STATE") as state:
            # Only durable-report publication is allowed after an attempt.
            with unittest.mock.patch.object(bridge, "remote_json", side_effect=AssertionError("REEXECUTED")):
                with unittest.mock.patch.object(bridge, "upload_result", return_value=None):
                    with unittest.mock.patch("pathlib.Path.is_dir", return_value=True):
                        with unittest.mock.patch("pathlib.Path.exists", return_value=False):
                            bridge.process_job("bdd114-roof-20261017")


if __name__ == "__main__":
    unittest.main()
