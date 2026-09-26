"""
BIMEXEC v1 — capability gating и верификация.

Три правила, закодированные здесь:

1. verify_spec обязан содержать обязательный минимум ИЗ КОНФИГА ROUTER (M8).
   План может расширить минимум, но не сузить. Иначе план с "verify": {}
   даст VERIFIED_OK на пустом множестве проверок.
2. Каждая проверка должна быть обеспечена capability (M21). Нет read-back —
   операция отбрасывается на ВАЛИДАЦИИ, а не в рантайме.
3. VERIFIED_OK требует минимум двух НЕЗАВИСИМЫХ путей read-back (M13/I5).
   Один путь может соврать тем же способом, что и create.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

from .binding import match_exact


class PlanRejected(Exception):
    pass


# --- вердикты ---------------------------------------------------------------

_SEVERITY = {"OK": 0, "UNSUPPORTED": 1, "UNAVAILABLE": 2, "INCONCLUSIVE": 3, "FAILED": 4}


class CheckVerdict(str, Enum):
    OK = "OK"
    FAILED = "FAILED"
    INCONCLUSIVE = "INCONCLUSIVE"
    UNAVAILABLE = "UNAVAILABLE"
    UNSUPPORTED = "UNSUPPORTED"


def aggregate(verdicts: list[CheckVerdict]) -> CheckVerdict:
    """Худший вердикт побеждает. UNSUPPORTED/UNAVAILABLE — не успех."""
    if not verdicts:
        return CheckVerdict.INCONCLUSIVE
    worst = max(verdicts, key=lambda v: _SEVERITY[v.value])
    return worst


@dataclass
class CheckResult:
    name: str
    verdict: CheckVerdict
    expected: Any = None
    actual: Any = None
    note: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "check": self.name,
            "verdict": self.verdict.value,
            "expected": self.expected,
            "actual": self.actual,
            "note": self.note,
        }


# --- capability matrix ------------------------------------------------------


@dataclass
class Capability:
    """Эмпирически измеренная возможность. Заполняется probe'ом, а не по докам."""

    op: str
    exec_backend: str
    readback_backends: list[str] = field(default_factory=list)
    readable_fields: set[str] = field(default_factory=set)
    marker_medium: str | None = None          # "property" | "element_id" | None
    marker_search_exact: bool = False
    marker_search_prefix: bool = False
    count_by_type: bool = False
    production_safe: bool = False
    verified_at: str = ""
    adapter_version: str = ""
    # Сертификация probe: capability считается пригодной только если она
    # подтверждена ЭМПИРИЧЕСКИ (а не взята из документации).
    probe_certified: bool = False
    probe_ts: str = ""
    duplicate_detection: str = "NONE"   # PREFIX | EMPTY_SCOPE_FALLBACK | NONE

    def runnable(self) -> bool:
        return self.production_safe and self.probe_certified

    def supports(self, check: str) -> bool:
        return check in self.readable_fields


@dataclass
class CapabilityMatrix:
    caps: dict[str, Capability] = field(default_factory=dict)
    invalidated: set[str] = field(default_factory=set)
    source: str = ""

    @classmethod
    def from_probe_report(cls, report: dict[str, Any]) -> "CapabilityMatrix":
        """Строит матрицу из отчёта probe. Проверки, не прошедшие сертификацию,
        просто не попадают в матрицу — Executor потом откажет по OUT_OF_SCOPE."""
        m = cls(source=report.get("generated_at", ""))
        for op, c in (report.get("capabilities") or {}).items():
            if not c.get("probe_certified"):
                continue
            m.add(
                Capability(
                    op=op,
                    exec_backend=c.get("exec_backend", ""),
                    readback_backends=list(c.get("readback_backends") or []),
                    readable_fields=set(c.get("readable_fields") or []),
                    marker_medium=c.get("marker_medium"),
                    marker_search_exact=bool(c.get("marker_search_exact")),
                    marker_search_prefix=bool(c.get("marker_search_prefix")),
                    count_by_type=bool(c.get("count_by_type")),
                    production_safe=bool(c.get("production_safe")),
                    probe_certified=bool(c.get("probe_certified")),
                    probe_ts=report.get("generated_at", ""),
                    duplicate_detection=c.get("duplicate_detection", "NONE"),
                    adapter_version=c.get("adapter_version", ""),
                )
            )
        return m

    def add(self, cap: Capability) -> None:
        self.caps[cap.op] = cap

    def get(self, op: str) -> Capability:
        cap = self.caps.get(op)
        if cap is None:
            raise PlanRejected(f"op '{op}' is OUT_OF_SCOPE: no capability record")
        return cap

    def invalidate(self, op: str) -> None:
        """UNSUPPORTED в рантайме = расхождение матрицы с реальностью."""
        self.invalidated.add(op)


# --- обязательный минимум (ИЗ КОНФИГА, НЕ ИЗ ПЛАНА) -------------------------

CHECK_WHITELIST: set[str] = {
    "exists",
    "type",
    "story",
    "layer",
    "marker_exact",
    "ref_line",
    "length",
    "height",
    "thickness",
    "angle",
    "count_delta",
    "library_part",
}

# exists — структурная предпосылка, её нельзя «забыть» и нельзя снять:
# Router требует её всегда, независимо от того, указал ли её план.
IMPLICIT_CHECKS: set[str] = {"exists"}

MANDATORY_FLOOR: dict[str, set[str]] = {
    "create_wall": {
        "exists",
        "type",
        "story",
        "layer",
        "marker_exact",
        "ref_line",
        "length",
        "height",
        "thickness",
        "count_delta",
    },
    "create_slab": {
        "exists",
        "type",
        "story",
        "layer",
        "marker_exact",
        "count_delta",
    },
}

# каждая проверка требуется хотя бы двумя независимыми путями
MIN_INDEPENDENT_PATHS = 2


def validate_verify_spec(op: dict[str, Any], cap: Capability) -> dict[str, Any]:
    """Валидация ДО dispatch. Любая проблема — PlanRejected."""
    op_type = op.get("op")
    spec = op.get("verify")
    if not isinstance(spec, dict) or not spec:
        raise PlanRejected(f"{op.get('id')}: verify_spec is missing or empty")

    floor = MANDATORY_FLOOR.get(op_type, set())
    declared = {k for k in spec if k in CHECK_WHITELIST}

    unknown = {k for k in spec if k not in CHECK_WHITELIST}
    if unknown:
        raise PlanRejected(f"{op.get('id')}: unknown checks {sorted(unknown)}")

    missing = (floor - declared) - IMPLICIT_CHECKS
    if missing:
        raise PlanRejected(
            f"{op.get('id')}: verify_spec narrows mandatory floor, missing {sorted(missing)}"
        )

    unsupported = {c for c in declared if not cap.supports(c)}
    if unsupported:
        raise PlanRejected(
            f"{op.get('id')}: checks {sorted(unsupported)} are not backed by read-back "
            f"capability of '{cap.op}' (capability gating: reject at validation, not at runtime)"
        )

    _assert_consistent_with_params(op, spec)
    return spec


def _assert_consistent_with_params(op: dict[str, Any], spec: dict[str, Any]) -> None:
    """verify не должен противоречить параметрам самой операции: иначе план
    может отправить height 3.0, а проверять height 30.0."""
    pairs = [("height", "height"), ("thickness", "thickness")]
    for param, check in pairs:
        if check in spec and param in op:
            want = spec[check].get("expected")
            if want is not None and abs(float(want) - float(op[param])) > 1e-9:
                raise PlanRejected(
                    f"{op.get('id')}: verify.{check}.expected={want} "
                    f"contradicts op.{param}={op[param]}"
                )
    if "story" in spec and "story" in op:
        s_spec, s_op = spec["story"], op["story"]
        if isinstance(s_spec, dict) and isinstance(s_op, dict):
            if s_spec.get("name") != s_op.get("name"):
                raise PlanRejected(f"{op.get('id')}: verify.story contradicts op.story")
    if "layer" in spec and "layer" in op and spec["layer"] != op["layer"]:
        raise PlanRejected(f"{op.get('id')}: verify.layer contradicts op.layer")


# --- проверки ---------------------------------------------------------------

Tolerance = float


def _tol(spec_value: Any, default: float) -> float:
    if isinstance(spec_value, dict):
        return float(spec_value.get("tolerance", default))
    return default


def _close(a: float, b: float, tol: float) -> bool:
    return abs(float(a) - float(b)) <= tol


def run_checks(
    op: dict[str, Any],
    spec: dict[str, Any],
    obs: dict[str, Any],
    cap: Capability,
    skip: set[str] | None = None,
) -> list[CheckResult]:
    out: list[CheckResult] = []

    def need(field_name: str) -> tuple[bool, Any]:
        """Возвращает (есть_наблюдение, значение). Отсутствие поля =
        UNAVAILABLE, если capability его обещал, иначе UNSUPPORTED."""
        if field_name not in obs:
            return False, None
        return True, obs[field_name]

    floor = MANDATORY_FLOOR.get(op.get("op", ""), set())
    # skip — проверки, неприменимые к данному пути (например, count_delta
    # при усыновлении: элемент уже был в модели, дельты нет)
    checks = sorted(({c for c in spec if c in CHECK_WHITELIST} | floor) - (skip or set()))

    for name in checks:
        supported = cap.supports(name)
        present, value = need(_OBS_FIELD.get(name, name))

        if not supported:
            out.append(CheckResult(name, CheckVerdict.UNSUPPORTED, note="no read-back capability"))
            continue
        if not present:
            out.append(CheckResult(name, CheckVerdict.UNAVAILABLE, note="field absent in observation"))
            continue

        fn: Callable[[], CheckResult] = lambda n=name, v=value: _eval(n, v, spec, op, obs)
        out.append(fn())

    return out


_OBS_FIELD = {
    "exists": "exists",
    "type": "type",
    "story": "story",
    "layer": "layer",
    "marker_exact": "marker",
    "ref_line": "ref_line",
    "length": "length",
    "height": "height",
    "thickness": "thickness",
    "angle": "angle",
    "count_delta": "count_delta",
    "library_part": "library_part",
}


def _eval(name: str, value: Any, spec: dict[str, Any], op: dict[str, Any], obs: dict[str, Any]) -> CheckResult:
    s = spec.get(name)
    # Проверка из mandatory floor без объявленного ожидания — ошибка контракта.
    # Возвращаем UNSUPPORTED (=> halt), но НЕ падаем: исключение внутри
    # верификации — это fail-open риск, его быть не должно.
    if s is None and name not in IMPLICIT_CHECKS:
        return CheckResult(name, CheckVerdict.UNSUPPORTED, note="no expectation in verify_spec")

    if name == "exists":
        ok = bool(value)
        return CheckResult(name, CheckVerdict.OK if ok else CheckVerdict.FAILED, True, value)

    if name == "type":
        want = s if isinstance(s, str) else (s or {}).get("expected")
        ok = str(value).lower() == str(want).lower()
        return CheckResult(name, CheckVerdict.OK if ok else CheckVerdict.FAILED, want, value)

    if name == "story":
        want = (s or {}) if isinstance(s, dict) else {"name": s}
        ok = (
            isinstance(value, dict)
            and value.get("name") == want.get("name")
            and _close(value.get("elevation", 0.0), want.get("elevation", 0.0), 1e-6)
        )
        return CheckResult(name, CheckVerdict.OK if ok else CheckVerdict.FAILED, want, value)

    if name == "layer":
        want = s if isinstance(s, str) else (s or {}).get("expected")
        ok = value == want
        return CheckResult(name, CheckVerdict.OK if ok else CheckVerdict.FAILED, want, value)

    if name == "marker_exact":
        want = (s or {}).get("exact")
        ok = match_exact(value, want) if want else False
        return CheckResult(name, CheckVerdict.OK if ok else CheckVerdict.FAILED, want, value)

    if name == "ref_line":
        want = (s or {}).get("from"), (s or {}).get("to")
        tol = _tol(s, 0.01)
        got = value or {}
        g_from, g_to = got.get("from"), got.get("to")
        ok = (
            g_from is not None
            and g_to is not None
            and _close(g_from[0], want[0][0], tol)
            and _close(g_from[1], want[0][1], tol)
            and _close(g_to[0], want[1][0], tol)
            and _close(g_to[1], want[1][1], tol)
        )
        return CheckResult(name, CheckVerdict.OK if ok else CheckVerdict.FAILED, want, got)

    if name in ("length", "height", "thickness", "angle"):
        want = (s or {}).get("expected")
        tol = _tol(s, 0.001 if name != "length" else 0.05)
        ok = want is not None and _close(value, want, tol)
        return CheckResult(name, CheckVerdict.OK if ok else CheckVerdict.FAILED, want, value)

    if name == "count_delta":
        want = s or {}
        got = value or {}
        ok = all(int(got.get(k, 0)) == int(v) for k, v in want.items())
        return CheckResult(name, CheckVerdict.OK if ok else CheckVerdict.FAILED, want, got)

    if name == "library_part":
        want = (s or {}).get("expected")
        ok = want is None or value == want
        return CheckResult(name, CheckVerdict.OK if ok else CheckVerdict.FAILED, want, value)

    return CheckResult(name, CheckVerdict.UNSUPPORTED, note="unknown check")


def with_runtime_marker(spec: dict[str, Any], marker: str) -> dict[str, Any]:
    """План не может содержать маркер: nonce генерирует Router перед dispatch.
    Router подставляет фактическое значение в спецификацию перед проверкой."""
    if "marker_exact" not in spec:
        return spec
    out = dict(spec)
    cur = out["marker_exact"]
    if cur is True or (isinstance(cur, dict) and "exact" not in cur):
        out["marker_exact"] = {"exact": marker}
    return out


def evaluate(
    op: dict[str, Any],
    spec: dict[str, Any],
    obs: dict[str, Any],
    cap: Capability,
    skip: set[str] | None = None,
) -> tuple[CheckVerdict, list[CheckResult]]:
    """Возвращает итоговый вердикт и разбор по проверкам."""
    results = run_checks(op, spec, obs, cap, skip)
    verdict = aggregate([r.verdict for r in results])

    # Требование независимости (I5): VERIFIED_OK только при >=2 путях read-back.
    paths = {p for p in obs.get("paths", []) if p}
    if verdict is CheckVerdict.OK and len(paths) < MIN_INDEPENDENT_PATHS:
        verdict = CheckVerdict.INCONCLUSIVE
        results.append(
            CheckResult(
                "independent_paths",
                CheckVerdict.INCONCLUSIVE,
                MIN_INDEPENDENT_PATHS,
                sorted(paths),
                note="VERIFIED_OK requires >=2 independent read-back paths",
            )
        )
    return verdict, results
