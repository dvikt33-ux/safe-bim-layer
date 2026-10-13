"""Official MCP SDK 2.3.0: one tiny safe tool, snapshot freshness, no writes."""
import asyncio
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from graph import build_index
from sections import build as build_sections
from mcp_adapter import SnapshotService, build_server


class MCPTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "repo"
        folder = self.root / "docs/research/apa-results/control"
        folder.mkdir(parents=True)
        (folder / "main.md").write_text("# Кровли\nКровельные примыкания исследовать точно.\n", encoding="utf-8")
        self.plan = {"revision": 3, "tasks": {
            "APA-P70.A02.S02": {
                "id":"APA-P70.A02.S02", "title":"Normative applicability",
                "status":"PARTIAL", "inputs":["ART-PLAN"], "evidence":[],
                "depends_on":[], "related":[], "owner":None, "claim_ref":None,
                "requires_approval":False}},
            "artifacts": {"ART-PLAN":{"id":"ART-PLAN", "kind":"DOCUMENT",
                                      "verification":"READBACK_VERIFIED",
                                      "uri":"docs/research/apa-results/control/main.md"}}}
        self.planpath = Path(self.tmp.name) / "plan.json"
        self.indexpath = Path(self.tmp.name) / "graph.json"
        self.secpath = Path(self.tmp.name) / "sections.sqlite"
        self.planpath.write_text(json.dumps(self.plan), encoding="utf-8")
        self.indexpath.write_text(json.dumps(build_index(self.plan)), encoding="utf-8")
        build_sections([self.root / "docs"], self.secpath)
        self.svc = SnapshotService(self.planpath, self.indexpath, self.secpath, self.root)

    def test_one_tool_only_and_no_model_access_to_paths(self):
        server = build_server(self.svc)
        tools = asyncio.run(server.list_tools())
        self.assertEqual([t.name for t in tools], ["apa_retrieve"])
        schema = tools[0].input_schema
        self.assertEqual(schema["type"], "object")
        self.assertNotIn("plan", schema["properties"])
        self.assertNotIn("index", schema["properties"])
        self.assertNotIn("repo_root", schema["properties"])
        self.assertEqual(schema["required"], ["query"])

    def test_real_mcp_call_returns_compact_exact_card(self):
        server = build_server(self.svc)
        r = asyncio.run(server.call_tool("apa_retrieve", {"query":"APA-P70.A02.S02"}))
        output = json.dumps(r.model_dump(mode="json"), ensure_ascii=False)
        self.assertIn("Normative applicability", output)
        self.assertIn("EXACT_TASK", output)
        self.assertNotIn("full normative", output)

    def test_untrusted_client_cannot_edit_status(self):
        snap = self.planpath.read_bytes()
        result = self.svc.query("APA-P70.A02.S02")
        self.assertEqual(result["items"][0]["status"], "PARTIAL")
        self.assertEqual(self.planpath.read_bytes(), snap)

    def test_freshness_check_rejects_changed_plan(self):
        modified = json.loads(self.planpath.read_text())
        modified["tasks"]["APA-P70.A02.S02"]["status"] = "IN_PROGRESS"
        self.planpath.write_text(json.dumps(modified), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "STALE_INDEX"):
            self.svc.query("APA-P70.A02.S02")

    def test_mcp_scope_normative_not_authority(self):
        r = self.svc.query("Кровли", mode="normative")
        self.assertEqual(r["status"], "NOT_VERIFIED_OFFICIAL_SOURCE")
        self.assertFalse(r["normative_authority"])
        self.assertTrue(all(x["source_legal_authority"] == "NOT_VERIFIED" for x in r["items"]))


if __name__ == "__main__":
    unittest.main()
