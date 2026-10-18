"""Pure/offline safety regression for the controller-only one-time updater."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import unittest

TARGET=Path(__file__).resolve().parents[1]/"scripts"/"install_apa_ap2_same_receiver_readonly.py"
spec=importlib.util.spec_from_file_location("installer_guard",TARGET)
I=importlib.util.module_from_spec(spec)
spec.loader.exec_module(I)

class TestSafeUpgrade(unittest.TestCase):
    def test_bdd_route_must_be_byte_identical(self):
        new=I.SOURCE.read_text(encoding="utf8")
        old=new.replace("AP2_READONLY_PROJECT_INVENTORY","OLD_NO_AP2")
        I.compare_source_guards(old,new)
        changed=old.replace(
            'INBOX = "safe-bim-mailbox/apa-ac29/jobs"',
            'INBOX = "safe-bim-mailbox/unreviewed/jobs"')
        with self.assertRaisesRegex(RuntimeError,
                                    "ORIGINAL_WORKER_TARGET_OR_QUEUE_CHANGED"):
            I.compare_source_guards(changed,new)

    def test_upgrade_rejects_target_already_updated(self):
        new=I.SOURCE.read_text(encoding="utf8")
        with self.assertRaisesRegex(RuntimeError,
                                    "AP2_NEW_CONTROLLER_IS_NOT_BOUNDED"):
            I.compare_source_guards(new,new)

    def test_no_pln_or_core_mutation_apis(self):
        src=TARGET.read_text(encoding="utf8")
        self.assertNotIn("CreateWalls",src)
        self.assertNotIn("CreateColumns",src)
        self.assertNotIn("ModifyWalls",src)
        self.assertNotIn(".unlink()",src)
        self.assertIn("EXISTING_APA_RECEIVERS",src.replace("RECEIVER","RECEIVERS") if "EXISTING_APA_RECEIVER" in src else "EXISTING_APA_RECEIVERS")
        self.assertIn("RECEIVER_NEW_BYTES_READBACK_FAILED",src)

if __name__=="__main__":
    unittest.main()
