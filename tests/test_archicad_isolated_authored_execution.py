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
from test_archicad_basic_slab_integration import CompositeDefaultNative
from test_archicad_project_library_pack import BM,BM_GUID


class IsolatedNative(CompositeDefaultNative):
    def __call__(self,command,params):
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
        return result


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
