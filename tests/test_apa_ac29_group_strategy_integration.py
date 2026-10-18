"""Only NEW AC29 group-selection integration; no redundant SDK mutation tests.

No Archicad, no local PLN, no native write. The existing native workflow
compiler/SceneWriter is represented by a strict capturing stub so that the
test checks *routing*, not a second implementation of the native operations.
"""
import copy
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from apa_ac29_group_strategy import route, workflow_for_selected
from apa_ac29_semantic_operation_selector import analyze

FAM = "COLUMN_NATIVE_BIM_FAMILY_SHA_abcdef1234567890"
REF = "KR_CONSTRUCTION_SOURCE_VERIFIED"
G1 = "8bcc2a69-43d7-472a-ba2b-97bd9599d25e"
G2 = "462bc642-a5fa-431f-b728-f5a25ecbfa64"
GROUP = "1991d5e5-74fb-462f-b482-dafd2773f789"


def source(guid, x, y):
    return dict(guid=guid, type="Column", familySignature=FAM,
                storyIndex=0, anchor=dict(x=x, y=y, z=0),
                nativeReadbackVerified=True)


def target(x, y):
    return dict(type="Column", familySignature=FAM,
                storyIndex=0, anchor=dict(x=x, y=y, z=0),
                sourceRef=REF)


def assembly(**updates):
    candidate = dict(sourceRef=REF, memberGuids=[G1, G2],
                     placements=[dict(dx=10, dy=0, dz=0),
                                 dict(dx=20, dy=0, dz=0)],
                     sameStory=True, dependenciesVerified=True,
                     existingGroupGuid=GROUP, groupReadbackVerified=True)
    candidate.update(updates)
    return candidate


def inputs():
    existing = [source(G1, 0, 0), source(G2, 0, 2)]
    targets = [target(x, y) for x in (10, 20) for y in (0, 2)]
    return existing, targets


class CapturingRouter:
    def __init__(self, *, runtime=True):
        self.catalog = {"commands": {
            "AddOn.TapirCommand.CreateNativeGroupV1": {},
            "AddOn.TapirCommand.CloneNativeGroupV1": {},
            "MoveElements": {},
            "CreateColumns": {},
            "CreateBeams": {},
        }}
        self.registration = {n: runtime for n in self.catalog["commands"]}

    def operation_kind(self, command):
        return "CREATE"


def capture_plan(router, existing, targets, groups):
    picked = route(existing, targets, groups)
    module = types.ModuleType("archicad_project_accelerator")
    called = []

    def prepare_native_task(_router, intent):
        assert _router is router
        called.append(copy.deepcopy(intent))
        return dict(schema="APA_NATIVE_TASK_PREVIEW_V1",
                    request=intent["request"],
                    workflow={"graph": intent["graph"]},
                    executionPermission=False)
    module.prepare_native_task = prepare_native_task
    with patch.dict(sys.modules, {"archicad_project_accelerator": module}):
        prepared = workflow_for_selected(router, "Group first", existing, targets, picked)
    return picked, prepared, called


class NativeGroupFirstRouting(unittest.TestCase):
    def test_exact_existing_group_covers_four_targets_no_member_recopy(self):
        existing, targets = inputs()
        result = analyze(existing, targets, assembly_groups=[assembly()])
        self.assertEqual(result["groupedTargets"], 4)
        self.assertEqual(result["ungroupedTargets"], 0)
        self.assertEqual(result["copies"], [])
        self.assertEqual(result["creates"], [])
        self.assertEqual(result["assemblies"][0]["routeCommands"],
                         ["CloneNativeGroupV1"])
        self.assertEqual(result["groupNativeCallsIfIndependentlyAuthorized"], 1)
        self.assertEqual(result["nativeModelWrites"], 0)
        self.assertFalse(result["automaticNativeExecution"])

    def test_existing_native_group_compiles_one_original_graph_command(self):
        existing, targets = inputs()
        chosen, preview, called = capture_plan(
            CapturingRouter(), existing, targets, [assembly()])
        graph = called[0]["graph"]["operations"]
        self.assertEqual(len(graph), 1)
        self.assertEqual(graph[0]["command"], "AddOn.TapirCommand.CloneNativeGroupV1")
        self.assertEqual(graph[0]["params"]["translations"], [
            dict(dx=10, dy=0, dz=0), dict(dx=20, dy=0, dz=0)
        ])
        self.assertEqual(graph[0]["params"]["groupId"]["guid"], GROUP)
        self.assertEqual(preview["status"], "ONE_SOURCE_QUALIFIED_STRATEGY_PREPARED")
        self.assertEqual(preview["groupedTargetCount"], 4)
        self.assertFalse(preview["nativeWritePermission"])
        self.assertEqual(chosen["coveredTargetIndices"], [0, 1, 2, 3])

    def test_ungrouped_assembly_compiles_create_then_clone_result_binding(self):
        existing, targets = inputs()
        planned = assembly(existingGroupGuid=None,
                           groupReadbackVerified=False,
                           ungroupedReadbackVerified=True)
        _, preview, called = capture_plan(
            CapturingRouter(), existing, targets, [planned])
        graph = called[0]["graph"]["operations"]
        self.assertEqual([s["command"] for s in graph], [
            "AddOn.TapirCommand.CreateNativeGroupV1",
            "AddOn.TapirCommand.CloneNativeGroupV1"
        ])
        self.assertEqual(
            graph[1]["params"]["groupId"],
            {"$result": {"step": graph[0]["id"], "pointer": "/groupId"}}
        )
        self.assertEqual(preview["groupNativeCallsIfAuthorized"], 2)

    def test_unregistered_native_commands_only_build_nonexecutable_preview(self):
        existing, targets = inputs()
        _, preview, _ = capture_plan(
            CapturingRouter(runtime=False), existing, targets, [assembly()])
        self.assertEqual(preview["status"],
                         "GROUP_WORKFLOW_REQUIRES_FRESH_RUNTIME_REGISTRATION")
        self.assertIsNone(preview["selectedNativeTaskPreview"])
        self.assertEqual(preview["unprobedCommands"],
                         ["AddOn.TapirCommand.CloneNativeGroupV1"])
        self.assertEqual(preview["nativeModelWrites"], 0)

    def test_mixed_group_then_single_copy_never_reduplicates_group_targets(self):
        existing, targets = inputs()
        targets.append(target(33, 0))
        result = analyze(existing, targets, assembly_groups=[assembly()])
        self.assertEqual(result["groupedTargets"], 4)
        self.assertEqual(result["copies"][0]["count"], 1)
        self.assertEqual(result["copies"][0]["nativeCommand"], "MoveElements")
        self.assertEqual(result["copyNativeCallsIfIndependentlyAuthorized"], 1)
        self.assertEqual(result["groupNativeCallsIfIndependentlyAuthorized"], 1)
        _, preview, called = capture_plan(
            CapturingRouter(), existing, targets, [assembly()])
        operations = called[0]["graph"]["operations"]
        self.assertEqual([row["command"] for row in operations],
                         ["AddOn.TapirCommand.CloneNativeGroupV1", "MoveElements"])
        rows = operations[1]["params"]["elementsWithMoveVectors"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["moveVector"], {"x": 33, "y": 0, "z": 0})
        self.assertEqual(preview["individuallyRoutedTargetCount"], 1)

    def test_unverified_or_incomplete_group_never_falls_back_to_members(self):
        existing, targets = inputs()
        for blocked in [
            assembly(groupReadbackVerified=False),
            assembly(dependenciesVerified=False),
            assembly(existingGroupGuid=None),
            assembly(sameStory=False),
            assembly(memberGuids=[G1, G1]),
        ]:
            with self.subTest(blocked=blocked), self.assertRaises(ValueError):
                analyze(existing, targets, assembly_groups=[blocked])

    def test_mismatched_target_geometry_or_provenance_fails_closed(self):
        existing, targets = inputs()
        tests = [
            [(dict(v) if i != 0 else dict(v, sourceRef="DIFFERENT_DOCUMENT"))
             for i, v in enumerate(targets)],
            targets[:-1] + [target(20, 3)],
            targets + [target(10, 0)],
        ]
        for payload in tests:
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                route(existing, payload, [assembly()])

    def test_no_group_intent_preserves_existing_single_copy_selector(self):
        existing, targets = inputs()
        result = analyze(existing, targets)
        self.assertEqual(result["groupedTargets"], 0)
        self.assertEqual(result["groupNativeCallsIfIndependentlyAuthorized"], 0)
        self.assertEqual(result["copies"][0]["count"], 2)
        self.assertTrue(result["copies"])


if __name__ == "__main__":
    unittest.main()
