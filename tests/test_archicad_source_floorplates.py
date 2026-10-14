"""Synthetic geometry/SQLite regression; never presented as Archicad LIVE."""
import copy,json,hashlib,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import archicad_project_accelerator as A
import archicad_building_shell as B
import archicad_authored_extension as E
import archicad_authored_geometry as G
from test_archicad_basic_slab_integration import CompositeDefaultNative,MATERIAL_NAME
from test_archicad_authored_native_plan import sample,HEIGHTS
from test_archicad_semantic_spatial import layout

def xy(points):return [dict(x=x,y=y) for x,y in points]
def geometry():return dict(polygonCoordinates=xy([(90,0),(100,0),(100,4),(96,4),(96,8),(90,8)]),holes=[dict(polygonCoordinates=xy([(91,1),(93,1),(93,3),(91,3)]))])
def intent():
    floor=dict(id='floor-a',story=dict(label='1 этаж',nativeIndex=0,floorId=1,level=0),thickness=.2,**geometry())
    return dict(schemaVersion='archicad-project-intent/1',projectId='source-floorplate',units='meters',components=[dict(id='source-plates',primitive='building-shell-v1',anchor=dict(x=90,y=0),specification=dict(floorPlans=[floor],slabBasicMaterialName=MATERIAL_NAME))])

class FloorplateNative(CompositeDefaultNative):
    def __call__(self,cmd,p):
        out=super().__call__(cmd,p)
        if cmd=='GetDetailsOfElements':
            g=p['elements'][0]['elementId']['guid'];entry=self.created.get(g)
            if entry and entry[0]=='CreateSlabs':
                out['detailsOfElements'][0]['details']['holes']=[dict(polygonOutline=h['polygonCoordinates']) for h in entry[1]['slabsData'][0].get('holes',[])]
                out['detailsOfElements'][0]['details']['zCoordinate']=entry[1]['slabsData'][0]['level']
        return out

class SourceFloorplateTests(unittest.TestCase):
    def test_native_source_contour_holes_and_net_area_compile_without_walls(self):
        p=A.compile_intent(intent(),A.RUN.DEFAULT_SCENE_SCHEMA)
        self.assertEqual(p['metrics']['grossFloorAreaSquareMeters'],60);self.assertEqual(len(p['graph']['operations']),1)
        self.assertEqual(p['routes']['floor-a']['executor'],'SceneWriter');self.assertEqual(p['graph']['operations'][0]['command'],'CreateSlabs')
    def test_touching_holes_self_crossings_and_opening_outside_are_denied(self):
        for points in [[(90,1),(92,1),(92,3),(90,3)],[(99,5),(100,5),(100,6),(99,6)]]:
            value=geometry();value['holes'][0]['polygonCoordinates']=xy(points)
            with self.assertRaisesRegex(ValueError,'STRICTLY_INSIDE'):B.source_floor_polygon(value)
        value=geometry();value['polygonCoordinates']=xy([(0,0),(2,2),(2,0),(0,2)]);value['holes']=[]
        with self.assertRaisesRegex(ValueError,'INVALID'):B.source_floor_polygon(value)
    def test_different_story_footprints_use_actual_independent_levels(self):
        doc=intent();second=copy.deepcopy(doc['components'][0]['specification']['floorPlans'][0]);second.update(id='floor-b',story=dict(label='upper',nativeIndex=3,floorId=7,level=4.1));second['polygonCoordinates']=xy([(90,0),(96,0),(96,8),(90,8)])
        doc['components'][0]['specification']['floorPlans'].append(second);p=A.compile_intent(doc,A.RUN.DEFAULT_SCENE_SCHEMA)
        rows=[op['params']['slabsData'][0] for op in p['graph']['operations']];self.assertEqual([r['level'] for r in rows],[0,4.1]);self.assertEqual([r['floorIndex'] for r in rows],[0,3])
    def test_hole_change_emits_one_native_edit_zero_create_same_guid(self):
        doc=intent();old=A.compile_intent(doc,A.RUN.DEFAULT_SCENE_SCHEMA);old['sourcePlanHash']='pinned';new=copy.deepcopy(doc);new['components'][0]['specification']['floorPlans'][0]['holes'][0]['polygonCoordinates']=xy([(91,1),(94,1),(94,3),(91,3)])
        g='00000000-0000-4000-8000-000000000002';created={'floor-a':dict(guid=g,kind='Slab',floorIndex=0)}
        with patch.object(E,'verify_model',return_value=created):delta=A.prepare_model_parameter_edit(None,old,created,new,A.RUN.DEFAULT_SCENE_SCHEMA)
        self.assertEqual(delta['newCreates'],0);self.assertEqual(len(delta['operations']),1);row=delta['operations'][0]['parameters']['slabsWithDetails'][0]
        self.assertEqual(row['elementId']['guid'],g);self.assertIn('polygonOutline',row);self.assertEqual(delta['newPlan']['metrics']['grossFloorAreaSquareMeters'],58)
        E.model_operation_scope('ModifySlabs',delta['operations'][0]['parameters'],'source',[g],['00000000-0000-4000-8000-000000000001'],'explicit')
    def test_missing_or_changed_hole_native_readback_cannot_pass(self):
        expected=dict(level=0,thickness=.2,**geometry());row=dict(type='Slab',floorIndex=0,details=dict(level=0,thickness=.2,polygonOutline=geometry()['polygonCoordinates'],holes=[]))
        with self.assertRaisesRegex(ValueError,'HOLE_READBACK_COUNT'):A.RUN.verify_readback('CreateSlabs',dict(slabsData=[expected]),row)
        row['details']['holes']=[dict(polygonOutline=xy([(91,1),(94,1),(94,3),(91,3)]))]
        with self.assertRaisesRegex(ValueError,'HOLE_READBACK_GEOMETRY'):A.RUN.verify_readback('CreateSlabs',dict(slabsData=[expected]),row)
    def test_same_sqlite_writer_executes_the_one_contoured_slab_source(self):
        native=FloorplateNative();preview=A.compile_intent(intent(),A.RUN.DEFAULT_SCENE_SCHEMA)
        with tempfile.TemporaryDirectory() as temp:
            writer=A.RUN.SceneWriter(native,Path(temp)/'existing.sqlite',A.RUN.DEFAULT_SCENE_SCHEMA,preview_factory=lambda *_:copy.deepcopy(preview))
            pre=writer.preflight(90,0);result=writer.execute(90,0,'source-floorplate-real-writer-fixture',pre['sourcePlanHash'])
        self.assertEqual(result['status'],'COMPLETE_UNSAVED',result);self.assertEqual(native.writes.count('CreateSlabs'),1)
    def test_authored_routes_accept_distinct_floor_contours_and_keep_one_graph(self):
        b,pack,api=sample();f=dict(polygonCoordinates=xy([(0,0),(10,0),(10,4),(8,4),(8,8),(0,8)]),holes=[dict(polygonCoordinates=xy([(6,1),(7,1),(7,2),(6,2)]))]);other=copy.deepcopy(f);other['holes']=[]
        p=A.compile_authored_native_candidate(b,pack,layout(),HEIGHTS,api,floor_plans={'level-1':f,'level-2':other})
        slabs=[s['params']['slabsData'][0] for s in p['graph']['operations'] if s['command']=='CreateSlabs'];self.assertEqual([len(s['holes']) for s in slabs],[1,0]);self.assertFalse(p['liveWriteAuthorized'])

class RuntimeIdentityTests(unittest.TestCase):
    def identity(self):return dict(contract='APA_NATIVE_RUNTIME_IDENTITY_V1',buildIdentity='a'*64,sourceRevision='b'*40,sdkMajor=29,developerId=826567491,localId=368333322,nativeModelWrites=0)
    def test_matching_live_build_identity_is_required_not_shared_tapir_version(self):
        p=self.identity();c=dict(commands={'GetAPARuntimeInfoV1':{}},_metadata=dict(binding=dict(apaRuntimeIdentity=p)))
        self.assertEqual(A.verify_native_runtime_identity(lambda *_:p,c),p)
        changed=dict(p,buildIdentity='c'*64)
        with self.assertRaisesRegex(ValueError,'CHANGED'):A.verify_native_runtime_identity(lambda *_:changed,c)
    def test_legacy_or_unpinned_runtime_cannot_enable_new_sdk_commands(self):
        for c in [dict(commands={}),dict(commands={'GetAPARuntimeInfoV1':{}})]:
            with self.assertRaisesRegex(ValueError,'NOT_EXPORTED'):A.verify_native_runtime_identity(lambda *_:self.identity(),c)

class BodylessStairScanTests(unittest.TestCase):
    def scan(self,member=True,parent_x=100):
        root='00000000-0000-4000-8000-000000000001';child='00000000-0000-4000-8000-000000000002'
        raw=dict(regenerated3D=True,coordinateSystem='ABSOLUTE_PROJECT_XYZ',nativeBodySlots=1,bodies=[dict(nativeBodyIndex=1)],deletedBodySlots=[],geometryScope='TEST_NATIVE_FILTER_SCOPE')
        normal=dict(elements=[dict(guid=child,type='Riser',nativeTypeId=48,bodies=[],relationships=dict(hostGuid=root)),dict(guid=root,type='Stair',nativeTypeId=47,bodies=[dict(vertices=[[parent_x,0,0],[parent_x+1,1,3]])])])
        def api(c,p):
            if c=='GetAllElements':return dict(elements=[dict(elementId=dict(guid=g)) for g in [child,root]])
            if c=='Get3DBoundingBoxes':return dict(boundingBoxes3D=[dict(boundingBox3D=dict(xMin=1e35,xMax=-1e35,yMin=1e35,yMax=-1e35,zMin=0,zMax=0)),dict(boundingBox3D=dict(xMin=parent_x,xMax=parent_x+1,yMin=0,yMax=1,zMin=0,zMax=3))])
            if c=='GetSubelementsOfHierarchicalElements':return dict(subelements=[dict(risers=[dict(elementId=dict(guid=child))] if member else [])])
            return raw
        with patch.object(G,'normalize_dump',return_value=normal):return A.RUN.scan_for_existing_geometry(api,0,0)
    def test_bodyless_child_needs_both_native_owner_and_specialized_membership(self):
        self.assertEqual(len(self.scan()['bodylessNativeStairChildren']),1)
        with self.assertRaisesRegex(ValueError,'membership mismatch'):self.scan(member=False)
    def test_bodyless_child_does_not_hide_actual_parent_collision(self):
        with self.assertRaisesRegex(ValueError,'SPATIAL_COLLISION'):self.scan(parent_x=0)

if __name__=='__main__':unittest.main()
