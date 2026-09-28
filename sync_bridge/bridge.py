"""Single-user companion. Local queue and mock context only; no Archicad write API.

Archicad model A: one Bridge multiplexes several clients in the same Windows
session. Clients are keyed by instance_id and never share project context.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone

from sync_bridge import BRIDGE_VERSION, PROTOCOL_VERSION
from sync_bridge.ai_broker import AIBroker, ProviderError
from sync_bridge.connections import ConnectionBoard
from sync_bridge.context import ContextReady, ContextService
from sync_bridge.git_fallback import narrow_fetch
from sync_bridge.identity import canonical_hash, canonical_json
from sync_bridge.instance_lock import OWNERSHIP_GATE, SQLITE_LEASE_ROLE, SingleInstanceLock
from sync_bridge.mailbox import AckLost, ETAG_POLICY, NeedsAuth, OfflineError, RateLimited, RemoteError
from sync_bridge.pipe_win32 import MAX_PIPE_INSTANCES, MULTIPLEX_MODEL, PipeApplicationGate
from sync_bridge.polling import PollScheduler
from sync_bridge.protocol import ProtocolError, decode_frame, envelope, parse_envelope
from sync_bridge.security import PeerIdentity, admit_peer
from sync_bridge.store import BridgeStore

ARCHICAD_MULTIPLEX = MULTIPLEX_MODEL


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stored_hash(payload) -> str:
    if not isinstance(payload, dict):
        return ''
    return canonical_hash(payload)


class InstanceConflict(RuntimeError):
    pass


class LeaseLost(RuntimeError):
    """This process no longer owns the bridge. Work must stop."""


class InjectedCrash(BaseException):
    """Fault-injection crash. BaseException so a tick cannot swallow it."""


def dead_letter_key(payload) -> str:
    try:
        raw = canonical_json(payload)
    except (TypeError, ValueError, UnicodeError):
        raw = 'non-json:' + type(payload).__module__ + '.' + type(payload).__qualname__
    return 'deadletter:' + hashlib.sha256(raw.encode('utf-8')).hexdigest()


class SafeBIMBridge:
    def __init__(self, store: BridgeStore, mailbox, *, owner: PeerIdentity, broker: AIBroker | None = None,
                 instance_id: str = 'bridge-1', clock=None, lease_ttl_seconds: float = 30,
                 mutex_kernel=None):
        self.store = store
        self.mailbox = mailbox
        self.owner = owner
        self.broker = broker
        self.instance_id = instance_id
        self.clock = clock or _now
        self.lease_ttl_seconds = lease_ttl_seconds
        self.process_token = uuid.uuid4().hex
        self.epoch = 0
        self.instance_lock = SingleInstanceLock(owner.user_sid, mutex_kernel)
        self.lease_state = 'NONE'
        self.poller = PollScheduler(mailbox)
        self.context = ContextService(store, _now)
        self.connections = ConnectionBoard()
        self.running = False
        self.logs: list[dict] = []
        self.needs_auth = False
        self.fault_after_persist = None
        self.pipe_gate = PipeApplicationGate()

    def start(self) -> dict:
        # Named mutex is the ownership gate. A live holder is not expired by TTL.
        acquired = self.instance_lock.try_acquire()
        if acquired == 'blocked':
            raise InstanceConflict('bridge lease held by another process')
        now = self.clock()
        if not self.store.acquire_lease(self.process_token, now, self.lease_ttl_seconds, self.instance_id):
            self.instance_lock.release()
            raise InstanceConflict('bridge lease held by another process')
        self.lease_state = 'HELD'
        self.epoch = int(self.store.meta('bridge_epoch') or '0')
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
        self.lease_state = 'RELEASED'
        self.store.release_lease(self.process_token)
        self.instance_lock.release()
        self.connections.set('BRIDGE', 'OFFLINE', 'stopped')
        self._log('stop', {})

    def crash(self) -> None:
        """Process death. The mutex is abandoned and this object stops heartbeating."""
        self.running = False
        self.lease_state = 'CRASHED'
        self.instance_lock.abandon()
        self._log('crash', {})

    def heartbeat(self) -> bool:
        """Renew diagnostic expiry. A live owner does not lose the mutex by TTL."""
        self._require_owner()
        if not self.store.renew_lease(self.process_token, self.clock(), self.lease_ttl_seconds):
            self._mark_lease_lost()
            raise LeaseLost('LEASE_LOST')
        return True

    def close(self) -> None:
        if self.running:
            self.stop()
        elif self.instance_lock.held():
            self.instance_lock.release()
        self.store.close()

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
            'leaseState': self.lease_state,
            'ownership': OWNERSHIP_GATE,
            'sqliteLeaseRole': SQLITE_LEASE_ROLE,
        }

    def handshake(self, hello: dict, peer: PeerIdentity) -> dict:
        self._require_owner()
        if not admit_peer(self.owner, peer):
            raise PermissionError('чужая Windows session или SID отклонены')
        message = parse_envelope(hello)
        if message.kind != 'HELLO':
            raise ProtocolError('HELLO required')
        existing = self.store.client(message.instance_id)
        if existing and existing['connection_state'] == 'CONNECTED' and int(existing.get('epoch') or -1) == self.epoch:
            raise InstanceConflict('duplicate instance_id')
        connected = [item for item in self.store.clients()
                     if item['connection_state'] == 'CONNECTED' and int(item.get('epoch') or -1) == self.epoch]
        if len(connected) >= MAX_PIPE_INSTANCES:
            raise InstanceConflict('archicad client limit')
        project = message.payload.get('logicalProjectId')
        self.store.upsert_client(message.instance_id, peer.session_id, project, _now(), 'CONNECTED', self.epoch)
        self.pipe_gate.handshaken.add(message.instance_id)
        self._refresh_archicad_channel()
        return envelope('HELLO_ACK', {'bridgeVersion': BRIDGE_VERSION, 'instanceId': message.instance_id},
                        instance_id=self.instance_id, request_id=message.request_id).to_dict()

    def disconnect_archicad(self, instance_id: str) -> None:
        self._require_owner()
        self.store.set_client_state(instance_id, 'DISCONNECTED', _now())
        self.pipe_gate.handshaken.discard(instance_id)
        self._refresh_archicad_channel()

    def accept_client_frame(self, peer: PeerIdentity, frame):
        self._require_owner()
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
        self._require_owner()
        if isinstance(payload, dict) and payload.get('_remoteError'):
            return self._quarantine(payload, str(payload['_remoteError']))
        if not isinstance(payload, dict) or not isinstance(payload.get('messageId'), str) or not payload.get('messageId').strip() or not isinstance(payload.get('body'), dict):
            return self._quarantine(payload)
        message_id = payload['messageId']
        incoming_hash = canonical_hash(payload)
        existing_message = self.store.message(message_id)
        if existing_message and existing_message['state'] == 'DEAD_LETTER':
            return {'status': 'DEAD_LETTER', 'jobCreated': False, 'messageId': message_id}
        if existing_message is not None:
            stored_hash = existing_message.get('payload_hash') or _stored_hash(existing_message.get('payload'))
            if stored_hash and stored_hash != incoming_hash:
                return {'status': 'MESSAGE_ID_CONFLICT', 'jobCreated': False, 'messageId': message_id}
        existing = self.store.job_for_message(message_id)
        if existing:
            return {'status': 'DUPLICATE', 'jobId': existing['job_id'], 'jobCreated': False}
        created = self.store.put_message(message_id, payload.get('kind', 'remote-job'), _now(),
                                         payload, 'ACCEPTED', 'inbox')
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

    def _quarantine(self, payload, reason: str = 'DEAD_LETTER') -> dict:
        key = dead_letter_key({'reason': reason, 'payload': payload})
        body = {'raw': payload} if isinstance(payload, dict) else {'value': str(payload)}
        state = 'DEAD_LETTER' if reason == 'DEAD_LETTER' else 'QUARANTINED'
        self.store.put_message(key, 'dead-letter', _now(), body, state, 'inbox')
        self._log('quarantine', {'messageId': key, 'reason': reason})
        return {'status': reason, 'jobCreated': False, 'messageId': key}

    def recover_corrupt(self, message_id: str) -> dict:
        stored = self.store.message(message_id)
        if stored is None:
            return {'status': 'MISSING'}
        if stored.get('payload_error'):
            self.store.set_message_state(message_id, 'CORRUPT')
            return {'status': 'CORRUPT', 'running': self.running}
        return {'status': stored['state']}

    def context_request(self, request: dict) -> dict:
        self._require_owner()
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
        self._require_owner()
        return self.context.apply_ready(ready)

    def queue_result(self, job_id: str, result: dict) -> None:
        self._require_owner()
        message_id = 'result-' + job_id
        self.store.enqueue_result(
            job_id, result, message_id, _now(),
            {'job_id': job_id, 'result': result, 'messageId': message_id})

    def tick(self) -> dict:
        try:
            self._require_owner()
        except LeaseLost:
            return {'status': 'LEASE_LOST', 'processed': 0, 'published': []}
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
        if polled['status'] == 'RATE_LIMITED':
            self.connections.set('REMOTE', 'DEGRADED', 'RATE_LIMITED')
            self.connections.set('BRIDGE', 'CONNECTED', 'local')
            polled['processed'] = 0
            return polled
        if polled['status'] == 'ERROR':
            self.connections.set('REMOTE', 'ERROR', polled.get('code', 'ERROR'))
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
        polled['published'] = published
        if polled.get('etag'):
            self.store.set_meta('remote_etag', polled['etag'])
            self.mailbox.commit_etag(polled['etag'])
        return polled

    def flush_outbox(self) -> list:
        self._require_owner()
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
            except RemoteError as exc:
                self.connections.set('REMOTE', 'ERROR', exc.code)
                results.append({'messageId': item['message_id'], 'status': exc.code})
                continue
            if published['status'] == 'MESSAGE_ID_CONFLICT':
                results.append(published)
                continue
            if published['status'] in {'CREATED', 'PUBLISHED', 'ALREADY_PUBLISHED'}:
                job_id = item['payload'].get('job_id')
                stored = self.store.result(job_id) if job_id else None
                sent_result = item['payload'].get('result')
                if stored is not None and canonical_hash(stored['result']) != canonical_hash(sent_result):
                    results.append({'messageId': item['message_id'], 'status': 'RESULT_MISMATCH'})
                    continue
                self.store.set_message_state(item['message_id'], 'SENT', item['retry_count'])
                if stored is not None:
                    self.store.put_result(job_id, stored['result'], 'SENT')
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
        connected = [item for item in self.store.clients()
                     if item['connection_state'] == 'CONNECTED' and int(item.get('epoch') or -1) == self.epoch]
        if connected:
            self.connections.set('ARCHICAD', 'CONNECTED', ','.join(item['instance_id'] for item in connected))
        else:
            self.connections.set('ARCHICAD', 'OFFLINE', 'no clients')

    def _require_running(self) -> None:
        if not self.running:
            raise RuntimeError('bridge is stopped')

    def _require_owner(self) -> None:
        if self.lease_state == 'LEASE_LOST':
            raise LeaseLost('LEASE_LOST')
        self._require_running()
        if not self.instance_lock.held():
            self._mark_lease_lost()
            raise LeaseLost('LEASE_LOST')

    def _mark_lease_lost(self) -> None:
        self.lease_state = 'LEASE_LOST'
        self.running = False
        self.connections.set('BRIDGE', 'ERROR', 'LEASE_LOST')
        self._log('LEASE_LOST', {})

    def _log(self, event: str, fields: dict) -> None:
        blocked = ('token', 'password', 'authorization', 'cookie', 'secret')
        safe = {key: value for key, value in fields.items()
                if not any(word in key.lower() for word in blocked)}
        self.logs.append({'event': event, 'at': _now(), **safe})
