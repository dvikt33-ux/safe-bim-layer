"""Offline guard/dispatch regression tests for the APA -> Cassis compatibility proxy."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "scripts" / "apa_cassis_compat_gateway.py"
spec = importlib.util.spec_from_file_location("apa_cassis_compat_gateway", SOURCE)
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)


class FakeTransport:
    def __init__(self, document):
        self.document = document
        self.active_path = document
        self.calls = []
        self.fail_next = False

    def call(self, name, arguments):
        self.calls.append((name, arguments))
        if self.fail_next and name != "getdocumentinfo":
            self.fail_next = False
            raise TimeoutError("simulated lost response after dispatch")
        if name == "getdocumentinfo":
            return {"ok": True, "open": True, "path": str(self.active_path),
                    "file": self.active_path.name}
        if name == "get_componentcount":
            return {"success": True, "components": 18,
                    "parameters": 10, "connections": 31}
        if name == "savedocument":
            self.document.write_bytes(self.document.read_bytes() + b"-saved")
        return {"success": True, "tool": name}


class TestCompatibilityGateway(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.exp = self.root / "experiments"
        self.exp.mkdir()
        self.doc = self.exp / "isolated.ghx"
        self.doc.write_bytes(b"<grasshopper-test/>")
        self.profile = self.root / "gh-profile.json"
        self.profile.write_text(json.dumps({
            "schema": "APA_GH_COMPAT_V1",
            "testDocument": str(self.doc),
            "documentSha256": hashlib.sha256(self.doc.read_bytes()).hexdigest(),
            "allowWrites": True,
        }), encoding="utf-8")
        self.fake = FakeTransport(self.doc)
        self.bridge = bridge.GrasshopperGate(
            workdir=self.root, profile=self.profile, transport=self.fake)

    def tearDown(self):
        self.temp.cleanup()

    def intent(self, tool, **arguments):
        return {"tool": tool, "arguments": arguments}

    def test_read_existing_graph_without_mcp_schema_update(self):
        result = self.bridge.perform(
            "gh-read", "gh-read-001", intent=self.intent("get_componentcount"))
        self.assertEqual(result["status"], "COMPLETE")
        self.assertEqual(result["result"]["components"], 18)
        self.assertEqual(result["result"]["connections"], 31)

    def test_read_receipt_is_available_by_job_id(self):
        self.bridge.perform("gh-read", "gh-read-002",
                            intent=self.intent("get_componentcount"))
        self.assertEqual(self.bridge.read_job("gh-read-002")["status"], "COMPLETE")

    def test_unknown_unprofiled_writer_is_rejected_without_tool_call(self):
        reader = bridge.GrasshopperGate(workdir=self.root, transport=self.fake)
        with self.assertRaisesRegex(ValueError, "GH_WRITES_REQUIRE"):
            reader.perform("gh-write", "gh-write-001",
                           intent=self.intent("addcomponent", name="Panel"))
        self.assertNotIn("addcomponent", [n for n, _ in self.fake.calls])

    def test_pinned_test_graph_can_add_component(self):
        result = self.bridge.perform("gh-write", "gh-write-002",
                                     intent=self.intent("addcomponent", name="Circle"))
        self.assertEqual(result["status"], "COMPLETE")
        self.assertIn("addcomponent", [n for n, _ in self.fake.calls])

    def test_repeated_job_id_does_not_execute_again(self):
        intent = self.intent("addcomponent", name="Circle")
        self.bridge.perform("gh-write", "gh-write-003", intent=intent)
        first_count = sum(n == "addcomponent" for n, _ in self.fake.calls)
        result = self.bridge.perform("gh-write", "gh-write-003", intent=intent)
        self.assertEqual(result["status"], "COMPLETE")
        self.assertEqual(first_count, sum(n == "addcomponent" for n, _ in self.fake.calls))

    def test_job_id_cannot_bind_different_request(self):
        self.bridge.perform("gh-read", "gh-read-003",
                            intent=self.intent("get_componentcount"))
        with self.assertRaisesRegex(ValueError, "GH_JOB_ID_REUSED"):
            self.bridge.perform("gh-read", "gh-read-003",
                                intent=self.intent("getdocumentinfo"))

    def test_foreign_active_document_is_blocked(self):
        self.fake.active_path = self.exp / "foreign.ghx"
        with self.assertRaisesRegex(ValueError, "GH_DIFFERENT_ACTIVE_DOCUMENT"):
            self.bridge.perform("gh-write", "gh-write-004",
                                intent=self.intent("addcomponent", name="Circle"))

    def test_external_document_hash_drift_is_blocked(self):
        self.doc.write_bytes(b"changed outside our control")
        with self.assertRaisesRegex(ValueError, "GH_TEST_DOCUMENT_MODIFIED"):
            self.bridge.perform("gh-write", "gh-write-005",
                                intent=self.intent("addcomponent", name="Circle"))

    def test_arbitrary_script_editing_not_allowed(self):
        with self.assertRaisesRegex(ValueError, "GH_TOOL_OUTSIDE_ALLOWLIST"):
            self.bridge.perform("gh-write", "gh-write-006",
                                intent=self.intent("edit_csharp_script", code="x"))

    def test_script_source_argument_disallowed(self):
        with self.assertRaisesRegex(ValueError, "GH_DANGEROUS_ARGUMENT_KEY"):
            self.bridge.perform("gh-write", "gh-write-007",
                                intent=self.intent("addcomponent", code="x"))

    def test_value_must_be_numeric(self):
        with self.assertRaisesRegex(ValueError, "GH_ONLY_NUMERIC"):
            self.bridge.perform("gh-write", "gh-write-008",
                                intent=self.intent("set_component_value",
                                                   componentId="a", parameterName="value",
                                                   value="not a number"))

    def test_only_pinned_file_can_be_saved(self):
        result = self.bridge.perform("gh-write", "gh-write-009",
                                     intent=self.intent("savedocument"))
        self.assertEqual(result["status"], "COMPLETE")
        self.assertEqual(hashlib.sha256(self.doc.read_bytes()).hexdigest(),
                         self.bridge.expected_hash)
        more = self.bridge.perform("gh-write", "gh-write-010",
                                   intent=self.intent("addcomponent", name="Circle"))
        self.assertEqual(more["status"], "COMPLETE")

    def test_ambiguous_write_never_retried_and_blocks_further_writes(self):
        self.fake.fail_next = True
        intent = self.intent("addcomponent", name="Circle")
        result = self.bridge.perform("gh-write", "gh-write-011", intent=intent)
        self.assertEqual(result["status"], "UNKNOWN_NO_AUTORETRY")
        first_count = sum(n == "addcomponent" for n, _ in self.fake.calls)
        again = self.bridge.perform("gh-write", "gh-write-011", intent=intent)
        self.assertEqual(again["status"], "UNKNOWN_NO_AUTORETRY")
        self.assertEqual(first_count, sum(n == "addcomponent" for n, _ in self.fake.calls))
        with self.assertRaisesRegex(ValueError, "GH_PREVIOUS_WRITE_NOT_RECONCILED"):
            self.bridge.perform("gh-write", "gh-write-after-unknown", intent=intent)

    def test_incomplete_previous_write_blocks_new_one(self):
        folder = self.bridge.store / "gh-write-pending"
        folder.mkdir()
        (folder / "request.json").write_text(
            json.dumps({"operation": "gh-write", "intent": self.intent("addcomponent")}),
            encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "GH_PREVIOUS_WRITE_NOT_RECONCILED"):
            self.bridge.perform("gh-write", "gh-write-012",
                                intent=self.intent("addcomponent", name="Circle"))

    def test_test_document_must_reside_in_authorized_workdir(self):
        other = self.root / "other"
        other.mkdir()
        other_doc = other / "other.ghx"
        other_doc.write_bytes(b"<ghx/>")
        data = json.loads(self.profile.read_text(encoding="utf-8"))
        data["testDocument"] = str(other_doc)
        data["documentSha256"] = hashlib.sha256(other_doc.read_bytes()).hexdigest()
        self.profile.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(ValueError):
            bridge.GrasshopperGate(workdir=self.exp, profile=self.profile,
                                   transport=self.fake)


if __name__ == "__main__":
    unittest.main()
