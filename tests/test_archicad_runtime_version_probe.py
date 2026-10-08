"""Synthetic test suite: verify version inventory is read-only and fail-closed."""
import importlib.util
from pathlib import Path
import unittest

PATH = Path(__file__).resolve().parents[1] / "scripts" / "archicad_runtime_version_probe.py"
spec = importlib.util.spec_from_file_location("archicad_runtime_version_probe", PATH)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)

EXPECTED_PATH = r"C:\LocalAI\SafeBIM_Global_Library_Test_Projects\Тест MER .pln"
EXPECTED_NAME = "Тест MER "


class Types:
    def AddOnCommandId(self, namespace, command):
        if namespace != "TapirCommand":
            raise AssertionError("unexpected namespace")
        return command


class Commands:
    def __init__(self, *, build=5101, correct=True, missing_product=False):
        self.calls = []
        self.build = build
        self.correct = correct
        self.missing_product = missing_product

    def GetProductInfo(self):
        self.calls.append("GetProductInfo")
        if self.missing_product:
            raise AttributeError("official command not exposed")
        return ("29", self.build, "RUS")

    def ExecuteAddOnCommand(self, command, params):
        self.calls.append(command)
        if params != {}:
            raise AssertionError("commands must have empty read-only params")
        if command == "GetProjectInfo":
            return {
                "projectName": EXPECTED_NAME if self.correct else "Another",
                "projectPath": EXPECTED_PATH if self.correct else "C:\\Other.pln",
                "isUntitled": False, "isTeamwork": False,
            }
        if command == "GetAddOnVersion":
            return {"version": "1.5.10"}
        if command == "GetStories":
            return {"actStory": 0, "stories": [
                {"index": 0, "name": "1 этаж", "level": 0.0},
                {"index": 1, "name": "2 этаж", "level": 4.5},
            ]}
        raise AssertionError("unexpected command " + command)


class Connection:
    types = Types()

    def __init__(self, **kwargs):
        self.commands = Commands(**kwargs)


class VersionProbeTests(unittest.TestCase):
    def test_exact_product_and_addon_readback(self):
        conn = Connection()
        report = probe.inventory(
            conn, port=19723, expected_name=EXPECTED_NAME,
            expected_path=EXPECTED_PATH)
        self.assertEqual(report["status"], "READ_ONLY_VERSION_CHECK")
        self.assertEqual(report["archicadProduct"]["buildNumber"], 5101)
        self.assertTrue(report["buildMatchesUserScreenshot"])
        self.assertEqual(report["tapirAddonVersion"], "1.5.10")
        self.assertEqual(report["storiesCount"], 2)
        self.assertEqual(report["writeCommandsCalled"], 0)
        self.assertEqual(conn.commands.calls, [
            "GetProjectInfo", "GetProductInfo", "GetAddOnVersion", "GetStories"
        ])

    def test_nested_graphisoft_addon_response(self):
        conn = Connection()
        original = conn.commands.ExecuteAddOnCommand
        def wrapped(command, params):
            return {"result": {"addOnCommandResponse": original(command, params)}}
        conn.commands.ExecuteAddOnCommand = wrapped
        report = probe.inventory(
            conn, port=19723, expected_name=EXPECTED_NAME,
            expected_path=EXPECTED_PATH)
        self.assertEqual(report["status"], "READ_ONLY_VERSION_CHECK")
        self.assertEqual(report["tapirAddonVersion"], "1.5.10")

    def test_wrong_pln_is_rejected_before_addon_query(self):
        conn = Connection(correct=False)
        report = probe.inventory(conn, port=19723, expected_name=EXPECTED_NAME,
                                 expected_path=EXPECTED_PATH)
        self.assertEqual(report["status"], "WRONG_PROJECT")
        self.assertEqual(conn.commands.calls, ["GetProjectInfo"])

    def test_mismatching_product_build_is_reported(self):
        report = probe.inventory(
            Connection(build=5000), port=19723,
            expected_name=EXPECTED_NAME, expected_path=EXPECTED_PATH)
        self.assertFalse(report["buildMatchesUserScreenshot"])

    def test_unavailable_product_info_does_not_invent_build(self):
        report = probe.inventory(
            Connection(missing_product=True), port=19723,
            expected_name=EXPECTED_NAME, expected_path=EXPECTED_PATH)
        self.assertIsNone(report["buildMatchesUserScreenshot"])
        self.assertIsNone(report["archicadProduct"].get("version"))

    def test_arbitrary_tapir_api_calls_are_refused(self):
        conn = Connection()
        with self.assertRaisesRegex(ValueError, "refused"):
            probe.tapir_read(conn, "CreateWalls")
        self.assertEqual(conn.commands.calls, [])


if __name__ == "__main__":
    unittest.main()
