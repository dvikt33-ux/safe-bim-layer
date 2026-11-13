from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import shutil
import sys
import tempfile
import time
import unittest

import anyio
from mcp.client import Client
from mcp.client.stdio import StdioServerParameters

from apa_ac29_save_isolation import write_new_json
from apa_control_mcp import Control, SCHEMA
from apa_release import MANIFEST, sha256


ROOT = Path(__file__).resolve().parents[1]


class ControlTransportTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name).resolve()
        self.build = self.root / "build"
        self.build.mkdir()
        for name in ("apa.py", "apa_release.py", "requirements-apa.lock"):
            shutil.copyfile(ROOT / name, self.build / name)
        for name in ("scripts", "schemas", "archicad-addon"):
            shutil.copytree(ROOT / name, self.build / name, ignore=shutil.ignore_patterns("__pycache__"))
        tracked = ["apa.py", "apa_release.py", "scripts/apa_control_mcp.py"]
        write_new_json(self.build / MANIFEST, dict(schema="APA_WINDOWS_RELEASE_V1", revision="a"*40,
            files={name: dict(bytes=(self.build / name).stat().st_size,
                              sha256=sha256(self.build / name)) for name in tracked}))
        self.profile = self.root / "test-profile.json"
        write_new_json(self.profile, dict(schema=SCHEMA, releaseManifestSha256=sha256(self.build / MANIFEST),
                                         campaigns={}))

    def client(self):
        params = StdioServerParameters(command=sys.executable, args=[
            "-I", "-B", "-X", "utf8", str(self.build / "apa.py"), "mcp-control",
            "--profile", str(self.profile)])
        return Client(params, read_timeout_seconds=20)

    async def value(self, client, tool, args):
        result = await client.call_tool(tool, args)
        self.assertFalse(result.is_error, result)
        return result.structured_content

    async def complete(self, client, job_id):
        with anyio.fail_after(25):
            while True:
                row = await self.value(client, "apa_read", dict(kind="job", job_id=job_id))
                if row["status"] not in {"QUEUED", "RUNNING"}:
                    return row
                await anyio.sleep(.1)

    def test_real_mcp_process_plan_receipt_and_reconnect(self):
        async def run():
            async with self.client() as client:
                self.assertEqual({tool.name for tool in (await client.list_tools()).tools},
                                 {"apa_read", "apa_execute"})
                status = await self.value(client, "apa_read", dict(kind="status"))
                self.assertEqual(status["releaseRevision"], "a"*40)
                proposal = json.loads((ROOT / "examples/accelerator/r04-project-design.json").read_text("utf-8"))
                args = dict(operation="plan", job_id="mcp-test-plan", intent=proposal)
                result = await self.value(client, "apa_execute", args)
                self.assertEqual(result["status"], "QUEUED")
                result = await self.complete(client, "mcp-test-plan")
                self.assertEqual((result["status"], result["exitCode"], result["stderr"]), ("COMPLETE", 0, ""))
                self.assertEqual(result["phaseStatus"], "DESIGN_VARIANTS_REVIEWED")
                pieces, offset = [], 0
                while offset is not None:
                    page = await self.value(client, "apa_read", dict(kind="receipt", artifact="plan",
                                            job_id="mcp-test-plan", offset=offset))
                    self.assertEqual(page["sha256"], result["artifacts"]["plan.json"])
                    pieces.append(page["content"])
                    offset = page["nextOffset"]
                report = json.loads("".join(pieces))
                self.assertEqual([row["status"] for row in report["variants"]],
                                 ["DESIGN_CHECKS_REVIEWABLE", "REQUIREMENTS_OPEN"])
            async with self.client() as client:
                replay = await self.value(client, "apa_execute", args)
                self.assertEqual(replay, result)
                conflicting = await client.call_tool("apa_execute", dict(operation="doctor", job_id="mcp-test-plan"))
                self.assertTrue(conflicting.is_error)
                denied = await client.call_tool("apa_execute", dict(operation="write", job_id="unauthorized",
                                                                  target="unknown-target"))
                self.assertTrue(denied.is_error)
                bad = await client.call_tool("apa_read", dict(kind="receipt", job_id="mcp-test-plan",
                                                             artifact="../../outside.txt"))
                self.assertTrue(bad.is_error)
        anyio.run(run)

    def test_same_job_concurrent_replay_and_interruption(self):
        with tempfile.TemporaryDirectory() as external:
            path = Path(external) / "outside.txt"
            path.write_text("local-only", encoding="utf-8")
            control = Control(self.build, self.profile)
            try:
                with ThreadPoolExecutor(max_workers=2) as callers:
                    replies = list(callers.map(lambda _: control.submit("doctor", "same-job"), range(2)))
                self.assertEqual({r["jobId"] for r in replies}, {"same-job"})
                until = time.monotonic()+15
                while control.read("job", job_id="same-job")["status"] in {"QUEUED", "RUNNING"}:
                    self.assertLess(time.monotonic(), until)
                    time.sleep(.05)
                with self.assertRaisesRegex(ValueError, "MCP_INVALID_JOB_ID"):
                    control.read("job", job_id="../outside")
                interrupted = control.folder("interrupted")
                interrupted.mkdir()
                write_new_json(interrupted / "request.json", dict(operation="write", target="fixture", intent=None,
                               profileSha256=control.profile_sha))
                write_new_json(interrupted / "running.json", dict(operation="write"))
            finally:
                control.close()
            reopened = Control(self.build, self.profile)
            try:
                row = reopened.read("job", job_id="interrupted")
                self.assertEqual(row["status"], "INTERRUPTED_NO_AUTORETRY")
                self.assertEqual(row["nativeOutcome"], "UNKNOWN")
                self.assertEqual(path.read_text("utf-8"), "local-only")
            finally:
                reopened.close()
