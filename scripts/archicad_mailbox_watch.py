"""Persistent read-only-by-policy watcher for new Safe BIM Mailbox JOBs.

On FIRST launch, inventories the existing inbox as a baseline and DOES NOT
process historical messages. Subsequently processes only unseen fresh dry-run
jobs with exactly the verified Archicad test project fingerprint.

Uses the EXISTING guarded local --message-id host, its pinned bridge checkout,
and its durable SQLite journals. Never enables execution, creates approvals,
saves a PLN, clears a journal, or retries an attempted job automatically.
"""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

REPO = "dvikt33-ux/safe-bim-bridge"
BRANCH = "main"
INBOX = "safe-bim-mailbox/gpt-live/inbox"
MAX_LISTED = 900
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")
_STATE_NAME = "mailbox-watcher-v1.json"


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def utc_time(value):
    if not isinstance(value, str):
        raise ValueError("datetime must be a string")
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("timezone missing")
    return dt.astimezone(timezone.utc)


def atomic_json(path, obj):
    text = json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True,
                      allow_nan=False) + "\n"
    tmp = path.with_name(path.name + ".pending")
    with tmp.open("w", encoding="utf-8") as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def gh_json(args, *, gh="gh"):
    proc = subprocess.run([gh, "api", *args], capture_output=True,
                          text=True, encoding="utf-8", errors="replace", timeout=35)
    if proc.returncode:
        raise RuntimeError("GitHub API failed; check gh auth status and connection")
    return json.loads(proc.stdout)


def list_inbox(gh="gh"):
    objects = gh_json([f"repos/{REPO}/contents/{INBOX}?ref={BRANCH}"], gh=gh)
    if not isinstance(objects, list) or len(objects) >= MAX_LISTED:
        raise RuntimeError("Inbox listing is unavailable or near API truncation; stop")
    result = {}
    for item in objects:
        name = item.get("name") if isinstance(item, dict) else None
        if isinstance(name, str) and name.endswith(".json"):
            mid = name[:-5]
            if SAFE_ID.fullmatch(mid):
                result[mid] = item.get("sha")
    return result


def load_remote_job(mid, gh="gh"):
    if not SAFE_ID.fullmatch(mid):
        raise ValueError("unsafe remote message ID")
    obj = gh_json([f"repos/{REPO}/contents/{INBOX}/{mid}.json?ref={BRANCH}"], gh=gh)
    raw = base64.b64decode(obj["content"].replace("\n", ""), validate=True)
    msg = json.loads(raw.decode("utf-8"))
    if not isinstance(msg, dict) or msg.get("messageId") != mid:
        raise ValueError("message id or envelope invalid")
    return msg


def validate_job(msg, mid, binding, now=None):
    """Validate only dry-run intake. Local one-shot worker revalidates everything."""
    try:
        if not isinstance(msg, dict) or msg.get("messageId") != mid:
            return "BAD_ENVELOPE"
        if msg.get("kind") != "JOB" or type(msg.get("protocolVersion")) is not int or msg["protocolVersion"] != 1:
            return "NOT_A_V1_JOB"
        payload = msg.get("payload")
        if not isinstance(payload, dict) or msg.get("payloadHash") != digest(payload):
            return "PAYLOAD_HASH_MISMATCH"
        created = utc_time(msg.get("createdAt"))
        expiration = utc_time(payload.get("expiresAt"))
        now = datetime.now(timezone.utc) if now is None else now
        if expiration <= now or created > now or expiration - created > timedelta(minutes=15):
            return "EXPIRED_OR_INVALID_WINDOW"
        if payload.get("mode", "dry-run") != "dry-run":
            return "EXECUTE_NOT_ENABLED"
        if payload.get("recipe") != "create_wall_v1":
            return "UNSUPPORTED_RECIPE"
        for key in ("instanceId", "logicalProjectId", "projectName", "projectPath", "port"):
            if payload.get(key) != binding.get(key):
                return "TARGET_MISMATCH"
        return "ACCEPT"
    except (ValueError, TypeError, OverflowError):
        return "INVALID_JOB"


def inspect_binding(python, host, bridge, state_dir):
    p = subprocess.run([str(python), str(host), "--bridge-source", str(bridge),
                        "--data-dir", str(state_dir), "--inspect"],
                       text=True, encoding="utf-8", errors="replace",
                       capture_output=True, timeout=60)
    if p.returncode:
        raise RuntimeError("Archicad --inspect failed; watcher will not process jobs")
    try:
        return json.loads(p.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Archicad --inspect did not return JSON") from exc


def run_one(python, host, bridge, state_dir, mid):
    # Deliberately never pass --enable-execute or --approval.
    p = subprocess.run([str(python), str(host), "--bridge-source", str(bridge),
                        "--data-dir", str(state_dir), "--message-id", mid],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=180)
    if p.returncode:
        return {"status": "WORKER_ERROR", "returnCode": p.returncode,
                "note": "not retried automatically"}
    try:
        report = json.loads(p.stdout)
    except json.JSONDecodeError:
        return {"status": "WORKER_INVALID_RESPONSE", "note": "not retried"}
    published = report.get("published", []) if isinstance(report, dict) else []
    writes = report.get("writes", []) if isinstance(report, dict) else []
    statuses = [x.get("result", {}).get("status") for x in writes if isinstance(x, dict)]
    return {"status": "PROCESSED", "writeResults": statuses,
            "publication": [x.get("status") for x in published if isinstance(x, dict)]}


def pump_one(state_path, inbox, read_remote, inspect, execute, expected, *, now=None):
    """Single scan, pure injectable transport hooks for offline tests."""
    now = datetime.now(timezone.utc) if now is None else now
    if not state_path.exists():
        state = {"version": 1, "createdAt": now.isoformat(),
                 "seen": {mid: "BASELINE" for mid in inbox}}
        atomic_json(state_path, state)
        return {"status": "BASELINE_CREATED", "oldJobsSkipped": len(inbox)}
    state = json.loads(state_path.read_text(encoding="utf-8"))
    if state.get("version") != 1 or not isinstance(state.get("seen"), dict):
        raise RuntimeError("watcher ledger invalid; never reset it automatically")
    new = [mid for mid in sorted(inbox) if mid not in state["seen"]]
    if not new:
        return {"status": "IDLE", "newJobs": 0}
    results = []
    for mid in new:
        # Fetch and validate the remote message BEFORE binding or triggering worker.
        # If Archicad is closed or the wrong project is open, PAUSE without
        # consuming the new request. Only authenticated input errors are
        # durably quarantined; the worker has not run at this point.
        try:
            binding = inspect()
        except Exception as exc:
            return {"status": "PAUSED_NO_ARCHICAD", "error": type(exc).__name__,
                    "pendingJobs": len(new), "jobPublished": False}
        if not isinstance(binding, dict) or any(binding.get(k) != expected.get(k)
               for k in ("instanceId", "logicalProjectId", "projectName",
                         "projectPath", "port")):
            return {"status": "PAUSED_WRONG_PROJECT", "pendingJobs": len(new),
                    "jobPublished": False}
        try:
            remote = read_remote(mid)
            decision = validate_job(remote, mid, binding, now)
        except Exception as exc:
            decision = "INPUT_ERROR_" + type(exc).__name__
        # Persist decision BEFORE any possible worker invocation.
        state["seen"][mid] = {"decision": decision, "recordedAt": now.isoformat()}
        atomic_json(state_path, state)
        if decision == "ACCEPT":
            # A crash after this point may leave an ambiguous outcome.
            # The ledger guarantees we never automatically resubmit.
            try:
                state["seen"][mid]["worker"] = execute(mid)
            except Exception as exc:
                state["seen"][mid]["worker"] = {
                    "status": "UNKNOWN_OUTCOME", "errorType": type(exc).__name__,
                    "automaticRetry": False}
            atomic_json(state_path, state)
        results.append({"messageId": mid, "decision": decision,
                        "worker": state["seen"][mid].get("worker")})
    return {"status": "SCANNED", "results": results}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--python", required=True, type=Path)
    ap.add_argument("--host-file", required=True, type=Path)
    ap.add_argument("--bridge-source", required=True, type=Path)
    ap.add_argument("--data-dir", required=True, type=Path)
    ap.add_argument("--expected-project-path", required=True)
    ap.add_argument("--expected-project-name", required=True)
    ap.add_argument("--expected-port", type=int, required=True)
    ap.add_argument("--poll-seconds", type=float, default=12)
    ap.add_argument("--loop", action="store_true", help="poll continuously; default performs a single scan")
    ap.add_argument("--gh", default="gh")
    args = ap.parse_args()
    if not (5 <= args.poll_seconds <= 600):
        ap.error("poll-seconds must be 5..600")
    for item in (args.python, args.host_file, args.bridge_source, args.data_dir):
        if not item.exists():
            ap.error(f"missing existing file or directory: {item}")
    state_path = args.data_dir / _STATE_NAME
    expected = None
    while True:
        try:
            actual = inspect_binding(args.python, args.host_file,
                                     args.bridge_source, args.data_dir)
            if (actual.get("projectPath") != args.expected_project_path
                or actual.get("projectName") != args.expected_project_name
                or actual.get("port") != args.expected_port):
                raise RuntimeError("current Archicad project is not the pinned test PLN")
            if expected is None:
                expected = {k: actual[k] for k in (
                    "instanceId", "logicalProjectId", "projectName", "projectPath", "port")}
            elif any(actual.get(k) != expected.get(k) for k in expected):
                # Reopening can change binding identity: never silently adopt it.
                raise RuntimeError("Archicad project binding changed since watcher activation")
            out = pump_one(state_path, list_inbox(args.gh),
                           lambda mid: load_remote_job(mid, args.gh),
                           lambda: inspect_binding(args.python, args.host_file,
                                                   args.bridge_source, args.data_dir),
                           lambda mid: run_one(args.python, args.host_file,
                                               args.bridge_source, args.data_dir, mid),
                           expected)
            print(json.dumps(out, ensure_ascii=False), flush=True)
        except Exception as exc:
            print(json.dumps({"status": "PAUSED", "error": type(exc).__name__,
                              "note": "No jobs were retried"}, ensure_ascii=False), flush=True)
            if not args.loop:
                return 2
        if not args.loop:
            return 0
        time.sleep(args.poll_seconds)


if __name__ == "__main__":
    sys.exit(main())
