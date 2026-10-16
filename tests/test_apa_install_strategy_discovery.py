"""Safety tests: never overwrite the user's recovered local APA source."""
from __future__ import annotations

import hashlib
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import apa_install_strategy_discovery as installer


LOCAL=(r'''
LOCAL_CUSTOMIZED_RUN_SETTINGS = "MUST_STAY_EXACTLY"

def prepare_optimized_native_task(router,intent,planner_python=None):
    return "local-original-optimized-task"

def run_native_task(router,api,preview,writer,scopes,checkpoint=None):
    return "original-SceneWriter"
''' + "# custom local APA action preserved\n"*800).encode()


class LocalAutoDiscoveryInstallTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.core=self.root/"archicad_project_accelerator.py"
        self.adapter=self.root/"archicad_execution_optimizer.py"
        self.localbackup=self.root/"archicad_project_accelerator.py.planner-install.bak"
        self.module=ROOT/"scripts"/"archicad_strategy_discovery.py"
        self.core.write_bytes(LOCAL)
        self.adapter.write_text("# pinned engine module, no real model writes",encoding="utf8")
        self.localbackup.write_text("protected older local source",encoding="utf8")

    def run_install(self, apply=False, expected=None):
        return installer.install(
            self.root,self.module,
            expected_sha=expected or hashlib.sha256(LOCAL).hexdigest(),
            apply=apply, smoke=False)

    def test_dry_run_leaves_every_file_unchanged(self):
        result=self.run_install()
        self.assertEqual(result["status"],"AUTO_DISCOVERY_ADDITIVE_PREFLIGHT_PASS")
        self.assertTrue(result["sourcePreservedByteForByte"])
        self.assertEqual(self.core.read_bytes(),LOCAL)
        self.assertFalse((self.root/"archicad_strategy_discovery.py").exists())
        self.assertFalse((self.root/"archicad_project_accelerator.py.before-auto-discovery.bak").exists())

    def test_install_preserves_old_core_bytes_and_immutable_old_backup(self):
        result=self.run_install(apply=True)
        self.assertEqual(result["status"],"AUTO_DISCOVERY_INSTALLED_WITH_ORIGINAL_APA_PRESERVED")
        patched=self.core.read_bytes()
        self.assertTrue(patched.startswith(LOCAL))
        self.assertIn(b'LOCAL_CUSTOMIZED_RUN_SETTINGS = "MUST_STAY_EXACTLY"',patched)
        self.assertEqual(patched.count(b"def prepare_auto_optimized_native_task("),1)
        self.assertEqual(patched.count(b"def run_auto_optimized_native_task("),1)
        self.assertEqual((self.root/"archicad_project_accelerator.py.before-auto-discovery.bak").read_bytes(),LOCAL)
        self.assertEqual(self.localbackup.read_text(encoding="utf8"),"protected older local source")
        self.assertEqual((self.root/"archicad_strategy_discovery.py").read_bytes(),self.module.read_bytes())
        with self.assertRaisesRegex(ValueError,"ALREADY_INSTALLED_OR_PREVIOUS_ATTEMPT"):
            self.run_install(apply=True)

    def test_local_drift_blocks_before_any_mutation(self):
        self.core.write_bytes(LOCAL+b"# user changed after previous install")
        with self.assertRaisesRegex(ValueError,"LOCAL_APA_HASH_DRIFT_NO_OVERWRITE"):
            self.run_install(apply=True)
        self.assertTrue(self.core.read_bytes().endswith(b"# user changed after previous install"))
        self.assertFalse((self.root/"archicad_strategy_discovery.py").exists())

    def test_missing_first_stage_adapter_and_backup_blocks(self):
        self.adapter.unlink()
        with self.assertRaisesRegex(ValueError,"LOCAL_RECOVERED_APA_AND_SOLVER_ADAPTER_REQUIRED"):
            self.run_install(apply=True)

    def test_existing_module_blocks_before_any_mutation(self):
        (self.root/"archicad_strategy_discovery.py").write_text("custom file",encoding="utf8")
        with self.assertRaisesRegex(ValueError,"ALREADY_INSTALLED_OR_PREVIOUS_ATTEMPT"):
            self.run_install(apply=True)
        self.assertEqual(self.core.read_bytes(),LOCAL)


if __name__=="__main__":
    unittest.main()
