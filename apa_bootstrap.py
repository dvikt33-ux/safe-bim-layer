"""Prepare this release's own Python environment and open APA for Windows."""

import json
import os
from pathlib import Path
import argparse
import platform
import subprocess
import sys
import venv

from apa_release import MANIFEST, read_release, sha256, verify_member


ROOT = Path(__file__).resolve().parent


def prepare_environment():
    import msvcrt

    if (platform.system() != "Windows" or sys.version_info[:2] != (3, 11) or sys.maxsize <= 2**32):
        raise ValueError("Требуется 64-разрядный Python 3.11")
    release = read_release(ROOT)
    for name in ("apa.py", "apa_app.py", "apa_bootstrap.py", "apa_release.py", "requirements-offline.txt"):
        verify_member(ROOT, release, name)
    environment = ROOT / ".apa-runtime"
    if environment.resolve() != environment:
        raise ValueError("Каталог окружения APA перенаправлен в другое место")
    environment.mkdir(exist_ok=True)
    with (environment / "setup.lock").open("a+b") as lock:
        lock.seek(0)
        try:
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError as exc:
            raise ValueError("Подготовка APA уже выполняется в другом окне") from exc
        try:
            manifest_sha = sha256(ROOT / MANIFEST)
            marker = environment / "installed.json"
            python = environment / "Scripts" / "python.exe"
            pythonw = python.with_name("pythonw.exe")
            installed = json.loads(marker.read_text(encoding="utf-8")) if marker.is_file() else {}
            if installed.get("releaseManifestSha256") != manifest_sha or not python.is_file() or not pythonw.is_file():
                print("Подготовка локального окружения APA", flush=True)
                venv.EnvBuilder(with_pip=True).create(environment)
                subprocess.run([str(python), "-I", "-m", "pip", "install", "--disable-pip-version-check",
                                "--no-index", "--no-input", "--only-binary", ":all:", "--require-hashes",
                                "--find-links", str(ROOT / "wheels"), "-r", str(ROOT / "requirements-offline.txt")],
                               check=True)
                subprocess.run([str(python), "-I", "-m", "pip", "check"], check=True)
                pending = marker.with_suffix(".tmp")
                pending.write_text(json.dumps({"releaseManifestSha256": manifest_sha}), encoding="utf-8")
                pending.replace(marker)
        finally:
            lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
    return python, pythonw


def launch(argv=None):
    parser = argparse.ArgumentParser(description="Запуск APA для Windows")
    parser.add_argument("--receiver-profile", type=Path, action="append")
    parser.add_argument("--stop-receiver", action="store_true")
    args = parser.parse_args(argv)
    receiver = ROOT / ".apa-runtime" / "receiver"
    if args.stop_receiver:
        if args.receiver_profile or not (receiver / "receiver-started.json").is_file():
            raise ValueError("Локальный фоновый приёмник ещё не запускался")
        (receiver / "receiver-stop").touch()
        print("Приёмник остановится после текущего задания")
        return
    python, pythonw = prepare_environment()
    if args.receiver_profile:
        stop = receiver / "receiver-stop"
        if stop.exists():
            sys.path.insert(0, str(ROOT / "scripts"))
            from apa_ac29_autonomous_job_bridge import acquire_singleton

            # Do not clear a stop request while its previous receiver still owns
            # the lock. This check never stops another process.
            with acquire_singleton(shared=True):
                stop.unlink(missing_ok=True)
        commands = [item for profile in args.receiver_profile
                    for item in ("--r03-profile", str(profile.resolve(strict=True)))]
        receiver.mkdir(exist_ok=True)
        with (receiver / "receiver.log").open("ab") as log:
            child = subprocess.Popen([str(python), "-E", "-s", "-X", "utf8", "-u", "-m", "apa",
                                      "mailbox", "--loop", *commands], cwd=ROOT,
                                     stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                                     creationflags=subprocess.CREATE_NO_WINDOW)
        print(f"Процесс приёмника PID {child.pid}. Готовность проверьте в {receiver / 'receiver.log'}")
        return
    with (ROOT / ".apa-runtime" / "application.log").open("ab") as log:
        subprocess.Popen([str(pythonw), "-E", "-s", "-X", "utf8", str(ROOT / "apa_app.py")],
                         cwd=ROOT, stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                         env={**os.environ, "PYTHONNOUSERSITE": "1"})


if __name__ == "__main__":
    try:
        launch()
    except Exception as exc:
        print(f"Не удалось открыть APA. {exc}", file=sys.stderr)
        sys.exit(2)
