"""SQLite-backed resumable executor for Safe BIM operations.

The executor owns persistence and state transitions.  BIM writes remain in
SafeBIMLayer (or another injected operation adapter), and every write is
checkpointed before dispatch and read back before DONE.
"""
from __future__ import annotations

import json
import sqlite3
import threading
import time
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

    def create_job(self, job_id: str, task_name: str, project_path: str,
                   steps: Iterable[StepSpec]):
        specs = list(steps)
        if not specs:
            raise ExecutorError("job requires at least one step")
        now = time.time()
        with self._lock, self._connect() as db:
            db.execute(
                "INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?,?,?)",
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

    def set_job(self, job_id: str, status: JobStatus, **flags):
        allowed = {"pause_requested", "cancel_requested", "current_step"}
        if set(flags) - allowed:
            raise ExecutorError("unsupported job field")
        fields = ["status=?", "updated_at=?"] + [f"{key}=?" for key in flags]
        values = [status.value, time.time(), *[flags[k] for k in flags], job_id]
        with self._lock, self._connect() as db:
            db.execute(f"UPDATE jobs SET {','.join(fields)} WHERE job_id=?", values)
            self._event(db, job_id, flags.get("current_step"), "JOB_STATUS",
                        {"status": status.value, **flags})

    def checkpoint_before_write(self, job_id: str, position: int, payload: dict[str, Any]):
        checkpoint = {"phase": "BEFORE_WRITE", "payload": payload, "at": time.time()}
        with self._lock, self._connect() as db:
            db.execute(
                "UPDATE steps SET status=?,attempts=attempts+1,checkpoint_json=?,updated_at=? "
                "WHERE job_id=? AND position=?",
                (JobStatus.RUNNING.value, json.dumps(checkpoint, ensure_ascii=False,
                 sort_keys=True), time.time(), job_id, position),
            )
            self._event(db, job_id, position, "CHECKPOINT_BEFORE_WRITE", checkpoint)

    def set_step(self, job_id: str, position: int, status: JobStatus,
                 result: dict[str, Any] | None = None, error: str | None = None):
        with self._lock, self._connect() as db:
            db.execute(
                "UPDATE steps SET status=?,result_json=?,error=?,updated_at=? "
                "WHERE job_id=? AND position=?",
                (status.value, json.dumps(result, ensure_ascii=False, sort_keys=True)
                 if result is not None else None, error, time.time(), job_id, position),
            )
            self._event(db, job_id, position, "STEP_STATUS",
                        {"status": status.value, "error": error})

    def request(self, job_id: str, field: str):
        if field not in {"pause_requested", "cancel_requested"}:
            raise ExecutorError("invalid request")
        with self._lock, self._connect() as db:
            db.execute(f"UPDATE jobs SET {field}=1,updated_at=? WHERE job_id=?",
                       (time.time(), job_id))
            self._event(db, job_id, None, field.upper(), {})


class ResumableExecutor:
    def __init__(self, store: SQLiteCheckpointStore,
                 execute: Callable[[str, dict[str, Any]], dict[str, Any]],
                 reconcile: Callable[[str, dict[str, Any], dict[str, Any] | None],
                                     dict[str, Any]],
                 current_project: Callable[[], str]):
        self.store = store
        self.execute_operation = execute
        self.reconcile_operation = reconcile
        self.current_project = current_project

    def resolve_job_id(self, job_id: str) -> str:
        if job_id != "active":
            return job_id
        jobs = self.store.jobs(50)
        for status in (JobStatus.RUNNING.value, JobStatus.WAITING_USER.value,
                       JobStatus.UNKNOWN_OUTCOME.value, JobStatus.PAUSED.value):
            match = next((job for job in jobs if job["status"] == status), None)
            if match:
                return match["job_id"]
        pending = next((job for job in jobs if job["status"] == JobStatus.PENDING.value), None)
        return (pending or jobs[0])["job_id"] if jobs else self.store.latest_job_id()

    def _assert_project(self, job):
        expected = str(Path(job["project_path"]).resolve())
        actual = str(Path(self.current_project()).resolve())
        if expected.casefold() != actual.casefold():
            raise ProjectMismatch(f"expected open PLN {expected!r}, got {actual!r}")

    @staticmethod
    def _has_readback(result):
        if result.get("readbackVerified") is True:
            return True
        return bool(result.get("readback")) and result.get("status") in {"PASS", "DONE"}

    def run(self, job_id: str) -> JobStatus:
        job_id = self.resolve_job_id(job_id)
        job = self.store.job(job_id)
        self._assert_project(job)
        if JobStatus(job["status"]) in TERMINAL:
            return JobStatus(job["status"])
        self.store.set_job(job_id, JobStatus.RUNNING, pause_requested=0)
        for step in self.store.job(job_id)["steps"]:
            status = JobStatus(step["status"])
            if status is JobStatus.DONE:
                continue
            if status is JobStatus.RUNNING:
                recovery = {"status": "UNKNOWN_OUTCOME", "retryAllowed": False,
                            "reason": "recovered pre-write checkpoint without durable outcome"}
                self.store.set_step(job_id, step["position"],
                                    JobStatus.UNKNOWN_OUTCOME, result=recovery)
                self.store.set_job(job_id, JobStatus.UNKNOWN_OUTCOME,
                                   current_step=step["position"])
                return JobStatus.UNKNOWN_OUTCOME
            if status is JobStatus.UNKNOWN_OUTCOME:
                self.store.set_job(job_id, JobStatus.WAITING_USER,
                                   current_step=step["position"])
                return JobStatus.WAITING_USER
            job = self.store.job(job_id)
            if job["cancel_requested"]:
                self.store.set_job(job_id, JobStatus.CANCELLED,
                                   current_step=step["position"])
                return JobStatus.CANCELLED
            if job["pause_requested"]:
                self.store.set_job(job_id, JobStatus.PAUSED,
                                   current_step=step["position"])
                return JobStatus.PAUSED
            payload = {"operation": step["operation"], "params": step["params"],
                       "floorIndex": step["floor_index"],
                       "verticalContext": step["params"].get("verticalContext"),
                       "expectedZFingerprint": step["params"].get("expectedZFingerprint")}
            self.store.set_job(job_id, JobStatus.RUNNING,
                               current_step=step["position"])
            self.store.checkpoint_before_write(job_id, step["position"], payload)
            try:
                result = self.execute_operation(step["operation"], step["params"])
            except TimeoutError as exc:
                result = {"status": "UNKNOWN_OUTCOME", "error": repr(exc),
                          "retryAllowed": False}
            except Exception as exc:
                if getattr(exc, "retry_allowed", True) is False:
                    result = {"status": "WAITING_USER", "error": repr(exc),
                              "retryAllowed": False, "requiresContinue": True}
                else:
                    self.store.set_step(job_id, step["position"], JobStatus.FAILED,
                                        error=f"{type(exc).__name__}: {exc}")
                    self.store.set_job(job_id, JobStatus.FAILED,
                                       current_step=step["position"])
                    return JobStatus.FAILED
            if result.get("status") == "WAITING_USER":
                self.store.set_step(job_id, step["position"], JobStatus.WAITING_USER,
                                    result=result)
                self.store.set_job(job_id, JobStatus.WAITING_USER,
                                   current_step=step["position"])
                return JobStatus.WAITING_USER
            if result.get("status") == "UNKNOWN_OUTCOME":
                result["retryAllowed"] = False
                self.store.set_step(job_id, step["position"],
                                    JobStatus.UNKNOWN_OUTCOME, result=result)
                self.store.set_job(job_id, JobStatus.UNKNOWN_OUTCOME,
                                   current_step=step["position"])
                return JobStatus.UNKNOWN_OUTCOME
            if not self._has_readback(result):
                self.store.set_step(job_id, step["position"], JobStatus.FAILED,
                                    result=result, error="read-back not verified")
                self.store.set_job(job_id, JobStatus.FAILED,
                                   current_step=step["position"])
                return JobStatus.FAILED
            self.store.set_step(job_id, step["position"], JobStatus.DONE, result=result)
        self.store.set_job(job_id, JobStatus.DONE,
                           current_step=self.store.job(job_id)["total_steps"])
        return JobStatus.DONE

    def resume(self, job_id: str) -> JobStatus:
        job_id = self.resolve_job_id(job_id)
        job = self.store.job(job_id)
        self._assert_project(job)
        if JobStatus(job["status"]) is JobStatus.CANCELLED:
            return JobStatus.CANCELLED
        unknown = next((s for s in job["steps"] if s["status"] in {
            JobStatus.UNKNOWN_OUTCOME.value, JobStatus.RUNNING.value}), None)
        if unknown:
            if unknown["status"] == JobStatus.RUNNING.value:
                recovered = {"status": "UNKNOWN_OUTCOME", "retryAllowed": False,
                             "reason": "resume found checkpoint without durable outcome"}
                self.store.set_step(job_id, unknown["position"],
                                    JobStatus.UNKNOWN_OUTCOME, result=recovered)
                unknown["result"] = recovered
            evidence = self.reconcile_operation(
                unknown["operation"], unknown["params"], unknown["result"])
            classification = evidence.get("classification")
            if classification == "APPLIED" and self._has_readback(evidence):
                self.store.set_step(job_id, unknown["position"], JobStatus.DONE,
                                    result=evidence)
            elif classification == "NOT_APPLIED":
                self.store.set_step(job_id, unknown["position"], JobStatus.PENDING,
                                    result=evidence)
            else:
                self.store.set_step(job_id, unknown["position"],
                                    JobStatus.UNKNOWN_OUTCOME, result=evidence)
                self.store.set_job(job_id, JobStatus.WAITING_USER,
                                   current_step=unknown["position"])
                return JobStatus.WAITING_USER
        return self.run(job_id)

    def pause(self, job_id: str) -> JobStatus:
        job_id = self.resolve_job_id(job_id)
        job = self.store.job(job_id)
        if JobStatus(job["status"]) in TERMINAL:
            return JobStatus(job["status"])
        self.store.request(job_id, "pause_requested")
        if JobStatus(job["status"]) is not JobStatus.RUNNING:
            self.store.set_job(job_id, JobStatus.PAUSED, pause_requested=1)
            return JobStatus.PAUSED
        return JobStatus.RUNNING

    def stop(self, job_id: str) -> JobStatus:
        job_id = self.resolve_job_id(job_id)
        job = self.store.job(job_id)
        if JobStatus(job["status"]) in TERMINAL:
            return JobStatus(job["status"])
        self.store.request(job_id, "cancel_requested")
        if JobStatus(job["status"]) is not JobStatus.RUNNING:
            self.store.set_job(job_id, JobStatus.CANCELLED, cancel_requested=1)
            return JobStatus.CANCELLED
        return JobStatus.RUNNING

    def palette_state(self, job_id: str) -> dict[str, Any]:
        requested_job_id = job_id
        job_id = self.resolve_job_id(job_id)
        job = self.store.job(job_id)
        position = min(job["current_step"], max(0, job["total_steps"] - 1))
        step = job["steps"][position]
        result = step.get("result") or {}
        return {
            "job_id": job_id,
            "task": job["task_name"],
            "status": job["status"],
            "step": step["name"],
            "progress": f"{min(position + 1, job['total_steps'])} из {job['total_steps']}",
            "floor": step["floor_index"],
            "readback": "Подтверждён" if self._has_readback(result) else "Не подтверждён",
            "enum": job["status"],
            "selection": "current" if requested_job_id == "active" else "history",
            "history": self.store.jobs(8),
            "controls": {
                "continue": job["status"] not in {s.value for s in TERMINAL},
                "pause": job["status"] in {JobStatus.RUNNING.value, JobStatus.PENDING.value},
                "stop": job["status"] not in {s.value for s in TERMINAL},
            },
        }
