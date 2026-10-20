"""Однократная безопасная установка единого бюро вместо PR139 Startup.

Никаких задач/моделей Archicad не меняет. Старый приемник не завершает
насильственно: при занятой блокировке APA установка отказывается продолжать.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from urllib.request import urlopen

from bureau_unified_service import config_load

APA_BLOB = "ef52f5fc184c6ac59c1197c14e1bbbc06237fdd2"
OLD_STARTUP = "APA-AC29-GPT-Bridge.vbs"
NEW_STARTUP = "Bureau-Unified-Dispatcher.vbs"


def git_blob_sha(data):
    return hashlib.sha1(
        b"blob " + str(len(data)).encode("ascii") + b"\0" + data
    ).hexdigest()


def safe_path(path):
    value = str(Path(path).resolve())
    if any(symbol in value for symbol in ('"', '\r', '\n', '%', '!', '^')):
        raise ValueError("PATH_UNSAFE_FOR_WINDOWS_STARTUP")
    return value


def startup_folder():
    roaming = os.environ.get("APPDATA")
    if not roaming:
        raise RuntimeError("WINDOWS_APPDATA_REQUIRED")
    return Path(roaming) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"


def check_existing_bridge(path):
    source = Path(path)
    if not source.is_file() or git_blob_sha(source.read_bytes()) != APA_BLOB:
        raise ValueError("INSTALLED_APA_BRIDGE_NOT_SOURCE_PINNED")
    spec = importlib.util.spec_from_file_location("approved_existing_bridge", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.STATE.mkdir(parents=True, exist_ok=True)
    try:
        handle = module.acquire_singleton()
    except Exception as exc:
        raise RuntimeError("OLD_APA_WORKER_STILL_RUNNING_STOP_ONCE_FIRST") from exc
    handle.close()
    return hashlib.sha256(source.read_bytes()).hexdigest()


def write_private_configuration(path, data):
    temp = path.with_suffix(".pending")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
    os.replace(temp, path)


def wait_health(port, child):
    """Ожидаем готовность только запущенного нами процесса; никакой чужой службы."""
    import json as json_module
    for _ in range(15):
        if child.poll() is not None:
            raise RuntimeError("UNIFIED_PROCESS_EXITED_BEFORE_READY")
        try:
            with urlopen(f"http://127.0.0.1:{port}/health", timeout=0.4) as reply:
                body = json_module.loads(reply.read())
            if (body.get("status") == "BUREAU_UNIFIED_ALIVE"
                    and body.get("apaAttached") is True):
                return True
        except (OSError, ValueError):
            time.sleep(0.3)
    raise RuntimeError("UNIFIED_HEALTH_NOT_CONFIRMED")


def install(config_path, root):
    if os.name != "nt":
        raise RuntimeError("WINDOWS_ONLY_INSTALLER")
    config_path = Path(config_path).resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if not config.get("apaEnabled"):
        raise ValueError("UNIFIED_INSTALL_REQUIRES_APA_ENABLED")
    if any(x["workflowId"].startswith("REPLACE_")
           for x in config.get("targets", {}).values()):
        raise ValueError("AUTOMA_WORKFLOW_IDS_NOT_CONFIGURED")
    pinned_sha = check_existing_bridge(config["apaBridgePath"])
    if config.get("apaBridgeSha256") == "AUTO_PIN_INSTALLED_BRIDGE":
        config["apaBridgeSha256"] = pinned_sha
        write_private_configuration(config_path, config)
    elif config.get("apaBridgeSha256") != pinned_sha:
        raise ValueError("APA_BRIDGE_HASH_MISMATCH")
    config = config_load(config_path)

    repo_scripts = Path(__file__).resolve().parent
    dest = Path(root) / "controllers" / "bureau-unified-v1"
    dest.mkdir(parents=True, exist_ok=True)
    for filename in ("bureau_unified_service.py",
                     "bureau_chat_activation_gateway.py"):
        shutil.copy2(repo_scripts / filename, dest / filename)

    state_dir = Path(root) / "bureau-unified-state"
    state_dir.mkdir(parents=True, exist_ok=True)
    log = state_dir / "service.log"
    db = state_dir / "jobs.sqlite"
    python = safe_path(sys.executable)
    script = safe_path(dest / "bureau_unified_service.py")
    cfg = safe_path(config_path)
    dbp = safe_path(db)
    logp = safe_path(log)
    launch_cmd = dest / "launch-bureau-unified.cmd"
    launch_cmd.write_text(
        "@echo off\r\n"
        f'"{python}" "{script}" --config "{cfg}" --db "{dbp}" run'
        f' >> "{logp}" 2>&1\r\n',
        encoding="utf-8"
    )

    startup = startup_folder()
    startup.mkdir(parents=True, exist_ok=True)
    old = startup / OLD_STARTUP
    disabled = startup / (OLD_STARTUP + ".disabled")
    new = startup / NEW_STARTUP
    if new.exists() or disabled.exists():
        raise RuntimeError("STARTUP_MIGRATION_ALREADY_PRESENT_REVIEW_MANUALLY")

    child = None
    old_moved = False
    try:
        if old.exists():
            old.rename(disabled)
            old_moved = True
        stop_file = safe_path(state_dir / "PAUSE_AUTOSTART")
        vbs = (
            'Set sh = CreateObject("WScript.Shell")\r\n'
            'Set fs = CreateObject("Scripting.FileSystemObject")\r\n'
            'Do While Not fs.FileExists("' + stop_file + '")\r\n'
            '  sh.Run Chr(34) & "' + safe_path(launch_cmd)
            + '" & Chr(34), 0, True\r\n'
            '  WScript.Sleep 15000\r\n'
            'Loop\r\n'
        )
        new.write_text(vbs, encoding="utf-8")
        with log.open("ab") as output:
            child = subprocess.Popen(
                [python, script, "--config", cfg, "--db", dbp, "run"],
                stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
            )
        wait_health(config["callbackPort"], child)
        receipt = {
            "status": "BUREAU_UNIFIED_LOCAL_PROCESS_READY",
            "oldStartupDisabled": old_moved,
            "newStartup": str(new),
            "apaBridgeSha256": pinned_sha,
            "servicePid": child.pid,
            "database": dbp,
            "log": logp,
            "httpPort": config["callbackPort"],
            "liveAutomaChatDispatchVerified": False,
            "liveReportChainingVerified": False,
            "restartWatchdog": "Windows Startup VBS supervised loop",
            "pauseAutostartSentinel": str(state_dir / "PAUSE_AUTOSTART")
        }
        (state_dir / "install-receipt.json").write_text(
            json.dumps(receipt, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8"
        )
        return receipt
    except Exception:
        if child is not None and child.poll() is None:
            child.terminate()
        new.unlink(missing_ok=True)
        if old_moved and disabled.exists():
            disabled.rename(old)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument(
        "--root", default=r"C:\LocalAI\APA_AC29_Stable")
    args = parser.parse_args()
    print(json.dumps(install(args.config, args.root),
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
