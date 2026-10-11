"""Real local bare-Git regression of report/receipt publication CAS recovery.

No GitHub writes, PLN/APX access, Slack or network. Two independent clones.
"""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "publish_stage_retry.sh"
BRANCH = "research/apa-verified-results-hub-20261010"
REF = "refs/heads/" + BRANCH
ROOT = Path("docs/research/apa-results")


def git(cwd, *args):
    proc = subprocess.run(["git", *args], cwd=cwd, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if proc.returncode:
        raise AssertionError(f"git {args}: {proc.stdout}")
    return proc.stdout.strip()


def identity(path):
    git(path, "config", "user.name", "APA Test")
    git(path, "config", "user.email", "apa@example.test")


class ImmutableStageRetry(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.remote = self.base / "origin.git"
        self.worker = self.base / "worker"
        self.rival = self.base / "rival"
        git(self.base, "init", "--bare", "--initial-branch=" + BRANCH, str(self.remote))
        git(self.base, "clone", "--quiet", str(self.remote), str(self.worker))
        identity(self.worker)
        root = self.worker / ROOT
        (root / "control").mkdir(parents=True)
        (root / "control/PROJECT_PLAN.json").write_text("revision=1\n")
        (root / "inbox").mkdir(parents=True)
        (root / "inbox/fake.json").write_text("inbox=stable\n")
        controller = self.worker / "tools/apa_controller/controller.py"
        controller.parent.mkdir(parents=True)
        controller.write_text("import sys\n# synthetic validation succeeds without modifying files\n", encoding="utf8")
        publisher = self.worker / "tools/apa_publisher/publisher.py"
        publisher.parent.mkdir(parents=True)
        publisher.write_text(
            "import pathlib,sys\n"
            "from hashlib import sha256\n"
            "root=pathlib.Path('docs/research/apa-results')\n"
            "if sys.argv[1]=='prepare':\n"
            "    report=root/'runs'/'2026-10-11'/'APA-RUN-test'/'REPORT.md'\n"
            "    report.parent.mkdir(parents=True, exist_ok=True)\n"
            "    raw=b'fixed immutable report\\n'\n"
            "    if report.exists() and report.read_bytes()!=raw:\n"
            "        raise ValueError('IMMUTABLE_CONFLICT')\n"
            "    report.write_bytes(raw)\n"
            "    index=root/'generated'/'INDEX.md'\n"
            "    index.parent.mkdir(parents=True, exist_ok=True)\n"
            "    index.write_bytes((root/'control'/'PROJECT_PLAN.json').read_bytes())\n"
            "    pathlib.Path('.apa-publisher-pending.json').write_text('pending')\n"
            "elif sys.argv[1]=='receipt':\n"
            "    anchor=sys.argv[3]\n"
            "    report=root/'runs'/'2026-10-11'/'APA-RUN-test'/'REPORT.md'\n"
            "    if not report.is_file(): raise ValueError('MISSING_REPORT')\n"
            "    dest=root/'receipts'/'APA-RUN-test.json'\n"
            "    dest.parent.mkdir(parents=True,exist_ok=True)\n"
            "    body=('sha256='+sha256(report.read_bytes()).hexdigest()+'\\nreport_commit='+anchor+'\\n').encode()\n"
            "    if dest.exists():\n"
            "        existing=dest.read_bytes()\n"
            "        if existing.splitlines()[0]!=body.splitlines()[0]:\n"
            "            raise ValueError('RECEIPT_CONFLICT')\n"
            "    else: dest.write_bytes(body)\n",
            encoding="utf8")
        git(self.worker, "add", "-A")
        git(self.worker, "commit", "-m", "base")
        git(self.worker, "push", "origin", "HEAD:" + REF)
        git(self.base, "clone", "--quiet", str(self.remote), str(self.rival))
        identity(self.rival)
        self.output = self.base / "output"
        self.env = {**os.environ, "GITHUB_REF": REF,
                    "GITHUB_REPOSITORY": "dvikt33-ux/safe-bim-layer",
                    "GITHUB_OUTPUT": str(self.output)}

    def execute(self, stage, report_sha=""):
        return subprocess.run(["bash", str(SCRIPT), stage, report_sha],
                              cwd=self.worker, env=self.env, text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    def push_rival_plan(self, revision="2"):
        target = self.rival / ROOT / "control/PROJECT_PLAN.json"
        target.write_text("revision=" + revision + "\n")
        git(self.rival, "add", "-A")
        git(self.rival, "commit", "-m", "concurrent plan change")
        git(self.rival, "push", "origin", "HEAD:" + REF)

    def setup_report_anchor(self):
        proc = subprocess.run(["python", "tools/apa_publisher/publisher.py", "prepare"],
                              cwd=self.worker, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        git(self.worker, "add", "-A", str(ROOT / "runs"), str(ROOT / "generated"))
        git(self.worker, "commit", "-m", "pinned verified report")
        anchor = git(self.worker, "rev-parse", "HEAD")
        git(self.worker, "push", "origin", "HEAD:" + REF)
        git(self.rival, "pull", "--ff-only")
        return anchor

    def test_report_first_attempt(self):
        out = self.execute("reports")
        self.assertEqual(out.returncode, 0, out.stdout)
        self.assertIn("stage=reports attempt=1", out.stdout)
        self.assertTrue(self.output.exists())

    def test_reports_rebuild_index_after_remote_cas(self):
        self.push_rival_plan()
        out = self.execute("reports")
        self.assertEqual(out.returncode, 0, out.stdout)
        self.assertIn("APA_STAGE_RACE stage=reports attempt=1", out.stdout)
        self.assertIn("stage=reports attempt=2", out.stdout)
        git(self.rival, "pull", "--ff-only")
        self.assertEqual((self.rival / ROOT / "generated/INDEX.md").read_text(), "revision=2\n")
        self.assertEqual((self.rival / ROOT / "runs/2026-10-11/APA-RUN-test/REPORT.md").read_bytes(),
                         b"fixed immutable report\n")

    def test_receipts_survive_remote_plan_cas(self):
        anchor = self.setup_report_anchor()
        self.push_rival_plan()
        out = self.execute("receipts", anchor)
        self.assertEqual(out.returncode, 0, out.stdout)
        self.assertIn("APA_STAGE_RACE stage=receipts attempt=1", out.stdout)
        self.assertIn("stage=receipts attempt=2", out.stdout)
        git(self.rival, "pull", "--ff-only")
        body = (self.rival / ROOT / "receipts/APA-RUN-test.json").read_text()
        self.assertIn("report_commit=" + anchor, body)
        self.assertEqual((self.rival / ROOT / "control/PROJECT_PLAN.json").read_text(), "revision=2\n")

    def test_competing_identical_receipt_is_preserved(self):
        anchor = self.setup_report_anchor()
        import hashlib
        receipt = self.rival / ROOT / "receipts/APA-RUN-test.json"
        receipt.parent.mkdir(parents=True, exist_ok=True)
        checksum = hashlib.sha256(b"fixed immutable report\n").hexdigest()
        receipt.write_text("sha256=" + checksum + "\nreport_commit=" + anchor + "\n")
        git(self.rival, "add", "-A")
        git(self.rival, "commit", "-m", "independent valid receipt")
        git(self.rival, "push", "origin", "HEAD:" + REF)
        expected_sha = git(self.rival, "rev-parse", "HEAD")
        out = self.execute("receipts", anchor)
        self.assertEqual(out.returncode, 0, out.stdout)
        self.assertIn("stage=receipts attempt=2", out.stdout)
        self.assertEqual(git(self.worker, "rev-parse", "HEAD"), expected_sha)
        self.assertEqual(receipt.read_text(),
                         (self.worker / ROOT / "receipts/APA-RUN-test.json").read_text())

    def test_competing_receipt_with_wrong_hash_is_rejected(self):
        anchor = self.setup_report_anchor()
        receipt = self.rival / ROOT / "receipts/APA-RUN-test.json"
        receipt.parent.mkdir(parents=True, exist_ok=True)
        receipt.write_text("sha256=unverified\nreport_commit=" + anchor + "\n")
        git(self.rival, "add", "-A")
        git(self.rival, "commit", "-m", "independent invalid receipt")
        git(self.rival, "push", "origin", "HEAD:" + REF)
        expected_sha = git(self.rival, "rev-parse", "HEAD")
        out = self.execute("receipts", anchor)
        self.assertNotEqual(out.returncode, 0, out.stdout)
        self.assertIn("RECEIPT_CONFLICT", out.stdout)
        self.assertFalse(self.output.exists())
        self.assertEqual(git(self.worker, "ls-remote", "origin", REF).split()[0],
                         expected_sha)

    def test_remote_immutable_mutation_fails_closed(self):
        anchor = self.setup_report_anchor()
        report = self.rival / ROOT / "runs/2026-10-11/APA-RUN-test/REPORT.md"
        report.write_text("MALICIOUS MUTATION\n")
        git(self.rival, "add", "-A")
        git(self.rival, "commit", "-m", "tamper report")
        git(self.rival, "push", "origin", "HEAD:" + REF)
        out = self.execute("receipts", anchor)
        self.assertEqual(out.returncode, 1, out.stdout)
        self.assertIn("immutable report or receipt mutated", out.stdout)
        self.assertFalse(self.output.exists())

    def test_code_change_fails_closed(self):
        target = self.rival / "tools/apa_publisher/publisher.py"
        with target.open("a") as f:
            f.write("\n# changed code\n")
        git(self.rival, "add", "-A")
        git(self.rival, "commit", "-m", "concurrent publisher change")
        git(self.rival, "push", "origin", "HEAD:" + REF)
        out = self.execute("reports")
        self.assertEqual(out.returncode, 1, out.stdout)
        self.assertIn("executable code changed", out.stdout)

    def test_server_denial_without_remote_advance(self):
        hook = self.remote / "hooks/pre-receive"
        hook.write_text("#!/bin/sh\necho DENIED >&2\nexit 1\n")
        hook.chmod(0o755)
        out = self.execute("reports")
        self.assertEqual(out.returncode, 1, out.stdout)
        self.assertIn("rejected push without remote advancement", out.stdout)
        self.assertNotIn("attempt=2", out.stdout)

    def test_wrong_ref_fails_closed(self):
        self.env["GITHUB_REF"] = "refs/heads/main"
        out = self.execute("reports")
        self.assertEqual(out.returncode, 2, out.stdout)
        self.assertIn("wrong workflow authority", out.stdout)


if __name__ == "__main__":
    unittest.main()
