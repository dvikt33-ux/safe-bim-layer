"""
Тесты capability probe (T0) и сертификации.

Проверяют не «работает ли Archicad», а что probe сам по себе честный:
  * без write-фазы ничего не сертифицируется (fail closed);
  * негативные контроли действительно контролируют;
  * отсутствие префиксного поиска деградирует в EMPTY_SCOPE_FALLBACK, а не в «ок»;
  * Executor отказывает на несертифицированной матрице.
"""
from __future__ import annotations

import os
import sys
import tempfile
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reference"))

from bimexec.adapters import ExecutorAdapter, FakeArchicad, FakeRaw
from bimexec.executor import Executor
from bimexec.probe import Probe, ProbeConfig, ProbeVerdict, render_text
from bimexec.verify import CapabilityMatrix, PlanRejected

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

TESTS: list[tuple[str, object]] = []


def test(fn):
    TESTS.append((fn.__name__, fn))
    return fn


def raw(**kw) -> FakeRaw:
    return FakeRaw(FakeArchicad(PROJECT, STORIES), **kw)


def verdicts(report):
    return {c["name"]: c["verdict"] for c in report["checks"]}


# --- fail closed ------------------------------------------------------------


@test
def readonly_probe_certifies_nothing():
    """Без write-фазы marker binding остаётся неподтверждённым."""
    r = Probe(raw(), ProbeConfig(allow_write=False)).run()
    v = verdicts(r)
    assert v["marker_write_roundtrip"] == "SKIPPED", v
    assert v["verify_discriminates"] == "SKIPPED", v
    assert r["verdicts"]["certified"] is False
    assert r["capabilities"]["create_wall"]["probe_certified"] is False


@test
def write_probe_certifies_full_binding():
    r = Probe(raw(), ProbeConfig(allow_write=True)).run()
    v = verdicts(r)
    for name in ("connection", "project_identity", "stories_read", "count_by_type",
                 "list_guids", "find_by_filter",
                 "marker_search_exact", "marker_search_prefix",
                 "create_wall", "details_of_created", "count_delta",
                 "marker_write_roundtrip", "marker_search_hit", "verify_discriminates"):
        assert v[name] == "CERTIFIED", f"{name}={v[name]}"
    assert r["verdicts"]["certified"] is True
    cap = r["capabilities"]["create_wall"]
    assert cap["marker_medium"] == "element_id"
    assert cap["duplicate_detection"] == "PREFIX"
    assert len(r["artifacts"]) == 2   # стена + маркер


@test
def negative_control_marker_search_returns_zero():
    """Поиск несуществующего маркера обязан вернуть 0. Если адаптер вернёт
    «всё» или ошибку — путь поиска непригоден."""
    r = Probe(raw(), ProbeConfig(allow_write=True)).run()
    c = next(c for c in r["checks"] if c["name"] == "marker_search_exact")
    assert c["detail"]["hits"] == 0, c["detail"]
    c2 = next(c for c in r["checks"] if c["name"] == "marker_search_prefix")
    assert c2["detail"]["hits"] == 0, c2["detail"]


@test
def negative_control_verify_discriminates():
    """Production-код верификации обязан сказать FAILED на сдвинутое ожидание.
    Без этого «проверка прошла» ничего не доказывает."""
    r = Probe(raw(), ProbeConfig(allow_write=True)).run()
    c = next(c for c in r["checks"] if c["name"] == "verify_discriminates")
    assert c["detail"]["on_correct"] == "OK", c["detail"]
    assert c["detail"]["on_wrong"] == "FAILED", c["detail"]


@test
def broken_details_is_reported_as_unknown():
    r = Probe(raw(broken_details=True), ProbeConfig(allow_write=True)).run()
    v = verdicts(r)
    assert v["details_of_created"] in ("UNKNOWN", "FAILED"), v
    assert r["verdicts"]["certified"] is False


# --- деградация, а не «ок» ---------------------------------------------------


@test
def no_prefix_search_falls_back_to_empty_scope():
    r = Probe(raw(no_prefix_search=True), ProbeConfig(allow_write=True)).run()
    v = verdicts(r)
    assert v["marker_search_prefix"] == "NOT_SUPPORTED", v
    cap = r["capabilities"]["create_wall"]
    assert cap["marker_search_prefix"] is False
    assert cap["duplicate_detection"] == "EMPTY_SCOPE_FALLBACK", cap
    assert r["verdicts"]["certified"] is True   # сертифицируемо, но с оговоркой


@test
def no_marker_search_at_all_is_not_certified():
    r = Probe(raw(no_marker_search=True), ProbeConfig(allow_write=True)).run()
    v = verdicts(r)
    assert v["marker_search_exact"] == "NOT_SUPPORTED", v
    assert r["verdicts"]["certified"] is False


@test
def first_working_medium_wins_and_is_not_overwritten():
    r = Probe(raw(), ProbeConfig(allow_write=True)).run()
    c = next(c for c in r["checks"] if c["name"] == "marker_write_roundtrip")
    assert c["detail"]["certified_medium"] == "element_id", c["detail"]
    # маркер не перезаписывается вторым носителем, иначе точный поиск сломается
    assert c["verdict"] == "CERTIFIED"


@test
def falls_back_to_second_medium():
    r = Probe(raw(unsupported_media={"element_id"}), ProbeConfig(allow_write=True)).run()
    c = next(c for c in r["checks"] if c["name"] == "marker_write_roundtrip")
    assert c["detail"]["element_id"]["supported"] is False, c["detail"]
    assert c["detail"]["certified_medium"] == "property", c["detail"]
    assert r["verdicts"]["certified"] is True


@test
def untitled_project_is_not_certified():
    ac = FakeArchicad(dict(PROJECT, is_untitled=True), STORIES)
    r = Probe(FakeRaw(ac), ProbeConfig(allow_write=True)).run()
    assert verdicts(r)["project_identity"] == "FAILED"
    assert r["verdicts"]["certified"] is False


@test
def teamproject_is_not_certified():
    ac = FakeArchicad(dict(PROJECT, is_teamwork=True), STORIES)
    r = Probe(FakeRaw(ac), ProbeConfig(allow_write=True)).run()
    assert verdicts(r)["project_identity"] == "FAILED"
    assert r["verdicts"]["certified"] is False


# --- интеграция с Executor ---------------------------------------------------


@test
def executor_refuses_uncertified_capability():
    report = Probe(raw(), ProbeConfig(allow_write=False)).run()
    m = CapabilityMatrix.from_probe_report(report)
    assert m.caps == {}, "несертифицированные capability не должны попадать в матрицу"

    d = tempfile.mkdtemp()
    ex = Executor(ExecutorAdapter(FakeRaw(FakeArchicad(PROJECT, STORIES)), "element_id"), m,
                  os.path.join(d, "j.jsonl"), lock_path=os.path.join(d, "l.lock"))
    try:
        ex.submit(_plan())
    except PlanRejected as e:
        assert "OUT_OF_SCOPE" in str(e) or "not certified" in str(e)
        return
    raise AssertionError("Executor must refuse an uncertified capability")


@test
def executor_accepts_certified_capability():
    report = Probe(raw(), ProbeConfig(allow_write=True)).run()
    m = CapabilityMatrix.from_probe_report(report)
    assert "create_wall" in m.caps
    assert m.caps["create_wall"].runnable() is True

    ac = FakeArchicad(PROJECT, STORIES)
    d = tempfile.mkdtemp()
    ex = Executor(ExecutorAdapter(FakeRaw(ac), "element_id"), m, os.path.join(d, "j.jsonl"),
                  lock_path=os.path.join(d, "l.lock"), write_gate=True)
    ex.confirm_token = "tok"
    ex.submit(_plan())
    assert ex.job is not None


@test
def empty_scope_fallback_blocks_foreign_element():
    """Без префиксного поиска чужой элемент в области обязан останавливать job,
    иначе мы не отличим его от наследия прошлого запуска."""
    report = Probe(raw(no_prefix_search=True), ProbeConfig(allow_write=True)).run()
    m = CapabilityMatrix.from_probe_report(report)
    assert m.caps["create_wall"].duplicate_detection == "EMPTY_SCOPE_FALLBACK"

    ac = FakeArchicad(PROJECT, STORIES)
    foreign = ac.add(type="Wall", story=STORIES[0], layer="A-WALL",
                     ref_line={"from": [20.0, 20.0], "to": [25.0, 20.0]},
                     height=3.0, thickness=0.30)
    d = tempfile.mkdtemp()
    ex = Executor(ExecutorAdapter(FakeRaw(ac, no_prefix_search=True), "element_id"), m,
                  os.path.join(d, "j.jsonl"), lock_path=os.path.join(d, "l.lock"), write_gate=True)
    ex.confirm_token = "tok"
    ex.submit(_plan())
    st = ex.run()
    assert st.value == "PAUSED", st
    assert "AMBIGUOUS_MATCH" in (ex.paused_reason or ""), ex.paused_reason
    assert len(ac.elements) == 1   # мы ничего не создали


def _plan() -> dict:
    return {
        "bimexec": 1,
        "schema_version": "1.0",
        "job": "HOUSE_001",
        "mode": "strict",
        "units": {"length": "m", "angle": "deg"},
        "origin": "project",
        "packages": [{
            "id": "PKG01",
            "type": "walls",
            "depends_on": [],
            "operations": [{
                "op": "create_wall",
                "id": "W_F1_EXT_001",
                "story": {"name": "Ground Floor", "elevation": 0.0},
                "layer": "A-WALL",
                "from": [1.5, 2.5],
                "to": [6.5, 2.5],
                "height": 3.0,
                "thickness": 0.30,
                "reference_line": "center",
                "base_level": 0.0,
                "top_link": "absolute",
                "verify": {
                    "type": "Wall",
                    "story": {"name": "Ground Floor", "elevation": 0.0},
                    "layer": "A-WALL",
                    "marker_exact": True,
                    "ref_line": {"from": [1.5, 2.5], "to": [6.5, 2.5], "tolerance": 0.01},
                    "length": {"expected": 5.0, "tolerance": 0.05},
                    "height": {"expected": 3.0, "tolerance": 0.001},
                    "thickness": {"expected": 0.30, "tolerance": 0.001},
                    "count_delta": {"Wall": 1},
                },
            }],
        }],
    }


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
