"""Real IfcOpenShell geometry exports through original DynamicCommands."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import ifcopenshell
from apa_external_ifc_vendor_smoke import create_ifc
import apa_ifc_geometry_b3 as B
from archicad_dynamic_commands import DynamicCommands


class GeometryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "model.ifc"
        self.guid = create_ifc(self.source, "Geometry wall")
        self.before = B.V2.digest(self.source)
        self.router = DynamicCommands({"common_schemas": {}, "commands": {}})
        B.register(self.router, sys.executable)

    def route(self, command, query="IfcWall"):
        out = self.root / "out"
        ticket = self.router.prepare("AddOn." + B.NAMESPACE + "." + command,
            {"a": str(self.source), "output": str(out), "query": query})
        self.assertFalse(ticket["nativeWritePermission"])
        result = self.router.read(None, ticket, reviewed_read_only=True)
        self.assertEqual(self.before, B.V2.digest(self.source))
        self.assertEqual(result, json.loads((out / "report.json").read_text(encoding="utf8")))
        self.assertEqual(result["processedElements"], 1)
        return result

    def test_obj_real_vertices_faces_and_material(self):
        result = self.route("IFCGeometryOBJ")
        self.assertGreater(result["artifact"]["faces"], 0)
        self.assertTrue((self.root / "out/model.mtl").is_file())
        self.assertEqual(result["artifact"]["materialLibrary"], "model.mtl")
        self.assertTrue((self.root / "out/model.obj").read_text().startswith("mtllib model.mtl\n"))

    def test_glb_binary_header_and_mesh(self):
        result = self.route("IFCGeometryGLB")
        self.assertEqual(result["artifact"]["meshes"], 1)
        self.assertTrue((self.root / "out/model.glb").read_bytes().startswith(b"glTF"))

    def test_bounds_real_world_metre_dimensions(self):
        self.route("IFCGeometryBounds")
        bounds = json.loads((self.root / "out/geometry-bounds.json").read_text())
        row = bounds["elements"]["items"][0]
        self.assertEqual(row["globalId"], self.guid)
        for actual, expected in zip(row["min"], [0, 0, 0]):
            self.assertAlmostEqual(actual, expected)
        for actual, expected in zip(row["max"], [5, 0.2, 3]):
            self.assertAlmostEqual(actual, expected)

    def test_bounds_include_placement(self):
        import numpy as np
        import ifcopenshell.api.geometry
        model = ifcopenshell.open(str(self.source))
        matrix = np.eye(4)
        matrix[:3, 3] = [10, 20, 30]
        ifcopenshell.api.geometry.edit_object_placement(model, product=model.by_guid(self.guid), matrix=matrix)
        model.write(str(self.source))
        self.before = B.V2.digest(self.source)
        self.route("IFCGeometryBounds")
        row = json.loads((self.root / "out/geometry-bounds.json").read_text())["elements"]["items"][0]
        self.assertEqual(row["min"], [10, 20, 30])

    def test_empty_or_non_geometric_selection_fails(self):
        with self.assertRaisesRegex(ValueError, "REPRESENTED_PRODUCTS"):
            self.route("IFCGeometryOBJ", query="IfcProject")
        self.assertFalse((self.root / "out/report.json").exists())

    def test_no_output_overwrite(self):
        self.route("IFCGeometryGLB")
        before = B.V2.digest(self.root / "out/model.glb")
        with self.assertRaisesRegex(ValueError, "NEW_DIRECTORY"):
            self.route("IFCGeometryGLB")
        self.assertEqual(before, B.V2.digest(self.root / "out/model.glb"))

    def test_version_drift(self):
        with mock.patch.object(B.importlib.metadata, "version", return_value="0.9"):
            with self.assertRaisesRegex(ValueError, "VERSION_DRIFT"):
                B.execute("bounds", {"a": str(self.source), "output": str(self.root / "out"), "query": "IfcWall"})

    def test_preserves_twenty_seven_existing_contracts(self):
        import apa_external_catalog as V1
        import apa_ifc_reports_b1 as B1
        import apa_dxf_geometry_c1 as C1
        router = DynamicCommands({"common_schemas": {}, "commands": {}})
        with mock.patch.object(V1, "verified_environment", return_value=(Path(sys.executable), Path(V1.__file__))):
            V1.register(router)
        with mock.patch.object(B.V2, "verified_python", return_value=Path(sys.executable)):
            B.V2.register(router)
            B1.register(router)
            B.B2.register(router, sys.executable)
            C1.register(router)
        before = copy.deepcopy(router.catalog["commands"])
        B.register(router, sys.executable)
        self.assertEqual(len(before), 27)
        self.assertEqual(len(router.catalog["commands"]), 30)
        for key, value in before.items():
            self.assertEqual(value, router.catalog["commands"][key])


if __name__ == "__main__":
    unittest.main()
