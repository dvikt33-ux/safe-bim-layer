import copy,json,sqlite3,sys,tempfile,unittest,hashlib
from pathlib import Path
from unittest.mock import patch
from contextlib import closing
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import archicad_project_accelerator as A
import archicad_authored_extension as E
import archicad_native_spatial_structure as S
import archicad_authored_geometry as GEOMETRY
import archicad_authored_native_plan as NATIVE_PLAN
from test_archicad_isolated_authored_execution import IsolatedNative
G='00000000-0000-4000-8000-000000000001'


class StoryNative(IsolatedNative):
    def __init__(self):
        super().__init__();self.inventory=[];self.story_rows=[dict(index=i,floorId=i+1,level=3.*i,height=3.,name='Первый Этаж' if i==0 else '',dispOnSections=True) for i in range(3)];self.story_writes=0;self.noop=False;self.timeout=False
    def __call__(self,c,p):
        if c=='GetStories':return dict(actStory=0,firstStory=0,lastStory=len(self.story_rows)-1,skipNullFloor=True,stories=copy.deepcopy(self.story_rows))
        if c=='GetAllElements':return {'elements':[{'elementId':{'guid':g}} for g in self.inventory]}
        if c=='SetStories':
            self.story_writes+=1
            if not self.noop:self.story_rows=[dict(r,floorId=r['index']+1,height=3.) for r in p['stories']]
            if self.timeout:raise TimeoutError('applied but uncertain')
            return {'success':True}
        return super().__call__(c,p)


class StoriesTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.file=self.root/'isolated.pln';self.file.write_bytes(b'empty-test-fixture');self.sha=hashlib.sha256(self.file.read_bytes()).hexdigest();self.api=StoryNative()
        for k,v in [('EXPECTED_PATH',str(self.file)),('EXPECTED_NAME','APA_Isolated_Writer_Test_01')]:
            p=patch.object(A.RUN,k,v);p.start();self.addCleanup(p.stop)
        p=patch.object(A.RUN,'authorized_authored_target',return_value=True);p.start();self.addCleanup(p.stop)
    def target(self):
        rows=S.story_settings(self.api.story_rows);rows[1]['level']=3.3;rows[2]['level']=6.3;return rows
    def prepared(self,phase='EMPTY_SETUP'):
        return S.prepare_story_operation(self.api,self.target(),self.api.inventory,[], 'explicit-test-authorization',phase)
    def writer(self):return A.RUN.SceneWriter(self.api,self.root/'journal.sqlite',A.RUN.DEFAULT_SCENE_SCHEMA)
    def test_global_story_edit_uses_actual_setstories_and_same_sqlite_writer(self):
        r=S.execute_story_operation(self.writer(),self.prepared(),'native-stories-unit-01',self.sha)
        self.assertEqual(r['status'],'PASS',r);self.assertEqual(self.api.story_writes,1);self.assertEqual(r['readback']['stories']['stories'][1]['level'],3.3);self.assertEqual(r['readback']['nativeElementCreates'],0)
        with closing(sqlite3.connect(self.root/'journal.sqlite')) as db:self.assertEqual(db.execute('SELECT state FROM steps').fetchone()[0],'PASS')
    def test_empty_setup_can_insert_real_story_in_schema(self):
        target=S.story_settings(self.api.story_rows)+[dict(index=3,name='Explicit test datum',level=9.,dispOnSections=True)]
        p=S.prepare_story_operation(self.api,target,[],[],'explicit','EMPTY_SETUP');r=S.execute_story_operation(self.writer(),p,'native-stories-create-unit',self.sha);self.assertEqual(r['status'],'PASS');self.assertEqual(len(self.api.story_rows),4)
    def test_foreign_or_old_accepted_guid_blocks_before_story_write(self):
        self.api.inventory=[G]
        with self.assertRaisesRegex(ValueError,'FOREIGN_OR_ACCEPTED'):S.prepare_story_operation(self.api,self.target(),[],[G],'explicit','EMPTY_SETUP')
        self.assertEqual(self.api.story_writes,0)
    def test_nonempty_project_cannot_use_empty_setup(self):
        self.api.inventory=[G]
        with self.assertRaisesRegex(ValueError,'EMPTY_PROJECT'):self.prepared()
    def test_owned_edit_cannot_delete_occupied_story(self):
        self.api.inventory=[G]
        with self.assertRaisesRegex(ValueError,'INSERT_OR_DELETE'):S.prepare_story_operation(self.api,self.target()[:2],[G],[],'explicit')
    def test_active_ground_anchor_cannot_move(self):
        target=self.target();target[0]['level']=.2
        with self.assertRaisesRegex(ValueError,'GROUND_ANCHOR'):S.prepare_story_operation(self.api,target,[],[],'explicit','EMPTY_SETUP')
    def test_nonascending_nonfinite_and_nonconsecutive_levels_rejected(self):
        for field,value in [('level',float('nan')),('level',-1),('index',8)]:
            rows=self.target();rows[1][field]=value
            with self.assertRaises(ValueError):S.story_settings(rows)
    def test_identical_stories_are_noop_not_new_mutation(self):
        with self.assertRaisesRegex(ValueError,'NO_STORY_CHANGE'):S.prepare_story_operation(self.api,S.story_settings(self.api.story_rows),[],[],'explicit','EMPTY_SETUP')
    def test_provider_success_without_actual_level_change_is_not_pass(self):
        self.api.noop=True;r=S.execute_story_operation(self.writer(),self.prepared(),'native-stories-noop-unit',self.sha);self.assertEqual(r['status'],'PARTIAL_OR_UNKNOWN_OUTCOME');self.assertEqual(self.api.story_writes,1)
    def test_unknown_applied_write_is_never_repeated(self):
        self.api.timeout=True;p=self.prepared();r=S.execute_story_operation(self.writer(),p,'native-stories-timeout-unit',self.sha);self.assertEqual(r['status'],'PARTIAL_OR_UNKNOWN_OUTCOME')
        with self.assertRaises(ValueError):S.execute_story_operation(self.writer(),p,'native-stories-timeout-unit',self.sha)
        self.assertEqual(self.api.story_writes,1)
    def test_changed_story_baseline_or_saved_bytes_blocks_before_write(self):
        p=self.prepared();self.api.story_rows[1]['name']='Changed'
        with self.assertRaisesRegex(ValueError,'BASELINE_CHANGED'):S.execute_story_operation(self.writer(),p,'native-stories-drift-unit',self.sha)
        self.api.story_rows[1]['name']='';self.file.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'SAVED_HASH_CHANGED'):S.execute_story_operation(self.writer(),p,'native-stories-hash-unit',self.sha)
        self.assertEqual(self.api.story_writes,0)
    def test_story_scope_cannot_be_combined_with_model_or_document_scope(self):
        p=self.prepared();p['integrationBindings']['dependencies']['modelOperation']={}
        with self.assertRaisesRegex(ValueError,'ONE_BOUNDED'):self.writer().execute_bound_operation(p,'native-stories-mixed-unit','SetStories',p['integrationBindings']['dependencies']['spatialOperation']['parameters'],'bad',lambda:{},lambda *_:{})
    def test_empty_retained_edit_requires_exact_isolated_owned_inventory(self):
        params={'wallsWithDetails':[{'elementId':{'guid':G},'height':3.1}]}
        with self.assertRaisesRegex(ValueError,'OWNERSHIP'):E.model_operation_scope('ModifyWalls',params,'hash',[G],[],'explicit')
        scope=E.model_operation_scope('ModifyWalls',params,'hash',[G],[],'explicit',isolated_inventory=[G]);E.qualify_model_operation(scope,'ModifyWalls',params,'hash')
        with self.assertRaisesRegex(ValueError,'OWNERSHIP'):E.model_operation_scope('ModifyWalls',params,'hash',[G],[],'explicit',isolated_inventory=[G,'foreign'])
    def test_empty_normalization_is_explicit_not_building_geometry_acceptance(self):
        raw=dict(nativeBodySlots=0,bodies=[],deletedBodySlots=[],regenerated3D=True,coordinateSystem='ABSOLUTE_PROJECT_XYZ',elements=[],materials=[])
        with self.assertRaisesRegex(ValueError,'zero bodies'):GEOMETRY.normalize_dump(raw)
        empty=GEOMETRY.normalize_dump(raw,allow_empty=True);self.assertEqual(empty['counts']['bodies'],0)
        raw['regenerated3D']=False
        with self.assertRaisesRegex(ValueError,'not independently'):GEOMETRY.normalize_dump(raw,allow_empty=True)
    def test_template_marker_guid_is_preserved_but_generic_object_is_rejected(self):
        raw=dict(nativeBodySlots=0,bodies=[],deletedBodySlots=[],regenerated3D=True,coordinateSystem='ABSOLUTE_PROJECT_XYZ',elements=[dict(guid=G,type='Object',homeStory=0,relationships={'hostGuid':G})],materials=[])
        def api(c,p):return copy.deepcopy(raw)
        with patch.object(A.RUN,'requested_details',return_value={'details':{'libPart':{'name':'Built-in Elevation Marker','ownUnID':{'guid':G}}}}):
            self.assertEqual(set(S.template_reference_signatures(api,[G])),{G})
        with patch.object(A.RUN,'requested_details',return_value={'details':{'libPart':{'name':'Furniture','ownUnID':{'guid':G}}}}):
            with self.assertRaisesRegex(ValueError,'SOURCE_VERIFIED_MARKER'):S.template_reference_signatures(api,[G])
    def test_non_ground_template_marker_cannot_be_excluded_from_story_ownership(self):
        raw=dict(nativeBodySlots=0,bodies=[],deletedBodySlots=[],regenerated3D=True,coordinateSystem='ABSOLUTE_PROJECT_XYZ',elements=[dict(guid=G,type='Elevation',homeStory=1)],materials=[])
        with self.assertRaisesRegex(ValueError,'GROUND_MARKER'):S.template_reference_signatures(lambda *_:copy.deepcopy(raw),[G])
    def test_utf8_story_scope_roundtrip_preserves_hash_and_native_name(self):
        p=self.prepared();file=self.root/'scope.json';A.write_json(file,p);loaded=json.loads(file.read_text(encoding='utf8'));scope=loaded['integrationBindings']['dependencies']['spatialOperation'];S.qualify_spatial_operation(scope,'SetStories',scope['parameters'],loaded['sourcePlanHash']);self.assertEqual(scope['beforeStories'][0]['name'],'Первый Этаж')
    def test_actual_stale_hosted_sill_emits_supported_native_correction(self):
        self.api.inventory=[G];target=self.target();created={'window':dict(guid=G,kind='Window',floorIndex=1)}
        scope=dict(parameters={'stories':target},ownedGuids=[G],templateSignatures={})
        change=dict(storyOperation={'integrationBindings':{'dependencies':{'spatialOperation':scope}}},created=created,newPlan={'graph':{'operations':[dict(id='window',command='CreateWindows',params={'windowsData':[{'sillHeight':1}]})]}})
        self.api.story_rows=[dict(r,floorId=r['index']+1) for r in target]
        with patch.object(A.RUN,'requested_details',return_value={'details':{'sillHeight':.7}}):r=S.prepare_dependency_corrections(self.api,change)
        self.assertEqual(r[0]['command'],'ModifyWindows');self.assertEqual(r[0]['beforeValue'],.7);self.assertEqual(r[0]['parameters']['windowsWithDetails'][0]['sillHeight'],1)
    def test_actual_supplied_schema_is_pinned_instead_of_hardcoded_default(self):
        intent=json.loads((ROOT/'examples/accelerator/model-first-building.json').read_text(encoding='utf8'))
        schema=self.root/'fresh-schema.json';raw=json.loads(A.RUN.DEFAULT_SCENE_SCHEMA.read_text(encoding='utf8'))
        for name in ('command_definitions.js','common_schema_definitions.js'):
            (self.root/name).write_bytes((A.RUN.DEFAULT_SCENE_SCHEMA.parent/name).read_bytes())
        binding=copy.deepcopy(raw['_metadata']['binding']);binding['testSource']='explicit fresh export';A.write_json(schema,A.parse_documentation(self.root,binding))
        with patch.object(A.RUN,'EXPECTED_PATH',intent['brief']['targetProjectPath']):
            compiled=A.compile_authored_intent(intent,schema,self.api)
        candidate=compiled['authoredCandidate']
        self.assertEqual(Path(candidate['schemaPath']),schema.resolve());self.assertEqual(compiled['schemaSha256'],hashlib.sha256(schema.read_bytes()).hexdigest())
        schema.write_text(schema.read_text(encoding='utf8')+' ',encoding='utf8')
        with self.assertRaisesRegex(ValueError,'PINNED_SCHEMA_CHANGED'):NATIVE_PLAN.as_existing_scene_writer_preview(candidate)


if __name__=='__main__':unittest.main()
