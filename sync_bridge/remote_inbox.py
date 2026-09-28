"""Test stand-in for a remote mailbox. Not a live GitHub backend.

DURABLE_REMOTE_INBOX_ROLE = TEST_STAND_IN_ONLY.
Deduping here does not prove GitHub idempotency. GitHub backend status
remains NOT_YET_LIVE_VERIFIED. Same idempotency key with a different
canonical payload is a conflict.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

from sync_bridge.identity import canonical_hash
from sync_bridge.mailbox import AckLost

DURABLE_REMOTE_INBOX_ROLE = 'TEST_STAND_IN_ONLY'


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class RemoteResponse:
    def __init__(self, status, json_body=None, headers=None):
        self.status = status
        self.json = json_body if json_body is not None else {}
        self.headers = headers or {}


class DurableRemoteInbox:
    """Private mailbox stand-in. Not a live GitHub backend. TEST_STAND_IN_ONLY."""

    open_inboxes: list = []

    def __init__(self, path):
        self.path = str(path)
        self._db = sqlite3.connect(self.path, isolation_level=None)
        self._db.row_factory = sqlite3.Row
        self._db.execute(
            'CREATE TABLE IF NOT EXISTS accepted ('
            'message_id TEXT PRIMARY KEY, body TEXT NOT NULL, accepted_at TEXT NOT NULL)')
        self.drop_next_ack = False
        DurableRemoteInbox.open_inboxes.append(self)
        self.calls = []
        self.head_messages = []
        self.head_etag = '"head"'

    def close(self) -> None:
        try:
            DurableRemoteInbox.open_inboxes.remove(self)
        except ValueError:
            pass
        db = self.__dict__.get('_db')
        if db is None:
            return
        self._db = None
        db.close()

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            return

    def request(self, method, url, headers, body=None):
        headers = dict(headers or {})
        self.calls.append((method, url, headers, body))
        if method == 'GET':
            if headers.get('If-None-Match') == self.head_etag:
                return RemoteResponse(304, {}, {'ETag': self.head_etag})
            return RemoteResponse(200, {'messages': list(self.head_messages)}, {'ETag': self.head_etag})
        if method == 'PUT':
            return self._accept(headers, body if isinstance(body, dict) else {})
        return RemoteResponse(405, {'error': 'method'})

    def count(self) -> int:
        return int(self._db.execute('SELECT COUNT(*) AS n FROM accepted').fetchone()['n'])

    def accepted_ids(self) -> list:
        return [row['message_id'] for row in self._db.execute(
            'SELECT message_id FROM accepted ORDER BY accepted_at, message_id')]

    def _accept(self, headers, body):
        key = headers.get('Idempotency-Key') or body.get('idempotencyKey') or body.get('messageId')
        if not isinstance(key, str) or not key.strip():
            return RemoteResponse(400, {'error': 'missing idempotency key'})
        encoded = json.dumps(body, ensure_ascii=False, sort_keys=True)
        digest = canonical_hash(body)
        existing = self._db.execute(
            'SELECT message_id, body FROM accepted WHERE message_id=?', (key,)).fetchone()
        if existing:
            stored = json.loads(existing['body'])
            if canonical_hash(stored) != digest:
                return RemoteResponse(409, {'conflict': True, 'messageId': key, 'status': 'MESSAGE_ID_CONFLICT'})
            return RemoteResponse(200, {'duplicate': True, 'messageId': key, 'status': 'duplicate'})
        self._db.execute(
            'INSERT INTO accepted(message_id, body, accepted_at) VALUES (?,?,?)',
            (key, encoded, _now()))
        if self.drop_next_ack:
            self.drop_next_ack = False
            raise AckLost('connection reset after accept')
        return RemoteResponse(200, {'duplicate': False, 'messageId': key, 'status': 'accepted'})
