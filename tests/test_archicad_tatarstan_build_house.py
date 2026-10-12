"""Fast offline contracts for building a *separate* native Tatarstan test shell."""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import apa_tatarstan_build_house as B
import apa_tatarstan_readonly_snapshot as R


MATERIAL = "63db2ce9-903d-45c0-b93c-b3c604c77394"


def box(x0=40, x1=50, y0=40, y1=48, z0=0, z1=7):
    return {"vertices": [
        {"x": x, "y": y, "z": z}
        for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)
    ]}


class FakeApi:
    def __init__(self, *, native_collision=False, wrong_path=False):
        self.native_collision = native_collision
        self.wrong_path = wrong_path
        self.called = []
        self.ids = [
            B.OLD_WALL, B.OLD_SLAB, B.OLD_ROOF,
            *[f"00000000-0000-0000-0000-{i:012x}" for i in range(104)]
        ]

    def __call__(self, name, params=None, timeout=600):
        self.called.append(name)
        if name == "GetProjectInfo":
            return {"projectPath": R.EXPECTED_PATH if not self.wrong_path
                    else r"C:\WRONG.pln",
                    "projectName": R.EXPECTED_NAME + " ",
                    "isUntitled": False, "isTeamwork": False}
        if name == "GetAddOnVersion":
            return {"version": R.EXPECTED_VERSION}
        if name == "GetStories":
            return {"stories": [
                {"index": 0, "level": 0}, {"index": 1, "level": 3},
                {"index": 2, "level": 6}]}
        if name == "GetAllElements":
            return {"elements": [
                {"elementId": {"guid": guid}} for guid in self.ids
            ]}
        if name == "GetModelDumpV1":
            return {"bodies": [
                box(112, 122, 39, 51) if self.native_collision
                else box(40, 50, 40, 48)
            ]}
        if name == "GetDetailsOfElements":
            guid = params["elements"][0]["elementId"]["guid"].lower()
            if guid == B.OLD_WALL:
                return {"detailsOfElements": [{
                    "type": "Wall", "floorIndex": 0,
                    "details": {"structureType": "Basic",
                        "buildingMaterialId": {"guid": MATERIAL},
                        "begCoordinate": {"x": 50, "y": 40}}
                }]}
            if guid == B.OLD_SLAB:
                return {"detailsOfElements": [{
                    "type": "Slab", "floorIndex": 0,
                    "details": {"structureType": "Basic", "thickness": .2,
                                "buildingMaterialId": {"guid": MATERIAL}}
                }]}
            if guid == B.OLD_ROOF:
                return {"detailsOfElements": [{
                    "type": "Roof", "floorIndex": 1,
                    "details": {"structureType": "Basic",
                                "roofClass": "SinglePlane",
                                "buildingMaterialId": {"guid": MATERIAL}}
                }]}
        raise AssertionError(f"Unexpected Fake API call: {name}")


class TatarstanHouseTests(unittest.TestCase):
    def test_scene_has_exactly_14_native_building_elements(self):
        ops = B.make_plan(MATERIAL)
        self.assertEqual(len(ops), 14)
        self.assertEqual(Counter(x["type"] for x in ops),
                         {"Wall": 10, "Slab": 2, "Roof": 2})
        self.assertTrue(all(x["command"] in B.WRITES for x in ops))
        self.assertTrue(all(x["type"] != "Morph" for x in ops))

    def test_story_levels_and_slab_absolute_z(self):
        ops = B.make_plan(MATERIAL)
        self.assertEqual(
            [(x["floor"], x["params"]["slabsData"][0]["level"])
             for x in ops if x["type"] == "Slab"],
            [(0, 0.0), (1, 3.0)]
        )
        self.assertEqual([x["floor"] for x in ops if x["type"] == "Roof"], [2, 2])
        self.assertEqual(
            {x["params"]["wallsData"][0]["zCoordinate"]
             for x in ops if x["type"] == "Wall"}, {0.0}
        )

    def test_gable_roof_rises_inward_and_has_35_degree_slope(self):
        ops = [x for x in B.make_plan(MATERIAL) if x["type"] == "Roof"]
        west, east = [x["params"]["roofsData"][0] for x in ops]
        self.assertAlmostEqual(west["angle"], B.PITCH)
        self.assertEqual(west["pivotLine"]["begCoordinate"], B.xy(112, 51))
        self.assertEqual(west["pivotLine"]["endCoordinate"], B.xy(112, 39))
        self.assertEqual(east["pivotLine"]["begCoordinate"], B.xy(122, 39))
        self.assertEqual(east["pivotLine"]["endCoordinate"], B.xy(122, 51))
        self.assertAlmostEqual(6 + 5 * __import__("math").tan(B.PITCH),
                               9.501037691, places=4)

    def test_real_original_binding_is_used_for_every_explicit_material(self):
        ops = B.make_plan(MATERIAL)
        for item in ops:
            if item["type"] != "Slab":
                data = next(iter(item["params"].values()))[0]
                self.assertEqual(data["buildingMaterialId"]["guid"], MATERIAL)

    def test_source_binding_and_107_old_guids_pass(self):
        api = FakeApi()
        plan = B.prepare(api)
        self.assertEqual(len(plan["baseline"]), 107)
        self.assertEqual(plan["material_guid"], MATERIAL)
        self.assertEqual(plan["existing_native_bodies_inspected"], 1)
        self.assertFalse(any(n.startswith("Create") for n in api.called))
        self.assertFalse(any(n.startswith("Modify") for n in api.called))

    def test_wrong_pln_never_writes(self):
        api = FakeApi(wrong_path=True)
        with self.assertRaisesRegex(RuntimeError, "WRONG_PROJECT"):
            B.prepare(api)
        self.assertEqual(api.called, ["GetProjectInfo"])

    def test_native_body_at_new_house_blocks_before_write(self):
        api = FakeApi(native_collision=True)
        with self.assertRaisesRegex(RuntimeError, "INTERSECTS_NATIVE_BODY"):
            B.prepare(api)
        self.assertFalse(any(n in B.WRITES for n in api.called))

    def test_invalid_native_vertices_block(self):
        x = box()
        x["vertices"][0]["x"] = 1e35
        with self.assertRaisesRegex(RuntimeError, "UNVERIFIABLE_NATIVE_BODY"):
            B.check_native_clearance({"bodies": [x]})

    def test_correct_bbox_vs_site(self):
        valid = {"xMin": 40, "xMax": 92, "yMin": 39, "yMax": 62,
                 "zMin": 0, "zMax": 8}
        collide = dict(valid, xMin=112, xMax=122)
        self.assertFalse(B.aabb_overlap(valid))
        self.assertTrue(B.aabb_overlap(collide))

    def test_explicit_save_and_slab_modify_result_contract(self):
        B.assert_response_success({"success": True}, "SaveProject")
        B.assert_modify_success({"executionResults": [{"success": True}]})
        with self.assertRaisesRegex(RuntimeError, "WRITE_RESULT_NOT_SUCCESS"):
            B.assert_response_success({"success": False}, "SaveProject")
        with self.assertRaisesRegex(RuntimeError, "SLAB_MODIFY_NOT_SUCCESS"):
            B.assert_modify_success({"executionResults": [{"success": False}]})

    def test_previous_attempt_marker_blocks_without_any_api_calls(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            (directory / "write_started.json").write_text("existing")
            api = FakeApi()
            with self.assertRaisesRegex(RuntimeError, "ALREADY_ATTEMPTED"):
                B.execute(api, out_dir=directory, source_pln=R.EXPECTED_PATH)
            self.assertEqual(api.called, [])

    def test_readonly_preview_has_no_mutation(self):
        api = FakeApi()
        B.prepare(api)
        self.assertFalse(set(api.called).intersection(B.WRITES))


if __name__ == "__main__":
    unittest.main()
