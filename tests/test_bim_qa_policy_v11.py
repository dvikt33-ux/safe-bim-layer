import json
import unittest

from bim_qa import (
    RULES_PATH,
    _element_economy,
    _story_assignment,
    attach_story_inventory,
    audit_snapshot,
)


def wall(guid='wall', floor=0, z=0.0):
    return {
        'guid': guid,
        'type': 'Wall',
        'floorIndex': floor,
        'details': {
            'geometryType': 'Straight',
            'arcAngle': 0.0,
            'begCoordinate': {'x': 0.0, 'y': 0.0},
            'endCoordinate': {'x': 7.0, 'y': 0.0},
            'zCoordinate': z,
            'height': 3.2,
        },
    }


def base_snapshot():
    return {
        'projectId': 'synthetic-project',
        'snapshotId': 'synthetic-revision-2',
        'auditScope': 'pilot',
        'inventoryComplete': True,
        'elements': [dict(wall(), boundingBox3D={
            'xMin': 0.0, 'xMax': 7.0, 'yMin': 0.0, 'yMax': 0.38, 'zMin': 0.0, 'zMax': 3.2})],
        'storiesComplete': True,
        'stories': [{'index': 0, 'level': 0.0, 'name': 'Ground'}],
        'boundingBoxesComplete': True,
        'controlledInventoryComplete': True,
        'controlledGuids': ['wall'],
        'storyIntentsComplete': True,
        'storyIntents': [{
            'guid': 'wall',
            'floorIndex': 0,
            'storyLevel': 0.0,
            'elevationMode': 'ABSOLUTE_BASE',
            'baseElevation': 0.0,
        }],
        'elementEconomyComplete': True,
        'elementEconomyIntents': [{
            'id': 'house/front/gable-wall',
            'semanticRole': 'gable wall',
            'guids': ['wall'],
            'maxElementCount': 1,
            'strategyKind': 'NATIVE_OPERATION',
            'operationName': 'TrimElementsToRoofShell',
        }],
    }


class StoryAssignmentTests(unittest.TestCase):
    def test_story_and_absolute_base_pass(self):
        s = base_snapshot()
        index = {row['guid']: row for row in s['elements']}
        self.assertEqual(_story_assignment(s, index)['status'], 'PASS')

    def test_wrong_story_fails(self):
        s = base_snapshot()
        s['elements'][0]['floorIndex'] = 1
        index = {row['guid']: row for row in s['elements']}
        self.assertEqual(_story_assignment(s, index)['status'], 'FAIL')

    def test_wrong_absolute_base_fails(self):
        s = base_snapshot()
        s['elements'][0]['boundingBox3D'] = {
            'xMin': 0, 'xMax': 7, 'yMin': 0, 'yMax': .38, 'zMin': .25, 'zMax': 3.45}
        index = {row['guid']: row for row in s['elements']}
        self.assertEqual(_story_assignment(s, index)['status'], 'FAIL')

    def test_story_only_does_not_invent_base_elevation(self):
        s = base_snapshot()
        s['storyIntents'][0] = {
            'guid': 'wall',
            'floorIndex': 0,
            'storyLevel': 0.0,
            'elevationMode': 'STORY_ONLY',
        }
        del s['elements'][0]['details']['zCoordinate']
        index = {row['guid']: row for row in s['elements']}
        self.assertEqual(_story_assignment(s, index)['status'], 'PASS')

    def test_missing_story_evidence_is_not_verified(self):
        for key in ('storyIntentsComplete', 'storyIntents', 'controlledInventoryComplete'):
            s = base_snapshot()
            del s[key]
            index = {row['guid']: row for row in s['elements']}
            self.assertEqual(_story_assignment(s, index)['status'], 'NOT_VERIFIED')

    def test_missing_actual_floor_is_not_verified(self):
        s = base_snapshot()
        del s['elements'][0]['floorIndex']
        index = {row['guid']: row for row in s['elements']}
        self.assertEqual(_story_assignment(s, index)['status'], 'NOT_VERIFIED')


class ElementEconomyTests(unittest.TestCase):
    def outcome(self, s):
        index = {row['guid']: row for row in s['elements']}
        return _element_economy(s, index)

    def test_one_wall_plus_trim_passes(self):
        self.assertEqual(self.outcome(base_snapshot())['status'], 'PASS')

    def test_gable_made_of_many_walls_fails(self):
        s = base_snapshot()
        s['elements'] = [wall('wall-1'), wall('wall-2'), wall('wall-3')]
        s['controlledGuids'] = ['wall-1', 'wall-2', 'wall-3']
        s['elementEconomyIntents'][0]['guids'] = list(s['controlledGuids'])
        self.assertEqual(self.outcome(s)['status'], 'FAIL')

    def test_real_construction_exception_can_allow_multiple_elements(self):
        s = base_snapshot()
        s['elements'] = [wall('wall-1'), wall('wall-2')]
        s['controlledGuids'] = ['wall-1', 'wall-2']
        intent = s['elementEconomyIntents'][0]
        intent['guids'] = list(s['controlledGuids'])
        intent['fragmentationException'] = {
            'category': 'construction',
            'reason': 'Independent structural movement joint',
            'reviewedBy': 'fixture-reviewer',
            'approved': True,
        }
        self.assertEqual(self.outcome(s)['status'], 'PASS')

    def test_api_limitation_is_not_automatic_permission_to_fragment(self):
        s = base_snapshot()
        s['elements'] = [wall('wall-1'), wall('wall-2')]
        s['controlledGuids'] = ['wall-1', 'wall-2']
        intent = s['elementEconomyIntents'][0]
        intent['guids'] = list(s['controlledGuids'])
        intent['fragmentationException'] = {
            'category': 'api_limitation',
            'reason': 'Transport cannot execute trim',
            'reviewedBy': 'fixture-reviewer',
            'approved': True,
        }
        self.assertEqual(self.outcome(s)['status'], 'FAIL')
        intent['fragmentationException']['fallbackReviewed'] = True
        self.assertEqual(self.outcome(s)['status'], 'PASS')

    def test_visual_or_script_convenience_is_never_valid_exception(self):
        for category in ('visual', 'opening', 'gable', 'script_simplification', 'convenience'):
            with self.subTest(category=category):
                s = base_snapshot()
                s['elements'] = [wall('wall-1'), wall('wall-2')]
                s['controlledGuids'] = ['wall-1', 'wall-2']
                intent = s['elementEconomyIntents'][0]
                intent['guids'] = list(s['controlledGuids'])
                intent['fragmentationException'] = {
                    'category': category,
                    'reason': 'easier',
                    'reviewedBy': 'fixture-reviewer',
                    'approved': True,
                }
                self.assertEqual(self.outcome(s)['status'], 'FAIL')

    def test_native_operation_requires_operation_name(self):
        s = base_snapshot()
        del s['elementEconomyIntents'][0]['operationName']
        self.assertEqual(self.outcome(s)['status'], 'NOT_VERIFIED')

    def test_missing_or_incomplete_economy_contract_is_not_verified(self):
        for key in ('elementEconomyComplete', 'elementEconomyIntents', 'controlledInventoryComplete'):
            s = base_snapshot()
            del s[key]
            self.assertEqual(self.outcome(s)['status'], 'NOT_VERIFIED')

    def test_economy_contract_must_cover_controlled_inventory_exactly(self):
        s = base_snapshot()
        s['elements'].append({
            'guid': 'slab',
            'type': 'Slab',
            'floorIndex': 0,
            'details': {},
        })
        s['controlledGuids'].append('slab')
        self.assertEqual(self.outcome(s)['status'], 'NOT_VERIFIED')

    def test_porch_native_operation_example_passes(self):
        s = base_snapshot()
        s['elements'] = [{
            'guid': 'porch-slab',
            'type': 'Slab',
            'floorIndex': 0,
            'details': {},
        }]
        s['controlledGuids'] = ['porch-slab']
        s['elementEconomyIntents'] = [{
            'id': 'house/porch/platform',
            'semanticRole': 'porch platform',
            'guids': ['porch-slab'],
            'maxElementCount': 1,
            'strategyKind': 'NATIVE_OPERATION',
            'operationName': 'SlabPolygonSubtract',
        }]
        self.assertEqual(self.outcome(s)['status'], 'PASS')

    def test_many_small_porch_slabs_fail_when_one_is_approved_representation(self):
        s = base_snapshot()
        s['elements'] = [
            {'guid': f'porch-{i}', 'type': 'Slab', 'floorIndex': 0, 'details': {}}
            for i in range(5)
        ]
        s['controlledGuids'] = [row['guid'] for row in s['elements']]
        s['elementEconomyIntents'] = [{
            'id': 'house/porch/platform',
            'semanticRole': 'porch platform',
            'guids': list(s['controlledGuids']),
            'maxElementCount': 1,
            'strategyKind': 'NATIVE_OPERATION',
            'operationName': 'SlabPolygonSubtract',
        }]
        self.assertEqual(self.outcome(s)['status'], 'FAIL')


class IntegrationMetadataTests(unittest.TestCase):
    def test_008_and_011_are_implemented_offline_but_not_live_verified(self):
        rules = json.loads(RULES_PATH.read_text(encoding='utf-8'))['rules']
        by_id = {rule['id']: rule for rule in rules}
        for rule_id in ('BIM-QA-008', 'BIM-QA-011'):
            self.assertEqual(by_id[rule_id]['implementationState'], 'IMPLEMENTED_OFFLINE')
            self.assertEqual(by_id[rule_id]['liveValidationState'], 'NOT_VERIFIED')

    def test_audit_exposes_new_rules_and_dependency_sees_them(self):
        s = base_snapshot()
        s.update({
            'openingIntentsComplete': True,
            'openingIntents': [],
            'wallSystemsComplete': True,
            'wallSystems': [{
                'id': 'gable',
                'guids': ['wall'],
                'begCoordinate': {'x': 0.0, 'y': 0.0},
                'endCoordinate': {'x': 7.0, 'y': 0.0},
                'floorIndex': 0,
                'zCoordinate': 0.0,
                'height': 3.2,
            }],
            'identityRegistryComplete': True,
            'identityRegistry': [{
                'guid': 'wall',
                'entityId': 'entity-wall',
                'role': 'house/front/gable-wall',
                'identityScope': 'pilot',
            }],
            'operationJournalComplete': True,
            'operationJournal': [{
                'operationId': 'op-1',
                'status': 'DONE',
                'guids': ['wall'],
            }],
        })
        s = attach_story_inventory(s, {
            'succeeded': True, 'result': {'addOnCommandResponse': {
                'firstStory': 0, 'lastStory': 0,
                'stories': [{'index': 0, 'level': 0.0, 'name': 'Ground'}]}}})
        s['boundingBoxesComplete'] = True
        s['storyIntents'][0]['storyLevel'] = 0.0
        report = audit_snapshot(s, 'PASS_2_WALLS')
        self.assertEqual(report['rules']['BIM-QA-008']['status'], 'PASS')
        self.assertEqual(report['rules']['BIM-QA-011']['status'], 'PASS')
        self.assertEqual(report['status'], 'NOT_VERIFIED')


if __name__ == '__main__':
    unittest.main()
