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
        self.assertEqual(interior["centerOffset"], 1.545)
        partition = by_id["exp-wall-part-1"]["params"]["wallsData"][0]
        self.assertEqual((partition["begCoordinate"]["y"], partition["endCoordinate"]["y"]), (-.12, 3.36))
        self.assertAlmostEqual(partition["begCoordinate"]["y"] + interior["centerOffset"], 1.425)
        self.assertEqual([j["kind"] for j in result["wallJunctions"]["experiment"]], ["L"] * 4 + ["T"] * 2)
        self.assertEqual(result["roomFacts"]["hall"]["areaM2"], 8.3916)
        self.assertEqual(result["routes"]["living"], ["entry", "passage"])
        self.assertTrue(all(row["status"] == "DESIGN_MODULE_MATCH" for row in result["masonryChecks"]))
        self.assertTrue(all(name.startswith("exp-") for name in by_id))
        self.assertEqual(result["inclusionMode"], "USER_COPY_THEN_READBACK")
        self.assertEqual(result["copyTranslationMM"], [13000, 0])
        self.assertIn("exp-wall-part-1", result["roomDependencies"]["hall"]["walls"])
        self.assertTrue(result["executionPermission"] is False)

    def test_wall_junction_far_faces_vary_with_angle_thickness_and_role(self):
        from apa_room_layout import wall_paths

        thicknesses = {"a": 100, "b": 200}
        for kind, runs, roles in (
            ("L", {"a": (0, 0, 1000, 0), "b": (0, 0, 1000, 1000)}, ("start", "start")),
            ("T", {"a": (-1000, 0, 1000, 0), "b": (-1000, -1000, 0, 0)}, ("through", "end")),
            ("X", {"a": (-1000, 0, 1000, 0), "b": (-1000, -1000, 1000, 1000)}, ("through", "through")),
        ):
            with self.subTest(kind=kind):
                corrected, nodes = wall_paths(runs, thicknesses, [(kind, "a", roles[0], "b", roles[1])])
                self.assertEqual(nodes[0]["pointMM"], [0, 0])
                if kind == "L":
                    self.assertAlmostEqual(corrected["a"][0], -100 * 2 ** .5)
                    self.assertEqual(corrected["b"][:2], (-50, -50))
                elif kind == "T":
                    self.assertEqual(corrected["a"], runs["a"])
                    self.assertEqual(corrected["b"][2:], (50, 50))
                else:
                    self.assertEqual(corrected, runs)
        with self.assertRaisesRegex(ValueError, "THROUGH_WALL_TOO_SHORT"):
            wall_paths({"a": (-20, 0, 20, 0), "b": (0, -1000, 0, 1000)}, thicknesses,
                       [("X", "a", "through", "b", "through")])

    def test_wall_brep_checks_gap_protrusion_double_body_and_material_priority(self):
        from apa_ac30_project import wall_system_geometry
        from tests.test_apa_ac30_native import wall_body

        walls = {
            "a": {"begCoordinate": {"x": -.1, "y": 0}, "endCoordinate": {"x": 1, "y": 0}, "thickness": .2},
            "b": {"begCoordinate": {"x": 0, "y": -.1}, "endCoordinate": {"x": 0, "y": 1}, "thickness": .2},
        }
        joints = [{"kind": "L", "walls": ["a", "b"], "pointMM": [0, 0]}]

        def evaluate(ymin, xmax, priority):
            model = {
                "a": {"guid": "a", "bodies": [wall_body((-.1, -.1, 0, xmax, .1, 2.7))]},
                "b": {"guid": "b", "bodies": [wall_body((-.1, ymin, 0, .1, 1, 2.7))]},
            }
            return wall_system_geometry(walls, model, joints, priority, 2.7)

        strong = {"a": 700, "b": 500}
        self.assertEqual(evaluate(.1, 1, strong)["joints"][0]["higherPriorityWall"], "a")
        for ymin, xmax, priority, error in (
            (.12, 1, strong, "BREP_GAP"),
            (.1, 1.02, strong, "BREP_PROTRUSION"),
            (-.1, 1, strong, "DOUBLE_BODY"),
            (.1, 1, {"a": 500, "b": 700}, "MATERIAL_PRIORITY_DRIFT"),
        ):
            with self.subTest(error=error), self.assertRaisesRegex(ValueError, error):
                evaluate(ymin, xmax, priority)

    def test_crossing_walls_accept_two_bodies_of_lower_priority(self):
        from apa_ac30_project import wall_system_geometry
        from tests.test_apa_ac30_native import wall_body

        walls = {
            'x': dict(begCoordinate={'x': -2, 'y': 0}, endCoordinate={'x': 2, 'y': 0}, thickness=.24),
            'y': dict(begCoordinate={'x': 0, 'y': -2}, endCoordinate={'x': 0, 'y': 2}, thickness=.12),
        }
        model = {
            'x': dict(guid='x', bodies=[wall_body((-2, -.12, 0, 2, .12, 2.772))]),
            'y': dict(guid='y', bodies=[wall_body((-.06, -2, 0, .06, -.12, 2.772)),
                                       wall_body((-.06, .12, 0, .06, 2, 2.772))]),
        }
        joints = [dict(kind='X', walls=['x', 'y'], pointMM=[0, 0])]
        proof = wall_system_geometry(walls, model, joints, {'x': 700, 'y': 500}, 2.772)
        self.assertEqual(proof['joints'][0]['higherPriorityWall'], 'x')
        self.assertAlmostEqual(proof['joints'][0]['sharedAreaM2'], 2 * .12 * 2.772)

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

    def test_layout_asks_for_room_purpose_when_name_cannot_be_classified(self):
        from apa_room_layout import compile_layout, unanswered

        value = sample()
        value["rooms"][0]["name"] = "Помещение А"
        questions = unanswered(value)
        self.assertEqual(set(questions), {"rooms[0].purpose"})
        value["rooms"][0]["purpose"] = "транзитное помещение"
        self.assertEqual(unanswered(value), {})
        result = compile_layout(value, self.router)
        self.assertEqual(result["roomFacts"]["hall"]["purpose"], "circulation")

    def test_five_rooms_reuse_the_same_pipeline(self):
        from apa_room_layout import compile_layout

        value = sample()
        for i in range(3, 6):
            value["rooms"].append({"id": f"room-{i}", "name": f"Спальня {i}", "widthMM": 2610, "minAreaM2": 8})
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
