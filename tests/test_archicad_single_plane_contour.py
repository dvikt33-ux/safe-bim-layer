import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import archicad_native_operations as N
import test_archicad_wall_roof_assessment as W

class SinglePlaneContourTests(unittest.TestCase):
    def setUp(self):
        _,self.roof,_,self.details,_=W.RealJunctionAssessmentTests().fixture()
        plane=N.roof_underside_plane(self.roof)
        face=next(f for f in N.C.G.planar_faces(self.roof) if all(abs(sum(plane['normal'][k]*v[k] for k in range(3))-plane['distance'])<1e-6 for v in f['points']))
        points=[[p[0],p[1]] for p in face['points']];points.append(points[0])
        self.details['details']['polygonOutline']=[dict(x=p[0],y=p[1]) for p in points]
    def assess(self,proposal=None):return N.assess_single_plane_contour_candidate(self.roof,self.details,proposal)
    def proposal(self):
        r=self.assess();return {'outline':[[x+.1,y] for x,y in r['actualOutline']], 'holes':[],
            'designSourceUri':'https://example.org/approved-contour','baselineBodyHash':r['sourceBodyHash']}
    def test_ready_sdk_candidate_never_executes_unsupported_tapir(self):
        r=self.assess();self.assertFalse(r['executionAllowed']);self.assertEqual(r['nativeWrites'],0)
        self.assertIn('APIMemoMask_RoofEdgeTypes',r['memoMasks'])
    def test_reference_contour_can_match_upper_face_with_lower_offset(self):
        plane=N.roof_underside_plane(self.roof);faces=N.C.G.planar_faces(self.roof)
        face=max((f for f in faces if len(f['points'])>=4),key=lambda f:sum(plane['normal'][k]*f['points'][0][k] for k in range(3)))
        points=[dict(x=p[0],y=p[1]) for p in face['points']];points.append(points[0]);self.details['details']['polygonOutline']=points
        r=self.assess();self.assertGreater(max(r['memoMatchedActualPlaneDistances']),r['lowerPlane']['distance'])
    def test_exact_proposed_contour_is_only_offline_candidate(self):
        r=self.assess(self.proposal());self.assertEqual(r['status'],'OFFLINE_GEOMETRY_CANDIDATE_NOT_EXECUTABLE');self.assertFalse(r['executionAllowed'])
    def test_wrong_roof_class_rejected(self):
        self.details['details']['roofClass']='MultiPlane'
        with self.assertRaisesRegex(ValueError,'SINGLE_PLANE'):self.assess()
    def test_morph_not_fallback(self):
        self.roof['type']='Morph'
        with self.assertRaisesRegex(ValueError,'SINGLE_PLANE'):self.assess()
    def test_memo_actual_mismatch_rejected(self):
        self.details['details']['polygonOutline'][1]['x']+=2
        with self.assertRaisesRegex(ValueError,'BREP_MISMATCH'):self.assess()
    def test_holes_not_silently_removed(self):
        self.details['details']['holes']=[{'polygon':[]}]
        with self.assertRaisesRegex(ValueError,'HOLE_MEMO'):self.assess()
    def test_added_node_requires_separate_topology_contract(self):
        p=self.proposal();p['outline'].insert(1,[1,2])
        with self.assertRaisesRegex(ValueError,'TOPOLOGY'):self.assess(p)
    def test_unclosed_outline_rejected(self):
        p=self.proposal();p['outline'][-1][0]+=1
        with self.assertRaisesRegex(ValueError,'TOPOLOGY'):self.assess(p)
    def test_changed_holes_rejected(self):
        p=self.proposal();p['holes']=[[]]
        with self.assertRaisesRegex(ValueError,'HOLES'):self.assess(p)
    def test_stale_baseline_rejected(self):
        p=self.proposal();p['baselineBodyHash']='stale'
        with self.assertRaisesRegex(ValueError,'SOURCE_BOUND'):self.assess(p)
    def test_missing_design_source_rejected(self):
        p=self.proposal();p['designSourceUri']=''
        with self.assertRaisesRegex(ValueError,'SOURCE_BOUND'):self.assess(p)
    def test_nonfinite_coordinates_rejected(self):
        p=self.proposal();p['outline'][1][0]=float('nan')
        with self.assertRaisesRegex(ValueError,'TOPOLOGY'):self.assess(p)

if __name__=='__main__':unittest.main()
