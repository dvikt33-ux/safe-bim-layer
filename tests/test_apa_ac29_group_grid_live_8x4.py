"""Dedicated AC29 8x4 one-shot lifecycle checks; NO Archicad during CI."""
import hashlib
import inspect
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import apa_ac29_group_grid_live_8x4 as LIVE
import apa_ac29_group_scenewriter_live as ORIGINAL
from test_apa_ac29_native_group_grid import input_source


class NativeGridOneShot(unittest.TestCase):
    def test_unique_stage_copies_bytes_only_and_rejects_any_retry(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            source = root / "immutable_source.pln"
            target = root / "new-grid-only.pln"
            state = root / "state"
            source.write_bytes(b"accepted source native 44 GUIDs")
            sha = hashlib.sha256(source.read_bytes()).hexdigest()
            audit = {
                "functionalSha256": "a" * 64,
                "sourceSavedSha256": sha,
                "sourceGroupId": LIVE.OLD_VERIFIED_GROUP,
                "priorSQLiteAuditSha256": "b" * 64
            }
            def sha_file(path):
                return hashlib.sha256(Path(path).read_bytes()).hexdigest()
            with (patch.object(LIVE, "SOURCE", source),
                  patch.object(LIVE, "SCRATCH", target),
                  patch.object(LIVE, "STATE", state),
                  patch.object(LIVE, "previous_proof", return_value=audit),
                  patch.object(LIVE.ORIGINAL, "require_local_branch",
                               return_value="a" * 40),
                  patch.object(LIVE.LIVE, "digest", side_effect=sha_file),
                  patch.object(LIVE.LIVE, "request",
                               side_effect=AssertionError("STAGE_CALLED_ARCHICAD"))):
                LIVE.stage()
                self.assertEqual(source.read_bytes(), target.read_bytes())
                self.assertEqual(LIVE.read(state / "stage.json")["status"],
                                 "STAGED_SAVED_COPY_ONLY_NO_ARCHICAD_CALLS")
                self.assertEqual(LIVE.read(state / "stage.json")["nativeModelWrites"], 0)
                self.assertEqual(LIVE.read(state / "stage.json")["archicadCalls"], 0)
                with self.assertRaisesRegex(RuntimeError,
                                            "GRID_STAGE_ALREADY_EXISTS_NO_OVERWRITE"):
                    LIVE.stage()

    def test_port_discovery_never_calls_archicad_on_protected_ports(self):
        old_port = LIVE.LIVE.PORT
        calls = []
        def response(command, data, *, addon, timeout):
            calls.append(LIVE.LIVE.PORT)
            self.assertEqual(command, "GetProjectInfo")
            self.assertTrue(addon)
            self.assertLessEqual(timeout, 2)
            if LIVE.LIVE.PORT == 19727:
                return {
                    "isUntitled": False, "isTeamwork": False,
                    "projectPath": str(LIVE.SCRATCH)
                }
            raise OSError("other program/port unavailable")
        try:
            with patch.object(LIVE.LIVE, "request", side_effect=response):
                chosen, info = LIVE.discover_dedicated_instance()
            self.assertEqual(chosen, 19727)
            self.assertEqual(info["projectPath"], str(LIVE.SCRATCH))
            self.assertEqual(sorted(set(calls)), list(LIVE.PORT_RANGE))
            self.assertTrue(all(i >= 19727 for i in calls))
        finally:
            LIVE.LIVE.PORT = old_port

    def test_missing_new_instance_does_not_rebind_existing_users(self):
        before = LIVE.LIVE.PORT
        with patch.object(LIVE.LIVE, "request", side_effect=OSError("no new AC29")):
            with self.assertRaisesRegex(RuntimeError,
                                        "EXACTLY_ONE_DEDICATED_INSTANCE"):
                LIVE.discover_dedicated_instance()
        self.assertEqual(before, LIVE.LIVE.PORT)

    def test_grid_intent_uses_native_provenance_not_unverified_members(self):
        original, group = input_source()
        group["sourceRef"] = LIVE.SOURCE_REF
        group["existingGroupGuid"] = LIVE.OLD_VERIFIED_GROUP
        baseline = {"existing": original, "assemblyGroups": [group],
                    "targets": [], "schemaVersion": "apa-native-group-auto/1"}
        candidate = LIVE.intent_factory(baseline)
        self.assertEqual(len(candidate["targets"]), 64)
        self.assertEqual(candidate["assemblyGroups"][0]["placements"], LIVE.SHIFTS)
        self.assertEqual(candidate["assemblyGroups"][0]["existingGroupGuid"],
                         LIVE.OLD_VERIFIED_GROUP)
        bad = json.loads(json.dumps(baseline))
        bad["assemblyGroups"][0]["existingGroupGuid"] = "abcdef"
        with self.assertRaisesRegex(RuntimeError,
                                    "GRID_ORIGINAL_NATIVE_SOURCE_GROUP_CHANGED"):
            LIVE.intent_factory(bad)

    def test_readonly_preflight_and_mutation_have_isolated_order(self):
        source = inspect.getsource(LIVE.read_only_check)
        self.assertIn("VERIFIER.verify_before(", source)
        self.assertIn("GRID_32_NATIVE_BREP_COLLISION_PREFLIGHT_NOT_CLEARED", source)
        self.assertIn("APA.prepare_current_runtime_group_native_task(", source)
        self.assertNotIn('LIVE.request("OpenProject"', source)
        self.assertNotIn('LIVE.request("SaveProject"', source)
        execution = inspect.getsource(LIVE.execute)
        self.assertLess(execution.index("read_only_check()"),
                        execution.index('MAILBOX.save(STATE / "attempted.json"'))
        self.assertLess(execution.index('MAILBOX.save(STATE / "attempted.json"'),
                        execution.index("ORIGINAL.execute_once("))
        self.assertIn("timeout=120", execution)
        self.assertIn("native_transport=bounded_native_transport", execution)
        self.assertIn("nativeRoundTripElapsedSeconds", execution)
        self.assertNotIn("OpenProject(", execution)
        self.assertNotIn("SaveProject(", execution)
        self.assertIn("GRID_PREVIOUS_MUTATION_ATTEMPT_NEVER_REPLAY", execution)

    def test_checks_all_44_previous_accepted_native_brep_not_only_group(self):
        code = inspect.getsource(LIVE.read_only_check)
        self.assertIn("HISTORICAL.records(", code)
        self.assertIn('row["command"] == "GetModelDumpV1"', code)
        self.assertIn("HISTORICAL.native_signatures(", code)
        self.assertIn("historical_signature == current_signature", code)
        self.assertLess(code.index("historical_signature == current_signature"),
                        code.index("VERIFIER.verify_before("))
        self.assertLess(code.index("VERIFIER.verify_before("),
                        code.index('return {'))
        self.assertNotIn("SaveProject(", code)
        self.assertNotIn("OpenProject(", code)

    def test_old_accepted_entry_defaults_to_original_transport_and_two_groups(self):
        source = inspect.getsource(ORIGINAL.execute_once)
        self.assertIn("native_transport or APA.native_transport", source)
        self.assertIn('len(entry["newGroupIds"]) == len(OFFSET)', source)
        self.assertIn('len(ids_after) == 44 + 4 * len(OFFSET)', source)
        self.assertEqual(LIVE.GRID_RECIPE["columns"] * LIVE.GRID_RECIPE["rows"], 32)
        self.assertEqual(len(LIVE.SHIFTS), 32)


if __name__ == "__main__":
    unittest.main()
