"""AC29 1..32 group grid: pure selection and variable-count verifier bookkeeping.

Does not call Archicad, does not bypass SceneWriter or write a PLN.
Geometry in the synthetic postflight is mocked: the real independent BREP
checks continue to run in the unchanged column_facts/verify_batch_layout
helpers, and >2-copy LIVE acceptance is expressly NOT claimed here.
"""
from pathlib import Path
import copy
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import apa_ac29_native_group_grid as GRID
import apa_ac29_native_group_clone_verifier as VERIFY

G1 = "8bcc2a69-43d7-472a-ba2b-97bd9599d25e"
G2 = "462bc642-a5fa-431f-b728-f5a25ecbfa64"
NATIVE_GROUP = "1991d5e5-74fb-462f-b482-dafd2773f789"
SOURCE_REF = "https://github.com/dvikt33-ux/safe-bim-layer/pull/164"
FAM1, FAM2 = "native-column-family-stable-01", "native-column-family-stable-02"


def grid(columns=8, rows=4, stepX=25, stepY=8, startDx=25, startDy=0):
    return {
        "schema": GRID.SCHEMA, "columns": columns, "rows": rows,
        "stepX": stepX, "stepY": stepY,
        "startDx": startDx, "startDy": startDy
    }


def input_source():
    existing = [
        dict(guid=G1, type="Column", familySignature=FAM1,
             storyIndex=0, anchor=dict(x=0, y=0, z=0),
             nativeReadbackVerified=True),
        dict(guid=G2, type="Column", familySignature=FAM2,
             storyIndex=0, anchor=dict(x=0, y=2, z=0),
             nativeReadbackVerified=True),
    ]
    assembly = dict(sourceRef=SOURCE_REF, memberGuids=[G1, G2],
                    sameStory=True, dependenciesVerified=True,
                    existingGroupGuid=NATIVE_GROUP,
                    groupReadbackVerified=True)
    return existing, assembly


def gid(number):
    return f"00000000-0000-4000-8000-{number:012d}"


def synthetic(native_offsets):
    """One complete set of deterministic GUIDs for synthetic strict bookkeeping."""
    source = gid(9000)
    members = [gid(1000), gid(1001)]
    old = {gid(1000 + i) for i in range(44)}
    group_guids = [gid(2000 + i) for i in range(len(native_offsets))]
    new_roots = [gid(3000 + i) for i in range(len(native_offsets) * 2)]
    new_children = [gid(4000 + i) for i in range(len(native_offsets) * 2)]
    groups = {source: set(members)}
    column_rows = {}
    src_anchor = [{"x": 0, "y": 0, "z": 0}, {"x": 0, "y": 2, "z": 0}]
    source_facts = {
        members[k]: dict(anchor=src_anchor[k], typed=f"typed-{k}",
                         solid=f"solid-{k}")
        for k in range(2)
    }
    for index, shift in enumerate(native_offsets):
        roots = new_roots[2*index:2*index + 2]
        groups[group_guids[index]] = set(roots)
        for k, parent in enumerate(roots):
            column_rows[parent] = dict(
                anchor={
                    "x": src_anchor[k]["x"] + shift["dx"],
                    "y": src_anchor[k]["y"] + shift["dy"],
                    "z": src_anchor[k]["z"] + shift["dz"],
                },
                typed=f"typed-{k}", solid=f"solid-{k}",
                source=({"guid": parent},
                        [(new_children[2*index+k], {"guid": new_children[2*index+k]})]))
    after = old | set(new_roots) | set(new_children)
    params = {
        "groupId": {"guid": source},
        "sourceRef": SOURCE_REF,
        "translations": native_offsets
    }
    proof = {
        "status": "GROUP_CLONE_SOURCE_OWNED_NATIVE_BREP_AND_LAYOUT_PASS",
        "group": source, "offsets": native_offsets,
        "members": members, "sourceFacts": source_facts,
        "sourceNativeGuidCount": len(old)
    }
    reply = {
        "nativeModelWrites": len(new_roots),
        "sourceGroupId": {"guid": source},
        "newGroupIds": [{"guid": g} for g in group_guids],
        "createdElements": [{"elementId": {"guid": g}} for g in new_roots]
    }
    nodes = [{"guid": g} for g in sorted(after)]
    return dict(groups=groups, columns=column_rows, source=source, members=members,
                before=old, after=after, params=params, proof=proof,
                native=reply, model={"elements": nodes})


def audited_postflight(data):
    with patch.object(VERIFY, "group_member_ids",
                      side_effect=lambda api, group: data["groups"][group]), \
         patch.object(VERIFY, "column_facts",
                      side_effect=lambda api, nodes, members:
                      {g: data["columns"][g] for g in members}):
        return VERIFY.verify_after(
            api=object(), command=VERIFY.CMD,
            parameters=data["params"], native_response=data["native"],
            before_guids=data["before"], after_guids=data["after"],
            affected=[], native_before={"elements": []},
            native_after=data["model"], source_proof=data["proof"]
        )


class AC29GridPreview(unittest.TestCase):
    def test_8_by_4_grid_compiles_one_existing_native_clone(self):
        from archicad_dynamic_commands import DynamicCommands
        import archicad_project_accelerator as APA
        root = Path(__file__).resolve().parents[1]
        router = DynamicCommands(APA.catalog_with_provenance(
            root / "schemas/tapir-live-1.5.10/tapir-scene-live.json"))
        APA.connect_functional_modules(router)
        router.register_availability(VERIFY.CMD, True)
        existing, assembly = input_source()
        original = copy.deepcopy((existing, assembly))
        result = GRID.prepare_group_grid_preview(
            router, existing, assembly, grid(), "Replicate 2 verified columns on 8x4")
        self.assertEqual((existing, assembly), original)
        self.assertEqual(result["executionPermission"], False)
        self.assertEqual(result["modelWrites"], 0)
        self.assertTrue(result["requiresNativeBREPCollisionVerifier"])
        self.assertEqual(len(result["intent"]["targets"]), 64)
        self.assertEqual(len(result["intent"]["assemblyGroups"][0]["placements"]), 32)
        preview = result["preview"]
        self.assertEqual(preview["nativeCallCountIfAuthorized"], 1)
        self.assertEqual(preview["groupNativeCallsIfAuthorized"], 1)
        self.assertEqual(preview["individuallyRoutedTargetCount"], 0)
        self.assertFalse(preview["nativeWritePermission"])
        graph = preview["selectedNativeTaskPreview"]["workflow"]["graph"]["operations"]
        self.assertEqual(len(graph), 1)
        self.assertEqual(graph[0]["command"], VERIFY.CMD)
        self.assertEqual(len(graph[0]["params"]["translations"]), 32)
        self.assertEqual(graph[0]["params"]["translations"][0],
                         {"dx": 25, "dy": 0, "dz": 0})
        self.assertEqual(graph[0]["params"]["translations"][-1],
                         {"dx": 200, "dy": 24, "dz": 0})

    def test_preview_with_unavailable_command_never_authorizes_writes(self):
        from archicad_dynamic_commands import DynamicCommands
        import archicad_project_accelerator as APA
        root = Path(__file__).resolve().parents[1]
        router = DynamicCommands(APA.catalog_with_provenance(
            root / "schemas/tapir-live-1.5.10/tapir-scene-live.json"))
        APA.connect_functional_modules(router)
        existing, assembly = input_source()
        result = GRID.prepare_group_grid_preview(
            router, existing, assembly, grid(2, 2),
            "No runtime confirmation")
        self.assertEqual(result["modelWrites"], 0)
        self.assertFalse(result["preview"]["nativeWritePermission"])
        self.assertIsNone(result["preview"]["selectedNativeTaskPreview"])
        self.assertEqual(result["preview"]["status"],
                         "GROUP_WORKFLOW_REQUIRES_FRESH_RUNTIME_REGISTRATION")

    def test_nonfinite_zero_duplicate_and_33th_placement_rejected(self):
        faulty = [
            grid(columns=33, rows=1), grid(columns=9, rows=4),
            grid(columns=0), grid(rows=0), grid(columns=True),
            grid(columns=2, rows=1, stepX=0),
            grid(columns=1, rows=2, stepY=0),
            grid(columns=1, rows=1, startDx=0, startDy=0),
            grid(columns=2, rows=2, startDx=0, startDy=0),
            grid(columns=1, rows=1, startDx=10001),
            grid(columns=8, rows=4, startDx=9999),
            grid(columns=2, rows=1, stepX=float("inf")),
            grid(columns=2, rows=1, stepX=float("nan"))
        ]
        for item in faulty:
            with self.subTest(grid=item), self.assertRaises(ValueError):
                GRID.grid_offsets(item)

    def test_source_provenance_and_stories_required(self):
        for change in [
            {"groupReadbackVerified": False},
            {"dependenciesVerified": False},
            {"sameStory": False},
            {"existingGroupGuid": None},
            {"memberGuids": [G1, G1]},
        ]:
            existing, assembly = input_source()
            assembly.update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                GRID.build_group_grid_intent(existing, assembly, grid(2,1),
                                             "reject unverified source")
        existing, assembly = input_source()
        existing[1]["storyIndex"] = 2
        with self.assertRaises(ValueError):
            GRID.build_group_grid_intent(existing, assembly, grid(2, 1),
                                         "reject mixed stories")
        existing, assembly = input_source()
        existing[1]["type"] = "Object"
        with self.assertRaises(ValueError):
            GRID.build_group_grid_intent(existing, assembly, grid(2, 1),
                                         "reject non-columns")


class AC29GridVerifier(unittest.TestCase):
    def test_source_preflight_32_positions_still_checks_full_brep_layout(self):
        shifts = GRID.grid_offsets(grid())
        data = synthetic(shifts)
        nodes = [{"guid": guid, "type": "Column"} for guid in data["before"]]
        source_facts = {g: {
            "anchor": data["proof"]["sourceFacts"][g]["anchor"],
            "typed": data["proof"]["sourceFacts"][g]["typed"],
            "solid": data["proof"]["sourceFacts"][g]["solid"],
            "source": ({"guid":g}, [(gid(5000+i), {})])
        } for i, g in enumerate(data["members"])}
        clearance = {"status": "MULTI_COPY_ALL_NATIVE_BREP_AABB_CLEAR_PASS",
                     "evaluatedSolidBoxes": len(shifts) * 4}
        with patch.object(VERIFY, "group_member_ids",
                          return_value=set(data["members"])), \
             patch.object(VERIFY, "column_facts",
                          return_value=source_facts), \
             patch.object(VERIFY.M, "verify_batch_layout",
                          return_value=clearance) as check:
            proof = VERIFY.verify_before(
                api=object(), command=VERIFY.CMD,
                parameters=data["params"], affected=[],
                native_before={"elements": nodes})
        self.assertEqual(proof["status"],
                         "GROUP_CLONE_SOURCE_OWNED_NATIVE_BREP_AND_LAYOUT_PASS")
        self.assertEqual(len(proof["offsets"]), 32)
        self.assertEqual(proof["collisionProof"], clearance)
        self.assertEqual(check.call_count, 1)
        self.assertEqual(sum(len(g) for g in check.call_args.args[3].values()), 64)

    def test_postflight_1_2_32_groups_exact_all_native_guids(self):
        for n in (1, 2, 32):
            with self.subTest(groups=n):
                shifts = GRID.grid_offsets(grid(n,1,stepY=0))
                data = synthetic(shifts)
                report = audited_postflight(data)
                self.assertEqual(report["groupCopyCount"], n)
                self.assertEqual(len(report["newRootGuids"]), 2*n)
                self.assertEqual(len(report["newSegmentGuids"]), 2*n)
                self.assertEqual(report["finalNativeGuidCount"], 44 + 4*n)
                self.assertTrue(report["allNativeRootsAndChildrenVerified"])

    def test_mutation_malformed_native_reply_fails_closed(self):
        shifts = GRID.grid_offsets(grid(4,1,stepY=0))
        for corruption in ("wrongNativeWrites", "missingGroup", "missingChild",
                           "duplicateGroup", "tamperedShift"):
            data = synthetic(shifts)
            if corruption == "wrongNativeWrites":
                data["native"]["nativeModelWrites"] -= 1
            if corruption == "missingGroup":
                data["native"]["newGroupIds"].pop()
            if corruption == "missingChild":
                lost = data["model"]["elements"].pop()
                data["after"].remove(lost["guid"])
            if corruption == "duplicateGroup":
                data["native"]["newGroupIds"][1] = data["native"]["newGroupIds"][0]
            if corruption == "tamperedShift":
                data["params"]["translations"] = copy.deepcopy(shifts)
                data["params"]["translations"][0]["dx"] += 1
            with self.subTest(error=corruption), self.assertRaises(ValueError):
                audited_postflight(data)

    def test_two_copy_live_accepted_subset_still_verifier_compatible(self):
        report = audited_postflight(synthetic(
            [{"dx":25, "dy":0, "dz":0}, {"dx":50, "dy":0, "dz":0}]))
        self.assertEqual(report["groupCopyCount"], 2)
        self.assertEqual(report["newGroupGuids"],
                         [gid(2000), gid(2001)])
        self.assertEqual(report["finalNativeGuidCount"], 52)


if __name__ == "__main__":
    unittest.main()
