from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WORK_ROOT = Path(r"C:\Users\Admin\Documents\Codex\safe-bim-s1.7-pc-test")
sys.path.insert(0, str(WORK_ROOT))

SCHEMA = WORK_ROOT / "tapir-1.5.9.json"
BRIDGE = "http://127.0.0.1:19723"
STATE_FILE = WORK_ROOT / "sb_gothic_lancet_large_v01_master_state.json"
TOWER_STATE = WORK_ROOT / "gothic_tower_top_stage_state.json"

COMPONENT_ID = "SB_GOTHIC_LANCET_LARGE_V01"
FLOOR_INDEX = 0

# Dedicated component workbench, far away from current model.
OX = 500.0
OY = 500.0

# Window authored flat on XY plane. When saved as Window choose Horizontal Plane
# as the host-wall/elevation plane.
OPENING_WIDTH = 1.48
RECT_HEIGHT = 2.70
ARCH_RISE = 1.62
FRAME = 0.17

# Depth around the future host-wall plane Z=0.
FRAME_TOP = 0.12
FRAME_THICKNESS = 0.24
GLASS_TOP = 0.015
GLASS_THICKNESS = 0.030

# Graphisoft placement rule: Wallhole slab top at Z=0.0.
WALLHOLE_TOP = 0.0
WALLHOLE_THICKNESS = 0.80

# ---------- Safe BIM policy ----------
import safe_bim_command_policy as policy

policy.READ_ONLY_COMMANDS = frozenset(
    set(policy.READ_ONLY_COMMANDS)
    | {"GetSelectedElements"}
)

for command in ("CreateSlabs", "ChangeSelectionOfElements"):
    policy._EXPLICIT[command] = policy.CommandClass.MODEL_MUTATION

policy.ADMITTED_MODEL_COMMANDS = frozenset(
    set(policy.ADMITTED_MODEL_COMMANDS)
    | {"CreateSlabs", "ChangeSelectionOfElements"}
)
policy._CREATE_ARRAY_FIELDS["CreateSlabs"] = "slabsData"

import importlib
from safe_bim_layer import TapirClient, SafeBIMLayer

gateway_module = importlib.import_module("safe_bim_mutation_gateway")
gateway_module = importlib.reload(gateway_module)
MutationGateway = gateway_module.MutationGateway

client = TapirClient(BRIDGE, str(SCHEMA))
gateway = MutationGateway(client)
bim = SafeBIMLayer(client, gateway=gateway)


def response_body(response):
    value = response.get("result", {}).get("addOnCommandResponse", {})
    return value if isinstance(value, dict) else {}


def read_one(guid: str):
    response = client.call(
        "GetDetailsOfElements",
        {"elements": [{"elementId": {"guid": guid}}]},
    )
    rows = response_body(response).get("detailsOfElements", [])
    if len(rows) != 1:
        raise RuntimeError(f"read-back {guid}: rows={len(rows)}")
    return rows[0]


def inventory(element_type: str):
    response = client.call("GetElementsByType", {"elementType": element_type})
    out = {}
    for item in response_body(response).get("elements", []):
        try:
            guid = item["elementId"]["guid"]
        except Exception:
            continue
        out[guid.lower()] = guid
    return out


def response_guids(response):
    result = []
    body = response_body(response)
    for row in body.get("executionResults", []):
        if isinstance(row, dict) and row.get("success") is False:
            raise RuntimeError(json.dumps(row, ensure_ascii=False, indent=2))
    for row in body.get("elements", []):
        if "error" in row:
            raise RuntimeError(json.dumps(row["error"], ensure_ascii=False, indent=2))
        try:
            result.append(row["elementId"]["guid"])
        except Exception:
            pass
    return result


def mutate(command: str, payload: dict, floor_index=None):
    client.validate_payload(command, payload)
    gateway.begin_step(command)
    try:
        if floor_index is not None:
            bim.ensure_active_story(floor_index)
        response = gateway.dispatch(command, payload)
    finally:
        gateway.end_step()
    return response


def load_state():
    if not STATE_FILE.exists():
        return {
            "componentId": COMPONENT_ID,
            "steps": {},
            "allGuids": [],
            "materialRoleMap": {},
        }
    state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    if state.get("componentId") != COMPONENT_ID:
        raise RuntimeError("State belongs to another component")
    return state


state = load_state()


def save_state():
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(STATE_FILE)


# Reuse the persisted role mapping established by the tower experiment.
if not state.get("materialRoleMap") and TOWER_STATE.exists():
    tower = json.loads(TOWER_STATE.read_text(encoding="utf-8"))
    state["materialRoleMap"] = tower.get("materialRoleMap", {})
    save_state()


def bm(role: str):
    entry = state.get("materialRoleMap", {}).get(role, {})
    guid = entry.get("buildingMaterialId") if isinstance(entry, dict) else None
    return {"guid": guid} if guid else None


def W(x: float, y: float):
    return {"x": OX + float(x), "y": OY + float(y)}


def arch_z(u: float, half_width: float, rise: float) -> float:
    a = half_width
    c = (rise * rise - a * a) / (2.0 * a)
    radius = a + c
    center = -c if u >= 0 else c
    return math.sqrt(max(0.0, radius * radius - (u - center) ** 2))


def pointed_outline(width: float, rect_h: float, rise: float, segments: int = 12):
    half = width / 2.0
    pts = [(-half, 0.0), (half, 0.0), (half, rect_h)]
    for i in range(1, segments + 1):
        u = half * (1.0 - i / segments)
        pts.append((u, rect_h + arch_z(u, half, rise)))
    for i in range(1, segments + 1):
        u = -half * i / segments
        pts.append((u, rect_h + arch_z(u, half, rise)))
    return pts


def arch_strip(side: str, inner_half: float, inner_rise: float, width: float, segments: int = 10):
    outer_half = inner_half + width
    outer_rise = inner_rise + width * 1.15

    if side == "right":
        outer_us = [outer_half * (1.0 - i / segments) for i in range(segments + 1)]
        inner_us = [inner_half * (1.0 - i / segments) for i in range(segments + 1)]
    else:
        outer_us = [-outer_half * (1.0 - i / segments) for i in range(segments + 1)]
        inner_us = [-inner_half * (1.0 - i / segments) for i in range(segments + 1)]

    outer = [
        (u, RECT_HEIGHT + arch_z(u, outer_half, outer_rise))
        for u in outer_us
    ]
    inner = [
        (u, RECT_HEIGHT + arch_z(u, inner_half, inner_rise))
        for u in inner_us
    ]
    return outer + list(reversed(inner))


def segment_strip(x1, y1, x2, y2, width):
    dx = x2 - x1
    dy = y2 - y1
    length = math.hypot(dx, dy)
    nx = -dy / length * width / 2.0
    ny = dx / length * width / 2.0
    return [
        (x1 + nx, y1 + ny),
        (x2 + nx, y2 + ny),
        (x2 - nx, y2 - ny),
        (x1 - nx, y1 - ny),
    ]


def existing_step(key: str):
    entry = state["steps"].get(key)
    if not isinstance(entry, dict) or not entry.get("guid"):
        return None
    guid = entry["guid"]
    row = read_one(guid)
    if row.get("type") != "Slab":
        raise RuntimeError(f"{key}: expected Slab, got {row.get('type')}")
    return guid


def create_slab(key: str, polygon, top: float, thickness: float, role: str):
    old = existing_step(key)
    if old:
        print(f"[SKIP] {key} | {old}")
        return old

    item = {
        "level": float(top),
        "floorIndex": FLOOR_INDEX,
        "thickness": float(thickness),
        "referencePlaneLocation": "Top",
        "polygonCoordinates": [W(x, y) for x, y in polygon],
    }
    material = bm(role)
    if material:
        item["buildingMaterialId"] = material

    before = inventory("Slab")
    response = mutate("CreateSlabs", {"slabsData": [item]}, FLOOR_INDEX)
    guids = response_guids(response)
    if not guids:
        after = inventory("Slab")
        guids = [after[k] for k in set(after) - set(before)]
    if len(guids) != 1:
        raise RuntimeError(f"{key}: expected one new Slab, got {guids}")

    guid = guids[0]
    row = read_one(guid)
    if row.get("type") != "Slab":
        raise RuntimeError(f"{key}: read-back type={row.get('type')}")

    state["steps"][key] = {"guid": guid, "type": "Slab", "role": role}
    if guid not in state["allGuids"]:
        state["allGuids"].append(guid)
    save_state()
    print(f"[PASS] {key} | {guid}")
    return guid


def select_only(guids):
    current = client.call("GetSelectedElements", {})
    selected = []
    for row in response_body(current).get("elements", []):
        try:
            selected.append(row["elementId"]["guid"])
        except Exception:
            pass

    payload = {
        "addElementsToSelection": [
            {"elementId": {"guid": guid}} for guid in guids
        ],
        "removeElementsFromSelection": [
            {"elementId": {"guid": guid}}
            for guid in selected
            if guid not in guids
        ],
    }
    mutate("ChangeSelectionOfElements", payload)


def build_master():
    print("\n=== LIBRARY-FIRST PILOT / GOTHIC LANCET MASTER ===")

    half = OPENING_WIDTH / 2.0

    # Exact future wall cut. Top of slab is exactly Z=0.0.
    wallhole = create_slab(
        "WALLHOLE",
        pointed_outline(OPENING_WIDTH, RECT_HEIGHT, ARCH_RISE, 16),
        WALLHOLE_TOP,
        WALLHOLE_THICKNESS,
        "STRUCTURAL_STONE",
    )

    # Jambs and sill.
    create_slab(
        "FRAME_JAMB_L",
        [
            (-half - FRAME, 0.0),
            (-half, 0.0),
            (-half, RECT_HEIGHT),
            (-half - FRAME, RECT_HEIGHT),
        ],
        FRAME_TOP,
        FRAME_THICKNESS,
        "TRIM_STONE",
    )
    create_slab(
        "FRAME_JAMB_R",
        [
            (half, 0.0),
            (half + FRAME, 0.0),
            (half + FRAME, RECT_HEIGHT),
            (half, RECT_HEIGHT),
        ],
        FRAME_TOP,
        FRAME_THICKNESS,
        "TRIM_STONE",
    )
    create_slab(
        "FRAME_SILL",
        [
            (-half - FRAME, -FRAME),
            (half + FRAME, -FRAME),
            (half + FRAME, 0.0),
            (-half - FRAME, 0.0),
        ],
        FRAME_TOP,
        FRAME_THICKNESS,
        "TRIM_STONE",
    )

    # Pointed archivolt, built as two clean native slab strips.
    create_slab(
        "ARCHIVOLT_L",
        arch_strip("left", half, ARCH_RISE, FRAME, 14),
        FRAME_TOP,
        FRAME_THICKNESS,
        "TRIM_STONE",
    )
    create_slab(
        "ARCHIVOLT_R",
        arch_strip("right", half, ARCH_RISE, FRAME, 14),
        FRAME_TOP,
        FRAME_THICKNESS,
        "TRIM_STONE",
    )

    # Glazing: a single pointed slab, slightly inset from the frame.
    glass_margin = 0.11
    glass_width = OPENING_WIDTH - 2.0 * glass_margin
    glass_rect = RECT_HEIGHT - 0.08
    glass_rise = ARCH_RISE - 0.14
    glass_poly = pointed_outline(glass_width, glass_rect, glass_rise, 16)
    glass_poly = [(x, y + 0.08) for x, y in glass_poly]
    create_slab(
        "GLASS",
        glass_poly,
        GLASS_TOP,
        GLASS_THICKNESS,
        "GLAZING",
    )

    # Central mullion.
    mullion = 0.085
    create_slab(
        "MULLION",
        [
            (-mullion / 2, 0.10),
            (mullion / 2, 0.10),
            (mullion / 2, RECT_HEIGHT + 0.25),
            (-mullion / 2, RECT_HEIGHT + 0.25),
        ],
        FRAME_TOP + 0.01,
        FRAME_THICKNESS * 0.72,
        "DECORATIVE_STONE",
    )

    # Y tracery.
    branch_y = RECT_HEIGHT + 0.12
    target_u = half * 0.42
    target_y = RECT_HEIGHT + arch_z(target_u, half, ARCH_RISE) - 0.10
    create_slab(
        "TRACERY_L",
        segment_strip(0.0, branch_y, -target_u, target_y, mullion),
        FRAME_TOP + 0.01,
        FRAME_THICKNESS * 0.72,
        "DECORATIVE_STONE",
    )
    create_slab(
        "TRACERY_R",
        segment_strip(0.0, branch_y, target_u, target_y, mullion),
        FRAME_TOP + 0.01,
        FRAME_THICKNESS * 0.72,
        "DECORATIVE_STONE",
    )

    state["wallholeGuid"] = wallhole
    state["authoring"] = {
        "origin": {"x": OX, "y": OY},
        "openingWidth": OPENING_WIDTH,
        "rectHeight": RECT_HEIGHT,
        "archRise": ARCH_RISE,
        "hostPlane": "Horizontal Plane",
        "wallholeTopZ": WALLHOLE_TOP,
    }
    save_state()

    select_only([wallhole])

    print("\nMASTER GEOMETRY READY")
    print("Wallhole selected:", wallhole)
    print("\nNEXT MANUAL STEP:")
    print("1) Ctrl+T -> Classification and Properties -> ID = Wallhole")
    print("2) OK")
    print("3) Run this script again with argument: select-all")


def select_all_master():
    guids = []
    for guid in state.get("allGuids", []):
        try:
            read_one(guid)
            guids.append(guid)
        except Exception:
            raise RuntimeError(f"Master element missing: {guid}")
    if not guids:
        raise RuntimeError("No master elements recorded")
    select_only(guids)
    print("Selected master elements:", len(guids))
    print("Now use File -> Libraries and Objects -> Save Selection As -> Window")
    print("Choose HORIZONTAL PLANE as host wall/elevation plane.")
    print("Save as: SB_Gothic_Lancet_Large_v01")


def select_wallhole():
    guid = state.get("wallholeGuid")
    if not guid:
        raise RuntimeError("Wallhole not recorded")
    read_one(guid)
    select_only([guid])
    print("Wallhole selected:", guid)


mode = sys.argv[1].strip().lower() if len(sys.argv) > 1 else "build"

if mode == "build":
    build_master()
elif mode == "select-all":
    select_all_master()
elif mode == "select-wallhole":
    select_wallhole()
else:
    raise SystemExit("Use: build | select-wallhole | select-all")
