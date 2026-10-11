"""Geometry negatives and ownership: synthetic evidence, no Archicad calls."""
import copy
from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import archicad_authored_geometry as G

BM='63DB2CE9-903D-45C0-B93C-B3C604C77394'
def element(guid,kind,floor,lo,hi,host=None):
    points=[] if lo is None else [[x,y,z] for x in (lo[0],hi[0]) for y in (lo[1],hi[1]) for z in (lo[2],hi[2])]
    return {'guid':guid,'type':kind,'homeStory':floor,'bodies':[{'vertices':points,'faces':[]}] if points else [],
        'relationships':{'hostGuid':host} if host else {},'materialBindings':{'buildingMaterial':{'guid':BM}}}

class GeometryTests(unittest.TestCase):
    def setUp(self):
        self.created={'lower':{'guid':'a','kind':'Slab','floorIndex':0},'upper':{'guid':'b','kind':'Slab','floorIndex':1},'column':{'guid':'c','kind':'Column','floorIndex':0}}
        polygon=[{'x':x,'y':y} for x,y in [(0,0),(2,0),(2,2),(0,2),(0,0)]]
        self.plan={'storyBindings':[{'nativeIndex':0,'level':0},{'nativeIndex':1,'level':3}],'slabBasicMaterialGuid':BM,
          'graph':{'operations':[{'id':sid,'command':'CreateSlabs','params':{'slabsData':[{'floorIndex':floor,'level':z,'thickness':.2,'polygonCoordinates':polygon}]}} for sid,floor,z in [('lower',0,0),('upper',1,3)]]+
            [{'id':'column','command':'CreateColumns','params':{'columnsData':[{'floorIndex':0,'coordinates':{'x':1,'y':1,'z':0},'width':.3,'depth':.3,'height':3,'buildingMaterialId':{'guid':BM}}]}}]}}
        self.model={'units':'m','coordinateSystem':'ABSOLUTE_PROJECT_XYZ','elements':[
            element('a','Slab',0,[0,0,-.2],[2,2,0]),element('b','Slab',1,[0,0,2.8],[2,2,3]),
            element('c','Column',0,None,None),element('d','ColumnSegment',0,[.85,.85,0],[1.15,1.15,3],host='c')]}
        self.children={'c':['d']}

    def audit(self):return G.analyze(self.model,self.plan,self.created,self.children,[],[])
    def test_xy_overlap_of_stacked_slabs_is_not_a_3d_collision(self):
        result=self.audit();self.assertIn(['a','b'],result['xyOverlapWithoutNativeVolumeCollision'])
        self.assertEqual(result['nativeVolumeIntersectionPairs'],[])
    def test_segment_body_covers_owned_column_and_preserves_primary_identity(self):
        result=self.audit();self.assertEqual(result['primaryCoverage'],3)
        self.assertEqual(result['bounds']['c']['max'],[1.15,1.15,3])
    def test_historical_wrong_upper_slab_z_is_rejected(self):
        for v in self.model['elements'][1]['bodies'][0]['vertices']:v[2]-=3
        with self.assertRaisesRegex(ValueError,'Z_EXTENT_MISMATCH'):self.audit()
    def test_wrong_segment_owner_is_rejected(self):
        self.model['elements'][3]['relationships']['hostGuid']='other'
        with self.assertRaisesRegex(ValueError,'SEGMENT_OWNER_MISMATCH'):self.audit()
    def test_missing_real_geometry_is_not_silently_accepted(self):
        self.model['elements'][3]['bodies']=[]
        with self.assertRaisesRegex(ValueError,'GEOMETRY_MISSING'):self.audit()
    def test_native_material_mismatch_is_rejected(self):
        self.model['elements'][3]['materialBindings']['buildingMaterial']['guid']='wrong'
        with self.assertRaisesRegex(ValueError,'MATERIAL_GUID_MISMATCH'):self.audit()

    def test_contact_uses_real_coplanar_faces_and_preserves_holes(self):
        face={'contours':[[0,1,2,3],[4,5,6,7]]}
        points=[[0,0,0],[2,0,0],[2,2,0],[0,2,0],[.5,.5,0],[1.5,.5,0],[1.5,1.5,0],[.5,1.5,0]]
        elements={g:{'bodies':[{'vertices':points,'faces':[face]}]} for g in ['a','b']}
        contacts=G.shared_surfaces(elements,{'a':'a','b':'b'})
        self.assertEqual(len(contacts),1);self.assertAlmostEqual(contacts[0]['sharedAreaSquareMeters'],3.)
