"""Build-only GitHub mailbox consumer for Archicad 29. No model writes or APX installation.

Reuses gh CLI, Git, and the existing Graphisoft DevKit/MSVC build_model_dump.py.
The job cannot choose source repository, build script, local paths, or command.
The local operator pins one reviewed source commit with --approved-sha.
"""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timedelta, timezone
import hashlib
import json
import msvcrt
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from urllib.parse import quote

SOURCE = "dvikt33-ux/safe-bim-layer"
BRIDGE = "dvikt33-ux/safe-bim-bridge"
BRANCH = "feature/apa-ac29-apx-build-mailbox-20261018"
INBOX = "safe-bim-mailbox/apa-ac29-apx-build/jobs"
OUTBOX = "safe-bim-mailbox/apa-ac29-apx-build/results"
HEX = re.compile(r"^[0-9a-f]{40}$")
JOB = re.compile(r"^apx-[a-z0-9-]{6,55}$")
IDENT = "APA_AC29_APX_BUILD_V1"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def git_blob(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def call(argv, timeout=75, cwd=None):
    p = subprocess.run(argv, cwd=cwd, capture_output=True, timeout=timeout, shell=False)
    if p.returncode != 0:
        raise RuntimeError(f"COMMAND_FAILED:{argv[0]}:{p.returncode}:"
                           + p.stderr.decode("utf-8", "replace")[-800:])
    return p.stdout


def gh(endpoint, *, put=None):
    args = ["gh", "api"]
    if put is None:
        args += [endpoint]
    else:
        args += ["-X", "PUT", endpoint]
        for key, value in put.items():
            args.extend(["-f", f"{key}={value}"])
    return json.loads(call(args).decode("utf-8-sig"))


def read_file(path):
    reply = gh(f"repos/{BRIDGE}/contents/{path}?ref={quote(BRANCH, safe='')}")
    require(reply.get("type") == "file", "MAILBOX_ITEM_NOT_FILE")
    payload = base64.b64decode(reply["content"])
    require(git_blob(payload) == reply["sha"], "MAILBOX_BLOB_MISMATCH")
    return json.loads(payload), reply["sha"]


def utc(value):
    require(isinstance(value, str) and value.endswith("Z"), "UTC_TIMESTAMP_REQUIRED")
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def validate(job, name, approved):
    require(type(job) is dict and set(job) == {
        "schema", "jobId", "action", "repo", "commit", "createdAt", "expiresAt"
    }, "UNEXPECTED_JOB_FIELDS")
    require(job["schema"] == IDENT and job["jobId"] == name
            and JOB.fullmatch(name), "JOB_ID_OR_SCHEMA_INVALID")
    require(job["action"] == "BUILD_APX_ONLY" and job["repo"] == SOURCE,
            "JOB_ACTION_OR_REPOSITORY_NOT_ALLOWED")
    require(job["commit"] == approved and HEX.fullmatch(approved),
            "SOURCE_COMMIT_NOT_LOCALLY_APPROVED")
    created, expires, now = utc(job["createdAt"]), utc(job["expiresAt"]), datetime.now(timezone.utc)
    require(created <= now < expires <= created + timedelta(days=2),
            "JOB_EXPIRED_OR_OUTSIDE_APPROVED_WINDOW")


def save(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf8") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)


def approve_repository(local):
    require((local / ".git").exists(), "LOCAL_SOURCE_REPO_NOT_CLONED")
    origin = call(["git", "-C", str(local), "remote", "get-url", "origin"]).decode().strip()
    normalized = origin.removesuffix(".git").rstrip("/")
    require(normalized in {
        "https://github.com/" + SOURCE,
        "git@github.com:" + SOURCE,
        "ssh://git@github.com/" + SOURCE
    }, "LOCAL_GIT_ORIGIN_NOT_APPROVED")


def build(args, job, folder):
    approve_repository(args.source_repo)
    require(args.tapir_repo.is_dir() and (args.tapir_repo / ".git").exists(),
            "LOCAL_TAPIR_CHECKOUT_NOT_FOUND")
    require(args.devkit.is_dir(), "LOCAL_ARCHICAD29_DEVKIT_NOT_FOUND")
    call(["git", "-C", str(args.source_repo), "fetch", "--no-tags", "origin", job["commit"]],
         timeout=180)
    observed = call(["git", "-C", str(args.source_repo), "rev-parse", job["commit"] + "^{commit}"]).decode().strip()
    require(observed == args.approved_sha == job["commit"], "FETCHED_REVISION_NOT_APPROVED")
    source = folder / "source"
    output = folder / "build-output"
    require(not source.exists() and not output.exists(), "JOB_NOT_FRESH")
    try:
        call(["git", "-C", str(args.source_repo), "worktree", "add", "--detach",
              str(source), observed], timeout=120)
        script = source / "archicad-addon" / "Examples" / "build_model_dump.py"
        require(script.is_file(), "PINNED_BUILDER_MISSING")
        cmd = [sys.executable, str(script), "--tapir-repo", str(args.tapir_repo),
               "--devkit", str(args.devkit), "--build", str(output),
               "--ref", args.tapir_ref]
        started = time.monotonic()
        p = subprocess.run(cmd, capture_output=True, timeout=1800, shell=False)
        duration = round(time.monotonic() - started, 3)
        log = (p.stdout + b"\n=== STDERR ===\n" + p.stderr).decode("utf-8", "replace")
        (folder / "build.log").write_text(log, encoding="utf8")
        receipt = output / "apa-binary-receipt.json"
        verified = json.loads(receipt.read_text("utf8")) if p.returncode == 0 and receipt.exists() else None
        status = "BUILD_PASS_BINARY_NOT_INSTALLED" if verified and verified.get("status") == "BUILD_PASS_BINARY_IDENTITY_VERIFIED_NOT_INSTALLED" else "BUILD_FAILED"
        return {
            "status": status, "commit": observed, "exitCode": p.returncode,
            "durationSeconds": duration, "receipt": verified,
            "localLogSha256": hashlib.sha256(log.encode("utf8")).hexdigest(),
            "logTail": log[-12000:],
            "apxInstalled": False, "archicadOpened": False, "modelWrites": 0
        }
    finally:
        if source.exists():
            call(["git", "-C", str(args.source_repo), "worktree", "remove",
                  "--force", str(source)], timeout=100)


def publish(name, folder):
    result_file = folder / "result.json"
    require(result_file.is_file(), "RESULT_NOT_READY")
    marker = folder / "published.json"
    if marker.exists():
        return
    path = f"{OUTBOX}/{name}.json"
    # Never overwrite or replace a prior result, even if a prior publish was uncertain.
    try:
        prior, _ = read_file(path)
    except Exception as error:
        if "404" not in str(error) and "Not Found" not in str(error):
            raise
    else:
        require(prior == json.loads(result_file.read_text("utf8")),
                "REMOTE_RESULT_COLLISION")
        save(marker, {"status": "ALREADY_IDENTICAL"})
        return
    data = result_file.read_bytes()
    response = gh(f"repos/{BRIDGE}/contents/{path}", put={
        "message": f"APA AC29 build receipt {name} (no deployment)",
        "branch": BRANCH,
        "content": base64.b64encode(data).decode("ascii")
    })
    require(response["content"]["sha"] == git_blob(data),
            "RESULT_PUBLICATION_NOT_VERIFIED")
    save(marker, {"status": "PUBLISHED", "blobSha": response["content"]["sha"]})


def run_one(args, name):
    folder = args.state / name
    if (folder / "result.json").exists():
        publish(name, folder)
        return "RESULT_REPUBLISHED_OR_ALREADY_PUBLISHED"
    if folder.exists():
        # Crash during a build must never restart from scratch automatically.
        return "PREVIOUS_ATTEMPT_REQUIRES_MANUAL_RECONCILIATION"
    envelope, blob = read_file(f"{INBOX}/{name}.json")
    validate(envelope, name, args.approved_sha)
    folder.mkdir(parents=True, exist_ok=False)
    save(folder / "attempted.json", {"jobId": name, "blobSha": blob,
                                    "sourceRevision": args.approved_sha,
                                    "started": datetime.now(timezone.utc).isoformat(),
                                    "automaticRetry": False})
    try:
        result = build(args, envelope, folder)
    except Exception as error:
        result = {"status": "BUILD_BLOCKED", "reason": type(error).__name__ + ":" + str(error)[-1800:],
                  "apxInstalled": False, "archicadOpened": False, "modelWrites": 0}
    payload = {"schema": "APA_AC29_APX_BUILD_RESULT_V1", "jobId": name,
               "sourceBlob": blob, "sourceRevision": args.approved_sha,
               "automaticRetry": False, "result": result}
    save(folder / "result.json", payload)
    publish(name, folder)
    return result["status"]


def scan(args):
    files = gh(f"repos/{BRIDGE}/contents/{INBOX}?ref={quote(BRANCH, safe='')}")
    require(isinstance(files, list) and len(files) < 100, "MAILBOX_UNBOUNDED")
    jobs = sorted(item["name"][:-5] for item in files
                  if item.get("type") == "file" and item["name"].endswith(".json")
                  and JOB.fullmatch(item["name"][:-5]))
    for name in jobs:
        try:
            print(name, run_one(args, name), flush=True)
        except Exception as error:
            print(name, "DENIED_OR_OFFLINE", type(error).__name__, str(error)[-350:], flush=True)
    return len(jobs)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source-repo", type=Path, required=True,
                    help="Local safe-bim-layer Git clone")
    ap.add_argument("--tapir-repo", type=Path, required=True,
                    help="Existing local Tapir 1.5.10 Git checkout")
    ap.add_argument("--devkit", type=Path, required=True,
                    help="Archicad 29 DevKit Support directory")
    ap.add_argument("--approved-sha", required=True,
                    help="Locally authorized exact 40-character reviewed commit")
    ap.add_argument("--tapir-ref", default="HEAD",
                    help="Pinned Tapir ref inside your LOCAL checkout")
    ap.add_argument("--state", type=Path,
                    default=Path(r"C:\LocalAI\apa-ac29-apx-build-state"))
    ap.add_argument("--loop", action="store_true")
    ap.add_argument("--interval", type=int, default=30)
    ap.add_argument("--healthcheck", action="store_true")
    args = ap.parse_args()
    require(HEX.fullmatch(args.approved_sha), "EXACT_COMMIT_SHA_REQUIRED")
    require(10 <= args.interval <= 3600, "BAD_INTERVAL")
    approve_repository(args.source_repo)
    require(args.tapir_repo.is_dir() and (args.tapir_repo / ".git").exists(),
            "LOCAL_TAPIR_CHECKOUT_NOT_FOUND")
    require(args.devkit.is_dir(), "LOCAL_DEVKIT_NOT_FOUND")
    call(["gh", "auth", "status"])
    if args.healthcheck:
        print("APA_AC29_BUILD_MAILBOX_HEALTHCHECK_PASS_NO_MODEL_CALLS", flush=True)
        return
    args.state.mkdir(parents=True, exist_ok=True)
    lock = (args.state / ".single-instance.lock").open("a+b")
    try:
        lock.seek(0)
        lock.write(b"\0")
        lock.flush()
        lock.seek(0)
        msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        while True:
            print("BUILD_MAILBOX_SCAN", scan(args), flush=True)
            if not args.loop:
                return
            time.sleep(args.interval)
    finally:
        lock.close()


if __name__ == "__main__":
    main()
