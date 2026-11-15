"""Source preflight tests: grouped walls must fail closed without native writes."""
import unittest
from unittest.mock import patch

from apa_ac30_wall_preflight import preflight,AC30GuardError

WALL="C8EBF5F0-BE73-4D3B-908C-14CD75132CB6"
GROUP="D609571F-E769-439F-B92B-8AECD1E2AC7F"
OTHER="7DDABE9B-7C3A-4955-AB7F-20CA54EC1BA3"

class Fake:
    def __init__(self):
        self.height=3.2
        self.typ="Wall"
        self.groups=[{"groupId":{"guid":GROUP}}]
        self.suspend=False
        self.commands=[]
    def guard(self):
        return {"project": "C:\\Test\\Verified_Copy.pln","archicadVersion":30}
    def call(self,command,args=None):
        self.commands.append(command)
        if command=="GetDetailsOfElements":
            return {"detailsOfElements":[{"type":self.typ,"details":{"height":self.height}}]}
        if command=="GetGroupsOfElements":
            return {"groupGuids":self.groups}
        if command=="GetSuspendGroupsMode":
            return {"suspendGroups":self.suspend}
        raise AssertionError("Any write command is forbidden")

class WallPreflightTests(unittest.TestCase):
    def setUp(self):
        self.mock=Fake()
        patcher=patch("apa_ac30_wall_preflight.AC30ReadSession",return_value=self.mock)
        patcher.start()
        self.addCleanup(patcher.stop)
    def run_check(self,wall=WALL,group=GROUP,old=3.2,new=3.6):
        return preflight({},wall,group,old,new)
    def test_grouped_wall_requires_suspend(self):
        record=self.run_check()
        self.assertEqual(record["status"],"AC30_GROUPED_WALL_PREFLIGHT_PASS")
        self.assertTrue(record["requiresSuspendGroups"])
        self.assertFalse(record["executionPermission"])
        self.assertEqual(record["modelWrites"],0)
        self.assertTrue(set(self.mock.commands)<=
                        {"GetDetailsOfElements","GetGroupsOfElements","GetSuspendGroupsMode"})
    def test_active_suspend_requires_no_mode_toggle(self):
        self.mock.suspend=True
        record=self.run_check()
        self.assertFalse(record["requiresSuspendGroups"])
    def test_wrong_group_fails_closed(self):
        with self.assertRaisesRegex(AC30GuardError,"EXPECTED_GROUP_MISSING"):
            self.run_check(group=OTHER)
    def test_stale_wall_height_fails_closed(self):
        self.mock.height=3.5
        with self.assertRaisesRegex(AC30GuardError,"HEIGHT_BASELINE_DRIFT"):
            self.run_check()
    def test_non_wall_rejected(self):
        self.mock.typ="Slab"
        with self.assertRaisesRegex(AC30GuardError,"EXPECTED_WALL_NOT_FOUND"):
            self.run_check()
    def test_invalid_or_no_op_height_rejected(self):
        for value in [float("nan"),-2,0,3.2]:
            with self.assertRaises(AC30GuardError):
                self.run_check(new=value)
    def test_guid_format_rejected_before_transport(self):
        with self.assertRaisesRegex(AC30GuardError,"WALL_GUID_REQUIRED"):
            self.run_check(wall="invalid")
        self.assertFalse(self.mock.commands)
if __name__=="__main__":
    unittest.main(verbosity=2)
