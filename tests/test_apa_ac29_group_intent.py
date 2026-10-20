"""New request recognition delegates to accepted original native adapters."""
import copy,unittest
from test_apa_ac29_native_group_create import gid,router,A
import apa_ac29_group_intent as I

def request(action):
    return dict(schemaVersion=I.SCHEMA,request={'CREATE':'Сгруппировать выбранные колонны','MOVE':'Переместить целую группу','UNGROUP':'Разгруппировать выбранную группу'}[action],
        sourceRef='https://github.com/dvikt33-ux/safe-bim-layer/pull/185',memberGuids=[gid(10),gid(11)],
        groupGuid=None if action=='CREATE' else gid(999),translation=dict(dx=100,dy=0,dz=0) if action=='MOVE' else None)

class IntentTests(unittest.TestCase):
    def test_each_request_selects_one_existing_command_without_input_mutation(self):
        for action,adapter in [('CREATE',I.N),('MOVE',I.M),('UNGROUP',I.U)]:
            with self.subTest(action=action):
                task=request(action);before=copy.deepcopy(task);r=router();adapter.attach(r);r.register_availability(adapter.CMD,True)
                result=A.prepare_auto_optimized_native_task(r,task)
                self.assertEqual(result['requiredRuntimeCommands'],[adapter.CMD]);self.assertEqual(result['nativeCallCountIfAuthorized'],1)
                self.assertEqual(result['recognizedGroupIntent']['codeOwnedVerifier'],adapter.VERIFIER)
                self.assertFalse(result['recognizedGroupIntent']['coordinatesInferred']);self.assertEqual(task,before)
                ops=result['selectedNativeTaskPreview']['workflow']['graph']['operations'];self.assertEqual(len(ops),1)
    def test_english_bounded_actions_select_same_adapters(self):
        for action,text,adapter in [('CREATE','Group selected columns',I.N),('MOVE','Move selected group',I.M),('UNGROUP','Ungroup selected group',I.U)]:
            task=request(action);task['request']=text
            typed,_=I.normalize(task);self.assertEqual(typed['schemaVersion'],adapter.SCHEMA)
    def test_composite_boolean_unknown_and_copy_requests_fail_closed(self):
        for text in ('Сгруппировать и переместить группу','Разгруппировать и переместить группу',
                     'boolean union group bodies','Скопировать группу','Просто проверить группу'):
            task=request('MOVE');task['request']=text
            with self.subTest(text=text),self.assertRaises(ValueError):I.normalize(task)
    def test_missing_source_guids_group_or_translation_cannot_be_inferred(self):
        for task in (dict(request('MOVE'),translation=None),dict(request('MOVE'),groupGuid=None),
                     dict(request('CREATE'),memberGuids=[]),dict(request('CREATE'),sourceRef=''),
                     dict(request('UNGROUP'),translation=dict(dx=1,dy=0,dz=0))):
            with self.assertRaises(ValueError):I.normalize(task)
    def test_unprobed_runtime_never_gets_write_preview_or_permission(self):
        result=A.prepare_auto_optimized_native_task(router(False),request('MOVE'))
        self.assertIsNone(result['selectedNativeTaskPreview']);self.assertFalse(result['nativeWritePermission'])

if __name__=='__main__':unittest.main()
