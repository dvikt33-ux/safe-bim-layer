"""384 NEW independent APA tests: native BREP quantities, IFC void relations,
Beam/Column segment ownership and runtime registration probes.

No original user models, Archicad/APX processes or network are touched.
The expected quantities/relationships derive from synthetic fixture geometry.
These scenarios are distinct from PR90, PR91 and PR92.
"""
from __future__ import annotations

import copy
import math
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from archicad_connected_ifc import native_body_quantities, native_element_quantities
from archicad_dynamic_commands import DynamicCommands
import archicad_local_modules as LOCAL


class NativeIFCAndRuntimeMatrix(unittest.TestCase):
    """Independent outcome oracles, no mocked copy of the measured algorithms."""


def add_case(prefix, seed, function):
    setattr(NativeIFCAndRuntimeMatrix,
            f"test_new_{prefix}_{seed:03d}", function)


def box_body(w, h, d, x=0., y=0., z=0.):
    vertices = [
        [x, y, z],
        [x + w, y, z],
        [x + w, y + h, z],
        [x, y + h, z],
        [x, y, z + d],
        [x + w, y, z + d],
        [x + w, y + h, z + d],
        [x, y + h, z + d],
    ]
    rings = [
        [0, 3, 2, 1],  # bottom (-z)
        [4, 5, 6, 7],  # top (+z)
        [0, 1, 5, 4],  # front (-y)
        [1, 2, 6, 5],  # right (+x)
        [2, 3, 7, 6],  # rear (+y)
        [3, 0, 4, 7],  # left (-x)
    ]
    return {"closed": True, "curved": False,
            "vertices": vertices,
            "faces": [{"contours": [face]} for face in rings]}


def expected_area(w, h, d):
    return 2 * (w * h + w * d + h * d)


def single_box_quantity_case(seed):
    def test(self):
        w = (seed % 11 + 1) / 2
        h = (seed % 13 + 2) / 3
        d = (seed % 7 + 3) / 4
        x, y, z = seed * 0.17, -seed * 0.13, seed * 0.07
        native = {"bodies": [box_body(w, h, d, x, y, z)]}
        out = native_body_quantities(native)
        self.assertEqual(out["status"], "NATIVE_PLANAR_BREP_QUANTITIES")
        self.assertEqual(out["bodyCount"], 1)
        self.assertAlmostEqual(out["volumeCubicMeters"], w * h * d, places=7)
        self.assertAlmostEqual(out["surfaceAreaSquareMeters"],
                               expected_area(w, h, d), places=7)
        self.assertIn("Actual resultant planar faces", out["authority"])
        self.assertNotIn("engineering", out)
    return test


for seed in range(80):
    add_case("cuboid_native_surface_volume", seed, single_box_quantity_case(seed))


def compound_box_quantity_case(seed):
    def test(self):
        w1 = 1 + seed % 5
        h1 = 2 + seed % 4
        d1 = 0.5 + (seed % 3) * 0.25
        w2 = 0.75 + seed % 7 / 8
        h2 = 1.25 + seed % 3 / 4
        d2 = 0.5 + seed % 4 / 6
        body1 = box_body(w1, h1, d1, seed * 0.1, 0, 0)
        body2 = box_body(w2, h2, d2, 100 + seed * 0.1, 0, 0)
        out = native_body_quantities({"bodies": [body1, body2]})
        self.assertEqual(out["status"], "NATIVE_PLANAR_BREP_QUANTITIES")
        self.assertEqual(out["bodyCount"], 2)
        self.assertAlmostEqual(out["volumeCubicMeters"],
                               w1 * h1 * d1 + w2 * h2 * d2, places=7)
        self.assertAlmostEqual(out["surfaceAreaSquareMeters"],
                               expected_area(w1, h1, d1) +
                               expected_area(w2, h2, d2), places=7)
    return test


for seed in range(48):
    add_case("multiple_native_solids_quantities", seed, compound_box_quantity_case(seed))


def invalid_brep_case(seed):
    def test(self):
        body = box_body(2 + seed % 4, 3 + seed % 5, 1 + seed % 3)
        mode = seed % 4
        if mode == 0:
            body["faces"].pop()
        elif mode == 1:
            body["faces"][0]["contours"][0].reverse()
        elif mode == 2:
            body["vertices"][6][2] += 0.7 + seed / 100
        else:
            body = box_body(2, 3, 0)
        result = native_body_quantities({"bodies": [body]})
        self.assertEqual(result["status"], "NATIVE_QUANTITIES_NOT_VERIFIED")
        self.assertTrue(result["reason"])
        self.assertNotIn("volumeCubicMeters", result)
        self.assertNotIn("surfaceAreaSquareMeters", result)
    return test


for seed in range(48):
    add_case("brep_invalid_topology_orientation", seed, invalid_brep_case(seed))


def unsupported_native_body_case(seed):
    def test(self):
        body = box_body(2 + seed % 8, 1 + seed % 5, 1 + seed % 7)
        if seed % 2:
            body["curved"] = True
            reason = "CURVED_NATIVE_BODY_NOT_QUANTIFIED"
        else:
            body["closed"] = False
            reason = "NATIVE_BODY_NOT_CLOSED"
        value = native_body_quantities({"bodies": [body]})
        self.assertEqual(value["status"], "NATIVE_QUANTITIES_NOT_VERIFIED")
        self.assertIn(reason, value["reason"])
        self.assertNotIn("volumeCubicMeters", value)
    return test


for seed in range(48):
    add_case("unsupported_native_curvature_closure", seed,
             unsupported_native_body_case(seed))


def segment_assembly_case(seed):
    def test(self):
        kind = "Beam" if seed % 2 else "Column"
        parent_guid = f"{seed + 1:08x}-1111-4111-8111-111111111111"
        child1 = f"{seed + 1:08x}-2222-4222-8222-222222222222"
        child2 = f"{seed + 1:08x}-3333-4333-8333-333333333333"
        p = {"guid": parent_guid, "type": kind, "homeStory": seed % 4,
             "bodies": []}
        dims = [(1 + seed % 3, 0.5, 1 + seed % 4),
                (1 + seed % 2, 1.25, 2 + seed % 3)]
        children = []
        for idx, (w, h, d) in enumerate(dims):
            children.append({
                "guid": [child1, child2][idx], "type": kind + "Segment",
                "homeStory": p["homeStory"],
                "relationships": {"hostGuid": parent_guid.upper()},
                "bodies": [box_body(w, h, d, x=idx * 50)],
            })
        rows = {e["guid"]: e for e in [p, *children]}
        out = native_element_quantities(rows, parent_guid)
        self.assertEqual(out["status"], "NATIVE_PLANAR_BREP_QUANTITIES")
        self.assertEqual(out["bodyCount"], 2)
        self.assertEqual(out["sourceSegmentGuids"], sorted([child1, child2]))
        self.assertEqual(out["ownershipAuthority"],
                         "SDK_HOST_GUID_AND_NATIVE_SEGMENT_TYPE")
        self.assertAlmostEqual(out["volumeCubicMeters"],
                               sum(w * h * d for w, h, d in dims), places=7)
        invalid = copy.deepcopy(rows)
        if seed % 3 == 0:
            invalid[child1]["homeStory"] += 1
        elif seed % 3 == 1:
            invalid[child2]["type"] = "UnrelatedSegment"
        else:
            invalid[child1]["bodies"] = []
        denied = native_element_quantities(invalid, parent_guid)
        self.assertEqual(denied["status"], "NATIVE_QUANTITIES_NOT_VERIFIED")
        self.assertIn("NATIVE_ASSEMBLY_SEGMENT_OWNERSHIP_NOT_PROVEN",
                      denied["reason"])
        self.assertNotIn("volumeCubicMeters", denied)
    return test


for seed in range(48):
    add_case("beam_column_segments_ownership", seed, segment_assembly_case(seed))


def synthetic_registration_case(seed):
    def test(self):
        namespace = f"OfflineVendor{seed}"
        action = f"ReadOnlyQuery{seed}"
        command = "AddOn." + namespace + "." + action
        r = DynamicCommands({"commands": {}, "common_schemas": {},
                             "_metadata": {"provider_version": "1.5.10"}})
        r.add_provider(namespace, {action: {
            "version": "29",
            "category": "Native runtime query simulation",
            "parameters": {"type": "object", "maxProperties": 0},
            "returns": {"type": "object"},
        }}, "Synthetic discovery, not native addon")
        expected = bool(seed % 2)

        class StubTransport:
            def __init__(self):
                self.allowed = set()
                self.calls = []

            def __call__(self, name, params):
                self.calls.append((name, copy.deepcopy(params)))
                return {"available": expected}

        transport = StubTransport()
        if expected:
            result = r.probe_runtime(transport, command)
            self.assertEqual(result["status"], "RUNTIME_AVAILABLE")
            self.assertEqual(result["namespace"], namespace)
            self.assertEqual(result["command"], action)
            self.assertEqual(r.select(command)["status"], "SCHEMA_VALID")
        else:
            with self.assertRaisesRegex(ValueError,
                                        "COMMAND_NOT_REGISTERED_IN_CURRENT_RUNTIME"):
                r.probe_runtime(transport, command)
            self.assertEqual(r.select(command)["status"], "BLOCKED")
        self.assertEqual(r.select(command)["runtimeRegistered"], expected)
        self.assertEqual(transport.calls, [(
            "API.IsAddOnCommandAvailable",
            {"addOnCommandId": {"commandNamespace": namespace,
                                "commandName": action}},
        )])
        self.assertIn("API.IsAddOnCommandAvailable", transport.allowed)
        self.assertNotIn(command, r.live)
        self.assertNotIn(command, r.callable)
        self.assertFalse(r.prepare(command, {})["nativeWritePermission"])
    return test


for seed in range(64):
    add_case("native_registration_transport_probe", seed,
             synthetic_registration_case(seed))


def ifc_void_relations_case(seed):
    def test(self):
        import ifcopenshell
        from archicad_connected_ifc import inspect_exchange_semantics
        count = 1 + seed % 3
        with tempfile.TemporaryDirectory(prefix="apa_ifc_void_") as directory:
            path = Path(directory) / ("voids_" + str(seed) + ".ifc")
            model = ifcopenshell.file(schema="IFC4")
            host = model.create_entity("IfcWall",
                                       GlobalId=ifcopenshell.guid.new(),
                                       Name="TestHostWall_" + str(seed))
            holes = []
            for index in range(count):
                opening = model.create_entity(
                    "IfcOpeningElement", GlobalId=ifcopenshell.guid.new(),
                    Name=f"Opening_{seed}_{index}")
                model.create_entity(
                    "IfcRelVoidsElement", GlobalId=ifcopenshell.guid.new(),
                    RelatingBuildingElement=host,
                    RelatedOpeningElement=opening)
                holes.append(opening)
            model.create_entity("IfcDoor", GlobalId=ifcopenshell.guid.new(),
                                Name="UnrelatedDoor_" + str(seed))
            model.write(str(path))
            facts = inspect_exchange_semantics(str(path))
            self.assertEqual(facts["schema"], "IFC4")
            self.assertEqual(len(facts["voidRelations"]), count)
            self.assertEqual(
                {record["openingIfcId"] for record in facts["voidRelations"]},
                {hole.GlobalId for hole in holes})
            self.assertTrue(all(
                record["hostIfcId"] == host.GlobalId
                and record["hostIfcType"] == "IfcWall"
                for record in facts["voidRelations"]))
            self.assertEqual(facts["nativePortRelationsExported"], [])
            self.assertEqual(facts["analyticalMembers"], [])
            self.assertEqual(facts["materialAssignments"], [])
            self.assertEqual(facts["semanticCompatibility"], "NOT_VERIFIED")
            self.assertEqual(facts["analyticalExchangeStatus"],
                             "NO_ANALYTICAL_MEMBERS_IN_ACTUAL_EXPORT")
            selected = LOCAL.ifc_select(str(path), "IfcOpeningElement")
            self.assertEqual(len(selected["elements"]), count)
            self.assertEqual({row["ifcId"] for row in selected["elements"]},
                             {hole.GlobalId for hole in holes})
    return test


for seed in range(48):
    add_case("ifc_real_void_host_relationships", seed, ifc_void_relations_case(seed))


COUNT = 80 + 48 + 48 + 48 + 48 + 64 + 48
assert len(unittest.defaultTestLoader.loadTestsFromTestCase(
    NativeIFCAndRuntimeMatrix)._tests) == COUNT == 384

if __name__ == "__main__":
    unittest.main()
