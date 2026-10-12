"""Requirement/source binding without implicit engineering acceptance."""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import archicad_normative_bindings as N
import archicad_project_accelerator as A
from test_archicad_semantic_brief import valid
from test_archicad_project_library_pack import specimen

class NormativeBindingsTests(unittest.TestCase):
    def setUp(self):
        self.brief=valid();self.pack=A.compile_project_library_pack(self.brief,specimen())
        self.context={'units':'m','coordinateSystem':'ABSOLUTE_PROJECT_XYZ',
            'elements':{'wall':{'guid':'wall','material':'concrete'},'roof':{'guid':'roof','roofClass':'SinglePlane'}},
            'nativeGeometrySignatures':{'wall':'body-wall','roof':'body-roof'}}
        self.junctions=[{'id':'east','family':'wall_roof','guids':['wall','roof']}]
        self.req={'jurisdiction':{'country':'RU','evidenceUri':'https://example.org/site'},
                  'cseFacts':{'east':{'sourceEvidenceUri':'https://example.org/cse',
                      'nativeContextSignature':N.native_binding_signature(self.context,['wall','roof'])}}}
    def compile(self):return N.compile_normative_pack(self.brief,self.pack,self.context,self.req,self.junctions)
    def row(self,key):return next(r for r in self.compile()['bindings'] if r['ruleId']==key)
    def test_existing_pack_end_to_end_digest_and_no_approval(self):
        result=A.compile_project_normative_pack(self.brief,self.pack,self.context,self.req,self.junctions)
        self.assertEqual(result['projectPack']['normativePackDigest'],result['normative']['normativePackDigest'])
        self.assertEqual(result['projectPack']['selectedCseCandidates'],self.pack['selectedCseCandidates'])
        self.assertFalse(result['projectPack']['selectedCseCandidates'][0]['engineeringApproved'])
        self.assertEqual(result['normative']['nativeWriteCalls'],0)
        self.assertFalse(any(r['engineeringApproved'] or r['numericEvaluationExecuted'] for r in result['normative']['bindings']))
    def test_region_does_not_certify_jurisdiction(self):
        self.req.pop('jurisdiction');self.assertIn('PROJECT_JURISDICTION_NOT_VERIFIED',self.row('roof-system-and-junction')['missingEvidence'])
    def test_requested_old_edition_requires_review(self):
        self.req['requestedEditions']={'thermal':'СП 50.13330.2012'}
        self.assertIn('REQUESTED_EDITION_DIFFERS_FROM_VERIFIED_REGISTRY',self.row('thermal-envelope-interface')['missingEvidence'])
    def test_bound_different_system_excludes_only_specific_rule(self):
        self.req['cseFacts']['east']['roofSystem']='metal_sheet'
        self.assertEqual(self.row('bitumen-parapet-detail')['status'],'NOT_APPLICABLE')
        self.assertEqual(self.row('roof-system-and-junction')['status'],'NOT_VERIFIED')
    def test_unbound_system_never_excludes(self):
        self.req['cseFacts']['east'].update(roofSystem='metal_sheet',nativeContextSignature='stale')
        self.assertEqual(self.row('bitumen-parapet-detail')['status'],'NOT_VERIFIED')
    def test_unknown_native_roof_class_is_not_technology(self):
        self.assertEqual(self.row('bitumen-parapet-detail')['status'],'NOT_VERIFIED')
    def test_malformed_predicate_not_exclusion(self):
        self.req['cseFacts']['east']['roofSystem']={'unknown':True}
        self.assertEqual(self.row('bitumen-parapet-detail')['status'],'NOT_VERIFIED')
    def test_material_change_invalidates_source(self):
        self.context['elements']['wall']['material']='other'
        self.assertIn('CSE_SOURCE_OR_NATIVE_SIGNATURE_NOT_BOUND',self.row('roof-system-and-junction')['missingEvidence'])
    def test_brep_change_invalidates_source_even_same_bounds(self):
        self.context['nativeGeometrySignatures']['roof']='changed-body'
        self.assertIn('CSE_SOURCE_OR_NATIVE_SIGNATURE_NOT_BOUND',self.row('roof-system-and-junction')['missingEvidence'])
    def test_missing_brep_does_not_certify_system_exclusion(self):
        self.context.pop('nativeGeometrySignatures');selected=self.req['cseFacts']['east']
        selected.update(roofSystem='metal_sheet',nativeContextSignature=N.native_binding_signature(self.context,['wall','roof']))
        row=self.row('bitumen-parapet-detail');self.assertEqual(row['status'],'NOT_VERIFIED')
        self.assertIn('NATIVE_BODY_SIGNATURE_NOT_BOUND',row['missingEvidence'])
    def test_family_scopes_window_rule(self):self.assertEqual(self.row('window-installation-layer-evidence')['status'],'NOT_APPLICABLE')
    def test_project_pack_change_invalidates_attachment(self):
        result=self.compile();self.pack['projectId']='changed'
        with self.assertRaisesRegex(ValueError,'INVALIDATED'):N.attach_to_project_pack(self.pack,result)
    def test_result_edit_invalidates_attachment(self):
        result=self.compile();result['bindings'][0]['engineeringApproved']=True
        with self.assertRaisesRegex(ValueError,'INVALIDATED'):N.attach_to_project_pack(self.pack,result)
    def test_missing_guid_rejected(self):
        self.junctions[0]['guids'].append('absent')
        with self.assertRaisesRegex(ValueError,'GUID_NOT_BOUND'):self.compile()
    def test_wrong_units_rejected(self):
        self.context['units']='mm'
        with self.assertRaisesRegex(ValueError,'CONTEXT_MISMATCH'):self.compile()
    def test_duplicate_junction_rejected(self):
        self.junctions+=copy.deepcopy(self.junctions)
        with self.assertRaisesRegex(ValueError,'DUPLICATE'):self.compile()
    def test_malformed_jurisdiction_rejected(self):
        self.req['jurisdiction']='RU'
        with self.assertRaisesRegex(ValueError,'JURISDICTION'):self.compile()
    def test_complete_declared_facts_still_require_clauses_and_engineering(self):
        catalog=self.compile()['registry'];self.req['projectFacts']={k:{'evidenceUri':'https://example.org/fact'} for r in catalog['rules'] for k in r['requiredProjectFacts']}
        self.req['cseFacts']['east'].update({k:'declared' for r in catalog['rules'] for k in r['requiredCseFacts']})
        rows=self.compile()['bindings'];self.assertFalse(any(r['status']=='VERIFIED' for r in rows))
        self.assertFalse(any(r['engineeringApproved'] for r in rows))

if __name__=='__main__':unittest.main()
