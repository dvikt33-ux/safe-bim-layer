"""Regression: failed PowerShell guard must not destroy local APA customizations."""
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import apa_recover_and_install_planner as repair


OLD = ("""\
# An existing locally customized APA writer.
UNIQUE_LOCAL_MODIFICATION = 'USER_KEPT_SETTINGS'

def native_command_router():
    return 1

def prepare_native_task():
    return 2

def run_native_task():
    return 3
""" + "# EXISTING USER LOCAL CONFIG KEEP\n" * 600).encode()

NEW = OLD + b"""
def prepare_optimized_native_task(router, intent, planner_python=None):
    from archicad_execution_optimizer import prepare_optimized_native_task as optimize
    return optimize(router, intent["request"], intent["strategies"], planner_python)

def run_optimized_native_task(router, api, optimized_preview, writer, scopes, checkpoint=None):
    return run_native_task()
"""

OPTIMIZER = b"# fake existing unchanged planner module\n"


class AdditiveRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        self.core = self.root / "archicad_project_accelerator.py"
        self.backup = self.root / "archicad_project_accelerator.py.planner-install.bak"
        self.optimizer = self.root / "archicad_execution_optimizer.py"
        self.expected = self.root / "upstream_core.py"
        self.expected_optimizer = self.root / "upstream_optimizer.py"
        self.backup.write_bytes(OLD)
        self.core.write_bytes(NEW)
        self.optimizer.write_bytes(OPTIMIZER)
        self.expected.write_bytes(NEW)
        self.expected_optimizer.write_bytes(OPTIMIZER)

    def invoke(self, **kw):
        return repair.install(self.root, self.expected, self.expected_optimizer,
                              smoke_import=False, **kw)

    def test_dry_run_has_zero_file_mutations(self):
        result = self.invoke()
        self.assertEqual(result["status"], "VALIDATED_RESTORE_AND_ADDITIVE_INSTALL")
        self.assertEqual(self.core.read_bytes(), NEW)
        self.assertEqual(self.backup.read_bytes(), OLD)
        self.assertFalse((self.root / "archicad_project_accelerator.py.planner-overwrite-before-repair.bak").exists())

    def test_patch_preserves_exact_original_prefix_and_functions(self):
        result = self.invoke(apply=True)
        self.assertEqual(result["status"], "LOCAL_APA_RESTORED_PLUS_PLANNER_WRAPPERS_INSTALLED")
        self.assertEqual(self.backup.read_bytes(), OLD)
        final = self.core.read_bytes()
        self.assertTrue(final.startswith(OLD))
        self.assertIn(b"USER_KEPT_SETTINGS", final)
        self.assertEqual(final.count(b"def prepare_optimized_native_task("), 1)
        self.assertEqual(final.count(b"def run_optimized_native_task("), 1)
        self.assertEqual(self.optimizer.read_bytes(), OPTIMIZER)
        self.assertEqual((self.root / "archicad_project_accelerator.py.planner-overwrite-before-repair.bak").read_bytes(), NEW)
        with self.assertRaisesRegex(ValueError, "CURRENT_LOCAL_APA_IS_NOT_EXACT_PINNED_OVERWRITE"):
            self.invoke(apply=True)

    def test_current_local_drift_blocks_without_any_changes(self):
        self.core.write_bytes(NEW+b"\n#user edit after install")
        with self.assertRaisesRegex(ValueError, "CURRENT_LOCAL_APA_IS_NOT_EXACT_PINNED_OVERWRITE"):
            self.invoke(apply=True)
        self.assertIn(b"#user edit after install", self.core.read_bytes())
        self.assertEqual(self.backup.read_bytes(), OLD)

    def test_missing_backup_or_optimizer_drift_blocks(self):
        self.backup.unlink()
        with self.assertRaisesRegex(ValueError, "REQUIRED_LOCAL_FILE_MISSING"):
            self.invoke(apply=True)
        self.backup.write_bytes(OLD)
        self.optimizer.write_bytes(OPTIMIZER+b"#modified")
        with self.assertRaisesRegex(ValueError, "INSTALLED_OPTIMIZER_DRIFT"):
            self.invoke(apply=True)
        self.assertEqual(self.core.read_bytes(), NEW)

    def test_double_wrappers_or_missing_native_executor_blocks(self):
        with self.assertRaisesRegex(ValueError, "ALREADY_HAS_PLANNER_WRAPPERS"):
            repair.additive_candidate(NEW, NEW)
        with self.assertRaisesRegex(ValueError, "MISSING_EXISTING_BIM_WRITER"):
            repair.additive_candidate(b"# no existing functions\n", NEW)


if __name__ == "__main__":
    unittest.main()
