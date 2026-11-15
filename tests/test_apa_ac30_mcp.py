"""Tests for separate pinned AC30 read-only MCP control; no model writes."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from apa_ac30_mcp import AC30MCPControl, MAX_MCP_ELEMENTS
from apa_ac30_tapir20 import AC30GuardError, SCHEMA

A="C8EBF5F0-BE73-4D3B-908C-14CD75132CB6"
B="7DDABE9B-7C3A-4955-AB7F-20CA54EC1BA3"

class MCPControlTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        base=Path(temporary.name).resolve()
        self.pln=base/"Test_Model.pln"
        backup=base/"Test_Model_Backup.pln"
        addon=base/"Tapir.apx"
        for file, contents in [(self.pln,b"test-pln"),
                               (backup,b"test-pln"),(addon,b"test-apx")]:
            file.write_bytes(contents)
        h=lambda file:hashlib.sha256(file.read_bytes()).hexdigest()
        profile=dict(schema=SCHEMA,project=str(self.pln),
                     projectSha256=h(self.pln),backup=str(backup),
                     backupSha256=h(backup),addon=str(addon),
                     addonSha256=h(addon),port=19725,
                     archicadVersion=30,tapirVersion="2.0.0")
        self.profile=base/"profile.json"
        self.profile.write_text(json.dumps(profile),encoding="utf-8")
        self.elements=base/"elements.json"
        self.elements.write_text(json.dumps([
            {"guid":A,"type":"Wall"},{"guid":B,"type":"Wall"}]),encoding="utf-8")
        self.calls=[]
        self.project_drift=False
        self.quantity_drift=False

    def fake(self,port,name,params=None):
        self.calls.append(name)
        if name=="GetProjectInfo":
            return {"projectPath":str(self.pln)+(".changed" if self.project_drift else ""),
                    "isUntitled":False,"isTeamwork":False}
        if name=="API.GetProductInfo":
            return {"version":30,"buildNumber":3001}
        if name=="GetAddOnVersion":
            return {"version":"2.0.0"}
        if name=="GetDetailsOfElements":
            return {"detailsOfElements":[{"type":"Wall"},{"type":"Wall"}]}
        if name=="GetQuantitiesOfElements":
            offset=1 if self.quantity_drift and params["calculateInOneCall"] else 0
            return {"quantitiesOfElements":[
                {"type":"Wall","quantities":{"volume":5+offset}},
                {"type":"Wall","quantities":{"volume":7+offset}}]}
        raise AssertionError("unapproved native command "+name)

    def test_pinned_status_contains_no_write_tools(self):
        ctl=AC30MCPControl(self.profile,self.elements,self.fake)
        record=ctl.read("status")
        self.assertEqual(record["status"],"AC30_MCP_READ_ONLY")
        self.assertEqual(record["modelWrites"],0)
        self.assertFalse(record["executionPermission"])
        self.assertEqual(record["elementCount"],2)
        self.assertFalse("GetQuantitiesOfElements" in self.calls)

    def test_typed_quantities_with_independent_parity(self):
        ctl=AC30MCPControl(self.profile,self.elements,self.fake)
        record=ctl.read("quantities")
        self.assertEqual(record["status"],"AC30_MCP_TYPED_QUANTITIES_PASS")
        self.assertEqual(record["typedGroups"][0]["guids"],[A,B])
        self.assertEqual(record["typedGroups"][0]["strategy"],"typed-batch-exact-parity")
        self.assertEqual(record["modelWrites"],0)
        self.assertFalse(record["executionPermission"])

    def test_operator_inputs_mutated_after_startup_blocked(self):
        ctl=AC30MCPControl(self.profile,self.elements,self.fake)
        self.elements.write_text("[]",encoding="utf-8")
        with self.assertRaisesRegex(AC30GuardError,"MCP_OPERATOR_INPUT_DRIFT"):
            ctl.read("quantities")
        self.assertFalse(self.calls)

    def test_profile_changed_after_startup_blocked(self):
        ctl=AC30MCPControl(self.profile,self.elements,self.fake)
        self.profile.write_text("{}",encoding="utf-8")
        with self.assertRaisesRegex(AC30GuardError,"MCP_OPERATOR_INPUT_DRIFT"):
            ctl.read("status")
        self.assertFalse(self.calls)

    def test_project_switch_fails(self):
        ctl=AC30MCPControl(self.profile,self.elements,self.fake)
        self.project_drift=True
        with self.assertRaisesRegex(AC30GuardError,"WRONG_OPEN_PROJECT"):
            ctl.read("status")

    def test_mismatched_quantities_fails(self):
        ctl=AC30MCPControl(self.profile,self.elements,self.fake)
        self.quantity_drift=True
        with self.assertRaisesRegex(AC30GuardError,"QUANTITY_PARITY_DRIFT"):
            ctl.read("quantities")

    def test_unknown_action_is_not_exposed(self):
        ctl=AC30MCPControl(self.profile,self.elements,self.fake)
        with self.assertRaisesRegex(AC30GuardError,"MCP_UNKNOWN_READ_KIND"):
            ctl.read("write")
        self.assertFalse(self.calls)

    def test_server_exports_only_one_read_tool(self):
        from apa_ac30_mcp import server_for
        server=server_for(AC30MCPControl(self.profile,self.elements,self.fake))
        self.assertEqual(set(server._tool_manager._tools),{"apa_ac30_read"})

if __name__=="__main__":
    unittest.main(verbosity=2)
