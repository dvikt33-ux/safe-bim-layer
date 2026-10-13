"""Tests for bounded local Markdown section retrieval and exact byte provenance."""
import hashlib
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sections import build, search, normalized_query


class SectionSearchTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "norm.md").write_text(
            "# Требования к кровле\nПроверяются кровельные примыкания по применимой редакции норм.\n"
            "## Кровля\nВода с кровли отводится проектным решением.\n"
            "## Санузлы\nКоличество санузлов зависит от задания и расчётов.\n", encoding="utf-8")
        (self.root / "geometry.md").write_text(
            "# Wall roof junction\nWall roof geometry must preserve host relations.\n"
            "## Materials\nComposite layers use materials and surfaces.\n", encoding="utf-8")
        self.db = self.root / "search.sqlite"
        self.meta = build([self.root], self.db)

    def test_indexes_all_sections(self):
        self.assertEqual(self.meta["files"], 2)
        self.assertGreaterEqual(self.meta["sections"], 4)

    def test_russian_search_bounded(self):
        res = search(self.db, "кровли", limit=2, max_snippet=90)
        self.assertEqual(res["status"], "OK")
        self.assertGreaterEqual(res["count"], 1)
        self.assertTrue(any("кровли" in x["excerpt"] for x in res["results"]))
        self.assertTrue(all(len(x["excerpt"]) <= 90 for x in res["results"]))
        self.assertTrue(all(len(x["source_sha256"]) == 64 for x in res["results"]))

    def test_two_doc_query(self):
        res = search(self.db, "roof", limit=5)
        self.assertGreaterEqual(res["count"], 1)

    def test_scope_excludes_unwanted_document_class(self):
        selected = search(self.db, "кровли", selected_class="OTHER_DOCUMENT")
        self.assertGreaterEqual(selected["count"], 1)
        self.assertEqual({r["source_class"] for r in selected["results"]}, {"OTHER_DOCUMENT"})
        meta_only = search(self.db, "кровли", selected_class="RESEARCH_RUN")
        self.assertEqual(meta_only["count"], 0)

    def test_unknown_source_class_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "Invalid source class"):
            search(self.db, "кровли", selected_class="LEGAL_NORM_APPROVED")

    def test_sqlite_fts_query_is_escaped(self):
        q = normalized_query('"; DROP TABLE sections; --')
        self.assertNotIn("DROP TABLE sections;", q)
        res = search(self.db, "кровли", limit=3)
        self.assertEqual(res["status"], "OK")

    def test_stale_index_detected_after_source_mutation(self):
        fp = self.root / "norm.md"
        fp.write_text(fp.read_text(encoding="utf-8") + "\nНовые данные.", encoding="utf-8")
        res = search(self.db, "кровли", limit=3)
        self.assertEqual(res["status"], "STALE_INDEX")

    def test_new_relevant_doc_not_silently_missed(self):
        (self.root / "new.md").write_text("# Новая кровля\\nНовая редакция кровли.", encoding="utf-8")
        result = search(self.db, "кровли", limit=3)
        self.assertEqual(result["status"], "STALE_INDEX")
        self.assertEqual(result["results"], [])

    def test_unrelated_nonhit_doc_modification_invalidates_index(self):
        (self.root / "geometry.md").write_text(
            "# Wall join\\nTotally different content.", encoding="utf-8")
        result = search(self.db, "кровли", limit=3)
        self.assertEqual(result["status"], "STALE_INDEX")

    def test_removed_document_invalidates_index(self):
        (self.root / "geometry.md").unlink()
        result = search(self.db, "кровли", limit=3)
        self.assertEqual(result["status"], "STALE_INDEX")

    def test_current_manifest_passed(self):
        result = search(self.db, "кровли", limit=3)
        self.assertEqual(result["source_manifest_check"], "PATH_SIZE_MTIME_MATCH")

    def test_no_overwrite_existing_database(self):
        with self.assertRaisesRegex(ValueError, "overwrite"):
            build([self.root], self.db)

    def test_validates_budget(self):
        with self.assertRaisesRegex(ValueError, "Bounded"):
            search(self.db, "roof", limit=500)
        with self.assertRaisesRegex(ValueError, "Bounded"):
            search(self.db, "roof", max_snippet=5000)

    def test_empty_query_rejected(self):
        with self.assertRaisesRegex(ValueError, "1-15"):
            search(self.db, "")


if __name__ == "__main__":
    unittest.main()
