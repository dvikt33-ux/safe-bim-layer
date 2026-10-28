#!/usr/bin/env python3
"""Download an official pinned portable MiniZinc bundle into this checkout only."""
import hashlib
from pathlib import Path
import platform
import tarfile
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[2]
PLATFORMS = {
    'Windows': ('MiniZinc-2.10.1-x86_64-windows.zip',
                '7c50b01be3b52aabcfe35842228a962b666ddfc32ddf92199d94c52b0da39094'),
    'Linux': ('MiniZinc-2.10.1-x86_64-linux-gnu.tar.gz',
              'ef7b97d7ce9bf848d2f7b5e412d4affb8f52167cb6fd0540c7c0a81a02940d1b')}


def install():
    if platform.machine().lower() not in {'amd64', 'x86_64'}:
        raise SystemExit('This bootstrap pins x86_64 bundles only')
    name, expected = PLATFORMS[platform.system()]
    runtime = ROOT / '.runtime'; runtime.mkdir(exist_ok=True)
    archive = runtime / ('minizinc.zip' if name.endswith('.zip') else 'minizinc.tar.gz')
    if not archive.exists():
        urllib.request.urlretrieve('https://github.com/MiniZinc/libminizinc/releases/download/2.10.1/' + name, archive)
    if hashlib.sha256(archive.read_bytes()).hexdigest() != expected:
        raise SystemExit('Official release archive SHA256 mismatch; refusing extraction')
    destination = runtime / 'minizinc'; destination.mkdir(exist_ok=True)
    executable_name = 'minizinc.exe' if platform.system() == 'Windows' else 'minizinc'
    executable = destination / name.removesuffix('.zip').removesuffix('.tar.gz') / 'bin' / executable_name
    if not executable.exists():
        if name.endswith('.zip'):
            with zipfile.ZipFile(archive) as z:
                z.extractall(destination)
        else:
            with tarfile.open(archive) as t:
                t.extractall(destination, filter='data')
    print(executable)
    return executable


if __name__ == '__main__':
    install()
