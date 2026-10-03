import copy
import unittest

from bim_coordination_qa import audit_coordination_snapshot


def verified_rule(rule_id, parameters, source_kind='NORMATIVE'):
    base = {
        'id': rule_id,
        'status': 'VERIFIED',
        'sourceKind': source_kind,
        'verifiedAt': '2026-10-03',
        'parameters': parameters,
    }
    if source_kind == 'NORMATIVE':
        base.update({
            'document': 'TEST-NORM',
            'edition': '2026',
            'clause': '1.1',
        })
    else:
        base.update({
            'basis': 'Approved project coordination rule',
            'approved': True,
        })
    return base


def base_snapshot():
    rules = [
        verified_rule('R-ROOF', {'minimumOverhang': 0.30}, 'PROJECT'),
        verified_rule('R-JOIN', {'maxGap': 0.002}, 'PROJECT'),
        verified_rule('R-SUPPORT', {'minSupportRatio': 0.90, 'maxHorizontalOffset': 0.02}, 'PROJECT'),
        verified_rule('R-WALL-OPENING', {'minClearance': 0.10}),
        verified_rule('R-CLEAR', {
            'windowCornerMin': 0.38,
            'doorWallMin': 0.13,
            'pierMin': 0.51,
        }),
        verified_rule('R-MASONRY', {
            'moduleStep': 0.13,
            'moduleTolerance': 0.002,
            'allowedResidues': [0.0],
        }, 'PROJECT'),
    ]
    return {
        'projectId': 'project',
        'snapshotId': 'rev-1',
        'auditScope': 'pilot',
        'inventoryComplete': True,
        'elements': [
            {'guid': 'ext', 'type': 'Wall', 'details': {}},
            {'guid': 'int', 'type': 'Wall', 'details': {}},
            {'guid': 'upper', 'type': 'Wall', 'details': {}},
            {'guid': 'lower', 'type': 'Wall', 'details': {}},
            {'guid': 'roof', 'type': 'Roof', 'details': {}},
            {'guid': 'win', 'type': 'Window', 'details': {'ownerElementId': {'guid': 'ext'}}},
            {'guid': 'door', 'type': 'Door', 'details': {'ownerElementId': {'guid': 'ext'}}},
        ],
        'ruleRegistryComplete': True,
        'ruleRegistry': rules,
        'roofCoverageComplete': True,
        'roofCoverageEvidence': [{
            'id': 'roof-ext',
            'wallGuid': 'ext',
            'roofGuid': 'roof',
            'probeSource': 'TRUSTED_GEOMETRY_COLLECTOR',
            'probeComplete': True,
            'actualOverhang': 0.35,
            'ruleId': 'R-ROOF',
            'parameter': 'minimumOverhang',
        }],
        'wallJunctionsComplete': True,
        'wallJunctions': [{
            'id': 'int-ext',
            'a': 'int',
            'b': 'ext',
            'expectedKind': 'T',
            'actualConnected': True,
            'gapDistance': 0.001,
            'probeComplete': True,
            'ruleId': 'R-JOIN',
            'parameter': 'maxGap',
        }],
        'loadBearingSupportComplete': True,
        'loadBearingSupportEvidence': [{
            'upperWallGuid': 'upper',
            'supportKind': 'WALL',
            'supportGuid': 'lower',
            'supportRatio': 0.95,
            'horizontalOffset': 0.01,
            'probeComplete': True,
            'ruleId': 'R-SUPPORT',
        }],
        'wallOpeningConflictComplete': True,
        'wallOpeningConflictEvidence': [{
            'id': 'int-vs-win',
            'approachWallGuid': 'int',
            'openingGuid': 'win',
            'intersectsOpening': False,
            'clearDistance': 0.20,
            'probeComplete': True,
            'ruleId': 'R-WALL-OPENING',
            'parameter': 'minClearance',
        }],
        'openingClearanceComplete': True,
        'openingClearanceEvidence': [
            {
                'id': 'win-corner',
                'openingGuid': 'win',
                'relationKind': 'WINDOW_TO_CORNER',
                'measuredDistance': 0.52,
                'probeComplete': True,
                'ruleId': 'R-CLEAR',
                'parameter': 'windowCornerMin',
            },
            {
                'id': 'door-wall',
                'openingGuid': 'door',
                'relationKind': 'DOOR_TO_WALL',
                'measuredDistance': 0.20,
                'probeComplete': True,
                'ruleId': 'R-CLEAR',
                'parameter': 'doorWallMin',
            },
            {
                'id': 'pier',
                'openingGuid': 'win',
                'neighborGuid': 'door',
                'relationKind': 'PIER_WIDTH',
                'measuredDistance': 0.65,
                'probeComplete': True,
                'ruleId': 'R-CLEAR',
                'parameter': 'pierMin',
            },
        ],
        'masonryModuleComplete': True,
        'masonryModuleEvidence': [
            {
                'id': 'pier-module',
                'wallGuid': 'ext',
                'openingGuid': 'win',
                'dimensionKind': 'PIER_WIDTH',
                'measuredValue': 0.65,
                'probeComplete': True,
                'ruleId': 'R-MASONRY',
            },
        ],
    }


class CoordinationQATests(unittest.TestCase):
    def outcome(self, s, rule):
        return audit_coordination_snapshot(s)['rules'][rule]

    def test_complete_fixture_passes(self):
        report = audit_coordination_snapshot(base_snapshot())
        self.assertEqual(report['status'], 'PASS')
        self.assertEqual(report['checkerId'], 'SAFE_BIM_COORDINATION_QA_V1')
        self.assertTrue(all(r['status'] == 'PASS' for r in report['rules'].values()))

    def test_roof_not_reaching_wall_fails(self):
        s = base_snapshot()
        s['roofCoverageEvidence'][0]['actualOverhang'] = 0.20
        self.assertEqual(self.outcome(s, 'BIM-QA-012')['status'], 'FAIL')

    def test_wall_gap_fails(self):
        s = base_snapshot()
        s['wallJunctions'][0]['actualConnected'] = False
        s['wallJunctions'][0]['gapDistance'] = 0.015
        self.assertEqual(self.outcome(s, 'BIM-QA-013')['status'], 'FAIL')

    def test_loadbearing_wall_not_over_support_fails(self):
        s = base_snapshot()
        s['loadBearingSupportEvidence'][0]['supportRatio'] = 0.40
        s['loadBearingSupportEvidence'][0]['horizontalOffset'] = 0.30
        self.assertEqual(self.outcome(s, 'BIM-QA-014')['status'], 'FAIL')

    def test_wrong_support_type_fails(self):
        s = base_snapshot()
        s['elements'][3]['type'] = 'Beam'
        self.assertEqual(self.outcome(s, 'BIM-QA-014')['status'], 'FAIL')

    def test_unapproved_transfer_structure_fails(self):
        s = base_snapshot()
        item = s['loadBearingSupportEvidence'][0]
        item['supportKind'] = 'TRANSFER_STRUCTURE'
        self.assertEqual(self.outcome(s, 'BIM-QA-014')['status'], 'FAIL')
        item['transferException'] = {
            'approved': True,
            'reason': 'Designed transfer beam system',
            'reviewedBy': 'structural-reviewer',
        }
        self.assertEqual(self.outcome(s, 'BIM-QA-014')['status'], 'PASS')

    def test_wall_through_window_fails(self):
        s = base_snapshot()
        s['wallOpeningConflictEvidence'][0]['intersectsOpening'] = True
        self.assertEqual(self.outcome(s, 'BIM-QA-015')['status'], 'FAIL')

    def test_wall_too_close_to_opening_fails(self):
        s = base_snapshot()
        s['wallOpeningConflictEvidence'][0]['clearDistance'] = 0.02
        self.assertEqual(self.outcome(s, 'BIM-QA-015')['status'], 'FAIL')

    def test_window_corner_clearance_fails(self):
        s = base_snapshot()
        s['openingClearanceEvidence'][0]['measuredDistance'] = 0.20
        self.assertEqual(self.outcome(s, 'BIM-QA-016')['status'], 'FAIL')

    def test_door_to_wall_clearance_fails(self):
        s = base_snapshot()
        s['openingClearanceEvidence'][1]['measuredDistance'] = 0.05
        self.assertEqual(self.outcome(s, 'BIM-QA-016')['status'], 'FAIL')

    def test_pier_width_fails(self):
        s = base_snapshot()
        s['openingClearanceEvidence'][2]['measuredDistance'] = 0.30
        self.assertEqual(self.outcome(s, 'BIM-QA-016')['status'], 'FAIL')

    def test_masonry_module_mismatch_fails(self):
        s = base_snapshot()
        s['masonryModuleEvidence'][0]['measuredValue'] = 0.61
        self.assertEqual(self.outcome(s, 'BIM-QA-017')['status'], 'FAIL')

    def test_module_residue_can_be_explicitly_allowed(self):
        s = base_snapshot()
        masonry = next(r for r in s['ruleRegistry'] if r['id'] == 'R-MASONRY')
        masonry['parameters']['allowedResidues'] = [0.0, 0.065]
        s['masonryModuleEvidence'][0]['measuredValue'] = 0.585
        self.assertEqual(self.outcome(s, 'BIM-QA-017')['status'], 'PASS')

    def test_no_hardcoded_clearance_threshold(self):
        s = base_snapshot()
        clear = next(r for r in s['ruleRegistry'] if r['id'] == 'R-CLEAR')
        s['openingClearanceEvidence'][0]['measuredDistance'] = 0.30
        self.assertEqual(self.outcome(s, 'BIM-QA-016')['status'], 'FAIL')
        clear['parameters']['windowCornerMin'] = 0.25
        self.assertEqual(self.outcome(s, 'BIM-QA-016')['status'], 'PASS')

    def test_missing_rule_is_data_missing_not_pass(self):
        s = base_snapshot()
        s['openingClearanceEvidence'][0]['ruleId'] = 'MISSING'
        outcome = self.outcome(s, 'BIM-QA-016')
        self.assertEqual(outcome['status'], 'NOT_VERIFIED')
        self.assertEqual(outcome['reasonCode'], 'DATA_MISSING')

    def test_unverified_rule_is_data_missing(self):
        s = base_snapshot()
        next(r for r in s['ruleRegistry'] if r['id'] == 'R-CLEAR')['status'] = 'DRAFT'
        report = audit_coordination_snapshot(s)
        self.assertEqual(report['status'], 'NOT_VERIFIED')
        self.assertEqual(report['rules']['BIM-QA-012']['reasonCode'], 'DATA_MISSING')

    def test_normative_rule_requires_document_edition_clause(self):
        s = base_snapshot()
        entry = next(r for r in s['ruleRegistry'] if r['id'] == 'R-CLEAR')
        del entry['clause']
        report = audit_coordination_snapshot(s)
        self.assertEqual(report['status'], 'NOT_VERIFIED')
        self.assertEqual(report['rules']['BIM-QA-016']['reasonCode'], 'DATA_MISSING')

    def test_project_rule_requires_approved_basis(self):
        s = base_snapshot()
        entry = next(r for r in s['ruleRegistry'] if r['id'] == 'R-MASONRY')
        entry['approved'] = False
        report = audit_coordination_snapshot(s)
        self.assertEqual(report['status'], 'NOT_VERIFIED')

    def test_incomplete_evidence_never_passes(self):
        flags = (
            'roofCoverageComplete',
            'wallJunctionsComplete',
            'loadBearingSupportComplete',
            'wallOpeningConflictComplete',
            'openingClearanceComplete',
            'masonryModuleComplete',
        )
        rules = (
            'BIM-QA-012', 'BIM-QA-013', 'BIM-QA-014',
            'BIM-QA-015', 'BIM-QA-016', 'BIM-QA-017',
        )
        for flag, rule in zip(flags, rules):
            with self.subTest(flag=flag):
                s = base_snapshot()
                s[flag] = False
                self.assertEqual(self.outcome(s, rule)['status'], 'NOT_VERIFIED')

    def test_transport_failure_blocks_every_rule(self):
        s = base_snapshot()
        s['coordinationTransportError'] = 'collector unavailable'
        report = audit_coordination_snapshot(s)
        self.assertEqual(report['status'], 'BLOCKED_BY_TRANSPORT')
        self.assertTrue(all(r['status'] == 'BLOCKED_BY_TRANSPORT' for r in report['rules'].values()))

    def test_wrong_element_type_fails(self):
        s = base_snapshot()
        next(e for e in s['elements'] if e['guid'] == 'roof')['type'] = 'Morph'
        self.assertEqual(self.outcome(s, 'BIM-QA-012')['status'], 'FAIL')


if __name__ == '__main__':
    unittest.main()
