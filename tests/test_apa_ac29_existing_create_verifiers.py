"""Focused reuse of AC29 Beam/Wall/Roof native readback contracts."""
import copy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import apa_ac29_existing_create_verifiers as X
import apa_ac29_dynamic_native_verifiers as REG

OLD="a8d528f0-ab6a-4ece-a62d-74e3a0d7c46c"
NEW="b8d528f0-ab6a-4ece-a62d-74e3a0d7c46c"
SEG="c8d528f0-ab6a-4ece-a62d-74e3a0d7c46c"
MAT="e7ef3819-b3e8-419f-b313-5172e6b0412c"


def material():
    return {"guid":MAT}


def beam():
    return {"beamsData":[{
        "begCoordinate":{"x":10.,"y":10.},
        "endCoordinate":{"x":12.,"y":10.},
        "zCoordinate":0.,"floorIndex":0,"offset":0.,
        "slantAngle":0.,"isSlanted":False,"profileAngle":0.,
        "arcAngle":0.,"verticalCurveHeight":0.,
        "width":.1,"height":.2,"anchorPoint":"Center",
        "circleBased":False,"isWidthAndHeightLinked":False,
        "buildingMaterialId":material()
    }]}


def wall():
    return {"wallsData":[{
        "begCoordinate":{"x":10.,"y":10.},
        "endCoordinate":{"x":12.,"y":10.},
        "zCoordinate":0.,"floorIndex":0,"height":2.9,
        "thickness":.2,"structureType":"Basic",
        "buildingMaterialId":material(),
        "referenceLineLocation":"Center"
    }]}


def slab():
    return {"slabsData":[{
        "polygonCoordinates":[{"x":10.,"y":10.},{"x":12.,"y":10.},
                              {"x":12.,"y":12.},{"x":10.,"y":12.}],
        "level":0.,"thickness":.2,"floorIndex":0,
        "structureType":"Basic","buildingMaterialId":material()
    }]}


def roof():
    return {"roofsData":[{
        "polygonCoordinates":[{"x":10.,"y":10.},{"x":12.,"y":10.},
                              {"x":12.,"y":12.},{"x":10.,"y":12.}],
        "pivotLine":{"begCoordinate":{"x":10.,"y":10.},
                     "endCoordinate":{"x":12.,"y":10.}},
        "level":0.,"angle":.2,"eavesOverhang":0.,
        "thickness":.2,"floorIndex":0,
        "structureType":"Basic","buildingMaterialId":material()
    }]}


def brep(kind,verts,owner=None):
    return {
        "guid": SEG if owner else NEW,
        "type":kind,
        "relationships":{"hostGuid":owner} if owner else {},
        "materialBindings":{"buildingMaterial":material()},
        "bodies":[{"closed":True,"vertices":verts,"faces":[
            {"contours":[[0,1,2]]}]}]
    }


class RegistryCoverage(unittest.TestCase):
    def test_existing_registry_retained_and_three_new_commands(self):
        available=REG.installed_verifiers()
        existing={("CreateColumns","CREATE"),("MoveElements","MODIFY"),
                  ("CreateBeams","CREATE"),("CreateWalls","CREATE"),
                  ("CreateRoofs","CREATE"),("ModifySlabs","MODIFY")}
        actual={(row.command,row.effect) for row in available.values()}
        self.assertTrue(existing <= actual, "Previously verified native handlers must remain installed")
        self.assertEqual(actual-existing,
                         {("AddOn.TapirCommand.CloneNativeGroupV1","CREATE")},
                         "Only the newly reviewed group-clone verifier may extend the registry")
        self.assertIn("VerifiedNativeGroupClone", available)

    def test_strict_basic_source_all_three_families(self):
        for command,params in [
            ("CreateBeams",beam()),("CreateWalls",wall()),
            ("CreateRoofs",roof())]:
            with self.subTest(command=command):
                row, box=X.checked_source(command,params)
                self.assertEqual(row["floorIndex"],0)
                self.assertEqual(len(box),3)

    def test_source_keys_match_real_1_5_10_live_export(self):
        import json
        root=Path(__file__).resolve().parents[1]
        catalog=json.loads((root/"schemas/tapir-live-1.5.10/tapir-scene-live.json").read_text())
        for command,params in (("CreateBeams",beam()),
                               ("CreateWalls",wall()),
                               ("CreateRoofs",roof())):
            slot=next(iter(params))
            props=catalog["commands"][command]["parameters"]["properties"][slot]["items"]["properties"]
            self.assertLessEqual(set(params[slot][0]),set(props),
                                 "Native source must use current Tapir export only")

        slab_props=catalog["commands"]["CreateSlabs"]["parameters"]["properties"]["slabsData"]["items"]["properties"]
        self.assertNotIn("buildingMaterialId",slab_props)
        self.assertNotIn("structureType",slab_props)

    def test_beam_native_profile_is_checked_using_existing_adapter_contract(self):
        bad=beam()
        bad["beamsData"][0]["isSlanted"]=True
        with self.assertRaisesRegex(ValueError,"BASIC_HORIZONTAL_BEAM"):
            X.checked_source("CreateBeams",bad)
        bad=beam()
        bad["beamsData"][0]["unknownGdlField"]=1
        with self.assertRaisesRegex(ValueError,"BASIC_HORIZONTAL_BEAM"):
            X.checked_source("CreateBeams",bad)

    def test_slab_remains_blocked_when_native_create_cannot_set_material(self):
        p=slab()
        with self.assertRaisesRegex(ValueError,"UNSUPPORTED_COMMAND"):
            X.checked_source("CreateSlabs",p)

    def test_roof_needs_exact_single_plane_pivot_and_eaves(self):
        p=roof()
        p["roofsData"][0].pop("eavesOverhang")
        with self.assertRaisesRegex(ValueError,"SINGLE_PLANE_BASIC_ROOF"):
            X.checked_source("CreateRoofs",p)
        p=roof()
        p["roofsData"][0]["angle"]=0
        with self.assertRaisesRegex(ValueError,"SINGLE_PLANE_BASIC_ROOF"):
            X.checked_source("CreateRoofs",p)


    def test_reject_wall_nonlinear_or_nonzero_story(self):
        p=wall();p["wallsData"][0]["arcAngle"]=.3
        with self.assertRaisesRegex(ValueError,"BASIC_STRAIGHT_WALL"):
            X.checked_source("CreateWalls",p)
        p=wall();p["wallsData"][0]["floorIndex"]=1
        with self.assertRaisesRegex(ValueError,"STORY0"):
            X.checked_source("CreateWalls",p)

    def test_preflight_fails_for_existing_solid_contact(self):
        native={"elements":[{
            "guid":OLD,"type":"ColumnSegment",
            "bodies":[{"closed":True,"vertices":[
                [10.5,9.95,0.],[11.5,10.05,0.],[11.5,10.05,2.]]}]
        }]}
        with self.assertRaisesRegex(ValueError,"JUNCTION_NOT_SOURCE_QUALIFIED"):
            X.verify_existing_create_before(
                api=None,command="CreateWalls",
                parameters=wall(),affected=[],native_before=native)

    def test_preflight_accepts_source_without_collision_no_writes(self):
        native={"elements":[{"guid":OLD,"type":"Column","bodies":[]}]}
        p=X.verify_existing_create_before(
            api=None,command="CreateBeams",parameters=beam(),
            affected=[],native_before=native)
        self.assertEqual(p["command"],"CreateBeams")
        self.assertTrue(p["status"].endswith("PASS"))

    def test_verified_wall_reuses_original_typed_readback(self):
        src=wall()
        proof=X.verify_existing_create_before(
            api=None,command="CreateWalls",parameters=src,
            affected=[],native_before={"elements":[
                {"guid":OLD,"type":"Object","bodies":[]}]})
        v=src["wallsData"][0]
        detail={"type":"Wall","floorIndex":0,"details":{
            "begCoordinate":v["begCoordinate"],
            "endCoordinate":v["endCoordinate"],
            "height":v["height"],"begThickness":v["thickness"],
            "endThickness":v["thickness"],"offset":0.,"arcAngle":0.,
            "zCoordinate":0.,"structureType":"Basic",
            "referenceLineLocation":"Center","geometryType":"Straight",
            "buildingMaterialId":material()
        }}
        wall_brep=brep("Wall",[[10.,9.9,0.],[12.,10.1,0.],
                                [12.,10.1,2.9],[10.,9.9,2.9]])
        with patch("archicad_scene_run.requested_details",return_value=detail):
            result=X.verify_existing_create_after(
                api=None,command="CreateWalls",parameters=src,
                native_response={"elements":[{"elementId":{"guid":NEW}}]},
                before_guids={OLD},after_guids={OLD,NEW},
                affected=[],native_before={"elements":[]},
                native_after={"elements":[
                    {"guid":OLD,"type":"Object","bodies":[]},wall_brep]},
                source_proof=proof)
        self.assertTrue(result["status"].endswith("PASS"))

    def test_roof_reuses_existing_native_adapter_readback(self):
        p=roof()
        proof=X.verify_existing_create_before(
            api=None,command="CreateRoofs",parameters=p,
            affected=[],native_before={"elements":[{
                "guid":OLD,"type":"Object","bodies":[]}]})
        roof_body=brep("Roof",[[10.,10.,0.],[12.,10.,0.],
                                [12.,12.,.4],[10.,12.,.4]])
        with patch("archicad_scene_run.requested_details",
                   return_value={"type":"Roof","floorIndex":0,"details":{}}), \
             patch("archicad_connected_components.NativeAdapter.verify",
                   return_value="Roof") as native_verify:
            result=X.verify_existing_create_after(
                api=None,command="CreateRoofs",parameters=p,
                native_response={"elements":[{"elementId":{"guid":NEW}}]},
                before_guids={OLD},after_guids={OLD,NEW},
                affected=[],native_before={"elements":[]},
                native_after={"elements":[{"guid":OLD,"type":"Object","bodies":[]},
                                          roof_body]},
                source_proof=proof)
        self.assertEqual(native_verify.call_count,1)
        self.assertEqual(result["rootGuid"],NEW)

    def test_unexpected_native_guid_delta_never_accepted(self):
        with self.assertRaisesRegex(ValueError,"GUID_DELTA_INVALID"):
            X.verify_existing_create_after(
                api=None,command="CreateBeams",parameters=beam(),
                native_response={"elements":[{"elementId":{"guid":NEW}}]},
                before_guids={OLD},after_guids={OLD,NEW},
                affected=[],native_before={"elements":[]},
                native_after={"elements":[]},
                source_proof={"command":"CreateBeams",
                              "expectedMaterial":MAT})

    def test_beam_reuses_native_adapter_not_new_scalar_checker(self):
        src=beam()
        proof=X.verify_existing_create_before(
            api=None,command="CreateBeams",parameters=src,
            affected=[],native_before={"elements":[
                {"guid":OLD,"type":"Object","bodies":[]}]})
        beam_brep={"guid":NEW,"type":"Beam","relationships":{},
                   "materialBindings":{"buildingMaterial":material()},
                   "bodies":[]}
        seg_brep=brep("BeamSegment",[
            [10.,9.95,-.1],[12.,10.05,.1],[10.,10.05,.1]
        ],owner=NEW)
        with patch("archicad_scene_run.requested_details",
                   return_value={"type":"Beam","floorIndex":0,"details":{}}), \
             patch("archicad_connected_components.NativeAdapter.verify",
                   return_value="Beam") as verify:
            result=X.verify_existing_create_after(
                api=None,command="CreateBeams",parameters=src,
                native_response={"elements":[{"elementId":{"guid":NEW}}]},
                before_guids={OLD},after_guids={OLD,NEW,SEG},
                affected=[],native_before={"elements":[]},
                native_after={"elements":[
                    {"guid":OLD,"type":"Object","bodies":[]},
                    beam_brep,seg_brep]},
                source_proof=proof)
        self.assertEqual(verify.call_count,1)
        self.assertEqual(result["childGuids"],[SEG])


if __name__=="__main__":
    unittest.main()
