"""Real ezdxf source geometry and existing-router subprocess tests."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import ezdxf
import apa_dxf_geometry_c1 as C
from archicad_dynamic_commands import DynamicCommands


class GeometryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "drawing.dxf"
        self.doc = ezdxf.new("R2013")
        self.doc.header["$INSUNITS"] = 4
        self.router = DynamicCommands({"common_schemas": {}, "commands": {}})
        patch = mock.patch.object(C.V2, "verified_python", return_value=Path(sys.executable))
        patch.start()
        self.addCleanup(patch.stop)
        C.register(self.router)

    def route(self, command):
        self.doc.saveas(str(self.source))
        before = C.V2.digest(self.source)
        output = self.root / "report.json"
        ticket = self.router.prepare("AddOn." + C.NAMESPACE + "." + command,
                                     {"a": str(self.source), "output": str(output)})
        self.assertFalse(ticket["nativeWritePermission"])
        result = self.router.read(None, ticket, reviewed_read_only=True)
        self.assertEqual(result, json.loads(output.read_text(encoding="utf8")))
        self.assertEqual(before, C.V2.digest(self.source))
        return result["result"]

    def test_rotated_scaled_block_world_coordinates(self):
        block = self.doc.blocks.new("A")
        block.add_line((0, 0), (2, 0))
        insert = self.doc.modelspace().add_blockref("A", (10, 20), dxfattribs={"xscale": 2, "yscale": 2, "rotation": 90})
        result = self.route("DXFWorldPaths")
        row = result["paths"]["items"][0]
        self.assertEqual(row["commands"][0]["points"][0], [10, 20, 0])
        self.assertEqual(row["commands"][1]["points"][0], [10, 24, 0])
        self.assertEqual(row["parentHandle"], insert.dxf.handle)
        self.assertEqual(result["insunitsCode"], 4)

    def test_closed_contours_only_with_no_bim_claim(self):
        space = self.doc.modelspace()
        space.add_line((0, 0), (1, 0))
        space.add_lwpolyline([(0, 0), (2, 0), (2, 2), (0, 2)], close=True)
        result = self.route("DXFClosedContours")
        self.assertEqual(result["paths"]["total"], 1)
        self.assertTrue(result["paths"]["items"][0]["closed"])
        self.assertFalse(result["bimElementsInferred"])
        self.assertFalse(result["planarityVerified"])

    def test_repeated_alias_blocks_compare_geometry(self):
        for name in ("A", "B"):
            self.doc.blocks.new(name).add_line((0, 0), (2, 0))
        space = self.doc.modelspace()
        space.add_blockref("A", (0, 0))
        space.add_blockref("B", (10, 0))
        space.add_blockref("A", (20, 0), dxfattribs={"rotation": 90})
        groups = self.route("DXFRepeatedAssemblies")["repeatedAssemblies"]
        self.assertEqual(groups["total"], 1)
        self.assertEqual(groups["items"][0]["instances"]["total"], 2)

    def test_unsupported_text_is_reported(self):
        self.doc.modelspace().add_text("Uncalibrated note")
        result = self.route("DXFWorldPaths")
        self.assertEqual(result["unsupportedEntityTypes"], {"TEXT": 1})
        self.assertEqual(result["paths"]["total"], 0)

    def test_curve_conversion_declares_approximation(self):
        self.doc.modelspace().add_circle((0, 0), radius=2)
        result = self.route("DXFWorldPaths")
        self.assertEqual(result["paths"]["items"][0]["curveRepresentation"], "EZDXF_BEZIER_APPROXIMATION")

    def test_decomposition_limit_fails(self):
        self.doc.modelspace().add_line((0, 0), (1, 0))
        with mock.patch.object(C, "MAX_DECOMPOSED", 0):
            with self.assertRaisesRegex(ValueError, "DECOMPOSITION_LIMIT"):
                C.analyze(self.doc, "paths")

    def test_prior_twenty_four_contracts_preserved(self):
        import apa_external_catalog as V1
        import apa_ifc_reports_b1 as B1
        import apa_ifc_artifacts_b2 as B2
        router = DynamicCommands({"common_schemas": {}, "commands": {}})
        with mock.patch.object(V1, "verified_environment", return_value=(Path(sys.executable), Path(V1.__file__))):
            V1.register(router)
        C.V2.register(router)
        B1.register(router)
        B2.register(router, sys.executable)
        before = copy.deepcopy(router.catalog["commands"])
        C.register(router)
        self.assertEqual(len(before), 24)
        self.assertEqual(len(router.catalog["commands"]), 27)
        for key, value in before.items():
            self.assertEqual(value, router.catalog["commands"][key])

    def test_parameter_extension_and_output_guards(self):
        self.doc.saveas(str(self.source))
        with self.assertRaisesRegex(ValueError, "INVALID_PARAMETERS"):
            C.inputs("paths", {"a": str(self.source), "output": "x", "extra": "no"})
        with self.assertRaisesRegex(ValueError, "NEW_JSON"):
            C.inputs("paths", {"a": str(self.source), "output": str(self.source)})


if __name__ == "__main__":
    unittest.main()
