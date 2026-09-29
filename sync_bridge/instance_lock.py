"""Per-user single-instance ownership.

The Windows production gate is a named mutex (`CreateMutexW` /
`WaitForSingleObject` / `ReleaseMutex`).

A Win32 mutex is recursive for the owning thread. Therefore a second
SafeBIMBridge created inside the same Python process/thread could otherwise
re-acquire the same named mutex. A process-local registry closes that gap.

SQLite lease rows are diagnostic session metadata only: they record
the token, expiry, and heartbeat. They are not proof that this process owns
the bridge.
"""
from __future__ import annotations

import os
import threading

ERROR_ALREADY_EXISTS = 183
WAIT_OBJECT_0 = 0x00000000
WAIT_ABANDONED = 0x00000080
WAIT_TIMEOUT = 0x00000102
INVALID_HANDLE_VALUE = -1

MUTEX_VERIFICATION = 'OFFLINE_CONTRACT_VERIFIED'
SQLITE_LEASE_ROLE = 'DIAGNOSTIC_ONLY'
OWNERSHIP_GATE = 'NAMED_MUTEX'

_PROCESS_LOCK = threading.RLock()
_PROCESS_OWNED_NAMES: set[str] = set()


def mutex_name(user_sid: str) -> str:
    return 'Local\\SafeBIMBridge-' + user_sid


def _process_try_claim(name: str) -> bool:
    """Prevent recursive duplicate ownership inside this Python process."""
    with _PROCESS_LOCK:
        if name in _PROCESS_OWNED_NAMES:
            return False
        _PROCESS_OWNED_NAMES.add(name)
        return True


def _process_release(name: str) -> None:
    with _PROCESS_LOCK:
        _PROCESS_OWNED_NAMES.discard(name)


class InProcessMutexKernel:
    """Offline kernel32 mutex table. One owner per name. Not a live mutex."""

    def __init__(self):
        self._by_name: dict[str, dict] = {}
        self._handles: dict[int, str] = {}
        self._next = 1
        self.last_error = 0
        self.calls: list[tuple] = []

    def CreateMutexW(self, security, initial_owner, name):
        self.calls.append(('CreateMutexW', name, bool(initial_owner)))
        handle = self._next
        self._next += 1
        entry = self._by_name.get(name)
        self._handles[handle] = name
        if entry is None or entry['state'] == 'free':
            self.last_error = 0
            self._by_name[name] = {'state': 'owned', 'owner_handle': handle}
            return handle
        self.last_error = ERROR_ALREADY_EXISTS
        return handle

    def GetLastError(self) -> int:
        return self.last_error

    def WaitForSingleObject(self, handle, timeout_ms):
        self.calls.append(('WaitForSingleObject', handle, timeout_ms))
        name = self._handles.get(handle)
        entry = self._by_name.get(name) if name else None
        if entry is None:
            return WAIT_TIMEOUT
        if entry['state'] == 'abandoned':
            entry['state'] = 'owned'
            entry['owner_handle'] = handle
            return WAIT_ABANDONED
        if entry['state'] == 'free':
            entry['state'] = 'owned'
            entry['owner_handle'] = handle
            return WAIT_OBJECT_0
        if entry.get('owner_handle') == handle:
            return WAIT_OBJECT_0
        return WAIT_TIMEOUT

    def ReleaseMutex(self, handle) -> bool:
        self.calls.append(('ReleaseMutex', handle))
        name = self._handles.get(handle)
        entry = self._by_name.get(name) if name else None
        if entry and entry.get('owner_handle') == handle and entry['state'] == 'owned':
            entry['state'] = 'free'
            entry['owner_handle'] = None
            return True
        return False

    def CloseHandle(self, handle) -> bool:
        self.calls.append(('CloseHandle', handle))
        name = self._handles.pop(handle, None)
        if name is None:
            return True
        entry = self._by_name.get(name)
        if entry and entry.get('owner_handle') == handle and entry['state'] == 'owned':
            # Closed without ReleaseMutex: the owning process is gone.
            entry['state'] = 'abandoned'
            entry['owner_handle'] = None
        return True

    def owns(self, handle) -> bool:
        name = self._handles.get(handle)
        entry = self._by_name.get(name) if name else None
        return bool(entry and entry['state'] == 'owned' and entry.get('owner_handle') == handle)

    def release_all(self) -> None:
        for entry in self._by_name.values():
            entry['state'] = 'free'
            entry['owner_handle'] = None
        self._handles.clear()


_DEFAULT_KERNEL = InProcessMutexKernel()


def default_kernel() -> InProcessMutexKernel:
    return _DEFAULT_KERNEL


class Kernel32MutexKernel:
    """Real kernel32 mutex. Used when os.name == 'nt'."""

    def __init__(self):
        import ctypes
        from ctypes import wintypes
        self._kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        self._kernel.CreateMutexW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
        self._kernel.CreateMutexW.restype = wintypes.HANDLE
        self._kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        self._kernel.WaitForSingleObject.restype = wintypes.DWORD
        self._kernel.ReleaseMutex.argtypes = [wintypes.HANDLE]
        self._kernel.ReleaseMutex.restype = wintypes.BOOL
        self._kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        self._kernel.CloseHandle.restype = wintypes.BOOL
        self._owned: set[int] = set()
        self.calls: list[tuple] = []

    def CreateMutexW(self, security, initial_owner, name):
        self.calls.append(('CreateMutexW', name, bool(initial_owner)))
        handle = self._kernel.CreateMutexW(None, bool(initial_owner), name)
        if not handle:
            return INVALID_HANDLE_VALUE
        if ctypes_last_error_is_fresh_owner():
            self._owned.add(int(handle))
        return handle

    def GetLastError(self) -> int:
        import ctypes
        return ctypes.get_last_error()

    def WaitForSingleObject(self, handle, timeout_ms):
        self.calls.append(('WaitForSingleObject', handle, timeout_ms))
        waited = self._kernel.WaitForSingleObject(handle, timeout_ms)
        if waited in (WAIT_OBJECT_0, WAIT_ABANDONED):
            self._owned.add(int(handle))
        return waited

    def ReleaseMutex(self, handle) -> bool:
        self.calls.append(('ReleaseMutex', handle))
        released = bool(self._kernel.ReleaseMutex(handle))
        if released:
            self._owned.discard(int(handle))
        return released

    def CloseHandle(self, handle) -> bool:
        self.calls.append(('CloseHandle', handle))
        closed = bool(self._kernel.CloseHandle(handle))
        self._owned.discard(int(handle))
        return closed

    def owns(self, handle) -> bool:
        return int(handle) in self._owned

    def release_all(self) -> None:
        for handle in list(self._owned):
            self.ReleaseMutex(handle)
            self.CloseHandle(handle)


def ctypes_last_error_is_fresh_owner() -> bool:
    import ctypes
    return ctypes.get_last_error() != ERROR_ALREADY_EXISTS


def select_kernel():
    """Windows uses kernel32. Other hosts use the offline stand-in."""
    if os.name == 'nt':
        return Kernel32MutexKernel()
    return default_kernel()


class SingleInstanceLock:
    """Hold the per-user named mutex for the lifetime of one bridge."""

    def __init__(self, user_sid: str, kernel=None):
        self.name = mutex_name(user_sid)
        self.kernel = kernel if kernel is not None else select_kernel()
        self.handle = None
        self.last_acquire = ''
        self._process_claimed = False

    def __del__(self) -> None:
        try:
            self.release()
        except Exception:
            return

    def try_acquire(self) -> str:
        if self.held():
            self.last_acquire = 'acquired'
            return 'acquired'

        # Win32 mutexes are recursive for the owning thread. Reject a second
        # bridge object in this Python process before touching the kernel mutex.
        if not _process_try_claim(self.name):
            self.last_acquire = 'blocked'
            return 'blocked'
        self._process_claimed = True

        handle = None
        try:
            handle = self.kernel.CreateMutexW(None, True, self.name)
            if handle in (None, INVALID_HANDLE_VALUE):
                self._drop_process_claim()
                self.last_acquire = 'blocked'
                return 'blocked'

            if self.kernel.GetLastError() == ERROR_ALREADY_EXISTS:
                waited = self.kernel.WaitForSingleObject(handle, 0)
                if waited == WAIT_TIMEOUT:
                    self.kernel.CloseHandle(handle)
                    self._drop_process_claim()
                    self.last_acquire = 'blocked'
                    return 'blocked'
                if waited == WAIT_ABANDONED:
                    self.handle = handle
                    self.last_acquire = 'abandoned'
                    return 'abandoned'
                if waited == WAIT_OBJECT_0:
                    self.handle = handle
                    self.last_acquire = 'acquired'
                    return 'acquired'
                self.kernel.CloseHandle(handle)
                self._drop_process_claim()
                self.last_acquire = 'blocked'
                return 'blocked'

            self.handle = handle
            self.last_acquire = 'acquired'
            return 'acquired'
        except BaseException:
            if handle is not None and handle != INVALID_HANDLE_VALUE:
                try:
                    self.kernel.CloseHandle(handle)
                except Exception:
                    pass
            self._drop_process_claim()
            raise

    def held(self) -> bool:
        return self.handle is not None and bool(self.kernel.owns(self.handle))

    def release(self) -> None:
        if self.handle is None:
            self._drop_process_claim()
            return
        try:
            if self.held():
                self.kernel.ReleaseMutex(self.handle)
            self.kernel.CloseHandle(self.handle)
        finally:
            self.handle = None
            self._drop_process_claim()

    def abandon(self) -> None:
        """Simulate owner death without ReleaseMutex."""
        if self.handle is None:
            self._drop_process_claim()
            return
        try:
            self.kernel.CloseHandle(self.handle)
        finally:
            self.handle = None
            self._drop_process_claim()

    def _drop_process_claim(self) -> None:
        if not self._process_claimed:
            return
        _process_release(self.name)
        self._process_claimed = False
