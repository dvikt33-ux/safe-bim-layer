"""The two PR87 regressions, now ordinary targeted checks after repair."""
import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from archicad_dynamic_commands import DynamicCommands
def router():return DynamicCommands(dict(commands={},common_schemas={},element_types={},_metadata=dict(provider_version='1.5.10')))
def entry(name='Call',reference='Payload'):
    return {name:dict(version='1',category='Test',parameters={'$ref':'#/'+reference},returns=dict(type='object'))}
def payload(kind):return dict(type='object',properties={'amount':dict(type=kind)},required=['amount'])
class ProviderRegistration(unittest.TestCase):
    def test_duplicate_batch_is_atomic_including_shared_schemas_and_fingerprint(self):
        r=router();r.add_provider('Vendor',entry(),'source-a',{'Payload':payload('integer')});before=copy.deepcopy(r.catalog);fingerprint=r.fingerprint
        with self.assertRaises(ValueError):r.add_provider('Vendor',{**entry('New'),**entry()},'source-b',{'Payload':payload('string')})
        self.assertEqual(r.catalog,before);self.assertEqual(r.fingerprint,fingerprint);r.prepare('AddOn.Vendor.Call',{'amount':2})
    def test_ambiguous_namespace_does_not_retype_preexisting_provider(self):
        r=router();r.add_provider('A__B',entry(reference='C'),'first',{'C':payload('integer')});old_hash=r.contract_hash('AddOn.A__B.Call')
        r.add_provider('A',entry('Other','B__C'),'second',{'B__C':payload('string')})
        r.prepare('AddOn.A__B.Call',{'amount':2});r.prepare('AddOn.A.Other',{'amount':'two'})
        self.assertEqual(r.contract_hash('AddOn.A__B.Call'),old_hash);self.assertEqual(len(r.catalog['common_schemas']),2)
if __name__=='__main__':unittest.main()
