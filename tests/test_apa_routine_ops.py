"""Offline regression tests for approval-free, typed APA routine workstation reads."""
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "apa_routine_ops.py"
spec = importlib.util.spec_from_file_location("apa_routine_ops", MODULE)
routine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(routine)


class TestRoutineRead(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "experiments").mkdir()
        (self.root / "experiments" / "wall.json").write_text('{"length":4000}', encoding="utf-8")
        (self.root / "experiments" / "notes.md").write_text("Wall 4000 mm", encoding="utf-8")
        self.calls = []
        self.reader = routine.RoutineRead(
            self.root,
            tasklist=lambda: [
                ["Rhino.exe", "493168", "Console", "1", "70,000 K"],
                ["Archicad.exe", "486172", "Console", "1", "100,000 K"],
                ["powershell.exe", "333", "Console", "1", "8,000 K"],
            ],
            socket_check=lambda port: self.calls.append(port) or port == 3003,
        )

    def tearDown(self):
        self.temp.cleanup()

    @staticmethod
    def intent(kind, **args):
        return {"kind": kind, "parameters": args}

    def run_read(self, job, kind, **args):
        return self.reader.perform(job, intent=self.intent(kind, **args))

    def test_status_explicitly_requires_no_approval(self):
        r = self.run_read("r-read-001", "status")
        self.assertEqual(r["status"], "COMPLETE")
        self.assertFalse(r["requiresApprove"])
        self.assertEqual(r["modelWrites"], 0)
        self.assertTrue(r["result"]["readOnly"])

    def test_processes_are_read_with_fixed_approved_names(self):
        r = self.run_read("r-read-002", "processes", names=["Rhino.exe", "Archicad.exe"])
        self.assertEqual(r["result"]["processes"], [
            {"name": "Rhino.exe", "pid": 493168},
            {"name": "Archicad.exe", "pid": 486172},
        ])

    def test_process_name_injection_rejected(self):
        r = self.run_read("r-read-003", "processes", names=["Rhino.exe; Remove-Item C:\\"])
        self.assertEqual(r["status"], "BLOCKED")
        self.assertEqual(r["reason"], "ROUTINE_PROCESS_NOT_ALLOWED")

    def test_ports_are_pinned_and_not_arbitrary(self):
        r = self.run_read("r-read-004", "ports", ports=[3003, 18787])
        self.assertEqual(r["result"]["ports"], [
            {"port": 3003, "acceptingTcp": True},
            {"port": 18787, "acceptingTcp": False},
        ])
        self.assertEqual(self.calls, [3003, 18787])

    def test_unknown_port_rejected(self):
        r = self.run_read("r-read-005", "ports", ports=[22])
        self.assertEqual(r["status"], "BLOCKED")
        self.assertEqual(r["reason"], "ROUTINE_PORT_NOT_ALLOWED")

    def test_directory_listing_only_in_workspace(self):
        r = self.run_read("r-read-006", "directory", relativePath="experiments")
        self.assertEqual(r["status"], "COMPLETE")
        self.assertIn("wall.json", [e["name"] for e in r["result"]["entries"]])

    def test_file_stat_and_sha(self):
        r = self.run_read("r-read-007", "file-stat", relativePath="experiments/wall.json")
        self.assertEqual(r["status"], "COMPLETE")
        data=(self.root / "experiments" / "wall.json").read_bytes()
        self.assertEqual(r["result"]["sha256"], hashlib.sha256(data).hexdigest())

    def test_text_read_only_in_workspace(self):
        r = self.run_read("r-read-008", "text-read", relativePath="experiments/notes.md")
        self.assertEqual(r["result"]["text"], "Wall 4000 mm")

    def test_path_traversal_is_blocked(self):
        r = self.run_read("r-read-009", "text-read", relativePath="../outside.txt")
        self.assertEqual(r["status"], "BLOCKED")
        self.assertEqual(r["modelWrites"], 0)

    def test_absolute_path_is_blocked(self):
        r = self.run_read("r-read-010", "file-stat", relativePath=str(self.root / "experiments" / "wall.json"))
        self.assertEqual(r["status"], "BLOCKED")

    def test_secret_named_file_is_blocked(self):
        (self.root / "experiments" / "secrets.json").write_text('{"token":"not for export"}')
        r = self.run_read("r-read-011", "text-read", relativePath="experiments/secrets.json")
        self.assertEqual(r["status"], "BLOCKED")
        self.assertEqual(r["reason"], "ROUTINE_TEXT_READ_BLOCKED")

    def test_large_text_is_blocked(self):
        (self.root / "experiments" / "large.txt").write_bytes(b"x" * (routine.MAX_TEXT_BYTES + 1))
        r = self.run_read("r-read-012", "text-read", relativePath="experiments/large.txt")
        self.assertEqual(r["status"], "BLOCKED")

    def test_unknown_kind_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "ROUTINE_OPERATION_NOT_ALLOWED"):
            self.reader.perform("r-read-013", intent=self.intent("execute-command", code="whoami"))

    def test_repeated_job_does_not_rerun_probe(self):
        arg = self.intent("ports", ports=[3003])
        one = self.reader.perform("r-read-014", intent=arg)
        two = self.reader.perform("r-read-014", intent=arg)
        self.assertEqual(one, two)
        self.assertEqual(self.calls, [3003])

    def test_conflicting_job_reuse_is_blocked(self):
        self.run_read("r-read-015", "status")
        with self.assertRaisesRegex(ValueError, "ROUTINE_JOB_ID_CONFLICT"):
            self.run_read("r-read-015", "ports", ports=[3003])

    def test_read_receipt(self):
        self.run_read("r-read-016", "status")
        r = self.reader.read_job("r-read-016")
        self.assertEqual(r["status"], "COMPLETE")
        self.assertEqual(r["kind"], "status")

    def test_missing_job_receipt_is_none(self):
        self.assertIsNone(self.reader.read_job("r-read-missing"))

    def test_extra_arguments_are_blocked(self):
        r = self.run_read("r-read-017", "status", arbitrary="command")
        self.assertEqual(r["status"], "BLOCKED")

    def test_symlink_cannot_escape_workspace(self):
        with tempfile.TemporaryDirectory() as external:
            target = Path(external) / "outside.txt"
            target.write_text("protected")
            link = self.root / "experiments" / "linked.txt"
            try:
                link.symlink_to(target)
            except OSError:
                self.skipTest("Creating symlinks requires elevated privileges on this platform")
            r = self.run_read("r-read-018", "text-read", relativePath="experiments/linked.txt")
            self.assertEqual(r["status"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
