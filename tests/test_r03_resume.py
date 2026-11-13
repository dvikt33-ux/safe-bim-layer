"""Regression fixtures for R03 readback and retryable architecture preflight."""
from contextlib import closing
import hashlib
import sqlite3
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

                evidence = state / "separate-proof"
                model = evidence / "model"
                model.mkdir(parents=True)
                copy = model / scratch.name
                copy.write_bytes(scratch.read_bytes())
                group.write_new_json(evidence / "startup.json", dict(
                    status="PROJECT_IDENTITY_VERIFIED", project=str(copy), originalProject=str(scratch),
                    projectSha256=saved_sha, verifiedPort=19723, plnBytesUnchanged=True, nativeModelWrites=0))
                original_receipt = (state / "reopened.json").read_bytes()
                observed = group.verify_reopen(state, reopen_port=19723, reopened_copy=copy, evidence_dir=evidence)
                self.assertEqual(observed["status"], "LIVE_NATIVE_GROUP_BATCH_SAVED_COPY_READBACK_PASS")
                self.assertFalse(observed["reopenVerified"])
                self.assertEqual((state / "reopened.json").read_bytes(), original_receipt)
                resumed = evidence / ("startup-resume-" + "a"*32 + ".json")
                process = {"pid": 99, "startedAt": "fresh-pid", "port": 19723}
                receipt = group.read(evidence / "startup.json")
                (evidence / "startup.json").write_text(group.R.canonical(dict(receipt, status="WAITING_FOR_OPERATOR",
                    events=[dict(status="WAITING_FOR_OPERATOR", pid=99, process={"ProcessId": 99})])), encoding="utf-8")
                prior = group.sha256(evidence / "startup.json")
                group.write_new_json(resumed, dict(receipt, priorStartupSha256=prior, verifiedListener=process))
                with patch("apa_r03_mailbox.listener", side_effect=[process, dict(process, pid=100)]):
                    with self.assertRaisesRegex(ValueError, "REOPEN_LISTENER_DRIFT"):
                        group.verify_reopen(state, reopen_port=19723, reopened_copy=copy,
                                            evidence_dir=evidence, startup_receipt=resumed)
                copy.write_bytes(b"changed fixture")
                with self.assertRaisesRegex(ValueError, "REOPENED_STARTUP_PROOF_REQUIRED"):
                    group.verify_reopen(state, reopen_port=19723, reopened_copy=copy, evidence_dir=evidence,
                                        startup_receipt=resumed)


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


class ArchitectureSaveContractTests(unittest.TestCase):
    def test_create_receipt_passes_both_save_checks_and_never_replays(self):
        for drift in (False, True):
            with self.subTest(protected_source_drift=drift):
                self.verify_save(drift)

    def verify_save(self, drift):
        # Use the real router, guard, save snapshot and SQLite writer. Only
        # transport, model capture, and the previously tested build are fixtures.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            job = root / "r03-architecture-save"
            job.mkdir()
            source, scratch = root / "donor.pln", job / arch.MODEL
            source.write_bytes(b"unchanged test donor")
            scratch.write_bytes(source.read_bytes())
            initial = arch.sha256(scratch)
            m = dict(project=str(scratch), original=str(source), initialSHA256=initial, port=19725,
                     jobId=job.name, authorizationRef="USER_APPROVED_APA_R03_" + job.name)
            intent = {"fixture": True}
            arch.write_new_json(job / "intent.json", intent)
            runtime = {"build": "fixture"}
            attempt = job / "preflight"
            attempt.mkdir()
            result_file = attempt / "result.json"
            arch.write_new_json(result_file, dict(status="READY_FOR_EXPLICIT_TEST_RUN",
                                modelWriteAttempts=0, confirmPlanHash="sealed-plan"))
            arch.write_new_json(job / "approved-preflight.json", dict(
                jobId=job.name, confirmHash="sealed-plan", port=19725,
                preflightSHA256=arch.sha256(result_file), runtime=runtime))
            old = "11111111-1111-4111-8111-111111111111"
            new = "22222222-2222-4222-8222-222222222222"
            ids = [old, new]
            model = {"elements": [dict(guid=new, bodies=[{}])]}
            signatures = {old: "existing wall signature", new: "new wall signature"}
            dispatched = []

            def transport(command, _):
                if command == "API.IsAddOnCommandAvailable":
                    return {"available": True}
                if command == "GetAddOnVersion":
                    return {"version": "1.5.10"}
                if command == "GetAllElements":
                    return {"elements": [{"elementId": {"guid": guid}} for guid in ids]}
                if command == "SaveProject":
                    dispatched.append(command)
                    scratch.write_bytes(b"saved architectural model")
                    return {"success": True}
                self.fail(f"Unexpected transport call {command}")

            def capture(_, __):
                if drift:
                    source.write_bytes(b"test source changed")
                return ids, model, signatures

            result = dict(status="COMPLETE_UNSAVED", wholeAssemblyReadback=True,
                          addedGuids=[new], modelWriteAttempts=1,
                          scene={"steps": {"wall": {"kind": "Wall", "guid": new}}})
            binding = dict(path=str(scratch), name=scratch.stem, port=19725, tapirVersion="1.5.10", storyIndex=0)
            with (patch.object(arch, "bind", return_value=runtime),
                  patch.object(arch, "probe_shell_runtime"),
                  patch.object(arch, "baseline_capture", return_value=([old], {old: signatures[old]})),
                  patch.object(arch, "capture", side_effect=capture),
                  patch.object(arch.A, "run_project", return_value=result),
                  patch.object(arch.A, "native_transport", transport),
                  patch.object(arch.R, "bind_authorized_saved_copy"),
                  patch.object(arch.R, "guarded_scene_project", return_value=binding),
                  patch.object(arch.group, "fingerprint", return_value="native-brep"),
                  patch.object(arch.group.D, "capture_full_model", return_value=model),
                  patch.object(arch.C, "retained_geometry_signatures", return_value=signatures)):
                if drift:
                    with self.assertRaisesRegex(ValueError, "PRE_SAVE_DRIFT"):
                        arch.execute(job, m, ("fixture", "fixture"))
                    self.assertFalse(dispatched)
                    self.assertFalse((job / "saved.json").exists())
                    return
                saved = arch.execute(job, m, ("fixture", "fixture"))
                self.assertEqual(saved["savedSHA256"], hashlib.sha256(b"saved architectural model").hexdigest())
                self.assertEqual(arch.saved_record(job, m), saved)
                self.assertEqual(arch.execute(job, m, ("fixture", "fixture"))["status"], "ALREADY_APPLIED")
            self.assertEqual(dispatched, ["SaveProject"])
            self.assertEqual(arch.sha256(source), initial)
            with closing(sqlite3.connect(job / "ledger" / "scene-v1-attempts.sqlite3")) as db:
                self.assertEqual(db.execute("SELECT state FROM scenes").fetchall(), [("PASS",)])
                self.assertEqual(db.execute("SELECT state FROM steps").fetchall(), [("PASS",)])
