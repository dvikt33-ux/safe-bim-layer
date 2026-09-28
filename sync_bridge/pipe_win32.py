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
ERROR_INVALID_HANDLE = 6
INVALID_HANDLE_VALUE = -1
MAX_PIPE_INSTANCES = 8
PIPE_VERIFICATION = 'OFFLINE_CONTRACT_VERIFIED'
MULTIPLEX_MODEL = 'single-bridge'


class NamedPipeUnavailable(RuntimeError):
    def __init__(self, message: str, *, win32_error: int | None = None, stage: str = 'open'):
        super().__init__(message)
        self.win32_error = win32_error
        self.stage = stage


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
            raise NamedPipeUnavailable('Windows Named Pipe is the primary transport; HTTP is not used', stage='platform')
        request = PipeOpenRequest(
            name=self.pipe_name,
            max_instances=MAX_PIPE_INSTANCES,
            sddl=sddl_for_user(self.user_sid),
            reject_remote=True,
        )
        security_descriptor = None
        local_free = None
        security_attributes = request.sddl

        try:
            if _is_ctypes_kernel(self.kernel):
                import ctypes

                security_attributes, security_descriptor, local_free = (
                    _security_attributes_from_sddl(request.sddl)
                )
                security_arg = ctypes.byref(security_attributes)
            else:
                # Injected kernels receive the SDDL directly so offline tests
                # can inspect the intended security policy.
                security_arg = security_attributes

            handle = self.kernel.CreateNamedPipeW(
                request.name,
                PIPE_ACCESS_DUPLEX,
                PIPE_TYPE_MESSAGE | PIPE_READMODE_MESSAGE | PIPE_WAIT | PIPE_REJECT_REMOTE_CLIENTS,
                request.max_instances,
                65536,
                65536,
                0,
                security_arg,
            )
        finally:
            if security_descriptor is not None and local_free is not None:
                local_free(security_descriptor)
        if handle in (None, INVALID_HANDLE_VALUE, ERROR_PIPE_BUSY) or _is_invalid_handle(handle):
            error = _last_error(self.kernel)
            detail = 'named pipe already owned or unavailable'
            if error is not None:
                detail += f' (Win32 error {error})'
            raise NamedPipeUnavailable(detail, win32_error=error, stage='CreateNamedPipeW')
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
    from ctypes import wintypes
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateNamedPipeW.argtypes = [
        wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.DWORD,
        wintypes.DWORD, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p,
    ]
    kernel.CreateNamedPipeW.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    return kernel



def _security_attributes_from_sddl(sddl: str):
    """Build LPSECURITY_ATTRIBUTES from SDDL for CreateNamedPipeW."""
    if os.name != 'nt':
        raise NamedPipeUnavailable(
            'security descriptor conversion requires Windows',
            stage='security-platform',
        )

    import ctypes
    from ctypes import wintypes

    SDDL_REVISION_1 = 1

    class SECURITY_ATTRIBUTES(ctypes.Structure):
        _fields_ = [
            ('nLength', wintypes.DWORD),
            ('lpSecurityDescriptor', ctypes.c_void_p),
            ('bInheritHandle', wintypes.BOOL),
        ]

    advapi32 = ctypes.WinDLL('advapi32', use_last_error=True)
    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

    convert = advapi32.ConvertStringSecurityDescriptorToSecurityDescriptorW
    convert.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.POINTER(wintypes.DWORD),
    ]
    convert.restype = wintypes.BOOL

    local_free = kernel32.LocalFree
    local_free.argtypes = [ctypes.c_void_p]
    local_free.restype = ctypes.c_void_p

    descriptor = ctypes.c_void_p()
    descriptor_size = wintypes.DWORD(0)

    if not convert(
        sddl,
        SDDL_REVISION_1,
        ctypes.byref(descriptor),
        ctypes.byref(descriptor_size),
    ):
        error = ctypes.get_last_error()
        raise NamedPipeUnavailable(
            f'cannot create pipe security descriptor (Win32 error {error})',
            win32_error=error,
            stage='ConvertStringSecurityDescriptorToSecurityDescriptorW',
        )

    attributes = SECURITY_ATTRIBUTES(
        ctypes.sizeof(SECURITY_ATTRIBUTES),
        descriptor.value,
        False,
    )
    return attributes, descriptor, local_free



def _last_error(kernel) -> int | None:
    try:
        import ctypes
        return ctypes.get_last_error()
    except (AttributeError, OSError):
        getter = getattr(kernel, 'GetLastError', None)
        return getter() if getter else None


def _is_invalid_handle(handle) -> bool:
    """ctypes may expose INVALID_HANDLE_VALUE as an unsigned 64-bit integer."""
    try:
        return int(handle) == (2**64 - 1)
    except (TypeError, ValueError):
        return False


def _is_ctypes_kernel(kernel) -> bool:
    return type(kernel).__module__ == 'ctypes'


def production_transport(user_sid: str, session_id: str):
    """Primary local transport. Never returns an HTTP server."""
    if os.name != 'nt':
        raise NamedPipeUnavailable('SafeBIMBridge requires a Windows Named Pipe')
    pipe = WindowsNamedPipe(user_sid, session_id)
    pipe.open_server()
    return pipe
