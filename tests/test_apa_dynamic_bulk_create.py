"""Focused proof that APA bulk path produces ONE native SceneWriter call per batch.

No mock Archicad production writes: exercises command/host safety and the
existing DynamicCommands.execute() delegation.
"""
import sys
from pathlib import Path
import unittest
from unittest.mock import Mock

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from archicad_dynamic_commands import DynamicCommands

HOST="7b332594-ab82-43b4-bfc2-ab5ad549c2c9"
def item(offset,width=1.0):
    return {"ownerWallId":{"guid":HOST},"centerOffset":offset,
            "width":width,"height":1.5,"sillHeight":.9}
def fixture():
    x=object.__new__(DynamicCommands)
    x.prepare=Mock(return_value={"effect":"CREATE","command":"CreateWindows"})
    x.execute=Mock()
    return x

def perform(router,items, proof=None):
    router.execute.side_effect=lambda *args,**kwargs: args[9](
        {"elements":[{"elementId":{"guid":"new-%02d"%i}} for i in range(len(items))]},
        {"modelBefore":"state"})
    return router.execute_batch(
        object(),"BDD_BULK_PERF_TEST","CreateWindows",items,[HOST],
        {}, "savedSHA", "authorization", "MODEL",
        proof or (lambda response,before:{"status":"NATIVE_GEOMETRY_PASS"}),
        verify_before=lambda *_:{"status":"SOURCE_HOST_PASS"})

class BatchRouteTests(unittest.TestCase):
    def test_bulk_100_is_a_single_scene_writer_delegation(self):
        router=fixture()
        rows=[item(1+i*2.0) for i in range(100)]
        result=perform(router,rows)
        self.assertEqual(result["nativeBatchCount"],100)
        self.assertEqual(len(result["nativeBatchGuids"]),100)
        self.assertEqual(router.execute.call_count,1)
        router.prepare.assert_called_once()
        self.assertEqual(len(router.prepare.call_args.args[1]["windowsData"]),100)
    def test_wall_host_must_be_approved_and_non_overlapping(self):
        router=fixture()
        with self.assertRaisesRegex(ValueError,"COLLISION"):
            perform(router,[item(3,1.6),item(3.5,1.6)])
        with self.assertRaisesRegex(ValueError,"HOST_NOT_IN_AFFECTED"):
            router.execute_batch(object(),"s","CreateWindows",[item(3)],
                                 ["NOT_THE_HOST"],{}, "sha","auth","MODEL",
                                 lambda *_:{"status":"PASS"},
                                 verify_before=lambda *_:{"status":"PASS"})
        router.execute.assert_not_called()
    def test_fail_closed_on_native_return_count_or_duplicate(self):
        router=fixture()
        def broken(*args,**kwargs):
            return args[9]({"elements":[{"elementId":{"guid":"same"}},
                                         {"elementId":{"guid":"same"}}]}, {})
        router.execute.side_effect=broken
        with self.assertRaisesRegex(ValueError,"DUPLICATE"):
            router.execute_batch(object(),"s","CreateWindows",[item(3),item(6)],
                                 [HOST],{}, "sha","auth","MODEL",
                                 lambda *_:{"status":"PASS"},
                                 verify_before=lambda *_:{"status":"PASS"})
    def test_no_unknown_command_or_unbounded_batches(self):
        router=fixture()
        for cmd in ("DeleteElements","ModifyWalls","SaveProject","OpenProject"):
            with self.assertRaisesRegex(ValueError,"NOT_SOURCE_QUALIFIED"):
                router.execute_batch(object(),"s",cmd,[item(3)],[HOST],{},
                     "sha","auth","MODEL",lambda *_:{"status":"PASS"},
                     verify_before=lambda *_:{"status":"PASS"})
        with self.assertRaisesRegex(ValueError,"1_TO_200"):
            perform(router,[item(3+i*2) for i in range(201)])
        router.execute.assert_not_called()

if __name__=="__main__": unittest.main()
