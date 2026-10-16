"""Focused BDD first native window: source coordinate, host, APA graph compile."""
import json
import pathlib
import sys
import unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import apa_bdd_native_first_window_scene_writer as W
import archicad_bim_graph as G

class TestWindowSourceAndRouter(unittest.TestCase):
    def test_source_is_exact(self):
        record=json.loads(W.SOURCE_INTENT.read_text(encoding="utf8"))
        s=record["sourceMeasurementsMillimeters"]
        self.assertEqual(sum(s["firstSevenIntervals"])+s["jambWidth"],s["windowFramedLeftFromSouth"])
        self.assertEqual(s["windowFramedRightFromSouth"]-s["windowFramedLeftFromSouth"],1600)
        self.assertEqual(s["openingClearWidth"],1500)
        self.assertEqual(s["openingCenterFromSouth"],4370)
        self.assertAlmostEqual(9.38-4.37,W.OP["centerOffset"])
        self.assertEqual(W.WALL_GUID,record["nativeHost"]["guid"])
        self.assertEqual(W.OP["width"],1.5)
        self.assertEqual(W.OP["height"],.9)
    def test_apa_graph_and_host_existing(self):
        c=json.loads(W.SCHEMA.read_text(encoding="utf8"))
        task=W.create_task()
        self.assertEqual(len(task["graph"]["operations"]),2)
        self.assertEqual(task["graph"]["operations"][-1]["command"],"CreateWindows")
        p=G.compile_graph(c,task["graph"],runtime_version="1.5.10")
        self.assertEqual(p["status"],"PLAN_VALIDATED_OFFLINE",p)
    def test_no_local_writer_or_transport(self):
        s=(ROOT/"scripts"/"apa_bdd_native_first_window_scene_writer.py").read_text(encoding="utf8")
        self.assertIn("router.execute(writer,",s)
        self.assertIn("RUN.SceneWriter(api,LEDGER",s)
        self.assertNotIn("urllib.request",s)
        self.assertNotIn("sqlite3.connect",s)
        self.assertIn("if not args.apply:",s)

if __name__=="__main__":unittest.main()
