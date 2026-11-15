from contextlib import closing
from pathlib import Path
import sqlite3
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import apa_tdk_wall as trace
import archicad_project_accelerator as core
from apa_ac29_group_batch_oneshot import IDENTITY
from apa_ac29_save_isolation import write_new_json


class TraceIntegration(unittest.TestCase):
    WALL = "11111111-1111-4111-8111-111111111111"
    PROPERTY = "22222222-2222-4222-8222-222222222222"
    NAME = "AI_SOURCE_PACK"
    HASH = "a" * 64

    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.source = self.root / "source.pln"
        self.source.write_bytes(b"protected fixture")
        self.job = self.root / "tdk-test-01"
        payload = self.root / "input.json"
        write_new_json(payload, {"operationId": "trace-fixture"})
        self.native = self.root / "test.apx"
        self.native.write_bytes(b"fixture")
        native_dir = self.root / "native"
        native_dir.mkdir()
        receipt = native_dir / "binary-receipt.json"
        write_new_json(receipt, {"binary": {"apxSHA256": trace.sha256(self.native),
            "sourceRevision": "b" * 40, "buildIdentity": "c" * 64}})
        write_new_json(self.root / trace.MANIFEST, dict(schema="APA_WINDOWS_RELEASE_V1",
            revision="d" * 40, files={"native/binary-receipt.json": {
                "bytes": receipt.stat().st_size, "sha256": trace.sha256(receipt)}}))
        self.vendor = SimpleNamespace(validate_payload=lambda value: value, state_hash=lambda _: self.HASH)
        self.props = {self.NAME: dict(propertyId={"guid": self.PROPERTY}, propertyName=self.NAME,
            propertyGroupName="AI_TRACE", propertyCollectionType="Single",
            propertyValueType="String", propertyIsEditable=True)}
        self.old = "before"
        self.actual = self.old
        self.writes = 0
        self.confirm_native_mutation = True
        self.signatures = {self.WALL: "wall-geometry"}
        self.product = dict(contract="APA_NATIVE_RUNTIME_IDENTITY_V1", sdkMajor=29, nativeModelWrites=0,
                            sourceRevision="b" * 40, buildIdentity="c" * 64)
        vendor = patch.object(trace, "vendor_module", return_value=self.vendor)
        vendor.start()
        self.addCleanup(vendor.stop)
        trace.stage_trace(self.root, self.job, self.source, payload)
        self.project = self.job / "TDK-AI-TRACE-test.pln"
        for patcher in (
            patch("apa_mailbox_profile.APX", self.native),
            patch.object(IDENTITY, "current_project"),
            patch.object(core, "native_transport", self.transport),
            patch.object(trace, "wall_runtime", return_value=self),
            patch.object(trace, "trace_snapshot", side_effect=lambda *_: ([self.WALL], dict(self.signatures))),
            patch.object(core.RUN, "bind_authorized_saved_copy"),
            patch.object(core.RUN, "guarded_scene_project", return_value={
                "path": str(self.project), "name": self.project.stem, "port": 19725,
                "tapirVersion": "1.5.10", "storyIndex": 0}),
            patch("archicad_bim_documentation.capture_full_model", return_value={}),
            patch("archicad_connected_components.retained_geometry_signatures", return_value={}),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)
        self.properties = self.props

    def trace_values(self, _payload, _desired_hash):
        return {self.NAME: "after"}

    def ensure(self, _payload, *, commit):
        self.assertFalse(commit)
        common = dict(dryRun=True, guid=self.WALL, desiredHash=self.HASH)
        if self.actual == "after":
            return dict(common, status="NO_CHANGE")
        return dict(common, status="WOULD_UPDATE_TRACE",
                    traceDelta={self.NAME: {"actual": self.actual, "desired": "after"}})

    def transport(self, command, parameters):
        if command == "GetAPARuntimeInfoV1":
            return self.product
        if command == "API.IsAddOnCommandAvailable":
            return {"available": True}
        if command == "GetAddOnVersion":
            return {"version": "1.5.10"}
        if command == "GetAllElements":
            return {"elements": [{"elementId": {"guid": self.WALL}}]}
        if command == trace.SET_TRACE:
            self.assertTrue((self.job / "trace-attempted.json").exists())
            with closing(sqlite3.connect(self.job / "scene-v1-attempts.sqlite3")) as db:
                self.assertEqual(db.execute("SELECT state FROM steps").fetchone(), ("ATTEMPTED",))
            self.writes += 1
            if self.confirm_native_mutation:
                self.actual = parameters["elementPropertyValues"][0]["propertyValue"]["value"]
            return {"executionResults": [{"success": True}]}
        raise AssertionError(command)

    def plan(self):
        result = trace.run_trace(self.root, self.job, 19725)
        self.assertEqual(result["status"], "TDK_TRACE_READY_FOR_EXPLICIT_TEST_RUN")
        self.assertEqual(self.writes, 0)
        return result["preflightSha256"]

    def test_one_existing_writer_call_and_readback_preserve_pln_and_inventory(self):
        expected = self.plan()
        result = trace.run_trace(self.root, self.job, 19725, confirm=expected)
        self.assertEqual(result["status"], "TDK_TRACE_READBACK_PASS", result)
        self.assertEqual(result["nativeWrites"], 1)
        self.assertFalse(result["plnSaved"])
        self.assertEqual(self.source.read_bytes(), self.project.read_bytes())
        with closing(sqlite3.connect(self.job / "scene-v1-attempts.sqlite3")) as db:
            self.assertEqual(db.execute("SELECT state FROM scenes").fetchall(), [("PASS",)])
        with self.assertRaisesRegex(ValueError, "ATTEMPT_EXISTS_NO_REPLAY"):
            trace.run_trace(self.root, self.job, 19725, confirm=expected)
        self.assertEqual(self.writes, 1)

    def test_stale_preflight_stops_before_writing(self):
        expected = self.plan()
        self.actual = "external change"
        with self.assertRaisesRegex(ValueError, "NATIVE_PREFLIGHT_DRIFT"):
            trace.run_trace(self.root, self.job, 19725, confirm=expected)
        self.assertFalse((self.job / "trace-attempted.json").exists())
        self.assertEqual(self.writes, 0)

    def test_success_response_without_actual_property_change_is_unknown(self):
        self.confirm_native_mutation = False
        expected = self.plan()
        result = trace.run_trace(self.root, self.job, 19725, confirm=expected)
        self.assertEqual(result["status"], "STOPPED_RECONCILE_NO_AUTORETRY", result)
        self.assertEqual(result["nativeWrites"], 1)
        with closing(sqlite3.connect(self.job / "scene-v1-attempts.sqlite3")) as db:
            self.assertEqual(db.execute("SELECT state FROM steps").fetchall(), [("UNKNOWN_OUTCOME",)])


if __name__ == "__main__":
    unittest.main()
