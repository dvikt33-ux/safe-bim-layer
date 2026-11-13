"""Regression fixtures for R03 readback and retryable architecture preflight."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import apa_ac29_group_batch_oneshot as group
import apa_r03_architecture as arch
from test_archicad_building_shell_integration import NamedStoriesNative


class ReopenReadbackTests(unittest.TestCase):
    def test_guid_or_brep_mismatch_cannot_emit_reopened_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory).resolve()
            scratch = state / "test.pln"
            scratch.write_bytes(b"saved fixture")
            saved_sha = group.sha256(scratch)
            planned = dict(baselineGuids=["old"], sourceProof={"sourceMaterials": {}},
                           runtimeIdentity={"build": "fixture"})
            group.write_new_json(state / "plan.json", planned)
            group.write_new_json(state / "baseline-native.json", {})
            group.write_new_json(state / "closed.json", dict(
                status="NATIVE_NO_OPEN_PROJECT_CONFIRMED", savedSHA256=saved_sha,
            ))
            ids = ["new", "old", "segment"]
            saved = dict(savedSHA256=saved_sha, finalGuidCount=3,
                         finalGuidSetSHA256=group.R.digest(ids), finalBrepSHA256="exact-brep",
                         nativeResponse={}, nativeReadback={"newRootGuids": ["new"],
                                                            "newSegmentGuids": ["segment"]})
            manifest = {"scratch": str(scratch), "port": 19723}

            class ReadOnly:
                write_attempts = 0

            with (patch.object(group, "saved_state", return_value=(manifest, saved)),
                  patch.object(group, "prepare_api", return_value=(ReadOnly(), None)),
                  patch.object(group, "router_for", return_value=(None, planned["runtimeIdentity"])),
                  patch.object(group, "verify_group_model") as result,
                  patch.object(group, "fingerprint") as fingerprint):
                for actual_ids, actual_brep in ((["other", "old", "segment"], "exact-brep"),
                                                (ids, "different-brep")):
                    with self.subTest(ids=actual_ids, brep=actual_brep):
                        result.return_value = (actual_ids, {}, {})
                        fingerprint.return_value = actual_brep
                        with self.assertRaisesRegex(ValueError, "FULL_NATIVE_BREP_OR_GUID_DRIFT"):
                            group.verify_reopen(state)
                        self.assertFalse((state / "reopened.json").exists())

                result.return_value = (ids, {}, {})
                fingerprint.return_value = "exact-brep"
                verified = group.verify_reopen(state)
                self.assertEqual(verified["reopenedGuids"], ids)
                self.assertEqual(verified["reopenedGuidSetSHA256"], saved["finalGuidSetSHA256"])
                self.assertEqual(verified["reopenedBrepSHA256"], saved["finalBrepSHA256"])
                self.assertEqual(verified["verificationNativeWrites"], 0)


class ArchitectureRetryTests(unittest.TestCase):
    def test_failed_readonly_attempt_preserved_and_fresh_port_can_be_used(self):
        with tempfile.TemporaryDirectory() as directory:
            job = Path(directory).resolve() / "R03-ARCH-TEST"
            job.mkdir()
            intent = arch.read(arch.SCHEMA.parents[2] / "examples/accelerator/building-shell.intent.json")
            arch.write_new_json(job / "intent.json", intent)
            manifest = dict(project=str(job / "test.pln"), port=19723,
                            offlinePlanHash=arch.A.compile_intent(intent, arch.SCHEMA)["sourcePlanHash"])
            native = NamedStoriesNative()
            wrong_story = True

            def transport(command, parameters):
                payload = native(command, parameters)
                if command == "GetStories" and wrong_story:
                    payload["stories"][1]["level"] = 4.0
                return payload

            with (patch.object(arch, "bind", return_value={"buildIdentity": "fixture"}),
                  patch.object(arch, "probe_shell_runtime"),
                  patch.object(arch, "capture", return_value=([], {}, {})),
                  patch.object(arch, "prove_retained"),
                  patch.object(arch.R, "_SAVED_COPY_AUTHORIZATION", {"fixture": True}),
                  patch.object(arch.R, "authorized_authored_target", return_value=True),
                  patch.object(arch.A, "native_transport", transport)):
                failed = arch.preflight(job, manifest, 19723, ("fixture", "fixture"))
                self.assertEqual(failed["status"], "BLOCKED", failed)
                blocked_report = Path(failed["evidencePath"])
                before = blocked_report.read_bytes()
                self.assertEqual(arch.status(job, manifest)["status"], "STAGED")
                wrong_story = False
                passed = arch.preflight(job, manifest, 19726, ("fixture", "fixture"))
                self.assertEqual(passed["status"], "READY_FOR_EXPLICIT_TEST_RUN", passed)
            self.assertEqual(blocked_report.read_bytes(), before)
            self.assertNotEqual(passed["evidencePath"], failed["evidencePath"])
            self.assertFalse(native.writes)
            approval = arch.read(job / "approved-preflight.json")
            self.assertEqual(approval["port"], 19726)
            self.assertEqual(arch.status(job, manifest)["status"], passed["status"])
            Path(passed["evidencePath"]).write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "PREFLIGHT_RESULT_DRIFT"):
                arch.status(job, manifest)
