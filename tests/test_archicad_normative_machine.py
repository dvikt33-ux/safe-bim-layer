import copy,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import archicad_normative_machine as M
import archicad_project_accelerator as A
import archicad_normative_bindings as N
import archicad_native_operations as G
import test_archicad_wall_roof_assessment as W
from test_archicad_semantic_brief import valid
from test_archicad_project_library_pack import specimen


class ExistingMachineTests(unittest.TestCase):
    def setUp(self):
        w,r,*_=W.RealJunctionAssessmentTests().fixture()
        native={'units':'m','coordinateSystem':'ABSOLUTE_PROJECT_XYZ','elements':[w,r],'materials':[]}
        self.context={'units':'m','coordinateSystem':'ABSOLUTE_PROJECT_XYZ',
            'elements':{'wall':{'guid':w['guid'],'type':'Wall'},'roof':{'guid':r['guid'],'type':'Roof'}},
            'nativeGeometrySignatures':G.C.retained_geometry_signatures(native,[w['guid'],r['guid']])}
        self.targets=[{'id':'east','family':'wall_roof','guids':[w['guid'],r['guid']]}]
        self.req={'jurisdiction':{'country':'RU','evidenceUri':'user:confirmed-RU'},'projectFacts':{},'cseFacts':{}}
        self.base=A.compile_project_normative_pack(valid(),A.compile_project_library_pack(valid(),specimen()),self.context,self.req,self.targets)
        self.legacy={'schema':'APA_NATIVE_SOURCE_CONDITION_RESULTS_V1',
            'inputNormativePackDigest':self.base['normative']['normativePackDigest'],
            'nativeMetrics':{},'checks':[{'junctionId':'east','status':'PASS_DOCUMENTED'}]}
        self.legacy['resultDigest']=N.RUN.digest(self.legacy)
        self.profile={'object_class':'residential','object_subclass':'izhs','active_functions':[],
            'modules':{'architecture':'details'},'project_phase':'design','jurisdiction':'RU','evidenceUri':'user:IZHS'}
    def evaluate(self):
        return A.connect_existing_normative_database(self.base['projectPack'],self.base['normative'],
            self.context,self.req,self.targets,self.legacy,self.profile)
    def result(self): return self.evaluate()['normative']
    def test_existing_executor_and_single_rule_file(self):
        r=self.result();self.assertEqual(r['status'],'EXISTING_MACHINE_CONNECTED')
        self.assertEqual(len(r['bindings']),9)
        self.assertEqual(r['ruleFilesRead'],[M.MACHINE+'rules/roofing_2026.yaml'])
        self.assertEqual(r['runtimeResolution']['targets'],['IZHS.ROOF.DETAILS'])
        self.assertEqual(r['runtimeResolution']['selected_closure'],['IZHS.ELEMENTS.CORE','IZHS.SHELL.CORE','IZHS.ROOF.DETAILS'])
    def test_quarantine_blocks_even_confirmed_valid_evidence(self):
        rows=self.result()['bindings'];valid_rows=[r for r in rows if r['evidenceGate']=='STORED_FIELDS_PASS']
        self.assertTrue(valid_rows);self.assertTrue(all(r['status']=='NOT_VERIFIED' for r in rows))
        self.assertTrue(all('QUARANTINED_SOURCE_DESIGN_ONLY_RELEASE' in r['missingEvidence'] for r in rows))
        self.assertEqual(self.result()['stagePack'],[]);self.assertFalse(self.result()['normativeAuthority'])
    def test_legacy_document_pass_not_rule_pass(self):
        r=self.result();self.assertEqual(r['legacy']['legacyChecks'],self.legacy['checks'])
        self.assertFalse(any(row['engineeringApproved'] for row in r['bindings']))
    def test_missing_project_type_fails_before_rules(self):
        self.profile.pop('object_subclass');r=self.result()
        self.assertEqual(r['status'],'NOT_VERIFIED_PROFILE');self.assertEqual(r['ruleFilesRead'],[])
    def test_missing_profile_evidence_fails(self):
        self.profile.pop('evidenceUri');self.assertIn('PROJECT_TYPE_EVIDENCE_REQUIRED',self.result()['profileErrors'])
    def test_mkd_no_izhs_roof_fallback(self):
        self.profile['object_subclass']='mkd';r=self.result()
        self.assertEqual(r['status'],'NOT_VERIFIED_ROUTE');self.assertEqual(r['ruleFilesRead'],[])
        self.assertNotIn(M.MACHINE+'routes/objects/residential.izhs.yaml',r['openedSourceFiles'])
    def test_trc_no_residential_rules(self):
        self.profile.update(object_class='public',object_subclass='trade_entertainment_complex')
        r=self.result();self.assertEqual(r['ruleFilesRead'],[]);self.assertEqual(r['status'],'NOT_VERIFIED_ROUTE')
    def test_pending_exact_route_never_parent_fallback(self):
        self.profile['object_subclass']='dormitory';r=self.result()
        self.assertEqual(r['runtimeResolution']['status'],'ROUTE_MISSING');self.assertEqual(r['ruleFilesRead'],[])
    def test_inactive_module_does_not_enable_from_stage(self):
        self.profile['modules']={'architecture':'off'};self.assertEqual(self.result()['ruleFilesRead'],[])
    def test_stage_missing_fails(self):
        self.profile.pop('project_phase');self.assertIn('PROJECT_STAGE_REQUIRED',self.result()['profileErrors'])
    def test_invalid_depth_denied(self):
        self.profile['modules']['architecture']='everything';self.assertIn('MODULE_DEPTH_INVALID:architecture',self.result()['profileErrors'])
    def test_unavailable_depth_does_not_search_library(self):
        self.profile['modules']['architecture']='working';self.assertEqual(self.result()['ruleFilesRead'],[])
    def test_inactive_engineering_blocks_not_read(self):
        paths=self.result()['openedSourceFiles']
        self.assertFalse(any('THERMAL.CORE' in p or 'STRUCTURES.CORE' in p or '/rules/roof_fire' in p for p in paths))
    def test_functions_deny_usable_roof_without_source(self):
        row=next(r for r in self.result()['bindings'] if r['ruleId']=='ROOF-USABLE-PARAPET-1200-001')
        self.assertEqual(row['scopeGate'],'DENY');self.assertIn('FUNCTION_SCOPE_INACTIVE',row['missingEvidence'])
    def test_table_procedure_does_not_invent_row(self):
        row=next(r for r in self.result()['bindings'] if r['ruleId']=='ROOF-SP17-MATERIAL-SLOPE-001')
        self.assertIn('EXACT_CURRENT_TABLE_ROW_OVERLAY_NOT_BOUND',row['missingEvidence'])
        self.assertFalse(row['numericEvaluationExecuted'])
    def test_no_mutation_of_native_or_cse_or_legacy(self):
        before=copy.deepcopy([self.context,self.base,self.legacy]);out=self.evaluate()
        self.assertEqual(before,[self.context,self.base,self.legacy]);self.assertEqual(out['normative']['nativeWriteCalls'],0)
        self.assertEqual(out['normative']['nativeReadCalls'],0);self.assertFalse(out['normative']['geometryRecomputed'])
        for key,value in self.base['projectPack'].items():self.assertEqual(out['projectPack'][key],value)
    def test_changed_cached_result_invalidates(self):
        self.legacy['checks'][0]['status']='PASS';
        with self.assertRaisesRegex(ValueError,'INPUT_EVIDENCE_INVALIDATED'):self.evaluate()
    def test_changed_native_context_invalidates(self):
        self.context['elements']['wall']['material']='different'
        with self.assertRaisesRegex(ValueError,'INPUT_EVIDENCE_INVALIDATED'):self.evaluate()
    def test_changed_requirements_invalidates(self):
        self.req['requestedEditions']={'roof':'СП 17.13330.2011'}
        with self.assertRaisesRegex(ValueError,'INPUT_EVIDENCE_INVALIDATED'):self.evaluate()
    def test_changed_attached_result_invalidates(self):
        r=self.result();r['normativeAuthority']=True
        with self.assertRaisesRegex(ValueError,'RESULT_OR_PROJECT_PACK_INVALIDATED'):M.attach_existing_machine(self.base['projectPack'],r)
    def test_bootstrap_protocol_first(self):
        source=M.ExistingMachineSource();self.assertEqual(source.opened[0],'NORMATIVE_WORK_PROTOCOL.md')
    def test_source_path_escape_denied(self):
        with self.assertRaisesRegex(ValueError,'SOURCE_NOT_PINNED'):M.ExistingMachineSource().read('../secret')
    def test_source_file_tamper_detected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'SOURCE_LOCK.json').write_bytes((M.SOURCE/'SOURCE_LOCK.json').read_bytes())
            (p/'NORMATIVE_WORK_PROTOCOL.md').write_text('modified',encoding='utf8')
            with self.assertRaisesRegex(ValueError,'SOURCE_BYTES_CHANGED'):M.ExistingMachineSource(p)
    def test_forged_lock_denied(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'SOURCE_LOCK.json').write_text('{}',encoding='utf8')
            with self.assertRaisesRegex(ValueError,'LOCK_BYTES_CHANGED'):M.ExistingMachineSource(p)
    def test_upstream_validator_rejects_card_only(self):
        s=M.ExistingMachineSource();gate=s.module('scripts/validate_normative_evidence.py','test_tdk_gate')
        rule=s.data(M.MACHINE+'rules/roofing_2026.yaml')['rules'][0]
        self.assertEqual(gate.validate_confirmed(rule,'fixture'),[])
        rule['verification']['content_access']='metadata_only'
        self.assertTrue(gate.validate_confirmed(rule,'fixture'))
    def test_explicit_edition_mismatch_never_floats(self):
        s=M.ExistingMachineSource();rule=s.data(M.MACHINE+'rules/roofing_2026.yaml')['rules'][0]
        passport=s.data(M.MACHINE+'evidence/sources_roofing_2026.yaml')['sources'][0]
        self.assertIn('REQUESTED_EDITION_NOT_BOUND',M._revision_errors(rule,passport,{'requestedEditions':{'roof':'СП 17.13330.2011'}}))
    def test_legacy_thermal_identity_not_global_reference_upgrade(self):
        r=self.result();m=r['legacy'];self.assertTrue(m['legacyDocumentPassIsNotMachineRulePass'])
        self.assertEqual(m['thermalReference'],'EXACT_REFERENCE_OCCURRENCE_REQUIRED_NO_GLOBAL_PIN_OR_UPGRADE')
        self.assertTrue(any(x['machineSourceId']=='SP-50-13330-2024-GARANT' for x in m['sourceMappings']))

if __name__=='__main__':unittest.main()
