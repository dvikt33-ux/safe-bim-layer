"""Windows Named Pipe transport contract. HTTP is not a fallback.

This module verifies the offline contract only. It does not claim that a
real Windows pipe was opened. Status: OFFLINE_CONTRACT_VERIFIED.

v0.1 model is one Bridge multiplexing several Archicad clients in the same
Windows session. ``MAX_PIPE_INSTANCES`` is that quota, not a second bridge.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from sync_bridge.protocol import ProtocolError
from sync_bridge.security import sddl_for_user

PIPE_ACCESS_DUPLEX = 0x00000003
PIPE_TYPE_MESSAGE = 0x00000004
PIPE_READMODE_MESSAGE = 0x00000002
PIPE_WAIT = 0x00000000
PIPE_REJECT_REMOTE_CLIENTS = 0x00000008
ERROR_PIPE_BUSY = 231
INVALID_HANDLE_VALUE = -1
MAX_PIPE_INSTANCES = 8
PIPE_VERIFICATION = 'OFFLINE_CONTRACT_VERIFIED'
MULTIPLEX_MODEL = 'single-bridge'


class NamedPipeUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class PipeOpenRequest:
    name: str
    max_instances: int
    sddl: str
    reject_remote: bool


class PipeApplicationGate:
    """Application frames are refused until HELLO for that instance_id."""

    def __init__(self):
        self.handshaken: set[str] = set()

    def accept(self, message) -> str:
        if message.instance_id not in self.handshaken:
            if message.kind != 'HELLO':
                raise ProtocolError('handshake required before application frame')
            self.handshaken.add(message.instance_id)
            return 'HANDSHAKE'
        return 'APPLICATION'


class WindowsNamedPipe:
    """CreateFile/CreateNamedPipe wrapper. Tests inject kernel32; production uses ctypes."""

    def __init__(self, user_sid: str, session_id: str, kernel=None, pipe_name: str | None = None):
        self.user_sid = user_sid
        self.session_id = session_id
        self.kernel = kernel if kernel is not None else _load_kernel32()
        self.pipe_name = pipe_name or r'\\.\pipe\SafeBIMBridge'
        self.handle = None
        self.open_request: PipeOpenRequest | None = None
        self.gate = PipeApplicationGate()

    def open_server(self) -> PipeOpenRequest:
        if os.name != 'nt' and self.kernel is _UNSET:
            raise NamedPipeUnavailable('Windows Named Pipe is the primary transport; HTTP is not used')
        request = PipeOpenRequest(
            name=self.pipe_name,
            max_instances=MAX_PIPE_INSTANCES,
            sddl=sddl_for_user(self.user_sid),
            reject_remote=True,
        )
        handle = self.kernel.CreateNamedPipeW(
            request.name,
            PIPE_ACCESS_DUPLEX,
            PIPE_TYPE_MESSAGE | PIPE_READMODE_MESSAGE | PIPE_WAIT | PIPE_REJECT_REMOTE_CLIENTS,
            request.max_instances,
            65536,
            65536,
            0,
            request.sddl,
        )
        if handle in (None, INVALID_HANDLE_VALUE, ERROR_PIPE_BUSY):
            raise NamedPipeUnavailable('named pipe already owned or unavailable')
        self.handle = handle
        self.open_request = request
        return request

    def close(self) -> None:
        if self.handle is not None and hasattr(self.kernel, 'CloseHandle'):
            self.kernel.CloseHandle(self.handle)
        self.handle = None


_UNSET = object()


def _load_kernel32():
    if os.name != 'nt':
        return _UNSET
    import ctypes
    return ctypes.windll.kernel32


def production_transport(user_sid: str, session_id: str):
    """Primary local transport. Never returns an HTTP server."""
    if os.name != 'nt':
        raise NamedPipeUnavailable('SafeBIMBridge requires a Windows Named Pipe')
    pipe = WindowsNamedPipe(user_sid, session_id)
    pipe.open_server()
    return pipe
