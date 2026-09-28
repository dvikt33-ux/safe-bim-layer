"""Remote mailbox boundary. GitHub is a mailbox, not the BIM transaction log."""
from __future__ import annotations

from dataclasses import dataclass, field


class OfflineError(ConnectionError):
    pass


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
        try:
            response = self.http.request('GET', self.head_url, headers)
        except ConnectionError as exc:
            raise OfflineError('mailbox unreachable') from exc
        if response.status == 304:
            return PollHead(False, self.etag, not_modified=True)
        if response.status == 429:
            raise RateLimited(float(response.headers.get('Retry-After', 30)))
        if response.status in (401, 403):
            raise NeedsAuth('GitHub authorization required')
        if response.status >= 500:
            raise OfflineError(f'mailbox status {response.status}')
        self.etag = response.headers.get('ETag', self.etag)
        messages = response.json.get('messages', [])
        if not isinstance(messages, list):
            raise ValueError('malformed mailbox head')
        return PollHead(True, self.etag, messages)

    def fetch_message(self, ref: str) -> dict:
        try:
            response = self.http.request('GET', ref, {})
        except ConnectionError as exc:
            raise OfflineError('fetch failed') from exc
        if response.status in (401, 403):
            raise NeedsAuth('GitHub authorization required')
        if not isinstance(response.json, dict):
            raise ValueError('malformed remote payload')
        return response.json

    def publish_message(self, message: dict) -> dict:
        return self._publish(message)

    def publish_result(self, result: dict) -> dict:
        return self._publish(result)

    def health(self) -> dict:
        try:
            response = self.http.request('GET', self.head_url, {'If-None-Match': self.etag} if self.etag else {})
        except ConnectionError:
            return {'status': 'OFFLINE'}
        if response.status in (401, 403):
            return {'status': 'NEEDS_AUTH'}
        if response.status in (200, 304):
            return {'status': 'CONNECTED'}
        return {'status': 'DEGRADED', 'code': response.status}

    def _publish(self, body: dict) -> dict:
        message_id = body.get('messageId') or body.get('job_id')
        if message_id in self._published:
            return {'status': 'ALREADY_PUBLISHED', 'messageId': message_id}
        try:
            response = self.http.request('PUT', self.head_url, {}, body)
        except ConnectionError as exc:
            raise OfflineError('publish failed') from exc
        if response.status in (401, 403):
            raise NeedsAuth('GitHub authorization required')
        if response.status == 429:
            raise RateLimited(float(response.headers.get('Retry-After', 30)))
        if response.status >= 500:
            raise OfflineError('publish failed')
        self._published.add(message_id)
        return {'status': 'PUBLISHED', 'messageId': message_id}
