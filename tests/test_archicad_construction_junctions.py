import copy,sys,unittest
from unittest.mock import patch
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import archicad_details_context as D
from test_archicad_functional_gaps import guid
from test_archicad_functional_expansion import cube
import test_archicad_functional_expansion as TEST_EXP


class JunctionCoverageTests(unittest.TestCase):
    def fixture(self,offset=(0,0,1)):
        rows=[cube((1,1,1)),cube((1,1,1),offset=offset)]
        for i,e in enumerate(rows):
            e['guid']=guid(i+1)
            for face in e['bodies'][0]['faces']:face['contours']=[face['vertices']]+face.get('holes',[])
        context={'units':'m','coordinateSystem':'ABSOLUTE_PROJECT_XYZ','elements':{
            'wall':{'guid':guid(1),'kind':'Wall','floorIndex':0,'bounds':[[[0,1],[0,1],[0,1]]],'materialBindings':{}},
            'floor':{'guid':guid(2),'kind':'Slab','floorIndex':0,'bounds':[[[offset[k],offset[k]+1] for k in range(3)]],'materialBindings':{}}}}
        return context,{'units':'m','coordinateSystem':'ABSOLUTE_PROJECT_XYZ','elements':rows}
    def evaluate(self,offset=(0,0,1),collisions=()):
        c,n=self.fixture(offset);return D.native_junction_coverage(c,n,D.DetailsContext(ROOT),collisions)
    def junction(self,r):return next(f for f in r['families'] if f['family']=='wall_floor')['junctions'][0]
    def test_face_contact_has_actual_area_and_no_engineering_approval(self):
        j=self.junction(self.evaluate());self.assertAlmostEqual(j['sharedAreaSquareMeters'],1)
        self.assertEqual(j['physicalRelation'],'SURFACE_CONTACT');self.assertFalse(j['nativeVolumeIntersection'])
        self.assertEqual(j['engineeringAcceptance'],'NOT_VERIFIED')
    def test_native_overlap_is_separate_from_shared_surface(self):
        j=self.junction(self.evaluate((.5,.5,.5),[(guid(1),guid(2))]))
        self.assertTrue(j['nativeVolumeIntersection']);self.assertEqual(j['physicalRelation'],'VOLUME_INTERSECTION')
        self.assertEqual(j['sharedAreaSquareMeters'],0)
    def test_only_edge_touch_is_not_bearing_area(self):
        j=self.junction(self.evaluate((1,0,1)));self.assertEqual(j['sharedAreaSquareMeters'],0)
        self.assertEqual(j['physicalRelation'],'NO_SHARED_SURFACE')
    def test_hole_is_not_filled_by_contact_analysis(self):
        c,n=self.fixture();body=n['elements'][0]['bodies'][0]
        face=next(f for f in body['faces'] if all(body['vertices'][i][2]==1 for i in f['vertices']))
        index=len(body['vertices']);body['vertices'] += [[.25,.25,1],[.75,.25,1],[.75,.75,1],[.25,.75,1]]
        face['contours'].append(list(range(index,index+4)))
        j=self.junction(D.native_junction_coverage(c,n,D.DetailsContext(ROOT)))
        self.assertAlmostEqual(j['sharedAreaSquareMeters'],.75)
    def test_roof_gap_remains_required_interface(self):
        c,n=self.fixture((0,0,1.5));c['elements']['floor']['kind']='Roof'
        r=D.native_junction_coverage(c,n,D.DetailsContext(ROOT));j=next(f for f in r['families'] if f['family']=='wall_roof')['junctions'][0]
        self.assertEqual(j['physicalRelation'],'NO_SHARED_SURFACE')
    def test_cladding_absent_is_not_pass(self):
        r=self.evaluate();f=next(f for f in r['families'] if f['family']=='cladding_structure')
        self.assertEqual(f['status'],'NOT_PRESENT_OR_NO_BOUND_INTERFACE');self.assertEqual(f['junctions'],[])
    def test_full_source_assembly_gates_preserved(self):
        r=self.evaluate();self.assertEqual(r['contextDetailCount'],73);self.assertEqual(r['sourceDetailCount'],1142)
        self.assertEqual(r['sourceApprovedFullAssemblyCount'],0)
        self.assertEqual(r['armopoyasAndFasteners']['status'],'NOT_VERIFIED')
    def test_nonplanar_face_is_explicitly_unverified(self):
        c,n=self.fixture();n['elements'][0]['bodies'][0]['vertices'][0][2]+=.1
        j=self.junction(D.native_junction_coverage(c,n,D.DetailsContext(ROOT)))
        self.assertEqual(j['physicalRelation'],'NOT_VERIFIED');self.assertIn('NONPLANAR',j['contactAnalysisLimitation'])
    def test_column_segment_geometry_is_attributed_to_native_parent(self):
        c,n=self.fixture();c['elements']['wall']['kind']='Column'
        child=copy.deepcopy(n['elements'][0]);child['guid']=guid(3);n['elements'][0]['bodies']=[]
        n['elements'].append(child);c['columnSegments']={guid(1):[guid(3)]}
        r=D.native_junction_coverage(c,n,D.DetailsContext(ROOT));j=next(f for f in r['families'] if f['family']=='column_floor')['junctions'][0]
        self.assertEqual(j['guids'],[guid(1),guid(2)]);self.assertAlmostEqual(j['sharedAreaSquareMeters'],1)
    def opening_fixture(self):
        c,n=self.fixture();c['elements'].pop('floor');n['elements'].pop()
        e=n['elements'][0]
        for p in e['bodies'][0]['vertices']:p[1]*=.3
        c['elements']['wall']['bounds']=[[[0,1],[0,.3],[0,1]]]
        body=e['bodies'][0]
        for face in body['faces']:
            points=[body['vertices'][i] for i in face['vertices']]
            if max(p[1] for p in points)==min(p[1] for p in points):
                y=points[0][1];index=len(body['vertices'])
                body['vertices'] += [[.25,y,.25],[.75,y,.25],[.75,y,.75],[.25,y,.75]]
                face['holes']=[list(range(index,index+4))];face['contours'].append(face['holes'][0])
        c['elements']['opening']={'guid':guid(9),'kind':'Opening','floorIndex':0,'hostGuid':guid(1),'bounds':[[[.25,.75],[0,.3],[.25,.75]]]}
        return c,n
    def test_opening_geometry_comes_from_actual_host_holes(self):
        c,n=self.opening_fixture();r=D.native_junction_coverage(c,n,D.DetailsContext(ROOT));o=r['hostedOpenings'][0]
        self.assertEqual(o['status'],'ACTUAL_HOST_INNER_CONTOURS_PASS');self.assertEqual(o['nativeHoleBoundsMeters'],[[.25,.75],[0,.3],[.25,.75]])
    def test_opening_proxy_without_host_cut_is_not_pass(self):
        c,n=self.opening_fixture()
        for face in n['elements'][0]['bodies'][0]['faces']:face['holes']=[]
        o=D.native_junction_coverage(c,n,D.DetailsContext(ROOT))['hostedOpenings'][0]
        self.assertEqual(o['status'],'NOT_VERIFIED');self.assertIn('AMBIGUOUS',o['limitation'])


class CounterbattenTests(unittest.TestCase):
    def fixture(self):
        source,context,native,selection=TEST_EXP.SourceSectionTests().fixture()
        material={'buildingMaterial':{'guid':selection['expectedGuid'],'name':selection['name']}}
        native['elements'][0]['materialBindings']=material;context['elements']['roof']['materialBindings']=material
        batten=D.prepare_source_section(ROOT,source,context,native,guid(2),'c4',selection)
        data=batten['plan']['graph']['operations'][0]['params']['morphsData'][0]
        body=cube((10,.15,.025));body['guid']=guid(4);body['homeStory']={'index':1};body['materialBindings']=material
        body['bodies'][0]['vertices']=[D.C.morph_api_world_point(p,data['basePoint'],[data[k] for k in ('xAxis','yAxis','zAxis')]) for p in data['body']['vertices']]
        wall=cube((10,.3,3),(40,47.85,3));wall.update(guid=guid(5),homeStory={'index':1},materialBindings=material)
        native['elements'] += [body,wall]
        context['elements']['batten']={'guid':guid(4),'kind':'Morph','floorIndex':1,'hostGuid':guid(2),'bounds':[D.C.ROOF.bounds(body)],'materialBindings':material}
        context['elements']['wall']={'guid':guid(5),'kind':'Wall','floorIndex':1,'bounds':[D.C.ROOF.bounds(wall)],'materialBindings':material}
        source['inventory']=[guid(2),guid(4),guid(5)]
        return source,context,native
    def part(self):
        s,c,n=self.fixture();return D.prepare_counterbatten_junction(ROOT,s,c,n,guid(4),guid(5))
    def test_source_relation_section_and_model_span_are_pinned(self):
        p=self.part();b=p['binding'];self.assertEqual(b['sourceSectionMeters'],{'width':.05,'height':.05})
        self.assertEqual(b['physicalContact']['sourceRelation'],'battens_supported_by_counterbattens')
        self.assertEqual(b['physicalContact']['expectedAreaSquareMeters'],.0075)
        self.assertEqual(len(b['nativeDependencyBodies']),2);self.assertFalse(b['assemblyWriteAllowed'])
        self.assertEqual(b['modelSpanAuthority']['endY'],47.85)
    def test_predicted_real_source_member_contacts_batten_underside(self):
        s,c,n=self.fixture();p=D.prepare_counterbatten_junction(ROOT,s,c,n,guid(4),guid(5));data=p['plan']['graph']['operations'][0]['params']['morphsData'][0]
        body=cube();body['guid']=guid(6)
        body['bodies'][0]['vertices']=[D.C.morph_api_world_point(v,data['basePoint'],[data[k] for k in ('xAxis','yAxis','zAxis')]) for v in data['body']['vertices']]
        pair={guid(4):n['elements'][1],guid(6):body}
        r=D.C.G.shared_surfaces(pair,{g:g for g in pair});self.assertAlmostEqual(r[0]['sharedAreaSquareMeters'],.0075,places=7)
        v=data['body']['vertices'];a=D.C.morph_api_world_point(v[0],data['basePoint'],[data[k] for k in ('xAxis','yAxis','zAxis')]);z=D.C.morph_api_world_point(v[-2],data['basePoint'],[data[k] for k in ('xAxis','yAxis','zAxis')])
        self.assertGreater(z[1],a[1]);self.assertGreater(z[2],a[2])
    def test_wrong_upper_wall_story_rejected(self):
        s,c,n=self.fixture()
        c['elements']['wall']['floorIndex']=0
        with self.assertRaisesRegex(ValueError,'UPPER_WALL'):D.prepare_counterbatten_junction(ROOT,s,c,n,guid(4),guid(5))
    def test_changed_batten_height_rejected(self):
        s,c,n=self.fixture();body=n['elements'][1]['bodies'][0]
        for i in (1,3,5,7):body['vertices'][i][2]+=.02
        with self.assertRaisesRegex(ValueError,'SECTION_DRIFT'):D.prepare_counterbatten_junction(ROOT,s,c,n,guid(4),guid(5))
    def test_before_write_rejects_wrong_counterbatten_material(self):
        p=self.part();params=copy.deepcopy(p['plan']['graph']['operations'][0]['params']);params['morphsData'][0]['buildingMaterialId']['guid']=guid(99)
        with patch.object(D,'verify_source_section_binding',return_value={}):
            with self.assertRaisesRegex(ValueError,'MATERIAL_MISMATCH'):D.C.NativeAdapter('CreateMorphs').before_write(None,params,p['plan'])
    def test_dependency_material_drift_invalidates_before_write(self):
        p=self.part();b=p['binding'];dep=b['nativeDependencyBodies'][0]
        def body(api,g):
            if g==b['hostGuid']:return {'native':{'homeStory':b['hostHomeStory'],'materialBindings':b['hostMaterialBindings'],'hash':b['hostGeometryHash']}}
            return {'native':{'homeStory':dep['homeStory'],'materialBindings':{},'hash':dep['geometryHash']}}
        with patch('archicad_native_operations.element_body',side_effect=body),patch.object(D.C.ROOF,'geometry_signature',side_effect=lambda n:n['hash']),patch.object(D.C.RUN,'digest',side_effect=lambda v:v),patch('archicad_native_material_selection.resolve',return_value={}):
            with self.assertRaisesRegex(ValueError,'DEPENDENCY_INVALIDATED'):D.verify_source_section_binding(None,b)


class NativeClassificationTests(unittest.TestCase):
    def selection(self):return {'systemName':'Native system','systemVersion':'2.0','systemGuid':guid(20),'itemId':'Beam','itemGuid':guid(21)}
    def read(self,value):
        with patch.object(D,'resolve_existing_classification',return_value={}):
            return D.verify_member_classification(lambda c,p:{'elementClassifications':[{'classificationIds':value}]},guid(6),self.selection())
    def wanted(self):return {'classificationSystemId':{'guid':guid(20)},'classificationItemId':{'guid':guid(21)}}
    def test_actual_direct_classification_row_is_verified(self):self.assertEqual(self.read([self.wanted()])['status'],'ACTUAL_NATIVE_MEMBER_CLASSIFICATION_PASS')
    def test_catalog_wrapped_classification_row_is_verified(self):self.assertEqual(self.read([{'classificationId':self.wanted()}])['status'],'ACTUAL_NATIVE_MEMBER_CLASSIFICATION_PASS')
    def test_wrong_item_or_duplicate_row_is_not_verified(self):
        wrong=self.wanted();wrong['classificationItemId']['guid']=guid(99)
        for rows in ([wrong],[self.wanted(),self.wanted()]):
            with self.assertRaisesRegex(ValueError,'READBACK_MISMATCH'):self.read(rows)
    def test_unrecognized_extra_wrapper_keys_are_rejected(self):
        with self.assertRaisesRegex(ValueError,'READBACK_MISMATCH'):self.read([{'classificationId':self.wanted(),'extra':True}])
    def test_changed_native_system_is_rejected(self):
        selection=self.selection()
        api=lambda c,p:{'classificationSystems':[{'name':selection['systemName'],'version':selection['systemVersion'],'classificationSystemId':{'guid':guid(99)}}]}
        with self.assertRaisesRegex(ValueError,'SYSTEM_INVALIDATED'):D.resolve_existing_classification(api,selection)
    def test_unclassifying_is_blocked_by_bounded_writer(self):
        writer=D.C.RUN.SceneWriter(None,'unused',adapters=D.C.adapters(['morph']))
        plan={'sourcePlanHash':'hash','binding':{}}
        params={'elementClassifications':[{'elementId':{'guid':guid(6)},'classificationId':{'classificationSystemId':{'guid':guid(20)}}}]}
        scene='negative-classification-explicit-item';command='SetClassificationsOfElements'
        digest=D.C.RUN.digest({'sceneId':scene,'sourcePlanHash':'hash','command':command,'parameters':params,'target':{}})
        with self.assertRaisesRegex(ValueError,'EXPLICIT_ITEM'):writer.execute_bound_operation(plan,scene,command,params,digest,lambda:None,lambda a,b:None)


if __name__=='__main__':unittest.main()
