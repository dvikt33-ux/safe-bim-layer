"""Remote mailbox boundary. GitHub is a mailbox, not the BIM transaction log.

Client ``_published`` is an optimisation for the current process only. The
remote protocol dedupes on ``Idempotency-Key`` (the durable message_id). A
new GitHubMailbox after a crash does not remember earlier publishes.

ETag policy (``ETAG_POLICY``): SafeBIMBridge persists the ETag only after a
tick completes. The first poll after restart sends If-None-Match when a
completed tick stored one. A crash before the tick finishes does not advance
the stored ETag, so that poll is unconditional.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from sync_bridge.protocol import ProtocolError

ETAG_POLICY = 'durable-after-completed-tick'


class OfflineError(ConnectionError):
    pass


class AckLost(Exception):
    """The request may have been accepted. Confirmation was not received."""


class RateLimited(RuntimeError):
    def __init__(self, retry_after: float):
        super().__init__('rate limited')
        self.retry_after = retry_after


class NeedsAuth(RuntimeError):
    pass


@dataclass
class PollHead:
    changed: bool
    etag: str | None
    messages: list = field(default_factory=list)
    needs_auth: bool = False
    not_modified: bool = False


class RemoteMailbox:
    def poll_head(self) -> PollHead:
        raise NotImplementedError

    def fetch_message(self, ref: str) -> dict:
        raise NotImplementedError

    def publish_message(self, message: dict) -> dict:
        raise NotImplementedError

    def publish_result(self, result: dict) -> dict:
        raise NotImplementedError

    def health(self) -> dict:
        raise NotImplementedError


def _header(response, name: str, default=None):
    headers = getattr(response, 'headers', {}) or {}
    if name in headers:
        return headers[name]
    lowered = name.lower()
    for key, value in headers.items():
        if str(key).lower() == lowered:
            return value
    return default


def _retry_after(response, default=30.0) -> float:
    try:
        return float(_header(response, 'Retry-After', default))
    except (TypeError, ValueError):
        return float(default)


def is_rate_limited(response) -> bool:
    if response.status == 429:
        return True
    if response.status != 403:
        return False
    if _header(response, 'Retry-After') not in (None, ''):
        return True
    if str(_header(response, 'X-RateLimit-Remaining', '')) == '0':
        return True
    body = response.json if isinstance(getattr(response, 'json', None), dict) else {}
    text = ' '.join(str(value) for value in body.values()).lower()
    return 'rate limit' in text


class GitHubMailbox(RemoteMailbox):
    """ETag conditional polling. No webhook, tunnel, or runner."""

    def __init__(self, http, head_url: str = 'https://example.invalid/mailbox/head'):
        self.http = http
        self.head_url = head_url
        self.etag: str | None = None
        self._published: set[str] = set()

    def poll_head(self) -> PollHead:
        headers = {}
        if self.etag:
            headers['If-None-Match'] = self.etag
        response = self._request('GET', self.head_url, headers)
        if response.status == 304:
            return PollHead(False, self.etag, not_modified=True)
        if is_rate_limited(response):
            raise RateLimited(_retry_after(response))
        if response.status in (401, 403):
            raise NeedsAuth('GitHub authorization required')
        if response.status >= 500:
            raise OfflineError(f'mailbox status {response.status}')
        self.etag = _header(response, 'ETag', self.etag)
        messages = response.json.get('messages', []) if isinstance(response.json, dict) else None
        if not isinstance(messages, list):
            raise ValueError('malformed mailbox head')
        return PollHead(True, self.etag, messages)

    def fetch_message(self, ref: str) -> dict:
        response = self._request('GET', ref, {})
        if is_rate_limited(response):
            raise RateLimited(_retry_after(response))
        if response.status in (401, 403):
            raise NeedsAuth('GitHub authorization required')
        if response.status >= 500:
            raise OfflineError(f'fetch status {response.status}')
        if not isinstance(response.json, dict):
            raise ValueError('malformed remote payload')
        return response.json

    def publish_message(self, message: dict) -> dict:
        return self._publish(message)

    def publish_result(self, result: dict) -> dict:
        return self._publish(result)

    def health(self) -> dict:
        try:
            response = self.http.request(
                'GET', self.head_url, {'If-None-Match': self.etag} if self.etag else {})
        except (ConnectionError, TimeoutError):
            return {'status': 'OFFLINE'}
        if is_rate_limited(response):
            return {'status': 'DEGRADED', 'code': response.status}
        if response.status in (401, 403):
            return {'status': 'NEEDS_AUTH'}
        if response.status in (200, 304):
            return {'status': 'CONNECTED'}
        return {'status': 'DEGRADED', 'code': response.status}

    def _request(self, method, url, headers, body=None):
        try:
            return self.http.request(method, url, headers, body)
        except AckLost:
            raise
        except (ConnectionError, TimeoutError) as exc:
            raise OfflineError('mailbox unreachable') from exc

    def _publish(self, body: dict) -> dict:
        message_id = body.get('messageId') or body.get('idempotencyKey') or body.get('job_id')
        if not isinstance(message_id, str) or not message_id.strip():
            raise ProtocolError('publish requires a durable messageId')
        if message_id in self._published:
            return {'status': 'ALREADY_PUBLISHED', 'messageId': message_id, 'authority': 'client-cache'}
        payload = dict(body)
        payload['idempotencyKey'] = message_id
        headers = {'Idempotency-Key': message_id}
        try:
            response = self.http.request('PUT', self.head_url, headers, payload)
        except AckLost:
            raise
        except (ConnectionError, TimeoutError) as exc:
            raise OfflineError('publish failed') from exc
        if is_rate_limited(response):
            raise RateLimited(_retry_after(response))
        if response.status in (401, 403):
            raise NeedsAuth('GitHub authorization required')
        if response.status >= 500:
            raise OfflineError('publish failed')
        if response.status >= 400:
            raise OfflineError(f'publish status {response.status}')
        self._published.add(message_id)
        duplicate = isinstance(response.json, dict) and bool(response.json.get('duplicate'))
        return {
            'status': 'ALREADY_PUBLISHED' if duplicate else 'PUBLISHED',
            'messageId': message_id,
            'authority': 'remote',
        }
