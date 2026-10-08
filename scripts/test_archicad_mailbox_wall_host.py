"""Synthetic safety tests; no live Archicad or GitHub calls."""
import copy
import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from datetime import timedelta
from pathlib import Path
from archicad_mailbox_wall_host import (
    WallExecutor, PORT, PROJECT_NAME, PROJECT_PATH, digest, utcnow, validate,
)


class FakeTransport:
    def __init__(self, job):
        self.job, self.binding_calls = job, 0
        self.switch_at = None
        self.bad_readback = False

    def binding(self):
        self.binding_calls += 1
        binding = {k: self.job[k] for k in ("instanceId", "logicalProjectId", "projectName", "projectPath", "port")}
        if self.switch_at == self.binding_calls:
            binding["logicalProjectId"] = "wrong-project"
        return binding

    def call(self, command, params):
        if command == "GetStories":
            return {"actStory": 0, "stories": [{"index": 0, "floorId": 1, "level": 0}]}
        wall = copy.deepcopy(self.job["wall"])
        wall.update(geometryType="Straight", begThickness=wall.pop("thickness"))
        wall["endThickness"] = wall["begThickness"]
        if self.bad_readback:
            wall["height"] += 1
        return {"detailsOfElements": [{"type": "Wall", "floorIndex": 0, "details": wall}]}


class SafetyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)
        self.job = {"recipe": "create_wall_v1", "operationId": "op-1", "instanceId": "archicad-19723",
                    "logicalProjectId": "live-local-test", "projectName": PROJECT_NAME, "projectPath": PROJECT_PATH,
                    "port": PORT, "expiresAt": (utcnow()+timedelta(minutes=10)).isoformat(),
                    "wall": {"begCoordinate": {"x": 23, "y": 20}, "endCoordinate": {"x": 24, "y": 20},
                             "floorIndex": 0, "zCoordinate": 0, "height": 3, "thickness": .2, "offset": 0,
                             "arcAngle": 0, "referenceLineLocation": "Center", "structureType": "Basic"}}
        self.transport = FakeTransport(self.job)
        self.writes = []
        self.approval = self.path / "approval.json"
        self.executor = WallExecutor(self.transport, self.path / "journal.sqlite3", enable_execute=True,
                                     approval=self.approval, writer=self.write)

    def approve(self):
        self.approval.write_text(json.dumps({"operationHash": digest(validate(self.job)),
            "expiresAt": self.job["expiresAt"], "approvedBy": "test-human", "permission": "CreateWalls"}), encoding="utf-8")

    def write(self, cmd, params):
        with closing(sqlite3.connect(self.executor.journal)) as db:
            self.assertEqual(db.execute("SELECT state FROM attempts").fetchone()[0], "ATTEMPTED")
        self.writes.append((cmd, params))
        return {"elements": [{"elementId": {"guid": "F0E8C2B3-1248-4D92-8890-EA1379E18152"}}]}

    def test_default_dry_run(self):
        self.assertEqual(self.executor.execute(self.job)["status"], "DRY_RUN")
        self.assertFalse(self.writes)

    def test_remote_execute_requires_local_approval(self):
        self.job["mode"] = "execute"
        self.assertEqual(self.executor.execute(self.job)["status"], "BLOCKED")
        self.assertFalse(self.writes)

    def test_success_and_duplicate_operation_under_new_message(self):
        self.approve(); self.job["mode"] = "execute"
        self.assertEqual(self.executor.execute(self.job)["status"], "PASS")
        self.assertEqual(self.executor.execute(self.job)["status"], "BLOCKED")
        self.assertEqual(len(self.writes), 1)

    def test_timeout_is_terminal(self):
        self.approve(); self.job["mode"] = "execute"
        def timeout(cmd, params):
            self.writes.append(cmd)
            raise TimeoutError("synthetic timeout")
        self.executor.writer = timeout
        self.assertEqual(self.executor.execute(self.job)["status"], "UNKNOWN_OUTCOME")
        self.assertEqual(self.executor.execute(self.job)["status"], "BLOCKED")
        self.assertEqual(len(self.writes), 1)

    def test_wrong_project_and_port(self):
        for key, value in (("projectPath", r"C:\Пятницкая точки.pln"), ("port", 19724), ("projectName", "Тест MER")):
            job = copy.deepcopy(self.job); job[key] = value
            self.assertEqual(self.executor.execute(job)["status"], "BLOCKED")
        self.assertFalse(self.writes)

    def test_binding_changes_at_write_boundary(self):
        self.approve(); self.job["mode"] = "execute"
        self.transport.switch_at = 3
        self.assertEqual(self.executor.execute(self.job)["status"], "UNKNOWN_OUTCOME")
        self.assertFalse(self.writes)
        self.assertEqual(self.executor.execute(self.job)["status"], "BLOCKED")

    def test_approval_cannot_authorize_changed_dimensions(self):
        self.approve(); self.job["mode"] = "execute"; self.job["wall"]["height"] = 4
        self.assertEqual(self.executor.execute(self.job)["status"], "BLOCKED")
        self.assertFalse(self.writes)

    def test_readback_mismatch_is_not_pass(self):
        self.approve(); self.job["mode"] = "execute"; self.transport.bad_readback = True
        result = self.executor.execute(self.job)
        self.assertEqual(result["status"], "BLOCKED_READBACK")
        self.assertTrue(result["mutationApplied"])

    def test_expired_and_nonfinite(self):
        self.job["expiresAt"] = (utcnow()-timedelta(seconds=1)).isoformat()
        self.assertEqual(self.executor.execute(self.job)["status"], "BLOCKED")
        self.job["expiresAt"] = (utcnow()+timedelta(minutes=10)).isoformat()
        self.job["wall"]["height"] = float("nan")
        self.assertEqual(self.executor.execute(self.job)["status"], "BLOCKED")
        self.assertFalse(self.writes)

    def test_no_execute_without_host_switch(self):
        self.approve(); self.job["mode"] = "execute"; self.executor.enable_execute = False
        self.assertEqual(self.executor.execute(self.job)["status"], "BLOCKED")
        self.assertFalse(self.writes)


if __name__ == "__main__":
    unittest.main()
