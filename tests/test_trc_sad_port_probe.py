"""Pure tests for the port-19727 read-only probe; no network or PLN usage."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import trc_sad_port_probe as P

PROJECT = {"projectName": "ТРЦ сад GP",
           "projectPath": r"C:\LocalAI\SafeBIM_Global_Library_Test_Projects\ТРЦ сад GP.pln",
           "isUntitled": False, "isTeamwork": False}
STORIES = {"stories": [
    {"index": 0, "floorId": 1, "level": 0, "height": 3},
    {"index": 1, "floorId": 2, "level": 3, "height": 3},
    {"index": 2, "floorId": 3, "level": 6, "height": 3}]}


class ProbeTests(unittest.TestCase):
    def setUp(self):
        self.spec = json.loads(P.PLAN.DEFAULT_SPEC.read_text(encoding="utf-8"))
        self.info, self.stories = copy.deepcopy(PROJECT), copy.deepcopy(STORIES)
        self.calls = []

    def read(self, command):
        self.calls.append(command)
        return copy.deepcopy({"GetProjectInfo": self.info, "GetStories": self.stories,
                              "GetAddOnVersion": {"version": "1.5.10"}}[command])

    def test_report_user_observed_mismatch_without_any_writes(self):
        report = P.inspect(self.read, self.spec)
        self.assertEqual(report["status"], "BLOCKED_STORY_ELEVATIONS_MISMATCH")
        self.assertEqual([r["story"] for r in report["discrepancies"]], ["2", "3", "-1"])
        self.assertEqual(report["actualStories"][1]["elevation"], 3)
        self.assertIsNone(report["nativeStoryBindings"])
        self.assertEqual(report["nativeWrites"], 0)
        self.assertFalse(report["plnChanged"])
        self.assertEqual(self.calls, ["GetProjectInfo", "GetAddOnVersion",
                                      "GetStories", "GetProjectInfo"])

    def test_wrong_directory_fails_before_stories(self):
        self.info["projectPath"] = r"C:\Other\ТРЦ сад GP.pln"
        self.assertEqual(P.inspect(self.read, self.spec)["status"], "BLOCKED_WRONG_PROJECT")
        self.assertEqual(self.calls, ["GetProjectInfo"])

    def test_wrong_name_fails_closed(self):
        self.info["projectName"] = "Other"
        self.assertEqual(P.inspect(self.read, self.spec)["status"], "BLOCKED_WRONG_PROJECT")

    def test_wrong_port_is_rejected_without_calls(self):
        with self.assertRaisesRegex(ValueError, "PORT_19727_ONLY"):
            P.inspect(self.read, self.spec, 19724)
        self.assertEqual(self.calls, [])

    def test_duplicate_native_story_index_refused(self):
        self.stories["stories"][2]["index"] = 1
        with self.assertRaisesRegex(ValueError, "INVALID_OR_DUPLICATE"):
            P.inspect(self.read, self.spec)

    def test_changed_project_identity_rejected(self):
        n = [0]
        def reader(cmd):
            d = self.read(cmd)
            if cmd == "GetProjectInfo":
                n[0] += 1
                if n[0] == 2:
                    d["projectName"] = "Switched"
            return d
        with self.assertRaisesRegex(ValueError, "PROJECT_CHANGED"):
            P.inspect(reader, self.spec)

    def test_valid_level_map_still_cannot_authorize_write(self):
        self.stories["stories"][1]["level"] = 6.3
        self.stories["stories"][2]["level"] = 12.6
        self.stories["stories"].insert(0, {"index": -1, "floorId": 0, "level": -4.5})
        r = P.inspect(self.read, self.spec)
        self.assertEqual(r["status"], "READ_ONLY_STORY_MAPPING_READY")
        self.assertEqual(r["nativeStoryBindings"]["3"]["elevation"], 12.6)
        self.assertEqual(r["nativeWrites"], 0)
        self.assertFalse(r["liveWriteAuthorized"])

    def test_main_writes_only_json_evidence(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "evidence.json"
            with patch.object(P, "tapir", side_effect=lambda port, cmd, params, timeout: self.read(cmd)):
                self.assertEqual(P.main(["--output", str(path)]), 2)
                result = json.loads(path.read_text(encoding="utf8"))
                self.assertEqual(result["status"], "BLOCKED_STORY_ELEVATIONS_MISMATCH")
                with self.assertRaises(FileExistsError):
                    P.main(["--output", str(path)])


if __name__ == "__main__":
    unittest.main()
