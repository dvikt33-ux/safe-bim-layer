from __future__ import annotations

import unittest

from sync_bridge.write_bridge import TapirJobExecutor


INSTANCE = 'archicad-19723'
PROJECT = 'live-local-testproject'


def job(command='CreateWalls', params=None):
    return {
        'requestId': 'req-1',
        'instanceId': INSTANCE,
        'logicalProjectId': PROJECT,
        'command': command,
        'params': params if params is not None else {},
    }


class FakeTransport:
    def __init__(self):
        self.calls = []
        self.timeout_on = None
        self.project = PROJECT

    def binding(self):
        return {
            'instanceId': INSTANCE,
            'logicalProjectId': self.project,
        }

    def execute(self, command, params):
        self.calls.append((command, params))
        if self.timeout_on == command:
            raise TimeoutError(command)
        if command == 'CreateWalls':
            return {
                'elements': [
                    {'elementId': {'guid': 'AAAAAAAA-BBBB-CCCC-DDDD-EEEEEEEEEEEE'}}
                ]
            }
        if command == 'GetDetailsOfElements':
            return {
                'detailsOfElements': [
                    {
                        'type': 'Wall',
                        'floorIndex': 0,
                        'details': {'height': 3.0, 'thickness': 0.44},
                    }
                ]
            }
        if command == 'Get3DBoundingBoxes':
            return {
                'boundingBoxes3D': [
                    {
                        'boundingBox3D': {
                            'xMin': 0.0, 'xMax': 4.0,
                            'yMin': -0.22, 'yMax': 0.22,
                            'zMin': 0.0, 'zMax': 3.0,
                        }
                    }
                ]
            }
        return {'executionResults': [{'success': True}]}


class MailboxWriteExecutorTests(unittest.TestCase):
    def test_write_executes_and_reads_back(self):
        transport = FakeTransport()
        executor = TapirJobExecutor(transport)
        result = executor.execute(job('CreateWalls', {'wallsData': [{}]}))

        self.assertEqual(result['status'], 'SUCCESS')
        self.assertTrue(result['success'])
        self.assertEqual(
            result['affectedElementGuids'],
            ['AAAAAAAA-BBBB-CCCC-DDDD-EEEEEEEEEEEE'],
        )
        self.assertEqual(
            [name for name, _params in transport.calls],
            ['CreateWalls', 'GetDetailsOfElements', 'Get3DBoundingBoxes'],
        )
        self.assertEqual(result['verification']['mode'], 'GUID_READBACK')

    def test_unknown_command_fails_closed_without_transport_call(self):
        transport = FakeTransport()
        executor = TapirJobExecutor(transport)
        result = executor.execute(job('RunArbitraryPython'))

        self.assertEqual(result['status'], 'FAILED')
        self.assertEqual(result['error']['code'], 'UNSUPPORTED_COMMAND')
        self.assertEqual(transport.calls, [])

    def test_write_timeout_is_unknown_outcome_and_not_retried(self):
        transport = FakeTransport()
        transport.timeout_on = 'CreateWalls'
        executor = TapirJobExecutor(transport)
        result = executor.execute(job('CreateWalls', {'wallsData': [{}]}))

        self.assertEqual(result['status'], 'UNKNOWN_OUTCOME')
        self.assertEqual(result['error']['code'], 'TIMEOUT')
        self.assertEqual(len(transport.calls), 1)

    def test_project_change_fails_before_mutation(self):
        transport = FakeTransport()
        transport.project = 'different-project'
        executor = TapirJobExecutor(transport)
        result = executor.execute(job('CreateWalls', {'wallsData': [{}]}))

        self.assertEqual(result['status'], 'FAILED')
        self.assertEqual(result['error']['code'], 'PROJECT_MISMATCH')
        self.assertEqual(transport.calls, [])


if __name__ == '__main__':
    unittest.main()
