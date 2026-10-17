"""No-native-call release and six-verifier receiver compatibility checks."""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys
import tempfile
from unittest import TestCase
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE/"scripts"))
import apa_ac29_dynamic_native_verifiers as REG

spec = importlib.util.spec_from_file_location(
    "six_verifier_receiver", HERE/"scripts"/"apa_ac29_autonomous_job_bridge.py")
WORKER = importlib.util.module_from_spec(spec)
spec.loader.exec_module(WORKER)


class RuntimeReceiptContract(TestCase):
    def test_exact_six_verifiers_and_no_unreviewed_commands(self):
        expected = {
            ("CreateColumns", "CREATE"), ("MoveElements", "MODIFY"),
            ("CreateBeams", "CREATE"), ("CreateWalls", "CREATE"),
            ("CreateRoofs", "CREATE"), ("ModifySlabs", "MODIFY")
        }
        entries = REG.installed_verifiers()
        self.assertEqual(len(entries), 6)
        self.assertEqual({(x.command, x.effect) for x in entries.values()}, expected)
        self.assertNotIn("CreateSlabs", {x.command for x in entries.values()})
        self.assertNotIn("APPROVED_DYNAMIC_CREATE", WORKER.ALLOWED)
        self.assertNotIn("APPROVED_DYNAMIC_MODIFY", WORKER.ALLOWED)

    def test_new_release_receipt_accepts_exact_six_verifier_module_hashes(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            (root/"controllers").mkdir()
            stamp = {
                "schema":"APA_AC29_RUNTIME_RELEASE_V1",
                "revision":"a"*40,
                "workerSHA256": WORKER.sha(Path(WORKER.__file__)),
                "moduleHashes": {
                    name:"b"*64 for name in (
                        set(WORKER.MODULE_HASHES) |
                        {"apa_ac29_dynamic_write_scopes.py",
                         "apa_ac29_dynamic_native_verifiers.py",
                         "apa_ac29_existing_create_verifiers.py",
                         "apa_ac29_existing_modify_verifiers.py",
                         "apa_ac29_reusable_native_copy.py",
                         "apa_ac29_multi_prototype_native_copy.py",
                         "apa_ac29_scene_reconciliation.py"})
                },
                "controllerHashes": {
                    name:"c"*64 for name in (
                        "apa_ac29_reusable_native_copy.py",
                        "apa_ac29_multi_prototype_native_copy.py",
                        "apa_ac29_scene_reconciliation.py")},
                "workingPlnSha256":"d"*64,
                "expectedGuidCount":298
            }
            report = root/"controllers"/"runtime-release.json"
            report.write_text(json.dumps(stamp))
            with patch.object(WORKER, "ROOT", root):
                self.assertEqual(
                    WORKER.runtime_release()["expectedGuidCount"], 298)
                stamp["moduleHashes"]["arbitrary_plugin.py"]="e"*64
                report.write_text(json.dumps(stamp))
                with self.assertRaisesRegex(ValueError,"RECEIPT_INVALID"):
                    WORKER.runtime_release()

    def test_release_bootstrap_requires_exact_existing_baseline(self):
        script = HERE/"scripts"/"release_apa_ac29_six_verifiers.py"
        compile(script.read_text(encoding="utf-8"),str(script),"exec")
        program = script.read_text(encoding="utf-8")
        self.assertIn("CURRENT_RELEASE = \"9cfe84c42db485a5ad536a38369de0b667e066f0\"",program)
        self.assertIn("EXPECTED_GUIDS = 298",program)
        self.assertIn("UPDATE_PREFLIGHT_PASS_NO_CHANGES",program)
        self.assertIn("old[\"workerSHA256\"] == sha(worker)",program)
        self.assertNotIn("CreateColumns(",program)
        self.assertNotIn("SaveProject(",program)
