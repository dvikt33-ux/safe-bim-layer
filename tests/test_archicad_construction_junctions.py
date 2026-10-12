import copy,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import archicad_details_context as D
from test_archicad_functional_gaps import guid
from test_archicad_functional_expansion import cube


class JunctionCoverageTests(unittest.TestCase):
    def fixture(self,offset=(0,0,1)):
        rows=[cube((1,1,1)),cube((1,1,1),offset=offset)]
        for i,e in enumerate(rows):
            e['guid']=guid(i+1)
            for face in e['bodies'][0]['faces']:face['contours']=[face['vertices']]+face.get('holes',[])
        context={'units':'m','coordinateSystem':'ABSOLUTE_PROJECT_XYZ','elements':{
            'wall':{'guid':guid(1),'kind':'Wall','floorIndex':0,'bounds':[[[0,1],[0,1],[0,1]]],'materialBindings':{}},
            'floor':{'guid':guid(2),'kind':'Slab','floorIndex':0,'bounds':[[[offset[k],offset[k]+1] for k in range(3)]],'materialBindings':{}}}}
        return context,{'units':'m','coordinateSystem':'ABSOLUTE_PROJECT_XYZ','elements':rows}
    def evaluate(self,offset=(0,0,1),collisions=()):
        c,n=self.fixture(offset);return D.native_junction_coverage(c,n,D.DetailsContext(ROOT),collisions)
    def junction(self,r):return next(f for f in r['families'] if f['family']=='wall_floor')['junctions'][0]
    def test_face_contact_has_actual_area_and_no_engineering_approval(self):
        j=self.junction(self.evaluate());self.assertAlmostEqual(j['sharedAreaSquareMeters'],1)
        self.assertEqual(j['physicalRelation'],'SURFACE_CONTACT');self.assertFalse(j['nativeVolumeIntersection'])
        self.assertEqual(j['engineeringAcceptance'],'NOT_VERIFIED')
    def test_native_overlap_is_separate_from_shared_surface(self):
        j=self.junction(self.evaluate((.5,.5,.5),[(guid(1),guid(2))]))
        self.assertTrue(j['nativeVolumeIntersection']);self.assertEqual(j['physicalRelation'],'VOLUME_INTERSECTION')
        self.assertEqual(j['sharedAreaSquareMeters'],0)
    def test_only_edge_touch_is_not_bearing_area(self):
        j=self.junction(self.evaluate((1,0,1)));self.assertEqual(j['sharedAreaSquareMeters'],0)
        self.assertEqual(j['physicalRelation'],'NO_SHARED_SURFACE')
    def test_hole_is_not_filled_by_contact_analysis(self):
        c,n=self.fixture();body=n['elements'][0]['bodies'][0]
        face=next(f for f in body['faces'] if all(body['vertices'][i][2]==1 for i in f['vertices']))
        index=len(body['vertices']);body['vertices'] += [[.25,.25,1],[.75,.25,1],[.75,.75,1],[.25,.75,1]]
        face['contours'].append(list(range(index,index+4)))
        j=self.junction(D.native_junction_coverage(c,n,D.DetailsContext(ROOT)))
        self.assertAlmostEqual(j['sharedAreaSquareMeters'],.75)
    def test_roof_gap_remains_required_interface(self):
        c,n=self.fixture((0,0,1.5));c['elements']['floor']['kind']='Roof'
        r=D.native_junction_coverage(c,n,D.DetailsContext(ROOT));j=next(f for f in r['families'] if f['family']=='wall_roof')['junctions'][0]
        self.assertEqual(j['physicalRelation'],'NO_SHARED_SURFACE')
    def test_cladding_absent_is_not_pass(self):
        r=self.evaluate();f=next(f for f in r['families'] if f['family']=='cladding_structure')
        self.assertEqual(f['status'],'NOT_PRESENT_OR_NO_BOUND_INTERFACE');self.assertEqual(f['junctions'],[])
    def test_full_source_assembly_gates_preserved(self):
        r=self.evaluate();self.assertEqual(r['contextDetailCount'],73);self.assertEqual(r['sourceDetailCount'],1142)
        self.assertEqual(r['sourceApprovedFullAssemblyCount'],0)
        self.assertEqual(r['armopoyasAndFasteners']['status'],'NOT_VERIFIED')
    def test_nonplanar_face_is_explicitly_unverified(self):
        c,n=self.fixture();n['elements'][0]['bodies'][0]['vertices'][0][2]+=.1
        j=self.junction(D.native_junction_coverage(c,n,D.DetailsContext(ROOT)))
        self.assertEqual(j['physicalRelation'],'NOT_VERIFIED');self.assertIn('NONPLANAR',j['contactAnalysisLimitation'])


if __name__=='__main__':unittest.main()
