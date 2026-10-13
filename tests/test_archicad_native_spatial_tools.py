"""Offline native contract gates and same-writer SQLite replay integration."""
import copy,json,hashlib,sqlite3,sys,tempfile,unittest,re
from pathlib import Path
from unittest.mock import patch
from contextlib import closing
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import archicad_native_spatial_tools as T
import archicad_project_accelerator as A
import archicad_connected_components as C
from test_archicad_scene_run import FakeNative
OLD='00000000-0000-4000-8000-000000000001';NEW='00000000-0000-4000-8000-000000000002'

def defaults():
    return dict(nativeTypeId=23,nativeVariationId=0x4752454c,nativeVariationName='APIVarId_GridElement',libraryPartIndex=77,nativeParameters=[dict(name='actual_length',nativeType=1,nativeTypeName='Length',isArray=False,value=8.),dict(name='actual_label',nativeType=11,nativeTypeName='String',isArray=False,value='source')])
def recipe():
    d=defaults();profile=dict(status='SOURCE_VERIFIED',defaultsHash=T.RUN.digest(d),lengthParameter='actual_length',labelParameter='actual_label')
    return T.prepare_axis(dict(id='axis-A',direction='X',coordinate=2),dict(xMin=0,xMax=10,yMin=0,yMax=8),d,profile)
def stair():return dict(favoriteName='source',baseLinePoints=[dict(x=70,y=0),dict(x=70,y=7.7)],zCoordinate=0,floorIndex=0,totalHeight=3.3,flightWidth=1,stepNum=22,riserHeight=.15,treadDepth=.35,treadDepthLocked=True,finishVisible=False)

class GridNative(FakeNative):
    def __init__(self):super().__init__();self.grid=None;self.timeout=False;self.bad_variation=False
    def __call__(self,c,p):
        if c=='GetNativeGridDefaultsV1':return defaults()
        if c=='GetModelDumpV1':return {'elements':[{'guid':OLD}]+([{'guid':NEW}] if self.grid else [])}
        if c=='CreateNativeGridElementsV1':
            self.writes.append(c);self.grid=copy.deepcopy(p['gridsData'][0])
            if self.timeout:raise TimeoutError('possibly applied')
            return {'elements':[{'elementId':{'guid':NEW}}]}
        if c=='ModifyNativeGridElementsV1':
            self.writes.append(c);self.grid.update({k:p['gridsWithDetails'][0][k] for k in ['x','y','angle']});return {'executionResults':[{'success':True}]}
        if c=='GetNativeGridElementsV1':
            d=defaults();row=self.grid
            return {'grids':[dict(elementId={'guid':NEW},nativeTypeName='GridElement',nativeTypeId=d['nativeTypeId'],nativeVariationName='Generic' if self.bad_variation else d['nativeVariationName'],nativeVariationId=d['nativeVariationId'],floorIndex=row['floorIndex'],libraryPartIndex=row['expectedLibraryPartIndex'],**{k:row[k] for k in ['x','y','angle']},nativeParameters=copy.deepcopy(row['parameters']))]}
        return super().__call__(c,p)

class SpatialSDKTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.file=self.root/'copy.pln';self.file.write_bytes(b'fixture');self.sha=hashlib.sha256(b'fixture').hexdigest();self.api=GridNative()
        p=patch.object(T.RUN,'EXPECTED_PATH',str(self.file));p.start();self.addCleanup(p.stop)
        catalog=json.loads(T.RUN.DEFAULT_SCENE_SCHEMA.read_text(encoding='utf8'));cpp=(ROOT/'archicad-addon/Sources/NativeGridCommands.cpp').read_text(encoding='utf8')
        for cmd in ['CreateNativeGridElementsV1','ModifyNativeGridElementsV1']:
            raw=re.search(cmd+r'Command::GetInputParametersSchema.*?return R"\((.*?)\)";',cpp,re.S).group(1)
            catalog['commands'][cmd]=dict(name=cmd,api='tapir',category='SDK_SOURCE_FIXTURE_NOT_INSTALLED',version='1.5.10',parameters=json.loads(raw),returns={})
        source_schema=self.root/'sdk-source-only.json';source_schema.write_text(json.dumps(catalog),encoding='utf8')
        self.writer=T.RUN.SceneWriter(self.api,self.root/'journal.sqlite',source_schema)
    def runtime(self):return patch.object(T,'runtime_catalog',return_value={})
    def geometry(self):
        a=patch.object(C.G,'normalize_dump',side_effect=lambda v:v);b=patch.object(C,'retained_geometry_signatures',return_value={OLD:'pinned'})
        a.start();b.start();self.addCleanup(a.stop);self.addCleanup(b.stop)
    def create(self,r=None):return A.apply_native_axis_grid(self.writer,r or recipe(),'grid-source-A',{OLD:'pinned'},self.sha,'explicit test')
    def test_real_writer_journal_creates_once_and_reuses_same_native_guid(self):
        self.geometry()
        with self.runtime():first=self.create();again=self.create()
        self.assertEqual(first['status'],'PASS',first);self.assertEqual(again['nativeCreateCalls'],0);self.assertEqual(first['createdGuid'],again['createdGuid']);self.assertEqual(self.api.writes,['CreateNativeGridElementsV1'])
        with closing(sqlite3.connect(self.writer.journal_path)) as db:self.assertEqual(db.execute('select state,guid from steps').fetchone(),('PASS',NEW))
    def test_ambiguous_create_keeps_unknown_and_never_repeats(self):
        self.geometry();self.api.timeout=True
        with self.runtime():r=self.create();self.assertEqual(r['status'],'PARTIAL_OR_UNKNOWN_OUTCOME')
        with self.runtime(),self.assertRaisesRegex(ValueError,'NEVER_RETRY'):self.create()
        self.assertEqual(len(self.api.writes),1)
    def test_generic_object_variation_cannot_pass_native_grid_acceptance(self):
        self.geometry();self.api.bad_variation=True
        with self.runtime():r=self.create()
        self.assertEqual(r['status'],'PARTIAL_OR_UNKNOWN_OUTCOME');self.assertIn('TRUE_GRID',r['reason'])
    def test_old_installed_schema_blocks_before_any_create(self):
        self.writer.schema_path=T.RUN.DEFAULT_SCENE_SCHEMA
        with self.assertRaisesRegex(ValueError,'CONTRACT_MISSING'):self.create()
        self.assertEqual(self.api.writes,[])
    def test_changed_defaults_block_before_dispatch(self):
        self.geometry();r=recipe();r['defaults']['libraryPartIndex']=88;r['sourceHash']=T.RUN.digest({k:v for k,v in r.items() if k not in {'sourceHash','graph'}})
        with self.runtime(),self.assertRaisesRegex(ValueError,'DEFAULTS_CHANGED'):self.create(r)
        self.assertEqual(self.api.writes,[])
    def test_guid_preserving_edit_updates_semantic_axis_and_existing_binding_reuse(self):
        self.geometry();r=recipe()
        with self.runtime():self.create(r);edit=T.edit_axis(self.writer,NEW,r,dict(x=3,y=0,angle=r['parameters']['gridsData'][0]['angle']),'grid-edit-source-A',{OLD:'pinned'},self.sha,'explicit test');again=A.apply_native_axis_grid(self.writer,edit['updatedRecipe'],'grid-source-A',{OLD:'pinned'},self.sha,'explicit test',existing_guid=NEW)
        self.assertEqual(edit['status'],'PASS',edit);self.assertEqual(edit['nativeAxisBinding']['coordinate'],3);self.assertEqual(again['nativeCreateCalls'],0);self.assertEqual(self.api.writes,['CreateNativeGridElementsV1','ModifyNativeGridElementsV1'])
    def test_grid_rotation_is_not_silently_bound_to_old_semantic_axis(self):
        self.api.grid=recipe()['parameters']['gridsData'][0]
        with self.assertRaisesRegex(ValueError,'SPAN_ORIENTATION'):T.edit_axis(self.writer,NEW,recipe(),dict(x=3,y=0,angle=0),'test',{OLD:'pinned'},self.sha,'explicit')
    def test_grid_role_mapping_requires_actual_named_length_and_string_parameters(self):
        d=defaults();bad=dict(status='SOURCE_VERIFIED',defaultsHash=T.RUN.digest(d),lengthParameter='guessed_A',labelParameter='actual_label')
        with self.assertRaisesRegex(ValueError,'ACTUAL_NATIVE'):T.prepare_axis(dict(id='A',direction='Y',coordinate=2),dict(xMin=0,xMax=10,yMin=0,yMax=8),d,bad)
    def test_tampered_recipe_blocks_before_native_write(self):
        r=recipe();r['parameters']['gridsData'][0]['x']=8
        with self.runtime(),self.assertRaisesRegex(ValueError,'RECIPE_CHANGED'):self.create(r)
    def test_new_grid_scope_does_not_grant_edit_of_retained_element(self):
        params={'gridsWithDetails':[dict(elementId={'guid':OLD},x=1,y=0,angle=0,expectedX=0,expectedY=0,expectedAngle=0)]}
        with self.assertRaises(ValueError):T.E.model_operation_scope('ModifyNativeGridElementsV1',params,'h',[NEW],[OLD],'explicit')
    def test_duplicate_grid_parameter_names_and_nonfinite_position_rejected(self):
        p=recipe()['parameters'];p['gridsData'][0]['parameters']*=2
        with self.assertRaisesRegex(ValueError,'DUPLICATE'):T.qualify_operation('CreateNativeGridElementsV1',p,set(),{OLD})
        p=recipe()['parameters'];p['gridsData'][0]['x']=float('nan')
        with self.assertRaises(ValueError):T.qualify_operation('CreateNativeGridElementsV1',p,set(),{OLD})
    def source_rules(self):
        tags=[]
        for prefix,low,high in [('Rule',.6,.65),('TreadDepth',.25,.35),('RiserHeight',.15,.2)]:
            for side,v in [('Min',low),('Max',high)]:tags.extend([f'<{prefix}{side}Value>{v}</{prefix}{side}Value>',f'<{prefix}{side}Applied>true</{prefix}{side}Applied>'])
        p=self.root/'favorite.xml';p.write_text('<Favorites><StairDefault><StairRules>'+''.join(tags)+'</StairRules></StairDefault></Favorites>',encoding='utf8');return T.favorite_rules(p)
    def test_source_rules_explain_observed_032_without_normative_inference(self):
        s=self.source_rules();bad=T.check_source_combination(s,3.3,20,.35);good=T.check_source_combination(s,3.3,20,.32)
        self.assertEqual(bad['status'],'SOURCE_RULE_CONFLICT');self.assertAlmostEqual(bad['twoRiserPlusGoing'],.68);self.assertEqual(bad['violations'][0]['rule'],'RuleMax');self.assertEqual(good['violations'],[]);self.assertEqual(good['nativeGeometry'],'NOT_VERIFIED')
    def test_compatible_test_combinations_are_not_native_or_engineering_pass(self):
        for h,n in [(3,20),(3.3,22)]:
            v=T.check_source_combination(self.source_rules(),h,n,.35);self.assertEqual(v['violations'],[]);self.assertEqual(v['nativeGeometry'],'NOT_VERIFIED');self.assertEqual(v['engineeringAcceptance'],'NOT_VERIFIED')
    def test_incomplete_favorite_rule_profile_is_default_denied(self):
        p=self.root/'incomplete.xml';p.write_text('<Favorites><StairDefault/></Favorites>',encoding='utf8')
        with self.assertRaisesRegex(ValueError,'RULE_MISSING'):T.favorite_rules(p)
    def test_incompatible_source_case_denied_before_native_create(self):
        source=self.source_rules();source.update(sourcePath=str(self.root/'favorite.xml'),favoriteName='source');row=stair();row.update(stepNum=20,riserHeight=.165)
        with self.assertRaisesRegex(ValueError,'SOURCE_RULE_CONFLICT_NO_CREATE'):A.apply_exact_native_stair(self.writer,row,'strict-stair-conflict',{OLD:'pinned'},self.sha,'explicit',source)
        self.assertEqual(self.api.writes,[])
    def test_changed_favorite_source_bytes_denied_before_native_create(self):
        source=self.source_rules();source.update(sourcePath=str(self.root/'favorite.xml'),favoriteName='source');(self.root/'favorite.xml').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'FAVORITE_SOURCE_CHANGED'):A.apply_exact_native_stair(self.writer,stair(),'strict-stair-source-change',{OLD:'pinned'},self.sha,'explicit',source)
        self.assertEqual(self.api.writes,[])
    def test_exact_stair_scope_requires_lock_and_consistent_rise(self):
        row=stair();row['treadDepthLocked']=False
        with self.assertRaises(ValueError):T.E.model_operation_scope('CreateExactStairsV1',{'stairsData':[row]},'h',[],[OLD],'explicit')
        row=stair();row['riserHeight']=.165
        with self.assertRaisesRegex(ValueError,'INCONSISTENT'):T.E.model_operation_scope('CreateExactStairsV1',{'stairsData':[row]},'h',[],[OLD],'explicit')
    def test_exact_native_readback_rejects_silent_going_or_baseline_change(self):
        row=stair();actual=dict(row,elementId={'guid':NEW},nativeType='Stair')
        actual['treadDepth']=.32
        with self.assertRaisesRegex(ValueError,'DIMENSION_MISMATCH'):T.verify_exact_stair(lambda *_:actual,NEW,row)
        actual['treadDepth']=.35;actual['baseLinePoints']=[dict(x=70,y=0),dict(x=70,y=7.6)]
        with self.assertRaisesRegex(ValueError,'BASELINE_MISMATCH'):T.verify_exact_stair(lambda *_:actual,NEW,row)
    def test_precise_source_dimension_pass_still_does_not_claim_engineering(self):
        row=stair();actual=dict(row,elementId={'guid':NEW},nativeType='Stair')
        p=T.verify_exact_stair(lambda *_:actual,NEW,row);self.assertEqual(p['sourceDimensionStatus'],'SOURCE_DIMENSION_PASS');self.assertEqual(p['engineeringAcceptance'],'NOT_VERIFIED')
    def test_stair_edit_cannot_touch_accepted_root_or_override_rules(self):
        p={k:v for k,v in stair().items() if k!='favoriteName'};p.update(elementId={'guid':OLD},expectedTotalHeight=3.3,expectedGoing=.32,expectedStepNum=20)
        with self.assertRaisesRegex(ValueError,'OWNED_TARGET'):T.qualify_operation('ModifyNativeStairGeometryV1',p,{NEW},{OLD})
        p['elementId']['guid']=NEW;p['rules']={'ruleMaxValue':.7}
        with self.assertRaisesRegex(ValueError,'SOURCE_REQUIRED'):T.qualify_operation('ModifyNativeStairGeometryV1',p,{NEW},{OLD})
    def test_overlay_registration_is_idempotent_and_preserves_original_commands(self):
        import importlib.util
        spec=importlib.util.spec_from_file_location('builder_test',ROOT/'archicad-addon/Examples/build_model_dump.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        source=self.root/'overlay';(source/'Sources').mkdir(parents=True);main=source/'Sources/AddOnMain.cpp';main.write_text('#include "ElementCommands.hpp"\n        err |= RegisterCommand<CreateWallsCommand> (elementCommands, "x", "original");\n        AddCommandGroup (elementCommands);\n        AddCommandGroup (projectCommands);',encoding='utf8')
        m.overlay_registration(source);first=main.read_bytes();m.overlay_registration(source);self.assertEqual(first,main.read_bytes());self.assertEqual(first.count(b'RegisterCommand<CreateWallsCommand>'),1);self.assertEqual(first.count(b'RegisterCommand<CreateExactStairsV1Command>'),1)

    def exact_stair_fixture(self):
        source=self.source_rules();source.update(sourcePath=str(self.root/'favorite.xml'),favoriteName='source')
        catalog=json.loads(self.writer.schema_path.read_text(encoding='utf8'))
        cpp=(ROOT/'archicad-addon/Sources/NativeStairCommands.cpp').read_text(encoding='utf8')
        item=json.loads(re.search(r'StairDataSchema.*?return R"\((.*?)\)";',cpp,re.S).group(1))
        catalog['commands']['CreateExactStairsV1']=dict(name='CreateExactStairsV1',api='tapir',version='1.5.10',category='SDK_SOURCE_FIXTURE_NOT_INSTALLED',parameters=dict(type='object',properties={'stairsData':dict(type='array',minItems=1,maxItems=1,items=item)},required=['stairsData'],additionalProperties=False),returns={})
        self.writer.schema_path.write_text(json.dumps(catalog),encoding='utf8')
        self.actual_stair=None;self.stair_timeout=False;old=self.api
        def native(command,params):
            if command=='GetFavoritesByType':return {'favorites':['source']}
            if command=='CreateExactStairsV1':
                old.writes.append(command);row=copy.deepcopy(params['stairsData'][0]);row.update(elementId={'guid':NEW},nativeType='Stair',rules={k[0].lower()+k[1:]:v for k,v in source['rules'].items()});self.actual_stair=row
                if self.stair_timeout:raise TimeoutError('possibly applied')
                return {'elements':[{'elementId':{'guid':NEW}}]}
            if command=='GetNativeStairGeometryV1':return copy.deepcopy(self.actual_stair)
            if command=='GetModelDumpV1':return {'elements':[{'guid':OLD}]+([{'guid':NEW}] if self.actual_stair else [])}
            return old(command,params)
        self.writer.api=native;self.geometry();return source
    def exact_create(self,source,row=None,retained=None):
        return A.apply_exact_native_stair(self.writer,row or stair(),'exact-stair-replay',retained or {OLD:'pinned'},self.sha,'explicit fixture',source)
    def test_exact_stair_completed_sqlite_result_reuses_without_second_create(self):
        source=self.exact_stair_fixture()
        with self.runtime():first=self.exact_create(source);again=self.exact_create(source)
        self.assertEqual(first['status'],'PASS',first);self.assertEqual(again['nativeCreateCalls'],0);self.assertEqual(again['createdGuid'],first['createdGuid']);self.assertEqual(self.api.writes,['CreateExactStairsV1'])
    def test_exact_stair_unknown_outcome_cannot_replay_even_if_element_exists(self):
        source=self.exact_stair_fixture();self.stair_timeout=True
        with self.runtime():first=self.exact_create(source)
        self.assertEqual(first['status'],'PARTIAL_OR_UNKNOWN_OUTCOME')
        with self.runtime(),self.assertRaisesRegex(ValueError,'NEVER_RETRY'):self.exact_create(source)
        self.assertEqual(self.api.writes,['CreateExactStairsV1'])
    def test_completed_stair_changed_source_requires_explicit_edit(self):
        source=self.exact_stair_fixture()
        with self.runtime():self.exact_create(source)
        row=stair();row['baseLinePoints'][0]['x']+=1;row['baseLinePoints'][1]['x']+=1
        with self.runtime(),self.assertRaisesRegex(ValueError,'EXPLICIT_EDIT'):self.exact_create(source,row)
        self.assertEqual(len(self.api.writes),1)
    def test_completed_stair_changed_native_going_cannot_reuse_pass(self):
        source=self.exact_stair_fixture()
        with self.runtime():self.exact_create(source)
        self.actual_stair['treadDepth']=.32
        with self.runtime(),self.assertRaisesRegex(ValueError,'DIMENSION_MISMATCH'):self.exact_create(source)
    def test_completed_stair_changed_native_rules_cannot_reuse_pass(self):
        source=self.exact_stair_fixture()
        with self.runtime():self.exact_create(source)
        self.actual_stair['rules']['ruleMaxValue']=.7
        with self.runtime(),self.assertRaisesRegex(ValueError,'RULE_READBACK'):self.exact_create(source)
    def test_completed_stair_wrong_project_is_denied_before_reuse(self):
        source=self.exact_stair_fixture()
        with self.runtime():self.exact_create(source)
        self.api.wrong_project=True
        with self.runtime(),self.assertRaises(ValueError):self.exact_create(source)
    def test_completed_stair_saved_file_drift_requires_reconciliation(self):
        source=self.exact_stair_fixture()
        with self.runtime():self.exact_create(source)
        self.file.write_bytes(b'changed')
        with self.runtime(),self.assertRaisesRegex(ValueError,'SAVED_FILE_HASH'):self.exact_create(source)
    def test_completed_stair_retained_geometry_drift_denies_reuse(self):
        source=self.exact_stair_fixture()
        with self.runtime():self.exact_create(source)
        with self.runtime(),patch.object(C,'retained_geometry_signatures',return_value={OLD:'changed'}),self.assertRaisesRegex(ValueError,'RETAINED_GEOMETRY'):self.exact_create(source)

if __name__=='__main__':unittest.main()
