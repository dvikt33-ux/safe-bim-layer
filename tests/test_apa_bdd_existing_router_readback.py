"""Targeted offline checks for BDD read-only runner over existing APA components."""
import sys
from pathlib import Path
import json
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import apa_bdd_existing_router_readback as R

class TestBDDExistingAPA(unittest.TestCase):
    def setUp(self):
        self.binding=json.loads(R.BINDING.read_text(encoding='utf-8'))
        self.task=json.loads(R.INTENT.read_text(encoding='utf-8'))

    def test_real_reference_guid_contract(self):
        all_ids,parents=R.baseline_ids(self.binding)
        self.assertEqual(len(all_ids),261)
        self.assertEqual(len(parents),125)
        self.assertNotEqual(R.ROOT / 'scripts/archicad_dynamic_commands.py',R.ROOT / 'scripts/apa_bdd_existing_router_readback.py')

    def test_real_intent_readonly_and_all_125_parents(self):
        steps=self.task['graph']['operations']
        self.assertEqual(len(steps),13)
        self.assertEqual({x['command'] for x in steps},R.COMMANDS)
        selected=[
            x['elementId']['guid'].lower()
            for op in steps if op['command']=='GetDetailsOfElements'
            for x in op['params']['elements']]
        self.assertEqual(len(selected),125)
        self.assertEqual(set(selected),R.baseline_ids(self.binding)[1])

    def test_exact_inventory_rejects_drift(self):
        expected,parents=R.baseline_ids(self.binding)
        array=[{'elementId':{'guid':g}} for g in sorted(expected)]
        actual=R.exact_model_set({'elements':array},expected)
        self.assertEqual(len(actual),261)
        with self.assertRaisesRegex(ValueError,'APA_MODEL_DRIFT'):
            R.exact_model_set({'elements':array[:-1]},expected)
        with self.assertRaisesRegex(ValueError,'APA_DUPLICATE_GUID'):
            R.exact_model_set({'elements':array+[array[0]]},expected)

    def test_existing_graph_compiler_not_shadowed(self):
        import archicad_bim_graph as G
        catalog=json.loads(R.SCHEMA.read_text(encoding='utf-8'))
        compile_result=G.compile_graph(catalog,self.task['graph'],runtime_version='1.5.10')
        self.assertEqual(compile_result['status'],'PLAN_VALIDATED_OFFLINE')

if __name__=='__main__':
    unittest.main()
