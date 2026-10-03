import copy
import json
from pathlib import Path
import unittest
import subprocess
import sys
import tempfile
from unittest.mock import patch

from bim_qa import audit_snapshot, snapshot_from_readback, _dependency, RULES_PATH


def wall(guid='wall', start=0, end=7):
    return {'guid': guid, 'type': 'Wall', 'floorIndex': 0, 'details': {
        'geometryType': 'Straight', 'arcAngle': 0, 'begCoordinate': {'x': start, 'y': 0},
        'endCoordinate': {'x': end, 'y': 0}, 'zCoordinate': 0, 'height': 3.2}}


def fixture():
    return {
        'projectId': 'synthetic-project', 'snapshotId': 'synthetic-revision-1', 'auditScope': 'pilot',
        'inventoryComplete': True, 'elements': [wall(),
            {'guid': 'window', 'type': 'Window', 'details': {'ownerElementId': {'guid': 'wall'}}},
            {'guid': 'door', 'type': 'Door', 'details': {'ownerElementId': {'guid': 'wall'}}}],
        'openingIntentsComplete': True,
        'openingIntents': [{'kind': 'Window', 'guid': 'window', 'hostGuid': 'wall'},
                           {'kind': 'Door', 'guid': 'door', 'hostGuid': 'wall'}],
        'wallSystemsComplete': True,
        'wallSystems': [{'id': 'south', 'guids': ['wall'], 'begCoordinate': {'x': 0, 'y': 0},
            'endCoordinate': {'x': 7, 'y': 0}, 'floorIndex': 0, 'zCoordinate': 0, 'height': 3.2}],
        'controlledInventoryComplete': True, 'controlledGuids': ['wall', 'window', 'door'],
        'identityRegistryComplete': True,
        'identityRegistry': [{'guid': g, 'entityId': 'entity-' + g, 'role': g, 'identityScope': 'pilot'}
                             for g in ('wall', 'window', 'door')],
        'operationJournalComplete': True,
        'operationJournal': [{'operationId': 'synthetic-op', 'status': 'DONE', 'guids': ['wall', 'window', 'door']}]
    }


class QATests(unittest.TestCase):
    def setUp(self):
        self.s = fixture()

    def outcome(self, rule):
        return audit_snapshot(self.s, 'PASS_3_WINDOWS_DOORS')['rules'][rule]['status']

    def test_complete_synthetic_checks_pass_but_stage_does_not(self):
        report = audit_snapshot(self.s, 'PASS_3_WINDOWS_DOORS')
        for rule in ('BIM-QA-001', 'BIM-QA-002', 'BIM-QA-003', 'BIM-QA-009'):
            self.assertEqual(report['rules'][rule]['status'], 'PASS')
        self.assertEqual(report['status'], 'NOT_VERIFIED')  # story checker remains unimplemented

    def test_empty_or_malformed_snapshot_never_passes(self):
        for s in ({}, None, [], {'elements': []}, {'elements': 'bad'}):
            with self.subTest(s=s):
                self.assertEqual(audit_snapshot(s, 'PASS_1_STORIES')['status'], 'NOT_VERIFIED')

    def test_no_implicit_completeness(self):
        for key in ('inventoryComplete', 'projectId', 'snapshotId', 'auditScope'):
            with self.subTest(key=key):
                s = fixture()
                del s[key]
                for r in ('BIM-QA-001', 'BIM-QA-002', 'BIM-QA-003', 'BIM-QA-009'):
                    self.assertEqual(audit_snapshot(s, 'PASS_2_WALLS')['rules'][r]['status'], 'NOT_VERIFIED')

    def test_inventory_duplicate_guid(self):
        self.s['elements'].append(wall())
        self.assertEqual(self.outcome('BIM-QA-009'), 'NOT_VERIFIED')

    def test_transport_failure(self):
        self.s['transportError'] = 'timeout'
        self.assertEqual(self.outcome('BIM-QA-002'), 'BLOCKED_BY_TRANSPORT')
        self.assertEqual(audit_snapshot(self.s, 'PASS_3_WINDOWS_DOORS')['status'], 'BLOCKED_BY_TRANSPORT')

    def test_morph_and_wrong_native_types_fail(self):
        for position, rule in ((1, 'BIM-QA-002'), (2, 'BIM-QA-003')):
            for kind in ('Morph', 'Object', 'Opening', 'Wall'):
                with self.subTest(rule=rule, kind=kind):
                    self.s = fixture()
                    self.s['elements'][position]['type'] = kind
                    self.assertEqual(self.outcome(rule), 'FAIL')

    def test_wrong_host_fails_both_kinds(self):
        for position, rule in ((1, 'BIM-QA-002'), (2, 'BIM-QA-003')):
            with self.subTest(rule=rule):
                self.s = fixture()
                self.s['elements'][position]['details']['ownerElementId']['guid'] = 'other'
                self.assertEqual(self.outcome(rule), 'FAIL')

    def test_missing_host_is_not_verified(self):
        for owner in (None, {}, {'guid': ''}, 'bad'):
            self.s['elements'][1]['details']['ownerElementId'] = owner
            self.assertEqual(self.outcome('BIM-QA-002'), 'NOT_VERIFIED')

    def test_host_not_in_inventory(self):
        self.s['elements'].pop(0)
        self.assertEqual(self.outcome('BIM-QA-002'), 'NOT_VERIFIED')

    def test_host_wrong_type(self):
        self.s['elements'][0]['type'] = 'Morph'
        self.assertEqual(self.outcome('BIM-QA-002'), 'FAIL')

    def test_missing_intended_element(self):
        self.s['elements'].pop(1)
        self.assertEqual(self.outcome('BIM-QA-002'), 'NOT_VERIFIED')

    def test_unmapped_native_element(self):
        self.s['openingIntents'] = [self.s['openingIntents'][1]]
        self.assertEqual(self.outcome('BIM-QA-002'), 'NOT_VERIFIED')

    def test_empty_openings_pass_only_if_explicitly_complete(self):
        self.s['elements'] = [wall()]
        self.s['openingIntents'] = []
        self.assertEqual(self.outcome('BIM-QA-002'), 'PASS')
        self.s['openingIntentsComplete'] = False
        self.assertEqual(self.outcome('BIM-QA-002'), 'NOT_VERIFIED')

    def split_wall(self):
        self.s['elements'][0] = wall('wall', 0, 3)
        self.s['elements'].append(wall('wall-2', 3, 7))
        self.s['wallSystems'][0]['guids'].append('wall-2')

    def test_fragmentation_fails(self):
        self.split_wall()
        self.assertEqual(self.outcome('BIM-QA-001'), 'FAIL')

    def test_reviewed_material_split_passes(self):
        self.split_wall()
        self.s['wallSystems'][0]['fragmentationException'] = {
            'category': 'material', 'reason': 'Masonry changes at x=3', 'reviewedBy': 'fixture-reviewer', 'approved': True}
        self.assertEqual(self.outcome('BIM-QA-001'), 'PASS')

    def test_opening_or_gable_excuses_never_pass(self):
        self.split_wall()
        for category in ('opening', 'gable', 'visual', ''):
            self.s['wallSystems'][0]['fragmentationException'] = {
                'category': category, 'reason': 'draw shape', 'reviewedBy': 'reviewer', 'approved': True}
            self.assertEqual(self.outcome('BIM-QA-001'), 'FAIL')

    def test_unreviewed_split_fails(self):
        self.split_wall()
        self.s['wallSystems'][0]['fragmentationException'] = {'category': 'material', 'reason': 'change'}
        self.assertEqual(self.outcome('BIM-QA-001'), 'FAIL')

    def test_wall_gaps_overlaps_and_stepped_verticals_fail(self):
        for field, value in (('begCoordinate', {'x': 4, 'y': 0}),
                             ('begCoordinate', {'x': 2, 'y': 0}),
                             ('zCoordinate', 1), ('height', 2)):
            self.s = fixture()
            self.split_wall()
            self.s['elements'][-1]['details'][field] = value
            self.assertEqual(self.outcome('BIM-QA-001'), 'FAIL')

    def test_reversed_wall_direction_passes(self):
        self.s['elements'][0] = wall('wall', 7, 0)
        self.assertEqual(self.outcome('BIM-QA-001'), 'PASS')

    def test_missing_wall_geometry_or_unsupported_curve(self):
        for key in ('begCoordinate', 'zCoordinate', 'height', 'geometryType', 'arcAngle'):
            self.s = fixture()
            del self.s['elements'][0]['details'][key]
            self.assertEqual(self.outcome('BIM-QA-001'), 'NOT_VERIFIED')
        self.s = fixture()
        self.s['elements'][0]['details']['geometryType'] = 'Trapezoid'
        self.assertEqual(self.outcome('BIM-QA-001'), 'NOT_VERIFIED')

    def test_nonfinite_and_boolean_geometry(self):
        for value in (float('nan'), float('inf'), True, '3.2', None):
            self.s['elements'][0]['details']['height'] = value
            self.assertEqual(self.outcome('BIM-QA-001'), 'NOT_VERIFIED')

    def test_wall_coverage_missing_or_repeated(self):
        self.s['elements'].append(wall('extra'))
        self.assertEqual(self.outcome('BIM-QA-001'), 'NOT_VERIFIED')
        self.s = fixture()
        self.s['wallSystems'].append(copy.deepcopy(self.s['wallSystems'][0]))
        self.assertEqual(self.outcome('BIM-QA-001'), 'NOT_VERIFIED')

    def test_duplicate_entity_and_role_fail(self):
        for key in ('entityId', 'role'):
            self.s = fixture()
            self.s['identityRegistry'][1][key] = self.s['identityRegistry'][0][key]
            self.assertEqual(self.outcome('BIM-QA-009'), 'FAIL')

    def test_same_role_in_different_identity_scope(self):
        self.s['identityRegistry'][1]['role'] = 'wall'
        self.s['identityRegistry'][1]['identityScope'] = 'other-building'
        self.assertEqual(self.outcome('BIM-QA-009'), 'PASS')

    def test_missing_registry_or_journal_blocks(self):
        for key in ('identityRegistry', 'operationJournal', 'controlledGuids', 'identityRegistryComplete',
                    'operationJournalComplete', 'controlledInventoryComplete'):
            self.s = fixture()
            del self.s[key]
            self.assertEqual(self.outcome('BIM-QA-009'), 'NOT_VERIFIED')

    def test_uncovered_controlled_element(self):
        self.s['identityRegistry'].pop()
        self.assertEqual(self.outcome('BIM-QA-009'), 'NOT_VERIFIED')

    def test_unknown_outcome_and_pending_operations_block(self):
        for status in ('UNKNOWN_OUTCOME', 'PENDING', 'WAITING_USER', 'FAIL', 'PASS', None):
            self.s['operationJournal'][0]['status'] = status
            self.assertEqual(self.outcome('BIM-QA-009'), 'NOT_VERIFIED')

    def test_retry_same_guid_is_not_duplicate(self):
        self.s['operationJournal'].append({'operationId': 'retry', 'status': 'RECONCILED', 'guids': ['wall']})
        self.assertEqual(self.outcome('BIM-QA-009'), 'PASS')

    def test_journal_guid_not_in_registry(self):
        self.s['operationJournal'][0]['guids'].append('ghost')
        self.assertEqual(self.outcome('BIM-QA-009'), 'NOT_VERIFIED')

    def test_empty_journal_or_duplicate_operation_id_cannot_pass(self):
        self.s['operationJournal'] = []
        self.assertEqual(self.outcome('BIM-QA-009'), 'NOT_VERIFIED')
        self.s = fixture()
        self.s['operationJournal'].append(copy.deepcopy(self.s['operationJournal'][0]))
        self.assertEqual(self.outcome('BIM-QA-009'), 'NOT_VERIFIED')

    def test_json_only_updates_implemented_rules(self):
        rules = json.loads(RULES_PATH.read_text())['rules']
        for rule in rules:
            if rule['id'] in ('BIM-QA-001', 'BIM-QA-002', 'BIM-QA-003', 'BIM-QA-009', 'BIM-QA-010'):
                self.assertEqual(rule['implementationState'], 'IMPLEMENTED_OFFLINE')
                self.assertEqual(rule['liveValidationState'], 'NOT_VERIFIED')
            else:
                self.assertEqual(rule['implementationStatus'], 'TO_IMPLEMENT')
                self.assertNotIn('implementationState', rule)

    def test_cli_missing_and_unverified_input_exit_nonzero(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'snapshot.json'
            for content in ('{}', '{bad json'):
                path.write_text(content)
                proc = subprocess.run([sys.executable, str(RULES_PATH.parent.parent / 'bim_qa.py'),
                    '--snapshot', str(path), '--stage', 'PASS_2_WALLS'], capture_output=True, text=True)
                self.assertEqual(proc.returncode, 1)
                self.assertEqual(json.loads(proc.stdout)['status'], 'NOT_VERIFIED')

    def test_safe_bim_adapter_valid_receipt_does_not_copy_operation_pass(self):
        response = {'detailsOfElements': [wall()]}
        operation = {'guids': ['wall'], 'status': 'PASS', 'readbackResponse': response}
        snap = snapshot_from_readback(operation, ['wall'], {})
        self.assertNotIn('transportError', snap)
        self.assertEqual(audit_snapshot(snap, 'PASS_2_WALLS')['status'], 'NOT_VERIFIED')

    def test_readback_adapter_uses_request_order_not_element_label(self):
        rows = [{k: v for k, v in row.items() if k != 'guid'} for row in self.s['elements']]
        rows[0]['id'] = 'Wall-001'
        response = {'succeeded': True, 'result': {'addOnCommandResponse': {'detailsOfElements': rows}}}
        snap = snapshot_from_readback(response, ['wall', 'window', 'door'], self.s)
        self.assertEqual(snap['elements'][0]['guid'], 'wall')
        self.assertEqual(audit_snapshot(snap, 'PASS_2_WALLS')['rules']['BIM-QA-001']['status'], 'PASS')

    def test_readback_errors_and_cardinality_fail_closed(self):
        for response in ({}, {'succeeded': False, 'result': {}}, {'error': 'bad'},
                         {'detailsOfElements': []}, {'detailsOfElements': [{}]},
                         {'result': {'error': 'bad'}}, {'detailsOfElements': 'bad'}):
            snap = snapshot_from_readback(response, ['wall'], self.s)
            self.assertIn('transportError', snap)
            self.assertEqual(audit_snapshot(snap, 'PASS_2_WALLS')['rules']['BIM-QA-001']['status'], 'BLOCKED_BY_TRANSPORT')

    def test_safe_bim_result_requires_matching_guids(self):
        operation = {'guids': ['wrong'], 'status': 'PASS', 'readbackResponse': {'detailsOfElements': [wall()]}}
        snap = snapshot_from_readback(operation, ['wall'], self.s)
        self.assertIn('transportError', snap)

    def test_real_sanitized_capture_remains_partial(self):
        capture = json.loads((Path(__file__).parent / 'fixtures' / 'tapir_readback_partial.json').read_text())
        rows = []
        for item in capture['captures']:
            adapted = snapshot_from_readback(item['response'], item['requestedGuids'], {})
            self.assertNotIn('transportError', adapted)
            rows.extend(adapted['elements'])
        s = {'projectId': 'historical-capture', 'snapshotId': 'historical', 'auditScope': 'partial', 'elements': rows}
        report = audit_snapshot(s, 'PASS_3_WINDOWS_DOORS')
        self.assertEqual(report['rules']['BIM-QA-002']['status'], 'NOT_VERIFIED')
        self.assertEqual([r['type'] for r in rows], ['Wall', 'Window', 'Window'])

    def dependency_fixture(self):
        rules = json.loads(RULES_PATH.read_text())
        outcomes = {r['id']: {'status': 'PASS'} for r in rules['rules']}
        audits = {p['id']: {**{k: self.s[k] for k in ('projectId', 'snapshotId', 'auditScope')},
                            'stage': p['id'], 'status': 'PASS', 'rules': copy.deepcopy(outcomes)}
                  for p in rules['pipeline']}
        return rules, outcomes, audits

    def test_dependency_positive_with_complete_external_audits(self):
        rules, outcomes, audits = self.dependency_fixture()
        self.assertEqual(_dependency(self.s, 'FINAL_BIM_AUDIT', audits, outcomes, rules)['status'], 'PASS')

    def test_dependency_every_nonpass_blocks_current_and_ancestors(self):
        for status in ('FAIL', 'NOT_VERIFIED', 'BLOCKED_BY_TRANSPORT', 'SUCCESS', None):
            for own in (True, False):
                rules, outcomes, audits = self.dependency_fixture()
                target = outcomes if own else audits['PASS_1_STORIES']['rules']
                target['BIM-QA-009'] = {'status': status}
                actual = _dependency(self.s, 'FINAL_BIM_AUDIT', audits, outcomes, rules)['status']
                self.assertEqual(actual, status if status in ('FAIL', 'BLOCKED_BY_TRANSPORT') else 'NOT_VERIFIED')

    def test_dependency_missing_result_cannot_hide_behind_pass_claim(self):
        rules, outcomes, audits = self.dependency_fixture()
        del audits['PASS_2_WALLS']['rules']['BIM-QA-001']
        self.assertEqual(_dependency(self.s, 'FINAL_BIM_AUDIT', audits, outcomes, rules)['status'], 'NOT_VERIFIED')

    def test_dependency_stale_wrong_project_scope_or_stage(self):
        for key in ('snapshotId', 'projectId', 'auditScope', 'stage'):
            rules, outcomes, audits = self.dependency_fixture()
            audits['PASS_1_STORIES'][key] = 'wrong'
            self.assertEqual(_dependency(self.s, 'PASS_2_WALLS', audits, outcomes, rules)['status'], 'NOT_VERIFIED')

    def test_unknown_stage(self):
        self.assertEqual(audit_snapshot(self.s, 'FAKE_STAGE')['status'], 'NOT_VERIFIED')

    def test_no_network_or_existing_runtime_mutation(self):
        before = copy.deepcopy(self.s)
        with patch('urllib.request.urlopen', side_effect=AssertionError('Network forbidden')):
            audit_snapshot(self.s, 'PASS_2_WALLS')
        self.assertEqual(self.s, before)


if __name__ == '__main__':
    unittest.main()
