"""Install the reviewed APA AC29 job bridge ONCE beside the stable APA core.

Installs a user-level Startup entry, launches a single background receiver,
never changes Dispatcher/GPT/Arena or the stable APA scripts. Safe, pinned
GitHub blobs and digest-checked local core; fails closed on mismatched versions.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(r"C:\LocalAI\APA_AC29_Stable")
CONTROLLERS = ROOT / "controllers"
REPO = "dvikt33-ux/safe-bim-layer"
WORKER_COMMIT = "dce42af8eac09b50a29c9a9a7970c01973ae12db"
WORKER_BLOB = "ef52f5fc184c6ac59c1197c14e1bbbc06237fdd2"
REVIEW_COMMIT = "b32e60f998f7c9337130ad58c723a947998753a8"
REVIEW_BLOB = "35a7bd794317ba91056334aff6801cd0ec71f220"
KNOWN = {
    "archicad_project_accelerator.py": "5ce7cbb91c8f799265a541f79922b50455fecf661ed9278a1cc4ffaff766ba4b",
    "archicad_dynamic_commands.py": "8effd2f294197179b4b18b785de80f7f78091649e7f105ee4cf66877dbe0e6f8",
    "archicad_strategy_discovery.py": "32b7f1c161c545695b6db20aa87003d08cbd86916bc880f9eba1434f3a0801ce",
}
NAME = "APA-AC29-GPT-Bridge"
LOG = ROOT / "apa-job-bridge-state" / "bridge.log"


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def source(repo, commit, path, sha):
    result = subprocess.run(
        ["gh", "api", f"repos/{repo}/contents/{path}?ref={commit}"],
        timeout=45, capture_output=True
    )
    require(result.returncode == 0, "GH_PINNED_SOURCE_ACCESS_FAILED:" +
            path)
    obj = json.loads(result.stdout.decode("utf-8"))
    data = base64.b64decode(obj["content"])
    calculated = hashlib.sha1(
        b"blob " + str(len(data)).encode("ascii") + b"\0" + data
    ).hexdigest()
    require(calculated == sha == obj["sha"], "RELEASE_GIT_BLOB_MISMATCH")
    compile(data.decode("utf-8-sig"), path, "exec")
    return data


def install():
    require(sys.platform == "win32", "WINDOWS_REQUIRED")
    for name, expected in KNOWN.items():
        local = ROOT / "scripts" / name
        require(local.is_file() and
                hashlib.sha256(local.read_bytes()).hexdigest() == expected,
                "EXISTING_APA_CHANGED_REFUSE_UNSAFE_UPDATE:" + name)
    receipt = ROOT / "apa-selector-install-receipt.json"
    require(receipt.is_file() and
            json.loads(receipt.read_text(encoding="utf-8"))["applied"] is True,
            "STABLE_APA_UNVERIFIED")
    worker = source(REPO, WORKER_COMMIT,
                    "scripts/apa_ac29_autonomous_job_bridge.py", WORKER_BLOB)
    review = source(REPO, REVIEW_COMMIT,
                    "scripts/apa_bdd114_native_roof_face_review.py", REVIEW_BLOB)
    require(not CONTROLLERS.exists(),
            "BRIDGE_CONTROLLERS_ALREADY_EXIST_NO_OVERWRITE")
    startup = (Path(os.environ["APPDATA"]) /
               "Microsoft/Windows/Start Menu/Programs/Startup")
    require(startup.is_dir(), "WINDOWS_USER_STARTUP_FOLDER_NOT_FOUND")
    entry = startup / (NAME + ".vbs")
    require(not entry.exists(), "AUTOSTART_ENTRY_ALREADY_EXISTS_NO_OVERWRITE")

    path = CONTROLLERS / "apa_ac29_autonomous_job_bridge.py"
    launcher = CONTROLLERS / "start-apa-bridge.cmd"
    try:
        CONTROLLERS.mkdir(parents=True, exist_ok=False)
        path.write_bytes(worker)
        (CONTROLLERS / "apa_bdd114_native_roof_face_review.py").write_bytes(review)
        logdir = LOG.parent
        logdir.mkdir(parents=True, exist_ok=True)
        py = Path(sys.executable).resolve()
        require(py.is_file(), "SELECTED_PYTHON_EXECUTABLE_MISSING")
        launcher.write_text(
            "@echo off\r\n"
            "cd /d \"" + str(ROOT) + "\"\r\n"
            "\"" + str(py) + "\" -u \"" + str(path) +
            "\" --loop >>\"" + str(LOG) + "\" 2>&1\r\n",
            encoding="utf-8"
        )
        vbs = (
            "Set shell = CreateObject(\"WScript.Shell\")\r\n"
            "shell.Run Chr(34) & \"" + str(launcher).replace("\\", "\\\\") +
            "\" & Chr(34), 0, False\r\n"
        )
        # VBS string literals use raw backslash, not Python/JSON escaping.
        vbs = vbs.replace("\\\\", "\\")
        entry.write_text(vbs, encoding="utf-8")
        checked = subprocess.run(
            [sys.executable, str(path), "--help"],
            capture_output=True, timeout=30
        )
        require(checked.returncode == 0,
                "INSTALLED_BRIDGE_CANNOT_IMPORT_OR_PARSE")
        # Create new detached process. Startup entry preserves it across reboot.
        with LOG.open("ab") as stream:
            spawned = subprocess.Popen(
                [str(py), "-u", str(path), "--loop"],
                cwd=ROOT, stdin=subprocess.DEVNULL,
                stdout=stream, stderr=stream,
                creationflags=subprocess.CREATE_NO_WINDOW,
                close_fds=True
            )
        report = {
            "schema": "APA_AC29_BRIDGE_INSTALL_V1",
            "status": "BRIDGE_AUTOSTART_INSTALLED_PROCESS_LAUNCHED",
            "root": str(ROOT),
            "workerSourceBlob": WORKER_BLOB,
            "reviewSourceBlob": REVIEW_BLOB,
            "workerPid": spawned.pid,
            "startupEntry": str(entry),
            "log": str(LOG),
            "apaCorePreserved": True,
            "apaDynamicPreserved": True,
            "apaSelectorPreserved": True,
            "existingDispatcherUnchanged": True,
            "existingMailboxWatcherUnchanged": True,
            "archicadModelWrites": 0,
            "nativeBuildAuthorization": False,
        }
        (CONTROLLERS / "installation.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8"
        )
        print("APA_STATUS:", report["status"])
        print("PID:", report["workerPid"])
        print("AUTOSTART:", entry)
        print("LOG:", LOG)
        print("MODEL_WRITES: 0")
    except Exception:
        # Never remove unknown/existing artifacts; rollback only known newly
        # created files. Do not alter the stable APA scripts or user PLN.
        if entry.exists():
            entry.unlink()
        raise


if __name__ == "__main__":
    try:
        install()
    except Exception as e:
        print("APA_STATUS: BRIDGE_INSTALL_BLOCKED")
        print("ERROR:", type(e).__name__ + ": " + str(e))
        sys.exit(2)
