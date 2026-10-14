import unittest,sys,copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import archicad_project_accelerator as A
import test_archicad_mass_capabilities as M

class ExecutableWorkflowTests(unittest.TestCase):
    def test_source_policy_rebinds_only_identical_contracts(self):
        r=M.MassTests().router();manifest=dict(catalogHash='old-project',operations={'GetSource':dict(kind='READ_ONLY',impact='READ_ONLY',evidence=dict(source='reviewed implementation',sha256='1'*64))},contractHashes={'GetSource':r.contract_hash('GetSource')})
        r.load_policies(manifest);r.catalog['commands']['GetSource']['version']='changed'
        with self.assertRaises(ValueError):r.load_policies(manifest)

    def test_created_success_union_and_high_level_task_use_existing_graph(self):
        r=M.MassTests().router();r.catalog['commands']['GetSource']['returns']=dict(type='object',properties={'value':{'oneOf':[dict(type='object',properties={'value':dict(type='integer')},required=['value']),dict(type='object',properties={'error':dict(type='string')},required=['error'])]}});r.fingerprint=A.RUN.digest(r.catalog)
        intent=dict(schemaVersion='apa-native-task/1',request='Create and edit a native test element',graph=dict(operations=[dict(id='source',command='GetSource',params={}),dict(id='next',command='Consume',params={'value':{'$result':dict(step='source',pointer='/value/value')}})]))
        preview=A.compile_intent(intent,None,router=r);self.assertEqual(preview['workflow']['executionOrder'],['source','next']);self.assertFalse(preview['executionPermission'])

    def test_create_host_guid_cannot_implicitly_mutate_retained_model(self):
        r=M.MassTests().router();r.catalog['commands']['Consume']['parameters']=dict(type='object');r.fingerprint=A.RUN.digest(r.catalog);r.review_policy('Consume','CREATE','MODEL',dict(source='reviewed host creation',sha256='1'*64))
        guid='11111111-1111-4111-8111-111111111111';t=r.prepare('Consume',dict(ownerWallId=dict(guid=guid)))
        with self.assertRaises(ValueError):r.scope(t,{},[],[guid],'explicit temporary creation','MODEL')

if __name__=='__main__':unittest.main()
