"""New group edit adapter uses original selector and membership readback."""
import copy,unittest
from test_apa_ac29_native_group_create import Api,gid,models,router,A
import apa_ac29_native_group_ungroup as U

def params():return dict(groupId=dict(guid=gid(999)),sourceRef='accepted-native-group')
def reply():return dict(nativeModelWrites=1,previousGroupId=dict(guid=gid(999)),releasedMembers=[dict(guid=gid(10)),dict(guid=gid(11))])

class UngroupTests(unittest.TestCase):
    def pre(self,affected=None):
        return U.before(api=Api(True),command=U.CMD,parameters=params(),affected=affected if affected is not None else [gid(10),gid(11)],native_before=models()[1])
    def post(self,api=None,native=None,response=None):
        b=models()[1];ids={r['guid'] for r in b['elements']}
        return U.after(api=api or Api(False),command=U.CMD,parameters=params(),native_response=response or reply(),
            before_guids=ids,after_guids=ids,affected=[gid(10),gid(11)],native_before=b,native_after=native or b,source_proof=self.pre())
    def test_exact_release_preserves_every_guid_and_other_memberships(self):
        self.assertEqual(self.post()['previousGroupId'],gid(999))
        self.assertTrue(self.post()['allPhysicalGeometryAndMaterialsPreserved'])
    def test_auto_selects_native_ungroup_once_with_no_physical_delete_permission(self):
        r=router();U.attach(r);r.register_availability(U.CMD,True)
        task=dict(schemaVersion=U.SCHEMA,request='Разгруппировать выбранную группу',sourceRef=params()['sourceRef'],groupGuid=gid(999),memberGuids=[gid(10),gid(11)])
        p=A.prepare_auto_optimized_native_task(r,task)
        self.assertEqual(p['requiredRuntimeCommands'],[U.CMD]);self.assertEqual(p['nativeCallCountIfAuthorized'],1)
        self.assertEqual(r.operation_kind(U.CMD),'MODIFY');self.assertFalse(p['nativeWritePermission'])
    def test_partial_member_authorization_rejected(self):
        with self.assertRaisesRegex(ValueError,'EXACT_EXISTING'):self.pre([gid(10)])
    def test_still_grouped_or_other_group_changed_is_not_pass(self):
        for api in (Api(True),Api(False,True)):
            with self.assertRaisesRegex(ValueError,'OTHER_GROUP_CHANGED'):self.post(api=api)
    def test_native_error_partial_release_or_wrong_group_rejected(self):
        for response in (dict(error=dict(code=1)),dict(reply(),releasedMembers=[dict(guid=gid(10))]),
                         dict(reply(),previousGroupId=dict(guid=gid(888))),dict(reply(),nativeModelWrites=0)):
            with self.assertRaises(ValueError):self.post(response=response)
    def test_changed_physical_material_rejected(self):
        n=copy.deepcopy(models()[1]);n['materials'][0]['color']['r']=.9
        with self.assertRaisesRegex(ValueError,'PHYSICAL_GEOMETRY'):self.post(native=n)

if __name__=='__main__':unittest.main()
