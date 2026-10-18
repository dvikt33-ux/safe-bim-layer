"""Fail-closed offline contracts for native Hotlink one-shot on disposable PLN."""
from __future__ import annotations

import hashlib
import json
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


if __name__ == "__main__":
    unittest.main()
