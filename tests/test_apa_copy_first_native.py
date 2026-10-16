"""Focused tests for native Archicad copy/linear Multiply through existing APA."""
from __future__ import annotations
import sys
from pathlib import Path
import unittest
from unittest.mock import Mock

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from archicad_dynamic_commands import DynamicCommands

MASTER="744a9a2e-985a-434f-b6ea-851a42e6075b"
def router():
    obj=object.__new__(DynamicCommands)
    obj.operation_kind=Mock(return_value="CREATE")
    obj.prepare=Mock(return_value={"command":"MoveElements","effect":"CREATE"})
    obj.execute=Mock()
    return obj

def execute_stub(obj, count, valid=True):
    def run(*args,**kwargs):
        verifier=args[8]
        return {"status":"PASS","readback":verifier(
            {"executionResults":[{"success":True} for _ in range(count)]}, {}
        )}
    obj.execute.side_effect=run

def verify(_reply,_before,n):
    return {"status":"NATIVE_COPY_READBACK_PASS",
            "newPhysicalCopyCount":n,
            "prototypeGuidUnchanged":True}

class TestNativeCopy(unittest.TestCase):
    def test_native_100_copies_use_one_moveelements_with_copy_true(self):
        obj=router()
        execute_stub(obj,100)
        result=obj.copy_linear_series(
            object(),"APA_ARRAY_TEST",MASTER,"Column",100,
            {"x":.6,"y":0,"z":0},{"unmodified":"hash"},"sha",
            "authorization",lambda *_:{"status":"SOURCE_VALID_PASS"},
            lambda a,b:verify(a,b,100))
        params=obj.prepare.call_args.args[1]["elementsWithMoveVectors"]
        self.assertEqual(len(params),100)
        self.assertTrue(all(x["copy"] is True for x in params))
        self.assertEqual(params[0]["moveVector"],{"x":.6,"y":0,"z":0})
        self.assertAlmostEqual(params[-1]["moveVector"]["x"],60)
        self.assertEqual(obj.execute.call_count,1)
        self.assertEqual(result["nativeCopyMetrics"]["requestedCopyCount"],100)
        self.assertEqual(result["readback"]["copyCount"],100)
    def test_native_rectangular_grid_is_one_copy_batch(self):
        obj=router()
        execute_stub(obj,5)
        result=obj.copy_rectangular_array(
            object(),"APA_NATIVE_GRID_TEST",MASTER,"Column",2,3,
            {"x":.6,"y":0,"z":0},{"x":0,"y":1.2,"z":0},
            {"unmodified":"hash"},"sha","authorization",
            lambda *_:{"status":"SOURCE_GRID_PASS"},
            lambda a,b:verify(a,b,5))
        rows=obj.prepare.call_args.args[1]["elementsWithMoveVectors"]
        self.assertEqual(len(rows),5)
        self.assertEqual(obj.execute.call_count,1)
        self.assertEqual({(v["moveVector"]["x"],v["moveVector"]["y"])
                          for v in rows},
                         {(0,1.2),(0,2.4),(.6,0),(.6,1.2),(.6,2.4)})
        self.assertEqual(result["readback"]["copyCount"],5)

    def test_equal_distribution_between_extreme_points_uses_one_native_call(self):
        obj=router()
        execute_stub(obj,10)
        result=obj.distribute_evenly_between(
            object(),"EQUAL_10_STUDS",MASTER,"Column",
            {"x":6.0,"y":0,"z":0},11,
            {"unmodified":"hash"},"sha","auth",
            lambda *_:{"status":"SOURCE_PASS"},
            lambda a,b:verify(a,b,10))
        rows=obj.prepare.call_args.args[1]["elementsWithMoveVectors"]
        self.assertEqual(len(rows),10)
        self.assertEqual(obj.execute.call_count,1)
        self.assertEqual([round(row["moveVector"]["x"],3) for row in rows],
                         [round(.6*i,3) for i in range(1,11)])
        self.assertEqual(result["nativeCopyMetrics"]["requestedCopyCount"],10)

    def test_polyline_distribution_preserves_source_and_places_uniformly(self):
        obj=router()
        execute_stub(obj,5)
        result=obj.distribute_along_polyline(
            object(),"POLYLINE_6_STUDS",MASTER,"Column",
            [{"x":0,"y":0,"z":0},{"x":3,"y":0,"z":0},{"x":3,"y":3,"z":0}],
            6,{"unmodified":"hash"},"sha","auth",
            lambda *_:{"status":"SOURCE_PASS"},lambda a,b:verify(a,b,5))
        rows=obj.prepare.call_args.args[1]["elementsWithMoveVectors"]
        pos=[(round(x["moveVector"]["x"],3),round(x["moveVector"]["y"],3))
             for x in rows]
        self.assertEqual(pos,[(1.2,0),(2.4,0),(3,.6),(3,1.8),(3,3)])
        self.assertEqual(obj.execute.call_count,1)
        self.assertEqual(result["nativeCopyMetrics"]["requestedCopyCount"],5)

    def test_source_distribution_rejects_duplicate_or_bad_grid(self):
        obj=router()
        with self.assertRaisesRegex(ValueError,"DISTRIBUTE_APPROVED_NONZERO_SPAN"):
            obj.distribute_evenly_between(
                object(),"s",MASTER,"Column",{"x":0,"y":0,"z":0},4,
                {},"sha","auth",lambda *_:{"status":"PASS"},
                lambda *_:{"status":"PASS"})
        with self.assertRaisesRegex(ValueError,"ZERO_LENGTH_SEGMENT"):
            obj.distribute_along_polyline(
                object(),"s",MASTER,"Column",
                [{"x":0,"y":0,"z":0},{"x":0,"y":0,"z":0}],
                4,{},"sha","auth",lambda *_:{"status":"PASS"},
                lambda *_:{"status":"PASS"})
        with self.assertRaisesRegex(ValueError,"NATIVE_COPY_NO_DUPLICATE_OR_ZERO_OFFSET"):
            obj.copy_rectangular_array(
                object(),"s",MASTER,"Column",2,2,
                {"x":1,"y":0,"z":0},{"x":2,"y":0,"z":0},
                {},"sha","auth",lambda *_:{"status":"PASS"},
                lambda *_:{"status":"PASS"})
        obj.execute.assert_not_called()

    def test_no_zero_duplicate_or_unknown_host(self):
        obj=router()
        for vectors in ([{"x":0,"y":0,"z":0}],
                        [{"x":.5,"y":0,"z":0},{"x":.5,"y":0,"z":0}]):
            with self.assertRaisesRegex(ValueError,"NATIVE_COPY_NO_DUPLICATE_OR_ZERO_OFFSET"):
                obj.copy_existing_many(object(),"s",MASTER,"Column",
                    vectors,{},"sha","a",
                    lambda *_:{"status":"PASS"},lambda a,b:verify(a,b,len(vectors)))
        with self.assertRaisesRegex(ValueError,"MUST_BE_AFFECTED"):
            obj.copy_existing_many(object(),"s",MASTER,"Column",
                [{"x":1,"y":0,"z":0}],{MASTER:"signature"},"sha",
                "a",lambda *_:{"status":"PASS"},lambda a,b:verify(a,b,1))
        obj.execute.assert_not_called()
    def test_only_reviewed_move_elements_copy_policy(self):
        obj=router()
        obj.operation_kind.return_value="UNKNOWN"
        with self.assertRaisesRegex(ValueError,"EXPLICIT_CREATE_POLICY"):
            obj.copy_existing_many(object(),"s",MASTER,"Column",
                [{"x":1,"y":0,"z":0}],{},"sha",
                "a",lambda *_:{"status":"PASS"},lambda a,b:verify(a,b,1))
        obj.execute.assert_not_called()
    def test_no_create_on_bad_result(self):
        obj=router()
        obj.execute.side_effect=lambda *args,**kwargs: args[8](
            {"executionResults":[{"success":False}]},{})
        with self.assertRaisesRegex(ValueError,"PARTIAL_OR_UNKNOWN"):
            obj.copy_existing_many(object(),"s",MASTER,"Column",
                [{"x":1,"y":0,"z":0}],{},"sha",
                "a",lambda *_:{"status":"PASS"},lambda a,b:verify(a,b,1))
        self.assertEqual(obj.execute.call_count,1)

if __name__=="__main__": unittest.main()
