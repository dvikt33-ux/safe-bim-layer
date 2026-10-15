"""192 new independent PR96 tests for the *actual* native relationship bridge.

Only imported production dependency_inputs / run and existing APA local graph
execute. Synthetic captures; no Archicad process, APX loading, PLN writes,
quantity engine, Drawing status call or network requests.
"""
from __future__ import annotations

import copy
import hashlib
import json
import sys
import unittest
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from apa_native_dependency_flow import dependency_inputs, run


class PR96IndependentRelationships(unittest.TestCase):
    pass


def test_group(name, seed, fn):
    setattr(PR96IndependentRelationships, f"test_pr96_{name}_{seed:03d}", fn)


def ident(value, lower=False):
    return {"guid": value.lower() if lower else value}


def pair_set(rows):
    return {tuple(pair) for pair in rows}


def membership_case(seed):
    def check(self):
        parent = f"PARENT-{seed:03d}"
        children = [f"CHILD-{seed:03d}-{i}" for i in range(1 + seed % 7)]
        owner = ident(parent, lower=bool(seed % 2))
        listed = [{"elementId": ident(x, lower=bool((seed + i) % 2))}
                  for i, x in enumerate(children)]
        # duplicate and invalid child must not increase edge count
        groups = [
            {"parentElementId": owner,
             "subelements": {"StairTreads": listed + [copy.deepcopy(listed[0])],
                             "Misc": [{"elementId": ident("")},
                                      {"elementId": {"guid": None}}]}}
        ]
        if seed % 3 == 0:
            groups.append({"parentElementId": ident("DISCARDED"),
                           "subelements": {"error": {"code": -1},
                                           "items": [{"elementId": ident("IGNORED")}]}})
        before = copy.deepcopy(groups)
        result = dependency_inputs(memberships=groups)
        self.assertEqual(groups, before)
        expected = {(parent, x) for x in children}
        self.assertEqual(pair_set(result["edges"]), expected)
        self.assertEqual(set(result["nodes"]), {parent, *children})
        self.assertEqual(len(result["relationshipEvidence"]), len(expected))
        self.assertTrue(all(row["kind"] == "NATIVE_HIERARCHICAL_MEMBERSHIP"
                            for row in result["relationshipEvidence"]))
        self.assertEqual(result["omitted"],
                         ["MEMBERSHIP_PARENT_OR_NATIVE_RESULT_MISSING"] if seed % 3 == 0 else [])
        self.assertEqual(result["edges"], sorted(result["edges"]))
        self.assertEqual(result["nodes"], sorted(result["nodes"]))
        self.assertEqual(result["authority"],
                         "CAPTURED_NATIVE_RELATIONSHIPS_NOT_PHYSICAL_CONTACT")
    return check


for i in range(32):
    test_group("stair_membership_duplicates_missing", i, membership_case(i))


def component_case(seed):
    def check(self):
        parent, root, child = (f"P-{seed:03d}", f"R-{seed:03d}", f"C-{seed:03d}")
        mode = seed % 8
        p = parent if mode != 1 else child
        r = root if mode in (1, 2, 3, 4, 5, 6, 7) else p
        parent_error = 0 if mode not in (2, 4) else -99
        root_error = 0 if mode not in (3, 4) else -99
        declared = "OTHER-OWNER" if mode in (5, 6) else p
        data = {"elements": [{
            "elementId": ident(child, lower=bool(seed % 2)),
            "parentElementId": ident(p),
            "rootElementId": ident(r),
            "declaredOwnerId": ident(declared),
            "parentQueryError": parent_error,
            "rootQueryError": root_error,
            "homeStory": seed - 16,
            "nativeComponentType": "StairRiser" if mode < 4 else "CurtainWallFrame",
        }]}
        original = copy.deepcopy(data)
        result = dependency_inputs(components=data)
        self.assertEqual(data, original)
        expected = set()
        if parent_error == 0 and p != child:
            expected.add((p, child))
        if root_error == 0 and r != child:
            expected.add((r, child))
        self.assertEqual(pair_set(result["edges"]), expected)
        self.assertEqual(set(result["nodes"]), {child} | {a for a, _ in expected})
        self.assertEqual(len(result["relationshipEvidence"]), len(expected))
        self.assertTrue(all(row["kind"] in
                            ("NATIVE_HIERARCHICAL_PARENT", "NATIVE_HIERARCHICAL_ROOT")
                            for row in result["relationshipEvidence"]))
        expected_omissions = (["DECLARED_OWNER_DIFFERS_FROM_PARENT_NO_INFERRED_EDGE"]
                             if declared != p and parent_error == 0 else [])
        self.assertEqual(result["omitted"], expected_omissions)
        self.assertNotIn((declared, child), expected if declared != p else set())
        self.assertNotIn((child, child), expected)
    return check


for i in range(32):
    test_group("component_parent_root_error_gates", i, component_case(i))


def opening_case(seed):
    def check(self):
        opening = f"OPEN-{seed:03d}"
        host = f"HOST-{seed:03d}"
        connected = f"OTHER-OPEN-{seed:03d}"
        cut_host = f"CUT-HOST-{seed:03d}"
        resolved = bool(seed & 1)
        cut = [ident(cut_host)]
        if seed % 3 == 0:
            cut.append(ident(host))
        links = [ident(connected), ident(connected, lower=True), ident(opening)]
        if seed % 4 == 0:
            links.append({"guid": None})
        payload = {"elements": [{
            "elementId": ident(opening, lower=bool(seed % 2)),
            "hostElementId": ident(host), "parentResolved": resolved,
            "connectedOpenings": links,
            "cutElements": cut,
            "extrusionFrame": {"orientation": seed * 0.1},
        }]}
        frozen = copy.deepcopy(payload)
        found = dependency_inputs(openings=payload)
        self.assertEqual(payload, frozen)
        expected = {(opening, connected), (cut_host, opening)}
        if resolved or seed % 3 == 0:
            expected.add((host, opening))
        self.assertEqual(pair_set(found["edges"]), expected)
        self.assertEqual(set(found["nodes"]),
                         {opening, connected, cut_host} |
                         ({host} if (resolved or seed % 3 == 0) else set()))
        self.assertEqual(len(found["relationshipEvidence"]), len(expected))
        self.assertTrue(all(row["kind"].startswith("NATIVE_")
                            for row in found["relationshipEvidence"]))
        self.assertEqual(found["omitted"], [])
        self.assertNotIn((opening, opening), expected)
        if not resolved and seed % 3 != 0:
            self.assertNotIn((host, opening), expected)
        self.assertEqual(found["authority"],
                         "CAPTURED_NATIVE_RELATIONSHIPS_NOT_PHYSICAL_CONTACT")
    return check


for i in range(32):
    test_group("opening_cut_host_connected_identity", i, opening_case(i))


def drawing_case(seed):
    def check(self):
        v1 = f"VIEW-{seed:03d}-KNOWN"
        v2 = f"VIEW-{seed:03d}-SECOND"
        rows = [
            {"elementId": ident(f"DWG-{seed}-1"), "linkGuid": ident(v1, lower=bool(seed % 2)),
             "viewDeleted": False, "updateStatus": -1},
            {"elementId": ident(f"DWG-{seed}-2"), "linkGuid": ident(v2),
             "viewDeleted": bool(seed % 2), "updateStatus": -1},
            {"elementId": ident(f"DWG-{seed}-3"), "linkGuid": ident("UNLISTED"),
             "viewDeleted": False, "updateStatus": 0},
            {"elementId": ident(f"DWG-{seed}-4"), "linkGuid": ident(v1),
             "viewDeleted": None, "updateStatus": -1},
        ]
        captures = {"drawings": rows}
        source = copy.deepcopy(captures)
        value = dependency_inputs(drawings=captures, view_ids=[v1.lower(), v2.lower()])
        self.assertEqual(captures, source)
        expected = {(v1, f"DWG-{seed}-1")}
        if seed % 2 == 0:
            expected.add((v2, f"DWG-{seed}-2"))
        self.assertEqual(pair_set(value["edges"]), expected)
        self.assertEqual(len(value["omitted"]), 2 + (seed % 2))
        self.assertTrue(all(reason == "DRAWING_SOURCE_NOT_IN_CAPTURED_VIEWMAP"
                            for reason in value["omitted"]))
        self.assertEqual(set(value["nodes"]),
                         {f"DWG-{seed}-{i}" for i in range(1, 5)} |
                         {a for a, _ in expected})
        self.assertTrue(all(e["kind"] == "NATIVE_DRAWING_LINK_VERIFIED_IN_VIEWMAP"
                            for e in value["relationshipEvidence"]))
        # A status of -1 is deliberately not converted into "up to date".
        self.assertNotIn("drawingFreshnessVerified", value)
    return check


for i in range(32):
    test_group("drawing_viewmap_fail_closed", i, drawing_case(i))


def mixed_permutation_case(seed):
    def check(self):
        root, comp, host, opening, view, drawing = (
            f"ROOT-{seed}", f"COMPONENT-{seed}", f"HOST-{seed}",
            f"OPENING-{seed}", f"VIEW-{seed}", f"DRAWING-{seed}")
        captured = {
            "memberships": [
                {"parentElementId": ident(root),
                 "subelements": {"Subcomponents": [{"elementId": ident(comp)}]}},
                {"parentElementId": ident(root.lower()),
                 "subelements": {"Another": [{"elementId": ident(comp.lower())}]}}],
            "components": {"elements": [
                {"elementId": ident(comp), "parentElementId": ident(root.lower()),
                 "rootElementId": ident(root), "parentQueryError": 0,
                 "rootQueryError": 0}]},
            "openings": {"elements": [
                {"elementId": ident(opening), "hostElementId": ident(host),
                 "parentResolved": True, "cutElements": [ident(host.lower())],
                 "connectedOpenings": []}]},
            "drawings": {"drawings": [
                {"elementId": ident(drawing), "linkGuid": ident(view),
                 "viewDeleted": False},
                {"elementId": ident("UNKNOWN-DRAWING"), "linkGuid": ident("MISSING"),
                 "viewDeleted": False}]},
            "view_ids": [view.lower()]
        }
        baseline = copy.deepcopy(captured)
        one = dependency_inputs(**captured)
        changed = copy.deepcopy(captured)
        changed["memberships"].reverse()
        changed["components"]["elements"].reverse()
        changed["openings"]["elements"].reverse()
        changed["drawings"]["drawings"].reverse()
        changed["view_ids"].reverse()
        two = dependency_inputs(**changed)
        self.assertEqual(captured, baseline)
        self.assertEqual(one["edges"], two["edges"])
        self.assertEqual(one["nodes"], two["nodes"])
        self.assertEqual(len(one["edges"]), 3)
        self.assertEqual(pair_set(one["edges"]),
                         {(root, comp), (host, opening), (view, drawing)})
        self.assertEqual(len(one["relationshipEvidence"]), 3)
        self.assertEqual(one["omitted"], ["DRAWING_SOURCE_NOT_IN_CAPTURED_VIEWMAP"])
        self.assertNotIn("PHYSICAL_CONTACT_VERIFIED", one["authority"])
        self.assertEqual(one["authority"],
                         "CAPTURED_NATIVE_RELATIONSHIPS_NOT_PHYSICAL_CONTACT")
    return check


for i in range(32):
    test_group("mixed_graph_permutation_dedup", i, mixed_permutation_case(i))


@lru_cache(maxsize=1)
def shared_router():
    import archicad_project_accelerator as A
    from archicad_dynamic_commands import DynamicCommands
    manifest = json.loads((ROOT / "schemas/accelerator/mass-capabilities/commands.json")
                          .read_text(encoding="utf8"))
    router = DynamicCommands(manifest)
    A.connect_functional_modules(router)
    return router


def graph_dispatch_case(seed):
    def check(self):
        parent = f"START-{seed:03d}"
        leaves = [f"LEAF-{seed:03d}-{i}" for i in range(1 + seed % 6)]
        capture = {
            "memberships": [
                {"parentElementId": ident(parent.lower()),
                 "subelements": {"StairTreads": [
                     {"elementId": ident(name.lower() if seed % 2 else name)}
                     for name in leaves]}}],
            "components": {"elements": [
                {"elementId": ident(leaves[0]),
                 "parentElementId": ident(parent), "rootElementId": ident(parent),
                 "parentQueryError": 0, "rootQueryError": 0}]},
        }
        router = shared_router()
        earlier = len(router.local_events)
        before = copy.deepcopy(capture)
        answer = run(router, capture, [parent.lower()])
        self.assertEqual(capture, before)
        self.assertEqual(answer["nativeModelWrites"], 0)
        self.assertFalse(answer["executionPermission"])
        self.assertEqual(answer["sourceSHA256"], hashlib.sha256(
            json.dumps(capture, sort_keys=True).encode()).hexdigest())
        self.assertEqual(len(answer["sourcePlanHash"]), 64)
        self.assertEqual(answer["status"], "WORKFLOW_CALLABLE_VERIFIED")
        self.assertEqual(set(answer["result"]["updateOrder"]), {parent, *leaves})
        self.assertEqual(answer["result"]["updateOrder"][0], parent)
        self.assertTrue(answer["result"]["executionAllowed"])
        self.assertEqual(len(router.local_events), earlier + 1)
        self.assertEqual(router.local_events[-1]["nativeWrites"], 0)
        with self.assertRaisesRegex(ValueError, "CHANGED_NODE_NOT_PRESENT"):
            run(router, capture, [f"MISSING-{seed}"])
        self.assertEqual(len(router.local_events), earlier + 1)
        self.assertNotIn("QUANTITIES", json.dumps(answer).upper())
    return check


for i in range(32):
    test_group("actual_graph_local_readonly_dispatch", i, graph_dispatch_case(i))


COUNT = 32 * 6
assert len(unittest.defaultTestLoader.loadTestsFromTestCase(
    PR96IndependentRelationships)._tests) == COUNT == 192

if __name__ == "__main__":
    unittest.main()
