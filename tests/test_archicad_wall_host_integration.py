"""Offline contract integration: existing deployed WallExecutor + BIM planner.

The 10 original tests are loaded without editing or moving their source.
No Archicad connection, GitHub mailbox action, SQLite production data, or PLN.
"""
from __future__ import annotations

from datetime import datetime, timezone
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import archicad_mailbox_wall_host as HOST

spec = importlib.util.spec_from_file_location(
    "archicad_mailbox_graph_adapter_integration", SCRIPTS / "archicad_mailbox_graph_adapter.py")
ADAPTER = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ADAPTER)

suite_spec = importlib.util.spec_from_file_location(
    "transferred_wall_host_safety_tests", SCRIPTS / "test_archicad_mailbox_wall_host.py")
TRANSFERRED = importlib.util.module_from_spec(suite_spec)
suite_spec.loader.exec_module(TRANSFERRED)


def load_tests(loader, tests, pattern):
    """Make sure CI discovers the unmodified 10 safety tests under scripts/."""
    tests.addTests(loader.loadTestsFromModule(TRANSFERRED))
    return tests


TARGET = {
    "instanceId": f"archicad-{HOST.PORT}",
    "logicalProjectId": "live-local-offline-fixture",
    "port": HOST.PORT,
    "projectName": HOST.PROJECT_NAME,
    "projectPath": HOST.PROJECT_PATH,
}


def wall():
    return {
        "begCoordinate": {"x": 26.0, "y": 20.0},
        "endCoordinate": {"x": 30.0, "y": 20.0},
        "floorIndex": 0, "zCoordinate": 0.0, "height": 3.0,
        "thickness": 0.2, "offset": 0.0, "arcAngle": 0.0,
        "referenceLineLocation": "Center", "structureType": "Basic",
    }


def plan():
    return {"operations": [
        {"id": "wall", "command": "CreateWalls",
         "params": {"wallsData": [wall()]}}
    ]}


class HostPlannerContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = ADAPTER.GRAPH.CONTRACTS.load_catalog(ROOT / "tapir-1.5.8.json")

    def test_exact_wall_preview_is_accepted_by_preserved_host_validator(self):
        created = datetime.now(timezone.utc).isoformat()
        preview = ADAPTER.prepare(
            self.catalog, plan(), [], TARGET, "offline-integration",
            mode="dry-run", created_at=created)
        self.assertEqual(preview["status"], "NEXT_JOB_PREVIEW")
        envelope = preview["mailboxEnvelope"]
        self.assertEqual(envelope["payload"]["recipe"], "create_wall_v1")
        self.assertEqual(envelope["payloadHash"], HOST.digest(envelope["payload"]))
        operation = HOST.validate(envelope["payload"])
        self.assertEqual(operation["wall"], envelope["payload"]["wall"])
        self.assertEqual(HOST.digest(operation), ADAPTER.digest(operation))
        self.assertFalse(preview["jobPublished"])

    def test_graph_rejects_walls_outside_host_geometry_limits(self):
        scenarios = [
            ("length", lambda w: w["endCoordinate"].update(x=32.5)),
            ("height", lambda w: w.update(height=5.01)),
            ("thickness", lambda w: w.update(thickness=0.6)),
            ("floor", lambda w: w.update(floorIndex=1)),
            ("z", lambda w: w.update(zCoordinate=1.0)),
        ]
        for label, transform in scenarios:
            with self.subTest(label=label):
                candidate = plan()
                transform(candidate["operations"][0]["params"]["wallsData"][0])
                with self.assertRaises(ValueError):
                    ADAPTER.prepare(self.catalog, candidate, [], TARGET, "offline-test")

    def test_schema_addon_version_mismatch_is_visible(self):
        self.assertEqual(ADAPTER.GRAPH.CONTRACTS.source_version(self.catalog), "1.5.8")
        report = ADAPTER.GRAPH.compile_graph(self.catalog, plan(), runtime_version="1.5.10")
        self.assertEqual(report["status"], "REQUIRES_UPDATED_SCHEMA")
        self.assertIs(report["executionSupported"], False)

    def test_writer_allowlist_remains_one_command(self):
        self.assertEqual(HOST.WRITES, frozenset({"CreateWalls"}))
        for command in ("CreateWindows", "CreateDoors", "CreateSlabs",
                        "CreateColumns", "CreateMEPElements", "SaveProject"):
            self.assertNotIn(command, HOST.WRITES)

    def test_door_owner_must_reference_wall(self):
        candidate = {"operations": [
            {"id": "column", "command": "CreateColumns", "params": {
                "columnsData": [{"coordinates": {"x": 2, "y": 3, "z": 0}, "height": 3}]
            }},
            {"id": "door", "command": "CreateDoors", "params": {
                "doorsData": [{"ownerWallId": {"guid": {"$createdGuid": "column"}},
                               "centerOffset": 0.5, "width": 0.9, "height": 2.1}]
            }},
        ]}
        result = ADAPTER.GRAPH.compile_graph(self.catalog, candidate)
        self.assertEqual(result["status"], "INVALID")
        self.assertTrue(any("host must be Wall" in err
                       for step in result["operations"] for err in step["errors"]))

    def test_slabs_columns_and_hosted_openings_only_offline(self):
        candidate = {"operations": [
            plan()["operations"][0],
            {"id": "window", "command": "CreateWindows", "params": {
                "windowsData": [{"ownerWallId": {"guid": {"$createdGuid": "wall"}},
                                 "centerOffset": 0.5, "width": 0.8, "height": 1.0}]
            }},
            {"id": "door", "command": "CreateDoors", "params": {
                "doorsData": [{"ownerWallId": {"guid": {"$createdGuid": "wall"}},
                               "centerOffset": 2.7, "width": 0.9, "height": 2.1}]
            }},
            {"id": "slab", "command": "CreateSlabs", "params": {
                "slabsData": [{"level": 0.0, "floorIndex": 0,
                               "polygonCoordinates": [
                                   {"x": 0, "y": 0}, {"x": 4, "y": 0},
                                   {"x": 4, "y": 4}, {"x": 0, "y": 4}]}]
            }},
            {"id": "column", "command": "CreateColumns", "params": {
                "columnsData": [{"coordinates": {"x": 1, "y": 1, "z": 0},
                                 "height": 3}]
            }}
        ]}
        report = ADAPTER.GRAPH.compile_graph(self.catalog, candidate)
        self.assertEqual(report["status"], "PLAN_VALIDATED_OFFLINE")
        preview = ADAPTER.prepare(self.catalog, candidate, [], TARGET,
                                  "offline-integration", mode="execute")
        self.assertEqual(preview["status"], "UNSUPPORTED_GRAPH")
        self.assertEqual(set(preview["unsupportedSteps"]),
                         {"window", "door", "slab", "column"})
        self.assertFalse(preview["jobPublished"])
        self.assertNotIn("mailboxEnvelope", preview)


if __name__ == "__main__":
    unittest.main()
