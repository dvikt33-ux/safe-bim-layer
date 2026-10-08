"""Offline Archicad graph -> verified create_wall_v1 GitHub Mailbox JOB adapter.

Given a schema-validated BIM graph and authenticated-looking RESULT evidence,
prepare ONE unsubmitted JOB at a time. No network use, no mailbox publication,
no Archicad connection, and no PLN mutation. Requires exact local worker gates.
Only the create_wall_v1 recipe already observed working with Tapir 1.5.10 is
translated. All other operation kinds remain intentionally unsupported.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
GRAPH_FILE = Path(__file__).with_name("archicad_bim_graph.py")
_SPEC = importlib.util.spec_from_file_location("archicad_bim_graph", GRAPH_FILE)
GRAPH = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(GRAPH)

_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")
_GUID = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
_REQUIRED_TARGET = {"instanceId", "logicalProjectId", "port", "projectName", "projectPath"}
_REQUIRED_WALL = {"begCoordinate", "endCoordinate", "floorIndex", "zCoordinate",
                  "height", "thickness", "offset", "arcAngle",
                  "referenceLineLocation", "structureType"}
_TOL = 1e-7


def canonical(value):
    """Exact canonical JSON used by the existing sync_bridge.identity."""
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def validate_target(target):
    if not isinstance(target, dict) or set(target) != _REQUIRED_TARGET:
        raise ValueError("target must contain exactly instanceId, logicalProjectId, port, projectName, projectPath")
    if not all(isinstance(target[k], str) and target[k].strip()
               for k in (_REQUIRED_TARGET - {"port"})):
        raise ValueError("invalid target strings")
    if type(target["port"]) is not int or not (1 <= target["port"] <= 65535):
        raise ValueError("invalid target port")
    if target["instanceId"] != f"archicad-{target['port']}":
        raise ValueError("instanceId must match the explicit port")
    if not target["projectPath"].lower().endswith(".pln"):
        raise ValueError("target must be a saved PLN, not an untitled project")
    # Actual target identity is rechecked by the LOCAL worker immediately
    # before the write. Offline input is not independent proof of connection.
    return dict(target)


def _xy(value, name):
    if not isinstance(value, dict) or set(value) != {"x", "y"}:
        raise ValueError(f"{name} must contain x and y")
    result = {}
    for key in ("x", "y"):
        v = value[key]
        if type(v) not in (int, float) or not math.isfinite(v) or abs(v) > 1e6:
            raise ValueError(f"{name}.{key} must be a finite coordinate")
        result[key] = float(v)
    return result


def _num(value, name, low, high):
    if type(value) not in (int, float) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError(f"{name} outside verified recipe limits")
    return float(value)


def _wall_params(params):
    if not isinstance(params, dict) or set(params) != {"wallsData"}:
        raise ValueError("only one CreateWalls wallsData array is supported")
    walls = params["wallsData"]
    if not isinstance(walls, list) or len(walls) != 1:
        raise ValueError("verified Mailbox recipe creates exactly one Wall per JOB")
    w = walls[0]
    if not isinstance(w, dict) or not (
        {"begCoordinate", "endCoordinate", "floorIndex", "height", "thickness"} <= set(w)
        <= _REQUIRED_WALL
    ):
        raise ValueError("unsupported wall field set for create_wall_v1")
    a = _xy(w["begCoordinate"], "begCoordinate")
    b = _xy(w["endCoordinate"], "endCoordinate")
    floor = w["floorIndex"]
    if type(floor) is not int:
        raise ValueError("native floorIndex must be an integer")
    z = _num(w.get("zCoordinate", 0), "zCoordinate", -50, 300)
    height = _num(w["height"], "height", 0.2, 20)
    thick = _num(w["thickness"], "thickness", 0.05, 2)
    offset = _num(w.get("offset", 0), "offset", -2, 2)
    arc = _num(w.get("arcAngle", 0), "arcAngle", 0, 0)
    if w.get("referenceLineLocation", "Center") != "Center":
        raise ValueError("only centered reference lines proven")
    if w.get("structureType", "Basic") != "Basic":
        raise ValueError("only Basic walls proven")
    length = math.hypot(b["x"] - a["x"], b["y"] - a["y"])
    if not 0.2 <= length <= 20:
        raise ValueError("wall length must be 0.2..20 meters")
    return {
        "begCoordinate": a, "endCoordinate": b, "floorIndex": floor,
        "zCoordinate": z, "height": height, "thickness": thick,
        "offset": offset, "arcAngle": arc,
        "referenceLineLocation": "Center", "structureType": "Basic",
    }


def ids_for(run_id, plan_hash, step_id, mode):
    if not isinstance(run_id, str) or not _ID.fullmatch(run_id):
        raise ValueError("run-id must be a 1..64 character stable ASCII identifier")
    seed = {"runId": run_id, "planHash": plan_hash, "stepId": step_id}
    operation_id = "graph-" + digest(seed)[:24]
    message_id = "gpt-graph-" + digest({**seed, "mode": mode})[:24]
    return operation_id, message_id


def _identical_wall(expected, actual):
    if not isinstance(actual, dict):
        return False
    d = actual.get("details")
    if not isinstance(d, dict) or actual.get("type") != "Wall":
        return False
    try:
        for key, detail_key in (("begCoordinate", "begCoordinate"),
                                ("endCoordinate", "endCoordinate")):
            xy = _xy(d[detail_key], detail_key)
            if any(abs(xy[a] - expected[key][a]) > _TOL for a in ("x", "y")):
                return False
        return (actual.get("floorIndex") == expected["floorIndex"]
                and d.get("geometryType") == "Straight"
                and d.get("structureType") == "Basic"
                and d.get("referenceLineLocation") == "Center"
                and all(type(d.get(k)) in (float, int) and
                        abs(float(d[k]) - expected[v]) <= _TOL
                        for k, v in (("height", "height"), ("begThickness", "thickness"),
                                     ("endThickness", "thickness"), ("offset", "offset"),
                                     ("zCoordinate", "zCoordinate"))))
    except (ValueError, KeyError, TypeError):
        return False


def _verify_result(envelope, expected_message_id, expected_operation_id, expected_target, expected_wall):
    if not isinstance(envelope, dict) or (
        envelope.get("kind") != "RESULT" or envelope.get("protocolVersion") != 1
        or not isinstance(envelope.get("payload"), dict)
    ):
        raise ValueError("invalid RESULT envelope")
    if digest(envelope["payload"]) != envelope.get("payloadHash"):
        raise ValueError("RESULT payloadHash mismatch")
    if envelope.get("messageId") != "result-job-" + expected_message_id:
        raise ValueError("RESULT envelope belongs to another command")
    payload = envelope["payload"]
    if payload.get("job_id") != "job-" + expected_message_id:
        raise ValueError("RESULT job_id mismatch")
    result = payload.get("result")
    if not isinstance(result, dict) or result.get("operationId") != expected_operation_id:
        raise ValueError("RESULT operationId mismatch")
    if result.get("target") != expected_target:
        raise ValueError("RESULT project fingerprint mismatch")
    if result.get("status") != "PASS":
        return {"status": "STOP", "reason": "RESULT not PASS (no auto-retry)",
                "outcome": result.get("status")}
    checks = result.get("verification")
    if (result.get("command") != "CreateWalls"
        or result.get("mutationApplied") is not True
        or result.get("automaticRetry") is not False
        or not isinstance(checks, dict) or not checks or not all(v is True for v in checks.values())
        or not _GUID.fullmatch(str(result.get("createdGuid", "")))
        or not _identical_wall(expected_wall, result.get("readback"))):
        raise ValueError("RESULT PASS lacks validated GUID/Wall geometry/readback")
    actual_params = result.get("parameters", {}).get("wallsData")
    if (not isinstance(actual_params, list) or len(actual_params) != 1
            or _wall_params({"wallsData": actual_params}) != expected_wall):
        raise ValueError("RESULT parameters do not match operation")
    return {"status": "PASS", "guid": result["createdGuid"]}


def prepare(catalog, plan, results, target, run_id, *, mode="dry-run", created_at=None):
    if mode not in ("dry-run", "execute"):
        raise ValueError("mode must be dry-run or execute")
    validate_target(target)
    if not isinstance(results, list):
        raise ValueError("results must be a list of complete RESULT envelopes")
    graph = GRAPH.compile_graph(catalog, plan)
    if graph["status"] != "PLAN_VALIDATED_OFFLINE":
        return {"status": "INVALID_GRAPH", "graph": graph}
    steps = {op["id"]: op for op in plan["operations"]}
    reported = {}
    for envelope in results:
        if not isinstance(envelope, dict) or not isinstance(envelope.get("payload"), dict):
            raise ValueError("malformed RESULT in history")
        if digest(envelope["payload"]) != envelope.get("payloadHash"):
            raise ValueError("RESULT history hash mismatch")
        result = envelope["payload"].get("result")
        if not isinstance(result, dict):
            raise ValueError("RESULT missing result object")
        op_id = result.get("operationId")
        matches = [id for id in steps
                   if ids_for(run_id, graph["sourcePlanHash"], id, "execute")[0] == op_id]
        if len(matches) != 1 or matches[0] in reported:
            raise ValueError("RESULT cannot be uniquely matched to one graph step")
        sid = matches[0]
        step = steps[sid]
        if step["command"] != "CreateWalls":
            raise ValueError("result for unimplemented recipe")
        expected = _wall_params(step["params"])
        op_id, mid = ids_for(run_id, graph["sourcePlanHash"], sid, "execute")
        reported[sid] = _verify_result(envelope, mid, op_id, target, expected)

    for sid in graph["executionOrder"]:
        if sid in reported and reported[sid]["status"] == "STOP":
            return {"status": "STOP", "stepId": sid,
                    "reason": reported[sid]["reason"], "outcome": reported[sid]["outcome"],
                    "automaticRetry": False}
    completed = {sid: row["guid"] for sid, row in reported.items()
                 if row["status"] == "PASS"}
    if len({x.lower() for x in completed.values()}) != len(completed):
        raise ValueError("same GUID seen for more than one completed step")
    if len(completed) == len(steps):
        return {"status": "GRAPH_COMPLETE", "createdGuids": completed,
                "executionSupported": False, "jobPublished": False}

    unsupported = [sid for sid in graph["executionOrder"]
                   if steps[sid]["command"] != "CreateWalls"]
    if mode == "execute" and unsupported and not completed:
        return {"status": "UNSUPPORTED_GRAPH", "unsupportedSteps": unsupported,
                "reason": "Cannot complete the graph with currently verified worker recipes",
                "jobPublished": False, "automaticRetry": False}
    next_id = next(sid for sid in graph["executionOrder"] if sid not in completed)
    operation = steps[next_id]
    deps = next(x["dependsOn"] for x in graph["operations"] if x["id"] == next_id)
    if any(dep not in completed for dep in deps):
        return {"status": "WAIT_FOR_DEPENDENCIES", "stepId": next_id,
                "waitingFor": [d for d in deps if d not in completed]}
    if operation["command"] != "CreateWalls":
        return {"status": "NEEDS_WORKER_RECIPE", "stepId": next_id,
                "command": operation["command"],
                "reason": "The deployed local Mailbox worker is only proven for create_wall_v1"}
    if next(x["references"] for x in graph["operations"] if x["id"] == next_id):
        return {"status": "NEEDS_WORKER_RECIPE", "stepId": next_id,
                "reason": "Wall with dynamically substituted GUID is not proven"}
    wall = _wall_params(operation["params"])
    op_id, message_id = ids_for(run_id, graph["sourcePlanHash"], next_id, mode)
    now = (datetime.now(timezone.utc) if created_at is None else
           datetime.fromisoformat(created_at.replace("Z", "+00:00")))
    if now.tzinfo is None:
        raise ValueError("createdAt requires timezone")
    now = now.astimezone(timezone.utc)
    payload = {
        "expiresAt": (now + timedelta(minutes=15)).isoformat(),
        "instanceId": target["instanceId"],
        "logicalProjectId": target["logicalProjectId"],
        "mode": mode,
        "operationId": op_id,
        "port": target["port"],
        "projectName": target["projectName"],
        "projectPath": target["projectPath"],
        "recipe": "create_wall_v1",
        "wall": wall,
    }
    envelope = {
        "protocolVersion": 1, "messageId": message_id, "kind": "JOB",
        "createdAt": now.isoformat(), "payload": payload,
        "payloadHash": digest(payload),
    }
    return {
        "status": "NEXT_JOB_PREVIEW",
        "stepId": next_id, "completedSteps": completed,
        "schemaVersion": GRAPH.CONTRACTS.source_version(catalog),
        "liveTapirVersionProvenForRecipe": "1.5.10",
        "jobPathRelative": f"safe-bim-mailbox/gpt-live/inbox/{message_id}.json",
        "mailboxEnvelope": envelope,
        "jobPublished": False, "automaticRetry": False,
        "note": "Preview only. Do not regenerate and repost with same messageId after a write.",
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--graph", type=Path, required=True)
    p.add_argument("--target", type=Path, required=True,
                   help="local exact target JSON (not committed to GitHub)")
    p.add_argument("--results", type=Path, help="array of existing RESULT envelopes")
    p.add_argument("--run-id", required=True)
    p.add_argument("--mode", choices=("dry-run", "execute"), default="dry-run")
    p.add_argument("--created-at", help="ISO timestamp with timezone for reproducible preview")
    p.add_argument("--output", type=Path, help="write unsubmitted preview JSON")
    p.add_argument("--schema", type=Path, default=GRAPH.CONTRACTS.DEFAULT_SCHEMA)
    args = p.parse_args(argv)
    try:
        catalog = GRAPH.CONTRACTS.load_catalog(args.schema)
        plan = json.loads(args.graph.read_text(encoding="utf-8-sig"))
        target = json.loads(args.target.read_text(encoding="utf-8-sig"))
        results = json.loads(args.results.read_text(encoding="utf-8-sig")) if args.results else []
        output = prepare(catalog, plan, results, target, args.run_id,
                         mode=args.mode, created_at=args.created_at)
        content = json.dumps(output, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(content, encoding="utf-8")
        print(content, end="")
        return 0 if output["status"] in ("GRAPH_COMPLETE", "NEXT_JOB_PREVIEW") else 2
    except Exception as exc:
        print(json.dumps({"status": "ERROR", "message": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    sys.exit(main())
