"""
BIMEXEC v1 — исполнитель.

Шаг операции (соответствует разделу 4.3 обзора P0):

  0. глобальный gate: нет неразрешённых операций
  1. PRECHECK: binding, state fingerprint, зависимости, refs, слой
  2. WAL INTENT (fsync)                       <-- до dispatch
  3. ENSURE: поиск по маркеру -> ADOPTED без мутации
  4. DISPATCH: одна попытка; не 200 с телом -> UNKNOWN
  5. WAL OUTCOME
  6. MARKER: tag-guard -> запись (со своим UNKNOWN) -> round-trip -> BOUND
  7. READ-BACK: независимые пути
  8. VERIFY: OK / FAILED / INCONCLUSIVE / UNAVAILABLE / UNSUPPORTED
  9. POSTCHECK: count_delta точно совпал; перебазирование fingerprint
 10. COMMIT

Любое состояние из OpState.halts_job() останавливает ВСЕ мутации в job.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from . import states as st
from .adapters import AdapterError, CreateResult, FakeAdapter
from .binding import (
    Binding,
    BindingError,
    assert_bindable,
    identity_fingerprint,
    make_marker,
    make_nonce,
    marker_prefix,
    state_fingerprint,
)
from .journal import (
    FINGERPRINT,
    JOB_CREATED,
    JOB_STATE,
    OP_COMMIT,
    OP_DECISION,
    OP_INTENT,
    OP_OUTCOME,
    OP_VERDICT,
    ORPHAN,
    PKG_STATE,
    Journal,
    write_snapshot,
)
from .journal import MARKER_INTENT, MARKER_RESULT
from .lock import ProcessLock, ProcessLockError, SingleFlight
from .verify import (
    CapabilityMatrix,
    CheckVerdict,
    PlanRejected,
    evaluate,
    validate_verify_spec,
    with_runtime_marker,
)


# --- записи состояния -------------------------------------------------------


@dataclass
class OpRecord:
    key: str                    # "<pkg_id>/<object_id>"
    pkg_id: str
    index: int
    op: dict[str, Any]
    object_id: str
    nonce: str
    idem_key: str
    marker: str
    state: st.OpState = st.OpState.PLANNED
    map_state: st.MapState = st.MapState.UNBOUND
    mapping_method: str | None = None
    candidate_guid: str | None = None
    baseline_guids: list[str] = field(default_factory=list)
    baseline_counts: dict[str, int] = field(default_factory=dict)
    verified_geometry_hash: str | None = None


@dataclass
class PkgRecord:
    id: str
    index: int
    depends_on: list[str]
    op_keys: list[str]
    state: st.PkgState = st.PkgState.PENDING


@dataclass
class JobRecord:
    job_id: str
    run_id: str
    plan_hash: str
    packages: list[PkgRecord]
    ops: dict[str, OpRecord]


class Halted(Exception):
    def __init__(self, reason: str, op_key: str | None = None):
        super().__init__(reason)
        self.reason = reason
        self.op_key = op_key


# --- план -------------------------------------------------------------------


def plan_hash(plan: dict[str, Any]) -> str:
    blob = json.dumps(plan.get("packages", []), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def _idem_key(job_id: str, run_id: str, object_id: str, attempt: int = 1) -> str:
    return f"{job_id}|{run_id}|{object_id}|{attempt}"


def _hash(obj: Any) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()[:16]


# --- исполнитель ------------------------------------------------------------

OP_TYPE_TO_ELEMENT = {"create_wall": "Wall", "create_slab": "Slab"}


class Executor:
    def __init__(
        self,
        adapter: Any,
        matrix: CapabilityMatrix,
        journal_path: str,
        lock_path: str | None = None,
        allowed_ops: set[str] | None = None,
        write_gate: bool = False,
    ) -> None:
        self.adapter = adapter
        self.matrix = matrix
        self.journal_path = journal_path
        self.snapshot_path = journal_path + ".snapshot.json"
        self.lock_path = lock_path or journal_path + ".lock"
        self.allowed_ops = allowed_ops or set(OP_TYPE_TO_ELEMENT)
        self.write_gate = write_gate          # по умолчанию OFF
        self.confirm_token: str | None = None

        self.lock = ProcessLock(self.lock_path)
        self.flight = SingleFlight()

        self.journal = Journal(journal_path)
        self.job: JobRecord | None = None
        self.job_state = st.JobState.CREATED
        self.paused_reason: str | None = None
        self.binding: Binding | None = None
        self.state_fp: str | None = None
        self.orphans: list[dict[str, Any]] = []
        self.reports: list[dict[str, Any]] = []
        self._dispatched: dict[str, dict[str, Any]] = {}

    # ================= валидация =================

    def submit(self, plan: dict[str, Any], run_id: str = "run-1") -> JobRecord:
        self._load()
        self.job_state = st.job_to(self.job_state, st.JobState.VALIDATING)

        ph = plan_hash(plan)
        if self.job is not None:
            if self.job.plan_hash != ph:
                raise PlanRejected("plan changed for an existing job: create a new job/run")
            return self.job

        self._validate(plan)
        ops: dict[str, OpRecord] = {}
        packages: list[PkgRecord] = []
        for pi, pkg in enumerate(plan["packages"]):
            keys = []
            for oi, op in enumerate(pkg["operations"]):
                oid = op["id"]
                key = f"{pkg['id']}/{oid}"
                if key in ops:
                    raise PlanRejected(f"duplicate object id in job: {oid}")
                nonce = make_nonce()
                ops[key] = OpRecord(
                    key=key,
                    pkg_id=pkg["id"],
                    index=oi,
                    op=op,
                    object_id=oid,
                    nonce=nonce,
                    idem_key=_idem_key(plan["job"], run_id, oid),
                    marker=make_marker(plan["job"], oid, nonce),
                )
                keys.append(key)
            packages.append(
                PkgRecord(
                    id=pkg["id"],
                    index=pi,
                    depends_on=list(pkg.get("depends_on", [])),
                    op_keys=keys,
                )
            )

        self.job = JobRecord(
            job_id=plan["job"], run_id=run_id, plan_hash=ph, packages=packages, ops=ops
        )
        self.journal.open()
        self.journal.append(
            {
                "kind": JOB_CREATED,
                "job_id": plan["job"],
                "run_id": run_id,
                "plan_hash": ph,
                "packages": [p.id for p in packages],
                "ops": {k: {"nonce": r.nonce, "idem_key": r.idem_key} for k, r in ops.items()},
                "ts": time.time(),
            }
        )
        self._bind()
        self._set_job_state(st.JobState.READY)
        return self.job

    def _validate(self, plan: dict[str, Any]) -> None:
        for need in ("bimexec", "job", "mode", "units", "packages"):
            if need not in plan:
                raise PlanRejected(f"plan missing required field '{need}'")
        if plan.get("mode") != "strict":
            raise PlanRejected("only mode='strict' is accepted in v1")

        seen: set[str] = set()
        for pkg in plan["packages"]:
            if pkg["id"] in seen:
                raise PlanRejected(f"duplicate package id {pkg['id']}")

            # D4: порядок массива = топологический порядок; планировщик не нужен
            for dep in pkg.get("depends_on", []):
                if dep not in seen:
                    raise PlanRejected(
                        f"package {pkg['id']} depends on {dep}, which is not earlier "
                        f"in the array (cycles and forward refs rejected at validation)"
                    )
            seen.add(pkg["id"])

            for op in pkg["operations"]:
                otype = op.get("op")
                if otype not in self.allowed_ops:
                    raise PlanRejected(f"op '{otype}' is not allowed in v1 scope")
                cap = self.matrix.get(otype)
                if not cap.production_safe:
                    raise PlanRejected(f"op '{otype}' is not marked production-safe")
                if not cap.probe_certified:
                    # capability matrix обязана быть измерена probe, а не взята из документации
                    raise PlanRejected(
                        f"op '{otype}' is not certified by capability probe: run tools/run_probe.py"
                    )
                validate_verify_spec(op, cap)
                self._assert_refs(op)

    def _assert_refs(self, op: dict[str, Any]) -> None:
        """host_wall и прочие refs — только по объявленным полям, без свободы для LLM."""
        if "host_wall" in op:
            if not isinstance(op["host_wall"], str):
                raise PlanRejected("host_wall must be a BIMEXEC object id (string)")
        for extra in ("script", "expr", "command", "tool"):
            if extra in op:
                raise PlanRejected(f"op contains forbidden free-form field '{extra}'")

    # ================= binding =================

    def _bind(self) -> None:
        self._set_job_state(st.JobState.BINDING)
        info = self.adapter.get_project_info()
        stories = self.adapter.get_stories()
        assert_bindable(info)                       # untitled / Teamwork -> отказ
        self.binding = Binding(
            port=info.get("port", 0),
            identity=identity_fingerprint(info, stories),
            project_info=info,
            stories=stories,
        )
        self._baseline_fingerprint()
        self._set_job_state(st.JobState.BOUND)

    def _revalidate_binding(self) -> None:
        """Перед КАЖДОЙ мутацией. Несовпадение или невозможность проверки -> halt."""
        try:
            info = self.adapter.get_project_info()
            stories = self.adapter.get_stories()
        except AdapterError as e:
            # «не смогли проверить» — это не «всё ещё тот же» (M17)
            raise Halted("INSTANCE_MISMATCH: binding revalidation unavailable") from e
        assert self.binding is not None
        if not self.binding.matches(info, stories):
            raise Halted("INSTANCE_MISMATCH")

    def _baseline_fingerprint(self) -> None:
        self.state_fp = state_fingerprint(
            self.adapter.count_by_type(),
            self.adapter.get_layer_state(),
            self.adapter.list_guids(),
        )
        self.journal.append({"kind": FINGERPRINT, "state": self.state_fp})

    # ================= запуск =================

    def run(self) -> st.JobState:
        assert self.job is not None
        if self.job_state.terminal():
            return self.job_state      # повторная доставка завершённого job: no-op
        if not self.write_gate:
            raise RuntimeError("WriteGate is OFF: refusing to execute (dry-run only)")
        if self.confirm_token is None:
            raise RuntimeError("confirm_token required to execute")

        self._assert_no_unresolved()
        self._set_job_state(st.JobState.RUNNING)

        for pkg in self.job.packages:
            if pkg.state.satisfied():
                continue  # уже завершён (например, после recovery)
            if not self._pkg_ready(pkg):
                self._set_pkg_state(pkg, st.PkgState.BLOCKED)
                self._pause("DEPENDENCY_BLOCKED", pkg.id)
                return self.job_state
            self._set_pkg_state(pkg, st.PkgState.READY)
            try:
                if not self._prefix_search_available(pkg):
                    # дубли от прошлых запусков больше нечем ловить на уровне операции
                    self._assert_scope_clean(pkg)
            except Halted as h:
                self._set_pkg_state(pkg, st.PkgState.HALTED)
                self._pause(h.reason, pkg.id)
                return self.job_state
            self._set_pkg_state(pkg, st.PkgState.RUNNING)
            for key in pkg.op_keys:
                rec = self.job.ops[key]
                if rec.state.counts_as_success():
                    continue
                try:
                    self._step(rec)
                except Halted as h:
                    self._set_pkg_state(pkg, st.PkgState.HALTED)
                    self._pause(h.reason, key)
                    return self.job_state
            done = all(self.job.ops[k].state.counts_as_success() for k in pkg.op_keys)
            any_ok = any(self.job.ops[k].state.counts_as_success() for k in pkg.op_keys)
            self._set_pkg_state(
                pkg,
                st.PkgState.COMPLETED
                if done
                else (st.PkgState.PARTIAL if any_ok else st.PkgState.HALTED),
            )

        if all(r.state.counts_as_success() for r in self.job.ops.values()):
            self._set_job_state(st.JobState.COMPLETED)
        else:
            self._pause("NOT_ALL_VERIFIED", None)
        return self.job_state

    def _prefix_search_available(self, pkg: PkgRecord) -> bool:
        for key in pkg.op_keys:
            return self.matrix.get(self.job.ops[key].op["op"]).marker_search_prefix
        return False

    def _assert_scope_clean(self, pkg: PkgRecord) -> None:
        """Fallback для адаптеров без префиксного поиска: на входе в пакет
        в области (тип, этаж, слой) не должно быть элементов, не привязанных
        к этому job. Иначе мы не отличим свои элементы от наследия прошлых
        запусков и создадим дубли."""
        for key in pkg.op_keys:
            rec = self.job.ops[key]
            etype = OP_TYPE_TO_ELEMENT.get(rec.op.get("op", ""))
            if not etype:
                continue
            story = rec.op["story"]["name"]
            layer = rec.op.get("layer")
            try:
                scoped = set(self.adapter.find_by_filter(etype, story, layer))
            except AdapterError as e:
                raise Halted("PRECONDITION_FAILED: cannot verify scope", key) from e
            bound = {
                r.candidate_guid
                for r in self.job.ops.values()
                if r.map_state.readable() and r.candidate_guid
            }
            extra = scoped - bound
            if extra:
                raise Halted(
                    f"AMBIGUOUS_MATCH: {len(extra)} unexpected element(s) in scope, "
                    f"no prefix search to tell them apart",
                    key,
                )
            return  # достаточно проверить первый тип элемента пакета

    def _pkg_ready(self, pkg: PkgRecord) -> bool:
        for dep_id in pkg.depends_on:
            dep = next(p for p in self.job.packages if p.id == dep_id)
            if not dep.state.satisfied():     # PARTIAL не считается (I7)
                return False
        return True

    def _assert_no_unresolved(self) -> None:
        bad = [
            k
            for k, r in (self.job.ops.items() if self.job else [])
            if r.state.halts_job() or r.state in (st.OpState.DISPATCHED, st.OpState.MARKER_WRITING)
        ]
        if bad:
            raise Halted(f"UNRESOLVED_OPERATIONS:{bad}")

    # ================= шаг операции =================

    def _step(self, rec: OpRecord) -> None:
        if self.flight.busy:
            raise ProcessLockError("single-flight violated")
        self.flight.acquire(rec.key)
        try:
            self._precheck(rec)
            self._dispatch(rec)

            if rec.state is st.OpState.ADOPTED:
                return  # ensure-ветка: верификация уже выполнена внутри _dispatch

            if rec.state is st.OpState.UNKNOWN:
                raise Halted("OP_UNKNOWN", rec.key)

            self._marker_phase(rec)
            if rec.state in (st.OpState.MARKER_UNKNOWN, st.OpState.CREATED_UNBOUND):
                raise Halted(rec.state.value, rec.key)

            self._verify_phase(rec)
            if rec.state is st.OpState.VERIFIED_OK:
                self._commit(rec)

            # I3: любой halting-исход останавливает job, даже если исключение не брошено
            if rec.state.halts_job():
                # OpState is deliberately low-level.  Durable job pause reasons
                # are the audit taxonomy, so a failed read-back must not leak
                # the generic state name "UNAVAILABLE" into recovery evidence.
                reason = (
                    "VERIFY_UNAVAILABLE"
                    if rec.state is st.OpState.UNAVAILABLE
                    else rec.state.value
                )
                raise Halted(reason, rec.key)
        finally:
            self.flight.release()

    # -- 1. precheck

    def _precheck(self, rec: OpRecord) -> None:
        self._revalidate_binding()
        current = state_fingerprint(
            self.adapter.count_by_type(),
            self.adapter.get_layer_state(),
            self.adapter.list_guids(),
        )
        if current != self.state_fp:
            raise Halted("MODEL_DRIFT", rec.key)

        layers = self.adapter.get_layer_state()
        layer = rec.op.get("layer")
        # предусловие по слою применяется только если адаптер УМЕЕТ сообщать
        # состояние слоёв. Иначе это молчаливое «слой в порядке», то есть дырка.
        if layers.get("known", True) and (layer in layers["locked"] or layer in layers["hidden"]):
            raise Halted("PRECONDITION_FAILED: layer locked or hidden", rec.key)

        # refs обязаны резолвиться в читаемое mapping (I9)
        if "host_wall" in rec.op:
            host = self._find_by_object_id(rec.op["host_wall"])
            if host is None or not host.map_state.readable():
                raise Halted("DEPENDENCY_BLOCKED: host_wall is not confirmed", rec.key)
            # геометрический дрифт дешёвым fingerprint не ловится (элемент
            # подвинули, а состав модели тот же) — поэтому host перепроверяется
            # целевым чтением прямо перед зависимой операцией
            if host.verified_geometry_hash is not None:
                now = self._geometry_hash(host.candidate_guid)
                if now != host.verified_geometry_hash:
                    raise Halted("MODEL_DRIFT: host geometry changed", rec.key)

        # baseline для count_delta и для доказательства уникальности при adopt
        etype = OP_TYPE_TO_ELEMENT[rec.op["op"]]
        rec.baseline_counts = self.adapter.count_by_type()
        story_name = rec.op["story"]["name"]
        rec.baseline_guids = self.adapter.find_by_filter(etype, story_name, layer)

    # -- 2-5. dispatch

    def _dispatch(self, rec: OpRecord) -> None:
        if rec.idem_key in self._dispatched:
            # повторная доставка того же задания — не dispatch (M3)
            raise Halted("DUPLICATE_DELIVERY", rec.key)

        self.journal.append(
            {
                "kind": OP_INTENT,
                "job_id": self.job.job_id,
                "run_id": self.job.run_id,
                "op_key": rec.key,
                "object_id": rec.object_id,
                "op": rec.op,            # полная операция: журнал должен годиться для аудита
                "op_type": rec.op["op"],
                "nonce": rec.nonce,
                "marker": rec.marker,
                "idem_key": rec.idem_key,
                "attempt": 1,
                "request_hash": _hash(rec.op),
                "baseline_guids": rec.baseline_guids,
                "baseline_counts": rec.baseline_counts,
            }
        )
        rec.state = st.op_to(rec.state, st.OpState.DISPATCHED)
        self._dispatched[rec.idem_key] = {"ts": time.time()}

        # ENSURE: если маркер уже в модели — мутацию не отправляем (M15/B3)
        found = self.adapter.find_by_marker(exact=rec.marker)
        if len(found) == 1:
            rec.candidate_guid = found[0]
            rec.state = st.op_to(rec.state, st.OpState.ADOPTED)
            self._set_map(rec, st.MapState.ADOPTED, method="ENSURE_MARKER")
            self._verify_phase(rec)
            return
        if len(found) > 1:
            raise Halted("AMBIGUOUS_MATCH", rec.key)

        try:
            result: CreateResult = getattr(self.adapter, rec.op["op"])(rec.op)
        except AdapterError as e:
            # ЕДИНСТВЕННО допустимая трактовка сбоя dispatch — UNKNOWN (M4)
            self.journal.append(
                {
                    "kind": OP_OUTCOME,
                    "op_key": rec.key,
                    "outcome": "UNKNOWN",
                    "error": str(e),
                }
            )
            rec.state = st.op_to(rec.state, st.OpState.UNKNOWN)
            return

        self.journal.append(
            {
                "kind": OP_OUTCOME,
                "op_key": rec.key,
                "outcome": "ok",
                "candidate_guid": result.candidate_guid,
                "response_hash": _hash(result.raw),
            }
        )
        rec.candidate_guid = result.candidate_guid
        rec.state = st.op_to(rec.state, st.OpState.APPLIED_UNVERIFIED)
        # GUID из create-response — НЕ доверенный (I4)
        self._set_map(rec, st.MapState.CANDIDATE, method="CREATE_CLAIM")

    # -- 6. marker

    def _marker_phase(self, rec: OpRecord) -> None:
        cap = self.matrix.get(rec.op["op"])
        assert cap.marker_medium is not None

        # tag-guard: не тегируем элемент, личность которого не подтверждена
        try:
            details = self.adapter.get_details(rec.candidate_guid)
        except AdapterError as e:
            self.journal.append(
                {"kind": MARKER_RESULT, "op_key": rec.key, "status": "TAG_GUARD_UNAVAILABLE"}
            )
            rec.state = st.op_to(rec.state, st.OpState.CREATED_UNBOUND)
            self._set_map(rec, st.MapState.CREATED_UNBOUND)
            self._register_orphan(rec, "TAG_GUARD_UNAVAILABLE")
            return

        if details is None or details.get("type") != OP_TYPE_TO_ELEMENT.get(rec.op["op"]):
            rec.state = st.op_to(rec.state, st.OpState.CREATED_UNBOUND)
            self._set_map(rec, st.MapState.CREATED_UNBOUND)
            self._register_orphan(rec, "TAG_GUARD_TYPE_MISMATCH")
            return
        if details.get("layer") != rec.op.get("layer") or details.get("story", {}).get(
            "name"
        ) != rec.op["story"].get("name"):
            rec.state = st.op_to(rec.state, st.OpState.CREATED_UNBOUND)
            self._set_map(rec, st.MapState.CREATED_UNBOUND)
            self._register_orphan(rec, "TAG_GUARD_SCOPE_MISMATCH")
            return

        self.journal.append(
            {
                "kind": MARKER_INTENT,
                "op_key": rec.key,
                "guid": rec.candidate_guid,
                "marker": rec.marker,
                "medium": cap.marker_medium,
            }
        )
        rec.state = st.op_to(rec.state, st.OpState.MARKER_WRITING)
        self._set_map(rec, st.MapState.MARKER_PENDING)

        try:
            self.adapter.set_marker(rec.candidate_guid, rec.marker, cap.marker_medium)
        except AdapterError as e:
            # запись маркера — отдельная мутация со своим UNKNOWN (M5, E2)
            self.journal.append(
                {"kind": MARKER_RESULT, "op_key": rec.key, "status": "UNKNOWN", "error": str(e)}
            )
            rec.state = st.op_to(rec.state, st.OpState.MARKER_UNKNOWN)
            self._set_map(rec, st.MapState.CREATED_UNBOUND)
            self._register_orphan(rec, "MARKER_UNKNOWN")
            return

        # round-trip: «write вернул ok» не значит «значение записано» (E3)
        back = self.adapter.read_marker(rec.candidate_guid, cap.marker_medium)
        if back != rec.marker:
            self.journal.append(
                {
                    "kind": MARKER_RESULT,
                    "op_key": rec.key,
                    "status": "SILENT_NOOP",
                    "read_back": back,
                }
            )
            rec.state = st.op_to(rec.state, st.OpState.CREATED_UNBOUND)
            self._set_map(rec, st.MapState.CREATED_UNBOUND)
            self._register_orphan(rec, "MARKER_SILENT_NOOP")
            return

        exact = self.adapter.find_by_marker(exact=rec.marker)
        if rec.candidate_guid not in exact or len(exact) > 1:
            self.journal.append(
                {"kind": MARKER_RESULT, "op_key": rec.key, "status": "AMBIGUOUS", "hits": exact}
            )
            rec.state = st.op_to(rec.state, st.OpState.CREATED_UNBOUND)
            self._set_map(rec, st.MapState.CREATED_UNBOUND)
            self._register_orphan(rec, "MARKER_AMBIGUOUS")
            raise Halted("AMBIGUOUS_MATCH", rec.key)

        # префиксный поиск ловит дубли от предыдущих запусков (M7).
        # Если адаптер его не умеет — дубли ловятся предусловием «чистая область»
        # на входе в пакет (см. _assert_scope_clean).
        if cap.marker_search_prefix:
            prefix_hits = self.adapter.find_by_marker(
                prefix=marker_prefix(self.job.job_id, rec.object_id)
            )
            prefix_hits = list(prefix_hits)
        else:
            prefix_hits = []
        if len(prefix_hits) > 1:
            self.journal.append(
                {
                    "kind": MARKER_RESULT,
                    "op_key": rec.key,
                    "status": "DUPLICATE_FROM_PREVIOUS_RUN",
                    "hits": prefix_hits,
                }
            )
            raise Halted("AMBIGUOUS_MATCH", rec.key)

        self.journal.append({"kind": MARKER_RESULT, "op_key": rec.key, "status": "BOUND"})
        rec.state = st.op_to(rec.state, st.OpState.BOUND)
        self._set_map(rec, st.MapState.CONFIRMED, method="MARKER_ROUNDTRIP")

    # -- 7-8. read-back и верификация

    def _verify_phase(self, rec: OpRecord) -> None:
        obs, paths = self._observe(rec)
        obs["paths"] = sorted(paths)   # independence requirement оценивается внутри verify
        cap = self.matrix.get(rec.op["op"])
        spec = with_runtime_marker(rec.op["verify"], rec.marker)
        # усыновление: элемент УЖЕ был в модели, дельты нет. Дубли ловятся
        # префиксным поиском в _marker_phase и предусловием «чистая область».
        skip = {"count_delta"} if rec.state is st.OpState.ADOPTED else None
        verdict, results = evaluate(rec.op, spec, obs, cap, skip)

        mapping = {
            CheckVerdict.OK: st.OpState.VERIFIED_OK,
            CheckVerdict.FAILED: st.OpState.VERIFIED_FAILED,
            CheckVerdict.INCONCLUSIVE: st.OpState.INCONCLUSIVE,
            CheckVerdict.UNAVAILABLE: st.OpState.UNAVAILABLE,
            CheckVerdict.UNSUPPORTED: st.OpState.UNSUPPORTED,
        }[verdict]

        self.journal.append(
            {
                "kind": OP_VERDICT,
                "op_key": rec.key,
                "verdict": verdict.value,
                "paths": sorted(paths),
                "checks": [r.as_dict() for r in results],
            }
        )
        # UNSUPPORTED — capability не обеспечивает проверку; UNAVAILABLE — обеспечивает,
        # но вызов не прошёл. Оба означают расхождение матрицы с реальностью.
        if verdict in (CheckVerdict.UNSUPPORTED, CheckVerdict.UNAVAILABLE):
            self.matrix.invalidate(rec.op["op"])

        if rec.state is st.OpState.ADOPTED:
            # усыновление не требует повторной верификации структуры
            if verdict is not CheckVerdict.OK:
                rec.state = st.OpState.INCONCLUSIVE
            return

        rec.state = st.op_to(rec.state, mapping)
        if verdict is not CheckVerdict.OK:
            self._register_orphan(rec, f"VERIFY_{verdict.value}")

    def _observe(self, rec: OpRecord) -> tuple[dict[str, Any], set[str]]:
        """Независимые пути read-back. Ни один не переиспользует ответ create."""
        obs: dict[str, Any] = {}
        paths: set[str] = set()
        etype = OP_TYPE_TO_ELEMENT[rec.op["op"]]
        story_name = rec.op["story"]["name"]
        layer = rec.op.get("layer")

        # путь 1: по GUID
        try:
            d = self.adapter.get_details(rec.candidate_guid)
            if d:
                obs.update({k: v for k, v in d.items() if v is not None})
                obs["exists"] = True
                paths.add("guid")
        except AdapterError:
            pass

        # путь 2: по фильтру тип+этаж+слой
        try:
            hits = self.adapter.find_by_filter(etype, story_name, layer)
            if rec.candidate_guid in hits:
                obs["exists"] = True
                paths.add("filter")
        except AdapterError:
            pass

        # путь 3: по маркеру
        try:
            if rec.candidate_guid in self.adapter.find_by_marker(exact=rec.marker):
                obs["marker"] = rec.marker
                paths.add("marker")
        except AdapterError:
            pass

        # путь 4: счётчик по типу
        try:
            now = self.adapter.count_by_type()
            delta = {k: now.get(k, 0) - rec.baseline_counts.get(k, 0) for k in set(now) | set(rec.baseline_counts)}
            obs["count_delta"] = {k: v for k, v in delta.items() if v != 0}
            paths.add("count")
        except AdapterError:
            pass

        faults = getattr(self.adapter, "faults", None)
        if faults is not None and getattr(faults, "drop_independent_path", False):
            paths = {"guid"}                      # инъекция для теста I5
        return obs, paths

    # -- 9-10. postcheck и commit

    def _commit(self, rec: OpRecord) -> None:
        expected = rec.op["verify"].get("count_delta", {})
        got = self._observe(rec)[0].get("count_delta", {})
        if any(int(got.get(k, 0)) != int(v) for k, v in expected.items()):
            self.journal.append(
                {"kind": OP_VERDICT, "op_key": rec.key, "verdict": "FAILED", "note": "count_delta"}
            )
            rec.state = st.OpState.VERIFIED_FAILED
            self._register_orphan(rec, "COUNT_DELTA_MISMATCH")
            raise Halted("VERIFIED_FAILED", rec.key)

        self.journal.append(
            {
                "kind": OP_COMMIT,
                "op_key": rec.key,
                "guid": rec.candidate_guid,
                "map_state": rec.map_state.value,
                "method": rec.mapping_method,
            }
        )
        # снимок геометрии — для целевой перепроверки зависимыми операциями
        rec.verified_geometry_hash = self._geometry_hash(rec.candidate_guid)
        self._baseline_fingerprint()
        self._snapshot()

    # ================= паузы, orphan, snapshot =================

    def _pause(self, reason: str, where: str | None) -> None:
        self.paused_reason = reason
        self._set_job_state(st.JobState.PAUSED)
        self.journal.append({"kind": JOB_STATE, "state": "PAUSED", "reason": reason, "at": where})
        self._snapshot()

    def _register_orphan(self, rec: OpRecord, reason: str) -> None:
        entry = {
            "op_key": rec.key,
            "object_id": rec.object_id,
            "candidate_guid": rec.candidate_guid,
            "marker": rec.marker,
            "story": rec.op.get("story", {}).get("name"),
            "layer": rec.op.get("layer"),
            "reason": reason,
            "cleaned": False,
        }
        self.orphans.append(entry)
        self.journal.append({"kind": ORPHAN, **entry})

    def _set_map(self, rec: OpRecord, new: st.MapState, method: str | None = None) -> None:
        rec.map_state = st.map_to(rec.map_state, new)
        if method:
            rec.mapping_method = method

    def _set_job_state(self, new: st.JobState) -> None:
        self.job_state = st.job_to(self.job_state, new)
        self.journal.append({"kind": JOB_STATE, "state": new.value})

    def _set_pkg_state(self, pkg: PkgRecord, new: st.PkgState) -> None:
        pkg.state = st.pkg_to(pkg.state, new)
        self.journal.append({"kind": PKG_STATE, "pkg": pkg.id, "state": new.value})

    def _snapshot(self) -> None:
        assert self.job is not None
        write_snapshot(
            self.snapshot_path,
            {
                "job_id": self.job.job_id,
                "run_id": self.job.run_id,
                "plan_hash": self.job.plan_hash,
                "job_state": self.job_state.value,
                "paused_reason": self.paused_reason,
                "state_fp": self.state_fp,
                "packages": {p.id: p.state.value for p in self.job.packages},
                "ops": {
                    k: {
                        "state": r.state.value,
                        "map": r.map_state.value,
                        "method": r.mapping_method,
                        "guid": r.candidate_guid,
                    }
                    for k, r in self.job.ops.items()
                },
                "orphans": self.orphans,
            },
        )

    # ================= recovery =================

    def _load(self) -> None:
        """Восстановление состояния из journal. INTENT без OUTCOME = UNKNOWN."""
        if not os.path.exists(self.journal_path):
            self.journal.open()
            return
        self.journal.open()
        events = self.journal.read_all()
        for e in events:
            kind = e.get("kind")
            if kind == JOB_CREATED:
                continue
        if not events:
            return

        created = next((e for e in events if e.get("kind") == JOB_CREATED), None)
        if created is None:
            return

        packages = [
            PkgRecord(id=pid, index=i, depends_on=[], op_keys=[])
            for i, pid in enumerate(created["packages"])
        ]
        ops: dict[str, OpRecord] = {}
        for key, meta in created["ops"].items():
            pkg_id, object_id = key.split("/", 1)
            ops[key] = OpRecord(
                key=key,
                pkg_id=pkg_id,
                index=0,
                op={},
                object_id=object_id,
                nonce=meta["nonce"],
                idem_key=meta["idem_key"],
                marker=make_marker(created["job_id"], object_id, meta["nonce"]),
                state=st.OpState.PLANNED,
            )
            pkg = next(p for p in packages if p.id == pkg_id)
            pkg.op_keys.append(key)

        # разворачиваем историю операций
        for e in events:
            k, key = e.get("kind"), e.get("op_key")
            if key not in ops:
                continue
            rec = ops[key]
            if k == OP_INTENT:
                rec.op = e.get("op", {}) or rec.op
                rec.baseline_guids = e.get("baseline_guids", [])
                rec.baseline_counts = e.get("baseline_counts", {})
                rec.state = st.OpState.DISPATCHED
                self._dispatched[rec.idem_key] = {"ts": e.get("ts")}
            elif k == OP_OUTCOME:
                if e.get("outcome") == "ok":
                    rec.state = st.OpState.APPLIED_UNVERIFIED
                    rec.candidate_guid = e.get("candidate_guid")
                    rec.map_state = st.MapState.CANDIDATE
                else:
                    rec.state = st.OpState.UNKNOWN
            elif k == MARKER_INTENT:
                if rec.state is st.OpState.APPLIED_UNVERIFIED:
                    rec.state = st.OpState.MARKER_WRITING
                    rec.map_state = st.MapState.MARKER_PENDING
            elif k == MARKER_RESULT:
                if e.get("status") == "BOUND":
                    rec.state = st.OpState.BOUND
                    rec.map_state = st.MapState.CONFIRMED
                    rec.mapping_method = "MARKER_ROUNDTRIP"
                elif e.get("status") == "UNKNOWN":
                    rec.state = st.OpState.MARKER_UNKNOWN
                    rec.map_state = st.MapState.CREATED_UNBOUND
                else:
                    rec.state = st.OpState.CREATED_UNBOUND
                    rec.map_state = st.MapState.CREATED_UNBOUND
            elif k == OP_VERDICT:
                try:
                    rec.state = st.OpState(e["verdict"])
                except ValueError:
                    pass
            elif k == OP_COMMIT:
                rec.state = st.OpState.VERIFIED_OK
                rec.candidate_guid = e.get("guid")
                rec.map_state = st.MapState(e["map_state"])
                rec.mapping_method = e.get("method")

        for e in events:
            if e.get("kind") == FINGERPRINT:
                self.state_fp = e["state"]
            elif e.get("kind") == PKG_STATE:
                pkg = next((p for p in packages if p.id == e.get("pkg")), None)
                if pkg is not None:
                    try:
                        pkg.state = st.PkgState(e["state"])
                    except ValueError:
                        pass
            elif e.get("kind") == JOB_STATE:
                try:
                    self.job_state = st.JobState(e["state"])
                except ValueError:
                    pass
                if e.get("state") == "PAUSED":
                    self.paused_reason = e.get("reason")
            elif e.get("kind") == ORPHAN:
                self.orphans.append({k: v for k, v in e.items() if k != "kind"})

        self.job = JobRecord(
            job_id=created["job_id"],
            run_id=created["run_id"],
            plan_hash=created["plan_hash"],
            packages=packages,
            ops=ops,
        )

    def startup(self) -> None:
        """Вызывается один раз при старте Router: singleton процесса."""
        self.lock.acquire()

    def recover(self) -> bool:
        """True, если после восстановления job требует реконсиляции."""
        self._load()
        if self.job is None:
            return False
        unresolved = [
            r
            for r in self.job.ops.values()
            if r.state in {st.OpState.DISPATCHED, st.OpState.UNKNOWN}
            or r.state.halts_job()
        ]
        if unresolved:
            self.paused_reason = self.paused_reason or "RECOVERY_REQUIRED"
            if self.job_state is not st.JobState.PAUSED:
                self.job_state = st.JobState.PAUSED
            return True
        return False

    def reconcile(self) -> dict[str, Any]:
        """Read-only сверка journal с фактической моделью. Мутаций нет (M23)."""
        assert self.job is not None
        self.job_state = st.job_to(self.job_state, st.JobState.RECONCILING)
        report: dict[str, Any] = {"ops": {}, "read_only": True}

        for rec in self.job.ops.values():
            if rec.state.counts_as_success():
                continue
            etype = OP_TYPE_TO_ELEMENT.get(rec.op.get("op", ""), "")
            story = (rec.op.get("story") or {}).get("name", "")
            layer = rec.op.get("layer")

            entry: dict[str, Any] = {"state": rec.state.value}
            try:
                hits_exact = self.adapter.find_by_marker(exact=rec.marker)
                hits_prefix = self.adapter.find_by_marker(
                    prefix=marker_prefix(self.job.job_id, rec.object_id)
                )
                details = (
                    self.adapter.get_details(rec.candidate_guid)
                    if rec.candidate_guid
                    else None
                )
                scoped = self.adapter.find_by_filter(etype, story, layer) if etype else []
            except AdapterError as e:
                entry["classification"] = "UNKNOWN_REMAINS"
                entry["note"] = f"read-back unavailable: {e}"
                report["ops"][rec.key] = entry
                continue

            if len(hits_exact) == 1:
                entry["classification"] = "APPLIED_BOUND"
                entry["guid"] = hits_exact[0]
            elif len(hits_exact) > 1 or len(hits_prefix) > 1:
                entry["classification"] = "AMBIGUOUS"
                entry["hits"] = hits_prefix
            else:
                baseline = set(rec.baseline_guids)
                fresh = [g for g in scoped if g not in baseline]
                if details is not None and rec.candidate_guid:
                    entry["classification"] = "APPLIED_UNBOUND"
                    entry["guid"] = rec.candidate_guid
                elif len(fresh) == 1:
                    # уникальность доказана: всё остальное в scope уже связано с нами (M15)
                    entry["classification"] = "APPLIED_ADOPTABLE_BY_ANCHOR"
                    entry["guid"] = fresh[0]
                elif len(fresh) > 1:
                    entry["classification"] = "AMBIGUOUS"
                    entry["hits"] = fresh
                else:
                    entry["classification"] = "NOT_APPLIED"
            report["ops"][rec.key] = entry

        self.reports.append(report)
        return report

    def resume(self, decisions: dict[str, str]) -> st.JobState:
        """decisions: {op_key: 'adopt' | 'not_applied' | 'abort'} — решение человека."""
        assert self.job is not None
        for key, decision in decisions.items():
            rec = self.job.ops[key]
            self.journal.append(
                {"kind": OP_DECISION, "op_key": key, "decision": decision, "by": "human"}
            )
            if decision == "adopt":
                if rec.state is st.OpState.MARKER_UNKNOWN:
                    rec.state = st.OpState.ADOPTED
                    rec.map_state = st.MapState.CONFIRMED
                    rec.mapping_method = "RECONCILE_MARKER"
                else:
                    rec.state = st.op_to(rec.state, st.OpState.ADOPTED)
                    self._set_map(rec, st.MapState.ADOPTED, method="RECONCILE_ANCHOR")
            elif decision == "not_applied":
                rec.state = st.op_to(rec.state, st.OpState.NOT_APPLIED_ASSERTED)
                rec.map_state = st.MapState.ORPHAN
            elif decision == "abort":
                self.job_state = st.job_to(self.job_state, st.JobState.QUARANTINED)
                self._snapshot()
                return self.job_state

        # после усыновления модель уже содержит элемент — fingerprint надо перебазировать,
        # иначе следующий шаг увидит собственное изменение как MODEL_DRIFT
        self.paused_reason = None
        self._baseline_fingerprint()
        self.job_state = st.JobState.BOUND
        self._set_job_state(st.JobState.READY)
        return self.job_state

    # ================= утилиты =================

    def _geometry_hash(self, guid: str | None) -> str | None:
        if not guid:
            return None
        try:
            d = self.adapter.get_details(guid)
        except AdapterError:
            return None
        if not d:
            return None
        return _hash({k: d.get(k) for k in ("type", "story", "layer", "ref_line", "height", "thickness")})

    def _find_by_object_id(self, object_id: str) -> OpRecord | None:
        for r in (self.job.ops.values() if self.job else []):
            if r.object_id == object_id:
                return r
        return None

    def close(self) -> None:
        self.journal.close()
        self.lock.release()
