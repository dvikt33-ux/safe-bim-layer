"""Synthetic new Slab contracts; these tests are not Archicad LIVE evidence."""
from pathlib import Path
import copy,sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import apa_ac29_native_copy_verifier as V
import apa_ac29_mass_request as Q
from test_apa_ac29_native_copy_verifier import gid,body

def detail(x=0):
    return dict(type='Slab',floorIndex=0,details=dict(structureType='Basic',thickness=3,
        zCoordinate=3,offsetFromTop=0,referencePlaneLocation='Top',buildingMaterialId=dict(guid=gid(99)),
        floorFill=dict(use=False,orientation=dict(type='Global',origin=dict(x=0,y=0))),
        polygonOutline=[dict(x=x,y=0),dict(x=x+.3,y=0),dict(x=x+.3,y=.3),dict(x=x,y=.3),dict(x=x,y=0)],holes=[]))

def slab(g,x=0):return dict(guid=g,type='Slab',homeStory=0,relationships={},materialBindings={},bodies=[body(g,x)])

class Api:
    def __init__(self):self.details={gid(1):detail(),gid(2):detail(10),gid(3):detail(20)};self.calls=[]
    def __call__(self,name,p):
        self.calls.append(name)
        if name=='GetNativeGroupRootsV1':
            return dict(nativeModelWrites=0,groups=[dict(elementId=r['elementId'],groupId=dict(guid=V.NULL),rootGroupId=dict(guid=V.NULL)) for r in p['elements']])
        if name=='GetDetailsOfElements':return dict(detailsOfElements=[self.details[r['elementId']['guid']] for r in p['elements']])
        raise AssertionError(name)

class SlabCopy(unittest.TestCase):
    def model(self):return dict(elements=[slab(gid(1))],materials=[dict(id=1,attribute=dict(guid=gid(99)))])
    def params(self):return dict(elementsWithMoveVectors=[dict(elementId=dict(guid=gid(1)),copy=True,moveVector=dict(x=x,y=0,z=0)) for x in (10,20)])
    def pre(self,b,api=None):return V.verify_before(api=api or Api(),command=V.CMD,parameters=self.params(),affected=[],native_before=b)
    def post(self,b,a,p,api=None):
        return V.verify_after(api=api or Api(),command=V.CMD,parameters=self.params(),native_response=dict(executionResults=[dict(success=True)]*2),
            before_guids={r['guid'] for r in b['elements']},after_guids={r['guid'] for r in a['elements']},affected=[],native_before=b,native_after=a,source_proof=p)
    def test_exact_slab_batch_no_automatic_segments(self):
        b=self.model();p=self.pre(b);a=copy.deepcopy(b);a['elements'] += [slab(gid(2),10),slab(gid(3),20)]
        r=self.post(b,a,p);self.assertEqual(r['newRootGuids'],[gid(2),gid(3)]);self.assertEqual(r['newChildGuids'],[])
        self.assertEqual(p['sourceFacts'][gid(1)]['anchor'],dict(x=0,y=0,z=3))
    def test_holes_fill_profiles_and_unknown_outline_rejected_before_write(self):
        for change in [dict(holes=[[dict(x=.1,y=.1)]]),dict(structureType='Composite'),dict(referencePlaneLocation='Bottom'),dict(floorFill=dict(use=True)),dict(offsetFromTop=.1)]:
            api=Api();api.details[gid(1)]['details'].update(change)
            with self.assertRaisesRegex(ValueError,'SLAB_REQUIRES'):self.pre(self.model(),api)
        api=Api();api.details[gid(1)]['details']['polygonOutline'][1]['arcAngle']=.1
        with self.assertRaisesRegex(ValueError,'SLAB_REQUIRES'):self.pre(self.model(),api)
    def test_cut_source_and_hosted_dependents_rejected(self):
        b=self.model();b['elements'][0]['bodies'][0]['vertices'][0][0]+=.01
        with self.assertRaisesRegex(ValueError,'RECTANGLE_EXTRUSION'):self.pre(b)
        b=self.model();b['elements'].append(dict(guid=gid(8),type='Opening',relationships=dict(hostGuid=gid(1))))
        with self.assertRaisesRegex(ValueError,'DEPENDENTS'):self.pre(b)
    def test_copy_shape_and_material_drift_fail_closed(self):
        for mutate in ('shape','material','typed'):
            b=self.model();p=self.pre(b);a=copy.deepcopy(b);a['elements'] += [slab(gid(2),10),slab(gid(3),20)];api=Api()
            if mutate=='shape':a['elements'][-1]['bodies'][0]['vertices'][0][0]+=.01
            if mutate=='material':a['elements'][-1]['bodies'][0]['faces'][0]['nativeStatus']=9
            if mutate=='typed':api.details[gid(3)]['details']['buildingMaterialId']['guid']=gid(98)
            with self.assertRaises(ValueError):self.post(b,a,p,api)
    def test_mass_request_selects_existing_native_copy_for_slab(self):
        from archicad_dynamic_commands import DynamicCommands
        import archicad_project_accelerator as A
        r=DynamicCommands(A.catalog_with_provenance(Path(__file__).resolve().parents[1]/'schemas/tapir-live-1.5.10/tapir-scene-live.json'))
        source=dict(guid=gid(1),type='Slab',storyIndex=0,anchor=dict(x=0,y=0,z=3),familySignature='verified-slab-family-01',nativeReadbackVerified=True,
            nativeDependenciesVerified=True,dependentElementGuids=[])
        t=dict(schemaVersion=Q.SCHEMA,request='Копировать перекрытие по линии',sourceRef='https://github.com/example/source',existing=[source],assembly=None,
            placements=dict(mode='LINEAR',count=2,start=dict(dx=10,dy=0,dz=0),step=dict(dx=10,dy=0,dz=0)))
        n=Q.normalize_mass_request(t);plan=r.plan_reuse_existing(n['existing'],n['targets'])
        self.assertEqual(plan['nativeCopyCallsRequired'],1)
        self.assertEqual(plan['newCopyCount'],2)
        self.assertEqual(plan['copyGroups'][0]['prototypeType'],'Slab')
        self.assertEqual(plan['unmatchedTargetsPendingPrototype'],[])

if __name__=='__main__':unittest.main()
