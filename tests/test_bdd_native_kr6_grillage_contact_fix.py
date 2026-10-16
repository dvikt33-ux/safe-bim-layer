"""Offline regression of source KR-6 grillage/joist/pile contact guards."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

p=Path(__file__).resolve().parents[1]/"scripts"/"apa_bdd_native_kr6_grillage_contact_fix.py"
spec=importlib.util.spec_from_file_location("bdd_grillage_fix",p)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class TestGrillageContact(unittest.TestCase):
    def test_commands_fenced(self):
        for command in ("CreateBeams","CreateWalls","DeleteElements","OpenProject","ModifySlabs","ModifyWalls"):
            with self.assertRaisesRegex(RuntimeError,"COMMAND NOT ALLOWED"):
                m.tapir(command,{},allow_write=True)
        with self.assertRaisesRegex(RuntimeError,"COMMAND NOT ALLOWED"):
            m.tapir("ModifyBeams",{},allow_write=False)

    def test_project_and_journals_are_separate(self):
        self.assertNotEqual(m.SOURCE,m.TARGET)
        self.assertNotEqual(m.TARGET,m.BACKUP)
        self.assertNotEqual(m.FLOOR,m.LOG)
        self.assertEqual(m.PORT,19727)

    def test_requires_evidence_before_read_or_write(self):
        with patch.object(m,"target"),patch.object(m.SOURCE,"is_file",return_value=False):
            with self.assertRaisesRegex(RuntimeError,"Missing source"):
                m.read_guards()

    def test_source_vertical_ties_invariant(self):
        self.assertTrue(m.close(-.6,-.6))
        self.assertTrue(m.close(-.3,-.3))
        self.assertAlmostEqual(-.3-(-.6),.3)
        self.assertFalse(m.close(-1.1,-.6))
        self.assertTrue(m.BACKUP.name.endswith(".before-KR6-grillage-correction.pln"))

if __name__=="__main__":
    unittest.main()
