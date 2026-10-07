"""Series 178 v0.2: open the stair access in CORE_N safely.

The photographed passport shows an opening from the 2.4 m corridor into the
central stair bay. This pass keeps the existing skeleton but replaces the one
continuous CORE_N wall by two copied Basic-wall segments, leaving a provisional
1.80 m clear opening centered in the verified 3.60 m stair bay.

Safety:
- standard Tapir only; no Model Dump dependency;
- exact project/story/skeleton GUID guards;
- creates and reads back both replacement segments BEFORE deleting CORE_N;
- writes every created GUID immediately;
- refuses duplicate/retry if live v0.2 access evidence already exists;
- never saves/opens/switches/closes the PLN.
"""
from __future__ import annotations

import argparse
import json
import os
import tempfile
import urllib.request
from pathlib import Path
from typing import Any

SKELETON = Path(tempfile.gettempdir()) / "series178-direct-19725-created.json"
EVIDENCE = Path(os.environ.get(
    "SAFE_BIM_MVP_EVIDENCE",
    Path(tempfile.gettempdir()) / "safe-bim-mvp-evidence"
)) / "series178-v02" / "stair-access.json"

WALL_ORDER = [
    "EXT_S_01","EXT_S_02","EXT_S_03","EXT_S_04","EXT_S_05","EXT_S_06","EXT_S_07",
    "EXT_N_01","EXT_N_02","EXT_N_03","EXT_N_04","EXT_N_05","EXT_N_06","EXT_N_07",
    "EXT_W_01","EXT_W_02","EXT_W_03","EXT_E_01","EXT_E_02","EXT_E_03",
    "INT_X_2","INT_X_3","INT_X_4","INT_X_6","INT_X_7","INT_X_8","CORE_S","CORE_N",
]


def api(port: int, command: str, params: dict | None = None) -> dict:
    payload = json.dumps({
        "command": "API.ExecuteAddOnCommand",
        "parameters": {
            "addOnCommandId": {
                "commandNamespace": "TapirCommand",
                "commandName": command,
            },
            "addOnCommandParameters": params or {},
        },
    }, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}",
        payload,
        {"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=90) as response:
        env = json.loads(response.read())
    if not env.get("succeeded"):
        raise RuntimeError(f"{command} transport failed: {env}")
    result = env.get("result", {}).get("addOnCommandResponse", {})
    if isinstance(result, dict) and result.get("error") is not None:
        raise RuntimeError(f"{command} failed: {result['error']}")
    return result


def write(value: Any) -> None:
    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE.write_text(
        json.dumps(value, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def elem(guid: str) -> dict:
    return {"elementId": {"guid": guid}}


def live_guids(port: int) -> set[str]:
    return {
        x["elementId"]["guid"].lower()
        for x in api(port, "GetAllElements").get("elements", [])
        if x.get("elementId", {}).get("guid")
    }


def detail(port: int, guid: str) -> dict:
    rows = api(
        port,
        "GetDetailsOfElements",
        {"elements": [elem(guid)]},
    ).get("detailsOfElements", [])
    if len(rows) != 1:
        raise RuntimeError(f"expected one detail row for {guid}, got {len(rows)}")
    return rows[0]


def one_guid(result: dict, label: str) -> str:
    rows = result.get("elements", [])
    ids = [x.get("elementId", {}).get("guid") for x in rows]
    ids = [x for x in ids if x]
    if len(ids) != 1:
        raise RuntimeError(f"{label} returned {rows}")
    return ids[0]


def create_segment(
    port: int,
    source_details: dict,
    a: tuple[float, float],
    b: tuple[float, float],
    story: int,
) -> str:
    d = source_details["details"]
    if d.get("geometryType") != "Straight":
        raise RuntimeError("CORE_N is no longer a straight Wall")
    structure = d.get("structureType", "Basic")
    if structure != "Basic":
        raise RuntimeError(
            f"CORE_N structure changed to {structure}; refuse provisional split"
        )

    row = {
        "begCoordinate": {"x": a[0], "y": a[1]},
        "endCoordinate": {"x": b[0], "y": b[1]},
        "floorIndex": story,
        "zCoordinate": float(d.get("bottomOffset", 0.0)),
        "height": float(d["height"]),
        "thickness": float(d.get("begThickness", 0.16)),
        "offset": float(d.get("offset", 0.0)),
        "arcAngle": 0.0,
        "referenceLineLocation": d.get("referenceLineLocation", "Center"),
        "structureType": "Basic",
    }
    bm = d.get("buildingMaterialId")
    if isinstance(bm, dict) and bm.get("guid"):
        row["buildingMaterialId"] = bm

    guid = one_guid(
        api(port, "CreateWalls", {"wallsData": [row]}),
        "CreateWalls",
    )
    rd = detail(port, guid)
    if rd.get("type") != "Wall" or int(rd.get("floorIndex", -999)) != story:
        raise RuntimeError(f"replacement wall read-back mismatch: {rd}")
    return guid


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--port", type=int, default=19725)
    ap.add_argument(
        "--expect-project-substring",
        default="SafeBIM_Global_Library_Test_Projects",
    )
    ap.add_argument("--execute", action="store_true")
    args = ap.parse_args()

    if not SKELETON.is_file():
        raise RuntimeError(f"missing skeleton manifest: {SKELETON}")
    sk = json.loads(SKELETON.read_text(encoding="utf-8-sig"))
    if len(sk.get("wallGuids", [])) != 28:
        raise RuntimeError("skeleton manifest does not contain 28 wall GUIDs")

    wall_map = dict(zip(WALL_ORDER, sk["wallGuids"]))
    core_guid = wall_map["CORE_N"]

    project = api(args.port, "GetProjectInfo")
    project_path = project.get("projectPath") or ""
    if args.expect_project_substring.lower() not in project_path.lower():
        raise RuntimeError(f"wrong project on port {args.port}: {project_path}")

    stories = api(args.port, "GetStories")
    story = int(sk.get("storyIndex", 0))
    if int(stories.get("actStory", -999)) != story:
        raise RuntimeError(
            f"active story {stories.get('actStory')} != target story {story}"
        )

    live = live_guids(args.port)
    required = {
        sk["slabGuid"].lower(),
        *[g.lower() for g in sk["wallGuids"]],
    }
    missing = sorted(required - live)
    if missing:
        raise RuntimeError(
            "skeleton GUID guard failed; do not split a changed skeleton: "
            f"{missing[:6]}"
        )

    if EVIDENCE.is_file():
        old = json.loads(EVIDENCE.read_text(encoding="utf-8-sig"))
        created = [
            x.get("guid", "").lower()
            for x in old.get("created", [])
            if x.get("guid")
        ]
        if any(g in live for g in created):
            raise RuntimeError(
                "stair-access replacement already exists; refusing duplicate"
            )

    source = detail(args.port, core_guid)
    if source.get("type") != "Wall" or int(source.get("floorIndex", -999)) != story:
        raise RuntimeError(f"CORE_N read-back mismatch: {source}")

    d = source["details"]
    ox = float(sk["originX"])
    oy = float(sk["originY"])

    # Verified skeleton CORE_N endpoints are x=6.6..16.8, y=7.8.
    # Stair bay is x=9.6..13.2. Provisional access = 1.80 m centered in bay.
    opening_left = ox + 10.50
    opening_right = ox + 12.30
    y = oy + 7.80

    plan = {
        "status": "DRY_RUN" if not args.execute else "PLANNED",
        "port": args.port,
        "projectPath": project_path,
        "storyIndex": story,
        "sourceCoreNGuid": core_guid,
        "opening": {
            "x": [opening_left, opening_right],
            "y": y,
            "width": 1.80,
            "status": "PROVISIONAL_VISUAL_RECONSTRUCTION",
        },
        "newSegments": [
            {"id": "CORE_N_L", "a": [ox + 6.60, y], "b": [opening_left, y]},
            {"id": "CORE_N_R", "a": [opening_right, y], "b": [ox + 16.80, y]},
        ],
        "sequence": "create+readback left; create+readback right; delete old CORE_N last",
        "savedProject": False,
    }

    if not args.execute:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return

    state = {**plan, "status": "IN_PROGRESS", "created": [], "deleted": []}
    write(state)

    left = create_segment(
        args.port,
        source,
        (ox + 6.60, y),
        (opening_left, y),
        story,
    )
    state["created"].append({"id": "CORE_N_L", "guid": left})
    write(state)

    right = create_segment(
        args.port,
        source,
        (opening_right, y),
        (ox + 16.80, y),
        story,
    )
    state["created"].append({"id": "CORE_N_R", "guid": right})
    write(state)

    delete_result = api(
        args.port,
        "DeleteElements",
        {"elements": [elem(core_guid)]},
    )
    if core_guid.lower() in live_guids(args.port):
        raise RuntimeError("old CORE_N still present after DeleteElements")
    state["deleted"].append({
        "id": "CORE_N",
        "guid": core_guid,
        "nativeResult": delete_result,
    })

    new_elements = [elem(left), elem(right)]
    try:
        api(args.port, "ChangeSelectionOfElements", {
            "addElementsToSelection": new_elements
        })
        api(args.port, "FitInWindow", {"elements": new_elements})
    except Exception:
        pass

    state["status"] = "PASS"
    state["elementCountAfter"] = len(live_guids(args.port))
    state["nextPhase"] = (
        "visual compare corridor-to-stair opening; then apartment partitions"
    )
    write(state)
    print(json.dumps(state, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(json.dumps({
            "status": "BLOCKED",
            "error": str(exc),
            "evidence": str(EVIDENCE),
            "note": "Do not retry blindly; inspect watcher/evidence first.",
        }, ensure_ascii=False, indent=2))
        raise SystemExit(2)
