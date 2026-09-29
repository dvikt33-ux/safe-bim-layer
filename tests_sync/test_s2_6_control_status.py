from __future__ import annotations

import json
import unittest

from sync_bridge.control_status import CONTROL_STATUS_VERSION, build_control_status


class ControlStatusProjectionTests(unittest.TestCase):
    def live_status(self):
        return {
            "hostStatus": "S2_5_RUNTIME_BOOTSTRAP_IMPLEMENTED_NOT_LIVE_VERIFIED",
            "running": True,
            "dbPath": r"C:\\Users\\Admin\\AppData\\Local\\SafeBIM\\bridge.sqlite3",
            "pipeOpen": True,
            "credentialSource": "gh-cli",
            "archicad": {
                "instanceId": "archicad-default",
                "logicalProjectId": "live-local-c2f11559056504438f4e",
                "applicationVersion": "29",
                "applicationBuild": "3000",
                "applicationLanguage": "RUS",
                "projectPath": r"C:\\Users\\Admin\\Downloads\\Test_House_WriteSandbox.pln",
            },
            "bridge": {
                "running": True,
                "version": "2.5",
                "protocolVersion": 1,
                "needsAuth": False,
                "connections": {
                    "ARCHICAD": {"status": "CONNECTED", "detail": "1 instance"},
                    "BRIDGE": {"status": "CONNECTED", "detail": "named-pipe"},
                    "REMOTE": {"status": "CONNECTED", "detail": "mailbox"},
                    "AI": {"status": "OFFLINE", "detail": "not configured"},
                },
                "archicadWriteApi": False,
                "leaseState": "HELD",
                "ownership": "NAMED_MUTEX",
                "sqliteLeaseRole": "DIAGNOSTIC_ONLY",
            },
            "token": "MUST_NOT_LEAK",
            "userSid": "S-1-5-21-MUST_NOT_LEAK",
        }

    def test_live_projection_exposes_only_ui_status(self):
        source = self.live_status()
        result = build_control_status(source)

        self.assertEqual(result["schemaVersion"], CONTROL_STATUS_VERSION)
        self.assertTrue(result["host"]["running"])
        self.assertTrue(result["host"]["pipeOpen"])

        self.assertEqual(result["archicad"]["status"], "CONNECTED")
        self.assertEqual(result["archicad"]["instanceId"], "archicad-default")
        self.assertEqual(result["archicad"]["version"], "29")
        self.assertEqual(result["archicad"]["build"], "3000")
        self.assertEqual(result["archicad"]["language"], "RUS")

        self.assertEqual(result["bridge"]["status"], "CONNECTED")
        self.assertEqual(result["bridge"]["ownership"], "NAMED_MUTEX")
        self.assertEqual(result["bridge"]["leaseState"], "HELD")
        self.assertEqual(result["bridge"]["sqliteLeaseRole"], "DIAGNOSTIC_ONLY")
        self.assertFalse(result["bridge"]["archicadWriteApi"])

        self.assertEqual(result["github"]["status"], "CONNECTED")
        self.assertEqual(result["github"]["credentialSource"], "gh-cli")
        self.assertFalse(result["github"]["needsAuth"])
        self.assertEqual(result["ai"]["status"], "OFFLINE")
        self.assertEqual(
            result["project"]["logicalProjectId"],
            "live-local-c2f11559056504438f4e",
        )

    def test_projection_does_not_leak_local_paths_or_credentials(self):
        source = self.live_status()
        result = build_control_status(source)
        encoded = json.dumps(result, ensure_ascii=False, sort_keys=True)

        self.assertNotIn("bridge.sqlite3", encoded)
        self.assertNotIn("Test_House_WriteSandbox.pln", encoded)
        self.assertNotIn("MUST_NOT_LEAK", encoded)
        self.assertNotIn("S-1-5-21", encoded)
        self.assertNotIn("dbPath", encoded)
        self.assertNotIn("projectPath", encoded)
        self.assertNotIn("token", encoded)

    def test_projection_does_not_mutate_host_status(self):
        source = self.live_status()
        before = json.dumps(source, ensure_ascii=False, sort_keys=True)
        build_control_status(source)
        after = json.dumps(source, ensure_ascii=False, sort_keys=True)
        self.assertEqual(after, before)

    def test_stopped_or_partial_host_fails_closed_to_offline(self):
        result = build_control_status({
            "hostStatus": "STOPPED",
            "running": False,
            "pipeOpen": False,
            "credentialSource": "none",
            "archicad": None,
            "bridge": None,
        })

        self.assertFalse(result["host"]["running"])
        self.assertEqual(result["bridge"]["status"], "OFFLINE")
        self.assertEqual(result["archicad"]["status"], "OFFLINE")
        self.assertEqual(result["github"]["status"], "OFFLINE")
        self.assertEqual(result["ai"]["status"], "OFFLINE")
        self.assertIsNone(result["project"]["logicalProjectId"])

    def test_unknown_connection_value_does_not_escape_contract(self):
        source = self.live_status()
        source["bridge"]["connections"]["REMOTE"] = {
            "status": "MAGIC",
            "detail": 123,
        }

        result = build_control_status(source)

        self.assertEqual(result["github"]["status"], "CONNECTING")
        self.assertEqual(result["github"]["detail"], "")

    def test_non_dict_is_rejected(self):
        with self.assertRaises(TypeError):
            build_control_status(None)


if __name__ == "__main__":
    unittest.main()
