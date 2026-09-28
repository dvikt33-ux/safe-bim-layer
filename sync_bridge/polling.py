"""One conditional poll at a time, with bounded backoff. Not a webhook client.

Delays are returned to the caller. This scheduler never sleeps, so tests can
inject ``rng`` for jitter without waiting.
"""
from __future__ import annotations

from dataclasses import dataclass

from sync_bridge.mailbox import NeedsAuth, OfflineError, RateLimited, RemoteError


@dataclass
class PollConfig:
    active_seconds: float = 5
    normal_seconds: float = 30
    idle_seconds: float = 120
    offline_seconds: float = 15
    backoff_max_seconds: float = 300


class PollScheduler:
    def __init__(self, mailbox, config: PollConfig | None = None, rng=None):
        self.mailbox = mailbox
        self.config = config or PollConfig()
        self.rng = rng
        self.mode = 'NORMAL'
        self.delay = self.config.normal_seconds
        self._polling = False
        self.calls = 0
        self.last_error = None

    @property
    def in_flight(self) -> bool:
        return self._polling

    def poll_once(self):
        if self._polling:
            return {'status': 'BUSY', 'calls': self.calls}
        self._polling = True
        self.calls += 1
        try:
            head = self.mailbox.poll_head()
        except RateLimited as exc:
            self.mode = 'IDLE'
            self.last_error = 'rate-limit'
            self._backoff(max(self.delay, exc.retry_after))
            return {'status': 'RATE_LIMITED', 'retryAfter': self.delay}
        except NeedsAuth:
            self.last_error = 'needs-auth'
            return {'status': 'NEEDS_AUTH'}
        except RemoteError as exc:
            self.mode = 'IDLE'
            self.last_error = exc.code
            self._backoff(self.delay * 2)
            return {'status': 'ERROR', 'code': exc.code, 'delay': self.delay}
        except OfflineError as exc:
            self.mode = 'OFFLINE'
            self.last_error = str(exc)
            self._backoff(self.delay * 2)
            return {'status': 'OFFLINE', 'delay': self.delay}
        finally:
            self._polling = False
        if head.not_modified:
            self._relax()
            return {'status': 'NOT_MODIFIED', 'etag': head.etag, 'messages': [], 'processed': 0}
        self.mode = 'ACTIVE'
        self.delay = self.config.active_seconds
        self.last_error = None
        return {'status': 'CHANGED', 'etag': head.etag, 'messages': list(head.messages),
                'processed': len(head.messages)}

    def _backoff(self, proposed: float) -> None:
        delay = min(self.config.backoff_max_seconds, max(self.config.offline_seconds, proposed))
        if self.rng is not None:
            factor = 0.8 + 0.2 * float(self.rng())
            delay = min(self.config.backoff_max_seconds, max(self.config.offline_seconds, delay * factor))
        if delay <= 0:
            delay = self.config.offline_seconds
        self.delay = delay

    def _relax(self):
        if self.mode == 'OFFLINE':
            self.mode = 'NORMAL'
        self.delay = {'ACTIVE': self.config.active_seconds, 'NORMAL': self.config.normal_seconds,
                      'IDLE': self.config.idle_seconds}.get(self.mode, self.config.normal_seconds)
