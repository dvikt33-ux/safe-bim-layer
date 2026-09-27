import unittest

from safe_bim_layer import StoryResolver, VerticalContext, preflight_plinth_geometry


class StoriesTapir:
    def call(self, command, payload):
        assert command == 'GetStories'
        return {'result': {'addOnCommandResponse': {'stories': [
            {'index': 0, 'name': 'Ground / пользовательское', 'level': 0.0},
            {'index': 1, 'name': 'Высокий торговый', 'level': 4.5},
            {'index': 2, 'name': 'Технический', 'level': 8.2},
            {'index': 3, 'name': 'Типовой', 'level': 11.2},
        ]}}}


class StoryVerticalTests(unittest.TestCase):
    def test_resolves_factual_elevations_and_variable_heights(self):
        stories = StoryResolver(StoriesTapir(), 0.0).resolve()
        self.assertEqual([s.height_to_next for s in stories[:1]], [4.5])
        self.assertAlmostEqual(stories[1].height_to_next, 3.7)
        self.assertEqual([s.height_to_next for s in stories[2:]], [3.0, None])
        self.assertEqual(StoryResolver(StoriesTapir()).by_index(2).elevation, 8.2)

    def test_names_do_not_affect_identity(self):
        story = StoryResolver(StoriesTapir()).by_index(1)
        self.assertEqual(story.story_index, 1)
        self.assertEqual(story.elevation, 4.5)

    def test_context_keeps_grade_and_plinth_separate(self):
        ctx = VerticalContext(0.0, grade_z=-1.5, plinth_bottom_z=-1.5,
                              plinth_top_z=0.0, source='confirmed brief')
        self.assertNotEqual(ctx.grade_z, ctx.project_zero_z)
        self.assertEqual(ctx.plinth_top_z, ctx.project_zero_z)

    def test_plinth_preflight_fails_closed_without_geometry_write(self):
        result = preflight_plinth_geometry(VerticalContext(
            0.0, grade_z=-0.6, plinth_bottom_z=-0.6, plinth_top_z=0.0,
            source='live audit'))
        self.assertEqual(result['status'], 'UNSUPPORTED_LIVE_GEOMETRY')
        self.assertFalse(result['writeAllowed'])
        self.assertEqual(result['expectedZFingerprint']['plinth_bottom_z'], -0.6)


if __name__ == '__main__':
    unittest.main()
