import copy,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import archicad_project_accelerator as A
import archicad_authored_extension as E
import archicad_native_stair_connection as T
G='00000000-0000-4000-8000-000000000001';CH='00000000-0000-4000-8000-000000000002';OLD='00000000-0000-4000-8000-000000000003'


class StairTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.xml=self.root/'favorite.xml';self.xml.write_text('<Favorites><Favorite><StairDefault><FlightWidth>1</FlightWidth><StepNum>20</StepNum><RiserHeight>0.15</RiserHeight><TreadDepth>0.35</TreadDepth><TotalHeight>3</TotalHeight></StairDefault></Favorite></Favorites>',encoding='utf8')
        self.data=dict(favoriteName='Source favorite',baseLinePoints=[dict(x=2,y=1),dict(x=2,y=7.65)],zCoordinate=0,floorIndex=0,totalHeight=3.3,flightWidth=1,stepNum=20,riserHeight=.165,treadDepth=.35,finishVisible=False)
    def test_native_favorite_dimensions_are_parsed_and_hashed(self):
        source=T.favorite_dimensions(self.xml,'Source favorite');self.assertEqual(source['values']['StepNum'],20);self.assertEqual(source['values']['FlightWidth'],1);self.assertEqual(source['engineeringAcceptance'],'NOT_VERIFIED');self.assertEqual(len(source['sourceSHA256']),64)
    def test_missing_or_inconsistent_source_rejected_without_guessing(self):
        for text in ['<Favorites/>','<Favorites><StairDefault/></Favorites>',self.xml.read_text().replace('<TotalHeight>3','<TotalHeight>4')]:
            self.xml.write_text(text,encoding='utf8')
            with self.assertRaises(ValueError):T.favorite_dimensions(self.xml,'Source')
    def test_stair_requires_full_source_values_and_consistent_rise(self):
        params={'stairsData':[self.data]};scope=E.model_operation_scope('CreateStairs',params,'hash',[G],[OLD],'explicit');E.qualify_model_operation(scope,'CreateStairs',params,'hash')
        self.data['riserHeight']=.15
        with self.assertRaisesRegex(ValueError,'SOURCE_BASELINE'):E.model_operation_scope('CreateStairs',params,'hash',[G],[OLD],'explicit')
    def test_stair_without_named_source_favorite_is_not_accepted(self):
        self.data.pop('favoriteName')
        with self.assertRaises(ValueError):E.model_operation_scope('CreateStairs',{'stairsData':[self.data]},'hash',[G],[OLD],'explicit')
    def test_slab_hole_scope_cannot_modify_foreign_slab(self):
        points=[dict(x=x,y=y) for x,y in [(1,1),(2,1),(2,4),(1,4)]]
        with self.assertRaisesRegex(ValueError,'ONLY_NEW_OWNED'):E.model_operation_scope('ModifySlabs',{'slabsWithDetails':[{'elementId':{'guid':OLD},'holes':[{'polygonCoordinates':points}]}]},'hash',[G],[OLD],'explicit')
    def test_existing_holes_cannot_be_silently_discarded(self):
        with self.assertRaisesRegex(ValueError,'DISCARD_EXISTING'):T.hole_from_native_stair({'bounds':{}},{'details':{'holes':[{}]}})
    def test_void_uses_actual_brep_bounds_and_must_fit_inside_native_slab(self):
        b={'xMin':1,'xMax':2,'yMin':1,'yMax':7.4};slab={'details':{'holes':[],'polygonOutline':[dict(x=x,y=y) for x,y in [(0,0),(4,0),(4,8),(0,8)]]}}
        p=T.hole_from_native_stair({'bounds':b},slab);self.assertEqual(p[2],dict(x=2,y=7.4))
        b['xMax']=8
        with self.assertRaisesRegex(ValueError,'INSIDE_UPPER_SLAB'):T.hole_from_native_stair({'bounds':b},slab)
    def test_native_contour_rotation_closure_and_precision_do_not_require_rewrite(self):
        outer=[dict(x=x,y=y) for x,y in [(0,0),(8,0),(8,8),(0,8),(0,0)]];hole=[dict(x=x,y=y) for x,y in [(1,1),(2,1),(2,7.4),(1,7.4)]]
        before={'floorIndex':1,'details':dict(polygonOutline=outer,holes=[],thickness=.2,zCoordinate=3.3,buildingMaterialId={'guid':G})};after=copy.deepcopy(before)
        after['details']['polygonOutline']=[dict(x=x+5e-8,y=y-5e-8) for x,y in [(8,8),(0,8),(0,0),(8,0),(8,8)]]
        after['details']['holes']=[{'polygonOutline':hole[1:]+hole[:1]+[hole[1]]}]
        self.assertEqual(T.verify_slab_void(before,after,hole)['status'],'NATIVE_SLAB_VOID_CONTOUR_READBACK_PASS')
        after['details']['buildingMaterialId']={'guid':OLD}
        with self.assertRaisesRegex(ValueError,'MATERIAL_CHANGED'):T.verify_slab_void(before,after,hole)
    def test_precise_properties_preserve_solver_mismatch_instead_of_false_pass(self):
        normalized={'elements':[{'guid':G,'type':'Stair','bodies':[]},{'guid':CH,'type':'StairStructure','bodies':[{'vertices':[[2,1,-.1],[3,1,0],[2,7.4,3.3],[3,7.4,3.3]]}]}]}
        def api(c,p):
            if c=='GetSubelementsOfHierarchicalElements':return {'subelements':[{'stairStructures':[{'elementId':{'guid':CH}}]}]}
            if c=='API.GetPropertyIds':return {'properties':[{}]*4}
            if c=='API.GetPropertyValuesOfElements':return {'propertyValuesForElements':[{'propertyValues':[{'propertyValue':dict(status='normal',type='length',value=v)} for v in [.32,.165,1,6.4]]}]}
            return {}
        with patch.object(A.RUN,'requested_details',return_value={'type':'Stair','floorIndex':0}),patch.object(T.C.G,'normalize_dump',return_value=normalized):
            r=T.read_native_stair(api,G,self.data)
        self.assertEqual(r['actualNumericProperties']['Stair_DefaultGoing'],.32);self.assertEqual(r['requestedGoingAcceptance'],'NOT_VERIFIED_NATIVE_SOLVER_CHANGED_GOING');self.assertEqual(r['requestedGoing'],.35)
    def test_native_sill_scope_accepts_zero_and_rejects_nonfinite_values(self):
        params={'windowsWithDetails':[{'elementId':{'guid':G},'sillHeight':0}]};E.model_operation_scope('ModifyWindows',params,'hash',[G],[OLD],'explicit')
        params['windowsWithDetails'][0]['sillHeight']=float('nan')
        with self.assertRaises(ValueError):E.model_operation_scope('ModifyWindows',params,'hash',[G],[OLD],'explicit')
    def test_stair_packet_refuses_existing_new_inventory_before_any_create(self):
        source=T.favorite_dimensions(self.xml,'Source favorite');writer=type('W',(),{})()
        writer.api=lambda c,p:{'elements':[{'elementId':{'guid':G}}]}
        with patch.object(T.E,'execute_model_operation') as mutation:
            with self.assertRaisesRegex(ValueError,'ALREADY_CREATED'):T.execute(writer,dict(source=source,baselineInventory=[]),'must-not-create','hash')
        mutation.assert_not_called()


if __name__=='__main__':unittest.main()
