"""3D view opt-in does not weaken the existing default SceneWriter authorization."""
import sys
from pathlib import Path
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import archicad_scene_run as RUN

INFO={"path":r"C:\LocalAI\BDD working.pln","name":"BDD working",
      "port":19727,"tapirVersion":"1.5.10","storyIndex":0,
      "activeViewStoryIndex":-1,
      "storyTopology":[{"index":0,"floorId":1,"level":0.0,"label":"Первый Этаж"}]}

class TestSHA3DSceneWriter(unittest.TestCase):
    def test_default_writer_retains_original_story_guard(self):
        writer=RUN.SceneWriter(lambda *args:None,Path("unused.sqlite"))
        self.assertFalse(writer.allow_3d_view_for_write)
        with patch.object(RUN,"guarded_project",return_value={"path":"ORIGINAL_GUARD"}) as guarded:
            self.assertEqual(writer.guarded_binding(),{"path":"ORIGINAL_GUARD"})
            guarded.assert_called_once()

    def test_explicit_sha_copy_allows_3d_with_normalized_binding(self):
        writer=RUN.SceneWriter(lambda *args:None,Path("unused.sqlite"),
                               allow_3d_view_for_write=True)
        with patch.object(RUN,"_SAVED_COPY_AUTHORIZATION",{"path":"mock"}),\
             patch.object(RUN,"authorized_authored_target",return_value=True),\
             patch.object(RUN,"guarded_project_for_read",return_value=INFO),\
             patch.object(RUN,"guarded_project",side_effect=AssertionError("MUST NOT CALL")):
            b=writer.guarded_binding()
        self.assertEqual(b["storyIndex"],0)
        self.assertEqual(b["port"],19727)
        self.assertNotIn("activeViewStoryIndex",b)

    def test_non_sha_authorized_copy_and_wrong_view_fail(self):
        writer=RUN.SceneWriter(lambda *args:None,Path("unused.sqlite"),
                               allow_3d_view_for_write=True)
        with patch.object(RUN,"_SAVED_COPY_AUTHORIZATION",None):
            with self.assertRaisesRegex(ValueError,"EXACT_SAVED_COPY"):
                writer.guarded_binding()
        with patch.object(RUN,"_SAVED_COPY_AUTHORIZATION",{"path":"mock"}),\
             patch.object(RUN,"authorized_authored_target",return_value=True),\
             patch.object(RUN,"guarded_project_for_read",return_value=dict(INFO,activeViewStoryIndex=2)):
            with self.assertRaisesRegex(ValueError,"3D_OR_STORY_ZERO"):
                writer.guarded_binding()

    def test_required_story_rejects_optin(self):
        writer=RUN.SceneWriter(lambda *args:None,Path("unused.sqlite"),
                               allow_3d_view_for_write=True)
        writer.required_story={"nativeIndex":2,"floorId":3,"level":6.0,"label":None}
        with patch.object(RUN,"_SAVED_COPY_AUTHORIZATION",{"path":"mock"}):
            with self.assertRaisesRegex(ValueError,"EXACT_SAVED_COPY"):
                writer.guarded_binding()

if __name__=="__main__":unittest.main()
