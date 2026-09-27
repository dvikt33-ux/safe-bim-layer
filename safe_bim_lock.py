"""Nonblocking, crash-released execution exclusion for one canonical SQLite DB.

The OS lock spans admission through readback/transitions, NOT a SQLite transaction.
Pause/Stop can still commit. Both process and thread exclusion are required.
"""
from contextlib import contextmanager
from pathlib import Path
import os
import threading

_registry_guard = threading.Lock()
_registry = {}


@contextmanager
def execution_lock(database):
    key = os.path.normcase(str(Path(database).resolve()))
    with _registry_guard:
        lock = _registry.setdefault(key, threading.Lock())
    if not lock.acquire(blocking=False):
        yield False
        return
    handle = None
    owned = False
    try:
        handle = open(key + '.execution.lock', 'a+b')
        if os.fstat(handle.fileno()).st_size == 0:
            handle.write(b'\0')
            handle.flush()
        handle.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            owned = True
        except (BlockingIOError, OSError):
            pass
        yield owned
    finally:
        if handle is not None:
            if owned:
                handle.seek(0)
                if os.name == 'nt':
                    import msvcrt
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            handle.close()
        lock.release()
