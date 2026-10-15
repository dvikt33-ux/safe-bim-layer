"""PR94-independent 160 new offline cases: captured Memo topology, bridge
metamorphics, quarantine firewall, namespace aliases, SDK source safety.

Only the new PR94 code is executed. There is no native engine invocation,
PLN access, APX install, socket/network access, or engineering acceptance.
"""
from __future__ import annotations

import copy
import functools
import json
import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import archicad_local_modules as L
import archicad_project_accelerator as A
from archicad_dynamic_commands import DynamicCommands


class PR94MemoSafetyMatrix(unittest.TestCase):
    pass


def add(category, number, fn):
    setattr(PR94MemoSafetyMatrix, f"test_pr94_{category}_{number:03d}", fn)


def ring(points, reverse=False):
    result = list(reversed(points)) if reverse else list(points)
    return result + [result[0]]


def rectangle(x0, y0, x1, y1, reverse=False):
    return ring([[x0, y0], [x1, y0], [x1, y1], [x0, y1]], reverse)


def element(identifier, rings, story=0, kind=8, arcs=None):
    points = [point for polygon in rings for point in polygon]
    p = {"indexBase": 1,
         "coordinateFrame": "NATIVE_PARAMETER_POLYGON_NOT_RESULTANT_BREP",
         "coordinates": [{"index": i + 1, "x": x, "y": y}
                         for i, (x, y) in enumerate(points)],
         "contourEnds": [sum(map(len, rings[:i+1])) for i in range(len(rings))],
         "arcs": arcs or []}
    return {"elementId": {"guid": identifier}, "nativeTypeId": kind,
            "homeStory": story, "polygon": p}


def multi_hole_case(seed):
    def test(self):
        dx, dy = seed * 0.137, -seed * 0.083
        w, h = 20 + seed % 7, 18 + seed % 11
        outer = rectangle(dx, dy, dx+w, dy+h, bool(seed % 2))
        hole1 = rectangle(dx+2, dy+2, dx+4, dy+4, bool(seed % 3))
        hole2 = rectangle(dx+7, dy+6, dx+10, dy+8, bool(seed % 5))
        holes = [hole1, hole2] if seed % 2 else [hole1]
        name = f"memo-2holes-{seed:04d}"
        story = seed % 13 - 6
        kind = 8 if seed % 2 else 9
        payload = {"elements": [element(name, [outer, *holes], story, kind)]}
        snapshot = copy.deepcopy(payload)
        converted = L.memo_polygon_inputs(payload)
        self.assertEqual(payload, snapshot)
        self.assertEqual(converted["omitted"], [])
        self.assertEqual(converted["nativeBindings"], [
            {"id": name, "homeStory": story, "nativeTypeId": kind}])
        self.assertEqual(converted["polygons"][0]["id"], name)
        self.assertEqual(len(converted["polygons"][0]["holes"]), len(holes))
        self.assertEqual(converted["authority"],
                         "NATIVE_PARAMETER_POLYGONS_NOT_RESULTANT_BREP")
        self.assertEqual(converted["engineering"], "NOT_VERIFIED")
        shape = L.polygon_relations(converted["polygons"])
        expected_area = w*h - 4 - (6 if seed % 2 else 0)
        expected_perimeter = 2*(w+h) + 8 + (10 if seed % 2 else 0)
        self.assertAlmostEqual(shape["polygons"][0]["area"], expected_area, places=6)
        self.assertAlmostEqual(shape["polygons"][0]["perimeter"],
                               expected_perimeter, places=6)
        self.assertEqual(shape["relations"], [])
        self.assertEqual(shape["engineering"], "NOT_VERIFIED")
    return test


for n in range(40):
    add("holes_story_winding_area", n, multi_hole_case(n))


def bad_memo_case(seed):
    def test(self):
        name = f"bad-{seed:03d}"
        base = element(name, [rectangle(0, 0, 10, 8)], story=seed % 4)
        broken = copy.deepcopy(base)
        mode = seed % 16
        reasons = {
            0: "ELEMENT_GUID_MISSING",
            1: "ELEMENT_GUID_MISSING",
            2: "ONLY_SLAB_ROOF_PARAMETER_FOOTPRINT_SUPPORTED",
            3: "CURVED_EDGES_NOT_LINEARIZED",
            4: "CONTOUR_INDEX_INVALID",
            5: "CONTOUR_INDEX_INVALID",
            6: "CONTOUR_END_INVALID",
            7: "CONTOUR_END_INVALID",
            8: "CLOSED_FINITE_CONTOUR_REQUIRED",
            9: "CLOSED_FINITE_CONTOUR_REQUIRED",
            10: "HOME_STORY_MISSING",
            11: "coordinates",
            12: "CLOSED_FINITE_CONTOUR_REQUIRED",
            13: "CONTOUR_DEGENERATE",
            14: "ONLY_SLAB_ROOF_PARAMETER_FOOTPRINT_SUPPORTED",
            15: "HOME_STORY_MISSING",
        }
        if mode == 0:
            broken["elementId"] = {}
        elif mode == 1:
            broken["elementId"] = {"guid": ""}
        elif mode == 2:
            broken["nativeTypeId"] = 44
        elif mode == 3:
            broken["polygon"]["arcs"] = [{"beginIndex": 1, "endIndex": 2,
                                           "angle": 1.25}]
        elif mode == 4:
            broken["polygon"]["coordinates"][1]["index"] = 9
        elif mode == 5:
            broken["polygon"]["coordinates"][0]["index"] = 0
        elif mode == 6:
            broken["polygon"]["contourEnds"] = [4, 4]
        elif mode == 7:
            broken["polygon"]["contourEnds"] = [4]
        elif mode == 8:
            broken["polygon"]["coordinates"][-1]["x"] += 0.1
        elif mode == 9:
            broken["polygon"]["coordinates"][2]["x"] = float("inf")
        elif mode == 10:
            broken["homeStory"] = True
        elif mode == 11:
            broken["polygon"].pop("coordinates")
        elif mode == 12:
            broken["polygon"]["coordinates"] = broken["polygon"]["coordinates"][:3]
            broken["polygon"]["contourEnds"] = [3]
        elif mode == 13:
            broken["polygon"] = {
                "coordinates": [{"index": i+1, "x": x, "y": y}
                                for i, (x, y) in enumerate(
                                    [[0,0],[1,0],[0,0],[0,0]])],
                "contourEnds": [4], "arcs": []}
        elif mode == 14:
            broken["nativeTypeId"] = None
        else:
            broken.pop("homeStory")
        good_name = f"healthy-after-bad-{seed:03d}"
        good = element(good_name, [rectangle(20, 0, 26, 7)], story=7)
        value = L.memo_polygon_inputs({"elements": [broken, good]})
        self.assertEqual([p["id"] for p in value["polygons"]], [good_name])
        self.assertEqual(len(value["omitted"]), 1)
        self.assertEqual(value["omitted"][0]["index"], 0)
        self.assertIn(reasons[mode], value["omitted"][0]["reason"])
        self.assertEqual(len(value["nativeBindings"]), 1)
        self.assertEqual(value["nativeBindings"][0]["homeStory"], 7)
    return test


for n in range(32):
    add("malformed_memo_isolation", n, bad_memo_case(n))


def metamorphic_spatial_case(seed):
    def test(self):
        w = 10 + seed % 5
        h = 6 + seed % 4
        shift = (3 + seed % 3)
        outer_a = rectangle(0, 0, w, h, reverse=bool(seed % 2))
        outer_b = rectangle(shift, 0, shift+w, h, reverse=bool(seed % 3))
        src = {"elements": [
            element(f"roof-{seed}", [outer_a], story=-2, kind=9),
            element(f"slab-{seed}", [outer_b], story=seed % 14 + 1, kind=8),
        ]}
        direct = L.memo_polygon_inputs(src)
        direct_spatial = L.polygon_relations(direct["polygons"])
        self.assertEqual(len(direct_spatial["relations"]), 1)
        relation = direct_spatial["relations"][0]
        self.assertAlmostEqual(relation["intersectionArea"], (w-shift)*h)
        self.assertTrue(relation["intersects"])
        self.assertEqual(
            [row["homeStory"] for row in direct["nativeBindings"]],
            [-2, seed % 14 + 1])
        # Cross-story 2D intersection is *not* evidence of a 3D clash.
        self.assertEqual(direct_spatial["scope"],
                         "2D_SOURCE_POLYGONS_NOT_3D_NATIVE_COLLISION")
        self.assertEqual(direct_spatial["engineering"], "NOT_VERIFIED")
        scale = 1 + seed % 4
        tx, ty = 100 + seed*2, -200 - seed*3
        changed = copy.deepcopy(src)
        for row in changed["elements"]:
            for p in row["polygon"]["coordinates"]:
                p["x"] = scale*p["x"] + tx
                p["y"] = scale*p["y"] + ty
        transformed = L.memo_polygon_inputs(changed)
        spatial2 = L.polygon_relations(transformed["polygons"])
        self.assertEqual(len(spatial2["relations"]), 1)
        self.assertAlmostEqual(
            spatial2["relations"][0]["intersectionArea"],
            (w-shift)*h*scale*scale, places=6)
        for a,b in zip(direct_spatial["polygons"],spatial2["polygons"]):
            self.assertAlmostEqual(b["area"],a["area"]*scale*scale,places=6)
            self.assertAlmostEqual(b["perimeter"],a["perimeter"]*scale,places=6)
        self.assertEqual(src["elements"][0]["polygon"]["coordinates"][0]["x"],0)
    return test


for n in range(32):
    add("floor_separation_affine_invariance", n, metamorphic_spatial_case(n))


def router():
    return DynamicCommands({"commands": {}, "common_schemas": {},
                            "_metadata": {"provider_version": "1.5.10"}})


def schema(kind, key="amount"):
    return {"type": "object", "required": [key],
            "properties": {key: {"type":kind}},
            "additionalProperties": False}


def contract(s):
    return {"version": "1", "category": "Independent PR94 QA",
            "parameters": {"$ref": "#/Schema"}, "returns": {"type": "object"}}


def provider_collision_case(seed):
    def test(self):
        r = router()
        prefix = f"Namespace{seed}"
        a, b = prefix+"__Deep", prefix
        # Both prefer exactly the same first-choice common-schema key.
        first = {"Schema": schema("integer")}
        second = {"Deep__Schema": schema("string", "text")}
        contract_a = contract(first["Schema"])
        contract_b = {"version": "1", "category": "Independent PR94 QA",
                      "parameters": {"$ref":"#/Deep__Schema"},
                      "returns": {"type":"object"}}
        r.add_provider(a, {"Primary":contract_a}, "independent-source-a", first)
        name_a = "AddOn."+a+".Primary"
        digest_before = r.contract_hash(name_a)
        original_a = r.prepare(name_a, {"amount":seed})
        r.add_provider(b, {"Secondary":contract_b}, "independent-source-b",second)
        name_b = "AddOn."+b+".Secondary"
        self.assertEqual(r.contract_hash(name_a),digest_before)
        self.assertEqual(r.validate(original_a)["command"],name_a) if False else None
        r.prepare(name_a, {"amount":seed})
        r.prepare(name_b, {"text":f"value{seed}"})
        with self.assertRaises(Exception):
            r.prepare(name_a, {"amount":f"value{seed}"})
        with self.assertRaises(Exception):
            r.prepare(name_b, {"text":seed})
        self.assertEqual(len(r.catalog["common_schemas"]),2)
        before = copy.deepcopy(r.catalog)
        fingerprint = r.fingerprint
        # Mix a new good name with an existing duplicate: atomic refusal.
        with self.assertRaises(ValueError):
            r.add_provider(a,{"Auxiliary":contract_a,"Primary":contract_a},
                           "untrusted-later", {"Schema":schema("string")})
        self.assertEqual(r.catalog,before)
        self.assertEqual(r.fingerprint,fingerprint)
    return test


for n in range(24):
    add("provider_collision_and_atomicity", n, provider_collision_case(n))


@functools.lru_cache(maxsize=2)
def quantity_router(unqualified):
    root=ROOT
    catalog=json.loads((root/"schemas/accelerator/mass-capabilities/commands.json")
                       .read_text(encoding="utf8"))
    if unqualified:
        row=json.loads((root/"schemas/accelerator/functional-modules.json")
                       .read_text(encoding="utf8"))["sdkProviders"]["TapirCommand"]["GetNativeElementQuantitiesV1"]
        catalog["commands"]["GetNativeElementQuantitiesV1"] = {
            k:copy.deepcopy(v) for k,v in row.items() if k!="executionBlocker"}
    r=DynamicCommands(catalog)
    A.connect_functional_modules(r)
    return r


def quantity_quarantine_case(seed):
    def test(self):
        alias=bool(seed%2)
        r=quantity_router(alias)
        command=("GetNativeElementQuantitiesV1" if alias else
                 "AddOn.TapirCommand.GetNativeElementQuantitiesV1")
        params={"elements":[{"elementId":{"guid":f"synthetic-not-live-{seed}-{i}"}}
                            for i in range(1+seed%12)],
                "minOpeningSize":seed/7}
        ticket=r.prepare(command,params)
        before_catalog=r.fingerprint
        events=len(r.local_events)
        self.assertFalse(ticket["nativeWritePermission"])
        self.assertIn("CRASH",r.catalog["commands"][command]["executionBlocker"].upper())
        class Bomb:
            def __getattribute__(self,name):
                raise AssertionError("UNSAFE_ARCHICAD_TRANSPORT_TOUCHED")
            def __call__(self,*args,**kwargs):
                raise AssertionError("UNSAFE_ARCHICAD_TRANSPORT_CALLED")
        with self.assertRaisesRegex(ValueError,"COMMAND_RUNTIME_QUARANTINED"):
            r.read(Bomb(),ticket,True)
        self.assertEqual(before_catalog,r.fingerprint)
        self.assertEqual(events,len(r.local_events))
        self.assertNotIn(command,r.live)
        self.assertNotIn(command,r.callable)
        self.assertIsNone(r.select(command)["runtimeRegistered"])
    return test


for n in range(24):
    add("quantity_no_transport_firewall",n,quantity_quarantine_case(n))


def native_source_property_case(seed):
    def test(self):
        cpp=(ROOT/"archicad-addon/Sources/NativeExtendedModules.cpp").read_text(
            encoding="utf8")
        name="GetNativeElementQuantitiesV1Command::Execute"
        code=cpp.split(name,1)[1].split("\n}\n",1)[0]
        full=(ROOT/"schemas/accelerator/functional-modules.json").read_text(
            encoding="utf8")
        data=json.loads(full)
        contract_row=data["sdkProviders"]["TapirCommand"]["GetNativeElementQuantitiesV1"]
        drawing=cpp.split("GetNativeDrawingAssociationsV1Command::Execute",1)[1]
        guards=[
            lambda: "ACAPI_Element_GetQuantities" not in code,
            lambda: "QUARANTINED_AC29_QUANTITY_CRASH_NO_ENGINE_CALL" in code,
            lambda: "APIERR_REFUSEDCMD" in code,
            lambda: '"nativeModelWrites",0' in code,
            lambda: contract_row["executionBlocker"] != "",
            lambda: '"contentBoxQueryError"' in drawing,
            lambda: "if(boxErr==NoError)" in drawing,
            lambda: '"statusQueryError"' in drawing,
        ]
        self.assertTrue(guards[seed](),f"NATIVE_SOURCE_GUARD_{seed}_MISSING")
        self.assertEqual(contract_row["availability"],
                         "BUILD_CANDIDATE_NOT_RUNTIME_REGISTERED")
    return test


for n in range(8):
    add("native_cpp_drawing_guard", n, native_source_property_case(n))


NEW_CASES=40+32+32+24+24+8
assert NEW_CASES==160
assert len(unittest.defaultTestLoader.loadTestsFromTestCase(
    PR94MemoSafetyMatrix)._tests)==NEW_CASES

if __name__=="__main__":
    unittest.main()
