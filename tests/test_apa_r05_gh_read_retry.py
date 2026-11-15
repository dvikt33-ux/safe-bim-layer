"""Fail-closed GitHub transport retry tests: no Archicad calls or model writes."""
import subprocess
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import apa_ac29_autonomous_job_bridge as bridge


def response(code=0, error=b"", data=b'{"ok":true}'):
    return subprocess.CompletedProcess(args=["gh", "api"], returncode=code,
                                       stdout=data, stderr=error)


class GitHubReadRetryTests(unittest.TestCase):
    def test_transport_tls_recovered_on_get(self):
        with patch.object(bridge.subprocess, "run", side_effect=[
                response(1, b'gh: Get "https://api.github.com": net/http: TLS handshake timeout'),
                response()]) as run, patch.object(bridge.time, "sleep") as sleep:
            self.assertTrue(bridge.gh_api("repos/example/read")["ok"])
            self.assertEqual(run.call_count, 2)
            sleep.assert_called_once_with(0.4)

    def test_eof_recovered_after_two_get_failures(self):
        with patch.object(bridge.subprocess, "run", side_effect=[
                response(1, b'gh: Get "https://api.github.com": EOF'),
                response(1, b'gh: unexpected EOF'), response()]) as run, \
                patch.object(bridge.time, "sleep") as sleep:
            self.assertTrue(bridge.gh_api("repos/example/read")["ok"])
            self.assertEqual(run.call_count, 3)
            self.assertEqual(sleep.call_count, 2)

    def test_read_timeout_is_bounded_and_retried(self):
        with patch.object(bridge.subprocess, "run", side_effect=[
                subprocess.TimeoutExpired(["gh", "api"], 50), response()]) as run, \
                patch.object(bridge.time, "sleep"):
            self.assertTrue(bridge.gh_api("repos/example/read")["ok"])
            self.assertEqual(run.call_count, 2)

    def test_404_allowed_missing_does_not_retry(self):
        with patch.object(bridge.subprocess, "run",
                          return_value=response(1, b"gh: Not Found (HTTP 404)")) as run, \
                patch.object(bridge.time, "sleep") as sleep:
            self.assertIsNone(bridge.gh_api("repos/example/missing", allow_missing=True))
            run.assert_called_once()
            sleep.assert_not_called()

    def test_403_does_not_retry(self):
        with patch.object(bridge.subprocess, "run",
                          return_value=response(1, b"gh: forbidden (HTTP 403)")) as run, \
                patch.object(bridge.time, "sleep") as sleep:
            with self.assertRaisesRegex(ValueError, "GITHUB_UNAVAILABLE"):
                bridge.gh_api("repos/example/read")
            run.assert_called_once()
            sleep.assert_not_called()

    def test_http_failure_is_not_classified_as_transport_even_with_eof_in_message(self):
        with patch.object(bridge.subprocess, "run",
                          return_value=response(1, b"gh: unexpected EOF (HTTP 403)")) as run, \
                patch.object(bridge.time, "sleep") as sleep:
            with self.assertRaisesRegex(ValueError, "GITHUB_UNAVAILABLE"):
                bridge.gh_api("repos/example/read")
            run.assert_called_once()
            sleep.assert_not_called()

    def test_put_is_never_automatically_replayed(self):
        with patch.object(bridge.subprocess, "run",
                          return_value=response(1, b"gh: unexpected EOF")) as run, \
                patch.object(bridge.time, "sleep") as sleep:
            with self.assertRaisesRegex(ValueError, "GITHUB_UNAVAILABLE"):
                bridge.gh_api("repos/example/file", body=Path("existing-manifest.json"))
            run.assert_called_once()
            sleep.assert_not_called()

    def test_get_stops_after_three_transient_errors(self):
        with patch.object(bridge.subprocess, "run",
                          return_value=response(1, b"gh: TLS handshake timeout")) as run, \
                patch.object(bridge.time, "sleep") as sleep:
            with self.assertRaisesRegex(ValueError, "GITHUB_UNAVAILABLE"):
                bridge.gh_api("repos/example/read")
            self.assertEqual(run.call_count, 3)
            self.assertEqual(sleep.call_count, 2)

    def test_success_requires_valid_json(self):
        with patch.object(bridge.subprocess, "run", return_value=response(data=b"{")) as run, \
                patch.object(bridge.time, "sleep") as sleep:
            with self.assertRaises(ValueError):
                bridge.gh_api("repos/example/read")
            run.assert_called_once()
            sleep.assert_not_called()


if __name__ == "__main__":
    unittest.main()
