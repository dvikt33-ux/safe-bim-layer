# -*- coding: utf-8 -*-
"""Canonical live smoke for a Basic Slab via a verified Archicad Favorite.

Verified on 2026-10-03 against Archicad/Tapir.
Expected canonical result:
- favorite: Перекрытие - Общее Железобетонное
- type: Slab
- structureType: Basic
- absolute Z: 3.00 m
- read-back home story: index 1 at 3.00 m
- read-back slab level: 0.00 m (story-relative)
- thickness: 0.22 m
- referencePlaneLocation: Top
- outline: 6.00 x 4.00 m

Important: CreateSlabs must not receive buildingMaterialId. Favorite establishes a
Basic slab; explicit geometry/thickness then overrides the favorite geometry.
"""

import json
import importlib.util
from pathlib import Path

ROOT = Path(r"C:\Users\Admin\Documents\Codex\safe-bim-s1.7-pc-test")
spec = importlib.util.spec_from_file_location("house", ROOT / "01_english_house_library.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
call = m.call

FAVORITE = "Перекрытие - Общее Железобетонное"
TARGET_Z = 3.0
TARGET_T = 0.22
X0, Y0 = 255.0, 0.0
W, D = 6.0, 4.0
TOL = 1e-6


def walk(x):
    if isinstance(x, dict):
        yield x
        for v in x.values():
            yield from walk(v)
    elif isinstance(x, list):
        for v in x:
            yield from walk(v)


def guid_from(result):
    for d in walk(result):
        eid = d.get("elementId")
        if isinstance(eid, dict):
            g = eid.get("guid")
            if isinstance(g, str) and len(g) == 36:
                return g
    return None


def almost(a, b):
    return abs(float(a) - float(b)) <= TOL


def read_one(guid):
    r = call("GetDetailsOfElements", {"elements": [{"elementId": {"guid": guid}}]})
    rows = r.get("detailsOfElements", [])
    if len(rows) != 1:
        raise RuntimeError("read-back failed")
    return rows[0]


stories = call("GetStories", {}).get("stories", [])
story_levels = {int(s["index"]): float(s["level"]) for s in stories}

payload = {
    "slabsData": [{
        "favoriteName": FAVORITE,
        "level": TARGET_Z,
        "thickness": TARGET_T,
        "referencePlaneLocation": "Top",
        "polygonCoordinates": [
            {"x": X0,     "y": Y0},
            {"x": X0 + W, "y": Y0},
            {"x": X0 + W, "y": Y0 + D},
            {"x": X0,     "y": Y0 + D},
        ],
    }]
}

result = call("CreateSlabs", payload)
guid = guid_from(result)
if not guid:
    raise RuntimeError(json.dumps(result, ensure_ascii=False, indent=2))

row = read_one(guid)
if row.get("type") != "Slab":
    raise RuntimeError(f"expected Slab, got {row.get('type')}")

d = row.get("details", {})
floor_index = int(row.get("floorIndex", 0))
story_z = story_levels.get(floor_index)
raw_level = float(d.get("level"))

if d.get("structureType") != "Basic":
    raise RuntimeError(f"structureType={d.get('structureType')}")
if not almost(d.get("thickness"), TARGET_T):
    raise RuntimeError(f"thickness={d.get('thickness')}")
if d.get("referencePlaneLocation") != "Top":
    raise RuntimeError(f"referencePlaneLocation={d.get('referencePlaneLocation')}")
if story_z is None or not almost(story_z + raw_level, TARGET_Z):
    raise RuntimeError(f"elevation mismatch: story={story_z}, level={raw_level}")

outline = d.get("polygonOutline", [])
xs = [float(p["x"]) for p in outline if isinstance(p, dict) and "x" in p]
ys = [float(p["y"]) for p in outline if isinstance(p, dict) and "y" in p]
if not xs or not ys or not almost(max(xs)-min(xs), W) or not almost(max(ys)-min(ys), D):
    raise RuntimeError("outline mismatch")

print("BASIC SLAB FAVORITE PASS")
print("GUID:", guid)
print("FAVORITE:", FAVORITE)
print("STRUCTURE: Basic")
print("ABS Z:", TARGET_Z)
print("HOME STORY:", floor_index, story_z)
print("READBACK LEVEL:", raw_level, "(story-relative)")
print("THICKNESS:", d.get("thickness"))
print("REFERENCE:", d.get("referencePlaneLocation"))
print("SIZE:", max(xs)-min(xs), "x", max(ys)-min(ys))
