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


if __name__ == "__main__":
    unittest.main()
