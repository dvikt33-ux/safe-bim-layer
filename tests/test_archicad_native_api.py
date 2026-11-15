"""The Archicad wire contract is shared by reads and guarded writers."""
import io
import json
import unittest
from unittest.mock import patch
from urllib.error import URLError

import archicad_native_api as api


class NativeApiTests(unittest.TestCase):
    def test_official_and_addon_calls_use_the_same_wire_transport(self):
        responses = [
            {"succeeded": True, "result": {"version": 30, "buildNumber": 3001}},
            {"succeeded": True, "result": {"addOnCommandResponse": {"stories": []}}},
            {"succeeded": True, "result": {"addOnCommandResponse": {"version": "2.0.0"}}},
        ]
        with patch.object(api.urllib.request, "urlopen",
                          side_effect=[io.BytesIO(json.dumps(row).encode()) for row in responses]) as http:
            self.assertEqual(api.native_command(19725, "API.GetProductInfo", {})["version"], 30)
            self.assertEqual(api.native_command(19725, "GetStories", {}), {"stories": []})
            self.assertEqual(api.native_command(19725, "AddOn.TapirCommand.GetAddOnVersion", {}),
                             {"version": "2.0.0"})
        requests = [json.loads(c.args[0].data) for c in http.call_args_list]
        self.assertEqual(requests[0]["command"], "API.GetProductInfo")
        self.assertEqual([r["command"] for r in requests[1:]], ["API.ExecuteAddOnCommand"] * 2)
        self.assertEqual(requests[1]["parameters"]["addOnCommandId"],
                         {"commandNamespace": "TapirCommand", "commandName": "GetStories"})
        self.assertEqual([c.args[0].full_url for c in http.call_args_list], ["http://127.0.0.1:19725"] * 3)

    def test_error_details_are_structured_and_transport_is_never_retried(self):
        error = {"code": -1, "message": "unavailable"}
        envelope = io.BytesIO(json.dumps({"succeeded": False, "error": error}).encode())
        with patch.object(api.urllib.request, "urlopen", return_value=envelope) as http:
            with self.assertRaises(api.ArchicadAPIError) as rejected:
                api.tapir(19725, "GetStories")
            self.assertEqual(rejected.exception.code, "ARCHICAD_COMMAND_REJECTED")
            self.assertEqual(rejected.exception.detail, error)
            http.assert_called_once()
        with patch.object(api.urllib.request, "urlopen", side_effect=URLError("offline")) as http:
            with self.assertRaises(api.ArchicadAPIError) as unavailable:
                api.tapir(19725, "GetStories")
            self.assertEqual(unavailable.exception.code, "ARCHICAD_CONNECTION_FAILED")
            http.assert_called_once()
