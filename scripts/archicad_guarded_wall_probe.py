"""One-wall Archicad 29 write probe: explicit port, exact PLN guard, read-back.

Default is DRY RUN. This script does not switch or save projects.
Execute ONCE, only after reviewing the dry-run result. If outcome is unclear,
inspect the existing PLN before retrying; a failed response may follow a write.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def tapir(port: int, command: str, params: dict | None = None) -> dict:
    request = {
        "command": "API.ExecuteAddOnCommand",
        "parameters": {
            "addOnCommandId": {
                "commandNamespace": "TapirCommand",
                "commandName": command,
            },
            "addOnCommandParameters": params or {},
        },
    }
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}",
        data=json.dumps(request, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as response:
        result = json.loads(response.read().decode("utf-8"))
    if result.get("succeeded") is not True:
        raise RuntimeError(f"{command} failed: {result.get('error')!r}")
    payload = result.get("result", {}).get("addOnCommandResponse")
    if not isinstance(payload, dict):
        raise RuntimeError(f"{command} returned no Tapir response")
    return payload


def guard(port: int, project_name: str, project_dir_hint: str) -> dict:
    project = tapir(port, "GetProjectInfo")
    name = str(project.get("projectName") or "").strip()
    path = str(project.get("projectPath") or "")
    if project.get("isUntitled") or project.get("isTeamwork"):
        raise RuntimeError("Expected a saved local test PLN, not Untitled/Teamwork")
    if name.casefold() != project_name.strip().casefold():
        raise RuntimeError(f"Wrong PLN name on port {port}: {name!r}")
    if project_dir_hint.casefold() not in path.casefold():
        raise RuntimeError(f"Wrong PLN directory on port {port}: {path!r}")
    stories = tapir(port, "GetStories")
    first = next((x for x in stories.get("stories", [])
                  if x.get("index") == 0), None)
    if (stories.get("actStory") != 0 or not first
            or first.get("floorId") != 1
            or abs(float(first.get("level", -999))) > 1e-6):
        raise RuntimeError("Expected the active first floor: index=0, floorId=1, level=0")
    return {"port": port, "name": name, "path": path,
            "story": 0, "storyElevation": float(first["level"])}


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")
    os.replace(tmp, path)


def run() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--port", type=int, required=True)
    p.add_argument("--expect-name", required=True)
    p.add_argument("--expect-dir", required=True)
    p.add_argument("--x", type=float, required=True)
    p.add_argument("--y", type=float, required=True)
    p.add_argument("--length", type=float, default=1.0)
    p.add_argument("--height", type=float, default=3.0)
    p.add_argument("--thickness", type=float, default=0.2)
    p.add_argument("--execute", action="store_true")
    args = p.parse_args()
    if not (1 <= args.port <= 65535):
        raise ValueError("invalid port")
    import math
    if (not all(map(math.isfinite, (args.x, args.y, args.length,
                                   args.height, args.thickness)))
            or not (0.2 <= args.length <= 5.0)
            or not (0.5 <= args.height <= 5.0)
            or not (0.05 <= args.thickness <= 0.5)):
        raise ValueError("invalid geometry (meters)")

    before = guard(args.port, args.expect_name, args.expect_dir)
    version = tapir(args.port, "GetAddOnVersion").get("version")
    wall = {
        "begCoordinate": {"x": args.x, "y": args.y},
        "endCoordinate": {"x": args.x + args.length, "y": args.y},
        "floorIndex": 0,
        "zCoordinate": 0.0,
        "height": args.height,
        "thickness": args.thickness,
        "offset": 0.0,
        "arcAngle": 0.0,
        "referenceLineLocation": "Center",
        "structureType": "Basic",
    }
    evidence_dir = Path(os.environ.get("SAFE_BIM_PROBE_DIR")
                        or (Path(os.environ.get("LOCALAPPDATA") or tempfile.gettempdir())
                            / "SafeBIM" / "wall-probe"))
    marker = evidence_dir / f"wall-probe-port-{args.port}.json"
    summary = {"status": "DRY_RUN", "target": before, "tapirVersion": version,
               "parameters": wall, "willSavePln": False}

    if not args.execute:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    if marker.exists():
        raise RuntimeError(f"Execution already attempted. Inspect {marker} before retrying.")
    if guard(args.port, args.expect_name, args.expect_dir) != before:
        raise RuntimeError("Target PLN changed since initial check")

    atomic_json(marker, {
        **summary, "status": "ATTEMPTED", "createdAt": datetime.now(timezone.utc).isoformat()
    })
    response = tapir(args.port, "CreateWalls", {"wallsData": [wall]})
    guids = [x.get("elementId", {}).get("guid") for x in response.get("elements", [])
             if isinstance(x, dict) and x.get("elementId", {}).get("guid")]
    if len(guids) != 1:
        raise RuntimeError(f"Ambiguous create response; DO NOT RETRY: {response!r}")
    created_guid = guids[0]
    atomic_json(marker, {**summary, "status": "CREATED_UNVERIFIED",
                         "createdGuid": created_guid})
    if guard(args.port, args.expect_name, args.expect_dir) != before:
        raise RuntimeError("Project changed after native create; do not retry")
    details = tapir(args.port, "GetDetailsOfElements", {
        "elements": [{"elementId": {"guid": created_guid}}]
    })
    rows = details.get("detailsOfElements", [])
    item = next((x for x in rows if isinstance(x, dict)
                 and x.get("elementId", {}).get("guid", "").casefold() == created_guid.casefold()), None)
    if item is None and len(rows) == 1 and isinstance(rows[0], dict):
        item = rows[0]
    ok = bool(item and item.get("type") == "Wall"
              and item.get("floorIndex") == 0)
    result = {
        **summary, "status": "PASS" if ok else "BLOCKED_READBACK",
        "createdGuid": created_guid, "readbackType": item.get("type") if item else None,
        "readbackFloorIndex": item.get("floorIndex") if item else None,
        "retained": True, "plnSaved": False,
    }
    atomic_json(marker, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if ok else 2


if __name__ == "__main__":
    try:
        raise SystemExit(run())
    except Exception as exc:
        print(json.dumps({"status": "BLOCKED", "error": str(exc),
                          "instruction": "Do not retry an uncertain write."},
                         ensure_ascii=False), file=sys.stderr)
        raise SystemExit(2)
