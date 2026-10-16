"""Short tests for additive update preservation, rollback and drift guards."""
import ast
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import apa_update_strategy_discovery as U


class AdditiveUpdate(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)/'installed'; self.root.mkdir()
        self.source = Path(self.tmp.name)/'source'; self.source.mkdir()
        self.core = b'# LOCAL CUSTOM CORE PRESERVE ALL BYTES\n'+b'\n'.join(
            ('def '+name+'(*args): pass').encode() for name in (
                'prepare_auto_optimized_native_task', 'run_auto_optimized_native_task',
                'prepare_native_task', 'run_native_task'))+b'\n'
        self.dynamic = b'# LOCAL CUSTOM PREFIX\nclass DynamicCommands:\n    @staticmethod\n    def plan_reuse_existing(existing, targets):\n        return "V1"\n\n    def local_only_feature(self):\n        return "PRESERVE"\n# LOCAL CUSTOM SUFFIX\n'
        self.old_module = b'def old_feature(): return 1\n'
        (self.root/'archicad_project_accelerator.py').write_bytes(self.core)
        (self.root/'archicad_dynamic_commands.py').write_bytes(self.dynamic)
        (self.root/'archicad_strategy_discovery.py').write_bytes(self.old_module)
        (self.source/'archicad_dynamic_commands.py').write_bytes(self.dynamic.replace(b'return "V1"', b'return "INTEGRATED"'))
        (self.source/'archicad_strategy_discovery.py').write_bytes(b'def discover_catalog_task(): pass\ndef catalog_capabilities(): pass\n')
        self.p1 = patch.object(U, 'V1_MODULE', U.digest(self.old_module)); self.p1.start(); self.addCleanup(self.p1.stop)
        self.p2 = patch.object(U, 'V1_METHOD_SOURCE', U.method(self.dynamic)[1]); self.p2.start(); self.addCleanup(self.p2.stop)

    def test_update_preserves_custom_core_and_other_dynamic_bytes_then_rollback(self):
        report = U.install(self.root, self.source, apply=True, smoke=lambda _: None)
        self.assertTrue(report['applied'])
        self.assertEqual((self.root/'archicad_project_accelerator.py').read_bytes(), self.core)
        self.assertEqual((self.root/'archicad_dynamic_commands.py').read_bytes(),
                         self.dynamic.replace(b'return "V1"', b'return "INTEGRATED"'))
        U.rollback(report['receipt'])
        self.assertEqual((self.root/'archicad_dynamic_commands.py').read_bytes(), self.dynamic)
        self.assertEqual((self.root/'archicad_strategy_discovery.py').read_bytes(), self.old_module)

    def test_failed_import_smoke_restores_both_files(self):
        def fail(_): raise RuntimeError('SIMULATED_IMPORT_FAILURE')
        with self.assertRaisesRegex(RuntimeError, 'SIMULATED_IMPORT_FAILURE'):
            U.install(self.root, self.source, apply=True, smoke=fail)
        self.assertEqual((self.root/'archicad_dynamic_commands.py').read_bytes(), self.dynamic)
        self.assertEqual((self.root/'archicad_strategy_discovery.py').read_bytes(), self.old_module)

    def test_existing_local_adapter_changes_are_not_overwritten(self):
        p = self.root/'archicad_strategy_discovery.py'; p.write_bytes(self.old_module+b'# LOCAL EDIT\n')
        with self.assertRaisesRegex(ValueError, 'NO_OVERWRITE'):
            U.install(self.root, self.source, apply=True, smoke=lambda _: None)
        self.assertFalse((self.root/'.apa-discovery-updates').exists())


if __name__ == '__main__': unittest.main()
