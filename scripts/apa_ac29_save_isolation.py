"""File-level isolation for APA AC29 native writes on a disposable PLN.

A cooperative cross-process reservation prevents two APA jobs from targeting
one scratch PLN. It cannot stop unsupervised Archicad sessions or filesystem
writers: a byte-exact save snapshot and SHA readbacks preserve/detect those
races. A native UNKNOWN is never retried.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil

_SHA = re.compile(r"^[0-9a-f]{64}$")


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def write_new_json(path, record):
    with Path(path).open("x", encoding="utf-8") as out:
        json.dump(record, out, ensure_ascii=False, indent=2, sort_keys=True,
                  allow_nan=False)
        out.write("\n")
        out.flush()
        os.fsync(out.fileno())


def copy_exclusive(source, destination):
    """Exclusive creation, flushed bytes, and no silent target overwrites."""
    with Path(source).open("rb") as src:
        with Path(destination).open("xb") as dst:
            shutil.copyfileobj(src, dst, length=1024 * 1024)
            dst.flush()
            os.fsync(dst.fileno())


class ScratchWriteLease:
    """Persistent, cooperative APA-only lease keyed by exact scratch path.

    Never remove after CREATE/SAVE UNKNOWN. No bypass or timeout-based reset.
    Human read-only reconciliation is required for a stale reservation.
    """

    def __init__(self, scratch_path, state_dir, expected_initial_sha):
        self.scratch = Path(scratch_path).resolve()
        self.state = Path(state_dir).resolve()
        self.expected_sha = expected_initial_sha
        self.lock = self.scratch.with_name(self.scratch.name + ".apa-write.lock")
        self.lock_sha = None

    def acquire(self):
        require(_SHA.fullmatch(self.expected_sha or "") and
                self.scratch.is_file() and self.state.is_dir() and
                sha256(self.scratch) == self.expected_sha and
                not self.lock.exists(), "APA_SAVE_LEASE_SCRATCH_OR_RESERVATION_INVALID")
        record = {
            "schema": "APA_SCRATCH_WRITE_LEASE_V1",
            "scratch": str(self.scratch), "state": str(self.state),
            "expectedInitialSHA256": self.expected_sha,
            "status": "ONE_SHOT_NATIVE_WRITE_RESERVED",
            "createdAtUTC": timestamp(), "pid": os.getpid(),
            "automaticRetry": False,
            "scope": "COOPERATING_APA_EXECUTORS_ONLY",
        }
        try:
            write_new_json(self.lock, record)
        except FileExistsError as exc:
            raise ValueError("APA_SAVE_LEASE_ALREADY_RESERVED_NO_PARALLEL_APA") from exc
        self.lock_sha = sha256(self.lock)
        return record

    def verify(self):
        require(self.lock_sha is not None and self.lock.is_file() and
                sha256(self.lock) == self.lock_sha and
                self.scratch.is_file(), "APA_SAVE_LEASE_LOST_OR_TAMPERED")
        return True


def preserve_guarded_save(project_path, snapshot_path, saved_sha,
                          protected_files):
    """Capture post-SaveProject *bytes*, not only its previously observed hash.

    The caller must supply GuardedSaveTransport.new_saved_sha and invoke this
    immediately in SaveProject's verify_after callback, before any other work.
    Refuse snapshots of externally modified or ambiguously saved projects.
    """
    project, snapshot = Path(project_path).resolve(), Path(snapshot_path).absolute()
    require(_SHA.fullmatch(saved_sha or "") and
            project.is_file() and snapshot.parent.is_dir() and
            snapshot != project and not snapshot.exists() and
            isinstance(protected_files, dict) and protected_files,
            "APA_SAVE_SNAPSHOT_FRESH_TARGET_AND_VALID_SHA_REQUIRED")
    original = {str(Path(path).resolve()): expected
                for path, expected in protected_files.items()}
    require(all(_SHA.fullmatch(expected or "") and
                Path(path).is_file() and sha256(path) == expected
                for path, expected in original.items()) and
            str(project) not in original and str(snapshot) not in original,
            "APA_SAVE_SNAPSHOT_PROTECTED_SOURCE_DRIFT")
    require(sha256(project) == saved_sha,
            "APA_SAVE_SNAPSHOT_PROJECT_CHANGED_BEFORE_COPY")
    copy_exclusive(project, snapshot)
    snapshot_sha = sha256(snapshot)
    require(snapshot_sha == saved_sha and sha256(project) == saved_sha and
            all(sha256(path) == expected for path, expected in original.items()),
            "APA_SAVE_SNAPSHOT_CONCURRENT_WRITE_OR_COPY_MISMATCH")
    # Filesystem permissions are not an immutable-storage guarantee;
    # preserve SHA lineage and use exclusive destination creation instead.
    return {"schema": "APA_SAVE_EXACT_SNAPSHOT_V1",
            "status": "BYTE_EXACT_GUARDED_SAVE_SNAPSHOT_CAPTURED",
            "savedSHA256": saved_sha, "snapshotSHA256": snapshot_sha,
            "snapshot": str(snapshot), "source": str(project),
            "protectedSHA256": original, "atUTC": timestamp(),
            "sourceRecheck": "PASS_AT_CAPTURE",
            "cooperatingAPALease": "REQUIRED_BY_CALLER",
            "blocksExternalArchicadWrites": False,
            "automaticReplay": False, "modelWrites": 0}


def stage_readonly_reopen(parent_state, fresh_copy, fresh_state, port):
    """Create a new immutable verification-only binding for *saved* bytes.

    The original manifest, ledger and saved receipt are never edited. A new
    scratch PLN receives exact snapshot bytes and an independent state with
    the original ATTEMPT guard, preventing accidental native re-execution.
    """
    parent = Path(parent_state).resolve()
    new_pln = Path(fresh_copy).absolute()
    new_state = Path(fresh_state).absolute()
    require(parent.is_dir() and new_pln.suffix.lower() == ".pln" and
            not new_pln.exists() and not new_state.exists() and
            new_pln.parent.is_dir() and new_state.parent.is_dir() and
            new_pln != new_state and type(port) is int and 1 <= port <= 65535,
            "APA_SAVE_REOPEN_FRESH_COPY_STATE_AND_PORT_REQUIRED")

    def source_json(filename):
        return json.loads((parent / filename).read_text(encoding="utf-8"))

    manifest, saved, snap = (source_json("manifest.json"),
                             source_json("saved.json"),
                             source_json("guarded-snapshot.json"))
    require(saved["status"] == "BATCH_NATIVE_SAVED_PENDING_REAL_REOPEN" and
            manifest["schema"] == "APA_AC29_HOTLINK_BATCH_V1" and
            snap["status"] == "BYTE_EXACT_GUARDED_SAVE_SNAPSHOT_CAPTURED" and
            snap["savedSHA256"] == snap["snapshotSHA256"] == saved["savedSHA256"] and
            saved["sourceSHA256"] == manifest["sourceSHA256"] and
            saved["moduleSHA256"] == manifest["moduleSHA256"],
            "APA_SAVE_REOPEN_SIGNED_GUARDED_SAVE_CHAIN_REQUIRED")
    original = Path(manifest["scratch"]).resolve()
    snapshot = Path(snap["snapshot"]).resolve()
    source = Path(manifest["source"]).resolve()
    module = Path(manifest["module"]).resolve()
    require(len({original, snapshot, new_pln.resolve(), source, module}) == 5
            and snapshot.is_file() and sha256(snapshot) == saved["savedSHA256"]
            and sha256(source) == saved["sourceSHA256"]
            and sha256(module) == saved["moduleSHA256"] and
            (parent / "attempted.json").is_file() and
            (parent / "batch-scenewriter.sqlite").is_file() and
            (parent / "plan.json").is_file(),
            "APA_SAVE_REOPEN_SNAPSHOT_AND_PARENT_FORENSICS_REQUIRED")
    protected = {str(source): saved["sourceSHA256"],
                 str(module): saved["moduleSHA256"]}
    require(snap["protectedSHA256"] == protected and
            sha256(parent / "saved.json") and
            sha256(parent / "batch-scenewriter.sqlite"),
            "APA_SAVE_REOPEN_SOURCE_PROVENANCE_DRIFT")

    # Before touching target files, pin the original evidence hashes.
    hashes = {name: sha256(parent / name) for name in
              ("manifest.json", "plan.json", "saved.json", "attempted.json",
               "batch-scenewriter.sqlite", "guarded-snapshot.json")}
    copy_exclusive(snapshot, new_pln)
    require(sha256(new_pln) == saved["savedSHA256"] and
            sha256(snapshot) == saved["savedSHA256"],
            "APA_SAVE_REOPEN_COPIED_SNAPSHOT_SHA_DRIFT")
    new_state.mkdir(exist_ok=False)
    for name in ("plan.json", "saved.json", "attempted.json",
                 "batch-scenewriter.sqlite", "guarded-snapshot.json"):
        copy_exclusive(parent / name, new_state / name)
        require(sha256(new_state / name) == hashes[name] and
                sha256(parent / name) == hashes[name],
                "APA_SAVE_REOPEN_PARENT_EVIDENCE_CHANGED_DURING_STAGE")
    derived = {**manifest, "scratch": str(new_pln), "port": port,
               "snapshotVerificationOnly": True,
               "parentStatePath": str(parent),
               "parentManifestSHA256": hashes["manifest.json"],
               "parentSavedReceiptSHA256": hashes["saved.json"],
               "parentLedgerSHA256": hashes["batch-scenewriter.sqlite"],
               "verifiedSourceSnapshotSHA256": saved["savedSHA256"]}
    write_new_json(new_state / "manifest.json", derived)
    provenance = {"schema": "APA_SAVE_REOPEN_DERIVED_STATE_V1",
                  "status": "SNAPSHOT_ONLY_READBACK_NO_MODEL_WRITES",
                  "parent": str(parent), "parentHashes": hashes,
                  "sourceSavedSHA256": saved["savedSHA256"],
                  "newVerificationPLN": str(new_pln),
                  "newPort": port, "atUTC": timestamp(),
                  "nativeCalls": 0, "automaticReplay": False}
    write_new_json(new_state / "snapshot-provenance.json", provenance)
    return provenance
