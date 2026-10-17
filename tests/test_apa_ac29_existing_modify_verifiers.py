"""Focused material-only ModifySlabs source and readback tests."""
import copy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import apa_ac29_existing_modify_verifiers as M
import apa_ac29_dynamic_native_verifiers as REG

SLAB="b8d528f0-ab6a-4ece-a62d-74e3a0d7c46c"
BASE="e7ef3819-b3e8-419f-b313-5172e6b0412c"
TARGET="d7ef3819-b3e8-419f-b313-5172e6b0412c"


def params():
    return {"slabsWithDetails":[{
        "elementId":{"guid":SLAB},
        "structureType":"Basic",
        "buildingMaterialId":{"guid":TARGET}}]}


def typed(material=BASE):
    return {"type":"Slab","floorIndex":0,"details":{
        "structureType":"Basic","thickness":0.2,
        "level":0.,"zCoordinate":0.,
        "polygonOutline":[{"x":0.,"y":0.},{"x":2.,"y":0.},
                          {"x":2.,"y":2.}],
        "buildingMaterialId":{"guid":material}}}


def native(material=BASE,geom="same"):
    return {"elements":[{"guid":SLAB,"type":"Slab",
        "relationships":{},
        "materialBindings":{"buildingMaterial":{"guid":material}},
        "bodies":[{"closed":True,"vertices":[[0.,0.,0.],[2.,0.,0.],
                                           [2.,2.,-.2]]}],
        "fixtureGeometry":geom}]}


class SlabMaterialContracts(unittest.TestCase):
    def test_registered_modify_only_not_create_slab(self):
        rows=REG.installed_verifiers()
        self.assertEqual(rows["VerifiedBasicSlabMaterial"].command,"ModifySlabs")
        self.assertEqual(rows["VerifiedBasicSlabMaterial"].effect,"MODIFY")
        self.assertFalse(any(row.command=="CreateSlabs"
                             for row in rows.values()))

    def test_current_tapir_modifyslabs_explicit_material_schema(self):
        import json
        catalog=json.loads((Path(__file__).resolve().parents[1]/
            "schemas/tapir-live-1.5.10/tapir-scene-live.json").read_text())
        native_props=catalog["commands"]["ModifySlabs"]["parameters"]["properties"][
            "slabsWithDetails"]["items"]["properties"]
        self.assertLessEqual(set(params()["slabsWithDetails"][0]),set(native_props))
        self.assertEqual(M.material_request(params()),(SLAB,TARGET))

    def test_unapproved_geometry_or_multiple_slabs_rejected(self):
        p=params();p["slabsWithDetails"][0]["thickness"]=.4
        with self.assertRaisesRegex(ValueError,"MATERIAL_OF_EXISTING_BASIC_SLAB"):
            M.material_request(p)
        p=params();p["slabsWithDetails"].append(copy.deepcopy(p["slabsWithDetails"][0]))
        with self.assertRaisesRegex(ValueError,"ONE_NATIVE_SCOPED"):
            M.material_request(p)

    def test_before_and_after_material_change_reuses_native_BREP_proof(self):
        with patch("archicad_scene_run.requested_details",side_effect=[
                typed(BASE),typed(TARGET)]), \
             patch("archicad_connected_components.ROOF.geometry_signature",
                   side_effect=lambda row:row["fixtureGeometry"]):
            before=M.verify_slab_material_before(
                api=None,command="ModifySlabs",parameters=params(),
                affected=[SLAB],native_before=native())
            self.assertTrue(before["status"].endswith("PASS"))
            after=M.verify_slab_material_after(
                api=None,command="ModifySlabs",parameters=params(),
                native_response={"executionResults":[{"success":True}]},
                before_guids={SLAB},after_guids={SLAB},
                affected=[SLAB],native_before=native(),
                native_after=native(TARGET),source_proof=before)
            self.assertTrue(after["status"].endswith("PASS"))

    def test_changed_slab_geometry_refused_even_if_material_is_right(self):
        with patch("archicad_scene_run.requested_details",side_effect=[
                typed(BASE),typed(TARGET)]), \
             patch("archicad_connected_components.ROOF.geometry_signature",
                   side_effect=lambda row:row["fixtureGeometry"]):
            before=M.verify_slab_material_before(
                api=None,command="ModifySlabs",parameters=params(),
                affected=[SLAB],native_before=native())
            with self.assertRaisesRegex(ValueError,"BREP_OR_MATERIAL_DRIFT"):
                M.verify_slab_material_after(
                    api=None,command="ModifySlabs",parameters=params(),
                    native_response={"executionResults":[{"success":True}]},
                    before_guids={SLAB},after_guids={SLAB},
                    affected=[SLAB],native_before=native(),
                    native_after=native(TARGET,"altered"),source_proof=before)

    def test_dependent_slab_rejected_before_write(self):
        data=native()
        data["elements"].append({
            "guid":"c8d528f0-ab6a-4ece-a62d-74e3a0d7c46c",
            "type":"Opening","relationships":{"hostGuid":SLAB},"bodies":[]})
        with self.assertRaisesRegex(ValueError,"DEPENDENT_ELEMENTS"):
            M.verify_slab_material_before(
                api=None,command="ModifySlabs",parameters=params(),
                affected=[SLAB],native_before=data)


if __name__=="__main__":
    unittest.main()
