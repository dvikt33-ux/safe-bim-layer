"""Synthetic exact group membership contract; no Archicad connection."""
import copy,unittest
from test_apa_ac29_native_copy_verifier import gid,models,ReadOnlyApi,V
from test_apa_ac29_mass_request import router,A
import apa_ac29_native_group_create as N
from apa_ac29_dynamic_native_verifiers import installed_verifiers

def params():return dict(memberIds=[dict(guid=gid(10)),dict(guid=gid(11))],sourceRef='native-source-receipt')

class Api(ReadOnlyApi):
    def __init__(self,after=False,other_changed=False):super().__init__();self.after=after;self.other_changed=other_changed
    def __call__(self,name,p):
        if name=='GetNativeGroupRootsV1':
            rows=[]
            for r in p['elements']:
                g=r['elementId']['guid'];group=(gid(888) if self.other_changed else gid(777)) if g==gid(1) else gid(999) if self.after else V.NULL
                rows.append(dict(elementId=dict(guid=g),groupId=dict(guid=group),rootGroupId=dict(guid=group)))
            return dict(nativeModelWrites=0,groups=rows)
        if name=='GetNativeGroupMembersV1':return dict(nativeModelWrites=0,groupId=dict(guid=gid(999)),memberIds=[dict(guid=gid(10)),dict(guid=gid(11))])
        return super().__call__(name,p)

class GroupCreateTests(unittest.TestCase):
    def pre(self,native=None):
        return N.before(api=Api(),command=N.CMD,parameters=params(),affected=[gid(10),gid(11)],native_before=native or models()[1])
    def post(self,native=None,api=None,reply=None):
        b=models()[1];ids={x['guid'] for x in b['elements']}
        return N.after(api=api or Api(True),command=N.CMD,parameters=params(),
            native_response=reply or dict(nativeModelWrites=1,groupId=dict(guid=gid(999)),memberCount=2),
            before_guids=ids,after_guids=ids,affected=[gid(10),gid(11)],native_before=b,
            native_after=native or b,source_proof=self.pre(b))
    def test_auto_selector_uses_one_existing_native_group_command_and_modify_member_scope(self):
        r=router();N.attach(r);r.register_availability(N.CMD,True)
        t=dict(schemaVersion=N.SCHEMA,request='Сгруппировать колонны',sourceRef=params()['sourceRef'],memberGuids=[gid(10),gid(11)])
        selected=A.prepare_auto_optimized_native_task(r,t)
        self.assertEqual(selected['requiredRuntimeCommands'],[N.CMD]);self.assertEqual(selected['nativeCallCountIfAuthorized'],1)
        p=selected['selectedNativeTaskPreview']['workflow']['graph']['operations'][0]['params']
        ticket=r.prepare(N.CMD,p)
        self.assertEqual(ticket['effect'],'MODIFY')
        scope=r.scope(ticket,{},[gid(10),gid(11)],[gid(1)],'USER_APPROVED_SYNTHETIC_GROUP','MODEL')
        self.assertEqual(scope['affectedGuids'],[gid(10),gid(11)])
        self.assertEqual(installed_verifiers()[N.VERIFIER].effect,'MODIFY')
    def test_exact_native_membership_and_other_groups_preserved(self):
        result=self.post();self.assertEqual(result['groupId'],gid(999));self.assertTrue(result['otherColumnGroupsUnchanged'])
    def test_unknown_or_duplicate_member_and_wrong_scope_fail_before_dispatch(self):
        for p in (dict(memberIds=params()['memberIds']*2,sourceRef='valid-source'),dict(memberIds=[dict(guid='missing')]*2,sourceRef='valid-source')):
            with self.assertRaises(ValueError):N.members(p)
        with self.assertRaisesRegex(ValueError,'EXPLICIT_EXISTING'):
            N.before(api=Api(),command=N.CMD,parameters=params(),affected=[],native_before=models()[1])
    def test_already_grouped_members_rejected(self):
        with self.assertRaisesRegex(ValueError,'EXISTING_GROUP'):
            N.before(api=Api(True),command=N.CMD,parameters=params(),affected=[gid(10),gid(11)],native_before=models()[1])
    def test_other_group_mutation_rejected(self):
        with self.assertRaisesRegex(ValueError,'OTHER_GROUP_CHANGED'):self.post(api=Api(True,True))
    def test_changed_material_or_geometry_rejected(self):
        for mutate in (lambda n:n['materials'][0]['color'].update(r=.9),lambda n:n['elements'][-1]['bodies'][0]['vertices'][0].__setitem__(0,99)):
            n=copy.deepcopy(models()[1]);mutate(n)
            with self.assertRaises(ValueError):self.post(native=n)
    def test_response_count_writecount_or_error_is_not_pass(self):
        for reply in (dict(error=dict(code=1)),dict(nativeModelWrites=2,groupId=dict(guid=gid(999)),memberCount=2),
                      dict(nativeModelWrites=1,groupId=dict(guid=gid(999)),memberCount=3)):
            with self.assertRaises(ValueError):self.post(reply=reply)

if __name__=='__main__':unittest.main()
