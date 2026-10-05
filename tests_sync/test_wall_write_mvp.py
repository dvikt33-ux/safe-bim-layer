"""Offline tests for the typed chat->bridge->Archicad Wall write MVP."""
from __future__ import annotations

import copy
import unittest

from sync_bridge.wall_write import ContinueWallExecutor, RECIPE


SOURCE_GUID = '5D743058-EAEF-4DB9-BB12-00F6D62E0813'
CREATED_GUID = 'CCA6E865-2393-4DDA-B75B-223555F196B2'
MATERIAL_GUID = '922C639B-9875-48DF-A3FC-E0A8AC5F2839'


def wall_row(guid, begin, end):
    return {
        'type': 'Wall',
        'floorIndex': 0,
        'details': {
            'geometryType': 'Straight',
            'arcAngle': 0,
            'structureType': 'Basic',
            'zCoordinate': 0,
            'begCoordinate': dict(begin),
            'endCoordinate': dict(end),
            'height': 12,
            'bottomOffset': 0,
            'offset': 0,
            'flipped': True,
            'begThickness': 0.25,
            'endThickness': 0.25,
            'buildingMaterialId': {'guid': MATERIAL_GUID},
            'referenceLineLocation': 'Center',
        },
        '_testGuid': guid,
    }


def expected_source():
    return {
        'floorIndex': 0,
        'begCoordinate': {'x': 60.0, 'y': 0.0},
        'endCoordinate': {'x': 60.0, 'y': 30.0},
        'zCoordinate': 0.0,
        'height': 12.0,
        'begThickness': 0.25,
        'endThickness': 0.25,
        'offset': 0.0,
        'buildingMaterialGuid': MATERIAL_GUID,
    }


def job(**overrides):
    value = {
        'recipe': RECIPE,
        'instanceId': 'archicad-default',
        'logicalProjectId': 'live-local-project',
        'sourceGuid': SOURCE_GUID,
        'sourceEndpoint': 'end',
        'lengthMeters': 0.25,
        'expectedSource': expected_source(),
    }
    value.update(overrides)
    return value


class FakeTransport:
    def __init__(self, *, binding=None, write_error=None, created=None, source=None):
        self.binding_value = binding or {
            'instanceId': 'archicad-default',
            'logicalProjectId': 'live-local-project',
        }
        self.write_error = write_error
        self.source = copy.deepcopy(source or wall_row(
            SOURCE_GUID, {'x': 60.0, 'y': 0.0}, {'x': 60.0, 'y': 30.0}))
        self.created = copy.deepcopy(created or wall_row(
            CREATED_GUID, {'x': 60.0, 'y': 30.0}, {'x': 60.0, 'y': 30.25}))
        self.read_calls = []
        self.write_calls = []

    def binding(self):
        return dict(self.binding_value)

    def call(self, command, params):
        self.read_calls.append((command, copy.deepcopy(params)))
        if command != 'GetDetailsOfElements':
            raise AssertionError(command)
        rows = params['elements']
        if len(rows) == 1:
            return {'detailsOfElements': [copy.deepcopy(self.source)]}
        if len(rows) == 2:
            return {'detailsOfElements': [
                copy.deepcopy(self.source), copy.deepcopy(self.created)]}
        raise AssertionError(params)

    def write_call(self, command, params):
        self.write_calls.append((command, copy.deepcopy(params)))
        if self.write_error is not None:
            raise self.write_error
        return {'elements': [{'elementId': {'guid': CREATED_GUID}}]}


class ContinueWallExecutorTests(unittest.TestCase):
    def test_success_derives_createwalls_and_requires_factual_readback(self):
        fake = FakeTransport()
        result = ContinueWallExecutor(fake).execute(job())

        self.assertEqual(result['status'], 'PASS')
        self.assertEqual(result['createdGuid'], CREATED_GUID)
        self.assertTrue(result['verification']['pass'])
        self.assertEqual(len(fake.write_calls), 1)
        command, params = fake.write_calls[0]
        self.assertEqual(command, 'CreateWalls')
        wall = params['wallsData'][0]
        self.assertEqual(wall['begCoordinate'], {'x': 60.0, 'y': 30.0})
        self.assertEqual(wall['endCoordinate'], {'x': 60.0, 'y': 30.25})
        self.assertEqual(wall['floorIndex'], 0)
        self.assertEqual(wall['height'], 12.0)
        self.assertEqual(wall['thickness'], 0.25)
        self.assertEqual(
            wall['buildingMaterialId']['guid'], MATERIAL_GUID)
        self.assertEqual(len(fake.read_calls), 2)
        self.assertFalse(result['automaticRetry'])

    def test_stale_source_blocks_before_write(self):
        changed = wall_row(
            SOURCE_GUID, {'x': 60.0, 'y': 0.0}, {'x': 60.0, 'y': 31.0})
        fake = FakeTransport(source=changed)
        result = ContinueWallExecutor(fake).execute(job())

        self.assertEqual(result['status'], 'BLOCKED')
        self.assertEqual(result['stage'], 'STALE_SOURCE')
        self.assertFalse(result['mutationApplied'])
        self.assertEqual(fake.write_calls, [])

    def test_wrong_project_identity_blocks_before_read_or_write(self):
        fake = FakeTransport(binding={
            'instanceId': 'archicad-default',
            'logicalProjectId': 'different-project',
        })
        result = ContinueWallExecutor(fake).execute(job())

        self.assertEqual(result['status'], 'BLOCKED')
        self.assertEqual(result['stage'], 'BINDING')
        self.assertEqual(fake.read_calls, [])
        self.assertEqual(fake.write_calls, [])

    def test_write_transport_loss_is_unknown_outcome_and_never_retryable(self):
        fake = FakeTransport(write_error=TimeoutError('lost reply'))
        result = ContinueWallExecutor(fake).execute(job())

        self.assertEqual(result['status'], 'UNKNOWN_OUTCOME')
        self.assertEqual(result['stage'], 'CREATE_WALLS')
        self.assertIsNone(result['mutationApplied'])
        self.assertFalse(result['automaticRetry'])
        self.assertEqual(len(fake.write_calls), 1)

    def test_readback_loss_after_returned_guid_is_unknown_outcome(self):
        class ReadbackFail(FakeTransport):
            def call(self, command, params):
                if len(params['elements']) == 2:
                    raise TimeoutError('readback lost')
                return super().call(command, params)

        fake = ReadbackFail()
        result = ContinueWallExecutor(fake).execute(job())

        self.assertEqual(result['status'], 'UNKNOWN_OUTCOME')
        self.assertEqual(result['stage'], 'READ_BACK')
        self.assertEqual(result['createdGuid'], CREATED_GUID)
        self.assertTrue(result['mutationApplied'])
        self.assertFalse(result['automaticRetry'])

    def test_arbitrary_recipe_and_extra_fields_fail_closed(self):
        fake = FakeTransport()
        invalid = job(recipe='raw_tapir_command')
        result = ContinueWallExecutor(fake).execute(invalid)
        self.assertEqual(result['status'], 'BLOCKED')
        self.assertEqual(result['stage'], 'VALIDATION')
        self.assertEqual(fake.write_calls, [])

        fake = FakeTransport()
        invalid = job()
        invalid['command'] = 'DeleteElements'
        result = ContinueWallExecutor(fake).execute(invalid)
        self.assertEqual(result['status'], 'BLOCKED')
        self.assertEqual(result['stage'], 'VALIDATION')
        self.assertEqual(fake.write_calls, [])

    def test_extension_length_is_bounded(self):
        fake = FakeTransport()
        result = ContinueWallExecutor(fake).execute(job(lengthMeters=1000.0))
        self.assertEqual(result['status'], 'BLOCKED')
        self.assertEqual(result['stage'], 'VALIDATION')
        self.assertEqual(fake.write_calls, [])


if __name__ == '__main__':
    unittest.main()
