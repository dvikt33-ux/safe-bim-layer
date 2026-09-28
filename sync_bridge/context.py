"""Mock project-context protocol and lease. No new Archicad reads."""
from __future__ import annotations

from dataclasses import dataclass

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
        if not isinstance(ready.root_hash, str) or not ready.root_hash.strip():
            return 'CONTEXT_ERROR'
        stored = self.store.context_request(ready.request_id)
        if stored is None:
            return 'CONTEXT_ERROR'
        if stored['state'] == 'CANCELLED':
            self.lease = 'CANCELLED'
            return 'CONTEXT_ERROR'
        if stored['project_id'] != ready.logical_project_id:
            self.store.set_context_state(ready.request_id, 'ERROR')
            return 'CONTEXT_ERROR'
        known = self._known_sequence(stored)
        if ready.sequence < known:
            return 'IGNORED_STALE'
        stream = _stream_key(stored)
        self.store.set_meta(f'context_sequence:{stream}', str(max(known, ready.sequence)))
        self._remember(stored.get('instance_id'), ready)
        self.lease = 'VALID'
        self.ui_banner = f'Контекст #{ready.sequence}'
        self.store.set_context_state(ready.request_id, 'VALID', ready.snapshot_id, {
            'kind': 'CONTEXT_READY', 'requestId': ready.request_id, 'snapshotId': ready.snapshot_id,
            'logicalProjectId': ready.logical_project_id, 'rootHash': ready.root_hash,
            'capturedAt': ready.captured_at, 'payload': ready.payload,
        })
        return 'CONTEXT_READY'

    def mark_changed(self) -> str:
        self.lease = 'STALE'
        self.ui_banner = UI_STALE
        return 'CONTEXT_CHANGED'

    def cancel(self, request_id: str) -> str:
        if self.store.context_request(request_id) is None:
            return 'CONTEXT_ERROR'
        self.store.set_context_state(request_id, 'CANCELLED')
        self.lease = 'CANCELLED'
        return 'CANCELLED'

    def refresh_label(self) -> str:
        return UI_REFRESH

    def _known_sequence(self, stored: dict) -> int:
        stream = _stream_key(stored)
        known = int(self.store.meta(f'context_sequence:{stream}') or 0)
        if self.current is None:
            return known
        current_row = self.store.context_request(self.current.request_id)
        if current_row is not None and _stream_key(current_row) == stream:
            return max(known, self.current.sequence)
        return known

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
        response = {
            'protocolVersion': 1,
            'kind': 'CONTEXT_READY',
            'requestId': ready.request_id,
            'snapshotId': ready.snapshot_id,
            'logicalProjectId': ready.logical_project_id,
            'rootHash': ready.root_hash,
            'capturedAt': ready.captured_at,
            'payload': ready.payload,
        }
        self.store.set_context_state(ready.request_id, 'VALID', ready.snapshot_id, response)
        self._remember(instance_id, ready)
        self.lease = 'VALID'
        self.ui_banner = f'Контекст #{ready.sequence}'
        return response

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
            self.store.set_meta('context_sequence', str(self.sequence))
            captures = int(self.store.meta('context_captures') or 0) + 1
            self.store.set_meta('context_captures', str(captures))
            snapshot_id = f'snap-{self.sequence:04d}'
            self.store.set_meta(f'context_op_capture:{request_id}', f'{self.sequence}:{snapshot_id}')
            sequence = self.sequence
            if self.fault_after_capture_assigned:
                self.fault_after_capture_assigned()
        else:
            sequence, snapshot_id = assigned
        return ContextReady(
            1, request_id, snapshot_id, project_id,
            f'mock-{project_id}-{sequence}', self.clock(),
            self._payload(project_id, scope, instance_id), sequence)


def _stream_key(stored: dict) -> str:
    instance_id = stored.get('instance_id') or ''
    if instance_id:
        return 'instance:' + instance_id
    return 'project:' + stored['project_id']


def _same_identity(existing: dict, project_id: str, scope: str, instance_id) -> bool:
    return (existing['project_id'] == project_id
            and existing['requested_scope'] == scope
            and (existing.get('instance_id') or None) == (instance_id or None))
