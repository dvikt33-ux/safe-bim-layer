"""Publisher watchdog: pure offline deterministic tests, no GitHub network."""
from datetime import datetime, timedelta, timezone
import pathlib
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import watchdog as wd

T = datetime(2026, 10, 11, 16, 0, tzinfo=timezone.utc)


def run(id=123, status="completed", conclusion="success", age_minutes=2, branch=wd.BRANCH):
    return {"id": id, "head_branch": branch, "status": status,
            "conclusion": conclusion,
            "created_at": (T - timedelta(minutes=age_minutes)).isoformat()}


class PublisherWatchdogTests(unittest.TestCase):
    def test_latest_success(self):
        x = wd.inspect([run()], now=T)
        self.assertEqual(x["health"], "HEALTHY")
        self.assertEqual(x["run_url"], "https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/123")

    def test_latest_success_supersedes_old_failure(self):
        x = wd.inspect([run(1, conclusion="failure", age_minutes=90),
                        run(2, age_minutes=3)], now=T)
        self.assertEqual(x["run_id"], 2)
        self.assertEqual(x["health"], "HEALTHY")

    def test_failed_latest(self):
        self.assertEqual(wd.inspect([run(conclusion="failure")], now=T)["health"], "FAILED")

    def test_cancelled_latest(self):
        self.assertEqual(wd.inspect([run(conclusion="cancelled")], now=T)["health"], "FAILED")

    def test_action_required_latest(self):
        self.assertEqual(wd.inspect([run(conclusion="action_required")], now=T)["health"], "FAILED")

    def test_active_recent(self):
        self.assertEqual(wd.inspect([run(status="in_progress", conclusion=None, age_minutes=15)], now=T)["health"], "RUNNING")

    def test_active_too_old(self):
        self.assertEqual(wd.inspect([run(status="queued", conclusion=None, age_minutes=70)], now=T)["health"], "STUCK")

    def test_active_exact_boundary(self):
        self.assertEqual(wd.inspect([run(status="in_progress", conclusion=None, age_minutes=45)], now=T)["health"], "RUNNING")

    def test_empty_data_rejected(self):
        with self.assertRaisesRegex(wd.WatchdogError, "No canonical"):
            wd.inspect([], now=T)

    def test_wrong_branch_not_used(self):
        with self.assertRaisesRegex(wd.WatchdogError, "No Publisher runs"):
            wd.inspect([run(branch="main")], now=T)

    def test_unknown_status_rejected(self):
        with self.assertRaisesRegex(wd.WatchdogError, "Unknown"):
            wd.inspect([run(status="new")], now=T)

    def test_missing_id_rejected(self):
        bad = run()
        bad.pop("id")
        with self.assertRaisesRegex(wd.WatchdogError, "ID"):
            wd.inspect([bad], now=T)

    def test_future_clock_rejected(self):
        with self.assertRaisesRegex(wd.WatchdogError, "future"):
            wd.inspect([run(age_minutes=-15)], now=T)

    def test_timestamp_missing_timezone_rejected(self):
        bad = run()
        bad["created_at"] = "2026-10-11T16:00:00"
        with self.assertRaisesRegex(wd.WatchdogError, "timezone"):
            wd.inspect([bad], now=T)

    def test_network_requires_token(self):
        with self.assertRaisesRegex(wd.WatchdogError, "TOKEN"):
            wd.fetch_runs("")

    def test_github_fetch_is_branch_scoped_readonly(self):
        class FakeResp:
            def __enter__(self): return self
            def __exit__(self, *_): return False
            def read(self, _): return b'{"workflow_runs":[]}'
        with patch.object(wd, "urlopen", return_value=FakeResp()) as call:
            self.assertEqual(wd.fetch_runs("fake-test-token"), [])
            req = call.call_args.args[0]
            self.assertEqual(req.get_method(), "GET")
            self.assertIn("/actions/workflows/apa-research-publisher.yml/runs?", req.full_url)
            self.assertIn("branch=research%2Fapa-verified-results-hub-20261010", req.full_url)

    def test_overridden_threshold(self):
        x = wd.inspect([run(status="pending", conclusion=None, age_minutes=30)], now=T,
                       max_active_minutes=20)
        self.assertEqual(x["health"], "STUCK")


if __name__ == "__main__":
    unittest.main()
