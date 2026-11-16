"""Isolation tests for APA Cassis adapter; no Rhino or Archicad required."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock
import hashlib
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from apa_cassis_bridge import CassisControl

ONE = "11111111-1111-1111-1111-111111111111"
TWO = "22222222-2222-2222-2222-222222222222"
OTHER = "33333333-3333-3333-3333-333333333333"


class TestCassisScope(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name) / "experiments"
        root.mkdir()
        self.doc = root / "isolated.ghx"
        self.doc.write_text("<test/>", encoding="utf-8")
        self.profile = root / "profile.json"
        self.profile.write_text(json.dumps({
            "schema": "APA_CASSIS_TEST_V1", "testDocument": str(self.doc),
            "documentSha256": hashlib.sha256(self.doc.read_bytes()).hexdigest(),
            "sliderIds": [ONE, TWO]}), encoding="utf-8")
        self.calls = []

        def transport(name, args):
            self.calls.append((name, args))
            if name == "getdocumentinfo":
                return {"ok": True, "open": True, "file": self.doc.name, "path": str(self.doc)}
            if name == "get_componentcount":
                return {"components": 1, "parameters": 2, "connections": 2}
            if name == "set_component_value":
                return {"success": True, "value": args["value"]}
            return {"success": True}
        self.transport = transport
        self.client = CassisControl(self.profile, transport=transport)

    def tearDown(self):
        self.tmp.cleanup()

    def test_status_checks_live_transport(self):
        out = self.client.perform("status")
        self.assertEqual(out["status"], "CASSIS_CONNECTED")
        self.assertTrue(out["activeDocumentPinned"])
        self.assertTrue(any(name == "getdocumentinfo" for name, _ in self.calls))

    def test_document_read(self):
        self.assertEqual(self.client.perform("document")["status"], "CASSIS_TEST_READ")

    def test_reject_unpinned_component(self):
        out = self.client.perform("set_slider", OTHER, 5000)
        self.assertEqual(out["status"], "BLOCKED")
        self.assertFalse(any(call == "set_component_value" for call, _ in self.calls))

    def test_reject_wrong_document(self):
        real = self.client._transport
        def swapped(name, args):
            if name == "getdocumentinfo":
                return {"ok": True, "open": True, "path": str(self.doc.with_name("other.ghx"))}
            return real(name, args)
        self.client._transport = swapped
        self.assertEqual(self.client.perform("set_slider", ONE, 4000)["status"], "BLOCKED")

    def test_reject_disk_drift(self):
        self.doc.write_text("<changed/>", encoding="utf-8")
        self.assertEqual(self.client.perform("set_slider", ONE, 4000)["status"], "BLOCKED")

    def test_reject_changed_profile(self):
        self.profile.write_text("{}", encoding="utf-8")
        self.assertEqual(self.client.perform("document")["status"], "BLOCKED")

    def test_allow_only_pinned_test_slider(self):
        out = self.client.perform("set_slider", ONE, 5000)
        self.assertEqual(out["status"], "CASSIS_TEST_PARAMETER_SET")
        self.assertTrue(any(name == "set_component_value" for name, _ in self.calls))

    def test_no_arbitrary_tool(self):
        self.assertEqual(self.client.perform("removecomponents")["status"], "BLOCKED")

    def test_no_boolean_value(self):
        self.assertEqual(self.client.perform("set_slider", ONE, True)["status"], "BLOCKED")

    def test_no_unbounded_value(self):
        self.assertEqual(self.client.perform("set_slider", ONE, 9000000)["status"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
