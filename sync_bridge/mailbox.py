"""Remote mailbox boundary. GitHub is a mailbox, not the BIM transaction log.

The production backend uses immutable JSON objects in the GitHub Contents API.
Local SQLite remains authoritative for queues, retries, jobs and recovery.

ETag policy: a poll returns a candidate ETag. ``SafeBIMBridge`` commits it only
after the complete tick has durably accepted every inbound object and finished
its outbox pass. A crash during the tick therefore cannot hide a delivery.
"""
from __future__ import annotations

import base64
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone

from sync_bridge import PROTOCOL_VERSION
from sync_bridge.identity import canonical_hash, canonical_json
from sync_bridge.protocol import ProtocolError

ETAG_POLICY = 'durable-after-completed-tick'
REMOTE_MAILBOX_PROTOCOL = 'OFFLINE_MOCK_VERIFIED'
GITHUB_MAILBOX_PROTOCOL = 'IMMUTABLE_GITHUB_CONTENTS_API'
GITHUB_BACKEND_STATUS = 'IMPLEMENTED_NOT_LIVE_VERIFIED'


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


class RemoteError(RuntimeError):
    """A classified remote/API failure with no response secrets attached."""

    def __init__(self, code: str, status: int | None = None):
        super().__init__(code)
        self.code = code
        self.status = status


class MissingRemoteObject(RemoteError):
    def __init__(self):
        super().__init__('REMOTE_OBJECT_MISSING', 404)


class MalformedRemoteObject(ValueError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


@dataclass
class HttpResponse:
    status: int
    json: object = field(default_factory=dict)
    headers: dict = field(default_factory=dict)


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

    def commit_etag(self, etag: str | None) -> None:
        del etag


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
    raw = _header(response, 'Retry-After')
    if raw not in (None, ''):
        try:
            return max(0.0, float(raw))
        except (TypeError, ValueError):
            pass
    reset = _header(response, 'X-RateLimit-Reset')
    if reset not in (None, ''):
        try:
            return max(0.0, float(reset) - time.time())
        except (TypeError, ValueError):
            pass
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


def _forbidden_classification(response) -> str:
    if _header(response, 'X-GitHub-SSO') not in (None, ''):
        return 'NEEDS_AUTH'
    body = response.json if isinstance(getattr(response, 'json', None), dict) else {}
    text = ' '.join(str(value) for value in body.values()).lower()
    auth_markers = (
        'authentication required',
        'authorization required',
        'auth required',
        'requires authentication',
        'must authenticate',
        'bad credentials',
        'reauthorize',
        'authorize your oauth token',
        'saml',
        'single sign-on',
        'single sign on',
        'sso authorization',
    )
    if any(marker in text for marker in auth_markers):
        return 'NEEDS_AUTH'
    permission_markers = (
        'permission denied',
        'insufficient permission',
        'insufficient scope',
        'resource not accessible by integration',
        'resource not accessible by personal access token',
        'must have push access',
        'write access to repository not granted',
    )
    if any(marker in text for marker in permission_markers):
        return 'PERMISSION_DENIED'
    return 'ACCESS_UNCERTAIN'


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_message_id(value) -> str:
    if type(value) is not str or not value:
        raise ProtocolError('publish requires a durable messageId')
    if any(ch not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-' for ch in value):
        raise ProtocolError('messageId contains unsafe path characters')
    if value in ('.', '..'):
        raise ProtocolError('messageId is not a safe path component')
    return value


def _path_message_id(path: str) -> str:
    if type(path) is not str:
        raise ProtocolError('remote path required')
    filename = path.rsplit('/', 1)[-1]
    if not filename.endswith('.json'):
        raise ProtocolError('remote path is not a JSON object')
    return _safe_message_id(filename[:-5])


def canonical_remote_object(body: dict, default_kind: str) -> dict:
    """Build the stable, transport-neutral object stored by GitHub."""
    if not isinstance(body, dict):
        raise ProtocolError('publish body must be an object')
    message_id = _safe_message_id(body.get('messageId'))
    if 'protocolVersion' in body:
        version = body['protocolVersion']
        if type(version) is not int or version != PROTOCOL_VERSION:
            raise ProtocolError('unsupported protocolVersion')
    if 'payload' in body and all(key in body for key in ('protocolVersion', 'kind', 'createdAt')):
        payload = body['payload']
        kind = body['kind']
        created_at = body['createdAt']
    else:
        excluded = {'protocolVersion', 'messageId', 'idempotencyKey', 'kind', 'createdAt', 'payloadHash'}
        payload = {key: value for key, value in body.items() if key not in excluded}
        kind = body.get('kind') or default_kind
        created_at = body.get('createdAt') or _now()
    if not isinstance(payload, dict):
        raise ProtocolError('payload must be an object')
    if not isinstance(kind, str) or not kind.strip():
        raise ProtocolError('kind required')
    if not isinstance(created_at, str) or not created_at.strip():
        raise ProtocolError('createdAt required')
    remote = {
        'protocolVersion': PROTOCOL_VERSION,
        'messageId': message_id,
        'kind': kind,
        'createdAt': created_at,
        'payload': payload,
        'payloadHash': '',
    }
    for key in ('requestId', 'logicalProjectId', 'snapshotId', 'rootHash'):
        if key in body:
            remote[key] = body[key]
    try:
        remote['payloadHash'] = canonical_hash(payload)
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ProtocolError('payload must contain only JSON data') from exc
    supplied = body.get('payloadHash')
    if supplied is not None and supplied != remote['payloadHash']:
        raise ProtocolError('payloadHash does not match canonical payload')
    return remote


def validate_remote_object(value, *, path: str | None = None) -> dict:
    if not isinstance(value, dict):
        raise MalformedRemoteObject('QUARANTINED')
    required = ('protocolVersion', 'messageId', 'kind', 'createdAt', 'payload', 'payloadHash')
    if any(key not in value for key in required):
        raise MalformedRemoteObject('QUARANTINED')
    if type(value['protocolVersion']) is not int or value['protocolVersion'] != PROTOCOL_VERSION:
        raise MalformedRemoteObject('QUARANTINED')
    try:
        message_id = _safe_message_id(value['messageId'])
    except ProtocolError as exc:
        raise MalformedRemoteObject('QUARANTINED') from exc
    if not isinstance(value['kind'], str) or not value['kind'].strip():
        raise MalformedRemoteObject('QUARANTINED')
    if not isinstance(value['createdAt'], str) or not value['createdAt'].strip():
        raise MalformedRemoteObject('QUARANTINED')
    if not isinstance(value['payload'], dict) or not isinstance(value['payloadHash'], str):
        raise MalformedRemoteObject('QUARANTINED')
    try:
        actual_hash = canonical_hash(value['payload'])
    except (TypeError, ValueError, UnicodeError) as exc:
        raise MalformedRemoteObject('QUARANTINED') from exc
    if actual_hash != value['payloadHash']:
        raise MalformedRemoteObject('REMOTE_HASH_MISMATCH')
    if path is not None:
        try:
            path_message_id = _path_message_id(path)
        except ProtocolError as exc:
            raise MalformedRemoteObject('MESSAGE_ID_CONFLICT') from exc
        if message_id != path_message_id:
            raise MalformedRemoteObject('MESSAGE_ID_CONFLICT')
    return value


def inbound_bridge_message(value: dict, *, path: str | None = None) -> dict:
    remote = validate_remote_object(value, path=path)
    result = {
        'protocolVersion': remote['protocolVersion'],
        'messageId': remote['messageId'],
        'kind': remote['kind'],
        'createdAt': remote['createdAt'],
        'body': remote['payload'],
        'payloadHash': remote['payloadHash'],
    }
    for key in ('requestId', 'logicalProjectId', 'snapshotId', 'rootHash'):
        if key in remote:
            result[key] = remote[key]
    return result


class UrllibGitHubHttp:
    """Small stdlib-only HTTP adapter. It never includes response text in errors."""

    def request(self, method, url, headers, body=None):
        data = None
        outgoing = dict(headers or {})
        if body is not None:
            data = canonical_json(body).encode('utf-8')
            outgoing.setdefault('Content-Type', 'application/json')
        request = urllib.request.Request(url, data=data, headers=outgoing, method=method)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                raw = response.read()
                return HttpResponse(response.status, _decode_json(raw), dict(response.headers.items()))
        except urllib.error.HTTPError as exc:
            raw = exc.read()
            return HttpResponse(exc.code, _decode_json(raw), dict(exc.headers.items()))
        except (urllib.error.URLError, TimeoutError, OSError):
            raise ConnectionError('GitHub API unreachable') from None


def _decode_json(raw: bytes):
    if not raw:
        return {}
    try:
        return json.loads(raw.decode('utf-8'))
    except (UnicodeError, json.JSONDecodeError):
        return {}


class GitHubContentsBackend:
    """Real GitHub Contents API transport for immutable mailbox objects."""

    def __init__(self, owner: str, repo: str, *, branch: str = 'main',
                 root: str = 'safe-bim-mailbox', http=None, token_provider=None,
                 api_base: str = 'https://api.github.com'):
        if not owner or not repo or not branch:
            raise ValueError('owner, repo and branch are required')
        self.owner = owner
        self.repo = repo
        self.branch = branch
        self.root = root.strip('/')
        self.http = http or UrllibGitHubHttp()
        self.token_provider = token_provider or self._environment_token
        self.api_base = api_base.rstrip('/')

    @staticmethod
    def _environment_token():
        return os.environ.get('SAFE_BIM_GITHUB_TOKEN') or os.environ.get('GITHUB_TOKEN')

    def has_credentials(self) -> bool:
        return bool(self.token_provider())

    def list_objects(self, folder: str, etag: str | None = None) -> tuple[int, str | None, list]:
        headers = {'If-None-Match': etag} if etag else {}
        response = self._request('GET', self._contents_url(folder), headers)
        if response.status == 304:
            return 304, etag, []
        if response.status == 404:
            self._require_visible_repository()
            return 200, _header(response, 'ETag', etag), []
        self._raise_for_status(response, 'LIST_FAILED')
        if not isinstance(response.json, list):
            raise RemoteError('MALFORMED_CONTENTS_LIST', response.status)
        entries = [item for item in response.json if isinstance(item, dict)
                   and item.get('type') == 'file' and str(item.get('name', '')).endswith('.json')
                   and isinstance(item.get('path'), str)]
        entries.sort(key=lambda item: item['path'])
        return response.status, _header(response, 'ETag', etag), entries

    def read_object(self, path: str) -> dict:
        response = self._request('GET', self._contents_url(path, rooted=False), {})
        if response.status == 404:
            raise MissingRemoteObject()
        self._raise_for_status(response, 'READ_FAILED')
        if not isinstance(response.json, dict):
            raise MalformedRemoteObject('QUARANTINED')
        content = response.json.get('content')
        encoding = response.json.get('encoding')
        if not isinstance(content, str) or encoding != 'base64':
            raise MalformedRemoteObject('QUARANTINED')
        try:
            raw = base64.b64decode(content.encode('ascii'), validate=False)
            value = json.loads(
                raw.decode('utf-8'),
                parse_constant=lambda _value: (_ for _ in ()).throw(ValueError('non-finite JSON number')),
            )
        except (ValueError, UnicodeError, json.JSONDecodeError) as exc:
            raise MalformedRemoteObject('QUARANTINED') from exc
        if not isinstance(value, dict):
            raise MalformedRemoteObject('QUARANTINED')
        return value

    def create_immutable(self, folder: str, value: dict) -> dict:
        message_id = _safe_message_id(value.get('messageId'))
        parent = self._join(folder)
        path = parent + '/' + message_id + '.json'
        existing = self._read_if_present(path)
        if existing is not None:
            return self._compare_existing(existing, value, message_id)
        body = {
            'message': 'Safe BIM mailbox ' + message_id,
            'content': base64.b64encode(canonical_json(value).encode('utf-8')).decode('ascii'),
            'branch': self.branch,
        }
        response = self._request(
            'PUT', self._contents_url(path, rooted=False, include_ref=False), {}, body)
        if response.status in (409, 422):
            winner = self._read_if_present(path)
            if winner is None:
                raise RemoteError('CREATE_REJECTED', response.status)
            return self._compare_existing(winner, value, message_id)
        self._raise_for_status(response, 'CREATE_FAILED')
        if response.status not in (200, 201):
            raise RemoteError('CREATE_FAILED', response.status)
        return {'status': 'CREATED', 'messageId': message_id, 'authority': 'remote'}

    def health(self) -> dict:
        try:
            response = self._request('GET', self._repo_url(), {})
        except NeedsAuth:
            return {'status': 'NEEDS_AUTH'}
        except OfflineError:
            return {'status': 'OFFLINE'}
        if is_rate_limited(response):
            return {'status': 'RATE_LIMITED', 'retryAfter': _retry_after(response)}
        if response.status == 401:
            return {'status': 'NEEDS_AUTH'}
        if response.status == 403:
            classification = _forbidden_classification(response)
            if classification == 'NEEDS_AUTH':
                return {'status': 'NEEDS_AUTH'}
            return {'status': 'ERROR', 'code': classification}
        if response.status == 404:
            return {'status': 'ERROR', 'code': 'ACCESS_UNCERTAIN'}
        if response.status >= 500:
            return {'status': 'OFFLINE'}
        if response.status == 200:
            return {'status': 'CONNECTED', 'backend': GITHUB_BACKEND_STATUS,
                    'protocol': GITHUB_MAILBOX_PROTOCOL}
        return {'status': 'ERROR', 'code': 'GITHUB_STATUS_' + str(response.status)}

    def _compare_existing(self, existing, desired, message_id: str) -> dict:
        try:
            current = validate_remote_object(existing)
            wanted = validate_remote_object(desired)
        except MalformedRemoteObject:
            return {'status': 'MESSAGE_ID_CONFLICT', 'messageId': message_id, 'authority': 'remote'}
        identity_keys = ('protocolVersion', 'messageId', 'kind', 'payloadHash',
                         'requestId', 'logicalProjectId', 'snapshotId', 'rootHash')
        if all(current.get(key) == wanted.get(key) for key in identity_keys):
            return {'status': 'ALREADY_PUBLISHED', 'messageId': message_id, 'authority': 'remote'}
        return {'status': 'MESSAGE_ID_CONFLICT', 'messageId': message_id, 'authority': 'remote'}

    def _read_if_present(self, path: str):
        try:
            return self.read_object(path)
        except MissingRemoteObject:
            return None

    def _require_visible_repository(self) -> None:
        response = self._request('GET', self._repo_url(), {})
        if response.status == 200:
            return
        if response.status == 404:
            raise RemoteError('ACCESS_UNCERTAIN', response.status)
        self._raise_for_status(response, 'REPOSITORY_CHECK_FAILED')
        raise RemoteError('ACCESS_UNCERTAIN', response.status)

    def fail_for_missing_listed_object(self) -> None:
        """Probe repository access before classifying a listed object's 404."""
        response = self._request('GET', self._repo_url(), {})
        if response.status == 200:
            raise RemoteError('TRANSIENT_REMOTE_INCONSISTENCY', 404)
        if response.status == 404:
            raise RemoteError('ACCESS_UNCERTAIN', response.status)
        self._raise_for_status(response, 'ACCESS_UNCERTAIN')
        raise RemoteError('ACCESS_UNCERTAIN', response.status)

    def _request(self, method, url, headers, body=None):
        outgoing = {
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28',
            'User-Agent': 'safe-bim-bridge',
        }
        outgoing.update(headers or {})
        try:
            token = self.token_provider()
        except Exception:
            raise NeedsAuth('GitHub authorization required') from None
        if token:
            outgoing['Authorization'] = 'Bearer ' + token
        try:
            return self.http.request(method, url, outgoing, body)
        except AckLost:
            raise
        except (ConnectionError, TimeoutError, OSError):
            raise OfflineError('GitHub API unreachable') from None
        except Exception:
            # Never copy third-party exception text; it may contain request headers.
            raise OfflineError('GitHub API request failed') from None

    def _raise_for_status(self, response, code: str) -> None:
        if is_rate_limited(response):
            raise RateLimited(_retry_after(response))
        if response.status == 401:
            raise NeedsAuth('GitHub authorization required')
        if response.status == 403:
            classification = _forbidden_classification(response)
            if classification == 'NEEDS_AUTH':
                raise NeedsAuth('GitHub authorization required')
            raise RemoteError(classification, response.status)
        if response.status >= 500 or response.status in (408,):
            raise OfflineError('GitHub API unavailable')
        if response.status >= 400:
            raise RemoteError(code, response.status)

    def _join(self, *parts: str) -> str:
        return '/'.join(part.strip('/') for part in (self.root, *parts) if part.strip('/'))

    def _contents_url(self, path: str, *, rooted: bool = True,
                      include_ref: bool = True) -> str:
        full = self._join(path) if rooted else path.strip('/')
        encoded = '/'.join(urllib.parse.quote(part, safe='') for part in full.split('/'))
        result = (f'{self.api_base}/repos/{urllib.parse.quote(self.owner, safe="")}/'
                  f'{urllib.parse.quote(self.repo, safe="")}/contents/{encoded}')
        return result + ('?' + urllib.parse.urlencode({'ref': self.branch}) if include_ref else '')

    def _repo_url(self) -> str:
        return (f'{self.api_base}/repos/{urllib.parse.quote(self.owner, safe="")}/'
                f'{urllib.parse.quote(self.repo, safe="")}')


class GitHubMailbox(RemoteMailbox):
    """Mailbox facade supporting a real Contents backend and legacy test HTTP."""

    def __init__(self, http=None, head_url: str = 'https://example.invalid/mailbox/head', *, backend=None):
        if backend is None and isinstance(http, GitHubContentsBackend):
            backend, http = http, None
        self.backend = backend
        self.http = http
        self.head_url = head_url
        self.etag: str | None = None
        self._published_hashes: dict[str, str] = {}

    @classmethod
    def for_repository(cls, owner: str, repo: str, **kwargs):
        return cls(backend=GitHubContentsBackend(owner, repo, **kwargs))

    def commit_etag(self, etag: str | None) -> None:
        if etag:
            self.etag = etag

    def poll_head(self) -> PollHead:
        if self.backend is not None:
            status, candidate, entries = self.backend.list_objects('inbox', self.etag)
            if status == 304:
                return PollHead(False, self.etag, not_modified=True)
            messages = []
            for entry in entries:
                path = entry['path']
                try:
                    messages.append(inbound_bridge_message(self.backend.read_object(path), path=path))
                except MalformedRemoteObject as exc:
                    messages.append({'_remoteError': exc.code, '_remotePath': path})
                except MissingRemoteObject:
                    self.backend.fail_for_missing_listed_object()
            return PollHead(True, candidate, messages)

        headers = {}
        if self.etag:
            headers['If-None-Match'] = self.etag
        response = self._request('GET', self.head_url, headers)
        if response.status == 304:
            return PollHead(False, self.etag, not_modified=True)
        self._raise_legacy(response, 'mailbox')
        messages = response.json.get('messages', []) if isinstance(response.json, dict) else None
        if not isinstance(messages, list):
            raise ValueError('malformed mailbox head')
        return PollHead(True, _header(response, 'ETag', self.etag), messages)

    def fetch_message(self, ref: str) -> dict:
        if self.backend is not None:
            return inbound_bridge_message(self.backend.read_object(ref), path=ref)
        response = self._request('GET', ref, {})
        self._raise_legacy(response, 'fetch')
        if not isinstance(response.json, dict):
            raise ValueError('malformed remote payload')
        return response.json

    def publish_message(self, message: dict) -> dict:
        return self._publish(message, 'inbox')

    def publish_result(self, result: dict) -> dict:
        return self._publish(result, 'results')

    def health(self) -> dict:
        if self.backend is not None:
            return self.backend.health()
        try:
            response = self.http.request(
                'GET', self.head_url, {'If-None-Match': self.etag} if self.etag else {})
        except (ConnectionError, TimeoutError):
            return {'status': 'OFFLINE'}
        if is_rate_limited(response):
            return {'status': 'RATE_LIMITED', 'code': response.status}
        if response.status == 401:
            return {'status': 'NEEDS_AUTH'}
        if response.status == 403:
            classification = _forbidden_classification(response)
            if classification == 'NEEDS_AUTH':
                return {'status': 'NEEDS_AUTH'}
            return {'status': 'ERROR', 'code': classification,
                    'backend': GITHUB_BACKEND_STATUS}
        if response.status in (200, 304):
            return {'status': 'CONNECTED', 'backend': GITHUB_BACKEND_STATUS,
                    'protocol': REMOTE_MAILBOX_PROTOCOL}
        return {'status': 'ERROR', 'code': response.status, 'backend': GITHUB_BACKEND_STATUS}

    def _request(self, method, url, headers, body=None):
        try:
            return self.http.request(method, url, headers, body)
        except AckLost:
            raise
        except (ConnectionError, TimeoutError) as exc:
            raise OfflineError('mailbox unreachable') from exc

    def _publish(self, body: dict, folder: str) -> dict:
        if self.backend is not None:
            remote = canonical_remote_object(body, 'result' if folder == 'results' else 'message')
            return self.backend.create_immutable(folder, remote)
        return self._publish_legacy(body)

    def _publish_legacy(self, body: dict) -> dict:
        message_id = body.get('messageId') or body.get('idempotencyKey') or body.get('job_id')
        if not isinstance(message_id, str) or not message_id.strip():
            raise ProtocolError('publish requires a durable messageId')
        payload = dict(body)
        payload['idempotencyKey'] = message_id
        digest = canonical_hash(payload)
        cached = self._published_hashes.get(message_id)
        if cached == digest:
            return {'status': 'ALREADY_PUBLISHED', 'messageId': message_id, 'authority': 'client-cache'}
        headers = {'Idempotency-Key': message_id, 'X-Payload-Sha256': digest}
        try:
            response = self.http.request('PUT', self.head_url, headers, payload)
        except AckLost:
            raise
        except (ConnectionError, TimeoutError) as exc:
            raise OfflineError('publish failed') from exc
        if isinstance(response.json, dict) and response.json.get('conflict'):
            return {'status': 'MESSAGE_ID_CONFLICT', 'messageId': message_id, 'authority': 'remote'}
        if response.status == 409:
            return {'status': 'MESSAGE_ID_CONFLICT', 'messageId': message_id, 'authority': 'remote'}
        self._raise_legacy(response, 'publish')
        self._published_hashes[message_id] = digest
        duplicate = isinstance(response.json, dict) and bool(response.json.get('duplicate'))
        return {
            'status': 'ALREADY_PUBLISHED' if duplicate else 'PUBLISHED',
            'messageId': message_id,
            'authority': 'remote',
        }

    @staticmethod
    def _raise_legacy(response, operation: str) -> None:
        if is_rate_limited(response):
            raise RateLimited(_retry_after(response))
        if response.status == 401:
            raise NeedsAuth('GitHub authorization required')
        if response.status == 403:
            classification = _forbidden_classification(response)
            if classification == 'NEEDS_AUTH':
                raise NeedsAuth('GitHub authorization required')
            raise RemoteError(classification, response.status)
        if response.status >= 500:
            raise OfflineError(operation + ' unavailable')
        if response.status >= 400 and response.status != 409:
            raise OfflineError(operation + ' failed')
