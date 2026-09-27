"""Single-process launcher for the Safe BIM runtime and controller."""
from __future__ import annotations

import argparse
import json
import logging
from logging.handlers import RotatingFileHandler
import msvcrt
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.request
import urllib.error

ROOT = Path(__file__).resolve().parent
HOST, PORT = "127.0.0.1", 19731


class LaunchAlreadyRunning(RuntimeError):
    pass


class LaunchError(RuntimeError):
    pass


class SingleInstance:
    def __init__(self, path: Path):
        self.path = path
        self.handle = None

    def __enter__(self):
        self.path.parent.mkdir(exist_ok=True)
        self.handle = self.path.open("a+")
        try:
            msvcrt.locking(self.handle.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError as exc:
            self.handle.close()
            raise LaunchAlreadyRunning("Safe BIM уже запущен") from exc
        return self

    def __exit__(self, *_):
        try:
            if self.handle:
                self.handle.seek(0)
                msvcrt.locking(self.handle.fileno(), msvcrt.LK_UNLCK, 1)
                self.handle.close()
        except OSError:
            pass


def runtime_listening(host: str = HOST, port: int = PORT, timeout: float = .25) -> bool:
    with socket.socket() as sock:
        sock.settimeout(timeout)
        return sock.connect_ex((host, port)) == 0


def runtime_ready(url: str = f"http://{HOST}:{PORT}", timeout: float = .5) -> bool:
    try:
        request = urllib.request.Request(url + "/state?job_id=active")
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status in (200, 404)
    except urllib.error.HTTPError as exc:
        return exc.code == 404
    except (OSError, ValueError):
        return False


def wait_ready(timeout: float = 12.0, interval: float = .2) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if runtime_listening() and runtime_ready():
            return True
        time.sleep(interval)
    return False


def start_runtime(log: logging.Logger) -> subprocess.Popen:
    command = [sys.executable, str(ROOT / "safe_bim_service.py")]
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    creationflags = flags if sys.platform == "win32" else 0
    kwargs = {"cwd": str(ROOT), "stdin": subprocess.DEVNULL,
              "stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL,
              "creationflags": creationflags}
    try:
        process = subprocess.Popen(command, **kwargs)
    except OSError as exc:
        raise LaunchError(f"Не удалось запустить runtime: {exc}") from exc
    log.info("started runtime pid=%s", process.pid)
    return process


def configure_logging() -> logging.Logger:
    log_dir = ROOT / "logs"
    log_dir.mkdir(exist_ok=True)
    logger = logging.getLogger("safe_bim_launcher")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = RotatingFileHandler(log_dir / "launcher.log", maxBytes=512 * 1024,
                                      backupCount=2, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(handler)
    return logger


def launch(timeout: float = 12.0, log: logging.Logger | None = None):
    log = log or configure_logging()
    owned_runtime = False
    if not runtime_listening():
        start_runtime(log)
        owned_runtime = True
    if not wait_ready(timeout):
        log.error("runtime readiness timeout after %.1fs", timeout)
        raise LaunchError("Runtime не ответил вовремя. Подробности: logs\\launcher.log")
    log.info("runtime ready; owned=%s", owned_runtime)
    return owned_runtime


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=float, default=12.0)
    args = parser.parse_args()
    log = configure_logging()
    try:
        with SingleInstance(ROOT / "logs" / "safe_bim_controller.lock"):
            launch(args.timeout, log)
            from controller.app import main as controller_main
            controller_main(use_lock=False)
    except (LaunchAlreadyRunning, LaunchError) as exc:
        log.error("launcher failed: %s", exc)
        print(f"Safe BIM: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
