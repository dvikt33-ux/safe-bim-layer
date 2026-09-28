"""Framed local protocol. Not an HTTP transport and not a BIM command bus."""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass

from sync_bridge import PROTOCOL_VERSION


class ProtocolError(ValueError):
    pass


REQUIRED_ENVELOPE = ('protocolVersion', 'messageId', 'requestId', 'instanceId', 'kind')
ALLOWED_KINDS = frozenset({
    'HELLO',
    'HELLO_ACK',
    'PING',
    'CONTEXT_REQUEST',
    'CONTEXT_READY',
    'CONTEXT_CHANGED',
    'CONTEXT_ERROR',
    'JOB',
    'RESULT',
})


@dataclass(frozen=True)
class Envelope:
    protocol_version: int
    message_id: str
    request_id: str
    instance_id: str
    kind: str
    payload: dict

    def to_dict(self) -> dict:
        return {
            'protocolVersion': self.protocol_version,
            'messageId': self.message_id,
            'requestId': self.request_id,
            'instanceId': self.instance_id,
            'kind': self.kind,
            'payload': self.payload,
        }


def new_id() -> str:
    return uuid.uuid4().hex


def envelope(kind: str, payload: dict, *, instance_id: str, request_id: str | None = None,
             message_id: str | None = None) -> Envelope:
    if kind not in ALLOWED_KINDS:
        raise ProtocolError(f'unknown kind {kind!r}')
    if not isinstance(payload, dict):
        raise ProtocolError('payload must be an object')
    return Envelope(PROTOCOL_VERSION, message_id or new_id(), request_id or new_id(),
                    instance_id, kind, payload)


def parse_envelope(data: dict) -> Envelope:
    if not isinstance(data, dict):
        raise ProtocolError('envelope must be an object')
    missing = [key for key in REQUIRED_ENVELOPE if key not in data]
    if missing:
        raise ProtocolError('missing envelope fields: ' + ','.join(missing))
    version = data['protocolVersion']
    if type(version) is not int or version != PROTOCOL_VERSION:
        raise ProtocolError(f'protocol version {version!r} is not {PROTOCOL_VERSION}')
    for key in ('messageId', 'requestId', 'instanceId', 'kind'):
        if not isinstance(data[key], str) or not data[key].strip():
            raise ProtocolError(f'{key} required')
    if data['kind'] not in ALLOWED_KINDS:
        raise ProtocolError(f'unknown kind {data["kind"]!r}')
    payload = data.get('payload', {})
    if not isinstance(payload, dict):
        raise ProtocolError('payload must be an object')
    return Envelope(version, data['messageId'], data['requestId'],
                    data['instanceId'], data['kind'], payload)


def encode_frame(message: Envelope) -> bytes:
    body = json.dumps(message.to_dict(), ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    if len(body) > 1_048_576:
        raise ProtocolError('frame exceeds 1 MiB')
    return len(body).to_bytes(4, 'big') + body


def decode_frame(buffer: bytes) -> tuple[Envelope, bytes]:
    if len(buffer) < 4:
        raise ProtocolError('incomplete frame')
    size = int.from_bytes(buffer[:4], 'big')
    if size <= 0 or size > 1_048_576:
        raise ProtocolError('invalid frame length')
    if len(buffer) < 4 + size:
        raise ProtocolError('incomplete frame')
    try:
        data = json.loads(buffer[4:4 + size].decode('utf-8'))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ProtocolError('corrupt frame') from exc
    return parse_envelope(data), buffer[4 + size:]
