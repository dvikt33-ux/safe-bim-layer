"""Independent PR96-specific OFFLINE QA: 192 newly discovered cases, six domains.

Scope: captured SDK *contracts* and native-relationship conversion through the
existing APA BIM Graph. No active Archicad, APX, PLN or native quantity calls.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import sys
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from apa_native_dependency_flow import dependency_inputs, run
from archicad_dynamic_commands import DynamicCommands
import archicad_project_accelerator as APA

COMMAND_NAMES = (
    "GetNativeComponentBindingsV1",
    "GetNativeOpeningConnectionsV1",
    "GetNativeQuantityPreflightV1",
    "GetNativeEnvelopeMemoV1",
    "GetNativeDrawingAssociationsV1",
)


def gid(value):
    return {"guid": value}


def named(seed, name):
    return f"{name}_{seed:03d}"


def edge_names(result):
    return {tuple(row) for row in result["edges"]}


def connected_router():
    catalog = json.loads((ROOT / "schemas/accelerator/mass-capabilities/commands.json")
                         .read_text(encoding="utf8"))
    r = DynamicCommands(catalog)
    APA.connect_functional_modules(r)
    return r


class PR96NativeRelationshipContracts(unittest.TestCase):
    """Unique deterministic mutation scenarios, no cloned production algorithm."""


def add_group(group, index, function):
    setattr(PR96NativeRelationshipContracts, f"test_pr96_{group}_{index:03d}", function)


def component_case(seed):
    def check(self):
        child, parent, root = (named(seed, s) for s in ("child", "parent", "root"))
        mode = seed % 8
        obj = {"elementId": gid(child), "parentElementId": gid(parent),
               "rootElementId": gid(root), "declaredOwnerId": gid(parent),
               "parentQueryError": 0, "rootQueryError": 0,
               "homeStory": seed % 9 - 4, "nativeTypeId": 160 + seed % 4}
        expected = {(parent.upper(), child.upper()),
                    (root.upper(), child.upper())}
        omitted = []
        if mode == 1:
            obj["rootElementId"] = gid(parent)
            expected = {(parent.upper(), child.upper())}
        elif mode == 2:
            obj["parentQueryError"] = -1
            expected = {(root.upper(), child.upper())}
        elif mode == 3:
            obj["rootQueryError"] = -1
            expected = {(parent.upper(), child.upper())}
        elif mode == 4:
            obj["parentQueryError"] = -1
            obj["rootQueryError"] = -2
            expected = set()
        elif mode == 5:
            obj["declaredOwnerId"] = gid(named(seed, "different"))
            omitted = ["DECLARED_OWNER_DIFFERS_FROM_PARENT_NO_INFERRED_EDGE"]
        elif mode == 6:
            obj["parentElementId"] = gid(child)
            obj["declaredOwnerId"] = gid(child)
            expected = {(root.upper(), child.upper())}
        elif mode == 7:
            obj["rootElementId"] = gid(child)
            expected = {(parent.upper(), child.upper())}
        source = {"elements": [obj]}
        immutable = copy.deepcopy(source)
        actual = dependency_inputs(components=source)
        self.assertEqual(source, immutable)
        self.assertEqual(edge_names(actual), expected)
        self.assertEqual(actual["omitted"], omitted)
        self.assertEqual(actual["authority"],
                         "CAPTURED_NATIVE_RELATIONSHIPS_NOT_PHYSICAL_CONTACT")
        self.assertTrue(all(x["kind"].startswith("NATIVE_HIERARCHICAL_")
                            for x in actual["relationshipEvidence"]))
        self.assertIn(child.upper(), actual["nodes"])
    return check


for i in range(32):
    add_group("component_error_owner_boundaries", i, component_case(i))


def opening_case(seed):
    def check(self):
        op, host, cut, side = (named(seed, s) for s in
                               ("opening", "host", "cut_host", "other_opening"))
        mode = seed % 8
        row = {"elementId": gid(op), "parentResolved": True,
               "hostElementId": gid(host), "cutElements": [gid(cut)],
               "connectedOpenings": [gid(side)], "nativeTypeId": 77}
        expected = {(host.upper(), op.upper()), (cut.upper(), op.upper()),
                    (op.upper(), side.upper())}
        omission = []
        if mode == 1:
            row["parentResolved"] = False
            expected.remove((host.upper(), op.upper()))
        elif mode == 2:
            row["hostElementId"] = gid(op)
            expected.remove((host.upper(), op.upper()))
        elif mode == 3:
            row["cutElements"] = [gid(host)]
            expected.remove((cut.upper(), op.upper()))
        elif mode == 4:
            row["parentResolved"] = False
            row["cutElements"] = []
            row["connectedOpenings"] = []
            expected = set()
        elif mode == 5:
            row["cutElements"] = [gid(cut), gid(cut.lower()), gid(cut.upper())]
        elif mode == 6:
            row["connectedOpenings"] = [gid(op), gid(side)]
        else:
            row = {"error": {"code": -100, "message": "not exposed"}}
            expected = set()
            omission = ["OPENING_ERROR_OR_ID_MISSING"]
        source = {"elements": [row]}
        before = copy.deepcopy(source)
        out = dependency_inputs(openings=source)
        self.assertEqual(source, before)
        self.assertEqual(edge_names(out), expected)
        self.assertEqual(out["omitted"], omission)
        self.assertEqual(len(out["relationshipEvidence"]), len(expected))
        self.assertTrue(all(e["kind"] in (
            "NATIVE_OPENING_HOST", "NATIVE_HOST_CONNECTED_OPENING",
            "NATIVE_OPENING_CUT_HOST") for e in out["relationshipEvidence"]))
        self.assertNotIn((op.upper(), op.upper()), expected)
        self.assertNotIn((op.upper(), op.upper()), edge_names(out))
    return check


for i in range(32):
    add_group("positive_opening_host_cut_contract", i, opening_case(i))


def drawing_case(seed):
    def check(self):
        drawing, view, unknown = (named(seed, s) for s in
                                  ("drawing", "captured_view", "external_view"))
        mode = seed % 8
        row = {"elementId": gid(drawing), "linkGuid": gid(view),
               "viewDeleted": False, "updateStatus": -1,
               "statusQueryError": 0, "contentBoxQueryError": 0}
        captured = [view]
        expected = {(view.upper(), drawing.upper())}
        omission = []
        if mode == 1:
            row["viewDeleted"] = True
            expected = set()
            omission = ["DRAWING_SOURCE_NOT_IN_CAPTURED_VIEWMAP"]
        elif mode == 2:
            row["linkGuid"] = gid(unknown)
            expected = set()
            omission = ["DRAWING_SOURCE_NOT_IN_CAPTURED_VIEWMAP"]
        elif mode == 3:
            row["viewDeleted"] = None
            expected = set()
            omission = ["DRAWING_SOURCE_NOT_IN_CAPTURED_VIEWMAP"]
        elif mode == 4:
            row["linkGuid"] = gid(view.lower())
            captured = [view.upper()]
        elif mode == 5:
            row["linkGuid"] = gid(view.upper())
        elif mode == 6:
            row["elementId"] = {}
            expected = set()
            omission = ["DRAWING_ERROR_OR_ID_MISSING"]
        else:
            row["updateStatus"] = -1
            row["statusQueryError"] = -55
            row["contentBoxQueryError"] = -55
            # A ViewMap link is structural, not proof of current contents.
        out = dependency_inputs(drawings={"drawings": [row]}, view_ids=captured)
        self.assertEqual(edge_names(out), expected)
        self.assertEqual(out["omitted"], omission)
        self.assertEqual(len(out["relationshipEvidence"]), len(expected))
        self.assertNotIn("UP_TO_DATE", json.dumps(out))
        self.assertTrue(all(e["kind"] == "NATIVE_DRAWING_LINK_VERIFIED_IN_VIEWMAP"
                            for e in out["relationshipEvidence"]))
    return check


for i in range(32):
    add_group("drawing_known_view_only", i, drawing_case(i))


def membership_case(seed):
    def check(self):
        parent = named(seed, "stair")
        children = [named(seed, f"stairpart{i}") for i in range(3)]
        mode = seed % 8
        group = {"parentElementId": gid(parent),
                 "subelements": {"Treads": [{"elementId": gid(children[0])}],
                                 "Risers": [{"elementId": gid(children[1])}],
                                 "Structures": [{"elementId": gid(children[2])}]}}
        expected = {(parent.upper(), c.upper()) for c in children}
        omitted = []
        if mode == 1:
            group["subelements"]["Structures"] = []
            expected.remove((parent.upper(), children[2].upper()))
        elif mode == 2:
            group["subelements"]["Risers"].append({"elementId": gid(children[0])})
        elif mode == 3:
            group["subelements"]["Treads"].append({"elementId": gid(parent)})
        elif mode == 4:
            group["parentElementId"] = {}
            expected = set()
            omitted = ["MEMBERSHIP_PARENT_OR_NATIVE_RESULT_MISSING"]
        elif mode == 5:
            group["subelements"] = {"error": -12}
            expected = set()
            omitted = ["MEMBERSHIP_PARENT_OR_NATIVE_RESULT_MISSING"]
        elif mode == 6:
            group["subelements"]["Other"] = "NOT_AN_ELEMENT_ARRAY"
        elif mode == 7:
            group["subelements"]["Risers"][0] = {"elementId": {}}
            expected.remove((parent.upper(), children[1].upper()))
        components = {"elements": [
            {"elementId": gid(children[0]), "parentElementId": gid(parent),
             "parentQueryError": 0, "rootElementId": gid(parent),
             "rootQueryError": 0}]}
        if mode in (4, 5):
            # Independent component evidence remains even if membership lookup fails.
            expected = {(parent.upper(), children[0].upper())}
        a = dependency_inputs(memberships=[group], components=components)
        self.assertEqual(edge_names(a), expected)
        self.assertEqual(a["omitted"], omitted)
        self.assertEqual(len(a["relationshipEvidence"]), len(expected))
    return check


for i in range(32):
    add_group("stair_membership_merge_dedup", i, membership_case(i))


def impact_case(seed):
    def check(self):
        root = named(seed, "roof")
        a, b, leaf = (named(seed, k) for k in ("frame_a", "frame_b", "surface"))
        isolated = named(seed, "alone")
        captured = {"components": {"elements": [
            {"elementId": gid(a), "parentElementId": gid(root),
             "parentQueryError": 0, "rootQueryError": -1},
            {"elementId": gid(b), "parentElementId": gid(root),
             "parentQueryError": 0, "rootQueryError": -1},
            {"elementId": gid(leaf), "parentElementId": gid(a),
             "parentQueryError": 0, "rootQueryError": -1},
            {"elementId": gid(isolated), "parentQueryError": -1, "rootQueryError": -1},
        ]}}
        mode = seed % 4
        changed = [root] if mode == 0 else [a] if mode == 1 else \
                  [isolated] if mode == 2 else [named(seed, "unseen")]
        expected = {root, a, b, leaf} if mode == 0 else \
                   {a, leaf} if mode == 1 else {isolated}
        r = connected_router()
        source = copy.deepcopy(captured)
        if mode == 3:
            with self.assertRaisesRegex(ValueError,
                                         "CHANGED_NODE_NOT_PRESENT_IN_NATIVE_RELATIONSHIPS"):
                run(r, captured, changed)
            self.assertEqual(captured, source)
            self.assertEqual(r.local_events, [])
            return
        out = run(r, captured, changed)
        self.assertEqual(captured, source)
        self.assertEqual(set(out["result"]["updateOrder"]),
                         {x.upper() for x in expected})
        order = out["result"]["updateOrder"]
        self.assertEqual(order[0], changed[0].upper())
        if mode == 0:
            self.assertLess(order.index(a.upper()), order.index(leaf.upper()))
        self.assertEqual(out["status"], "WORKFLOW_CALLABLE_VERIFIED")
        self.assertFalse(out["executionPermission"])
        self.assertEqual(out["nativeModelWrites"], 0)
        self.assertEqual(out["sourceSHA256"], hashlib.sha256(
            json.dumps(captured, sort_keys=True).encode()).hexdigest())
        self.assertEqual(len(out["sourcePlanHash"]), 64)
        self.assertEqual(len(r.local_events), 1)
    return check


for i in range(32):
    add_group("real_bim_graph_multibranch_impact", i, impact_case(i))


def sdk_abi_case(seed):
    def check(self):
        manifest = json.loads(
            (ROOT / "schemas/accelerator/functional-modules.json")
            .read_text(encoding="utf8"))["sdkProviders"]["TapirCommand"]
        exported = (ROOT / "archicad-addon/Sources/NativeExtendedSchemas.inc"
                    ).read_text(encoding="utf8")
        name = COMMAND_NAMES[seed % len(COMMAND_NAMES)]
        entry = manifest[name]
        def native_schema(method):
            pattern = re.escape(name) + r'Command::' + method + \
                      r'\(\) const \{return R"APA\((.*?)\)APA";\}'
            match = re.search(pattern, exported, flags=re.DOTALL)
            self.assertIsNotNone(match, f"Missing generated native schema for {name}")
            return json.loads(match.group(1))

        input_sdk = native_schema("GetInputParametersSchema")
        output_sdk = native_schema("GetRawResponseSchema")
        self.assertEqual(input_sdk, entry["parameters"])
        self.assertEqual(output_sdk, entry["returns"])
        params = {"elements": [{"elementId": gid(named(seed, "sdk_element"))}]}
        if name == "GetNativeDrawingAssociationsV1":
            params["elements"][0]["databaseId"] = gid(named(seed, "layout"))
        Draft202012Validator(input_sdk).validate(params)
        # Distinct invalid request shapes, rejected identically by C++ and APA.
        invalid = copy.deepcopy(params)
        mutation = seed % 6
        if mutation == 0:
            invalid["elements"] = []
        elif mutation == 1:
            invalid["elements"] = params["elements"] * 33
        elif mutation == 2:
            invalid["elements"][0]["elementId"]["guid"] = ""
        elif mutation == 3:
            invalid["elements"][0]["elementId"]["guid"] = 42
        elif mutation == 4:
            invalid["elements"][0]["unknownField"] = seed
        else:
            invalid["unexpected"] = True
        self.assertFalse(Draft202012Validator(input_sdk).is_valid(invalid))
        self.assertFalse(Draft202012Validator(entry["parameters"]).is_valid(invalid))
        # PRE-ENGINE response never admits escalation of the native quantity engine.
        if name == "GetNativeQuantityPreflightV1":
            successful = {"nativeModelWrites": 0, "quantityEngineCalled": False,
                          "quarantineRetained": True, "elements": [{
                              "elementId": gid(named(seed, "sdk_element")),
                              "nativeTypeId": 8, "homeStory": 0,
                              "stage": "PRE_ENGINE_ELEMENT_IDENTIFIED_NO_QUANTITY_CALL",
                              "engineCallAllowed": False,
                          }]}
            Draft202012Validator(output_sdk).validate(successful)
            for key, val in (("quantityEngineCalled", True),
                             ("quarantineRetained", False),
                             ("nativeModelWrites", 1)):
                changed = copy.deepcopy(successful)
                changed[key] = val
                self.assertFalse(Draft202012Validator(output_sdk).is_valid(changed))
    return check


for i in range(32):
    add_group("native_cpp_manifest_schema_parity", i, sdk_abi_case(i))


EXPECTED = 192
assert len(unittest.defaultTestLoader.loadTestsFromTestCase(
    PR96NativeRelationshipContracts)._tests) == EXPECTED

if __name__ == "__main__":
    unittest.main()
