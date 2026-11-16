import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from apa_rule_audit import RuleAuditControl


class TestRuleAudit(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name) / "experiments"
        root.mkdir()
        self.snapshot = root / "snapshot.json"
        self.rules = root / "rules.yaml"
        self.profile = root / "profile.json"
        self.data = {
            "schema": "APA_MODEL_RULE_SNAPSHOT_V1",
            "coverage": {"properties": ["OFFICE/Fire Rating"],
                         "classifications": ["ARCHICAD Classification"],
                         "layers": True, "zones": True},
            "elements": [
                {"guid": "w-01", "element_type": "Wall", "layer": "A-WALL",
                 "properties": {"OFFICE/Fire Rating": "REI45"},
                 "classifications": {"ARCHICAD Classification": "Wall"},
                 "zone_number": None, "unread": []},
                {"guid": "z-01", "element_type": "Zone", "layer": "A-ZONE",
                 "properties": {}, "classifications": {},
                 "zone_number": "101", "unread": []}]}
        self.rules_text = """
- id: wall-fire
  type: property-required
  property: OFFICE/Fire Rating
  applies_to: {element_type: Wall}
- id: wall-layer
  type: layer-compliance
  allowed: [A-WALL]
  applies_to: {element_type: Wall}
- id: wall-classified
  type: classification-required
  system: ARCHICAD Classification
  applies_to: {element_type: Wall}
- id: zones-numbered
  type: zone-number-required
"""
        self._save()

    def tearDown(self):
        self.temp.cleanup()

    def _save(self):
        self.snapshot.write_text(json.dumps(self.data), encoding="utf-8")
        self.rules.write_text(self.rules_text, encoding="utf-8")
        def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
        self.profile.write_text(json.dumps({
            "schema": "APA_RULE_AUDIT_PROFILE_V1",
            "snapshot": str(self.snapshot), "snapshotSha256": sha(self.snapshot),
            "rules": str(self.rules), "rulesSha256": sha(self.rules)}), encoding="utf-8")

    def test_all_pass(self):
        result = RuleAuditControl(self.profile).perform("audit")
        self.assertEqual(result["status"], "APA_RULE_PASS")
        self.assertEqual(len(result["results"]), 4)
        self.assertEqual((result["nativeCalls"], result["modelWrites"]), (0, 0))

    def test_missing_property_fails(self):
        del self.data["elements"][0]["properties"]["OFFICE/Fire Rating"]
        self._save()
        result = RuleAuditControl(self.profile).perform("audit")
        self.assertEqual(result["status"], "APA_RULE_FAIL")
        self.assertEqual(result["results"][0]["failingGuids"], ["w-01"])

    def test_unread_does_not_false_fail(self):
        self.data["elements"][0]["properties"].clear()
        self.data["elements"][0]["unread"] = ["property:OFFICE/Fire Rating"]
        self._save()
        result = RuleAuditControl(self.profile).perform("audit")
        self.assertEqual(result["status"], "APA_RULE_INCOMPLETE")
        self.assertEqual(result["results"][0]["status"], "SKIPPED")

    def test_uncaptured_field_is_skipped(self):
        self.data["coverage"]["properties"] = []
        self._save()
        result = RuleAuditControl(self.profile).perform("audit")
        self.assertEqual(result["status"], "APA_RULE_INCOMPLETE")
        self.assertEqual(result["results"][0]["reason"], "SOURCE_FIELD_NOT_CAPTURED")

    def test_layer_failure(self):
        self.data["elements"][0]["layer"] = "WRONG"
        self._save()
        result = RuleAuditControl(self.profile).perform("audit")
        self.assertEqual(result["status"], "APA_RULE_FAIL")
        self.assertEqual(result["results"][1]["failingGuids"], ["w-01"])

    def test_zone_failure(self):
        self.data["elements"][1]["zone_number"] = ""
        self._save()
        result = RuleAuditControl(self.profile).perform("audit")
        self.assertEqual(result["status"], "APA_RULE_FAIL")
        self.assertEqual(result["results"][3]["failingCount"], 1)

    def test_warning_cannot_fail_overall(self):
        self.rules_text = self.rules_text.replace("id: wall-layer", "id: wall-layer\n  severity: warning")
        self.data["elements"][0]["layer"] = "WRONG"
        self._save()
        result = RuleAuditControl(self.profile).perform("audit")
        self.assertEqual(result["status"], "APA_RULE_PASS")
        self.assertEqual(result["results"][1]["status"], "FAIL")

    def test_tampered_snapshot_blocks(self):
        client = RuleAuditControl(self.profile)
        self.snapshot.write_text("{}", encoding="utf-8")
        self.assertEqual(client.perform("audit")["status"], "BLOCKED")

    def test_tampered_rules_blocks(self):
        client = RuleAuditControl(self.profile)
        self.rules.write_text("[]", encoding="utf-8")
        self.assertEqual(client.perform("audit")["status"], "BLOCKED")

    def test_arbitrary_python_rule_rejected(self):
        self.rules_text += "\n- id: arbitrary\n  type: custom\n  code: import os\n"
        self._save()
        self.assertEqual(RuleAuditControl(self.profile).perform("audit")["status"], "BLOCKED")

    def test_unsupported_where_rejected(self):
        self.rules_text = self.rules_text.replace(
            "applies_to: {element_type: Wall}",
            "applies_to: {element_type: Wall, where: [{property: x}]}",
            1)
        self._save()
        self.assertEqual(RuleAuditControl(self.profile).perform("audit")["status"], "BLOCKED")

    def test_operation_not_allowed(self):
        self.assertEqual(RuleAuditControl(self.profile).perform("execute")["status"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
