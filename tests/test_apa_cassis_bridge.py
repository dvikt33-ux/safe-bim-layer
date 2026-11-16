"""Guardrails for the bounded APA -> Cassis Grasshopper bridge."""
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest

from apa_cassis_bridge import CassisBridge, INTENT_SCHEMA, SCHEMA


RECT = "66bd8530-bc2d-4d45-a49b-bfeabac6e92f"
X = "1f438aec-c32b-4cfa-afbe-0a1954afd705"
Y = "c397b299-ec09-4c64-aa4c-a19bb940e140"


class FakeCassis:
    def __init__(self, source):
        self.path = str(source)
        self.open = True
        self.modified = False
        self.values = {X: 4000, Y: 3000}
        self.calls = []
        self.rogue = False
        self.reopen_lag_reads = 0
        self.pending_reopen_reads = 0

    def __call__(self, root):
        self.calls.append(("open-client", root is None))
        return self

    def tool(self, name, arguments=None):
        args = arguments or {}
        self.calls.append((name, dict(args)))
        if name == "getdocumentinfo":
            if self.pending_reopen_reads:
                self.pending_reopen_reads -= 1
                return dict(ok=True, open=False, mod=False, n=0)
            return dict(ok=True, open=self.open, path=self.path,
                        mod=self.modified, n=3)
        if name == "getsystemhealth":
            return {"OverallStatus": "Healthy"}
        if name == "get_componentcount":
            return dict(success=True, components=1, parameters=2,
                        groups=0, connections=2)
        if name == "get_allcomponents":
            rows = [
                dict(id=RECT, typeName="CurveComponents.Component_Rectangle_OBSOLETE"),
                dict(id=X, typeName="Grasshopper.Kernel.Special.GH_NumberSlider"),
                dict(id=Y, typeName="Grasshopper.Kernel.Special.GH_NumberSlider"),
            ]
            if self.rogue:
                rows.append(dict(id="archicad", typeName="ArchicadSlabCreator"))
            return dict(success=True, count=len(rows), components=rows)
        if name == "getallconnections":
            return dict(success=True, count=2, connections=[
                dict(SourceComponentId=X, TargetComponentId=RECT, TargetInputIndex=1),
                dict(SourceComponentId=Y, TargetComponentId=RECT, TargetInputIndex=2)])
        if name == "get_component_output":
            perimeter = 2 * (self.values[X] + self.values[Y])
            value = ({"isClosed": True, "length": perimeter}
                     if args["outputIndex"] == 0 else perimeter)
            return {"Output": {"Branches": [{"Items": [{"Value": value}]}]}}
        if name == "set_component_value":
            self.values[args["componentId"]] = float(args["value"])
            self.modified = True
            return dict(success=True)
        if name == "forcedocumentsolution":
            return dict(success=True)
        if name == "savedocument":
            Path(args["filePath"]).write_bytes(b"mock ghx output")
            self.path = str(args["filePath"])
            self.modified = False
            return dict(ok=True, file=Path(self.path).name)
        if name == "closedocument":
            self.open = False
            return dict(ok=True)
        if name == "loaddocument":
            self.path = str(args["filePath"])
            self.open = True
            self.modified = False
            self.pending_reopen_reads = self.reopen_lag_reads
            return dict(ok=True)
        raise AssertionError("Unreviewed tool: " + name)


class CassisBridgeTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name).resolve()
        self.source = self.root / "APA_Cassis_Rectangle_4x3m.ghx"
        self.source.write_bytes(b"source ghx")
        self.profile = self.root / "profile.json"
        self.profile.write_text(json.dumps({
            "schema": SCHEMA,
            "testRoot": str(self.root),
            "document": str(self.source),
            "documentSha256": sha256(self.source.read_bytes()).hexdigest(),
            "rectangleId": RECT,
            "widthSliderId": X,
            "heightSliderId": Y,
            "writeEnabled": True,
        }), encoding="utf-8")
        self.fake = FakeCassis(self.source)
        self.bridge = CassisBridge(self.profile, client_factory=self.fake)

    def test_read_tool_bound_and_no_native(self):
        intent = {"schemaVersion": INTENT_SCHEMA,
                  "tool": "get_componentcount", "arguments": {}}
        result = self.bridge.run("gh-read", intent)
        self.assertEqual(result["status"], "GH_READ_VERIFIED")
        self.assertEqual(result["result"]["connections"], 2)
        self.assertEqual(result["nativeWrites"], 0)
        self.assertFalse(any(name in {"savedocument", "set_component_value"}
                             for name, _ in self.fake.calls))

    def test_denies_unreviewed_tools_and_arguments(self):
        for tool, args in [
            ("removecomponents", {}),
            ("addcomponent", {"type": "Archicad Slab"}),
            ("get_component_output", {"componentId": "rogue", "outputIndex": 0}),
            ("get_componentcount", {"a": 1}),
        ]:
            with self.subTest(tool=tool):
                with self.assertRaises(ValueError):
                    self.bridge.run("gh-read", {
                        "schemaVersion": INTENT_SCHEMA, "tool": tool,
                        "arguments": args,
                    })

    def test_wrong_document_blocks_read_and_write(self):
        self.fake.path = str(self.root / "unrelated.ghx")
        with self.assertRaisesRegex(ValueError, "GH_WRONG_ACTIVE_DOCUMENT"):
            self.bridge.run("gh-read", {
                "schemaVersion": INTENT_SCHEMA, "tool": "get_componentcount",
                "arguments": {},
            })
        with self.assertRaisesRegex(ValueError, "GH_WRONG_ACTIVE_DOCUMENT"):
            self.bridge.run("gh-rectangle", self.intent())
        self.assertFalse(any(name == "set_component_value" for name, _ in self.fake.calls))

    def intent(self):
        return {"schemaVersion": INTENT_SCHEMA, "widthMm": 5000,
                "heightMm": 3000,
                "outputFile": str(self.root / "APA_Cassis_Rectangle_5x3m_test.ghx")}

    def test_rogue_archicad_component_blocks_before_write(self):
        self.fake.rogue = True
        with self.assertRaisesRegex(ValueError, "GH_GRAPH_OWNERSHIP_DRIFT"):
            self.bridge.run("gh-rectangle", self.intent())
        self.assertFalse(any(name == "set_component_value" for name, _ in self.fake.calls))

    def test_sha_and_dimensions_block_before_write(self):
        self.source.write_bytes(b"changed externally")
        with self.assertRaisesRegex(ValueError, "GH_DOCUMENT_SHA_OR_DIRTY_STATE"):
            self.bridge.run("gh-rectangle", self.intent())
        self.assertFalse(any(name == "set_component_value" for name, _ in self.fake.calls))
        intent = self.intent()
        intent["widthMm"] = 1
        with self.assertRaisesRegex(ValueError, "GH_RECTANGLE_DIMENSIONS_INVALID"):
            self.bridge.run("gh-rectangle", intent)

    def test_save_and_separate_verify_without_replay(self):
        intent = self.intent()
        saved = self.bridge.run("gh-rectangle", intent)
        self.assertEqual(saved["status"], "GH_RECTANGLE_SAVED_PENDING_REOPEN")
        self.assertEqual(saved["afterPerimeterMm"], 16_000)
        self.assertTrue(Path(saved["output"]).exists())
        self.assertEqual(self.fake.open, True)
        with self.assertRaisesRegex(ValueError, "GH_OUTPUT_SCOPE_OR_EXISTS"):
            self.bridge.run("gh-rectangle", intent)
        verify = {"schemaVersion": INTENT_SCHEMA,
                  "outputFile": saved["output"],
                  "outputSha256": saved["outputSha256"],
                  "expectedPerimeterMm": saved["afterPerimeterMm"]}
        result = self.bridge.run("gh-verify", verify)
        self.assertEqual(result["status"], "GH_RECTANGLE_REOPEN_VERIFIED")
        self.assertEqual(result["afterPerimeterMm"], 16_000)
        self.assertIn(("open-client", True), self.fake.calls)
        self.assertEqual(result["nativeWrites"], 0)
        self.assertEqual(sha256(Path(saved["output"]).read_bytes()).hexdigest(),
                         saved["outputSha256"])


    def test_reopen_waits_for_observable_document_without_rewriting(self):
        self.fake.reopen_lag_reads = 2
        saved = self.bridge.run("gh-rectangle", self.intent())
        self.assertEqual(saved["status"], "GH_RECTANGLE_SAVED_PENDING_REOPEN")
        result = self.bridge.run("gh-verify", {
            "schemaVersion": INTENT_SCHEMA,
            "outputFile": saved["output"],
            "outputSha256": saved["outputSha256"],
            "expectedPerimeterMm": 16000,
        })
        self.assertEqual(result["status"], "GH_RECTANGLE_REOPEN_VERIFIED")
        self.assertEqual(sum(1 for n, _ in self.fake.calls if n == "savedocument"), 1)


if __name__ == "__main__":
    unittest.main()
