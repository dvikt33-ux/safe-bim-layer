"""APA AC29 isolated test-house bulk benchmark, one opt-in 100->200->1000 run.

One disposable PLN, one SOURCE Column, six native MoveElements(copy=true)
batches of 100, 100, 200, 200, 200, 200. Each batch goes via the existing
DynamicCommands -> SceneWriter durable journal, never through a new writer.
Stop on uncertain result; no retry, delete, SaveProject, or BDD contact.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sqlite3
import sys
import time

ROOT = Path(r"C:\LocalAI\APA_AC29_Stable")
sys.path.insert(0, str(ROOT / "scripts"))
import archicad_project_accelerator as APA
import archicad_scene_run as RUN
import archicad_bim_documentation as DOC
import archicad_connected_components as CONNECTED

TARGET = Path(r"C:\LocalAI\APA_Functional_Test_House_01.pln")
LEDGER = Path(r"C:\LocalAI\APA_Functional_Test_House_01_ledger\scene-v1-attempts.sqlite3")
OUT = Path(r"C:\LocalAI\APA_Functional_Test_House_01_bulk1000_20261018")
SCHEMA = ROOT / "schemas/tapir-live-1.5.10/tapir-scene-live.json"
PORT = 19726
PROTOTYPE = "a457ec9e-e034-4abe-af5c-a7d2ecb689dc"
ORIGINAL_SCENE = "apa_functional_house_01_first_build"
SUFFIX_SCENE = "apa_functional_house_01_verified_suffix_20261017"
REPAIR_TABLE = "apa_functional_house_slab_repair_v1"
EXPECTED_ROOTS = (
    "8bcc2a69-43d7-472a-ba2b-97bd9599d25e",
    "462bc642-a5fa-431f-b728-f5a25ecbfa64",
    "cf1853a5-d3cf-40d5-9e06-00bed7219e6e",
    "293d0f57-7b5f-488c-bbd9-9216b318cbc5",
    "2a50acd3-1eb9-4cd9-a584-e96a2f3343f7",
    "a457ec9e-e034-4abe-af5c-a7d2ecb689dc",
    "c7e72514-3c33-4cb2-8cc2-310d59430437",
    "d595303f-e259-4ce5-a1d6-fef52a9ae23e",
    "8513e799-460a-4830-88d1-7197a30893e4",
    "3d1a324c-c339-4e6c-8133-67b9da02f597",
    "48dc9ed3-af9a-40f0-bbdb-812b761d82e1",
    "9918ac62-5a25-47f9-bec2-46b16d2718cf",
)
CHUNKS = (100, 100, 200, 200, 200, 200)
STAGE_TOTALS = (100, 200, 1000)
AUTHORIZATION = "2026-10-18 USER_APPROVED_ALL_100_200_1000_BULK_IN_ONE_PACKAGE"


def require(value, message):
    if not value:
        raise ValueError(message)


def digest_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name, data):
    p = OUT / name
    require(not p.exists(), "EVIDENCE_OVERWRITE_DENIED: " + str(p))
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def close(a, b, eps=1.e-5):
    return isinstance(a, (int, float)) and math.isfinite(a) and abs(a - b) <= eps


def inventory(api):
    response = api("GetAllElements", {})
    rows = response.get("elements")
    require(isinstance(rows, list), "NATIVE_GUID_INVENTORY_MISSING")
    result = {}
    for row in rows:
        guid = (row.get("elementId") or {}).get("guid")
        require(isinstance(guid, str) and RUN._GUID.fullmatch(guid)
                and guid.lower() not in result, "INVALID_OR_DUPLICATED_NATIVE_GUID")
        result[guid.lower()] = row
    return result


def typed_details(api, guids):
    result = {}
    for start in range(0, len(guids), 80):
        chunk = guids[start:start + 80]
        response = api("GetDetailsOfElements", {
            "elements": [{"elementId": {"guid": guid}} for guid in chunk]
        })
        rows = response.get("detailsOfElements")
        require(isinstance(rows, list) and len(rows) == len(chunk),
                "NATIVE_DETAILS_COUNT_MISMATCH")
        for guid, row in zip(chunk, rows):
            require(isinstance(row, dict) and "error" not in row
                    and (row.get("elementId") or {}).get("guid", guid).lower() == guid.lower(),
                    "NATIVE_DETAIL_GUID_OR_ERROR")
            result[guid.lower()] = row
    return result


def hierarchy(api, parent_guids):
    mapping = {}
    # Reuse existing native hierarchy validation rather than inferring ownership
    # from inventory order or element type.
    for begin in range(0, len(parent_guids), 80):
        chunk = parent_guids[begin:begin + 80]
        owned = APA.column_subelements(
            api, {"column_" + str(j): {"guid": guid, "kind": "Column"}
                  for j, guid in enumerate(chunk)}
        )
        require(set(owned) == set(chunk), "HIERARCHY_PARENT_SET_MISMATCH")
        mapping.update(owned)
    require(len(mapping) == len(parent_guids), "HIERARCHY_INCOMPLETE")
    return mapping


def native_box(element):
    vertices = [vertex for body in element.get("bodies", [])
                for vertex in body.get("vertices", [])]
    return ([(min(v[i] for v in vertices), max(v[i] for v in vertices))
             for i in range(3)] if vertices else None)


def preview_targets():
    # One reserved remote test yard; 2 m pitch, no touching the small house.
    points = [(round(400.35 + 2.0 * ix, 6),
               round(400.35 + 2.0 * iy, 6))
              for ix in range(20) for iy in range(50)]
    require(len(points) == len(set(points)) == 1000, "TARGET_GRID_NOT_1000")
    require(all(399 < x < 440 and 399 < y < 500 for x, y in points),
            "TARGET_GRID_OUTSIDE_TEST_YARD")
    return points


def validate_saved_scene(api, saved_sha):
    require(TARGET.is_file() and SCHEMA.is_file() and LEDGER.is_file(),
            "TEST_PLN_OR_INSTALLED_SCHEMA_OR_LEDGER_MISSING")
    require(digest_file(TARGET) == saved_sha, "TARGET_PLN_BYTES_CHANGED")
    project = api("GetProjectInfo", {})
    require(project.get("projectPath") == str(TARGET)
            and project.get("projectName") == TARGET.stem
            and project.get("isUntitled") is False
            and project.get("isTeamwork") is False, "WRONG_ARCHICAD_INSTANCE")
    product = APA.archicad29(api)
    require(product.get("version") == 29, "ARCHICAD_29_REQUIRED")
    with sqlite3.connect("file:" + LEDGER.as_posix() + "?mode=ro", uri=True) as db:
        first = db.execute("SELECT state FROM scenes WHERE scene_id=?",
                           (ORIGINAL_SCENE,)).fetchone()
        second = db.execute("SELECT state,result FROM scenes WHERE scene_id=?",
                            (SUFFIX_SCENE,)).fetchone()
        repaired = db.execute("SELECT state FROM " + REPAIR_TABLE
                              + " WHERE scene_id=?", (ORIGINAL_SCENE,)).fetchone()
        written = db.execute("SELECT COUNT(*) FROM steps WHERE scene_id=?"
                             " AND state='PASS'", (SUFFIX_SCENE,)).fetchone()[0]
        for i in range(len(CHUNKS)):
            sid = "apa-house-bulk1000-20261018-batch-%02d" % (i + 1)
            require(db.execute("SELECT 1 FROM scenes WHERE scene_id=?",
                               (sid,)).fetchone() is None,
                    "BATCH_SCENE_ALREADY_RESERVED: " + sid)
    require(first == ("PARTIAL_OR_UNKNOWN_OUTCOME",)
            and second is not None and second[0] == "PARTIAL_OR_UNKNOWN_OUTCOME"
            and json.loads(second[1]).get("failedStep") == "FINAL_READBACK"
            and repaired == ("READBACK_PASS",) and written == 7,
            "ORIGINAL_SCENE_AND_RECOVERY_NOT_VERIFIED")
    initial = inventory(api)
    require(len(initial) == 36 and set(EXPECTED_ROOTS) <= set(initial),
            "TEST_HOUSE_36_NATIVE_GUID_BASELINE_DRIFT")
    ownership = hierarchy(api, [
        "a457ec9e-e034-4abe-af5c-a7d2ecb689dc",
        "c7e72514-3c33-4cb2-8cc2-310d59430437",
        "d595303f-e259-4ce5-a1d6-fef52a9ae23e",
        "8513e799-460a-4830-88d1-7197a30893e4"
    ])
    descendants = {child for children in ownership.values() for child in children}
    require(len(descendants) == 4 and all(len(children) == 1
                                         for children in ownership.values())
            and descendants <= set(initial), "EXISTING_COLUMN_SEGMENT_OWNERSHIP_DRIFT")
    source = typed_details(api, [PROTOTYPE])[PROTOTYPE]
    fields = source.get("details") or {}
    origin = fields.get("origin") or {}
    require(source.get("type") == "Column" and source.get("floorIndex") == 0
            and close(origin.get("x"), 300.35)
            and close(origin.get("y"), 300.35)
            and close(fields.get("height"), 3.0)
            and close(fields.get("width"), .25)
            and close(fields.get("depth"), .25),
            "PINNED_250X250X3000_SOURCE_COLUMN_DRIFT")
    return initial, source, ownership[PROTOTYPE][0]


def source_fingerprint(api, source, original_segment_guid, native):
    members = {e["guid"].lower(): e for e in native["elements"]}
    require(PROTOTYPE in members and original_segment_guid in members,
            "SOURCE_BREP_INCOMPLETE")
    root, child = members[PROTOTYPE], members[original_segment_guid]
    require(child["type"] == "ColumnSegment"
            and child.get("relationships", {}).get("hostGuid", "").lower()
                == PROTOTYPE, "SOURCE_SEGMENT_PARENT_RELATION_INVALID")
    bounds = native_box(child)
    require(bounds is not None, "SOURCE_CHILD_BREP_EMPTY")
    require(all(close(bounds[i][1] - bounds[i][0], extent)
                for i, extent in enumerate((.25, .25, 3.0))),
            "SOURCE_PHYSICAL_BREP_DIMENSIONS_DRIFT")
    return RUN.digest({
        "root": CONNECTED.ROOF.geometry_signature(root),
        "child": CONNECTED.ROOF.geometry_signature(child),
        "details": source,
    }), bounds


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true",
                        help="One irreversible set of six native copy batches; no retry")
    args = parser.parse_args()
    require(args.apply, "EXPLICIT_APPLY_REQUIRED")

    # No new benchmark run can reuse an ambiguous previous result directory.
    require(not OUT.exists(), "BENCHMARK_DIRECTORY_ALREADY_EXISTS_DO_NOT_RETRY")
    require(TARGET.is_file(), "EXACT_TEST_PLN_NOT_FOUND")
    saved_sha = digest_file(TARGET)
    RUN.bind_authorized_saved_copy(PORT, str(TARGET), TARGET.stem,
                                   saved_sha, AUTHORIZATION)

    OUT.mkdir(parents=True, exist_ok=False)
    (OUT / "native").mkdir()
    started = time.perf_counter()
    stats = {"calls": 0, "times": []}

    def measured(command, params):
        if command in APA.NATIVE_MUTATIONS:
            require(command == "MoveElements",
                    "UNAUTHORIZED_NATIVE_MUTATION: " + command)
            moves = params.get("elementsWithMoveVectors")
            require(isinstance(moves, list) and 1 <= len(moves) <= 200
                    and all(row.get("copy") is True
                            and (row.get("elementId") or {}).get("guid", "").lower()
                            == PROTOTYPE for row in moves),
                    "ONLY_APPROVED_COLUMN_COPY_BATCH_PERMITTED")
            stats["calls"] += 1
            begin = time.perf_counter()
            try:
                # Use the exact established Tapir transport with a longer
                # timeout for large native batch requests. No fallback/retry.
                return RUN.tapir(PORT, command, params, timeout=120)
            finally:
                stats["times"].append(round(time.perf_counter() - begin, 6))
        if command.startswith("API."):
            return APA.native_transport(command, params)
        return RUN.tapir(PORT, command, params, timeout=120)

    api = APA.EvidenceAPI(measured, OUT / "native", execute=True)
    router = APA.native_command_router(SCHEMA, include_functional_modules=False)
    router.review_policy("MoveElements", "CREATE", "MODEL", {
        "source": "Installed Tapir 1.5.10 MoveElements(copy=true); user-approved isolated functional-house 100-to-1000 copy benchmark",
        "sha256": router.contract_hash("MoveElements"),
    })
    writer = RUN.SceneWriter(api, LEDGER, SCHEMA,
                             allow_3d_view_for_write=True)
    original, source, source_segment = validate_saved_scene(api, saved_sha)
    points = preview_targets()
    known = dict(original)
    old = DOC.capture_full_model(api, sorted(known))
    model = {e["guid"].lower(): e for e in old["elements"]}
    fingerprint, source_bounds = source_fingerprint(
        api, source, source_segment, old)
    require(set(known) <= set(model), "INITIAL_NATIVE_BREP_NOT_COMPLETE")
    yard = ((399.0, 440.0), (399.0, 500.0), (-.2, 3.3))
    for guid, element in model.items():
        box = native_box(element)
        if box and all(box[i][0] < yard[i][1]
                       and yard[i][0] < box[i][1] for i in range(3)):
            raise ValueError("TEST_YARD_COLLIDES_WITH_EXISTING_ELEMENT: " + guid)
    require(writer.guarded_binding()["path"] == str(TARGET),
            "WRITER_NOT_PINNED_TO_FUNCTIONAL_TEST_PLN")
    result = {
        "status": "PREFLIGHT_PASS",
        "target": str(TARGET),
        "port": PORT,
        "baselineSavedSHA256": saved_sha,
        "initialGuids": len(original),
        "initialHouseRoots": 12,
        "prototypeGuid": PROTOTYPE,
        "prototypeSegmentGuid": source_segment,
        "prototypeBrepDigest": fingerprint,
        "targets": {"total": 1000, "grid": "20x50",
                    "pitchMeters": 2.0, "first": points[0], "last": points[-1]},
        "stages": [100, 200, 1000],
        "nativeBatchSizes": list(CHUNKS),
        "nativeWrites": 0,
        "plnSaved": False,
    }
    write("preflight.json", result)
    print("PREFLIGHT: PASS | 36 GUID | 1000 disjoint target positions | PORT 19726",
          flush=True)
    (OUT / "ATTEMPTED.no-replay").write_text(
        datetime.now(timezone.utc).isoformat(), encoding="ascii")

    batches = []
    stage_done = []
    cumulative = 0
    stage_begin = time.perf_counter()
    end_to_end = {}

    for batch_index, size in enumerate(CHUNKS):
        batch_num = batch_index + 1
        sid = "apa-house-bulk1000-20261018-batch-%02d" % batch_num
        targets = points[cumulative:cumulative + size]
        expect = {(round(x, 5), round(y, 5)) for x, y in targets}
        before = dict(known)
        raw_before = DOC.capture_full_model(api, sorted(before))
        retained = sorted(set(before) - {PROTOTYPE})
        signatures = CONNECTED.retained_geometry_signatures(raw_before, retained)
        require(set(signatures) == set(retained),
                "RETAINED_NATIVE_SIGNATURES_INCOMPLETE")
        vectors = [{"x": round(x - 300.35, 6),
                    "y": round(y - 300.35, 6), "z": 0.}
                   for x, y in targets]
        ticket = router.prepare("MoveElements", {
            "elementsWithMoveVectors": [
                {"elementId": {"guid": PROTOTYPE},
                 "moveVector": vector, "copy": True}
                for vector in vectors
            ]
        })
        require(ticket["effect"] == "CREATE", "NATIVE_COPY_POLICY_NOT_CREATE")
        write("batch-%02d-intent.json" % batch_num, {
            "status": "PREPARED",
            "sceneId": sid,
            "sourceGuid": PROTOTYPE,
            "size": size,
            "beforeGUIDCount": len(before),
            "planHash": ticket["hash"],
            "targetFirst": targets[0], "targetLast": targets[-1],
        })

        def before_check(working_api):
            require(inventory(working_api).keys() == before.keys(),
                    "MODEL_DRIFT_BEFORE_NATIVE_COPY")
            d = typed_details(working_api, [PROTOTYPE])[PROTOTYPE]
            require(d == source, "SOURCE_COLUMN_DETAIL_DRIFT")
            return {"status": "SOURCE_AND_BASELINE_PASS"}

        def after_check(reply, _):
            now = inventory(api)
            require(set(before) <= set(now),
                    "PREVIOUS_NATIVE_GUID_DISAPPEARED")
            added = sorted(set(now) - set(before))
            require(len(added) == 2 * size,
                    "COPY_NATIVE_GUID_DELTA_NOT_ROOT_PLUS_SEGMENT")
            new_details = typed_details(api, added)
            parents = sorted(g for g in added
                             if new_details[g].get("type") == "Column")
            children = sorted(g for g in added
                              if new_details[g].get("type") == "ColumnSegment")
            require(len(parents) == len(children) == size,
                    "NEW_COLUMN_PARENT_CHILD_TYPE_CARDINALITY")
            owned = hierarchy(api, parents)
            linked = sorted(g for arr in owned.values() for g in arr)
            require(linked == children and all(len(x) == 1
                                                for x in owned.values()),
                    "NATIVE_PARENT_CHILD_OWNERSHIP_NOT_EXACT")
            positions = {}
            for guid in parents:
                row = new_details[guid]
                d = row.get("details") or {}
                o = d.get("origin") or {}
                require(row.get("floorIndex") == 0
                        and close(d.get("width"), .25)
                        and close(d.get("depth"), .25)
                        and close(d.get("height"), 3.0),
                        "COPY_PARENT_SHAPE_OR_STORY_DRIFT")
                key = (round(o.get("x"), 5), round(o.get("y"), 5))
                require(key not in positions and key in expect,
                        "COPY_PARENT_TARGET_POSITION_MISMATCH")
                positions[key] = guid
            require(set(positions) == expect, "NOT_ALL_NATIVE_COPY_TARGETS_HIT")
            native = DOC.capture_full_model(api, sorted(now))
            elements = {e["guid"].lower(): e for e in native["elements"]}
            source_after, _ = source_fingerprint(
                api, typed_details(api, [PROTOTYPE])[PROTOTYPE],
                source_segment, native)
            require(source_after == fingerprint,
                    "SOURCE_ROOT_OR_SEGMENT_BREP_CHANGED")
            for xy, parent in positions.items():
                child = owned[parent][0]
                seg = elements.get(child)
                require(seg is not None and seg["type"] == "ColumnSegment"
                        and seg.get("relationships", {}).get("hostGuid", "").lower()
                            == parent, "COLUMN_SEGMENT_PHYSICAL_OWNER_MISMATCH")
                box = native_box(seg)
                require(box is not None, "NEW_SEGMENT_BREP_MISSING")
                for axis in range(3):
                    expected_min = source_bounds[axis][0] + (
                        (xy[axis] - 300.35) if axis < 2 else 0.0)
                    expected_max = source_bounds[axis][1] + (
                        (xy[axis] - 300.35) if axis < 2 else 0.0)
                    require(close(box[axis][0], expected_min)
                            and close(box[axis][1], expected_max),
                            "NEW_SEGMENT_NATIVE_BREP_TRANSLATION_MISMATCH")
            require(digest_file(TARGET) == saved_sha,
                    "SAVED_PLN_CHANGED_DURING_NATIVE_COPY")
            return {"status": "BULK_COLUMNS_SEGMENTS_BREP_PASS",
                    "newPhysicalCopyCount": size,
                    "prototypeGuidUnchanged": True,
                    "newColumnGuids": parents,
                    "newSegmentGuids": children,
                    "newNativeGuidCount": len(added),
                    "afterNativeGUIDCount": len(now)}

        started_batch = time.perf_counter()
        response = router.copy_existing_many(
            writer, sid, PROTOTYPE, "Column", vectors, signatures,
            saved_sha, AUTHORIZATION, before_check, after_check)
        elapsed = round(time.perf_counter() - started_batch, 4)
        status = response.get("status")
        proof = response.get("readback") or {}
        batch_report = {
            "batch": batch_num, "sceneId": sid,
            "status": status,
            "newCopiesRequested": size,
            "nativeCallElapsedSeconds": stats["times"][-1] if stats["times"] else None,
            "endToEndSeconds": elapsed,
            "newColumnsVerified": len(proof.get("newColumnGuids", [])),
            "newSegmentsVerified": len(proof.get("newSegmentGuids", [])),
            "nativeCopyMetrics": response.get("nativeCopyMetrics"),
        }
        write("batch-%02d-result.json" % batch_num, batch_report)
        print("BATCH %d/%d: %s | +%d columns | %.3f s end-to-end" %
              (batch_num, len(CHUNKS), status, size, elapsed), flush=True)
        require(status == "PASS", "BATCH_PARTIAL_OR_UNKNOWN_NO_RETRY")
        require(len(proof["newColumnGuids"]) == size
                and len(proof["newSegmentGuids"]) == size,
                "BATCH_RECEIPT_INCOMPLETE")
        known = inventory(api)
        require(len(known) == len(before) + 2 * size,
                "POST_NATIVE_BATCH_GUID_COUNT_DRIFT")
        batches.append(batch_report)
        cumulative += size

        if cumulative in STAGE_TOTALS:
            stage = {"totalNewColumns": cumulative,
                     "newColumnSegments": cumulative,
                     "nativeBatches": len(batches),
                     "stageElapsedSeconds": round(time.perf_counter() - stage_begin, 3),
                     "nativeMoveCalls": stats["calls"],
                     "totalModelGUIDs": len(known)}
            write("milestone-%04d.json" % cumulative, stage)
            stage_done.append(stage)
            print("MILESTONE %d/1000: PASS | native GUIDs=%d" %
                  (cumulative, len(known)), flush=True)
            stage_begin = time.perf_counter()

    require(cumulative == 1000 and stats["calls"] == 6
            and len(known) == 2036, "FINAL_1000_PARENT_1000_CHILD_NOT_CONFIRMED")
    require(set(original) <= set(known)
            and digest_file(TARGET) == saved_sha,
            "FINAL_ORIGINAL_ELEMENTS_OR_SAVED_PLN_DRIFT")
    report = {
        "status": "NATIVE_BULK_100_200_1000_ALL_PASS",
        "port": PORT, "plnPath": str(TARGET),
        "newColumnRoots": 1000, "newColumnSegments": 1000,
        "finalNativeGuidCount": len(known), "baselineNativeGuidCount": len(original),
        "nativeMoveCalls": stats["calls"],
        "nativeMoveTransportSeconds": stats["times"],
        "perBatchResults": batches, "milestones": stage_done,
        "totalSeconds": round(time.perf_counter() - started, 3),
        "savedPLNUnchanged": True, "plnSaved": False,
        "automaticRetry": False,
        "journal": str(LEDGER),
    }
    write("RESULT.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)
    print("APA NATIVE BULK: 100 -> 200 -> 1000 ALL VERIFIED, UNSAVED",
          flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        try:
            if OUT.exists():
                path = OUT / "STOPPED_NO_RETRY.json"
                if not path.exists():
                    path.write_text(json.dumps({
                        "status": "UNKNOWN_OR_BLOCKED_STOP_NO_RETRY",
                        "reason": type(exc).__name__ + ": " + str(exc),
                        "nativeWritesMayHaveOccurred": (OUT / "ATTEMPTED.no-replay").exists(),
                    }, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass
        print("APA BULK STOPPED (DO NOT RESTART): " + type(exc).__name__
              + ": " + str(exc), file=sys.stderr, flush=True)
        raise SystemExit(2)
