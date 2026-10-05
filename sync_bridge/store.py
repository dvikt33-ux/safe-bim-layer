"""Crash-safe local state. Not the authority for a BIM transaction."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from sync_bridge.identity import canonical_hash


SCHEMA = """
CREATE TABLE IF NOT EXISTS messages (
    message_id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    created_at TEXT NOT NULL,
    payload TEXT NOT NULL,
    state TEXT NOT NULL,
    retry_count INTEGER NOT NULL DEFAULT 0,
    direction TEXT NOT NULL,
    payload_hash TEXT
);
CREATE TABLE IF NOT EXISTS context_requests (
    request_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    requested_scope TEXT NOT NULL,
    state TEXT NOT NULL,
    snapshot_id TEXT,
    response_json TEXT,
    created_at TEXT NOT NULL,
    instance_id TEXT,
    generation INTEGER
);
CREATE TABLE IF NOT EXISTS archicad_clients (
    instance_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    logical_project_id TEXT,
    last_seen TEXT NOT NULL,
    connection_state TEXT NOT NULL,
    epoch INTEGER
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
    open_stores: list = []

    def __init__(self, path: str | Path):
        self.path = str(path)
        self._db = sqlite3.connect(self.path, isolation_level=None)
        self._db.row_factory = sqlite3.Row
        self._db.execute('PRAGMA journal_mode=WAL')
        self._db.execute('PRAGMA foreign_keys=ON')
        self._db.executescript(SCHEMA)
        self._migrate()
        self.fault_before_result_commit = None
        self.fault_before_context_commit = None
        self.fault_before_invalidation_commit = None
        BridgeStore.open_stores.append(self)

    def close(self) -> None:
        try:
            BridgeStore.open_stores.remove(self)
        except ValueError:
            pass
        db = self.__dict__.get('_db')
        if db is None:
            return
        self._db = None
        db.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            return

    def reopen(self) -> 'BridgeStore':
        self.close()
        return BridgeStore(self.path)

    def put_message(self, message_id: str, kind: str, created_at: str, payload: dict,
                    state: str, direction: str) -> bool:
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        digest = canonical_hash(payload)
        cur = self._db.execute(
            'INSERT OR IGNORE INTO messages(message_id,kind,created_at,payload,state,retry_count,direction,payload_hash) '
            'VALUES (?,?,?,?,?,0,?,?)',
            (message_id, kind, created_at, encoded, state, direction, digest))
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
                            response: dict | None = None, instance_id: str | None = None,
                            generation: int | None = None) -> bool:
        cur = self._db.execute(
            'INSERT OR IGNORE INTO context_requests(request_id,project_id,requested_scope,state,snapshot_id,response_json,created_at,instance_id,generation) '
            'VALUES (?,?,?,?,?,?,?,?,?)',
            (request_id, project_id, scope, state, snapshot_id,
             json.dumps(response, ensure_ascii=False) if response is not None else None, created_at,
             instance_id, generation))
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

    def jobs_by_state(self, state: str, limit: int | None = None):
        sql = 'SELECT * FROM remote_jobs WHERE state=? ORDER BY created_at'
        params = [state]
        if limit is not None:
            sql += ' LIMIT ?'
            params.append(int(limit))
        rows = self._db.execute(sql, tuple(params)).fetchall()
        return [_decode_payload(row) for row in rows]

    def claim_job(self, job_id: str) -> bool:
        cur = self._db.execute(
            "UPDATE remote_jobs SET state='RUNNING' WHERE job_id=? AND state='QUEUED'",
            (job_id,))
        return cur.rowcount == 1

    def set_job_state(self, job_id: str, state: str) -> None:
        self._db.execute('UPDATE remote_jobs SET state=? WHERE job_id=?', (state, job_id))

    def put_result(self, job_id: str, result: dict, upload_state: str) -> None:
        existing = self.result(job_id)
        if existing is not None and canonical_hash(existing['result']) != canonical_hash(result):
            raise ResultConflict('job result is immutable')
        encoded = json.dumps(result, ensure_ascii=False, sort_keys=True)
        self._db.execute(
            'INSERT INTO results(job_id,result,upload_state) VALUES (?,?,?) '
            'ON CONFLICT(job_id) DO UPDATE SET result=excluded.result,upload_state=excluded.upload_state',
            (job_id, encoded, upload_state))

    def enqueue_result(self, job_id: str, result: dict, message_id: str, created_at: str, payload: dict) -> None:
        """Commit the result row and its outbox message together, or neither."""
        self._db.execute('BEGIN IMMEDIATE')
        try:
            self.put_result(job_id, result, 'PENDING')
            self.put_message(message_id, 'result', created_at, payload, 'PENDING', 'outbox')
            if self.fault_before_result_commit:
                self.fault_before_result_commit()
            self._db.execute('COMMIT')
        except BaseException:
            self._db.execute('ROLLBACK')
            raise

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
                      last_seen: str, state: str, epoch: int | None = None) -> None:
        self._db.execute(
            'INSERT INTO archicad_clients(instance_id,session_id,logical_project_id,last_seen,connection_state,epoch) '
            'VALUES (?,?,?,?,?,?) ON CONFLICT(instance_id) DO UPDATE SET '
            'session_id=excluded.session_id, logical_project_id=excluded.logical_project_id, '
            'last_seen=excluded.last_seen, connection_state=excluded.connection_state, epoch=excluded.epoch',
            (instance_id, session_id, project_id, last_seen, state, epoch))

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

    def acquire_lease(self, token: str, now: str, ttl_seconds: float, public_id: str) -> bool:
        """Record diagnostic lease metadata after mutex ownership is established.

        The per-user Windows named mutex is the ownership gate.
        SQLite lease metadata is diagnostic only and must not delay takeover
        after the previous mutex owner has terminated.
        """
        expires = (datetime.fromisoformat(now) + timedelta(seconds=ttl_seconds)).isoformat()
        self._db.execute('BEGIN IMMEDIATE')
        try:
            current = self._meta_in_tx('lease_token') or ''
            new_owner = current != token
            self._set_meta_in_tx('lease_token', token)
            self._set_meta_in_tx('lease_expires', expires)
            self._set_meta_in_tx('lease_heartbeat', now)
            self._set_meta_in_tx('lease_public_id', public_id)
            self._set_meta_in_tx('lease_role', 'DIAGNOSTIC_ONLY')
            if new_owner:
                epoch = int(self._meta_in_tx('bridge_epoch') or '0') + 1
                self._set_meta_in_tx('bridge_epoch', str(epoch))
                self._db.execute(
                    "UPDATE archicad_clients SET connection_state='DISCONNECTED' "
                    "WHERE connection_state='CONNECTED' AND IFNULL(epoch, -1) != ?",
                    (epoch,))
            self._db.execute('COMMIT')
            return True
        except BaseException:
            self._db.execute('ROLLBACK')
            raise

    def renew_lease(self, token: str, now: str, ttl_seconds: float) -> bool:
        """Refresh diagnostic expiry. Does not transfer ownership."""
        expires = (datetime.fromisoformat(now) + timedelta(seconds=ttl_seconds)).isoformat()
        self._db.execute('BEGIN IMMEDIATE')
        try:
            if (self._meta_in_tx('lease_token') or '') != token:
                self._db.execute('ROLLBACK')
                return False
            self._set_meta_in_tx('lease_expires', expires)
            self._set_meta_in_tx('lease_heartbeat', now)
            self._db.execute('COMMIT')
            return True
        except BaseException:
            self._db.execute('ROLLBACK')
            raise

    def assign_capture(self, request_id: str, sequence: int, snapshot_id: str,
                       revision: int, captures: int) -> None:
        """Persist the capture operation and the stream revision it started against."""
        self._db.execute('BEGIN IMMEDIATE')
        try:
            self._set_meta_in_tx('context_sequence', str(sequence))
            self._set_meta_in_tx('context_captures', str(captures))
            self._set_meta_in_tx(f'context_op_capture:{request_id}', f'{sequence}:{snapshot_id}')
            self._set_meta_in_tx(f'context_op_capture_revision:{request_id}', str(revision))
            self._db.execute('COMMIT')
        except BaseException:
            self._db.execute('ROLLBACK')
            raise

    def commit_context_ready(self, request_id: str, snapshot_id: str, response: dict,
                             stream_key: str, sequence: int, identity_hash: str,
                             expected_capture_revision: int | None = None) -> str:
        """VALID snapshot, watermark, and generation identity commit together, or neither.

        A capture may become current only if the stored capture-start revision
        still matches the stream. A missing fence is not filled from the live
        stream revision, and a mismatch writes nothing.
        """
        del expected_capture_revision  # a caller cannot fill in a missing start fence
        encoded = json.dumps(response, ensure_ascii=False)
        self._db.execute('BEGIN IMMEDIATE')
        try:
            current = self._db.execute(
                'SELECT request_id, state, response_json FROM context_requests WHERE request_id=?',
                (request_id,)).fetchone()
            if current is None:
                raise KeyError(request_id)
            generation_status = self._context_generation_guard_in_tx(
                current, stream_key, sequence, identity_hash)
            if generation_status is not None:
                self._db.execute('ROLLBACK')
                return generation_status
            stored_expected = self._meta_in_tx(f'context_op_capture_revision:{request_id}')
            if stored_expected is None:
                self._db.execute('ROLLBACK')
                return 'CAPTURE_REVISION_MISSING'
            expected = int(stored_expected)
            current_revision = int(self._meta_in_tx('context_revision:' + stream_key) or 0)
            if self.fault_before_context_commit:
                self.fault_before_context_commit()
            if current_revision != expected:
                self._db.execute('ROLLBACK')
                return 'CAPTURE_REVISION_CONFLICT'
            self._db.execute(
                'UPDATE context_requests SET state=?,snapshot_id=?,response_json=? WHERE request_id=?',
                ('VALID', snapshot_id, encoded, request_id))
            self._set_meta_in_tx('context_sequence:' + stream_key, str(sequence))
            self._set_meta_in_tx(f'context_identity:{stream_key}:{sequence}', identity_hash)
            self._set_meta_in_tx(f'context_capture_revision:{request_id}', str(expected))
            self._set_meta_in_tx('context_validity:' + stream_key, 'VALID')
            self._set_meta_in_tx('context_valid_revision:' + stream_key, str(expected))
            self._db.execute('COMMIT')
            return 'CONTEXT_READY'
        except BaseException:
            self._db.execute('ROLLBACK')
            raise

    def commit_context_ready_with_outbox(
            self, request_id: str, snapshot_id: str, response: dict,
            stream_key: str, sequence: int, identity_hash: str,
            message_id: str, outbox_payload: dict, created_at: str) -> str:
        """Atomically commit context evidence and its immutable publish intent."""
        encoded = json.dumps(response, ensure_ascii=False)
        outbox_encoded = json.dumps(outbox_payload, ensure_ascii=False, sort_keys=True)
        outbox_hash = canonical_hash(outbox_payload)
        self._db.execute('BEGIN IMMEDIATE')
        try:
            current = self._db.execute(
                'SELECT request_id, state, response_json FROM context_requests WHERE request_id=?',
                (request_id,)).fetchone()
            if current is None:
                raise KeyError(request_id)
            generation_status = self._context_generation_guard_in_tx(
                current, stream_key, sequence, identity_hash)
            if generation_status is not None:
                self._db.execute('ROLLBACK')
                return generation_status
            stored_expected = self._meta_in_tx(f'context_op_capture_revision:{request_id}')
            if stored_expected is None:
                self._db.execute('ROLLBACK')
                return 'CAPTURE_REVISION_MISSING'
            expected = int(stored_expected)
            current_revision = int(self._meta_in_tx('context_revision:' + stream_key) or 0)
            if self.fault_before_context_commit:
                self.fault_before_context_commit()
            if current_revision != expected:
                self._db.execute('ROLLBACK')
                return 'CAPTURE_REVISION_CONFLICT'
            existing_outbox = self._db.execute(
                'SELECT payload_hash,payload FROM messages WHERE message_id=?', (message_id,)).fetchone()
            if existing_outbox is not None:
                stored_hash = existing_outbox['payload_hash']
                if not stored_hash:
                    stored_hash = canonical_hash(json.loads(existing_outbox['payload']))
                if stored_hash != outbox_hash:
                    self._db.execute('ROLLBACK')
                    return 'MESSAGE_ID_CONFLICT'
            self._db.execute(
                'UPDATE context_requests SET state=?,snapshot_id=?,response_json=? WHERE request_id=?',
                ('VALID', snapshot_id, encoded, request_id))
            self._set_meta_in_tx('context_sequence:' + stream_key, str(sequence))
            self._set_meta_in_tx(f'context_identity:{stream_key}:{sequence}', identity_hash)
            self._set_meta_in_tx(f'context_capture_revision:{request_id}', str(expected))
            self._set_meta_in_tx('context_validity:' + stream_key, 'VALID')
            self._set_meta_in_tx('context_valid_revision:' + stream_key, str(expected))
            if existing_outbox is None:
                self._db.execute(
                    'INSERT INTO messages(message_id,kind,created_at,payload,state,retry_count,direction,payload_hash) '
                    'VALUES (?,?,?,?,?,0,?,?)',
                    (message_id, 'CONTEXT_READY', created_at, outbox_encoded,
                     'PENDING', 'outbox', outbox_hash))
            self._db.execute('COMMIT')
            return 'CONTEXT_READY'
        except BaseException:
            self._db.execute('ROLLBACK')
            raise

    def invalidate_stream(self, stream_key: str) -> int:
        """Bump one stream revision. Completed request rows stay historical evidence."""
        if stream_key.startswith('instance:'):
            if not stream_key.split(':', 1)[1]:
                raise ValueError(stream_key)
        elif stream_key.startswith('project:'):
            if not stream_key.split(':', 1)[1]:
                raise ValueError(stream_key)
        else:
            raise ValueError(stream_key)
        self._db.execute('BEGIN IMMEDIATE')
        try:
            revision = int(self._meta_in_tx('context_revision:' + stream_key) or 0) + 1
            self._set_meta_in_tx('context_revision:' + stream_key, str(revision))
            self._set_meta_in_tx('context_validity:' + stream_key, 'STALE')
            if self.fault_before_invalidation_commit:
                self.fault_before_invalidation_commit()
            self._db.execute('COMMIT')
            return revision
        except BaseException:
            self._db.execute('ROLLBACK')
            raise

    def release_lease(self, token: str) -> None:
        self._db.execute('BEGIN IMMEDIATE')
        try:
            if (self._meta_in_tx('lease_token') or '') == token:
                self._set_meta_in_tx('lease_token', '')
                self._set_meta_in_tx('lease_expires', '')
            self._db.execute('COMMIT')
        except BaseException:
            self._db.execute('ROLLBACK')
            raise

    def _meta_in_tx(self, key: str):
        row = self._db.execute('SELECT value FROM meta WHERE key=?', (key,)).fetchone()
        return row['value'] if row else None

    def _context_generation_guard_in_tx(
            self, request, stream_key: str, sequence: int, identity_hash: str) -> str | None:
        """Reject rollback or equal-generation takeover before context writes."""
        current_sequence = int(self._meta_in_tx('context_sequence:' + stream_key) or 0)
        if current_sequence > sequence:
            return 'IGNORED_STALE'
        if current_sequence < sequence:
            return None
        recorded = self._meta_in_tx(f'context_identity:{stream_key}:{sequence}')
        if (recorded == identity_hash and request['state'] == 'VALID'
                and request['response_json'] is not None):
            return 'IDEMPOTENT'
        return 'CONTEXT_SEQUENCE_CONFLICT'

    def _set_meta_in_tx(self, key: str, value: str) -> None:
        self._db.execute(
            'INSERT INTO meta(key,value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',
            (key, value))

    def _migrate(self) -> None:
        columns = {row['name'] for row in self._db.execute('PRAGMA table_info(context_requests)')}
        if 'instance_id' not in columns:
            self._db.execute('ALTER TABLE context_requests ADD COLUMN instance_id TEXT')
        if 'generation' not in columns:
            self._db.execute('ALTER TABLE context_requests ADD COLUMN generation INTEGER')
        message_columns = {row['name'] for row in self._db.execute('PRAGMA table_info(messages)')}
        if 'payload_hash' not in message_columns:
            self._db.execute('ALTER TABLE messages ADD COLUMN payload_hash TEXT')
        client_columns = {row['name'] for row in self._db.execute('PRAGMA table_info(archicad_clients)')}
        if 'epoch' not in client_columns:
            self._db.execute('ALTER TABLE archicad_clients ADD COLUMN epoch INTEGER')


class ResultConflict(RuntimeError):
    """A job already has a different final result."""


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
