"""Series 178-07sm.86 CLEAN REBUILD — one-shot submission floor.

Hard-resets only elements created by our Series 178 scripts (from evidence GUIDs),
then rebuilds one clean typical floor from the photographed passport:
- verified 23400 x 13200 modular grid;
- split transverse bearing walls and 2400 corridor;
- central stair bay with landing connected to corridor;
- main room/service partitions;
- facade windows, balcony doors and 4 balcony slabs;
- apartment/internal doors;
- native Archicad associative dimensions;
- room-area and apartment labels;
- NO Zone elements / blue crosses.

Never opens/switches/saves/closes the PLN.
"""
from __future__ import annotations
import argparse
import json
import os
import tempfile
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(tempfile.gettempdir())
BASE = Path(os.environ.get("SAFE_BIM_MVP_EVIDENCE", ROOT / "safe-bim-mvp-evidence"))
SK = ROOT / "series178-direct-19725-created.json"
OUT = BASE / "series178-CLEAN" / "manifest.json"
PORT: int | None = None

EVIDENCE_FILES = [
    BASE / "series178-v02" / "stair.json",
    BASE / "series178-v02" / "stair-access.json",
    BASE / "series178-v03" / "manifest.json",
    BASE / "series178-v04" / "manifest.json",
    BASE / "series178-v05" / "manifest.json",
    BASE / "series178-v06" / "manifest.json",
    BASE / "series178-v07" / "manifest.json",
    BASE / "series178-v08" / "manifest.json",
    BASE / "series178-FINAL" / "manifest.json",
]


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
    rows = api("GetDetailsOfElements", {"elements": [E(guid)]}).get(
        "detailsOfElements", []
    )
    if len(rows) != 1:
        raise RuntimeError(f"detail missing for {guid}")
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
        sk = json.loads(SK.read_text(encoding="utf-8-sig"))
        if sk.get("slabGuid"):
            out.add(sk["slabGuid"])
        out.update(sk.get("wallGuids", []))

    for path in EVIDENCE_FILES:
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
        except Exception:
            continue

        g = data.get("guid")
        if isinstance(g, str):
            out.add(g)

        for row in data.get("created", []):
            g = row.get("guid") if isinstance(row, dict) else None
            if g:
                out.add(g)

        for g in data.get("dimensionGuids", []):
            if isinstance(g, str):
                out.add(g)

    if OUT.is_file():
        try:
            data = json.loads(OUT.read_text(encoding="utf-8-sig"))
            for row in data.get("created", []):
                g = row.get("guid")
                if g:
                    out.add(g)
        except Exception:
            pass
    return out


def delete_our_live_elements(m: dict) -> None:
    targets = collect_our_guids()
    live = live_guids()
    active = [g for g in targets if g.lower() in live]

    priority = {
        "Zone": 0, "Text": 1, "Dimension": 2, "Window": 3, "Door": 3,
        "Stair": 4, "Slab": 5, "Wall": 6,
    }
    typed: list[tuple[int, str, str]] = []
    for g in active:
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


def wall(
    a: tuple[float, float],
    b: tuple[float, float],
    story: int,
    thickness: float,
    height: float = 2.84,
) -> str:
    result = api("CreateWalls", {"wallsData": [{
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
    }]})
    g = one_guid(result, "CreateWalls")
    d = detail(g)
    if d.get("type") != "Wall":
        raise RuntimeError(f"wall read-back failed {g}")
    return g


def slab(
    polygon: list[tuple[float, float]],
    story: int,
    level: float,
    thickness: float = 0.16,
) -> str:
    result = api("CreateSlabs", {"slabsData": [{
        "level": level,
        "floorIndex": story,
        "thickness": thickness,
        "referencePlaneLocation": "Top",
        "polygonCoordinates": [{"x": x, "y": y} for x, y in polygon],
    }]})
    g = one_guid(result, "CreateSlabs")
    if detail(g).get("type") != "Slab":
        raise RuntimeError(f"slab read-back failed {g}")
    return g


def window(host: str, offset: float, width: float, height: float = 1.50, sill: float = .90) -> str:
    result = api("CreateWindows", {"windowsData": [{
        "ownerWallId": {"guid": host},
        "centerOffset": offset,
        "sillHeight": sill,
        "width": width,
        "height": height,
        "reflected": False,
        "refSide": False,
        "oSide": False,
    }]})
    g = one_guid(result, "CreateWindows")
    if detail(g).get("type") != "Window":
        raise RuntimeError(f"window read-back failed {g}")
    return g


def door(host: str, offset: float, width: float = .80, height: float = 2.05) -> str:
    result = api("CreateDoors", {"doorsData": [{
        "ownerWallId": {"guid": host},
        "centerOffset": offset,
        "sillHeight": 0.0,
        "width": width,
        "height": height,
        "reflected": False,
        "refSide": False,
        "oSide": False,
    }]})
    g = one_guid(result, "CreateDoors")
    if detail(g).get("type") != "Door":
        raise RuntimeError(f"door read-back failed {g}")
    return g


def stair(ox: float, oy: float, level: float, story: int) -> str:
    baseline = [
        {"x": ox + 10.05, "y": oy + 8.25},
        {"x": ox + 10.05, "y": oy + 12.75},
        {"x": ox + 12.75, "y": oy + 12.75},
        {"x": ox + 12.75, "y": oy + 8.25},
    ]
    result = api("CreateStairs", {"stairsData": [{
        "baseLinePoints": baseline,
        "zCoordinate": level,
        "floorIndex": story,
        "totalHeight": 3.0,
        "flightWidth": 1.05,
        "stepNum": 18,
        "riserHeight": 3.0 / 18.0,
        "treadDepth": .28,
    }]})
    g = one_guid(result, "CreateStairs")
    if detail(g).get("type") != "Stair":
        raise RuntimeError(f"stair read-back failed {g}")
    return g


def native_dimension(
    ref: tuple[float, float],
    direction: tuple[float, float],
    story: int,
    witnesses: list[tuple[str, int]],
) -> str:
    result = api("CreateAssociativeDimensions", {"dimensionsData": [{
        "referencePoint": {"x": ref[0], "y": ref[1]},
        "direction": {"x": direction[0], "y": direction[1]},
        "floorIndex": story,
        "witnessPoints": [
            {"elementId": {"guid": g}, "inIndex": idx}
            for g, idx in witnesses
        ],
    }]})
    g = one_guid(result, "CreateAssociativeDimensions")
    if detail(g).get("type") != "Dimension":
        raise RuntimeError(f"dimension read-back failed {g}")
    return g


def text(x: float, y: float, z: float, story: int, value: str, height: float = 2.4) -> str:
    result = api("CreateTexts", {"textsData": [{
        "coordinate": {"x": x, "y": y, "z": z},
        "text": value,
        "height": height,
        "pen": 1,
        "angle": 0.0,
        "justification": "Center",
        "floorIndex": story,
    }]})
    return one_guid(result, "CreateTexts")


def main() -> None:
    global PORT

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()

    PORT, project_path = discover()

    if not SK.is_file():
        raise RuntimeError(f"missing skeleton origin manifest {SK}")
    sk = json.loads(SK.read_text(encoding="utf-8-sig"))
    ox = float(sk["originX"])
    oy = float(sk["originY"])

    stories = api("GetStories")
    story = int(sk.get("storyIndex", 0))
    if int(stories.get("actStory", -999)) != story:
        raise RuntimeError(f"active story {stories.get('actStory')} != {story}")
    story_row = next(r for r in stories["stories"] if int(r["index"]) == story)
    level = float(story_row.get("level", 0.0))

    plan = {
        "status": "DRY_RUN" if not args.execute else "IN_PROGRESS",
        "port": PORT,
        "projectPath": project_path,
        "storyIndex": story,
        "origin": {"x": ox, "y": oy},
        "verifiedGrid": {
            "xMm": [3000,3600,3000,3600,3600,3600,3000],
            "xOverallMm": 23400,
            "yMm": [5400,2400,5400],
            "yOverallMm": 13200,
        },
        "created": [],
        "deleted": [],
        "savedProject": False,
    }

    if not args.execute:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return

    save(plan)
    delete_our_live_elements(plan)

    W: dict[str, str] = {}

    g = slab(
        [(ox,oy),(ox+23.4,oy),(ox+23.4,oy+13.2),(ox,oy+13.2)],
        story, level,
    )
    add(plan, "SLAB_MAIN", "Slab", g)

    xs = [0.0,3.0,6.6,9.6,13.2,16.8,20.4,23.4]
    xnames = ["01","02","03","04","05","06","07"]

    for i, name in enumerate(xnames):
        a = xs[i]; b = xs[i+1]
        W[f"S{name}"] = add(
            plan, f"EXT_S_{name}", "Wall",
            wall((ox+a,oy),(ox+b,oy),story,.35)
        )
        W[f"N{name}"] = add(
            plan, f"EXT_N_{name}", "Wall",
            wall((ox+a,oy+13.2),(ox+b,oy+13.2),story,.35)
        )

    yspans = [(0.0,5.4),(5.4,7.8),(7.8,13.2)]
    for i,(a,b) in enumerate(yspans,1):
        W[f"W{i}"] = add(
            plan, f"EXT_W_{i}", "Wall",
            wall((ox,oy+a),(ox,oy+b),story,.35)
        )
        W[f"E{i}"] = add(
            plan, f"EXT_E_{i}", "Wall",
            wall((ox+23.4,oy+a),(ox+23.4,oy+b),story,.35)
        )

    axis_x = {
        "X2":3.0, "X3":6.6, "X4":9.6,
        "X6":13.2, "X7":16.8, "X8":20.4,
    }
    for key,x in axis_x.items():
        W[f"{key}S"] = add(
            plan, f"{key}_S", "Wall",
            wall((ox+x,oy),(ox+x,oy+5.4),story,.16)
        )
        W[f"{key}N"] = add(
            plan, f"{key}_N", "Wall",
            wall((ox+x,oy+7.8),(ox+x,oy+13.2),story,.16)
        )

    W["CORE_S"] = add(
        plan, "CORE_S", "Wall",
        wall((ox+6.6,oy+5.4),(ox+16.8,oy+5.4),story,.16)
    )
    W["CORE_N_L"] = add(
        plan, "CORE_N_L", "Wall",
        wall((ox+6.6,oy+7.8),(ox+10.0,oy+7.8),story,.16)
    )
    W["CORE_N_R"] = add(
        plan, "CORE_N_R", "Wall",
        wall((ox+12.8,oy+7.8),(ox+16.8,oy+7.8),story,.16)
    )

    partitions = [
        ("S_OUT_L",(0.0,4.10),(3.0,4.10)),
        ("S_KIT_L",(3.0,2.45),(6.6,2.45)),
        ("S_ROOM_2B",(6.6,3.45),(9.6,3.45)),
        ("S_KIT_R",(16.8,2.45),(20.4,2.45)),
        ("S_OUT_R",(20.4,4.10),(23.4,4.10)),
        ("N_OUT_L",(0.0,9.45),(3.0,9.45)),
        ("N_KIT_L",(3.0,10.75),(6.6,10.75)),
        ("N_KIT_R",(16.8,10.75),(20.4,10.75)),
        ("N_OUT_R",(20.4,9.45),(23.4,9.45)),
        ("LS_H1",(0.0,4.75),(3.0,4.75)),
        ("LS_V1",(1.15,4.10),(1.15,5.40)),
        ("LS_HALL_H",(3.0,4.15),(6.6,4.15)),
        ("LS_HALL_V",(4.55,2.45),(4.55,5.40)),
        ("LS_2B_H",(6.6,4.35),(9.6,4.35)),
        ("LS_2B_V",(7.40,4.35),(7.40,5.40)),
        ("RS_H1",(20.4,4.75),(23.4,4.75)),
        ("RS_V1",(22.25,4.10),(22.25,5.40)),
        ("RS_HALL_H",(16.8,4.15),(20.4,4.15)),
        ("RS_HALL_V",(18.85,2.45),(18.85,5.40)),
        ("RS_1B_V",(15.95,4.35),(15.95,5.40)),
        ("LN_H1",(0.0,8.65),(3.0,8.65)),
        ("LN_V1",(1.15,7.80),(1.15,9.45)),
        ("LN_HALL_H",(3.0,9.55),(6.6,9.55)),
        ("LN_HALL_V",(4.55,7.80),(4.55,10.75)),
        ("RN_H1",(20.4,8.65),(23.4,8.65)),
        ("RN_V1",(22.25,7.80),(22.25,9.45)),
        ("RN_HALL_H",(16.8,9.55),(20.4,9.55)),
        ("RN_HALL_V",(18.85,7.80),(18.85,10.75)),
    ]
    for id_,a,b in partitions:
        W[id_] = add(
            plan,id_,"Wall",
            wall((ox+a[0],oy+a[1]),(ox+b[0],oy+b[1]),story,.08),
            {"status":"passport-traced/provisional service detail"}
        )

    landing = slab(
        [(ox+10.0,oy+7.80),(ox+12.8,oy+7.80),
         (ox+12.8,oy+8.55),(ox+10.0,oy+8.55)],
        story, level, .16,
    )
    add(plan,"STAIR_LANDING","Slab",landing)

    sg = stair(ox,oy,level,story)
    add(plan,"STAIR","Stair",sg)

    for key,length in [
        ("S01",3.0),("S03",3.0),("S04",3.6),("S05",3.6),("S07",3.0),
        ("N01",3.0),("N03",3.0),("N04",3.6),("N05",3.6),("N07",3.0),
    ]:
        wg = window(W[key], length/2.0, 1.50, 1.50, .90)
        add(plan,f"WIN_{key}","Window",wg)

    for key in ["S02","S06","N02","N06"]:
        dg = door(W[key], .75, .90, 2.10)
        add(plan,f"BAL_DOOR_{key}","Door",dg)
        wg = window(W[key], 2.35, 1.40, 1.45, .90)
        add(plan,f"BAL_WIN_{key}","Window",wg)

    balcony_polys = [
        ("BAL_S_L",[(3.0,0.0),(6.6,0.0),(6.6,-1.2),(3.0,-1.2)]),
        ("BAL_S_R",[(16.8,0.0),(20.4,0.0),(20.4,-1.2),(16.8,-1.2)]),
        ("BAL_N_L",[(3.0,13.2),(6.6,13.2),(6.6,14.4),(3.0,14.4)]),
        ("BAL_N_R",[(16.8,13.2),(20.4,13.2),(20.4,14.4),(16.8,14.4)]),
    ]
    for id_,poly in balcony_polys:
        bg = slab([(ox+x,oy+y) for x,y in poly],story,level,.16)
        add(plan,id_,"Slab",bg)

    for id_,host,off,width in [
        ("ENTRY_3B_L",W["CORE_N_L"],1.55,.90),
        ("ENTRY_3B_R",W["CORE_N_R"],2.45,.90),
        ("ENTRY_2B",W["CORE_S"],2.15,.90),
        ("ENTRY_1B",W["CORE_S"],7.65,.90),
        ("D_X2_S",W["X2S"],3.25,.80),
        ("D_X3_S",W["X3S"],2.95,.80),
        ("D_X4_S",W["X4S"],2.60,.80),
        ("D_X6_S",W["X6S"],2.60,.80),
        ("D_X7_S",W["X7S"],2.95,.80),
        ("D_X8_S",W["X8S"],3.25,.80),
        ("D_X2_N",W["X2N"],2.15,.80),
        ("D_X3_N",W["X3N"],1.75,.80),
        ("D_X7_N",W["X7N"],1.75,.80),
        ("D_X8_N",W["X8N"],2.15,.80),
        ("D_KIT_S_L",W["S_KIT_L"],1.70,.80),
        ("D_ROOM_2B",W["S_ROOM_2B"],1.55,.80),
        ("D_KIT_S_R",W["S_KIT_R"],1.70,.80),
        ("D_KIT_N_L",W["N_KIT_L"],1.70,.80),
        ("D_KIT_N_R",W["N_KIT_R"],1.70,.80),
    ]:
        dg = door(host,off,width,2.05)
        add(plan,id_,"Door",dg)

    x_witnesses = [
        (W["S01"],1),(W["S01"],2),(W["S02"],2),(W["S03"],2),
        (W["S04"],2),(W["S05"],2),(W["S06"],2),(W["S07"],2),
    ]
    y_witnesses = [
        (W["W1"],1),(W["W1"],2),(W["W2"],2),(W["W3"],2),
    ]

    dims = [
        ("DIM_X_CHAIN",(ox,oy-1.80),(1.0,0.0),x_witnesses),
        ("DIM_X_TOTAL",(ox,oy-2.70),(1.0,0.0),[x_witnesses[0],x_witnesses[-1]]),
        ("DIM_Y_CHAIN",(ox-1.80,oy),(0.0,1.0),y_witnesses),
        ("DIM_Y_TOTAL",(ox-2.70,oy),(0.0,1.0),[y_witnesses[0],y_witnesses[-1]]),
    ]
    for id_,ref,direction,wit in dims:
        dg = native_dimension(ref,direction,story,wit)
        add(plan,id_,"Dimension",dg)

    room_labels = [
        ("11,25",1.50,11.80),("8,76",4.80,11.80),("17,96",8.10,11.60),
        ("17,96",15.00,11.60),("8,76",18.60,11.80),("11,25",21.90,11.80),
        ("12,38",1.50,1.30),("8,76",4.80,1.30),("10,39",8.10,1.30),
        ("17,96",11.40,1.30),("17,96",15.00,1.30),("8,76",18.60,1.30),
        ("12,38",21.90,1.30),("6,19",11.40,6.60),
    ]
    for i,(value,x,y) in enumerate(room_labels,1):
        tg = text(ox+x,oy+y,level,story,value,2.4)
        add(plan,f"ROOM_AREA_{i:02d}","Text",tg)

    apartment_labels = [
        ("3Б  41,59 / 70,87",8.05,9.90),
        ("3Б  41,59 / 70,87",14.75,9.90),
        ("2Б  28,35 / 53,27",10.20,4.65),
        ("1Б  17,96 / 38,43",14.45,4.65),
    ]
    for i,(value,x,y) in enumerate(apartment_labels,1):
        tg = text(ox+x,oy+y,level,story,value,3.0)
        add(plan,f"APT_{i}","Text",tg)

    plan["status"] = "PASS"
    plan["elementCountAfter"] = len(live_rows())
    plan["nextPhase"] = "visual QA + manual save/print; no more staged rebuilds"
    save(plan)

    try:
        api("FitInWindow", {})
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
            "note": "do not rerun blindly; CLEAN manifest records every created GUID",
        }, ensure_ascii=False, indent=2))
        raise SystemExit(2)
