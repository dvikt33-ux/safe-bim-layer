"""Локальный шлюз GitHub -> Automa: только активация существующего чата.

Первый рубеж интеграции. Никакого ввода сообщений и операций Archicad.
События принимаются из отдельной папки safe-bim-bridge; настройки Opera
и идентификаторы Automa хранятся только на компьютере пользователя.
"""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import time
from urllib.parse import quote

REPOSITORY = "dvikt33-ux/safe-bim-bridge"
INBOX = "safe-bim-mailbox/chat-dispatch/jobs"
SCHEMA = "BUREAU_CHAT_ACTIVATION_V1"
ID = re.compile(r"^[a-z][a-z0-9-]{7,63}$")
EXTENSION_ID = re.compile(r"^[a-p]{32}$")
WORKFLOW_ID = re.compile(r"^[a-zA-Z0-9_-]{8,100}$")
HELD = ("LAUNCHING", "AWAIT_TAB_PROOF", "BLOCKED_NEEDS_RECONCILE")


def utc_now():
    return datetime.now(timezone.utc)


def iso(value):
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError("UTC_TIMESTAMP_REQUIRED")
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def git_blob_sha(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def validate(event, filename, targets, now=None):
    """Запрет удалённой передачи произвольного URL, текста или программы."""
    expected = {
        "schema", "jobId", "eventType", "targetChat",
        "action", "createdAt", "expiresAt", "sourceRef"
    }
    if not isinstance(event, dict) or set(event) != expected:
        raise ValueError("EVENT_FIELDS_INVALID")
    name = event["jobId"]
    if (event["schema"] != SCHEMA or not isinstance(name, str)
            or not ID.fullmatch(name) or name != filename):
        raise ValueError("EVENT_ID_INVALID")
    if event["action"] != "ACTIVATE_ONLY":
        raise ValueError("SEND_AND_WRITE_NOT_AUTHORIZED")
    if event["eventType"] not in (
        "REPORT_READY", "DEPARTMENT_REPORT_READY",
        "HQ_BRIEF_READY", "ARENA_RESULT_READY", "TRIGGER_PROBE"
    ):
        raise ValueError("EVENT_TYPE_NOT_ALLOWED")
    if not isinstance(event["targetChat"], str) or event["targetChat"] not in targets:
        raise ValueError("CHAT_NOT_IN_LOCAL_ALLOWLIST")
    source = event["sourceRef"]
    if source is not None:
        if (not isinstance(source, dict)
                or set(source) != {"repo", "path", "sha"}
                or not all(isinstance(source[key], str) for key in source)
                or not re.fullmatch(r"[0-9a-f]{40}", source["sha"])
                or ".." in source["path"]):
            raise ValueError("SOURCE_REF_INVALID")
    start, expiry = iso(event["createdAt"]), iso(event["expiresAt"])
    now = now or utc_now()
    if not (start <= now < expiry and
            0 < (expiry - start).total_seconds() <= 7 * 86400):
        raise ValueError("EVENT_EXPIRED_OR_INVALID")
    return event


def gh_api(api_path):
    process = subprocess.run(
        ["gh", "api", api_path], capture_output=True, text=True,
        timeout=30, check=False
    )
    if process.returncode:
        raise RuntimeError("GITHUB_API_UNAVAILABLE: " + process.stderr[-250:])
    return json.loads(process.stdout)


def fetch_events(known=None):
    """Общий транспорт, но отдельный от inbox PR #139 и его native-исполнителя."""
    items = gh_api(f"repos/{REPOSITORY}/contents/{INBOX}?ref=main")
    if not isinstance(items, list) or len(items) > 500:
        raise ValueError("UNEXPECTED_OR_OVERSIZED_GITHUB_INBOX")
    for item in sorted(items, key=lambda x: x["name"]):
        if (item.get("type") != "file" or
                not item["name"].endswith(".json")):
            continue
        name = item["name"][:-5]
        if not ID.fullmatch(name):
            continue
        if known is not None and name in known:
            if known[name] != item["sha"]:
                raise ValueError("IMMUTABLE_EVENT_REWRITTEN")
            continue
        obj = gh_api(f"repos/{REPOSITORY}/contents/{INBOX}/{name}.json?ref=main")
        raw = base64.b64decode("".join(obj["content"].split()), validate=True)
        sha = git_blob_sha(raw)
        if sha != obj["sha"] or sha != item["sha"]:
            raise ValueError("GITHUB_CONTENT_SHA_MISMATCH")
        yield name, json.loads(raw.decode("utf-8-sig")), sha


def database(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(str(path), timeout=20, isolation_level=None)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
          job_id TEXT PRIMARY KEY,
          target TEXT NOT NULL,
          event_type TEXT NOT NULL,
          blob_sha TEXT NOT NULL,
          created_at TEXT NOT NULL,
          expires_at TEXT NOT NULL,
          status TEXT NOT NULL,
          proof TEXT,
          changed_at TEXT NOT NULL
        )
    """)
    db.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS one_live_job_per_chat
        ON jobs(target) WHERE status IN
          ('LAUNCHING', 'AWAIT_TAB_PROOF', 'BLOCKED_NEEDS_RECONCILE')
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS transitions (
          seq INTEGER PRIMARY KEY AUTOINCREMENT,
          job_id TEXT NOT NULL,
          status TEXT NOT NULL,
          at TEXT NOT NULL,
          detail TEXT NOT NULL
        )
    """)
    return db


def transition(db, job_id, status, detail=""):
    now = utc_now().isoformat()
    db.execute("UPDATE jobs SET status=?,changed_at=? WHERE job_id=?",
               (status, now, job_id))
    db.execute(
        "INSERT INTO transitions(job_id,status,at,detail) VALUES(?,?,?,?)",
        (job_id, status, now, detail[:300])
    )


def ingest(db, event, sha, targets, now=None):
    validate(event, event["jobId"], targets, now=now)
    job_id = event["jobId"]
    db.execute("BEGIN IMMEDIATE")
    try:
        previous = db.execute(
            "SELECT blob_sha FROM jobs WHERE job_id=?", (job_id,)
        ).fetchone()
        if previous:
            if previous[0] != sha:
                raise ValueError("IMMUTABLE_EVENT_REWRITTEN")
            db.execute("COMMIT")
            return "DUPLICATE_IGNORED"
        db.execute(
            """INSERT INTO jobs
               (job_id,target,event_type,blob_sha,created_at,expires_at,status,changed_at)
               VALUES(?,?,?,?,?,?,'QUEUED',?)""",
            (job_id, event["targetChat"], event["eventType"],
             sha, iso(event["createdAt"]).isoformat(),
             iso(event["expiresAt"]).isoformat(), utc_now().isoformat())
        )
        transition(db, job_id, "QUEUED", "GITHUB_BLOB_VERIFIED")
        db.execute("COMMIT")
        return "QUEUED"
    except Exception:
        db.execute("ROLLBACK")
        raise


def claim(db):
    """Атомарно выдаёт одно UI-переключение за раз, не прерывая другие исследования."""
    db.execute("BEGIN IMMEDIATE")
    try:
        now = utc_now().isoformat()
        for (expired_id,) in db.execute(
            "SELECT job_id FROM jobs WHERE status='QUEUED' AND expires_at <= ?",
            (now,)
        ).fetchall():
            transition(db, expired_id, "EXPIRED", "NOT_LAUNCHED_AFTER_EXPIRY")
        row = db.execute(
            """SELECT job_id,target FROM jobs AS j
               WHERE status='QUEUED' AND NOT EXISTS (
                 SELECT 1 FROM jobs AS busy
                 WHERE busy.status IN
                   ('LAUNCHING','AWAIT_TAB_PROOF','BLOCKED_NEEDS_RECONCILE')
               )
               ORDER BY created_at,job_id LIMIT 1"""
        ).fetchone()
        if row:
            transition(db, row[0], "LAUNCHING", "INTENT_DURABLE_BEFORE_BROWSER")
        db.execute("COMMIT")
        return row
    except Exception:
        db.execute("ROLLBACK")
        raise


def load_config(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if set(data) != {"operaExe", "extensionId", "targets"}:
        raise ValueError("LOCAL_CONFIG_FIELDS_INVALID")
    if not EXTENSION_ID.fullmatch(data["extensionId"]):
        raise ValueError("INVALID_LOCAL_EXTENSION_ID")
    if not isinstance(data["targets"], dict) or not data["targets"]:
        raise ValueError("EMPTY_LOCAL_TARGET_ALLOWLIST")
    for key, target in data["targets"].items():
        if (not re.fullmatch(r"[A-Za-z][A-Za-z0-9-]{1,32}", key)
                or not isinstance(target, dict)
                or set(target) != {"workflowId"}
                or not WORKFLOW_ID.fullmatch(target["workflowId"])):
            raise ValueError("INVALID_LOCAL_TARGET")
    return data


def activation_url(config, job_id, target):
    """Официальный URL-триггер Automa; данные GitHub не задают URL чата."""
    workflow = config["targets"][target]["workflowId"]
    extension = config["extensionId"]
    return (
        f"chrome-extension://{extension}/execute.html#/{workflow}"
        f"?jobId={quote(job_id, safe='')}&targetChat={quote(target, safe='')}"
    )


def dispatch_one(db, config, open_browser=None):
    """Popen подтверждает лишь запрос браузеру, но НЕ запуск Automa."""
    opera = Path(config["operaExe"])
    if not opera.is_file():
        raise ValueError("OPERA_EXE_NOT_FOUND")
    row = claim(db)
    if not row:
        return "NO_ELIGIBLE_JOBS"
    job_id, target = row
    url = activation_url(config, job_id, target)
    if open_browser is None:
        def open_browser(exe, link):
            subprocess.Popen([str(exe), link],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL, close_fds=True)
    try:
        open_browser(opera, url)
    except Exception as exc:
        transition(db, job_id, "BLOCKED_NEEDS_RECONCILE",
                   "BROWSER_START_ERROR:" + type(exc).__name__)
        return "BLOCKED_NEEDS_RECONCILE:" + job_id
    transition(db, job_id, "AWAIT_TAB_PROOF", "BROWSER_INVOCATION_ONLY")
    return "AWAIT_TAB_PROOF:" + job_id


def confirm_tab(db, job_id, proof):
    """Только после отдельного подтверждения выбора нужной вкладки."""
    if not proof or len(proof) > 300:
        raise ValueError("NONEMPTY_SHORT_PROOF_REQUIRED")
    db.execute("BEGIN IMMEDIATE")
    try:
        row = db.execute(
            "SELECT status FROM jobs WHERE job_id=?", (job_id,)
        ).fetchone()
        if not row or row[0] != "AWAIT_TAB_PROOF":
            raise ValueError("JOB_NOT_WAITING_FOR_TAB_CONFIRMATION")
        transition(db, job_id, "TAB_SELECTED_CONFIRMED", proof)
        db.execute("COMMIT")
    except Exception:
        db.execute("ROLLBACK")
        raise


def cancel_blocked(db, job_id, proof):
    """После ручной сверки разблокировать неизвестный результат без повтора."""
    if not proof or len(proof) > 300:
        raise ValueError("NONEMPTY_SHORT_PROOF_REQUIRED")
    db.execute("BEGIN IMMEDIATE")
    try:
        row = db.execute(
            "SELECT status FROM jobs WHERE job_id=?", (job_id,)
        ).fetchone()
        if not row or row[0] not in ("LAUNCHING", "BLOCKED_NEEDS_RECONCILE"):
            raise ValueError("JOB_NOT_BLOCKED_FOR_REVIEW")
        transition(db, job_id, "CANCELLED_AFTER_REVIEW", proof)
        db.execute("COMMIT")
    except Exception:
        db.execute("ROLLBACK")
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True)
    parser.add_argument("--config", required=True)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("scan")
    sub.add_parser("dispatch")
    sub.add_parser("status")
    watch = sub.add_parser("watch")
    watch.add_argument("--interval", type=int, default=5)
    ack = sub.add_parser("confirm-tab")
    ack.add_argument("job_id")
    ack.add_argument("--proof", required=True)
    cancel = sub.add_parser("cancel-blocked")
    cancel.add_argument("job_id")
    cancel.add_argument("--proof", required=True)
    args = parser.parse_args(argv)
    config = load_config(args.config)
    db = database(args.db)
    try:
        if args.command in ("scan", "watch"):
            if args.command == "watch" and not 5 <= args.interval <= 3600:
                raise ValueError("INVALID_WATCH_INTERVAL")
            while True:
                try:
                    known = dict(db.execute("SELECT job_id,blob_sha FROM jobs"))
                    for name, event, sha in fetch_events(known):
                        validate(event, name, config["targets"])
                        print(name, ingest(db, event, sha, config["targets"]), flush=True)
                    if args.command == "watch":
                        print(dispatch_one(db, config), flush=True)
                except Exception as exc:
                    if args.command == "scan":
                        raise
                    print("WATCH_BLOCKED:", type(exc).__name__, str(exc)[:200], flush=True)
                if args.command != "watch":
                    break
                time.sleep(args.interval)
        elif args.command == "dispatch":
            print(dispatch_one(db, config))
        elif args.command == "confirm-tab":
            confirm_tab(db, args.job_id, args.proof)
            print("TAB_SELECTED_CONFIRMED", args.job_id)
        elif args.command == "cancel-blocked":
            cancel_blocked(db, args.job_id, args.proof)
            print("CANCELLED_AFTER_REVIEW", args.job_id)
        else:
            for row in db.execute(
                "SELECT job_id,target,event_type,status FROM jobs ORDER BY created_at,job_id"
            ):
                print(*row, sep=" | ")
    finally:
        db.close()


if __name__ == "__main__":
    main()
