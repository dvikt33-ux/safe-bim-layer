"""Single-user companion. Local queue and mock context only; no Archicad write API."""
from __future__ import annotations

import json
from datetime import datetime, timezone

from sync_bridge import BRIDGE_VERSION, PROTOCOL_VERSION
from sync_bridge.ai_broker import AIBroker, ProviderError
from sync_bridge.connections import ConnectionBoard
from sync_bridge.context import ContextReady, ContextService
from sync_bridge.git_fallback import narrow_fetch
from sync_bridge.mailbox import NeedsAuth, OfflineError, RateLimited
from sync_bridge.polling import PollScheduler
from sync_bridge.protocol import ProtocolError, envelope, parse_envelope
from sync_bridge.security import PeerIdentity, admit_peer
from sync_bridge.store import BridgeStore


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class InstanceConflict(RuntimeError):
    pass


class SafeBIMBridge:
    def __init__(self, store: BridgeStore, mailbox, *, owner: PeerIdentity, broker: AIBroker | None = None,
                 instance_id: str = 'bridge-1'):
        self.store = store
        self.mailbox = mailbox
        self.owner = owner
        self.broker = broker
        self.instance_id = instance_id
        self.poller = PollScheduler(mailbox)
        self.context = ContextService(store, _now)
        self.connections = ConnectionBoard()
        self.running = False
        self.bound_archicad = None
        self.logs: list[dict] = []
        self.needs_auth = False

    def start(self) -> dict:
        lock = self.store.meta('instance_lock') or ''
        if lock and lock != self.instance_id:
            raise InstanceConflict('bridge already running for this user')
        self.store.set_meta('instance_lock', self.instance_id)
        self.store.set_meta('version', BRIDGE_VERSION)
        self.running = True
        self.connections.set('BRIDGE', 'CONNECTED', 'named-pipe')
        self._log('start', {'version': BRIDGE_VERSION})
        return self.health()

    def stop(self) -> None:
        self.running = False
        self.store.set_meta('instance_lock', '')
        self.connections.set('BRIDGE', 'OFFLINE', 'stopped')
        self._log('stop', {})

    def health(self) -> dict:
        return {
            'running': self.running,
            'version': BRIDGE_VERSION,
            'protocolVersion': PROTOCOL_VERSION,
            'instanceId': self.instance_id,
            'needsAuth': self.needs_auth,
            'connections': self.connections.snapshot(),
            'archicadWriteApi': False,
        }

    def handshake(self, hello: dict, peer: PeerIdentity) -> dict:
        self._require_running()
        if not admit_peer(self.owner, peer):
            raise PermissionError('чужая Windows session отклонена')
        message = parse_envelope(hello)
        if message.kind != 'HELLO':
            raise ProtocolError('HELLO required')
        if self.bound_archicad and self.bound_archicad != message.instance_id:
            raise InstanceConflict('второй экземпляр Archicad отклонён')
        self.bound_archicad = message.instance_id
        self.connections.set('ARCHICAD', 'CONNECTED', message.instance_id)
        return envelope('HELLO_ACK', {'bridgeVersion': BRIDGE_VERSION},
                        instance_id=self.instance_id, request_id=message.request_id).to_dict()

    def accept_remote_message(self, payload: dict) -> dict:
        self._require_running()
        if not isinstance(payload, dict) or 'messageId' not in payload or not isinstance(payload.get('body'), dict):
            self._log('reject', {'reason': 'malformed'})
            return {'status': 'REJECTED', 'jobCreated': False}
        message_id = payload['messageId']
        created = self.store.put_message(message_id, payload.get('kind', 'remote-job'), _now(),
                                         payload, 'ACCEPTED', 'inbox')
        existing = self.store.job_for_message(message_id)
        if existing:
            return {'status': 'DUPLICATE', 'jobId': existing['job_id'], 'jobCreated': False}
        if not created and existing is None:
            stored = self.store.message(message_id)
            if stored and stored.get('payload_error'):
                self.store.set_message_state(message_id, 'CORRUPT')
                return {'status': 'CORRUPT', 'jobCreated': False}
        job_id = 'job-' + message_id
        self.store.put_remote_job(job_id, payload.get('snapshotId'), payload['body'], 'QUEUED', message_id, _now())
        return {'status': 'QUEUED', 'jobId': job_id, 'jobCreated': True}

    def recover_corrupt(self, message_id: str) -> dict:
        stored = self.store.message(message_id)
        if stored is None:
            return {'status': 'MISSING'}
        if stored.get('payload_error'):
            self.store.set_message_state(message_id, 'CORRUPT')
            return {'status': 'CORRUPT', 'running': self.running}
        return {'status': stored['state']}

    def context_request(self, request: dict) -> dict:
        self._require_running()
        message = {
            'requestId': request['requestId'],
            'logicalProjectId': request['logicalProjectId'],
            'requestedScope': request['requestedScope'],
            'requestedAt': request.get('requestedAt', _now()),
        }
        return self.context.request(message)

    def apply_context_ready(self, ready: ContextReady) -> str:
        return self.context.apply_ready(ready)

    def queue_result(self, job_id: str, result: dict) -> None:
        self.store.put_result(job_id, result, 'PENDING')
        self.store.put_message('result-' + job_id, 'result', _now(),
                               {'job_id': job_id, 'result': result, 'messageId': 'result-' + job_id},
                               'PENDING', 'outbox')

    def tick(self) -> dict:
        self._require_running()
        try:
            polled = self.poller.poll_once()
        except Exception as exc:  # bridge process must stay up
            self._log('tick-error', {'error': type(exc).__name__})
            return {'status': 'ERROR', 'error': type(exc).__name__}
        if polled['status'] == 'OFFLINE':
            self.connections.mark_internet_offline()
            self.connections.set('BRIDGE', 'CONNECTED', 'local')
            return polled
        if polled['status'] == 'NEEDS_AUTH':
            self.needs_auth = True
            self.connections.set('REMOTE', 'ERROR', 'NEEDS_AUTH')
            self.connections.set('BRIDGE', 'CONNECTED', 'local')
            return polled
        if polled['status'] == 'CHANGED':
            accepted = []
            for item in polled['messages']:
                try:
                    accepted.append(self.accept_remote_message(item))
                except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                    accepted.append({'status': 'REJECTED', 'jobCreated': False})
            polled['accepted'] = accepted
            self.connections.set('REMOTE', 'CONNECTED', 'mailbox')
        published = self.flush_outbox()
        polled['published'] = published
        return polled

    def flush_outbox(self) -> list:
        results = []
        for item in self.store.pending_outbox():
            try:
                published = self.mailbox.publish_result(item['payload'])
            except OfflineError:
                retry = item['retry_count'] + 1
                self.store.set_message_state(item['message_id'], 'RETRY', retry)
                self.connections.mark_internet_offline()
                results.append({'messageId': item['message_id'], 'status': 'QUEUED'})
                continue
            except (NeedsAuth, RateLimited) as exc:
                self.needs_auth = isinstance(exc, NeedsAuth)
                results.append({'messageId': item['message_id'], 'status': type(exc).__name__})
                continue
            if published['status'] in {'PUBLISHED', 'ALREADY_PUBLISHED'}:
                self.store.set_message_state(item['message_id'], 'SENT', item['retry_count'])
                job_id = item['payload'].get('job_id')
                if job_id and self.store.result(job_id):
                    self.store.put_result(job_id, self.store.result(job_id)['result'], 'SENT')
            results.append(published)
        return results

    def git_fallback(self, ref: str, runner) -> dict:
        result = narrow_fetch(ref, runner)
        self.needs_auth = result['status'] == 'NEEDS_AUTH'
        return result

    def ai_complete(self, prompt: str):
        if self.broker is None:
            raise ProviderError('AI broker is not configured')
        try:
            return self.broker.complete(prompt)
        except ProviderError:
            self.connections.set('AI', 'OFFLINE', 'нет доступного ИИ')
            raise

    def _require_running(self) -> None:
        if not self.running:
            raise RuntimeError('bridge is stopped')

    def _log(self, event: str, fields: dict) -> None:
        safe = {key: value for key, value in fields.items() if 'token' not in key.lower() and 'password' not in key.lower()}
        self.logs.append({'event': event, 'at': _now(), **safe})
