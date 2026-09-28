"""Separate connection facts. Offline internet is not a dead Archicad."""
from __future__ import annotations

CHANNELS = ('ARCHICAD', 'BRIDGE', 'REMOTE', 'AI')
STATUSES = ('CONNECTED', 'CONNECTING', 'DEGRADED', 'OFFLINE', 'ERROR')


class ConnectionBoard:
    def __init__(self):
        self._state = {channel: {'status': 'CONNECTING', 'detail': ''} for channel in CHANNELS}

    def set(self, channel: str, status: str, detail: str = '') -> None:
        if channel not in CHANNELS:
            raise KeyError(channel)
        if status not in STATUSES:
            raise ValueError(status)
        self._state[channel] = {'status': status, 'detail': detail}

    def get(self, channel: str) -> dict:
        return dict(self._state[channel])

    def snapshot(self) -> dict:
        return {channel: self.get(channel) for channel in CHANNELS}

    def mark_internet_offline(self) -> None:
        self.set('REMOTE', 'OFFLINE', 'нет интернета')
        self.set('AI', 'OFFLINE', 'облачный ИИ недоступен')

    def confused(self) -> bool:
        """True only if internet loss was stored as an Archicad failure."""
        remote = self.get('REMOTE')['status']
        archicad = self.get('ARCHICAD')['status']
        return remote == 'OFFLINE' and archicad in {'OFFLINE', 'ERROR'} and self.get('ARCHICAD')['detail'] == 'нет интернета'
