"""Prepare this release's own Python environment and open APA for Windows."""

import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import venv

from apa_release import MANIFEST, read_release, sha256, verify_member


ROOT = Path(__file__).resolve().parent


def launch():
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
    with (environment / "application.log").open("ab") as log:
        subprocess.Popen([str(pythonw), "-E", "-s", "-X", "utf8", str(ROOT / "apa_app.py")],
                         cwd=ROOT, stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                         env={**os.environ, "PYTHONNOUSERSITE": "1"})


if __name__ == "__main__":
    try:
        launch()
    except Exception as exc:
        print(f"Не удалось открыть APA. {exc}", file=sys.stderr)
        sys.exit(2)
