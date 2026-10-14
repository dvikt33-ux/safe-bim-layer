import sys,unittest,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from archicad_dynamic_commands import DynamicCommands
import archicad_project_accelerator as A

class MassTests(unittest.TestCase):
    def router(self):
        return DynamicCommands(dict(common_schemas={},_metadata=dict(provider_version='1.5.10'),commands={
            'GetSource':dict(name='GetSource',version='1',category='Test',parameters=dict(type='object',maxProperties=0),returns=dict(type='object',properties={'value':dict(type='integer')},required=['value'])),
            'Consume':dict(name='Consume',version='1',category='Test',parameters=dict(type='object',properties={'value':dict(type='integer')},required=['value']),returns=dict(type='object'))}))

    def test_name_never_grants_read_and_policy_changes_invalidate_ticket(self):
        r=self.router();ticket=r.prepare('GetSource',{})
        with self.assertRaises(ValueError):r.read(None,ticket,True)
        r.review_policy('GetSource','READ_ONLY','READ_ONLY',dict(source='synthetic reviewed implementation',sha256='1'*64))
        with self.assertRaises(ValueError):r.validate(ticket)
        self.assertEqual(r.prepare('GetSource',{})['effect'],'READ_ONLY')

    def test_existing_graph_resolves_data_dependencies_and_rejects_cycle(self):
        r=self.router();graph=dict(operations=[dict(id='source',command='GetSource',params={}),dict(id='consumer',command='Consume',params=dict(value={'$result':dict(step='source',pointer='/value')}))])
        plan=r.prepare_workflow(graph);self.assertEqual(plan['executionOrder'],['source','consumer']);self.assertEqual(plan['dependencies']['consumer'],['source'])
        graph['operations'][0]['after']=['consumer']
        with self.assertRaises(ValueError):r.prepare_workflow(graph)

    def test_provider_schema_refs_and_identifiers_are_namespaced(self):
        r=self.router();r.add_provider('Vendor',{'Call':dict(version='1',category='Test',parameters={'$ref':'#/Payload'},returns=dict(type='object'))},'synthetic source',{'Payload':dict(type='object',properties={'n':dict(type='integer')},required=['n'])})
        ticket=r.prepare('AddOn.Vendor.Call',{'n':2});self.assertEqual(ticket['command'],'AddOn.Vendor.Call')
        with self.assertRaises(Exception):r.prepare('AddOn.Vendor.Call',{'n':'bad'})
        self.assertEqual(r.select(ticket['command'])['runtimeRegistered'],None)

    def test_unknown_model_target_cannot_escape_scope(self):
        r=self.router();r.catalog['commands']['Consume']['parameters']=dict(type='object');r.fingerprint=A.RUN.digest(r.catalog)
        r.review_policy('Consume','MODIFY','MODEL',dict(source='synthetic reviewed implementation',sha256='1'*64))
        ticket=r.prepare('Consume',dict(elementId=dict(guid='11111111-1111-4111-8111-111111111111')))
        with self.assertRaises(ValueError):r.scope(ticket,{},[],[],'explicit test','MODEL')

if __name__=='__main__':unittest.main()
