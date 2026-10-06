import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from closed_loop.live_wall import LiveSession, load


def wall(guid, begin_x, end_x):
    return {
        'guid': guid, 'type': 'Wall', 'homeStory': 0,
        'placement': {'referenceGeometry': {
            'kind': 'WallReferenceLine',
            'begin': {'x': begin_x, 'y': 0.0},
            'end': {'x': end_x, 'y': 0.0},
            'arcAngle': 0, 'bottomOffsetFromHomeStory': 0.0,
            'height': 3.0, 'thickness': 0.3}},
        'bodies': []
    }


class FixtureBindingTests(unittest.TestCase):
    def session(self, project_path):
        session = LiveSession.__new__(LiveSession)
        session.identity = {'projectPath': project_path}
        session.chat = load('stage4_fixture_test_chat', 'scripts/archicad_chat_executor.py')
        return session

    def test_fixture_chain_returns_unique_current_endpoint_and_plans_from_it(self):
        project = r'C:\Users\Admin\Downloads\дбликат.pln'
        with tempfile.TemporaryDirectory() as temp:
            report = Path(temp)/'fixture-report.json'
            report.write_text(
                '{"status":"PASS","projectPath":"C:\\\\Users\\\\Admin\\\\Downloads\\\\дбликат.pln","seedGuid":"SEED"}',
                encoding='utf-8')
            data = {'stories':[{'index':0,'elevation':0.0}],
                'elements':[wall('SEED',0.0,0.5),wall('NEXT',0.5,1.5)],
                'unresolvedBodyOwners':[]}
            session = self.session(project)
            with patch.dict(os.environ, {'SAFE_BIM_STAGE4_FIXTURE_REPORT':str(report)}):
                endpoint = session.fixture_chain_source(data)
                self.assertEqual(endpoint['guid'],'NEXT')
                plan = session.bound_fixture_plan(data, .5)
                self.assertEqual(plan['status'],'PLANNED')
                self.assertEqual(plan['request']['sourceGuid'],'NEXT')

    def test_fixture_chain_ambiguity_fails_closed(self):
        project = r'C:\Users\Admin\Downloads\дбликат.pln'
        with tempfile.TemporaryDirectory() as temp:
            report = Path(temp)/'fixture-report.json'
            report.write_text(
                '{"status":"PASS","projectPath":"C:\\\\Users\\\\Admin\\\\Downloads\\\\дбликат.pln","seedGuid":"SEED"}',
                encoding='utf-8')
            data = {'stories':[{'index':0,'elevation':0.0}],
                'elements':[wall('SEED',0.0,0.5),wall('A',0.5,1.0),wall('B',0.5,1.25)],
                'unresolvedBodyOwners':[]}
            session = self.session(project)
            with patch.dict(os.environ, {'SAFE_BIM_STAGE4_FIXTURE_REPORT':str(report)}):
                with self.assertRaisesRegex(ValueError,'ambiguous'):
                    session.fixture_chain_source(data)


if __name__=='__main__':
    unittest.main()
