"""Read-only coordinate tests use the published #171 facts and synthetic BREP."""
from __future__ import annotations

import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import apa_ac29_hotlink_batch_geometry as G


def guid(n):
    return "00000000-0000-4000-8000-" + str(n).zfill(12)


def vertices(x0, x1, y0=0, y1=5, z0=0, z1=3):
    return [[x, y, z] for x in (x0, x1) for y in (y0, y1)
            for z in (z0, z1)]


def element(n, kind, verts):
    return {"guid": guid(n), "type": kind,
            "bodies": [] if not verts else [{"vertices": verts}]}


class BatchCoordinateTests(unittest.TestCase):
    def test_real_published_one_shot_clearance_and_corrected_origin(self):
        proof = G.published_one_shot_coordinate_proof()
        self.assertEqual(proof["status"],
                         "PUBLISHED_BREP_ARITHMETIC_VERIFIED_NOT_SECOND_LIVE_RUN")
        self.assertAlmostEqual(proof["sourceLocalMinX"], 300, delta=0.00003)
        self.assertAlmostEqual(proof["hostMaxX"], 330.475, places=3)
        self.assertAlmostEqual(proof["previousClearanceMeters"], 316, places=3)
        self.assertAlmostEqual(proof["forTenMeterGapOriginX"], 40.475, places=3)
        self.assertAlmostEqual(proof["predictedClearanceMeters"], 10, places=6)
        self.assertNotAlmostEqual(proof["forTenMeterGapOriginX"], 346.475,
                                  delta=1)

    def test_published_coordinate_proof_matches_live_readback_arithmetic(self):
        import json
        fixture = json.loads((Path(__file__).resolve().parents[1] /
            "docs/evidence/apa-ac29-hotlink-batch-20261018/coordinate-proof.json"
        ).read_text(encoding="utf8"))
        expected = G.published_one_shot_coordinate_proof()
        self.assertEqual(fixture["nativeModelWrites"], 0)
        self.assertEqual(fixture["status"],
                         "READ_ONLY_PUBLISHED_EVIDENCE_REPRODUCED_BATCH_NOT_LIVE")
        self.assertAlmostEqual(fixture["derived"]["moduleLocalMinX"],
                               expected["sourceLocalMinX"], places=8)
        self.assertAlmostEqual(fixture["derived"]["hostMaxX"],
                               expected["hostMaxX"], places=8)
        self.assertAlmostEqual(
            fixture["correctedOriginalHost"]["targetOriginX"],
            expected["forTenMeterGapOriginX"], places=8)
        self.assertAlmostEqual(
            fixture["newBatchAfterAcceptedInstance"]["predictedGapMeters"], 10,
            places=8)
        self.assertGreater(
            fixture["newBatchAfterAcceptedInstance"]["firstOriginX"],
            fixture["correctedOriginalHost"]["targetOriginX"])

    def test_batch_spacing_uses_module_local_min_not_its_width(self):
        local = {"x": [300, 330.475], "y": [0, 18.595],
                 "z": [-0.2, 3]}
        occupied = [{"x": [0, 330.475], "y": [0, 30], "z": [-0.2, 3]},
                    {"x": [646.475, 676.95], "y": [0, 18.595],
                     "z": [-0.2, 3]}]
        origins, targets = G.batch_origins(
            local, occupied, {"x": 346.475, "y": 0, "z": 0}, 10, 3)
        self.assertEqual(len(origins), 3)
        self.assertEqual([round(o["x"], 3) for o in origins],
                         [386.95, 427.425, 467.9])
        self.assertAlmostEqual(targets[0]["x"][0] - 676.95, 10, places=5)
        self.assertAlmostEqual(targets[1]["x"][0] - targets[0]["x"][1], 10, places=5)
        self.assertTrue(all(not G.clash(t, existing)
                            for t in targets for existing in occupied))

    def test_source_local_box_recovered_from_real_placed_module(self):
        node, root = guid(10), guid(11)
        source_ids = [guid(12), guid(13)]
        received = []
        native = {"elements": [
            element(1, "Wall", vertices(0, 330.475)),
            element(11, "Hotlink", []),
            element(12, "Wall", vertices(646.475, 660)),
            element(13, "Slab", vertices(660, 676.95))
        ]}
        def api(command, params):
            self.assertEqual(command, "GetDetailsOfElements")
            received.append(params)
            ids = [x["elementId"]["guid"].lower() for x in params["elements"]]
            if ids == [root]:
                return {"detailsOfElements": [{
                    "type": "Hotlink", "floorIndex": 0,
                    "details": {"hotlinkType": "Module",
                                "hotlinkNodeId": {"guid": node},
                                "origin": {"x": 346.475, "y": 0, "z": 0},
                                "rotationAngle": 0, "mirrored": False,
                                "floorDifference": 0, "skipNested": False,
                                "suspendFixAngle": False,
                                "ignoreTopFloorLinks": True,
                                "relinkWallOpenings": True,
                                "adjustLevelDiffs": True}}]}
            result = []
            for id_ in ids:
                typ = {"1": "Wall", "12": "Wall", "13": "Slab"}
                kind = next(e["type"] for e in native["elements"]
                            if e["guid"] == id_)
                result.append({"type": kind, "floorIndex": 0,
                               "hotlinkId": {"guid": root} if id_ in source_ids else None,
                               "details": {}})
            return {"detailsOfElements": result}
        obj = G.placed_prototype(
            api, native, node, root, {"x": 346.475, "y": 0, "z": 0})
        self.assertEqual(obj["ownedCount"], 2)
        self.assertEqual(obj["typeHistogram"], {"Wall": 1, "Slab": 1})
        self.assertAlmostEqual(obj["sourceLocalBounds"]["x"][0], 300, places=5)
        p = G.planned_batch(obj, 2, 10)
        self.assertEqual(p["status"], "SOURCE_BREP_COORDINATE_PLAN_PASS_NO_WRITES")
        self.assertEqual(len(p["origins"]), 2)
        self.assertEqual(p["sourceOwnedCount"], 2)
        self.assertTrue(received)

    def test_invalid_native_vertices_or_nan_are_rejected(self):
        for v in ([[0, 0, 0], [math.nan, 1, 0]], [], [[1, 2]]):
            with self.assertRaisesRegex(ValueError, "BREP_VERTICES"):
                G.bounds(v)

    def test_reject_unbounded_count_negative_gap_and_empty_source(self):
        local = {"x": [300, 330], "y": [0, 5], "z": [0, 3]}
        boxes = [{"x": [0, 30], "y": [0, 5], "z": [0, 3]}]
        for count, gap in [(0, 10), (33, 10), (2, -1),
                           (2, math.inf), (True, 10)]:
            with self.assertRaisesRegex(ValueError, "BOUNDED_BATCH"):
                G.batch_origins(local, boxes, {"x": 0, "y": 0, "z": 0},
                                gap, count)
        with self.assertRaisesRegex(ValueError, "SPATIAL_AABB"):
            G.batch_origins(local, [None], {"x": 0, "y": 0, "z": 0}, 5, 2)

    def test_native_bounds_excludes_nonspatial_roots(self):
        rows = [{"guid": guid(1), "type": "Hotlink", "bodies": []},
                element(2, "Wall", vertices(-3, 20)),
                element(3, "Door", [])]
        box = G.world_boxes({"elements": rows})
        self.assertIsNone(box[guid(1)])
        self.assertIsNone(box[guid(3)])
        self.assertEqual(box[guid(2)]["x"], [-3, 20])

    def test_invalid_rotation_fails_closed_through_existing_verifier(self):
        node, root = guid(1), guid(2)
        def api(command, params):
            return {"detailsOfElements": [{
                "type": "Hotlink", "floorIndex": 0,
                "details": {"hotlinkType": "Module",
                            "hotlinkNodeId": {"guid": node},
                            "origin": {"x": 10, "y": 0, "z": 0},
                            "rotationAngle": 1.57,
                            "mirrored": False}}]}
        with self.assertRaisesRegex(ValueError, "ROOT_NODE_OR_TRANSFORM"):
            G.placed_prototype(api, {
                "elements": [element(2, "Hotlink", [])]},
                node, root, {"x": 10, "y": 0, "z": 0})


if __name__ == "__main__":
    unittest.main()
