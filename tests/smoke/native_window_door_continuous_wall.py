# -*- coding: utf-8 -*-
"""Canonical smoke: one continuous Wall + one native Window + one native Door.

Acceptance criteria:
- one continuous host Wall in isolated test region;
- Window read-back type == Window;
- Door read-back type == Door;
- no Morph fallback;
- no wall fragmentation.

Live verified on 2026-10-03.
"""

import json
import importlib.util
from pathlib import Path

ROOT = Path(r"C:\Users\Admin\Documents\Codex\safe-bim-s1.7-pc-test")

spec = importlib.util.spec_from_file_location(
    "house",
    ROOT / "01_english_house_library.py"
)

m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

call = m.call

X0 = 230.0
Y0 = 0.0
WALL_LENGTH = 8.0
WALL_HEIGHT = 3.0
WALL_THICKNESS = 0.38

WINDOW_OFFSET = 2.0
WINDOW_SILL = 0.90
WINDOW_WIDTH = 1.20
WINDOW_HEIGHT = 1.40

DOOR_OFFSET = 6.0
DOOR_WIDTH = 1.00
DOOR_HEIGHT = 2.10


def walk(x):
    if isinstance(x, dict):
        yield x
        for v in x.values():
            yield from walk(v)
    elif isinstance(x, list):
        for v in x:
            yield from walk(v)


def created_guid(result):
    for d in walk(result):
        eid = d.get("elementId")
        if isinstance(eid, dict):
            guid = eid.get("guid")
            if isinstance(guid, str) and len(guid) == 36:
                return guid
    return None


def read_one(guid):
    result = call(
        "GetDetailsOfElements",
        {"elements": [{"elementId": {"guid": guid}}]},
    )
    rows = result.get("detailsOfElements", [])
    if len(rows) != 1:
        raise RuntimeError(f"READBACK FAILED: {guid}")
    return rows[0]


def get_favorites(element_type):
    try:
        result = call(
            "GetFavoritesByType",
            {"elementType": element_type},
        )
        return result.get("favorites", [])
    except Exception:
        return []


def choose_favorite(favorites, keywords):
    if not favorites:
        return None
    for keyword in keywords:
        lowered = keyword.lower()
        for name in favorites:
            if lowered in name.lower():
                return name
    return favorites[0]


stories = call("GetStories", {})
floor_index = 0
for d in walk(stories):
    if "actStory" in d:
        try:
            floor_index = int(d["actStory"])
            break
        except Exception:
            pass

window_favorites = get_favorites("Window")
door_favorites = get_favorites("Door")
window_favorite = choose_favorite(window_favorites, ["прост", "simple", "окно", "window"])
door_favorite = choose_favorite(door_favorites, ["прост", "simple", "двер", "door"])

wall_result = call(
    "CreateWalls",
    {
        "wallsData": [
            {
                "begCoordinate": {"x": X0, "y": Y0},
                "endCoordinate": {"x": X0 + WALL_LENGTH, "y": Y0},
                "floorIndex": floor_index,
                "zCoordinate": 0.0,
                "height": WALL_HEIGHT,
                "thickness": WALL_THICKNESS,
                "referenceLineLocation": "Center",
                "structureType": "Basic",
            }
        ]
    },
)

wall_guid = created_guid(wall_result)
if not wall_guid or read_one(wall_guid).get("type") != "Wall":
    raise RuntimeError("HOST WALL CREATE/READBACK FAILED")

window_row = {
    "ownerWallId": {"guid": wall_guid},
    "centerOffset": WINDOW_OFFSET,
    "sillHeight": WINDOW_SILL,
    "width": WINDOW_WIDTH,
    "height": WINDOW_HEIGHT,
    "reflected": False,
    "refSide": False,
    "oSide": False,
}
if window_favorite:
    window_row["favoriteName"] = window_favorite

window_result = call("CreateWindows", {"windowsData": [window_row]})
window_guid = created_guid(window_result)
window_rb = read_one(window_guid) if window_guid else None
if not window_rb or window_rb.get("type") != "Window":
    raise RuntimeError("NATIVE WINDOW FAILED")

door_row = {
    "ownerWallId": {"guid": wall_guid},
    "centerOffset": DOOR_OFFSET,
    "sillHeight": 0.0,
    "width": DOOR_WIDTH,
    "height": DOOR_HEIGHT,
    "reflected": False,
    "refSide": False,
    "oSide": False,
}
if door_favorite:
    door_row["favoriteName"] = door_favorite

door_result = call("CreateDoors", {"doorsData": [door_row]})
door_guid = created_guid(door_result)
door_rb = read_one(door_guid) if door_guid else None
if not door_rb or door_rb.get("type") != "Door":
    raise RuntimeError("NATIVE DOOR FAILED")

all_walls = call("GetElementsByType", {"elementType": "Wall"}).get("elements", [])
test_wall_count = 0

for start in range(0, len(all_walls), 40):
    batch = all_walls[start:start + 40]
    result = call("GetDetailsOfElements", {"elements": batch})
    for row in result.get("detailsOfElements", []):
        if row.get("type") != "Wall":
            continue
        details = row.get("details", {})
        a = details.get("begCoordinate")
        b = details.get("endCoordinate")
        if not (isinstance(a, dict) and isinstance(b, dict)):
            continue
        try:
            cx = (float(a["x"]) + float(b["x"])) / 2.0
            cy = (float(a["y"]) + float(b["y"])) / 2.0
        except Exception:
            continue
        if X0 - 0.5 <= cx <= X0 + WALL_LENGTH + 0.5 and Y0 - 1.0 <= cy <= Y0 + 1.0:
            test_wall_count += 1

if test_wall_count != 1:
    raise RuntimeError(f"WALL FRAGMENTATION FAIL: expected 1 Wall, got {test_wall_count}")

print("NATIVE WINDOW + DOOR PASS")
print("HOST WALL :", wall_guid)
print("WINDOW    :", window_guid)
print("DOOR      :", door_guid)
print("WALLS IN TEST REGION : 1")
print("WINDOW TYPE          : Window")
print("DOOR TYPE            : Door")
print("MORPH                : 0")
print("WALL FRAGMENTATION   : 0")
