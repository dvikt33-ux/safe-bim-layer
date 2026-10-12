import copy,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import archicad_functional_expansion as X
import archicad_connected_ifc as I
import archicad_details_context as D
from test_archicad_functional_gaps import native_fixture,guid
C=X.C;M=X.M


def cube(size=(2.,3.,4.),offset=(0.,0.,0.)):
    raw=C.explicit_box_body(dict(zip(('x','y','z'),size)))
    return {'guid':guid(2),'bodies':[{'closed':True,'curved':False,
        'vertices':[[v[k]+offset[i] for i,k in enumerate(('x','y','z'))] for v in raw['vertices']],
        'faces':[{'contours':[p['vertexIds']],'vertices':p['vertexIds'],'holes':[]} for p in raw['polygons']]}]}


class QuantitiesTests(unittest.TestCase):
    def test_resultant_brep_box_measures_closed_faces(self):
        r=I.native_body_quantities(cube());self.assertEqual(r['status'],'NATIVE_PLANAR_BREP_QUANTITIES')
        self.assertAlmostEqual(r['volumeCubicMeters'],24);self.assertAlmostEqual(r['surfaceAreaSquareMeters'],52)
    def test_volume_independent_of_world_translation(self):
        r=I.native_body_quantities(cube(offset=(70.,60.,6.)));self.assertAlmostEqual(r['volumeCubicMeters'],24)
    def test_missing_face_not_promoted_to_volume(self):
        e=cube();e['bodies'][0]['faces'].pop();self.assertEqual(I.native_body_quantities(e)['status'],'NATIVE_QUANTITIES_NOT_VERIFIED')
    def test_inconsistent_orientation_rejected(self):
        e=cube();e['bodies'][0]['faces'][0]['contours'][0].reverse()
        self.assertIn('ORIENTATION',I.native_body_quantities(e)['reason'])
    def test_curved_body_not_silently_approximated(self):
        e=cube();e['bodies'][0]['curved']=True;self.assertIn('CURVED',I.native_body_quantities(e)['reason'])
    def test_empty_body_has_explicit_status(self):self.assertEqual(I.native_body_quantities({})['status'],'NATIVE_BODY_NOT_AVAILABLE')
    def test_ifc_actual_classification_material_and_source_quantity(self):
        import ifcopenshell
        f=ifcopenshell.file(schema='IFC4');new=ifcopenshell.guid.new
        wall=f.create_entity('IfcWall',GlobalId=new(),Name='test wall')
        material=f.create_entity('IfcMaterial',Name='test material')
        f.create_entity('IfcRelAssociatesMaterial',GlobalId=new(),RelatedObjects=[wall],RelatingMaterial=material)
        classification=f.create_entity('IfcClassification',Name='test classifier')
        reference=f.create_entity('IfcClassificationReference',Identification='real-test-code',Name='wall code',ReferencedSource=classification)
        f.create_entity('IfcRelAssociatesClassification',GlobalId=new(),RelatedObjects=[wall],RelatingClassification=reference)
        quantity=f.create_entity('IfcQuantityVolume',Name='NetVolume',VolumeValue=7.)
        qset=f.create_entity('IfcElementQuantity',GlobalId=new(),Name='Qto_WallBaseQuantities',Quantities=[quantity])
        f.create_entity('IfcRelDefinesByProperties',GlobalId=new(),RelatedObjects=[wall],RelatingPropertyDefinition=qset)
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'actual.ifc';f.write(str(path));r=I.inspect_quantified_exchange(path)
        e=r['elements'][0];self.assertEqual(e['materials'][0]['name'],'test material')
        self.assertEqual(e['classifications'][0]['identifier'],'real-test-code')
        self.assertEqual(e['sourceQuantities']['Qto_WallBaseQuantities']['NetVolume'],7.)
        self.assertEqual(r['semanticCompatibility'],'NOT_VERIFIED');self.assertNotIn('volumeCubicMeters',e['geometry'])
    def test_ifc_missing_semantics_are_empty(self):
        import ifcopenshell
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'empty.ifc';ifcopenshell.file(schema='IFC4').write(str(path));r=I.inspect_quantified_exchange(path)
        self.assertEqual(r['elements'],[]);self.assertEqual(r['portConnections'],[]);self.assertEqual(r['quantityMatchCount'],0)
    def test_ifc_native_units_gate_precedes_file_read(self):
        with self.assertRaisesRegex(ValueError,'WORLD_METRES'):I.inspect_quantified_exchange('missing',{'units':'mm'})
    def test_ifc_duplicate_guid_mapping_rejected(self):
        import ifcopenshell
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'empty.ifc';ifcopenshell.file(schema='IFC4').write(str(path))
            with self.assertRaisesRegex(ValueError,'NOT_UNIQUE'):I.inspect_quantified_exchange(path,native_ifc_map={guid(1):'same',guid(2):'same'})


class ExpandedMEPTests(unittest.TestCase):
    def read(self,replies):return M.read_network(lambda c,p:copy.deepcopy(replies[c]),[guid(10),guid(11)],guid(1))
    def test_disconnected_native_components_share_system_attribute(self):
        r,_=native_fixture();system=r['GetMEPDistributionSystems']['distributionSystems'][0]
        a,b=system['elements'];system['elements']=[a]
        r['GetMEPDistributionSystems']['distributionSystems'].append({**system,'elements':[b]})
        self.assertEqual(self.read(r)['distributionComponentCount'],2)
    def test_duplicate_native_membership_rejected(self):
        r,_=native_fixture();r['GetMEPDistributionSystems']['distributionSystems']*=2
        with self.assertRaisesRegex(ValueError,'DUPLICATED'):self.read(r)
    def test_linked_ports_at_different_positions_rejected(self):
        r,_=native_fixture();r['GetMEPPorts']['elementPorts'][1]['ports'][0]['position']['x']=1.1
        with self.assertRaisesRegex(ValueError,'POSITION_MISMATCH'):self.read(r)
    def test_trimmed_native_duct_still_maps_to_logical_route(self):
        r,_=native_fixture();r['GetMEPPorts']['elementPorts'][0]['ports'][0]['position']['x']=.2
        self.assertEqual(self.read(r)['routePhysicalMembers'][guid(10)],[guid(20)])
    def test_overshooting_duct_not_falsely_owned(self):
        r,_=native_fixture();r['GetMEPPorts']['elementPorts'][0]['ports'][0]['position']['x']=-.2
        self.assertEqual(self.read(r)['routePhysicalMembers'][guid(10)],[])
    def test_gdl_read_unknown_mep_type_blocked_before_query(self):
        calls=[]
        with patch.object(C.RUN,'requested_details',return_value={'type':'Unknown'}):
            with self.assertRaisesRegex(ValueError,'DEDICATED_MEP'):X.guarded_parameter_read(lambda c,p:calls.append(c),[guid(1)])
        self.assertEqual(calls,[])
    def test_gdl_known_object_can_use_retained_api(self):
        with patch.object(C.RUN,'requested_details',return_value={'type':'Object'}):
            self.assertEqual(X.guarded_parameter_read(lambda c,p:{'command':c},[guid(1)])['command'],'GetGDLParametersOfElements')
    def test_component_creation_is_opt_in(self):
        self.assertNotIn('CreateMEPElements',C.RUN.SceneWriter(None,'unused').allowed_writes)
        self.assertIn('CreateMEPElements',C.RUN.SceneWriter(None,'unused',adapters=C.adapters(['mep-component'])).allowed_writes)


class SourceSectionTests(unittest.TestCase):
    def fixture(self):
        # Explicit synthetic planar roof: real source dimensions, synthetic model.
        e=cube((10.,8.,.2),(40.,40.,6.));e.update(homeStory={'index':1},materialBindings={'buildingMaterialGuid':guid(3)})
        for p in e['bodies'][0]['vertices']:p[2]+=.15*(p[1]-40.)
        e['guid']=guid(2)
        host={'guid':guid(2),'kind':'Roof','floorIndex':1,'materialBindings':e['materialBindings'],'bounds':[[[40,50],[40,48],[6,7.4]]]}
        context={'units':'m','coordinateSystem':'ABSOLUTE_PROJECT_XYZ','elements':{'roof':host}}
        source={'inventory':[guid(2)],'preflight':{'binding':{},'storyBindings':[], 'schemaVersion':'1.5.10',
            'schemaSha256':'source','sourcePlanHash':'source'}}
        selection={'kind':'BuildingMaterial','name':'project material','expectedGuid':guid(3)}
        return source,context,{'elements':[e]},selection
    def part(self):
        s,c,n,m=self.fixture();return D.prepare_source_section(ROOT,s,c,n,guid(2),'c4',m)
    def test_actual_source_joins_to_native_graph_without_invented_dimensions(self):
        r=self.part();b=r['binding'];self.assertEqual(b['sourceSectionMeters'],{'width':.15,'height':.025})
        self.assertEqual(b['modelDerivedLengthMeters'],10);self.assertEqual(len(b['missingAssemblyDimensionEntities']),8)
        self.assertFalse(b['assemblyWriteAllowed']);self.assertEqual(r['nativeWrites'],0)
        self.assertEqual(r['plan']['graph']['operations'][0]['command'],'CreateMorphs')
    def test_unknown_entity_not_turned_into_geometry(self):
        s,c,n,m=self.fixture()
        with self.assertRaisesRegex(ValueError,'CROSS_SECTION'):D.prepare_source_section(ROOT,s,c,n,guid(2),'c1',m)
    def test_counterbatten_requires_actual_rafter_orientation(self):
        s,c,n,m=self.fixture()
        with self.assertRaisesRegex(ValueError,'ORIENTATION'):D.prepare_source_section(ROOT,s,c,n,guid(2),'c5',m)
    def test_source_part_wrong_host_rejected(self):
        s,c,n,m=self.fixture();c['elements']['roof']['kind']='Wall'
        with self.assertRaisesRegex(ValueError,'ROOF'):D.prepare_source_section(ROOT,s,c,n,guid(2),'c4',m)
    def test_source_part_before_write_rejects_shifted_placement(self):
        r=self.part();params=copy.deepcopy(r['plan']['graph']['operations'][0]['params']);params['morphsData'][0]['basePoint']['x']+=1
        with patch.object(D,'verify_source_section_binding',return_value={}):
            with self.assertRaisesRegex(ValueError,'PLACEMENT'):C.NativeAdapter('CreateMorphs').before_write(None,params,r['plan'])
    def test_source_part_before_write_rejects_changed_source_section(self):
        r=self.part();r['binding']['sourceSectionMeters']['height']=.1
        with patch.object(D,'verify_source_section_binding',return_value={}):
            with self.assertRaisesRegex(ValueError,'DIMENSION'):C.NativeAdapter('CreateMorphs').before_write(None,r['plan']['graph']['operations'][0]['params'],r['plan'])
    def test_source_part_host_invalidates_geometry_before_material_read(self):
        r=self.part()
        with patch('archicad_native_operations.element_body',return_value={'native':cube()}):
            with self.assertRaisesRegex(ValueError,'GEOMETRY_INVALIDATED'):D.verify_source_section_binding(None,r['binding'])
    def test_junction_matrix_preserves_existing_tasks_and_source_gates(self):
        _,context,_,_=self.fixture();context['elements']['wall']={'guid':guid(5),'kind':'Wall','floorIndex':1,'bounds':[[[0,1],[0,1],[0,1]]],'materialBindings':{}}
        evaluated=D.DetailsContext(ROOT).evaluate(context);r=D.required_junction_matrix(context,evaluated)
        self.assertEqual(r['existingTasks'],['APA-P70.A04.S01','APA-P70.A04.S02','APA-P70.A04.S03'])
        roof=next(x for x in r['families'] if x['family']=='wall_roof');self.assertTrue(roof['sourceCandidates'])
        self.assertTrue(all(x['sourceBlockers'] for x in roof['sourceCandidates']))


if __name__=='__main__':unittest.main()
