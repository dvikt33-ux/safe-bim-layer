import copy
import unittest

from bim_qa import attach_bounding_boxes, attach_story_inventory, _story_assignment
from tests.test_bim_qa_policy_v11 import base_snapshot


class TapirStoryEvidenceTests(unittest.TestCase):
    def stories(self):
        return {'succeeded': True, 'result': {'addOnCommandResponse': {
            'firstStory': 0, 'lastStory': 1, 'actStory': 0, 'skipNullFloor': False,
            'stories': [{'index': 0, 'floorId': 1, 'level': 0, 'name': 'Ground'},
                        {'index': 1, 'floorId': 2, 'level': 3, 'name': 'First'}]}}}

    def test_story_response_validates_full_range_and_not_empty_success(self):
        response = self.stories()
        self.assertTrue(attach_story_inventory({}, response)['storiesComplete'])
        response['result']['addOnCommandResponse']['stories'].pop()
        attached = attach_story_inventory({}, response)
        self.assertFalse(attached['storiesComplete'])
        self.assertIn('storyTransportError', attached)

    def test_story_response_error_is_retained_as_transport_failure(self):
        for response in ({'succeeded': False}, {'error': 'timeout'},
                         {'result': {'addOnCommandResponse': {'error': 'API failure'}}}):
            attached = attach_story_inventory({}, response)
            self.assertFalse(attached['storiesComplete'])
            self.assertEqual(_story_assignment(attached, {})['status'], 'BLOCKED_BY_TRANSPORT')

    def test_missing_or_duplicate_story_inventory_never_passes(self):
        for stories in ([], [{'index': 0, 'level': 0, 'name': 'A'}, {'index': 0, 'level': 1, 'name': 'B'}]):
            response = self.stories()
            payload = response['result']['addOnCommandResponse']
            payload['firstStory'] = payload['lastStory'] = 0
            payload['stories'] = stories
            self.assertFalse(attach_story_inventory({}, response)['storiesComplete'])

    def test_bbox_rows_bind_to_exact_request_order_without_mutating_source(self):
        snapshot = base_snapshot()
        before = copy.deepcopy(snapshot)
        response = {'boundingBoxes3D': [
            {'boundingBox3D': {'xMin': 0, 'xMax': 7, 'yMin': 0, 'yMax': .38, 'zMin': 0, 'zMax': 3.2}}]}
        attached = attach_bounding_boxes(snapshot, response, ['wall'])
        self.assertTrue(attached['boundingBoxesComplete'])
        self.assertEqual(attached['elements'][0]['boundingBox3D']['zMin'], 0)
        self.assertEqual(snapshot, before)

    def test_bbox_cardinality_or_error_blocks(self):
        snapshot = attach_story_inventory(base_snapshot(), self.stories())
        for response, guids in (({'boundingBoxes3D': []}, ['wall']),
                                ({'boundingBoxes3D': [{'error': 'missing'}]}, ['wall']),
                                ({'succeeded': False}, ['wall'])):
            attached = attach_bounding_boxes(snapshot, response, guids)
            self.assertFalse(attached['boundingBoxesComplete'])
            self.assertEqual(_story_assignment(attached, {'wall': attached['elements'][0]})['status'], 'BLOCKED_BY_TRANSPORT')

    def test_absolute_base_uses_actual_box_zmin(self):
        snapshot = base_snapshot()
        snapshot['stories'] = [{'index': 0, 'level': 0.0, 'name': 'Ground'}]
        snapshot['storiesComplete'] = True
        snapshot['boundingBoxesComplete'] = True
        snapshot['storyIntents'][0]['storyLevel'] = 0.0
        snapshot['elements'][0]['boundingBox3D'] = {
            'xMin': 0, 'xMax': 7, 'yMin': 0, 'yMax': .38, 'zMin': .25, 'zMax': 3.45}
        self.assertEqual(_story_assignment(snapshot, {'wall': snapshot['elements'][0]})['status'], 'FAIL')

    def test_story_level_must_match_intended_level(self):
        snapshot = base_snapshot()
        snapshot['stories'] = [{'index': 0, 'level': 3.0, 'name': 'Ground'}]
        snapshot['storyIntents'][0]['storyLevel'] = 0.0
        snapshot['storyIntents'][0]['elevationMode'] = 'STORY_ONLY'
        self.assertEqual(_story_assignment(snapshot, {'wall': snapshot['elements'][0]})['status'], 'FAIL')


if __name__ == '__main__':
    unittest.main()
