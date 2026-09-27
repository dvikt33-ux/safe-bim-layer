import json
import unittest
from unittest.mock import patch, Mock
from pathlib import Path

from controller.client import RuntimeState, SafeBIMClient
from launcher import LaunchAlreadyRunning, LaunchError, launch, runtime_ready


class ControllerClientTests(unittest.TestCase):
    def test_state_mapping(self):
        state = RuntimeState.from_payload({"job_id": "j1", "task": "Дом", "status": "WAITING_USER",
            "step": "Стены", "progress": "2 из 3", "floor": 2, "readback": "Не подтверждён", "enum": "WAITING_USER"})
        self.assertEqual(state.job_id, "j1")
        self.assertEqual(state.floor, 2)

    @patch("controller.client.urllib.request.urlopen")
    def test_explicit_post_and_active_state(self, urlopen):
        response = urlopen.return_value.__enter__.return_value
        response.read.return_value = json.dumps({"job_id": "j1", "status": "PAUSED"}).encode()
        client = SafeBIMClient()
        client.command("pause")
        request = urlopen.call_args.args[0]
        self.assertEqual(request.method, "POST")
        self.assertTrue(request.full_url.endswith("/jobs/active/pause"))

    @patch("launcher.urllib.request.urlopen")
    def test_runtime_ready_accepts_missing_active_job(self, urlopen):
        urlopen.return_value.__enter__.return_value.status = 404
        self.assertTrue(runtime_ready())

    @patch("controller.client.urllib.request.urlopen", side_effect=__import__("urllib.error").error.HTTPError(
        "http://127.0.0.1:19731/state", 404, "Not Found", {}, None))
    def test_missing_active_job_is_connected_idle_state(self, _urlopen):
        state = SafeBIMClient().state()
        self.assertEqual(state.status, "PENDING")
        self.assertEqual(state.enum, "PENDING")

    @patch("launcher.msvcrt.locking", side_effect=OSError("locked"))
    def test_duplicate_launch_lock(self, _locking):
        from launcher import SingleInstance
        with self.assertRaises(LaunchAlreadyRunning):
            with SingleInstance(__import__("pathlib").Path("logs/test.lock")):
                pass

    @patch("controller.app._run_controller")
    def test_launcher_lock_then_controller_same_process_does_not_self_lock(self, run_controller):
        from controller.app import main as controller_main
        with patch("launcher.msvcrt.locking") as locking:
            with __import__("launcher").SingleInstance(Path("logs/self-lock-regression.lock")):
                controller_main(use_lock=False)
        run_controller.assert_called_once_with()
        self.assertEqual(locking.call_count, 2)

    @patch("launcher.msvcrt.locking", side_effect=OSError("locked"))
    def test_second_launcher_is_clean_already_running(self, _locking):
        from launcher import main
        with patch("launcher.configure_logging", return_value=Mock()), \
             patch("launcher.argparse.ArgumentParser.parse_args", return_value=Mock(timeout=1.0)), \
             patch("builtins.print") as printer:
            self.assertEqual(main(), 2)
        printer.assert_called_once()
        self.assertNotIn("Traceback", str(printer.call_args))

    @patch("launcher.wait_ready", return_value=True)
    @patch("launcher.start_runtime")
    @patch("launcher.runtime_listening", return_value=False)
    def test_launcher_starts_runtime_when_missing(self, _listening, start, _ready):
        self.assertTrue(launch(log=Mock()))
        start.assert_called_once()

    @patch("launcher.wait_ready", return_value=False)
    @patch("launcher.start_runtime")
    @patch("launcher.runtime_listening", return_value=False)
    def test_launcher_timeout_is_finite_failure(self, _listening, start, _ready):
        with self.assertRaises(LaunchError):
            launch(timeout=.01, log=Mock())
        start.assert_called_once()


if __name__ == "__main__":
    unittest.main()
