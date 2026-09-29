from __future__ import annotations

import unittest

from sync_bridge.control_status import build_control_status
from sync_bridge.host import TapirReadTransport


class FakeTapirBackend:
    def __init__(self, project, product=(29, 3000, 'RUS')):
        self.project = dict(project)
        self.product = product
        self.calls = []
        self.official_calls = []

    def _tapir(self, name):
        self.calls.append(name)
        return lambda params=None: dict(self.project)

    def _official(self, name):
        self.official_calls.append(name)
        return lambda: self.product


class S26ProjectNameTests(unittest.TestCase):
    def test_binding_exposes_display_name_without_project_path(self):
        backend = FakeTapirBackend({
            'projectPath': r'C:\Users\Secret\Test_House_WriteSandbox.pln',
            'projectName': 'Test_House_WriteSandbox',
            'isUntitled': False,
            'isTeamwork': False,
        })

        binding = TapirReadTransport(backend=backend).binding()

        self.assertEqual(binding['projectName'], 'Test_House_WriteSandbox')
        self.assertNotIn('projectPath', binding)
        self.assertNotIn(r'C:\Users\Secret', repr(binding))
        self.assertEqual(binding['applicationVersion'], '29')
        self.assertEqual(binding['applicationBuild'], '3000')
        self.assertEqual(binding['applicationLanguage'], 'RUS')
        self.assertEqual(backend.calls, ['GetProjectInfo'])
        self.assertEqual(backend.official_calls, ['GetProductInfo'])

    def test_control_snapshot_receives_name_without_local_path(self):
        backend = FakeTapirBackend({
            'projectPath': r'C:\Users\Secret\Test_House_WriteSandbox.pln',
            'projectName': 'Test_House_WriteSandbox',
            'isUntitled': False,
            'isTeamwork': False,
        })
        binding = TapirReadTransport(backend=backend).binding()

        snapshot = build_control_status({
            'hostStatus': 'S2_5_RUNTIME_BOOTSTRAP_IMPLEMENTED_NOT_LIVE_VERIFIED',
            'running': True,
            'dbPath': r'C:\Users\Secret\AppData\Local\SafeBIM\bridge.sqlite3',
            'pipeOpen': True,
            'credentialSource': 'none',
            'archicad': binding,
            'bridge': {
                'running': True,
                'version': '0.1.0',
                'protocolVersion': 1,
                'needsAuth': False,
                'connections': {
                    'ARCHICAD': {'status': 'CONNECTED', 'detail': 'archicad-default'},
                    'BRIDGE': {'status': 'CONNECTED', 'detail': 'named-pipe'},
                    'REMOTE': {'status': 'CONNECTING', 'detail': ''},
                    'AI': {'status': 'CONNECTING', 'detail': ''},
                },
                'archicadWriteApi': False,
                'leaseState': 'HELD',
                'ownership': 'NAMED_MUTEX',
                'sqliteLeaseRole': 'DIAGNOSTIC_ONLY',
            },
        })

        self.assertEqual(snapshot['project']['name'], 'Test_House_WriteSandbox')
        encoded = repr(snapshot)
        self.assertNotIn('.pln', encoded)
        self.assertNotIn(r'C:\Users', encoded)
        self.assertNotIn('projectPath', encoded)


if __name__ == '__main__':
    unittest.main()
