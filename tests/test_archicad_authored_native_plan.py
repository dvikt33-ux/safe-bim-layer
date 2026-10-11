"""S02 native BIM DAG from authored lines: synthetic read-only, no SceneWriter."""
from pathlib import Path
import copy
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import archicad_project_accelerator as A
from test_archicad_semantic_brief import valid
from test_archicad_project_library_pack import specimen,NativeGetOnly
from test_archicad_semantic_spatial import layout


HEIGHTS={"level-1":3.0,"level-2":3.0}


def sample():
    b=valid()
    native=NativeGetOnly()
    pack=A.compile_project_library_pack(b,specimen(),native)
    return b,pack,native


class AuthoredNativePlanTests(unittest.TestCase):
    def test_two_authored_walls_two_slabs_compile_into_same_bim_dag(self):
        b,pack,native=sample()
        native.calls.clear()
        out=A.compile_authored_native_candidate(b,pack,layout(),HEIGHTS,native)
        self.assertEqual(out["status"],"OFFLINE_EXISTING_BIM_GRAPH_COMPILED_NOT_AUTHORIZED")
        self.assertEqual(out["operationCount"],4)
        self.assertEqual(out["plannedNativeCommands"],{"CreateSlabs":2,"CreateWalls":2})
        self.assertEqual(len(out["executionOrder"]),4)
        self.assertEqual(out["schemaVersion"],"1.5.10")
        self.assertEqual(out["graphValidator"],"EXISTING_ARCHICAD_BIM_GRAPH_COMPILE_GRAPH")
        self.assertEqual(out["nativeWriter"],"EXISTING_SCENE_WRITER_NOT_CALLED")
        self.assertFalse(out["liveWriteAuthorized"])
        self.assertFalse(out["sceneReservationCreated"])
        self.assertFalse(out["plnChanged"])
        self.assertEqual(out["nativeWriteCalls"],0)
        self.assertEqual(out["authoredRoomIds"],["living-01","bed-01"])
        self.assertEqual(native.calls,[
            "GetProjectInfo","GetStories","GetProjectInfo",
            "GetAttributesByType","GetProjectInfo"])

    def test_native_indices_come_from_current_getstories_not_first_floor_label(self):
        b,pack,native=sample()
        out=A.compile_authored_native_candidate(b,pack,layout(),HEIGHTS,native)
        ops=out["graph"]["operations"]
        floors=[next(iter(op["params"].values()))[0]["floorIndex"] for op in ops]
        self.assertEqual(floors,[1,1,3,3])
        self.assertEqual([x["architecturalStoryId"] for x in out["storyBindings"]],
                         ["level-1","level-2"])

    def test_wall_coordinates_preserve_authored_continuous_axis(self):
        b,pack,native=sample()
        out=A.compile_authored_native_candidate(b,pack,layout(),HEIGHTS,native)
        w=[x for x in out["graph"]["operations"] if x["command"]=="CreateWalls"]
        self.assertEqual(len(w),2)
        for op in w:
            part=op["params"]["wallsData"][0]
            self.assertEqual(part["begCoordinate"],{"x":0.0,"y":0.0})
            self.assertEqual(part["endCoordinate"],{"x":0.0,"y":8.0})
            self.assertEqual(part["height"],3.0)
            self.assertEqual(part["thickness"],.3)
            self.assertEqual(part["structureType"],"Basic")

    def test_slabs_reuse_exact_native_bm_and_authored_footprint(self):
        b,pack,native=sample()
        out=A.compile_authored_native_candidate(b,pack,layout(),HEIGHTS,native)
        self.assertEqual(out["provisionalBasicSlabMaterialGuid"],
                         pack["selectedCseCandidates"][0]["native"]["guid"])
        slabs=[o["params"]["slabsData"][0] for o in out["graph"]["operations"]
               if o["command"]=="CreateSlabs"]
        self.assertEqual(len(slabs),2)
        for s in slabs:
            self.assertEqual(s["thickness"],.2)
            self.assertEqual(s["level"],0)
            self.assertEqual(s["referencePlaneLocation"],"Top")
            self.assertEqual(len(s["polygonCoordinates"]),4)

    def test_unverified_structure_cannot_gain_write_right_from_valid_graph(self):
        b,pack,native=sample()
        out=A.compile_authored_native_candidate(b,pack,layout(),HEIGHTS,native)
        self.assertEqual(len(out["unresolved"]["wallCse"]),2)
        self.assertEqual(len(out["unresolved"]["junctions"]),3)
        self.assertIn("STRUCTURAL_LOAD_PATH_UNVERIFIED",
                      out["unresolved"]["engineeringChecks"])
        self.assertFalse(out["liveWriteAuthorized"])

    def test_stale_story_mapping_blocks(self):
        b,pack,native=sample()
        pack["nativeStoryBindings"][0]["nativeIndex"]=0
        with self.assertRaisesRegex(ValueError,"PROJECT_STORY_MAPPING_CHANGED"):
            A.compile_authored_native_candidate(b,pack,layout(),HEIGHTS,native)

    def test_missing_or_mismatched_authored_height_rejected(self):
        b,pack,native=sample()
        with self.assertRaisesRegex(ValueError,"STORY_HEIGHTS_MUST_BE_AUTHORED"):
            A.compile_authored_native_candidate(b,pack,layout(),{},native)
        with self.assertRaisesRegex(ValueError,"STORY_HEIGHT_INCONSISTENT"):
            A.compile_authored_native_candidate(b,pack,layout(),
                                                {"level-1":2.8,"level-2":3},native)

    def test_wrong_file_is_fail_closed_before_inventory(self):
        b,pack,native=sample()
        native.calls.clear()
        def wrong(cmd,args):
            result=native(cmd,args)
            if cmd=="GetProjectInfo":
                result["projectPath"]=r"C:\temporary\wrong.bpn"
            return result
        with self.assertRaisesRegex(ValueError,"WRONG_ACTIVE_SINGLE_PLN"):
            A.compile_authored_native_candidate(b,pack,layout(),HEIGHTS,wrong)
        self.assertEqual(native.calls,["GetProjectInfo"])

    def test_material_guid_drift_is_blocking(self):
        b,pack,native=sample()
        pack["selectedCseCandidates"][0]["native"]["guid"]="11111111-1111-4111-8111-111111111111"
        with self.assertRaisesRegex(ValueError,"PROJECT_SLAB_MATERIAL_CHANGED"):
            A.compile_authored_native_candidate(b,pack,layout(),HEIGHTS,native)

    def test_unauthenticated_offline_pack_must_not_be_emitted(self):
        b=valid()
        pack=A.compile_project_library_pack(b,specimen())
        with self.assertRaisesRegex(ValueError,"PROJECT_NATIVE_CSE_BINDING_NOT_ESTABLISHED"):
            A.compile_authored_native_candidate(b,pack,layout(),HEIGHTS,NativeGetOnly())

    def test_authored_layout_geometry_is_required_not_silent_room_bays(self):
        b,pack,native=sample()
        wrong=layout()
        wrong["bearingLines"][0]["axisId"]="missing-axis"
        with self.assertRaisesRegex(ValueError,"UNKNOWN_OR_DUPLICATE_BEARING_LINE"):
            A.compile_authored_native_candidate(b,pack,wrong,HEIGHTS,native)


if __name__=="__main__":
    unittest.main()
