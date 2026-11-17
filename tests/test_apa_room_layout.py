import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


def sample():
    return json.loads((ROOT / "examples/accelerator/two-room-layout.json").read_text(encoding="utf-8"))


class RoomLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from archicad_tapir_catalog import load_for_runtime

        cls.router, _ = load_for_runtime({}, {"archicadVersion": 30, "tapirVersion": "2.0.0"})

    def test_shared_wall_door_and_manual_zones_in_two_disjoint_regions(self):
        from apa_room_layout import compile_layout

        result = compile_layout(sample(), self.router)
        statements = result["graph"]["operations"]
        self.assertEqual(len(statements), 9)
        by_id = {item["id"]: item for item in statements}
        included = {item["id"]: item for item in result["inclusionGraph"]["operations"]}
        first = by_id["exp-zone-hall"]["params"]["zonesData"][0]
        second = included["accept-zone-hall"]["params"]["zonesData"][0]
        self.assertEqual(first["geometry"]["polygonCoordinates"][2], {"x": 2.59, "y": 3.24})
        self.assertEqual(second["geometry"]["polygonCoordinates"][2], {"x": 15.59, "y": 3.24})
        self.assertEqual(first["numberStr"], second["numberStr"])
        interior = by_id["exp-door-passage"]["params"]["doorsData"][0]
        self.assertEqual(interior["ownerWallId"]["guid"]["$createdGuid"], "exp-wall-part-1")
        self.assertEqual(interior["width"], 1.05)
        self.assertEqual(interior["centerOffset"], 1.425)
        self.assertEqual(result["roomFacts"]["hall"]["areaM2"], 8.3916)
        self.assertEqual(result["routes"]["living"], ["entry", "passage"])
        self.assertTrue(all(row["status"] == "DESIGN_MODULE_MATCH" for row in result["masonryChecks"]))
        self.assertTrue(all(name.startswith("exp-") for name in by_id))
        self.assertEqual(result["inclusionMode"], "USER_COPY_THEN_READBACK")
        self.assertEqual(result["copyTranslationMM"], [13000, 0])
        self.assertIn("exp-wall-part-1", result["roomDependencies"]["hall"]["walls"])
        self.assertTrue(result["executionPermission"] is False)

    def test_invalid_layouts_are_rejected_before_graph_execution(self):
        from apa_room_layout import compile_layout

        for change, reason in (
            (lambda d: d["originsMM"].update(acceptance=[0, 0]), "REGIONS_OVERLAP"),
            (lambda d: d["rooms"][0].update(minAreaM2=9), "ROOM_MINIMUM_AREA"),
            (lambda d: d["doors"].pop(), "CONNECTIONS"),
            (lambda d: d["doors"][1].update(fromFaceMM=250), "MINIMUM_PIER"),
            (lambda d: d["doors"][1].update(fromFaceMM=901), "MODULE_CONFLICT"),
            (lambda d: d["wall"].update(thicknessMM=121), "THICKNESS"),
            (lambda d: d["wall"].update(heightMM=True), "HEIGHT"),
            (lambda d: d.update(windows=[{}]), "WINDOWS_NOT_SUPPORTED"),
        ):
            with self.subTest(reason=reason):
                value = sample()
                change(value)
                with self.assertRaisesRegex(ValueError, reason):
                    compile_layout(value, self.router)

    def test_five_rooms_reuse_the_same_pipeline(self):
        from apa_room_layout import compile_layout

        value = sample()
        for i in range(3, 6):
            value["rooms"].append({"id": f"room-{i}", "name": f"Комната {i}", "widthMM": 2610, "minAreaM2": 8})
            value["doors"].append({"id": f"door-{i}", "from": "living" if i == 3 else f"room-{i-1}",
                                   "to": f"room-{i}", "fromFaceMM": 900, "widthMM": 1050, "heightMM": 2079})
        value["originsMM"]["acceptance"] = [26000, 0]
        result = compile_layout(value, self.router)
        self.assertEqual(len(result["graph"]["operations"]), 18)
        self.assertEqual(len(result["inclusionGraph"]["operations"]), 18)
        self.assertEqual(result["routes"]["room-5"], ["entry", "passage", "door-3", "door-4", "door-5"])
        self.assertEqual(result["roomFacts"]["room-5"]["areaM2"], 8.4564)


if __name__ == "__main__":
    unittest.main()
