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
    def test_actual_three_story_inventory_maps_only_two_authored_floors(self):
        b=valid()
        b["stories"][0].update({"existingNativeIndex":0,"existingFloorId":1})
        b["stories"][1].update({"existingNativeLabel":"",
                               "existingNativeIndex":1,"existingFloorId":2})
        class ThreeLevelNative(NativeGetOnly):
            def __call__(self,cmd,args):
                if cmd=="GetStories":
                    self.calls.append(cmd)
                    return {"actStory":0,"stories":[
                        {"index":0,"floorId":1,"name":"Первый Этаж",
                         "level":0,"height":3},
                        {"index":1,"floorId":2,"name":"",
                         "level":3,"height":3},
                        {"index":2,"floorId":3,"name":"",
                         "level":6,"height":3}]}
                return super().__call__(cmd,args)
        api=ThreeLevelNative()
        pack=A.compile_project_library_pack(b,specimen(),read_api=api)
        self.assertEqual(pack["status"],
                         "PROJECT_NATIVE_MATERIAL_RESOLVED_NOT_ENGINEER_APPROVED")
        out=A.compile_authored_native_candidate(b,pack,layout(),HEIGHTS,api)
        floors=[next(iter(x["params"].values()))[0]["floorIndex"]
                for x in out["graph"]["operations"]]
        self.assertEqual(floors,[0,0,1,1])
        self.assertEqual([x["nativeLabel"] for x in out["storyBindings"]],
                         ["Первый Этаж",""])
        self.assertEqual(out["provisionalBasicSlabMaterialGuid"],
                         pack["selectedCseCandidates"][0]["native"]["guid"])
        self.assertFalse(out["liveWriteAuthorized"])
        self.assertEqual(out["nativeWriteCalls"],0)

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


    def test_existing_writer_preview_denies_all_unapproved_open_pln_paths(self):
        import archicad_authored_native_plan as N
        b,pack,native=sample()
        c=A.compile_authored_native_candidate(b,pack,layout(),HEIGHTS,native)
        with self.assertRaisesRegex(ValueError,"WRITER_PREVIEW_ONLY_FOR_EXISTING_APPROVED"):
            N.as_existing_scene_writer_preview(c)

    def test_existing_writer_preview_exact_guard_and_authored_4_steps(self):
        import archicad_authored_native_plan as N
        b=valid()
        b["targetProjectPath"]=A.RUN.APPROVED_SCRATCH_PATH
        native=NativeGetOnly()
        def approved(cmd,params):
            result=native(cmd,params)
            if cmd=="GetProjectInfo":
                result["projectPath"]=A.RUN.APPROVED_SCRATCH_PATH
            return result
        pack=A.compile_project_library_pack(b,specimen(),approved)
        candidate=A.compile_authored_native_candidate(
            b,pack,layout(),HEIGHTS,approved)
        preview=N.as_existing_scene_writer_preview(candidate)
        self.assertEqual(preview["metrics"]["elementCount"],4)
        self.assertEqual(preview["storyBindings"][0]["label"],"Первый Этаж")
        self.assertEqual(preview["storyBindings"][0]["nativeIndex"],1)
        self.assertEqual(preview["storyBindings"][1]["nativeIndex"],3)
        self.assertEqual(preview["slabBasicMaterialName"],"Железобетон - Конструкционный")
        self.assertEqual(preview["envelope"]["zMin"],-.3)
        self.assertEqual(preview["envelope"]["zMax"],6.3)
        self.assertEqual(preview["schemaVersion"],"1.5.10")
        self.assertFalse(preview["liveWriteAuthorized"])
        self.assertFalse(preview["plnChanged"])
        self.assertTrue(set(native.calls)<={"GetProjectInfo","GetStories","GetAttributesByType"})

    def test_writer_preview_rejects_source_plan_changed_after_native_compilation(self):
        import archicad_authored_native_plan as N
        b=valid()
        b["targetProjectPath"]=A.RUN.APPROVED_SCRATCH_PATH
        def approved(cmd,params):
            x=NativeGetOnly()(cmd,params)
            if cmd=="GetProjectInfo":
                x["projectPath"]=A.RUN.APPROVED_SCRATCH_PATH
            return x
        pack=A.compile_project_library_pack(b,specimen(),approved)
        c=A.compile_authored_native_candidate(b,pack,layout(),HEIGHTS,approved)
        c["graph"]["operations"][0]["params"]["slabsData"][0]["thickness"]=.3
        with self.assertRaisesRegex(ValueError,"AUTHORED_OPERATION_GRAPH_DRIFT"):
            N.as_existing_scene_writer_preview(c)


if __name__=="__main__":
    unittest.main()
