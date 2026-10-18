"""Fail-closed offline contracts for native Hotlink one-shot on disposable PLN."""
from __future__ import annotations

import hashlib
from contextlib import closing
import json
import sqlite3
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import apa_ac29_hotlink_native_verifiers as V
import apa_ac29_hotlink_oneshot as H


def uid(n):
    return "00000000-0000-4000-8000-" + str(n).zfill(12)


class HotlinkTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.source = self.root / "original.pln"
        self.module = self.root / "module.pln"
        self.scratch = self.root / "scratch.pln"
        self.state = self.root / "hotlink-state"
        self.source.write_bytes(b"original BIM test PLN")
        self.module.write_bytes(b"source hotlink fixture")
        self.origin = {"x": 42.0, "y": 0.0, "z": 0.0}

    def stage(self):
        return H.stage(self.source, self.module, self.scratch,
                       self.state, self.origin, 19724)

    def test_declared_native_parameters_match_exact_1510_schema(self):
        doc = json.loads((ROOT / "schemas/tapir-live-1.5.10/tapir-scene-live.json")
                         .read_text(encoding="utf8"))
        names = ("GetHotlinks", "CreateHotlinkNodes", "CreateHotlinkInstances")
        for name in names:
            self.assertIn(name, doc["commands"])
        n = V.node_parameters(self.module)
        i = V.instance_parameters(uid(10), self.origin)
        self.assertEqual(set(n), {"hotlinkNodes"})
        self.assertEqual(set(n["hotlinkNodes"][0]),
                         {"sourceLocation", "name", "storyRangeType"})
        self.assertEqual(set(i), {"hotlinkInstances"})
        self.assertEqual(set(i["hotlinkInstances"][0]),
                         {"hotlinkNodeId", "origin", "rotationAngle",
                          "mirrored", "floorIndex"})
        self.assertEqual(doc["commands"]["CreateHotlinkNodes"]["parameters"]
                         ["required"], ["hotlinkNodes"])
        self.assertEqual(doc["commands"]["CreateHotlinkInstances"]["parameters"]
                         ["required"], ["hotlinkInstances"])

    def test_exact_bim_graph_compiles_two_one_write_hotlink_tasks(self):
        router = H.APA.native_command_router(
            H.SCHEMA_PATH, include_functional_modules=False)
        for command, params in (
            (V.NODE, V.node_parameters(self.module)),
            (V.INSTANCE, V.instance_parameters(uid(2), self.origin)),
        ):
            router.review_policy(command, "CREATE", "MODEL", {
                "source": H.SOURCE_REF,
                "sha256": router.contract_hash(command)})
            preview = H.APA.prepare_native_task(router, {
                "schemaVersion": "apa-native-task/1",
                "request": "Exactly one reviewed disposable Hotlink call",
                "graph": {"operations": [{"id": "OneHotlinkStep",
                        "command": command, "params": params, "after": []}]}
            })
            self.assertFalse(preview["workflow"]["executionPermission"])
            self.assertEqual(len(preview["workflow"]["graph"]["operations"]), 1)
            self.assertEqual(preview["workflow"]["executionOrder"], ["OneHotlinkStep"])

    def test_staging_copies_only_disposable_pln_and_binds_hashes(self):
        s = self.stage()
        self.assertEqual(s["status"], "STAGED_NOT_EXECUTED")
        self.assertEqual(H.digest(self.scratch), H.digest(self.source))
        self.assertEqual(H.digest(self.source),
                         hashlib.sha256(b"original BIM test PLN").hexdigest())
        self.assertEqual(H.digest(self.module),
                         hashlib.sha256(b"source hotlink fixture").hexdigest())
        self.assertEqual(H.guard_manifest(self.state), s)
        self.assertFalse((self.state / "attempted.json").exists())
        self.assertFalse((self.state / "scenewriter.sqlite").exists())

    def test_duplicate_staging_denied_and_original_unchanged(self):
        self.stage()
        with self.assertRaisesRegex(ValueError, "UNIQUE_EXISTING_SOURCES"):
            self.stage()
        self.assertEqual(self.source.read_bytes(), b"original BIM test PLN")
        self.assertEqual(self.scratch.read_bytes(), b"original BIM test PLN")

    def test_invalid_origin_and_same_file_denied(self):
        for origin in (
            {"x": float("nan"), "y": 0.0, "z": 0.0},
            {"x": 1.0, "y": 0.0},
            {"x": 0.0, "y": 0.0, "z": float("inf")},
        ):
            with self.assertRaises(ValueError):
                H.stage(self.source, self.module, self.scratch,
                        self.state, origin, 19724)
        with self.assertRaisesRegex(ValueError, "UNIQUE_EXISTING_SOURCES"):
            H.stage(self.source, self.source, self.scratch,
                    self.state, self.origin, 19724)

    def test_no_replay_after_attempt_reserved(self):
        self.stage()
        H.write_new(self.state / "attempted.json", {"attempted": True})
        with self.assertRaisesRegex(ValueError, "ONCE_ONLY"):
            H.guard_manifest(self.state)
        self.assertFalse((self.state / "scenewriter.sqlite").exists())

    def test_source_or_test_copy_tamper_denied(self):
        self.stage()
        self.module.write_bytes(b"changed hotlink module")
        with self.assertRaisesRegex(ValueError, "PROTECTED_FILES"):
            H.guard_manifest(self.state)

    def test_hotlink_node_before_after_independent_readback(self):
        prior = [(V.canonical_location("C:/already.mod"), uid(1))]
        def api(command, params):
            self.assertEqual(command, "GetHotlinks")
            children = [{"location": "C:/already.mod",
                         "hotlinkNodeId": {"guid": uid(1)}}]
            if api.created:
                children.append({"location": str(self.module),
                                 "hotlinkNodeId": {"guid": uid(2)}})
            return {"hotlinks": children}
        api.created = False
        ver = V.installed_hotlink_verifiers(self.module, V.digest(self.module),
                                             self.origin)["VerifiedHotlinkNodeOneShot"]
        params = V.node_parameters(self.module)
        before = ver.before(api=api, command=V.NODE, parameters=params,
                            affected=[], native_before={"elements": [{"guid": uid(5)}]})
        self.assertEqual(before["existing"], prior)
        api.created = True
        after = ver.after(api=api, command=V.NODE, parameters=params,
                          native_response={"hotlinkNodes": [{"hotlinkNodeId":
                            {"guid": uid(2)}, "existing": False}]},
                          before_guids={uid(5)}, after_guids={uid(5)}, affected=[],
                          native_before={}, native_after={}, source_proof=before)
        self.assertEqual(after["status"], "HOTLINK_NODE_NATIVE_READBACK_PASS")

    def test_reject_existing_node_or_forged_node_response(self):
        ver = V.installed_hotlink_verifiers(self.module, V.digest(self.module),
                                             self.origin)["VerifiedHotlinkNodeOneShot"]
        api = Mock(return_value={"hotlinks": [{"location": str(self.module),
                     "hotlinkNodeId": {"guid": uid(2)}}]})
        with self.assertRaisesRegex(ValueError, "ALREADY_HAS_NODE"):
            ver.before(api=api, command=V.NODE,
                       parameters=V.node_parameters(self.module),
                       affected=[], native_before={"elements": [{"guid": uid(5)}]})
        with self.assertRaisesRegex(ValueError, "NOT_NEW"):
            V.parse_node_reply({"hotlinkNodes": [{"hotlinkNodeId":
                               {"guid": uid(2)}, "existing": True}]})

    def test_instance_ownership_readback_and_wrong_owner_rejection(self):
        node, instance, old, child = uid(2), uid(3), uid(5), uid(6)
        state = {"wrong": False}
        def api(command, params):
            if command == "GetHotlinks":
                return {"hotlinks": [{"location": str(self.module),
                        "hotlinkNodeId": {"guid": node}}]}
            if command == "GetDetailsOfElements":
                self.assertEqual(len(params["elements"]), 1)
                if params["elements"][0]["elementId"]["guid"] == instance:
                    return {"detailsOfElements": [self.instance_root(node)]}
                return {"detailsOfElements": [{"hotlinkId": {
                    "guid": uid(8) if state["wrong"] else instance
                }}]}
            self.fail("Unexpected native command: " + command)
        ver = V.installed_hotlink_verifiers(self.module, V.digest(self.module),
                    self.origin, verified_node_guid=node)["VerifiedHotlinkInstanceOneShot"]
        params = V.instance_parameters(node, self.origin)
        before = ver.before(api=api, command=V.INSTANCE, parameters=params,
                            affected=[], native_before={"elements": [{"guid": old}]})
        kw = dict(api=api, command=V.INSTANCE, parameters=params,
                  native_response={"elements": [{"elementId": {"guid": instance}}]},
                  before_guids={old}, after_guids={old, instance, child},
                  affected=[], native_before={}, native_after={},
                  source_proof=before)
        self.assertEqual(ver.after(**kw)["importedElementCount"], 1)
        state["wrong"] = True
        with self.assertRaisesRegex(ValueError, "NOT_OWNED"):
            ver.after(**kw)

    def test_original_router_scenewriter_and_no_auto_open(self):
        source = (ROOT / "scripts/apa_ac29_hotlink_oneshot.py").read_text()
        self.assertIn("RUN.SceneWriter(", source)
        self.assertIn("build_existing_workflow_scopes(", source)
        self.assertIn("APA.run_native_task(", source)
        self.assertIn('router.execute(', source)
        self.assertIn("GuardedSaveTransport", source)
        self.assertIn('state / "attempted.json"', source)
        self.assertNotIn('api("OpenProject"', source)
        self.assertNotIn('RUN.tapir(manifest["port"], "OpenProject"', source)
        self.assertIn("reopenVerified", source)
        self.assertIn("baselineGuids", source)
        self.assertNotIn("default=[100.0", source)

    def test_reopen_blocked_without_verified_native_save(self):
        self.stage()
        with self.assertRaises(FileNotFoundError):
            H.verify_reopen(self.state)

    def node_reply(self):
        return {"hotlinkNodes": [{"existing": False, "hotlinkNodeId": {"guid": uid(2)}}]}

    def instance_root(self, node):
        return {"type":"Hotlink", "floorIndex":0, "details": {
            "hotlinkType":"Module", "hotlinkNodeId":{"guid":node},
            "origin":dict(self.origin), "rotationAngle":0, "mirrored":False}}

    def test_root_requires_exact_native_node_and_transform(self):
        row = self.instance_root(uid(2))
        api = Mock(return_value={"detailsOfElements":[row]})
        self.assertEqual(V.verify_instance_root(api,uid(2),uid(3),self.origin),row)
        row['details']['hotlinkNodeId']['guid'] = uid(8)
        with self.assertRaisesRegex(ValueError, 'NODE_OR_TRANSFORM'):
            V.verify_instance_root(api,uid(2),uid(3),self.origin)
        row['details']['hotlinkNodeId']['guid'] = uid(2)
        row['details']['origin']['x'] += 1
        with self.assertRaisesRegex(ValueError, 'NODE_OR_TRANSFORM'):
            V.verify_instance_root(api,uid(2),uid(3),self.origin)

    def test_unplaced_node_is_pending_and_first_instance_still_requires_readback(self):
        registry = V.installed_hotlink_verifiers(self.module, V.digest(self.module), self.origin)
        v = registry["VerifiedHotlinkNodeOneShot"]
        pending = v.after(api=Mock(return_value={"hotlinks": []}), command=V.NODE,
                          parameters=V.node_parameters(self.module), native_response=self.node_reply(),
                          before_guids={uid(5)}, after_guids={uid(5)}, affected=[],
                          native_before={}, native_after={}, source_proof={"existing": []})
        self.assertEqual(pending["status"], "HOTLINK_UNPLACED_NODE_RESPONSE_ONLY_PASS")
        self.assertFalse(pending["independentReadbackVerified"])
        v = V.installed_hotlink_verifiers(self.module, V.digest(self.module), self.origin,
                    verified_node_guid=uid(2), unplaced_node_response=self.node_reply())[
                    "VerifiedHotlinkInstanceOneShot"]
        api = Mock(return_value={"hotlinks": []})
        before = v.before(api=api, command=V.INSTANCE,
                    parameters=V.instance_parameters(uid(2), self.origin), affected=[],
                    native_before={"elements": [{"guid": uid(5)}]})
        with self.assertRaisesRegex(ValueError, "NODE_RELATION_LOST"):
            v.after(api=api, command=V.INSTANCE, parameters={}, native_response={
                    "elements": [{"elementId": {"guid": uid(3)}}]},
                    before_guids={uid(5)}, after_guids={uid(5),uid(6)}, affected=[],
                    native_before={}, native_after={}, source_proof=before)
        with self.assertRaisesRegex(ValueError, "RESPONSE_MISMATCH"):
            V.installed_hotlink_verifiers(self.module, V.digest(self.module), self.origin,
                    verified_node_guid=uid(8), unplaced_node_response=self.node_reply())

    def recovery_fixture(self):
        m = self.stage()
        H.write_new(self.state / 'attempted.json', {'scratchSHA256': m['scratchInitialSHA256']})
        H.write_new(self.state / 'failed.json', {'status': 'STOPPED_NO_REPLAY_RECONCILIATION_REQUIRED'})
        outcome = {'reason': 'ValueError: HOTLINK_NODE_INDEPENDENT_READBACK_DIFFERENT',
                   'command':'CreateHotlinkNodes', 'nativeResponse': self.node_reply(),
                   'intent': {'parameters': V.node_parameters(self.module),
                              'target': {'port':19724, 'path':str(self.scratch)}}}
        with closing(sqlite3.connect(self.state / 'scenewriter.sqlite')) as db, db:
            db.execute('CREATE TABLE scenes(scene_id TEXT,state TEXT,result TEXT)')
            db.execute('CREATE TABLE steps(scene_id TEXT,state TEXT)')
            db.execute('INSERT INTO scenes VALUES(?,?,?)',
                       (H.SCENES[0], 'PARTIAL_OR_UNKNOWN_OUTCOME', json.dumps(outcome)))
            db.execute('INSERT INTO steps VALUES(?,?)', (H.SCENES[0], 'UNKNOWN_OUTCOME'))
        trace = self.state / 'trace-live'
        trace.mkdir()
        raw = [{'command': 'CreateHotlinkNodes', 'parameters': V.node_parameters(self.module),
                'response': self.node_reply()}, {'command':'GetHotlinks', 'response':{'hotlinks':[]}}]
        (trace / 'raw.jsonl').write_text('\n'.join(json.dumps(r) for r in raw), encoding='utf8')
        return m, outcome

    def test_recovery_pins_original_response_and_never_replays_node(self):
        m, _ = self.recovery_fixture()
        self.assertEqual(H.unplaced_node_evidence(self.state,m), self.node_reply())
        H.write_new(self.state / 'resume-attempted.json', {'reserved': True})
        with self.assertRaisesRegex(ValueError, 'RESUME_ONCE_ONLY'):
            H.unplaced_node_evidence(self.state,m)
        with self.assertRaisesRegex(ValueError, 'ONCE_ONLY'):
            H.guard_manifest(self.state)

    def test_recovery_rejects_timeout_or_different_native_target(self):
        m, outcome = self.recovery_fixture()
        for field, value in [('reason','TimeoutError: unknown'), ('target','C:/foreign.pln')]:
            mutated = json.loads(json.dumps(outcome))
            if field == 'reason': mutated['reason'] = value
            else: mutated['intent']['target']['path'] = value
            with closing(sqlite3.connect(self.state / 'scenewriter.sqlite')) as db, db:
                db.execute('UPDATE scenes SET result=?', (json.dumps(mutated),))
            with self.assertRaises(ValueError):
                H.unplaced_node_evidence(self.state,m)

    def test_recovery_rejects_any_prior_instance_dispatch(self):
        m, _ = self.recovery_fixture()
        p = self.state / 'trace-live/raw.jsonl'
        with p.open('a', encoding='utf8') as f:
            f.write('\n' + json.dumps({'command':'CreateHotlinkInstances','parameters':{},'response':{}}))
        with self.assertRaisesRegex(ValueError, 'COMPLETE_NATIVE_RESPONSE'):
            H.unplaced_node_evidence(self.state,m)

    def test_pending_ledger_proof_is_hash_bound_and_preserves_unknown(self):
        m, outcome = self.recovery_fixture()
        from apa_ac29_dynamic_write_scopes import validate_existing_ledger
        raw = json.dumps(outcome)
        proof = {'schema':'APA_AC29_UNPLACED_HOTLINK_RECONCILIATION_V1',
                 'status':'NODE_RESPONSE_PINNED_FIRST_INSTANCE_READBACK_PENDING',
                 'sceneId':H.SCENES[0], 'originalResultSHA256':hashlib.sha256(raw.encode()).hexdigest(),
                 'originalUnknownPreserved':True, 'modelWrites':0, 'nativeNodeGuid':uid(2)}
        path = self.state/'scenewriter.sqlite'
        self.assertEqual(validate_existing_ledger(path,H.SCENES[1],proof),
                         [(H.SCENES[0],'PARTIAL_OR_UNKNOWN_OUTCOME')])
        for key,value in [('originalResultSHA256','0'*64),('nativeNodeGuid',uid(8)),
                          ('modelWrites',1),('originalUnknownPreserved',False)]:
            with self.assertRaises(ValueError):
                validate_existing_ledger(path,H.SCENES[1],{**proof,key:value})
        with self.assertRaisesRegex(ValueError,'ALREADY_USED_NEVER_RETRY'):
            validate_existing_ledger(path,H.SCENES[0],proof)
        with closing(sqlite3.connect(path)) as db:
            self.assertEqual(db.execute('SELECT state FROM scenes').fetchone()[0],
                             'PARTIAL_OR_UNKNOWN_OUTCOME')


if __name__ == "__main__":
    unittest.main()
