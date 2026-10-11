"""Offline Git push-race regression via a local bare repo. No tokens/network."""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "publish_generated_retry.sh"
BRANCH = "research/apa-verified-results-hub-20261010"
REF = "refs/heads/" + BRANCH


def git(cwd, *args):
    p = subprocess.run(["git", *args], cwd=cwd, text=True,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if p.returncode:
        raise AssertionError(f"git {args}: {p.stdout}")
    return p


class ControllerPushRaceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.origin = self.root / "origin.git"
        self.worker = self.root / "worker"
        self.rival = self.root / "rival"
        git(self.root, "init", "--bare", "--initial-branch=" + BRANCH, str(self.origin))
        git(self.root, "clone", "--quiet", str(self.origin), str(self.worker))
        self._identity(self.worker)
        plan = self.worker / "docs/research/apa-results/control/PROJECT_PLAN.json"
        plan.parent.mkdir(parents=True)
        plan.write_text("rev1\n", encoding="utf8")
        controller = self.worker / "tools/apa_controller/controller.py"
        controller.parent.mkdir(parents=True)
        controller.write_text(
            "import pathlib,sys\n"
            "root=pathlib.Path('docs/research/apa-results/control')\n"
            "if sys.argv[1]=='build':\n"
            "    target=root/'generated'/'HANDOFF.md'\n"
            "    target.parent.mkdir(parents=True,exist_ok=True)\n"
            "    target.write_bytes((root/'PROJECT_PLAN.json').read_bytes())\n",
            encoding="utf8")
        target = self.worker / "docs/research/apa-results/control/generated/HANDOFF.md"
        target.parent.mkdir(exist_ok=True)
        target.write_text("rev1\n")
        git(self.worker, "add", "-A")
        git(self.worker, "commit", "-m", "source baseline")
        git(self.worker, "push", "origin", "HEAD:" + REF)
        git(self.root, "clone", "--quiet", str(self.origin), str(self.rival))
        self._identity(self.rival)
        self.output = self.root / "outputs"
        self.env = {**os.environ, "GITHUB_REF": REF,
                    "GITHUB_REPOSITORY": "dvikt33-ux/safe-bim-layer",
                    "GITHUB_OUTPUT": str(self.output)}

    @staticmethod
    def _identity(path):
        git(path, "config", "user.name", "test-publisher")
        git(path, "config", "user.email", "test@example.test")

    def execute(self, env=None):
        return subprocess.run(["bash", str(SCRIPT)], cwd=self.worker,
                              env=env or self.env, text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    def rival_commit(self, *, code=False):
        plan = self.rival / "docs/research/apa-results/control/PROJECT_PLAN.json"
        plan.write_text("rev2\n")
        if code:
            with (self.rival / "tools/apa_controller/controller.py").open("a") as f:
                f.write("\n# concurrently altered executable controller\n")
        git(self.rival, "add", "-A")
        git(self.rival, "commit", "-m", "concurrent controller CAS update")
        git(self.rival, "push", "origin", "HEAD:" + REF)

    def test_clean_push_first_attempt(self):
        (self.worker / "docs/research/apa-results/control/generated/HANDOFF.md").write_text("stale\n")
        p = self.execute()
        self.assertEqual(p.returncode, 0, p.stdout)
        self.assertIn("attempt=1", p.stdout)
        self.assertTrue(self.output.read_text().startswith("sha="))

    def test_concurrent_plan_update_is_not_lost(self):
        self.rival_commit()
        (self.worker / "docs/research/apa-results/control/generated/HANDOFF.md").write_text("stale\n")
        p = self.execute()
        self.assertEqual(p.returncode, 0, p.stdout)
        self.assertIn("CONTROLLER_PUSH_RACE attempt=1", p.stdout)
        self.assertIn("CONTROLLER_PUSH_VERIFIED_FAST_FORWARD attempt=2", p.stdout)
        git(self.rival, "pull", "--ff-only")
        self.assertEqual((self.rival / "docs/research/apa-results/control/generated/HANDOFF.md").read_text(), "rev2\n")
        self.assertEqual((self.rival / "docs/research/apa-results/control/PROJECT_PLAN.json").read_text(), "rev2\n")

    def test_concurrent_executable_mutation_fails_closed(self):
        self.rival_commit(code=True)
        (self.worker / "docs/research/apa-results/control/generated/HANDOFF.md").write_text("stale\n")
        p = self.execute()
        self.assertEqual(p.returncode, 1, p.stdout)
        self.assertIn("executable code changed", p.stdout)
        self.assertFalse(self.output.exists())

    def test_wrong_repository_is_rejected(self):
        p = self.execute({**self.env, "GITHUB_REPOSITORY": "forged/repo"})
        self.assertEqual(p.returncode, 2, p.stdout)
        self.assertIn("CONTROLLER_PUSH_BLOCKED", p.stdout)


if __name__ == "__main__":
    unittest.main()
