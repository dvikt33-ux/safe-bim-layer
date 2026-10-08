"""No network, Archicad, local host, or PLN operations in these tests."""
from datetime import datetime, timedelta, timezone
import importlib.util
from pathlib import Path
import tempfile
import unittest

MOD = Path(__file__).resolve().parents[1] / "scripts" / "archicad_mailbox_watch.py"
spec = importlib.util.spec_from_file_location("archicad_mailbox_watch", MOD)
watch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(watch)

NOW = datetime(2026, 10, 9, 0, 0, tzinfo=timezone.utc)
TARGET = {
    "instanceId": "archicad-19723",
    "logicalProjectId": "live-local-synthetic",
    "projectName": "Тест MER ",
    "projectPath": "C:\\LocalAI\\SafeBIM_Global_Library_Test_Projects\\Тест MER .pln",
    "port": 19723,
}


def job(mid, *, mode="dry-run", target=None, created=None, expires=None):
    target = TARGET if target is None else target
    created = (NOW - timedelta(minutes=1)) if created is None else created
    expires = (NOW + timedelta(minutes=10)) if expires is None else expires
    p = {
        **target,
        "mode": mode, "recipe": "create_wall_v1",
        "operationId": "dry-example", "expiresAt": expires.isoformat(),
        "wall": {
            "begCoordinate": {"x": 50.0, "y": 20.0},
            "endCoordinate": {"x": 51.0, "y": 20.0},
            "height": 3.0, "thickness": 0.2, "floorIndex": 0,
            "zCoordinate": 0.0, "offset": 0.0, "arcAngle": 0.0,
            "referenceLineLocation": "Center", "structureType": "Basic",
        },
    }
    return {
        "protocolVersion": 1, "messageId": mid, "kind": "JOB",
        "createdAt": created.isoformat(), "payload": p,
        "payloadHash": watch.digest(p),
    }


class WatcherTests(unittest.TestCase):
    def test_dry_run_accepted_and_execute_rejected(self):
        self.assertEqual(watch.validate_job(job("dry"), "dry", TARGET, NOW), "ACCEPT")
        self.assertEqual(watch.validate_job(job("exec", mode="execute"), "exec",
                                            TARGET, NOW), "EXECUTE_NOT_ENABLED")

    def test_target_and_expiry_fail_closed(self):
        bad = dict(TARGET, projectName="Пятницкая точки")
        self.assertEqual(watch.validate_job(job("wrong", target=bad), "wrong",
                                            TARGET, NOW), "TARGET_MISMATCH")
        self.assertEqual(watch.validate_job(
            job("expired", expires=NOW - timedelta(seconds=1)),
            "expired", TARGET, NOW), "EXPIRED_OR_INVALID_WINDOW")

    def test_payload_hash_tamper_rejected(self):
        value = job("tamper")
        value["payload"]["projectPath"] = "C:\\Other.pln"
        self.assertEqual(watch.validate_job(value, "tamper", TARGET, NOW),
                         "PAYLOAD_HASH_MISMATCH")

    def test_first_scan_baselines_existing_jobs(self):
        with tempfile.TemporaryDirectory() as folder:
            state = Path(folder) / "watch.json"
            invoked = []
            seen = {"old-1": "x", "old-2": "y"}
            out = watch.pump_one(state, seen, lambda mid: job(mid),
                                lambda: TARGET,
                                lambda mid: invoked.append(mid), TARGET, now=NOW)
            self.assertEqual(out["status"], "BASELINE_CREATED")
            self.assertEqual(out["oldJobsSkipped"], 2)
            self.assertEqual(invoked, [])
            self.assertEqual(watch.pump_one(state, seen, lambda mid: job(mid),
                             lambda: TARGET, lambda mid: invoked.append(mid),
                             TARGET, now=NOW)["status"], "IDLE")

    def test_new_job_processed_once_and_durable(self):
        with tempfile.TemporaryDirectory() as folder:
            state = Path(folder) / "watch.json"
            worker_calls = []
            run = lambda mid: worker_calls.append(mid) or {"status": "PROCESSED"}
            watch.pump_one(state, {"old": "sha"}, lambda mid: job(mid),
                           lambda: TARGET, run, TARGET, now=NOW)
            added = {"old": "sha", "new": "sha"}
            out = watch.pump_one(state, added, lambda mid: job(mid),
                                 lambda: TARGET, run, TARGET, now=NOW)
            self.assertEqual(out["results"][0]["decision"], "ACCEPT")
            self.assertEqual(worker_calls, ["new"])
            watch.pump_one(state, added, lambda mid: job(mid),
                           lambda: TARGET, run, TARGET, now=NOW)
            self.assertEqual(worker_calls, ["new"])

    def test_wrong_live_project_cannot_start_worker(self):
        with tempfile.TemporaryDirectory() as folder:
            state = Path(folder) / "watch.json"
            watch.pump_one(state, {}, lambda mid: job(mid),
                           lambda: TARGET, lambda mid: None, TARGET, now=NOW)
            invoked = []
            out = watch.pump_one(state, {"new": "sha"}, lambda mid: job(mid),
                    lambda: dict(TARGET, projectPath="C:\\Wrong.pln"),
                    lambda mid: invoked.append(mid), TARGET, now=NOW)
            self.assertEqual(out["results"][0]["decision"], "LIVE_PROJECT_NOT_ALLOWED")
            self.assertFalse(invoked)

    def test_worker_failure_is_not_retried(self):
        with tempfile.TemporaryDirectory() as folder:
            state = Path(folder) / "watch.json"
            watch.pump_one(state, {}, lambda mid: job(mid),
                           lambda: TARGET, lambda mid: None, TARGET, now=NOW)
            count = []
            def failed(mid):
                count.append(mid)
                raise TimeoutError("unknown")
            out = watch.pump_one(state, {"new": "sha"}, lambda mid: job(mid),
                                 lambda: TARGET, failed, TARGET, now=NOW)
            self.assertEqual(out["results"][0]["worker"]["status"], "UNKNOWN_OUTCOME")
            self.assertEqual(len(count), 1)
            watch.pump_one(state, {"new": "sha"}, lambda mid: job(mid),
                           lambda: TARGET, failed, TARGET, now=NOW)
            self.assertEqual(len(count), 1)

    def test_message_name_mismatch_is_rejected(self):
        self.assertEqual(watch.validate_job(job("foo"), "bar", TARGET, NOW),
                         "BAD_ENVELOPE")


if __name__ == "__main__":
    unittest.main()
