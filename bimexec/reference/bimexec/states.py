"""
BIMEXEC v1 — машины состояний.

Ключевое свойство: недопустимый переход — это исключение, а не предупреждение.
Система обязана падать (fail closed), а не «продолжить с неожиданным состоянием».
"""
from __future__ import annotations

from enum import Enum
from typing import Iterable


class TransitionError(RuntimeError):
    pass


class JobState(str, Enum):
    CREATED = "CREATED"
    VALIDATING = "VALIDATING"
    REJECTED = "REJECTED"
    BINDING = "BINDING"
    BOUND = "BOUND"
    READY = "READY"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    RECONCILING = "RECONCILING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    QUARANTINED = "QUARANTINED"
    ABORTED = "ABORTED"

    def terminal(self) -> bool:
        return self in {
            JobState.REJECTED,
            JobState.COMPLETED,
            JobState.FAILED,
            JobState.QUARANTINED,
            JobState.ABORTED,
        }


class PkgState(str, Enum):
    PENDING = "PENDING"
    BLOCKED = "BLOCKED"
    READY = "READY"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    HALTED = "HALTED"
    SKIPPED_DEP = "SKIPPED_DEP"
    PRECHECK_FAILED = "PRECHECK_FAILED"

    def satisfied(self) -> bool:
        """Только COMPLETED удовлетворяет зависимость. PARTIAL — нет (инвариант I7)."""
        return self is PkgState.COMPLETED


class OpState(str, Enum):
    PLANNED = "PLANNED"
    PRECHECK_FAILED = "PRECHECK_FAILED"
    DISPATCHED = "DISPATCHED"

    APPLIED_UNVERIFIED = "APPLIED_UNVERIFIED"   # create ответил успешно; GUID = CANDIDATE
    MARKER_WRITING = "MARKER_WRITING"
    MARKER_UNKNOWN = "MARKER_UNKNOWN"
    BOUND = "BOUND"                             # round-trip маркера доказан

    VERIFIED_OK = "VERIFIED_OK"
    VERIFIED_FAILED = "VERIFIED_FAILED"
    INCONCLUSIVE = "INCONCLUSIVE"
    UNAVAILABLE = "UNAVAILABLE"
    UNSUPPORTED = "UNSUPPORTED"

    CREATED_UNBOUND = "CREATED_UNBOUND"         # элемент есть, привязка недоказуема
    UNKNOWN = "UNKNOWN"                         # dispatch без известного исхода
    ADOPTED = "ADOPTED"                         # найден по маркеру/якорю, мутации не было
    NOT_APPLIED_ASSERTED = "NOT_APPLIED_ASSERTED"  # доказано ТОЛЬКО реконсиляцией
    SKIPPED = "SKIPPED"

    def halts_job(self) -> bool:
        """Любое из этих состояний останавливает все мутации в job (инвариант I3)."""
        return self in {
            OpState.UNKNOWN,
            OpState.MARKER_UNKNOWN,
            OpState.CREATED_UNBOUND,
            OpState.VERIFIED_FAILED,
            OpState.INCONCLUSIVE,
            OpState.UNAVAILABLE,
            OpState.UNSUPPORTED,
            OpState.PRECHECK_FAILED,
        }

    def terminal(self) -> bool:
        return self in {
            OpState.VERIFIED_OK,
            OpState.ADOPTED,
            OpState.SKIPPED,
            OpState.NOT_APPLIED_ASSERTED,
            OpState.PRECHECK_FAILED,
        }

    def counts_as_success(self) -> bool:
        return self in {OpState.VERIFIED_OK, OpState.ADOPTED, OpState.SKIPPED}


class MapState(str, Enum):
    UNBOUND = "UNBOUND"
    CANDIDATE = "CANDIDATE"          # GUID из create-response, НЕ доверенный
    MARKER_PENDING = "MARKER_PENDING"
    CONFIRMED = "CONFIRMED"
    ADOPTED = "ADOPTED"
    CREATED_UNBOUND = "CREATED_UNBOUND"
    STALE = "STALE"
    ORPHAN = "ORPHAN"

    def readable(self) -> bool:
        """Только эти состояния видны другим операциям (инвариант I9)."""
        return self in {MapState.CONFIRMED, MapState.ADOPTED}


# --- таблицы переходов ------------------------------------------------------

JOB_TRANSITIONS: dict[JobState, set[JobState]] = {
    JobState.CREATED: {JobState.VALIDATING, JobState.REJECTED, JobState.ABORTED},
    JobState.VALIDATING: {JobState.BINDING, JobState.REJECTED, JobState.ABORTED},
    JobState.BINDING: {JobState.BOUND, JobState.REJECTED, JobState.ABORTED},
    JobState.BOUND: {JobState.READY, JobState.ABORTED},
    JobState.READY: {JobState.RUNNING, JobState.ABORTED},
    JobState.RUNNING: {JobState.PAUSED, JobState.COMPLETED, JobState.ABORTED},
    JobState.PAUSED: {JobState.RECONCILING, JobState.ABORTED, JobState.QUARANTINED},
    JobState.RECONCILING: {
        JobState.BOUND,       # re-bind после INSTANCE_MISMATCH
        JobState.READY,       # человек разрешил продолжить
        JobState.FAILED,
        JobState.QUARANTINED,
        JobState.ABORTED,
    },
}

PKG_TRANSITIONS: dict[PkgState, set[PkgState]] = {
    PkgState.PENDING: {PkgState.BLOCKED, PkgState.READY, PkgState.SKIPPED_DEP},
    PkgState.BLOCKED: {PkgState.READY, PkgState.SKIPPED_DEP},
    PkgState.READY: {PkgState.RUNNING, PkgState.PRECHECK_FAILED, PkgState.HALTED},
    # PARTIAL/HALTED — «пакет остановлен посередине»; после решения человека
    # по неразрешённой операции resume доигрывает его
    PkgState.PARTIAL: {PkgState.READY, PkgState.RUNNING, PkgState.HALTED},
    PkgState.HALTED: {PkgState.READY, PkgState.RUNNING, PkgState.HALTED},
    PkgState.RUNNING: {
        PkgState.COMPLETED,
        PkgState.PARTIAL,
        PkgState.HALTED,
        PkgState.PRECHECK_FAILED,
    },
}

OP_TRANSITIONS: dict[OpState, set[OpState]] = {
    OpState.PLANNED: {
        OpState.DISPATCHED,
        OpState.ADOPTED,
        OpState.PRECHECK_FAILED,
        OpState.SKIPPED,
    },
    OpState.DISPATCHED: {OpState.APPLIED_UNVERIFIED, OpState.UNKNOWN, OpState.ADOPTED},
    OpState.APPLIED_UNVERIFIED: {
        OpState.MARKER_WRITING,
        OpState.CREATED_UNBOUND,   # tag-guard не прошёл
        OpState.UNKNOWN,
    },
    OpState.MARKER_WRITING: {OpState.BOUND, OpState.MARKER_UNKNOWN, OpState.CREATED_UNBOUND},
    OpState.MARKER_UNKNOWN: {OpState.BOUND, OpState.CREATED_UNBOUND, OpState.ADOPTED},
    OpState.BOUND: {
        OpState.VERIFIED_OK,
        OpState.VERIFIED_FAILED,
        OpState.INCONCLUSIVE,
        OpState.UNAVAILABLE,
        OpState.UNSUPPORTED,
    },
    # из любого «плохого» состояния — только по решению человека
    OpState.UNKNOWN: {OpState.ADOPTED, OpState.NOT_APPLIED_ASSERTED},
    OpState.CREATED_UNBOUND: {OpState.ADOPTED},
    OpState.MARKER_UNKNOWN: {OpState.BOUND, OpState.CREATED_UNBOUND},
}

MAP_TRANSITIONS: dict[MapState, set[MapState]] = {
    MapState.UNBOUND: {MapState.CANDIDATE, MapState.ADOPTED, MapState.CREATED_UNBOUND},
    MapState.CANDIDATE: {MapState.MARKER_PENDING, MapState.CREATED_UNBOUND, MapState.STALE},
    MapState.MARKER_PENDING: {MapState.CONFIRMED, MapState.CREATED_UNBOUND},
    MapState.CONFIRMED: {MapState.STALE, MapState.ORPHAN},
    MapState.ADOPTED: {MapState.STALE, MapState.ORPHAN},
    MapState.CREATED_UNBOUND: {MapState.CONFIRMED, MapState.ADOPTED, MapState.ORPHAN},
    MapState.STALE: {MapState.ORPHAN},
}


def can(table: dict, cur: Enum, nxt: Enum) -> bool:
    return nxt in table.get(cur, set())


def must(table: dict, cur: Enum, nxt: Enum) -> Enum:
    """Fail closed: недопустимый переход — исключение, а не молчаливый пропуск."""
    if not can(table, cur, nxt):
        raise TransitionError(
            f"illegal transition {type(cur).__name__}: {cur.value} -> {nxt.value}"
        )
    return nxt


def job_to(cur: JobState, nxt: JobState) -> JobState:
    return must(JOB_TRANSITIONS, cur, nxt)


def pkg_to(cur: PkgState, nxt: PkgState) -> PkgState:
    return must(PKG_TRANSITIONS, cur, nxt)


def op_to(cur: OpState, nxt: OpState) -> OpState:
    return must(OP_TRANSITIONS, cur, nxt)


def map_to(cur: MapState, nxt: MapState) -> MapState:
    return must(MAP_TRANSITIONS, cur, nxt)


def halting_states(states: Iterable[OpState]) -> list[OpState]:
    return [s for s in states if s.halts_job()]
