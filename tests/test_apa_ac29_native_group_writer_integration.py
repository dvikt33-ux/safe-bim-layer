"""Focused offline test of the NEW group-specific scope verifier, no Archicad.

The real native grouping and copy were already tested; these tests check
only newly added safety boundaries and wiring into the original APA engine.
"""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from apa_ac29_dynamic_native_verifiers import installed_verifiers
from apa_ac29_native_group_clone_verifier import verify_before, CMD
from apa_ac29_group_scenewriter_live import (
    AUTH_REF, BRANCH, SCENE, SCRATCH, SOURCE, STATE, OFFSET
)


class NoApiWrites:
    def __init__(self):
        self.calls = []

    def __call__(self, name, params):
        self.calls.append(name)
        raise AssertionError("API call without complete typed preflight")


class GroupWriterScope(unittest.TestCase):
    def test_installed_verifier_registered_and_reviewed_effect(self):
        registry = installed_verifiers()
        self.assertIn("VerifiedNativeGroupClone", registry)
        verifier = registry["VerifiedNativeGroupClone"]
        self.assertEqual(verifier.command, CMD)
        self.assertEqual(verifier.effect, "CREATE")
        self.assertIs(verifier.before, verify_before)
        self.assertTrue(callable(verifier.after))

    def test_rejects_wrong_command_and_affected_existing_guid(self):
        for name, affected in [
            ("MoveNativeGroupV1", []),
            (CMD, ["00000000-0000-4000-8000-000000000000"])
        ]:
            api = NoApiWrites()
            with self.subTest(name=name, affected=affected):
                with self.assertRaises(ValueError):
                    verify_before(
                        api=api, command=name,
                        parameters={
                            "groupId": {"guid": "0a17fb15-3639-4dfa-ab01-cd910ae112b0"},
                            "sourceRef": "SOURCE_VERIFIED_TEST",
                            "translations": list(OFFSET)
                        },
                        affected=affected, native_before={"elements": []}
                    )
                self.assertEqual(api.calls, [])

    def test_rejects_unapproved_shift_without_api_call(self):
        gid = "0a17fb15-3639-4dfa-ab01-cd910ae112b0"
        bad = [
            [{"dx": 25, "dy": 0, "dz": 0}],
            [{"dx": 25, "dy": 0, "dz": 0}] * 2,
            [{"dx": 25, "dy": 0, "dz": 1}, {"dx": 50, "dy": 0, "dz": 0}],
            [{"dx": 25, "dy": 5, "dz": 0}, {"dx": 50, "dy": 0, "dz": 0}],
            [{"dx": -25, "dy": 0, "dz": 0}, {"dx": 50, "dy": 0, "dz": 0}],
        ]
        for shifts in bad:
            api = NoApiWrites()
            with self.subTest(shifts=shifts), self.assertRaises(ValueError):
                verify_before(
                    api=api, command=CMD,
                    parameters={"groupId": {"guid": gid},
                                "sourceRef": "SOURCE_VERIFIED_TEST",
                                "translations": shifts},
                    affected=[], native_before={"elements": []}
                )
            self.assertEqual(api.calls, [])

    def test_exact_project_scope_is_different_from_bdd_and_saved_source(self):
        self.assertNotEqual(str(SCRATCH).lower(), str(SOURCE).lower())
        self.assertTrue(str(SCRATCH).lower().startswith(
            r"c:\localai\apa_group_acceptance"))
        self.assertIn("scene-writer", str(SCRATCH).lower())
        self.assertEqual(SCENE, "GroupCloneWriter29_20261018_01")
        self.assertEqual(BRANCH, "feature/apa-ac29-group-scenewriter-live-20261018")
        self.assertTrue(AUTH_REF.startswith("USER_APPROVED_"))
        self.assertNotEqual(STATE / "original-scenewriter.sqlite", SOURCE)

    def test_exactly_one_unreplayed_writer_dispatch_in_code(self):
        source = (Path(__file__).resolve().parents[1] / "scripts" /
                  "apa_ac29_group_scenewriter_live.py").read_text(encoding="utf8")
        self.assertIn("APA.run_auto_optimized_native_task(", source)
        self.assertIn("build_existing_workflow_scopes(", source)
        self.assertIn("RUN.SceneWriter(", source)
        self.assertIn('allow_3d_view_for_write=True', source)
        self.assertIn('need(not STATE.exists() and not SCRATCH.exists()', source)
        self.assertIn('"before-native-dispatch.json"', source)
        self.assertNotIn('LIVE.request("CloneNativeGroupV1"', source)
        self.assertNotIn('LIVE.request("SaveProject"', source)


    def test_real_apa_bim_graph_routes_one_group_step_to_original_writer(self):
        from unittest.mock import patch
        from archicad_dynamic_commands import DynamicCommands
        from archicad_batch_contracts import load_catalog
        import archicad_project_accelerator as APA
        from test_apa_ac29_group_strategy_integration import inputs, assembly
        root = Path(__file__).resolve().parents[1]
        router = DynamicCommands(load_catalog(root / "tapir-1.5.8.json"))
        APA.connect_functional_modules(router)
        router.register_availability(CMD, True)
        existing, targets = inputs()
        intent = dict(schemaVersion="apa-native-group-auto/1",
                      request="One group clone through original BIM graph",
                      existing=existing, targets=targets,
                      assemblyGroups=[assembly()])
        preview = APA.prepare_auto_optimized_native_task(router, intent)
        self.assertEqual(preview["status"], "ONE_SOURCE_QUALIFIED_STRATEGY_PREPARED")
        calls = []
        def original_scene_writer_dispatch(writer, scene_id, ticket,
                                           affected, retained_signatures,
                                           saved_sha256, authorization, impact,
                                           verify_after, verify_before=None):
            calls.append({"scene": scene_id, "command": ticket["command"],
                          "effect": ticket["effect"],
                          "approved": authorization, "impact": impact})
            self.assertIsNotNone(writer)
            self.assertEqual(ticket["parameters"]["translations"], [dict(dx=10,dy=0,dz=0), dict(dx=20,dy=0,dz=0)])
            return {"status": "PASS", "nativeResponse": {
                "nativeModelWrites": 4,
                "sourceGroupId": ticket["parameters"]["groupId"],
                "newGroupIds": [{"guid": "00000000-0000-4000-8000-000000000101"},
                                {"guid": "00000000-0000-4000-8000-000000000102"}],
                "createdElements": [
                    {"elementId": {"guid": f"00000000-0000-4000-8000-{i:012d}"}}
                    for i in range(1, 5)]
            }}
        def scope(step, ticket, previous):
            self.assertEqual(previous, {})
            return dict(scene_id=SCENE, affected=[], retained_signatures={},
                        saved_sha256="0" * 64, authorization=AUTH_REF,
                        impact="MODEL", verify_after=lambda *args: None,
                        verify_before=lambda *args: None)
        with patch.object(router, "execute", side_effect=original_scene_writer_dispatch):
            result = APA.run_auto_optimized_native_task(router, object(), preview,
                                                       object(), scope)
        self.assertEqual(result["status"], "WORKFLOW_CALLABLE_VERIFIED")
        self.assertEqual(len(result["trace"]), 1)
        self.assertEqual(calls, [{"scene": SCENE, "command": CMD,
                                  "effect": "CREATE", "approved": AUTH_REF,
                                  "impact": "MODEL"}])
        self.assertEqual(result["trace"][0]["command"], CMD)

    def test_graph_unknown_outcome_never_dispatches_second_group_clone(self):
        from unittest.mock import patch
        from archicad_dynamic_commands import DynamicCommands
        from archicad_batch_contracts import load_catalog
        import archicad_project_accelerator as APA
        from test_apa_ac29_group_strategy_integration import inputs, assembly
        root = Path(__file__).resolve().parents[1]
        router = DynamicCommands(load_catalog(root / "tapir-1.5.8.json"))
        APA.connect_functional_modules(router)
        router.register_availability(CMD, True)
        existing, targets = inputs()
        intent = dict(schemaVersion="apa-native-group-auto/1",
                      request="Reject replay when group native outcome unknown",
                      existing=existing, targets=targets,
                      assemblyGroups=[assembly()])
        preview = APA.prepare_auto_optimized_native_task(router, intent)
        def scope(step, ticket, previous):
            return dict(scene_id=SCENE, affected=[], retained_signatures={},
                        saved_sha256="0" * 64, authorization=AUTH_REF,
                        impact="MODEL", verify_after=lambda *args: None,
                        verify_before=lambda *args: None)
        with patch.object(router, "execute",
                          return_value={"status": "PARTIAL_OR_UNKNOWN_OUTCOME",
                                        "manualReconciliationRequired": True}) as dispatched:
            report = APA.run_auto_optimized_native_task(router, object(), preview,
                                                       object(), scope)
        self.assertEqual(dispatched.call_count, 1)
        self.assertEqual(report["status"], "STOPPED_UNKNOWN_OUTCOME")
        self.assertEqual(report["stoppedAt"], "assembly_0_clone")
        self.assertFalse(report["automaticRetry"])
        self.assertEqual(report["completedSteps"], [])


    def test_live_1510_catalog_provenance_used_for_scenewriter(self):
        import archicad_project_accelerator as APA
        import archicad_batch_contracts as CONTRACTS
        from archicad_dynamic_commands import DynamicCommands
        root = Path(__file__).resolve().parents[1]
        export = root / "schemas" / "tapir-live-1.5.10" / "tapir-scene-live.json"
        catalog = APA.catalog_with_provenance(export)
        self.assertEqual(CONTRACTS.source_version(catalog), "1.5.10")
        self.assertEqual(APA.RUN.EXPECTED_TAPIR, "1.5.10")
        router = DynamicCommands(catalog)
        APA.connect_functional_modules(router)
        self.assertEqual(CONTRACTS.source_version(router.catalog), "1.5.10")
        self.assertIn(CMD, router.catalog["commands"])
        local = (root / "scripts" / "apa_ac29_group_scenewriter_live.py").read_text(encoding="utf8")
        self.assertIn("APA.catalog_with_provenance(", local)
        self.assertNotIn('CONTRACTS.load_catalog(ROOT / "tapir-1.5.8.json")', local)

    def test_failed_scenewriter_forensic_has_only_read_or_publish_actions(self):
        from apa_ac29_group_scenewriter_reconcile_readonly import run
        import inspect
        source = inspect.getsource(run)
        self.assertNotIn('LIVE.request("OpenProject"', source)
        self.assertNotIn('LIVE.request("SaveProject"', source)
        self.assertNotIn('LIVE.request("CloneNativeGroupV1"', source)
        self.assertIn('"OpenProject", "MoveElements"', source)
        self.assertNotIn("create_and_open_copy", source)
        self.assertIn("WRITER_PRE_DISPATCH_STOP_AND_LIVE_NATIVE_BASELINE_PASS", source)


    def test_forensic_tapir_inventory_and_version_route_are_addon_only(self):
        import inspect
        import apa_ac29_group_scenewriter_reconcile_readonly as forensic
        from apa_ac29_group_acceptance_mailbox import read_elements
        run_source = inspect.getsource(forensic.run)
        inventory_source = inspect.getsource(read_elements)
        self.assertIn("inventory = sorted(guid.lower() for guid in LIVE.read_elements())", run_source)
        self.assertIn('request("GetAllElements", {}, addon=True)', inventory_source)
        self.assertIn('LIVE.request("GetAddOnVersion", {}, addon=True)', run_source)
        self.assertNotIn('APA.inventory_guids(lambda name, params:', run_source)



if __name__ == "__main__":
    unittest.main()
