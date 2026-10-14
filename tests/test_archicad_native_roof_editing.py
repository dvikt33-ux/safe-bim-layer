import copy,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import archicad_native_roof_editing as R
import archicad_authored_extension as E
G='00000000-0000-4000-8000-000000000001';A='00000000-0000-4000-8000-000000000002';B='00000000-0000-4000-8000-000000000003'


class RoofTests(unittest.TestCase):
    def setUp(self):
        self.source=dict(type='Roof',floorIndex=1,details=dict(structureType='Basic',thickness=.2,zCoordinate=6.5,buildingMaterialId=dict(guid=G),holes=[]))
    def test_source_rectangle_emits_two_native_slopes_with_common_ridge(self):
        p=R.rectangle_recipe(G,self.source,20,30,12,8,'GABLE',25,.4)
        self.assertEqual(len(p['roofsData']),2);self.assertEqual(p['expectedPlanes'],2)
        a,b=p['roofsData'];self.assertEqual(a['polygonCoordinates'][2],b['polygonCoordinates'][1]);self.assertEqual(a['polygonCoordinates'][3],b['polygonCoordinates'][0]);self.assertEqual(a['floorIndex'],1);self.assertEqual(a['level'],6.5);self.assertEqual(a['buildingMaterialId'],self.source['details']['buildingMaterialId'])
        self.assertEqual(p['engineering'],'NOT_VERIFIED')
    def test_hip_prefers_one_true_multiplane_with_explicit_overhang(self):
        p=R.rectangle_recipe(G,self.source,20,30,12,8,'HIP',30,.4);self.assertEqual(len(p['roofsData']),1);self.assertNotIn('pivotLine',p['roofsData'][0]);self.assertEqual(p['roofsData'][0]['eavesOverhang'],.4);self.assertEqual(p['expectedPlanes'],4)
    def test_source_holes_are_not_silently_discarded(self):
        self.source['details']['holes']=[{}]
        with self.assertRaisesRegex(ValueError,'HOLE_ROUTING'):R.rectangle_recipe(G,self.source,20,30,12,8,'HIP',30)
    def test_degenerate_hip_ridge_and_nonfinite_dimensions_denied(self):
        for width,angle in [(8,30),(12,float('nan'))]:
            with self.assertRaises(ValueError):R.rectangle_recipe(G,self.source,20,30,width,8,'HIP',angle)
    def test_paired_edit_cannot_touch_a_retained_roof_or_repeat_target(self):
        params=dict(roofsWithDetails=[dict(elementId=dict(guid=A),angle=.4),dict(elementId=dict(guid=B),angle=.4)])
        R.qualify_operation('ModifyRoofs',params,{A,B},{G})
        with self.assertRaisesRegex(ValueError,'OUTSIDE_EXPERIMENT'):R.qualify_operation('ModifyRoofs',params,{A},{B,G})
        params['roofsWithDetails'][1]['elementId']['guid']=A
        with self.assertRaisesRegex(ValueError,'DUPLICATE_TARGET'):R.qualify_operation('ModifyRoofs',params,{A,B},{G})
    def test_contour_edit_requires_complete_explicit_hole_contract(self):
        params=dict(roofsWithDetails=[dict(elementId=dict(guid=A),polygonOutline=[dict(x=0,y=0),dict(x=2,y=0),dict(x=2,y=2)])])
        with self.assertRaisesRegex(ValueError,'EXPLICIT_HOLES'):R.qualify_operation('ModifyRoofs',params,{A},{G})
    def test_source_creation_is_scoped_in_the_existing_writer(self):
        p=R.rectangle_recipe(G,self.source,20,30,12,8,'HIP',30,.4);params=dict(roofsData=p['roofsData'])
        scope=E.model_operation_scope('CreateRoofs',params,'sourcehash',[],[G],'explicitRoofTest');self.assertEqual(scope['command'],'CreateRoofs')
        params['roofsData'][0]['sourceRoofId']['guid']=B
        with self.assertRaisesRegex(ValueError,'OUTSIDE_VERIFIED_SCOPE'):E.model_operation_scope('CreateRoofs',params,'sourcehash',[],[G],'explicitRoofTest')


if __name__=='__main__':unittest.main()
