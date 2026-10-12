import copy,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import archicad_native_operations as N
import archicad_wall_roof_assessment as B
import test_archicad_roof_underside as U
from test_archicad_functional_gaps import guid


class RealJunctionAssessmentTests(unittest.TestCase):
    def fixture(self):
        w,r,_=U.UndersideGeometryTests().fixture()
        for v in w['bodies'][0]['vertices']:
            if v[2]>5.9:v[2]=6.
        for e,g in ((w,guid(1)),(r,guid(2))):
            e.update(guid=g,materialBindings={'buildingMaterial':{'guid':guid(3)}})
        wd={'type':'Wall','floorIndex':1,'details':{'geometryType':'Straight','arcAngle':0,'profileType':'Normal',
            'structureType':'Basic','height':3.,'relativeTopStory':0,'isAutoOnStoryVisibility':False}}
        rd={'type':'Roof','floorIndex':1,'details':{'roofClass':'SinglePlane','structureType':'Basic','holes':[]}}
        links={'solidLinksWithTheGivenTarget':[],'solidLinksWithTheGivenOperator':[]}
        return w,r,wd,rd,links
    def assess(self,fixture=None):return N.assess_wall_roof_junction(*(fixture or self.fixture()))
    def test_full_coverage_gap_qualifies_exact_height_then_seo_not_execution(self):
        a=self.assess();self.assertEqual(a['status'],'APPLICABLE_NOT_EXECUTED')
        self.assertEqual(a['measurementStatus'],'VERIFIED');self.assertFalse(a['repairExecuted'])
        self.assertAlmostEqual(a['gap']['coverageFraction'],1.)
        self.assertEqual([s['command'] for s in a['operationCandidates']],['ModifyWalls','CreateSolidElementLinks'])
        self.assertEqual(a['operationCandidates'][0]['params']['wallsWithDetails'][0]['height'],a['temporaryUncutTopZ']-3)
    def test_partial_roof_overlap_cannot_be_declared_complete_repair(self):
        w,r,*rest=self.fixture()
        for v in w['bodies'][0]['vertices']:v[0]-=5.
        a=self.assess((w,r,*rest));self.assertEqual(a['status'],'NOT_APPLICABLE')
        self.assertGreater(a['gap']['uncoveredCapAreaSquareMeters'],0)
        self.assertFalse(a['executionAllowed']);self.assertIn('DOES_NOT_COVER',a['reasons'][0])
    def test_roof_hole_crossing_cap_remains_uncovered(self):
        w,r,*rest=self.fixture();body=r['bodies'][0];plane=N.roof_underside_plane(r)
        face=next(f for f in body['faces'] if all(abs(sum(plane['normal'][k]*body['vertices'][i][k] for k in range(3))-plane['distance'])<1e-6 for i in f['contours'][0]))
        ring=[]
        for x,y in [(44.9,42),(45.1,42),(45.1,43),(44.9,43)]:
            ring.append(len(body['vertices']));body['vertices'].append([x,y,(plane['distance']-plane['normal'][1]*y)/plane['normal'][2]])
        face['contours'].append(ring)
        a=self.assess((w,r,*rest));self.assertEqual(a['status'],'NOT_APPLICABLE')
        self.assertAlmostEqual(a['gap']['uncoveredCapAreaSquareMeters'],.2)
    def test_nonoverlap_returns_not_verified_not_a_bbox_pass(self):
        w,r,*rest=self.fixture()
        for v in w['bodies'][0]['vertices']:v[0]+=100
        a=self.assess((w,r,*rest));self.assertEqual(a['status'],'NOT_VERIFIED');self.assertFalse(a['executionAllowed'])
    def test_unknown_native_tool_is_not_a_morph_fallback(self):
        f=list(self.fixture());f[0]['type']='Morph'
        self.assertEqual(self.assess(f)['status'],'NOT_VERIFIED')
    def test_story_mismatch_is_not_applicable(self):
        f=list(self.fixture());f[0]['homeStory']=2
        self.assertEqual(self.assess(f)['status'],'NOT_VERIFIED')
    def test_curved_geometry_cannot_be_treated_as_planar_native_body(self):
        f=list(self.fixture());f[0]['bodies'][0]['curved']=True
        self.assertEqual(self.assess(f)['status'],'NOT_VERIFIED')
    def test_top_link_and_auto_visibility_need_separate_source_plan(self):
        for field,value in [('relativeTopStory',1),('isAutoOnStoryVisibility',True)]:
            f=list(self.fixture());f[2]['details'][field]=value
            self.assertEqual(self.assess(f)['status'],'NOT_VERIFIED')
    def test_ambiguous_seo_readback_stops_qualification(self):
        f=list(self.fixture());f[-1]={}
        self.assertEqual(self.assess(f)['status'],'NOT_VERIFIED')
    def test_existing_seo_dependency_has_no_automatic_replay(self):
        f=list(self.fixture());f[-1]['solidLinksWithTheGivenTarget']=[{'operatorId':{'guid':guid(4)}}]
        self.assertEqual(self.assess(f)['status'],'NOT_APPLICABLE')
    def test_nonintersecting_roof_hole_is_still_not_qualified_with_unknown_flag(self):
        f=list(self.fixture());f[3]['details']['holes']=[{'polygon':[]}]
        a=self.assess(f);self.assertEqual(a['status'],'NOT_APPLICABLE');self.assertIn('SKIP_FLAG',a['reasons'][0])
    def test_batch_joins_existing_details_and_one_shared_dependency(self):
        w,r,wd,rd,links=self.fixture();native={'units':'m','coordinateSystem':'ABSOLUTE_PROJECT_XYZ','elements':[w,r]}
        result=B.assess_batch(native,[{'id':'west','wallGuid':guid(1),'roofGuid':guid(2)}],
            {guid(1):wd,guid(2):rd},{guid(1):links},{'families':[{'family':'wall_roof','sourceCandidates':[{'detailId':'source'}]}]})
        self.assertEqual(result['junctions'][0]['existingDetailsSourceCandidates'][0]['detailId'],'source')
        self.assertEqual(result['sharedDependencyGraph']['edges'],[[guid(2),guid(1)]])
        self.assertEqual(result['nativeWrites'],0)
    def test_batch_rejects_duplicate_targets(self):
        w,r,wd,rd,links=self.fixture();t={'id':'west','wallGuid':guid(1),'roofGuid':guid(2)}
        with self.assertRaisesRegex(ValueError,'DUPLICATE'):
            B.assess_batch({'units':'m','coordinateSystem':'ABSOLUTE_PROJECT_XYZ','elements':[w,r]},[t,t],{guid(1):wd,guid(2):rd},{guid(1):links})
    def test_modified_assessment_hash_rejects_plan(self):
        a=self.assess();a['operationCandidates'][0]['params']['wallsWithDetails'][0]['height']+=1
        with self.assertRaisesRegex(ValueError,'NOT_QUALIFIED'):N.prepare_wall_roof_repair({},a)
    def test_partial_assessment_cannot_prepare_write(self):
        a=self.assess();a['status']='NOT_APPLICABLE'
        with self.assertRaisesRegex(ValueError,'NOT_QUALIFIED'):N.prepare_wall_roof_repair({},a)
    def test_no_separate_copy_approval_prevents_native_write(self):
        a=self.assess();plan={'integrationBindings':{'dependencies':{'wallRoofRepair':a}},'binding':{'path':r'Q:\fixture\copy.pln'},'sourcePlanHash':'reviewed'}
        writer=N.C.RUN.SceneWriter(lambda c,p:self.fail('Native API called before approval'),':memory:')
        with self.assertRaisesRegex(ValueError,'AUTHORIZATION_REQUIRED'):
            N.execute_wall_roof_repair(writer,plan,{}, {},'repair')
    def test_bounded_writer_rejects_arbitrary_wall_height_without_assessment(self):
        writer=N.C.RUN.SceneWriter(lambda c,p:self.fail('Native API called before qualification'),':memory:')
        params={'wallsWithDetails':[{'elementId':{'guid':guid(1)},'height':7.}]}
        plan={'sourcePlanHash':'reviewed','binding':{}}
        intent={'sceneId':'repair','sourcePlanHash':'reviewed','command':'ModifyWalls','parameters':params,'target':{}}
        with self.assertRaisesRegex(ValueError,'QUALIFIED_EXACT_JUNCTION'):
            writer.execute_bound_operation(plan,'repair','ModifyWalls',params,N.C.RUN.digest(intent),lambda:{},lambda r,b:{})
    def reviewed_plan(self):
        import hashlib
        a=self.assess()
        binding={'path':r'Q:\fixture\copy.pln','name':'copy','port':19724,'tapirVersion':'1.5.10','storyIndex':1}
        source={'inventory':[guid(1),guid(2)],'preflight':{'binding':binding,
            'storyBindings':[{'nativeIndex':1,'floorId':2,'level':3.,'label':'upper'}],
            'schemaVersion':'1.5.10','schemaSha256':hashlib.sha256(N.C.RUN.DEFAULT_SCENE_SCHEMA.read_bytes()).hexdigest()}}
        return a,N.prepare_wall_roof_repair(source,a)
    def test_actual_catalog_compiles_ordered_native_operations(self):
        a,plan=self.reviewed_plan();self.assertEqual(plan['executionOrder'],['raise-wall','seo-underside'])
        self.assertEqual(plan['graph']['operations'],a['operationCandidates'])
    def authorized(self,plan):
        return {'scope':'ONE_WALL_HEIGHT_AND_UNDERSIDE_SEO_IN_SEPARATE_COPY','sourcePlanHash':plan['sourcePlanHash'],
            'wallGuid':guid(1),'copyBinding':plan['binding'],'protectedSourcePath':r'Q:\fixture\original.pln',
            'savedSha256':'0'*64,'humanAuthorizationRef':'Explicit synthetic fixture approval'}
    def baseline(self):return {'inventory':[guid(1),guid(2)],'geometrySignatures':{guid(1):'wall',guid(2):'roof'}}
    def test_source_file_cannot_be_approved_as_the_copy(self):
        a,plan=self.reviewed_plan();auth=self.authorized(plan);auth['protectedSourcePath']=plan['binding']['path']
        with self.assertRaisesRegex(ValueError,'AUTHORIZATION_REQUIRED'):
            N.execute_wall_roof_repair(None,plan,self.baseline(),auth,'repair')
    def test_changed_reviewed_plan_cannot_execute(self):
        a,plan=self.reviewed_plan();auth=self.authorized(plan);plan['graph']['operations'][0]['params']['wallsWithDetails'][0]['height']+=.1
        with self.assertRaisesRegex(ValueError,'REVIEWED_PLAN_CHANGED'):
            N.execute_wall_roof_repair(None,plan,self.baseline(),auth,'repair')
    def test_unknown_height_outcome_never_dispatches_seo(self):
        a,plan=self.reviewed_plan();calls=[]
        class Writer:
            def execute_bound_operation(self,*args):
                calls.append(args[2]);return {'status':'PARTIAL_OR_UNKNOWN_OUTCOME'}
        result=N.execute_wall_roof_repair(Writer(),plan,self.baseline(),self.authorized(plan),'repair')
        self.assertEqual(calls,['ModifyWalls']);self.assertTrue(result['manualReconciliationRequired'])
    def test_synthetic_sequence_uses_existing_writer_and_does_not_claim_save_open(self):
        a,plan=self.reviewed_plan();calls=[]
        class Writer:
            def execute_bound_operation(self,*args):
                calls.append(args[2]);return {'status':'PASS'}
        result=N.execute_wall_roof_repair(Writer(),plan,self.baseline(),self.authorized(plan),'repair')
        self.assertEqual(calls,['ModifyWalls','CreateSolidElementLinks'])
        self.assertEqual(result['persistence'],'SAVE_OPEN_NOT_VERIFIED')
    def test_source_guard_failure_after_height_stops_without_seo_or_replay(self):
        a,plan=self.reviewed_plan();calls=[]
        class Writer:
            def execute_bound_operation(self,*args):
                calls.append(args[2])
                if len(calls)==2:raise ValueError('ROOF_SOURCE_INVALIDATED')
                return {'status':'PASS'}
        result=N.execute_wall_roof_repair(Writer(),plan,self.baseline(),self.authorized(plan),'repair')
        self.assertEqual(result['status'],'PARTIAL_OR_UNKNOWN_OUTCOME')
        self.assertEqual(len(result['operations']),1);self.assertTrue(result['manualReconciliationRequired'])
    def simulated_native_repair(self,new_collision=False,roof_drift=False):
        import hashlib
        a,plan=self.reviewed_plan();w,r,wd,rd,empty=self.fixture()
        native={'elements':[w,r],'materials':[],'units':'m','coordinateSystem':'ABSOLUTE_PROJECT_XYZ'}
        baseline={'inventory':[guid(1),guid(2)],'geometrySignatures':N.C.retained_geometry_signatures(native,[guid(1),guid(2)]),'targetCollisions':[]}
        auth=self.authorized(plan);auth['savedSha256']=hashlib.sha256(b'approved-copy').hexdigest()
        writes=[];linked=False
        def api(command,params):
            nonlocal linked
            if command=='GetProjectInfo':return {'projectName':'copy','projectPath':plan['binding']['path'],'isUntitled':False,'isTeamwork':False}
            if command=='GetStories':return {'actStory':1,'stories':[{'index':1,'floorId':2,'level':3.,'name':'upper'}]}
            if command=='GetAddOnVersion':return {'version':'1.5.10'}
            if command=='GetAllElements':return {'elements':[{'elementId':{'guid':g}} for g in baseline['inventory']]}
            if command=='GetModelDumpV1':return copy.deepcopy(native)
            if command=='GetDetailsOfElements':return {'detailsOfElements':[copy.deepcopy(wd if e['elementId']['guid']==guid(1) else rd) for e in params['elements']]}
            if command=='GetSolidElementLinks':
                row=copy.deepcopy(empty)
                if linked:row['solidLinksWithTheGivenTarget']=[{'operatorId':{'guid':guid(2)},'operation':'SubtractionUpwards','linkFlags':{'inheritOperatorAttributes':False,'skipPolygonHoles':False}}]
                return {'solidLinks':[row]}
            if command=='GetCollisions':return {'collisions':[{'unexpected':'collision'}] if new_collision and len(params['elementsGroup2'])>0 else []}
            if command=='ModifyWalls':
                writes.append(command);wd['details']['height']=params['wallsWithDetails'][0]['height']
                for v in w['bodies'][0]['vertices']:
                    if v[2]>5.9:v[2]=a['temporaryUncutTopZ']
                if roof_drift:r['bodies'][0]['vertices'][0][2]+=.01
                return {'executionResults':[{'success':True}]}
            if command=='CreateSolidElementLinks':
                writes.append(command);linked=True;p=a['gap']['roofUndersidePlane'];n,d=p['normal'],p['distance']
                for v in w['bodies'][0]['vertices']:
                    if v[2]>5.9:v[2]=(d-n[0]*v[0]-n[1]*v[1])/n[2]
                return {'executionResults':[{'success':True}]}
            raise AssertionError(command)
        original_read=Path.read_bytes
        def file_bytes(path):return b'approved-copy' if str(path)==plan['binding']['path'] else original_read(path)
        with tempfile.TemporaryDirectory() as td,patch.object(N.C.G,'normalize_dump',side_effect=copy.deepcopy),patch.object(Path,'read_bytes',file_bytes),\
                patch.object(N.C.RUN,'PORT',19724),patch.object(N.C.RUN,'EXPECTED_PATH',plan['binding']['path']),patch.object(N.C.RUN,'EXPECTED_NAME','copy'):
            writer=N.C.RUN.SceneWriter(api,str(Path(td)/'journal.sqlite3'),adapters=N.C.adapters(['roof','wall']))
            result=N.execute_wall_roof_repair(writer,plan,baseline,auth,'fixture-junction')
            return result,writes
    def test_synthetic_native_callbacks_prove_geometry_preservation_and_flag_difference(self):
        result,writes=self.simulated_native_repair()
        self.assertEqual(writes,['ModifyWalls','CreateSolidElementLinks'])
        self.assertEqual(result['status'],'NATIVE_COMPLETE_CAP_REPAIR_UNSAVED_PASS')
        proof=result['operations'][1]['readback']['contact']
        self.assertEqual(proof['nativeFlagReadback'],'NOT_VERIFIED_REQUEST_READBACK_DIFFERENCE')
        self.assertAlmostEqual(proof['undersideContact']['sharedAreaSquareMeters'],self.assess()['expectedCompleteContactSquareMeters'])
    def test_synthetic_roof_drift_after_height_prevents_seo_dispatch(self):
        result,writes=self.simulated_native_repair(roof_drift=True)
        self.assertEqual(writes,['ModifyWalls']);self.assertEqual(result['status'],'PARTIAL_OR_UNKNOWN_OUTCOME')
    def test_synthetic_collision_after_seo_is_unknown_not_pass(self):
        result,writes=self.simulated_native_repair(new_collision=True)
        self.assertEqual(writes,['ModifyWalls','CreateSolidElementLinks'])
        self.assertEqual(result['status'],'PARTIAL_OR_UNKNOWN_OUTCOME')


if __name__=='__main__':unittest.main()
