"""Synthetic end-to-end authored input through the original writer and SQLite."""
import copy
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import archicad_project_accelerator as A
import archicad_authored_extension as EXT
from test_archicad_basic_slab_integration import CompositeDefaultNative
from test_archicad_project_library_pack import BM,BM_GUID


class IsolatedNative(CompositeDefaultNative):
    def __call__(self,command,params):
        if command=='GetSubelementsOfHierarchicalElements':
            self.calls.append(command)
            return {'subelements':[{'columnSegments':[{'elementId':{'guid':g}}]} for g in self.segments()]}
        if command=='GetAllElements':
            result=super().__call__(command,params)
            result['elements'].extend({'elementId':{'guid':g}} for g in self.segments())
            return result
        if command=='ModifyWalls':
            self.calls.append(command);self.writes.append(command)
            if getattr(self,'wall_modify_timeout',False):raise TimeoutError('uncertain wall modify')
            for item in params['wallsWithDetails']:
                if not getattr(self,'wall_modify_noop',False):
                    self.created[item['elementId']['guid']][1]['wallsData'][0]['buildingMaterialId']=item['buildingMaterialId']
            return {'executionResults':[{'success':True} for _ in params['wallsWithDetails']]}
        if command=='ModifyWindows':
            self.calls.append(command);self.writes.append(command)
            item=params['windowsWithDetails'][0]
            self.created[item['elementId']['guid']][1]['windowsData'][0]['width']=item['width']
            return {'executionResults':[{'success':True}]}
        if command=='GetStories':
            self.calls.append(command)
            return {'actStory':0,'stories':[
                {'index':0,'floorId':1,'level':0.,'name':'Первый Этаж'},
                {'index':1,'floorId':2,'level':3.,'name':''},
                {'index':2,'floorId':3,'level':6.,'name':''}]}
        if command=='GetAttributesByType':
            self.calls.append(command)
            return {'attributes':[{'attributeId':{'guid':BM_GUID},'name':BM}]}
        result=super().__call__(command,params)
        if command=='GetDetailsOfElements':
            guid=params['elements'][0]['elementId']['guid']
            source,args=self.created[guid]
            if source=='CreateSlabs':
                slab=args['slabsData'][0]
                details=result['detailsOfElements'][0]['details']
                details['zCoordinate']=slab['level']
                details['level']=slab['level']-3*slab['floorIndex']
            if source=='CreateColumns':
                result['detailsOfElements'][0]['details']['buildingMaterialId']=args['columnsData'][0]['buildingMaterialId']
        return result

    def segments(self):
        return ['00000000-0000-4000-8000-00000000000'+str(i+1)
                for i,(cmd,_) in enumerate(v for v in self.created.values() if v[0]=='CreateColumns')]


class IsolatedAuthoredExecutionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.state=self.root/'ledger';self.state.mkdir()
        self.intent=json.loads((ROOT/'examples/accelerator/isolated-authored-project.json').read_text(encoding='utf8'))
        self.native=IsolatedNative();self.counter=0
        for name,value in [('PORT',19724),('EXPECTED_PATH',A.RUN.APPROVED_ISOLATED_WRITER_PATH),('EXPECTED_NAME','APA_Isolated_Writer_Test_01')]:
            patcher=patch.object(A.RUN,name,value);patcher.start();self.addCleanup(patcher.stop)

    def run_project(self,mode='preflight',token=None,native=None):
        self.counter+=1
        return A.run_project(self.intent,A.RUN.DEFAULT_SCENE_SCHEMA,self.root/f'run-{self.counter}',self.state,mode,native or self.native,'isolated-authored-one-shot-01',token)

    def test_authored_brief_to_ten_native_elements_and_whole_model_readback(self):
        pre=self.run_project();self.assertEqual(pre['status'],'READY_FOR_EXPLICIT_TEST_RUN',pre)
        self.assertEqual(pre['modelWriteAttempts'],0)
        self.assertFalse((self.state/'scene-v1-attempts.sqlite3').exists())
        result=self.run_project('execute',pre['confirmPlanHash'])
        self.assertEqual(result['status'],'COMPLETE_UNSAVED',result)
        self.assertTrue(result['wholeAssemblyReadback'])
        self.assertEqual(len(result['addedGuids']),10)
        self.assertEqual(result['removedGuids'],[])
        self.assertEqual(result['modelWriteAttempts'],12)
        self.assertEqual(self.native.writes.count('CreateWalls'),8)
        self.assertEqual(self.native.writes.count('CreateSlabs'),2)
        with closing(sqlite3.connect(self.state/'scene-v1-attempts.sqlite3')) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM steps WHERE state='PASS'").fetchone()[0],10)

    def test_explicit_isolated_binding_cannot_admit_an_arbitrary_pln(self):
        for path in [r'C:\other.pln',A.RUN.APPROVED_SCRATCH_PATH]:
            with self.assertRaisesRegex(ValueError,'ISOLATED_WRITER_PLN_NOT_APPROVED'):
                A.RUN.bind_isolated_writer_pln(19724,path)
        self.assertEqual(A.RUN.EXPECTED_PATH,A.RUN.APPROVED_ISOLATED_WRITER_PATH)
        for port in [True,0,65536]:
            with self.assertRaisesRegex(ValueError,'INVALID_TEST_PORT'):A.RUN.bind_isolated_writer_pln(port)

    def test_wrong_current_project_stops_at_identity_without_inventory(self):
        self.native.wrong_project=True
        result=self.run_project();self.assertEqual(result['status'],'BLOCKED',result)
        self.assertEqual(self.native.calls,['GetProjectInfo']);self.assertFalse(self.native.writes)

    def test_changed_authored_input_invalidates_preflight_before_write(self):
        pre=self.run_project();self.intent['brief']['rooms'][0]['name']='Changed room'
        result=self.run_project('execute',pre['confirmPlanHash'])
        self.assertEqual(result['status'],'BLOCKED',result);self.assertFalse(self.native.writes)

    def test_modify_timeout_preserves_guid_and_blocks_repeat_creation(self):
        pre=self.run_project();self.native.modify_timeout=True
        result=self.run_project('execute',pre['confirmPlanHash'])
        self.assertEqual(result['status'],'PARTIAL_OR_UNKNOWN_OUTCOME',result)
        count=len(self.native.writes)
        result=self.run_project('execute',pre['confirmPlanHash'])
        self.assertEqual(result['status'],'BLOCKED',result);self.assertEqual(len(self.native.writes),count)

    def test_authored_preview_cannot_be_retargeted_by_writer_globals(self):
        compiled=A.compile_authored_intent(self.intent,A.RUN.DEFAULT_SCENE_SCHEMA,self.native)
        factory=A.AUTHORED_NATIVE.make_read_only_scene_writer_preview_factory(compiled['authoredCandidate'])
        with patch.object(A.RUN,'EXPECTED_PATH',A.RUN.APPROVED_SCRATCH_PATH):
            writer=A.RUN.SceneWriter(self.native,self.state/'unused.sqlite3',preview_factory=factory)
            with self.assertRaisesRegex(ValueError,'AUTHORED_TARGET_DIFFERS'):writer.preflight(40,40)
        self.assertFalse(self.native.writes)

    def test_material_changed_between_compile_and_preflight_blocks(self):
        compiled=A.compile_authored_intent(self.intent,A.RUN.DEFAULT_SCENE_SCHEMA,self.native)
        factory=A.AUTHORED_NATIVE.make_read_only_scene_writer_preview_factory(compiled['authoredCandidate'])
        def drift(cmd,params):
            if cmd=='GetAttributesByType':return {'attributes':[{'name':BM,'attributeId':{'guid':'11111111-1111-4111-8111-111111111111'}}]}
            return self.native(cmd,params)
        writer=A.RUN.SceneWriter(drift,self.state/'unused.sqlite3',preview_factory=factory)
        with self.assertRaisesRegex(ValueError,'AUTHORED_SLAB_MATERIAL_CHANGED'):writer.preflight(40,40)
        self.assertFalse(self.native.writes)

    def test_upper_slab_requires_absolute_three_meters_and_relative_zero(self):
        compiled=A.compile_authored_intent(self.intent,A.RUN.DEFAULT_SCENE_SCHEMA,self.native)
        upper=next(s for s in compiled['graph']['operations'] if s['id']=='native-slab-level-2')
        self.assertEqual(upper['params']['slabsData'][0]['level'],3.)
        row={'type':'Slab','floorIndex':1,'details':{
            'level':-3.,'zCoordinate':0.,'structureType':'Composite','thickness':.3,
            'polygonOutline':upper['params']['slabsData'][0]['polygonCoordinates']}}
        with self.assertRaisesRegex(ValueError,'SLAB_READBACK_MISMATCH'):
            A.RUN.verify_readback('CreateSlabs',upper['params'],row,
                expected_floor=1,expected_story_level=3.,slab_level_is_absolute=True,
                allow_slab_thickness_mismatch=True)

    def extension(self):
        pre=self.run_project()
        result=self.run_project('execute',pre['confirmPlanHash'])
        self.assertEqual(result['status'],'COMPLETE_UNSAVED',result)
        plan=json.loads((self.root/'run-2/preflight.json').read_text(encoding='utf8'))
        intent=json.loads((ROOT/'examples/accelerator/isolated-authored-building.json').read_text(encoding='utf8'))
        ticket=EXT.prepare(self.native,intent,plan,result['scene']['steps'],self.state/'scene-v1-attempts.sqlite3','extension-test-01')
        return intent,ticket

    def test_existing_ten_guids_extend_to_seventeen_with_hosted_openings(self):
        _,ticket=self.extension()
        count=len(self.native.writes)
        result=EXT.execute(self.native,ticket,self.state/'scene-v1-attempts.sqlite3',ticket['confirmPlanHash'])
        self.assertEqual(result['status'],'COMPLETE_UNSAVED',result)
        self.assertEqual(result['reusedCount'],10);self.assertEqual(result['newCreatedCount'],7)
        self.assertEqual(len(self.native.writes)-count,8)
        self.assertEqual({k:v['guid'] for k,v in ticket['intent']['oldCreated'].items()},
            {k:result['steps'][k]['guid'] for k in ticket['intent']['oldCreated']})
        with self.assertRaises(sqlite3.IntegrityError):
            EXT.execute(self.native,ticket,self.state/'scene-v1-attempts.sqlite3',ticket['confirmPlanHash'])
        self.assertEqual(len(self.native.writes)-count,8)

    def test_material_noop_stops_before_any_additional_creates(self):
        _,ticket=self.extension();self.native.wall_modify_noop=True;count=len(self.native.writes)
        result=EXT.execute(self.native,ticket,self.state/'scene-v1-attempts.sqlite3',ticket['confirmPlanHash'])
        self.assertEqual(result['status'],'PARTIAL_OR_UNKNOWN_OUTCOME',result)
        self.assertIn('WALL_MATERIAL_READBACK_MISMATCH',result['reason'])
        self.assertEqual(self.native.writes[count:],['ModifyWalls'])

    def test_authored_column_outside_building_and_unsupported_command_block(self):
        intent=json.loads((ROOT/'examples/accelerator/isolated-authored-building.json').read_text(encoding='utf8'))
        intent['nativeComponents'][0]['params']['columnsData'][0]['coordinates']['x']=500
        with self.assertRaisesRegex(ValueError,'OUTSIDE_BUILDING'):
            A.compile_authored_intent(intent,A.RUN.DEFAULT_SCENE_SCHEMA,self.native)
        intent['nativeComponents'][0]={'command':'DeleteElements'}
        with self.assertRaisesRegex(ValueError,'UNSUPPORTED_AUTHORED_NATIVE_COMPONENT'):
            A.compile_authored_intent(intent,A.RUN.DEFAULT_SCENE_SCHEMA,self.native)
        self.assertFalse(self.native.writes)

    def test_full_authored_input_counts_proven_column_segments(self):
        self.intent=json.loads((ROOT/'examples/accelerator/isolated-authored-building.json').read_text(encoding='utf8'))
        pre=self.run_project();result=self.run_project('execute',pre['confirmPlanHash'])
        self.assertEqual(result['status'],'COMPLETE_UNSAVED',result)
        self.assertEqual(len(result['addedGuids']),19)
        self.assertEqual(len(result['ownedColumnSegments']),2)
        self.assertEqual(len(result['scene']['steps']),17)

    def test_unrelated_extra_guid_still_blocks_final_acceptance(self):
        _,ticket=self.extension()
        def transport(cmd,params):
            if cmd=='GetSubelementsOfHierarchicalElements':
                self.native.existing.append('99999999-9999-4999-8999-999999999999')
            return self.native(cmd,params)
        result=EXT.execute(transport,ticket,self.state/'scene-v1-attempts.sqlite3',ticket['confirmPlanHash'])
        self.assertEqual(result['status'],'PARTIAL_OR_UNKNOWN_OUTCOME',result)
        self.assertIn('FINAL_WHOLE_MODEL_GUID_DIFF',result['reason'])

    def test_existing_window_edit_and_explicit_restore_preserve_all_guids(self):
        _,ticket=self.extension();journal=self.state/'scene-v1-attempts.sqlite3'
        result=EXT.execute(self.native,ticket,journal,ticket['confirmPlanHash'])
        self.assertEqual(result['status'],'COMPLETE_UNSAVED',result)
        initial=A.inventory_guids(self.native);plan=ticket['preflight'];count=len(self.native.writes)
        for op_id,width in [('edit-window-01',1.4),('restore-window-01',1.2)]:
            edit=EXT.prepare_opening_width(self.native,plan,result['steps'],'authored-window-east-1',width,journal,op_id)
            receipt=EXT.execute_opening_width(self.native,edit,journal,edit['confirmPlanHash'])
            self.assertEqual(receipt['status'],'EXISTING_OPENING_EDIT_READBACK_PASS',receipt)
            plan=edit['intent']['newPlan']
        self.assertEqual(A.inventory_guids(self.native),initial)
        self.assertEqual(self.native.writes[count:],['ModifyWindows','ModifyWindows'])
        self.assertEqual(plan['sourcePlanHash'],ticket['preflight']['sourcePlanHash'])
