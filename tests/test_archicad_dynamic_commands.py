import sys,unittest,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import archicad_project_accelerator as A
from archicad_dynamic_commands import DynamicCommands

def router():
    r=DynamicCommands(dict(common_schemas={},commands={'NewNativeCommand':dict(name='NewNativeCommand',version='1',category='Test',parameters=dict(type='object',properties={'value':dict(type='integer')},required=['value'],additionalProperties=False),returns=dict(type='object',properties={'success':dict(type='boolean')},required=['success']))}))
    r.review_policy('NewNativeCommand','MODIFY','MODEL',dict(source='synthetic reviewed contract',sha256='1'*64))
    return r

class DynamicTests(unittest.TestCase):
    def test_new_command_no_name_handler_and_schema_gate(self):
        r=router();ticket=r.prepare('NewNativeCommand',{'value':2});self.assertEqual(r.select('NewNativeCommand')['status'],'SCHEMA_VALID')
        with self.assertRaises(Exception):r.prepare('NewNativeCommand',{'value':'bad'})
        with self.assertRaises(ValueError):r.read(None,ticket,True)

    def test_ticket_cannot_grant_different_call(self):
        r=router();ticket=r.prepare('NewNativeCommand',{'value':2})
        with tempfile.TemporaryDirectory() as temp:
            api=A.EvidenceAPI(lambda *_:{'success':True},temp);api.bind_dynamic_commands(r)
            scope=r.scope(ticket,{},[],[],'synthetic-test','MODEL')
            with self.assertRaises(ValueError):
                with api.dynamic_call(ticket):pass
            with api.dynamic_call(ticket,journal_scope=scope):
                with self.assertRaises(ValueError):api('NewNativeCommand',{'value':3})
            with self.assertRaises(ValueError):api('NewNativeCommand',{'value':2})

    def test_existing_scene_writer_journal_and_unknown_no_replay(self):
        r=router();ticket=r.prepare('NewNativeCommand',{'value':2});binding={'path':'synthetic.pln'}
        scope=r.scope(ticket,binding,[],[],'synthetic-test','MODEL')
        with tempfile.TemporaryDirectory() as temp:
            calls=[];api=A.EvidenceAPI(lambda *a:calls.append(a) or {'success':True},temp);api.bind_dynamic_commands(r)
            w=A.RUN.SceneWriter(api,Path(temp)/'existing.sqlite3');w.guarded_binding=lambda:binding
            pre=dict(sourcePlanHash=ticket['hash'],binding=binding,integrationBindings=dict(dependencies=dict(dynamicOperation=scope)))
            intent=dict(sceneId='dynamic-synthetic-01',sourcePlanHash=ticket['hash'],command=ticket['command'],parameters=ticket['parameters'],target=binding)
            def unknown(*_):raise ValueError('READBACK_UNCERTAIN')
            result=w.execute_bound_operation(pre,intent['sceneId'],ticket['command'],ticket['parameters'],A.RUN.digest(intent),lambda:{'status':'PASS'},unknown)
            self.assertEqual(result['status'],'PARTIAL_OR_UNKNOWN_OUTCOME')
            with self.assertRaises(ValueError):w.execute_bound_operation(pre,intent['sceneId'],ticket['command'],ticket['parameters'],A.RUN.digest(intent),lambda:{'status':'PASS'},unknown)
            self.assertEqual(len(calls),1)

if __name__=='__main__':unittest.main()
