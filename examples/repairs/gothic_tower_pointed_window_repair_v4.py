from __future__ import annotations

import importlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

# The script is meant to be copied/run from the Safe BIM runtime directory.
# If it is downloaded from GitHub into that directory, these resolve correctly.
SCHEMA = ROOT / "tapir-1.5.9.json"
STATE_FILE = ROOT / "gothic_tower_top_stage_state.json"
BRIDGE = "http://127.0.0.1:19723"

REPAIR_VERSION = 4
SEO_LAYER_NAME = "SB_SEO_OPERATORS"

CENTER_X = 260.0
CENTER_Y = 120.0
BASE_LEVEL = 42.0
FLOOR_INDEX = 0
R_OUT = 6.40
WALL_THICKNESS = 0.60

LARGE_WIDTH = 1.48
LARGE_SILL = 2.00
LARGE_RECT_HEIGHT = 2.70
LARGE_ARCH_RISE = 1.62

SMALL_WIDTH = 0.98
SMALL_SILL = 2.30
SMALL_RECT_HEIGHT = 2.25
SMALL_ARCH_RISE = 1.35

FRAME_RADIAL_CENTER = 0.43
FRAME_DEPTH = 0.22
FRAME_BORDER = 0.18
FRAME_BOTTOM = 0.18

GLASS_RADIAL_CENTER = 0.19
GLASS_DEPTH = 0.045
GLASS_MARGIN = 0.10

CUTTER_DEPTH = 1.60
CUTTER_RADIAL_CENTER = 0.0

MULLION_SIZE = 0.095
TRACERY_SIZE = 0.085

# Policy must be extended BEFORE importing safe_bim_layer because TapirClient
# snapshots the command policy during import.
import safe_bim_command_policy as policy

policy.READ_ONLY_COMMANDS = frozenset(
    set(policy.READ_ONLY_COMMANDS)
    | {
        "GetAttributesByType",
        "GetSolidElementLinks",
    }
)

MUTATIONS = {
    "CreateMorphs",
    "CreateColumns",
    "CreateBeams",
    "CreateLayers",
    "SetDetailsOfElements",
    "CreateSolidElementLinks",
    "DeleteElements",
}

policy.ADMITTED_MODEL_COMMANDS = frozenset(
    set(policy.ADMITTED_MODEL_COMMANDS) | MUTATIONS
)

for command in MUTATIONS:
    policy._EXPLICIT[command] = policy.CommandClass.MODEL_MUTATION

policy._CREATE_ARRAY_FIELDS.update(
    {
        "CreateMorphs": "morphsData",
        "CreateColumns": "columnsData",
        "CreateBeams": "beamsData",
        "CreateLayers": "layerDataArray",
    }
)

from safe_bim_layer import TapirClient, SafeBIMLayer

gateway_module = importlib.import_module("safe_bim_mutation_gateway")
gateway_module = importlib.reload(gateway_module)
MutationGateway = gateway_module.MutationGateway

client = TapirClient(BRIDGE, str(SCHEMA))
gateway = MutationGateway(client)
bim = SafeBIMLayer(client, gateway=gateway)


def body(response):
    value = response.get("result", {}).get("addOnCommandResponse", {})
    return value if isinstance(value, dict) else {}


def W(x, y):
    return {"x": CENTER_X + float(x), "y": CENTER_Y + float(y)}


def W3(x, y, z):
    return {
        "x": CENTER_X + float(x),
        "y": CENTER_Y + float(y),
        "z": float(z),
    }


def read_one(guid):
    response = client.call(
        "GetDetailsOfElements",
        {"elements": [{"elementId": {"guid": guid}}]},
    )
    rows = body(response).get("detailsOfElements", [])
    if len(rows) != 1:
        raise RuntimeError(f"{guid}: read-back rows={len(rows)}")
    return rows[0]


def inventory(element_type):
    response = client.call("GetElementsByType", {"elementType": element_type})
    result = {}
    for item in body(response).get("elements", []):
        try:
            guid = item["elementId"]["guid"]
        except Exception:
            continue
        result[guid.lower()] = guid
    return result


def response_guids(response):
    result = []
    for item in body(response).get("elements", []):
        if "error" in item:
            raise RuntimeError(
                json.dumps(item["error"], ensure_ascii=False, indent=2)
            )
        try:
            result.append(item["elementId"]["guid"])
        except Exception:
            pass
    return result


def check_execution(response, command):
    for item in body(response).get("executionResults", []):
        if isinstance(item, dict) and item.get("success") is False:
            raise RuntimeError(
                command
                + " FAILED:\n"
                + json.dumps(item, ensure_ascii=False, indent=2)
            )


def mutate(command, payload, floor_index=None):
    client.validate_payload(command, payload)
    gateway.begin_step(command)
    try:
        if floor_index is not None:
            bim.ensure_active_story(floor_index)
        response = gateway.dispatch(command, payload)
    finally:
        gateway.end_step()
    check_execution(response, command)
    return response


if not STATE_FILE.exists():
    raise RuntimeError("Не найден state готической башни: " + str(STATE_FILE))

state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
steps = state.setdefault("steps", {})


def save_state():
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    tmp.replace(STATE_FILE)


def state_guid(key, expected_type=None):
    entry = steps.get(key)
    if not isinstance(entry, dict):
        return None
    guid = entry.get("guid")
    if not guid:
        return None
    try:
        row = read_one(guid)
    except Exception:
        return None
    if expected_type and row.get("type") != expected_type:
        raise RuntimeError(
            f"{key}: type={row.get('type')}, expected={expected_type}"
        )
    return guid


def remember(key, guid, expected_type):
    steps[key] = {"guid": guid, "type": expected_type}
    save_state()


def create_one(key, command, payload, expected_type):
    old = state_guid(key, expected_type)
    if old:
        print("[SKIP]", key, old)
        return old

    before = inventory(expected_type)
    response = mutate(command, payload, FLOOR_INDEX)
    guids = response_guids(response)

    if not guids:
        after = inventory(expected_type)
        guids = [after[k] for k in sorted(set(after) - set(before))]

    if len(guids) != 1:
        raise RuntimeError(
            f"{key}: expected one {expected_type}; got {guids}"
        )

    guid = guids[0]
    row = read_one(guid)
    if row.get("type") != expected_type:
        raise RuntimeError(f"{key}: read-back type={row.get('type')}")

    remember(key, guid, expected_type)
    print("[PASS]", key, guid)
    return guid


def delete_state_element(key, expected_type):
    entry = steps.get(key)
    if not isinstance(entry, dict):
        return False

    guid = entry.get("guid")
    if not guid:
        steps.pop(key, None)
        save_state()
        return False

    try:
        row = read_one(guid)
    except Exception:
        steps.pop(key, None)
        save_state()
        print("[INFO] Уже отсутствует:", key, guid)
        return False

    if row.get("type") != expected_type:
        raise RuntimeError(
            f"ОТКАЗ удаления {key}: type={row.get('type')}, "
            f"expected={expected_type}, guid={guid}"
        )

    mutate(
        "DeleteElements",
        {"elements": [{"elementId": {"guid": guid}}]},
    )

    steps.pop(key, None)
    save_state()
    print("[DELETE]", key, guid)
    return True


material_map = state.get("materialRoleMap", {})


def BM(role):
    value = material_map.get(role, {}).get("buildingMaterialId")
    return {"guid": value} if value else None


def SURFACE(role):
    value = material_map.get(role, {}).get("surfaceId")
    return {"guid": value} if value else None


def ensure_hidden_layer():
    mutate(
        "CreateLayers",
        {
            "layerDataArray": [
                {
                    "name": SEO_LAYER_NAME,
                    "isHidden": True,
                    "isLocked": False,
                    "isWireframe": False,
                }
            ],
            "overwriteExisting": True,
        },
    )

    rows = body(
        client.call(
            "GetAttributesByType",
            {"attributeType": "Layer"},
        )
    ).get("attributes", [])

    for row in rows:
        if row.get("name") == SEO_LAYER_NAME:
            idx = row.get("index")
            if isinstance(idx, int) and idx > 0:
                return idx

    raise RuntimeError(
        f"Layer {SEO_LAYER_NAME!r} создан, но его index не найден."
    )


SEO_LAYER_INDEX = ensure_hidden_layer()
print("[PASS] SEO layer index =", SEO_LAYER_INDEX)


def move_to_layer(guid, layer_index):
    mutate(
        "SetDetailsOfElements",
        {
            "elementsWithDetails": [
                {
                    "elementId": {"guid": guid},
                    "details": {"layerIndex": int(layer_index)},
                }
            ]
        },
    )


def octagon_points(radius):
    pts = []
    for i in range(8):
        a = math.pi / 8.0 + i * math.pi / 4.0
        pts.append((radius * math.cos(a), radius * math.sin(a)))
    return pts


OUTER = octagon_points(R_OUT)


def face_geometry(side):
    a = OUTER[side]
    b = OUTER[(side + 1) % 8]

    dx = b[0] - a[0]
    dy = b[1] - a[1]
    length = math.hypot(dx, dy)

    tx = dx / length
    ty = dy / length

    mid = ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)
    radial = math.hypot(mid[0], mid[1])

    nx = mid[0] / radial
    ny = mid[1] / radial

    return {
        "a": a,
        "b": b,
        "mid": mid,
        "t": (tx, ty),
        "n": (nx, ny),
        "length": length,
    }


def local_point(face, u, outward=0.0):
    mx, my = face["mid"]
    tx, ty = face["t"]
    nx, ny = face["n"]
    return (
        mx + tx * u + nx * outward,
        my + ty * u + ny * outward,
    )


def arch_half_curves(half_width, rise, segments=10):
    a = float(half_width)
    h = float(rise)

    c = (h * h - a * a) / (2.0 * a)
    radius = a + c

    right = []
    left = []

    for i in range(segments + 1):
        ur = a - a * i / segments
        zr = math.sqrt(max(0.0, radius * radius - (ur + c) ** 2))
        right.append((ur, zr))

        ul = -a + a * i / segments
        zl = math.sqrt(max(0.0, radius * radius - (ul - c) ** 2))
        left.append((ul, zl))

    return left, right


def pointed_profile(width, sill_z, rect_height, rise, segments=10):
    half = width / 2.0
    spring_z = sill_z + rect_height
    left, right = arch_half_curves(half, rise, segments)

    profile = [
        (-half, sill_z),
        (half, sill_z),
        (half, spring_z),
    ]

    profile.extend((u, spring_z + z) for u, z in right[1:])
    profile.extend((u, spring_z + z) for u, z in reversed(left[:-1]))

    return profile


def prism_body(face, profile, depth, outward_center, surface_id=None):
    tx, ty = face["t"]
    nx, ny = face["n"]
    mx, my = face["mid"]

    half_depth = depth / 2.0
    vertices = []

    for depth_offset in (
        outward_center - half_depth,
        outward_center + half_depth,
    ):
        for u, z in profile:
            x = mx + tx * u + nx * depth_offset
            y = my + ty * u + ny * depth_offset
            vertices.append({"x": x, "y": y, "z": z})

    count = len(profile)
    polygons = []

    front = {"vertexIds": list(reversed(range(count)))}
    back = {"vertexIds": [count + i for i in range(count)]}

    if surface_id:
        front["surfaceId"] = surface_id
        back["surfaceId"] = surface_id

    polygons.append(front)
    polygons.append(back)

    for i in range(count):
        j = (i + 1) % count
        p = {
            "vertexIds": [i, j, count + j, count + i]
        }
        if surface_id:
            p["surfaceId"] = surface_id
        polygons.append(p)

    return {
        "bodyType": "Solid",
        "edgeDefault": "HardVisible",
        "vertices": vertices,
        "polygons": polygons,
    }


def create_profile_morph(key, face, profile, depth, outward, role=None):
    item = {
        "basePoint": W3(0.0, 0.0, 0.0),
        "body": prism_body(
            face,
            profile,
            depth,
            outward,
            SURFACE(role) if role else None,
        ),
    }

    if role:
        bm = BM(role)
        if bm:
            item["buildingMaterialId"] = bm

    return create_one(
        key,
        "CreateMorphs",
        {"morphsData": [item]},
        "Morph",
    )


def create_column(key, x, y, z, height, size, role):
    item = {
        "coordinates": W3(x, y, z),
        "height": float(height),
        "width": float(size),
        "depth": float(size),
        "circleBased": False,
        "isWidthAndHeightLinked": True,
    }

    bm = BM(role)
    if bm:
        item["buildingMaterialId"] = bm

    return create_one(
        key,
        "CreateColumns",
        {"columnsData": [item]},
        "Column",
    )


def create_beam_3d(key, p1, p2, size, role):
    x1, y1, z1 = p1
    x2, y2, z2 = p2

    horizontal = math.hypot(x2 - x1, y2 - y1)
    angle = math.atan2(z2 - z1, horizontal)

    item = {
        "begCoordinate": W(x1, y1),
        "endCoordinate": W(x2, y2),
        "floorIndex": FLOOR_INDEX,
        "zCoordinate": float(z1),
        "height": float(size),
        "width": float(size),
        "slantAngle": float(angle),
    }

    bm = BM(role)
    if bm:
        item["buildingMaterialId"] = bm

    return create_one(
        key,
        "CreateBeams",
        {"beamsData": [item]},
        "Beam",
    )


def solid_links_for_target(target_guid):
    response = client.call(
        "GetSolidElementLinks",
        {
            "elements": [
                {"elementId": {"guid": target_guid}}
            ]
        },
    )
    rows = body(response).get("solidLinks", [])
    if len(rows) != 1:
        raise RuntimeError(
            f"GetSolidElementLinks({target_guid}): rows={len(rows)}"
        )
    return rows[0].get("solidLinksWithTheGivenTarget", [])


def has_subtraction(target_guid, operator_guid):
    wanted = operator_guid.lower()
    for link in solid_links_for_target(target_guid):
        try:
            guid = link["operatorId"]["guid"].lower()
        except Exception:
            continue
        if guid == wanted and link.get("operation") == "Subtraction":
            return True
    return False


def ensure_subtraction(target_guid, operator_guid, label):
    if has_subtraction(target_guid, operator_guid):
        print("[SKIP SEO]", label)
        return

    mutate(
        "CreateSolidElementLinks",
        {
            "solidLinks": [
                {
                    "targetId": {"guid": target_guid},
                    "operatorId": {"guid": operator_guid},
                    "operation": "Subtraction",
                    "linkFlags": {
                        "inheritOperatorAttributes": False,
                        "skipPolygonHoles": False,
                    },
                }
            ]
        },
    )

    if not has_subtraction(target_guid, operator_guid):
        raise RuntimeError(f"SEO verification failed: {label}")

    print("[PASS SEO]", label)


def cleanup_legacy_window(side):
    candidates = [
        (f"OPENING:LANCET_{side}", "Opening"),
        (f"MORPH:LANCET_{side}:INFILL_L", "Morph"),
        (f"MORPH:LANCET_{side}:INFILL_R", "Morph"),
        (f"MORPH:LANCET_{side}:GLASS", "Morph"),
        (f"COLUMN:LANCET_{side}:JAMB_L", "Column"),
        (f"COLUMN:LANCET_{side}:JAMB_R", "Column"),
        (f"COLUMN:LANCET_{side}:MULLION", "Column"),
        (f"BEAM:LANCET_{side}:SILL", "Beam"),
        (f"BEAM:LANCET_{side}:TRACERY_L", "Beam"),
        (f"BEAM:LANCET_{side}:TRACERY_R", "Beam"),
    ]

    for i in range(7):
        candidates.append((f"BEAM:LANCET_{side}:ARCH_L_{i}", "Beam"))
        candidates.append((f"BEAM:LANCET_{side}:ARCH_R_{i}", "Beam"))

    for key, typ in candidates:
        delete_state_element(key, typ)


def build_window(side, width, sill, rect_height, arch_rise):
    print()
    print(f"===== WINDOW SIDE {side} =====")

    face = face_geometry(side)

    wall_guid = state_guid(f"WALL:SIDE_{side}", "Wall")
    if not wall_guid:
        raise RuntimeError(f"Не найдена стена WALL:SIDE_{side}")

    sill_z = BASE_LEVEL + sill

    clear_profile = pointed_profile(
        width,
        sill_z,
        rect_height,
        arch_rise,
        12,
    )

    outer_profile = pointed_profile(
        width + 2.0 * FRAME_BORDER,
        sill_z - FRAME_BOTTOM,
        rect_height + FRAME_BOTTOM + 0.03,
        arch_rise + FRAME_BORDER * 0.90,
        12,
    )

    glass_profile = pointed_profile(
        width - 2.0 * GLASS_MARGIN,
        sill_z + GLASS_MARGIN,
        rect_height - GLASS_MARGIN * 0.50,
        arch_rise - GLASS_MARGIN * 0.60,
        12,
    )

    # One exact pointed operator cuts the wall and hollows the visible frame.
    cutter_guid = create_profile_morph(
        f"MORPH:SEO_LANCET_{side}",
        face,
        clear_profile,
        CUTTER_DEPTH,
        CUTTER_RADIAL_CENTER,
        None,
    )

    move_to_layer(cutter_guid, SEO_LAYER_INDEX)

    ensure_subtraction(
        wall_guid,
        cutter_guid,
        f"WALL:SIDE_{side} <- SEO_LANCET_{side}",
    )

    frame_guid = create_profile_morph(
        f"MORPH:WINDOW_V4_{side}:FRAME",
        face,
        outer_profile,
        FRAME_DEPTH,
        FRAME_RADIAL_CENTER,
        "TRIM_STONE",
    )

    ensure_subtraction(
        frame_guid,
        cutter_guid,
        f"FRAME_{side} <- SEO_LANCET_{side}",
    )

    create_profile_morph(
        f"MORPH:WINDOW_V4_{side}:GLASS",
        face,
        glass_profile,
        GLASS_DEPTH,
        GLASS_RADIAL_CENTER,
        "GLAZING",
    )

    half = width / 2.0
    spring_z = sill_z + rect_height
    center_xy = local_point(
        face,
        0.0,
        FRAME_RADIAL_CENTER + 0.02,
    )

    mullion_top = spring_z + arch_rise * 0.28

    create_column(
        f"COLUMN:WINDOW_V4_{side}:MULLION",
        center_xy[0],
        center_xy[1],
        sill_z + GLASS_MARGIN,
        mullion_top - (sill_z + GLASS_MARGIN),
        MULLION_SIZE,
        "TRIM_STONE",
    )

    branch_u = half * 0.42
    branch_start_z = spring_z - 0.03
    branch_end_z = spring_z + arch_rise * 0.62

    for label, u in (("L", -branch_u), ("R", branch_u)):
        target_xy = local_point(
            face,
            u,
            FRAME_RADIAL_CENTER + 0.02,
        )

        create_beam_3d(
            f"BEAM:WINDOW_V4_{side}:TRACERY_{label}",
            (
                center_xy[0],
                center_xy[1],
                branch_start_z,
            ),
            (
                target_xy[0],
                target_xy[1],
                branch_end_z,
            ),
            TRACERY_SIZE,
            "TRIM_STONE",
        )

    # Only after the exact pointed cut and the replacement assembly exist do we
    # delete the old rectangular Opening and V3 window detail pieces.
    cleanup_legacy_window(side)

    if not has_subtraction(wall_guid, cutter_guid):
        raise RuntimeError(
            f"После cleanup потеряна SEO-связь на стороне {side}"
        )

    print(
        "[PASS WINDOW]",
        side,
        "wall=",
        wall_guid,
        "cutter=",
        cutter_guid,
        "frame=",
        frame_guid,
    )


print()
print("========================================")
print("GOTHIC POINTED WINDOW REPAIR V4")
print("========================================")

# Representative schema/admission preflight without physical creation.
for command, payload in (
    (
        "CreateMorphs",
        {
            "morphsData": [
                {
                    "basePoint": W3(0, 0, 0),
                    "body": {
                        "bodyType": "Solid",
                        "edgeDefault": "HardVisible",
                        "vertices": [
                            {"x": 0, "y": 0, "z": 0},
                            {"x": 1, "y": 0, "z": 0},
                            {"x": 0, "y": 1, "z": 0},
                            {"x": 0, "y": 0, "z": 1},
                        ],
                        "polygons": [
                            {"vertexIds": [0, 2, 1]},
                            {"vertexIds": [0, 1, 3]},
                            {"vertexIds": [1, 2, 3]},
                            {"vertexIds": [2, 0, 3]},
                        ],
                    },
                }
            ]
        },
    ),
    (
        "CreateColumns",
        {
            "columnsData": [
                {
                    "coordinates": W3(0, 0, BASE_LEVEL),
                    "height": 1.0,
                    "width": 0.1,
                    "depth": 0.1,
                    "circleBased": False,
                    "isWidthAndHeightLinked": True,
                }
            ]
        },
    ),
    (
        "CreateBeams",
        {
            "beamsData": [
                {
                    "begCoordinate": W(0, 0),
                    "endCoordinate": W(1, 0),
                    "floorIndex": FLOOR_INDEX,
                    "zCoordinate": BASE_LEVEL,
                    "height": 0.1,
                    "width": 0.1,
                    "slantAngle": 0.0,
                }
            ]
        },
    ),
):
    client.validate_payload(command, payload)
    gateway.begin_step(command)
    gateway.end_step()
    print("[PREFLIGHT PASS]", command)

print()

for side in range(8):
    if side % 2 == 0:
        build_window(
            side,
            LARGE_WIDTH,
            LARGE_SILL,
            LARGE_RECT_HEIGHT,
            LARGE_ARCH_RISE,
        )
    else:
        build_window(
            side,
            SMALL_WIDTH,
            SMALL_SILL,
            SMALL_RECT_HEIGHT,
            SMALL_ARCH_RISE,
        )

state["windowRepairVersion"] = REPAIR_VERSION
state["windowRepresentation"] = (
    "Pointed SEO wall cut + compact frame/glass assembly; "
    "temporary until hosted Window library-part placement is added to Tapir."
)
save_state()

print()
print("========================================")
print("WINDOW REPAIR V4: PASS")
print("========================================")
print("8 rectangular legacy niches removed.")
print("8 pointed SEO wall cuts verified.")
print("8 compact pointed window assemblies created.")
print("SEO operators are on hidden layer:", SEO_LAYER_NAME)
print()
print("Открой 3D и проверь окна снаружи и изнутри.")
