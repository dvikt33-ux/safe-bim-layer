"""Private MCP transport for the existing APA CLI and guarded test campaigns."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from threading import Lock
from typing import Literal

from mcp.types import CallToolResult, TextContent, ToolAnnotations

from apa_ac29_save_isolation import require, write_new_json
from apa_release import MANIFEST, read_json, read_release, sha256, verify_member


SCHEMA = "APA_MCP_PROFILE_V1"
ID = re.compile(r"[a-z0-9][a-z0-9-]{2,63}")
HEX = re.compile(r"[a-f0-9]{64}")
TEST_ID = re.compile(r"r03-(?:authored|gpt-shell)-mcp-[a-z0-9-]{4,40}")
Operation = Literal["doctor", "plan", "native-read", "preflight", "write", "check-closed", "verify-reopen"]
ReadKind = Literal["status", "job", "receipt"]
Receipt = Literal["plan", "native-inventory", "stdout", "stderr"]
ARTIFACTS = {"plan": "plan.json", "native-inventory": "native-inventory.json",
             "stdout": "stdout.txt", "stderr": "stderr.txt"}
NATIVE = {"native-read", "preflight", "write", "check-closed", "verify-reopen"}
PRE_SAVE = {"preflight", "write"}
MAX_INPUT = 256_000
MAX_ACTIVE = 8
PROTECTED_RUNTIME = Path(r"C:\LocalAI\APA_AC29_Stable")


def exact_path(path, *, exists=True):
    require(path.is_absolute() and path.resolve(strict=exists) == path, "MCP_REDIRECTED_PATH")
    return path


def file_json(path, limit=MAX_INPUT):
    path = exact_path(path)
    require(path.is_file() and path.stat().st_size <= limit, "MCP_FILE_SCOPE_OR_SIZE")
    return read_json(path)


def output_json(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True)


class Control:
    """Bind to operator-owned campaign manifests and keep transport receipts on disk."""
    def __init__(self, root, profile, *, worker=True):
        self.root = root.resolve()
        self.profile = exact_path(profile)
        require(self.profile.is_file() and self.profile.stat().st_size <= MAX_INPUT, "MCP_FILE_SCOPE_OR_SIZE")
        profile_bytes = self.profile.read_bytes()
        require(len(profile_bytes) <= MAX_INPUT, "MCP_FILE_SCOPE_OR_SIZE")
        config = json.loads(profile_bytes)
        self.release = read_release(self.root)
        self.release_sha = sha256(self.root / MANIFEST)
        require(isinstance(config, dict) and set(config) == {"schema", "releaseManifestSha256", "campaigns"}
                and config["schema"] == SCHEMA and config["releaseManifestSha256"] == self.release_sha
                and isinstance(config["campaigns"], dict) and len(config["campaigns"]) <= 12,
                "MCP_PROFILE_RELEASE_OR_SCHEMA_DRIFT")
        self.profile_sha = hashlib.sha256(profile_bytes).hexdigest()
        self.campaigns = config["campaigns"]
        for target, row in self.campaigns.items():
            require(isinstance(row, dict) and set(row) == {"job", "stageSha256", "writeEnabled"}
                    and ID.fullmatch(target) and isinstance(row["stageSha256"], str) and HEX.fullmatch(row["stageSha256"])
                    and type(row["writeEnabled"]) is bool, "MCP_CAMPAIGN_SCOPE_INVALID")
            self.campaign(target)
        self.check_release(full=True)
        self.state = exact_path(self.profile.with_name(self.profile.stem + "-jobs"), exists=False)
        self.state.mkdir(exist_ok=True)
        if not worker:
            return
        from bureau_unified_service import exclusive_process_lock

        self.lock = exclusive_process_lock(self.state / "transport")
        self.lock.__enter__()
        try:
            self.recover()
            self.submission = Lock()
            self.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="apa-mcp")
        except BaseException:
            self.lock.__exit__(*sys.exc_info())
            raise

    def close(self):
        try:
            self.pool.shutdown(wait=True)
        finally:
            self.lock.__exit__(None, None, None)

    def check_release(self, *, full=False):
        require(sha256(self.profile) == self.profile_sha
                and sha256(self.root / MANIFEST) == self.release_sha, "MCP_PROFILE_OR_RELEASE_DRIFT")
        names = {"apa.py", "apa_release.py", "scripts/apa_control_mcp.py"}
        if full:
            names.update(name for name in self.release["files"]
                         if name.startswith(("scripts/", "schemas/", "archicad-addon/Sources/")))
        for name in sorted(names):
            verify_member(self.root, self.release, name)

    def campaign(self, target):
        row = self.campaigns.get(target)
        require(row is not None, "MCP_TARGET_NOT_CONFIGURED")
        job = exact_path(Path(row["job"]))
        stage = exact_path(job / "job.json")
        record = file_json(stage)
        require(record.get("jobId") == job.name and not job.is_relative_to(self.root)
                and not job.is_relative_to(PROTECTED_RUNTIME.resolve())
                and not self.profile.is_relative_to(job)
                and (not row["writeEnabled"] or TEST_ID.fullmatch(job.name)), "MCP_CAMPAIGN_SCOPE_INVALID")
        from apa_r03_architecture import check

        manifest = check(job, exact_path(Path(record["original"])), record["initialSHA256"])
        require(sha256(stage) == row["stageSha256"] and manifest == record, "MCP_CAMPAIGN_MANIFEST_DRIFT")
        if row["writeEnabled"]:
            require("authoredIntentHash" in manifest and exact_path(job / "intent.json").is_file(),
                    "MCP_AUTHORED_TEST_CAMPAIGN_REQUIRED")
        return job, manifest, row

    def folder(self, job_id):
        require(isinstance(job_id, str) and ID.fullmatch(job_id), "MCP_INVALID_JOB_ID")
        return exact_path(self.state / job_id, exists=False)

    def result(self, folder, request, **facts):
        return dict(jobId=folder.name, operation=request["operation"], target=request["target"],
                    releaseRevision=self.release["revision"], automaticRetry=False, **facts)

    def recover(self):
        for folder in self.state.iterdir():
            if not ID.fullmatch(folder.name) or not folder.is_dir() or folder.resolve() != folder:
                continue
            request = folder / "request.json"
            if request.is_file() and not (folder / "result.json").exists():
                record = file_json(request)
                if record["profileSha256"] != self.profile_sha:
                    continue
                self.finish(folder, record, "INTERRUPTED_NO_AUTORETRY",
                            nativeOutcome="UNKNOWN" if (folder / "running.json").exists() else "NOT_STARTED")

    def finish(self, folder, request, status, **facts):
        from apa_ac29_autonomous_job_bridge import durable_write

        receipt = self.result(folder, request, status=status, finishedAt=self.utc_now(), **facts)
        durable_write(folder / "result.json", receipt)
        return receipt

    def submit(self, operation, job_id, target=None, intent=None):
        self.check_release()
        require(operation in {"doctor", "plan"} | NATIVE, "MCP_OPERATION_NOT_ALLOWED")
        require((target is not None) == (operation in NATIVE)
                and (intent is not None) == (operation == "plan"), "MCP_OPERATION_ARGUMENTS_INVALID")
        if intent is not None:
            try:
                size = len(output_json(intent).encode("utf-8"))
            except (RecursionError, ValueError) as exc:
                raise ValueError("MCP_PLAN_INPUT_INVALID") from exc
            require(isinstance(intent, dict) and intent.get("schemaVersion") in {
                "apa-semantic-project-brief/1", "apa-project-design/1"}
                and size <= MAX_INPUT // 4, "MCP_PLAN_INPUT_INVALID")
        folder = self.folder(job_id)
        request = dict(operation=operation, target=target, intent=intent, profileSha256=self.profile_sha)
        with self.submission:
            return self.queue(folder, request)

    def queue(self, folder, request):
        from apa_ac29_autonomous_job_bridge import durable_write

        operation, target = request["operation"], request["target"]
        if folder.exists():
            path = folder / "request.json"
            require(path.is_file(), "MCP_INTERRUPTED_SUBMISSION_NO_REPLAY")
            previous = file_json(path)
            require({k: v for k, v in previous.items() if k != "queuedAt"} == request,
                    "MCP_JOB_ID_ALREADY_BOUND")
            return self.read("job", job_id=folder.name)
        if target is not None:
            require(target in self.campaigns, "MCP_TARGET_NOT_CONFIGURED")
        if operation == "write":
            self.local_grant(folder.name, target)
        active = sum((p / "request.json").is_file() and not (p / "result.json").is_file()
                     for p in self.state.iterdir() if ID.fullmatch(p.name) and p.resolve() == p)
        require(active < MAX_ACTIVE, "MCP_QUEUE_FULL")
        folder.mkdir()
        request["queuedAt"] = self.utc_now()
        durable_write(folder / "request.json", request)
        self.pool.submit(self.run_job, folder, request)
        return self.result(folder, request, status="QUEUED", queuedAt=request["queuedAt"])

    def grant_record(self, job_id, target, confirm=None):
        folder = self.folder(job_id)
        job, stage, row = self.campaign(target)
        require(row["writeEnabled"] and "authoredIntentHash" in stage, "MCP_NATIVE_WRITE_DISABLED")
        approval = exact_path(job / "approved-preflight.json")
        actual = sha256(approval)
        if confirm is not None:
            require(confirm == actual, "MCP_PREFLIGHT_SHA_MISMATCH")
        from apa_r03_architecture import approved_result, status

        approved = file_json(approval)
        approved_result(job, approved)
        require(status(job, stage)["status"] == "READY_FOR_EXPLICIT_TEST_RUN"
                and isinstance(approved.get("listener"), dict), "MCP_EXACT_PREFLIGHT_REQUIRED")
        require(sha256(approval) == actual, "MCP_PREFLIGHT_CHANGED_DURING_APPROVAL")
        return folder.with_suffix(".grant.json"), dict(jobId=job_id, target=target, stageSha256=row["stageSha256"],
                    profileSha256=self.profile_sha, preflightSha256=actual, intentSha256=stage["intentSHA256"],
                    initialPlnSha256=stage["initialSHA256"], listener=approved["listener"])

    def local_grant(self, job_id, target):
        path, expected = self.grant_record(job_id, target)
        require(path.is_file() and file_json(path) == expected, "MCP_EXPLICIT_LOCAL_GRANT_REQUIRED")
        return expected

    def run_job(self, folder, request):
        operation, target = request["operation"], request["target"]
        dispatched = False
        try:
            require(request["profileSha256"] == self.profile_sha, "MCP_PROFILE_CHANGED")
            self.check_release(full=operation != "doctor")
            args = [sys.executable, "-I", "-B", "-X", "utf8", str(self.root / "apa.py")]
            if operation == "doctor":
                args += ["doctor"]
            elif operation == "plan":
                source, result = folder / "intent.json", folder / "plan.json"
                write_new_json(source, request["intent"])
                args += ["plan", "--intent", str(source), "--output", str(result)]
            else:
                args += self.native_args(folder, operation, target)
                dispatched = True
            return self.run_command(folder, request, args)
        except subprocess.TimeoutExpired as exc:
            facts = self.record_output(folder, exc.stdout or b"", exc.stderr or b"")
            return self.finish(folder, request, "TIMED_OUT_NO_AUTORETRY",
                               nativeOutcome="UNKNOWN" if operation == "write" else "NO_MODEL_WRITE",
                               exitCode=None, **facts)
        except (OSError, ValueError, KeyError, TypeError, RuntimeError, subprocess.SubprocessError) as exc:
            return self.finish(folder, request, "BLOCKED",
                               reason=str(exc).replace(str(self.root), "APA")[:260],
                               nativeOutcome="UNKNOWN" if dispatched and operation == "write" else "NOT_DISPATCHED",
                               exitCode=None)

    def native_args(self, folder, operation, target):
        from apa_r03_architecture import status

        job, manifest, _ = self.campaign(target)
        stage_status = status(job, manifest)["status"]
        if operation in PRE_SAVE:
            require(stage_status in {"STAGED", "READY_FOR_EXPLICIT_TEST_RUN"}, "MCP_CAMPAIGN_ALREADY_ATTEMPTED")
        args = ["architecture-runtime", operation, "--job", str(job), "--shared-native-lock",
                "--expected-stage-sha", self.campaigns[target]["stageSha256"]]
        if operation in {"native-read", "preflight", "verify-reopen"}:
            args.append("--discover-test-port")
        if operation == "native-read":
            args += ["--output", str(folder / "native-inventory.json")]
        if operation == "write":
            grant = self.local_grant(folder.name, target)
            args[1] = "execute"
            args += ["--confirm-preflight", grant["preflightSha256"]]
        return args

    def run_command(self, folder, request, args):
        write_new_json(folder / "running.json", {"operation": request["operation"], "startedAt": self.utc_now()})
        environment = {k: v for k, v in os.environ.items() if k.upper() not in
                       {"OPENAI_API_KEY", "OPENAI_ADMIN_KEY", "CONTROL_PLANE_API_KEY"}}
        process = subprocess.run(args, cwd=self.root, stdin=subprocess.DEVNULL, env=environment,
                                 capture_output=True, timeout=600 if request["operation"] in NATIVE else 60,
                                 creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        facts = self.record_output(folder, process.stdout, process.stderr)
        receipt, phase = None, None
        try:
            receipt = json.loads(process.stdout)
            phase = receipt.get("status") if isinstance(receipt, dict) else None
        except ValueError:
            pass
        if request["operation"] == "write":
            ok = process.returncode == 0 and phase == "LIVE_ARCHITECTURE_SAVED_PENDING_REAL_REOPEN"
        else:
            ok = process.returncode == 0 and phase is not None
        return self.finish(folder, request, "COMPLETE" if ok else "FAILED",
                           phaseStatus=phase, exitCode=process.returncode,
                           nativeOutcome=("RECORDED" if ok else "CHECK_NATIVE_JOURNAL_NO_REPLAY")
                           if request["operation"] == "write" else "NO_MODEL_WRITE",
                           receipt=receipt if isinstance(receipt, dict) and len(process.stdout) <= 8_000 else None,
                           **facts)

    def record_output(self, folder, stdout, stderr):
        for artifact, payload in (("stdout", stdout), ("stderr", stderr)):
            with (folder / ARTIFACTS[artifact]).open("xb") as stream:
                stream.write(payload)
        artifacts = {name: sha256(exact_path(folder / name)) for name in ARTIFACTS.values()
                     if (folder / name).is_file()}
        return dict(stdout=stdout[:8_000].decode("utf-8", errors="replace"),
                    stderr=stderr[:4_000].decode("utf-8", errors="replace"),
                    stdoutTruncated=len(stdout) > 8_000, stderrTruncated=len(stderr) > 4_000,
                    artifacts=artifacts)

    def read(self, kind, job_id=None, artifact=None, offset=0):
        self.check_release()
        if kind == "status":
            require(job_id is None and artifact is None and offset == 0, "MCP_READ_ARGUMENTS_INVALID")
            return dict(status="MCP_APA_READY", releaseRevision=self.release["revision"],
                        manifestSha256=self.release_sha, nativeRuntime="REQUEST_NATIVE_READ",
                        targets=[dict(id=target, writeEnabled=row["writeEnabled"])
                                 for target, row in self.campaigns.items()])
        require(kind in {"job", "receipt"}, "MCP_READ_KIND_NOT_ALLOWED")
        folder = self.folder(job_id)
        require(folder.is_dir(), "MCP_UNKNOWN_JOB_ID")
        request = file_json(folder / "request.json")
        require(request["profileSha256"] == self.profile_sha, "MCP_JOB_PROFILE_CHANGED")
        result = folder / "result.json"
        if kind == "job":
            require(artifact is None and offset == 0, "MCP_READ_ARGUMENTS_INVALID")
            if result.is_file():
                return file_json(result)
            running = folder / "running.json"
            return self.result(folder, request, status="RUNNING" if running.exists() else "QUEUED",
                               queuedAt=request.get("queuedAt"))
        require(artifact in ARTIFACTS and type(offset) is int and offset >= 0,
                "MCP_RECEIPT_NOT_ALLOWED")
        require(result.is_file(), "MCP_RECEIPT_NOT_READY")
        path = exact_path(folder / ARTIFACTS[artifact])
        proof = file_json(result).get("artifacts", {}).get(path.name)
        require(proof is not None and sha256(path) == proof and path.stat().st_size <= 8_000_000,
                "MCP_RECEIPT_INTEGRITY_REQUIRED")
        content = path.read_bytes().decode("utf-8", errors="replace")
        require(offset <= len(content), "MCP_INVALID_RECEIPT_OFFSET")
        end = min(offset + 8_000, len(content))
        return dict(jobId=job_id, artifact=artifact, sha256=proof, offset=offset,
                    nextOffset=end if end < len(content) else None, content=content[offset:end])

    @staticmethod
    def utc_now():
        return datetime.now(timezone.utc).isoformat()


def server_for(control):
    import anyio
    from mcp.server import MCPServer

    server = MCPServer("APA Windows")

    def reply(row):
        return CallToolResult(content=[TextContent(type="text", text=output_json(row))], structured_content=row)

    async def call(function, *args):
        try:
            return reply(await anyio.to_thread.run_sync(function, *args))
        except (OSError, ValueError, KeyError, TypeError, RuntimeError) as exc:
            reason = str(exc)
            if not re.fullmatch(r"[A-Z][A-Z0-9_]{5,100}", reason):
                reason = "MCP_REQUEST_BLOCKED_CHECK_LOCAL_DIAGNOSTICS"
            row = dict(status="BLOCKED", reason=reason)
            return CallToolResult(content=[TextContent(type="text", text=output_json(row))],
                                  structured_content=row, is_error=True)

    @server.tool(annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=False))
    async def apa_read(kind: ReadKind, job_id: str | None = None, artifact: Receipt | None = None,
                       offset: int = 0) -> CallToolResult:
        """Read APA revision, a named job or a page of its verified plan or inventory."""
        return await call(control.read, kind, job_id, artifact, offset)

    @server.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True,
                                            idempotentHint=True, openWorldHint=False))
    async def apa_execute(operation: Operation, job_id: str, target: str | None = None,
                          intent: dict | None = None) -> CallToolResult:
        """Queue an approved APA operation under an immutable job ID; use apa_read for the result.

        Plan accepts a semantic brief or project variants. Native operations require a named
        local test campaign. Write additionally requires an exact local operator grant.
        """
        return await call(control.submit, operation, job_id, target, intent)

    return server


def main(argv=None):
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument("--port", type=int, help="Optional HTTP port on 127.0.0.1. Default is stdio.")
    parser.add_argument("--grant", nargs=3, metavar=("JOB_ID", "TARGET", "PREFLIGHT_SHA256"))
    args = parser.parse_args(argv)
    require(not (args.port and args.grant), "MCP_SELECT_ONE_MODE")
    profile = args.profile.absolute()
    if args.grant:
        # A local operator grant may be added while the single MCP transport is running.
        control = Control(root, profile, worker=False)
        job_id, target, confirm = args.grant
        require(not control.folder(job_id).exists(), "MCP_GRANT_REQUIRES_UNUSED_JOB_ID")
        path, receipt = control.grant_record(job_id, target, confirm)
        pending = path.with_suffix(".pending")
        write_new_json(pending, receipt)
        try:
            os.link(pending, path)
        finally:
            pending.unlink()
        print(output_json(dict(status="MCP_LOCAL_GRANT_RECORDED", jobId=job_id, target=target,
                               preflightSha256=receipt["preflightSha256"])))
        return 0
    control = Control(root, profile)
    try:
        server = server_for(control)
        if args.port is None:
            server.run(transport="stdio")
        else:
            require(1024 <= args.port <= 65535, "MCP_INVALID_LOOPBACK_PORT")
            server.run(transport="streamable-http", host="127.0.0.1", port=args.port,
                       stateless_http=True, json_response=True, max_request_body_size=MAX_INPUT)
    finally:
        control.close()
    return 0
