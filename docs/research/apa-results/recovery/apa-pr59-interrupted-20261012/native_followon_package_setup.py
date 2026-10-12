#!/usr/bin/env python3
"""Reconstructed offline PR #59 code archive creator. No Archicad/PLN/APX access.

This is NOT the original lost Work script and NOT an installer. It reads
13 files directly from the exact PR #59 Git commit already present in a local
Git clone, verifies their published Git blob SHA-1, and produces a preview ZIP.
It never fetches, merges, checks out, builds, launches Archicad or mutates a PLN.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path, PurePosixPath


PROOF_NAME = "native-followon-ci-proof.json"
HEAD_EXPECTED = "744e0bd184a11f1de4a1cf16382d21aec6f8cfca"
ZIP_TIMESTAMP = (2020, 1, 1, 0, 0, 0)
DENY_EXTENSIONS = {".pln", ".apx", ".ifc", ".exe", ".dll", ".key", ".p12", ".pem"}


def git(repo: Path, *args: str) -> bytes:
    command = ["git", "-C", str(repo), *args]
    proc = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode:
        raise RuntimeError(
            "Git read failed: " + " ".join(args) + ": "
            + proc.stderr.decode("utf-8", "replace").strip()
        )
    return proc.stdout


def sha1_blob(data: bytes) -> str:
    prefix = ("blob " + str(len(data)) + "\0").encode("ascii")
    return hashlib.sha1(prefix + data).hexdigest()


def validate_path(raw: str) -> None:
    path = PurePosixPath(raw)
    if path.is_absolute() or ".." in path.parts or "\\" in raw:
        raise ValueError("Unsafe archive path: " + raw)
    if not raw or str(path) != raw:
        raise ValueError("Noncanonical archive path: " + raw)
    if path.suffix.lower() in DENY_EXTENSIONS:
        raise ValueError("Native/binary output not eligible for code preview: " + raw)


def zip_write(zf: zipfile.ZipFile, name: str, data: bytes) -> None:
    entry = zipfile.ZipInfo(name, date_time=ZIP_TIMESTAMP)
    entry.compress_type = zipfile.ZIP_DEFLATED
    entry.external_attr = 0o100644 << 16
    zf.writestr(entry, data)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=Path, default=Path.cwd(), help="Local Git clone with PR #59 commit")
    ap.add_argument("--proof", type=Path, default=Path(__file__).with_name(PROOF_NAME))
    ap.add_argument("--output", type=Path, default=None, help="Nonexistent ZIP path")
    args = ap.parse_args()

    repo = args.repo.resolve()
    if not (repo / ".git").exists():
        raise RuntimeError("Expected local Git clone at --repo; repository was not modified")
    proof_bytes = args.proof.read_bytes()
    proof = json.loads(proof_bytes.decode("utf-8"))
    if proof.get("provenance") != "RECONSTRUCTED_FROM_PUBLISHED_GITHUB; NOT_ORIGINAL_WORK_FILE":
        raise RuntimeError("Unexpected recovery-proof provenance")
    if proof.get("source_head") != HEAD_EXPECTED:
        raise RuntimeError("Source head mismatch")

    try:
        commit_type = git(repo, "cat-file", "-t", HEAD_EXPECTED).strip()
    except RuntimeError as exc:
        raise RuntimeError(
            "PR #59 commit not found in the local clone. Fetch the feature branch "
            "manually after reviewing the source, then rerun. No auto-fetch performed."
        ) from exc
    if commit_type != b"commit":
        raise RuntimeError("Source object is not a commit")

    blobs = proof.get("source_blobs", [])
    if len(blobs) != 13:
        raise RuntimeError("Expected exactly 13 verified GitHub source blobs")

    source = []
    manifest = []
    seen = set()
    for record in blobs:
        path = record["path"]
        validate_path(path)
        if path in seen:
            raise RuntimeError("Duplicate source path: " + path)
        seen.add(path)

        mode_line = git(repo, "ls-tree", HEAD_EXPECTED, "--", path).decode("utf-8", "replace")
        if not mode_line.startswith("100644 blob ") and not mode_line.startswith("100755 blob "):
            raise RuntimeError("Missing or nonregular Git source blob: " + path)
        data = git(repo, "show", HEAD_EXPECTED + ":" + path)
        actual_blob = sha1_blob(data)
        if actual_blob != record["blob"]:
            raise RuntimeError("Published GitHub blob differs: " + path)
        source.append((path, data))
        manifest.append({
            "path": path,
            "git_blob_sha1": actual_blob,
            "sha256": hashlib.sha256(data).hexdigest(),
            "bytes": len(data),
        })

    output = args.output or (repo / "dist" / "APA_PR59_CODE_PREVIEW_744e0bd.zip")
    output = output.resolve()
    if output.exists():
        raise FileExistsError("Refusing to overwrite existing preview ZIP: " + str(output))
    output.parent.mkdir(parents=True, exist_ok=True)

    archive_manifest = {
        "schema": "APA_PR59_OFFLINE_ARCHIVE_PREVIEW_V1",
        "status": "RECONSTRUCTED_FROM_PUBLISHED_GITHUB",
        "source_commit": HEAD_EXPECTED,
        "source_count": len(source),
        "source_files": manifest,
        "scope": "CODE_PREVIEW_ONLY; NOT_AN_INSTALLER; NO_LIVE_RETEST",
        "excludes": "Local PLN, APX, IFC, raw Work evidence and any credentials",
    }
    manifest_bytes = (json.dumps(archive_manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")

    try:
        with output.open("xb") as file_obj:
            with zipfile.ZipFile(file_obj, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
                for path, data in source:
                    zip_write(zf, "source/" + path, data)
                zip_write(zf, "proof/" + PROOF_NAME, proof_bytes)
                zip_write(zf, "proof/archive-manifest.json", manifest_bytes)
    except BaseException:
        output.unlink(missing_ok=True)
        raise

    # Independently check every entry after closing ZIP.
    with zipfile.ZipFile(output, "r") as zf:
        for path, data in source:
            if zf.read("source/" + path) != data:
                raise RuntimeError("ZIP round-trip mismatch: " + path)
        if zf.read("proof/archive-manifest.json") != manifest_bytes:
            raise RuntimeError("ZIP manifest mismatch")

    print("OFFLINE ARCHIVE PREVIEW: PASS")
    print("PR59_SOURCE_SHA:", HEAD_EXPECTED)
    print("VERIFIED_SOURCE_BLOBS:", len(source))
    print("ZIP:", output)
    print("ZIP_SHA256:", hashlib.sha256(output.read_bytes()).hexdigest())
    print("NATIVE LIVE TEST: NOT RUN")
    print("PLN/APX/IFC MODIFIED: NO")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print("OFFLINE ARCHIVE PREVIEW: FAIL:", exc, file=sys.stderr)
        sys.exit(1)
