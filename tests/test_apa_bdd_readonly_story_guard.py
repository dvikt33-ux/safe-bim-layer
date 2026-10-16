"""Regression: upper-floor and 3D view do not block read-only APA.

The existing guarded_project() / SceneWriter write safety must not change.
"""
import inspect
import sys
from pathlib import Path
from unittest import TestCase, main
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import archicad_scene_run as RUN
import archicad_dynamic_commands as DYNAMIC

EXPECTED_PATH=r"C:\LocalAI\SafeBIM_Global_Library_Test_Projects\BDD дом - по чертежам 2022.pln"
EXPECTED_NAME="BDD дом - по чертежам 2022"


def fake_api(active=2, *, path=EXPECTED_PATH, floor_id=1, level=0.0):
    evidence={
        "GetProjectInfo":{
            "projectName":EXPECTED_NAME,
            "projectPath":path,
            "isUntitled":False,"isTeamwork":False,
        },
        "GetStories":{
            "actStory":active,
            "stories":[
                {"index":0,"floorId":floor_id,"level":level,"name":"Первый Этаж"},
                {"index":1,"floorId":2,"level":3.0,"name":""},
                {"index":2,"floorId":3,"level":6.0,"name":""},
            ],
        },
        "GetAddOnVersion":{"version":"1.5.10"},
    }
    return lambda cmd, params: evidence[cmd]


class StoryReadOnlyGuard(TestCase):
    def test_3d_and_upper_view_accepted_only_for_native_read(self):
        with patch.object(RUN,"PORT",19727),\
             patch.object(RUN,"EXPECTED_PATH",EXPECTED_PATH),\
             patch.object(RUN,"EXPECTED_NAME",EXPECTED_NAME):
            for active in (-1,1,2):
                self.assertEqual(
                    RUN.guarded_project_for_read(fake_api(active))["activeViewStoryIndex"],
                    active)
                with self.assertRaisesRegex(ValueError,"STORY_MISMATCH"):
                    RUN.guarded_project(fake_api(active))
            self.assertEqual(
                RUN.guarded_project(fake_api(0))["storyIndex"],0)

    def test_wrong_target_and_story_topology_remain_blocked(self):
        with patch.object(RUN,"PORT",19727),\
             patch.object(RUN,"EXPECTED_PATH",EXPECTED_PATH),\
             patch.object(RUN,"EXPECTED_NAME",EXPECTED_NAME):
            with self.assertRaisesRegex(ValueError,"WRONG_PROJECT"):
                RUN.guarded_project_for_read(fake_api(2,path=r"C:\LocalAI\WRONG.pln"))
            with self.assertRaisesRegex(ValueError,"FIRST_STORY_MISMATCH"):
                RUN.guarded_project_for_read(fake_api(2,floor_id=999))
            with self.assertRaisesRegex(ValueError,"FIRST_STORY_MISMATCH"):
                RUN.guarded_project_for_read(fake_api(2,level=1.0))
            with self.assertRaisesRegex(ValueError,"ACTIVE_VIEW_INDEX"):
                RUN.guarded_project_for_read(fake_api(None))

    def test_read_path_and_writer_path_stay_distinct(self):
        dynamic_source=inspect.getsource(DYNAMIC.DynamicCommands.read)
        self.assertIn("RUN.guarded_project_for_read(api)",dynamic_source)
        writer_source=inspect.getsource(RUN.SceneWriter.guarded_binding)
        self.assertIn("guarded_project(self.api, self.required_story)",writer_source)
        self.assertIn("if not self.allow_3d_view_for_write:",writer_source)
        self.assertIn("3D_WRITER_REQUIRES_EXACT_SAVED_COPY_AUTHORIZATION",writer_source)
        self.assertIn("guarded_project_for_read",writer_source)

if __name__=="__main__":
    main()
