"""Independent PR107 192-case offline contract suite.

Tests production APA native parametric *preparation*, existing GDL matrix
setter ticket, MEP ownership graph and reciprocal port evidence. No native
runtime, writer invocation, dynamic SDK write or PLN access.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import sys
import unittest
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import apa_native_parameter_edit as EDIT
from apa_native_dependency_flow import dependency_inputs


class PR107ParametricOffline(unittest.TestCase):
    pass


def testcase(name, index, case):
    setattr(PR107ParametricOffline, f"test_pr107_{name}_{index:03d}", case)


@lru_cache(maxsize=1)
def router():
    from archicad_dynamic_commands import DynamicCommands
    import archicad_project_accelerator as A
    catalog = json.loads((ROOT / "schemas/accelerator/mass-capabilities/commands.json")
                         .read_text(encoding="utf8"))
    r = DynamicCommands(catalog)
    A.connect_functional_modules(r)
    return r


def gdl_array(name, values, d1, d2, param_type):
    return dict(name=name, value=values, dimension1=d1, dimension2=d2,
                type=param_type, isLocked=False, flags=[])


def guid(name):
    return {"guid": name}


def pairs(out):
    return {tuple(x) for x in out["edges"]}


def gdl_matrix_roundtrip(seed):
    def check(self):
        rows = 2 + seed % 5
        columns = 2 + (seed // 5) % 4
        name = f"Param_{seed}"
        n = rows * columns
        mode = seed % 4
        if mode == 0:
            old = list(range(n))
            new = list(range(seed * 10, seed * 10 + n))
            kind = "Integer"
        elif mode == 1:
            old = [float(i) / 7 for i in range(n)]
            new = [float(i + seed) / 8 for i in range(n)]
            kind = "Real"
        elif mode == 2:
            old = [str(i) for i in range(n)]
            new = [f"cell_{seed}_{i}" for i in range(n)]
            kind = "String"
        else:
            old = [(i % 2) == 0 for i in range(n)]
            new = [(i % 3) == 0 for i in range(n)]
            kind = "Boolean"
        source = [gdl_array(name, old, rows, columns, kind)]
        change = {name: [list(new[i*columns:(i+1)*columns])
                         for i in range(rows)] if seed % 2 else new}
        old_source, old_change = copy.deepcopy(source), copy.deepcopy(change)
        preview = EDIT.prepare_existing_gdl_edit(router(), f"00000000-0000-4000-8000-{seed+1:012x}", source, change)
        self.assertEqual(source, old_source)
        self.assertEqual(change, old_change)
        self.assertFalse(preview["executionPermission"])
        self.assertEqual(preview["nativeModelWrites"], 0)
        self.assertEqual(preview["sourceParametersSHA256"], EDIT.digest(source))
        self.assertEqual(preview["dimensions"], [dict(
            name=name, dimension1=rows, dimension2=columns,
            serialization="ROW_MAJOR_MATRIX", rankPreserved=True)])
        ticket = preview["ticket"]
        router().validate(ticket)
        self.assertFalse(ticket["nativeWritePermission"])
        self.assertEqual(ticket["parameters"]["elementsWithGDLParameters"][0]
                         ["gdlParameters"][0]["value"],
                         [new[i*columns:(i+1)*columns] for i in range(rows)])
        self.assertIn("SetGDLParametersOfElements", ticket["command"])
    return check


for i in range(40):
    testcase("gdl_rectangular_matrix_rank", i, gdl_matrix_roundtrip(i))


def gdl_invalid(seed):
    def check(self):
        name = f"Q{seed}"
        base = gdl_array(name, [1.0, 2.0, 3.0, 4.0], 2, 2, "Real")
        source = [base]
        changes = {name: [5.0, 6.0, 7.0, 8.0]}
        mode = seed % 8
        if mode == 0:
            source = [base, copy.deepcopy(base)]
            expected = "AMBIGUOUS_GDL_PARAMETER_NAME"
        elif mode == 1:
            base["isLocked"] = True
            expected = "GDL_PARAMETER_LOCKED_OR_DISABLED"
        elif mode == 2:
            base["flags"] = ["Disabled"]
            expected = "GDL_PARAMETER_LOCKED_OR_DISABLED"
        elif mode == 3:
            base["dimension2"] = 3
            expected = "GDL_DIMENSION_OR_CARDINALITY_MISMATCH"
        elif mode == 4:
            changes[name] = [[5.0, 6.0], [7.0]]
            expected = "GDL_DIMENSION_OR_CARDINALITY_MISMATCH"
        elif mode == 5:
            changes[name] = [5.0, True, 7.0, 8.0]
            expected = "GDL_PARAMETER_TYPE_MISMATCH"
        elif mode == 6:
            changes[name] = 4.5
            expected = "GDL_SCALAR_ARRAY_RANK_CHANGE_NOT_SUPPORTED"
        else:
            changes[name] = [5.0, 6.0, float("nan"), 8.0]
            expected = "GDL_PARAMETER_TYPE_MISMATCH"
        original = copy.deepcopy(source)
        with self.assertRaisesRegex(ValueError, expected):
            EDIT.prepare_existing_gdl_edit(router(), f"00000000-0000-4000-8000-{seed+1:012x}", source, changes)
        if mode != 7:
            self.assertEqual(source, original)
    return check


for i in range(32):
    testcase("gdl_invalid_rank_lock_type", i, gdl_invalid(i))


ASSEMBLY_KINDS = (
    ("CurtainWall", "heightMetres"),
    ("CurtainWallFrame", "surfaceId"),
    ("CurtainWallPanel", "thicknessMetres"),
    ("Railing", "defaultSegmentHeightMetres"),
    ("RailingSegment", "heightMetres"),
    ("RailingNode", "elevationMetres"),
    ("RailingRail", "horizontalOffsetMetres"),
    ("RailingHandrail", "visible"),
    ("Shell", "relativeLevelMetres"),
)


def assembly_snapshot(kind, field, seed):
    value = (bool(seed % 2) if field == "visible"
             else {"guid": f"attr-{seed}"} if field.endswith("Id")
             else float(seed) / 7)
    attribute = field.endswith("Id")
    return {
        "elementId": guid(f"assembly-{seed}"),
        "kind": kind,
        "modificationStamp": str(400000 + seed),
        "homeStory": seed % 5 - 2,
        "values": {} if attribute else {field: 0.0 if field != "visible" else True},
        "attributes": {field: {"attributeId": guid(f"old-attr-{seed}")}} if attribute else {},
        "rootElementId": guid(f"assembly-root-{seed}"),
    }, {field: value}


def assembly_valid(seed):
    def check(self):
        kind, field = ASSEMBLY_KINDS[seed % len(ASSEMBLY_KINDS)]
        source, changed = assembly_snapshot(kind, field, seed)
        before_source = copy.deepcopy(source)
        before_change = copy.deepcopy(changed)
        prepared = EDIT.prepare_assembly_edit(router(), source, changed)
        self.assertEqual(source, before_source)
        self.assertEqual(changed, before_change)
        self.assertEqual(prepared["state"], before_source)
        self.assertEqual(prepared["stateHash"], EDIT.digest(source))
        self.assertEqual(prepared["executor"], "SceneWriter")
        self.assertFalse(prepared["executionPermission"])
        self.assertEqual(prepared["nativeModelWrites"], 0)
        self.assertEqual(prepared["engineering"], "NOT_VERIFIED")
        ticket = prepared["ticket"]
        self.assertFalse(ticket["nativeWritePermission"])
        router().validate(ticket)
        self.assertIn("ModifyNativeAssemblyV1", ticket["command"])
        self.assertEqual(ticket["parameters"], dict(
            elementId=source["elementId"], expectedKind=kind,
            expectedModificationStamp=source["modificationStamp"], changes=changed))
        self.assertEqual(ticket["effect"], "MODIFY")
        self.assertEqual(router().catalog["commands"][ticket["command"]]["impact"],
                         "MODEL")
    return check


for i in range(32):
    testcase("assembly_preview_no_write_intent", i, assembly_valid(i))


def assembly_rejected(seed):
    def check(self):
        kind, field = ASSEMBLY_KINDS[seed % len(ASSEMBLY_KINDS)]
        state, changes = assembly_snapshot(kind, field, seed)
        mode = seed % 8
        if mode == 0:
            changes = {}
            expected = "ASSEMBLY_FIELD_NOT_APPLICABLE_TO_CAPTURED_STATE"
        elif mode == 1:
            changes = {"unknownPhysicalContact": "guessed"}
            expected = "ASSEMBLY_FIELD_NOT_APPLICABLE_TO_CAPTURED_STATE"
        elif mode == 2:
            state["modificationStamp"] = "-100"
            expected = None
        elif mode == 3:
            state["kind"] = "NonNativeMorph"
            expected = None
        elif mode == 4:
            state["elementId"] = {"guid": ""}
            expected = None
        elif mode == 5:
            state["values"]["heightMetres"] = 1
            changes = {"heightMetres": float("inf")}
            expected = None
        elif mode == 6:
            state["values"]["heightMetres"] = 1
            changes = {"heightMetres": 1000001.0}
            expected = None
        else:
            state["values"]["profileCoordinates"] = []
            changes = {"profileCoordinates": [{"x": 0, "y": 0}]}
            expected = None
        copy_state = copy.deepcopy(state)
        with self.assertRaises(Exception) as caught:
            EDIT.prepare_assembly_edit(router(), state, changes)
        if expected is not None:
            self.assertIn(expected, str(caught.exception))
        self.assertEqual(state, copy_state)
    return check


for i in range(32):
    testcase("assembly_reject_unbounded_or_inapplicable", i, assembly_rejected(i))


def topology_namespace_case(seed):
    def check(self):
        kind = ("RoutingElement", "RoutingSegment", "RoutingNode",
                "RigidSegment", "Transition")[seed % 5]
        target = f"TARGET-{seed}"
        owner = f"ROUTE-{seed}"
        segment = f"SEGMENT-{seed}"
        node = f"NODE-{seed}"
        row = dict(elementId=guid(target.lower() if seed % 2 else target),
                   kind=kind, routingElementId=guid(owner),
                   routingSegmentId=guid(segment), routingNodeId=guid(node))
        captured = {"elements": [row]}
        copy_capture = copy.deepcopy(captured)
        result = dependency_inputs(mep_topology=captured)
        target_id = ("MEP_SEGMENT:" if kind == "RoutingSegment" else
                     "MEP_NODE:" if kind == "RoutingNode" else "") + target
        expected = {
            (owner, target_id),
            ("MEP_SEGMENT:" + segment, target_id),
            ("MEP_NODE:" + node, target_id),
        }
        expected = {(a,b) for a,b in expected if a != b}
        self.assertEqual(pairs(result), expected)
        self.assertEqual(captured, copy_capture)
        self.assertEqual(result["nodes"], sorted(set(
            [n for p in expected for n in p])))
        self.assertEqual(set(e["kind"] for e in result["relationshipEvidence"]), {
            "NATIVE_MEP_ROUTE_OWNERSHIP",
            "NATIVE_MEP_RIGID_SEGMENT_OWNER",
            "NATIVE_MEP_FITTING_NODE_OWNER",
        })
        self.assertEqual(result["connectionFacts"], [])
        self.assertEqual(result["ifcPropertyFacts"], [])
        self.assertEqual(result["authority"],
                         "CAPTURED_NATIVE_RELATIONSHIPS_NOT_PHYSICAL_CONTACT")
    return check


for i in range(32):
    testcase("mep_route_segment_node_identity", i, topology_namespace_case(i))


def reciprocal_mep_case(seed):
    def check(self):
        mode = seed % 4
        owner_a, owner_b = f"OWNER-A-{seed}", f"OWNER-B-{seed}"
        pa, pb = f"PORT-A-{seed}", f"PORT-B-{seed}"
        a = {"portId": pa, "connectedPortId": pb, "isPhysicallyConnected": True}
        b = {"portId": pb, "connectedPortId": pa, "isPhysicallyConnected": True}
        if mode == 1:
            b["connectedPortId"] = "PORT-THIRD-NOT-CAPTURED"
        elif mode == 2:
            b["isPhysicallyConnected"] = False
        elif mode == 3:
            b["connectedPortId"] = None
        capture = {"portGroups": [
            {"elementId": guid(owner_a), "identityAuthority": "SOURCE_ORDERED_REQUEST",
             "native": {"ports": [a]}},
            {"elementId": guid(owner_b), "identityAuthority": "SOURCE_ORDERED_REQUEST",
             "native": {"ports": [b]}}
        ]}
        original = copy.deepcopy(capture)
        r = dependency_inputs(mep=capture)
        self.assertEqual(capture, original)
        cands = [v for v in r["connectionFacts"]
                 if v["connection"] == "MEP_CONNECTION:" + ":".join(sorted((pa,pb)))]
        self.assertEqual(len(cands), 1)
        c = cands[0]
        self.assertEqual(c["peerCaptured"], True)
        self.assertEqual(c["reciprocal"], mode == 0 or mode == 2)
        self.assertEqual(c["physical"], True if mode == 0 else None)
        self.assertEqual(c["authority"],
                         "BILATERAL_NATIVE_PORT_READ" if mode == 0
                         else "SINGLE_SIDED_OR_LOGICAL_NATIVE_REFERENCE_NOT_PHYSICAL_PASS")
        self.assertTrue(all("NOT_PHYSICAL_CONTACT" in r["authority"]
                            for _ in range(1)))
        self.assertEqual(len([p for p in r["edges"]
                              if "MEP_CONNECTION:" in p[1]]), 3 if mode == 1 else 2)
    return check


for i in range(24):
    testcase("mep_reciprocal_physical_proof", i, reciprocal_mep_case(i))


TOTAL = 40 + 32 + 32 + 32 + 32 + 24
assert TOTAL == 192
assert len(unittest.defaultTestLoader.loadTestsFromTestCase(
    PR107ParametricOffline)._tests) == TOTAL

if __name__ == "__main__":
    unittest.main()
