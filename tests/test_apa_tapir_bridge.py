"""Verify both product branches against real Tapir schemas with a simulated transport."""
from __future__ import annotations

import asyncio
from hashlib import sha256
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from archicad_tapir_profile import BRIDGE_SCHEMA
from apa_control_mcp import server_for
from apa_tapir_bridge import TapirControl
import archicad_native_api as NATIVE
import archicad_tapir_catalog as CATALOG


class TapirBridgeTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.folder = Path(temp.name).resolve()
        self.profile = self.folder / "tapir-profile.json"
        self.native = []
        self.probes = []
        self.available = True
        self.responses = {}
        self.major = 30
        self.version = "2.0.0"
        self.configure()

    def configure(self, catalog=None):
        config = dict(schema=BRIDGE_SCHEMA, port=19725,
                      archicadVersion=self.major, tapirVersion=self.version)
        for key, suffix, contents in [
            ("project", ".pln", b"synthetic project"), ("backup", ".pln", b"synthetic project"),
            ("addon", ".apx", b"synthetic addon"),
        ]:
            path = self.folder / (key + suffix)
            if not path.exists():
                path.write_bytes(contents)
            config.update({key: str(path), key + "Sha256": sha256(path.read_bytes()).hexdigest()})
        if catalog is not None:
            config.update(catalog=str(catalog), catalogSha256=sha256(catalog.read_bytes()).hexdigest())
        self.config = config
        self.profile.write_text(json.dumps(config), encoding="utf-8")

    def http(self, request, timeout):
        self.assertEqual(request.full_url, "http://127.0.0.1:19725")
        self.assertEqual(request.method, "POST")
        payload = json.loads(request.data)
        command = payload["command"]
        parameters = payload["parameters"]
        if command == "API.IsAddOnCommandAvailable":
            self.probes.append(parameters["addOnCommandId"]["commandName"])
            result = {"available": self.available}
        elif command == "API.GetProductInfo":
            result = {"version": self.major, "buildNumber": 3001}
        else:
            self.assertEqual(command, "API.ExecuteAddOnCommand")
            addon = parameters["addOnCommandId"]
            self.assertEqual(addon["commandNamespace"], "TapirCommand")
            command = addon["commandName"]
            self.native.append((command, parameters["addOnCommandParameters"]))
            result = {"addOnCommandResponse": {
                "GetAddOnVersion": {"version": self.version},
                "GetProjectInfo": {"projectPath": self.config["project"], "isUntitled": False, "isTeamwork": False},
                "GetStories": {"firstStory": 0, "lastStory": 0, "actStory": 0, "skipNullFloor": False, "stories": []},
                "GetSelectedElements": {"elements": []},
                "GetElementsByType": {"elements": []},
                "GetSuspendGroupsMode": {"suspendGroups": False},
                **self.responses,
            }[command]}
        return io.BytesIO(json.dumps({"succeeded": True, "result": result}).encode())

    def test_29_and_30_use_same_entrypoint_and_wire_commands(self):
        for major, version, documented in ((29, "1.5.10", 262), (29, "2.0.0", 789), (30, "2.0.0", 789)):
            with self.subTest(major=major, tapir=version):
                self.major, self.version = major, version
                self.configure()
                with patch.object(NATIVE.urllib.request, "urlopen", side_effect=self.http):
                    bridge = TapirControl(self.profile)
                    status = bridge.perform("status")
                    self.assertEqual(status["runtime"]["tapirVersion"], version)
                    self.assertEqual(status["documentedCommands"], documented)
                    commands = [("GetStories", {}), ("GetSelectedElements", {}), ("GetElementsByType", {"elementType": "Wall"})]
                    if major == 30:
                        commands.append(("GetSuspendGroupsMode", {}))
                    for name, parameters in commands:
                        result = bridge.perform("read", name, parameters)
                        self.assertEqual(result["status"], "TAPIR_READ_VERIFIED", result)
                        self.assertEqual(result["parameters"], parameters)
                        self.assertIn((name, parameters), self.native)
                        self.assertIn(name, self.probes)

    def test_catalog_discovery_distinguishes_schema_registration_and_policy(self):
        with patch.object(NATIVE.urllib.request, "urlopen", side_effect=self.http):
            bridge = TapirControl(self.profile)
            page = bridge.perform("catalog")
            self.assertEqual(page["nextOffset"], len(page["commands"]))
            self.assertFalse(self.probes)
            self.available = False
            item = bridge.perform("catalog", "GetElementsByType", probe=True)
            self.assertEqual(item["commands"], [
                dict(name="GetElementsByType", effect="READ_ONLY", runtimeRegistered=False)])
            self.assertIn("ElementType", item["contract"]["commonSchemas"])
            result = bridge.perform("read", "GetElementsByType", {"elementType": "Wall"})
            self.assertEqual(result["reason"], "COMMAND_NOT_REGISTERED_IN_CURRENT_RUNTIME")
            self.assertNotIn("GetElementsByType", [name for name, _ in self.native])

    def test_unreviewed_invalid_and_unknown_requests_denied_before_dispatch(self):
        with patch.object(NATIVE.urllib.request, "urlopen", side_effect=self.http):
            bridge = TapirControl(self.profile)
            for command, reason in [
                ("UnknownCommand", "COMMAND_NOT_DISCOVERED"),
                ("CreateWalls", "SOURCE_REVIEWED_READ_ONLY_EFFECT_REQUIRED"),
                ("GenerateDocumentation", "SOURCE_REVIEWED_READ_ONLY_EFFECT_REQUIRED"),
                ("GetElementsByType", "TAPIR_SCHEMA_VALIDATION_FAILED"),
            ]:
                result = bridge.perform("read", command, {})
                self.assertEqual(result["reason"], reason, result)
                self.assertNotIn(command, [name for name, _ in self.native])
            self.assertFalse(self.probes)

    def test_schema_and_native_failure_are_reported_without_a_second_dispatch(self):
        self.responses["GetSelectedElements"] = {}
        with patch.object(NATIVE.urllib.request, "urlopen", side_effect=self.http):
            result = TapirControl(self.profile).perform("read", "GetSelectedElements")
        self.assertEqual(result["reason"], "TAPIR_SCHEMA_VALIDATION_FAILED")
        self.assertEqual(self.native.count(("GetSelectedElements", {})), 1)

    def test_wrong_project_and_missing_catalog_block_native_operation(self):
        self.responses["GetProjectInfo"] = {"projectPath": self.config["backup"],
                                            "isUntitled": False, "isTeamwork": False}
        with patch.object(NATIVE.urllib.request, "urlopen", side_effect=self.http):
            result = TapirControl(self.profile).perform("read", "GetStories")
        self.assertEqual(result["reason"], "APA_TAPIR_WRONG_OPEN_PROJECT")
        self.responses.clear()
        self.version = "2.1.0"
        self.configure()
        with patch.object(NATIVE.urllib.request, "urlopen", side_effect=self.http):
            bridge = TapirControl(self.profile)
            status = bridge.perform("status")
            self.assertEqual(status["runtime"]["tapirVersion"], self.version)
            self.assertEqual(status["catalogStatus"], "TAPIR_CATALOG_FOR_RUNTIME_REQUIRED")
            self.assertEqual(bridge.perform("read", "GetStories")["reason"], status["catalogStatus"])
        self.assertNotIn(("GetStories", {}), self.native)

    def test_add_existing_upstream_command_by_catalog_update_alone(self):
        raw = CATALOG.ROOT / "schemas/tapir-bridge/2.0.0.json"
        snapshot = json.loads(raw.read_bytes())["snapshot"]
        added = snapshot["commands"].pop("GetArchicadLocation")
        variant = self.folder / "extended-catalog.json"
        variant.write_text(json.dumps(CATALOG.record_for(snapshot, [30], {})), encoding="utf-8")
        self.configure(variant)
        with patch.object(NATIVE.urllib.request, "urlopen", side_effect=self.http):
            self.assertEqual(TapirControl(self.profile).perform("read", "GetArchicadLocation")["reason"],
                             "COMMAND_NOT_DISCOVERED")
        snapshot["commands"]["GetArchicadLocation"] = added
        proof = dict(source="reviewed upstream ApplicationCommands.cpp", sha256="a" * 64)
        variant.write_text(json.dumps(CATALOG.record_for(snapshot, [30], {"GetArchicadLocation": proof})),
                           encoding="utf-8")
        self.configure(variant)
        self.responses["GetArchicadLocation"] = {"archicadLocation": "C:/Archicad"}
        with patch.object(NATIVE.urllib.request, "urlopen", side_effect=self.http):
            bridge = TapirControl(self.profile)
            row = bridge.perform("read", "GetArchicadLocation")
            self.assertEqual(row["status"], "TAPIR_READ_VERIFIED", row)
            variant.write_text("{}", encoding="utf-8")
            self.assertEqual(bridge.perform("read", "GetArchicadLocation")["reason"], "TAPIR_CATALOG_HASH_DRIFT")
        with self.assertRaisesRegex(ValueError, "TAPIR_REVIEWED_COMMAND_NOT_READ_ELIGIBLE"):
            CATALOG.record_for(snapshot, [30], {"CreateWalls": proof})

    def test_mcp_tool_is_read_only_and_uses_bridge_without_per_command_handlers(self):
        server = server_for(tapir=TapirControl(self.profile))
        tools = asyncio.run(server.list_tools())
        self.assertEqual([tool.name for tool in tools], ["apa_tapir"])
        self.assertTrue(tools[0].annotations.read_only_hint)
        with patch.object(NATIVE.urllib.request, "urlopen", side_effect=self.http):
            result = asyncio.run(server.call_tool("apa_tapir", {"operation": "read", "command": "GetStories"}))
        self.assertEqual(result.structured_content["status"], "TAPIR_READ_VERIFIED")
