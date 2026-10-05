import io
import json
import hashlib
import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from closed_loop.stage4_preflight import preflight


class IdentityGateTests(unittest.TestCase):
    def envelope(self,value):
        return io.BytesIO(json.dumps({'succeeded':True,'result':{'addOnCommandResponse':value}}).encode())

    def test_wrong_project_stops_before_product_tapir_or_dump(self):
        with tempfile.TemporaryDirectory() as temp, \
                patch('closed_loop.stage4_preflight.read',return_value={'identity':{'projectPath':'expected.pln'}}), \
                patch('closed_loop.stage4_preflight.urllib.request.urlopen',return_value=self.envelope({'projectPath':'wrong.pln'})) as transport:
            result=preflight(Path(temp)/'gate')
            self.assertEqual(result['status'],'BLOCKED')
            self.assertFalse(result['mutationAttempted'])
            self.assertEqual(transport.call_count,1)

    def test_exact_identity_and_environment_pass_read_only(self):
        identity={'projectPath':'expected.pln','isUntitled':False}
        product={'version':29,'buildNumber':3000,'languageCode':'RUS'}
        tapir={'version':'1.5.10'}
        with tempfile.TemporaryDirectory() as temp, \
                patch('closed_loop.stage4_preflight.read',return_value={'identity':identity,'tapir':tapir}), \
                patch('closed_loop.stage4_preflight.urllib.request.urlopen',side_effect=[self.envelope(identity),self.envelope(product),self.envelope(tapir)]) as transport:
            result=preflight(Path(temp)/'gate')
            self.assertEqual(result['status'],'PASS')
            self.assertFalse(result['mutationAttempted'])
            self.assertEqual(transport.call_count,3)

    def test_environment_mismatch_cannot_pass(self):
        identity={'projectPath':'expected.pln'}
        with tempfile.TemporaryDirectory() as temp, \
                patch('closed_loop.stage4_preflight.read',return_value={'identity':identity,'tapir':{'version':'1.5.10'}}), \
                patch('closed_loop.stage4_preflight.urllib.request.urlopen',side_effect=[self.envelope(identity),self.envelope({'version':30}),self.envelope({'version':'1.5.10'})]):
            result=preflight(Path(temp)/'gate')
            self.assertEqual(result['status'],'BLOCKED')

    def test_live_scenario_does_not_construct_executor_after_wrong_project(self):
        from closed_loop import stage4_live_scenario as runner
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            pins=[]
            for name in runner.IMPLEMENTATION_FILES:
                path=root/name
                path.parent.mkdir(parents=True,exist_ok=True)
                path.write_bytes(b'fixture implementation pin')
                pins.append({'path':name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
            proof=root/'offline-proof.json'
            proof.write_text(json.dumps({'status':'PASS','oldTests':95,'newTests':1,
                'tests':{'old':{'status':'PASS'}},'implementationFiles':pins}))
            output=root/'outputs/closed-loop-stage4/S4-01'
            with patch.object(runner,'ROOT',root),patch.object(sys,'argv',['scenario','--scenario','S4-01',
                    '--output',str(output),'--offline-proof',str(proof),'--live']), \
                    patch.object(runner,'preflight',return_value={'status':'BLOCKED','reason':'WRONG_PROJECT'}), \
                    patch.object(runner,'LiveSession',side_effect=AssertionError('No adapters after identity mismatch')):
                self.assertEqual(runner.main(),1)
                report=json.loads((output/'verification-report.json').read_text())
                self.assertEqual(report['physicalMutationCalls'],0)
                self.assertEqual(report['status'],'BLOCKED')


if __name__=='__main__':unittest.main()
