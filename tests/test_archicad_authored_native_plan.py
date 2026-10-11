"""S02 native BIM DAG from authored lines: synthetic read-only, no SceneWriter."""
from pathlib import Path
import copy
import sys
import unittest
from unittest.mock import patch

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


    def _writer_fixture(self):
        import archicad_authored_native_plan as N
        b=valid()
        b["targetProjectPath"]=A.RUN.APPROVED_SCRATCH_PATH
        class ReadOnlyNative(NativeGetOnly):
            def __init__(self):
                super().__init__()
                self.refuse_writes=True
                self.inject_story=None
            def __call__(self, cmd, params):
                if cmd in ("CreateWalls","CreateSlabs","ModifySlabs",
                           "CreateColumns","CreateDoors","CreateWindows"):
                    raise AssertionError("NATIVE_WRITE_CALL_IN_READ_ONLY_PREFLIGHT")
                if cmd=="GetProjectInfo":
                    self.calls.append(cmd)
                    return {"projectPath":A.RUN.APPROVED_SCRATCH_PATH,
                            "projectName":"APA_Test_House_01",
                            "isUntitled":False,"isTeamwork":False}
                if cmd=="GetStories" and self.inject_story is not None:
                    result=super().__call__(cmd,params)
                    result["actStory"]=self.inject_story
                    return result
                if cmd=="GetAddOnVersion":
                    self.calls.append(cmd)
                    return {"version":"1.5.10"}
                if cmd=="GetAllElements":
                    self.calls.append(cmd)
                    return {"elements":[]}
                return super().__call__(cmd,params)
        native=ReadOnlyNative()
        pack=A.compile_project_library_pack(b,specimen(),native)
        compiled=A.compile_authored_native_candidate(b,pack,layout(),HEIGHTS,native)
        return N, native, compiled

    def test_existing_scene_writer_preflight_uses_authored_metrics_and_zero_writes(self):
        N, native, compiled=self._writer_fixture()
        preview_factory=N.make_read_only_scene_writer_preview_factory(compiled)
        preview=preview_factory(0,0,A.RUN.DEFAULT_SCENE_SCHEMA)
        self.assertEqual(preview["metrics"]["dimensionsMeters"],
                         {"width":10.0,"depth":8.0,"height":6.0})
        self.assertEqual(preview["metrics"]["elementCount"],4)
        self.assertEqual(preview["sourcePlanHash"],compiled["sourcePlanHash"])
        self.assertFalse(preview["liveWriteAuthorized"])
        native.calls.clear()
        with patch.object(A.RUN,"EXPECTED_PATH",A.RUN.APPROVED_SCRATCH_PATH), \
             patch.object(A.RUN,"EXPECTED_NAME","APA_Test_House_01"), \
             patch.object(A.RUN,"PORT",19726):
            writer=A.RUN.SceneWriter(
                native,Path("never-create-synthetic-journal.sqlite3"),
                preview_factory=preview_factory)
            outcome=writer.preflight(0,0)
        self.assertEqual(outcome["status"],"READY_FOR_EXPLICIT_TEST_RUN")
        self.assertEqual(outcome["metrics"]["dimensionsMeters"],
                         {"width":10.0,"depth":8.0,"height":6.0})
        self.assertEqual(outcome["nativeElementsInspected"],0)
        self.assertEqual(outcome["binding"]["storyIndex"],1)
        self.assertEqual(outcome["slabBasicMaterialGuid"],
                         compiled["provisionalBasicSlabMaterialGuid"])
        self.assertFalse(outcome["liveWriteAuthorized"])
        self.assertTrue(set(native.calls)<={
            "GetProjectInfo","GetStories","GetAddOnVersion",
            "GetAttributesByType","GetAllElements"})

    def test_read_only_factory_never_ignores_authored_anchor_or_schema(self):
        N, native, compiled=self._writer_fixture()
        factory=N.make_read_only_scene_writer_preview_factory(compiled)
        with self.assertRaisesRegex(ValueError,"SCENE_ANCHOR_DIFFERS"):
            factory(30,0,A.RUN.DEFAULT_SCENE_SCHEMA)
        with self.assertRaisesRegex(ValueError,"WRITER_SCHEMA_PATH_CHANGED"):
            factory(0,0,Path("not-approved-schema.json"))
        ok=factory(0,0,A.RUN.DEFAULT_SCENE_SCHEMA)
        ok["graph"]["operations"][0]["params"]["slabsData"][0]["thickness"]=.3
        again=factory(0,0,A.RUN.DEFAULT_SCENE_SCHEMA)
        self.assertEqual(again["graph"]["operations"][0]
                         ["params"]["slabsData"][0]["thickness"],.2)
        self.assertEqual(compiled["graph"]["operations"][0]
                         ["params"]["slabsData"][0]["thickness"],.2)

    def test_existing_writer_preflight_wrong_active_story_stops_without_write(self):
        N, native, compiled=self._writer_fixture()
        native.inject_story=0
        with patch.object(A.RUN,"EXPECTED_PATH",A.RUN.APPROVED_SCRATCH_PATH), \
             patch.object(A.RUN,"EXPECTED_NAME","APA_Test_House_01"):
            writer=A.RUN.SceneWriter(
                native,Path("never-create-synthetic-journal.sqlite3"),
                preview_factory=N.make_read_only_scene_writer_preview_factory(compiled))
            with self.assertRaisesRegex(ValueError,"STORY_MISMATCH"):
                writer.preflight(0,0)
        self.assertNotIn("GetAllElements",native.calls)

    def test_existing_writer_refuses_user_saved_copy_candidate(self):
        import archicad_authored_native_plan as N
        b,pack,native=sample()
        compiled=A.compile_authored_native_candidate(b,pack,layout(),HEIGHTS,native)
        compiled["nativeTargetProjectPath"]="C:/Users/owner/saved-evidence.pln"
        with self.assertRaisesRegex(ValueError,"WRITER_PREVIEW_ONLY_FOR_EXISTING_APPROVED"):
            N.make_read_only_scene_writer_preview_factory(compiled)


    def test_20_owner_observed_template_boxes_block_origin_but_clear_40_40(self):
        import archicad_authored_native_plan as N
        # The owner reported 16 Object and 4 Elevation at native Z = 0.
        # Bounding boxes below are exact user-returned XY readings; simulated
        # native APIs here do NOT establish the future live model inventory.
        raw=[
            (-4.87509,-.7,27.4,28),
            (7.12491,11.3,27.4,28),
            (22.7,26.87509,27.4,28),
            (-3.862057698,0,-.361429,.33),
            (27.4,28,22.7,27.00447),
            (27.4,28,10.7,15.00447),
            (27.4,28,-5.00447,-.7),
            (-3.862057698,0,-.361429,.33),
            (-4.36844,-.7,-6,-5.4),
            (7.63156,11.3,-6,-5.4),
            (22.7,26.36844,-6,-5.4),
            (-3.862057698,0,-.361429,.33),
            (-6,-5.4,22.7,26.84657),
            (-6,-5.4,10.7,14.84657),
            (-6,-5.4,-4.84657,-.7),
            (-3.862057698,0,-.361429,.33),
            (-1,23,27.4,28),
            (27.4,28,-1,23),
            (-1,23,-6,-5.4),
            (-6,-5.4,-1,23)
        ]
        ids=[{"elementId":{"guid":
                "00000000-0000-4000-8000-"+format(i+1,"012x")}}
             for i in range(20)]
        calls=[]
        def fake_get(cmd,params):
            calls.append(cmd)
            if cmd=="GetAllElements":
                return {"elements":ids}
            if cmd=="Get3DBoundingBoxes":
                batch=params["elements"]
                return {"boundingBoxes3D":[{
                    "boundingBox3D":{
                        "xMin":raw[int(x["elementId"]["guid"][-12:],16)-1][0],
                        "xMax":raw[int(x["elementId"]["guid"][-12:],16)-1][1],
                        "yMin":raw[int(x["elementId"]["guid"][-12:],16)-1][2],
                        "yMax":raw[int(x["elementId"]["guid"][-12:],16)-1][3],
                        "zMin":0,"zMax":0
                    }} for x in batch]}
            raise AssertionError("READ_ONLY_NATIVE_COMMANDS_ONLY")
        layout_shifted=N.SPATIAL.relocate_authored_xy(layout(),40,40)
        b,pack,native=sample()
        compiled=A.compile_authored_native_candidate(
            b,pack,layout_shifted,HEIGHTS,native)
        self.assertEqual(compiled["authoredOutline"],layout_shifted["outline"])
        slabs=[x["params"]["slabsData"][0] for x in compiled["graph"]["operations"]
               if x["command"]=="CreateSlabs"]
        self.assertTrue(all(x["polygonCoordinates"][0]=={"x":40.0,"y":40.0}
                            for x in slabs))
        envelope={**layout_shifted["outline"],"zMin":-.3,"zMax":6.3}
        accepted=A.RUN.scan_for_existing_geometry(fake_get,40,40,envelope)
        self.assertEqual(accepted["nativeElementsInspected"],20)
        self.assertEqual(accepted["volumetricBodiesChecked"],20)
        self.assertEqual(accepted["nonSpatialElementsVerified"],0)
        self.assertTrue(set(calls)<={"GetAllElements","Get3DBoundingBoxes"})
        with self.assertRaisesRegex(ValueError,"SPATIAL_COLLISION"):
            A.RUN.scan_for_existing_geometry(fake_get,0,0,{
                "xMin":0,"xMax":10,"yMin":0,"yMax":8,
                "zMin":-.3,"zMax":6.3})


if __name__=="__main__":
    unittest.main()
