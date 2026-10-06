#!/usr/bin/env python3
from __future__ import annotations
import base64, hashlib, pathlib, tarfile, sys

ARCHIVE_SHA256 = "124c6eb3abc76568737d224fc4eab70cdd1320c871f20743853ea3f72e3ff925"
B64_SHA256 = "75f14d41728501d93db3f88b19c8c0025879cc00919be8ef4bc8717c4a440a40"

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def main() -> int:
    here = pathlib.Path(__file__).resolve().parent
    src = here / "porotherm-v2.3-source-patch.tar.gz.b64"
    data = src.read_bytes()
    if sha256_bytes(data) != B64_SHA256:
        raise SystemExit("encoded transport SHA-256 mismatch")
    archive = base64.b64decode(data)
    if sha256_bytes(archive) != ARCHIVE_SHA256:
        raise SystemExit("decoded archive SHA-256 mismatch")
    target = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else here / "unpacked"
    target.mkdir(parents=True, exist_ok=True)
    tmp = target / "porotherm-v2.3-source-patch.tar.gz"
    tmp.write_bytes(archive)
    with tarfile.open(tmp, "r:gz") as tf:
        tf.extractall(target)
    print(target)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())