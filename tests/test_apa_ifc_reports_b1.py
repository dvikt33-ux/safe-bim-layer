"""Real vendor/real DynamicCommands tests on disposable IFC and IDS files."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import ifcopenshell
from ifctester import ids
import apa_ifc_reports_b1 as B
from archicad_dynamic_commands import DynamicCommands


class ReportsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "model.ifc"
        model = ifcopenshell.file(schema="IFC4")
        self.guid = ifcopenshell.guid.new()
        wall = model.create_entity("IfcWall", GlobalId=self.guid, Name="Wall A")
        storey = model.create_entity("IfcBuildingStorey", GlobalId=ifcopenshell.guid.new())
        model.create_entity("IfcRelContainedInSpatialStructure", GlobalId=ifcopenshell.guid.new(),
                            RelatedElements=[wall], RelatingStructure=storey)
        model.write(str(self.source))
        self.sha = B.V2.digest(self.source)
        self.spec = self.root / "requirements.ids"
        document = ids.Ids(title="Names")
        spec = ids.Specification(name="Wall names", ifcVersion=["IFC4"])
        spec.applicability.append(ids.Entity(name="IFCWALL"))
        spec.requirements.append(ids.Attribute(name="Name"))
        document.specifications.append(spec)
        document.to_xml(str(self.spec))
        self.router = DynamicCommands({"common_schemas": {}, "commands": {}})
        self.patch = mock.patch.object(B.V2, "verified_python", return_value=Path(sys.executable))
        self.patch.start()
        self.addCleanup(self.patch.stop)
        B.register(self.router)

    def route(self, name, folder="out", **params):
        key = "AddOn." + B.NAMESPACE + "." + name
        params.update(a=str(self.source), output=str(self.root / folder))
        ticket = self.router.prepare(key, params)
        self.assertFalse(ticket["nativeWritePermission"])
        result = self.router.read(None, ticket, reviewed_read_only=True)
        self.assertEqual(B.V2.digest(self.source), self.sha)
        self.assertEqual(result, json.loads((self.root / folder / "report.json").read_text(encoding="utf8")))
        return result

    def test_select_real_router_subprocess_relations(self):
        result = self.route("IFCSelect", query="IfcWall")
        row = result["result"]["elements"]["items"][0]
        self.assertEqual(row["globalId"], self.guid)
        self.assertEqual(row["inverseReferences"]["items"][0]["ifcClass"], "IfcRelContainedInSpatialStructure")

    def test_schema_validation_detects_invalid_guid(self):
        model = ifcopenshell.open(str(self.source))
        model.by_type("IfcWall")[0].GlobalId = "invalid"
        model.write(str(self.source))
        self.sha = B.V2.digest(self.source)
        result = self.route("IFCSchemaValidate")
        self.assertFalse(result["result"]["schemaValid"])
        self.assertGreater(result["result"]["issues"]["total"], 0)

    def test_ods_is_real_zip_and_ids_result(self):
        before = B.V2.digest(self.spec)
        result = self.route("IDSReportODS", ids=str(self.spec))
        self.assertTrue(result["result"]["idsPassed"])
        self.assertEqual(result["artifacts"][0], B.ods_readback(self.root / "out" / "ids-report.ods"))
        self.assertEqual(before, B.V2.digest(self.spec))

    def test_ids_failure_is_reported_not_success(self):
        model = ifcopenshell.open(str(self.source))
        model.by_type("IfcWall")[0].Name = None
        model.write(str(self.source))
        self.sha = B.V2.digest(self.source)
        self.assertFalse(self.route("IDSReportODS", ids=str(self.spec))["result"]["idsPassed"])

    def test_ifc2x3_select(self):
        model = ifcopenshell.file(schema="IFC2X3")
        model.create_entity("IfcWall", GlobalId=self.guid)
        model.write(str(self.source))
        self.sha = B.V2.digest(self.source)
        self.assertEqual(self.route("IFCSelect", query="IfcWall")["ifcSchema"], "IFC2X3")

    def test_output_never_overwritten(self):
        self.route("IFCSelect", query="IfcWall")
        old = B.V2.digest(self.root / "out" / "report.json")
        with self.assertRaisesRegex(ValueError, "NEW_DIRECTORY"):
            self.route("IFCSelect", query="IfcWall")
        self.assertEqual(old, B.V2.digest(self.root / "out" / "report.json"))

    def test_parameter_and_stable_output_guards(self):
        with self.assertRaises(ValueError):
            B.call("select", {"a": str(self.source), "output": str(self.root / "out"),
                              "query": "IfcWall", "extra": "no"})
        with mock.patch.object(B.V2, "STABLE", self.root):
            with self.assertRaisesRegex(ValueError, "OUTSIDE_APA"):
                B.inputs("validate", {"a": str(self.source), "output": str(self.root / "out")})

    def test_version_drift(self):
        with mock.patch.object(B.importlib.metadata, "version", return_value="0.9.0"):
            with self.assertRaisesRegex(ValueError, "VERSION_DRIFT"):
                B.versions("validate")

    def test_invalid_query_no_success_report(self):
        with self.assertRaisesRegex(ValueError, "VENDOR_FAILED"):
            self.route("IFCSelect", query="not a valid {{{ selector")
        self.assertFalse((self.root / "out" / "report.json").exists())

    def test_forged_artifact_is_rejected(self):
        path = self.root / "invalid.ods"
        path.write_text('{"success": true}')
        with self.assertRaises(B.zipfile.BadZipFile):
            B.ods_readback(path)


if __name__ == "__main__":
    unittest.main()
