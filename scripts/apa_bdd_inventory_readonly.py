#!/usr/bin/env python3
"""Read-only BDD house inventory from the exact Archicad 29 PLN.

Only calls these Tapir read commands: GetProjectInfo, GetAddOnVersion,
GetStories, GetAllElements, GetDetailsOfElements, Get3DBoundingBoxes.
No edits, project switching, selection changes, saving or BIM mutation.

Local output: %TEMP%/APA_BDD_Readonly/
Optional --publish: a NEW immutable result JSON in private safe-bim-bridge
mailbox results, using the user's existing GitHub CLI authentication.
"""
from __future__ import annotations

import argparse
import base64
from collections import Counter
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import urllib.request
import uuid

EXPECTED_PATH = "C:\\LocalAI\\SafeBIM_Global_Library_Test_Projects\\BDD \u0434\u043e\u043c .pln"
EXPECTED_NAME = "BDD \u0434\u043e\u043c "
ALLOWED = frozenset({
    "GetProjectInfo", "GetAddOnVersion", "GetStories", "GetAllElements",
    "GetDetailsOfElements", "Get3DBoundingBoxes",
})
GEOMETRY_FIELDS = (
    "begCoordinate", "endCoordinate", "zCoordinate", "height", "thickness",
    "begThickness", "endThickness", "bottomOffset", "topOffset", "offset",
    "level", "levels", "polygonCoordinates", "polygonOutline",
    "pivotPolygonOutline", "roofClass", "geometryType", "structureType",
    "referenceLineLocation", "arcAngle", "sillHeight", "openingWidth",
    "openingHeight", "width", "length", "radius", "eavesOverhang",
    "slantAlpha", "slantBeta", "position", "floorIndex",
)


def tapir(port: int, command: str, params: dict | None = None) -> dict:
    if command not in ALLOWED:
        raise ValueError("READ-ONLY FENCE: " + command)
    request = {
        "command": "API.ExecuteAddOnCommand",
        "parameters": {
            "addOnCommandId": {
                "commandNamespace": "TapirCommand", "commandName": command
            },
            "addOnCommandParameters": params or {},
        },
    }
    body = json.dumps(request, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        "http://127.0.0.1:%d" % port, body,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as response:
        envelope = json.load(response)
    if envelope.get("succeeded") is not True:
        raise RuntimeError("%s transport failure: %s" % (
            command, str(envelope.get("error", "unknown"))[:250]))
    result = envelope.get("result", {}).get("addOnCommandResponse", {})
    if not isinstance(result, dict) or result.get("error") is not None:
        raise RuntimeError("%s returned an error" % command)
    return result


def require_target(port: int) -> dict:
    p = tapir(port, "GetProjectInfo")
    actual_path = p.get("projectPath") or p.get("projectLocation") or ""
    if (
        actual_path.casefold() != EXPECTED_PATH.casefold()
        or p.get("projectName") != EXPECTED_NAME
        or p.get("isUntitled")
        or p.get("isTeamwork")
    ):
        raise RuntimeError(
            "WRONG PLN on port %d; actual=%r. No snapshot or upload." %
            (port, actual_path))
    return p


def guid_of(row: dict) -> str | None:
    if not isinstance(row, dict):
        return None
    e = row.get("elementId", {})
    if isinstance(e, dict):
        return e.get("guid") or row.get("guid")
    return row.get("guid")


def read_batch(port: int, command: str, guids: list[str], key: str):
    data = {"elements": [{"elementId": {"guid": g}} for g in guids]}
    try:
        result = tapir(port, command, data)
        values = result.get(key)
        if not isinstance(values, list) or len(values) != len(guids):
            raise ValueError("response length or shape mismatch")
        return values, []
    except Exception as exc:
        errors = [{"command": command, "count": len(guids),
                   "error": type(exc).__name__ + ": " + str(exc)[:180]}]
        # Recheck one by one so one unsupported element does not lose all
        # available evidence. Every call remains read-only.
        values = []
        for g in guids:
            try:
                items = tapir(port, command, {
                    "elements": [{"elementId": {"guid": g}}]
                }).get(key, [])
                values.append(items[0] if isinstance(items, list) and len(items) == 1 else None)
            except Exception:
                values.append(None)
        return values, errors


def raw_box(value):
    if not isinstance(value, dict):
        return None
    return value.get("boundingBox3D") if "boundingBox3D" in value else value


def element_info(guid: str, detail, bbox):
    d = detail if isinstance(detail, dict) else {}
    meta = d.get("metadata") if isinstance(d.get("metadata"), dict) else {}
    params = d.get("details") if isinstance(d.get("details"), dict) else {}
    geometry = {k: params[k] for k in GEOMETRY_FIELDS if k in params}
    return {
        "guid": guid,
        "type": d.get("type") or meta.get("type") or "UNKNOWN",
        "elementId": d.get("id") or meta.get("id"),
        "floorIndex": d.get("floorIndex", meta.get("floorIndex")),
        "layerIndex": d.get("layerIndex", meta.get("layerIndex")),
        "boundingBox3D": raw_box(bbox),
        "geometry": geometry,
        "detailsPresent": detail is not None,
        "bboxPresent": bbox is not None,
    }


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def publish_to_private_mailbox(report: Path, now: str) -> str:
    destination = (
        "safe-bim-mailbox/gpt-live/results/"
        "apa-bdd-inventory-%s-%s.json" % (now, uuid.uuid4().hex[:8]))
    contents = base64.b64encode(report.read_bytes()).decode("ascii")
    payload = {
        "message": "Read-only Archicad 29 BDD house inventory",
        "branch": "main",
        "content": contents,
    }
    body_path = report.with_suffix(".github-payload.tmp.json")
    try:
        write_json(body_path, payload)
        call = subprocess.run(
            ["gh", "api", "--method", "PUT",
             "repos/dvikt33-ux/safe-bim-bridge/contents/" + destination,
             "--input", str(body_path)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            timeout=180, check=False,
        )
        if call.returncode:
            raise RuntimeError("GitHub upload failed: " + call.stderr[-700:])
    finally:
        body_path.unlink(missing_ok=True)
    return "https://github.com/dvikt33-ux/safe-bim-bridge/blob/main/" + destination


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--port", type=int, default=19727)
    ap.add_argument("--publish", action="store_true",
                    help="Upload compact evidence to the private GitHub bridge mailbox")
    args = ap.parse_args()
    if args.port != 19727:
        raise RuntimeError("Locked to verified BDD port 19727")
    before = require_target(args.port)
    print('TARGET VERIFIED; starting read-only inventory on port 19727', flush=True)
    addon = tapir(args.port, "GetAddOnVersion")
    stories = tapir(args.port, "GetStories")
    all_rows = tapir(args.port, "GetAllElements").get("elements")
    if not isinstance(all_rows, list):
        raise RuntimeError("GetAllElements did not return an elements list")
    guids = sorted([g for g in (guid_of(x) for x in all_rows) if g])
    if len(set(x.casefold() for x in guids)) != len(guids):
        raise RuntimeError("Duplicate GUIDs: inventory aborted")

    details, bboxes, warnings = [], [], []
    for start in range(0, len(guids), 48):
        group = guids[start:start + 48]
        ds, es = read_batch(args.port, "GetDetailsOfElements",
                            group, "detailsOfElements")
        bs, eb = read_batch(args.port, "Get3DBoundingBoxes",
                            group, "boundingBoxes3D")
        details.extend(ds)
        bboxes.extend(bs)
        warnings.extend(es + eb)
        print('READ PROGRESS: %d/%d GUIDs' % (min(start + len(group), len(guids)), len(guids)), flush=True)
        if start % 240 == 0:
            require_target(args.port)

    after = require_target(args.port)
    final_rows = tapir(args.port, "GetAllElements").get("elements")
    require_target(args.port)
    final_guids = [g for g in (guid_of(x) for x in final_rows) if g]
    if (set(x.casefold() for x in final_guids)
            != set(x.casefold() for x in guids)):
        raise RuntimeError("Model changed during capture; no upload")

    elements = [
        element_info(g, details[i], bboxes[i])
        for i, g in enumerate(guids)
    ]
    type_counts = dict(sorted(Counter(e["type"] for e in elements).items()))
    story_counts = dict(sorted(Counter(
        str(e["floorIndex"]) for e in elements).items()))
    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = Path(tempfile.gettempdir()) / "APA_BDD_Readonly"
    output_dir.mkdir(parents=True, exist_ok=True)
    full = output_dir / ("bdd-full-%s.json" % now)
    compact = output_dir / ("bdd-inventory-%s.json" % now)

    raw_evidence = {
        "capturedAtUTC": now,
        "port": args.port,
        "projectBefore": before,
        "projectAfter": after,
        "addon": addon,
        "stories": stories,
        "guids": guids,
        "details": details,
        "boundingBoxes": bboxes,
        "warnings": warnings,
        "readOnly": True,
    }
    report = {
        "schema": "apa.bdd.inventory.readonly.v1",
        "status": "PARTIAL" if warnings or any(
            not e["detailsPresent"] or not e["bboxPresent"] for e in elements) else "PASS",
        "capturedAtUTC": now,
        "source": "LIVE_ARCHICAD_29_TAPIR",
        "readOnly": True,
        "mutationApplied": False,
        "port": args.port,
        "projectName": before["projectName"],
        "projectPath": before["projectPath"],
        "tapirVersion": addon.get("version"),
        "stories": stories.get("stories", []),
        "currentStory": stories.get("actStory"),
        "elementCount": len(guids),
        "detailsFound": sum(e["detailsPresent"] for e in elements),
        "bboxFound": sum(e["bboxPresent"] for e in elements),
        "countsByType": type_counts,
        "countsByStoryIndex": story_counts,
        "warnings": warnings,
        "elements": elements,
    }
    write_json(full, raw_evidence)
    write_json(compact, report)
    print("BDD INVENTORY:", report["status"])
    print("PROJECT:", ascii(before["projectName"]))
    print("PORT:", args.port, "ELEMENTS:", len(guids))
    print("TYPES:", json.dumps(type_counts, ensure_ascii=True))
    print("DETAILS:", report["detailsFound"], "BOXES:", report["bboxFound"])
    print("FULL LOCAL:", full)
    print("REPORT LOCAL:", compact)
    if args.publish:
        link = publish_to_private_mailbox(compact, now)
        print("PRIVATE GITHUB REPORT:", link)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print("ERROR:", type(exc).__name__ + ":", str(exc), file=sys.stderr)
        raise SystemExit(2)
