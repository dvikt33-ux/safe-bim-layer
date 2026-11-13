"""Bind explicit R03 jobs to the existing GitHub receiver and native workflows."""
from __future__ import annotations

from datetime import timedelta
import json
import os
from pathlib import Path
import re
import subprocess
import urllib.error

import apa_ac29_group_batch_oneshot as group
import apa_r03_architecture as architecture
from apa_ac29_save_isolation import (
    confirm_project_closed, require, reservation_owner_exited, write_new_json,
)
from apa_mailbox_profile import APX, LEGACY_ROOT
from apa_release import MANIFEST, read_json, read_release, sha256, verify_member


PROFILE = "APA_AC29_R03_MAILBOX_PROFILE_V1"
JOB = "APA_AC29_R03_MAILBOX_JOB_V1"
SOURCE_REPO = "dvikt33-ux/safe-bim-layer"
SOURCES = {
    "ARCHITECTURE": "examples/accelerator/r03-gpt-shell-e2e.intent.json",
    "GROUP": "examples/accelerator/r03-gpt-grid-e2e.placements.json",
}
PHASES = {"plan": "PLAN", "execute": "EXECUTE", "closed": "CHECK_CLOSED", "reopen": "VERIFY_REOPEN"}
HEX40 = re.compile(r"[0-9a-f]{40}")
HEX64 = re.compile(r"[0-9a-f]{64}")


def staging(job_dir, kind):
    require(kind in SOURCES, "R03_MAILBOX_STAGE_KIND_REQUIRED")
    state = job_dir if kind == "ARCHITECTURE" else job_dir / "state"
    record = state / ("job.json" if kind == "ARCHITECTURE" else "manifest.json")
    manifest = read_json(record)
    authorization = "USER_APPROVED_APA_R03_" + job_dir.name
    if kind == "ARCHITECTURE":
        project, donor = Path(manifest["project"]), Path(manifest["original"])
        initial_sha = manifest["initialSHA256"]
        architecture.check(job_dir, donor, initial_sha)
    else:
        project, donor = Path(manifest["scratch"]), Path(manifest["source"])
        initial_sha = manifest["scratchInitialSHA256"]
        group.manifest_for(state)
        require(initial_sha == manifest["sourceSHA256"] and "adoptedPrior174Stage" not in manifest,
                "R03_MAILBOX_GROUP_REQUIRES_FRESH_COPY")
    require(project.is_file() and donor.is_file() and project.resolve() == project
            and project.parent == job_dir / "model" and not project.samefile(donor)
            and state.resolve() == state and record.resolve() == record
            and manifest["authorizationRef"] == authorization, "R03_MAILBOX_COPY_SCOPE_DRIFT")
    return state, record, manifest, project, initial_sha


def prepare_profile(root, job_dir, kind):
    job_dir = job_dir.resolve(strict=True)
    state, record, _, project, initial_sha = staging(job_dir, kind)
    require(sha256(project) == initial_sha and not (state / "attempted.json").exists()
            and not Path(str(project) + ".apa-write.lock").exists(), "R03_MAILBOX_ALREADY_ATTEMPTED")
    release = read_release(root)
    path = job_dir / "mailbox-profile.json"
    config = dict(schema=PROFILE, kind=kind, target=job_dir.name,
                  releaseRevision=release["revision"], releaseManifestSha256=sha256(root / MANIFEST),
                  stageReceiptSha256=sha256(record))
    profile = Campaign(root, path, config=config)
    write_new_json(path, config)
    return profile.health() | {"profile": str(path), "bindingSha256": sha256(path)}


def listener(port):
    """Resolve the Windows listener to one Archicad process and start time."""
    require(type(port) is int and 19723 <= port <= 19743, "R03_MAILBOX_ARCHICAD_PORT_REQUIRED")
    script = (
        f"$c = @(Get-NetTCPConnection -State Listen -LocalPort {port} -ErrorAction Stop "
        "| Select-Object -ExpandProperty OwningProcess -Unique)\n"
        "if ($c.Count -ne 1) { exit 2 }\n"
        "$p = Get-Process -Id $c[0] -ErrorAction Stop\n"
        "if ($p.ProcessName -ne 'Archicad') { exit 3 }\n"
        "@{pid=$p.Id; startedAt=$p.StartTime.ToUniversalTime().ToString('o')} | ConvertTo-Json -Compress"
    )
    response = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
                              capture_output=True, timeout=20)
    require(response.returncode == 0, "R03_MAILBOX_ARCHICAD_LISTENER_NOT_FOUND")
    return dict(json.loads(response.stdout), port=port)


def project_ports(pid=None):
    script = (
        "$ports = @(Get-NetTCPConnection -State Listen -ErrorAction Stop | "
        "Where-Object {$_.LocalPort -ge 19723 -and $_.LocalPort -le 19743"
        + (f" -and $_.OwningProcess -eq {pid}" if pid is not None else "") + "} | "
        "Select-Object -ExpandProperty LocalPort -Unique)\n"
        "ConvertTo-Json -InputObject $ports -Compress"
    )
    response = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
                              capture_output=True, timeout=15)
    require(response.returncode == 0, "R03_MAILBOX_LISTENER_ENUMERATION_FAILED")
    return json.loads(response.stdout)


def open_test_port(project):
    """Discover only loopback listeners that already report this exact test PLN."""
    matches = []
    for port in project_ports():
        try:
            listener(port)
            info = group.R.tapir(port, "GetProjectInfo", {}, timeout=2)
        except (RuntimeError, urllib.error.URLError, OSError):
            continue
        if (info.get("projectPath") == str(project) and info.get("isUntitled") is False
                and info.get("isTeamwork") is False):
            matches.append(port)
    require(len(matches) <= 1, "R03_MAILBOX_EXACT_PROJECT_OPEN_IN_MULTIPLE_INSTANCES")
    return next(iter(matches), None)


class Campaign:
    job_schema = JOB
    def __init__(self, root, path, *, config=None):
        self.root = Path(root).resolve()
        self.path = Path(path).absolute()
        self.job_dir = self.path.parent.resolve(strict=True)
        self.config = read_json(self.path) if config is None else config
        self.target = self.job_dir.name
        require(self.path == self.job_dir / "mailbox-profile.json"
                and self.path.resolve() == self.path
                and not self.job_dir.is_relative_to(LEGACY_ROOT.resolve())
                and re.fullmatch(r"r03-[a-z0-9-]{5,40}", self.target),
                "R03_MAILBOX_PROFILE_PATH_INVALID")
        keys = {"schema", "kind", "target", "releaseRevision", "releaseManifestSha256", "stageReceiptSha256"}
        require(set(self.config) == keys and self.config["schema"] == PROFILE
                and self.config["target"] == self.target and self.config["kind"] in SOURCES,
                "R03_MAILBOX_PROFILE_SCHEMA_INVALID")
        self.release = read_release(self.root)
        require(self.release["revision"] == self.config["releaseRevision"]
                and HEX40.fullmatch(self.release["revision"])
                and sha256(self.root / MANIFEST) == self.config["releaseManifestSha256"],
                "R03_MAILBOX_RELEASE_DRIFT")
        self.kind = self.config["kind"]
        self.state, self.stage, self.manifest, self.project, self.initial_sha = staging(self.job_dir, self.kind)
        require(sha256(self.stage) == self.config["stageReceiptSha256"], "R03_MAILBOX_STAGE_RECEIPT_DRIFT")
        self.history = self.job_dir / "mailbox-jobs"
        self.session_path = self.job_dir / "mailbox-plan-session.json"
        self.closed_path = self.job_dir / "mailbox-closed-phase.json"
        require(all(path.resolve() == path for path in (self.history, self.session_path, self.closed_path)),
                "R03_MAILBOX_HISTORY_PATH_DRIFT")
        self.source_path = SOURCES[self.kind]
        self.source = verify_member(self.root, self.release, self.source_path).read_bytes()
        if self.kind == "ARCHITECTURE":
            matches = self.source == (self.job_dir / "intent.json").read_bytes()
        else:
            matches = json.loads(self.source) == self.manifest["placements"]
        require(matches, "R03_MAILBOX_SOURCE_DOES_NOT_MATCH_STAGING")
        self.verify_code()
        binary = read_json(verify_member(self.root, self.release, "native/binary-receipt.json"))["binary"]
        require(sha256(APX) == binary["apxSHA256"], "R03_MAILBOX_INSTALLED_APX_DRIFT")
        self.pinned_runtime = binary["sourceRevision"], binary["buildIdentity"]
        self.apx_sha = binary["apxSHA256"]

    def verify_code(self):
        for relative in self.release["files"]:
            if relative.startswith(("scripts/", "schemas/")) or relative in ("apa.py", "apa_release.py"):
                verify_member(self.root, self.release, relative)

    def health(self):
        return dict(status="R03_MAILBOX_LOCAL_BINDING_VERIFIED", target=self.target, kind=self.kind,
                    releaseRevision=self.release["revision"], stagedPlnSha256=self.initial_sha,
                    currentPlnSha256=sha256(self.project), apxSha256=self.apx_sha,
                    sourcePath=self.source_path, nativeCalls=0)

    def phase(self, name):
        tail = name.removeprefix(self.target + "-")
        require(tail != name and re.fullmatch(r"(plan|execute|closed|reopen)(?:-[1-9][0-9]?)?", tail),
                "R03_MAILBOX_JOB_ID_OUTSIDE_PROFILE")
        phase = tail.split("-")[0]
        require(phase != "execute" or tail == phase, "R03_MAILBOX_EXECUTE_ID_MUST_BE_UNIQUE")
        return PHASES[phase]

    def preflight_path(self):
        return self.state / ("approved-preflight.json" if self.kind == "ARCHITECTURE" else "plan.json")

    def planned_session(self):
        session = read_json(self.session_path)
        require(session["preflightSha256"] == sha256(self.preflight_path())
                and session["target"] == self.target
                and session["bindingSha256"] == sha256(self.path), "R03_MAILBOX_PREFLIGHT_SESSION_DRIFT")
        return session["listener"]

    def saved(self):
        if self.kind == "ARCHITECTURE":
            return architecture.saved_record(self.state, self.manifest)
        return group.saved_state(self.state)[1]

    def phase_file_hashes(self, action):
        if action == "PLAN":
            return self.initial_sha, None
        self.planned_session()
        project_sha = self.initial_sha if action == "EXECUTE" else self.saved()["savedSHA256"]
        return project_sha, sha256(self.preflight_path())

    def envelope(self, bridge, name):
        action = self.phase(name)
        project_sha, plan_sha = self.phase_file_hashes(action)
        require(sha256(self.project) == project_sha, "R03_MAILBOX_LOCAL_PLN_DRIFT")
        now = bridge.current_utc()
        return dict(schema=JOB, jobId=name, target=self.target, action=action,
                    createdAt=now.isoformat().replace("+00:00", "Z"),
                    expiresAt=(now + timedelta(hours=2)).isoformat().replace("+00:00", "Z"),
                    releaseRevision=self.release["revision"], bindingSha256=sha256(self.path),
                    projectSha256=project_sha, preflightSha256=plan_sha,
                    sourceTask=dict(repo=SOURCE_REPO, ref=self.release["revision"],
                                    path=self.source_path, blobSha1=bridge.git_sha(self.source)))

    def fetch(self, bridge, name):
        expected = self.envelope(bridge, name)
        job, blob = bridge.remote_json(bridge.BRIDGE, f"{bridge.INBOX}/{name}.json", "main")
        require(set(job) == set(expected) and all(job[k] == v for k, v in expected.items()
                if k not in {"createdAt", "expiresAt"}), "R03_MAILBOX_ENVELOPE_SCOPE_DRIFT")
        start, end = bridge.date(job["createdAt"]), bridge.date(job["expiresAt"])
        require(start <= bridge.current_utc() < end and end - start <= timedelta(days=1),
                "R03_MAILBOX_JOB_TIME_WINDOW_INVALID")
        ref = job["sourceTask"]
        source, _ = bridge.remote_json(ref["repo"], ref["path"], ref["ref"], ref["blobSha1"])
        require(source == json.loads(self.source), "R03_MAILBOX_SOURCE_READBACK_DRIFT")
        return job, blob

    def grant(self, bridge, name, *, create=False, confirm=None):
        require(self.phase(name) == "EXECUTE", "R03_MAILBOX_GRANT_ONLY_FOR_EXECUTE")
        job, blob = self.fetch(bridge, name)
        self.require_plan_result(bridge, read_only=create)
        grant = dict(schema="APA_AC29_R03_LOCAL_GRANT_V1", job=job, jobBlobSha1=blob,
                     stageReceiptSha256=self.config["stageReceiptSha256"])
        path = self.job_dir / "mailbox-local-grant.json"
        require(path.resolve() == path, "R03_MAILBOX_GRANT_PATH_DRIFT")
        if create:
            require(confirm == job["preflightSha256"], "R03_MAILBOX_EXPLICIT_PREFLIGHT_SHA_REQUIRED")
            require(not (self.history / name).exists(), "R03_MAILBOX_ALREADY_ATTEMPTED")
            temporary = path.with_name("mailbox-local-grant.pending")
            write_new_json(temporary, grant)
            # Publish a complete grant as one exclusive operation. A worker
            # never sees a partial JSON file or a reissued authorization.
            try:
                os.link(temporary, path)
            finally:
                temporary.unlink()
        else:
            require(path.is_file() and read_json(path) == grant, "R03_MAILBOX_LOCAL_GRANT_MISSING_OR_DRIFTED")
        return job, blob

    def require_published_result(self, folder, action):
        result, marker = read_json(folder / "result.json"), read_json(folder / "published.json")
        require(result["jobId"] == folder.name and result["action"] == action
                and result["result"]["target"] == self.target
                and result["result"]["bindingSha256"] == sha256(self.path)
                and marker["verifiedBytes"] is True, "R03_MAILBOX_PREVIOUS_RESULT_MISSING_OR_DRIFTED")
        return result["result"]

    def require_plan_result(self, bridge, *, read_only=False):
        session = read_json(self.session_path)
        self.planned_session()
        require(self.phase(session["planJob"]) == "PLAN", "R03_MAILBOX_PLAN_JOB_DRIFT")
        folder = self.history / session["planJob"]
        result = self.require_published_result(folder, "PLAN")
        require(result["jobStatus"] == "READY_FOR_EXPLICIT_TEST_RUN"
                and result["preflightSha256"] == sha256(self.preflight_path()), "R03_MAILBOX_PLAN_NOT_PUBLISHED")
        if read_only:
            remote, _ = bridge.remote_json(bridge.BRIDGE,
                f"{bridge.RESULTS}/{session['planJob']}.json", "main", bridge.git_sha((folder / "result.json").read_bytes()))
            require(remote["result"] == result, "R03_MAILBOX_PLAN_READBACK_DRIFT")
        else:
            bridge.upload_result(session["planJob"], folder, verify_existing=True)

    def require_saved_result(self, bridge):
        name = f"{self.target}-execute"
        folder = self.history / name
        result = self.require_published_result(folder, "EXECUTE")
        require(result["jobStatus"] == "WAITING_CLOSE_AND_REOPEN"
                and result["savedSha256"] == self.saved()["savedSHA256"], "R03_MAILBOX_SAVE_NOT_PUBLISHED")
        bridge.upload_result(name, folder, verify_existing=True)

    def require_closed_result(self, bridge):
        record = read_json(self.closed_path)
        name = record["closedJob"]
        require(self.phase(name) == "CHECK_CLOSED"
                and record["closedReceiptSha256"] == sha256(self.state / "closed.json"),
                "R03_MAILBOX_CLOSE_RECEIPT_DRIFT")
        folder = self.history / name
        result = self.require_published_result(folder, "CHECK_CLOSED")
        require(result["jobStatus"] == "READY_FOR_REOPEN"
                and result["closedReceiptSha256"] == record["closedReceiptSha256"],
                "R03_MAILBOX_CLOSE_NOT_PUBLISHED")
        bridge.upload_result(name, folder, verify_existing=True)

    def group_identity(self, port, *, saved_sha=None):
        manifest = dict(self.manifest, port=port)
        api, _ = group.prepare_api(manifest, self.state, execute=False, saved_sha=saved_sha)
        group.IDENTITY.current_project(api, manifest["scratch"])
        return architecture.runtime_identity(api, self.pinned_runtime)

    def run_plan(self, name, port):
        before = listener(port)
        require(not self.session_path.exists(), "R03_MAILBOX_PREFLIGHT_ALREADY_BOUND")
        if self.kind == "ARCHITECTURE":
            result = architecture.preflight(self.state, self.manifest, port, self.pinned_runtime)
            if result["status"] != "READY_FOR_EXPLICIT_TEST_RUN":
                return dict(jobStatus="BLOCKED", detail=result.get("reason"), nativeWrites=0)
            plan = read_json(self.preflight_path())
            facts = dict(confirmPlanHash=plan["confirmHash"], metrics=result["metrics"])
        else:
            runtime = self.group_identity(port)
            plan = group.plan(self.state, port=port)
            require(plan["runtimeIdentity"] == runtime and plan["nativeWrites"] == 0,
                    "R03_MAILBOX_GROUP_RUNTIME_OR_PREFLIGHT_DRIFT")
            facts = dict(groupCount=self.manifest["groupCount"], baselineGuidCount=len(plan["baselineGuids"]),
                         cloneContractSha256=plan["contractSHA256"])
        require(listener(port) == before and sha256(self.project) == self.initial_sha,
                "R03_MAILBOX_PLAN_PROCESS_OR_PLN_DRIFT")
        plan_sha = sha256(self.preflight_path())
        write_new_json(self.session_path, dict(target=self.target, listener=before, planJob=name,
                       preflightSha256=plan_sha, bindingSha256=sha256(self.path)))
        return dict(jobStatus="READY_FOR_EXPLICIT_TEST_RUN", preflightSha256=plan_sha,
                    baselineGuidSetSha256=self.manifest["baselineGuidSetSHA256"],
                    baselineBrepSha256=self.manifest["baselineBrepSHA256"],
                    nativeWrites=0, saveReopenVerified=False, **facts)

    def run_execute(self, session):
        port = session["port"]
        require(listener(port) == session, "R03_MAILBOX_EXECUTE_PROCESS_DRIFT")
        if self.kind == "ARCHITECTURE":
            result = architecture.execute(self.state, self.manifest, self.pinned_runtime)
            require(result["status"] == "LIVE_ARCHITECTURE_SAVED_PENDING_REAL_REOPEN",
                    "R03_MAILBOX_ARCHITECTURE_INCOMPLETE:" + str(result.get("reason", result["status"])))
            facts = dict(guidCount=result["elementCount"], addedGuids=result["addedGuids"],
                         addedByKind=result["addedByKind"], bodyCountByAddedGuid=result["bodyCountByAddedGuid"],
                         nativeModelWriteAttempts=result["nativeModelWriteAttempts"], saveCalls=result["nativeSaveCalls"])
        else:
            self.group_identity(port)
            result = group.execute(self.state, port=port)
            require(result["status"] == "GROUP_BATCH_SAVED_PENDING_REAL_REOPEN", "R03_MAILBOX_GROUP_INCOMPLETE")
            facts = dict(guidCount=result["finalGuidCount"], groupCount=result["groupCount"],
                         nativeCloneCalls=result["nativeCloneCalls"], saveCalls=result["saveCalls"],
                         addedGuids=sorted(result["nativeReadback"]["newRootGuids"]
                                           + result["nativeReadback"]["newSegmentGuids"]))
        require(listener(port) == session and self.saved()["savedSHA256"] == result["savedSHA256"],
                "R03_MAILBOX_SAVED_PROCESS_OR_PLN_DRIFT")
        return dict(jobStatus="WAITING_CLOSE_AND_REOPEN", saveReopenVerified=False,
                    savedSha256=result["savedSHA256"], guidSetSha256=result["finalGuidSetSHA256"],
                    brepSha256=result["finalBrepSHA256"], savedReceiptSha256=sha256(self.state / "saved.json"),
                    authorizedNativeExecution=True, **facts)

    def run_closed(self, name, session):
        pid, port = session["pid"], session["port"]
        exited = reservation_owner_exited(pid)
        if not exited:
            require(listener(port) == session, "R03_MAILBOX_CLOSE_PROCESS_DRIFT")
        if self.kind == "ARCHITECTURE":
            closed = architecture.check_closed(self.state, self.manifest, self.pinned_runtime, process_id=pid)
            if closed["status"] == "NATIVE_NO_OPEN_PROJECT_CONFIRMED":
                require(listener(port) == session, "R03_MAILBOX_CLOSE_PROCESS_DRIFT")
        else:
            saved = self.saved()
            status = "ARCHICAD_TEST_PROCESS_EXIT_CONFIRMED"
            if not exited:
                api, _ = group.prepare_api(dict(self.manifest, port=port), self.state, execute=False,
                                           saved_sha=saved["savedSHA256"])
                require(architecture.runtime_identity(api, self.pinned_runtime)
                        == read_json(self.preflight_path())["runtimeIdentity"], "R03_MAILBOX_CLOSE_RUNTIME_DRIFT")
                confirm_project_closed(api)
                require(listener(port) == session, "R03_MAILBOX_CLOSE_PROCESS_DRIFT")
                status = "NATIVE_NO_OPEN_PROJECT_CONFIRMED"
            require(self.saved() == saved, "R03_MAILBOX_SAVED_BYTES_CHANGED_AT_CLOSE")
            closed = dict(schema=group.SCHEMA, status=status, savedSHA256=saved["savedSHA256"],
                          nativeWrites=0, pid=pid, port=port)
            write_new_json(self.state / "closed.json", closed)
        closed_sha = sha256(self.state / "closed.json")
        write_new_json(self.closed_path, dict(closedJob=name, closedReceiptSha256=closed_sha))
        return dict(jobStatus="READY_FOR_REOPEN", closeEvidence=closed["status"], nativeWrites=0,
                    closedReceiptSha256=closed_sha, saveReopenVerified=False)

    def run_reopen(self, session, port):
        closed = read_json(self.state / "closed.json")
        require(closed.get("pid") == session["pid"] and closed.get("port") == session["port"],
                "R03_MAILBOX_CLOSE_SESSION_DRIFT")
        before = listener(port)
        if closed["status"] == "NATIVE_NO_OPEN_PROJECT_CONFIRMED":
            require(before == session, "R03_MAILBOX_REOPEN_PROCESS_DRIFT")
        else:
            require(reservation_owner_exited(session["pid"]), "R03_MAILBOX_OLD_PROCESS_STILL_RUNNING")
        if self.kind == "ARCHITECTURE":
            result = architecture.verify_reopen(self.state, self.manifest, self.pinned_runtime, port)
        else:
            self.group_identity(port, saved_sha=self.saved()["savedSHA256"])
            result = group.verify_reopen(self.state, reopen_port=port)
        saved = self.saved()
        require(listener(port) == before and result["reopenVerified"] is True
                and result["reopenedGuidSetSHA256"] == saved["finalGuidSetSHA256"]
                and result["reopenedBrepSHA256"] == saved["finalBrepSHA256"]
                and result["savedSHA256"] == saved["savedSHA256"] and result["verificationNativeWrites"] == 0,
                "R03_MAILBOX_REOPEN_READBACK_MISMATCH")
        return dict(jobStatus="COMPLETE", verification="SAVE_REOPEN_VERIFIED", saveReopenVerified=True,
                    nativeWrites=0, savedSha256=result["savedSHA256"], guids=result["reopenedGuids"],
                    guidSetSha256=result["reopenedGuidSetSHA256"], brepSha256=result["reopenedBrepSHA256"],
                    reopenedReceiptSha256=sha256(self.state / "reopened.json"))

    def poll_job(self, bridge, name):
        action = self.phase(name)
        folder = self.history / name
        require(folder.resolve() == folder, "R03_MAILBOX_JOB_HISTORY_PATH_DRIFT")
        if (folder / "published.json").is_file():
            return
        if folder.exists():
            return self.process(bridge, name)
        require(self.path.resolve() == self.path and read_json(self.path) == self.config
                and sha256(self.stage) == self.config["stageReceiptSha256"]
                and sha256(self.root / MANIFEST) == self.config["releaseManifestSha256"]
                and sha256(APX) == self.apx_sha, "R03_MAILBOX_CONFIG_OR_RELEASE_DRIFT")
        if self.kind == "ARCHITECTURE":
            architecture.check(self.job_dir, Path(self.manifest["original"]), self.initial_sha)
        else:
            group.manifest_for(self.state)
        if action == "EXECUTE":
            if not (self.job_dir / "mailbox-local-grant.json").is_file():
                return
            session = self.planned_session()
            if open_test_port(self.project) != session["port"] or listener(session["port"]) != session:
                return
        if action in {"CHECK_CLOSED", "VERIFY_REOPEN"}:
            if not (self.state / "saved.json").is_file():
                return
            if action == "VERIFY_REOPEN" and not self.closed_path.is_file():
                return
        self.fetch(bridge, name)
        port = open_test_port(self.project) if action in {"PLAN", "VERIFY_REOPEN"} else None
        if action in {"PLAN", "VERIFY_REOPEN"} and port is None:
            return
        if action == "CHECK_CLOSED":
            session = self.planned_session()
            if not reservation_owner_exited(session["pid"]):
                try:
                    if listener(session["port"]) != session:
                        return
                    confirm_project_closed(lambda cmd, params: group.R.tapir(session["port"], cmd, params,
                                                                          timeout=2))
                except (ValueError, RuntimeError, OSError):
                    return
        self.verify_code()
        return self.process(bridge, name, port=port)

    def record_failure(self, bridge, folder, action, exc):
        error = type(exc).__name__ + ": " + str(exc)
        bridge.durable_write(folder / "diagnostic.json", dict(error=error, action=action))
        if action != "EXECUTE":
            return dict(jobStatus="BLOCKED", nativeOutcome="NO_MODEL_WRITE",
                        error=error.replace(str(self.job_dir), self.target)[:360], saveReopenVerified=False)
        reserved = (self.state / "attempted.json").exists() or Path(str(self.project) + ".apa-write.lock").exists()
        outcome = "UNKNOWN" if reserved else "NOT_EXECUTED"
        if self.kind == "ARCHITECTURE" and outcome == "UNKNOWN":
            try:
                creation = read_json(self.state / "build" / "result.json")
                if creation["status"] == "COMPLETE_UNSAVED" and not (self.state / "saved.json").exists():
                    trace = self.state / "save-trace" / "dispatch.jsonl"
                    if not trace.exists() or not any(json.loads(line)["command"] == "SaveProject"
                                                      for line in trace.read_text(encoding="utf-8").splitlines()):
                        outcome = "EXECUTED_UNSAVED"
            except (OSError, ValueError, KeyError, TypeError):
                pass  # The evidence cannot narrow the unknown native outcome.
        return dict(jobStatus="STOPPED_RECONCILE_NO_AUTORETRY", nativeOutcome=outcome,
                    error=error.replace(str(self.job_dir), self.target)[:360], saveReopenVerified=False)

    def process(self, bridge, name, *, port=None):
        """Reserve once, dispatch to existing runtime, publish only durable results."""
        action = self.phase(name)
        binding_sha = sha256(self.path)
        folder = self.history / name
        require(folder.resolve() == folder, "R03_MAILBOX_JOB_HISTORY_PATH_DRIFT")
        common = dict(target=self.target, releaseRevision=self.release["revision"], bindingSha256=binding_sha)
        if folder.exists():
            attempt = read_json(folder / "attempted.json")
            require(attempt["job"] == name and attempt["action"] == action
                    and attempt["bindingSha256"] == binding_sha and HEX40.fullmatch(attempt["sourceBlob"]),
                    "R03_MAILBOX_ATTEMPT_IDENTITY_DRIFT")
            if not (folder / "result.json").exists():
                response = dict(common, jobStatus="STOPPED_RECONCILE_NO_AUTORETRY",
                                nativeOutcome="UNKNOWN" if action == "EXECUTE" else "NO_MODEL_WRITE",
                                saveReopenVerified=False, error="INTERRUPTED_AFTER_DURABLE_RESERVATION")
                bridge.durable_write(folder / "result.json",
                                     bridge.result_payload(name, action, attempt["sourceBlob"], response))
            recorded = read_json(folder / "result.json")
            require(recorded["jobId"] == name and recorded["action"] == action
                    and recorded["sourceBlob"] == attempt["sourceBlob"]
                    and recorded["result"]["bindingSha256"] == binding_sha, "R03_MAILBOX_RESULT_IDENTITY_DRIFT")
            bridge.upload_result(name, folder, verify_existing=True)
            return recorded

        if action == "EXECUTE":
            job, blob = self.grant(bridge, name)
            require(not (self.state / "attempted.json").exists()
                    and not Path(str(self.project) + ".apa-write.lock").exists(), "R03_MAILBOX_ALREADY_ATTEMPTED")
        else:
            job, blob = self.fetch(bridge, name)
        if action in {"CHECK_CLOSED", "VERIFY_REOPEN"}:
            self.require_saved_result(bridge)
        if action == "VERIFY_REOPEN":
            self.require_closed_result(bridge)
        require(bridge.gh_api(f"repos/{bridge.BRIDGE}/contents/{bridge.RESULTS}/{name}.json?ref=main",
                              allow_missing=True) is None, "R03_MAILBOX_REMOTE_RESULT_ALREADY_EXISTS")
        session = None if action == "PLAN" else self.planned_session()
        require(port is None or action in {"PLAN", "VERIFY_REOPEN"}, "R03_MAILBOX_PORT_FROM_LOCAL_PREFLIGHT")
        if action == "PLAN":
            require(type(port) is int and 19723 <= port <= 19743, "R03_MAILBOX_PLAN_REQUIRES_LOCAL_PORT")
        self.history.mkdir(exist_ok=True)
        folder.mkdir()
        bridge.durable_write(folder / "attempted.json", dict(job=name, action=action, bindingSha256=binding_sha,
                             sourceBlob=blob, projectSha256=job["projectSha256"],
                             startedAt=bridge.current_utc().isoformat(), automaticRetry=False))
        try:
            if action == "PLAN":
                response = self.run_plan(name, port)
            elif action == "EXECUTE":
                response = self.run_execute(session)
            elif action == "CHECK_CLOSED":
                response = self.run_closed(name, session)
            else:
                response = self.run_reopen(session, port if port is not None else session["port"])
        except Exception as exc:
            response = self.record_failure(bridge, folder, action, exc)
        response.update(common)
        payload = bridge.result_payload(name, action, blob, response)
        bridge.durable_write(folder / "result.json", payload)
        bridge.upload_result(name, folder, verify_existing=True)
        return payload
