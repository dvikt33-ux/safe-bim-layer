"""Fail-closed source tests for the isolated Archicad 30 read-only adapter."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from apa_ac30_tapir20 import (
    AC30GuardError,AC30ReadSession,SCHEMA,api_http,
    inputs_file,profile_from_path,run_readonly,
)

A="C8EBF5F0-BE73-4D3B-908C-14CD75132CB6"
B="7DDABE9B-7C3A-4955-AB7F-20CA54EC1BA3"
C="5D759916-D4BC-4E1D-A25F-9FAE18D3B1C4"

class TestAC30Guard(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base=Path(self.temporary.name).resolve()
        self.model=self.base/"model"
        self.model.mkdir()
        self.evidence=self.base/"evidence"
        self.evidence.mkdir()
        self.pln=self.model/"Test_Copy.pln"
        self.backup=self.model/"Test_Copy_Backup.pln"
        self.apx=self.model/"Tapir_AC30.apx"
        self.pln.write_bytes(b"test-bim-snapshot")
        self.backup.write_bytes(b"test-bim-snapshot")
        self.apx.write_bytes(b"test-addon")
        h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
        self.config=dict(schema=SCHEMA,project=str(self.pln),projectSha256=h(self.pln),
                         backup=str(self.backup),backupSha256=h(self.backup),
                         addon=str(self.apx),addonSha256=h(self.apx),port=19725,
                         archicadVersion=30,tapirVersion="2.0.0")
        self.profile=self.evidence/"profile.json"
        self.profile.write_text(json.dumps(self.config),encoding="utf-8")
        self.elements=self.evidence/"elements.json"
        self.entries=[{"guid":A,"type":"Wall"},{"guid":B,"type":"Wall"},
                      {"guid":C,"type":"Roof"}]
        self.elements.write_text(json.dumps(self.entries),encoding="utf-8")
        self.calls=[]
        self.batch_failure=False
        self.parity_drift=False
        self.wrong_project=False
    def fake(self,port,command,params=None):
        self.calls.append((port,command,params))
        if command=="GetProjectInfo":
            return {"projectPath":str(self.pln if not self.wrong_project else self.backup),
                    "isUntitled":False,"isTeamwork":False}
        if command=="API.GetProductInfo":
            return {"version":30,"buildNumber":3001}
        if command=="GetAddOnVersion":
            return {"version":"2.0.0"}
        if command=="GetDetailsOfElements":
            guids=[e["elementId"]["guid"] for e in params["elements"]]
            typ="Wall" if guids[0] in (A,B) else "Roof"
            return {"detailsOfElements":[{"type":typ} for _ in guids]}
        if command=="GetQuantitiesOfElements":
            guids=[e["elementId"]["guid"] for e in params["elements"]]
            typ="Wall" if guids[0] in (A,B) else "Roof"
            if self.batch_failure and params["calculateInOneCall"] and typ=="Wall":
                return {"quantitiesOfElements":[{"type":typ,"error":"batch failure"} for _ in guids]}
            diff=5 if self.parity_drift and params["calculateInOneCall"] else 0
            return {"quantitiesOfElements":[{"type":typ,"quantities":{"volume":i+1+diff}} for i,_ in enumerate(guids)]}
        raise AssertionError("Not a permitted test read: "+command)
    def test_end_to_end_type_batches_parity_and_guard(self):
        result=run_readonly(self.profile,self.elements,self.evidence/"receipt.json",self.fake)
        self.assertEqual(result["status"],"AC30_TAPIR20_R04_SOURCE_READ_PASS")
        self.assertEqual(result["modelWrites"],0)
        self.assertEqual(result["elementCount"],3)
        self.assertEqual([len(x["guids"]) for x in result["typedGroups"]],[2,1])
        self.assertTrue(all(row["independentExactParity"] for row in result["typedGroups"]))
        for _,command,params in self.calls:
            if command=="GetQuantitiesOfElements":
                self.assertEqual(len({e["elementId"]["guid"] in (A,B) for e in params["elements"]}),1)
        self.assertTrue((self.evidence/"receipt.json").exists())
        with self.assertRaises(AC30GuardError):
            run_readonly(self.profile,self.elements,self.evidence/"receipt.json",self.fake)
    def test_batch_failure_homogeneous_fallback(self):
        self.batch_failure=True
        result=run_readonly(self.profile,self.elements,self.evidence/"fallback.json",self.fake)
        self.assertEqual(result["typedGroups"][0]["strategy"],"typed-batch-failed-independent-fallback")
    def test_batch_drift_blocked_no_receipt(self):
        self.parity_drift=True
        out=self.evidence/"unsafe.json"
        with self.assertRaisesRegex(AC30GuardError,"QUANTITY_PARITY_DRIFT"):
            run_readonly(self.profile,self.elements,out,self.fake)
        self.assertFalse(out.exists())
    def test_wrong_open_project(self):
        self.wrong_project=True
        with self.assertRaisesRegex(AC30GuardError,"WRONG_OPEN_PROJECT"):
            run_readonly(self.profile,self.elements,self.evidence/"wrong.json",self.fake)
    def test_changed_backup_hash_blocked_before_network(self):
        self.backup.write_bytes(b"tampered")
        with self.assertRaisesRegex(AC30GuardError,"HASH_DRIFT_BACKUP"):
            run_readonly(self.profile,self.elements,self.evidence/"bad.json",self.fake)
        self.assertFalse(self.calls)
    def test_wrong_addon_hash_blocked(self):
        self.apx.write_bytes(b"modified")
        with self.assertRaisesRegex(AC30GuardError,"HASH_DRIFT_ADDON"):
            run_readonly(self.profile,self.elements,self.evidence/"bad.json",self.fake)
        self.assertFalse(self.calls)
    def test_cross_platform_unapproved_path_rejected(self):
        self.config["project"]="relative.pln"
        self.profile.write_text(json.dumps(self.config),encoding="utf-8")
        with self.assertRaisesRegex(AC30GuardError,"UNTRUSTED_PATH"):
            profile_from_path(self.profile)
    def test_duplicate_guid_rejected(self):
        self.elements.write_text(json.dumps(self.entries+[self.entries[0]]),encoding="utf-8")
        with self.assertRaisesRegex(AC30GuardError,"DUPLICATE_GUID"):
            inputs_file(self.elements)
    def test_whitelist_blocks_all_mutations(self):
        session=AC30ReadSession(self.config,transport=self.fake)
        with self.assertRaisesRegex(AC30GuardError,"WRITE_OR_UNKNOWN_COMMAND"):
            session.call("ModifyWalls",{"wallsWithDetails":[]})
        with self.assertRaisesRegex(AC30GuardError,"READ_ONLY_COMMAND_REQUIRED"):
            api_http(19725,"SaveProject",{})
        self.assertFalse(self.calls)
    def test_output_inside_model_dir_denied(self):
        with self.assertRaisesRegex(AC30GuardError,"OUTPUT_MUST_BE_NEW"):
            run_readonly(self.profile,self.elements,self.model/"receipt.json",self.fake)
if __name__=="__main__":
    unittest.main(verbosity=2)
