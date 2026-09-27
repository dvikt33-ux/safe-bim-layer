#!/usr/bin/env python3
"""Audit T3: dependency chain STORIES -> WALL -> OPENING.

Standalone live probe for disposable MCP_TEST.pln. Not production Router.

Safety contract:
- dry-run only locates a free area and prints the exact plan;
- live mode requires explicit origin from prior dry-run;
- wall package cannot start before stories package COMPLETED;
- opening package cannot start before wall package COMPLETED and mapping CONFIRMED;
- one attempt per mutation, never automatic retry;
- receipt is fsynced before every mutation;
- created wall/opening are independently identified by GUID-set difference;
- create-return GUID is checked only after independent identification;
- wall gets temporary Element ID marker and marker is restored before PKG02 completes;
- opening host binding is verified by read-back ownerElementId == confirmed wall GUID;
- no automatic delete/undo; artifacts remain for manual visual inspection.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import platform
import sys
import time
import uuid
from typing import Any

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import backends as base
from backends_v13 import TapirBackendV13
import probe_t2_connections_v13 as t2c

VER = "1.0"
ADDON = "1.5.9"
PREFIX = "BX:T3:"
WALL_LENGTH = 6.0
OPENING_WIDTH = 1.0
OPENING_HEIGHT = 1.0
OPENING_Z = 1.0
RADIUS = 3.0

PKG01 = "PKG01_STORIES"
PKG02 = "PKG02_WALL"
PKG04 = "PKG04_OPENING"
DEPS = {PKG01: [], PKG02: [PKG01], PKG04: [PKG02]}


class Stop(Exception):
    def __init__(self, stage: str, reason: str, status: str = "UNKNOWN"):
        super().__init__(reason)
        self.stage = stage
        self.reason = reason
        self.status = status


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def jwrite(path: str, obj: Any) -> None:
    base.write_json_atomic(path, obj)


def close(a: Any, b: Any, tol: float = 0.001) -> bool:
    try:
        return abs(float(a) - float(b)) <= tol
    except Exception:
        return False


def project_recheck(b: TapirBackendV13, expect_project: str):
    try:
        return t2c.project_recheck(b, expect_project)
    except t2c.Stop as e:
        raise Stop(e.stage, e.reason, e.status) from e


def witness_composite(b: TapirBackendV13) -> str:
    try:
        return t2c.witness_composite(b)
    except t2c.Stop as e:
        raise Stop(e.stage, e.reason, e.status) from e


def wall_segment(origin: tuple[float, float]) -> dict[str, Any]:
    ox, oy = origin
    return {
        "label": "T3_HOST_WALL",
        "role": "dependency_host",
        "from_abs": (ox, oy),
        "to_abs": (ox + WALL_LENGTH, oy),
        "length": WALL_LENGTH,
    }


def wall_payload(origin: tuple[float, float], comp_guid: str) -> dict[str, Any]:
    return t2c.wall_payload(wall_segment(origin), comp_guid)


def opening_base(origin: tuple[float, float]) -> tuple[float, float, float]:
    ox, oy = origin
    return (ox + (WALL_LENGTH - OPENING_WIDTH) / 2.0, oy, OPENING_Z)


def opening_payload(origin: tuple[float, float], wall_guid: str) -> dict[str, Any]:
    x, y, z = opening_base(origin)
    return {
        "openingsData": [{
            "ownerElementId": {"guid": wall_guid},
            "basePoint": {"x": x, "y": y, "z": z},
            "width": OPENING_WIDTH,
            "height": OPENING_HEIGHT,
        }]
    }


def protection_box(origin: tuple[float, float]) -> list[float]:
    ox, oy = origin
    return [ox - RADIUS, oy - RADIUS, 0.0,
            ox + WALL_LENGTH + RADIUS, oy + RADIUS, t2c.HEIGHT]


def overlaps(a: list[float], b: list[float]) -> bool:
    return not (
        a[3] < b[0] or a[0] > b[3] or
        a[4] < b[1] or a[1] > b[4] or
        a[5] < b[2] or a[2] > b[5]
    )


def conflicts(boxes: dict[str, list[float]], origin: tuple[float, float], allowed: set[str] | None = None):
    pbox = protection_box(origin)
    allowed = allowed or set()
    return [{"guid": g, "bbox": box} for g, box in boxes.items()
            if g not in allowed and overlaps(box, pbox)]


def choose_free_origin(b: TapirBackendV13, guids: set[str]) -> tuple[float, float]:
    boxes = t2c.bbox_map(b, guids)
    for origin in t2c.candidate_origins():
        if not conflicts(boxes, origin):
            return origin
    raise Stop("PRECHECK_AREA", "no free candidate origin in +/-100 m grid", "NO_GO")


def assert_area_clean(b: TapirBackendV13, guids: set[str], origin: tuple[float, float], allowed: set[str] | None = None):
    bad = conflicts(t2c.bbox_map(b, guids), origin, allowed)
    if bad:
        raise Stop("PRECHECK_AREA", f"foreign element in T3 protection volume: {bad}", "NO_GO")


def create_wall_once(b: TapirBackendV13, payload: dict[str, Any]) -> list[str]:
    return t2c.create_once(b, payload)


def set_layer_once(b: TapirBackendV13, guid: str) -> None:
    return t2c.set_layer_once(b, guid)


def create_opening_once(b: TapirBackendV13, payload: dict[str, Any]) -> list[str]:
    res = t2c.addon_once(b, "CreateOpenings", payload)
    d = base._to_dict(res)
    items = base._as_list(d.get("elements") or res)
    guids: list[str] = []
    errors: list[Any] = []
    for item in items:
        row = base._to_dict(item)
        if row.get("error"):
            errors.append(row["error"])
            continue
        g = base._guid(item)
        if g:
            guids.append(g)
    if errors:
        raise base.BackendError(f"CreateOpenings errors: {errors}")
    return guids


def _find_key(obj: Any, key: str) -> Any:
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for v in obj.values():
            got = _find_key(v, key)
            if got is not None:
                return got
    elif isinstance(obj, list):
        for v in obj:
            got = _find_key(v, key)
            if got is not None:
                return got
    return None


def _guid_value(obj: Any) -> str | None:
    if obj is None:
        return None
    g = base._guid(obj)
    if g:
        return str(g)
    d = base._to_dict(obj)
    if d.get("guid"):
        return str(d["guid"])
    return None


def observe_opening(b: TapirBackendV13, guid: str) -> dict[str, Any]:
    raw = b.details_raw(guid) or {}
    owner = _guid_value(_find_key(raw, "ownerElementId"))
    bp = base._to_dict(_find_key(raw, "basePoint"))
    width = _find_key(raw, "width")
    height = _find_key(raw, "height")
    return {
        "type": raw.get("type"),
        "floor_index": raw.get("floorIndex"),
        "owner_guid": owner,
        "base_point": bp,
        "width": width,
        "height": height,
        "raw": raw,
    }


def opening_checks(obs: dict[str, Any], origin: tuple[float, float], wall_guid: str) -> dict[str, bool]:
    x, y, z = opening_base(origin)
    bp = obs.get("base_point") or {}
    return {
        "type": obs.get("type") == "Opening",
        "floor": obs.get("floor_index") == t2c.FLOOR,
        "owner_binding": obs.get("owner_guid") == wall_guid,
        "base_point": close(bp.get("x"), x, 0.01) and close(bp.get("y"), y, 0.01) and close(bp.get("z"), z, 0.01),
        "width": close(obs.get("width"), OPENING_WIDTH, 0.01),
        "height": close(obs.get("height"), OPENING_HEIGHT, 0.01),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--expect-project", required=True)
    ap.add_argument("--port", type=int, default=19723)
    ap.add_argument("--origin-x", type=float, default=None)
    ap.add_argument("--origin-y", type=float, default=None)
    ap.add_argument("--out", default="t3_dependency_receipt_live_v13.json")
    ap.add_argument("--report", default="t3_dependency_report_live_v13.json")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--allow-write", action="store_true")
    ap.add_argument("--i-understand-this-writes-to-archicad", action="store_true")
    a = ap.parse_args()

    if a.allow_write != a.i_understand_this_writes_to_archicad:
        print("STOP: нужны оба write-флага одновременно", file=sys.stderr)
        return 1
    write_enabled = bool(a.allow_write and a.i_understand_this_writes_to_archicad)
    if write_enabled and (a.origin_x is None or a.origin_y is None):
        print("STOP: live T3 requires explicit --origin-x and --origin-y from prior dry-run", file=sys.stderr)
        return 1
    if (a.origin_x is None) != (a.origin_y is None):
        print("STOP: origin requires both --origin-x and --origin-y", file=sys.stderr)
        return 1
    if os.path.exists(a.out):
        print(f"STOP: receipt already exists: {a.out}", file=sys.stderr)
        return 1

    rec: dict[str, Any] = {
        "probe": "AUDIT_T3_DEPENDENCY",
        "version": VER,
        "host": f"{platform.system()} {platform.release()}",
        "started_at": now(),
        "status": "RUNNING",
        "packages": {PKG01: "PENDING", PKG02: "PENDING", PKG04: "PENDING"},
        "mapping": {},
        "stages": [],
        "artifacts": [],
        "cleanup": None,
    }
    jwrite(a.out, rec)

    def stage(name: str, **kw: Any) -> None:
        rec["stages"].append({"stage": name, "at": now(), **kw})
        jwrite(a.out, rec)

    def setrec(**kw: Any) -> None:
        rec.update(kw)
        jwrite(a.out, rec)

    def start_pkg(name: str) -> None:
        unsat = [d for d in DEPS[name] if rec["packages"].get(d) != "COMPLETED"]
        if unsat:
            raise Stop("DEPENDENCY_GATE", f"{name} blocked by {unsat}", "DEPENDENCY_BLOCKED")
        if rec["packages"].get(name) != "PENDING":
            raise Stop("PACKAGE_STATE", f"cannot start {name} from {rec['packages'].get(name)}", "UNKNOWN")
        rec["packages"][name] = "RUNNING"
        stage("PACKAGE_STARTED", package=name, deps=DEPS[name], states=dict(rec["packages"]))

    def complete_pkg(name: str) -> None:
        if rec["packages"].get(name) != "RUNNING":
            raise Stop("PACKAGE_STATE", f"cannot complete {name} from {rec['packages'].get(name)}", "UNKNOWN")
        rec["packages"][name] = "COMPLETED"
        stage("PACKAGE_COMPLETED", package=name, states=dict(rec["packages"]))

    lock = a.out + ".lock"
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.close(fd)
    except FileExistsError:
        setrec(status="STOP", reason="concurrent probe lock")
        print(f"STOP: {lock} exists", file=sys.stderr)
        return 1

    try:
        b = TapirBackendV13(port=a.port)
        ok, why = b.available()
        if not ok:
            raise Stop("BACKEND", why, "NO_GO")
        addon = b.addon_version()
        if addon != ADDON:
            raise Stop("BACKEND", f"Tapir {addon!r} != {ADDON!r}", "NO_GO")

        info, stories = project_recheck(b, a.expect_project)
        comp = witness_composite(b)
        before_all = set(b.all_elements() or [])
        before_walls = set(b.elements_by_type("Wall") or [])
        before_openings = set(b.elements_by_type("Opening") or [])
        leftovers = t2c.scan_prefix(b, before_all, "BX:")
        if leftovers:
            raise Stop("PRECHECK_MARKERS", f"existing BX markers: {leftovers}", "NO_GO")

        if a.origin_x is None:
            origin = choose_free_origin(b, before_all)
        else:
            origin = (float(a.origin_x), float(a.origin_y))
            assert_area_clean(b, before_all, origin)

        wall_plan = wall_payload(origin, comp)
        opening_template = opening_payload(origin, "<CONFIRMED_T3_WALL_GUID>")
        stage("PRECHECK", project=info, addon=addon, origin=list(origin),
              protection_box=protection_box(origin), scratch="FREE",
              before_all=len(before_all), before_walls=len(before_walls),
              before_openings=len(before_openings), composite_guid=comp,
              package_plan=[PKG01, PKG02, PKG04], wall_payload=wall_plan,
              opening_payload_template=opening_template)

        if a.dry_run or not write_enabled:
            setrec(status="DRY_RUN_OK", origin=list(origin))
            print("AUDIT T3 DEPENDENCY DRY-RUN OK")
            print("MUTATIONS: 0")
            print(f"SUGGESTED ORIGIN: --origin-x {origin[0]} --origin-y {origin[1]}")
            print("PACKAGE ORDER:", " -> ".join([PKG01, PKG02, PKG04]))
            print("WALL PAYLOAD:")
            print(json.dumps(wall_plan, ensure_ascii=False, indent=2))
            print("OPENING TEMPLATE:")
            print(json.dumps(opening_template, ensure_ascii=False, indent=2))
            return 0

        # PKG01: read-only story resolution.
        start_pkg(PKG01)
        info_now, stories_now = project_recheck(b, a.expect_project)
        st = t2c.story_at(stories_now, t2c.FLOOR)
        if not st:
            raise Stop("PKG01_STORY", "target story not found", "VERIFY_FAILED")
        stage("STORY_RESOLVED", package=PKG01, story=st, project=info_now)
        complete_pkg(PKG01)

        # PKG02: create and fully confirm the host wall.
        start_pkg(PKG02)
        project_recheck(b, a.expect_project)
        assert_area_clean(b, set(b.all_elements() or []), origin)
        before_wall_all = set(b.all_elements() or [])
        before_wall_set = set(b.elements_by_type("Wall") or [])
        stage("WALL_CREATE_INTENT", package=PKG02, payload=wall_plan, attempt=1,
              note="receipt fsynced; exactly one CreateWalls attempt")
        try:
            returned_wall = create_wall_once(b, wall_plan)
        except Exception as e:
            setrec(status="UNKNOWN", cleanup={"action": "DO NOT RETRY; reconcile T3 host wall",
                                              "reason": "CreateWalls may have applied"})
            raise Stop("WALL_CREATE_DISPATCH", f"{type(e).__name__}: {e}", "UNKNOWN")

        after_wall_all = set(b.all_elements() or [])
        after_wall_set = set(b.elements_by_type("Wall") or [])
        new_all = sorted(after_wall_all - before_wall_all)
        new_walls = sorted(after_wall_set - before_wall_set)
        if len(new_all) != 1 or new_all != new_walls:
            raise Stop("WALL_IDENTIFY", f"new_all={new_all}, new_walls={new_walls}", "UNKNOWN")
        wall_guid = new_walls[0]
        if returned_wall != [wall_guid]:
            raise Stop("WALL_RESPONSE_CHECK", f"returned={returned_wall}, independent={[wall_guid]}", "UNKNOWN")

        wall_obs0 = t2c.observe(b, wall_guid, stories_now)
        wall_checks0 = t2c.geometry_checks(wall_obs0, wall_segment(origin))
        wall_checks0.pop("layer", None)
        if not all(wall_checks0.values()):
            raise Stop("WALL_GEOMETRY", f"checks={wall_checks0}; obs={wall_obs0}", "VERIFY_FAILED")
        stage("WALL_IDENTIFIED", package=PKG02, guid=wall_guid, returned=returned_wall,
              checks=wall_checks0, observation=wall_obs0)

        project_recheck(b, a.expect_project)
        stage("WALL_LAYER_INTENT", package=PKG02, guid=wall_guid, layer_index=t2c.LAYER_INDEX, attempt=1)
        try:
            set_layer_once(b, wall_guid)
        except Exception as e:
            raise Stop("WALL_LAYER_WRITE", f"{type(e).__name__}: {e}", "UNKNOWN")
        raw_wall = b.details_raw(wall_guid) or {}
        wall_layer_name = t2c.read1(b, t2c.LAYER_REF, wall_guid)
        if int(raw_wall.get("layerIndex", -1)) != t2c.LAYER_INDEX or wall_layer_name != t2c.LAYER_NAME:
            raise Stop("WALL_LAYER_READBACK", f"layerIndex={raw_wall.get('layerIndex')}, name={wall_layer_name!r}", "VERIFY_FAILED")

        original_wall_id = t2c.read1(b, t2c.ID_REF, wall_guid)
        wall_marker = f"{PREFIX}{uuid.uuid4().hex}:WALL"
        rec["artifacts"].append({"kind": "Wall", "guid": wall_guid,
                                 "original_element_id": original_wall_id,
                                 "manual_cleanup": "delete/undo only after visual inspection; never auto-delete"})
        setrec(artifacts=rec["artifacts"], cleanup={"action": "do not auto-delete T3 artifacts"})

        project_recheck(b, a.expect_project)
        stage("WALL_MARKER_INTENT", package=PKG02, guid=wall_guid, marker=wall_marker, attempt=1)
        try:
            b.set_property_value(wall_guid, t2c.ID_REF, wall_marker)
        except Exception as e:
            raise Stop("WALL_MARKER_WRITE", f"{type(e).__name__}: {e}", "UNKNOWN")
        if t2c.read1(b, t2c.ID_REF, wall_guid) != wall_marker:
            raise Stop("WALL_MARKER_READBACK", "marker mismatch", "VERIFY_FAILED")
        marker_hits = [g for g in b.all_elements() or [] if t2c.read1(b, t2c.ID_REF, g) == wall_marker]
        if marker_hits != [wall_guid]:
            raise Stop("WALL_MARKER_SEARCH", f"hits={marker_hits}", "VERIFY_FAILED")

        wall_obs = t2c.observe(b, wall_guid, stories_now)
        wall_checks = t2c.geometry_checks(wall_obs, wall_segment(origin))
        if not all(wall_checks.values()):
            raise Stop("WALL_FINAL_VERIFY", f"checks={wall_checks}; obs={wall_obs}", "VERIFY_FAILED")

        stage("WALL_RESTORE_MARKER_INTENT", package=PKG02, guid=wall_guid,
              restore_to=original_wall_id, attempt=1)
        try:
            b.set_property_value(wall_guid, t2c.ID_REF,
                                 original_wall_id if original_wall_id not in (None, "") else "")
        except Exception as e:
            raise Stop("WALL_RESTORE_MARKER", f"{type(e).__name__}: {e}", "UNKNOWN")
        restored = t2c.read1(b, t2c.ID_REF, wall_guid)
        want = original_wall_id if original_wall_id not in (None, "") else None
        got = restored if restored not in (None, "") else None
        if got != want:
            raise Stop("WALL_RESTORE_VERIFY", f"expected={want!r}, got={restored!r}", "UNKNOWN")
        if t2c.scan_prefix(b, set(b.all_elements() or []), PREFIX):
            raise Stop("WALL_MARKER_SWEEP", "T3 marker leftover", "UNKNOWN")

        rec["mapping"]["host_wall"] = {
            "state": "CONFIRMED",
            "guid": wall_guid,
            "method": "SET_DIFF+CREATE_RESPONSE_MATCH+MARKER_ROUNDTRIP+READBACK",
        }
        setrec(mapping=rec["mapping"])
        stage("WALL_MAPPING_CONFIRMED", package=PKG02, mapping=rec["mapping"]["host_wall"])
        complete_pkg(PKG02)

        # PKG04: opening may start only after PKG02 is COMPLETED and mapping is confirmed.
        if rec["packages"].get(PKG02) != "COMPLETED" or rec["mapping"].get("host_wall", {}).get("state") != "CONFIRMED":
            raise Stop("DEPENDENCY_GATE", "opening dispatch attempted without completed/confirmed wall", "DEPENDENCY_BLOCKED")
        start_pkg(PKG04)

        project_recheck(b, a.expect_project)
        host_obs = t2c.observe(b, wall_guid, b.stories())
        host_checks = t2c.geometry_checks(host_obs, wall_segment(origin))
        if not all(host_checks.values()):
            raise Stop("HOST_DRIFT_BEFORE_OPENING", f"checks={host_checks}; obs={host_obs}", "MODEL_DRIFT")
        assert_area_clean(b, set(b.all_elements() or []), origin, allowed={wall_guid})
        stage("OPENING_DEPENDENCY_GATE", package=PKG04, wall_package=rec["packages"][PKG02],
              wall_mapping=rec["mapping"]["host_wall"], host_checks=host_checks)

        before_open_all = set(b.all_elements() or [])
        before_open_set = set(b.elements_by_type("Opening") or [])
        op_payload = opening_payload(origin, wall_guid)
        stage("OPENING_CREATE_INTENT", package=PKG04, payload=op_payload, attempt=1,
              dependency_wall_guid=wall_guid,
              note="receipt fsynced; exactly one CreateOpenings attempt")
        try:
            returned_opening = create_opening_once(b, op_payload)
        except Exception as e:
            setrec(status="UNKNOWN", cleanup={"action": "DO NOT RETRY; reconcile T3 opening",
                                              "host_wall_guid": wall_guid,
                                              "reason": "CreateOpenings may have applied"})
            raise Stop("OPENING_CREATE_DISPATCH", f"{type(e).__name__}: {e}", "UNKNOWN")

        after_open_all = set(b.all_elements() or [])
        after_open_set = set(b.elements_by_type("Opening") or [])
        new_all2 = sorted(after_open_all - before_open_all)
        new_openings = sorted(after_open_set - before_open_set)
        if len(new_all2) != 1 or new_all2 != new_openings:
            raise Stop("OPENING_IDENTIFY", f"new_all={new_all2}, new_openings={new_openings}", "UNKNOWN")
        opening_guid = new_openings[0]
        if returned_opening != [opening_guid]:
            raise Stop("OPENING_RESPONSE_CHECK", f"returned={returned_opening}, independent={[opening_guid]}", "UNKNOWN")
        rec["artifacts"].append({"kind": "Opening", "guid": opening_guid,
                                 "host_wall_guid": wall_guid,
                                 "manual_cleanup": "delete/undo only after visual inspection; never auto-delete"})
        setrec(artifacts=rec["artifacts"], cleanup={"action": "do not auto-delete T3 artifacts"})

        op_obs = observe_opening(b, opening_guid)
        required_fields = [op_obs.get("type"), op_obs.get("owner_guid"), op_obs.get("base_point"),
                           op_obs.get("width"), op_obs.get("height")]
        if any(v in (None, {}) for v in required_fields):
            raise Stop("OPENING_READBACK", f"required opening fields unavailable: {op_obs}", "VERIFY_UNAVAILABLE")
        op_checks = opening_checks(op_obs, origin, wall_guid)
        if not all(op_checks.values()):
            raise Stop("OPENING_VERIFY", f"checks={op_checks}; obs={op_obs}", "VERIFY_FAILED")
        stage("OPENING_BOUND_TO_HOST", package=PKG04, guid=opening_guid,
              host_wall_guid=wall_guid, returned=returned_opening,
              checks=op_checks, observation=op_obs)

        rec["mapping"]["opening"] = {
            "state": "CONFIRMED",
            "guid": opening_guid,
            "owner_wall_guid": wall_guid,
            "method": "SET_DIFF+CREATE_RESPONSE_MATCH+OWNER_READBACK",
        }
        setrec(mapping=rec["mapping"])
        complete_pkg(PKG04)

        final_walls = set(b.elements_by_type("Wall") or [])
        final_openings = set(b.elements_by_type("Opening") or [])
        wall_delta = len(final_walls) - len(before_walls)
        opening_delta = len(final_openings) - len(before_openings)
        if wall_delta != 1 or opening_delta != 1:
            raise Stop("FINAL_COUNT", f"wall_delta={wall_delta}, opening_delta={opening_delta}", "VERIFY_FAILED")

        report = {
            "probe": "AUDIT_T3_DEPENDENCY",
            "version": VER,
            "generated_at": now(),
            "archicad": info,
            "backend": "tapir",
            "adapter_version": addon,
            "origin": list(origin),
            "packages": dict(rec["packages"]),
            "mapping": rec["mapping"],
            "artifacts": rec["artifacts"],
            "results": {
                "package_order": [PKG01, PKG02, PKG04],
                "opening_dispatched_after_wall_completed": True,
                "opening_bound_to_confirmed_wall": True,
                "wall_delta": wall_delta,
                "opening_delta": opening_delta,
                "opening_checks": op_checks,
            },
            "verdicts": {
                "audit_t3_machine_go": True,
                "manual_visual_check_required": True,
                "production_integration_ready": False,
            },
            "blocked_by": ["manual_visual_check_pending", "live_T4_T7_not_run"],
        }
        jwrite(a.report, report)
        setrec(status="MACHINE_OK_VISUAL_PENDING", cleanup=None, finished_at=now(), report=a.report)

        print("AUDIT T3 DEPENDENCY MACHINE GO")
        print("package order      :", " -> ".join([PKG01, PKG02, PKG04]))
        print("host wall GUID     :", wall_guid)
        print("opening GUID       :", opening_guid)
        print("opening owner GUID :", op_obs["owner_guid"])
        print("wall delta         :", wall_delta)
        print("opening delta      :", opening_delta)
        print("DEPENDENCY GATE    : OK")
        print("OWNER BINDING      : OK")
        print("MANUAL VISUAL CHECK REQUIRED")
        print("DO NOT delete/undo T3 artifacts yet.")
        print("receipt:", a.out)
        print("report :", a.report)
        return 0

    except Stop as s:
        setrec(status=s.status, stopped_at_stage=s.stage, reason=s.reason, stopped_at=now())
        print(f"STOP at {s.stage}: {s.reason}", file=sys.stderr)
        print("receipt:", a.out, file=sys.stderr)
        return 1
    except Exception as e:
        setrec(status="UNKNOWN", reason=f"{type(e).__name__}: {e}", stopped_at=now())
        print(f"UNKNOWN: {type(e).__name__}: {e}", file=sys.stderr)
        print("receipt:", a.out, file=sys.stderr)
        return 1
    finally:
        try:
            os.unlink(lock)
        except OSError:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
