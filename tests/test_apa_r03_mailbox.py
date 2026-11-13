import base64
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import apa_ac29_autonomous_job_bridge as bridge
import apa_r03_mailbox as mailbox
import archicad_project_accelerator as core
from apa_ac29_save_isolation import write_new_json
from apa_release import sha256
from test_archicad_building_shell_integration import ExactScratchProjectNative


class MailboxContract(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.job = self.root / "r03-test-workflow-01"
        self.project = self.job / "model" / mailbox.architecture.MODEL
        self.project.parent.mkdir(parents=True)
        self.donor = self.root / "original.pln"
        self.donor.write_bytes(b"initial fixture")
        self.project.write_bytes(self.donor.read_bytes())
        self.source_path = mailbox.SOURCES["ARCHITECTURE"]
        self.source = (ROOT / self.source_path).read_bytes()
        (self.job / "intent.json").write_bytes(self.source)
        self.initial = sha256(self.project)
        write_new_json(self.job / "job.json", dict(schema="APA_R03_ARCHITECTURE_JOB_V1", status="STAGED",
            jobId=self.job.name, project=str(self.project), initialSHA256=self.initial, original=str(self.donor),
            baselineGuidSetSHA256="a" * 64, baselineBrepSHA256="b" * 64,
            authorizationRef="USER_APPROVED_APA_R03_" + self.job.name, intentSHA256=sha256(self.job / "intent.json")))
        native = self.root / "test.apx"
        native.write_bytes(b"compiled APX fixture")
        self.pin = ("1" * 40, "2" * 64)
        self.package = self.root / "release"
        self.members = {}
        self.member(self.source_path, self.source)
        self.member("native/binary-receipt.json", json.dumps(dict(binary=dict(
            sourceRevision=self.pin[0], buildIdentity=self.pin[1], apxSHA256=sha256(native)))).encode())
        write_new_json(self.package / mailbox.MANIFEST, dict(
            schema="APA_WINDOWS_RELEASE_V1", revision="3" * 40, files=self.members))
        apx = patch.object(mailbox, "APX", native)
        apx.start()
        self.addCleanup(apx.stop)
        mailbox.prepare_profile(self.package, self.job, "ARCHITECTURE")
        self.profile = self.job / "mailbox-profile.json"
        self.c = mailbox.Campaign(self.package, self.profile)
        self.remote = {}
        self.puts = []
        self.endpoint = f"repos/{bridge.BRIDGE}/contents/"
        self.patcher = patch.multiple(bridge, gh_api=self.gh_api,
                                      current_utc=lambda: datetime(2026, 11, 13, tzinfo=timezone.utc))
        self.patcher.start()
        self.addCleanup(self.patcher.stop)
        self.remote[f"repos/{mailbox.SOURCE_REPO}/contents/{self.source_path}?ref=" + "3" * 40] = self.source
        self.session = dict(port=19725, pid=10001, startedAt="test-start")

    def member(self, name, data):
        path = self.package / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        self.members[name] = dict(bytes=len(data), sha256=sha256(path))

    def gh_api(self, endpoint, *, body=None, allow_missing=False):
        if body is not None:
            upload = json.loads(body.read_text(encoding="utf-8"))
            self.assertNotIn("sha", upload)
            self.assertNotIn(endpoint + "?ref=main", self.remote)
            self.puts.append(endpoint)
            self.remote[endpoint + "?ref=main"] = base64.b64decode(upload["content"])
            return {}
        raw = self.remote.get(endpoint)
        if raw is None:
            if allow_missing:
                return None
            raise ValueError("missing GitHub fixture")
        return dict(type="file", sha=bridge.git_sha(raw), encoding="base64",
                    content=base64.b64encode(raw).decode(), html_url="https://example.invalid/result")

    def submit(self, suffix, **extra):
        name = f"{self.job.name}-{suffix}"
        request = self.c.envelope(bridge, name)
        self.remote[self.endpoint + f"{bridge.INBOX}/{name}.json?ref=main"] = json.dumps(request | extra).encode()
        return name

    def stage_plan(self):
        name = self.submit("plan")
        path = self.c.preflight_path()

        def preflight(*_):
            write_new_json(path, dict(confirmHash="exact-local-native-plan"))
            return dict(status="READY_FOR_EXPLICIT_TEST_RUN", metrics={"elementCount": 10})

        with (patch.object(mailbox, "listener", return_value=self.session),
              patch.object(mailbox.architecture, "preflight", side_effect=preflight)):
            result = self.c.process(bridge, name, port=self.session["port"])
        self.assertEqual(result["result"]["preflightSha256"], sha256(path))
        return sha256(path)

    def test_complete_transport_contract_uses_one_native_dispatch_and_reads_github_bytes(self):
        plan_sha = self.stage_plan()
        execute = self.submit("execute")
        guids = ["fixture-a", "fixture-b"]
        guid_sha = mailbox.group.R.digest(guids)
        brep_sha = "a" * 64
        saved = {}

        def run(*_):
            self.assertTrue((self.c.history / execute / "attempted.json").exists())
            self.project.write_bytes(b"changed fixture")
            saved.update(status="LIVE_ARCHITECTURE_SAVED_PENDING_REAL_REOPEN", addedGuids=[guids[-1]],
                         savedSHA256=sha256(self.project), finalGuidSetSHA256=guid_sha, finalBrepSHA256=brep_sha,
                         elementCount=2, addedByKind={"Wall": 1}, bodyCountByAddedGuid={guids[-1]: 1},
                         nativeModelWriteAttempts=1, nativeSaveCalls=1)
            write_new_json(self.job / "saved.json", saved)
            return saved

        with (patch.object(mailbox, "listener", return_value=self.session),
              patch.object(mailbox.architecture, "execute", side_effect=run) as execute_native,
              patch.object(mailbox.architecture, "saved_record", side_effect=lambda *_: saved)):
            with self.assertRaisesRegex(ValueError, "LOCAL_GRANT_MISSING"):
                self.c.process(bridge, execute)
            self.assertFalse((self.c.history / execute).exists())
            with self.assertRaisesRegex(ValueError, "EXPLICIT_PREFLIGHT_SHA"):
                self.c.grant(bridge, execute, create=True, confirm="wrong")
            self.c.grant(bridge, execute, create=True, confirm=plan_sha)
            initial = self.c.process(bridge, execute)
            self.assertFalse(initial["result"]["saveReopenVerified"])
            self.assertTrue(initial["modelWritesAuthorized"])
            self.assertEqual(initial, self.c.process(bridge, execute))
            execute_native.assert_called_once()

            def close(*_, **kwargs):
                row = dict(status="NATIVE_NO_OPEN_PROJECT_CONFIRMED", port=19725, pid=kwargs["process_id"])
                write_new_json(self.job / "closed.json", row)
                return row

            def reopen(*_):
                row = dict(reopenVerified=True, reopenedGuidSetSHA256=guid_sha, reopenedBrepSHA256=brep_sha,
                           verificationNativeWrites=0, savedSHA256=saved["savedSHA256"], reopenedGuids=guids)
                write_new_json(self.job / "reopened.json", row)
                return row

            with (patch.object(mailbox, "reservation_owner_exited", return_value=False),
                  patch.object(mailbox.architecture, "check_closed", side_effect=close),
                  patch.object(mailbox.architecture, "verify_reopen", side_effect=reopen)):
                result = self.c.process(bridge, self.submit("closed"))
                self.assertEqual(result["result"]["jobStatus"], "READY_FOR_REOPEN")
                result = self.c.process(bridge, self.submit("reopen"))
            self.assertEqual(result["result"]["verification"], "SAVE_REOPEN_VERIFIED")
            self.assertEqual(result["result"]["guids"], guids)
            self.assertFalse(result["modelWritesAuthorized"])
            self.assertEqual(len(self.puts), 4)
            self.assertEqual(sha256(self.donor), self.initial)

    def test_grant_is_tied_to_original_remote_blob_even_for_same_json(self):
        sha = self.stage_plan()
        name = self.submit("execute")
        self.c.grant(bridge, name, create=True, confirm=sha)
        key = self.endpoint + f"{bridge.INBOX}/{name}.json?ref=main"
        self.remote[key] += b"\n"
        with patch.object(self.c, "run_execute") as run:
            with self.assertRaisesRegex(ValueError, "GRANT_MISSING_OR_DRIFTED"):
                self.c.process(bridge, name)
        run.assert_not_called()

    def test_interrupted_execute_is_reconciled_as_unknown_without_retry(self):
        folder = self.c.history / f"{self.job.name}-execute"
        folder.mkdir(parents=True)
        write_new_json(folder / "attempted.json", dict(job=folder.name, action="EXECUTE", sourceBlob="a" * 40,
                                                        bindingSha256=sha256(self.profile)))
        with patch.object(self.c, "run_execute") as run:
            result = self.c.process(bridge, folder.name)
            self.assertEqual(result, self.c.process(bridge, folder.name))
        self.assertEqual(result["result"]["nativeOutcome"], "UNKNOWN")
        self.assertEqual(result["result"]["jobStatus"], "STOPPED_RECONCILE_NO_AUTORETRY")
        self.assertEqual(len(self.puts), 1)
        run.assert_not_called()

    def test_remote_cannot_override_the_local_path_or_port(self):
        name = self.submit("plan", port=19729, path=str(self.donor))
        with patch.object(self.c, "run_plan") as run:
            with self.assertRaisesRegex(ValueError, "ENVELOPE_SCOPE_DRIFT"):
                self.c.process(bridge, name, port=19725)
        run.assert_not_called()

    def test_conflicting_result_cannot_start_native_and_remotely_changed_report_fails_readback(self):
        name = self.submit("plan")
        key = self.endpoint + f"{bridge.RESULTS}/{name}.json?ref=main"
        self.remote[key] = b'{"drift":true}'
        with patch.object(self.c, "run_plan") as run:
            with self.assertRaisesRegex(ValueError, "REMOTE_RESULT_ALREADY_EXISTS"):
                self.c.process(bridge, name, port=19725)
        run.assert_not_called()
        del self.remote[key]
        self.stage_plan()
        previous = self.remote.pop(key)
        with self.assertRaisesRegex(ValueError, "PUBLISHED_REMOTE_RESULT_DISAPPEARED"):
            self.c.process(bridge, name)
        self.remote[key] = previous
        self.remote[key] += b"\n"
        with self.assertRaisesRegex(ValueError, "REMOTE_RESULT_CONFLICT"):
            self.c.process(bridge, name)
        self.assertEqual(len(self.puts), 1)

    def test_group_route_uses_existing_plan_and_port_bound_executor(self):
        state = self.job / "state"
        state.mkdir()
        self.c.kind = "GROUP"
        self.c.state = state
        self.c.manifest = dict(self.c.manifest, groupCount=32)
        runtime = {"sourceRevision": self.pin[0], "buildIdentity": self.pin[1]}
        planned = dict(runtimeIdentity=runtime, nativeWrites=0, baselineGuids=["fixture"],
                       contractSHA256="a" * 64)

        def group_plan(path, *, port):
            self.assertEqual(path, state)
            self.assertEqual(port, 19725)
            write_new_json(path / "plan.json", planned)
            return planned

        saved = dict(status="GROUP_BATCH_SAVED_PENDING_REAL_REOPEN", finalGuidCount=172,
                     groupCount=32, nativeCloneCalls=1, saveCalls=1, savedSHA256="b" * 64,
                     finalGuidSetSHA256="c" * 64, finalBrepSHA256="d" * 64,
                     nativeReadback=dict(newRootGuids=["1"], newSegmentGuids=["2"]))
        write_new_json(state / "saved.json", saved)
        with (patch.object(self.c, "group_identity", return_value=runtime),
              patch.object(mailbox, "listener", return_value=self.session),
              patch.object(mailbox.group, "plan", side_effect=group_plan),
              patch.object(mailbox.group, "execute", return_value=saved) as execute,
              patch.object(self.c, "saved", return_value=saved)):
            plan = self.c.run_plan(f"{self.job.name}-plan", self.session["port"])
            receipt = self.c.run_execute(self.session)
        self.assertEqual(plan["groupCount"], 32)
        self.assertEqual(receipt["guidCount"], 172)
        self.assertEqual(receipt["addedGuids"], ["1", "2"])
        self.assertFalse(receipt["saveReopenVerified"])
        execute.assert_called_once_with(state, port=19725)

    def test_r03_single_story_scene_survives_native_3d_view(self):
        intent = json.loads(self.source)
        # Existing typed slab tests exercise the Basic material mutation.
        # Here the fixture isolates the named story and 3D view binding.
        del intent["components"][0]["specification"]["slabBasicMaterialName"]
        fixture = ExactScratchProjectNative()

        def api(command, params):
            row = fixture(command, params)
            if command == "GetStories":
                row["actStory"] = -1
            return row

        ledger = self.root / "ledger"
        ledger.mkdir()
        with (patch.object(core.RUN, "_SAVED_COPY_AUTHORIZATION", {"fixture": True}),
              patch.object(core.RUN, "authorized_authored_target", return_value=True)):
            plan = core.run_project(intent, core.RUN.DEFAULT_SCENE_SCHEMA, self.root / "plan", ledger,
                                    "preflight", api, allow_3d_view_for_write=True)
            self.assertEqual(plan["status"], "READY_FOR_EXPLICIT_TEST_RUN", plan)
            self.assertEqual(plan["modelWriteAttempts"], 0)
            result = core.run_project(intent, core.RUN.DEFAULT_SCENE_SCHEMA, self.root / "run", ledger,
                                      "execute", api, "synthetic-r03-one", plan["confirmPlanHash"],
                                      allow_3d_view_for_write=True)
            self.assertEqual(result["status"], "COMPLETE_UNSAVED", result)
            self.assertEqual(len(result["addedGuids"]), 10)
            self.assertTrue(result["wholeAssemblyReadback"])


if __name__ == "__main__":
    unittest.main()
