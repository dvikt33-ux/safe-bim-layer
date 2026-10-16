"""Small offline geometry/guard test for APA BDD house generator.

Never connects to Archicad or writes a PLN. Run:
    python -m unittest discover -s tests -p 'test_bdd_house_builder.py'
"""
import importlib.util
from pathlib import Path
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "apa_bdd_house_native_builder.py"
spec = importlib.util.spec_from_file_location("apa_bdd_house_native_builder", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class HousePlanTests(unittest.TestCase):
    def test_pdf_pile_count_and_uniqueness(self):
        self.assertEqual(len(mod.PILES), 49)
        self.assertEqual(len(set(mod.PILES)), 49)

    def test_dimensions_chains(self):
        d = mod.DIMENSION_CHECK
        self.assertAlmostEqual(sum(d["xChain"]), 14.28)
        self.assertAlmostEqual(sum(d["yChain"]), 9.38)
        self.assertEqual(d["generalNotesConflict"], [14.18, 9.28])

    def test_plan_geometric_quantities(self):
        p = mod.plan()
        self.assertEqual(len(p["piles"]), 49)
        self.assertEqual(len(p["grillage"]), 17)
        self.assertEqual(len(p["exteriorWalls"]), 6)
        self.assertEqual(len(p["floorJoists"]), 48)
        self.assertEqual(len(p["floorPanels"]), 1)
        self.assertEqual(len(p["terracePlatforms"]), 2)
        self.assertEqual(len(p["roofEnvelope"]), 1)

    def test_source_read_fidelity(self):
        p = mod.plan()
        self.assertEqual(p["piles"][0]["coordinates"]["y"], 9.38)
        self.assertEqual(p["piles"][-1]["coordinates"]["y"], -1.5)
        self.assertTrue(all(x["height"] == 2.4 for x in p["piles"]))
        self.assertTrue(all(x["thickness"] == 0.25 for x in p["exteriorWalls"]))

    def test_no_implicit_write(self):
        self.assertTrue(mod.ORIGINAL.name.endswith("BDD дом .pln"))
        self.assertNotEqual(mod.ORIGINAL, mod.WORKING)
        self.assertTrue(mod.WORKING.name.endswith("2022.pln"))
        self.assertEqual(mod.PORT, 19727)


if __name__ == "__main__":
    unittest.main()
