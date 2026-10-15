"""Offline cross-platform atomic APA user cache setup / no source writes."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bootstrap import setup
from graph import fingerprint
from gateway import retrieve
from sections import search


class BootstrapTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "source"
        self.docs = self.root / "docs/research/apa-results"
        folder = self.docs / "control"
        folder.mkdir(parents=True)
        self.plan_path = folder / "PROJECT_PLAN.json"
        self.plan = {"revision": 27,
                     "tasks":{"APA-P50.A01.S01":{
                         "id":"APA-P50.A01.S01","title":"Exact task", "status":"PARTIAL",
                         "depends_on":[], "inputs":["ART-DOC"], "evidence":[], "related":[]}},
                     "artifacts":{"ART-DOC":{
                         "id":"ART-DOC","uri":"docs/research/apa-results/control/evidence.md",
                         "kind":"DOCUMENT","verification":"READBACK_VERIFIED"}}}
        self.plan_path.write_text(json.dumps(self.plan), encoding="utf-8")
        (folder / "evidence.md").write_text("# Кровли\nКровельные узлы требуют проверки.\n", encoding="utf-8")
        self.cache = Path(self.tmp.name) / "outside-cache"

    def test_build_and_query_complete_local_cache(self):
        before = self.plan_path.read_bytes()
        r = setup(self.root, self.cache)
        self.assertEqual(r["status"], "LOCAL_DERIVED_CACHE_READY")
        self.assertEqual(r["task_count"], 1)
        self.assertTrue(Path(r["index"]).is_file())
        self.assertTrue(Path(r["sections"]).is_file())
        self.assertEqual(self.plan_path.read_bytes(), before)
        graph = json.loads(Path(r["index"]).read_text(encoding="utf-8"))
        result = retrieve(graph, self.plan, r["sections"], self.root,
                          "dvikt33-ux/safe-bim-layer", "кровли", source_class="PROJECT_CONTROL")
        self.assertEqual(result["status"], "OK")
        self.assertTrue(result["items"])
        self.assertEqual(result["items"][0]["artifact_ids"], ["ART-DOC"])

    def test_atomic_rebuild_after_plan_change(self):
        first = setup(self.root, self.cache)
        updated = json.loads(self.plan_path.read_text(encoding="utf-8"))
        updated["tasks"]["APA-P50.A01.S01"]["status"] = "READY"
        self.plan_path.write_text(json.dumps(updated), encoding="utf-8")
        second = setup(self.root, self.cache)
        ix = json.loads(Path(second["index"]).read_text(encoding="utf-8"))
        self.assertEqual(ix["plan_sha256"], fingerprint(updated))
        self.assertEqual(ix["tasks"]["APA-P50.A01.S01"]["status"], "READY")
        self.assertEqual(first["cache"], second["cache"])

    def test_never_put_derived_database_inside_checkout(self):
        with self.assertRaisesRegex(ValueError, "outside checkout"):
            setup(self.root, self.root / ".cache")

    def test_refuse_checkout_with_missing_plan(self):
        with self.assertRaisesRegex(ValueError, "Expected APA checkout"):
            setup(Path(self.tmp.name), self.cache)

    def test_mcp_command_operator_owned_paths(self):
        r = setup(self.root, self.cache)
        cmd = r["optional_local_mcp_command"]
        self.assertEqual(cmd[2], "--plan")
        self.assertEqual(cmd[-2], "--repo-root")
        self.assertTrue(all(x not in cmd for x in ("--allow-class", "ARCHIVED_SOURCE")))


if __name__ == "__main__":
    unittest.main()
