"""Synthetic shared-scope tests; never Archicad LIVE evidence."""
from pathlib import Path
import copy,json,sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import apa_ac29_native_copy_verifier as V
from apa_ac29_dynamic_native_verifiers import installed_verifiers

def gid(i):return f'00000000-0000-4000-8000-{i:012d}'

def body(g,x):
    box=V.C.explicit_box_body(dict(x=.3,y=.3,z=3))
    return dict(parentGuid=g,closed=True,
        vertices=[[p['x']+x,p['y'],p['z']] for p in box['vertices']],
        faces=[dict(contours=[p['vertexIds']],materialId=1,nativeStatus=0) for p in box['polygons']])

def column(g,c,x):
    return [dict(guid=g,type='Column',homeStory=0,relationships={},materialBindings={},bodies=[]),
        dict(guid=c,type='ColumnSegment',homeStory=0,relationships=dict(hostGuid=g),materialBindings={},bodies=[body(c,x)])]

def models():
    original=column(gid(1),gid(2),0)
    original.append(dict(guid=gid(3),type='Wall',homeStory=0,relationships={},materialBindings={},bodies=[body(gid(3),50)]))
    before=dict(elements=original,materials=[dict(id=1,modelMaterialIndex=1,attribute=dict(guid=gid(90)),color=dict(r=.5),texture=dict(name='same'))])
    after=copy.deepcopy(before)
    after['elements']+=column(gid(10),gid(20),10)+column(gid(11),gid(21),20)
    return before,after

def params():return dict(elementsWithMoveVectors=[dict(elementId=dict(guid=gid(1)),moveVector=dict(x=x,y=0,z=0),copy=True) for x in (10,20)])

class ReadOnlyApi:
    def __init__(self,grouped=False):self.calls=[];self.grouped=grouped
    def __call__(self,name,p):
        self.calls.append(name)
        if name=='GetNativeGroupRootsV1':
            return dict(nativeModelWrites=0,groups=[dict(elementId=r['elementId'],groupId=dict(guid=gid(999) if self.grouped else V.NULL),rootGroupId=dict(guid=gid(999) if self.grouped else V.NULL)) for r in p['elements']])
        if name=='GetDetailsOfElements':
            rows=[]
            for r in p['elements']:
                g=r['elementId']['guid'];x={gid(1):0,gid(10):10,gid(11):20}[g]
                rows.append(dict(elementId=dict(guid=g),type='Column',floorIndex=0,details=dict(origin=dict(x=x,y=0),zCoordinate=0,height=3,width=.3)))
            return dict(detailsOfElements=rows)
        raise AssertionError('unexpected native command:'+name)

class SharedCopy(unittest.TestCase):
    def copy_router(self,kind='CREATE'):
        from archicad_dynamic_commands import DynamicCommands
        import archicad_project_accelerator as A
        r=DynamicCommands(A.catalog_with_provenance(Path(__file__).resolve().parents[1]/'schemas/tapir-live-1.5.10/tapir-scene-live.json'))
        r.review_policy('MoveElements',kind,'MODEL',dict(source='PR143 source copy branch',sha256=r.contract_hash('MoveElements')))
        return r

    def test_shared_create_scope_accepts_only_retained_copy_prototypes(self):
        r=self.copy_router();ticket=r.prepare('MoveElements',params())
        s=r.scope(ticket,{},[],[gid(1)],'USER_APPROVED_SYNTHETIC_COPY','MODEL')
        self.assertEqual(s['affectedGuids'],[])
        self.assertEqual(s['retainedGuids'],[gid(1)])
        self.assertEqual(s['copySourceGuids'],[gid(1)])
        r.qualify_scope(s,'MoveElements',params(),ticket['hash'])

    def test_copy_scope_cannot_import_source_from_outside_baseline(self):
        r=self.copy_router();ticket=r.prepare('MoveElements',params())
        with self.assertRaisesRegex(ValueError,'SOURCE_OUTSIDE_AUTHORIZED_BASELINE'):
            r.scope(ticket,{},[],[gid(99)],'USER_APPROVED_SYNTHETIC_COPY','MODEL')

    def test_real_relocation_cannot_modify_retained_source(self):
        r=self.copy_router('MODIFY');p=params()
        for row in p['elementsWithMoveVectors']:row['copy']=False
        ticket=r.prepare('MoveElements',p)
        with self.assertRaisesRegex(ValueError,'TARGET_OUTSIDE_AUTHORIZED_SCOPE'):
            r.scope(ticket,{},[],[gid(1)],'USER_APPROVED_SYNTHETIC_MODIFY','MODEL')

    def pre(self,b=None,p=None,api=None):
        return V.verify_before(api=api or ReadOnlyApi(),command=V.CMD,parameters=p or params(),affected=[],native_before=b or models()[0])
    def post(self,b,a,proof,reply=None):
        return V.verify_after(api=ReadOnlyApi(),command=V.CMD,parameters=params(),native_response=reply or dict(executionResults=[dict(success=True)]*2),before_guids={r['guid'] for r in b['elements']},after_guids={r['guid'] for r in a['elements']},affected=[],native_before=b,native_after=a,source_proof=proof)

    def test_registry_adds_create_without_replacing_translation_modify(self):
        r=installed_verifiers();self.assertEqual(r['VerifiedNativeBatchCopy'].effect,'CREATE')
        self.assertEqual(r['VerifiedNativeTranslation'].effect,'MODIFY')

    def test_exact_two_column_copies_with_owned_segments(self):
        b,a=models();p=self.pre(b);r=self.post(b,a,p)
        self.assertEqual(r['newRootGuids'],[gid(10),gid(11)])
        self.assertEqual(r['newChildGuids'],[gid(20),gid(21)])
        self.assertTrue(r['allOriginalGeometryAndFaceMaterialsPreserved'])

    def test_persisted_source_proof_and_material_pool_reindexing(self):
        b,a=models();p=json.loads(json.dumps(self.pre(b)))
        a['materials'][0].update(id=4,modelMaterialIndex=4)
        for row in a['elements']:
            for body in row['bodies']:
                for face in body['faces']:face['materialId']=4
        self.assertEqual(self.post(b,a,p)['newPhysicalCopyCount'],2)

    def test_relocation_and_mixed_batch_rejected_before_reads(self):
        for value in (False,None):
            p=params();p['elementsWithMoveVectors'][0]['copy']=value;api=ReadOnlyApi()
            with self.assertRaisesRegex(ValueError,'RELOCATION_OR_MIXED'):self.pre(p=p,api=api)
            self.assertEqual(api.calls,[])

    def test_vertical_copy_and_duplicate_target_rejected(self):
        p=params();p['elementsWithMoveVectors'][0]['moveVector']['z']=1
        with self.assertRaisesRegex(ValueError,'HORIZONTAL'):self.pre(p=p)
        p=params();p['elementsWithMoveVectors'][1]=copy.deepcopy(p['elementsWithMoveVectors'][0])
        with self.assertRaisesRegex(ValueError,'UNIQUE_BOUNDED'):self.pre(p=p)

    def test_existing_group_never_silently_copies_one_member(self):
        with self.assertRaisesRegex(ValueError,'WHOLE_GROUP_ADAPTER'):self.pre(api=ReadOnlyApi(grouped=True))

    def test_collision_rejected_using_actual_source_brep(self):
        p=params();p['elementsWithMoveVectors'][0]['moveVector']['x']=50
        with self.assertRaisesRegex(ValueError,'BREP_CONTACT'):self.pre(p=p)

    def test_changed_old_face_material_rejected(self):
        b,a=models();p=self.pre(b);a['materials'][0]['color']['r']=.7
        with self.assertRaisesRegex(ValueError,'GEOMETRY_OR_MATERIAL_CHANGED'):self.post(b,a,p)

    def test_changed_copy_brep_rejected(self):
        b,a=models();p=self.pre(b);a['elements'][-1]['bodies'][0]['vertices'][0][0]+=.02
        with self.assertRaisesRegex(ValueError,'BREP_ATTRIBUTES_NOT_UNIQUE'):self.post(b,a,p)

    def test_lost_native_segment_owner_rejected(self):
        b,a=models();p=self.pre(b);a['elements'][-1]['relationships']['hostGuid']=gid(1)
        with self.assertRaises(ValueError):self.post(b,a,p)

    def test_partial_native_response_never_claims_success(self):
        b,a=models();p=self.pre(b)
        with self.assertRaisesRegex(ValueError,'UNKNOWN_NO_REPLAY'):self.post(b,a,p,dict(executionResults=[dict(success=True)]))


if __name__=='__main__':unittest.main()
