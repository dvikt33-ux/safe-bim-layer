"""R05: exact-PLN auto port selection; no native model operations."""
import importlib.util
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

ROOT = Path(os.environ.get("APA_TEST_ROOT", Path(__file__).resolve().parents[1]))
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
MODULE = Path(os.environ.get("APA_TEST_MODULE", ROOT / "scripts" / "apa_r03_mailbox.py"))
spec = importlib.util.spec_from_file_location("apa_r03_mailbox_autoport_under_test", MODULE)
mailbox = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mailbox)
EXPECTED = Path(r"C:\projects\chosen\test.pln")
UNRELATED = Path(r"C:\projects\other\test.pln")
def info(path):
    return {"projectPath": str(path), "isUntitled": False, "isTeamwork": False}

class TestExactProjectPort(unittest.TestCase):
    def test_only_matching_process_gets_expensive_listener_check(self):
        def api(port, command, params, timeout=2):
            self.assertEqual(command, "GetProjectInfo")
            return info(EXPECTED if port == 19723 else UNRELATED)
        with patch.object(mailbox, "project_ports", return_value=[19728, 19723]), \
             patch.object(mailbox.group.R, "tapir", side_effect=api), \
             patch.object(mailbox, "listener", return_value={"pid": 123, "startedAt": "fixed"}) as listener:
            self.assertEqual(mailbox.required_test_port(EXPECTED), 19723)
            self.assertEqual(listener.call_count, 2)

    def test_wrong_active_project_does_not_override_target(self):
        with patch.object(mailbox, "project_ports", return_value=[19728]), \
             patch.object(mailbox.group.R, "tapir", return_value=info(UNRELATED)), \
             patch.object(mailbox, "listener") as listener:
            self.assertIsNone(mailbox.open_test_port(EXPECTED))
            listener.assert_not_called()

    def test_missing_target_is_blocked_without_write(self):
        with patch.object(mailbox, "open_test_port", return_value=None):
            with self.assertRaisesRegex(ValueError, "R03_MAILBOX_EXACT_PROJECT_NOT_OPEN"):
                mailbox.required_test_port(EXPECTED)

    def test_duplicate_exact_projects_are_ambiguous(self):
        with patch.object(mailbox, "project_ports", return_value=[19723, 19728]), \
             patch.object(mailbox.group.R, "tapir", return_value=info(EXPECTED)), \
             patch.object(mailbox, "listener", return_value={"pid": 123, "startedAt": "fixed"}):
            with self.assertRaisesRegex(ValueError, "R03_MAILBOX_EXACT_PROJECT_OPEN_IN_MULTIPLE_INSTANCES"):
                mailbox.open_test_port(EXPECTED)

    def test_switch_during_readback_is_rejected(self):
        replies = [info(EXPECTED), info(UNRELATED)]
        with patch.object(mailbox, "project_ports", return_value=[19723]), \
             patch.object(mailbox.group.R, "tapir", side_effect=lambda *a, **k: replies.pop(0)), \
             patch.object(mailbox, "listener", return_value={"pid": 123, "startedAt": "fixed"}):
            self.assertIsNone(mailbox.open_test_port(EXPECTED))

    def test_stale_explicit_port_is_overridden_before_fetch(self):
        class Halt(Exception):
            pass
        with TemporaryDirectory() as temp:
            # GitHub Windows runners can resolve temporary paths through a junction.
            folder = Path(temp).resolve()
            profile = folder / "mailbox-profile.json"
            profile.write_text("{}", encoding="utf-8")
            campaign = mailbox.Campaign.__new__(mailbox.Campaign)
            campaign.path = profile
            campaign.history = folder / "history"
            campaign.target = "r03-autotest"
            campaign.release = {"revision": "test"}
            campaign.project = EXPECTED
            campaign.phase = lambda _: "PLAN"
            observed = []
            def stop_before_fetch(*a):
                observed.append(sys._getframe(1).f_locals["port"])
                raise Halt()
            campaign.fetch = stop_before_fetch
            with patch.object(mailbox, "required_test_port", return_value=19728) as resolve:
                with self.assertRaises(Halt):
                    campaign.process(object(), "r03-autotest-plan", port=19723)
                resolve.assert_called_once_with(EXPECTED)
                self.assertEqual(observed, [19728])
                self.assertFalse(campaign.history.exists())

if __name__ == "__main__":
    unittest.main()