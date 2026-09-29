from __future__ import annotations

import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from sync_bridge.control_status_file import (
    CONTROL_STATUS_TRANSPORT_VERSION,
    ControlStatusFilePublisher,
    read_control_status_file,
    status_snapshot_is_fresh,
)


class ControlStatusFileTests(unittest.TestCase):
    def raw_host_status(self):
        return {
            "hostStatus": "S2_5_RUNTIME_BOOTSTRAP_IMPLEMENTED_NOT_LIVE_VERIFIED",
            "running": True,
            "dbPath": r"C:\Users\Admin\AppData\Local\SafeBIM\bridge.sqlite3",
            "pipeOpen": True,
            "credentialSource": "none",
            "archicad": {
                "instanceId": "archicad-default",
                "logicalProjectId": "live-local-c2f11559056504438f4e",
                "projectName": "Test_House_WriteSandbox",
                "projectPath": r"C:\Users\Admin\Downloads\Test_House_WriteSandbox.pln",
                "applicationVersion": "29",
                "applicationBuild": "3000",
                "applicationLanguage": "RUS",
            },
            "bridge": {
                "running": True,
                "version": "0.1.0",
                "protocolVersion": 1,
                "needsAuth": False,
                "connections": {
                    "ARCHICAD": {
                        "status": "CONNECTED",
                        "detail": "archicad-default",
                    },
                    "BRIDGE": {
                        "status": "CONNECTED",
                        "detail": "named-pipe",
                    },
                    "REMOTE": {
                        "status": "CONNECTING",
                        "detail": "",
                    },
                    "AI": {
                        "status": "CONNECTING",
                        "detail": "",
                    },
                },
                "archicadWriteApi": False,
                "leaseState": "HELD",
                "ownership": "NAMED_MUTEX",
                "sqliteLeaseRole": "DIAGNOSTIC_ONLY",
            },
            "token": "MUST_NOT_LEAK",
            "userSid": "S-1-5-21-MUST_NOT_LEAK",
        }

    def test_publish_sanitizes_raw_host_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "control-status.json"
            publisher = ControlStatusFilePublisher(
                path,
                publisher_id="publisher-a",
                clock_ms=lambda: 1_000,
            )

            result = publisher.publish(self.raw_host_status())
            loaded = read_control_status_file(path)

            self.assertEqual(result, loaded)
            self.assertEqual(
                loaded["transportVersion"],
                CONTROL_STATUS_TRANSPORT_VERSION,
            )
            self.assertEqual(
                loaded["status"]["project"]["name"],
                "Test_House_WriteSandbox",
            )

            encoded = json.dumps(loaded, ensure_ascii=False)
            self.assertNotIn("bridge.sqlite3", encoded)
            self.assertNotIn(".pln", encoded)
            self.assertNotIn(r"C:\Users", encoded)
            self.assertNotIn("MUST_NOT_LEAK", encoded)
            self.assertNotIn("projectPath", encoded)
            self.assertNotIn("dbPath", encoded)
            self.assertNotIn("userSid", encoded)
            self.assertNotIn('"token"', encoded)

    def test_sequence_increases_and_replace_leaves_no_temp_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "control-status.json"
            publisher = ControlStatusFilePublisher(
                path,
                publisher_id="publisher-a",
                clock_ms=lambda: 2_000,
            )

            first = publisher.publish(self.raw_host_status())
            second = publisher.publish(self.raw_host_status())

            self.assertEqual(first["sequence"], 1)
            self.assertEqual(second["sequence"], 2)
            self.assertEqual(publisher.sequence, 2)
            self.assertEqual(read_control_status_file(path)["sequence"], 2)
            self.assertEqual(
                list(root.glob(".control-status.json.*.tmp")),
                [],
            )

    def test_new_publisher_has_new_identity_and_new_sequence(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "control-status.json"

            first = ControlStatusFilePublisher(
                path,
                publisher_id="process-a",
                clock_ms=lambda: 1_000,
            ).publish(self.raw_host_status())

            second = ControlStatusFilePublisher(
                path,
                publisher_id="process-b",
                clock_ms=lambda: 2_000,
            ).publish(self.raw_host_status())

            self.assertEqual(first["publisherId"], "process-a")
            self.assertEqual(second["publisherId"], "process-b")
            self.assertEqual(first["sequence"], 1)
            self.assertEqual(second["sequence"], 1)

    def test_publish_does_not_mutate_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = self.raw_host_status()
            before = deepcopy(source)

            ControlStatusFilePublisher(
                Path(tmp) / "status.json",
                publisher_id="publisher-a",
                clock_ms=lambda: 1,
            ).publish(source)

            self.assertEqual(source, before)

    def test_reader_rejects_wrong_transport_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "status.json"
            publisher = ControlStatusFilePublisher(
                path,
                publisher_id="publisher-a",
                clock_ms=lambda: 1,
            )
            data = publisher.publish(self.raw_host_status())
            data["transportVersion"] = 999
            path.write_text(json.dumps(data), encoding="utf-8")

            with self.assertRaises(ValueError):
                read_control_status_file(path)

    def test_reader_rejects_malformed_envelope(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "status.json"
            path.write_text('{"transportVersion":1}', encoding="utf-8")

            with self.assertRaises(ValueError):
                read_control_status_file(path)

    def test_freshness_detects_live_and_stale_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            publisher = ControlStatusFilePublisher(
                Path(tmp) / "status.json",
                publisher_id="publisher-a",
                clock_ms=lambda: 10_000,
            )
            envelope = publisher.publish(self.raw_host_status())

            self.assertTrue(
                status_snapshot_is_fresh(
                    envelope,
                    now_ms=14_999,
                    max_age_ms=5_000,
                )
            )
            self.assertFalse(
                status_snapshot_is_fresh(
                    envelope,
                    now_ms=15_001,
                    max_age_ms=5_000,
                )
            )
            self.assertFalse(
                status_snapshot_is_fresh(
                    envelope,
                    now_ms=9_999,
                    max_age_ms=5_000,
                )
            )


if __name__ == "__main__":
    unittest.main()