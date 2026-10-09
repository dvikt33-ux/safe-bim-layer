"""APA event ledger. Standard-library only; never touches Archicad, PLN or Git."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import json
import re
import sqlite3
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

EVENT_PREFIX = "APA_EVENT_V1"
EVENT_PATTERN = re.compile(
    r"\AAPA_EVENT_V1\s*\n[\s\S]*?```(?:json|JSON)?\s*\n(?P<payload>\{[\s\S]*?\})\s*\n```\s*\Z"
)
IDENT = re.compile(r"\A[A-Za-z0-9][A-Za-z0-9_.:-]{2,95}\Z")
STATUSES = frozenset({"INFO", "PASS", "BLOCKED", "NOT_VERIFIED"})
PHASES = frozenset({"SOURCE", "OFFLINE", "SYNTHETIC", "BUILD", "LIVE"})
FIELDS = frozenset({
    "event_id", "task_id", "status", "phase", "source",
    "summary", "evidence_urls", "supersedes",
})


class InvalidEvent(ValueError):
    """A malformed event is ignored by the event listener."""


def parse_event(text: str) -> dict | None:
    """Parse only explicit, fenced APA events; never infer from ordinary chat."""
    if not isinstance(text, str) or not text.startswith(EVENT_PREFIX):
        return None
    if len(text) > 5000:
        raise InvalidEvent("Event exceeds 5000 characters")
    match = EVENT_PATTERN.fullmatch(text)
    if match is None:
        raise InvalidEvent("Expected APA_EVENT_V1 and one JSON code fence")
    try:
        event = json.loads(match.group("payload"))
    except json.JSONDecodeError as exc:
        raise InvalidEvent("Invalid event JSON") from exc
    if not isinstance(event, dict) or set(event) - FIELDS:
        raise InvalidEvent("Unexpected event keys")
    for key in ("event_id", "task_id", "status", "phase", "source", "summary"):
        if not isinstance(event.get(key), str):
            raise InvalidEvent(f"Missing or invalid {key}")
    for key in ("event_id", "task_id"):
        if not IDENT.fullmatch(event[key]):
            raise InvalidEvent(f"Invalid {key}")
    if event["status"] not in STATUSES or event["phase"] not in PHASES:
        raise InvalidEvent("Unknown status or phase")
    if not 1 <= len(event["source"]) <= 100:
        raise InvalidEvent("Invalid source")
    if not 1 <= len(event["summary"]) <= 1000:
        raise InvalidEvent("Invalid summary")
    evidence = event.get("evidence_urls", [])
    if not isinstance(evidence, list) or len(evidence) > 8:
        raise InvalidEvent("Invalid evidence_urls")
    for url in evidence:
        if not isinstance(url, str) or len(url) > 500:
            raise InvalidEvent("Invalid evidence URL")
        parsed = urlsplit(url)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise InvalidEvent("Evidence URL must be HTTPS without credentials")
    if event["status"] == "PASS" and not evidence:
        raise InvalidEvent("PASS requires a verifiable evidence URL")
    supersedes = event.get("supersedes")
    if supersedes is not None and (not isinstance(supersedes, str) or not IDENT.fullmatch(supersedes)):
        raise InvalidEvent("Invalid supersedes event ID")
    event["evidence_urls"] = evidence
    event["supersedes"] = supersedes
    return event


def format_event(event: dict) -> str:
    """Human-readable title plus machine-readable fenced event."""
    payload = json.dumps(event, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return f"{EVENT_PREFIX}\n{event['task_id']} | {event['status']} | {event['phase']}: {event['summary']}\n```json\n{payload}\n```"


class EventStore:
    """Append-only, idempotent SQLite ledger with explicit conflict detection."""

    def __init__(self, path: str | Path):
        self.path = Path(path).expanduser()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL UNIQUE,
                    task_id TEXT NOT NULL,
                    phase TEXT NOT NULL,
                    status TEXT NOT NULL,
                    source TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    supersedes TEXT,
                    conflict INTEGER NOT NULL,
                    slack_channel TEXT NOT NULL,
                    slack_ts TEXT NOT NULL,
                    ingested_at TEXT NOT NULL,
                    UNIQUE (slack_channel, slack_ts)
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS events_task_phase ON events(task_id, phase, seq)")

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(str(self.path), timeout=15)
        conn.row_factory = sqlite3.Row
        try:
            with conn:
                yield conn
        finally:
            # sqlite3's context manager commits but does NOT close the file.
            # Explicit close is required for Windows temporary directories.
            conn.close()

    def ingest(self, text: str, *, slack_channel: str, slack_ts: str) -> dict:
        event = parse_event(text)
        if event is None:
            return {"accepted": False, "reason": "not_an_apa_event"}
        if not slack_channel or not slack_ts:
            raise InvalidEvent("Slack channel and timestamp required")
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            dup = conn.execute(
                "SELECT seq,event_id,payload,slack_channel,slack_ts FROM events WHERE event_id=? OR (slack_channel=? AND slack_ts=?)",
                (event["event_id"], slack_channel, slack_ts),
            ).fetchone()
            if dup:
                current_payload = json.loads(dup["payload"])
                if dup["event_id"] != event["event_id"] or current_payload != event:
                    raise InvalidEvent("Event ID or Slack timestamp reused with different content")
                return {"accepted": False, "reason": "duplicate", "seq": dup["seq"]}
            prev = conn.execute(
                "SELECT event_id,status,conflict,seq FROM events WHERE task_id=? AND phase=? ORDER BY seq DESC LIMIT 1",
                (event["task_id"], event["phase"]),
            ).fetchone()
            supersedes = event["supersedes"]
            if supersedes and (prev is None or prev["event_id"] != supersedes):
                raise InvalidEvent("supersedes must reference the latest event of the same task and phase")
            # Once a conflict exists, ordinary repeat messages cannot clear it.
            # Only explicit supersession of the latest event resolves the dispute.
            conflict = bool(prev and supersedes is None and (
                prev["status"] != event["status"] or prev["conflict"]
            ))
            now = datetime.now(timezone.utc).isoformat(timespec="seconds")
            cur = conn.execute("""
                INSERT INTO events(
                    event_id,task_id,phase,status,source,summary,payload,supersedes,
                    conflict,slack_channel,slack_ts,ingested_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                event["event_id"], event["task_id"], event["phase"], event["status"],
                event["source"], event["summary"],
                json.dumps(event, ensure_ascii=False, sort_keys=True),
                supersedes, int(conflict), slack_channel, slack_ts, now,
            ))
            return {"accepted": True, "seq": cur.lastrowid, "conflict": conflict}

    def changes(self, after: int = 0, limit: int = 100) -> dict:
        if not isinstance(after, int) or after < 0:
            raise ValueError("after must be a nonnegative integer")
        limit = min(200, max(1, int(limit)))
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM events WHERE seq > ? ORDER BY seq ASC LIMIT ?",
                (after, limit),
            ).fetchall()
        changes = [self._present(row) for row in rows]
        return {"changes": changes, "next_cursor": changes[-1]["seq"] if changes else after}

    def latest_states(self) -> dict:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM events ORDER BY seq DESC").fetchall()
        latest = {}
        for row in rows:
            key = f"{row['task_id']}:{row['phase']}"
            if key not in latest:
                latest[key] = self._present(row)
                latest[key]["effective_status"] = "CONFLICT" if row["conflict"] else row["status"]
        return {"state": latest}

    @staticmethod
    def _present(row: sqlite3.Row) -> dict:
        return {
            "seq": row["seq"], "event_id": row["event_id"],
            "task_id": row["task_id"], "phase": row["phase"],
            "status": row["status"], "source": row["source"],
            "summary": row["summary"], "payload": json.loads(row["payload"]),
            "conflict": bool(row["conflict"]), "slack_channel": row["slack_channel"],
            "slack_ts": row["slack_ts"], "ingested_at": row["ingested_at"],
        }


def make_handler(store: EventStore):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            path = urlsplit(self.path)
            try:
                if path.path == "/health":
                    result = {"ok": True, "mode": "read_only_local"}
                elif path.path == "/v1/changes":
                    query = parse_qs(path.query)
                    result = store.changes(
                        after=int(query.get("after", ["0"])[0]),
                        limit=int(query.get("limit", ["100"])[0]),
                    )
                elif path.path == "/v1/state":
                    result = store.latest_states()
                else:
                    return self._send(404, {"error": "not_found"})
            except (ValueError, TypeError, OverflowError):
                return self._send(400, {"error": "bad_query"})
            return self._send(200, result)

        def _send(self, status: int, data: dict):
            body = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return Handler


def make_server(store: EventStore, *, host: str = "127.0.0.1", port: int = 8765):
    if host != "127.0.0.1":
        raise ValueError("Coordinator HTTP API is intentionally localhost-only")
    return ThreadingHTTPServer((host, port), make_handler(store))


def main():
    parser = argparse.ArgumentParser(description="APA local read-only event API")
    parser.add_argument("--db", default="data/apa-sync/events.sqlite3")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    store = EventStore(args.db)
    server = make_server(store, port=args.port)
    print(f"APA ledger listening at http://127.0.0.1:{server.server_port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
