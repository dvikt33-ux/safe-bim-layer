from collections import Counter
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import scripts.stage4_audit_pack as stage4_pack
from scripts.stage4_audit_pack import source_contract, build_pack, verify_pack
from scripts.audit_pack import AuditError, model_summary, read_json, scan_public_pack
from closed_loop.wall_attempts import durable_json
from tests_stage4_live.test_attempts import fixture


class ScenarioPackTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.scenario = self.root/'S4-03'
        self.scenario.mkdir()
        before, after, attempt = fixture()
        before['elements'][0]['bodies'] = [{'nativeBodyIndex': 1}]
        after['elements'][0]['bodies'] = [{'nativeBodyIndex': 9}]
        self.before_data, self.after_data = deepcopy(before), deepcopy(after)
        self.before, self.after = self.scenario/'before.json', self.scenario/'after.json'
        self.record = self.scenario/'job.json'
        durable_json(self.before, before)
        durable_json(self.after, after)
        durable_json(self.record, {'state':'UNKNOWN_OUTCOME', 'attempt':attempt, 'localPath':'C:\\Users\\Private\\project.pln'})
        self.contract = source_contract(self.root, self.scenario, [self.before,self.after],
            [(self.before,self.after)], [self.record], 'C:\\Users\\Private\\project.pln', 'OFFLINE_FIXTURE')
        self.pack = self.scenario/'audit-pack'

    def test_failed_scenario_pack_is_public_source_pinned_and_semantic(self):
        build_pack(self.root,self.contract,self.pack)
        self.assertEqual(verify_pack(self.root,self.pack)['status'],'PASS')
        self.assertEqual(scan_public_pack(self.pack)['status'],'PASS')
        delta = read_json(self.pack/'deltas/001.json')
        self.assertEqual(delta['rawChanged'],['SOURCE'])
        self.assertEqual(delta['semanticChanged'],[])
        self.assertEqual(delta['technicalNoiseChanged'],['SOURCE'])

    def test_changed_source_rejects_existing_pack(self):
        build_pack(self.root,self.contract,self.pack)
        durable_json(self.after, {'elements':[]})
        with self.assertRaises(AuditError): verify_pack(self.root,self.pack)

    def test_forged_compact_delta_or_extra_file_rejects(self):
        build_pack(self.root,self.contract,self.pack)
        durable_json(self.pack/'deltas/001.json',{'semanticChanged':[]})
        with self.assertRaises(AuditError): verify_pack(self.root,self.pack)

    def test_zero_mutation_scenario_still_has_verified_evidence_pack(self):
        self.contract['pairs']=[]
        build_pack(self.root,self.contract,self.pack)
        self.assertEqual(verify_pack(self.root,self.pack)['status'],'PASS')


    def test_each_snapshot_is_parsed_once_per_extraction(self):
        calls = []
        snapshot_names = set(self.contract['snapshots'])
        original = stage4_pack._pinned_json_once

        def counted(root, spec):
            if spec['path'] in snapshot_names:
                calls.append(spec['path'])
            return original(root, spec)

        with patch.object(stage4_pack, '_pinned_json_once', side_effect=counted):
            stage4_pack.extract(self.root, self.contract)

        self.assertEqual(Counter(calls), Counter(self.contract['snapshots']))


    def test_optimized_model_summary_is_byte_equivalent(self):
        after_data = read_json(self.after)
        old_summary, old_index = model_summary(after_data, 'fixture')
        new_summary, new_index = stage4_pack._model_summary_once(after_data, 'fixture')
        self.assertEqual(new_summary, old_summary)
        self.assertEqual(new_index, old_index)


    def test_timing_only_snapshots_share_one_semantic_parse(self):
        a = deepcopy(self.before_data)
        b = deepcopy(self.before_data)
        a['nativeSeconds'] = 0.125
        b['nativeSeconds'] = 9.875
        first = self.scenario/'same-a.json'
        second = self.scenario/'same-b.json'
        durable_json(first, a)
        durable_json(second, b)
        contract = source_contract(self.root, self.scenario, [first, second], [(first, second)],
            [first, second], 'fixture', 'OFFLINE_FIXTURE')
        calls = []
        original = stage4_pack._pinned_json_once

        def counted(root, spec):
            calls.append(spec['path'])
            return original(root, spec)

        with patch.object(stage4_pack, '_pinned_json_once', side_effect=counted):
            blobs = stage4_pack.extract(self.root, contract)

        snapshot_paths = set(contract['snapshots'])
        parsed_snapshots = [path for path in calls if path in snapshot_paths]
        self.assertEqual(len(parsed_snapshots), 1)
        delta = __import__('json').loads(blobs['deltas/001.json'])
        self.assertEqual(delta['added'], [])
        self.assertEqual(delta['removed'], [])
        self.assertEqual(delta['changed'], [])

    def test_nested_native_seconds_never_collapses_semantic_change(self):
        a = deepcopy(self.before_data)
        b = deepcopy(self.before_data)
        a['nativeSeconds'] = 1.0
        b['nativeSeconds'] = 2.0
        a['elements'][0]['properties']['nativeSeconds'] = 10
        b['elements'][0]['properties']['nativeSeconds'] = 11
        first = self.scenario/'nested-a.json'
        second = self.scenario/'nested-b.json'
        durable_json(first, a)
        durable_json(second, b)
        sa = stage4_pack.file_info(self.root, first.relative_to(self.root).as_posix())
        sb = stage4_pack.file_info(self.root, second.relative_to(self.root).as_posix())
        self.assertNotEqual(stage4_pack._semantic_source_key(self.root, sa),
                            stage4_pack._semantic_source_key(self.root, sb))


if __name__ == '__main__': unittest.main()
