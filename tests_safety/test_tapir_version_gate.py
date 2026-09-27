import json
import unittest
from unittest.mock import patch

from safe_bim_layer import SafeBIMError, TapirClient
from safe_bim_operations import SafeBIMOperations
from tests_safety.fake_bim import WALL, FakeBIM


class _Response:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.payload


class VersionGateTests(unittest.TestCase):
    def test_mismatch_blocks_executor_write(self):
        fake = FakeBIM()
        fake.addon_version = '1.5.8'
        with self.assertRaises(SafeBIMError):
            SafeBIMOperations(fake).execute('create_wall_loop', WALL)
        self.assertEqual(fake.dispatches, [])
        self.assertNotIn('CreateWalls', [command for command, _, _ in fake.calls])

    def test_missing_or_unparseable_version_blocks_write(self):
        fake = FakeBIM()
        fake.addon_version = None
        with self.assertRaises(SafeBIMError):
            SafeBIMOperations(fake).execute('create_wall_loop', WALL)
        self.assertEqual(fake.dispatches, [])

        fake = FakeBIM()
        fake.on_call = lambda command, payload: {'version': '1.5.9'} if command == 'GetAddOnVersion' else None
        with self.assertRaises(SafeBIMError):
            SafeBIMOperations(fake).execute('create_wall_loop', WALL)
        self.assertEqual(fake.dispatches, [])

    def test_matching_version_allows_one_existing_dispatch(self):
        fake = FakeBIM()
        result = SafeBIMOperations(fake).execute('create_wall_loop', WALL)
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual(len(fake.dispatches), 1)
        self.assertEqual(fake.dispatches[0][0], 'CreateWalls')

    def test_direct_client_does_not_send_a_write_when_version_is_wrong(self):
        seen = []

        def urlopen(req, timeout=120):
            body = json.loads(req.data.decode())
            name = body['parameters']['addOnCommandId']['commandName']
            seen.append(name)
            return _Response({'succeeded': True, 'result': {'addOnCommandResponse': {'version': '1.5.8'}}})

        with patch('urllib.request.urlopen', side_effect=urlopen):
            with self.assertRaises(SafeBIMError):
                TapirClient().call('CreateWalls', {'wallsData': []})
        self.assertEqual(seen, ['GetAddOnVersion'])


if __name__ == '__main__':
    unittest.main()
