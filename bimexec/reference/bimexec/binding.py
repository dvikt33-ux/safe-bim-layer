"""
BIMEXEC v1 — marker binding и fingerprint'ы.

Маркер — единственный механизм доказательства «этот GUID = этот BIMEXEC ID».
Ответ create не является доказательством (инвариант I4).
"""
from __future__ import annotations

import hashlib
import json
import secrets
from dataclasses import dataclass
from typing import Any

MARKER_PREFIX = "BX"
MARKER_SEP = ":"


# --- маркер -----------------------------------------------------------------


def make_nonce(nbytes: int = 6) -> str:
    """Случайный nonce. Должен быть записан в WAL ДО dispatch, иначе
    элемент от прошлого запуска невозможно будет отличить."""
    return secrets.token_hex(nbytes)


def make_marker(job_id: str, object_id: str, nonce: str) -> str:
    """Формат согласован с принятым P0: BX:<job>:<object-id>:<nonce>

    run_id в строку не входит: усыновление проверяется по mapping-записи,
    а префиксный поиск по object-id ловит дубли от других запусков.
    """
    return f"{MARKER_PREFIX}{MARKER_SEP}{job_id}{MARKER_SEP}{object_id}{MARKER_SEP}{nonce}"


def marker_prefix(job_id: str, object_id: str) -> str:
    """Поиск без nonce — детектит элементы от предыдущих UNKNOWN-запусков."""
    return f"{MARKER_PREFIX}{MARKER_SEP}{job_id}{MARKER_SEP}{object_id}{MARKER_SEP}"


def parse_marker(value: str | None) -> tuple[str, str, str] | None:
    if not value or not value.startswith(MARKER_PREFIX + MARKER_SEP):
        return None
    parts = value.split(MARKER_SEP)
    if len(parts) != 4:
        return None
    _, job_id, object_id, nonce = parts
    if not (job_id and object_id and nonce):
        return None
    return job_id, object_id, nonce


def match_exact(value: str | None, marker: str) -> bool:
    return value is not None and value == marker


def match_prefix(value: str | None, prefix: str) -> bool:
    return value is not None and value.startswith(prefix)


# --- fingerprint'ы ----------------------------------------------------------

# ДВА РАЗНЫХ механизма. Путать их нельзя:
#   identity — «тот ли это Archicad/проект». НЕ содержит счётчиков элементов,
#              иначе будет меняться от наших же мутаций.
#   state    — «не изменилась ли модель под нами». Проверяется на каждом шаге,
#              перебазируется с ожидаемой дельтой.


def identity_fingerprint(project_info: dict[str, Any], stories: list[dict[str, Any]]) -> str:
    """Кто это. Порт сюда НЕ входит — порт это адрес, а не идентичность."""
    payload = {
        "project_path": project_info.get("project_path"),
        "project_name": project_info.get("project_name"),
        "is_untitled": project_info.get("is_untitled"),
        "is_teamwork": project_info.get("is_teamwork"),
        "archicad_version": project_info.get("archicad_version"),
        "archicad_build": project_info.get("archicad_build"),
        "stories": [(s.get("name"), s.get("elevation")) for s in stories],
    }
    return _hash(payload)


def state_fingerprint(
    counts: dict[str, int], layer_state: dict[str, Any], guids: list[str] | None = None
) -> str:
    """Что в модели. Меняется нашими мутациями — это нормально, важна дельта.

    Состав намеренно дешёвый (1–2 read-вызова на шаг): счётчики по типам,
    состояние слоёв и МНОЖЕСТВО GUID. Он ловит добавление, удаление и
    откат пользователем (Ctrl+Z), но НЕ ловит геометрический дрифт
    (элемент подвинули). Геометрический дрифт ловится целевой перепроверкой
    host-элемента перед зависимой операцией — см. Executor._precheck.
    """
    return _hash(
        {"counts": counts, "layers": layer_state, "guids": sorted(guids or [])}
    )


def _hash(payload: Any) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:32]


# --- привязка к инстансу ----------------------------------------------------


@dataclass
class Binding:
    port: int                  # адрес, не идентичность
    identity: str              # identity_fingerprint
    project_info: dict[str, Any]
    stories: list[dict[str, Any]]

    def matches(self, project_info: dict[str, Any], stories: list[dict[str, Any]]) -> bool:
        return self.identity == identity_fingerprint(project_info, stories)


class BindingError(Exception):
    """Расхождение binding — всегда halt, никогда «наверное всё ещё тот же»."""


def assert_bindable(project_info: dict[str, Any]) -> None:
    """Отказ биндиться к проектам, идентичность которых нестабильна."""
    if project_info.get("is_untitled"):
        raise BindingError("refuse to bind: project is untitled (no stable project_path)")
    if project_info.get("is_teamwork"):
        raise BindingError("refuse to bind: Teamwork/BIMcloud out of scope for v1")
