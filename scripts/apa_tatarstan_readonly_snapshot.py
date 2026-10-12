#!/usr/bin/env python3
"""Read-only Archicad 29 snapshot of ONE explicitly pinned 'Tatarstan' PLN.

Reads live project identity, stories, entire element inventory, typed details and
3D bounding boxes. Requests native GetModelDumpV1 if installed and includes its
complete native geometry and materials in a local ZIP. Otherwise the ZIP clearly
states that geometry is typed/AABB-only. No user-supplied arbitrary target path,
native writes, model save, upload, GitHub push, or changes to other PLN files.

The native GetModelDumpV1 reader may regenerate the active 3D view; its current
visibility filters define the dump's coverage. This is not a claim that every
hidden element has a body.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import urllib.error
import urllib.request
import uuid
import zipfile

PORT_DEFAULT = 19724
EXPECTED_PATH = r"C:\институт проект\для теста из изоляции татарстан .pln"
EXPECTED_NAME = "для теста из изоляции татарстан"
EXPECTED_VERSION = "1.5.10"
READ_COMMANDS = frozenset({
    "GetProjectInfo", "GetAddOnVersion", "GetStories", "GetAllElements",
    "GetDetailsOfElements", "Get3DBoundingBoxes", "GetModelDumpV1",
})
GUID_PATTERN = __import__("re").compile(
    r"^[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}$"
)


def tapir(command: str, parameters: dict | None = None, *, port: int, timeout: int = 120):
    if command not in READ_COMMANDS:
        raise ValueError("WRITE_OR_UNKNOWN_COMMAND_REFUSED: " + command)
    message = {
        "command": "API.ExecuteAddOnCommand",
        "parameters": {
            "addOnCommandId": {
                "commandNamespace": "TapirCommand", "commandName": command,
            },
            "addOnCommandParameters": parameters if parameters is not None else {},
        },
    }
    payload = json.dumps(message, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}/", data=payload,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            envelope = json.load(response)
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(f"HOST_UNAVAILABLE_OR_TIMEOUT: {command}: {exc}") from exc
    if envelope.get("succeeded") is not True:
        raise RuntimeError(f"ARCHICAD_API_FAILURE: {command}: {envelope.get('error')}")
    result = envelope.get("result", {}).get("addOnCommandResponse")
    if not isinstance(result, dict) or "error" in result:
        raise RuntimeError(f"TAPIR_COMMAND_FAILURE: {command}: {result}")
    return result


def assert_project(api):
    info = api("GetProjectInfo", {})
    if (info.get("projectPath", "").casefold() != EXPECTED_PATH.casefold()
            or info.get("projectName", "").rstrip(" ") != EXPECTED_NAME
            or info.get("isUntitled") is not False
            or info.get("isTeamwork") is not False):
        raise RuntimeError(
            "WRONG_PROJECT_ABORTED: expected exact saved Tatarstan PLN, got "
            + repr({"path": info.get("projectPath"), "name": info.get("projectName")})
        )
    return info


def inventory(api):
    response = api("GetAllElements", {})
    rows = response.get("elements")
    if not isinstance(rows, list):
        raise RuntimeError("INVENTORY_NOT_A_LIST: " + repr(response))
    identifiers = []
    for row in rows:
        guid = (row.get("elementId") or {}).get("guid") if isinstance(row, dict) else None
        if not isinstance(guid, str) or not GUID_PATTERN.fullmatch(guid):
            raise RuntimeError("INVALID_INVENTORY_ELEMENT: " + repr(row)[:300])
        identifiers.append(guid.lower())
    if len(identifiers) != len(set(identifiers)):
        raise RuntimeError("DUPLICATE_BIM_GUID_IN_INVENTORY")
    return sorted(identifiers)


def read_typed_elements(api, ids):
    """Keep provider rows verbatim, including per-element errors and unsupported types."""
    details = []
    bounding_boxes = []
    for start in range(0, len(ids), 32):
        batch = ids[start:start + 32]
        elements = [{"elementId": {"guid": guid}} for guid in batch]
        detail_data = api("GetDetailsOfElements", {
            "elements": elements,
            "fields": ["type", "id", "floorIndex", "layerIndex", "drawIndex",
                       "details", "hotlinkId"],
        })
        detail_rows = detail_data.get("detailsOfElements")
        if not isinstance(detail_rows, list) or len(detail_rows) != len(batch):
            raise RuntimeError("DETAILS_ORDER_OR_COUNT_UNVERIFIED")
        bbox_data = api("Get3DBoundingBoxes", {"elements": elements})
        bbox_rows = bbox_data.get("boundingBoxes3D")
        if not isinstance(bbox_rows, list) or len(bbox_rows) != len(batch):
            raise RuntimeError("BBOX_ORDER_OR_COUNT_UNVERIFIED")
        for guid, detail, bbox in zip(batch, detail_rows, bbox_rows):
            details.append({"guid": guid, "provider": detail})
            bounding_boxes.append({"guid": guid, "provider": bbox})
    return details, bounding_boxes


def collect(api):
    start = assert_project(api)
    version = api("GetAddOnVersion", {}).get("version")
    if version != EXPECTED_VERSION:
        raise RuntimeError(f"TAPIR_VERSION_MISMATCH: {version}")
    stories = api("GetStories", {})
    known_stories = stories.get("stories")
    if not isinstance(known_stories, list):
        raise RuntimeError("STORIES_NOT_VERIFIED")
    for index, level in [(0, 0.0), (1, 3.0), (2, 6.0)]:
        if sum(
            row.get("index") == index and
            isinstance(row.get("level"), (int, float)) and
            abs(row["level"] - level) < 1e-4
            for row in known_stories if isinstance(row, dict)
        ) != 1:
            raise RuntimeError(f"STORY_INDEX_OR_LEVEL_MISMATCH: {index}")

    baseline = inventory(api)
    details, boxes = read_typed_elements(api, baseline)
    assert_project(api)

    native_dump = None
    native_status = "NOT_AVAILABLE"
    native_error = None
    try:
        candidate = api("GetModelDumpV1", {}, timeout=600)
        if not isinstance(candidate.get("elements"), list) or not isinstance(
                candidate.get("bodies"), list) or not isinstance(
                candidate.get("materials"), list):
            raise RuntimeError("NATIVE_DUMP_SHAPE_UNVERIFIED")
        native_dump = candidate
        native_status = "NATIVE_GEOMETRY_RETURNED"
    except (RuntimeError, KeyError, TypeError, ValueError) as exc:
        native_error = str(exc)[:2000]
        native_status = "UNAVAILABLE_TYPED_AND_AABB_FALLBACK"

    end = assert_project(api)
    after = inventory(api)
    if after != baseline or end != start:
        raise RuntimeError("MODEL_OR_PROJECT_DRIFT_DURING_READ; NO_SNAPSHOT_ACCEPTED")

    typed_counts = dict(Counter(
        (row["provider"].get("type") or "UNRESOLVED")
        if isinstance(row["provider"], dict) else "UNRESOLVED"
        for row in details
    ))
    bboxes_ok = sum(isinstance(row["provider"], dict) and
                    isinstance(row["provider"].get("boundingBox3D"), dict)
                    for row in boxes)
    snapshot = {
        "schema": "APA_TATARSTAN_READONLY_SNAPSHOT_V1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "project": start,
        "tapir_version": version,
        "stories": stories,
        "inventory_guids": baseline,
        "inventory_count": len(baseline),
        "typed_element_counts": typed_counts,
        "typed_readback": details,
        "bounding_boxes_3d": boxes,
        "bounding_boxes_available": bboxes_ok,
        "native_status": native_status,
        "native_error": native_error,
        "geometry_coverage": (
            "NATIVE_BODIES_SUBJECT_TO_ACTIVE_3D_VIEW_FILTERS"
            if native_dump is not None else
            "TYPED_DETAILS_AND_AXIS_ALIGNED_BOUNDS_ONLY; FULL_MESH_NOT_VERIFIED"
        ),
        "original_pln_modified_by_this_script": False,
        "sent_model_write_commands": 0,
        "upload_to_github": False,
        "saved_pln": False,
        "new_house_10x12_status": "NOT_INFERRED_FROM_PLAN; INSPECT_ACTUAL_ELEMENTS",
    }
    return snapshot, native_dump


def write_archive(snapshot, native_dump, target_dir: Path):
    target_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    name = f"APA_TATARSTAN_{stamp}_{uuid.uuid4().hex[:8]}.zip"
    dest = target_dir / name
    temporary = target_dir / (name + ".partial")
    def payload(obj):
        return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    try:
        with zipfile.ZipFile(temporary, "x", compression=zipfile.ZIP_DEFLATED,
                             compresslevel=6, allowZip64=True) as archive:
            archive.writestr("snapshot.json", payload(snapshot))
            if native_dump is not None:
                archive.writestr("native-model.json", payload(native_dump))
            archive.writestr("README.txt",
                "Read-only Archicad model snapshot, not an installer or a design approval.\n"
                "No model write/save/commit was issued. "
                "Share only with an intended recipient; BIM may contain private data.\n")
        with zipfile.ZipFile(temporary) as verified:
            if verified.testzip() is not None:
                raise RuntimeError("ZIP_CRC_VERIFICATION_FAILED")
            if "snapshot.json" not in verified.namelist():
                raise RuntimeError("ZIP_SNAPSHOT_MISSING")
        if dest.exists():
            raise FileExistsError(str(dest))
        os.replace(temporary, dest)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return dest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=PORT_DEFAULT)
    parser.add_argument("--output-dir", type=Path,
                        default=Path.home() / "Desktop" / "APA_Tatarstan_Snapshots")
    args = parser.parse_args(argv)
    if not 1 <= args.port <= 65535:
        parser.error("Invalid API port")
    def api(name, data=None, timeout=120):
        return tapir(name, data, port=args.port, timeout=timeout)
    snapshot, native_dump = collect(api)
    path = write_archive(snapshot, native_dump, args.output_dir)
    print("PROJECT VERIFIED:", snapshot["project"]["projectPath"])
    print("INVENTORY GUIDS:", snapshot["inventory_count"])
    print("TYPED ELEMENTS:", snapshot["typed_element_counts"])
    print("3D BOUNDS:", snapshot["bounding_boxes_available"])
    print("MODEL DUMP:", snapshot["native_status"])
    if snapshot["native_error"]:
        print("MODEL DUMP LIMIT:", snapshot["native_error"])
    print("SAVED SNAPSHOT ZIP:", path)
    print("MODEL WRITES: 0; PLN SAVE: 0; GITHUB UPLOAD: 0")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print("READONLY_SNAPSHOT_FAILED:", exc, file=sys.stderr)
        sys.exit(1)
