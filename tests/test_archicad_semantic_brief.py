"""APA-P70.A02.S01 read-only semantic brief and GetStories mapping gates."""
import copy
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import archicad_project_accelerator as A


def valid(mode="ADAPT_EXISTING"):
    return {
        "schemaVersion":"apa-semantic-project-brief/1",
        "projectId":"sample-2026",
        "mode":mode,
        "units":"meters",
        "site":{"siteId":"parcel-a","region":"Россия"},
        "stories":[
            {"id":"level-1","label":"1 этаж","level":0.0,
             "existingNativeLabel":"Первый Этаж"},
            {"id":"level-2","label":"2 этаж","level":3.0,
             "existingNativeLabel":"Второй Этаж"},
        ],
        "rooms":[
            {"id":"living-01","name":"Гостиная","storyId":"level-1","minAreaM2":20.0},
            {"id":"bed-01","name":"Спальня","storyId":"level-2","minAreaM2":12.0},
        ],
        "constraints":[
            {"id":"stairs-source","text":"Лестничная связь между этажами",
             "evidenceStatus":"UNVERIFIED"},
        ],
        **({"targetProjectPath":r"C:\test\Project_01.pln"}
           if mode=="ADAPT_EXISTING" else {}),
    }


class SyntheticStories:
    def __init__(self, indices=(1,3), names=("Первый Этаж","Второй Этаж")):
        self.calls=[]
        self.indices=indices
        self.names=names
    def __call__(self,cmd,args):
        self.calls.append(cmd)
        if cmd=="GetProjectInfo":
            return {"projectPath":r"C:\test\Project_01.pln",
                    "isUntitled":False,"isTeamwork":False}
        if cmd=="GetStories":
            return {"actStory":self.indices[0], "stories":[
                {"index":self.indices[0],"floorId":2,"level":0.0,
                 "name":self.names[0]},
                {"index":self.indices[1],"floorId":4,"level":3.0,
                 "name":self.names[1]}]}
        raise AssertionError("non-read-only command: "+cmd)


class SemanticBriefTests(unittest.TestCase):
    def test_generate_mode_offline_never_guesses_native_index(self):
        new=valid("GENERATE_FROM_ZERO")
        res=A.compile_project_brief(new)
        self.assertEqual(res["nativeResolution"],"NEEDS_NEW_PROJECT_SETUP")
        self.assertEqual(res["nativeStoryBindings"],[])
        self.assertEqual(res["mode"],"GENERATE_FROM_ZERO")
        self.assertEqual(res["stories"][0]["label"],"1 этаж")
        self.assertEqual(res["stories"][0]["level"],0.0)
        self.assertEqual(res["nativeWriteCalls"],0)

    def test_adapt_existing_offline_is_not_assumed_ready(self):
        data=A.compile_project_brief(valid())
        self.assertEqual(data["nativeResolution"],"NEEDS_STORY_RESOLUTION")
        self.assertEqual(data["nativeStoryBindings"],[])

    def test_adapt_existing_getstories_nonzero_native_indices(self):
        api=SyntheticStories()
        data=A.compile_project_brief(valid(),read_api=api)
        self.assertEqual(data["nativeResolution"],"READY_FOR_ATTRIBUTE_RESOLUTION")
        self.assertEqual([x["nativeIndex"] for x in data["nativeStoryBindings"]],[1,3])
        self.assertEqual([x["floorId"] for x in data["nativeStoryBindings"]],[2,4])
        self.assertEqual(api.calls,["GetProjectInfo","GetStories"])
        self.assertEqual(data["nativeWriteCalls"],0)

    def test_same_arch_floor_can_native_index_zero(self):
        api=SyntheticStories(indices=(0,1))
        data=A.compile_project_brief(valid(),read_api=api)
        self.assertEqual([x["nativeIndex"] for x in data["nativeStoryBindings"]],[0,1])
        self.assertEqual(api.calls,["GetProjectInfo","GetStories"])

    def test_differently_named_native_floor_blocks_not_rename(self):
        api=SyntheticStories(names=("Other","Второй Этаж"))
        data=A.compile_project_brief(valid(),read_api=api)
        self.assertEqual(data["nativeResolution"],"NEEDS_STORY_RESOLUTION")
        self.assertEqual(data["nativeStoryBindings"],[])
        self.assertEqual(data["unresolvedArchitecturalStoryId"],"level-1")
        self.assertEqual(api.calls,["GetProjectInfo","GetStories"])

    def test_wrong_project_blocks_before_story_read(self):
        api=SyntheticStories()
        def wrong(cmd,args):
            res=api(cmd,args)
            if cmd=="GetProjectInfo": res["projectPath"]=r"C:\wrong.pln"
            return res
        with self.assertRaisesRegex(ValueError,"WRONG_ACTIVE_SINGLE_PLN"):
            A.compile_project_brief(valid(),read_api=wrong)
        self.assertEqual(api.calls,["GetProjectInfo"])

    def test_first_arch_floor_number_cannot_be_zero(self):
        v=valid()
        v["stories"][0]["label"]="0 этаж"
        with self.assertRaisesRegex(ValueError,"FIRST_ARCHITECTURAL_STORY"):
            A.compile_project_brief(v)

    def test_first_floor_elevation_is_explicit_not_guessed(self):
        v=valid()
        v["stories"][0]["level"]=2.0
        with self.assertRaisesRegex(ValueError,"FIRST_ARCHITECTURAL_STORY"):
            A.compile_project_brief(v)

    def test_existing_requires_exact_path_and_prevents_bpn(self):
        v=valid(); v.pop("targetProjectPath")
        with self.assertRaisesRegex(ValueError,"EXISTING_MODE_NEEDS_EXACT_PLN"):
            A.compile_project_brief(v)
        v=valid();v["targetProjectPath"]=r"C:\test\something.bpn"
        with self.assertRaisesRegex(ValueError,"EXACT_WINDOWS_PLN"):
            A.compile_project_brief(v)
        v=valid();v["targetProjectPath"]=r"C:relative.pln"
        with self.assertRaisesRegex(ValueError,"EXACT_WINDOWS_PLN"):
            A.compile_project_brief(v)

    def test_never_accepts_unverified_room_story_or_forged_norm_pass(self):
        v=valid();v["rooms"][0]["storyId"]="unknown"
        with self.assertRaisesRegex(ValueError,"ROOM_HAS_UNKNOWN_STORY"):
            A.compile_project_brief(v)
        v=valid();v["constraints"][0]["evidenceStatus"]="PASS"
        with self.assertRaisesRegex(ValueError,"DUPLICATE_OR_UNVERIFIED_PROVENANCE"):
            A.compile_project_brief(v)

    def test_duplicate_native_mapping_blocks(self):
        api=SyntheticStories(indices=(1,1),names=("Первый Этаж","Второй Этаж"))
        r=A.compile_project_brief(valid(),read_api=api)
        self.assertEqual(r["nativeResolution"],"NEEDS_STORY_RESOLUTION")
        self.assertFalse(r["nativeStoryBindings"])

    def test_live_three_stories_with_unnamed_second_resolves_explicit_native_pins(self):
        v=valid()
        v["stories"][0].update({"existingNativeIndex":0,"existingFloorId":1})
        v["stories"][1].update({"existingNativeIndex":1,"existingFloorId":2,
                                "existingNativeLabel":""})
        seen=[]
        def live(cmd,args):
            seen.append(cmd)
            if cmd=="GetProjectInfo":
                return {"projectPath":v["targetProjectPath"],
                        "isUntitled":False,"isTeamwork":False}
            if cmd=="GetStories":
                return {"actStory":0,"stories":[
                    {"index":0,"floorId":1,"level":0,"height":3,"name":"Первый Этаж"},
                    {"index":1,"floorId":2,"level":3,"height":3,"name":""},
                    {"index":2,"floorId":3,"level":6,"height":3,"name":""}]}
            raise AssertionError("Read-only only")
        out=A.compile_project_brief(v,read_api=live)
        self.assertEqual(out["nativeResolution"],"READY_FOR_ATTRIBUTE_RESOLUTION")
        self.assertEqual([(x["nativeIndex"],x["floorId"],x["nativeLabel"])
                          for x in out["nativeStoryBindings"]],
                         [(0,1,"Первый Этаж"),(1,2,"")])
        self.assertEqual(seen,["GetProjectInfo","GetStories"])
        self.assertEqual(out["nativeWriteCalls"],0)

    def test_unnamed_stories_must_be_pinned_by_both_native_ids(self):
        v=valid()
        v["stories"][1]["existingNativeLabel"]=""
        with self.assertRaisesRegex(ValueError,"INVALID_EXISTING_STORY_LABEL"):
            A.compile_project_brief(v)
        v["stories"][1]["existingNativeIndex"]=1
        with self.assertRaisesRegex(ValueError,"EXPLICIT_NATIVE_STORY_IDENTITY"):
            A.compile_project_brief(v)
        v["stories"][1]["existingFloorId"]=2
        self.assertEqual(A.compile_project_brief(v)["nativeResolution"],
                         "NEEDS_STORY_RESOLUTION")

    def test_pinned_unnamed_story_wrong_floor_id_is_not_silently_reassigned(self):
        v=valid()
        v["stories"][1].update({"existingNativeLabel":"",
                                "existingNativeIndex":1,"existingFloorId":99})
        seen=[]
        def native(cmd,args):
            seen.append(cmd)
            if cmd=="GetProjectInfo":
                return {"projectPath":v["targetProjectPath"],
                        "isUntitled":False,"isTeamwork":False}
            if cmd=="GetStories":
                return {"stories":[
                    {"index":0,"floorId":1,"level":0,"name":"Первый Этаж"},
                    {"index":1,"floorId":2,"level":3,"name":""},
                    {"index":2,"floorId":3,"level":6,"name":""}]}
            raise AssertionError("unexpected command")
        out=A.compile_project_brief(v,read_api=native)
        self.assertEqual(out["nativeResolution"],"NEEDS_STORY_RESOLUTION")
        self.assertEqual(out["unresolvedArchitecturalStoryId"],"level-2")
        self.assertEqual(out["nativeStoryBindings"],[])
        self.assertEqual(seen,["GetProjectInfo","GetStories"])

    def test_two_unnamed_native_levels_can_resolve_only_with_distinct_pins(self):
        v=valid()
        v["stories"][1].update({"existingNativeLabel":"",
                                "existingNativeIndex":1,"existingFloorId":2})
        v["stories"].append({"id":"level-3","label":"3 этаж","level":6.0,
                             "existingNativeLabel":"",
                             "existingNativeIndex":2,"existingFloorId":3})
        self.assertEqual(len(A.compile_project_brief(v)["stories"]),3)
        v["stories"][2]["existingNativeIndex"]=1
        with self.assertRaisesRegex(ValueError,"DUPLICATE_PINNED_NATIVE_STORY"):
            A.compile_project_brief(v)

    def test_zero_floor_pins_cannot_be_forged_in_generate_from_zero_mode(self):
        v=valid("GENERATE_FROM_ZERO")
        v["stories"][0].update({"existingNativeIndex":0,"existingFloorId":1})
        with self.assertRaisesRegex(ValueError,"EXPLICIT_NATIVE_STORY_IDENTITY"):
            A.compile_project_brief(v)

    def test_old_legacy_compiler_contract_unchanged(self):
        v=valid()
        with self.assertRaisesRegex(ValueError,"INVALID_PROJECT_INTENT"):
            A.compile_intent(v,A.RUN.DEFAULT_SCENE_SCHEMA)


if __name__=="__main__":
    unittest.main()
