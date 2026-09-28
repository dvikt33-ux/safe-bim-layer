"""Crash-safe local state. Not the authority for a BIM transaction."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path


SCHEMA = """
CREATE TABLE IF NOT EXISTS messages (
    message_id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    created_at TEXT NOT NULL,
    payload TEXT NOT NULL,
    state TEXT NOT NULL,
    retry_count INTEGER NOT NULL DEFAULT 0,
    direction TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS context_requests (
    request_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    requested_scope TEXT NOT NULL,
    state TEXT NOT NULL,
    snapshot_id TEXT,
    response_json TEXT,
    created_at TEXT NOT NULL,
    instance_id TEXT
);
CREATE TABLE IF NOT EXISTS archicad_clients (
    instance_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    logical_project_id TEXT,
    last_seen TEXT NOT NULL,
    connection_state TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS remote_jobs (
    job_id TEXT PRIMARY KEY,
    snapshot_id TEXT,
    payload TEXT NOT NULL,
    state TEXT NOT NULL,
    source_message_id TEXT UNIQUE,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS results (
    job_id TEXT PRIMARY KEY,
    result TEXT NOT NULL,
    upload_state TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS connection_state (
    channel TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    detail TEXT,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


class BridgeStore:
    def __init__(self, path: str | Path):
        self.path = str(path)
        self._db = sqlite3.connect(self.path, isolation_level=None)
        self._db.row_factory = sqlite3.Row
        self._db.execute('PRAGMA journal_mode=WAL')
        self._db.execute('PRAGMA foreign_keys=ON')
        self._db.executescript(SCHEMA)
        self._migrate()

    def close(self) -> None:
        self._db.close()

    def reopen(self) -> 'BridgeStore':
        self.close()
        return BridgeStore(self.path)

    def put_message(self, message_id: str, kind: str, created_at: str, payload: dict,
                    state: str, direction: str) -> bool:
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        cur = self._db.execute(
            'INSERT OR IGNORE INTO messages(message_id,kind,created_at,payload,state,retry_count,direction) '
            'VALUES (?,?,?,?,?,0,?)',
            (message_id, kind, created_at, encoded, state, direction))
        return cur.rowcount == 1

    def message(self, message_id: str):
        row = self._db.execute('SELECT * FROM messages WHERE message_id=?', (message_id,)).fetchone()
        return _decode_payload(row) if row else None

    def set_message_state(self, message_id: str, state: str, retry_count: int | None = None) -> None:
        if retry_count is None:
            self._db.execute('UPDATE messages SET state=? WHERE message_id=?', (state, message_id))
        else:
            self._db.execute('UPDATE messages SET state=?,retry_count=? WHERE message_id=?',
                             (state, retry_count, message_id))

    def pending_outbox(self):
        rows = self._db.execute(
            "SELECT * FROM messages WHERE direction='outbox' AND state IN ('PENDING','RETRY','UNCERTAIN') ORDER BY created_at").fetchall()
        return [_decode_payload(row) for row in rows]

    def put_context_request(self, request_id: str, project_id: str, scope: str, state: str,
                            created_at: str, snapshot_id: str | None = None,
                            response: dict | None = None, instance_id: str | None = None) -> bool:
        cur = self._db.execute(
            'INSERT OR IGNORE INTO context_requests(request_id,project_id,requested_scope,state,snapshot_id,response_json,created_at,instance_id) '
            'VALUES (?,?,?,?,?,?,?,?)',
            (request_id, project_id, scope, state, snapshot_id,
             json.dumps(response, ensure_ascii=False) if response is not None else None, created_at,
             instance_id))
        return cur.rowcount == 1

    def context_request(self, request_id: str):
        row = self._db.execute('SELECT * FROM context_requests WHERE request_id=?', (request_id,)).fetchone()
        if row is None:
            return None
        value = dict(row)
        raw = value.get('response_json')
        value['response'] = json.loads(raw) if raw else None
        return value

    def set_context_state(self, request_id: str, state: str, snapshot_id: str | None = None,
                          response: dict | None = None) -> None:
        current = self.context_request(request_id)
        if current is None:
            raise KeyError(request_id)
        self._db.execute(
            'UPDATE context_requests SET state=?,snapshot_id=?,response_json=? WHERE request_id=?',
            (state, snapshot_id if snapshot_id is not None else current.get('snapshot_id'),
             json.dumps(response, ensure_ascii=False) if response is not None else current.get('response_json'),
             request_id))

    def put_remote_job(self, job_id: str, snapshot_id: str | None, payload: dict, state: str,
                       source_message_id: str, created_at: str) -> bool:
        cur = self._db.execute(
            'INSERT OR IGNORE INTO remote_jobs(job_id,snapshot_id,payload,state,source_message_id,created_at) '
            'VALUES (?,?,?,?,?,?)',
            (job_id, snapshot_id, json.dumps(payload, ensure_ascii=False, sort_keys=True),
             state, source_message_id, created_at))
        return cur.rowcount == 1

    def job_for_message(self, source_message_id: str):
        row = self._db.execute(
            'SELECT * FROM remote_jobs WHERE source_message_id=?', (source_message_id,)).fetchone()
        return _decode_payload(row) if row else None

    def jobs(self):
        return [_decode_payload(row) for row in self._db.execute('SELECT * FROM remote_jobs ORDER BY created_at')]

    def put_result(self, job_id: str, result: dict, upload_state: str) -> None:
        encoded = json.dumps(result, ensure_ascii=False, sort_keys=True)
        self._db.execute(
            'INSERT INTO results(job_id,result,upload_state) VALUES (?,?,?) '
            'ON CONFLICT(job_id) DO UPDATE SET result=excluded.result,upload_state=excluded.upload_state',
            (job_id, encoded, upload_state))

    def result(self, job_id: str):
        row = self._db.execute('SELECT * FROM results WHERE job_id=?', (job_id,)).fetchone()
        return _decode_payload(row, payload_key='result') if row else None

    def set_connection(self, channel: str, status: str, detail: str, updated_at: str) -> None:
        self._db.execute(
            'INSERT INTO connection_state(channel,status,detail,updated_at) VALUES (?,?,?,?) '
            'ON CONFLICT(channel) DO UPDATE SET status=excluded.status,detail=excluded.detail,updated_at=excluded.updated_at',
            (channel, status, detail, updated_at))

    def connection(self, channel: str):
        row = self._db.execute('SELECT * FROM connection_state WHERE channel=?', (channel,)).fetchone()
        return dict(row) if row else None

    def set_meta(self, key: str, value: str) -> None:
        self._db.execute(
            'INSERT INTO meta(key,value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',
            (key, value))

    def meta(self, key: str, default=None):
        row = self._db.execute('SELECT value FROM meta WHERE key=?', (key,)).fetchone()
        return row['value'] if row else default

    def corrupt_message_payload(self, message_id: str) -> None:
        self._db.execute("UPDATE messages SET payload=? WHERE message_id=?", ('{not-json', message_id))

    def messages_by_state(self, state: str):
        rows = self._db.execute(
            'SELECT * FROM messages WHERE state=? ORDER BY created_at', (state,)).fetchall()
        return [_decode_payload(row) for row in rows]

    def upsert_client(self, instance_id: str, session_id: str, project_id: str | None,
                      last_seen: str, state: str) -> None:
        self._db.execute(
            'INSERT INTO archicad_clients(instance_id,session_id,logical_project_id,last_seen,connection_state) '
            'VALUES (?,?,?,?,?) ON CONFLICT(instance_id) DO UPDATE SET '
            'session_id=excluded.session_id, logical_project_id=excluded.logical_project_id, '
            'last_seen=excluded.last_seen, connection_state=excluded.connection_state',
            (instance_id, session_id, project_id, last_seen, state))

    def set_client_state(self, instance_id: str, state: str, last_seen: str) -> None:
        self._db.execute(
            'UPDATE archicad_clients SET connection_state=?, last_seen=? WHERE instance_id=?',
            (state, last_seen, instance_id))

    def client(self, instance_id: str):
        row = self._db.execute(
            'SELECT * FROM archicad_clients WHERE instance_id=?', (instance_id,)).fetchone()
        return dict(row) if row else None

    def clients(self):
        return [dict(row) for row in self._db.execute(
            'SELECT * FROM archicad_clients ORDER BY instance_id')]

    def _migrate(self) -> None:
        columns = {row['name'] for row in self._db.execute('PRAGMA table_info(context_requests)')}
        if 'instance_id' not in columns:
            self._db.execute('ALTER TABLE context_requests ADD COLUMN instance_id TEXT')


def _decode_payload(row, payload_key='payload'):
    value = dict(row)
    raw = value.get(payload_key)
    if raw is None:
        value['payload_error'] = None
        return value
    try:
        value[payload_key] = json.loads(raw)
        value['payload_error'] = None
    except json.JSONDecodeError as exc:
        value[payload_key] = None
        value['payload_error'] = str(exc)
    return value
