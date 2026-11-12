"""Real vendor end-to-end tests: CSV, IFC copy extraction, BCF ZIP."""
import csv
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import ifcopenshell
import ifcopenshell.api.pset
from apa_external_ifc_vendor_smoke import create_ifc
import apa_ifc_artifacts_b2 as B
from archicad_dynamic_commands import DynamicCommands


class ArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "model.ifc"
        self.guid = create_ifc(self.source, "=formula")
        model = ifcopenshell.open(str(self.source))
        wall = model.by_guid(self.guid)
        pset = ifcopenshell.api.pset.add_pset(model, product=wall, name="Pset_WallCommon")
        ifcopenshell.api.pset.edit_pset(model, pset=pset, properties={"Reference": "W-01"})
        qto = ifcopenshell.api.pset.add_qto(model, product=wall, name="Qto_WallBaseQuantities")
        ifcopenshell.api.pset.edit_qto(model, qto=qto, properties={"Length": 5.0})
        model.create_entity("IfcSlab", GlobalId=ifcopenshell.guid.new(), Name="Not selected")
        model.write(str(self.source))
        self.before = B.V2.digest(self.source)
        self.router = DynamicCommands({"common_schemas": {}, "commands": {}})
        B.register(self.router, sys.executable)

    def route(self, command, **kw):
        params = {"a": str(self.source), "output": str(self.root / "out"), "query": "IfcWall", **kw}
        ticket = self.router.prepare("AddOn." + B.NAMESPACE + "." + command, params)
        self.assertFalse(ticket["nativeWritePermission"])
        result = self.router.read(None, ticket, reviewed_read_only=True)
        self.assertEqual(self.before, B.V2.digest(self.source))
        self.assertEqual(result, json.loads((self.root / "out" / "report.json").read_text(encoding="utf8")))
        return result

    def test_csv_properties_quantities_formula_escape(self):
        result = self.route("IFCCSVExport", attributes=["Name", "Pset_WallCommon.Reference", "Qto_WallBaseQuantities.Length"])
        with (self.root / "out" / "properties.csv").open(encoding="utf8", newline="") as stream:
            rows = list(csv.reader(stream))
        self.assertEqual(rows[1], [self.guid, "'=formula", "W-01", "5.0"])
        self.assertEqual(result["result"]["spreadsheetFormulaEscapes"], 1)

    def test_extract_reopens_and_preserves_spatial_tree_properties(self):
        self.route("IFCExtractElements")
        model = ifcopenshell.open(str(self.root / "out" / "subset.ifc"))
        wall = model.by_guid(self.guid)
        self.assertEqual(len(model.by_type("IfcWall")), 1)
        self.assertEqual(len(model.by_type("IfcSlab")), 0)
        self.assertEqual(wall.ContainedInStructure[0].RelatingStructure.Name, "Level 0")
        self.assertEqual(ifcopenshell.util.element.get_psets(wall)["Pset_WallCommon"]["Reference"], "W-01")
        self.assertIsNotNone(wall.Representation)

    def test_bcf_real_zip_guid_and_topic(self):
        result = self.route("IFCBCFIssues", title="Review wall", description="Check reference", author="APA test")
        self.assertEqual(result["artifact"]["selectedIfcGuids"], [self.guid])
        from bcf.v2.bcfxml import BcfXml
        document = BcfXml.load(self.root / "out" / "issues.bcfzip")
        self.assertEqual(len(document.topics), 1)
        self.assertEqual(next(iter(document.topics.values())).topic.title, "Review wall")
        document.close()

    def test_no_overwrite(self):
        self.route("IFCExtractElements")
        before = B.V2.digest(self.root / "out" / "subset.ifc")
        with self.assertRaisesRegex(ValueError, "NEW_DIRECTORY"):
            self.route("IFCExtractElements")
        self.assertEqual(before, B.V2.digest(self.root / "out" / "subset.ifc"))

    def test_empty_selection_fails_without_success_receipt(self):
        with self.assertRaisesRegex(ValueError, "SELECTION_EMPTY"):
            self.route("IFCExtractElements", query="IfcDoor")
        self.assertFalse((self.root / "out" / "report.json").exists())
        self.assertEqual(self.before, B.V2.digest(self.source))

    def test_bcf_rejects_unplaced_elements(self):
        with self.assertRaisesRegex(ValueError, "PLACED_PRODUCTS"):
            self.route("IFCBCFIssues", query="IfcSlab", title="Review", description="Test", author="APA test")

    def test_version_drift_and_output_boundary(self):
        params = {"a": str(self.source), "output": str(self.root / "out"), "query": "IfcWall"}
        with mock.patch.object(B.importlib.metadata, "version", return_value="0.9"):
            with self.assertRaisesRegex(ValueError, "VERSION_DRIFT"):
                B.execute("extract", params)
        with mock.patch.object(B.V2, "STABLE", self.root):
            with self.assertRaisesRegex(ValueError, "NEW_DIRECTORY"):
                B.inputs("extract", params)

    def test_recipe_environment_cannot_replace_fixed_recipe(self):
        with mock.patch.dict("os.environ", {"IFCPATCH_RECIPE_DIR": str(self.root / "nonexistent")}):
            self.route("IFCExtractElements")

    def test_preserves_all_twenty_one_existing_contracts(self):
        import apa_external_catalog as V1
        import apa_ifc_reports_b1 as B1
        router = DynamicCommands({"common_schemas": {}, "commands": {}})
        with mock.patch.object(V1, "verified_environment", return_value=(Path(sys.executable), Path(V1.__file__))):
            V1.register(router)
        with mock.patch.object(B.V2, "verified_python", return_value=Path(sys.executable)):
            B.V2.register(router)
            B1.register(router)
        before = copy.deepcopy(router.catalog["commands"])
        self.assertEqual(len(before), 21)
        B.register(router, sys.executable)
        self.assertEqual(len(router.catalog["commands"]), 24)
        for key, value in before.items():
            self.assertEqual(value, router.catalog["commands"][key])


if __name__ == "__main__":
    unittest.main()
