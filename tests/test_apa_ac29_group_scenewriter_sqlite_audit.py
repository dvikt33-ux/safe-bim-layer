"""Strict no-Archicad unit coverage for the V2 SQLite forensic checker."""
from pathlib import Path
import json
from contextlib import closing
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import apa_ac29_group_scenewriter_sqlite_audit_readonly as AUDIT


def guid(number):
    return f"00000000-0000-4000-8000-{number:012d}"


def sample():
    groups = [guid(100), guid(101)]
    roots = [guid(i) for i in range(1, 5)]
    children = [guid(i) for i in range(11, 15)]
    source = guid(1000)
    params = {
        "groupId": {"guid": source},
        "sourceRef": "https://github.com/dvikt33-ux/safe-bim-layer/pull/162",
        "translations": [{"dx": 25, "dy": 0, "dz": 0},
                         {"dx": 50, "dy": 0, "dz": 0}]
    }
    native = {
        "nativeModelWrites": 4,
        "sourceGroupId": {"guid": source},
        "newGroupIds": [{"guid": g} for g in groups],
        "createdElements": [{"elementId": {"guid": g}} for g in roots]
    }
    result = {
        "status": "PASS", "sceneId": AUDIT.SCENE,
        "command": AUDIT.COMMAND,
        "operationHash": "a" * 64, "automaticRetry": False,
        "intent": {
            "sceneId": AUDIT.SCENE,
            "command": AUDIT.COMMAND,
            "parameters": params,
            "sourcePlanHash": "b" * 64,
            "target": {"path": str(AUDIT.SCRATCH),
                       "port": 19724}
        },
        "nativeResponse": native,
        "readback": {
            "status": "GROUP_CLONE_SCENEWRITER_NATIVE_BREP_GUID_READBACK_PASS",
            "originalNativeGuidCount": 44,
            "finalNativeGuidCount": 52,
            "originalGroupUnchanged": True,
            "allNativeRootsAndChildrenVerified": True,
            "newRootGuids": roots,
            "newSegmentGuids": children,
            "newGroupGuids": groups
        }
    }
    receipt = {
        "schema": "APA_AC29_GROUP_SCENEWRITER_ACCEPTANCE_V1",
        "scenario": AUDIT.SCENE,
        "result": {
            "status": "LIVE_SCENEWRITER_NATIVE_GROUP_CLONE_PASS",
            "scratchProject": str(AUDIT.SCRATCH),
            "baseGuidCount": 44, "postGuidCount": 52,
            "nativeMutationCalls": 1,
            "nativeModelWritesFromAddOn": 4,
            "createdGroupCount": 2, "createdRootCount": 4,
            "sceneWriterOriginalWorkflow": "WORKFLOW_CALLABLE_VERIFIED",
            "verifierId": "VerifiedNativeGroupClone",
            "saveCalls": 0, "automaticRetry": False,
            "uncommittedScratchPlnChanges": True,
            "sourceGroupId": source,
            "sourceRevision": "c" * 40
        }
    }
    before = {
        "sceneId": AUDIT.SCENE, "command": AUDIT.COMMAND,
        "scratchPath": str(AUDIT.SCRATCH),
        "automaticRetry": False, "repositoryRevision": "c" * 40,
        "parameters": params
    }
    scene = [(AUDIT.SCENE, "a" * 64, "PASS", json.dumps(result))]
    step = [(AUDIT.SCENE, "operation", "PASS", None, json.dumps(result))]
    dispatched = [{"command": "GetModelDumpV1", "parameters": {}},
                  {"command": AUDIT.COMMAND, "parameters": params},
                  {"command": "GetModelDumpV1", "parameters": {}}]
    returned = [{"command": "GetModelDumpV1", "parameters": {},
                 "response": {"elements": []}},
                {"command": AUDIT.COMMAND, "parameters": params,
                 "response": native},
                {"command": "GetModelDumpV1", "parameters": {},
                 "response": {"elements": []}}]
    return receipt, before, scene, step, dispatched, returned


class SQLiteGroupForensic(unittest.TestCase):
    def test_sqlite_pass_matches_exactly_one_native_dispatch(self):
        facts = AUDIT.verify_evidence(*sample())
        self.assertEqual(facts["sqlJournalRows"], 2)
        self.assertEqual(facts["nativeMutationDispatches"], 1)
        self.assertEqual(facts["createdSegmentCount"], 4)
        self.assertTrue(facts["nativeResponseMatchesLoggedTransport"])

    def test_extra_sqlite_scene_fails_closed(self):
        receipt, before, scenes, steps, dispatch, trace = sample()
        scenes.append(("unreviewed", "z" * 64, "PASS", "{}"))
        with self.assertRaisesRegex(RuntimeError, "EXACT_ONE_SCENE"):
            AUDIT.verify_evidence(receipt, before, scenes, steps, dispatch, trace)

    def test_unknown_or_second_native_write_fails_closed(self):
        receipt, before, scenes, steps, dispatch, trace = sample()
        dispatch.append({"command": "ModifyWalls", "parameters": {}})
        trace.append({"command": "ModifyWalls", "parameters": {},
                      "response": {"success": True}})
        with self.assertRaisesRegex(RuntimeError, "UNAPPROVED_NATIVE_DISPATCH"):
            AUDIT.verify_evidence(receipt, before, scenes, steps, dispatch, trace)
        dispatch[-1]["command"] = AUDIT.COMMAND
        trace[-1]["command"] = AUDIT.COMMAND
        with self.assertRaisesRegex(RuntimeError, "EXACTLY_ONE_SUCCESSFUL"):
            AUDIT.verify_evidence(receipt, before, scenes, steps, dispatch, trace)

    def test_journal_readback_guid_mismatch_fails_closed(self):
        receipt, before, scenes, steps, dispatch, trace = sample()
        result = json.loads(scenes[0][-1])
        result["readback"]["newRootGuids"][0] = guid(20)
        altered = json.dumps(result)
        scenes[0] = (*scenes[0][:3], altered)
        steps[0] = (*steps[0][:4], altered)
        with self.assertRaisesRegex(RuntimeError, "OWNERSHIP_DRIFT"):
            AUDIT.verify_evidence(receipt, before, scenes, steps, dispatch, trace)

    def test_no_model_interface_and_sqlite_read_only(self):
        source = (Path(__file__).resolve().parents[1] /
                  "scripts" /
                  "apa_ac29_group_scenewriter_sqlite_audit_readonly.py"
                 ).read_text(encoding="utf8")
        self.assertIn("mode=ro", source)
        self.assertIn("PRAGMA query_only = ON", source)
        self.assertNotIn("LIVE.request(", source)
        self.assertNotIn("SceneWriter(", source)
        self.assertNotIn('subprocess.run(', source)
        with tempfile.TemporaryDirectory() as d:
            db = Path(d) / "test.sqlite"
            import sqlite3
            with closing(sqlite3.connect(db)) as sql:
                sql.execute("CREATE TABLE scenes (scene_id,plan_hash,state,result)")
                sql.execute("CREATE TABLE steps (scene_id,step_id,state,guid,output)")
                sql.commit()
            self.assertEqual(AUDIT.sqlite_rows(db), ([], []))


if __name__ == "__main__":
    unittest.main()
