"""
BIMEXEC v1 — durable journal (WAL).

Правило, ради которого существует этот файл (инвариант I1):
    запись о намерении должна быть на диске ДО того, как мутация уйдёт в Archicad.

Формат: append-only JSONL, одна строка = одно событие, fsync после каждой записи.
Последняя неполная строка (крах во время записи) считается оторванной и
отбрасывается при открытии.
"""
from __future__ import annotations

import json
import os
from typing import Any, Iterator

# --- типы событий -----------------------------------------------------------

JOB_CREATED = "JOB_CREATED"
JOB_STATE = "JOB_STATE"
PKG_STATE = "PKG_STATE"

OP_INTENT = "OP_INTENT"          # ДО dispatch (fsync обязателен)
OP_OUTCOME = "OP_OUTCOME"        # исход вызова create
MARKER_INTENT = "MARKER_INTENT"  # ДО записи маркера
MARKER_RESULT = "MARKER_RESULT"  # исход записи + round-trip
OP_VERDICT = "OP_VERDICT"        # вердикт верификации
OP_COMMIT = "OP_COMMIT"          # фиксация операции
OP_DECISION = "OP_DECISION"      # решение человека при recovery
FINGERPRINT = "FINGERPRINT"      # перебазирование state fingerprint
ORPHAN = "ORPHAN"                # элемент создан, но не подтверждён


class Journal:
    def __init__(self, path: str) -> None:
        self.path = path
        self._f = None
        self._seq = 0
        self._last_line_was_torn = False

    # -- жизненный цикл ------------------------------------------------------

    def open(self) -> "Journal":
        d = os.path.dirname(os.path.abspath(self.path))
        os.makedirs(d, exist_ok=True)
        self._truncate_torn()
        self._f = open(self.path, "a", encoding="utf-8")
        return self

    def close(self) -> None:
        if self._f is not None:
            self._f.close()
            self._f = None

    def __enter__(self) -> "Journal":
        return self.open()

    def __exit__(self, *exc) -> None:
        self.close()

    # -- запись --------------------------------------------------------------

    @property
    def seq(self) -> int:
        return self._seq

    def append(self, event: dict[str, Any]) -> int:
        """Пишет событие, fsync, возвращает присвоенный seq."""
        if self._f is None:
            raise RuntimeError("journal is not open")
        self._seq += 1
        payload = dict(event)
        payload["seq"] = self._seq
        line = json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n"
        self._f.write(line)
        self._f.flush()
        os.fsync(self._f.fileno())  # I1: intent должен пережить kill -9
        return self._seq

    # -- чтение --------------------------------------------------------------

    def read_all(self) -> list[dict[str, Any]]:
        if not os.path.exists(self.path):
            return []
        out: list[dict[str, Any]] = []
        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    # оторванная запись в середине файла — не молчим
                    raise
        return out

    def events(self, *kinds: str) -> Iterator[dict[str, Any]]:
        for e in self.read_all():
            if e.get("kind") in kinds:
                yield e

    # -- внутреннее ----------------------------------------------------------

    def _truncate_torn(self) -> None:
        """Отбрасывает хвост без завершающего '\\n' (крах во время append)."""
        if not os.path.exists(self.path):
            return
        with open(self.path, "rb") as f:
            data = f.read()
        if not data:
            return
        if data.endswith(b"\n"):
            complete = data
            self._last_line_was_torn = False
        else:
            cut = data.rfind(b"\n")
            complete = data[: cut + 1] if cut != -1 else b""
            self._last_line_was_torn = True
        if len(complete) != len(data):
            tmp = self.path + ".tmp"
            with open(tmp, "wb") as f:
                f.write(complete)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, self.path)
        # seq = числу полных записей
        self._seq = complete.count(b"\n")


# --- атомарный snapshot состояния -------------------------------------------


def write_snapshot(path: str, obj: Any) -> None:
    """Атомарная запись состояния: tmp + fsync + os.replace."""
    d = os.path.dirname(os.path.abspath(path))
    os.makedirs(d, exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, sort_keys=True, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
    # fsync каталога, чтобы переименование тоже пережило крах
    try:
        dirfd = os.open(d or ".", os.O_RDONLY)
        try:
            os.fsync(dirfd)
        finally:
            os.close(dirfd)
    except OSError:
        pass


def read_snapshot(path: str) -> Any | None:
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
