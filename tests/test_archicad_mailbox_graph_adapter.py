"""Offline tests for graph -> existing Mailbox JOB/RESULT compatibility."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "archicad_mailbox_graph_adapter",
    ROOT / "scripts" / "archicad_mailbox_graph_adapter.py")
bridge = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bridge)

TARGET = {
    "instanceId": "archicad-19723",
    "logicalProjectId": "synthetic-local-test-project",
    "port": 19723,
    "projectName": "Offline fixture",
    "projectPath": "C:\\Synthetic\\Offline Fixture.pln",
}
STAMP = "2026-10-09T00:00:00+00:00"
GUID = "6246AAAF-F18B-4FB7-8F5A-9C70CECA2FDD"


def wall(x):
    return {"begCoordinate": {"x": x, "y": 20},
            "endCoordinate": {"x": x + 1, "y": 20},
            "floorIndex": 0, "zCoordinate": 0,
            "height": 3, "thickness": 0.2, "offset": 0,
            "arcAngle": 0, "referenceLineLocation": "Center",
            "structureType": "Basic"}


def step(sid, x, after=None):
    result = {"id": sid, "command": "CreateWalls",
              "params": {"wallsData": [wall(x)]}}
    if after is not None:
        result["after"] = after
    return result


def generated_result(preview, *, status="PASS", target=None):
    job = preview["mailboxEnvelope"]
    payload = job["payload"]
    w = payload["wall"]
    result = {
        "automaticRetry": False, "command": "CreateWalls",
        "createdGuid": GUID, "mutationApplied": True,
        "operationId": payload["operationId"],
        "parameters": {"wallsData": [w]}, "plnSaved": False,
        "readback": {
            "type": "Wall", "floorIndex": w["floorIndex"],
            "details": {
                "geometryType": "Straight",
                "structureType": "Basic",
                "referenceLineLocation": "Center",
                "begCoordinate": w["begCoordinate"],
                "endCoordinate": w["endCoordinate"],
                "height": w["height"],
                "begThickness": w["thickness"],
                "endThickness": w["thickness"],
                "offset": w["offset"],
                "zCoordinate": w["zCoordinate"],
            }
        },
        "target": target or TARGET, "verification": {"type": True},
        "status": status,
    }
    body = {"job_id": "job-" + job["messageId"], "result": result}
    return {"protocolVersion": 1,
            "messageId": "result-job-" + job["messageId"],
            "kind": "RESULT", "createdAt": STAMP,
            "payload": body, "payloadHash": bridge.digest(body)}


class GraphToMailboxTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = bridge.GRAPH.CONTRACTS.load_catalog(ROOT / "tapir-1.5.8.json")

    def prepare(self, plan, history=None, **kwargs):
        return bridge.prepare(
            self.catalog, plan, history or [], TARGET, "test-run-001",
            created_at=STAMP, **kwargs)

    def test_exact_mailbox_shape_and_payload_hash(self):
        plan = {"operations": [step("wall", 23)]}
        preview = self.prepare(plan)
        self.assertEqual(preview["status"], "NEXT_JOB_PREVIEW")
        remote = preview["mailboxEnvelope"]
        self.assertEqual(remote["kind"], "JOB")
        self.assertEqual(remote["protocolVersion"], 1)
        self.assertEqual(remote["payloadHash"], bridge.digest(remote["payload"]))
        self.assertEqual(remote["payload"]["recipe"], "create_wall_v1")
        self.assertEqual(remote["payload"]["mode"], "dry-run")
        self.assertFalse(preview["jobPublished"])

    def test_two_steps_advance_only_after_matching_verified_pass(self):
        plan = {"operations": [step("second", 30, ["first"]), step("first", 23)]}
        first = self.prepare(plan, mode="execute")
        self.assertEqual(first["stepId"], "first")
        second = self.prepare(plan, [generated_result(first)], mode="execute")
        self.assertEqual(second["status"], "NEXT_JOB_PREVIEW")
        self.assertEqual(second["stepId"], "second")
        self.assertEqual(second["completedSteps"]["first"], GUID)
        self.assertNotEqual(first["mailboxEnvelope"]["messageId"],
                            second["mailboxEnvelope"]["messageId"])

    def test_graph_complete_only_after_every_verified_pass(self):
        plan = {"operations": [step("only", 23)]}
        first = self.prepare(plan, mode="execute")
        complete = self.prepare(plan, [generated_result(first)], mode="execute")
        self.assertEqual(complete["status"], "GRAPH_COMPLETE")
        self.assertEqual(complete["createdGuids"]["only"], GUID)

    def test_tampering_result_hash_fails_closed(self):
        plan = {"operations": [step("wall", 23)]}
        preview = self.prepare(plan, mode="execute")
        response = generated_result(preview)
        response["payload"]["result"]["createdGuid"] = "00000000-0000-0000-0000-000000000000"
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            self.prepare(plan, [response], mode="execute")

    def test_wrong_target_even_with_correct_hash_fails(self):
        plan = {"operations": [step("wall", 23)]}
        preview = self.prepare(plan, mode="execute")
        response = generated_result(preview,
            target={**TARGET, "projectPath": "C:\\Synthetic\\Other.pln"})
        with self.assertRaisesRegex(ValueError, "project fingerprint mismatch"):
            self.prepare(plan, [response], mode="execute")

    def test_wrong_readback_geometry_fails(self):
        plan = {"operations": [step("wall", 23)]}
        preview = self.prepare(plan, mode="execute")
        response = generated_result(preview)
        response["payload"]["result"]["readback"]["details"]["endCoordinate"]["x"] = 99
        response["payloadHash"] = bridge.digest(response["payload"])
        with self.assertRaisesRegex(ValueError, "geometry"):
            self.prepare(plan, [response], mode="execute")

    def test_unknown_result_blocks_automatic_retry(self):
        plan = {"operations": [step("wall", 23)]}
        preview = self.prepare(plan, mode="execute")
        response = generated_result(preview, status="UNKNOWN_OUTCOME")
        out = self.prepare(plan, [response], mode="execute")
        self.assertEqual(out["status"], "STOP")
        self.assertFalse(out["automaticRetry"])

    def test_window_after_wall_needs_worker_recipe(self):
        plan = {"operations": [
            step("wall", 23),
            {"id": "window", "command": "CreateWindows", "params": {
                "windowsData": [{"ownerWallId": {"guid": {"$createdGuid": "wall"}},
                                 "centerOffset": 0.5, "width": 0.6, "height": 1.2}]}}
        ]}
        preview = self.prepare(plan)
        self.assertEqual(preview["status"], "NEXT_JOB_PREVIEW")
        out = self.prepare(plan, mode="execute")
        self.assertEqual(out["status"], "UNSUPPORTED_GRAPH")
        self.assertIn("window", out["unsupportedSteps"])
        self.assertFalse(out.get("jobPublished", False))

    def test_rejects_unknown_input_and_improper_wall(self):
        plan = {"operations": [step("wall", 23)]}
        self.assertRaises(ValueError, bridge.prepare, self.catalog, plan, [],
                          {**TARGET, "instanceId": "archicad-19724"}, "run-id")
        plan["operations"][0]["params"]["wallsData"][0]["structureType"] = "Composite"
        with self.assertRaisesRegex(ValueError, "only Basic walls proven"):
            self.prepare(plan)

    def test_stable_identity_across_preview_and_execute_modes(self):
        plan = {"operations": [step("wall", 23)]}
        a = self.prepare(plan)
        b = self.prepare(plan, mode="execute")
        self.assertEqual(a["mailboxEnvelope"]["payload"]["operationId"],
                         b["mailboxEnvelope"]["payload"]["operationId"])
        self.assertNotEqual(a["mailboxEnvelope"]["messageId"],
                            b["mailboxEnvelope"]["messageId"])


if __name__ == "__main__":
    unittest.main()
