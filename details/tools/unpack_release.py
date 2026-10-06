#!/usr/bin/env python3
from __future__ import annotations
import hashlib
import pathlib
import tarfile
import sys

EXPECTED_SHA256 = "57edcbfef8f1bf4b9d946e212c7a2c3e0c1a0a12f285e1aa3f974c178dcdf16e"


def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    here = pathlib.Path(__file__).resolve().parents[1]
    release = here / "releases" / "v2.2" / "machine-state-v2.2.tar.gz"
    if not release.exists():
        raise SystemExit(f"missing release archive: {release}")
    actual = sha256(release)
    if actual != EXPECTED_SHA256:
        raise SystemExit(f"SHA-256 mismatch: {actual}")
    target = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else release.with_suffix("").with_suffix("")
    target.mkdir(parents=True, exist_ok=True)
    with tarfile.open(release, "r:gz") as tf:
        tf.extractall(target)
    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())