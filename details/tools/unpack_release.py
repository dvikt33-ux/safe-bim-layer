#!/usr/bin/env python3
from __future__ import annotations
import base64
import hashlib
import pathlib
import tarfile
import sys

ACTIVE_RELEASE = "v2.3"
EXPECTED_SHA256 = "0ea044a2c7f60809a8f8ea474dbaf4b0d0cb0039ed3b6b1b8f924c55368ea50f"

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def main() -> int:
    details = pathlib.Path(__file__).resolve().parents[1]
    release_dir = details / "releases" / ACTIVE_RELEASE
    raw = release_dir / f"machine-state-{ACTIVE_RELEASE}.tar.gz"
    b64 = release_dir / f"machine-state-{ACTIVE_RELEASE}.tar.gz.b64"
    if raw.exists():
        data = raw.read_bytes()
    elif b64.exists():
        data = base64.b64decode(b64.read_text(encoding="ascii"))
    else:
        raise SystemExit(f"missing release archive transport: {raw} or {b64}")
    actual = sha256_bytes(data)
    if actual != EXPECTED_SHA256:
        raise SystemExit(f"SHA-256 mismatch: {actual}")
    target = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else details / "releases" / f"{ACTIVE_RELEASE}-unpacked"
    target.mkdir(parents=True, exist_ok=True)
    temp = target / f"machine-state-{ACTIVE_RELEASE}.tar.gz"
    temp.write_bytes(data)
    with tarfile.open(temp, "r:gz") as tf:
        tf.extractall(target)
    temp.unlink()
    print(target)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())