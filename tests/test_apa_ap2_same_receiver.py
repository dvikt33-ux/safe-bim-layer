"""Offline regression for pinned AP2 target in existing single autonomous receiver."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "scripts" / "apa_ac29_autonomous_job_bridge.py"
spec = importlib.util.spec_from_file_location("apa_ap2_worker_test", SOURCE)
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)


class TestAP2NativeReadOnly(unittest.TestCase):
    def test_gate_requires_exact_source_hash_and_null_source_task(self):
        with tempfile.TemporaryDirectory() as td:
            original = worker.AP2_PROJECT
            worker.AP2_PROJECT = Path(td) / "isolated-ap2.pln"
            try:
                worker.AP2_PROJECT.write_bytes(b"archicad model fixture" * 15000)
                now = datetime.now(timezone.utc)
                obj = {
                    "schema": "APA_AC29_AUTONOMOUS_JOB_V1",
                    "jobId": "ap2-readonly-synthetic-0001",
                    "action": "AP2_READONLY_PROJECT_INVENTORY",
                    "createdAt": (now-timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "expiresAt": (now+timedelta(minutes=8)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "projectSha256": worker.sha(worker.AP2_PROJECT),
                    "sourceTask": None,
                }
                self.assertEqual(worker.validate_job(obj, obj["jobId"]), obj)
                wrong = dict(obj, projectSha256="a"*64)
                with self.assertRaisesRegex(ValueError, "JOB_ACTION_OR_TARGET_NOT_ALLOWED"):
                    worker.validate_job(wrong, obj["jobId"])
                wrong = dict(obj, sourceTask={"any": "source"})
                with self.assertRaisesRegex(ValueError, "LOCAL_APPROVED_ACTION"):
                    worker.validate_job(wrong, obj["jobId"])
            finally:
                worker.AP2_PROJECT = original

    def test_readonly_inventory_valid_and_no_writes(self):
        with tempfile.TemporaryDirectory() as td:
            original = worker.AP2_PROJECT
            read = worker.ap2_tapir_read
            worker.AP2_PROJECT = Path(td) / "ap2-test.pln"
            worker.AP2_PROJECT.write_bytes(b"AP2" * 60000)
            hits = []
            def only_reads(name, params=None):
                hits.append(name)
                if name == "GetProjectInfo":
                    return {"isUntitled": False, "isTeamwork": False,
                            "projectPath": str(worker.AP2_PROJECT)}
                if name == "GetAllElements":
                    return {"elements": [{"elementId": {"guid":
                        "4cb6a018-1663-4baf-b3d6-9967b15ec0e1"}}]}
                if name == "GetStories":
                    return {"stories": [{"index": 0, "level": 0, "height": 3}]}
                raise AssertionError("unknown command")
            try:
                worker.ap2_tapir_read = only_reads
                job = {"action":"AP2_READONLY_PROJECT_INVENTORY",
                       "sourceTask":None,
                       "projectSha256":worker.sha(worker.AP2_PROJECT)}
                report = worker.capture_ap2_inventory(job, Path(td))
                self.assertEqual(hits, ["GetProjectInfo","GetAllElements",
                                        "GetStories","GetProjectInfo"])
                self.assertEqual(report["nativeElementCount"], 1)
                self.assertEqual(report["nativeWrites"], 0)
                self.assertFalse(report["readyForConstructionWrite"])
            finally:
                worker.AP2_PROJECT = original
                worker.ap2_tapir_read = read

    def test_readonly_inventory_rejects_wrong_active_pln(self):
        with tempfile.TemporaryDirectory() as td:
            original = worker.AP2_PROJECT
            read = worker.ap2_tapir_read
            worker.AP2_PROJECT = Path(td) / "ap2-test.pln"
            worker.AP2_PROJECT.write_bytes(b"AP2" * 60000)
            try:
                worker.ap2_tapir_read = lambda name, params=None: {
                    "isUntitled":False,"isTeamwork":False,
                    "projectPath":r"C:\LocalAI\SafeBIM_Global_Library_Test_Projects\BDD dummy.pln"}
                with self.assertRaisesRegex(ValueError,"AP2_ACTIVE_PROJECT_PATH"):
                    worker.capture_ap2_inventory(
                        {"action":"AP2_READONLY_PROJECT_INVENTORY",
                         "sourceTask":None,
                         "projectSha256":worker.sha(worker.AP2_PROJECT)},
                        Path(td))
            finally:
                worker.AP2_PROJECT = original
                worker.ap2_tapir_read = read

    def test_ap2_readonly_allowlist_only(self):
        self.assertIn("AP2_READONLY_PROJECT_INVENTORY", worker.ALLOWED)
        self.assertEqual(worker.AP2_PORT,19725)
        self.assertTrue(worker.AP2_PROJECT.name.endswith(".pln"))
        # No native arbitrary commands accepted by AP2 reader.
        with self.assertRaisesRegex(ValueError, "AP2_UNAPPROVED_NATIVE_COMMAND"):
            worker.ap2_tapir_read("CreateWalls")

if __name__ == "__main__":
    unittest.main()
