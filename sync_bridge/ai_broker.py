"""Route a prompt to cloud or local AI. Never executes a BIM action.

Cloud is preferred on every request. A timeout falls back to local for that
request only; the next request tries cloud again when it is healthy. STARTING
is not reported as OFFLINE.
"""
from __future__ import annotations

from dataclasses import dataclass

FORBIDDEN_MARKERS = ('CreateWalls', 'ModifySlabs', 'DeleteElements', 'OpenProject', 'TapirCommand')


class ProviderError(RuntimeError):
    pass


class ProviderTimeout(ProviderError):
    pass


@dataclass(frozen=True)
class Proposal:
    kind: str
    text: str
    provider: str
    executable: bool = False

    def __post_init__(self):
        if self.kind not in {'proposal', 'mock_recipe'}:
            raise ProviderError('AI output must be a typed proposal')
        if self.executable:
            raise ProviderError('AI output cannot be executable')
        if any(marker in self.text for marker in FORBIDDEN_MARKERS):
            raise ProviderError('AI output cannot contain a Tapir command')


class CloudProvider:
    def __init__(self, endpoint, model_id='cloud-mock'):
        self.endpoint = endpoint
        self.model_id = model_id

    def health(self) -> dict:
        try:
            report = self.endpoint.health()
        except ProviderTimeout:
            return {'status': 'OFFLINE', 'modelId': self.model_id}
        except ConnectionError:
            return {'status': 'OFFLINE', 'modelId': self.model_id}
        return {'status': report.get('status', 'CONNECTED'), 'modelId': self.model_id}

    def complete(self, prompt: str) -> Proposal:
        raw = self.endpoint.complete(prompt)
        return _proposal_from_raw(raw, 'cloud')


class AIBroker:
    def __init__(self, cloud: CloudProvider | None, local=None):
        self.cloud = cloud
        self.local = local
        self.last_route = None

    def health(self) -> dict:
        cloud = self.cloud.health() if self.cloud else {'status': 'OFFLINE'}
        local = self.local.health() if self.local else {'status': 'UNAVAILABLE', 'loadState': 'UNAVAILABLE'}
        if cloud.get('status') == 'CONNECTED':
            route = 'cloud'
        elif local.get('status') == 'CONNECTED':
            route = 'local'
        elif local.get('status') == 'STARTING':
            route = 'starting'
        else:
            route = 'unavailable'
        return {'route': route, 'cloud': cloud, 'local': local}

    def complete(self, prompt: str) -> Proposal:
        if self.cloud is not None and self.cloud.health().get('status') == 'CONNECTED':
            try:
                proposal = self.cloud.complete(prompt)
            except (ProviderTimeout, ConnectionError, ProviderError):
                proposal = None
            else:
                self.last_route = 'cloud'
                return proposal
        if self.local is not None:
            if getattr(self.local, 'load_state', None) == 'UNLOADED':
                self.local.lazy_start()
            local_status = self.local.health().get('status')
            if local_status == 'STARTING':
                self.last_route = 'starting'
                raise ProviderError('локальный ИИ запускается')
            if local_status == 'CONNECTED':
                proposal = self.local.complete(prompt)
                self.last_route = 'local'
                return proposal
        self.last_route = 'unavailable'
        raise ProviderError('облачный и локальный ИИ недоступны')

    def cancel(self) -> None:
        if self.local is not None and hasattr(self.local, 'cancel'):
            self.local.cancel()
        self.last_route = 'cancelled'


def _proposal_from_raw(raw: dict, provider: str) -> Proposal:
    if not isinstance(raw, dict) or raw.get('kind') not in {'proposal', 'mock_recipe'}:
        raise ProviderError('malformed AI proposal')
    return Proposal(raw['kind'], str(raw.get('text', '')), provider, executable=False)
