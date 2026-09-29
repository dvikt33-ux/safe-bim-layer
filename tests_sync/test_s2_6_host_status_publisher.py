from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from sync_bridge.control_status_file import read_control_status_file
from sync_bridge.host import BridgeHost, HostConfig
from sync_bridge.security import PeerIdentity


class FakePipe:
    def __init__(self):
        self.handle = 123
        self.closed = False

    def close(self):
        self.closed = True
        self.handle = None


class FakeTransport:
    def __init__(self):
        self.value = {
            "instanceId": "archicad-default",
            "logicalProjectId": "project-a",
            "projectName": "Project A",
            "applicationVersion": "29",
            "applicationBuild": "3000",
            "applicationLanguage": "RUS",
        }

    def binding(self):
        return dict(self.value)

    def call(self, command, params):
        raise AssertionError("context capture was not requested")


class BrokenPublisher:
    def publish(self, status):
        raise OSError("injected status write failure")


def _make_host(root: Path, *, status_publisher_factory=None):
    pipe = FakePipe()
    transport = FakeTransport()
    kwargs = {}
    if status_publisher_factory is not None:
        kwargs["status_publisher_factory"] = status_publisher_factory
    host = BridgeHost(
        HostConfig(
            data_dir=root,
            db_path=root / "bridge.sqlite3",
        ),
        identity=PeerIdentity("S-1-5-21-s26", "26"),
        token_provider=lambda: None,
        pipe_factory=lambda sid, session: pipe,
        transport=transport,
        monotonic=lambda: 0.0,
        **kwargs,
    )
    return host, pipe, transport


class AutomaticControlStatusPublicationTests(unittest.TestCase):
    def test_start_publishes_live_snapshot_and_close_publishes_offline(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            status_path = root / "control-status.json"
            host, pipe, _transport = _make_host(root)

            host.start()

            live = read_control_status_file(status_path)
            self.assertEqual(live["sequence"], 1)
            self.assertTrue(live["status"]["host"]["running"])
            self.assertTrue(live["status"]["host"]["pipeOpen"])
            self.assertEqual(live["status"]["archicad"]["status"], "CONNECTED")
            self.assertEqual(live["status"]["bridge"]["status"], "CONNECTED")
            self.assertEqual(live["status"]["project"]["name"], "Project A")

            publisher_id = live["publisherId"]

            host.close()

            stopped = read_control_status_file(status_path)
            self.assertEqual(stopped["publisherId"], publisher_id)
            self.assertEqual(stopped["sequence"], 2)
            self.assertFalse(stopped["status"]["host"]["running"])
            self.assertFalse(stopped["status"]["host"]["pipeOpen"])
            self.assertEqual(stopped["status"]["archicad"]["status"], "OFFLINE")
            self.assertEqual(stopped["status"]["bridge"]["status"], "OFFLINE")
            self.assertEqual(stopped["status"]["github"]["status"], "OFFLINE")
            self.assertEqual(stopped["status"]["ai"]["status"], "OFFLINE")
            self.assertIsNone(stopped["status"]["project"]["name"])
            self.assertTrue(pipe.closed)

    def test_direct_archicad_refresh_publishes_updated_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            status_path = root / "control-status.json"
            host, _pipe, transport = _make_host(root)

            try:
                host.start()
                first = read_control_status_file(status_path)
                self.assertEqual(first["sequence"], 1)

                transport.value = {
                    "instanceId": "archicad-default",
                    "logicalProjectId": "project-b",
                    "projectName": "Project B",
                    "applicationVersion": "29",
                    "applicationBuild": "3000",
                    "applicationLanguage": "RUS",
                }

                host.refresh_archicad()

                second = read_control_status_file(status_path)
                self.assertEqual(second["sequence"], 2)
                self.assertEqual(
                    second["status"]["project"]["logicalProjectId"],
                    "project-b",
                )
                self.assertEqual(second["status"]["project"]["name"], "Project B")
            finally:
                host.close()

    def test_step_publishes_post_tick_connection_state_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            status_path = root / "control-status.json"
            host, _pipe, _transport = _make_host(root)

            try:
                host.start()
                host._next_archicad_refresh = 100.0
                host._next_heartbeat = 100.0

                def fake_tick():
                    host.bridge.connections.set(
                        "REMOTE",
                        "CONNECTED",
                        "mailbox",
                    )
                    return {"status": "IDLE"}

                host.bridge.tick = fake_tick

                result = host.step()

                self.assertEqual(result["remote"], {"status": "IDLE"})
                snapshot = read_control_status_file(status_path)
                self.assertEqual(snapshot["sequence"], 2)
                self.assertEqual(
                    snapshot["status"]["github"]["status"],
                    "CONNECTED",
                )
                self.assertEqual(
                    snapshot["status"]["github"]["detail"],
                    "mailbox",
                )
            finally:
                host.close()

    def test_status_publish_failure_is_nonfatal_and_bridge_can_close(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            host, pipe, _transport = _make_host(
                root,
                status_publisher_factory=lambda path: BrokenPublisher(),
            )

            status = host.start()
            self.assertTrue(status["running"])
            self.assertTrue(host.running)

            refreshed = host.refresh_archicad()
            self.assertEqual(refreshed["status"], "ARCHICAD_CONNECTED")
            self.assertTrue(host.running)

            host.close()

            self.assertFalse(host.running)
            self.assertTrue(pipe.closed)
            self.assertIsNone(host.status_publisher)


if __name__ == "__main__":
    unittest.main()
