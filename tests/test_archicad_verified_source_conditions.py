import copy,math,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import archicad_normative_bindings as N
import archicad_native_operations as G
import archicad_project_accelerator as A
import test_archicad_wall_roof_assessment as W
from test_archicad_semantic_brief import valid
from test_archicad_project_library_pack import specimen

class VerifiedSourceConditionsTests(unittest.TestCase):
    def setUp(self):
        w,r,_,self.rd,_=W.RealJunctionAssessmentTests().fixture();self.w=w;self.r=r
        self.native={'units':'m','coordinateSystem':'ABSOLUTE_PROJECT_XYZ','elements':[w,r],'materials':[]}
        self.context={'units':'m','coordinateSystem':'ABSOLUTE_PROJECT_XYZ','elements':{'wall':{'guid':w['guid']},'roof':{'guid':r['guid']}},
            'nativeGeometrySignatures':G.C.retained_geometry_signatures(self.native,[w['guid'],r['guid']])}
        self.brief=valid();self.pack=A.compile_project_library_pack(self.brief,specimen())
        self.targets=[{'id':'east','family':'wall_roof','guids':[w['guid'],r['guid']]}]
        self.req={'jurisdiction':{'country':'RU','evidenceUri':'user:confirmed-project'},'projectFacts':{},'cseFacts':{}}
    def compiled(self):return N.compile_normative_pack(self.brief,self.pack,self.context,self.req,self.targets)
    def evaluate(self):return A.evaluate_project_native_requirements(self.compiled(),self.context,self.native,self.req,self.targets)
    def row(self,key):return next(r for r in self.evaluate()['checks'] if r['ruleId']==key)
    def source_fact(self,key,value):self.req['projectFacts'][key]={'value':value,'evidenceUri':'https://example.org/design'}
    def roof_system(self,system):
        self.source_fact('roofWorkType','new');self.req['cseFacts']['east']={'roofSystem':system,'sourceEvidenceUri':'https://example.org/cse',
            'nativeContextSignature':N.native_binding_signature(self.context,self.targets[0]['guids'])}
    def thermal_facts(self):
        for key,v in dict(buildingWorkType='new',buildingUse='residential',totalBuildingAreaM2=100,maintainedTemperatureHumidity=True,architecturalHistoricSignificance=False).items():self.source_fact(key,v)
        for key in self.evaluate()['sourceConditions']['sources']['thermalScope']['exclusions']:self.source_fact('thermalExclusion:'+key,False)
    def test_reference_instruction_checks_actual_graph_without_compliance(self):
        result=self.evaluate();self.assertEqual(self.row('sp17-amendment5-thermal-reference')['status'],'PASS_DOCUMENTED')
        self.assertEqual(self.row('sp17-roof-scope')['status'],'NOT_VERIFIED')
        self.assertFalse(any(r['engineeringApproved'] for r in result['checks']))
        self.assertEqual(result['nativeWriteCalls'],0);self.assertTrue(result['dependencyGraph']['acyclic'])
    def test_stale_thermal_reference_is_document_failure(self):
        self.req['requestedEditions']={'thermal':'СП 50.13330.2012'}
        self.assertEqual(self.row('sp17-amendment5-thermal-reference')['status'],'FAIL_DOCUMENT_REFERENCE')
    def test_wrong_roof_edition_never_promotes_source_instruction(self):
        self.req['requestedEditions']={'roof':'СП 17.13330.2011'}
        self.assertEqual(self.row('sp17-amendment5-thermal-reference')['status'],'NOT_VERIFIED')
    def test_source_bound_known_roof_technology_only_verifies_scope(self):
        self.roof_system('metal_profile_sheet');self.assertEqual(self.row('sp17-roof-scope')['status'],'APPLICABLE')
        self.assertFalse(self.row('sp17-roof-scope')['engineeringApproved'])
    def test_concrete_material_does_not_prove_trough_panels(self):self.assertEqual(self.row('sp17-roof-scope')['status'],'NOT_VERIFIED')
    def test_single_plane_or_unknown_name_does_not_exclude_roof_norm(self):
        for value in ('SinglePlane','unknown'):
            self.roof_system(value);self.assertEqual(self.row('sp17-roof-scope')['status'],'NOT_VERIFIED')
    def test_stale_cse_binding_does_not_establish_scope(self):
        self.roof_system('metal_profile_sheet');self.req['cseFacts']['east']['nativeContextSignature']='stale'
        self.assertEqual(self.row('sp17-roof-scope')['status'],'NOT_VERIFIED')
    def test_actual_native_slope_has_no_invented_limit(self):
        row=next(iter(self.evaluate()['nativeMetrics'].values()));self.assertEqual(row['status'],'VERIFIED_NATIVE_GEOMETRY')
        self.assertIsNone(row['normativeSlopeThreshold']);self.assertEqual(row['normativeSlopeResult'],'NOT_VERIFIED')
    def test_brep_edit_even_same_metadata_invalidates_input(self):
        self.r['bodies'][0]['vertices'][0][0]+=.1
        with self.assertRaisesRegex(ValueError,'BREP_INVALIDATED'):self.evaluate()
    def test_context_edit_cannot_reuse_pack(self):
        p=self.compiled();self.context['elements']['wall']['material']='changed'
        with self.assertRaisesRegex(ValueError,'INPUT_INVALIDATED'):N.evaluate_native_source_conditions(p,self.context,self.native,self.req,self.targets)
    def test_missing_scope_inputs_not_guessed_from_slabs_or_brief(self):self.assertEqual(self.row('sp50-envelope-scope')['status'],'NOT_VERIFIED')
    def test_thermal_scope_area_boundary_is_strict(self):
        self.thermal_facts();self.source_fact('totalBuildingAreaM2',50)
        self.assertEqual(self.row('sp50-envelope-scope')['status'],'NOT_APPLICABLE')
        self.source_fact('totalBuildingAreaM2',50.01);self.assertEqual(self.row('sp50-envelope-scope')['status'],'APPLICABLE')
    def test_boolean_area_not_numeric_evidence(self):
        self.thermal_facts();self.source_fact('totalBuildingAreaM2',True)
        self.assertEqual(self.row('sp50-envelope-scope')['status'],'NOT_VERIFIED')
    def test_each_thermal_exclusion_prevents_false_applicability(self):
        self.thermal_facts()
        for key in self.evaluate()['sourceConditions']['sources']['thermalScope']['exclusions']:
            self.source_fact('thermalExclusion:'+key,True);self.assertEqual(self.row('sp50-envelope-scope')['status'],'NOT_APPLICABLE');self.source_fact('thermalExclusion:'+key,False)
    def test_unknown_exclusion_stays_not_verified(self):
        self.thermal_facts();self.req['projectFacts'].pop('thermalExclusion:cold_store')
        self.assertEqual(self.row('sp50-envelope-scope')['status'],'NOT_VERIFIED')
    def test_historic_authority_decision_is_not_automatic_applicability(self):
        self.thermal_facts();self.source_fact('architecturalHistoricSignificance',True)
        self.assertEqual(self.row('sp50-envelope-scope')['status'],'NOT_VERIFIED')
    def test_unknown_building_use_is_not_automatic_exclusion(self):
        self.thermal_facts();self.source_fact('buildingUse','unknown')
        self.assertEqual(self.row('sp50-envelope-scope')['status'],'NOT_VERIFIED')
    def test_one_shared_roof_metric_for_multiple_junctions(self):
        self.targets.append(dict(self.targets[0],id='west'));self.assertEqual(len(self.evaluate()['nativeMetrics']),1)
    def test_units_mismatch_rejected(self):
        self.native['units']='mm'
        with self.assertRaisesRegex(ValueError,'METRES'):self.evaluate()
    def test_missing_actual_guid_rejected(self):
        self.native['elements'].pop()
        with self.assertRaisesRegex(ValueError,'GUID_MISSING'):self.evaluate()

if __name__=='__main__':unittest.main()
