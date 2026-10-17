"""One-time in-place upgrade of the EXISTING APA AC29 GitHub receiver.

Installs only the two reusable execution helpers and a source-pinned worker.
No model writes, no new dispatcher/service, no SQLite mutation, no job replay.
Fails closed if another unrecognized or in-flight worker may be active.
"""
from __future__ import annotations
import base64
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT = Path(r"C:\LocalAI\APA_AC29_Stable")
CTRL = ROOT / "controllers"
STATE = ROOT / "apa-job-bridge-state"
WORKER = CTRL / "apa_ac29_autonomous_job_bridge.py"
REPO = "dvikt33-ux/safe-bim-layer"
SOURCE_COMMIT = "3a44d04e82cca8f0c52f93f7ff72674770680048"
CURRENT_WORKER_SHA1 = "4bf5f463517b3fa95b5c103a9377c3155acb9b2d"
FILES = {
    "apa_ac29_autonomous_job_bridge.py": "71c29d15723c2fda59f169b40ba0f09eddb4ff60",
    "apa_ac29_reusable_native_copy.py": "c16cd5caa2df4b7959bca766dce0e706a7f23dcc",
    "apa_ac29_scene_reconciliation.py": "1ba5d59755f9c96a46d292fe8e282061eb56286a",
}
BASE_WORKING_SHA256 = "e91d5670f20202c269d442bafc6e66a4cb13d223344122243b7237047a9ff3aa"
BASE_PROTECTED_SHA256 = "33b96850ad07547a9b12524de8bc46479fd98fbbce6772436d388be679836d66"
WORKING = Path(r"C:\LocalAI\SafeBIM_Global_Library_Test_Projects\BDD дом - по чертежам 2022.pln")
PROTECTED = Path(r"C:\LocalAI\SafeBIM_Global_Library_Test_Projects\BDD дом .pln")
BACKUP = CTRL / "apa_ac29_autonomous_job_bridge.py.v2-before-general-native-copy.bak"
RECEIPT = CTRL / "apa-ac29-reusable-native-copy-upgrade.json"


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def blob(data):
    return hashlib.sha1(
        b"blob " + str(len(data)).encode("ascii") + bytes([0]) + data
    ).hexdigest()


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def download_code(name, expected):
    command = ["gh", "api", f"repos/{REPO}/contents/scripts/{name}?ref={SOURCE_COMMIT}"]
    proc = subprocess.run(command, capture_output=True, timeout=45)
    require(proc.returncode == 0, "PINNED_RELEASE_SOURCE_NOT_ACCESSIBLE:" + name)
    doc = json.loads(proc.stdout.decode("utf-8"))
    raw = base64.b64decode(doc["content"])
    require(blob(raw) == expected == doc["sha"],
            "PINNED_RELEASE_BLOB_SHA_DRIFT:" + name)
    compile(raw.decode("utf-8-sig"), name, "exec")
    return raw


def current_processes():
    """WMI only exact APA worker path; exclude unrelated GPT/Arena dispatchers."""
    powershell = (
        "$ErrorActionPreference='Stop';"
        "Get-CimInstance Win32_Process | "
        "Where-Object {$_.Name -in @('python.exe','pythonw.exe') -and "
        "$_.CommandLine -match 'apa_ac29_autonomous_job_bridge[.]py'} | "
        "Select-Object ProcessId,ParentProcessId,CommandLine | "
        "ConvertTo-Json -Compress"
    )
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive",
         "-Command", powershell],
        capture_output=True, timeout=30)
    require(result.returncode == 0, "WIN32_RECEIVER_INSPECTION_FAILED")
    data = result.stdout.decode("utf-8-sig", errors="replace").strip()
    if not data:
        return []
    records = json.loads(data)
    if isinstance(records, dict):
        records = [records]
    require(isinstance(records, list) and len(records) <= 4,
            "UNRECOGNIZED_PROCESS_COUNT")
    for row in records:
        cmd = str(row.get("CommandLine") or "").lower()
        require(str(WORKER).lower() in cmd and "--loop" in cmd and
                type(row.get("ProcessId")) is int and
                type(row.get("ParentProcessId")) is int,
                "FOREIGN_PROCESS_MATCHED_NAME_REFUSE_TO_KILL")
    require(len(set(row["ProcessId"] for row in records)) == len(records),
            "DUPLICATE_PROCESS_IDENTIFIERS")
    return records


def safe_past_jobs():
    require(STATE.is_dir(), "EXISTING_RECEIVER_STATE_ABSENT")
    for directory in STATE.iterdir():
        if not directory.is_dir():
            continue
        if (directory / "attempted.json").exists():
            require((directory / "result.json").is_file(),
                    "IN_FLIGHT_OR_UNRESOLVED_JOB_REFUSE_UPGRADE:" + directory.name)


def stop_exact_worker_only():
    existing = current_processes()
    safe_past_jobs()
    all_ids = {r["ProcessId"] for r in existing}
    # Stop possible Python child wrapper before its parent.
    ordered = sorted(existing,
                     key=lambda row: row["ParentProcessId"] not in all_ids)
    pids = []
    for row in ordered:
        pid = row["ProcessId"]
        live = {p["ProcessId"]:p for p in current_processes()}
        if pid not in live:
            continue
        require(live[pid]["CommandLine"] == row["CommandLine"] and
                live[pid]["ParentProcessId"] == row["ParentProcessId"],
                "PID_REUSED_OR_COMMAND_CHANGED_NO_TERMINATION")
        safe_past_jobs()
        os.kill(pid, signal.SIGTERM)
        pids.append(pid)
    for _ in range(40):
        time.sleep(.2)
        if not current_processes():
            return pids
    raise ValueError("OLD_RECEIVER_PROCESSES_STILL_RUNNING")


def install():
    require(sys.platform == "win32", "WINDOWS_REQUIRED")
    require(WORKER.is_file() and STATE.is_dir(),
            "ORIGINAL_AC29_RECEIVER_MISSING")
    exact = blob(WORKER.read_bytes())
    if exact == FILES[WORKER.name] and all(
            (CTRL / name).is_file() and
            blob((CTRL / name).read_bytes()) == digest
            for name, digest in FILES.items()):
        print("APA_STATUS: REUSABLE_NATIVE_WORKER_ALREADY_INSTALLED")
        return
    require(exact == CURRENT_WORKER_SHA1,
            "INSTALLED_RECEIVER_NOT_RECOGNIZED_REFUSE_OVERWRITE")
    require(sha256(WORKING) == BASE_WORKING_SHA256 and
            sha256(PROTECTED) == BASE_PROTECTED_SHA256,
            "PROJECT_SAVED_HASH_DRIFT")
    startup = Path(os.environ["APPDATA"]) / (
        "Microsoft/Windows/Start Menu/Programs/Startup/"
        "APA-AC29-GPT-Bridge.vbs")
    launcher = CTRL / "start-apa-bridge.cmd"
    require(startup.is_file() and launcher.is_file() and
            str(WORKER).lower() in launcher.read_text(encoding="utf-8").lower(),
            "EXISTING_USER_STARTUP_NOT_VERIFIED")
    for name in FILES:
        if name != WORKER.name:
            require(not (CTRL / name).exists(),
                    "NEW_HELPER_PATH_ALREADY_IN_USE:" + name)
    require(not BACKUP.exists() and not RECEIPT.exists(),
            "UPGRADE_ALREADY_STAGED_OR_COMPLETED")
    safe_past_jobs()
    sources = {name: download_code(name, digest)
               for name, digest in FILES.items()}
    stages = {}
    for name, raw in sources.items():
        stage = CTRL / (name + ".reusable-v1.new")
        require(not stage.exists(), "EXISTING_UPGRADE_STAGE_NOT_SAFE_TO_REPLACE")
        stage.write_bytes(raw)
        stages[name] = stage
    ready = subprocess.run([sys.executable, str(stages[WORKER.name]), "--help"],
                           capture_output=True, timeout=30)
    require(ready.returncode == 0,
            "UPDATED_WORKER_CLI_IMPORT_CHECK_FAILED")
    original_processes = stop_exact_worker_only()
    # No runtime worker left. Preserve the previous executable exactly.
    BACKUP.write_bytes(WORKER.read_bytes())
    for name, stage in stages.items():
        os.replace(stage, CTRL / name)
    with (STATE / "bridge.log").open("ab") as stream:
        proc = subprocess.Popen(
            [sys.executable, "-u", str(WORKER), "--loop"],
            cwd=ROOT, stdin=subprocess.DEVNULL,
            stdout=stream, stderr=stream, close_fds=True,
            creationflags=subprocess.CREATE_NO_WINDOW)
    time.sleep(2)
    require(proc.poll() is None, "UPDATED_RECEIVER_EXITED_IMMEDIATELY")
    report = {
        "status": "APA_REUSABLE_NATIVE_EXECUTOR_DEPLOYED",
        "oldProcessIds": original_processes,
        "newProcessId": proc.pid,
        "sourceCommit": SOURCE_COMMIT,
        "installedBlobs": FILES,
        "previousWorkerBackup": str(BACKUP),
        "existingJobQueuePreserved": True,
        "originalSceneWriterLedgerUnchanged": True,
        "originalPlnUnchanged": True,
        "workingPlnUnchanged": True,
        "existingUiDispatcherUnchanged": True,
        "nativeWriteCallsByInstaller": 0,
        "readyForExplicitlyApprovedNativeCopyJobs": True,
        "noNewJobEnqueued": True,
    }
    RECEIPT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",
                       encoding="utf-8")
    print("APA_STATUS:", report["status"])
    print("NEW_PID:", report["newProcessId"])
    print("NATIVE_WRITES:", 0)
    print("RECEIPT:", RECEIPT)


if __name__ == "__main__":
    try:
        install()
    except Exception as exc:
        print("APA_STATUS: REUSABLE_NATIVE_UPGRADE_BLOCKED")
        print("ERROR:", type(exc).__name__ + ": " + str(exc))
        sys.exit(2)
