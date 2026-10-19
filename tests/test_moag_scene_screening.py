"""One-pass screening keeps scene exclusions source-backed."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "tools/moag_topology/scene_screening.py"
SPEC = importlib.util.spec_from_file_location("moag_scene_screening", MODULE)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)

class SceneScreeningTests(unittest.TestCase):
    def test_screening_is_source_linked_and_keeps_full_audit_separate(self):
        out = module.check()
        self.assertEqual(out["schema"], "APA-MOAG-SCENE-SCREENING-VALIDATION/1")
        self.assertEqual(out["screened_pages_in_package"], 58)
        self.assertEqual(out["chapters"], 18)
        self.assertEqual(out["scenes"], 27)
        self.assertEqual(out["character_location_events"], 51)
        self.assertTrue(out["full_page_audits_are_separate"])
        self.assertFalse(out["native_write_authorized"])

if __name__ == "__main__":
    unittest.main()
