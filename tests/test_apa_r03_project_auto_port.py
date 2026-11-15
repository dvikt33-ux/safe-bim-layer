"""Exact-PLN auto port selection with synthetic listener readback."""
from pathlib import Path
import sys
import unittest
from unittest.mock import call, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import apa_r03_mailbox as mailbox

EXPECTED = Path(r"C:\projects\chosen\test.pln")
UNRELATED = Path(r"C:\projects\other\test.pln")
LISTENER = {"pid": 123, "startedAt": "fixed"}


def info(path):
    return {"projectPath": str(path), "isUntitled": False, "isTeamwork": False}


class TestExactProjectPort(unittest.TestCase):
    def test_exact_path_wins_between_same_named_projects(self):
        with (patch.object(mailbox, "project_ports", return_value=[19728, 19723]),
              patch.object(mailbox.group.R, "tapir", side_effect=[info(UNRELATED), info(EXPECTED), info(EXPECTED)]) as api,
              patch.object(mailbox, "listener", return_value=LISTENER) as listener):
            self.assertEqual(mailbox.open_test_port(EXPECTED), 19723)
        self.assertEqual(api.call_args_list,
                         [call(port, "GetProjectInfo", {}, timeout=2) for port in (19728, 19723, 19723)])
        self.assertEqual(listener.call_args_list, [call(19728), call(19723), call(19723)])

    def test_wrong_active_project_does_not_override_target(self):
        with patch.object(mailbox, "project_ports", return_value=[19728]), \
             patch.object(mailbox.group.R, "tapir", return_value=info(UNRELATED)), \
             patch.object(mailbox, "listener", return_value=LISTENER):
            self.assertIsNone(mailbox.open_test_port(EXPECTED))

    def test_unverified_listener_receives_no_api_request(self):
        with (patch.object(mailbox, "project_ports", return_value=[19728]),
              patch.object(mailbox.group.R, "tapir") as api,
              patch.object(mailbox, "listener", side_effect=ValueError("unknown owner"))):
            self.assertIsNone(mailbox.open_test_port(EXPECTED))
        api.assert_not_called()

    def test_duplicate_exact_projects_are_ambiguous(self):
        with patch.object(mailbox, "project_ports", return_value=[19723, 19728]), \
             patch.object(mailbox.group.R, "tapir", return_value=info(EXPECTED)), \
             patch.object(mailbox, "listener", return_value=LISTENER):
            with self.assertRaisesRegex(ValueError, "R03_MAILBOX_EXACT_PROJECT_OPEN_IN_MULTIPLE_INSTANCES"):
                mailbox.open_test_port(EXPECTED)

    def test_switch_during_readback_is_rejected(self):
        with (patch.object(mailbox, "project_ports", return_value=[19723, 19728]),
              patch.object(mailbox.group.R, "tapir", side_effect=[info(EXPECTED), info(UNRELATED)]) as api,
              patch.object(mailbox, "listener", return_value=LISTENER)):
            with self.assertRaisesRegex(ValueError, "R03_MAILBOX_PROJECT_CHANGED_DURING_DISCOVERY"):
                mailbox.open_test_port(EXPECTED)
        self.assertEqual([args.args[0] for args in api.call_args_list], [19723, 19723])

    def test_same_path_with_replaced_listener_is_rejected(self):
        with (patch.object(mailbox, "project_ports", return_value=[19723]),
              patch.object(mailbox.group.R, "tapir", return_value=info(EXPECTED)),
              patch.object(mailbox, "listener", side_effect=[LISTENER, dict(LISTENER, startedAt="replaced")])):
            with self.assertRaisesRegex(ValueError, "R03_MAILBOX_PROJECT_CHANGED_DURING_DISCOVERY"):
                mailbox.open_test_port(EXPECTED)

if __name__ == "__main__":
    unittest.main()
