"""
BIMEXEC v1 — тесты P0.

Гоняются без внешних зависимостей:  python tests/test_p0.py
(структура совместима с pytest).

Имитация адаптера воспроизводит задокументированные классы отказов,
а не «сферический Archicad»: E2, E3, AC29-read-broken, чужой GUID из create,
таймаут после применения, дубль от прошлого запуска.
"""
from __future__ import annotations

import copy
import os
import sys
import tempfile
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reference"))

from bimexec.adapters import FakeAdapter, FakeArchicad, Faults
from bimexec.binding import make_marker
from bimexec.executor import Executor
from bimexec.journal import Journal
from bimexec.lock import ProcessLock, ProcessLockError
from bimexec.states import JobState, MapState, OpState, PkgState, TransitionError
from bimexec.verify import Capability, CapabilityMatrix, PlanRejected

PROJECT = {
    "port": 19723,
    "project_path": "/pln/sandbox.pln",
    "project_name": "SANDBOX",
    "is_untitled": False,
    "is_teamwork": False,
    "archicad_version": "29",
    "archicad_build": "29.0.0",
}
STORIES = [{"name": "Ground Floor", "elevation": 0.0}]

KEY = "PKG01/W_F1_EXT_001"


# --- helpers ----------------------------------------------------------------


def cap_matrix(production_safe: bool = True, drop_fields: set[str] | None = None) -> CapabilityMatrix:
    fields = {
        "exists", "type", "story", "layer", "marker_exact",
        "ref_line", "length", "height", "thickness", "angle", "count_delta",
    } - (drop_fields or set())
    m = CapabilityMatrix()
    m.add(
        Capability(
            op="create_wall",
            exec_backend="BIBIM",
            readback_backends=["GetDetailsOfElements", "GetElementsByType", "PropertyAPI"],
            readable_fields=fields,
            marker_medium="element_id",
            marker_search_exact=True,
            marker_search_prefix=True,
            count_by_type=True,
            production_safe=production_safe,
            probe_certified=production_safe,
            duplicate_detection="PREFIX",
            adapter_version="test",
        )
    )
    return m


def verify_block(**over) -> dict:
    v = {
        "type": "Wall",
        "story": {"name": "Ground Floor", "elevation": 0.0},
        "layer": "A-WALL",
        "marker_exact": True,
        "ref_line": {"from": [1.5, 2.5], "to": [6.5, 2.5], "tolerance": 0.01},
        "length": {"expected": 5.0, "tolerance": 0.05},
        "height": {"expected": 3.0, "tolerance": 0.001},
        "thickness": {"expected": 0.30, "tolerance": 0.001},
        "count_delta": {"Wall": 1},
    }
    v.update(over)
    return v


def wall_op(oid: str = "W_F1_EXT_001", frm=(1.5, 2.5), to=(6.5, 2.5), **over) -> dict:
    op = {
        "op": "create_wall",
        "id": oid,
        "story": {"name": "Ground Floor", "elevation": 0.0},
        "layer": "A-WALL",
        "from": list(frm),
        "to": list(to),
        "height": 3.0,
        "thickness": 0.30,
        "reference_line": "center",
        "base_level": 0.0,
        "top_link": "absolute",
        "verify": verify_block(),
    }
    op.update(over)
    return op


def plan(packages=None, job: str = "HOUSE_001") -> dict:
    if packages is None:
        packages = [{"id": "PKG01", "type": "walls", "depends_on": [], "operations": [wall_op()]}]
    return {
        "bimexec": 1,
        "schema_version": "1.0",
        "job": job,
        "mode": "strict",
        "units": {"length": "m", "angle": "deg"},
        "origin": "project",
        "packages": packages,
    }


def make(faults: Faults | None = None, matrix: CapabilityMatrix | None = None, seed=None):
    d = tempfile.mkdtemp()
    ac = FakeArchicad(PROJECT, STORIES)
    if seed:
        seed(ac)
    ad = FakeAdapter(ac, faults or Faults())
    ex = Executor(
        ad,
        matrix or cap_matrix(),
        os.path.join(d, "journal.jsonl"),
        lock_path=os.path.join(d, "router.lock"),
        write_gate=True,
    )
    ex.confirm_token = "tok"
    return ex, ac, d


def reopen(ac: FakeArchicad, d: str, faults: Faults | None = None,
           matrix: CapabilityMatrix | None = None) -> Executor:
    """Имитация рестарта Router на той же директории journal."""
    ex = Executor(
        FakeAdapter(ac, faults or Faults()),
        matrix or cap_matrix(),
        os.path.join(d, "journal.jsonl"),
        lock_path=os.path.join(d, "router.lock"),
        write_gate=True,
    )
    ex.confirm_token = "tok"
    return ex


# --- мини-раннер ------------------------------------------------------------

TESTS: list[tuple[str, object]] = []


def test(fn):
    TESTS.append((fn.__name__, fn))
    return fn


# ==== A. Валидация отбрасывает до dispatch ==================================


@test
def validation_rejects_empty_verify():
    p = plan()
    p["packages"][0]["operations"][0].pop("verify")
    ex, ac, d = make()
    try:
        ex.submit(p)
    except PlanRejected as e:
        assert "verify_spec is missing or empty" in str(e)
        assert len(ac.elements) == 0
        return
    raise AssertionError("empty verify must be rejected")


@test
def validation_rejects_narrowed_floor():
    """План не вправе сужать обязательный минимум: это минимум из конфига Router."""
    p = plan()
    p["packages"][0]["operations"][0]["verify"] = {"type": "Wall", "height": {"expected": 3.0}}
    ex, ac, d = make()
    try:
        ex.submit(p)
    except PlanRejected as e:
        assert "narrows mandatory floor" in str(e)
        return
    raise AssertionError("narrowed verify must be rejected")


@test
def validation_rejects_verify_contradicting_params():
    p = plan()
    p["packages"][0]["operations"][0]["verify"]["height"] = {"expected": 30.0}
    ex, ac, d = make()
    try:
        ex.submit(p)
    except PlanRejected as e:
        assert "contradicts" in str(e)
        return
    raise AssertionError("contradiction between verify and params must be rejected")


@test
def validation_rejects_unsupported_check():
    """Capability gating: нет read-back — отбрасываем на валидации, не в рантайме."""
    ex, ac, d = make(matrix=cap_matrix(drop_fields={"ref_line", "length"}))
    try:
        ex.submit(plan())
    except PlanRejected as e:
        assert "not backed by read-back capability" in str(e)
        return
    raise AssertionError("unsupported checks must be rejected at validation")


@test
def validation_rejects_forward_dependency():
    p = plan(
        packages=[
            {"id": "PKG01", "depends_on": ["PKG02"], "operations": [wall_op()]},
            {"id": "PKG02", "depends_on": [], "operations": [wall_op("W_002")]},
        ]
    )
    ex, ac, d = make()
    try:
        ex.submit(p)
    except PlanRejected as e:
        assert "not earlier in the array" in str(e)
        return
    raise AssertionError("forward deps (and cycles) must be rejected")


@test
def validation_rejects_freeform_fields():
    p = plan()
    p["packages"][0]["operations"][0]["script"] = "ac.create(...)"
    ex, ac, d = make()
    try:
        ex.submit(p)
    except PlanRejected as e:
        assert "forbidden free-form field" in str(e)
        return
    raise AssertionError("free-form fields from LLM must be rejected")


@test
def validation_rejects_non_production_safe_op():
    ex, ac, d = make(matrix=cap_matrix(production_safe=False))
    try:
        ex.submit(plan())
    except PlanRejected:
        return
    raise AssertionError("op not marked production-safe must be rejected")


# ==== B. Happy path и binding ===============================================


@test
def happy_path_single_wall():
    ex, ac, d = make()
    ex.submit(plan())
    st = ex.run()
    assert st is JobState.COMPLETED, (st, ex.paused_reason)
    rec = ex.job.ops[KEY]
    assert rec.state is OpState.VERIFIED_OK
    assert rec.map_state is MapState.CONFIRMED
    assert rec.mapping_method == "MARKER_ROUNDTRIP"
    assert len(ac.elements) == 1
    el = next(iter(ac.elements.values()))
    assert el.marker == rec.marker
    assert ex.orphans == []
    # маркер строково совпадает с ожидаемым форматом BX:<job>:<object-id>:<nonce>
    assert el.marker.startswith(f"BX:HOUSE_001:W_F1_EXT_001:")
    return ex, ac


@test
def journal_is_complete_and_monotonic():
    ex, ac, d = make()
    ex.submit(plan())
    ex.run()
    events = ex.journal.read_all()
    seqs = [e["seq"] for e in events]
    assert seqs == list(range(1, len(seqs) + 1)), "seq must have no gaps"
    kinds = [e["kind"] for e in events]
    for need in ("JOB_CREATED", "OP_INTENT", "OP_OUTCOME", "MARKER_INTENT", "MARKER_RESULT", "OP_COMMIT"):
        assert need in kinds, need
    # INTENT обязан идти РАНЬШЕ OUTCOME (иначе UNKNOWN неотличим от «не отправляли»)
    assert kinds.index("OP_INTENT") < kinds.index("OP_OUTCOME")


@test
def write_gate_off_refuses_execution():
    ex, ac, d = make()
    ex.write_gate = False
    ex.submit(plan())
    try:
        ex.run()
    except RuntimeError as e:
        assert "WriteGate" in str(e)
        assert len(ac.elements) == 0
        return
    raise AssertionError("execution must be refused while WriteGate is OFF")


# ==== C. Классы отказов, подтверждённые практикой API =======================


@test
def create_applied_but_timeout_then_recovery():
    """T3: kill/таймаут между dispatch и ответом. Никаких автоповторов."""
    ex, ac, d = make(Faults(create_applied_but_timeout=True))
    ex.submit(plan())
    st = ex.run()
    assert st is JobState.PAUSED and ex.paused_reason == "OP_UNKNOWN"
    assert len(ac.elements) == 1, "мутация применилась, хотя ответа не было"

    # рестарт Router
    ex2 = reopen(ac, d)
    assert ex2.recover() is True
    rep = ex2.reconcile()
    cls = rep["ops"][KEY]["classification"]
    assert cls == "APPLIED_ADOPTABLE_BY_ANCHOR", cls

    ex2.resume({KEY: "adopt"})
    st2 = ex2.run()
    assert st2 is JobState.COMPLETED, (st2, ex2.paused_reason)
    assert len(ac.elements) == 1, "второй стены быть не должно"
    assert ex2.job.ops[KEY].map_state is MapState.ADOPTED


@test
def marker_write_unknown_is_own_failure_mode():
    """E2: SetPropertyValuesOfElements -> Permission Denied / нет ответа."""
    ex, ac, d = make(Faults(marker_write_unknown=True))
    ex.submit(plan())
    st = ex.run()
    assert st is JobState.PAUSED and ex.paused_reason == "MARKER_UNKNOWN"
    rec = ex.job.ops[KEY]
    assert rec.state is OpState.MARKER_UNKNOWN
    assert rec.map_state is MapState.CREATED_UNBOUND
    assert len(ac.elements) == 1
    # элемент зарегистрирован как orphan: «без компенсаций» != «без следа»
    assert len(ex.orphans) == 1 and ex.orphans[0]["reason"] == "MARKER_UNKNOWN"


@test
def marker_silent_noop_is_detected():
    """E3: write вернул ok, значение не записано. Обнаруживается только round-trip."""
    ex, ac, d = make(Faults(marker_silent_noop=True))
    ex.submit(plan())
    st = ex.run()
    assert st is JobState.PAUSED and ex.paused_reason == "CREATED_UNBOUND"
    assert ex.job.ops[KEY].map_state is MapState.CREATED_UNBOUND
    assert ex.orphans[0]["reason"] == "MARKER_SILENT_NOOP"


@test
def readback_broken_after_marker_halts():
    """AC29: писать можно, читать нельзя. Это UNAVAILABLE, а не «продолжаем»."""
    ex, ac, d = make(Faults(readback_broken_after_marker=True))
    ex.submit(plan())
    st = ex.run()
    assert st is JobState.PAUSED
    assert ex.job.ops[KEY].state is OpState.UNAVAILABLE
    assert "create_wall" in ex.matrix.invalidated, "матрица capability должна быть помечена"


@test
def single_independent_path_downgrades_to_inconclusive():
    """I5: VERIFIED_OK только при >=2 независимых путях read-back."""
    ex, ac, d = make(Faults(drop_independent_path=True))
    ex.submit(plan())
    st = ex.run()
    assert st is JobState.PAUSED
    assert ex.job.ops[KEY].state is OpState.INCONCLUSIVE


@test
def create_returns_wrong_guid_does_not_tag_foreign_element():
    """GUID из create не доверенный: tag-guard не даёт пометить чужой элемент."""
    ex, ac, d = make(Faults(create_returns_wrong_guid=True))
    ex.submit(plan())
    st = ex.run()
    assert st is JobState.PAUSED and ex.paused_reason == "CREATED_UNBOUND"
    foreign = [e for e in ac.elements.values() if e.type == "Slab"]
    assert foreign and foreign[0].marker is None, "чужой элемент не должен быть помечен"
    assert ex.orphans[0]["reason"] == "TAG_GUARD_TYPE_MISMATCH"


@test
def duplicate_from_previous_run_is_ambiguous():
    """M7: префиксный поиск ловит элемент от прошлого UNKNOWN-запуска."""
    def seed(ac):
        decoy = ac.add(
            type="Wall", story=STORIES[0], layer="A-WALL",
            ref_line={"from": [1.5, 2.5], "to": [6.5, 2.5]},
            height=3.0, thickness=0.30,
        )
        decoy.marker = make_marker("HOUSE_001", "W_F1_EXT_001", "decoynonce")

    ex, ac, d = make(seed=seed)
    ex.submit(plan())
    st = ex.run()
    assert st is JobState.PAUSED and ex.paused_reason == "AMBIGUOUS_MATCH"
    assert len(ac.elements) == 2


@test
def wrong_geometry_fails_verification():
    """T5: verify обязан уметь падать."""
    ex, ac, d = make(Faults(wrong_geometry=True))
    ex.submit(plan())
    st = ex.run()
    assert st is JobState.PAUSED and ex.paused_reason == "VERIFIED_FAILED"
    assert ex.job.ops[KEY].state is OpState.VERIFIED_FAILED
    assert len(ex.orphans) == 1


# ==== D. Идемпотентность, дрифт, зависимости ================================


@test
def repeated_delivery_does_not_redispatch():
    """T6: та же доставка задания трижды -> один dispatch."""
    p = plan()
    ex, ac, d = make()
    ex.submit(p)
    ex.run()
    assert len(ac.elements) == 1

    for _ in range(3):
        ex2 = reopen(ac, d)
        assert ex2.recover() is False
        ex2.run()
    assert len(ac.elements) == 1, "повторная доставка не должна создавать элементы"


class DriftAdapter(FakeAdapter):
    """Двигает элемент ровно перед указанным по счёту вызовом list_guids —
    имитация «человек подвинул стену между шагами»."""

    def __init__(self, ac, on_call: int):
        super().__init__(ac, Faults())
        self.on_call = on_call
        self.n = 0

    def list_guids(self):
        self.n += 1
        if self.n == self.on_call:
            self.ac.move_first(0.5)
        return super().list_guids()


@test
def host_geometry_drift_is_caught_before_dependent_op():
    """Геометрический дрифт НЕ ловится дешёвым fingerprint (count/слои/GUID
    не изменились). Он ловится целевой перепроверкой host перед зависимой op."""
    d = tempfile.mkdtemp()
    ac = FakeArchicad(PROJECT, STORIES)
    # вызовы list_guids: 1=bind, 2=precheck W_001, 3=commit W_001, 4=precheck W_002
    ad = DriftAdapter(ac, on_call=4)
    ex = Executor(ad, cap_matrix(), os.path.join(d, "j.jsonl"),
                  lock_path=os.path.join(d, "l.lock"), write_gate=True)
    ex.confirm_token = "tok"

    p = plan(
        packages=[
            {"id": "PKG01", "depends_on": [], "operations": [wall_op("W_001")]},
            {
                "id": "PKG02",
                "depends_on": ["PKG01"],
                "operations": [dict(wall_op("W_002"), host_wall="W_001")],
            },
        ]
    )
    ex.submit(p)
    st = ex.run()
    assert st is JobState.PAUSED, st
    assert "MODEL_DRIFT" in (ex.paused_reason or ""), ex.paused_reason
    assert len(ac.elements) == 1, "зависимая операция не должна быть отправлена"


@test
def halt_inside_package_protects_dependents():
    """В последовательной модели PARTIAL недостижим как «успех для зависимых»:
    job останавливается внутри пакета, и зависимый пакет вообще не стартует."""
    assert PkgState.PARTIAL.satisfied() is False
    assert PkgState.COMPLETED.satisfied() is True
    assert PkgState.BLOCKED.satisfied() is False

    ex, ac, d = make(Faults(wrong_geometry=True))
    p = plan(
        packages=[
            {"id": "PKG01", "depends_on": [], "operations": [wall_op("W_001")]},
            {"id": "PKG02", "depends_on": ["PKG01"], "operations": [wall_op("W_002")]},
        ]
    )
    ex.submit(p)
    st = ex.run()
    assert st is JobState.PAUSED
    assert ex.job.packages[0].state is PkgState.HALTED
    assert ex.job.packages[1].state is PkgState.PENDING
    assert "PKG01/W_002" not in [o for o in ex.job.ops]
    assert len(ac.elements) == 1


@test
def binding_mismatch_halts():
    ex, ac, d = make()
    ex.submit(plan())
    ac.project_info["project_path"] = "/pln/another.pln"   # открыли другой проект
    ex.write_gate = True
    st = ex.run()
    assert st is JobState.PAUSED and ex.paused_reason == "INSTANCE_MISMATCH"
    assert len(ac.elements) == 0


@test
def untitled_project_is_refused():
    ac = FakeArchicad(dict(PROJECT, is_untitled=True), STORIES)
    d = tempfile.mkdtemp()
    ex = Executor(FakeAdapter(ac), cap_matrix(), os.path.join(d, "j.jsonl"),
                  lock_path=os.path.join(d, "l.lock"))
    try:
        ex.submit(plan())
    except Exception as e:
        assert "untitled" in str(e)
        return
    raise AssertionError("untitled project must be refused")


@test
def teamproject_is_refused():
    ac = FakeArchicad(dict(PROJECT, is_teamwork=True), STORIES)
    d = tempfile.mkdtemp()
    ex = Executor(FakeAdapter(ac), cap_matrix(), os.path.join(d, "j.jsonl"),
                  lock_path=os.path.join(d, "l.lock"))
    try:
        ex.submit(plan())
    except Exception as e:
        assert "Teamwork" in str(e)
        return
    raise AssertionError("Teamwork project must be refused in v1")


# ==== E. Механизмы безопасности =============================================


@test
def illegal_transition_raises():
    from bimexec import states as st

    try:
        st.op_to(OpState.PLANNED, OpState.VERIFIED_OK)
    except TransitionError:
        pass
    else:
        raise AssertionError("illegal transition must raise")

    try:
        st.op_to(OpState.UNKNOWN, OpState.VERIFIED_OK)
    except TransitionError:
        pass
    else:
        raise AssertionError("UNKNOWN must not jump straight to VERIFIED_OK")


@test
def unresolved_operation_blocks_further_mutation():
    """I3: пока есть UNKNOWN — никаких мутаций по job."""
    ex, ac, d = make(Faults(create_applied_but_timeout=True))
    ex.submit(plan())
    ex.run()
    assert ex.job.ops[KEY].state is OpState.UNKNOWN
    from bimexec.executor import Halted

    try:
        ex._assert_no_unresolved()
    except Halted:
        pass
    else:
        raise AssertionError("unresolved op must block further mutation")


@test
def single_flight_refuses_second_mutation():
    from bimexec.lock import SingleFlight

    f = SingleFlight()
    f.acquire("op-a")
    try:
        f.acquire("op-b")
    except ProcessLockError:
        return
    finally:
        f.release()
    raise AssertionError("second concurrent mutation must be refused")


@test
def process_singleton_refuses_second_instance():
    d = tempfile.mkdtemp()
    p = os.path.join(d, "router.lock")
    a = ProcessLock(p)
    a.acquire()
    b = ProcessLock(p)
    try:
        b.acquire()
    except ProcessLockError:
        return
    finally:
        a.release()
    raise AssertionError("second Router instance must be refused")


@test
def journal_survives_torn_record():
    """Крах во время append — последняя запись отбрасывается, seq без дыр."""
    d = tempfile.mkdtemp()
    path = os.path.join(d, "j.jsonl")
    with Journal(path) as j:
        j.append({"kind": "A"})
        j.append({"kind": "B"})
    with open(path, "a", encoding="utf-8") as f:
        f.write('{"kind":"BROKEN"')       # крах посреди записи
    with Journal(path) as j:
        events = j.read_all()
        assert [e["kind"] for e in events] == ["A", "B"], events
        assert j.seq == 2
        j.append({"kind": "C"})
    with Journal(path) as j:
        assert [e["kind"] for e in j.read_all()] == ["A", "B", "C"]


@test
def no_automatic_retry_after_unknown():
    """Мутирующий вызов dispatched ровно один раз, без автоповтора."""
    ex, ac, d = make(Faults(create_applied_but_timeout=True))
    ex.submit(plan())
    ex.run()
    creates = [c for c in ex.adapter.calls if c == "create_wall"]
    assert len(creates) == 1, f"create dispatched {len(creates)} times"


@test
def ensure_path_adopts_without_mutation():
    """Повторный запуск с уже существующим маркером не должен создавать элемент."""
    ex, ac, d = make()
    ex.submit(plan())
    ex.run()
    assert len(ac.elements) == 1

    # «второй запуск» того же run: маркер уже в модели
    ex.job.ops[KEY].state = OpState.PLANNED
    ex.job.ops[KEY].map_state = MapState.UNBOUND
    ex._dispatched.pop(ex.job.ops[KEY].idem_key, None)
    ex.job.packages[0].state = PkgState.PENDING
    ex.job_state = JobState.READY
    ex._step(ex.job.ops[KEY])
    assert len(ac.elements) == 1, "ensure не должен создавать второй элемент"
    # ADOPTED, а не VERIFIED_OK: мутация не отправлялась, элемент усыновлён
    assert ex.job.ops[KEY].state is OpState.ADOPTED
    assert ex.job.ops[KEY].map_state is MapState.ADOPTED


# --- запуск -----------------------------------------------------------------


def main() -> int:
    failed = 0
    for name, fn in TESTS:
        try:
            fn()
            print(f"  PASS  {name}")
        except Exception:
            failed += 1
            print(f"  FAIL  {name}")
            traceback.print_exc()
    print(f"\n{len(TESTS) - failed}/{len(TESTS)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
