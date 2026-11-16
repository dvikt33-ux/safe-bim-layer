"""Multi-instance discovery contract tests. Entirely offline; no Archicad calls."""
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from apa_archicad_instances import ArchicadInstanceDiscovery, inspect


PROJECT = str((Path.cwd() / "APA_TEST.pln").resolve())


def identity(port):
    return {"product": {"version": 30, "buildNumber": 3001},
            "project": {"projectPath": PROJECT, "isUntitled": False, "isTeamwork": False},
            "addon": {"version": "2.0.0"}}


class InstanceTests(unittest.TestCase):
    def setUp(self):
        self.transport = Mock(side_effect=identity)
        self.client = ArchicadInstanceDiscovery(transport=self.transport)

    def test_list_port_order_and_no_auto_selection(self):
        result = self.client.perform("list", [19723, 19724])
        self.assertEqual(result["status"], "APA_INSTANCES_SCANNED")
        self.assertEqual([r["port"] for r in result["instances"]], [19723, 19724])
        self.assertFalse(result["autoSelection"])
        self.assertEqual(result["modelWrites"], 0)
        self.assertEqual(self.transport.call_count, 2)

    def test_match_pinned(self):
        result = self.client.perform("match", [19724], PROJECT, 30, "2.0.0")
        self.assertEqual(result["status"], "APA_INSTANCE_IDENTITY_MATCH")
        self.assertFalse(result["writePermission"])
        self.assertFalse(result["nativeReadbackVerified"])

    def test_wrong_project_blocked(self):
        self.assertEqual(self.client.perform("match", [19724], str((Path.cwd() / "OTHER.pln").resolve()), 30, "2.0.0")["status"], "BLOCKED")

    def test_wrong_version_blocked(self):
        self.assertEqual(self.client.perform("match", [19723], PROJECT, 29, "2.0.0")["reason"],
                         "APA_DISCOVERY_WRONG_INSTANCE")

    def test_wrong_addon_blocked(self):
        self.assertEqual(self.client.perform("match", [19723], PROJECT, 30, "1.5.10")["status"], "BLOCKED")

    def test_multi_port_never_auto_selects_target(self):
        self.assertEqual(self.client.perform("match", [19723, 19724], PROJECT, 30, "2.0.0")["status"], "BLOCKED")
        self.transport.assert_not_called()

    def test_duplicate_port_blocked_before_transport(self):
        self.assertEqual(self.client.perform("list", [19723, 19723])["status"], "BLOCKED")
        self.transport.assert_not_called()

    def test_untrusted_port_blocked_before_transport(self):
        self.assertEqual(self.client.perform("list", [3003])["reason"], "APA_DISCOVERY_PORT_RANGE_INVALID")
        self.transport.assert_not_called()

    def test_unapproved_operation_blocked(self):
        self.assertEqual(self.client.perform("execute", [19723])["status"], "BLOCKED")
        self.transport.assert_not_called()

    def test_metadata_must_have_solo_project_and_tapir(self):
        def broken(port):
            raw = identity(port)
            raw["project"]["isTeamwork"] = True
            return raw
        self.client.transport = broken
        self.assertEqual(self.client.perform("list", [19723])["instances"][0]["status"], "UNAVAILABLE")

    def test_connection_failure_reports_not_verified(self):
        self.client.transport = Mock(side_effect=ConnectionError("connection refused"))
        row = self.client.perform("list", [19723])
        self.assertEqual(row["instances"][0]["status"], "UNAVAILABLE")
        self.assertNotIn("projectPath", row["instances"][0])

    def test_bool_port_denied(self):
        self.assertEqual(self.client.perform("list", [True])["status"], "BLOCKED")

    def test_no_writes_by_calls(self):
        self.client.perform("list", [19723])
        self.client.perform("match", [19723], PROJECT, 30, "2.0.0")
        self.assertEqual(self.transport.call_count, 2)


if __name__ == "__main__":
    unittest.main()
