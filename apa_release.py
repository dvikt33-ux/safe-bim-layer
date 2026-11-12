"""Integrity checks shared by the Windows launcher and the packaged receiver."""

import hashlib
import json
from pathlib import Path


MANIFEST = "apa-release.json"


def sha256(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def read_release(root):
    manifest = read_json(root / MANIFEST)
    if manifest.get("schema") != "APA_WINDOWS_RELEASE_V1" or not isinstance(manifest.get("files"), dict):
        raise ValueError("Неверный манифест Windows-комплекта APA")
    return manifest


def verify_member(root, manifest, relative):
    root = Path(root).resolve()
    path = (root / relative).resolve(strict=True)
    entry = manifest["files"].get(relative)
    if (not path.is_relative_to(root) or not path.is_file() or entry is None
            or path.stat().st_size != entry["bytes"] or sha256(path) != entry["sha256"]):
        raise ValueError(f"Нарушена целостность комплекта APA: {relative}")
    return path
