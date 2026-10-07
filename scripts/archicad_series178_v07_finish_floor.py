"""Series 178-07sm.86 v0.7 — finish the whole typical floor in one pass.

What this pass does:
1. Creates REAL Archicad associative Dimension chains from Wall endpoints:
   X: 3000+3600+3000+3600+3600+3600+3000 = 23400 mm
   Y: 5400+2400+5400 = 13200 mm
2. Deletes the fake Line/Text control dimensions from v0.6 only AFTER native
   Dimension elements exist.
3. Builds the remaining main room/service partitions in one batch-style loop.
4. Creates apartment-entry and internal doors.
5. Leaves the proven stair, facade windows/doors, balconies and split bearing
   walls in place.

The passport fixes the modular grid and room-area labels. Small wet-room/service
partitions that are not legible on the passport remain explicitly provisional,
but the topology follows the photographed plan rather than the earlier stripe
layout.

Never opens/switches/saves/closes the PLN. Every created GUID is persisted
immediately so a partial failure is recoverable without blind retry.
"""
from __future__ import annotations

import argparse
import json
import os
import tempfile
import urllib.request
from pathlib import Path
from typing import Any

PORT = 19725
ROOT = Path(tempfile.gettempdir())
BASE = Path(os.environ.get(
    "SAFE_BIM_MVP_EVIDENCE",
    ROOT / "safe-bim-mvp-evidence",
))
SK = ROOT / "series178-direct-19725-created.json"
V03 = BASE / "series178-v03" / "manifest.json"
V05 = BASE / "series178-v05" / "manifest.json"
V06 = BASE / "series178-v06" / "manifest.json"
V02_ACCESS = BASE / "series178-v02" / "stair-access.json"
OUT = BASE / "series178-v07" / "manifest.json"

WALL_IDS = [
    "EXT_S_01","EXT_S_02","EXT_S_03","EXT_S_04","EXT_S_05","EXT_S_06","EXT_S_07",
    "EXT_N_01","EXT_N_02","EXT_N_03","EXT_N_04","EXT_N_05","EXT_N_06","EXT_N_07",
    "EXT_W_01","EXT_W_02","EXT_W_03","EXT_E_01","EXT_E_02","EXT_E_03",
    "INT_X_2","INT_X_3","INT_X_4","INT_X_6","INT_X_7","INT_X_8","CORE_S","CORE_N",
]
TRANSVERSE = ["INT_X_2","INT_X_3","INT_X_4","INT_X_6","INT_X_7","INT_X_8"]


def api(cmd: str, params: dict | None = None) -> dict:
    body = {
        "command": "API.ExecuteAddOnCommand",
        "parameters": {
            "addOnCommandId": {
                "commandNamespace": "TapirCommand",
                "commandName": cmd,
            },
            "addOnCommandParameters": params or {},
        },
    }
    req = urllib.request.Request(
        f"http://127.0.0.1:{PORT}",
        json.dumps(body, ensure_ascii=False).encode("utf-8"),
        {"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=90) as response:
        env = json.loads(response.read())
    if not env.get("succeeded"):
        raise RuntimeError(f"{cmd} transport failed: {env}")
    out = env.get("result", {}).get("addOnCommandResponse", {})
    if isinstance(out, dict) and out.get("error") is not None:
        raise RuntimeError(f"{cmd}: {out['error']}")
    return out


def E(guid: str) -> dict:
    return {"elementId": {"guid": guid}}


def live_guids() -> set[str]:
    return {
        row["elementId"]["guid"].lower()
        for row in api("GetAllElements").get("elements", [])
        if row.get("elementId", {}).get("guid")
    }


def detail(guid: str) -> dict:
    rows = api(
        "GetDetailsOfElements",
        {"elements": [E(guid)]},
    ).get("detailsOfElements", [])
    if len(rows) != 1:
        raise RuntimeError(f"GetDetailsOfElements returned {len(rows)} rows for {guid}")
    return rows[0]


def one_guid(result: dict, label: str) -> str:
    guids = [
        row.get("elementId", {}).get("guid")
        for row in result.get("elements", [])
    ]
    guids = [g for g in guids if g]
    if len(guids) != 1:
        raise RuntimeError(f"{label}: expected one GUID, got {result}")
    return guids[0]


def all_created_guids(result: dict, label: str) -> list[str]:
    rows = result.get("elements", [])
    out: list[str] = []
    errors: list[Any] = []
    for row in rows:
        guid = row.get("elementId", {}).get("guid")
        if guid:
            out.append(guid)
        elif row.get("error"):
            errors.append(row["error"])
    if errors:
        raise RuntimeError(f"{label}: native errors: {errors}")
    return out


def save(manifest: dict) -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def add(manifest: dict, id_: str, type_: str, guid: str, meta: dict | None = None) -> None:
    row = {"id": id_, "type": type_, "guid": guid}
    if meta:
        row["meta"] = meta
    manifest["created"].append(row)
    save(manifest)


def create_wall(
    a: tuple[float, float],
    b: tuple[float, float],
    story: int,
    thickness: float = 0.08,
    height: float = 2.84,
) -> str:
    result = api(
        "CreateWalls",
        {
            "wallsData": [{
                "begCoordinate": {"x": a[0], "y": a[1]},
                "endCoordinate": {"x": b[0], "y": b[1]},
                "floorIndex": story,
                "zCoordinate": 0.0,
                "height": height,
                "thickness": thickness,
                "offset": 0.0,
                "arcAngle": 0.0,
                "referenceLineLocation": "Center",
                "structureType": "Basic",
            }]
        },
    )
    guid = one_guid(result, "CreateWalls")
    d = detail(guid)
    if d.get("type") != "Wall" or int(d.get("floorIndex", -999)) != story:
        raise RuntimeError(f"Wall read-back mismatch for {guid}: {d}")
    return guid


def create_door(
    host_guid: str,
    offset: float,
    width: float = 0.80,
    height: float = 2.05,
) -> str:
    result = api(
        "CreateDoors",
        {
            "doorsData": [{
                "ownerWallId": {"guid": host_guid},
                "centerOffset": offset,
                "sillHeight": 0.0,
                "width": width,
                "height": height,
                "reflected": False,
                "refSide": False,
                "oSide": False,
            }]
        },
    )
    guid = one_guid(result, "CreateDoors")
    d = detail(guid)
    if d.get("type") != "Door":
        raise RuntimeError(f"Door read-back mismatch for {guid}: {d}")
    return guid


def create_native_dimension(
    reference_point: tuple[float, float],
    direction: tuple[float, float],
    story: int,
    witnesses: list[tuple[str, int]],
) -> str:
    data = {
        "referencePoint": {"x": reference_point[0], "y": reference_point[1]},
        "direction": {"x": direction[0], "y": direction[1]},
        "floorIndex": story,
        "witnessPoints": [
            {
                "elementId": {"guid": guid},
                "inIndex": in_index,
            }
            for guid, in_index in witnesses
        ],
    }
    result = api(
        "CreateAssociativeDimensions",
        {"dimensionsData": [data]},
    )
    guid = one_guid(result, "CreateAssociativeDimensions")
    # Do not require full Dimension details; Tapir 1.5.x may expose only type data.
    d = detail(guid)
    if d.get("type") != "Dimension":
        raise RuntimeError(f"Native dimension read-back mismatch: {d}")
    return guid


def resolve_split_walls(v05: dict) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for key in TRANSVERSE:
        result[key] = {}
    for row in v05.get("created", []):
        id_ = row.get("id", "")
        guid = row.get("guid")
        if not guid:
            continue
        for key in TRANSVERSE:
            if id_ == key + "_S":
                result[key]["S"] = guid
            elif id_ == key + "_N":
                result[key]["N"] = guid
    for key in TRANSVERSE:
        if set(result[key]) != {"S", "N"}:
            raise RuntimeError(f"v0.5 replacement pair missing for {key}: {result[key]}")
    return result


def resolve_core_n(v03: dict) -> tuple[str, str]:
    left = None
    right = None
    # v0.3 creates CORE_N_L/R and persists them in its own manifest.
    for row in v03.get("created", []):
        if row.get("id") == "CORE_N_L":
            left = row.get("guid")
        elif row.get("id") == "CORE_N_R":
            right = row.get("guid")
    if not left or not right:
        # fallback to v0.2 dedicated access manifest if that path was used
        if V02_ACCESS.is_file():
            data = json.loads(V02_ACCESS.read_text(encoding="utf-8-sig"))
            for row in data.get("created", []):
                if row.get("id") == "CORE_N_L":
                    left = row.get("guid")
                elif row.get("id") == "CORE_N_R":
                    right = row.get("guid")
    if not left or not right:
        raise RuntimeError("CORE_N_L / CORE_N_R not found in v0.3/v0.2 evidence")
    return left, right


def main() -> None:
    global PORT

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    PORT = args.port

    for path in (SK, V03, V05, V06):
        if not path.is_file():
            raise RuntimeError(f"missing required manifest: {path}")

    sk = json.loads(SK.read_text(encoding="utf-8-sig"))
    v03 = json.loads(V03.read_text(encoding="utf-8-sig"))
    v05 = json.loads(V05.read_text(encoding="utf-8-sig"))
    v06 = json.loads(V06.read_text(encoding="utf-8-sig"))

    project = api("GetProjectInfo")
    project_path = project.get("projectPath") or ""
    if "SafeBIM_Global_Library_Test_Projects".lower() not in project_path.lower():
        raise RuntimeError(f"wrong project on port {PORT}: {project_path}")

    stories = api("GetStories")
    story = int(sk.get("storyIndex", 0))
    if int(stories.get("actStory", -999)) != story:
        raise RuntimeError(
            f"active story {stories.get('actStory')} != target story {story}"
        )

    if len(sk.get("wallGuids", [])) != 28:
        raise RuntimeError("skeleton manifest is incomplete")

    wm = dict(zip(WALL_IDS, sk["wallGuids"]))
    split = resolve_split_walls(v05)
    core_n_l, core_n_r = resolve_core_n(v03)

    live = live_guids()

    # Required geometry that must still be present.
    required = [
        *[wm[f"EXT_S_0{i}"] for i in range(1, 8)],
        wm["EXT_W_01"], wm["EXT_W_02"], wm["EXT_W_03"],
        wm["CORE_S"],
        core_n_l, core_n_r,
    ]
    for key in TRANSVERSE:
        required += [split[key]["S"], split[key]["N"]]
    missing = [g for g in required if g.lower() not in live]
    if missing:
        raise RuntimeError(f"required live geometry missing: {missing[:8]}")

    if OUT.is_file():
        old = json.loads(OUT.read_text(encoding="utf-8-sig"))
        old_live = [
            x.get("guid")
            for x in old.get("created", [])
            if x.get("guid") and x["guid"].lower() in live
        ]
        if old.get("status") == "PASS" and old_live:
            raise RuntimeError("v0.7 already present; refusing duplicate")

    ox = float(sk["originX"])
    oy = float(sk["originY"])

    # Main partition geometry. This follows the passport topology:
    # four apartment groups around a central 2.4 m corridor/stair core.
    main_partitions = [
        # SOUTH / left 3B + 2B
        ("S_L_OUTER_ROOM", (ox+0.00, oy+4.10), (ox+3.00, oy+4.10), 12.38),
        ("S_L_KITCHEN",    (ox+3.00, oy+2.45), (ox+6.60, oy+2.45), 8.76),
        ("S_2B_ROOM",      (ox+6.60, oy+3.45), (ox+9.60, oy+3.45), 10.39),
        # SOUTH / right 1B + right 3B
        ("S_R_KITCHEN",    (ox+16.80, oy+2.45), (ox+20.40, oy+2.45), 8.76),
        ("S_R_OUTER_ROOM", (ox+20.40, oy+4.10), (ox+23.40, oy+4.10), 12.38),

        # NORTH / left 3B
        ("N_L_OUTER_ROOM", (ox+0.00, oy+9.45), (ox+3.00, oy+9.45), 11.25),
        ("N_L_KITCHEN",    (ox+3.00, oy+10.75), (ox+6.60, oy+10.75), 8.76),
        # NORTH / right 3B
        ("N_R_KITCHEN",    (ox+16.80, oy+10.75), (ox+20.40, oy+10.75), 8.76),
        ("N_R_OUTER_ROOM", (ox+20.40, oy+9.45), (ox+23.40, oy+9.45), 11.25),
    ]

    # Small service/wet-room partitions traced from the passport's symmetric
    # clusters. Exact sanitary cubicle dimensions are provisional.
    service_partitions = [
        # LEFT, north of corridor
        ("LN_WET_V1", (ox+1.35, oy+7.80), (ox+1.35, oy+9.45)),
        ("LN_WET_H1", (ox+0.00, oy+8.65), (ox+3.00, oy+8.65)),
        ("LN_HALL_V", (ox+4.55, oy+7.80), (ox+4.55, oy+10.75)),
        ("LN_HALL_H", (ox+3.00, oy+9.55), (ox+6.60, oy+9.55)),

        # LEFT, south of corridor
        ("LS_WET_V1", (ox+1.35, oy+4.10), (ox+1.35, oy+5.40)),
        ("LS_WET_H1", (ox+0.00, oy+4.75), (ox+3.00, oy+4.75)),
        ("LS_HALL_V", (ox+4.55, oy+2.45), (ox+4.55, oy+5.40)),
        ("LS_HALL_H", (ox+3.00, oy+4.15), (ox+6.60, oy+4.15)),
        ("LS_2B_HALL", (ox+6.60, oy+4.35), (ox+9.60, oy+4.35)),

        # RIGHT, north of corridor
        ("RN_HALL_V", (ox+18.85, oy+7.80), (ox+18.85, oy+10.75)),
        ("RN_HALL_H", (ox+16.80, oy+9.55), (ox+20.40, oy+9.55)),
        ("RN_WET_V1", (ox+22.05, oy+7.80), (ox+22.05, oy+9.45)),
        ("RN_WET_H1", (ox+20.40, oy+8.65), (ox+23.40, oy+8.65)),

        # RIGHT, south of corridor
        ("RS_HALL_V", (ox+18.85, oy+2.45), (ox+18.85, oy+5.40)),
        ("RS_HALL_H", (ox+16.80, oy+4.15), (ox+20.40, oy+4.15)),
        ("RS_WET_V1", (ox+22.05, oy+4.10), (ox+22.05, oy+5.40)),
        ("RS_WET_H1", (ox+20.40, oy+4.75), (ox+23.40, oy+4.75)),

        # South-center apartment entrance/service strips
        ("C2B_SERVICE", (ox+7.40, oy+4.35), (ox+7.40, oy+5.40)),
        ("C1B_SERVICE", (ox+15.95, oy+4.35), (ox+15.95, oy+5.40)),
    ]

    fake_dimension_guids = [
        guid for guid in v06.get("dimensionGuids", [])
        if guid and guid.lower() in live
    ]

    plan = {
        "status": "DRY_RUN" if not args.execute else "IN_PROGRESS",
        "port": PORT,
        "projectPath": project_path,
        "storyIndex": story,
        "nativeDimensions": {
            "xSegmentsMm": [3000,3600,3000,3600,3600,3600,3000],
            "xOverallMm": 23400,
            "ySegmentsMm": [5400,2400,5400],
            "yOverallMm": 13200,
            "tool": "CreateAssociativeDimensions",
        },
        "fakeDimensionDeleteCount": len(fake_dimension_guids),
        "mainPartitionCount": len(main_partitions),
        "servicePartitionCount": len(service_partitions),
        "created": [],
        "deleted": [],
        "dimensionVerification": [],
        "savedProject": False,
    }

    if not args.execute:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return

    save(plan)

    # ------------------------------------------------------------------
    # 1. REAL ARCHICAD DIMENSIONS FIRST
    # ------------------------------------------------------------------

    x_witnesses = [
        (wm["EXT_S_01"], 1),
        (wm["EXT_S_01"], 2),
        (wm["EXT_S_02"], 2),
        (wm["EXT_S_03"], 2),
        (wm["EXT_S_04"], 2),
        (wm["EXT_S_05"], 2),
        (wm["EXT_S_06"], 2),
        (wm["EXT_S_07"], 2),
    ]
    y_witnesses = [
        (wm["EXT_W_01"], 1),
        (wm["EXT_W_01"], 2),
        (wm["EXT_W_02"], 2),
        (wm["EXT_W_03"], 2),
    ]

    dimension_specs = [
        ("DIM_X_CHAIN", (ox, oy-1.80), (1.0, 0.0), x_witnesses),
        ("DIM_X_TOTAL", (ox, oy-2.70), (1.0, 0.0), [x_witnesses[0], x_witnesses[-1]]),
        ("DIM_Y_CHAIN", (ox-1.80, oy), (0.0, 1.0), y_witnesses),
        ("DIM_Y_TOTAL", (ox-2.70, oy), (0.0, 1.0), [y_witnesses[0], y_witnesses[-1]]),
    ]

    dimension_guids: list[str] = []
    for id_, ref, direction, witnesses in dimension_specs:
        guid = create_native_dimension(ref, direction, story, witnesses)
        dimension_guids.append(guid)
        add(plan, id_, "Dimension", guid)

        # Direct JSON Tapir often returns usable values even where higher-level
        # connector schemas lag. Record verification if available, but do not
        # destroy a valid dimension merely because GetDimensionData is incomplete.
        try:
            vr = api("GetDimensionData", {"elements": [E(guid)]})
            plan["dimensionVerification"].append({"id": id_, "result": vr})
            save(plan)
        except Exception as exc:
            plan["dimensionVerification"].append({"id": id_, "warning": str(exc)})
            save(plan)

    # Delete v0.6 Line/Text pseudo-dimensions only after all four native
    # Dimension elements exist.
    if len(dimension_guids) != 4:
        raise RuntimeError("native dimension creation incomplete; fake dimensions retained")

    for guid in fake_dimension_guids:
        api("DeleteElements", {"elements": [E(guid)]})
        if guid.lower() in live_guids():
            raise RuntimeError(f"failed to delete fake dimension element {guid}")
        plan["deleted"].append({
            "id": "V06_FAKE_DIM",
            "guid": guid,
        })
        save(plan)

    # ------------------------------------------------------------------
    # 2. MAIN + SERVICE PARTITIONS
    # ------------------------------------------------------------------

    created_walls: dict[str, str] = {}

    for id_, a, b, area in main_partitions:
        guid = create_wall(a, b, story, thickness=0.08)
        created_walls[id_] = guid
        add(
            plan,
            id_,
            "Wall",
            guid,
            {
                "printedRoomAreaM2": area,
                "status": "PASSPORT_GUIDED",
            },
        )

    for id_, a, b in service_partitions:
        guid = create_wall(a, b, story, thickness=0.08)
        created_walls[id_] = guid
        add(
            plan,
            id_,
            "Wall",
            guid,
            {"status": "PROVISIONAL_FROM_PASSPORT_TRACE"},
        )

    # ------------------------------------------------------------------
    # 3. APARTMENT ENTRY DOORS
    # ------------------------------------------------------------------

    entries = [
        ("ENTRY_3B_L", core_n_l, 1.90, 0.90),
        ("ENTRY_3B_R", core_n_r, 2.25, 0.90),
        ("ENTRY_2B", wm["CORE_S"], 2.15, 0.90),
        ("ENTRY_1B", wm["CORE_S"], 7.65, 0.90),
    ]
    for id_, host, offset, width in entries:
        guid = create_door(host, offset, width=width, height=2.10)
        add(plan, id_, "Door", guid, {"status": "PASSPORT_GUIDED"})

    # ------------------------------------------------------------------
    # 4. INTERNAL DOORS — on split bearing walls + new partitions
    # ------------------------------------------------------------------

    door_specs = [
        # Left 3B
        ("D_L3B_OUT_S", split["INT_X_2"]["S"], 3.25, 0.80),
        ("D_L3B_IN_S",  split["INT_X_3"]["S"], 2.95, 0.80),
        ("D_L3B_OUT_N", split["INT_X_2"]["N"], 2.20, 0.80),
        ("D_L3B_IN_N",  split["INT_X_3"]["N"], 1.75, 0.80),

        # 2B + 1B south center
        ("D_2B_BEAR", split["INT_X_4"]["S"], 2.55, 0.80),
        ("D_1B_BEAR", split["INT_X_6"]["S"], 2.55, 0.80),

        # Right 3B
        ("D_R3B_IN_S",  split["INT_X_7"]["S"], 2.95, 0.80),
        ("D_R3B_OUT_S", split["INT_X_8"]["S"], 3.25, 0.80),
        ("D_R3B_IN_N",  split["INT_X_7"]["N"], 1.75, 0.80),
        ("D_R3B_OUT_N", split["INT_X_8"]["N"], 2.20, 0.80),
    ]

    for id_, host, offset, width in door_specs:
        guid = create_door(host, offset, width=width)
        add(plan, id_, "Door", guid, {"status": "PROVISIONAL_TRACE"})

    # Doors in several new horizontal/vertical service partitions.
    new_partition_doors = [
        ("D_LN_KITCHEN", "N_L_KITCHEN", 1.70, 0.80),
        ("D_LS_KITCHEN", "S_L_KITCHEN", 1.70, 0.80),
        ("D_RN_KITCHEN", "N_R_KITCHEN", 1.70, 0.80),
        ("D_RS_KITCHEN", "S_R_KITCHEN", 1.70, 0.80),
        ("D_2B_ROOM", "S_2B_ROOM", 1.55, 0.80),
    ]
    for id_, wall_id, offset, width in new_partition_doors:
        host = created_walls[wall_id]
        guid = create_door(host, offset, width=width)
        add(plan, id_, "Door", guid, {"status": "PROVISIONAL_TRACE"})

    plan["status"] = "PASS"
    plan["elementCountAfter"] = len(live_guids())
    plan["nextPhase"] = "single visual QA; then upper-storey copy"
    save(plan)

    try:
        new_elements = [E(row["guid"]) for row in plan["created"]]
        api("ChangeSelectionOfElements", {"addElementsToSelection": new_elements})
        api("FitInWindow", {"elements": new_elements})
    except Exception:
        pass

    print(json.dumps(plan, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(json.dumps({
            "status": "BLOCKED",
            "error": str(exc),
            "evidence": str(OUT),
            "note": "Do not blindly rerun; every created GUID is persisted.",
        }, ensure_ascii=False, indent=2))
        raise SystemExit(2)
