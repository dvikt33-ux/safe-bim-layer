"""P70.A03.S01: authored spatial/structure semantics, no fake load proof."""
import copy
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import archicad_project_accelerator as A
from test_archicad_semantic_brief import valid
from test_archicad_project_library_pack import specimen


def layout():
    return {
        "schemaVersion":"apa-authored-spatial-layout/1",
        "outline":{"xMin":0,"xMax":10,"yMin":0,"yMax":8},
        "rooms":[
            {"roomId":"living-01","storyId":"level-1",
             "rectangle":{"xMin":0,"xMax":5,"yMin":0,"yMax":8}},
            {"roomId":"bed-01","storyId":"level-2",
             "rectangle":{"xMin":0,"xMax":5,"yMin":0,"yMax":8}},
        ],
        "axes":[{"id":"axis-x-west","direction":"X","coordinate":0}],
        "bearingLines":[
            {"id":"wall-west-first","storyId":"level-1",
             "axisId":"axis-x-west","fromCoordinate":0,"toCoordinate":8,
             "wallThicknessMeters":0.3,"cseCandidateId":None},
            {"id":"wall-west-second","storyId":"level-2",
             "axisId":"axis-x-west","fromCoordinate":0,"toCoordinate":8,
             "wallThicknessMeters":0.3,"cseCandidateId":None},
        ],
        "loadPaths":[{"upperMemberId":"wall-west-second",
                      "lowerMemberId":"wall-west-first"}],
    }


def evaluate(doc=None,plp=None,geo=None):
    b=doc if doc is not None else valid()
    pack=plp if plp is not None else A.compile_project_library_pack(b,specimen())
    return A.compile_project_spatial_plan(b,pack,geo if geo is not None else layout())


class SpatialPlanTests(unittest.TestCase):
    def test_two_storey_author_supplied_geometry_is_linked_and_not_engineered(self):
        x=evaluate()
        self.assertEqual(x["status"],"AUTHORED_SPATIAL_GEOMETRY_CHECKED_ENGINEERING_PENDING")
        self.assertEqual(x["summary"]["roomCount"],2)
        self.assertEqual(x["summary"]["authoredBearingLineCount"],2)
        self.assertEqual(x["summary"]["alignedCandidateLoadPathCount"],1)
        self.assertTrue(x["loadPaths"][0]["geometryAligned"])
        self.assertFalse(x["loadPaths"][0]["forceTransferProved"])
        self.assertEqual(x["unresolvedWallCseMemberIds"],["wall-west-first","wall-west-second"])
        self.assertEqual(x["upperMembersWithoutLoadPath"],[])
        self.assertEqual(x["missingSlabCseStoryIds"],[])
        self.assertEqual(len(x["unresolvedJunctionConditions"]),3)
        self.assertFalse(x["bimEmissionAuthorized"])
        self.assertEqual(x["nativeBimGraph"],"EXISTING_ARCHICAD_BIM_GRAPH_ONLY")
        self.assertEqual(x["nativeWriteCalls"],0)

    def test_same_layout_is_valid_for_new_project_brief_without_ghost_floor(self):
        b=valid("GENERATE_FROM_ZERO")
        result=evaluate(doc=b)
        self.assertEqual(result["projectId"],b["projectId"])
        self.assertEqual({r["storyId"] for r in result["rooms"]},
                         {"level-1","level-2"})
        self.assertFalse(result["bimEmissionAuthorized"])

    def test_author_walls_cannot_appear_without_axes(self):
        x=layout();x["axes"]=[]
        with self.assertRaisesRegex(ValueError,"AXES_REQUIRED"):
            evaluate(geo=x)

    def test_plp_must_match_exact_project_identity(self):
        b=valid();other=valid();other["projectId"]="other-unique"
        pack=A.compile_project_library_pack(other,specimen())
        with self.assertRaisesRegex(ValueError,"PROJECT_PACK_AND_BRIEF"):
            evaluate(doc=b,plp=pack)

    def test_room_cannot_be_located_on_another_storey(self):
        x=layout();x["rooms"][0]["storyId"]="level-2"
        with self.assertRaisesRegex(ValueError,"ROOM_ID_OR_STORY"):
            evaluate(geo=x)

    def test_room_minimum_area_cannot_be_ignored(self):
        x=layout();x["rooms"][0]["rectangle"]["xMax"]=2
        with self.assertRaisesRegex(ValueError,"ROOM_MINIMUM_AREA"):
            evaluate(geo=x)

    def test_room_outside_footprint_rejected(self):
        x=layout();x["rooms"][0]["rectangle"]["xMax"]=15
        with self.assertRaisesRegex(ValueError,"ROOM_OUTSIDE_APPROVED"):
            evaluate(geo=x)

    def test_overlap_same_storey_rejected(self):
        b=valid();b["rooms"].append(
            {"id":"new-room","name":"Office","storyId":"level-1","minAreaM2":10})
        x=layout();x["rooms"].append({"roomId":"new-room","storyId":"level-1",
             "rectangle":{"xMin":3,"xMax":8,"yMin":0,"yMax":8}})
        with self.assertRaisesRegex(ValueError,"ROOM_POLYGONS_OVERLAP"):
            evaluate(doc=b,geo=x)

    def test_bearing_line_must_touch_authored_room_edge(self):
        x=layout();x["axes"][0]["coordinate"]=2
        with self.assertRaisesRegex(ValueError,"BEARING_LINE_NOT_ON_AUTHORED"):
            evaluate(geo=x)

    def test_wall_cse_cannot_impersonate_slab_cse(self):
        x=layout();x["bearingLines"][0]["cseCandidateId"]="rc-basic-slab-v1"
        with self.assertRaisesRegex(ValueError,"BEARING_WALL_CSE_ROLE_NOT_MATCHED"):
            evaluate(geo=x)

    def test_duplicate_collinear_bearing_lines_rejected(self):
        x=layout();x["bearingLines"].append({
            **x["bearingLines"][0],"id":"wall-duplicate",
            "fromCoordinate":1,"toCoordinate":7})
        with self.assertRaisesRegex(ValueError,"DUPLICATE_COLLINEAR"):
            evaluate(geo=x)

    def test_misaligned_force_transfer_is_rejected(self):
        x=layout()
        x["axes"].append({"id":"axis-x-east","direction":"X","coordinate":5})
        x["bearingLines"][1]["axisId"]="axis-x-east"
        with self.assertRaisesRegex(ValueError,"LOAD_PATH_GEOMETRIC_SUPPORT_NOT_ALIGNED"):
            evaluate(geo=x)

    def test_load_path_must_reach_lower_storey(self):
        x=layout()
        x["loadPaths"]=[{"upperMemberId":"wall-west-first",
                         "lowerMemberId":"wall-west-second"}]
        with self.assertRaisesRegex(ValueError,"LOAD_PATH_MUST_REACH"):
            evaluate(geo=x)

    def test_missing_upper_support_is_preserved_not_silently_claimed(self):
        x=layout();x["loadPaths"]=[]
        res=evaluate(geo=x)
        self.assertEqual(res["upperMembersWithoutLoadPath"],["wall-west-second"])
        self.assertFalse(res["engineeringApproved"])

    def test_false_approval_in_pack_blocks(self):
        pack=A.compile_project_library_pack(valid(),specimen())
        pack["selectedCseCandidates"][0]["engineeringApproved"]=True
        with self.assertRaisesRegex(ValueError,"UNTRUSTED_SELF_APPROVED"):
            evaluate(plp=pack)

    def test_no_new_graph_or_executor(self):
        x=evaluate()
        self.assertEqual(x["nativeBimGraph"],"EXISTING_ARCHICAD_BIM_GRAPH_ONLY")
        self.assertNotIn("operations",x)
        self.assertNotIn("schemaPath",x)
        self.assertEqual(x["nativeWriteCalls"],0)


    def test_explicit_xy_shift_preserves_rooms_axes_loadpaths_and_original(self):
        import archicad_semantic_spatial as S
        source=layout()
        relocated=S.relocate_authored_xy(source,40,40)
        self.assertEqual(source["outline"]["xMin"],0)
        self.assertEqual(relocated["outline"],
                         {"xMin":40.0,"xMax":50.0,"yMin":40.0,"yMax":48.0})
        self.assertEqual(relocated["rooms"][0]["rectangle"]["xMin"],40.0)
        self.assertEqual(relocated["rooms"][0]["rectangle"]["yMax"],48.0)
        self.assertEqual(relocated["axes"][0]["coordinate"],40.0)
        self.assertEqual(relocated["bearingLines"][0]["fromCoordinate"],40.0)
        self.assertEqual(relocated["bearingLines"][0]["toCoordinate"],48.0)
        self.assertEqual(relocated["loadPaths"],source["loadPaths"])
        result=evaluate(geo=relocated)
        self.assertEqual(result["summary"]["alignedCandidateLoadPathCount"],1)
        self.assertFalse(result["bimEmissionAuthorized"])

    def test_shift_y_axis_bearing_line_uses_x_displacement(self):
        import archicad_semantic_spatial as S
        x=layout()
        x["axes"].append({"id":"axis-y-south","direction":"Y","coordinate":0})
        x["bearingLines"].append({
            "id":"wall-south-first","storyId":"level-1",
            "axisId":"axis-y-south","fromCoordinate":0,"toCoordinate":5,
            "wallThicknessMeters":.3,"cseCandidateId":None})
        q=S.relocate_authored_xy(x,40,50)
        by_id={m["id"]:m for m in q["bearingLines"]}
        self.assertEqual(by_id["wall-south-first"]["fromCoordinate"],40.0)
        self.assertEqual(by_id["wall-south-first"]["toCoordinate"],45.0)
        self.assertEqual(q["axes"][1]["coordinate"],50.0)
        self.assertEqual(by_id["wall-west-first"]["fromCoordinate"],50.0)
        self.assertEqual(evaluate(geo=q)["summary"]["authoredBearingLineCount"],3)

    def test_bad_shift_is_fail_closed_and_never_authorizes_creation(self):
        import archicad_semantic_spatial as S
        for dx,dy in [(float("inf"),0),(float("nan"),0),
                      ("40",0),(1000001,0)]:
            with self.subTest(dx=dx):
                with self.assertRaises(ValueError):
                    S.relocate_authored_xy(layout(),dx,dy)
        bad=layout()
        bad["bearingLines"][0]["axisId"]="missing-axis"
        with self.assertRaisesRegex(ValueError,"TRANSLATION_UNKNOWN_BEARING_AXIS"):
            S.relocate_authored_xy(bad,40,40)


if __name__=="__main__":
    unittest.main()
