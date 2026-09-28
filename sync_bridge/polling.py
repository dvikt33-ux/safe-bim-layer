"""One conditional poll at a time, with backoff. Not a webhook client."""
from __future__ import annotations

from dataclasses import dataclass

from sync_bridge.mailbox import NeedsAuth, OfflineError, RateLimited


@dataclass
class PollConfig:
    active_seconds: float = 5
    normal_seconds: float = 30
    idle_seconds: float = 120
    offline_seconds: float = 15
    backoff_max_seconds: float = 300


class PollScheduler:
    def __init__(self, mailbox, config: PollConfig | None = None):
        self.mailbox = mailbox
        self.config = config or PollConfig()
        self.mode = 'NORMAL'
        self.delay = self.config.normal_seconds
        self._polling = False
        self.calls = 0
        self.last_error = None

    def poll_once(self):
        if self._polling:
            return {'status': 'BUSY', 'calls': self.calls}
        self._polling = True
        self.calls += 1
        try:
            head = self.mailbox.poll_head()
        except RateLimited as exc:
            self.mode = 'IDLE'
            self.delay = min(self.config.backoff_max_seconds, max(self.delay, exc.retry_after))
            self.last_error = 'rate-limit'
            return {'status': 'RATE_LIMITED', 'retryAfter': self.delay}
        except NeedsAuth:
            self.last_error = 'needs-auth'
            return {'status': 'NEEDS_AUTH'}
        except OfflineError as exc:
            self.mode = 'OFFLINE'
            self.delay = min(self.config.backoff_max_seconds, max(self.config.offline_seconds, self.delay * 2))
            self.last_error = str(exc)
            return {'status': 'OFFLINE', 'delay': self.delay}
        finally:
            self._polling = False
        if head.not_modified:
            self._relax()
            return {'status': 'NOT_MODIFIED', 'etag': head.etag, 'messages': []}
        self.mode = 'ACTIVE'
        self.delay = self.config.active_seconds
        self.last_error = None
        return {'status': 'CHANGED', 'etag': head.etag, 'messages': list(head.messages)}

    def _relax(self):
        if self.mode == 'OFFLINE':
            self.mode = 'NORMAL'
        self.delay = {'ACTIVE': self.config.active_seconds, 'NORMAL': self.config.normal_seconds,
                      'IDLE': self.config.idle_seconds}.get(self.mode, self.config.normal_seconds)
