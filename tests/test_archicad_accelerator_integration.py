"""Integrated scenario and safety checks; transports here are synthetic only."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import archicad_accelerator_integration as I
from test_archicad_project_accelerator import WholeNative


class SyntheticWhole(WholeNative):
    evidence_kind='SYNTHETIC'


class IntegratedTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.output=Path(self.tmp.name)/'integration'
        self.intent=json.loads((ROOT/'examples/accelerator/pavilion.intent.json').read_text())
        self.native=SyntheticWhole()

    def test_complete_integrated_frame_and_sources_and_saved_geometry(self):
        result=I.run_integration(self.intent,self.output,transport=self.native,
            saved_dump=ROOT/'examples/model_dump_v1.sample.json',synthetic_execute=True)
        self.assertEqual(result['status'],'SYNTHETIC_WHOLE_SCENE_VERIFIED',result)
        self.assertEqual(result['syntheticWriteAttempts'],12)
        self.assertEqual(result['modelWriteAttempts'],0)
        self.assertTrue(result['assembly']['wholeAssemblyReadback'])
        self.assertEqual(result['assembly']['removedGuids'],[])
        self.assertEqual(len(result['assembly']['addedGuids']),12)
        refs=json.loads((self.output/'source-index.json').read_text(encoding='utf-8'))
        self.assertEqual(len(refs['researchFiles']),113)
        geometry=json.loads((self.output/'saved-geometry.json').read_text())
        self.assertFalse(geometry['pavilionGeometryVerified'])
        self.assertGreater(geometry['counts']['vertices'],0)

    def test_missing_mandatory_mep_blocks_before_any_transport(self):
        result=I.run_integration(self.intent,self.output,transport=self.native,
            required=['pavilion-frame-v1','mep-designer'],synthetic_execute=True)
        self.assertEqual(result['status'],'BLOCKED')
        self.assertFalse(self.native.calls)

    def test_wrong_pln_stops_before_followons(self):
        self.native.wrong_project=True
        result=I.run_integration(self.intent,self.output,mode='preflight',transport=self.native)
        self.assertEqual(result['status'],'BLOCKED')
        self.assertEqual(self.native.calls,['GetProjectInfo'])

    def test_readonly_adapter_rejects_writes_and_crash_prone_property_reads(self):
        adapter=I.ReadAdapter('direct')
        for command in ['CreateWalls','DeleteElements','GetPropertyValuesOfElements','SaveProject','GetModelDumpV1']:
            with self.assertRaisesRegex(ValueError,'READ_ADAPTER_REFUSED'):
                adapter(command,{})
        self.assertFalse(adapter.calls)

    def test_installed_connection_shim_preserves_exact_payload_without_discovery(self):
        class Core:
            def __init__(self): self.calls=[]
            def official(self,command,params):
                self.calls.append((command,params))
                return {'addOnCommandResponse':{'projectName':'synthetic'}}
        core=Core()
        adapter=I.ReadAdapter('alesdev88',core)
        self.assertEqual(adapter('GetProjectInfo',{}),{'projectName':'synthetic'})
        self.assertEqual(core.calls,[('API.ExecuteAddOnCommand',{
            'addOnCommandId':{'commandNamespace':'TapirCommand','commandName':'GetProjectInfo'},
            'addOnCommandParameters':{}})])

    def test_invalid_face_and_material_pool_are_blocked(self):
        sample=json.loads((ROOT/'examples/model_dump_v1.sample.json').read_text(encoding='utf-8'))
        sample['elements'][0]['bodies'][0]['faces'][0]['materialId']=-987
        path=Path(self.tmp.name)/'bad-dump.json'
        path.write_text(json.dumps(sample),encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'UNRESOLVED_MATERIAL_POOL_ID'):
            I.verify_saved_dump(path)

    def test_timeout_and_assembly_drift_never_complete_integration(self):
        self.native.fail_at='CreateSlabs'
        result=I.run_integration(self.intent,self.output,transport=self.native,synthetic_execute=True)
        self.assertEqual(result['status'],'BLOCKED')
        self.assertEqual(result['assembly']['status'],'PARTIAL_OR_UNKNOWN_OUTCOME')
        self.assertEqual(self.native.writes,['CreateWalls']*4+['CreateSlabs'])

    def test_preflight_registration_is_not_deep_geometry_pass(self):
        class ReadNative(SyntheticWhole):
            def __call__(self,command,params):
                if command=='API.IsAddOnCommandAvailable':
                    self.calls.append(command)
                    return {'available':False}
                return super().__call__(command,params)
        native=ReadNative()
        result=I.run_integration(self.intent,self.output,mode='preflight',transport=native)
        self.assertEqual(result['status'],'READ_ONLY_PREFLIGHT_READY')
        self.assertEqual(result['deepGeometryCoverage'],'UNAVAILABLE_IN_CURRENT_ADDON')
        self.assertFalse(native.writes)


if __name__=='__main__':
    unittest.main()
