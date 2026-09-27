"""Strict client for explicit, revision-bound localhost JSON commands."""
import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field

STATUSES = {'PENDING', 'RUNNING', 'PAUSED', 'WAITING_USER', 'UNKNOWN_OUTCOME', 'DONE', 'FAILED', 'CANCELLED'}


class ControllerConnectionError(RuntimeError):
    def __init__(self, message, status=None, code=None):
        super().__init__(message)
        self.status, self.code = status, code


@dataclass(frozen=True)
class RuntimeState:
    job_id: str
    task: str
    status: str
    step: str
    progress: str
    floor: object
    readback: str
    enum: str
    selection: str = 'current'
    history: tuple = ()
    controls: dict = field(default_factory=dict)
    revision: int = 0
    capability: str = ''

    @classmethod
    def from_payload(cls, payload):
        required = ('job_id', 'task', 'status', 'step', 'progress', 'readback', 'enum')
        if not isinstance(payload, dict) or any(not isinstance(payload.get(k), str) for k in required):
            raise ValueError('invalid state fields')
        if payload['status'] not in STATUSES or payload['enum'] != payload['status']:
            raise ValueError('invalid state enum')
        revision = payload.get('revision', 0)
        if type(revision) is not int or revision < 0:
            raise ValueError('invalid revision')
        history = payload.get('history', [])
        if not isinstance(history, (list, tuple)):
            raise ValueError('history array required')
        for row in history:
            if not isinstance(row, dict) or any(not isinstance(row.get(k), str) for k in ('job_id', 'status', 'task_name')) or row['status'] not in STATUSES:
                raise ValueError('malformed history entry')
        controls = payload.get('controls', {})
        if not isinstance(controls, dict) or set(controls) - {'continue', 'pause', 'stop'} or any(type(v) is not bool for v in controls.values()):
            raise ValueError('invalid controls')
        selection = payload.get('selection', 'current')
        capability = payload.get('capability', '')
        if selection not in {'current', 'history'} or not isinstance(capability, str):
            raise ValueError('invalid state metadata')
        return cls(*(payload[k] for k in required[:5]), payload.get('floor'), payload['readback'], payload['enum'],
                   selection, tuple(history), controls, revision, capability)


class SafeBIMClient:
    def __init__(self, base_url='http://127.0.0.1:19731', timeout=2.5):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self._states = {}

    def _request(self, path, method='GET', body=None, capability=None):
        headers = {}
        data = None
        if body is not None:
            data = json.dumps(body, allow_nan=False).encode()
            headers = {'Content-Type': 'application/json', 'X-Safe-BIM-Token': capability or ''}
        request = urllib.request.Request(self.base_url + path, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode())
        except urllib.error.HTTPError as exc:
            code = None
            try:
                error = json.loads(exc.read().decode())
                code = error.get('code') if isinstance(error, dict) else None
            except Exception:
                pass
            raise ControllerConnectionError(str(exc), exc.code, code) from exc
        except (OSError, urllib.error.URLError, ValueError) as exc:
            raise ControllerConnectionError(str(exc)) from exc
        if not isinstance(payload, dict) or 'error' in payload:
            raise ControllerConnectionError('invalid/error response')
        return payload

    def state(self, job_id='active'):
        encoded = urllib.parse.quote(job_id, safe='')
        try:
            state = RuntimeState.from_payload(self._request(f'/state?job_id={encoded}'))
            self._states[state.job_id] = state
            return state
        except ControllerConnectionError as exc:
            if job_id == 'active' and exc.status == 404:
                return RuntimeState('', '—', 'PENDING', '—', '—', None, 'Активная задача отсутствует', 'PENDING')
            raise

    def command(self, action, job_id=None, revision=None, capability=None):
        if action not in {'continue', 'pause', 'stop'} or not isinstance(job_id, str) or not job_id or job_id == 'active':
            raise ValueError('known action and explicitly displayed job_id required')
        state = self._states.get(job_id)
        revision = state.revision if revision is None and state else revision
        capability = state.capability if capability is None and state else capability
        if type(revision) is not int or not isinstance(capability, str) or not capability:
            raise ControllerConnectionError('refresh displayed job state before commanding')
        encoded = urllib.parse.quote(job_id, safe='')
        return self._request(f'/jobs/{encoded}/{action}', method='POST',
                             body={'job_id': job_id, 'action': action, 'revision': revision}, capability=capability)
