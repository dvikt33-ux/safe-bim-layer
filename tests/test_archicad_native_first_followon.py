import copy,sys,unittest
from unittest.mock import patch
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import archicad_native_mep_network as M
import archicad_native_beam_details as B
import test_archicad_construction_junctions as J
import test_archicad_functional_expansion as X
import archicad_functional_expansion as E
import archicad_connected_ifc as I
import archicad_native_operations as N
from test_archicad_functional_gaps import guid


class CircularReferenceTests(unittest.TestCase):
    def tables(self):return {'tables':[{'guid':guid(1),'rows':[{'referenceId':200,'diameter':.2,'description':'source row'}]}]}
    def select(self,tables=None):return M.circular_reference_selection(lambda c,p:copy.deepcopy(tables or self.tables()),'Ventilation',.2,200)
    def data(self):return {'domain':'Ventilation','crossSectionShape':'Circular','crossSectionWidth':.2,'crossSectionHeight':.2,'crossSectionReferenceId':200}
    def test_exact_installed_row_without_write(self):
        calls=[]
        def api(c,p):calls.append((c,p));return self.tables()
        s=M.circular_reference_selection(api,'Ventilation',.2,200)
        self.assertEqual(s['referenceId'],200);self.assertEqual(calls,[('GetMEPPreferenceTables',{'domain':'Ventilation'})])
    def test_duplicate_reference_in_two_tables_is_ambiguous(self):
        t=self.tables();t['tables'].append({'guid':guid(2),'rows':[{'referenceId':200,'diameter':.2}]})
        with self.assertRaisesRegex(ValueError,'NOT_UNIQUE'):self.select(t)
    def test_requested_width_does_not_override_wrong_preference(self):
        t=self.tables();t['tables'][0]['rows'][0]['diameter']=.8
        with self.assertRaisesRegex(ValueError,'DIAMETER_MISMATCH'):self.select(t)
    def test_table_drift_invalidates_bound_operation(self):
        s=self.select();t=self.tables();t['tables'][0]['rows'][0]['description']='changed'
        with self.assertRaisesRegex(ValueError,'INVALIDATED'):M.verify_circular_reference_binding(lambda c,p:t,self.data(),s)
    def test_rectangle_wrong_reference_and_bool_cannot_pass_binding(self):
        for key,value in [('crossSectionShape','Rectangular'),('crossSectionReferenceId',800),('crossSectionReferenceId',True),('crossSectionHeight',.15)]:
            d=self.data();d[key]=value
            with self.assertRaisesRegex(ValueError,'PARAMETERS_MISMATCH'):M.verify_circular_reference_binding(lambda c,p:self.tables(),d,self.select())
    def test_unbound_circular_create_is_rejected_before_transport(self):
        with self.assertRaisesRegex(ValueError,'EXPLICIT_REFERENCE_BINDING'):M.C.NativeAdapter('CreateMEPRoutingElements').before_write(None,{'routingElementsData':[self.data()]},{})


class NativeBeamTests(unittest.TestCase):
    def test_batten_recipe_selects_actual_beam_and_independent_width_height(self):
        s,c,n,m=X.SourceSectionTests().fixture()
        part=B.D.prepare_source_section(ROOT,s,c,n,guid(2),'c4',m)
        r=B.prepare_beam(s,part);op=r['plan']['graph']['operations'][0]
        self.assertEqual(op['command'],'CreateBeams');data=op['params']['beamsData'][0]
        self.assertEqual((data['width'],data['height']),(.15,.025));self.assertFalse(data['isWidthAndHeightLinked'])
        self.assertEqual(data['anchorPoint'],'Center');self.assertAlmostEqual(data['profileAngle'],-__import__('math').atan(.15))
        self.assertEqual(data['endCoordinate']['x']-data['begCoordinate']['x'],10.)
    def test_counterbatten_keeps_measured_slope_and_source_dimensions(self):
        s,c,n=J.CounterbattenTests().fixture()
        part=B.D.prepare_counterbatten_junction(ROOT,s,c,n,guid(4),guid(5))
        r=B.prepare_beam(s,part,-2.5,'Measured roof quarter X');data=r['binding']['expectedNativeBeamParameters']
        self.assertEqual((data['width'],data['height']),(.05,.05));self.assertTrue(data['isSlanted'])
        self.assertAlmostEqual(data['slantAngle'],__import__('math').atan(.15));self.assertAlmostEqual(data['begCoordinate']['x'],42.5)
    def test_translation_needs_model_authority(self):
        with self.assertRaisesRegex(ValueError,'AUTHORITY_REQUIRED'):B.prepare_beam({},X.SourceSectionTests().part(),1.)
    def test_morph_missing_adapter_is_not_an_exemption(self):
        with self.assertRaisesRegex(ValueError,'NATIVE_TOOL_EVIDENCE'):B.require_morph_last_resort({})
    def test_rectangular_source_section_cannot_become_morph_despite_claimed_exemption(self):
        with self.assertRaisesRegex(ValueError,'NATIVE_BEAM_REQUIRED'):B.require_morph_last_resort({'sourceDetailBinding':{'entityId':'c5'}})
    def test_beam_hierarchy_preserves_parent_and_detects_duplicate_child(self):
        created={'beam':{'guid':guid(1),'kind':'Beam'}}
        r=M.C.A.assembly_subelements(lambda c,p:{'subelements':[{'beamSegments':[{'elementId':{'guid':guid(2)}}]}]},created,'Beam')
        self.assertEqual(r,{guid(1):[guid(2)]})
        with self.assertRaisesRegex(ValueError,'DUPLICATED'):M.C.A.assembly_subelements(lambda c,p:{'subelements':[{'beamSegments':[{'elementId':{'guid':guid(1)}}]}]},created,'Beam')
    def test_classified_morph_is_not_native_beam(self):
        with self.assertRaisesRegex(ValueError,'NATIVE_TYPE'):M.C.NativeAdapter('CreateBeams').verify(None,guid(1),{'beamsData':[{}]},
            {'type':'Morph','floorIndex':1,'details':{'classification':'Beam'}},1,3.)
    def test_section_link_default_cannot_override_rectangular_dimensions(self):
        r=B.prepare_native_batten(ROOT,*X.SourceSectionTests().fixture()[:3],guid(2),X.SourceSectionTests().fixture()[3])
        op=r['plan']['graph']['operations'][0];op['params']['beamsData'][0]['isWidthAndHeightLinked']=True
        with self.assertRaisesRegex(ValueError,'EXPLICIT_BASIC'):M.C.NativeAdapter('CreateBeams').resolve(op,{},r['plan'])
    def test_native_owned_segment_quantities_are_attributed_to_beam_root(self):
        parent={'guid':guid(1),'type':'Beam','homeStory':1,'bodies':[]}
        child=X.cube((10,.15,.025));child.update(guid=guid(2),type='BeamSegment',homeStory=1,relationships={'hostGuid':guid(1)})
        r=I.native_element_quantities({guid(1):parent,guid(2):child},guid(1))
        self.assertEqual(r['status'],'NATIVE_PLANAR_BREP_QUANTITIES');self.assertAlmostEqual(r['volumeCubicMeters'],.0375)
        self.assertEqual(r['sourceSegmentGuids'],[guid(2)])
    def test_foreign_segment_type_does_not_supply_beam_quantities(self):
        p={'guid':guid(1),'type':'Beam','homeStory':1,'bodies':[]}
        child=X.cube();child.update(guid=guid(2),type='ColumnSegment',homeStory=1,relationships={'hostGuid':guid(1)})
        self.assertEqual(I.native_element_quantities({guid(1):p,guid(2):child},guid(1))['status'],'NATIVE_QUANTITIES_NOT_VERIFIED')
    def test_auto_connected_terminal_preserves_single_context_identity(self):
        context={'elements':{'terminal':{'guid':guid(1),'kind':'MEPTerminal','sourceRole':'supply'}},'inventory':[guid(1)]}
        native={'elements':[dict(X.cube(),guid=guid(1))]}
        network={'routes':[],'routePhysicalMembers':{},'physicalGuids':[guid(1)]}
        with patch.object(E,'preserve_baseline',return_value={'native':native,'inventory':[guid(1)]}),patch.object(E,'discover_network',return_value=network),patch.object(M.C.RUN,'requested_details',return_value={'floorIndex':0}):
            result,_,_=E.expanded_context(None,{'shared':{'context':context}})
        self.assertEqual(list(result['elements']),['terminal']);self.assertEqual(result['elements']['terminal']['sourceRole'],'supply')
    def test_owned_beam_children_are_included_in_whole_inventory_gate(self):
        c={'inventory':[guid(1),guid(2)],'beamSegments':{guid(1):[guid(2)]}}
        self.assertEqual(M.C.verify_inventory(c,{'inventory':[]},{'beam':{'guid':guid(1)}},[]),[guid(1),guid(2)])
    def test_beam_segment_contact_is_attributed_to_native_parent(self):
        c,n=J.JunctionCoverageTests().fixture();c['elements']['wall']['kind']='Beam';c['elements']['floor']['kind']='Roof'
        child=copy.deepcopy(n['elements'][0]);child['guid']=guid(3);n['elements'][0]['bodies']=[]
        n['elements'].append(child);c['beamSegments']={guid(1):[guid(3)]}
        r=B.D.native_junction_coverage(c,n,B.D.DetailsContext(ROOT))
        j=next(f for f in r['families'] if f['family']=='roof_members_and_abutments')['junctions'][0]
        self.assertEqual(j['guids'],[guid(1),guid(2)]);self.assertAlmostEqual(j['sharedAreaSquareMeters'],1.)
    def test_native_batten_can_supply_the_next_native_counterbatten_recipe(self):
        s,c,n=J.CounterbattenTests().fixture();batten=next(e for e in n['elements'] if e['guid']==guid(4))
        child=copy.deepcopy(batten);child.update(guid=guid(6),type='BeamSegment',relationships={'hostGuid':guid(4)})
        batten.update(type='Beam',bodies=[]);n['elements'].append(child);c['elements']['batten']['kind']='Beam'
        r=B.prepare_native_counterbatten(ROOT,s,c,n,guid(4),guid(5))
        self.assertEqual(r['plan']['graph']['operations'][0]['command'],'CreateBeams')
        self.assertIn(guid(6),[d['guid'] for d in r['binding']['nativeDependencyBodies']])


class NativeRoofTrimTests(unittest.TestCase):
    def rows(self):return {'elementTrims':[{'error':{'code':-2130313103,'message':'Failed to read the elements this element trims.'}},
        {'trimmedBy':[],'trims':[{'elementId':{'guid':guid(1)}}]}]}
    def test_operator_relation_does_not_promote_failed_reverse_metadata(self):
        wall=dict(X.cube((1,1,1)),type='Wall');roof=dict(X.cube((1,1,1),(0,0,1)),type='Roof')
        def body(api,g):return {'native':wall if g==guid(1) else roof,'geometryHash':'new'}
        def api(c,p):return self.rows() if c=='GetElementTrims' else {'collisions':[]}
        with patch.object(N,'element_body',side_effect=body):r=N.roof_trim_readback(api,guid(1),guid(2),{'geometryHash':'old'},1.)
        self.assertEqual(r['sharedAreaSquareMeters'],1.);self.assertEqual(r['reciprocalTrimMetadata'],'NOT_VERIFIED_INSTALLED_PROVIDER_TARGET_ROW_ERROR')
    def test_unrelated_target_error_is_not_silently_treated_as_known_gap(self):
        rows=self.rows();rows['elementTrims'][0]['error']['message']='Unknown deleted target'
        with self.assertRaisesRegex(ValueError,'UNEXPLAINED'):N.roof_trim_readback(lambda c,p:rows,guid(1),guid(2),{},1.)
    def test_missing_operator_relation_cannot_pass_from_positive_area(self):
        rows=self.rows();rows['elementTrims'][1]['trims']=[]
        with self.assertRaisesRegex(ValueError,'OPERATOR_RELATION'):N.roof_trim_readback(lambda c,p:rows,guid(1),guid(2),{},1.)


if __name__=='__main__':unittest.main()
