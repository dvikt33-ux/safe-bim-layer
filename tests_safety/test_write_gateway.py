"""Offline proof of the single mutation gateway. No network and no Archicad."""
import ast
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from safe_bim_command_policy import CommandClass, classify
from safe_bim_layer import SafeBIMError, SafeBIMLayer, TapirClient
from safe_bim_operations import SafeBIMOperations
from safe_bim_runtime import JobStatus, ResumableExecutor, SQLiteCheckpointStore, StepSpec
from safe_bim_service import DEFAULT_SCHEMA
from tests_safety.fake_bim import PLINTH, PROJECT, WALL, FakeBIM


ROOT = Path(__file__).resolve().parents[1]
PRODUCTION_SKIP = {
    'tests_safety', 'tests_house_primitives', 'offline_reference', 'bimexec',
}
ALLOWED_MUTATION_FILES = {'safe_bim_mutation_gateway.py'}


class ClassificationTests(unittest.TestCase):
    def test_required_table(self):
        reads = (
            'GetAddOnVersion', 'GetProjectInfo', 'GetStories',
            'GetDetailsOfElements', 'GetElementsByType',
        )
        for name in reads:
            self.assertEqual(classify(name), CommandClass.READ_ONLY)
        self.assertEqual(classify('CreateWalls'), CommandClass.MODEL_MUTATION)
        self.assertEqual(classify('CreateSlabs'), CommandClass.MODEL_MUTATION)
        self.assertEqual(classify('ModifySlabs'), CommandClass.MODEL_MUTATION)
        self.assertEqual(classify('DeleteElements'), CommandClass.MODEL_MUTATION)
        self.assertEqual(classify('OpenProject'), CommandClass.SESSION_MUTATION)
        self.assertEqual(classify('ChangeWindow'), CommandClass.SESSION_MUTATION)
        self.assertEqual(classify('SaveProject'), CommandClass.SESSION_MUTATION)
        self.assertEqual(classify('SetLibraries'), CommandClass.ATTRIBUTE_MUTATION)
        self.assertEqual(classify('TrimElements'), CommandClass.MODEL_MUTATION)
        self.assertEqual(classify('SomeFutureTapirCommand'), CommandClass.UNKNOWN)
        self.assertNotEqual(classify('SomeFutureTapirCommand'), CommandClass.READ_ONLY)
        self.assertNotEqual(classify('GetAllElements'), CommandClass.READ_ONLY)

    def test_prefix_is_not_permission(self):
        self.assertEqual(classify('CreateNotInSnapshot'), CommandClass.UNKNOWN)
        self.assertEqual(classify('GetNotAllowlisted'), CommandClass.UNKNOWN)


class SchemaAndPublicCallTests(unittest.TestCase):
    def test_service_default_schema_is_159(self):
        self.assertEqual(DEFAULT_SCHEMA, 'tapir-1.5.9.json')
        text = (ROOT / 'safe_bim_service.py').read_text(encoding='utf-8')
        self.assertNotIn('tapir-1.5.8.json', text)

    def test_schema_158_with_runtime_159_denies_mutation(self):
        fake = FakeBIM()
        fake.schema = json.loads((ROOT / 'tapir-1.5.8.json').read_text(encoding='utf-8'))
        fake.addon_version = '1.5.9'
        with self.assertRaises(SafeBIMError):
            SafeBIMOperations(fake).execute('create_plinth_segment', PLINTH)
        self.assertEqual(fake.dispatches, [])

    def test_public_call_refuses_mutations_without_http(self):
        seen = []

        def urlopen(req, timeout=120):
            seen.append(req)
            raise AssertionError('public call must not open a socket')

        client = TapirClient(schema_path=str(ROOT / 'tapir-1.5.9.json'))
        with patch('urllib.request.urlopen', side_effect=urlopen):
            for command in ('CreateWalls', 'OpenProject', 'DeleteElements', 'SetLibraries',
                            'TrimElements', 'SaveProject', 'ChangeWindow', 'SomeFutureTapirCommand'):
                with self.assertRaises(SafeBIMError):
                    client.call(command, {})
        self.assertEqual(seen, [])

    def test_direct_transport_without_permit_is_refused(self):
        fake = FakeBIM()
        with self.assertRaises(SafeBIMError):
            fake.transport('CreateWalls', {'wallsData': [{}]})
        self.assertEqual(fake.dispatches, [])


class OneItemCreateTests(unittest.TestCase):
    def test_two_item_create_is_denied_before_transport(self):
        fake = FakeBIM()
        result = SafeBIMLayer(fake).create_wall_loop(
            [{'x': 0, 'y': 0}, {'x': 2, 'y': 0}, {'x': 2, 'y': 2}, {'x': 0, 'y': 2}],
            0, 3.0, 0.25)
        self.assertNotEqual(result['status'], 'PASS')
        self.assertEqual(fake.dispatches, [])
        self.assertNotIn('CreateWalls', [name for name, _, _ in fake.calls])

    def test_one_item_create_can_be_admitted(self):
        fake = FakeBIM()
        result = SafeBIMOperations(fake).execute('create_plinth_segment', PLINTH)
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual(len(fake.dispatches), 1)
        self.assertEqual(len(fake.dispatches[0][1]['wallsData']), 1)

    def test_wall_loop_becomes_one_item_resumable_steps(self):
        folder = ROOT / 'tests_safety'
        import tempfile
        from pathlib import Path as P
        with tempfile.TemporaryDirectory() as directory:
            fake = FakeBIM()
            ops = SafeBIMOperations(fake)
            store = SQLiteCheckpointStore(P(directory) / 'job.sqlite3')
            store.create_job('job', 'loop', PROJECT, [StepSpec('loop', 'create_wall_loop', WALL, 0)])
            ex = ResumableExecutor(store, ops.execute, ops.reconcile, ops.current_project)
            self.assertEqual(ex.run('job'), JobStatus.DONE)
            steps = store.job('job')['steps']
            self.assertGreater(len(steps), 1)
            self.assertTrue(all(step['operation'] == 'create_wall_segment' for step in steps))
            self.assertEqual(len(fake.dispatches), len(steps))
            self.assertTrue(all(len(item[1]['wallsData']) == 1 for item in fake.dispatches))

    def test_second_wall_failure_keeps_first_receipt_and_does_not_retry(self):
        import tempfile
        from pathlib import Path as P
        with tempfile.TemporaryDirectory() as directory:
            fake = FakeBIM()
            seen = {'n': 0}

            def created(command, guids):
                seen['n'] += 1
                if seen['n'] == 2:
                    raise TimeoutError('lost after second wall')

            fake.on_created = created
            ops = SafeBIMOperations(fake)
            store = SQLiteCheckpointStore(P(directory) / 'job.sqlite3')
            store.create_job('job', 'loop', PROJECT, [StepSpec('loop', 'create_wall_loop', WALL, 0)])
            ex = ResumableExecutor(store, ops.execute, ops.reconcile, ops.current_project)
            self.assertEqual(ex.run('job'), JobStatus.UNKNOWN_OUTCOME)
            steps = store.job('job')['steps']
            self.assertEqual(steps[0]['status'], 'DONE')
            self.assertTrue(steps[0]['result']['readbackVerified'])
            self.assertEqual(steps[1]['status'], 'UNKNOWN_OUTCOME')
            self.assertFalse(steps[1]['result'].get('retryAllowed', False))
            self.assertEqual(steps[2]['status'], 'PENDING')
            self.assertEqual(len(fake.dispatches), 2)
            self.assertNotIn('DeleteElements', [name for name, _, _ in fake.calls])
            fake.on_created = lambda *_: None
            self.assertEqual(ex.resume('job'), JobStatus.WAITING_USER)
            self.assertEqual(len(fake.dispatches), 2)


class StaticEscapeTests(unittest.TestCase):
    def test_production_sources_have_no_direct_mutation_call(self):
        violations = []
        for path in ROOT.rglob('*.py'):
            if any(part in PRODUCTION_SKIP or part == 'palette' for part in path.parts):
                continue
            if path.name.startswith('test_'):
                continue
            if path.name in ALLOWED_MUTATION_FILES:
                continue
            violations.extend(_mutation_calls(path))
        self.assertEqual(violations, [])


def _mutation_calls(path: Path):
    tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr not in {'call', 'transport', 'change_floor_plan', 'change_floor_plan_navigator_item'}:
            continue
        if not node.args:
            found.append(f'{path.name}:{node.lineno}: bare {node.func.attr}')
            continue
        arg = node.args[0]
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            if classify(arg.value) != CommandClass.READ_ONLY:
                found.append(f'{path.name}:{node.lineno}: {node.func.attr}({arg.value})')
        else:
            found.append(f'{path.name}:{node.lineno}: non-constant {node.func.attr}')
    return found


if __name__ == '__main__':
    unittest.main()
