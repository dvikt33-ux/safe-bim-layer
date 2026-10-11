"""Isolated durable send journal for opt-in APA GitHub receipt notifications.

This file is NOT the canonical APA task controller. It never edits PROJECT_PLAN,
the Slack receiver's SQLite database, or Archicad. A network uncertainty fails
closed rather than automatically posting a second copy.
"""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import sqlite3


class OutboxError(ValueError):
    pass


def default_path() -> Path:
    base = Path(os.environ.get("LOCALAPPDATA") or "data")
    return base / "SafeBIM" / "APA-Sync" / "receipt-outbox.sqlite3"


def payload_hash(event: dict) -> str:
    if not isinstance(event, dict) or not isinstance(event.get("event_id"), str):
        raise OutboxError("invalid notification event")
    body = json.dumps(event, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


class NotificationOutbox:
    """Single-writer SQLite reservations; no automatic retry after send uncertainty.

    Lifecycle: RESERVED → IN_FLIGHT → SENT.
    After a send exception: UNCERTAIN, so a future explicit request must find
    the same immutable event on Slack, or stop and require manual reconciliation.
    A crash during IN_FLIGHT is likewise never blindly retried.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS notifications(
                event_id TEXT PRIMARY KEY,
                payload_sha256 TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN
                    ('RESERVED','IN_FLIGHT','UNCERTAIN','SENT')),
                slack_ts TEXT,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )""")

    @contextmanager
    def _connect(self):
        db = sqlite3.connect(str(self.path), timeout=15)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def reserve(self, event: dict) -> str:
        """Idempotent reservation: conflicting same event ID is never reused."""
        event_id, digest = event["event_id"], payload_hash(event)
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT payload_sha256,status FROM notifications WHERE event_id=?",
                (event_id,)
            ).fetchone()
            if row is not None:
                if row["payload_sha256"] != digest:
                    raise OutboxError("notification event ID reused with different payload")
                return row["status"]
            db.execute(
                "INSERT INTO notifications(event_id,payload_sha256,status) VALUES(?,?,'RESERVED')",
                (event_id,digest)
            )
            return "RESERVED"

    def begin_send(self, event_id: str) -> None:
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            result = db.execute(
                """UPDATE notifications SET status='IN_FLIGHT',
                       updated_at=CURRENT_TIMESTAMP
                   WHERE event_id=? AND status='RESERVED'""",
                (event_id,)
            )
            if result.rowcount != 1:
                raise OutboxError("notification already in flight or sent")

    def mark_uncertain(self, event_id: str) -> None:
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute(
                """UPDATE notifications SET status='UNCERTAIN',
                       updated_at=CURRENT_TIMESTAMP
                   WHERE event_id=? AND status='IN_FLIGHT'""",
                (event_id,)
            )

    def mark_sent(self, event_id: str, slack_ts: str) -> None:
        if not isinstance(slack_ts, str) or not slack_ts:
            raise OutboxError("missing Slack timestamp, send status remains unverified")
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            result = db.execute(
                """UPDATE notifications SET status='SENT',slack_ts=?,
                       updated_at=CURRENT_TIMESTAMP WHERE event_id=?""",
                (slack_ts,event_id)
            )
            if result.rowcount != 1:
                raise OutboxError("notification reservation missing")

    def status(self, event_id: str) -> dict | None:
        with self._connect() as db:
            row = db.execute(
                "SELECT event_id,status,slack_ts FROM notifications WHERE event_id=?",
                (event_id,)
            ).fetchone()
            return dict(row) if row else None
