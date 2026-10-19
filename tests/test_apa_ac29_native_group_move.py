"""Whole group move contracts: exact source, scope, collision and readback."""
import copy,unittest
from test_apa_ac29_native_group_create import Api,gid,models,router,A
import apa_ac29_native_group_move as M

def params(dx=100):return dict(groupId=dict(guid=gid(999)),sourceRef='accepted-native-group',translation=dict(dx=dx,dy=0,dz=0))
OWNED=[gid(10),gid(11),gid(20),gid(21)]
class Moved(Api):
    def __init__(self,wrong=False):super().__init__(True);self.wrong=wrong
    def __call__(self,name,p):
        r=super().__call__(name,p)
        if name=='GetDetailsOfElements':
            for row in r['detailsOfElements']:row['details']['origin']['x']+=99 if self.wrong else 100
        return r
def moved():
    n=copy.deepcopy(models()[1])
    for row in n['elements']:
        if row['guid'] in OWNED:
            for body in row['bodies']:
                for v in body['vertices']:v[0]+=100
    return n
class MoveTests(unittest.TestCase):
    def pre(self,p=None,affected=None):
        return M.before(api=Api(True),command=M.CMD,parameters=p or params(),affected=affected or OWNED,native_before=models()[1])
    def post(self,api=None,native=None):
        b=models()[1];ids={r['guid'] for r in b['elements']}
        return M.after(api=api or Moved(),command=M.CMD,parameters=params(),native_response=dict(nativeModelWrites=2,groupId=dict(guid=gid(999)),movedMembers=[dict(guid=gid(10)),dict(guid=gid(11))]),
            before_guids=ids,after_guids=ids,affected=OWNED,native_before=b,native_after=native or moved(),source_proof=self.pre())
    def test_exact_translated_group_retains_guid_shape_material_and_membership(self):
        r=self.post();self.assertEqual(r['groupId'],gid(999));self.assertTrue(r['allColumnGroupsUnchanged'])
        self.assertEqual([x['target']['x'] for x in r['mapping']],[110,120])
    def test_move_selector_chooses_one_native_group_command(self):
        r=router();M.attach(r);r.register_availability(M.CMD,True)
        t=dict(schemaVersion=M.SCHEMA,request='Переместить целую группу',sourceRef=params()['sourceRef'],groupGuid=gid(999),memberGuids=[gid(10),gid(11)],translation=params()['translation'])
        p=A.prepare_auto_optimized_native_task(r,t);self.assertEqual(p['requiredRuntimeCommands'],[M.CMD]);self.assertEqual(p['nativeCallCountIfAuthorized'],1)
    def test_owned_segments_must_be_authorized(self):
        with self.assertRaisesRegex(ValueError,'FULL_OWNED'):self.pre(affected=[gid(10),gid(11)])
    def test_target_collision_rejected(self):
        with self.assertRaisesRegex(ValueError,'TOUCH_OR_INTERSECT'):self.pre(params(-10))
    def test_wrong_typed_target_or_retained_model_change_rejected(self):
        with self.assertRaisesRegex(ValueError,'POSITION_SHAPE'):self.post(api=Moved(True))
        n=moved();n['elements'][2]['bodies'][0]['vertices'][0][0]+=1
        with self.assertRaisesRegex(ValueError,'RETAINED_PHYSICAL'):self.post(native=n)
    def test_zero_vertical_or_nonfinite_shift_rejected(self):
        for s in (dict(dx=0,dy=0,dz=0),dict(dx=1,dy=0,dz=1),dict(dx=float('nan'),dy=0,dz=0)):
            with self.assertRaises(ValueError):M.shift(s)
if __name__=='__main__':unittest.main()
