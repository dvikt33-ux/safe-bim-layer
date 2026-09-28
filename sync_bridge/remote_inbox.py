"""Server-side mailbox. Dedupes by idempotency key across client process restarts.

``GitHubMailbox._published`` is not this store. A new client can resend the
same message_id and must still see one accepted result.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

from sync_bridge.mailbox import AckLost


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class RemoteResponse:
    def __init__(self, status, json_body=None, headers=None):
        self.status = status
        self.json = json_body if json_body is not None else {}
        self.headers = headers or {}


class DurableRemoteInbox:
    """Private GitHub-mailbox stand-in. Persistence is the dedup authority."""

    def __init__(self, path):
        self.path = str(path)
        self._db = sqlite3.connect(self.path, isolation_level=None)
        self._db.row_factory = sqlite3.Row
        self._db.execute(
            'CREATE TABLE IF NOT EXISTS accepted ('
            'message_id TEXT PRIMARY KEY, body TEXT NOT NULL, accepted_at TEXT NOT NULL)')
        self.drop_next_ack = False
        self.calls = []
        self.head_messages = []
        self.head_etag = '"head"'

    def close(self) -> None:
        self._db.close()

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
        existing = self._db.execute(
            'SELECT message_id FROM accepted WHERE message_id=?', (key,)).fetchone()
        if existing:
            return RemoteResponse(200, {'duplicate': True, 'messageId': key, 'status': 'duplicate'})
        self._db.execute(
            'INSERT INTO accepted(message_id, body, accepted_at) VALUES (?,?,?)',
            (key, json.dumps(body, ensure_ascii=False, sort_keys=True), _now()))
        if self.drop_next_ack:
            self.drop_next_ack = False
            raise AckLost('connection reset after accept')
        return RemoteResponse(200, {'duplicate': False, 'messageId': key, 'status': 'accepted'})
