#!/usr/bin/env python3
from __future__ import annotations

import argparse, json, os, platform, sys, time, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import backends as base
from backends_v13 import TapirBackendV13
import ac29_contract as contract

VER = "1.0"
ADDON = "1.5.9"
P0, P1 = (1.5, 2.5), (6.5, 2.5)
FLOOR, STORY, ELEV = 0, "Первый Этаж", 0.0
HEIGHT, THICK, OFFSET, ARC = 3.0, 0.30, 0.0, 0.0
REFLINE, RADIUS = "CoreOutside", 3.0
LAYER_INDEX = 33
LAYER_NAME = "Конструктив - Несущие Элементы"
WITNESS = "A0159B37-5EA0-48BB-A8C4-4DDE446DAF61"
ID_REF = {"kind": "builtin", "id": "General_ElementID"}
LAYER_REF = {"kind": "name", "address": "ModelView_LayerName"}
PREFIX = "BX:T2:"


class Stop(Exception):
    def __init__(self, stage, reason, status="UNKNOWN"):
        super().__init__(reason)
        self.stage, self.reason, self.status = stage, reason, status


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def jwrite(path, obj):
    base.write_json_atomic(path, obj)


def read1(b, ref, guid):
    return (b.get_property_values(ref, [guid]) or {}).get(guid)


def close(a, b, tol=0.001):
    try:
        return abs(float(a) - float(b)) <= tol
    except Exception:
        return False


def story_at(stories, idx):
    return next((s for s in stories if s.get("index") == idx), None)


def scan_prefix(b, guids, prefix):
    vals = b.get_property_values(ID_REF, list(guids)) or {}
    return sorted(g for g, v in vals.items()
                  if isinstance(v, str) and v.startswith(prefix))


def witness_composite(b):
    raw = b.details_raw(WITNESS) or {}
    det = raw.get("details") if isinstance(raw.get("details"), dict) else {}
    if int(raw.get("layerIndex", -1)) != LAYER_INDEX:
        raise Stop("PRECHECK_LAYER", f"witness layerIndex={raw.get('layerIndex')}", "NO_GO")
    if read1(b, LAYER_REF, WITNESS) != LAYER_NAME:
        raise Stop("PRECHECK_LAYER", "witness layer name mismatch", "NO_GO")
    if det.get("structureType") != "Composite":
        raise Stop("PRECHECK_STRUCTURE", f"structureType={det.get('structureType')!r}", "NO_GO")
    comp = base._to_dict(det.get("compositeId"))
    if not comp.get("guid"):
        raise Stop("PRECHECK_STRUCTURE", "compositeId missing", "NO_GO")
    return str(comp["guid"])


def payload(comp_guid):
    return contract.wall_payload(
        P0, P1, floor_index=FLOOR, height=HEIGHT, thickness=THICK,
        reference_line=REFLINE, structure_type="Composite", composite_id=comp_guid)


def assert_scratch_free(b, guids):
    ordered = sorted(guids)
    res = b.raw_call("Get3DBoundingBoxes", {
        "elements": [{"elementId": {"guid": g}} for g in ordered]
    })
    d = base._to_dict(res)
    items = base._as_list(d.get("boundingBoxes3D") or d.get("boundingBoxes") or res)
    if len(items) != len(ordered):
        raise Stop("PRECHECK_BBOX",
                   f"requested={len(ordered)} returned={len(items)}", "NO_GO")
    xmin, xmax = min(P0[0], P1[0]) - RADIUS, max(P0[0], P1[0]) + RADIUS
    ymin, ymax = min(P0[1], P1[1]) - RADIUS, max(P0[1], P1[1]) + RADIUS
    blocked = []
    for g, obj in zip(ordered, items):
        row = base._to_dict(obj)
        if row.get("error"):
            raise Stop("PRECHECK_BBOX", f"{g}: {row['error']}", "NO_GO")
        box = base._to_dict(row.get("boundingBox3D") or row.get("boundingBox"))
        keys = ("xMin", "yMin", "zMin", "xMax", "yMax", "zMax")
        if any(box.get(k) is None for k in keys):
            raise Stop("PRECHECK_BBOX", f"{g}: incomplete bbox {box}", "NO_GO")
        x0, y0, z0, x1, y1, z1 = [float(box[k]) for k in keys]
        if not (x1 < xmin or x0 > xmax or y1 < ymin or y0 > ymax) and not (z1 < 0 or z0 > HEIGHT):
            blocked.append({"guid": g, "bbox": [x0, y0, z0, x1, y1, z1]})
    if blocked:
        raise Stop("PRECHECK_BBOX", f"scratch blocked: {blocked}", "NO_GO")


def addon_once(b, name, params):
    # Dedicated T2 write path. We intentionally do NOT widen the T0 backend
    # denylist; only this standalone probe can dispatch these explicit commands.
    b._connect()
    act = b.conn.types
    return b.conn.commands.ExecuteAddOnCommand(
        act.AddOnCommandId(b.ns, name), params
    )


def create_once(b, p):
    return contract.create_wall_once(b, p)


def set_layer_once(b, guid):
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


def observe(b, guid, stories):
    raw = b.details_raw(guid) or {}
    norm = b.details(guid) or {}
    det = raw.get("details") if isinstance(raw.get("details"), dict) else {}
    out = {k: v for k, v in norm.items() if v is not None}
    st = story_at(stories, int(raw["floorIndex"])) if raw.get("floorIndex") is not None else None
    if st:
        out["story"] = {"name": st.get("name"), "elevation": st.get("elevation")}
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
    }
    return out


def refline_ok(obs):
    rl = obs.get("ref_line") or {}
    a, z = rl.get("from"), rl.get("to")
    return (
        isinstance(a, list) and isinstance(z, list) and len(a) == 2 and len(z) == 2
        and close(a[0], P0[0], 0.01) and close(a[1], P0[1], 0.01)
        and close(z[0], P1[0], 0.01) and close(z[1], P1[1], 0.01)
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--expect-project", required=True)
    ap.add_argument("--port", type=int, default=19723)
    ap.add_argument("--out", default="t2_receipt_live_v13.json")
    ap.add_argument("--report", default="t2_report_live_v13.json")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--allow-write", action="store_true")
    ap.add_argument("--i-understand-this-writes-to-archicad", action="store_true")
    a = ap.parse_args()

    if a.allow_write != a.i_understand_this_writes_to_archicad:
        print("STOP: нужны оба write-флага одновременно", file=sys.stderr)
        return 1
    if os.path.exists(a.out):
        print(f"STOP: receipt already exists: {a.out}", file=sys.stderr)
        return 1

    rec = {
        "probe": "T2", "version": VER,
        "host": f"{platform.system()} {platform.release()}",
        "started_at": now(), "status": "RUNNING", "stages": [],
        "artifact": None, "cleanup": None,
    }
    jwrite(a.out, rec)

    def stage(name, **kw):
        rec["stages"].append({"stage": name, "at": now(), **kw})
        jwrite(a.out, rec)

    def setrec(**kw):
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

        info = b.project_info()
        path = info.get("project_path") or ""
        if (os.path.normcase(path) != os.path.normcase(a.expect_project)
                or info.get("is_untitled") or info.get("is_teamwork")):
            raise Stop("PRECHECK_PROJECT", str(info), "NO_GO")

        stories = b.stories()
        st = story_at(stories, FLOOR)
        if (not st or (st.get("name") or "").strip() != STORY
                or not close(st.get("elevation"), ELEV, 1e-9)):
            raise Stop("PRECHECK_STORY", str(st), "NO_GO")

        comp = witness_composite(b)
        before_all = set(b.all_elements() or [])
        before_walls = set(b.elements_by_type("Wall") or [])
        before_counts = b.count_by_type()
        leftovers = scan_prefix(b, before_all, "BX:")
        if leftovers:
            raise Stop("PRECHECK_MARKERS", f"existing BX markers: {leftovers}", "NO_GO")
        assert_scratch_free(b, before_all)
        p = payload(comp)

        stage("PRECHECK", project=info, addon=addon, story=st,
              before_all=len(before_all), before_walls=len(before_walls),
              before_counts=before_counts, scratch="FREE",
              layer_index=LAYER_INDEX, layer_name=LAYER_NAME,
              composite_guid=comp, payload=p)

        write_enabled = a.allow_write and a.i_understand_this_writes_to_archicad
        if a.dry_run or not write_enabled:
            setrec(status="DRY_RUN_OK")
            print("T2 DRY-RUN OK")
            print("MUTATIONS: 0")
            print(json.dumps(p, ensure_ascii=False, indent=2))
            return 0

        stage("CREATE_INTENT", payload=p, attempt=1,
              note="receipt fsynced before CreateWalls")
        try:
            returned = create_once(b, p)
        except Exception as e:
            setrec(status="UNKNOWN", cleanup={
                "action": "DO NOT RETRY; inspect MCP_TEST.pln and reconcile",
                "reason": "CreateWalls may have applied before error",
            })
            raise Stop("CREATE_DISPATCH", f"{type(e).__name__}: {e}", "UNKNOWN")
        stage("CREATE_RETURNED", returned_guids=returned)

        after_all = set(b.all_elements() or [])
        after_walls = set(b.elements_by_type("Wall") or [])
        new_all = sorted(after_all - before_all)
        new_walls = sorted(after_walls - before_walls)
        if len(new_all) != 1 or new_all != new_walls:
            raise Stop("IDENTIFY_NEW_WALL",
                       f"new_all={new_all}, new_walls={new_walls}", "UNKNOWN")
        guid = new_walls[0]
        setrec(artifact={
            "guid": guid, "kind": "Wall",
            "manual_cleanup": "delete/undo after visual inspection; never auto-delete"
        })
        stage("IDENTIFIED", guid=guid, new_all=new_all, new_walls=new_walls)
        if returned != [guid]:
            raise Stop("CREATE_RESPONSE_CHECK",
                       f"returned={returned}, set_diff={[guid]}", "UNKNOWN")

        o0 = observe(b, guid, stories)
        e0 = o0["_extra"]
        if not (
            o0.get("type") == "Wall"
            and o0.get("floor_index") == FLOOR
            and refline_ok(o0)
            and close(o0.get("length"), 5.0, 0.05)
            and close(o0.get("height"), HEIGHT)
            and close(o0.get("thickness"), THICK)
            and e0.get("referenceLineLocation") == REFLINE
            and close(e0.get("offset"), OFFSET)
            and close(e0.get("arcAngle"), ARC)
        ):
            raise Stop("VERIFY_CREATED_GEOMETRY", json.dumps(o0, ensure_ascii=False), "UNKNOWN")
        stage("CREATED_GEOMETRY_VERIFIED", guid=guid, observation=o0)

        stage("LAYER_INTENT", guid=guid, layer_index=LAYER_INDEX, attempt=1)
        try:
            set_layer_once(b, guid)
        except Exception as e:
            raise Stop("LAYER_WRITE", f"{type(e).__name__}: {e}", "UNKNOWN")
        raw = b.details_raw(guid) or {}
        layer_name = read1(b, LAYER_REF, guid)
        if int(raw.get("layerIndex", -1)) != LAYER_INDEX or layer_name != LAYER_NAME:
            raise Stop("LAYER_READ_BACK",
                       f"layerIndex={raw.get('layerIndex')}, name={layer_name!r}", "UNKNOWN")
        stage("LAYER_READ_BACK", layer_index=LAYER_INDEX, layer_name=layer_name)

        original_id = read1(b, ID_REF, guid)
        marker = f"{PREFIX}{uuid.uuid4().hex}"
        setrec(cleanup={
            "guid": guid, "marker": marker, "restore_element_id_to": original_id,
            "manual_artifact_cleanup": "delete/undo wall after visual inspection",
        })
        stage("MARKER_INTENT", guid=guid, marker=marker,
              original_element_id=original_id, attempt=1)
        try:
            b.set_property_value(guid, ID_REF, marker)
        except Exception as e:
            raise Stop("MARKER_WRITE", f"{type(e).__name__}: {e}", "UNKNOWN")
        if read1(b, ID_REF, guid) != marker:
            raise Stop("MARKER_READ_BACK", "marker mismatch", "UNKNOWN")

        all_now = sorted(b.all_elements() or [])
        vals = b.get_property_values(ID_REF, all_now) or {}
        exact = sorted(g for g, v in vals.items() if v == marker)
        prefix = sorted(g for g, v in vals.items()
                        if isinstance(v, str) and v.startswith(PREFIX))
        if exact != [guid] or prefix != [guid]:
            raise Stop("MARKER_SEARCH", f"exact={exact}, prefix={prefix}", "UNKNOWN")
        stage("MARKER_ROUNDTRIP", exact=exact, prefix=prefix)

        after_counts = b.count_by_type()
        delta = {k: int(after_counts.get(k, 0)) - int(before_counts.get(k, 0))
                 for k in set(after_counts) | set(before_counts)}
        delta = {k: v for k, v in delta.items() if v}
        obs = observe(b, guid, stories)
        ex = obs["_extra"]
        checks = {
            "type": obs.get("type") == "Wall",
            "story": isinstance(obs.get("story"), dict)
                     and obs["story"].get("name") == STORY
                     and close(obs["story"].get("elevation"), ELEV, 1e-6),
            "layer": obs.get("layer") == LAYER_NAME,
            "ref_line": refline_ok(obs),
            "length": close(obs.get("length"), 5.0, 0.05),
            "height": close(obs.get("height"), HEIGHT),
            "thickness": close(obs.get("thickness"), THICK),
            "referenceLineLocation": ex.get("referenceLineLocation") == REFLINE,
            "offset": close(ex.get("offset"), OFFSET),
            "arcAngle": close(ex.get("arcAngle"), ARC),
            "count_delta": delta == {"Wall": 1},
            "marker_exact": exact == [guid],
            "marker_prefix": prefix == [guid],
        }
        wrong_height_rejected = not close(obs.get("height"), HEIGHT + 0.5)
        if not all(checks.values()) or not wrong_height_rejected:
            raise Stop("VERIFY",
                       f"checks={checks}, wrong_height_rejected={wrong_height_rejected}",
                       "UNKNOWN")
        stage("VERIFY", checks=checks, wrong_height_rejected=wrong_height_rejected,
              count_delta=delta, observation=obs)

        stage("RESTORE_MARKER_INTENT", restore_to=original_id, attempt=1)
        try:
            b.set_property_value(guid, ID_REF,
                                 original_id if original_id not in (None, "") else "")
        except Exception as e:
            raise Stop("RESTORE_MARKER", f"{type(e).__name__}: {e}", "UNKNOWN")
        restored = read1(b, ID_REF, guid)
        want = original_id if original_id not in (None, "") else None
        got = restored if restored not in (None, "") else None
        if got != want:
            raise Stop("VERIFY_MARKER_RESTORE",
                       f"expected={want!r}, got={restored!r}", "UNKNOWN")
        stage("VERIFY_MARKER_RESTORE", value=restored)

        left = scan_prefix(b, b.all_elements() or [], PREFIX)
        if left:
            raise Stop("FINAL_SWEEP", f"leftovers={left}", "UNKNOWN")
        stage("FINAL_SWEEP", markers=[])

        report = {
            "probe": "T2", "version": VER, "generated_at": now(),
            "archicad": info, "backend": "tapir", "adapter_version": addon,
            "artifact": rec["artifact"], "payload": p,
            "results": {
                "create_return_guid": returned[0],
                "independent_guid": guid,
                "count_delta": delta,
                "layer_roundtrip": True,
                "marker_roundtrip": True,
                "marker_restored": True,
                "checks": checks,
                "wrong_height_rejected": wrong_height_rejected,
            },
            "capabilities": {"create_wall": {
                "production_safe": False,
                "probe_certified": False,
                "machine_certified": True,
                "blocked_by": [
                    "manual_visual_check_pending",
                    "live_failure_injections_T3_T7_not_run"
                ]
            }},
            "verdicts": {
                "t2_machine_go": True,
                "manual_visual_check_required": True,
                "production_integration_ready": False,
            }
        }
        jwrite(a.report, report)
        setrec(status="MACHINE_OK_VISUAL_PENDING", cleanup=None,
               finished_at=now(), report=a.report)

        print("T2 MACHINE GO")
        print("created wall GUID :", guid)
        print("count delta       :", delta)
        print("layer round-trip  : OK")
        print("marker round-trip : OK + restored")
        print("negative control  : wrong height rejected")
        print("FINAL_SWEEP       : 0 T2 markers")
        print("MANUAL VISUAL CHECK REQUIRED")
        print("DO NOT delete/undo the wall yet.")
        print("receipt:", a.out)
        print("report :", a.report)
        return 0

    except Stop as s:
        setrec(status=s.status, stopped_at_stage=s.stage,
               reason=s.reason, stopped_at=now())
        print(f"STOP at {s.stage}: {s.reason}", file=sys.stderr)
        print("receipt:", a.out, file=sys.stderr)
        return 1
    except Exception as e:
        setrec(status="UNKNOWN", reason=f"{type(e).__name__}: {e}",
               stopped_at=now())
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
