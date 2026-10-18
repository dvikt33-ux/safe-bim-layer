"""Pure/offline safety regression for the controller-only one-time updater."""
from __future__ import annotations
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import json
import tempfile
from unittest.mock import patch
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

    def process(self, pid, ppid, loop=True):
        cmd=f'"C:\\LocalAI\\APA_AC29_Stable\\venv\\Scripts\\python.exe" -u "{I.WORKER}"'
        if loop: cmd+=' --loop'
        return {"ProcessId": pid, "ParentProcessId": ppid, "CommandLine": cmd}

    def test_one_receiver_with_parent_and_child_is_valid(self):
        processes=[self.process(600, 99),self.process(601, 600)]
        fake=SimpleNamespace(processes=lambda worker: list(processes))
        self.assertEqual(I.worker_processes(fake), processes)

    def test_two_unrelated_receiver_roots_are_blocked(self):
        processes=[self.process(600, 99),self.process(701, 100)]
        fake=SimpleNamespace(processes=lambda worker: processes)
        with self.assertRaisesRegex(RuntimeError,
                                    "MULTIPLE_APA_RECEIVERS_FOUND_REFUSE_UPDATE"):
            I.worker_processes(fake)

    def test_missing_loop_flag_cannot_authorize_process_termination(self):
        processes=[self.process(600, 99, loop=False)]
        fake=SimpleNamespace(processes=lambda worker: processes)
        with self.assertRaisesRegex(RuntimeError,
                                    "APA_RECEIVER_UNEXPECTED_COMMAND_LINE"):
            I.worker_processes(fake)

    def test_verified_tree_stops_children_before_parent_no_taskkill_T(self):
        processes=[self.process(600, 99), self.process(601, 600),
                   self.process(602, 601)]
        fake=SimpleNamespace(processes=lambda worker: list(processes))
        before=I.worker_processes(fake)
        killed=[]
        def terminate(command,**kwargs):
            self.assertEqual(command[:2],["taskkill","/PID"])
            self.assertEqual(command[3:],["/F"])
            pid=int(command[2])
            killed.append(pid)
            processes[:]=[row for row in processes if row["ProcessId"]!=pid]
            return SimpleNamespace(returncode=0)
        with patch.object(I.subprocess,"run",side_effect=terminate):
            I.stop_receiver_tree(fake,before)
        self.assertEqual(killed,[602,601,600])
        self.assertEqual(processes,[])

    def test_tree_changed_before_stop_blocks_without_termination(self):
        processes=[self.process(600, 99), self.process(601, 600)]
        fake=SimpleNamespace(processes=lambda worker: list(processes))
        before=I.worker_processes(fake)
        processes.pop()
        with patch.object(I.subprocess,"run") as stop:
            with self.assertRaisesRegex(RuntimeError,
                                        "RECEIVER_PROCESS_TREE_CHANGED_BEFORE_STOP"):
                I.stop_receiver_tree(fake,before)
            stop.assert_not_called()

    def test_venv_actual_worker_child_pid_is_accepted(self):
        # Popen tracks the launcher while worker main() runs in its child.
        rows=[self.process(2200, 88), self.process(2244, 2200)]
        fake=SimpleNamespace(processes=lambda worker: list(rows))
        with tempfile.TemporaryDirectory() as td:
            marker=Path(td)/"receiver-started.json"
            marker.write_text(json.dumps({
                "workerSHA256":"b"*64,"pid":2244}),encoding="utf8")
            self.assertEqual(I.verified_launched_receiver(
                fake,2200,"b"*64,marker),2244)

    def test_venv_shim_exits_but_child_identity_remains(self):
        # Python virtualenv redirector can exit and leave only the child.
        rows=[self.process(2244, 2200)]
        fake=SimpleNamespace(processes=lambda worker: list(rows))
        with tempfile.TemporaryDirectory() as td:
            marker=Path(td)/"receiver-started.json"
            marker.write_text(json.dumps({
                "workerSHA256":"b"*64,"pid":2244}),encoding="utf8")
            self.assertEqual(I.verified_launched_receiver(
                fake,2200,"b"*64,marker),2244)

    def test_marker_from_old_receiver_rejected(self):
        rows=[self.process(2200, 88),self.process(2244, 2200)]
        fake=SimpleNamespace(processes=lambda worker: list(rows))
        with tempfile.TemporaryDirectory() as td:
            marker=Path(td)/"receiver-started.json"
            marker.write_text(json.dumps({
                "workerSHA256":"a"*64,"pid":2244}),encoding="utf8")
            with self.assertRaisesRegex(RuntimeError,
                                        "RECEIVER_STARTED_MARKER_DOES_NOT_MATCH"):
                I.verified_launched_receiver(fake,2200,"b"*64,marker)

    def test_marker_from_unrelated_process_is_rejected(self):
        rows=[self.process(2200, 88),self.process(2244, 2200)]
        fake=SimpleNamespace(processes=lambda worker: list(rows))
        with tempfile.TemporaryDirectory() as td:
            marker=Path(td)/"receiver-started.json"
            marker.write_text(json.dumps({
                "workerSHA256":"b"*64,"pid":9999}),encoding="utf8")
            with self.assertRaisesRegex(RuntimeError,
                                        "RECEIVER_STARTED_MARKER_DOES_NOT_MATCH"):
                I.verified_launched_receiver(fake,2200,"b"*64,marker)

    def test_rogue_unrelated_receiver_fails_confirmation(self):
        rows=[self.process(2200, 45)]
        fake=SimpleNamespace(processes=lambda worker: list(rows))
        with tempfile.TemporaryDirectory() as td:
            marker=Path(td)/"receiver-started.json"
            marker.write_text(json.dumps({
                "workerSHA256":"b"*64,"pid":2200}),encoding="utf8")
            with self.assertRaisesRegex(RuntimeError,
                                        "RECEIVER_STARTED_TREE_IS_NOT_OUR_LAUNCH"):
                I.verified_launched_receiver(fake,7777,"b"*64,marker)

    def test_installer_success_requires_singleton_proof(self):
        src=TARGET.read_text(encoding="utf8")
        self.assertIn("receiver_holds_singleton()",src)
        self.assertIn("STOP",I.stop_receiver_tree.__name__.upper())
        self.assertIn("ROLLBACK_BLOCKED_LIVE_RECEIVER_STILL_RUNNING",src)

    def test_no_pln_or_core_mutation_apis(self):
        src=TARGET.read_text(encoding="utf8")
        self.assertNotIn("CreateWalls",src)
        self.assertNotIn("CreateColumns",src)
        self.assertNotIn("ModifyWalls",src)
        self.assertNotIn(".unlink()",src)
        self.assertIn("MULTIPLE_APA_RECEIVERS_FOUND_REFUSE_UPDATE",src)
        self.assertIn("RECEIVER_NEW_BYTES_READBACK_FAILED",src)

if __name__=="__main__":
    unittest.main()
