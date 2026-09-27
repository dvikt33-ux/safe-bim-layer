#!/usr/bin/env python3
"""Audit T2: four-wall closed contour + T-junction + abutment.

This is a standalone live probe for the disposable MCP_TEST.pln. It is NOT the
production Router.

Safety contract:
- read-only dry-run can auto-locate a free candidate area;
- a live run MUST receive the exact origin explicitly;
- six wall creates are six single-item dispatches, never a bulk create;
- one attempt per mutation, no automatic retry;
- receipt is fsynced before every mutation;
- every newly created wall is independently identified by GUID-set difference;
- create-return GUID is checked only after independent identification;
- each wall gets a temporary unique Element ID marker, then all markers are
  restored after final verification;
- walls are NEVER auto-deleted; manual visual inspection/cleanup is required;
- an expected geometry mismatch at a join is VERIFY_SPEC_NOT_READY, not UNKNOWN.

The historical probe_t2_live_v13.py corresponds to audit T1 (single wall).
See TEST_SEQUENCE.md.
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

VER = "1.0"
ADDON = "1.5.9"
FLOOR, STORY, ELEV = 0, "Первый Этаж", 0.0
HEIGHT, THICK, OFFSET, ARC = 3.0, 0.30, 0.0, 0.0
REFLINE, RADIUS = "CoreOutside", 3.0
LAYER_INDEX = 33
LAYER_NAME = "Конструктив - Несущие Элементы"
WITNESS = "A0159B37-5EA0-48BB-A8C4-4DDE446DAF61"
ID_REF = {"kind": "builtin", "id": "General_ElementID"}
LAYER_REF = {"kind": "name", "address": "ModelView_LayerName"}
PREFIX = "BX:T2C:"

# Relative geometry. The rectangle is 6 x 4 m. T_INNER terminates at the
# middle of RECT_BOTTOM; ABUT_OUTER terminates at the middle of RECT_RIGHT
# from the outside. Together they exercise join/abutment behaviour and
# direction-sensitive CoreOutside reference lines.
SEGMENTS = [
    {"label": "RECT_BOTTOM", "role": "closed_contour", "from": (0.0, 0.0), "to": (6.0, 0.0)},
    {"label": "RECT_RIGHT", "role": "closed_contour", "from": (6.0, 0.0), "to": (6.0, 4.0)},
    {"label": "RECT_TOP", "role": "closed_contour", "from": (6.0, 4.0), "to": (0.0, 4.0)},
    {"label": "RECT_LEFT", "role": "closed_contour", "from": (0.0, 4.0), "to": (0.0, 0.0)},
    {"label": "T_INNER", "role": "t_junction", "from": (3.0, 0.0), "to": (3.0, 2.0)},
    {"label": "ABUT_OUTER", "role": "abutment", "from": (9.0, 2.0), "to": (6.0, 2.0)},
]


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


def read1(b: TapirBackendV13, ref: dict[str, Any], guid: str) -> Any:
    return (b.get_property_values(ref, [guid]) or {}).get(guid)


def story_at(stories: list[dict[str, Any]], idx: int) -> dict[str, Any] | None:
    return next((s for s in stories if s.get("index") == idx), None)


def scan_prefix(b: TapirBackendV13, guids: list[str] | set[str], prefix: str) -> list[str]:
    ordered = sorted(guids)
    vals = b.get_property_values(ID_REF, ordered) or {}
    return sorted(g for g, v in vals.items() if isinstance(v, str) and v.startswith(prefix))


def witness_composite(b: TapirBackendV13) -> str:
    raw = b.details_raw(WITNESS) or {}
    det = raw.get("details") if isinstance(raw.get("details"), dict) else {}
    if int(raw.get("layerIndex", -1)) != LAYER_INDEX:
        raise Stop("PRECHECK_LAYER", f"witness layerIndex={raw.get('layerIndex')}", "NO_GO")
    if read1(b, LAYER_REF, WITNESS) != LAYER_NAME:
        raise Stop("PRECHECK_LAYER", "witness layer name mismatch", "NO_GO")
    if det.get("structureType") != "Composite":
        raise Stop("PRECHECK_STRUCTURE", f"witness structureType={det.get('structureType')!r}", "NO_GO")
    comp = base._to_dict(det.get("compositeId"))
    if not comp.get("guid"):
        raise Stop("PRECHECK_STRUCTURE", "witness compositeId missing", "NO_GO")
    return str(comp["guid"])


def abs_segments(origin: tuple[float, float]) -> list[dict[str, Any]]:
    ox, oy = origin
    out = []
    for seg in SEGMENTS:
        a = (ox + seg["from"][0], oy + seg["from"][1])
        z = (ox + seg["to"][0], oy + seg["to"][1])
        out.append({**seg, "from_abs": a, "to_abs": z, "length": math.hypot(z[0] - a[0], z[1] - a[1])})
    return out


def wall_payload(seg: dict[str, Any], comp_guid: str) -> dict[str, Any]:
    a, z = seg["from_abs"], seg["to_abs"]
    return {"wallsData": [{
        "begCoordinate": {"x": a[0], "y": a[1]},
        "endCoordinate": {"x": z[0], "y": z[1]},
        "floorIndex": FLOOR,
        "zCoordinate": 0.0,
        "height": HEIGHT,
        "thickness": THICK,
        "offset": OFFSET,
        "arcAngle": ARC,
        "referenceLineLocation": REFLINE,
        "structureType": "Composite",
        "compositeId": {"guid": comp_guid},
    }]}


def addon_once(b: TapirBackendV13, name: str, params: dict[str, Any]) -> Any:
    raise RuntimeError('probe write path is disabled: Tapir mutations must use the Safe BIM gateway')
    # Dedicated live-probe path. Do not widen T0's mutation denylist.
    b._connect()
    act = b.conn.types
    return b.conn.commands.ExecuteAddOnCommand(act.AddOnCommandId(b.ns, name), params)


def create_once(b: TapirBackendV13, payload: dict[str, Any]) -> list[str]:
    res = addon_once(b, "CreateWalls", payload)
    d = base._to_dict(res)
    items = base._as_list(d.get("elements") or res)
    guids, errors = [], []
    for item in items:
        row = base._to_dict(item)
        if row.get("error"):
            errors.append(row["error"])
            continue
        g = base._guid(item)
        if g:
            guids.append(g)
    if errors:
        raise base.BackendError(f"CreateWalls errors: {errors}")
    return guids


def set_layer_once(b: TapirBackendV13, guid: str) -> None:
    res = addon_once(b, "SetDetailsOfElements", {
        "elementsWithDetails": [{
            "elementId": {"guid": guid},
            "details": {"layerIndex": LAYER_INDEX},
        }]
    })
    d = base._to_dict(res)
    for item in base._as_list(d.get("executionResults") or res):
        row = base._to_dict(item)
        if row.get("error") or row.get("success") is False:
            raise base.BackendError(f"SetDetailsOfElements failed: {row}")


def bbox_map(b: TapirBackendV13, guids: list[str] | set[str]) -> dict[str, list[float]]:
    ordered = sorted(guids)
    if not ordered:
        return {}
    res = b.raw_call("Get3DBoundingBoxes", {
        "elements": [{"elementId": {"guid": g}} for g in ordered]
    })
    d = base._to_dict(res)
    items = base._as_list(d.get("boundingBoxes3D") or d.get("boundingBoxes") or res)
    if len(items) != len(ordered):
        raise Stop("BBOX", f"requested={len(ordered)} returned={len(items)}", "NO_GO")
    out: dict[str, list[float]] = {}
    keys = ("xMin", "yMin", "zMin", "xMax", "yMax", "zMax")
    for g, obj in zip(ordered, items):
        row = base._to_dict(obj)
        if row.get("error"):
            raise Stop("BBOX", f"{g}: {row['error']}", "NO_GO")
        box = base._to_dict(row.get("boundingBox3D") or row.get("boundingBox"))
        if any(box.get(k) is None for k in keys):
            raise Stop("BBOX", f"{g}: incomplete bbox {box}", "NO_GO")
        out[g] = [float(box[k]) for k in keys]
    return out


def protection_box(origin: tuple[float, float]) -> list[float]:
    segs = abs_segments(origin)
    xs = [p for s in segs for p in (s["from_abs"][0], s["to_abs"][0])]
    ys = [p for s in segs for p in (s["from_abs"][1], s["to_abs"][1])]
    return [min(xs) - RADIUS, min(ys) - RADIUS, 0.0,
            max(xs) + RADIUS, max(ys) + RADIUS, HEIGHT]


def overlaps(a: list[float], b: list[float]) -> bool:
    return not (
        a[3] < b[0] or a[0] > b[3] or
        a[4] < b[1] or a[1] > b[4] or
        a[5] < b[2] or a[2] > b[5]
    )


def conflicts(boxes: dict[str, list[float]], origin: tuple[float, float], allowed: set[str] | None = None) -> list[dict[str, Any]]:
    pbox = protection_box(origin)
    allowed = allowed or set()
    return [{"guid": g, "bbox": box} for g, box in boxes.items()
            if g not in allowed and overlaps(box, pbox)]


def candidate_origins() -> list[tuple[float, float]]:
    vals = list(range(-100, 101, 20))
    pts = [(float(x), float(y)) for x in vals for y in vals]
    # Prefer nearby positive coordinates after the already-used origin area.
    pts.sort(key=lambda p: (p[0] * p[0] + p[1] * p[1], p[0] < 0, p[1] < 0, p[0], p[1]))
    return pts


def choose_free_origin(b: TapirBackendV13, guids: set[str]) -> tuple[float, float]:
    boxes = bbox_map(b, guids)
    for origin in candidate_origins():
        if not conflicts(boxes, origin):
            return origin
    raise Stop("PRECHECK_AREA", "no free candidate origin in +/-100 m grid", "NO_GO")


def assert_area_clean(b: TapirBackendV13, guids: set[str], origin: tuple[float, float], allowed: set[str] | None = None) -> None:
    bad = conflicts(bbox_map(b, guids), origin, allowed)
    if bad:
        raise Stop("PRECHECK_AREA", f"foreign element in protection volume: {bad}", "NO_GO")


def project_recheck(b: TapirBackendV13, expect_project: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    info = b.project_info()
    path = info.get("project_path") or ""
    if (os.path.normcase(path) != os.path.normcase(expect_project)
            or info.get("is_untitled") or info.get("is_teamwork")):
        raise Stop("BINDING", f"project mismatch: {info}", "UNKNOWN")
    stories = b.stories()
    st = story_at(stories, FLOOR)
    if (not st or (st.get("name") or "").strip() != STORY
            or not close(st.get("elevation"), ELEV, 1e-9)):
        raise Stop("BINDING", f"story mismatch: {st}", "UNKNOWN")
    return info, stories


def observe(b: TapirBackendV13, guid: str, stories: list[dict[str, Any]]) -> dict[str, Any]:
    raw = b.details_raw(guid) or {}
    norm = b.details(guid) or {}
    det = raw.get("details") if isinstance(raw.get("details"), dict) else {}
    out = {k: v for k, v in norm.items() if v is not None}
    out["type"] = norm.get("type") or raw.get("type")
    out["floor_index"] = raw.get("floorIndex")
    st = story_at(stories, int(raw["floorIndex"])) if raw.get("floorIndex") is not None else None
    if st:
        out["story"] = {"name": st.get("name"), "elevation": st.get("elevation")}
    out["layer_index"] = raw.get("layerIndex")
    out["layer"] = read1(b, LAYER_REF, guid)
    if det.get("height") is not None:
        out["height"] = float(det["height"])
    bt, et = det.get("begThickness"), det.get("endThickness")
    if bt is not None and et is not None and close(bt, et, 1e-9):
        out["thickness"] = float(bt)
    out["_extra"] = {
        "referenceLineLocation": det.get("referenceLineLocation"),
        "offset": det.get("offset"),
        "arcAngle": det.get("arcAngle"),
        "structureType": det.get("structureType"),
        "compositeId": base._to_dict(det.get("compositeId")),
    }
    return out


def refline_matches(obs: dict[str, Any], seg: dict[str, Any], tol: float = 0.01) -> bool:
    rl = obs.get("ref_line") or {}
    a, z = rl.get("from"), rl.get("to")
    want_a, want_z = seg["from_abs"], seg["to_abs"]
    return (
        isinstance(a, list) and isinstance(z, list) and len(a) == 2 and len(z) == 2
        and close(a[0], want_a[0], tol) and close(a[1], want_a[1], tol)
        and close(z[0], want_z[0], tol) and close(z[1], want_z[1], tol)
    )


def geometry_checks(obs: dict[str, Any], seg: dict[str, Any], marker: str | None = None) -> dict[str, bool]:
    ex = obs.get("_extra") or {}
    checks = {
        "type": obs.get("type") == "Wall",
        "story": isinstance(obs.get("story"), dict)
                 and obs["story"].get("name") == STORY
                 and close(obs["story"].get("elevation"), ELEV, 1e-6),
        "layer": obs.get("layer") == LAYER_NAME,
        "ref_line": refline_matches(obs, seg),
        "length": close(obs.get("length"), seg["length"], 0.05),
        "height": close(obs.get("height"), HEIGHT),
        "thickness": close(obs.get("thickness"), THICK),
        "referenceLineLocation": ex.get("referenceLineLocation") == REFLINE,
        "offset": close(ex.get("offset"), OFFSET),
        "arcAngle": close(ex.get("arcAngle"), ARC),
    }
    if marker is not None:
        checks["marker_exact"] = True  # exact search is checked separately and recorded.
    return checks


def rough_identity_ok(obs: dict[str, Any], seg: dict[str, Any]) -> bool:
    # This guard runs immediately after each single create, before future joins can
    # alter presentation. It intentionally ignores layer because layer is set next.
    checks = geometry_checks(obs, seg)
    checks.pop("layer", None)
    return all(checks.values())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--expect-project", required=True)
    ap.add_argument("--port", type=int, default=19723)
    ap.add_argument("--origin-x", type=float, default=None)
    ap.add_argument("--origin-y", type=float, default=None)
    ap.add_argument("--out", default="t2_connections_receipt_live_v13.json")
    ap.add_argument("--report", default="t2_connections_report_live_v13.json")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--allow-write", action="store_true")
    ap.add_argument("--i-understand-this-writes-to-archicad", action="store_true")
    a = ap.parse_args()

    if a.allow_write != a.i_understand_this_writes_to_archicad:
        print("STOP: нужны оба write-флага одновременно", file=sys.stderr)
        return 1
    write_enabled = bool(a.allow_write and a.i_understand_this_writes_to_archicad)
    if write_enabled and (a.origin_x is None or a.origin_y is None):
        print("STOP: live T2 requires explicit --origin-x and --origin-y from a prior dry-run", file=sys.stderr)
        return 1
    if (a.origin_x is None) != (a.origin_y is None):
        print("STOP: origin requires both --origin-x and --origin-y", file=sys.stderr)
        return 1
    if os.path.exists(a.out):
        print(f"STOP: receipt already exists: {a.out}", file=sys.stderr)
        return 1

    rec: dict[str, Any] = {
        "probe": "AUDIT_T2_CONNECTIONS", "version": VER,
        "host": f"{platform.system()} {platform.release()}",
        "started_at": now(), "status": "RUNNING", "stages": [],
        "artifacts": [], "cleanup": None,
    }
    jwrite(a.out, rec)

    def stage(name: str, **kw: Any) -> None:
        rec["stages"].append({"stage": name, "at": now(), **kw})
        jwrite(a.out, rec)

    def setrec(**kw: Any) -> None:
        rec.update(kw)
        jwrite(a.out, rec)

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
        before_counts = b.count_by_type()
        leftovers = scan_prefix(b, before_all, "BX:")
        if leftovers:
            raise Stop("PRECHECK_MARKERS", f"existing BX markers: {leftovers}", "NO_GO")

        if a.origin_x is None:
            origin = choose_free_origin(b, before_all)
        else:
            origin = (float(a.origin_x), float(a.origin_y))
            assert_area_clean(b, before_all, origin)
        segs = abs_segments(origin)
        payloads = [{"label": s["label"], "role": s["role"], "payload": wall_payload(s, comp)} for s in segs]

        stage("PRECHECK", project=info, addon=addon, origin=list(origin),
              protection_box=protection_box(origin), before_all=len(before_all),
              before_walls=len(before_walls), before_counts=before_counts,
              scratch="FREE", composite_guid=comp, planned=payloads)

        if a.dry_run or not write_enabled:
            setrec(status="DRY_RUN_OK", origin=list(origin))
            print("AUDIT T2 CONNECTIONS DRY-RUN OK")
            print("MUTATIONS: 0")
            print(f"SUGGESTED ORIGIN: --origin-x {origin[0]} --origin-y {origin[1]}")
            print(json.dumps(payloads, ensure_ascii=False, indent=2))
            return 0

        created: list[dict[str, Any]] = []
        created_guids: set[str] = set()

        for idx, seg in enumerate(segs, 1):
            # Revalidate binding and ensure no foreign element entered the whole T2 area.
            info_now, stories_now = project_recheck(b, a.expect_project)
            current_all = set(b.all_elements() or [])
            assert_area_clean(b, current_all, origin, allowed=created_guids)
            before_step_all = current_all
            before_step_walls = set(b.elements_by_type("Wall") or [])
            p = wall_payload(seg, comp)

            stage("CREATE_INTENT", index=idx, label=seg["label"], role=seg["role"],
                  payload=p, attempt=1, project=info_now,
                  note="receipt fsynced before single-wall CreateWalls")
            try:
                returned = create_once(b, p)
            except Exception as e:
                setrec(status="UNKNOWN", cleanup={
                    "action": "DO NOT RETRY; inspect/reconcile MCP_TEST.pln",
                    "created_so_far": created,
                    "reason": f"CreateWalls for {seg['label']} may have applied before error",
                })
                raise Stop("CREATE_DISPATCH", f"{seg['label']}: {type(e).__name__}: {e}", "UNKNOWN")

            after_step_all = set(b.all_elements() or [])
            after_step_walls = set(b.elements_by_type("Wall") or [])
            new_all = sorted(after_step_all - before_step_all)
            new_walls = sorted(after_step_walls - before_step_walls)
            if len(new_all) != 1 or new_all != new_walls:
                raise Stop("IDENTIFY_NEW_WALL",
                           f"{seg['label']}: new_all={new_all}, new_walls={new_walls}", "UNKNOWN")
            guid = new_walls[0]
            if returned != [guid]:
                raise Stop("CREATE_RESPONSE_CHECK",
                           f"{seg['label']}: returned={returned}, independent={[guid]}", "UNKNOWN")

            obs0 = observe(b, guid, stories_now)
            if not rough_identity_ok(obs0, seg):
                raise Stop("TAG_GUARD_GEOMETRY",
                           f"{seg['label']}: {json.dumps(obs0, ensure_ascii=False)}", "UNKNOWN")
            stage("IDENTIFIED", index=idx, label=seg["label"], guid=guid,
                  returned=returned, observation=obs0)

            project_recheck(b, a.expect_project)
            stage("LAYER_INTENT", index=idx, label=seg["label"], guid=guid,
                  layer_index=LAYER_INDEX, attempt=1)
            try:
                set_layer_once(b, guid)
            except Exception as e:
                raise Stop("LAYER_WRITE", f"{seg['label']}: {type(e).__name__}: {e}", "UNKNOWN")
            raw = b.details_raw(guid) or {}
            layer_name = read1(b, LAYER_REF, guid)
            if int(raw.get("layerIndex", -1)) != LAYER_INDEX or layer_name != LAYER_NAME:
                raise Stop("LAYER_READ_BACK",
                           f"{seg['label']}: layerIndex={raw.get('layerIndex')}, name={layer_name!r}", "UNKNOWN")
            stage("LAYER_READ_BACK", index=idx, label=seg["label"], guid=guid,
                  layer_index=LAYER_INDEX, layer_name=layer_name)

            original_id = read1(b, ID_REF, guid)
            marker = f"{PREFIX}{uuid.uuid4().hex}:{idx}"
            artifact = {
                "index": idx, "label": seg["label"], "role": seg["role"],
                "guid": guid, "requested": {"from": list(seg["from_abs"]), "to": list(seg["to_abs"]),
                                               "length": seg["length"]},
                "original_element_id": original_id, "marker": marker,
                "manual_cleanup": "delete/undo wall only after visual inspection; never auto-delete",
            }
            created.append(artifact)
            created_guids.add(guid)
            setrec(artifacts=created, cleanup={
                "action": "restore any remaining BX:T2C markers manually; do not auto-delete walls",
                "artifacts": created,
            })

            project_recheck(b, a.expect_project)
            stage("MARKER_INTENT", index=idx, label=seg["label"], guid=guid,
                  marker=marker, original_element_id=original_id, attempt=1)
            try:
                b.set_property_value(guid, ID_REF, marker)
            except Exception as e:
                raise Stop("MARKER_WRITE", f"{seg['label']}: {type(e).__name__}: {e}", "UNKNOWN")
            if read1(b, ID_REF, guid) != marker:
                raise Stop("MARKER_READ_BACK", f"{seg['label']}: marker mismatch", "UNKNOWN")
            all_now = sorted(b.all_elements() or [])
            vals = b.get_property_values(ID_REF, all_now) or {}
            exact = sorted(g for g, v in vals.items() if v == marker)
            prefix = sorted(g for g, v in vals.items() if isinstance(v, str) and v.startswith(PREFIX))
            if exact != [guid] or prefix != sorted(created_guids):
                raise Stop("MARKER_SEARCH",
                           f"{seg['label']}: exact={exact}, prefix={prefix}, expected_prefix={sorted(created_guids)}",
                           "UNKNOWN")
            stage("MARKER_BOUND", index=idx, label=seg["label"], guid=guid,
                  exact=exact, prefix=prefix)

        after_counts = b.count_by_type()
        delta = {k: int(after_counts.get(k, 0)) - int(before_counts.get(k, 0))
                 for k in set(after_counts) | set(before_counts)}
        delta = {k: v for k, v in delta.items() if v}
        if delta != {"Wall": len(segs)}:
            raise Stop("COUNT_DELTA", f"expected Wall={len(segs)}, got {delta}", "UNKNOWN")

        # Final geometry verification occurs only after all joins exist.
        final_rows = []
        strict_all = True
        for seg, art in zip(segs, created):
            obs = observe(b, art["guid"], stories)
            exact = [g for g in b.all_elements() or [] if read1(b, ID_REF, g) == art["marker"]]
            checks = geometry_checks(obs, seg, art["marker"])
            checks["marker_exact"] = exact == [art["guid"]]
            ok = all(checks.values())
            strict_all = strict_all and ok
            final_rows.append({
                "label": seg["label"], "role": seg["role"], "guid": art["guid"],
                "requested": {"from": list(seg["from_abs"]), "to": list(seg["to_abs"]),
                              "length": seg["length"]},
                "observation": obs, "checks": checks, "strict_ok": ok,
            })

        wrong_height_rejected = bool(final_rows) and not close(
            final_rows[0]["observation"].get("height"), HEIGHT + 0.5)
        if not wrong_height_rejected:
            raise Stop("NEGATIVE_CONTROL", "wrong-height expectation was not rejected", "UNKNOWN")
        stage("FINAL_VERIFY", strict_all=strict_all, count_delta=delta,
              wrong_height_rejected=wrong_height_rejected, walls=final_rows)

        # Restore temporary markers even when F-9 says verify_spec is not ready.
        for art in created:
            project_recheck(b, a.expect_project)
            stage("RESTORE_MARKER_INTENT", label=art["label"], guid=art["guid"],
                  restore_to=art["original_element_id"], attempt=1)
            try:
                b.set_property_value(
                    art["guid"], ID_REF,
                    art["original_element_id"] if art["original_element_id"] not in (None, "") else "")
            except Exception as e:
                raise Stop("RESTORE_MARKER", f"{art['label']}: {type(e).__name__}: {e}", "UNKNOWN")
            restored = read1(b, ID_REF, art["guid"])
            want = art["original_element_id"] if art["original_element_id"] not in (None, "") else None
            got = restored if restored not in (None, "") else None
            if got != want:
                raise Stop("VERIFY_MARKER_RESTORE",
                           f"{art['label']}: expected={want!r}, got={restored!r}", "UNKNOWN")
            stage("VERIFY_MARKER_RESTORE", label=art["label"], guid=art["guid"], value=restored)

        left = scan_prefix(b, set(b.all_elements() or []), PREFIX)
        if left:
            raise Stop("FINAL_SWEEP", f"leftovers={left}", "UNKNOWN")
        stage("FINAL_SWEEP", markers=[])

        report = {
            "probe": "AUDIT_T2_CONNECTIONS", "version": VER, "generated_at": now(),
            "audit_mapping": {
                "historical_probe_t2_live_v13": "AUDIT_T1_SINGLE_WALL",
                "this_probe": "AUDIT_T2_CONNECTIONS",
            },
            "archicad": info, "backend": "tapir", "adapter_version": addon,
            "origin": list(origin), "protection_box": protection_box(origin),
            "artifacts": created,
            "results": {
                "count_delta": delta,
                "walls": final_rows,
                "strict_geometry_all_ok": strict_all,
                "wrong_height_rejected": wrong_height_rejected,
                "marker_restored": True,
                "final_sweep": [],
            },
            "verdicts": {
                "audit_t2_machine_go": strict_all,
                "verify_spec_ready_for_connections": strict_all,
                "manual_visual_check_required": True,
                "production_integration_ready": False,
            },
            "capabilities": {"create_wall": {
                "production_safe": False,
                "probe_certified": False,
                "machine_certified_single_wall": True,
                "connections_tested": True,
                "connections_strict_ok": strict_all,
                "blocked_by": (["manual_visual_check_pending", "live_T3_T7_not_run"]
                               if strict_all else ["F9_verify_spec_connection_mismatch", "manual_visual_check_pending", "live_T3_T7_not_run"]),
            }},
        }
        jwrite(a.report, report)
        setrec(status=("MACHINE_OK_VISUAL_PENDING" if strict_all else "VERIFY_SPEC_NOT_READY"),
               cleanup=None, finished_at=now(), report=a.report)

        if strict_all:
            print("AUDIT T2 CONNECTIONS MACHINE GO")
            print("created walls     :", len(created))
            print("count delta       :", delta)
            print("strict geometry   : 6/6 OK after joins")
            print("negative control  : wrong height rejected")
            print("FINAL_SWEEP       : 0 T2C markers")
            print("MANUAL VISUAL CHECK REQUIRED")
            print("DO NOT delete/undo the walls yet.")
            print("receipt:", a.out)
            print("report :", a.report)
            return 0

        print("AUDIT T2 VERIFY_SPEC_NOT_READY", file=sys.stderr)
        print("At least one post-join strict geometry check mismatched.", file=sys.stderr)
        print("This is an F-9 result, not permission to loosen tolerances automatically.", file=sys.stderr)
        print("Walls remain for manual inspection; markers were restored.", file=sys.stderr)
        print("report:", a.report, file=sys.stderr)
        return 1

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
