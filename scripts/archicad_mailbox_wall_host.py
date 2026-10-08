"""Guarded CreateWalls adapter for the existing sync_bridge Mailbox host.

No execution by default. A local approval must match the canonical operation
hash and expiry. Never save, switch project, or retry an attempted operation.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import math
import re
import sqlite3
import subprocess
import sys
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from archicad_guarded_wall_probe import tapir

PORT = 19723
PROJECT_NAME = "Тест MER "  # GetProjectInfo includes this trailing space.
PROJECT_PATH = r"C:\LocalAI\SafeBIM_Global_Library_Test_Projects\Тест MER .pln"
BRIDGE_COMMIT = "27906e2a1370146a8d740f02384ab02a584ce918"
READS = {"GetProjectInfo", "GetStories", "GetAddOnVersion", "GetSelectedElements", "GetDetailsOfElements"}
WRITES = frozenset({"CreateWalls"})


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def utcnow():
    return datetime.now(timezone.utc)


def fresh_until(value):
    expiry = datetime.fromisoformat(value)
    if expiry.tzinfo is None or not 0 < (expiry - utcnow()).total_seconds() <= 900:
        raise ValueError("expired or excessive validity; maximum 15 minutes")


def exact_project(info):
    if (info.get("projectName") != PROJECT_NAME or info.get("projectPath") != PROJECT_PATH
            or info.get("isUntitled") is not False or info.get("isTeamwork") is not False):
        raise ValueError("exact test PLN identity mismatch")


class GuardedTransport:
    # Deliberately no write_call: the inherited continuation executor is disabled.
    def call(self, command, params):
        if command not in READS:
            raise ValueError("read allowlist refused command")
        info = tapir(PORT, "GetProjectInfo")
        exact_project(info)
        return info if command == "GetProjectInfo" else tapir(PORT, command, params)

    def binding(self):
        info = self.call("GetProjectInfo", {})
        identity = {key: info.get(key) for key in (
            "projectPath", "projectLocation", "projectName", "isUntitled", "isTeamwork")}
        return {"instanceId": f"archicad-{PORT}", "logicalProjectId": "live-local-" + digest(identity)[:20],
                "projectName": info["projectName"], "projectPath": info["projectPath"], "port": PORT}


def validate(job):
    fields = {"recipe", "operationId", "instanceId", "logicalProjectId", "projectName",
              "projectPath", "port", "expiresAt", "wall"}
    if not isinstance(job, dict) or set(job) - (fields | {"mode"}) or not fields <= set(job):
        raise ValueError("unexpected or missing operation fields")
    if job.get("recipe") != "create_wall_v1" or job.get("mode", "dry-run") not in {"dry-run", "execute"}:
        raise ValueError("unsupported recipe or mode")
    if not isinstance(job["operationId"], str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", job["operationId"]):
        raise ValueError("invalid operationId")
    if job["port"] != PORT or type(job["port"]) is not int:
        raise ValueError("port mismatch")
    if job["projectName"] != PROJECT_NAME or job["projectPath"] != PROJECT_PATH:
        raise ValueError("target mismatch")
    if job["instanceId"] != f"archicad-{PORT}" or not isinstance(job["logicalProjectId"], str):
        raise ValueError("instance mismatch")
    fresh_until(job["expiresAt"])
    wall = job["wall"]
    required = {"begCoordinate", "endCoordinate", "floorIndex", "zCoordinate", "height", "thickness",
                "offset", "arcAngle", "referenceLineLocation", "structureType"}
    if not isinstance(wall, dict) or set(wall) != required:
        raise ValueError("wall fields must match the single Basic Wall recipe")
    numbers = []
    for key in ("begCoordinate", "endCoordinate"):
        if not isinstance(wall[key], dict) or set(wall[key]) != {"x", "y"}:
            raise ValueError("invalid coordinates")
        numbers.extend(wall[key].values())
    numbers.extend(wall[k] for k in ("zCoordinate", "height", "thickness", "offset", "arcAngle"))
    if any(type(v) not in (int, float) or not math.isfinite(v) for v in numbers):
        raise ValueError("geometry must be finite numeric values")
    a, b = wall["begCoordinate"], wall["endCoordinate"]
    if (not 0.2 <= math.hypot(b["x"]-a["x"], b["y"]-a["y"]) <= 5
            or not 0.5 <= wall["height"] <= 5 or not 0.05 <= wall["thickness"] <= 0.5
            or type(wall["floorIndex"]) is not int or wall["floorIndex"] != 0
            or any(wall[k] != 0 for k in ("zCoordinate", "offset", "arcAngle"))
            or wall["referenceLineLocation"] != "Center" or wall["structureType"] != "Basic"):
        raise ValueError("geometry outside MVP bounds")
    return {k: v for k, v in job.items() if k != "mode"}


class WallExecutor:
    def __init__(self, transport, journal, *, enable_execute=False, approval=None, writer=None):
        self.transport, self.journal = transport, Path(journal)
        self.enable_execute, self.approval = enable_execute, approval
        self.writer = writer or (lambda cmd, params: tapir(PORT, cmd, params))

    def check_target(self, job):
        binding = self.transport.binding()
        for key in ("instanceId", "logicalProjectId", "projectName", "projectPath", "port"):
            if binding.get(key) != job[key]:
                raise ValueError("binding mismatch: " + key)
        stories = self.transport.call("GetStories", {})
        floor = next((s for s in stories.get("stories", []) if s.get("index") == 0), {})
        if stories.get("actStory") != 0 or floor.get("level") != 0 or floor.get("floorId") != 1:
            raise ValueError("expected active ground floor at zero elevation")
        return binding

    def authorize(self, operation):
        if not self.enable_execute or not self.approval:
            raise ValueError("explicit local approval and --enable-execute required")
        approval = json.loads(Path(self.approval).read_text(encoding="utf-8"))
        if (set(approval) != {"operationHash", "expiresAt", "approvedBy", "permission"}
                or approval["operationHash"] != digest(operation)
                or approval["permission"] != "CreateWalls"
                or not isinstance(approval["approvedBy"], str) or not approval["approvedBy"].strip()):
            raise ValueError("approval does not authorize this exact operation")
        fresh_until(approval["expiresAt"])

    def execute(self, job):
        base = {"mutationApplied": False, "automaticRetry": False, "plnSaved": False}
        attempted = False
        try:
            operation = validate(job)
            binding = self.check_target(operation)
            wall = operation["wall"]
            params = {"wallsData": [wall]}
            plan = {**base, "operationId": operation["operationId"], "operationHash": digest(operation),
                    "target": binding, "command": "CreateWalls", "parameters": params}
            if job.get("mode", "dry-run") == "dry-run":
                return {**plan, "status": "DRY_RUN"}
            self.authorize(operation)
            self.journal.parent.mkdir(parents=True, exist_ok=True)
            with closing(sqlite3.connect(self.journal)) as db:
                db.execute("PRAGMA synchronous=FULL")
                db.execute("CREATE TABLE IF NOT EXISTS attempts (operation_id TEXT PRIMARY KEY, operation_hash TEXT UNIQUE, payload TEXT NOT NULL, state TEXT NOT NULL, result TEXT)")
                db.commit()
                # Transactional unique reservation plus durable intent BEFORE write.
                db.execute("BEGIN IMMEDIATE")
                if db.execute("SELECT 1 FROM attempts WHERE operation_id=? OR operation_hash=?",
                              (operation["operationId"], digest(operation))).fetchone():
                    return {**plan, "status": "BLOCKED", "reason": "operation already attempted; reconcile, never retry"}
                self.check_target(operation)
                self.authorize(operation)
                fresh_until(operation["expiresAt"])
                db.execute("INSERT INTO attempts VALUES (?,?,?,'ATTEMPTED',NULL)",
                           (operation["operationId"], digest(operation), canonical(plan)))
                db.commit()
                attempted = True
                result = {**plan, "status": "UNKNOWN_OUTCOME", "mutationApplied": None}
                try:
                    # Repeat identity after journal commit, directly at the write boundary.
                    self.check_target(operation)
                    self.authorize(operation)
                    fresh_until(operation["expiresAt"])
                    if "CreateWalls" not in WRITES:
                        raise ValueError("write allowlist refused command")
                    raw = self.writer("CreateWalls", params)
                    rows = raw.get("elements", [])
                    if len(rows) != 1:
                        raise ValueError("ambiguous creation result")
                    guid = rows[0]["elementId"]["guid"]
                    if not isinstance(guid, str) or not re.fullmatch(r"[0-9a-fA-F]{8}(-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}", guid):
                        raise ValueError("invalid created GUID")
                    result.update(createdGuid=guid, mutationApplied=True)
                    db.execute("UPDATE attempts SET state='CREATED_UNVERIFIED',result=? WHERE operation_id=?",
                               (canonical(result), operation["operationId"]))
                    db.commit()
                    self.check_target(operation)
                    details = self.transport.call("GetDetailsOfElements", {"elements": [{"elementId": {"guid": guid}}]})
                    entries = details.get("detailsOfElements", [])
                    if len(entries) != 1:
                        raise ValueError("expected one readback row")
                    row = entries[0]
                    # Tapir details may omit elementId; singleton response is correlated
                    # to the one GUID requested, and an explicit returned ID must match.
                    if row.get("elementId", {}).get("guid", guid).lower() != guid.lower():
                        raise ValueError("readback GUID mismatch")
                    d = row.get("details", {})
                    checks = {"type": row.get("type") == "Wall", "floorIndex": row.get("floorIndex") == 0,
                              "geometryType": d.get("geometryType") == "Straight",
                              "structureType": d.get("structureType") == "Basic",
                              "referenceLineLocation": d.get("referenceLineLocation") == "Center"}
                    for key in ("begCoordinate", "endCoordinate"):
                        for axis in ("x", "y"):
                            checks[key + "." + axis] = self.close(d.get(key, {}).get(axis), wall[key][axis])
                    for key, expected in (("height", wall["height"]), ("begThickness", wall["thickness"]),
                                          ("endThickness", wall["thickness"]), ("zCoordinate", 0), ("offset", 0), ("arcAngle", 0)):
                        checks[key] = self.close(d.get(key), expected)
                    self.check_target(operation)
                    result.update(status="PASS" if all(checks.values()) else "BLOCKED_READBACK",
                                  verification=checks, readback=row, guidCorrelation="singleton-request")
                except Exception as exc:
                    result.update(reason=type(exc).__name__ + ": " + str(exc))
                db.execute("UPDATE attempts SET state=?,result=? WHERE operation_id=?",
                           (result["status"], canonical(result), operation["operationId"]))
                db.commit()
                return result
        except Exception as exc:
            return {**base, "status": "UNKNOWN_OUTCOME" if attempted else "BLOCKED",
                    "mutationApplied": None if attempted else False, "reason": str(exc)}

    @staticmethod
    def close(value, expected):
        return type(value) in (float, int) and math.isfinite(value) and abs(value - expected) <= 1e-6


def load_bridge(source):
    source = Path(source).resolve()
    head = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
    dirty = subprocess.check_output(["git", "-C", str(source), "status", "--porcelain"], text=True).strip()
    if head != BRIDGE_COMMIT or dirty:
        raise ValueError("bridge source must be clean pinned commit " + BRIDGE_COMMIT)
    sys.path.insert(0, str(source))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--bridge-source", required=True)
    p.add_argument("--data-dir", type=Path, required=True)
    p.add_argument("--inspect", action="store_true")
    p.add_argument("--message-id", help="Process exactly this GitHub inbox JOB once")
    p.add_argument("--enable-execute", action="store_true")
    p.add_argument("--approval", type=Path)
    args = p.parse_args()
    load_bridge(args.bridge_source)
    transport = GuardedTransport()
    binding = transport.binding()  # identity gate before starting the host
    if args.inspect:
        print(json.dumps(binding, ensure_ascii=False, indent=2))
        return
    from sync_bridge.host import BridgeHost, HostConfig
    from sync_bridge.mailbox import inbound_bridge_message

    class GuardedHost(BridgeHost):
        def start(self):
            result = super().start()
            self.write_executor = WallExecutor(transport, args.data_dir / "wall-attempts.sqlite3",
                                              enable_execute=args.enable_execute, approval=args.approval)
            self.bridge.archicad_write_api = args.enable_execute and args.approval is not None
            self._publish_status()
            return result

    config = HostConfig(data_dir=args.data_dir, db_path=args.data_dir / "bridge.sqlite3",
                        github_root="safe-bim-mailbox/gpt-live", archicad_port=PORT,
                        bridge_instance_id="gpt-guarded-wall-19723")
    host = GuardedHost(config, transport=transport)
    try:
        if args.message_id:
            if not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", args.message_id):
                raise ValueError("invalid message ID")
            endpoint = "repos/dvikt33-ux/safe-bim-bridge/contents/safe-bim-mailbox/gpt-live/inbox/" + args.message_id + ".json?ref=main"
            raw = subprocess.check_output(["gh", "api", endpoint], text=True, encoding="utf-8")
            obj = json.loads(base64.b64decode(json.loads(raw)["content"]))
            message = inbound_bridge_message(obj, path=args.message_id + ".json")
            if message["kind"] != "JOB":
                raise ValueError("single-operation entry only accepts JOB")
            host.start()
            accepted = host.bridge.accept_remote_message(message)
            if accepted.get("jobCreated"):
                # A reused database may contain interrupted/pending jobs: never
                # accidentally run one instead of the explicitly named message.
                pending = host.store.jobs_by_state("QUEUED")
                if len(pending) != 1 or pending[0]["source_message_id"] != args.message_id:
                    raise ValueError("unexpected queued jobs; inspect state before continuing")
                writes = host._execute_one_write_job()
            else:
                writes = []
            published = host.bridge.flush_outbox()
            print(json.dumps({"accepted": accepted, "writes": writes, "published": published,
                              "binding": binding}, ensure_ascii=False, indent=2))
        else:
            host.run_forever()
    finally:
        host.close()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    try:
        main()
    except Exception as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(2)
