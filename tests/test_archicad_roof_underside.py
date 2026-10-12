import copy,math,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import archicad_native_operations as N
import test_archicad_functional_expansion as X
from test_archicad_functional_gaps import guid


class UndersideGeometryTests(unittest.TestCase):
    def fixture(self,slope=math.tan(.15)):
        roof=X.cube((10,8,.2),(40,40,6));roof.update(type='Roof',homeStory=1)
        wall=X.cube((.3,7.7,3),(44.85,40.15,3));wall.update(type='Wall',homeStory=1)
        for v in roof['bodies'][0]['vertices']:v[2]+=slope*(v[1]-40)
        for v in wall['bodies'][0]['vertices']:
            if v[2]>5.9:v[2]+=slope*(v[1]-40)
        return wall,roof,7.7*.3*math.sqrt(1+slope*slope)
    def test_measured_pitched_underside_contact_has_actual_face_area(self):
        w,r,area=self.fixture();proof=N.underside_contact_geometry(w,r,area)
        self.assertAlmostEqual(proof['sharedAreaSquareMeters'],area)
        self.assertTrue(proof['wallEntirelyBelowUnderside'])
    def test_positive_top_plane_contact_cannot_be_promoted_to_underside(self):
        w,r,area=self.fixture()
        for v in w['bodies'][0]['vertices']:
            if v[2]>5.9:v[2]+=.2
        self.assertAlmostEqual(sum(x['sharedAreaSquareMeters'] for x in N.C.G.shared_surfaces({'w':w,'r':r},{'w':'w','r':'r'})),area)
        with self.assertRaisesRegex(ValueError,'ABOVE_ROOF_UNDERSIDE'):N.underside_contact_geometry(w,r,area)
    def test_real_gap_is_not_accepted_as_contact(self):
        w,r,area=self.fixture()
        for v in w['bodies'][0]['vertices']:
            if v[2]>5.9:v[2]-=.01
        with self.assertRaisesRegex(ValueError,'CONTACT_AREA_MISMATCH'):N.underside_contact_geometry(w,r,area)
    def test_sloped_gap_uses_actual_wall_overlap_not_roof_minimum_z(self):
        w,r,area=self.fixture()
        for v in w['bodies'][0]['vertices']:
            if v[2]>5.9:v[2]=6.
        proof=N.wall_roof_underside_gap(w,r)
        self.assertAlmostEqual(proof['minimumVerticalGapMeters'],math.tan(.15)*.15,5)
        self.assertAlmostEqual(proof['maximumVerticalGapMeters'],math.tan(.15)*7.85,5)
    def test_gap_with_no_actual_roof_overlap_is_rejected(self):
        w,r,area=self.fixture()
        for v in w['bodies'][0]['vertices']:v[0]+=100
        with self.assertRaisesRegex(ValueError,'NO_ACTUAL_PROJECTED_FACE_OVERLAP'):N.wall_roof_underside_gap(w,r)
    def test_holes_remain_holes_even_when_seo_ignores_operator_holes(self):
        w,r,area=self.fixture();body=r['bodies'][0]
        face=next(f for f in body['faces'] if all(abs(v[2]-(6+math.tan(.15)*(v[1]-40)))<1e-6 for v in [body['vertices'][i] for i in f['contours'][0]]))
        # Use the actual wall top contour order rather than inventing a ring.
        wb=w['bodies'][0];wf=next(f for f in wb['faces'] if all(wb['vertices'][i][2]>5.9 for i in f['contours'][0]))
        ring=[]
        for i in wf['contours'][0]:ring.append(len(body['vertices']));body['vertices'].append(copy.deepcopy(wb['vertices'][i]))
        face['contours'].append(ring)
        with self.assertRaisesRegex(ValueError,'CONTACT_AREA_MISMATCH'):N.underside_contact_geometry(w,r,area)
    def test_changed_roof_plane_invalidates_source_binding(self):
        w,r,area=self.fixture();plane=N.roof_underside_plane(r)
        for v in r['bodies'][0]['vertices']:v[2]+=.01
        with self.assertRaisesRegex(ValueError,'PINNED_PLANE_CHANGED'):N.underside_contact_geometry(w,r,area,plane)
    def test_morph_cannot_replace_native_wall(self):
        w,r,area=self.fixture();w['type']='Morph'
        with self.assertRaisesRegex(ValueError,'NATIVE_WALL_ROOF'):N.underside_contact_geometry(w,r,area)
    def test_malformed_seo_relation_without_flag_fields_does_not_pass(self):
        api=lambda c,p:{'solidLinks':[{'solidLinksWithTheGivenTarget':[{'operatorId':{'guid':guid(2)},'operation':'SubtractionUpwards'}]}]}
        with self.assertRaisesRegex(ValueError,'SEO_LINK_NOT_PROVEN'):N.roof_bearing_seo_readback(api,guid(1),guid(2),{},1.)
    def test_flag_metadata_difference_does_not_replace_factual_geometry(self):
        w,r,area=self.fixture()
        def api(c,p):
            if c=='GetCollisions':return {'collisions':[]}
            return {'solidLinks':[{'solidLinksWithTheGivenTarget':[{'operatorId':{'guid':guid(2)},'operation':'SubtractionUpwards','linkFlags':{'inheritOperatorAttributes':False,'skipPolygonHoles':False}}]}]}
        def body(api,g):return {'native':w if g==guid(1) else r,'geometryHash':'changed'}
        with patch.object(N,'element_body',side_effect=body):proof=N.roof_bearing_seo_readback(api,guid(1),guid(2),{'geometryHash':'before'},area)
        self.assertEqual(proof['nativeFlagReadback'],'NOT_VERIFIED_REQUEST_READBACK_DIFFERENCE')
        self.assertAlmostEqual(proof['undersideContact']['sharedAreaSquareMeters'],area)
    def test_no_native_body_change_does_not_pass_an_accepted_seo_link(self):
        api=lambda c,p:{'solidLinks':[{'solidLinksWithTheGivenTarget':[{'operatorId':{'guid':guid(2)},'operation':'SubtractionUpwards','linkFlags':{'inheritOperatorAttributes':False,'skipPolygonHoles':True}}]}]}
        with patch.object(N,'element_body',return_value={'geometryHash':'same'}):
            with self.assertRaisesRegex(ValueError,'BODY_NOT_CHANGED'):N.roof_bearing_seo_readback(api,guid(1),guid(2),{'geometryHash':'same'},1.)


class AuthorizedSavedCopyTests(unittest.TestCase):
    def test_hash_drift_keeps_original_binding(self):
        before=(N.C.RUN.PORT,N.C.RUN.EXPECTED_PATH,N.C.RUN.EXPECTED_NAME)
        with patch.object(Path,'read_bytes',return_value=b'changed'):
            with self.assertRaisesRegex(ValueError,'HASH_MISMATCH'):
                N.C.RUN.bind_authorized_saved_copy(19724,r'Q:\fixture\approved-copy.pln','approved-copy','0'*64,'Explicit current user authorization')
        self.assertEqual(before,(N.C.RUN.PORT,N.C.RUN.EXPECTED_PATH,N.C.RUN.EXPECTED_NAME))
    def test_missing_authorization_or_wrong_name_cannot_override_target(self):
        for name,auth in [('approved-copy',''),('other','Explicit')]:
            with self.assertRaisesRegex(ValueError,'AUTHORIZATION_REQUIRED'):
                N.C.RUN.bind_authorized_saved_copy(19724,r'Q:\fixture\approved-copy.pln',name,'0'*64,auth)
    def test_source_drift_is_rejected_by_existing_writer(self):
        writer=N.C.RUN.SceneWriter(lambda c,p:{},':memory:')
        preflight={'integrationBindings':{'dependencies':{'sourceRoofTrimBinding':{'sourceBodies':[]}}}}
        with patch.object(N,'verify_roof_trim_source',side_effect=ValueError('ROOF_TRIM_SOURCE_INVALIDATED')):
            with self.assertRaisesRegex(ValueError,'SOURCE_INVALIDATED'):writer.verify_source_bindings(preflight)


if __name__=='__main__':unittest.main()
