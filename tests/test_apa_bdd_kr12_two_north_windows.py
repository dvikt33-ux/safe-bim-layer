"""Targeted tests for the BDD KR12 2-window task on the original APA graph."""
import json
import pathlib
import sys
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import apa_bdd_kr12_two_north_windows as W
import archicad_bim_graph as GRAPH

class TestNorthWindows(unittest.TestCase):
    def setUp(self):
        self.source=json.loads(W.SOURCE.read_text(encoding="utf-8"))
        self.binding=json.loads(W.BASE.read_text(encoding="utf-8"))

    def test_source_offsets_and_wall_face_alignment(self):
        W.source_verify(self.source)
        self.assertEqual([s["centerOffset"] for s in W.STAGES],[12.605,8.06])
        self.assertEqual([s["width"] for s in W.STAGES],[1.6,.8])
        self.assertTrue(all(s["sillHeight"]==.9 for s in W.STAGES))
        self.assertTrue(all(s["height"]==1.5 for s in W.STAGES))
        self.assertEqual(W.HOST,self.source["nativeHost"]["guid"])

    def test_baseline_is_original_plus_first_saved_window(self):
        expected=W.baseline(self.binding)
        self.assertEqual(len(expected),262)
        self.assertIn(W.PREVIOUS,expected)
        self.assertIn(W.HOST,expected)

    def test_existing_apa_graph_compiles_two_real_create_windows(self):
        catalog=json.loads(W.SCHEMA.read_text(encoding="utf-8"))
        for s in W.STAGES:
            task=W.task_for(W.stage_params(s))
            self.assertEqual([x["command"] for x in task["graph"]["operations"]],
                             ["GetDetailsOfElements","CreateWindows"])
            compiled=GRAPH.compile_graph(catalog,task["graph"],runtime_version="1.5.10")
            self.assertEqual(compiled["status"],"PLAN_VALIDATED_OFFLINE")

    def test_native_host_and_first_window_baseline_checks(self):
        W.check_host({"type":"Wall","floorIndex":0,"details":{
            "height":3,"begThickness":.25,"endThickness":.25,
            "zCoordinate":-.1,
            "begCoordinate":{"x":14.28,"y":9.38},
            "endCoordinate":{"x":0,"y":9.38}}})
        W.check_window({"type":"Window","floorIndex":0,
            "details":{"ownerElementId":{"guid":W.PREVIOUS_HOST},
                       "width":1.5,"height":.9,"sillHeight":1.1,
                       "centerOffset":5.01}},
            {"width":1.5,"height":.9,"sillHeight":1.1,"centerOffset":5.01},
            W.PREVIOUS_HOST)
        with self.assertRaisesRegex(ValueError,"OWNER"):
            W.check_window({"type":"Window","floorIndex":0,
                "details":{"ownerElementId":{"guid":W.HOST},
                           "width":1.5,"height":.9,"sillHeight":1.1,
                           "centerOffset":5.01}},
                {"width":1.5,"height":.9,"sillHeight":1.1,"centerOffset":5.01},
                W.PREVIOUS_HOST)

    def test_existing_writer_only_not_direct_tapir(self):
        src=(ROOT/"scripts"/"apa_bdd_kr12_two_north_windows.py").read_text(encoding="utf-8")
        self.assertIn("router.execute(writer,scene_id",src)
        self.assertIn("RUN.SceneWriter(api,LEDGER",src)
        self.assertNotIn("urllib.request",src)
        self.assertNotIn("sqlite3.connect(",src.replace('sqlite3.connect("file:"+LEDGER.as_posix()+"?mode=ro",uri=True)',""))

if __name__=="__main__":
    unittest.main()
