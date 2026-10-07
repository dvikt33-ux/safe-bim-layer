import copy
import unittest

from bim_geometry_qa import audit_geometry_snapshot


def roof(guid):
    return {'guid': guid, 'type': 'Roof', 'details': {}}


def wall(guid='gable'):
    return {'guid': guid, 'type': 'Wall', 'details': {}}


def beam(guid='rafter'):
    return {'guid': guid, 'type': 'Beam', 'details': {'beamShape': 'Straight', 'arcAngle': 0.0}}


def fixture():
    return {
        'projectId': 'synthetic-project',
        'snapshotId': 'geometry-rev-1',
        'auditScope': 'pilot-gable',
        'inventoryComplete': True,
        'elements': [roof('roof-left'), roof('roof-right'), wall(), beam()],
        'roofTopologyComplete': True,
        'roofGuids': ['roof-left', 'roof-right'],
        'roofPairEvidenceComplete': True,
        'roofPairEvidence': [{
            'a': 'roof-left',
            'b': 'roof-right',
            'expectedRelation': 'RIDGE',
            'actualRelation': 'EDGE',
            'gapDistance': 0.0001,
            'gapTolerance': 0.001,
            'probeComplete': True,
        }],
        'wallRoofRelationsComplete': True,
        'roofAdjacentWallGuids': ['gable'],
        'wallRoofRelations': [{
            'wallGuid': 'gable',
            'roofGuids': ['roof-left', 'roof-right'],
            'operationKind': 'TRIM_TO_ROOF_SHELL',
            'operationApplied': True,
            'steppedFragments': False,
            'maxProtrusion': 0.0,
            'geometryVerified': True,
        }],
        'rafterEvidenceComplete': True,
        'rafterGuids': ['rafter'],
        'rafterEvidence': [{
            'beamGuid': 'rafter',
            'roofGuid': 'roof-left',
            'axisStart': {'x': 0, 'y': 0, 'z': 0},
            'axisEnd': {'x': 1, 'y': 0, 'z': 1},
            'bearingPoint': {'x': 0, 'y': 0, 'z': 0},
            'upperTargetPoint': {'x': 1, 'y': 0, 'z': 1},
            'roofPlanePoint': {'x': 0, 'y': 0, 'z': 0},
            'roofPlaneNormal': {'x': -1, 'y': 0, 'z': 1},
            'axisSource': 'BEAM_READBACK_RECONSTRUCTED',
            'roofPlaneSource': 'TRUSTED_GEOMETRY_COLLECTOR',
        }],
    }


class GeometryQATests(unittest.TestCase):
    def outcome(self, snapshot, rule):
        return audit_geometry_snapshot(snapshot)['rules'][rule]['status']

    def test_complete_reference_fragment_passes(self):
        report = audit_geometry_snapshot(fixture())
        self.assertEqual(report['status'], 'PASS')
        for rule in ('BIM-QA-004', 'BIM-QA-005', 'BIM-QA-006', 'BIM-QA-007'):
            self.assertEqual(report['rules'][rule]['status'], 'PASS')

    def test_transport_failure_blocks_all(self):
        s = fixture()
        s['geometryTransportError'] = 'collector timeout'
        report = audit_geometry_snapshot(s)
        self.assertEqual(report['status'], 'BLOCKED_BY_TRANSPORT')
        self.assertTrue(all(v['status'] == 'BLOCKED_BY_TRANSPORT' for v in report['rules'].values()))

    def test_roof_area_overlap_fails_collision(self):
        s = fixture()
        s['roofPairEvidence'][0]['actualRelation'] = 'AREA_OVERLAP'
        self.assertEqual(self.outcome(s, 'BIM-QA-004'), 'FAIL')

    def test_roof_volume_overlap_fails_collision(self):
        s = fixture()
        s['roofPairEvidence'][0]['actualRelation'] = 'VOLUME_OVERLAP'
        self.assertEqual(self.outcome(s, 'BIM-QA-004'), 'FAIL')

    def test_unintended_touch_of_disjoint_roofs_fails_collision(self):
        s = fixture()
        s['roofPairEvidence'][0]['expectedRelation'] = 'DISJOINT'
        s['roofPairEvidence'][0]['actualRelation'] = 'POINT'
        self.assertEqual(self.outcome(s, 'BIM-QA-004'), 'FAIL')

    def test_missing_roof_pair_is_not_verified(self):
        s = fixture()
        s['elements'].append(roof('roof-third'))
        s['roofGuids'].append('roof-third')
        self.assertEqual(self.outcome(s, 'BIM-QA-004'), 'NOT_VERIFIED')
        self.assertEqual(self.outcome(s, 'BIM-QA-005'), 'NOT_VERIFIED')

    def test_duplicate_pair_is_not_verified(self):
        s = fixture()
        s['roofPairEvidence'].append(copy.deepcopy(s['roofPairEvidence'][0]))
        self.assertEqual(self.outcome(s, 'BIM-QA-004'), 'NOT_VERIFIED')

    def test_ridge_gap_fails(self):
        s = fixture()
        s['roofPairEvidence'][0]['actualRelation'] = 'DISJOINT'
        s['roofPairEvidence'][0]['gapDistance'] = 0.05
        self.assertEqual(self.outcome(s, 'BIM-QA-005'), 'FAIL')

    def test_excessive_gap_tolerance_is_not_verified(self):
        s = fixture()
        s['roofPairEvidence'][0]['gapTolerance'] = 0.5
        self.assertEqual(self.outcome(s, 'BIM-QA-005'), 'NOT_VERIFIED')

    def test_point_touch_can_be_explicitly_expected(self):
        s = fixture()
        s['roofPairEvidence'][0].update(
            expectedRelation='POINT_TOUCH', actualRelation='POINT', gapDistance=0.0
        )
        self.assertEqual(self.outcome(s, 'BIM-QA-004'), 'PASS')
        self.assertEqual(self.outcome(s, 'BIM-QA-005'), 'PASS')

    def test_stepped_gable_fails_wall_top(self):
        s = fixture()
        s['wallRoofRelations'][0]['steppedFragments'] = True
        self.assertEqual(self.outcome(s, 'BIM-QA-006'), 'FAIL')

    def test_missing_trim_operation_fails_wall_top(self):
        s = fixture()
        s['wallRoofRelations'][0]['operationKind'] = 'MANUAL_STACKED_WALLS'
        self.assertEqual(self.outcome(s, 'BIM-QA-006'), 'FAIL')

    def test_wall_protrusion_fails(self):
        s = fixture()
        s['wallRoofRelations'][0]['maxProtrusion'] = 0.05
        self.assertEqual(self.outcome(s, 'BIM-QA-006'), 'FAIL')

    def test_unverified_wall_geometry_is_not_verified(self):
        s = fixture()
        s['wallRoofRelations'][0]['geometryVerified'] = False
        self.assertEqual(self.outcome(s, 'BIM-QA-006'), 'NOT_VERIFIED')

    def test_wall_relation_must_cover_all_adjacent_walls(self):
        s = fixture()
        s['elements'].append(wall('gable-2'))
        s['roofAdjacentWallGuids'].append('gable-2')
        self.assertEqual(self.outcome(s, 'BIM-QA-006'), 'NOT_VERIFIED')

    def test_rafter_off_roof_plane_fails(self):
        s = fixture()
        s['rafterEvidence'][0]['axisEnd']['z'] = 1.2
        self.assertEqual(self.outcome(s, 'BIM-QA-007'), 'FAIL')

    def test_rafter_wrong_bearing_or_upper_target_fails(self):
        s = fixture()
        s['rafterEvidence'][0]['upperTargetPoint'] = {'x': 2, 'y': 0, 'z': 2}
        self.assertEqual(self.outcome(s, 'BIM-QA-007'), 'FAIL')

    def test_rafter_wrong_element_type_fails(self):
        s = fixture()
        next(row for row in s['elements'] if row['guid'] == 'rafter')['type'] = 'Morph'
        self.assertEqual(self.outcome(s, 'BIM-QA-007'), 'FAIL')

    def test_rafter_geometry_source_is_required(self):
        s = fixture()
        del s['rafterEvidence'][0]['axisSource']
        self.assertEqual(self.outcome(s, 'BIM-QA-007'), 'NOT_VERIFIED')

    def test_curved_beam_fails_rafter_rule(self):
        s = fixture()
        details = next(row for row in s['elements'] if row['guid'] == 'rafter')['details']
        details['beamShape'] = 'HorizontallyCurved'
        self.assertEqual(self.outcome(s, 'BIM-QA-007'), 'FAIL')

    def test_missing_inventory_is_not_verified(self):
        s = fixture()
        s['inventoryComplete'] = False
        self.assertEqual(audit_geometry_snapshot(s)['status'], 'NOT_VERIFIED')


if __name__ == '__main__':
    unittest.main()
