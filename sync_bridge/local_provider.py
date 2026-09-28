"""Placeholder for a future local OpenAI-compatible Qwen. No model is installed here."""
from __future__ import annotations

from sync_bridge.ai_broker import Proposal, ProviderError, ProviderTimeout


class LocalOpenAICompatibleProvider:
    def __init__(self, endpoint=None, model_id='qwen-27b-placeholder', ttl_seconds=300):
        self.endpoint = endpoint
        self.model_id = model_id
        self.ttl_seconds = ttl_seconds
        self.load_state = 'UNLOADED'
        self.fallback_status = 'IDLE'
        self.started = False
        self.cancelled = False

    def begin_start(self) -> str:
        if self.endpoint is None:
            self.load_state = 'UNAVAILABLE'
            self.fallback_status = 'UNAVAILABLE'
            return self.load_state
        self.load_state = 'STARTING'
        self.fallback_status = 'STARTING'
        self.started = False
        return self.load_state

    def lazy_start(self) -> str:
        if self.endpoint is None:
            self.load_state = 'UNAVAILABLE'
            self.fallback_status = 'UNAVAILABLE'
            return self.load_state
        self.started = True
        self.load_state = 'LOADING'
        report = self.endpoint.health()
        self.load_state = 'READY' if report.get('status') == 'CONNECTED' else 'UNAVAILABLE'
        self.fallback_status = 'READY' if self.load_state == 'READY' else 'UNAVAILABLE'
        return self.load_state

    def health(self) -> dict:
        """Passive report. UNLOADED stays UNLOADED until an explicit start."""
        if self.load_state == 'STARTING':
            return {'status': 'STARTING', 'modelId': self.model_id, 'loadState': 'STARTING',
                    'fallbackStatus': self.fallback_status}
        if self.load_state == 'UNLOADED':
            return {'status': 'UNLOADED', 'modelId': self.model_id, 'loadState': 'UNLOADED',
                    'fallbackStatus': self.fallback_status}
        if self.load_state == 'READY':
            return {'status': 'CONNECTED', 'modelId': self.model_id, 'loadState': 'READY',
                    'fallbackStatus': self.fallback_status}
        return {'status': 'UNAVAILABLE', 'modelId': self.model_id, 'loadState': self.load_state,
                'fallbackStatus': self.fallback_status}

    def complete(self, prompt: str) -> Proposal:
        if self.cancelled:
            raise ProviderError('local completion cancelled')
        if self.health()['status'] != 'CONNECTED':
            raise ProviderError('локальная модель недоступна')
        try:
            raw = self.endpoint.complete(prompt)
        except TimeoutError as exc:
            raise ProviderTimeout('local model timed out') from exc
        if not isinstance(raw, dict):
            raise ProviderError('malformed local proposal')
        return Proposal(raw.get('kind', 'proposal'), str(raw.get('text', '')), 'local')

    def cancel(self) -> None:
        self.cancelled = True
        self.fallback_status = 'CANCELLED'

    def reset(self) -> str:
        """Clear a cancel so this same instance can start again."""
        self.cancelled = False
        self.started = False
        self.load_state = 'UNLOADED'
        self.fallback_status = 'IDLE'
        return self.fallback_status

    def unload(self) -> str:
        self.load_state = 'UNLOADED'
        self.started = False
        self.cancelled = False
        self.fallback_status = 'UNLOADED'
        return self.load_state
