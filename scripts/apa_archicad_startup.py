"""Observe Windows startup for one already staged test copy."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import time
from types import SimpleNamespace

from apa_ac29_save_isolation import require, timestamp, write_new_json
from apa_r03_mailbox import Campaign, group, listener, project_ports
from apa_mailbox_profile import APX
from apa_release import read_json, read_release, sha256, verify_member


ARCHICAD = Path(r"C:\Program Files\Graphisoft\Archicad 29")
STARTERS = {"direct": "Archicad.exe", "starter": "Archicad Starter.exe"}
PROBE_ERRORS = (OSError, RuntimeError, ValueError, subprocess.SubprocessError)


def archicad_processes():
    script = (
        "$p = @(Get-CimInstance Win32_Process -Filter \"Name='Archicad.exe' OR Name='Archicad Starter.exe'\" "
        "-ErrorAction Stop | Select-Object ProcessId,ParentProcessId,ExecutablePath,"
        "@{Name='startedAt';Expression={$_.CreationDate.ToUniversalTime().ToString('o')}})\n"
        "ConvertTo-Json -InputObject $p -Compress"
    )
    response = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
                              capture_output=True, timeout=12)
    require(response.returncode == 0, "APA_STARTUP_PROCESS_ENUMERATION_FAILED")
    known_paths = {(ARCHICAD / exe).resolve() for exe in STARTERS.values()}
    return [row for row in json.loads(response.stdout) if row["ExecutablePath"]
            and Path(row["ExecutablePath"]).resolve() in known_paths]


def followed_processes(snapshot, tracked):
    """Follow the exact launch or observe PID, including a Starter child."""
    for row in sorted(snapshot, key=lambda p: p["startedAt"]):
        pid, parent, started = row["ProcessId"], row["ParentProcessId"], row["startedAt"]
        if pid in tracked and tracked[pid] is None:
            tracked[pid] = started
        elif pid not in tracked and parent in tracked:
            parent_started = tracked[parent]
            if parent_started is None or started >= parent_started:
                tracked[pid] = started
    return [row for row in snapshot if row["ProcessId"] in tracked
            and row["startedAt"] == tracked[row["ProcessId"]]]


def process_windows(pid):
    import pywintypes
    import win32gui
    import win32process

    found = []

    def visit(handle, _):
        try:
            _, owner_pid = win32process.GetWindowThreadProcessId(handle)
            if owner_pid == pid:
                owner = win32gui.GetWindow(handle, 4)
                found.append(dict(handle=handle, owner=owner or None,
                                  ownerPid=win32process.GetWindowThreadProcessId(owner)[1] if owner else None,
                                  windowClass=win32gui.GetClassName(handle),
                                  caption=win32gui.GetWindowText(handle),
                                  visible=bool(win32gui.IsWindowVisible(handle)),
                                  enabled=bool(win32gui.IsWindowEnabled(handle))))
        except pywintypes.error:
            if win32gui.IsWindow(handle):
                raise
        return True

    try:
        win32gui.EnumWindows(visit, None)
    except pywintypes.error as exc:
        raise OSError("APA_STARTUP_WINDOW_ENUMERATION_FAILED") from exc
    return found


def pending_window(windows, pid):
    candidates = []
    for row in windows:
        if (not row["visible"] or not row["enabled"]
                or row["windowClass"] not in {"DGModalDlgClass", "#32770"}
                or row["ownerPid"] not in (pid, None)):
            continue
        title = row["caption"].casefold()
        if ("восстанов" in title and "проект" in title) or ("recover" in title and "project" in title):
            kind = "POSSIBLE_PROJECT_RECOVERY"
        elif any(key in title for key in ("сохран", "save changes", "save project")):
            kind = "POSSIBLE_SAVE_PROMPT"
        elif any(key in title for key in ("ошибка", "error", "license", "лицензи")):
            kind = "POSSIBLE_ERROR_DIALOG"
        else:
            kind = "UNCLASSIFIED_MODAL"
        candidates.append(dict(row, kind=kind, requiresOperator=True))
    return candidates


def inspect_project(campaign, pid, ports, windows, read):
    observation = dict(pid=pid, windows=windows, dialogs=pending_window(windows, pid),
                       listeningPorts=ports, nativeModelWrites=0)
    if observation["dialogs"]:
        return dict(observation, status="WAITING_FOR_OPERATOR")
    if not ports:
        return dict(observation, status="MAIN_WINDOW_READY" if any(w["visible"] and w["caption"] for w in windows)
                    else "PROCESS_CREATED")
    issues = []
    for port in ports:
        try:
            project = read(port, "GetProjectInfo")
        except PROBE_ERRORS as exc:
            issues.append(dict(port=port, phase="PROJECT_INFO", error=str(exc)[:220]))
            continue
        if (project.get("projectPath") != str(campaign.project) or project.get("projectName") != campaign.project.stem
                or project.get("isUntitled") is not False
                or project.get("isTeamwork") is not False):
            issues.append(dict(port=port, phase="PROJECT_IDENTITY", observed=project.get("projectPath")))
            continue
        try:
            product = read(port, "API.GetProductInfo")
            version = read(port, "GetAddOnVersion")
            runtime = read(port, "GetAPARuntimeInfoV1")
        except PROBE_ERRORS as exc:
            issues.append(dict(port=port, phase="RUNTIME_IDENTITY", error=str(exc)[:220]))
            continue
        if (product.get("version") == 29 and product.get("buildNumber") == 5101
                and version.get("version") == "1.5.10" and runtime.get("contract") == "APA_NATIVE_RUNTIME_IDENTITY_V1"
                and runtime.get("sdkMajor") == 29 and runtime.get("nativeModelWrites") == 0
                and (runtime.get("sourceRevision"), runtime.get("buildIdentity")) == campaign.pinned_runtime):
            return dict(observation, status="PROJECT_IDENTITY_VERIFIED", port=port,
                        project=str(campaign.project), product=product, runtime=runtime)
        issues.append(dict(port=port, phase="RUNTIME_IDENTITY", reason="ARCHICAD_OR_LOADED_APX_MISMATCH"))
    return dict(observation, status="API_LISTENING", issues=issues)


def observe(campaign, processes):
    import urllib.request

    def read(port, command):
        if command != "API.GetProductInfo":
            return group.R.tapir(port, command, {}, timeout=2)
        request = urllib.request.Request(
            f"http://127.0.0.1:{port}", data=json.dumps(dict(command=command, parameters={})).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(request, timeout=2) as reply:
            response = json.load(reply)
        require(response.get("succeeded") is True and isinstance(response.get("result"), dict),
                "APA_STARTUP_ARCHICAD_PRODUCT_INFO_UNAVAILABLE")
        return response["result"]

    observations = []
    for process in processes:
        pid = process["ProcessId"]
        try:
            candidates = {port: listener(port) for port in project_ports(pid)}
            ports = [port for port, identity in candidates.items() if identity["pid"] == pid]
            row = inspect_project(campaign, pid, ports, process_windows(pid), read)
            if row["status"] == "PROJECT_IDENTITY_VERIFIED":
                port = row["port"]
                identity = listener(port)
                require(identity == candidates[port], "APA_STARTUP_API_LISTENER_CHANGED")
                row["listener"] = identity
            observations.append(dict(row, process=process))
        except PROBE_ERRORS as exc:
            observations.append(dict(status="OBSERVATION_UNAVAILABLE", pid=pid, error=str(exc),
                                     nativeModelWrites=0))
    return observations


def resume_session(folder, source, expected, pid):
    """Reobserve a previously blocked recovery copy in the exact same instance."""
    path = folder / "startup.json"
    previous = read_json(path)
    launch = read_json(folder / "launch-intent.json")
    project = folder / "model" / source.name
    require(path.resolve(strict=True) == path and project.resolve(strict=True) == project
            and previous["status"] == "WAITING_FOR_OPERATOR"
            and previous["project"] == launch["project"] == str(project)
            and previous["originalProject"] == str(source)
            and previous["projectSha256"] == launch["sha256"] == sha256(project) == expected
            and previous["plnBytesUnchanged"] is True and previous["nativeModelWrites"] == 0
            and not project.samefile(source), "APA_STARTUP_RESUME_SOURCE_DRIFT")
    last = next((row for row in reversed(previous["events"])
                 if row.get("status") == "WAITING_FOR_OPERATOR" and row.get("pid") == pid), None)
    require(last is not None and last.get("process", {}).get("ProcessId") == pid
            and last["process"].get("startedAt"), "APA_STARTUP_RESUME_PID_NOT_PROVEN")
    return project, last["process"], sha256(path)


def main(argv=None):
    root = Path(__file__).resolve().parents[1]
    cli = argparse.ArgumentParser(description=__doc__)
    target = cli.add_mutually_exclusive_group(required=True)
    target.add_argument("--r03-profile", type=Path)
    target.add_argument("--saved-group-state", type=Path)
    cli.add_argument("--phase", choices=("staged", "saved"), required=True)
    cli.add_argument("--output", type=Path, required=True)
    cli.add_argument("--recovery-copy", type=Path, help="A fresh diagnostic PLN from a closed saved group")
    cli.add_argument("--resume", action="store_true",
                     help="Append an observation in an existing saved-group recovery-copy directory")
    mode = cli.add_mutually_exclusive_group(required=True)
    mode.add_argument("--launch", choices=STARTERS)
    mode.add_argument("--pid", type=int)
    cli.add_argument("--timeout", type=int, default=45)
    args = cli.parse_args(argv)
    require(not args.resume or (args.saved_group_state and args.pid and args.recovery_copy is None),
            "APA_STARTUP_RESUME_REQUIRES_SAVED_GROUP_PID")
    if args.saved_group_state:
        require(args.phase == "saved", "APA_STARTUP_HISTORICAL_GROUP_REQUIRES_SAVED_PHASE")
        state = args.saved_group_state.resolve(strict=True)
        manifest, saved = group.saved_state(state)
        group.group_close_proof(state, manifest, saved)
        project = Path(manifest["scratch"]).resolve(strict=True)
        require(project.parent == state.parent / "model" and not project.samefile(manifest["source"]),
                "APA_STARTUP_HISTORICAL_GROUP_COPY_SCOPE_DRIFT")
        binary = read_json(verify_member(root, read_release(root), "native/binary-receipt.json"))["binary"]
        require(sha256(APX) == binary["apxSHA256"], "APA_STARTUP_INSTALLED_APX_DRIFT")
        campaign = SimpleNamespace(project=project,
                                   pinned_runtime=(binary["sourceRevision"], binary["buildIdentity"]))
        expected = saved["savedSHA256"]
    else:
        require(args.recovery_copy is None, "APA_STARTUP_RECOVERY_COPY_REQUIRES_CLOSED_SAVED_GROUP")
        campaign = Campaign(root, args.r03_profile)
        expected = campaign.saved()["savedSHA256"] if args.phase == "saved" else campaign.initial_sha
    require(sha256(campaign.project) == expected and 5 <= args.timeout <= 120
            and (args.pid is None or args.pid > 0), "APA_STARTUP_TEST_BYTES_OR_OPTIONS_INVALID")
    args.output = args.output.resolve()
    if not args.resume:
        args.output.mkdir()
    source_project = campaign.project
    prior_process = None
    resume_proof = None
    if args.resume:
        campaign.project, prior_process, resume_proof = resume_session(
            args.output, source_project, expected, args.pid)
        require(prior_process in archicad_processes(), "APA_STARTUP_RESUME_PROCESS_CHANGED")
    if args.recovery_copy:
        from apa_ac29_save_isolation import copy_exclusive

        recovery = args.recovery_copy.resolve()
        require(recovery.suffix.casefold() == ".pln" and recovery.name == source_project.name
                and recovery.parent == args.output.resolve() / "model" and args.launch,
                "APA_STARTUP_FRESH_RECOVERY_COPY_PATH_REQUIRED")
        recovery.parent.mkdir()
        copy_exclusive(source_project, recovery)
        require(sha256(recovery) == sha256(source_project) == expected, "APA_STARTUP_RECOVERY_COPY_BYTES_DRIFT")
        campaign.project = recovery
    events = []
    child = None
    if args.launch:
        lock = Path(str(campaign.project) + ".lck")
        if lock.exists():
            record = dict(status="TEST_PLN_LOCK_PRESENT", project=str(campaign.project),
                          projectSha256=expected, lock=str(lock), nativeModelWrites=0)
            write_new_json(args.output / "startup.json", record)
            print(json.dumps(record, ensure_ascii=False, indent=2))
            return 2
        exe = (ARCHICAD / STARTERS[args.launch]).resolve(strict=True)
        require(exe.parent == ARCHICAD.resolve(), "APA_STARTUP_EXECUTABLE_IDENTITY_DRIFT")
        write_new_json(args.output / "launch-intent.json", dict(executable=str(exe),
                       project=str(campaign.project), sha256=expected))
        child = subprocess.Popen([str(exe), str(campaign.project)], cwd=exe.parent)
        events.append(dict(status="PROCESS_CREATED", pid=child.pid, executable=str(exe)))
    tracked = {child.pid if child else args.pid: prior_process["startedAt"] if prior_process else None}
    deadline = time.monotonic() + args.timeout
    last_rows = None
    while True:
        try:
            snapshot = archicad_processes()
            processes = ([prior_process] if prior_process in snapshot else []) if args.resume else followed_processes(snapshot, tracked)
            rows = observe(campaign, processes)
        except PROBE_ERRORS as exc:
            rows = [dict(status="OBSERVATION_UNAVAILABLE", error=str(exc), nativeModelWrites=0)]
        if rows != last_rows:
            events.extend(rows)
            last_rows = rows
        verified = [row for row in rows if row["status"] == "PROJECT_IDENTITY_VERIFIED"]
        if verified:
            status = "PROJECT_IDENTITY_VERIFIED"
            break
        if any(row["status"] == "WAITING_FOR_OPERATOR" for row in rows):
            status = "WAITING_FOR_OPERATOR"
            break
        if time.monotonic() >= deadline:
            status = ("LAUNCH_PROCESS_EXITED_WITHOUT_VERIFIED_TEST_COPY"
                      if child and child.poll() is not None and not rows else "STARTUP_NOT_VERIFIED")
            break
        time.sleep(1)
    bytes_unchanged = (campaign.project.is_file() and sha256(campaign.project) == expected
                       and source_project.is_file() and sha256(source_project) == expected)
    if not bytes_unchanged:
        status = "TEST_PLN_BYTES_DRIFT"
    verified_row = verified[0] if status == "PROJECT_IDENTITY_VERIFIED" else {}
    receipt = dict(status=status, project=str(campaign.project), projectSha256=expected, events=events,
                   originalProject=str(source_project),
                   plnBytesUnchanged=bytes_unchanged, processExitCode=child.poll() if child else None,
                   verifiedPort=verified_row.get("port"), verifiedListener=verified_row.get("listener"),
                   observedAt=timestamp(), nativeModelWrites=0)
    receipt_path = args.output / "startup.json"
    if args.resume:
        require(sha256(receipt_path) == resume_proof, "APA_STARTUP_RESUME_PRIOR_PROOF_DRIFT")
        from uuid import uuid4

        receipt["priorStartupSha256"] = resume_proof
        receipt_path = args.output / f"startup-resume-{uuid4().hex}.json"
    write_new_json(receipt_path, receipt)
    receipt["receiptPath"] = str(receipt_path)
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0 if status == "PROJECT_IDENTITY_VERIFIED" else 2
