from __future__ import annotations

import base64
import hashlib
import json
import os
import shutil
import subprocess
import time
import urllib.parse
import uuid
from datetime import datetime, timezone
from pathlib import Path

SOURCE_REPO = "https://github.com/dvikt33-ux/safe-bim-layer.git"
SOURCE_BRANCH = "prototype/s2.6-control-surface-20260929"
SOURCE_COMMIT = "7469b775f2552e41846c86512e87c13cdb864b6b"
MAILBOX_REPO = "dvikt33-ux/safe-bim-bridge"
MAILBOX_BRANCH = "main"
MAILBOX_ROOT = "safe-bim-mailbox/gpt-live"


def run(cmd, *, cwd=None, env=None, check=True, capture=False):
    kw = {"cwd": str(cwd) if cwd else None, "env": env, "text": True, "check": check}
    if capture:
        kw.update(stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return subprocess.run(cmd, **kw)


def require(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise RuntimeError(f"Не найден {name}.exe")
    return path


def choose_python() -> str:
    candidates = []
    if os.environ.get("SAFE_BIM_PYTHON"):
        candidates.append(Path(os.environ["SAFE_BIM_PYTHON"]))
    if os.environ.get("APPDATA"):
        candidates.append(Path(os.environ["APPDATA"]) / "uv" / "tools" / "archicad-mcp-server" / "Scripts" / "python.exe")
    generic = shutil.which("py") or shutil.which("python")
    if generic:
        candidates.append(Path(generic))
    for candidate in candidates:
        if candidate.is_file() and subprocess.run(
            [str(candidate), "-c", "import archicad"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        ).returncode == 0:
            return str(candidate)
    raise RuntimeError("Не найден Python runtime с установленным пакетом archicad")


def prepare_source(source_dir: Path) -> None:
    git = require("git")
    if not (source_dir / ".git").is_dir():
        source_dir.parent.mkdir(parents=True, exist_ok=True)
        run([git, "clone", "--filter=blob:none", "--single-branch", "--branch", SOURCE_BRANCH,
             SOURCE_REPO, str(source_dir)])
    else:
        run([git, "-C", str(source_dir), "fetch", "origin", SOURCE_BRANCH])
    run([git, "-C", str(source_dir), "checkout", "--detach", SOURCE_COMMIT])


def load_status(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None


def ready(data) -> bool:
    try:
        s = data["status"]
        return (s["host"]["running"] is True
                and s["archicad"]["status"] == "CONNECTED"
                and bool(s["archicad"]["instanceId"])
                and bool(s["project"]["logicalProjectId"]))
    except (KeyError, TypeError):
        return False


def start_bridge(python: str, source_dir: Path, data_dir: Path):
    env = os.environ.copy()
    env.update({
        "SAFE_BIM_DATA_DIR": str(data_dir),
        "SAFE_BIM_GITHUB_OWNER": "dvikt33-ux",
        "SAFE_BIM_GITHUB_REPO": "safe-bim-bridge",
        "SAFE_BIM_GITHUB_BRANCH": MAILBOX_BRANCH,
        "SAFE_BIM_GITHUB_ROOT": MAILBOX_ROOT,
        "SAFE_BIM_BRIDGE_INSTANCE_ID": "gpt-direct-bridge",
    })
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    return subprocess.Popen(
        [python, "-m", "sync_bridge"], cwd=str(source_dir), env=env,
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=flags,
    )


def canonical_json(value) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False)


def gh_json(endpoint: str):
    return json.loads(run(["gh", "api", endpoint], capture=True).stdout)


def publish_probe(status: dict) -> str:
    s = status["status"]
    instance_id = s["archicad"]["instanceId"]
    project_id = s["project"]["logicalProjectId"]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    token = uuid.uuid4().hex[:12]
    request_id = f"gpt-direct-{stamp}-{token}"
    message_id = f"gpt-context-{stamp}-{token}"
    now = datetime.now(timezone.utc).isoformat()
    payload = {
        "generation": 1,
        "instanceId": instance_id,
        "logicalProjectId": project_id,
        "requestId": request_id,
        "requestedAt": now,
        "requestedScope": "selection",
    }
    payload_hash = hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()
    remote = {
        "protocolVersion": 1,
        "messageId": message_id,
        "kind": "CONTEXT_REQUEST",
        "createdAt": now,
        "payload": payload,
        "payloadHash": payload_hash,
        "requestId": request_id,
        "logicalProjectId": project_id,
    }
    content = base64.b64encode(canonical_json(remote).encode("utf-8")).decode("ascii")
    path = f"{MAILBOX_ROOT}/inbox/{message_id}.json"
    endpoint = f"repos/{MAILBOX_REPO}/contents/{urllib.parse.quote(path, safe='/')}"
    run(["gh", "api", "--method", "PUT", endpoint,
         "-f", f"message=Safe BIM GPT direct context {message_id}",
         "-f", f"content={content}", "-f", f"branch={MAILBOX_BRANCH}"], capture=True)
    return request_id


def find_result(request_id: str):
    folder = urllib.parse.quote(f"{MAILBOX_ROOT}/results", safe="/")
    try:
        entries = gh_json(f"repos/{MAILBOX_REPO}/contents/{folder}?ref={MAILBOX_BRANCH}")
    except subprocess.CalledProcessError:
        return None
    if not isinstance(entries, list):
        return None
    for entry in entries:
        path = entry.get("path") if isinstance(entry, dict) else None
        if not isinstance(path, str) or not path.endswith(".json"):
            continue
        try:
            encoded = gh_json(
                f"repos/{MAILBOX_REPO}/contents/{urllib.parse.quote(path, safe='/')}?ref={MAILBOX_BRANCH}"
            )["content"]
            obj = json.loads(base64.b64decode(encoded).decode("utf-8"))
        except Exception:
            continue
        payload = obj.get("payload") if isinstance(obj, dict) else None
        if obj.get("requestId") == request_id or (isinstance(payload, dict) and payload.get("requestId") == request_id):
            return obj
    return None


def tail(path: Path, count=30) -> str:
    try:
        return "\n".join(path.read_text(encoding="utf-8", errors="replace").splitlines()[-count:])
    except OSError:
        return ""


def main() -> int:
    if os.name != "nt":
        print("ERROR: bootstrap предназначен для Windows")
        return 2
    try:
        require("gh")
        auth = run(["gh", "auth", "status", "-h", "github.com"], capture=True, check=False)
        if auth.returncode != 0:
            raise RuntimeError("GitHub CLI не авторизован; нужен gh auth login")
        python = choose_python()
        local = os.environ.get("LOCALAPPDATA")
        if not local:
            raise RuntimeError("LOCALAPPDATA не определён")

        base = Path(local) / "SafeBIM" / "gpt-direct"
        source_dir = base / "runtime-src"
        data_dir = base / "data"
        status_path = data_dir / "control-status.json"
        data_dir.mkdir(parents=True, exist_ok=True)

        print("[1/4] Проверяю runtime")
        prepare_source(source_dir)
        run([python, "-c", "import archicad; import sync_bridge"], cwd=source_dir, capture=True)

        status = load_status(status_path)
        proc = None
        if not ready(status):
            print("[2/4] Запускаю Safe BIM Bridge")
            proc = start_bridge(python, source_dir, data_dir)
            (base / "bridge.pid").write_text(str(proc.pid), encoding="ascii")
            deadline = time.time() + 25
            while time.time() < deadline:
                if proc.poll() is not None:
                    break
                status = load_status(status_path)
                if ready(status):
                    break
                time.sleep(0.5)
        else:
            print("[2/4] Bridge уже работает")

        if not ready(status):
            raise RuntimeError("Bridge не увидел Archicad\n" + (tail(data_dir / "bridge-host.log") or "Лог пуст"))

        s = status["status"]
        print("    Archicad:", s["archicad"].get("version"), "| project:", s["project"].get("name"))
        print("    GitHub:", s["github"].get("status"), "| credential:", s["github"].get("credentialSource"))
        if s["github"].get("needsAuth") is True:
            raise RuntimeError("Bridge сообщает NEEDS_AUTH")

        print("[3/4] Отправляю read-only CONTEXT_REQUEST")
        request_id = publish_probe(status)
        print("[4/4] Жду CONTEXT_READY")
        deadline = time.time() + 30
        result = None
        while time.time() < deadline:
            result = find_result(request_id)
            if result:
                break
            time.sleep(1)
        if not result:
            raise RuntimeError("CONTEXT_READY не появился; см. bridge-host.log")

        payload = result.get("payload") if isinstance(result.get("payload"), dict) else {}
        snapshot = payload.get("snapshot") if isinstance(payload.get("snapshot"), dict) else {}
        selection = snapshot.get("selection") if isinstance(snapshot.get("selection"), dict) else {}
        print("E2E OK: GPT/GitHub <-> Archicad")
        print("requestId:", request_id)
        print("selection.count:", selection.get("count"))
        print("rootHash:", result.get("rootHash") or payload.get("rootHash"))
        print("Model mutations: 0")
        return 0
    except subprocess.CalledProcessError as exc:
        print("ERROR: внешняя команда завершилась с ошибкой")
        if isinstance(exc.stderr, str) and exc.stderr.strip():
            print(exc.stderr.strip()[-2000:])
        return 2
    except Exception as exc:
        print("ERROR:", exc)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
