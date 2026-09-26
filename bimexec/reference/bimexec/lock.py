"""
BIMEXEC v1 — process singleton + single-flight.

Инвариант I2: ровно одна мутация в полёте на весь Router, и ровно один
живой процесс Router. Без этого «после UNKNOWN запрещены мутации»
невыполнимо: параллельный HTTP-запрос или второй процесс просто не увидят
флага остановки.
"""
from __future__ import annotations

import os
import threading


class ProcessLockError(RuntimeError):
    pass


class ProcessLock:
    """Межпроцессный lock на файле (flock). Не наследуется через fork+exec
    ровно настолько, насколько нам нужно: второй процесс получит исключение."""

    def __init__(self, path: str) -> None:
        self.path = path
        self._fd: int | None = None

    def acquire(self) -> None:
        d = os.path.dirname(os.path.abspath(self.path))
        os.makedirs(d, exist_ok=True)
        self._fd = os.open(self.path, os.O_CREAT | os.O_RDWR, 0o644)
        try:
            if os.name == "nt":
                # msvcrt.locking locks a byte starting at the current offset.
                # Keep the descriptor open for the lifetime of the Router.
                import msvcrt

                os.lseek(self._fd, 0, os.SEEK_SET)
                os.write(self._fd, b"0")
                os.lseek(self._fd, 0, os.SEEK_SET)
                msvcrt.locking(self._fd, msvcrt.LK_NBLCK, 1)
            else:
                import fcntl  # POSIX

                fcntl.flock(self._fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as e:
            os.close(self._fd)
            self._fd = None
            raise ProcessLockError(
                f"another Router instance holds {self.path}; refusing to start"
            ) from e
        os.ftruncate(self._fd, 0)
        os.write(self._fd, str(os.getpid()).encode())

    def release(self) -> None:
        if self._fd is not None:
            try:
                if os.name == "nt":
                    import msvcrt

                    os.lseek(self._fd, 0, os.SEEK_SET)
                    msvcrt.locking(self._fd, msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(self._fd, fcntl.LOCK_UN)
            finally:
                os.close(self._fd)
                self._fd = None

    def __enter__(self) -> "ProcessLock":
        self.acquire()
        return self

    def __exit__(self, *exc) -> None:
        self.release()


class SingleFlight:
    """Одна мутация в полёте. Побочный выигрыш: при крахе не более одной
    операции остаётся в UNKNOWN — recovery становится тривиальным."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._busy = False
        self._owner: str | None = None

    @property
    def busy(self) -> bool:
        return self._busy

    def acquire(self, who: str) -> None:
        if not self._lock.acquire(blocking=False):  # pragma: no cover
            raise ProcessLockError("single-flight lock contended")
        try:
            if self._busy:
                raise ProcessLockError(
                    f"a mutation is already in flight ({self._owner}); refusing {who}"
                )
            self._busy = True
            self._owner = who
        finally:
            self._lock.release()

    def release(self) -> None:
        self._busy = False
        self._owner = None

    def __enter__(self) -> None:
        # имя берётся из acquire(); здесь только для симметрии
        pass

    def __exit__(self, *exc) -> None:
        self.release()
