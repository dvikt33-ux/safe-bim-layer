"""Mock project-context protocol and lease. No new Archicad reads.

A stream generation is immutable. ``capturedAt`` is part of that identity:
an exact replay must carry the same timestamp, and a different timestamp is
a conflict rather than a silent rewrite.
"""
from __future__ import annotations

from dataclasses import dataclass

from sync_bridge import PROTOCOL_VERSION
from sync_bridge.identity import canonical_hash

LEASE_STATES = ('NONE', 'CAPTURING', 'READY', 'VALID', 'STALE', 'CANCELLED')
UI_CAPTURING = 'ИИ: считываю проект…'
UI_STALE = 'Контекст устарел'
UI_REFRESH = 'Обновить контекст'


@dataclass(frozen=True)
class ContextReady:
    protocol_version: int
    request_id: str
    snapshot_id: str
    logical_project_id: str
    root_hash: str
    captured_at: str
    payload: dict
    sequence: int


class ContextService:
    def __init__(self, store, clock):
        self.store = store
        self.clock = clock
        self.lease = 'NONE'
        self.sequence = int(self.store.meta('context_sequence') or 0)
        self.current: ContextReady | None = None
        self.by_instance: dict[str, ContextReady] = {}
        self.active_stream: str | None = None
        self.ui_banner = ''
        self.fault_after_capture_assigned = None

    def request(self, message: dict) -> dict:
        request_id = message['requestId']
        project_id = message['logicalProjectId']
        scope = message['requestedScope']
        instance_id = message.get('instanceId')
        existing = self.store.context_request(request_id)
        if existing:
            if not _same_identity(existing, project_id, scope, instance_id):
                return {
                    'kind': 'REQUEST_ID_CONFLICT',
                    'requestId': request_id,
                    'reason': 'requestId payload conflict',
                }
            if existing['state'] == 'CANCELLED':
                self.lease = 'CANCELLED'
                return {'kind': 'CONTEXT_ERROR', 'requestId': request_id, 'reason': 'cancelled'}
            if existing['state'] == 'STALE' or self._derived_stale(existing):
                self._present(instance_id, project_id, 'STALE', UI_STALE)
                return _stale_reply(existing)
            if existing.get('response'):
                self.lease = existing['state'] if existing['state'] in LEASE_STATES else 'VALID'
                self._remember(instance_id, None)
                return existing['response']
            if existing['state'] == 'CAPTURING':
                return self._resume_capturing(existing)
            self.lease = existing['state'] if existing['state'] in LEASE_STATES else 'NONE'
            return {
                'kind': 'CONTEXT_REQUEST',
                'requestId': request_id,
                'state': existing['state'],
                'logicalProjectId': existing['project_id'],
                'requestedScope': existing['requested_scope'],
                'instanceId': existing.get('instance_id'),
            }
        self.lease = 'CAPTURING'
        self.ui_banner = UI_CAPTURING
        self.store.put_context_request(
            request_id, project_id, scope, 'CAPTURING', message.get('requestedAt', self.clock()),
            instance_id=instance_id)
        ready = self._capture(request_id, project_id, scope, instance_id)
        return self._publish(ready, instance_id)

    def apply_ready(self, ready: ContextReady) -> str:
        invalid = _ready_error(ready)
        if invalid:
            return invalid
        stored = self.store.context_request(ready.request_id)
        if stored is None:
            return 'CONTEXT_ERROR'
        if stored['state'] == 'CANCELLED':
            self.lease = 'CANCELLED'
            return 'CONTEXT_ERROR'
        if stored['state'] == 'STALE' or self._derived_stale(stored):
            return self._apply_stale(ready, stored)
        if _is_completed(stored):
            return self._apply_completed(ready, stored)
        if stored['project_id'] != ready.logical_project_id:
            self.store.set_context_state(ready.request_id, 'ERROR')
            return 'CONTEXT_ERROR'
        known = self._known_sequence(stored)
        if ready.sequence < known:
            return 'IGNORED_STALE'
        stream = _stream_key(stored)
        incoming = generation_hash(ready)
        recorded = self._recorded_hash(stream, ready.sequence, stored)
        same_request_generation = _response_sequence(stored) == ready.sequence
        if ready.sequence == known or same_request_generation:
            if recorded == incoming:
                return 'IDEMPOTENT'
            if recorded is not None or ready.sequence == known:
                return 'CONTEXT_SEQUENCE_CONFLICT'
        response = _ready_response(ready)
        status = self.store.commit_context_ready(
            ready.request_id, ready.snapshot_id, response, stream, ready.sequence, incoming,
            expected_capture_revision=self._expected_capture_revision(ready.request_id))
        if status != 'CONTEXT_READY':
            return status
        self._remember(stored.get('instance_id'), ready)
        self._present(stored.get('instance_id'), stored['project_id'], 'VALID', f'Контекст #{ready.sequence}', force=True)
        return 'CONTEXT_READY'

    def _apply_completed(self, ready: ContextReady, stored: dict) -> str:
        """A VALID response is immutable. A new snapshot needs a new requestId."""
        if stored['project_id'] != ready.logical_project_id:
            return 'CONTEXT_ERROR'
        incoming = generation_hash(ready)
        recorded = canonical_hash(_identity_from_response(stored['response']))
        if incoming == recorded:
            return 'IDEMPOTENT'
        stored_sequence = _response_sequence(stored)
        if stored_sequence is not None and ready.sequence == stored_sequence:
            return 'CONTEXT_SEQUENCE_CONFLICT'
        if stored_sequence is not None and ready.sequence < stored_sequence:
            return 'IGNORED_STALE'
        if ready.sequence < self._known_sequence(stored):
            return 'IGNORED_STALE'
        return 'REQUEST_GENERATION_CONFLICT'

    def _apply_stale(self, ready: ContextReady, stored: dict) -> str:
        """A stale generation stays stale. Replay must not publish it as VALID."""
        if stored['project_id'] != ready.logical_project_id:
            return 'CONTEXT_ERROR'
        response = stored.get('response')
        if isinstance(response, dict) and generation_hash(ready) == canonical_hash(_identity_from_response(response)):
            return 'IDEMPOTENT_STALE'
        stored_sequence = _response_sequence(stored)
        if stored_sequence is not None and ready.sequence == stored_sequence:
            return 'CONTEXT_SEQUENCE_CONFLICT'
        if stored_sequence is not None and ready.sequence < stored_sequence:
            return 'IGNORED_STALE'
        if ready.sequence < self._known_sequence(stored):
            return 'IGNORED_STALE'
        return 'REQUEST_GENERATION_CONFLICT'

    def mark_changed(self, instance_id=None, logical_project_id=None) -> str:
        """Invalidate one stream. A missing target keeps the legacy global banner."""
        scoped = bool(instance_id) or bool(logical_project_id)
        if not scoped:
            instance_id, logical_project_id = self._active_target()
        stream = None
        if instance_id or logical_project_id:
            stream = _stream_key({'instance_id': instance_id, 'project_id': logical_project_id or ''})
            self.store.invalidate_stream(stream)
            if instance_id:
                self.by_instance.pop(instance_id, None)
            if self.current is not None and _ready_stream(self.current) == stream:
                self.current = None
        if stream and (not scoped or stream == self.active_stream):
            self._present(instance_id, logical_project_id, 'STALE', UI_STALE, force=True)
        elif not scoped:
            self.lease = 'STALE'
            self.ui_banner = UI_STALE
        return 'CONTEXT_CHANGED'

    def stream_view(self, instance_id=None, logical_project_id=None) -> dict:
        """Durable presentation for one stream. Another stream is not included."""
        stream = _stream_key({'instance_id': instance_id, 'project_id': logical_project_id or ''})
        validity = self.store.meta('context_validity:' + stream)
        sequence = self.store.meta('context_sequence:' + stream)
        if validity == 'STALE':
            return {
                'stream': stream, 'lease': 'STALE', 'banner': UI_STALE,
                'refresh_label': UI_REFRESH,
            }
        if validity == 'VALID' and sequence:
            return {
                'stream': stream, 'lease': 'VALID', 'banner': f'Контекст #{sequence}',
                'refresh_label': '',
            }
        return {'stream': stream, 'lease': 'NONE', 'banner': '', 'refresh_label': ''}

    def apply_stream_ui(self, ui, instance_id=None, logical_project_id=None) -> dict:
        view = self.stream_view(instance_id, logical_project_id)
        ui.apply_context_lease(view['lease'], view['banner'])
        return view

    def context_admission(self, request_id: str) -> str:
        """Current only when the stored capture revision still matches the stream.

        ``context_validity`` is a presentation cache. It cannot make a revision
        mismatch current.
        """
        stored = self.store.context_request(request_id)
        if stored is None or not self._currently_usable(stored):
            return 'STALE_CONTEXT'
        return 'CURRENT'

    def cancel(self, request_id: str) -> str:
        if self.store.context_request(request_id) is None:
            return 'CONTEXT_ERROR'
        self.store.set_context_state(request_id, 'CANCELLED')
        self.lease = 'CANCELLED'
        return 'CANCELLED'

    def refresh_label(self) -> str:
        return UI_REFRESH

    def _stream_revision(self, stream: str) -> int:
        return int(self.store.meta('context_revision:' + stream) or 0)

    def _expected_capture_revision(self, request_id: str) -> int | None:
        raw = self.store.meta(f'context_op_capture_revision:{request_id}')
        if raw is None:
            return None
        return int(raw)

    def _currently_usable(self, stored: dict) -> bool:
        """Revision binding decides. A VALID cache cannot override a mismatch."""
        if stored.get('state') != 'VALID':
            return False
        stream = _stream_key(stored)
        bound = self.store.meta(f'context_capture_revision:{stored["request_id"]}')
        if bound is None or int(bound) != self._stream_revision(stream):
            return False
        return self.store.meta('context_validity:' + stream) != 'STALE'

    def _derived_stale(self, stored: dict) -> bool:
        return _is_completed(stored) and not self._currently_usable(stored)

    def _known_sequence(self, stored: dict) -> int:
        stream = _stream_key(stored)
        known = int(self.store.meta(f'context_sequence:{stream}') or 0)
        if self.current is None:
            return known
        current_row = self.store.context_request(self.current.request_id)
        if current_row is not None and _stream_key(current_row) == stream:
            return max(known, self.current.sequence)
        return known

    def _recorded_hash(self, stream: str, sequence: int, stored: dict) -> str | None:
        saved = self.store.meta(f'context_identity:{stream}:{sequence}')
        if saved:
            return saved
        response = stored.get('response') if stored else None
        if isinstance(response, dict) and response.get('sequence') == sequence:
            return canonical_hash(_identity_from_response(response))
        if (self.current is not None and self.current.sequence == sequence
                and _stream_key({'instance_id': stored.get('instance_id'), 'project_id': stored['project_id']}) == stream):
            return generation_hash(self.current)
        return None

    def _resume_capturing(self, existing: dict) -> dict:
        """Continue the one stored operation. A second capture is not started."""
        self.lease = 'CAPTURING'
        self.ui_banner = UI_CAPTURING
        request_id = existing['request_id']
        if self._assigned(request_id) is None:
            return {
                'kind': 'CONTEXT_REQUEST',
                'requestId': request_id,
                'state': 'CAPTURING',
                'logicalProjectId': existing['project_id'],
                'requestedScope': existing['requested_scope'],
                'instanceId': existing.get('instance_id'),
                'resumed': True,
            }
        ready = self._capture(
            request_id, existing['project_id'], existing['requested_scope'], existing.get('instance_id'))
        return self._publish(ready, existing.get('instance_id'))

    def _publish(self, ready: ContextReady, instance_id) -> dict:
        response = _ready_response(ready)
        stream = _stream_key({'instance_id': instance_id, 'project_id': ready.logical_project_id})
        status = self.store.commit_context_ready(
            ready.request_id, ready.snapshot_id, response, stream, ready.sequence, generation_hash(ready),
            expected_capture_revision=self._expected_capture_revision(ready.request_id))
        if status != 'CONTEXT_READY':
            self._present(instance_id, ready.logical_project_id, 'STALE', UI_STALE)
            return {
                'kind': status,
                'requestId': ready.request_id,
                'reason': 'capture revision',
                'refreshRequired': True,
            }
        self._remember(instance_id, ready)
        self._present(instance_id, ready.logical_project_id, 'VALID', f'Контекст #{ready.sequence}', force=True)
        return response

    def _present(self, instance_id, project_id, lease: str, banner: str, force: bool = False) -> None:
        stream = _stream_key({'instance_id': instance_id, 'project_id': project_id or ''})
        if force or self.active_stream in (None, stream):
            self.active_stream = stream
            self.lease = lease
            self.ui_banner = banner

    def _active_target(self):
        ready = self.current
        if ready is None:
            return None, None
        instance_id = None
        if isinstance(ready.payload, dict):
            instance_id = ready.payload.get('instanceId') or None
        return instance_id, ready.logical_project_id

    def _remember(self, instance_id, ready: ContextReady | None) -> None:
        # Last-seen only. request() must not route through this global.
        if ready is not None:
            self.current = ready
        if instance_id and ready is not None:
            self.by_instance[instance_id] = ready

    def _assigned(self, request_id: str):
        raw = self.store.meta(f'context_op_capture:{request_id}')
        if not raw:
            return None
        sequence, snapshot_id = str(raw).split(':', 1)
        return int(sequence), snapshot_id

    def _payload(self, project_id: str, scope: str, instance_id) -> dict:
        return {
            'source': 'mock',
            'logicalProjectId': project_id,
            'instanceId': instance_id,
            'scope': scope,
            'projectName': None,
            'story': None,
            'selection': None,
            'note': 'mock context; no Archicad read was performed',
        }

    def _capture(self, request_id: str, project_id: str, scope: str, instance_id=None) -> ContextReady:
        assigned = self._assigned(request_id)
        if assigned is None:
            self.sequence += 1
            captures = int(self.store.meta('context_captures') or 0) + 1
            snapshot_id = f'snap-{self.sequence:04d}'
            stream = _stream_key({'instance_id': instance_id, 'project_id': project_id})
            self.store.assign_capture(
                request_id, self.sequence, snapshot_id, self._stream_revision(stream), captures)
            sequence = self.sequence
            if self.fault_after_capture_assigned:
                self.fault_after_capture_assigned()
        else:
            sequence, snapshot_id = assigned
        return ContextReady(
            PROTOCOL_VERSION, request_id, snapshot_id, project_id,
            f'mock-{project_id}-{sequence}', self.clock(),
            self._payload(project_id, scope, instance_id), sequence)


def generation_identity(ready: ContextReady) -> dict:
    """Canonical generation. ``capturedAt`` is included and must not drift."""
    return {
        'protocolVersion': ready.protocol_version,
        'requestId': ready.request_id,
        'snapshotId': ready.snapshot_id,
        'logicalProjectId': ready.logical_project_id,
        'rootHash': ready.root_hash,
        'payload': ready.payload,
        'sequence': ready.sequence,
        'capturedAt': ready.captured_at,
    }


def generation_hash(ready: ContextReady) -> str:
    return canonical_hash(generation_identity(ready))


def _ready_response(ready: ContextReady) -> dict:
    body = generation_identity(ready)
    body['kind'] = 'CONTEXT_READY'
    return body


def _identity_from_response(response: dict) -> dict:
    return {
        'protocolVersion': response.get('protocolVersion', PROTOCOL_VERSION),
        'requestId': response.get('requestId'),
        'snapshotId': response.get('snapshotId'),
        'logicalProjectId': response.get('logicalProjectId'),
        'rootHash': response.get('rootHash'),
        'payload': response.get('payload'),
        'sequence': response.get('sequence'),
        'capturedAt': response.get('capturedAt'),
    }


def _stale_reply(stored: dict) -> dict:
    return {
        'kind': 'CONTEXT_STALE',
        'requestId': stored['request_id'],
        'reason': 'stale',
        'state': 'STALE',
        'snapshotId': stored.get('snapshot_id'),
        'refreshRequired': True,
    }


def _is_completed(stored: dict) -> bool:
    return stored.get('state') == 'VALID' and isinstance(stored.get('response'), dict)


def _response_sequence(stored: dict):
    response = stored.get('response') if stored else None
    if not isinstance(response, dict):
        return None
    sequence = response.get('sequence')
    if isinstance(sequence, bool) or not isinstance(sequence, int):
        return None
    return sequence


def _ready_error(ready) -> str | None:
    if not isinstance(ready, ContextReady):
        return 'CONTEXT_ERROR'
    version = ready.protocol_version
    if isinstance(version, bool) or not isinstance(version, int) or version != PROTOCOL_VERSION:
        return 'PROTOCOL_ERROR'
    if not isinstance(ready.request_id, str) or not ready.request_id.strip():
        return 'CONTEXT_ERROR'
    if not isinstance(ready.snapshot_id, str) or not ready.snapshot_id.strip():
        return 'CONTEXT_ERROR'
    if not isinstance(ready.logical_project_id, str) or not ready.logical_project_id.strip():
        return 'CONTEXT_ERROR'
    if not isinstance(ready.root_hash, str) or not ready.root_hash.strip():
        return 'CONTEXT_ERROR'
    if not isinstance(ready.captured_at, str) or not ready.captured_at.strip():
        return 'CONTEXT_ERROR'
    if not isinstance(ready.payload, dict):
        return 'CONTEXT_ERROR'
    if isinstance(ready.sequence, bool) or not isinstance(ready.sequence, int) or ready.sequence <= 0:
        return 'CONTEXT_ERROR'
    return None


def _ready_stream(ready: ContextReady) -> str:
    instance_id = None
    if isinstance(ready.payload, dict):
        instance_id = ready.payload.get('instanceId') or None
    return _stream_key({'instance_id': instance_id, 'project_id': ready.logical_project_id})


def _stream_key(stored: dict) -> str:
    instance_id = stored.get('instance_id') or ''
    if instance_id:
        return 'instance:' + instance_id
    return 'project:' + stored['project_id']


def _same_identity(existing: dict, project_id: str, scope: str, instance_id) -> bool:
    return (existing['project_id'] == project_id
            and existing['requested_scope'] == scope
            and (existing.get('instance_id') or None) == (instance_id or None))
