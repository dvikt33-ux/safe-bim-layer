from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from sync_bridge.control_status import build_control_status
from sync_bridge.host import BridgeHost, HOST_STATUS, HostConfig


class HostStatusSemanticsTests(unittest.TestCase):
    def test_host_status_is_stable_ready_contract(self):
        self.assertEqual(HOST_STATUS, "READY")

    def test_stopped_host_and_control_projection_report_ready_but_not_running(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            host = BridgeHost(
                HostConfig(
                    data_dir=root,
                    db_path=root / "bridge.sqlite3",
                ),
                transport=object(),
            )

            raw = host.status()
            snapshot = build_control_status(raw)

            self.assertEqual(raw["hostStatus"], "READY")
            self.assertFalse(raw["running"])
            self.assertFalse(raw["pipeOpen"])

            self.assertEqual(snapshot["host"]["status"], "READY")
            self.assertFalse(snapshot["host"]["running"])
            self.assertFalse(snapshot["host"]["pipeOpen"])

            self.assertEqual(snapshot["archicad"]["status"], "OFFLINE")
            self.assertEqual(snapshot["bridge"]["status"], "OFFLINE")


if __name__ == "__main__":
    unittest.main()