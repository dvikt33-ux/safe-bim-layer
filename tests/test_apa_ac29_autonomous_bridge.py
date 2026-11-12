"""Only new GitHub bridge authorization, deduplication and ingress checks."""
from datetime import datetime, timedelta, timezone
import json
from tempfile import TemporaryDirectory
import sys
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import apa_ac29_autonomous_job_bridge as bridge


def sample(action="BDD114_ROOF_FINALIZE", name="bdd114-roof-20261017"):
    now = datetime.now(timezone.utc)
    stamp = lambda value: value.strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "schema": "APA_AC29_AUTONOMOUS_JOB_V1",
        "jobId": name,
        "action": action,
        "createdAt": stamp(now-timedelta(seconds=30)),
        "expiresAt": stamp(now+timedelta(hours=2)),
        "projectSha256": bridge.BASE_SHA,
        "sourceTask": None,
    }


class GateTests(TestCase):
    def test_source_review_only_job_is_accepted(self):
        m = sample()
        self.assertEqual(bridge.validate_job(m, m["jobId"])["action"],
                         "BDD114_ROOF_FINALIZE")

    def test_no_unreviewed_write_action(self):
        m = sample()
        m["action"] = "CREATE_COLUMNS"
        with self.assertRaisesRegex(ValueError, "JOB_ACTION_OR_TARGET_NOT_ALLOWED"):
            bridge.validate_job(m, m["jobId"])

    def test_no_foreign_pln_hash(self):
        m = sample()
        m["projectSha256"] = "0"*64
        with self.assertRaisesRegex(ValueError, "JOB_ACTION_OR_TARGET_NOT_ALLOWED"):
            bridge.validate_job(m, m["jobId"])

    def test_no_unpinned_source_task(self):
        m = sample("SOURCE_QUALIFIED_NATIVE_READ")
        m["sourceTask"] = {"repo": "dvikt33-ux/safe-bim-layer",
                           "ref": "main",
                           "path": "examples/accelerator/bdd-house.json",
                           "blobSha1": "a"*40}
        with self.assertRaisesRegex(ValueError, "READ_TASK_NOT_PINNED"):
            bridge.validate_job(m, m["jobId"])

    def test_no_replay_when_attempt_exists(self):
        with unittest.mock.patch.object(bridge, "STATE") as state:
            # Only durable-report publication is allowed after an attempt.
            with unittest.mock.patch.object(bridge, "remote_json", side_effect=AssertionError("REEXECUTED")):
                with unittest.mock.patch.object(bridge, "upload_result", return_value=None):
                    with unittest.mock.patch("pathlib.Path.is_dir", return_value=True):
                        with unittest.mock.patch("pathlib.Path.exists", return_value=False):
                            bridge.process_job("bdd114-roof-20261017")




def grid_sample(action="GRID_8X4_CHECK", name="grid-8x4-check-20261113"):
    now = datetime.now(timezone.utc)
    stamp = lambda value: value.strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "schema": "APA_AC29_GROUP_GRID_JOB_V1",
        "jobId": name,
        "action": action,
        "createdAt": stamp(now-timedelta(seconds=40)),
        "expiresAt": stamp(now+timedelta(hours=2)),
        "target": bridge.GRID_SCRATCH.name,
        "sourceCommit": bridge.GRID_SOURCE_COMMIT,
        "preflightSha256": None if action == "GRID_8X4_CHECK" else "b"*64,
        "authorizationRef": bridge.GRID_APPROVAL,
    }


class GridGateTests(TestCase):
    def test_checked_envelope_exact_scoped_job(self):
        job = grid_sample()
        self.assertEqual(bridge.validate_grid_job(job, job["jobId"]), job)

    def test_unrelated_file_or_source_rejected(self):
        for key, value in (
            ("target", "other.pln"),
            ("sourceCommit", "0"*40),
            ("authorizationRef", "UNAPPROVED"),
        ):
            job = grid_sample()
            job[key] = value
            with self.subTest(key=key), self.assertRaisesRegex(
                ValueError, "GRID_JOB_TARGET_SOURCE_OR_AUTHORIZATION_INVALID"
            ):
                bridge.validate_grid_job(job, job["jobId"])

    def test_execute_without_actual_preflight_receipt_pin_rejected(self):
        job = grid_sample("GRID_8X4_EXECUTE", "grid-8x4-execute-20261113")
        job["preflightSha256"] = None
        with self.assertRaisesRegex(ValueError, "GRID_EXECUTE_REQUIRES_PINNED"):
            bridge.validate_grid_job(job, job["jobId"])

    def test_extra_keys_and_unrelated_action_rejected(self):
        job = grid_sample()
        job["shell"] = "powershell"
        with self.assertRaisesRegex(ValueError, "GRID_JOB_ENVELOPE_KEYS_INVALID"):
            bridge.validate_grid_job(job, job["jobId"])
        job = grid_sample()
        job["action"] = "RUN_ARBITRARY_COMMAND"
        with self.assertRaisesRegex(ValueError, "GRID_JOB_SCHEMA_ID_OR_ACTION_INVALID"):
            bridge.validate_grid_job(job, job["jobId"])

    def test_invalid_expiry_rejected(self):
        job = grid_sample()
        job["expiresAt"] = "2025-01-01T00:00:00Z"
        with self.assertRaisesRegex(ValueError, "GRID_JOB_TIME_WINDOW_INVALID"):
            bridge.validate_grid_job(job, job["jobId"])

    def setUp(self):
        self.temp = TemporaryDirectory()
        root = Path(self.temp.name)
        self.script = root / "source" / "scripts" / "apa_ac29_group_grid_live_8x4.py"
        self.script.parent.mkdir(parents=True)
        self.script.write_text("# reviewed grid runner\n", encoding="utf-8")
        self.state = root / "state"
        self.state.mkdir()
        self.original = root / "original.pln"
        self.original.write_bytes(b"original saved model, fixed")
        self.scratch = root / "group-ac29-grid-8x4-20261018-01.pln"
        self.scratch.write_bytes(self.original.read_bytes())
        self.stage = {
            "schema": "APA_AC29_GROUP_GRID_STAGE_V1",
            "status": "STAGED_SAVED_COPY_ONLY_NO_ARCHICAD_CALLS",
            "scratchProject": str(self.scratch),
            "sourceProject": str(self.original),
            "sourceSavedSha256": bridge.sha(self.original),
            "sourceGroupId": bridge.GRID_SOURCE_GROUP,
            "expectedOriginalGuids": 44,
            "expectedPostGuids": 172,
        }
        (self.state / "stage.json").write_text(
            json.dumps(self.stage), encoding="utf-8")
        patches = (
            patch.object(bridge, "GRID_SCRIPT", self.script),
            patch.object(bridge, "GRID_STATE", self.state),
            patch.object(bridge, "GRID_SCRATCH", self.scratch),
            patch.object(bridge, "GRID_SCRIPT_BLOB_SHA1",
                         bridge.git_sha(self.script.read_bytes())),
            patch.object(bridge.subprocess, "run", return_value=type(
                "P", (), {"returncode": 0,
                           "stdout": bridge.GRID_SOURCE_COMMIT+"\n"})()),
        )
        self.patches = patches
        for p in patches:
            p.start()

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()
        self.temp.cleanup()

    def test_readonly_grid_scope_passes_without_native_calls(self):
        result = bridge.grid_scope_preflight(grid_sample())
        self.assertEqual(result["sourceSavedSha256"], bridge.sha(self.original))

    def test_stage_source_or_scratch_mutation_blocks_execution(self):
        self.scratch.write_bytes(b"unreviewed changes")
        with self.assertRaisesRegex(ValueError, "GRID_ORIGINAL_OR_COPY_SHA256_DRIFT"):
            bridge.grid_scope_preflight(grid_sample())

    def test_duplicate_attempt_blocks_all_replay(self):
        (self.state / "attempted.json").write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "GRID_PREVIOUS_NATIVE_ATTEMPT_NEVER_REPLAY"):
            bridge.grid_scope_preflight(grid_sample())

    def test_grid_execute_requires_matching_readonly_preflight(self):
        pre = {
            "status": "GRID_8X4_NATIVE_BREP_AND_RUNTIME_PREFLIGHT_PASS",
            "sourceRevision": bridge.GRID_SOURCE_COMMIT,
            "sourcePlnSha256": bridge.sha(self.scratch),
            "scratchPath": str(self.scratch),
            "originalSourceGuidCount": 44,
            "expectedGuidCountAfter": 172,
            "nativeCallCountIfAuthorized": 1,
            "archicadWrites": 0,
            "saveCalls": 0,
            "automaticRetry": False,
        }
        receipt = self.state / "preflight.json"
        receipt.write_text(json.dumps(pre), encoding="utf-8")
        job = grid_sample("GRID_8X4_EXECUTE", "grid-8x4-execute-20261113")
        job["preflightSha256"] = bridge.sha(receipt)
        bridge.grid_scope_preflight(job)
        job["preflightSha256"] = "a"*64
        with self.assertRaisesRegex(ValueError, "GRID_EXECUTION_PREFLIGHT_RECEIPT_SHA256_DRIFT"):
            bridge.grid_scope_preflight(job)

if __name__ == "__main__":
    unittest.main()
