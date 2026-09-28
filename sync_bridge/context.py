"""Mock project-context protocol and lease. No new Archicad reads."""
from __future__ import annotations

from dataclasses import dataclass

LEASE_STATES = ('CAPTURING', 'READY', 'VALID', 'STALE', 'CANCELLED')
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
        self.lease = 'READY'
        self.sequence = 0
        self.current: ContextReady | None = None
        self.ui_banner = ''

    def request(self, message: dict) -> dict:
        request_id = message['requestId']
        project_id = message['logicalProjectId']
        scope = message['requestedScope']
        existing = self.store.context_request(request_id)
        if existing and existing.get('response'):
            self.lease = existing['state'] if existing['state'] in LEASE_STATES else 'VALID'
            return existing['response']
        self.lease = 'CAPTURING'
        self.ui_banner = UI_CAPTURING
        self.store.put_context_request(request_id, project_id, scope, 'CAPTURING', message.get('requestedAt', self.clock()))
        ready = self._capture(request_id, project_id, scope)
        response = {
            'protocolVersion': 1,
            'kind': 'CONTEXT_READY',
            'requestId': request_id,
            'snapshotId': ready.snapshot_id,
            'logicalProjectId': ready.logical_project_id,
            'rootHash': ready.root_hash,
            'capturedAt': ready.captured_at,
            'payload': ready.payload,
        }
        self.store.set_context_state(request_id, 'VALID', ready.snapshot_id, response)
        self.current = ready
        self.lease = 'VALID'
        self.ui_banner = f'Контекст #{ready.sequence}'
        return response

    def apply_ready(self, ready: ContextReady) -> str:
        stored = self.store.context_request(ready.request_id)
        if stored is None:
            return 'CONTEXT_ERROR'
        if stored['state'] == 'CANCELLED':
            return 'CONTEXT_ERROR'
        if stored['project_id'] != ready.logical_project_id:
            self.store.set_context_state(ready.request_id, 'ERROR')
            return 'CONTEXT_ERROR'
        if self.current is not None and ready.sequence < self.current.sequence:
            return 'IGNORED_STALE'
        self.current = ready
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

    def _capture(self, request_id: str, project_id: str, scope: str) -> ContextReady:
        self.sequence += 1
        payload = {
            'source': 'mock',
            'logicalProjectId': project_id,
            'scope': scope,
            'projectName': 'Test_House',
            'story': 1,
            'selection': '6 стен',
            'note': 'mock context; no Archicad read was performed',
        }
        return ContextReady(
            1, request_id, f'snap-{self.sequence:04d}', project_id,
            f'mock-{project_id}-{self.sequence}', self.clock(), payload, self.sequence)
