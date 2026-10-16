"""KR-6 native floor correction: focused structural regression, no Archicad writes."""
import importlib.util
import pathlib
import unittest
from unittest.mock import patch

p=pathlib.Path(__file__).resolve().parents[1]/"scripts"/"apa_bdd_native_kr6_floor_repair.py"
spec=importlib.util.spec_from_file_location("apa_bdd_native_kr6_floor_repair",p)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class TestKR6Repair(unittest.TestCase):
    def test_write_command_fence(self):
        for c in ("DeleteElements","OpenProject","CreateWalls","CreateSlabs","ModifyWalls","ModifyColumns","ModifyRoofs"):
            with self.assertRaisesRegex(RuntimeError,"COMMAND_FENCE"):
                m.api(c,{},write=True)
        with self.assertRaisesRegex(RuntimeError,"COMMAND_FENCE"):
            m.api("ModifyBeams",{},write=False)

    def test_correct_joist_geometry_expected(self):
        row={"type":"Beam","details":{"level":-.1,"height":.2,"width":.1},
             "bbox":{"zMin":-.3,"zMax":-.1}}
        m.verify_joist(row,{})
        row["bbox"]["zMax"]=-.3
        with self.assertRaisesRegex(RuntimeError,"bbox"):
            m.verify_joist(row,{})

    def test_correct_floor_slab_geometry_expected(self):
        row={"type":"Slab","details":{"structureType":"Basic","thickness":.022,
                                        "zCoordinate":-.078},
             "bbox":{"zMin":-.1,"zMax":-.078}}
        instruction={"elementId":{"guid":"TEST"},"expected":{"thickness":.022,"top":-.078}}
        m.verify_slab(row,instruction)
        row["details"]["thickness"]=.3
        with self.assertRaisesRegex(RuntimeError,"readback mismatch"):
            m.verify_slab(row,instruction)

    def test_preflight_rejects_default_composite_changed(self):
        groups={"Timber joists nominal @ 600 mm":["J"],
                "Floor sheathing":["F"],"Terrace platforms":["T"]}
        rows={
            "j":{"type":"Beam","details":{"width":.1,"height":.2,"level":-.3},
                 "bbox":{"zMin":-.5,"zMax":-.3}},
            "f":{"type":"Slab","details":{"structureType":"Composite",
                  "thickness":.3,"zCoordinate":0},
                 "bbox":{"zMin":-.3,"zMax":0}},
            "t":{"type":"Slab","details":{"structureType":"Composite",
                  "thickness":.3,"zCoordinate":-.05},
                 "bbox":{"zMin":-.35,"zMax":-.05}}
        }
        m.exact_inputs(rows,groups)
        rows["f"]["details"]["thickness"]=.022
        with self.assertRaisesRegex(RuntimeError,"changed since audited"):
            m.exact_inputs(rows,groups)

    def test_journal_existing_backup_guards(self):
        self.assertNotEqual(m.TARGET,m.SOURCE)
        self.assertNotEqual(m.TARGET,m.BACKUP)
        self.assertIn("before-KR6-floor-correction",str(m.BACKUP))
        self.assertEqual(m.PORT,19727)

if __name__=="__main__":unittest.main()
