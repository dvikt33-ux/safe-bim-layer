"""Series 178-07см.86 QUALITY REBUILD.

Rebuilds the photographed passport plan from a rectified 23.4 x 13.2 m trace.
Key rule: plumbing/kitchen graphics are NOT converted into walls. Only traced
architectural boundaries become BIM Walls; secondary source linework is drawn
thin as 2D detail.

Creates:
- real exterior / bearing / partition Walls;
- main Slab;
- four balcony slabs with parapets;
- real facade Windows / balcony Doors;
- central Stair plus landing connected to corridor;
- thin source-traced service/detail graphics;
- native associative dimensions and axis labels;
- room/apartment text labels;
- no Zones.

Never opens, switches, saves or closes the PLN.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(tempfile.gettempdir())
BASE = Path(os.environ.get("SAFE_BIM_MVP_EVIDENCE", ROOT / "safe-bim-mvp-evidence"))
SK = ROOT / "series178-direct-19725-created.json"
OUT = BASE / "series178-QUALITY" / "manifest.json"
PORT: int | None = None

# Source trace: metres in the rectified 23.4 x 13.2 passport rectangle.
TRACE = [
(0.00,13.04,23.40,13.04),(0.00,0.10,23.40,0.10),
(0.05,0.10,0.05,13.20),(23.30,0.10,23.30,13.04),
(3.30,8.74,3.30,13.10),(6.94,9.12,6.94,13.08),(10.69,6.42,10.69,13.04),
(13.58,6.40,13.58,13.02),(17.15,9.14,17.15,13.04),(20.53,8.68,20.53,12.96),
(6.95,0.04,6.95,4.02),(10.03,0.06,10.03,4.04),(13.59,0.08,13.59,5.66),
(17.13,0.14,17.13,3.88),(20.57,0.16,20.57,7.66),
(3.16,9.58,6.00,9.58),(18.28,9.44,20.66,9.44),
(0.00,8.85,1.90,8.85),(21.64,8.75,23.40,8.75),
(2.58,7.68,5.82,7.68),(6.38,7.64,11.48,7.64),(12.42,7.61,17.46,7.61),(18.00,7.54,21.12,7.54),
(7.36,7.12,10.08,7.12),(14.08,7.06,16.54,7.06),
(1.18,6.98,3.62,6.98),(20.58,6.91,22.34,6.91),
(6.88,6.85,10.78,6.85),(13.50,6.84,17.18,6.84),
(3.50,6.03,5.58,6.03),(18.22,5.98,20.18,5.98),
(1.12,5.57,3.08,5.57),(20.60,5.54,22.38,5.54),
(1.16,5.41,4.04,5.41),(4.64,5.41,5.86,5.41),(6.40,5.37,17.50,5.37),(18.00,5.39,19.16,5.39),(19.70,5.38,22.38,5.38),
(1.18,4.31,3.36,4.31),(20.40,4.29,22.38,4.29),
(8.16,3.95,10.12,3.95),(3.14,3.68,5.48,3.68),(18.28,3.70,20.14,3.70),
(3.14,2.79,5.62,2.79),(5.74,2.79,7.04,2.79),(17.00,2.77,18.16,2.77),(18.26,2.79,20.10,2.79),
(3.12,2.12,5.10,2.12),(18.78,2.14,20.64,2.14),
(1.26,5.16,1.26,7.82),(3.40,5.34,3.40,7.76),(5.44,4.98,5.44,7.88),
(6.96,6.66,6.96,8.62),(10.04,4.42,10.04,5.44),(17.08,6.58,17.08,8.64),
(18.29,5.18,18.29,7.98),(19.06,5.28,19.06,6.88),(19.86,3.66,19.86,6.74),
(20.22,5.30,20.22,7.86),(21.79,6.10,21.79,7.84),(22.27,5.30,22.27,7.70),
(3.87,3.66,3.87,5.68),(5.22,2.72,5.22,3.92),(3.71,2.08,3.71,3.78),
(19.84,2.74,19.84,3.76),(20.07,2.10,20.07,3.78),
(3.94,11.04,3.94,12.60),(5.04,9.46,5.04,11.10),
(18.81,9.38,18.81,11.00),(19.88,10.92,19.88,12.52)
]

# Only these source segments are architectural wall boundaries.
# The rest of TRACE is retained as thin 2D service/fixture detail.
REAL_WALLS = [
(3.30,8.74,3.30,13.10),(6.94,9.12,6.94,13.08),(10.69,6.42,10.69,13.04),
(13.58,6.40,13.58,13.02),(17.15,9.14,17.15,13.04),(20.53,8.68,20.53,12.96),
(6.95,0.04,6.95,4.02),(10.03,0.06,10.03,4.04),(13.59,0.08,13.59,5.66),
(17.13,0.14,17.13,3.88),(20.57,0.16,20.57,7.66),
(1.26,5.16,1.26,7.82),(3.40,5.34,3.40,7.76),(5.44,4.98,5.44,7.88),
(6.96,6.66,6.96,8.62),(10.04,4.42,10.04,5.44),(17.08,6.58,17.08,8.64),
(18.29,5.18,18.29,7.98),(20.22,5.30,20.22,7.86),(22.27,5.30,22.27,7.70),
(3.87,3.66,3.87,5.68),(5.22,2.72,5.22,3.92),(3.71,2.08,3.71,3.78),
(19.84,2.74,19.84,3.76),(20.07,2.10,20.07,3.78),
(3.16,9.58,6.00,9.58),(18.28,9.44,20.66,9.44),
(0.00,8.85,1.90,8.85),(21.64,8.75,23.40,8.75),
(2.58,7.68,5.82,7.68),(6.38,7.64,11.48,7.64),(12.42,7.61,17.46,7.61),(18.00,7.54,21.12,7.54),
(1.18,6.98,3.62,6.98),(20.58,6.91,22.34,6.91),
(3.50,6.03,5.58,6.03),(18.22,5.98,20.18,5.98),
(1.12,5.57,3.08,5.57),(20.60,5.54,22.38,5.54),
(1.16,5.41,4.04,5.41),(4.64,5.41,5.86,5.41),
# lower corridor is split at the two apartment entries:
(6.40,5.37,10.05,5.37),(10.85,5.37,13.00,5.37),(13.80,5.37,17.50,5.37),
(18.00,5.39,19.16,5.39),(19.70,5.38,22.38,5.38),
(1.18,4.31,3.36,4.31),(20.40,4.29,22.38,4.29),
(8.16,3.95,10.12,3.95),(3.14,3.68,5.48,3.68),(18.28,3.70,20.14,3.70)
]

OUTER_TRACE = {
(0.00,13.04,23.40,13.04),(0.00,0.10,23.40,0.10),
(0.05,0.10,0.05,13.20),(23.30,0.10,23.30,13.04)
}


def call(port: int, cmd: str, params: dict | None = None, timeout: int = 90) -> dict:
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
        f"http://127.0.0.1:{port}",
        json.dumps(body, ensure_ascii=False).encode("utf-8"),
        {"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        env = json.loads(response.read())
    if not env.get("succeeded"):
        raise RuntimeError(f"{port}/{cmd} transport failed")
    out = env.get("result", {}).get("addOnCommandResponse", {})
    if isinstance(out, dict) and out.get("error") is not None:
        raise RuntimeError(f"{port}/{cmd}: {out['error']}")
    return out


def discover() -> tuple[int, str]:
    hits: list[tuple[int, str]] = []
    for port in range(19723, 19731):
        try:
            info = call(port, "GetProjectInfo", timeout=3)
            path = info.get("projectPath") or ""
            if "SafeBIM_Global_Library_Test_Projects".lower() in path.lower():
                hits.append((port, path))
        except Exception:
            pass
    if not hits:
        raise RuntimeError("target PLN not found on Tapir ports 19723..19730")
    for port, path in hits:
        if "план типовая" in path.lower():
            return port, path
    return hits[0]


def api(cmd: str, params: dict | None = None) -> dict:
    assert PORT is not None
    return call(PORT, cmd, params)


def E(guid: str) -> dict:
    return {"elementId": {"guid": guid}}


def live_rows() -> list[dict]:
    return api("GetAllElements").get("elements", [])


def live_guids() -> set[str]:
    return {
        row["elementId"]["guid"].lower()
        for row in live_rows()
        if row.get("elementId", {}).get("guid")
    }


def detail(guid: str) -> dict:
    rows = api("GetDetailsOfElements", {"elements": [E(guid)]}).get("detailsOfElements", [])
    if len(rows) != 1:
        raise RuntimeError(f"detail missing for {guid}")
    return rows[0]


def one_guid(result: dict, label: str) -> str:
    guids = [row.get("elementId", {}).get("guid") for row in result.get("elements", [])]
    guids = [g for g in guids if g]
    if len(guids) != 1:
        raise RuntimeError(f"{label}: expected one GUID, got {result}")
    return guids[0]


def save(m: dict) -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")


def add(m: dict, id_: str, type_: str, guid: str, meta: dict | None = None) -> str:
    row = {"id": id_, "type": type_, "guid": guid}
    if meta:
        row["meta"] = meta
    m["created"].append(row)
    save(m)
    return guid


def collect_our_guids() -> set[str]:
    out: set[str] = set()

    if SK.is_file():
        try:
            data = json.loads(SK.read_text(encoding="utf-8-sig"))
            if data.get("slabGuid"):
                out.add(data["slabGuid"])
            out.update(data.get("wallGuids", []))
        except Exception:
            pass

    # Collect only Series-178 evidence, including all previous emergency passes.
    if BASE.exists():
        for folder in BASE.glob("series178*"):
            if not folder.is_dir():
                continue
            for path in folder.rglob("*.json"):
                try:
                    data = json.loads(path.read_text(encoding="utf-8-sig"))
                except Exception:
                    continue
                if isinstance(data.get("guid"), str):
                    out.add(data["guid"])
                if isinstance(data.get("slabGuid"), str):
                    out.add(data["slabGuid"])
                out.update(g for g in data.get("wallGuids", []) if isinstance(g, str))
                out.update(g for g in data.get("dimensionGuids", []) if isinstance(g, str))
                for row in data.get("created", []):
                    if isinstance(row, dict) and isinstance(row.get("guid"), str):
                        out.add(row["guid"])

    return out


def cleanup(m: dict) -> None:
    current = live_guids()
    targets = [g for g in collect_our_guids() if g.lower() in current]
    priority = {
        "Zone": 0, "Text": 1, "Dimension": 2, "Polyline": 2, "Line": 2, "Arc": 2,
        "Window": 3, "Door": 3, "Stair": 4, "Slab": 5, "Wall": 6,
    }
    typed: list[tuple[int, str, str]] = []
    for g in targets:
        try:
            typ = detail(g).get("type", "")
        except Exception:
            typ = ""
        typed.append((priority.get(typ, 10), typ, g))
    typed.sort()

    for _, typ, g in typed:
        if g.lower() not in live_guids():
            continue
        try:
            api("DeleteElements", {"elements": [E(g)]})
        except Exception as exc:
            if g.lower() in live_guids():
                raise RuntimeError(f"cleanup failed for {typ} {g}: {exc}") from exc
        m["deleted"].append({"guid": g, "type": typ})
        save(m)


def wall(a: tuple[float, float], b: tuple[float, float], story: int,
         thickness: float, height: float = 2.84) -> str:
    return one_guid(api("CreateWalls", {"wallsData": [{
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
    }]}), "CreateWalls")


def slab(poly: list[tuple[float, float]], story: int, level: float,
         thickness: float = .16) -> str:
    return one_guid(api("CreateSlabs", {"slabsData": [{
        "level": level,
        "floorIndex": story,
        "thickness": thickness,
        "referencePlaneLocation": "Top",
        "polygonCoordinates": [{"x": x, "y": y} for x, y in poly],
    }]}), "CreateSlabs")


def window(host: str, offset: float, width: float = 1.50,
           height: float = 1.50, sill: float = .90) -> str:
    return one_guid(api("CreateWindows", {"windowsData": [{
        "ownerWallId": {"guid": host},
        "centerOffset": offset,
        "sillHeight": sill,
        "width": width,
        "height": height,
        "reflected": False,
        "refSide": False,
        "oSide": False,
    }]}), "CreateWindows")


def door(host: str, offset: float, width: float = .90,
         height: float = 2.10) -> str:
    return one_guid(api("CreateDoors", {"doorsData": [{
        "ownerWallId": {"guid": host},
        "centerOffset": offset,
        "sillHeight": 0.0,
        "width": width,
        "height": height,
        "reflected": False,
        "refSide": False,
        "oSide": False,
    }]}), "CreateDoors")


def polyline(points: list[tuple[float, float]], story: int,
             weight: float = .12) -> str:
    return one_guid(api("CreatePolylines", {"polylinesData": [{
        "floorInd": story,
        "linePenIndex": 1,
        "penWeightMm": weight,
        "roomSeparator": False,
        "coordinates": [{"x": x, "y": y} for x, y in points],
    }]}), "CreatePolylines")


def line(a: tuple[float, float], b: tuple[float, float], story: int,
         weight: float = .18) -> str:
    return polyline([a, b], story, weight)


def arc(origin: tuple[float, float], radius: float,
        a1: float, a2: float, story: int) -> str:
    return one_guid(api("CreateArcs", {"arcsData": [{
        "floorInd": story,
        "origin": {"x": origin[0], "y": origin[1]},
        "radius": radius,
        "begAngle": a1,
        "endAngle": a2,
        "linePenIndex": 1,
        "roomSeparator": False,
    }]}), "CreateArcs")


def stair(ox: float, oy: float, level: float, story: int) -> str:
    baseline = [
        {"x": ox + 11.00, "y": oy + 8.92},
        {"x": ox + 11.00, "y": oy + 12.55},
        {"x": ox + 13.18, "y": oy + 12.55},
        {"x": ox + 13.18, "y": oy + 8.92},
    ]
    return one_guid(api("CreateStairs", {"stairsData": [{
        "baseLinePoints": baseline,
        "zCoordinate": level,
        "floorIndex": story,
        "totalHeight": 3.0,
        "flightWidth": .95,
        "stepNum": 18,
        "riserHeight": 3.0 / 18.0,
        "treadDepth": .28,
    }]}), "CreateStairs")


def native_dimension(ref: tuple[float, float], direction: tuple[float, float],
                     story: int, witnesses: list[tuple[str, int]]) -> str:
    return one_guid(api("CreateAssociativeDimensions", {"dimensionsData": [{
        "referencePoint": {"x": ref[0], "y": ref[1]},
        "direction": {"x": direction[0], "y": direction[1]},
        "floorIndex": story,
        "witnessPoints": [
            {"elementId": {"guid": g}, "inIndex": idx}
            for g, idx in witnesses
        ],
    }]}), "CreateAssociativeDimensions")


def text(x: float, y: float, z: float, story: int,
         value: str, height: float = 1.8) -> str:
    return one_guid(api("CreateTexts", {"textsData": [{
        "coordinate": {"x": x, "y": y, "z": z},
        "text": value,
        "height": height,
        "pen": 1,
        "angle": 0.0,
        "justification": "Center",
        "floorIndex": story,
    }]}), "CreateTexts")


def door_symbol(m: dict, id_: str, hinge: tuple[float, float],
                direction: tuple[float, float], story: int,
                width: float = .80) -> None:
    # direction is the open leaf vector, normalized axis/diagonal is allowed.
    dx, dy = direction
    norm = math.hypot(dx, dy)
    dx, dy = dx / norm, dy / norm
    end = (hinge[0] + dx * width, hinge[1] + dy * width)
    add(m, id_ + "_LEAF", "Polyline", line(hinge, end, story, .18))


def main() -> None:
    global PORT

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()

    PORT, project_path = discover()
    if not SK.is_file():
        raise RuntimeError(f"missing origin manifest {SK}")

    sk = json.loads(SK.read_text(encoding="utf-8-sig"))
    ox = float(sk["originX"])
    oy = float(sk["originY"])

    stories = api("GetStories")
    story = int(sk.get("storyIndex", 0))
    if int(stories.get("actStory", -999)) != story:
        raise RuntimeError(f"active story {stories.get('actStory')} != {story}")
    sr = next(r for r in stories["stories"] if int(r["index"]) == story)
    level = float(sr.get("level", 0.0))

    m = {
        "status": "DRY_RUN" if not args.execute else "IN_PROGRESS",
        "port": PORT,
        "projectPath": project_path,
        "storyIndex": story,
        "origin": {"x": ox, "y": oy},
        "mode": "QUALITY_SOURCE_TRACE_BIM",
        "source": {
            "project": "178-07см.86",
            "rectifiedEnvelopeM": [23.4, 13.2],
            "gridXmm": [3000, 3600, 3000, 3600, 3600, 3600, 3000],
            "gridYmm": [5400, 2400, 5400],
        },
        "created": [],
        "deleted": [],
        "savedProject": False,
    }

    if not args.execute:
        print(json.dumps(m, ensure_ascii=False, indent=2))
        return

    save(m)
    cleanup(m)

    # Main slab.
    add(m, "SLAB_MAIN", "Slab",
        slab([(ox,oy),(ox+23.4,oy),(ox+23.4,oy+13.2),(ox,oy+13.2)], story, level))

    # Exterior walls are split only at verified modular axes so native dimensions
    # stay exact while the facade remains geometrically continuous.
    xs = [0.0, 3.0, 6.6, 9.6, 13.2, 16.8, 20.4, 23.4]
    ys = [0.0, 5.4, 7.8, 13.2]
    S: list[str] = []
    N: list[str] = []
    W: list[str] = []
    E_: list[str] = []

    for i in range(7):
        S.append(add(m, f"EXT_S_{i+1}", "Wall",
                     wall((ox+xs[i],oy),(ox+xs[i+1],oy),story,.30)))
        N.append(add(m, f"EXT_N_{i+1}", "Wall",
                     wall((ox+xs[i],oy+13.2),(ox+xs[i+1],oy+13.2),story,.30)))

    for i in range(3):
        W.append(add(m, f"EXT_W_{i+1}", "Wall",
                     wall((ox,oy+ys[i]),(ox,oy+ys[i+1]),story,.30)))
        E_.append(add(m, f"EXT_E_{i+1}", "Wall",
                      wall((ox+23.4,oy+ys[i]),(ox+23.4,oy+ys[i+1]),story,.30)))

    # Actual BIM interior walls from the photographed source trace.
    for i, seg in enumerate(REAL_WALLS, 1):
        x1,y1,x2,y2 = seg
        length = math.hypot(x2-x1, y2-y1)
        major = (
            length >= 3.0
            or abs(y1-7.64) < .12 or abs(y1-7.61) < .12
            or abs(y1-5.37) < .12
            or any(abs(x1-v) < .10 and abs(x2-v) < .10
                   for v in (3.30,6.94,10.69,13.58,17.15,20.53))
        )
        thickness = .15 if major else .08
        add(m, f"WALL_SRC_{i:02d}", "Wall",
            wall((ox+x1,oy+y1),(ox+x2,oy+y2),story,thickness),
            {"trace": [x1,y1,x2,y2], "thicknessStatus": "provisional"})

    # Source service/fixture trace. These are intentionally NOT Walls.
    real_set = set(REAL_WALLS)
    for i, seg in enumerate(TRACE, 1):
        if seg in OUTER_TRACE or seg in real_set:
            continue
        x1,y1,x2,y2 = seg
        add(m, f"DETAIL_SRC_{i:02d}", "Polyline",
            line((ox+x1,oy+y1),(ox+x2,oy+y2),story,.10),
            {"role": "source service/fixture detail, not wall"})

    # Connected stair landing + actual stair.
    add(m, "STAIR_LANDING", "Slab",
        slab([(ox+10.69,oy+7.64),(ox+13.58,oy+7.64),
              (ox+13.58,oy+8.90),(ox+10.69,oy+8.90)], story, level, .16))
    add(m, "STAIR", "Stair", stair(ox, oy, level, story))

    # Balcony geometry read from the same rectified source.
    balconies = [
        ("BAL_N_L", [(3.20,13.2),(3.20,14.88),(3.45,15.08),(6.60,15.08),(6.84,14.88),(6.84,13.2)]),
        ("BAL_N_R", [(16.30,13.2),(16.30,14.88),(16.55,15.08),(20.35,15.08),(20.60,14.88),(20.60,13.2)]),
        ("BAL_S_L", [(3.10,0.0),(3.10,-1.55),(3.35,-1.75),(7.20,-1.75),(7.45,-1.55),(7.45,0.0)]),
        ("BAL_S_R", [(16.40,0.0),(16.40,-1.55),(16.65,-1.75),(20.50,-1.75),(20.75,-1.55),(20.75,0.0)]),
    ]
    for name, poly in balconies:
        pts = [(ox+x,oy+y) for x,y in poly]
        add(m, name, "Slab", slab(pts, story, level, .16))
        # parapet only on the free perimeter (not along facade)
        for j in range(1, len(poly)-1):
            a = (ox+poly[j][0], oy+poly[j][1])
            b = (ox+poly[j+1][0], oy+poly[j+1][1])
            add(m, f"{name}_PAR_{j}", "Wall", wall(a,b,story,.10,1.05))

    # Facade openings. Their host grid is verified; sizes remain provisional.
    for i, length in enumerate([3.0,3.6,3.0,3.6,3.6,3.6,3.0]):
        if i in (1,5):
            add(m, f"S_BAL_DOOR_{i+1}", "Door", door(S[i], .70, .90, 2.10))
            add(m, f"S_BAL_WIN_{i+1}", "Window", window(S[i], 2.25, 1.35, 1.45, .90))
            add(m, f"N_BAL_DOOR_{i+1}", "Door", door(N[i], .70, .90, 2.10))
            add(m, f"N_BAL_WIN_{i+1}", "Window", window(N[i], 2.25, 1.35, 1.45, .90))
        else:
            add(m, f"S_WIN_{i+1}", "Window", window(S[i], length/2.0, 1.45, 1.50, .90))
            add(m, f"N_WIN_{i+1}", "Window", window(N[i], length/2.0, 1.45, 1.50, .90))

    # Source-style apartment entry leaves at the four visible entrances.
    door_symbol(m, "ENTRY_3B_L", (ox+6.94,oy+7.64), (-.70,-.55), story)
    door_symbol(m, "ENTRY_3B_R", (ox+17.08,oy+7.61), (.70,-.55), story)
    door_symbol(m, "ENTRY_2B", (ox+10.05,oy+5.37), (.60,.55), story)
    door_symbol(m, "ENTRY_1B", (ox+13.80,oy+5.37), (-.60,.55), story)

    # Native associative dimensions.
    xwit = [
        (S[0],1),(S[0],2),(S[1],2),(S[2],2),
        (S[3],2),(S[4],2),(S[5],2),(S[6],2),
    ]
    ywit = [(W[0],1),(W[0],2),(W[1],2),(W[2],2)]

    for id_, ref, direction, wit in [
        ("DIM_X_CHAIN",(ox,oy-2.20),(1.0,0.0),xwit),
        ("DIM_X_TOTAL",(ox,oy-3.00),(1.0,0.0),[xwit[0],xwit[-1]]),
        ("DIM_Y_CHAIN",(ox-2.20,oy),(0.0,1.0),ywit),
        ("DIM_Y_TOTAL",(ox-3.00,oy),(0.0,1.0),[ywit[0],ywit[-1]]),
    ]:
        add(m, id_, "Dimension", native_dimension(ref,direction,story,wit))

    # Axis labels.
    for label, x in zip(["1с","2с","3с","4с","6с","7с","8с","9с"], xs):
        add(m, f"AX_X_{label}", "Text", text(ox+x,oy-3.45,level,story,label,1.6))
    for label, y in zip(["А","Б","В","Г"], ys):
        add(m, f"AX_Y_{label}", "Text", text(ox-3.45,oy+y,level,story,label,1.6))

    # Source labels, deliberately smaller than earlier passes.
    room_labels = [
        ("11,25",1.45,12.15),("8,76",4.75,12.10),("17,96",8.45,11.95),
        ("17,96",15.05,11.95),("8,76",18.70,12.10),("11,25",22.00,12.15),
        ("12,38",1.45,1.05),("8,76",4.75,1.05),("10,39",8.50,1.05),
        ("17,96",11.85,1.05),("17,96",15.15,1.05),("8,76",18.75,1.05),
        ("12,38",22.05,1.05),("6,19",11.85,6.45),
    ]
    for i,(value,x,y) in enumerate(room_labels,1):
        add(m, f"AREA_{i:02d}", "Text", text(ox+x,oy+y,level,story,value,1.7))

    apartment_labels = [
        ("3Б\n41,59 / 70,87",8.55,10.05),
        ("3Б\n41,59 / 70,87",15.05,10.05),
        ("2Б\n28,35 / 53,27",11.25,4.25),
        ("1Б\n17,96 / 38,43",15.15,4.25),
    ]
    for i,(value,x,y) in enumerate(apartment_labels,1):
        add(m, f"APT_{i}", "Text", text(ox+x,oy+y,level,story,value,2.0))

    m["status"] = "PASS"
    m["elementCountAfter"] = len(live_rows())
    m["qualityNotes"] = {
        "wallGeometry": "source-traced",
        "fixtures": "thin 2D trace, never promoted to walls",
        "grid": "verified 23400 x 13200",
        "wallThicknesses": "provisional 300/150/80 mm",
        "openingSizes": "provisional",
    }
    m["nextPhase"] = "visual compare against passport; correct only measured mismatches"
    save(m)

    try:
        api("FitInWindow", {})
    except Exception:
        pass

    print(json.dumps(m, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(json.dumps({
            "status": "BLOCKED",
            "error": str(exc),
            "evidence": str(OUT),
            "note": "do not rerun blindly; inspect manifest first",
        }, ensure_ascii=False, indent=2))
        raise SystemExit(2)
