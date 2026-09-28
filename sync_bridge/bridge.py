"""Single-user companion. Local queue and mock context only; no Archicad write API.

Archicad model A: one Bridge multiplexes several clients in the same Windows
session. Clients are keyed by instance_id and never share project context.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from sync_bridge import BRIDGE_VERSION, PROTOCOL_VERSION
from sync_bridge.ai_broker import AIBroker, ProviderError
from sync_bridge.connections import ConnectionBoard
from sync_bridge.context import ContextReady, ContextService
from sync_bridge.git_fallback import narrow_fetch
from sync_bridge.mailbox import AckLost, ETAG_POLICY, NeedsAuth, OfflineError, RateLimited
from sync_bridge.pipe_win32 import MAX_PIPE_INSTANCES, MULTIPLEX_MODEL, PipeApplicationGate
from sync_bridge.polling import PollScheduler
from sync_bridge.protocol import ProtocolError, decode_frame, envelope, parse_envelope
from sync_bridge.security import PeerIdentity, admit_peer
from sync_bridge.store import BridgeStore

ARCHICAD_MULTIPLEX = MULTIPLEX_MODEL


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class InstanceConflict(RuntimeError):
    pass


class InjectedCrash(BaseException):
    """Fault-injection crash. BaseException so a tick cannot swallow it."""


def dead_letter_key(payload) -> str:
    try:
        raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    except TypeError:
        raw = str(payload)
    return 'deadletter:' + hashlib.sha256(raw.encode('utf-8')).hexdigest()


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
        self.logs: list[dict] = []
        self.needs_auth = False
        self.fault_after_persist = None
        self.pipe_gate = PipeApplicationGate()

    def start(self) -> dict:
        lock = self.store.meta('instance_lock') or ''
        if lock and lock != self.instance_id:
            raise InstanceConflict('bridge already running for this user')
        self.store.set_meta('instance_lock', self.instance_id)
        self.store.set_meta('version', BRIDGE_VERSION)
        stored_etag = self.store.meta('remote_etag')
        if stored_etag:
            self.mailbox.etag = stored_etag
        self.running = True
        self.connections.set('BRIDGE', 'CONNECTED', 'named-pipe')
        self._refresh_archicad_channel()
        self._log('start', {'version': BRIDGE_VERSION, 'etagPolicy': ETAG_POLICY})
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
            'archicadMultiplex': ARCHICAD_MULTIPLEX,
            'etagPolicy': ETAG_POLICY,
        }

    def handshake(self, hello: dict, peer: PeerIdentity) -> dict:
        self._require_running()
        if not admit_peer(self.owner, peer):
            raise PermissionError('чужая Windows session или SID отклонены')
        message = parse_envelope(hello)
        if message.kind != 'HELLO':
            raise ProtocolError('HELLO required')
        existing = self.store.client(message.instance_id)
        if existing and existing['connection_state'] == 'CONNECTED':
            raise InstanceConflict('duplicate instance_id')
        connected = [item for item in self.store.clients() if item['connection_state'] == 'CONNECTED']
        if len(connected) >= MAX_PIPE_INSTANCES:
            raise InstanceConflict('archicad client limit')
        project = message.payload.get('logicalProjectId')
        self.store.upsert_client(message.instance_id, peer.session_id, project, _now(), 'CONNECTED')
        self.pipe_gate.handshaken.add(message.instance_id)
        self._refresh_archicad_channel()
        return envelope('HELLO_ACK', {'bridgeVersion': BRIDGE_VERSION, 'instanceId': message.instance_id},
                        instance_id=self.instance_id, request_id=message.request_id).to_dict()

    def disconnect_archicad(self, instance_id: str) -> None:
        self._require_running()
        self.store.set_client_state(instance_id, 'DISCONNECTED', _now())
        self.pipe_gate.handshaken.discard(instance_id)
        self._refresh_archicad_channel()

    def accept_client_frame(self, peer: PeerIdentity, frame):
        self._require_running()
        if not admit_peer(self.owner, peer):
            raise PermissionError('чужая Windows session или SID отклонены')
        if isinstance(frame, (bytes, bytearray)):
            message, _rest = decode_frame(bytes(frame))
        else:
            message = parse_envelope(frame)
        if message.kind != 'HELLO' and message.instance_id not in self.pipe_gate.handshaken:
            raise ProtocolError('handshake required before application frame')
        if message.kind == 'HELLO':
            return self.handshake(message.to_dict(), peer)
        self.pipe_gate.accept(message)
        return message.to_dict()

    def accept_remote_message(self, payload: dict) -> dict:
        self._require_running()
        if not isinstance(payload, dict) or not isinstance(payload.get('messageId'), str) or not payload.get('messageId').strip() or not isinstance(payload.get('body'), dict):
            return self._quarantine(payload)
        message_id = payload['messageId']
        existing_message = self.store.message(message_id)
        if existing_message and existing_message['state'] == 'DEAD_LETTER':
            return {'status': 'DEAD_LETTER', 'jobCreated': False, 'messageId': message_id}
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
        if self.fault_after_persist:
            self.fault_after_persist()
        return {'status': 'QUEUED', 'jobId': job_id, 'jobCreated': True}

    def _quarantine(self, payload) -> dict:
        key = dead_letter_key(payload)
        body = {'raw': payload} if isinstance(payload, dict) else {'value': str(payload)}
        self.store.put_message(key, 'dead-letter', _now(), body, 'DEAD_LETTER', 'inbox')
        self._log('quarantine', {'messageId': key})
        return {'status': 'DEAD_LETTER', 'jobCreated': False, 'messageId': key}

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
        instance_id = request.get('instanceId')
        project_id = request['logicalProjectId']
        client = self.store.client(instance_id) if instance_id else None
        if client and client.get('logical_project_id') not in (None, '', project_id):
            return {'kind': 'CONTEXT_ERROR', 'requestId': request['requestId'], 'reason': 'wrong project'}
        message = {
            'requestId': request['requestId'],
            'logicalProjectId': project_id,
            'requestedScope': request['requestedScope'],
            'requestedAt': request.get('requestedAt', _now()),
            'instanceId': instance_id,
        }
        response = self.context.request(message)
        if isinstance(response, dict) and response.get('logicalProjectId') not in (None, project_id):
            return {'kind': 'CONTEXT_ERROR', 'requestId': request['requestId'], 'reason': 'cross-project snapshot'}
        return response

    def apply_context_ready(self, ready: ContextReady) -> str:
        return self.context.apply_ready(ready)

    def queue_result(self, job_id: str, result: dict) -> None:
        message_id = 'result-' + job_id
        self.store.put_result(job_id, result, 'PENDING')
        self.store.put_message(message_id, 'result', _now(),
                               {'job_id': job_id, 'result': result, 'messageId': message_id},
                               'PENDING', 'outbox')

    def tick(self) -> dict:
        self._require_running()
        try:
            polled = self.poller.poll_once()
        except InjectedCrash:
            raise
        except Exception as exc:  # bridge process must stay up
            self._log('tick-error', {'error': type(exc).__name__})
            return {'status': 'ERROR', 'error': type(exc).__name__}
        if polled['status'] == 'OFFLINE':
            self.connections.mark_internet_offline()
            self.connections.set('BRIDGE', 'CONNECTED', 'local')
            polled['processed'] = 0
            return polled
        if polled['status'] == 'NEEDS_AUTH':
            self.needs_auth = True
            self.connections.set('REMOTE', 'ERROR', 'NEEDS_AUTH')
            self.connections.set('BRIDGE', 'CONNECTED', 'local')
            polled['processed'] = 0
            return polled
        if polled['status'] == 'CHANGED':
            accepted = []
            for item in polled['messages']:
                try:
                    accepted.append(self.accept_remote_message(item))
                except InjectedCrash:
                    raise
                except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                    accepted.append(self._quarantine(item))
            polled['accepted'] = accepted
            polled['processed'] = len(polled['messages'])
            self.connections.set('REMOTE', 'CONNECTED', 'mailbox')
        else:
            polled['processed'] = 0
        published = self.flush_outbox()
        if polled.get('etag'):
            self.store.set_meta('remote_etag', polled['etag'])
        polled['published'] = published
        return polled

    def flush_outbox(self) -> list:
        results = []
        for item in self.store.pending_outbox():
            try:
                published = self.mailbox.publish_result(item['payload'])
            except AckLost:
                retry = item['retry_count'] + 1
                self.store.set_message_state(item['message_id'], 'UNCERTAIN', retry)
                results.append({'messageId': item['message_id'], 'status': 'UNCERTAIN'})
                continue
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
            if self.broker.last_route == 'starting':
                self.connections.set('AI', 'CONNECTING', 'STARTING')
            else:
                self.connections.set('AI', 'OFFLINE', 'нет доступного ИИ')
            raise

    def ai_cancel(self) -> dict:
        if self.broker is not None:
            self.broker.cancel()
        return {'jobs': len(self.store.jobs()), 'outbox': len(self.store.pending_outbox())}

    def _refresh_archicad_channel(self) -> None:
        connected = [item for item in self.store.clients() if item['connection_state'] == 'CONNECTED']
        if connected:
            self.connections.set('ARCHICAD', 'CONNECTED', ','.join(item['instance_id'] for item in connected))
        else:
            self.connections.set('ARCHICAD', 'OFFLINE', 'no clients')

    def _require_running(self) -> None:
        if not self.running:
            raise RuntimeError('bridge is stopped')

    def _log(self, event: str, fields: dict) -> None:
        safe = {key: value for key, value in fields.items() if 'token' not in key.lower() and 'password' not in key.lower()}
        self.logs.append({'event': event, 'at': _now(), **safe})
