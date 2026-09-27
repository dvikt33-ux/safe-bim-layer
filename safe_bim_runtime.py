"""SQLite-backed resumable executor for Safe BIM operations.

The executor owns persistence and state transitions.  BIM writes remain in
SafeBIMLayer (or another injected operation adapter), and every write is
checkpointed before dispatch and read back before DONE.
"""
from __future__ import annotations

import json
import hashlib
import uuid
import sqlite3
import threading
import time

from safe_bim_lock import execution_lock
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Iterable


class JobStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"
    WAITING_USER = "WAITING_USER"
    UNKNOWN_OUTCOME = "UNKNOWN_OUTCOME"
    PAUSED = "PAUSED"
    CANCELLED = "CANCELLED"


TERMINAL = {JobStatus.DONE, JobStatus.FAILED, JobStatus.CANCELLED}


class ExecutorError(RuntimeError):
    pass


class ProjectMismatch(ExecutorError):
    pass


class LeaseLost(ExecutorError):
    execution_control = True


class WorkerPaused(ExecutorError):
    execution_control = True


def valid_job_id(value):
    return (isinstance(value, str) and 0 < len(value) <= 128 and value != "active"
            and value == value.strip() and not any(ord(c) < 32 or c in "/\\" for c in value))


@dataclass(frozen=True)
class StepSpec:
    name: str
    operation: str
    params: dict[str, Any]
    floor_index: int | None = None


class SQLiteCheckpointStore:
    def __init__(self, path: str | Path):
        self.path = str(path)
        self._lock = threading.RLock()
        self._init_schema()

    @contextmanager
    def _connect(self):
        db = sqlite3.connect(self.path, timeout=30)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA journal_mode=WAL")
        try:
            with db:
                yield db
        finally:
            db.close()

    def _init_schema(self):
        with self._connect() as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                task_name TEXT NOT NULL,
                project_path TEXT NOT NULL,
                status TEXT NOT NULL,
                current_step INTEGER NOT NULL DEFAULT 0,
                total_steps INTEGER NOT NULL,
                pause_requested INTEGER NOT NULL DEFAULT 0,
                cancel_requested INTEGER NOT NULL DEFAULT 0,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS steps (
                job_id TEXT NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
                position INTEGER NOT NULL,
                name TEXT NOT NULL,
                operation TEXT NOT NULL,
                params_json TEXT NOT NULL,
                floor_index INTEGER,
                status TEXT NOT NULL,
                attempts INTEGER NOT NULL DEFAULT 0,
                checkpoint_json TEXT,
                result_json TEXT,
                error TEXT,
                updated_at REAL NOT NULL,
                PRIMARY KEY (job_id, position)
            );
            CREATE TABLE IF NOT EXISTS events (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT NOT NULL,
                position INTEGER,
                event TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at REAL NOT NULL
            );
            """)
            db.execute("BEGIN IMMEDIATE")
            columns = {row[1] for row in db.execute("PRAGMA table_info(jobs)")}
            for name in ("generation", "revision"):
                if name not in columns:
                    db.execute(f"ALTER TABLE jobs ADD COLUMN {name} INTEGER NOT NULL DEFAULT 0")

    def create_job(self, job_id: str, task_name: str, project_path: str,
                   steps: Iterable[StepSpec]):
        specs = list(steps)
        if not valid_job_id(job_id) or not isinstance(project_path, str) or not project_path.strip():
            raise ExecutorError("explicit valid job_id and project_path required")
        if not specs:
            raise ExecutorError("job requires at least one step")
        for spec in specs:
            if (not isinstance(spec.name, str) or not spec.name or not isinstance(spec.operation, str)
                    or not isinstance(spec.params, dict) or
                    (spec.floor_index is not None and type(spec.floor_index) is not int)):
                raise ExecutorError("invalid step specification")
            json.dumps(spec.params, allow_nan=False)
        now = time.time()
        with self._lock, self._connect() as db:
            db.execute(
                "INSERT INTO jobs(job_id,task_name,project_path,status,current_step,total_steps,"
                "pause_requested,cancel_requested,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (job_id, task_name, str(Path(project_path)), JobStatus.PENDING.value,
                 0, len(specs), 0, 0, now, now),
            )
            db.executemany(
                "INSERT INTO steps VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                [(job_id, i, s.name, s.operation,
                  json.dumps(s.params, ensure_ascii=False, sort_keys=True),
                  s.floor_index, JobStatus.PENDING.value, 0, None, None, None, now)
                 for i, s in enumerate(specs)],
            )
            self._event(db, job_id, None, "JOB_CREATED", {"steps": len(specs)})

    @staticmethod
    def _event(db, job_id, position, event, payload):
        db.execute(
            "INSERT INTO events(job_id,position,event,payload_json,created_at) VALUES(?,?,?,?,?)",
            (job_id, position, event,
             json.dumps(payload, ensure_ascii=False, sort_keys=True), time.time()),
        )

    def job(self, job_id: str) -> dict[str, Any]:
        with self._connect() as db:
            row = db.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone()
            if row is None:
                raise ExecutorError(f"unknown job {job_id}")
            out = dict(row)
            out["steps"] = [self._decode_step(r) for r in db.execute(
                "SELECT * FROM steps WHERE job_id=? ORDER BY position", (job_id,))]
            return out

    def latest_job_id(self) -> str:
        with self._connect() as db:
            row = db.execute(
                "SELECT job_id FROM jobs ORDER BY updated_at DESC LIMIT 1").fetchone()
            if row is None:
                raise ExecutorError("no jobs")
            return row["job_id"]

    def jobs(self, limit: int = 8) -> list[dict[str, Any]]:
        limit = max(1, min(int(limit), 50))
        with self._connect() as db:
            rows = db.execute(
                "SELECT job_id,task_name,status,current_step,total_steps,created_at,updated_at "
                "FROM jobs ORDER BY updated_at DESC LIMIT ?", (limit,)).fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def _decode_step(row):
        value = dict(row)
        for source, target in (("params_json", "params"),
                               ("checkpoint_json", "checkpoint"),
                               ("result_json", "result")):
            raw = value.pop(source)
            value[target] = json.loads(raw) if raw else None
        return value

    def _check(self, db, job_id, lease=None, revision=None):
        db.execute("BEGIN IMMEDIATE")
        row = db.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone()
        if row is None:
            raise ExecutorError(f"unknown job {job_id}")
        if revision is not None and row["revision"] != revision:
            raise ExecutorError("stale job revision; refresh state")
        if lease is not None and (row["generation"] != lease or
                JobStatus(row["status"]) in TERMINAL or row["cancel_requested"]):
            raise LeaseLost("execution lease revoked")
        return row

    @staticmethod
    def _touch(db, job_id):
        db.execute("UPDATE jobs SET revision=revision+1,updated_at=? WHERE job_id=?",
                   (time.time(), job_id))

    def claim(self, job_id, revision=None):
        with self._lock, self._connect() as db:
            row = self._check(db, job_id, revision=revision)
            if JobStatus(row["status"]) in TERMINAL:
                return None
            if row["cancel_requested"]:
                db.execute("UPDATE jobs SET status='CANCELLED',generation=generation+1 WHERE job_id=?", (job_id,))
                self._touch(db, job_id)
                return None
            lease = row["generation"] + 1
            db.execute("UPDATE jobs SET generation=?,status='RUNNING',pause_requested=0 WHERE job_id=?",
                       (lease, job_id))
            self._touch(db, job_id)
            self._event(db, job_id, None, "EXECUTION_ADMITTED", {"lease": lease})
            return lease

    def check_lease(self, job_id, lease, dispatch=False):
        with self._lock, self._connect() as db:
            row = self._check(db, job_id, lease)
            if dispatch and row["pause_requested"]:
                raise WorkerPaused("pause requested before dispatch")

    def set_job(self, job_id: str, status: JobStatus, *, lease=None, **flags):
        allowed = {"pause_requested", "cancel_requested", "current_step"}
        if set(flags) - allowed:
            raise ExecutorError("unsupported job field")
        with self._lock, self._connect() as db:
            row = self._check(db, job_id, lease)
            if JobStatus(row["status"]) in TERMINAL:
                return False
            fields = ["status=?"] + [f"{key}=?" for key in flags]
            db.execute(f"UPDATE jobs SET {','.join(fields)} WHERE job_id=?",
                       [status.value, *flags.values(), job_id])
            self._touch(db, job_id)
            self._event(db, job_id, flags.get("current_step"), "JOB_STATUS", {"status": status.value, **flags})
            return True

    def checkpoint_before_write(self, job_id, position, payload, *, lease=None):
        checkpoint = {"version": 1, "attemptId": uuid.uuid4().hex, "job_id": job_id, "position": position,
                      "phase": "BEFORE_WRITE", "dispatchStarted": False, "payload": payload, "at": time.time()}
        with self._lock, self._connect() as db:
            row = self._check(db, job_id, lease)
            if JobStatus(row["status"]) in TERMINAL:
                raise LeaseLost("terminal job")
            if row["pause_requested"]:
                raise WorkerPaused("pause requested")
            previous = db.execute("SELECT attempts FROM steps WHERE job_id=? AND position=?", (job_id, position)).fetchone()
            if previous is None:
                raise ExecutorError("unknown step")
            checkpoint["attempt"] = previous[0] + 1
            db.execute("UPDATE steps SET status=?,attempts=attempts+1,checkpoint_json=?,"
                       "result_json=NULL,error=NULL,updated_at=? WHERE job_id=? AND position=?",
                       (JobStatus.RUNNING.value, json.dumps(checkpoint, ensure_ascii=False, allow_nan=False),
                        time.time(), job_id, position))
            self._touch(db, job_id)
            self._event(db, job_id, position, "CHECKPOINT_BEFORE_WRITE", checkpoint)

    def replace_pending_step(self, job_id, position, specs, lease):
        """Replace one undispatched step with resumable single-item steps. No BIM call."""
        specs = list(specs)
        if not specs:
            raise ExecutorError("expansion produced no steps")
        with self._lock, self._connect() as db:
            self._check(db, job_id, lease)
            rows = db.execute(
                "SELECT * FROM steps WHERE job_id=? ORDER BY position", (job_id,)).fetchall()
            target = next((row for row in rows if row["position"] == position), None)
            if target is None:
                raise ExecutorError("unknown step")
            if target["status"] != JobStatus.PENDING.value or target["checkpoint_json"] or target["attempts"]:
                raise ExecutorError("refusing to expand a step that may already have been dispatched")
            rebuilt = []
            for row in rows:
                if row["position"] == position:
                    rebuilt.extend(specs)
                else:
                    rebuilt.append(row)
            db.execute("DELETE FROM steps WHERE job_id=?", (job_id,))
            now = time.time()
            for index, item in enumerate(rebuilt):
                if isinstance(item, StepSpec):
                    db.execute(
                        "INSERT INTO steps VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                        (job_id, index, item.name, item.operation,
                         json.dumps(item.params, ensure_ascii=False, sort_keys=True),
                         item.floor_index, JobStatus.PENDING.value, 0, None, None, None, now))
                else:
                    db.execute(
                        "INSERT INTO steps VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                        (job_id, index, item["name"], item["operation"], item["params_json"],
                         item["floor_index"], item["status"], item["attempts"], item["checkpoint_json"],
                         item["result_json"], item["error"], now))
            db.execute("UPDATE jobs SET total_steps=?,updated_at=? WHERE job_id=?", (len(rebuilt), now, job_id))
            self._touch(db, job_id)
            self._event(db, job_id, position, "STEP_EXPANDED", {"count": len(specs)})

    def update_checkpoint(self, job_id, position, lease, *, prepared=None, command=None, policy_denied=False):
        with self._lock, self._connect() as db:
            row = self._check(db, job_id, lease)
            if command and row["pause_requested"]:
                raise WorkerPaused("pause requested before physical dispatch")
            step = db.execute("SELECT checkpoint_json FROM steps WHERE job_id=? AND position=?", (job_id, position)).fetchone()
            checkpoint = json.loads(step[0])
            if prepared is not None:
                checkpoint["payload"]["prepared"] = prepared
                checkpoint["payload"]["expectedZFingerprint"] = prepared.get("expectedZFingerprint")
            if policy_denied:
                checkpoint["policyDenied"] = True
                checkpoint["dispatchStarted"] = False
            if command:
                checkpoint["dispatchStarted"] = True
                checkpoint["lastCommand"] = command
                checkpoint["dispatchCount"] = checkpoint.get("dispatchCount", 0) + 1
            db.execute("UPDATE steps SET checkpoint_json=?,updated_at=? WHERE job_id=? AND position=?",
                       (json.dumps(checkpoint, ensure_ascii=False, allow_nan=False), time.time(), job_id, position))
            self._touch(db, job_id)
            self._event(db, job_id, position, "DISPATCH_ADMITTED" if command else "PREFLIGHT_PREPARED", checkpoint)

    def set_step(self, job_id, position, status, result=None, error=None, *, lease=None):
        with self._lock, self._connect() as db:
            row = self._check(db, job_id, lease)
            if JobStatus(row["status"]) in TERMINAL:
                return False
            db.execute("UPDATE steps SET status=?,result_json=?,error=?,updated_at=? WHERE job_id=? AND position=?",
                       (status.value, json.dumps(result, ensure_ascii=False, allow_nan=False) if result is not None else None,
                        error, time.time(), job_id, position))
            self._touch(db, job_id)
            self._event(db, job_id, position, "STEP_STATUS", {"status": status.value, "error": error})
            return True

    def control(self, job_id, action, revision=None):
        with self._lock, self._connect() as db:
            row = self._check(db, job_id, revision=revision)
            status = JobStatus(row["status"])
            if status in TERMINAL:
                return status
            if action == "stop":
                db.execute("UPDATE jobs SET status='CANCELLED',cancel_requested=1,generation=generation+1 WHERE job_id=?", (job_id,))
                status = JobStatus.CANCELLED
            elif action == "pause":
                status = JobStatus.RUNNING if status == JobStatus.RUNNING else JobStatus.PAUSED
                db.execute("UPDATE jobs SET status=?,pause_requested=1 WHERE job_id=?", (status.value, job_id))
            else:
                raise ExecutorError("invalid control")
            self._touch(db, job_id)
            self._event(db, job_id, None, action.upper(), {"status": status.value})
            return status

    def request(self, job_id, field):
        if field not in {"pause_requested", "cancel_requested"}:
            raise ExecutorError("invalid request")
        return self.control(job_id, "pause" if field == "pause_requested" else "stop")


class ResumableExecutor:
    def __init__(self, store, execute, reconcile, current_project):
        self.store = store
        self.execute_operation = execute
        self.reconcile_operation = reconcile
        self.current_project = current_project
        adapter = getattr(execute, "__self__", None)
        self.adapter = adapter if hasattr(adapter, "execution_context") else None

    def resolve_job_id(self, job_id):
        if job_id != "active":
            if not valid_job_id(job_id):
                raise ExecutorError("explicit valid job_id required")
            return job_id
        with self.store._connect() as db:
            row = db.execute("""SELECT job_id FROM jobs ORDER BY CASE status
                WHEN 'RUNNING' THEN 0 WHEN 'WAITING_USER' THEN 1
                WHEN 'UNKNOWN_OUTCOME' THEN 2 WHEN 'PAUSED' THEN 3
                WHEN 'PENDING' THEN 4 ELSE 5 END, updated_at DESC, job_id LIMIT 1""").fetchone()
            if not row:
                raise ExecutorError("no jobs")
            return row[0]

    def _assert_project(self, job):
        current = self.current_project()
        if not isinstance(current, str) or not current.strip():
            raise ProjectMismatch("current project identity unavailable")
        expected = str(Path(job["project_path"]).resolve()).casefold()
        actual = str(Path(current).resolve()).casefold()
        if expected != actual:
            raise ProjectMismatch(f"expected open PLN {expected!r}, got {actual!r}")

    @staticmethod
    def _has_readback(result):
        return (isinstance(result, dict) and result.get("readbackVerified") is True
                and result.get("status") in {"PASS", "DONE"}
                and isinstance(result.get("readback"), list) and bool(result["readback"]))

    def _state(self, job_id):
        return JobStatus(self.store.job(job_id)["status"])

    def run(self, job_id, expected_revision=None):
        return self._admit(job_id, False, expected_revision)

    def resume(self, job_id, expected_revision=None):
        return self._admit(job_id, True, expected_revision)

    def _admit(self, job_id, recover, revision):
        # 'active' is a READ alias only. No destructive action may resolve latest.
        if not valid_job_id(job_id):
            raise ExecutorError("commands require explicit job_id, not active")
        job = self.store.job(job_id)
        if revision is not None and revision != job["revision"]:
            raise ExecutorError("stale job revision; refresh state")
        if JobStatus(job["status"]) in TERMINAL:
            return JobStatus(job["status"])
        with execution_lock(self.store.path) as owned:
            if not owned:
                return self._state(job_id)
            lease = self.store.claim(job_id, revision)
            if lease is None:
                return self._state(job_id)
            try:
                return self._drive(job_id, lease, recover)
            except LeaseLost:
                return self._state(job_id)
            except WorkerPaused:
                try:
                    self.store.set_job(job_id, JobStatus.PAUSED, lease=lease)
                except LeaseLost:
                    pass
                return self._state(job_id)

    def _boundary(self, job_id, lease):
        self.store.check_lease(job_id, lease, dispatch=True)

    def _wait(self, job_id, position, lease, error, unknown=False, result=None):
        status = JobStatus.UNKNOWN_OUTCOME if unknown else JobStatus.WAITING_USER
        evidence = dict(result or {})
        evidence.update(status=status.value, retryAllowed=False, error=str(error))
        self.store.set_step(job_id, position, status, result=evidence, lease=lease)
        self.store.set_job(job_id, status, current_step=position, lease=lease)
        return status

    def _expand_wall_loops(self, job_id, lease):
        if self.adapter is None:
            return None
        while True:
            self._boundary(job_id, lease)
            pending = [step for step in self.store.job(job_id)["steps"]
                       if step["operation"] == "create_wall_loop" and step["status"] == JobStatus.PENDING.value
                       and not step.get("checkpoint")]
            if not pending:
                return None
            step = pending[0]
            try:
                prepared = self.adapter.prepare("create_wall_loop", step["params"])
                walls = prepared["payload"]["wallsData"]
                if not isinstance(walls, list) or len(walls) < 1:
                    raise ExecutorError("wall loop produced no segments")
                specs = [StepSpec(
                    f"{step['name']}:{index + 1}", "create_wall_segment",
                    {"start": wall["begCoordinate"], "end": wall["endCoordinate"],
                     "floor_index": wall["floorIndex"], "height": wall["height"],
                     "thickness": wall["thickness"]}, wall["floorIndex"])
                    for index, wall in enumerate(walls)]
            except (LeaseLost, WorkerPaused):
                raise
            except Exception as exc:
                return self._wait(job_id, step["position"], lease, exc)
            self.store.replace_pending_step(job_id, step["position"], specs, lease)

    def _drive(self, job_id, lease, recover):
        stopped = self._expand_wall_loops(job_id, lease)
        if stopped is not None:
            return stopped
        for initial in self.store.job(job_id)["steps"]:
            self._boundary(job_id, lease)
            step = self.store.job(job_id)["steps"][initial["position"]]
            pos = step["position"]
            if step["status"] == JobStatus.DONE.value:
                continue
            uncertain = step["status"] in {"RUNNING", "UNKNOWN_OUTCOME", "WAITING_USER"}
            if uncertain:
                if not recover:
                    return self._wait(job_id, pos, lease, "reconciliation required", unknown=step["status"] == "RUNNING", result=step.get("result"))
                previous = {"checkpoint": step["checkpoint"], "result": step["result"],
                            "job_id": job_id, "position": pos, "attempt": step["attempts"],
                            "projectPath": self.store.job(job_id)["project_path"]}
                try:
                    self._assert_project(self.store.job(job_id))
                    evidence = self.reconcile_operation(step["operation"], step["params"], previous)
                    self._assert_project(self.store.job(job_id))
                    self._boundary(job_id, lease)
                    if not isinstance(evidence, dict):
                        raise ExecutorError("malformed reconciliation")
                except (LeaseLost, WorkerPaused):
                    raise
                except Exception as exc:
                    return self._wait(job_id, pos, lease, exc, result=step.get("result"))
                if evidence.get("classification") == "APPLIED" and self._has_readback(evidence):
                    self.store.set_step(job_id, pos, JobStatus.DONE, result=evidence, lease=lease)
                    continue
                if not (evidence.get("classification") == "NOT_APPLIED" and evidence.get("absenceProven") is True):
                    # Retain any sealed receipt for future read-only reconciliation.
                    retained = dict(step.get("result") or {})
                    retained["classification"] = "AMBIGUOUS"
                    retained["reconciliation"] = evidence
                    return self._wait(job_id, pos, lease, "ambiguous outcome; no retry", result=retained)
                self.store.set_step(job_id, pos, JobStatus.PENDING, result=evidence, lease=lease)
            self._boundary(job_id, lease)
            payload = {"operation": step["operation"], "params": step["params"],
                       "floorIndex": step["floor_index"], "projectPath": self.store.job(job_id)["project_path"],
                       "expectedZFingerprint": None}
            self.store.set_job(job_id, JobStatus.RUNNING, current_step=pos, lease=lease)
            self.store.checkpoint_before_write(job_id, pos, payload, lease=lease)
            try:
                self._assert_project(self.store.job(job_id))
                self._boundary(job_id, lease)
                if self.adapter:
                    prepared = self.adapter.prepare(step["operation"], step["params"])
                    attempt = self.store.job(job_id)["steps"][pos]
                    prepared["executionIdentity"] = {"job_id": job_id, "position": pos,
                        "attempt": attempt["attempts"], "attempt_id": attempt["checkpoint"]["attemptId"],
                        "projectPath": payload["projectPath"]}
                    prepared.pop("contractHash", None)
                    prepared["contractHash"] = hashlib.sha256(json.dumps(prepared, sort_keys=True,
                        ensure_ascii=False, allow_nan=False).encode()).hexdigest()
                    self.store.update_checkpoint(job_id, pos, lease, prepared=prepared)
                    from safe_bim_command_policy import PolicyError, assert_single_create_item
                    try:
                        assert_single_create_item(prepared["command"], prepared["payload"])
                    except PolicyError as exc:
                        self.store.update_checkpoint(job_id, pos, lease, policy_denied=True)
                        return self._wait(job_id, pos, lease, exc)
                    def before_write(command, _payload):
                        self._boundary(job_id, lease)
                        self._assert_project(self.store.job(job_id))
                        self._boundary(job_id, lease)
                        self.store.update_checkpoint(job_id, pos, lease, command=command)
                    def verified_receipt(result):
                        self._assert_project(self.store.job(job_id))
                        self.store.set_step(job_id, pos, JobStatus.RUNNING, result=result, lease=lease)
                    with self.adapter.execution_context(prepared, before_write, verified_receipt):
                        result = self.execute_operation(step["operation"], step["params"])
                else:
                    # Injected callbacks are trusted adapters; conservatively assume dispatch
                    # as soon as called. They must explicitly attest complete verification.
                    self._assert_project(self.store.job(job_id))
                    self.store.update_checkpoint(job_id, pos, lease, command=step["operation"])
                    result = self.execute_operation(step["operation"], step["params"])
                self.store.check_lease(job_id, lease)
                self._assert_project(self.store.job(job_id))
                if not self._has_readback(result):
                    raise ExecutorError(result.get("error", "complete operation-specific read-back not verified") if isinstance(result, dict) else "malformed operation result")
                self.store.set_step(job_id, pos, JobStatus.DONE, result=result, lease=lease)
            except (LeaseLost, WorkerPaused):
                raise
            except Exception as exc:
                persisted = self.store.job(job_id)["steps"][pos]
                started = (persisted["checkpoint"] or {}).get("dispatchStarted", True)
                return self._wait(job_id, pos, lease, exc, unknown=started, result=persisted.get("result"))
            self._boundary(job_id, lease)
        self._boundary(job_id, lease)
        self.store.set_job(job_id, JobStatus.DONE, current_step=self.store.job(job_id)["total_steps"], lease=lease)
        return JobStatus.DONE

    def pause(self, job_id, expected_revision=None):
        if not valid_job_id(job_id):
            raise ExecutorError("commands require explicit job_id")
        return self.store.control(job_id, "pause", expected_revision)

    def stop(self, job_id, expected_revision=None):
        if not valid_job_id(job_id):
            raise ExecutorError("commands require explicit job_id")
        return self.store.control(job_id, "stop", expected_revision)

    def palette_state(self, job_id):
        requested = job_id
        job_id = self.resolve_job_id(job_id)
        job = self.store.job(job_id)
        position = min(job["current_step"], max(0, job["total_steps"] - 1))
        step = job["steps"][position]
        terminal = JobStatus(job["status"]) in TERMINAL
        return {"job_id": job_id, "revision": job["revision"], "task": job["task_name"],
                "status": job["status"], "step": step["name"],
                "progress": f"{min(position + 1, job['total_steps'])} из {job['total_steps']}",
                "floor": step["floor_index"],
                "readback": "Подтверждён" if self._has_readback(step.get("result")) else "Не подтверждён",
                "enum": job["status"], "selection": "current" if requested == "active" and not terminal else "history",
                "history": self.store.jobs(8),
                "controls": {"continue": not terminal and job["status"] != "RUNNING",
                             "pause": job["status"] in {"RUNNING", "PENDING"}, "stop": not terminal}}
