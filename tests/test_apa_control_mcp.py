from concurrent.futures import ThreadPoolExecutor
from argparse import Namespace
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
        tracked = sorted(path.relative_to(self.build).as_posix()
                         for path in self.build.rglob("*") if path.is_file())
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
                brief = dict(proposal["brief"], openQuestions=["Уточнить методику площади"])
                await self.value(client, "apa_execute", dict(operation="plan", job_id="mcp-test-brief", intent=brief))
                brief_result = await self.complete(client, "mcp-test-brief")
                self.assertEqual((brief_result["status"], brief_result["exitCode"]), ("COMPLETE", 0))
                self.assertEqual(brief_result["phaseStatus"], "SEMANTIC_BRIEF_VALIDATED")
                self.assertEqual(brief_result["receipt"]["openQuestions"], brief["openQuestions"])
                self.assertFalse(brief_result["receipt"]["executionPermission"])
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

    def test_room_layout_plan_via_existing_mcp_tools(self):
        from tests.test_apa_room_layout import sample

        async def run():
            async with self.client() as client:
                job = "mcp-plan-layout"
                await self.value(client, "apa_execute", dict(operation="plan", job_id=job, intent=sample()))
                result = await self.complete(client, job)
                self.assertEqual(result["phaseStatus"], "LAYOUT_PLAN_VALIDATED_OFFLINE")
                self.assertEqual(result["receipt"]["operations"], 9)
                self.assertEqual(result["receipt"]["inclusionMode"], "USER_COPY_THEN_READBACK")
                self.assertFalse(result["receipt"]["executionPermission"])
                replay = await self.value(client, "apa_execute", dict(operation="plan", job_id=job, intent=sample()))
                self.assertEqual(replay, result)
                await self.value(client, "apa_execute", dict(operation="plan", job_id="mcp-layout-input-needed",
                                 intent={"schemaVersion": "apa-room-layout/1"}))
                missing = await self.complete(client, "mcp-layout-input-needed")
                self.assertEqual(missing["phaseStatus"], "LAYOUT_INPUT_REQUIRED")
                self.assertIn("minPierMM", missing["receipt"]["missingInputs"])
                self.assertFalse(missing["receipt"]["executionPermission"])
        anyio.run(run)

    def test_layout_route_requires_a_local_grant_bound_to_exact_preflight(self):
        from apa_ac30_native import Job, stage
        from tests.test_apa_room_layout import sample

        donor = self.root / "donor.pln"
        addon = self.root / "tapir.apx"
        intent = self.root / "layout.json"
        target = self.root / "layout-mcp-fixture"
        donor.write_bytes(b"Original donor")
        revision, identity = "a" * 40, "b" * 64
        addon.write_bytes(revision.encode() + identity.encode())
        write_new_json(intent, sample())
        stage(Namespace(action="stage-layout", job=target, source=donor, source_sha=sha256(donor),
                        addon=addon, addon_sha=sha256(addon), source_revision=revision,
                        build_identity=identity, build=3001, design=intent))
        job = Job(target)
        profile = self.root / "layout-profile.json"
        row = dict(job=str(target), stageSha256=job.manifest_sha, writeEnabled=True)
        write_new_json(profile, dict(schema=SCHEMA, releaseManifestSha256=sha256(self.build / MANIFEST),
                                     campaigns={target.name: row}))
        control = Control(self.build, profile, worker=False)
        self.assertEqual(control.native_args(control.folder("preflight-room"), "preflight", target.name)[:2],
                         ["ac30-native", "preflight"])
        self.assertEqual(control.native_args(control.folder("verify-copy"), "verify-inclusion", target.name)[:2],
                         ["ac30-native", "verify-inclusion"])
        with self.assertRaises(FileNotFoundError):
            control.local_grant("write-room", target.name)
        preflight = job.path / "preflight.json"
        write_new_json(preflight, dict(status="READY_FOR_EXPLICIT_TEST_RUN", manifestSha256=job.manifest_sha,
                                     recipe=job.recipe, binding=dict(path=str(job.project), listener=dict(pid=1)),
                                     modelWrites=0, executionPermission=False))
        with self.assertRaisesRegex(ValueError, "EXPLICIT_LOCAL_GRANT"):
            control.local_grant("write-room", target.name)
        with self.assertRaisesRegex(ValueError, "PREFLIGHT_SHA_MISMATCH"):
            control.grant_record("write-room", target.name, "0" * 64)
        grant_path, grant = control.grant_record("write-room", target.name, sha256(preflight))
        write_new_json(grant_path, grant)
        self.assertEqual(control.native_args(control.folder("write-room"), "write", target.name),
                         ["ac30-native", "execute", "--job", str(target), "--confirm-preflight", sha256(preflight)])
        with self.assertRaisesRegex(ValueError, "EXPLICIT_LOCAL_GRANT"):
            control.local_grant("different-write-id", target.name)
        write_new_json(job.path / "attempted.json", {"automaticReplay": False})
        with self.assertRaisesRegex(ValueError, "NO_REPLAY"):
            control.local_grant("write-room", target.name)
        self.assertEqual(donor.read_bytes(), b"Original donor")

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
