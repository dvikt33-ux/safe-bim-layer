"""Offline/source-only contract tests for APA AC29 high-density V2.

No installed Archicad, Tapir, IfcOpenShell or ezdxf required. These tests do
not claim native LIVE acceptance or any benchmark.
"""
from __future__ import annotations

from pathlib import Path
import json
import sys
import tempfile
from types import SimpleNamespace as N
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import apa_high_density_readonly_v2 as P
import apa_high_density_entrypoint_v2 as E
import apa_external_readonly as V1


class IfcItem:
    def __init__(self, cls, guid=None, eid=1, **kw):
        self._class, self.GlobalId, self._eid = cls, guid, eid
        self.__dict__.update(kw)

    def is_a(self):
        return self._class

    def id(self):
        return self._eid


class IfcModel:
    schema = "IFC4"

    def __init__(self, **groups):
        self.groups = groups

    def by_type(self, type_name):
        return self.groups.get(type_name, [])


class FakeRouter:
    def __init__(self):
        self.contracts = {}
        self.handlers = {}
        self.policies = []
        self.catalog = {"commands": {
            "AddOn.APAExternalReadOnly." + n: {"api": "local-python"}
            for n in ("IFCDiff", "IFCClash", "IDSValidate",
                      "IFCQuantities", "PDFVectors", "DXFVectors")}}

    def add_local_provider(self, namespace, contracts, handlers, owner, dependencies):
        for name, contract in contracts.items():
            key = "AddOn." + namespace + "." + name
            self.catalog["commands"][key] = {"api": "local-python"}
            self.contracts[key] = contract
            self.handlers[key] = handlers[name]

    def review_policy(self, name, original, reviewed, proof):
        self.policies.append((name, original, reviewed))

    def contract_hash(self, name):
        return "fixture-hash"

    def operation_kind(self, name):
        return "READ_ONLY"

    def prepare(self, name, args):
        return {"nativeWritePermission": False, "effect": "READ_ONLY",
                "operation": name}

    def read(self, api, ticket, reviewed_read_only):
        return {}


class FeaturePackTests(unittest.TestCase):
    def test_cardinality_and_no_original_duplicate(self):
        self.assertEqual(len(P.COMMANDS), 12)
        self.assertEqual(len(P.ACTIONS), 12)
        self.assertTrue(set(P.ACTIONS).isdisjoint(V1.OPERATIONS))
        self.assertEqual(sum(ext == ".ifc" for _, ext in P.COMMANDS.values()), 8)
        self.assertEqual(sum(ext == ".dxf" for _, ext in P.COMMANDS.values()), 4)

    def test_input_suffix_and_original_protected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            good = root / "a.ifc"
            good.write_bytes(b"fixture")
            self.assertEqual(P.input_file(str(good), ".ifc"), good.resolve())
            with self.assertRaisesRegex(ValueError, "SOURCE_EXTENSION"):
                P.input_file(str(good), ".dxf")
            destination = root / "out.json"
            destination.write_text("existing")
            with self.assertRaisesRegex(ValueError, "OUTPUT_MUST_BE_NEW"):
                P.output_file(str(destination), good)
            with mock.patch.object(P, "STABLE", root):
                with self.assertRaisesRegex(ValueError, "INSIDE_STABLE"):
                    P.output_file(str(root / "created.json"), good)

    def test_ifc_schema_reports_counts_not_native_acceptance(self):
        model = IfcModel(IfcProduct=[
            IfcItem("IfcWall", "A"), IfcItem("IfcWall", "B"),
            IfcItem("IfcSlab", "C")],
            IfcRoot=[IfcItem("IfcWall", "A"), IfcItem("IfcWall", "B")],
            IfcSpatialStructureElement=[IfcItem("IfcBuildingStorey", "S")])
        result = P._ifc_schema(model)
        self.assertEqual(result["productTypes"], {"IfcSlab": 1, "IfcWall": 2})
        self.assertEqual(result["rootCount"], 2)
        self.assertIn("NOT_NATIVE", result["status"])

    def test_globalid_duplicate_and_missing(self):
        model = IfcModel(IfcRoot=[IfcItem("IfcWall", "A"),
                                  IfcItem("IfcWall", "A"),
                                  IfcItem("IfcDoor", None),
                                  IfcItem("IfcWindow", "B")])
        result = P._ifc_globalids(model)
        self.assertEqual(result["duplicateCount"], 1)
        self.assertEqual(result["missingCount"], 1)
        self.assertEqual(result["distinctGlobalIds"], 2)
        self.assertFalse(result["nativeGuidMappingChecked"])

    def test_ifc_opening_and_port_relations_do_not_claim_live(self):
        wall, hole, window = (IfcItem("IfcWall", "W"),
                              IfcItem("IfcOpeningElement", "O"),
                              IfcItem("IfcWindow", "F"))
        a, b, c = (IfcItem("IfcDistributionPort", x) for x in ("P1", "P2", "P3"))
        model = IfcModel(
            IfcRelVoidsElement=[N(RelatingBuildingElement=wall,
                                  RelatedOpeningElement=hole)],
            IfcRelFillsElement=[N(RelatingOpeningElement=hole,
                                  RelatedBuildingElement=window)],
            IfcDistributionPort=[a, b, c],
            IfcRelConnectsPorts=[N(RelatingPort=a, RelatedPort=b,
                                  GlobalId="R")])
        self.assertEqual(P._ifc_openings(model)["fills"], 1)
        port = P._ifc_ports(model)
        self.assertEqual(port["ports"], 3)
        self.assertEqual(port["unlinkedByIfcRelConnectsPorts"], 1)
        self.assertFalse(port["nativeMEPConnectionVerified"])

    def test_schema_optional_ifc2x3_georeference(self):
        class Legacy:
            schema = "IFC2X3"
            def by_type(self, typ):
                if typ in ("IfcMapConversion", "IfcProjectedCRS"):
                    raise RuntimeError("entity absent in schema")
                return []
        result = P._ifc_georef(Legacy())
        self.assertEqual(result["mapConversions"], [])
        self.assertFalse(result["worldCoordinateCalibrationVerified"])

    def test_property_sets_and_classifications_read_only(self):
        prop = N(Name="Pset_WallCommon", is_a=lambda: "IfcPropertySet")
        rel = N(RelatingPropertyDefinition=prop, RelatedObjects=[1, 2])
        classifications = N(
            RelatingClassification=N(
                is_a=lambda: "IfcClassificationReference", Identification="123"),
            RelatedObjects=[1])
        model = IfcModel(IfcRelDefinesByProperties=[rel],
                         IfcRelAssociatesClassification=[classifications])
        self.assertEqual(P._ifc_psets(model)["coverageBySetName"], {
            "Pset_WallCommon": 2})
        self.assertEqual(P._ifc_classifications(model)["total"], 1)

    def test_dxf_fact_extraction_no_geometric_mutation(self):
        class DXF:
            def __init__(self, **fields):
                self.fields = fields
                self.__dict__.update(fields)
            def get(self, name, default=None):
                return self.fields.get(name, default)

        def ent(kind, **fields):
            return N(dxftype=lambda: kind, dxf=DXF(**fields),
                     attribs=[], text=fields.get("text", ""))
        modelspace = [
            ent("INSERT", name="DOOR_BLOCK", layer="WALL", insert=(1, 2, 0)),
            ent("TEXT", layer="NOTES", text="Подпись", insert=(2, 3, 0)),
            ent("DIMENSION", layer="DIMS", defpoint=(0, 0, 0), dimtype=0)]
        doc = N(modelspace=lambda: modelspace,
                layers=[N(dxf=DXF(name="WALL", color=7), is_off=lambda: False)],
                header={"$INSUNITS": 4})
        self.assertEqual(P._dxf_layers(doc)["insunitsCode"], 4)
        self.assertEqual(P._dxf_blocks(doc)["insertions"]["total"], 1)
        self.assertFalse(P._dxf_blocks(doc)["bimFamiliesInferred"])
        self.assertEqual(P._dxf_text(doc)["annotations"]["total"], 1)
        self.assertFalse(P._dxf_dimensions(doc)
                         ["dimensionIsAuthoritativeConstructionMeasure"])

    def test_register_only_readonly_does_not_touch_v1_six(self):
        router = FakeRouter()
        old = set(router.catalog["commands"])
        with mock.patch.object(P, "verified_python", return_value=Path("C:/py.exe")):
            result = P.register(router)
        self.assertEqual(result["addedCommands"], 12)
        self.assertEqual(set(router.catalog["commands"]) - old,
                         set(result["commands"]))
        self.assertEqual(len(router.policies), 12)
        self.assertTrue(all(k[1:] == ("READ_ONLY", "READ_ONLY")
                            for k in router.policies))
        self.assertEqual(result["modelWrites"], result["nativeCalls"])

    def test_unsafe_router_response_is_blocked(self):
        router = FakeRouter()
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "a.ifc"
            src.write_text("fixture", encoding="utf8")
            with (mock.patch.object(E.V1, "verified_session",
                                    return_value=(N(native_command_router=
                                                    lambda *args, **kwargs: router),
                                                  "schema")),
                  mock.patch.object(E.Pack, "verified_python",
                                    return_value=Path("C:/py.exe"))):
                with self.assertRaisesRegex(ValueError,
                                            "EVIDENCE_INCOMPLETE"):
                    E.route_once("IFCGlobalIdAudit", str(src),
                                 str(Path(td) / "new.json"))


    def test_router_rejects_forged_source_sha_despite_success_json(self):
        router = FakeRouter()
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "model.ifc"
            source.write_text("source")
            destination = Path(td) / "evidence.json"
            forged = {"schema": "APA_HIGH_DENSITY_READONLY_V2",
                      "action": "ifc-globalids", "modelWrites": 0,
                      "nativeCalls": 0,
                      "adapterSha256": P.digest(P.__file__),
                      "sources": [{"name": "model.ifc",
                                   "sha256": "0" * 64}]}
            def fake_read(*args, **kwargs):
                destination.write_text(json.dumps(forged))
                return forged
            with (mock.patch.object(E.V1, "verified_session",
                                    return_value=(N(native_command_router=
                                                    lambda *args, **kwargs: router),
                                                  "schema")),
                  mock.patch.object(E.Pack, "verified_python",
                                    return_value=Path("C:/py.exe")),
                  mock.patch.object(router, "read", side_effect=fake_read)):
                with self.assertRaisesRegex(ValueError,
                                            "V2_ROUTER_EVIDENCE_SHA_OR_READBACK_MISMATCH"):
                    E.route_once("IFCGlobalIdAudit", str(source), str(destination))

    def test_router_accepts_exact_source_adapter_and_json_disk_readback(self):
        router = FakeRouter()
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "model.ifc"
            source.write_text("source")
            destination = Path(td) / "evidence.json"
            expected = {"schema": "APA_HIGH_DENSITY_READONLY_V2",
                        "action": "ifc-globalids", "modelWrites": 0,
                        "nativeCalls": 0,
                        "adapterSha256": P.digest(P.__file__),
                        "sources": [{"name": "model.ifc",
                                     "sha256": P.digest(source)}]}
            def fake_read(*args, **kwargs):
                destination.write_text(json.dumps(expected))
                return expected
            with (mock.patch.object(E.V1, "verified_session",
                                    return_value=(N(native_command_router=
                                                    lambda *args, **kwargs: router),
                                                  "schema")),
                  mock.patch.object(E.Pack, "verified_python",
                                    return_value=Path("C:/py.exe")),
                  mock.patch.object(router, "read", side_effect=fake_read)):
                result = E.route_once(
                    "IFCGlobalIdAudit", str(source), str(destination))
            self.assertEqual(result["status"],
                             "READ_ONLY_REPORT_CREATED_NOT_BIM_ACCEPTED")
            self.assertEqual(result["evidenceSha256"], P.digest(destination))
            self.assertEqual(result["newReadOnlyCommandsRegistered"], 12)


if __name__ == "__main__":
    unittest.main()
