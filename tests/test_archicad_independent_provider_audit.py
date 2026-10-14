"""Independent targeted offline regression probes for APA's dynamic provider bridge.

Pinned starting code: PR #85 at 45ef6b734e70c0e2c40ea57ed9a0099d70c4a917.
No Archicad connection, no PLN/APX writes, no external service calls.

Expected-failure tests are *existing known issues*, not acceptance of behavior.
They become unexpected successes when fixed and should then become ordinary tests.
"""
import copy
import sys
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import archicad_project_accelerator as A
from archicad_dynamic_commands import DynamicCommands
import test_archicad_mass_capabilities as M


GUID_A = "11111111-1111-4111-8111-111111111111"
GUID_B = "22222222-2222-4222-8222-222222222222"


class IndependentProviderAuditTests(unittest.TestCase):
    @staticmethod
    def router():
        return M.MassTests().router()

    def test_source_snapshot_remains_unverified(self):
        r = self.router()
        source = {
            "common_schemas": {},
            "commands": {
                "AbsentProviderCommand": {
                    "name": "AbsentProviderCommand",
                    "version": "1",
                    "category": "Test",
                    "parameters": {"type": "object", "maxProperties": 0},
                    "returns": {"type": "object"},
                }
            },
        }
        self.assertEqual(r.include_source_snapshot(source, "missing-apx"), ["AbsentProviderCommand"])
        row = r.select("AbsentProviderCommand")
        self.assertEqual(row["availability"], "SOURCE_SNAPSHOT_NOT_RUNTIME_PROBED")
        self.assertIsNone(row["runtimeRegistered"])
        self.assertEqual(row["status"], "SCHEMA_VALID")

    def test_source_snapshot_unregistered_runtime_fails_closed(self):
        r = self.router()
        source = {
            "common_schemas": {},
            "commands": {
                "AbsentProviderCommand": {
                    "name": "AbsentProviderCommand", "version": "1", "category": "Test",
                    "parameters": {"type": "object", "maxProperties": 0},
                    "returns": {"type": "object"}
                }
            },
        }
        r.include_source_snapshot(source, "missing-apx")
        class MissingRuntime:
            allowed = set()
            def __call__(self, command, params):
                self.last_command = command
                return {"available": False}
        stub = MissingRuntime()
        with self.assertRaises(ValueError):
            r.probe_runtime(stub, "AbsentProviderCommand")
        self.assertEqual(stub.last_command, "API.IsAddOnCommandAvailable")
        self.assertFalse(r.select("AbsentProviderCommand")["runtimeRegistered"])

    def test_registration_failure_stays_blocked(self):
        r = self.router()
        r.register_availability("GetSource", False)
        self.assertEqual(r.select("GetSource")["status"], "BLOCKED")

    def test_registration_does_not_impersonate_live_evidence(self):
        r = self.router()
        r.register_availability("GetSource", True)
        self.assertEqual(r.select("GetSource")["status"], "SCHEMA_VALID")
        self.assertTrue(r.select("GetSource")["runtimeRegistered"])

    def test_provider_qualified_command_does_not_replace_tapir(self):
        r = self.router()
        r.add_provider("Vendor", {"GetSource": {
            "version": "1", "category": "Test",
            "parameters": {"type": "object", "maxProperties": 0},
            "returns": {"type": "object"}
        }}, "independent source")
        self.assertIn("GetSource", r.catalog["commands"])
        self.assertIn("AddOn.Vendor.GetSource", r.catalog["commands"])
        self.assertEqual(r.prepare("GetSource", {})["command"], "GetSource")
        self.assertEqual(r.prepare("AddOn.Vendor.GetSource", {})["command"],
                         "AddOn.Vendor.GetSource")

    def test_provider_duplicate_rejected(self):
        r = self.router()
        command = {"Call": {"version": "1", "category": "Test",
                            "parameters": {"type": "object"}, "returns": {"type": "object"}}}
        r.add_provider("Vendor", command, "source")
        with self.assertRaises(ValueError):
            r.add_provider("Vendor", command, "source")

    def test_namespaced_ref_schema_checked(self):
        r = self.router()
        r.add_provider("Vendor", {
            "Call": {
                "version": "1", "category": "Test",
                "parameters": {"$ref": "#/Payload"},
                "returns": {"type": "object"},
            }
        }, "source", {"Payload": {
            "type": "object", "additionalProperties": False,
            "properties": {"amount": {"type": "integer"}},
            "required": ["amount"],
        }})
        self.assertEqual(r.prepare("AddOn.Vendor.Call", {"amount": 2})["command"],
                         "AddOn.Vendor.Call")
        with self.assertRaises(Exception):
            r.prepare("AddOn.Vendor.Call", {"amount": "invalid"})

    def test_contract_manifest_hash_mismatch_fails(self):
        r = self.router()
        manifest = {
            "catalogHash": "different-catalog",
            "operations": {"GetSource": {
                "kind": "READ_ONLY", "impact": "READ_ONLY",
                "evidence": {"source": "source", "sha256": "1" * 64},
            }},
            "contractHashes": {"GetSource": "f" * 64},
        }
        with self.assertRaises(ValueError):
            r.load_policies(manifest)

    def test_policy_without_source_evidence_fails(self):
        r = self.router()
        with self.assertRaises(ValueError):
            r.review_policy("GetSource", "READ_ONLY", "READ_ONLY",
                            {"source": "review without hash"})

    def test_scope_rejects_retained_owner(self):
        r = self.router()
        r.catalog["commands"]["Consume"]["parameters"] = {"type": "object"}
        r.fingerprint = A.RUN.digest(r.catalog)
        r.review_policy("Consume", "CREATE", "MODEL",
                        {"source": "test", "sha256": "1" * 64})
        ticket = r.prepare("Consume", {"ownerWallId": {"guid": GUID_A}})
        with self.assertRaises(ValueError):
            r.scope(ticket, {}, [], [GUID_A], "synthetic authorization", "MODEL")

    def test_scope_rejects_unlisted_element_id(self):
        r = self.router()
        r.catalog["commands"]["Consume"]["parameters"] = {"type": "object"}
        r.fingerprint = A.RUN.digest(r.catalog)
        r.review_policy("Consume", "MODIFY", "MODEL",
                        {"source": "test", "sha256": "1" * 64})
        ticket = r.prepare("Consume", {"elementId": {"guid": GUID_B}})
        with self.assertRaises(ValueError):
            r.scope(ticket, {}, [], [GUID_A], "synthetic authorization", "MODEL")

    def test_ticket_copy_freezes_params(self):
        r = self.router()
        params = {"value": 2}
        ticket = r.prepare("Consume", params)
        params["value"] = 3
        self.assertEqual(ticket["parameters"], {"value": 2})
        r.validate(ticket)

    def test_ticket_changes_when_policy_reviewed(self):
        r = self.router()
        ticket = r.prepare("GetSource", {})
        r.review_policy("GetSource", "READ_ONLY", "READ_ONLY",
                        {"source": "test", "sha256": "1" * 64})
        with self.assertRaises(ValueError):
            r.validate(ticket)

    def test_cycle_preparation_rejected(self):
        r = self.router()
        graph = {"operations": [
            {"id": "source", "command": "GetSource", "params": {}, "after": ["next"]},
            {"id": "next", "command": "Consume", "params": {
                "value": {"$result": {"step": "source", "pointer": "/value"}}}},
        ]}
        with self.assertRaises(ValueError):
            r.prepare_workflow(graph)

    def test_true_success_result_accepted(self):
        r = self.router()
        data = {"success": True}
        self.assertEqual(r.validate_result("Consume", data), data)

    def test_false_success_result_rejected(self):
        r = self.router()
        with self.assertRaises(ValueError):
            r.validate_result("Consume", {"success": False})

    def test_json_pointer_escaped_slash(self):
        r = self.router()
        self.assertEqual(r._result_at({"a/b": 7}, "/a~1b"), 7)

    @unittest.expectedFailure
    def test_known_gap_empty_member_json_pointer(self):
        r = self.router()
        self.assertEqual(r._result_at({"a": {"": 7}}, "/a/"), 7)

    @unittest.expectedFailure
    def test_known_gap_negative_array_index_accepted(self):
        r = self.router()
        with self.assertRaises((ValueError, KeyError, IndexError)):
            r._result_at({"arr": [11, 22]}, "/arr/-1")

    @unittest.expectedFailure
    def test_known_gap_unlisted_owner_guid_not_rejected(self):
        r = self.router()
        r.catalog["commands"]["Consume"]["parameters"] = {"type": "object"}
        r.fingerprint = A.RUN.digest(r.catalog)
        r.review_policy("Consume", "CREATE", "MODEL",
                        {"source": "test", "sha256": "1" * 64})
        ticket = r.prepare("Consume", {"ownerWallId": {"guid": GUID_B}})
        with self.assertRaises(ValueError):
            r.scope(ticket, {}, [], [GUID_A], "synthetic authorization", "MODEL")

    @unittest.expectedFailure
    def test_known_gap_nullable_error_treated_as_failure(self):
        r = self.router()
        value = {"success": True, "error": None}
        self.assertEqual(r.validate_result("Consume", value), value)

    @unittest.expectedFailure
    def test_known_gap_placeholder_ignores_maximum(self):
        r = self.router()
        schema = {"type": "integer", "maximum": 0}
        Draft202012Validator(schema).validate(r._schema_example(schema))


if __name__ == "__main__":
    unittest.main()
