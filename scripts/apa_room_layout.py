"""Compile one-storey rectangular room fragments for the existing AC30 job."""
from __future__ import annotations

from itertools import pairwise
import math
import re
import unicodedata

import archicad_bim_graph as GRAPH
import archicad_normative_bindings as NORM
import archicad_semantic_brief as BRIEF
import archicad_semantic_spatial as SPATIAL
import archicad_scene_run as RUN
from apa_ac29_save_isolation import require


SCHEMA = "apa-room-layout/1"
REGIONS = {"experiment": "exp", "acceptance": "accept"}
OUTPUT_TYPES = {"CreateWalls", "CreateDoors", "CreateZones"}
INPUT_FIELDS = ("schemaVersion", "projectId", "storyLevelMM", "depthMM", "wall",
                "minPierMM", "originsMM", "rooms", "doors")
ZONE_PURPOSES = {
    "circulation": (("транзитные помещения", "circulation"),
                    ("холл", "прихожая", "коридор", "тамбур", "вестибюль", "транзитное помещение",
                     "hall", "hallway", "corridor", "lobby")),
    "residential": (("жилье и отдых", "жилые помещения", "residential", "residential and recreation"),
                    ("гостиная", "спальня", "детская комната", "жилая комната", "жилое помещение",
                     "living room", "bedroom")),
    "office": (("офисные помещения",), ("офис", "офисное помещение")),
    "education": (("образование и культура",), ("учебный класс", "учебная аудитория")),
    "medical": (("медицинское обслуживание",), ("смотровая", "процедурная", "больничная палата")),
    "retail_storage": (("торговые и складские помещения",), ("торговый зал", "склад")),
    "technical": (("техническое оборудование",), ("техническое помещение", "котельная", "венткамера")),
    "production_research": (("производство и исследование",),
                            ("производственный цех", "исследовательская лаборатория")),
}


def fields(value, required, reason, optional=()):
    require(isinstance(value, dict) and set(required) <= value.keys() <= set(required) | set(optional), reason)


def millimeters(value, field, *, minimum=0):
    require(type(value) is int and minimum <= value <= 10_000_000, "LAYOUT_INVALID_" + field)
    return value


def point(value):
    require(isinstance(value, list) and len(value) == 2, "LAYOUT_ORIGIN_XY_REQUIRED")
    return tuple(millimeters(coordinate, "ORIGIN", minimum=-10_000_000) for coordinate in value)


def xy(x, y):
    return {"x": x / 1000, "y": y / 1000}


def category_text(text):
    return " ".join(unicodedata.normalize("NFC", text).casefold().replace("ё", "е").split())


def room_purpose(room):
    name = room.get("purpose") if room.get("purpose") is not None else room.get("name")
    if not isinstance(name, str):
        return None
    name = re.sub(r"\s+(?:№\s*)?\d+$", "", category_text(name))
    return next((purpose for purpose, (categories, aliases) in ZONE_PURPOSES.items()
                 if name in (purpose, *categories, *aliases)), None)


def resolve_zone_categories(recipe, attributes):
    """Bind each room to one existing attribute of the exact target PLN."""
    legacy = recipe.get("zoneCategory")
    result = {}
    for room_id, room in recipe["roomFacts"].items():
        purpose = "legacy_shared" if legacy else room["purpose"]
        names = (legacy,) if legacy else ZONE_PURPOSES[purpose][0]
        matches = [row for row in attributes if isinstance(row.get("name"), str)
                   and (row["name"] if legacy else category_text(row["name"])) in names]
        location = f"{room_id}:{purpose}"
        require(matches, f"LAYOUT_ZONE_CATEGORY_MISSING:{location}")
        require(len(matches) == 1, f"LAYOUT_ZONE_CATEGORY_AMBIGUOUS:{location}")
        match, = matches
        identity = match.get("attributeId")
        guid = identity.get("guid") if isinstance(identity, dict) else None
        require(isinstance(guid, str) and RUN._GUID.fullmatch(guid),
                f"LAYOUT_ZONE_CATEGORY_INVALID_GUID:{location}")
        result[room_id] = dict(purpose=purpose, name=match["name"], guid=guid.lower())
    return result


def semantic_brief(value, rooms):
    brief = {
        "schemaVersion": BRIEF.SCHEMA, "projectId": value["projectId"], "mode": "GENERATE_FROM_ZERO",
        "units": "meters", "site": {"siteId": "layout-fragment", "region": None},
        "stories": [{"id": "fragment", "label": "1 этаж", "level": 0}],
        "rooms": [dict(id=r["id"], name=r["name"], storyId="fragment", minAreaM2=r["minAreaM2"])
                  for r in rooms],
        "constraints": value.get("constraints", []),
    }
    return BRIEF.normalize(brief)


def room_dimensions(rooms, depth, thickness):
    facts = {}
    start = 0
    for room in rooms:
        width = millimeters(room["widthMM"], "ROOM_WIDTH", minimum=1)
        area = width * depth / 1_000_000
        require(area >= room["minAreaM2"], "LAYOUT_ROOM_MINIMUM_AREA:" + room["id"])
        end = start + width
        facts[room["id"]] = dict(name=room["name"], widthMM=width, depthMM=depth, areaM2=area,
                                 minAreaM2=room["minAreaM2"], xStartMM=start, xEndMM=end)
        start = end + thickness
    return facts, start - thickness


def masonry_runs(rooms, span, depth, thickness):
    # Keep the clear masonry runs and the doorway datum immune to changes
    # in the native reference-line endpoints within junctions.
    half = thickness / 2
    paths = {
        "wall-bottom": (-thickness, -half, span + thickness, -half),
        "wall-top": (-thickness, depth + half, span + thickness, depth + half),
        "wall-left": (-half, 0, -half, depth),
        "wall-right": (span + half, 0, span + half, depth),
    }
    for i, room in enumerate(list(rooms.values())[:-1], 1):
        x = room["xEndMM"] + half
        paths[f"wall-part-{i}"] = (x, 0, x, depth)
    return paths


def wall_paths(runs, thicknesses, connections):
    """Extend named ends to the other wall's far face (coordinates in mm)."""
    axes = {}
    extents = {}
    for name, (x0, y0, x1, y1) in runs.items():
        length = math.hypot(x1 - x0, y1 - y0)
        require(length > 0 and thicknesses[name] > 0, 'LAYOUT_JUNCTION_INVALID_WALL:' + name)
        axes[name] = (x0, y0, (x1 - x0) / length, (y1 - y0) / length, length)
        extents[name] = [0, length]
    nodes, through, assigned = [], [], set()
    for kind, first, first_end, second, second_end in connections:
        roles = (first_end, second_end)
        require(all(role in {'start', 'end', 'through'} for role in roles)
                and roles.count('through') == {'L': 0, 'T': 1, 'X': 2}.get(kind),
                'LAYOUT_JUNCTION_INVALID_TOPOLOGY')
        x, y, ux, uy, _ = axes[first]
        vx, vy, wx, wy, _ = axes[second]
        cross = ux * wy - uy * wx
        require(abs(cross) > 1e-6, 'LAYOUT_JUNCTION_PARALLEL_OR_UNSTABLE')
        s = ((vx - x) * wy - (vy - y) * wx) / cross
        t = ((vx - x) * uy - (vy - y) * ux) / cross
        for name, role, along, neighbour in ((first, first_end, s, second), (second, second_end, t, first)):
            reach = thicknesses[neighbour] / (2 * abs(cross))
            if role == 'through':
                through.append((name, along, reach))
                continue
            require((name, role) not in assigned, 'LAYOUT_JUNCTION_ENDPOINT_ASSIGNED_TWICE')
            end_index = int(role == 'end')
            location = axes[name][-1] if end_index else 0
            require(abs(location - along) <= reach + 1e-6, 'LAYOUT_JUNCTION_REMOTE_ENDPOINT:' + name)
            extents[name][end_index] = along + (reach if end_index else -reach)
            assigned.add((name, role))
        nodes.append(dict(kind=kind, walls=[first, second], roles=list(roles),
                          pointMM=[round(x + s * ux, 9), round(y + s * uy, 9)]))
    for name, along, reach in through:
        start, end = extents[name]
        require(start <= along - reach + 1e-6 and end >= along + reach - 1e-6,
                'LAYOUT_JUNCTION_THROUGH_WALL_TOO_SHORT:' + name)
    paths = {}
    for name, (x, y, ux, uy, _) in axes.items():
        start, end = extents[name]
        require(start < end, 'LAYOUT_JUNCTION_REVERSED_WALL:' + name)
        paths[name] = tuple(round(value, 9) for value in (x + start * ux, y + start * uy,
                                                        x + end * ux, y + end * uy))
    return paths, nodes


def room_junctions(room_count):
    return [
        ('L', 'wall-bottom', 'start', 'wall-left', 'start'),
        ('L', 'wall-bottom', 'end', 'wall-right', 'start'),
        ('L', 'wall-top', 'start', 'wall-left', 'end'),
        ('L', 'wall-top', 'end', 'wall-right', 'end'),
        *((kind, f'wall-part-{i}', end, host, 'through')
          for i in range(1, room_count)
          for kind, end, host in (('T', 'start', 'wall-bottom'), ('T', 'end', 'wall-top'))),
    ]


def qualified_doors(value, rooms, walls, height):
    room_ids = list(rooms)
    expected = {frozenset((BRIEF.EXTERIOR, room_ids[0])): "wall-bottom"}
    expected.update({frozenset(pair): f"wall-part-{i}" for i, pair in enumerate(pairwise(room_ids), 1)})
    minimum_pier = millimeters(value["minPierMM"], "MINIMUM_PIER", minimum=1)
    doors = value["doors"]
    require(isinstance(doors, list) and len(doors) == len(expected), "LAYOUT_CONNECTIONS_REQUIRED")
    used = set()
    normalized = []
    for door in doors:
        fields(door, ("id", "from", "to", "fromFaceMM", "widthMM", "heightMM"),
               "LAYOUT_DOOR_FIELDS", ("favoriteName",))
        door_id = BRIEF._id(door["id"], "DOOR_ID")
        require(all(isinstance(door[key], str) for key in ("from", "to")), "LAYOUT_DOOR_ROOM_ID_REQUIRED")
        pair = frozenset((door["from"], door["to"]))
        require(door_id not in used and pair in expected, "LAYOUT_CONNECTIONS_UNEXPECTED_OR_DUPLICATE")
        used.add(door_id)
        host = expected.pop(pair)
        begin = millimeters(door["fromFaceMM"], "OPENING_OFFSET")
        width = millimeters(door["widthMM"], "OPENING_WIDTH", minimum=1)
        door_height = millimeters(door["heightMM"], "OPENING_HEIGHT", minimum=1)
        x0, y0, x1, y1 = walls[host]
        length = (x1 - x0) + (y1 - y0)
        end = begin + width
        require(door_height <= height, "LAYOUT_DOOR_ABOVE_WALL:" + door_id)
        require(begin >= minimum_pier and length - end >= minimum_pier, "LAYOUT_MINIMUM_PIER:" + door_id)
        if host == "wall-bottom":
            entry_room = rooms[room_ids[0]]
            require(x0 + begin >= entry_room["xStartMM"] and x0 + end <= entry_room["xEndMM"],
                    "LAYOUT_ENTRY_DOES_NOT_OPEN_IN_FIRST_ROOM")
        row = dict(id=door_id, hostMemberId=host, kind="DOOR", connects=[door["from"], door["to"]],
                   width=width / 1000, height=door_height / 1000, sillHeight=0,
                   centerOffset=(begin + width / 2) / 1000, piersMM=[begin, length - end])
        if "favoriteName" in door:
            row["favoriteName"] = BRIEF._name(door["favoriteName"], "DOOR_FAVORITE")
        normalized.append(row)
    return normalized


def masonry_checks(walls, wall, doors, thickness, height):
    profile = NORM.wall_coordination_profile(wall["coordination"], thickness / 1000)
    require(height % profile["courseModuleMM"] == 0, "LAYOUT_WALL_COURSE_MODULE_CONFLICT")
    members = {}
    for name, (x0, y0, x1, y1) in walls.items():
        horizontal = y0 == y1
        start, end = (x0, x1) if horizontal else (y0, y1)
        members[name] = dict(id=name, wallCseCandidateId="masonry", storyId="fragment",
                             direction="X" if horizontal else "Y", fromCoordinate=start / 1000,
                             toCoordinate=end / 1000, constantCoordinate=(y0 if horizontal else x0) / 1000,
                             thicknessMeters=thickness / 1000,
                             coordinationEnds={"start": "$wall-end", "end": "$wall-end"})
    checks = NORM.wall_coordination_checks(members, [{"id": "masonry", "coordination": profile}], doors)
    require(all(r["status"] == "DESIGN_MODULE_MATCH" for r in checks), "LAYOUT_MASONRY_MODULE_CONFLICT")
    return profile, checks


def verify_requirements(brief, rooms, doors):
    routes = {name: SPATIAL.access_path({"from": BRIEF.EXTERIOR, "to": name}, doors) for name in rooms}
    require(all(routes.values()), "LAYOUT_CONNECTIONS_REQUIRED")
    for row in brief["constraints"]:
        criterion = row.get("criterion", {})
        kind = criterion.get("kind")
        if kind == "ROOM_CLEAR_AREA":
            require(rooms[criterion["roomId"]]["areaM2"] >= criterion["minimumAreaM2"],
                    "LAYOUT_ROOM_MINIMUM_AREA:" + row["id"])
        elif kind in {"ENTRANCE", "ROOM_CONNECTION", "ACCESS_PATH"}:
            require(not criterion.get("minimumOpeningWidthM"), "LAYOUT_NET_OPENING_WIDTH_NOT_VERIFIED:" + row["id"])
            if kind == "ACCESS_PATH":
                require(SPATIAL.access_path(criterion, doors), "LAYOUT_CONNECTIONS:" + row["id"])
            else:
                expected = {criterion["from"], criterion["to"]}
                require(any(set(door["connects"]) == expected for door in doors), "LAYOUT_CONNECTIONS:" + row["id"])
        else:
            raise ValueError("LAYOUT_UNSUPPORTED_REQUIREMENT:" + row["id"])
    return routes


def region_bounds(origin, span, depth, thickness, level, height):
    x, y = origin
    return dict(xMin=(x - thickness) / 1000, xMax=(x + span + thickness) / 1000,
                yMin=(y - thickness) / 1000, yMax=(y + depth + thickness) / 1000,
                zMin=level / 1000, zMax=(level + height) / 1000)


def region_operations(prefix, origin, walls, runs, rooms, doors, thickness, height, depth, project_id):
    ox, oy = origin
    steps = []
    for name, (x0, y0, x1, y1) in walls.items():
        identifier = f"{prefix}-{name}"
        args = dict(begCoordinate=xy(ox + x0, oy + y0), endCoordinate=xy(ox + x1, oy + y1),
                    structureType="Basic", referenceLineLocation="Center", thickness=thickness / 1000,
                    height=height / 1000, floorIndex=0, zCoordinate=0, offset=0, arcAngle=0)
        after = [] if not steps else [steps[0]["id"]]
        steps.append(dict(id=identifier, command="CreateWalls", params={"wallsData": [args]}, after=after))
    for door in doors:
        member = door['hostMemberId']
        host = f"{prefix}-{member}"
        args = {k: door[k] for k in ("width", "height", "centerOffset", "sillHeight")}
        # The door's requested location is on the original masonry datum.
        start_shift = math.dist(runs[member][:2], walls[member][:2])
        args["centerOffset"] = round(args["centerOffset"] + start_shift / 1000, 12)
        if "favoriteName" in door:
            args["favoriteName"] = door["favoriteName"]
        args["ownerWallId"] = {"guid": {"$createdGuid": host}}
        steps.append(dict(id=f"{prefix}-door-{door['id']}", command="CreateDoors", params={"doorsData": [args]},
                          after=[host]))
    dependencies = [step["id"] for step in steps]
    for i, (room_id, room) in enumerate(rooms.items(), 1):
        west, east = ox + room["xStartMM"], ox + room["xEndMM"]
        polygon = [xy(west, oy), xy(east, oy), xy(east, oy + depth), xy(west, oy + depth)]
        ident = RUN.digest(project_id)[:8].upper() + f"-{i:02d}"
        args = dict(name=room["name"], numberStr=ident, height=height / 1000, bottomOffset=0, floorIndex=0,
                    stampPosition=xy((west + east) / 2, oy + depth / 2), allowOverlap=False,
                    geometry={"polygonCoordinates": polygon})
        steps.append(dict(id=f"{prefix}-zone-{room_id}", command="CreateZones", params={"zonesData": [args]},
                          after=dependencies))
    return steps


def unanswered(value):
    """Return missing inputs without resolving project choices by assumption."""
    require(isinstance(value, dict) and value.get("schemaVersion") == SCHEMA, "LAYOUT_SCHEMA_REQUIRED")
    prompts = {
        "projectId": "Идентификатор проектного фрагмента",
        "storyLevelMM": "Отметка выбранного этажа в миллиметрах",
        "depthMM": "Общая чистая глубина помещений в миллиметрах",
        "wall": "Материал, толщина, высота и подтверждённый профиль кладки",
        "minPierMM": "Минимальный простенок по проектному заданию в миллиметрах",
        "originsMM": "Координаты начала экспериментальной и принимаемой областей",
        "rooms": "Назначение, чистая ширина и минимальная площадь каждого помещения",
        "doors": "Связи помещений, ширина, высота и положение каждой двери",
    }
    questions = {key: prompts[key] for key in INPUT_FIELDS if key not in value or value[key] is None}
    nested = {
        "wall": {"materialName": "Имя строительного материала в PLN", "thicknessMM": "Толщина стены",
                 "heightMM": "Высота стены", "coordination": "Выбранный профиль кладочного модуля"},
        "originsMM": {name: "Координаты X и Y начала области" for name in REGIONS},
    }
    for section, names in nested.items():
        if isinstance(value.get(section), dict):
            questions.update({f"{section}.{key}": prompt for key, prompt in names.items()
                              if value[section].get(key) is None})
    rooms = value.get("rooms")
    if value.get("zoneCategoryName") is None and isinstance(rooms, list):
        for i, room in enumerate(rooms):
            if isinstance(room, dict) and room_purpose(room) is None:
                questions[f"rooms[{i}].purpose"] = (
                    f"Уточните назначение помещения «{room.get('name') or i + 1}», "
                    "например гостиная, холл или офис."
                )
    return questions


def compile_layout(value, router, *, joined=True):
    fields(value, INPUT_FIELDS, "LAYOUT_INPUT_FIELDS", ("constraints", "windows", "zoneCategoryName"))
    require(value["schemaVersion"] == SCHEMA, "LAYOUT_SCHEMA_REQUIRED")
    require(value.get("windows", []) == [], "LAYOUT_NATIVE_WINDOWS_NOT_SUPPORTED_IN_THIS_VARIANT")
    fields(value["wall"], ("materialName", "thicknessMM", "heightMM", "coordination"), "LAYOUT_WALL_FIELDS")
    fields(value["originsMM"], REGIONS, "LAYOUT_TWO_REGIONS_REQUIRED")
    rooms = value["rooms"]
    require(isinstance(rooms, list) and 2 <= len(rooms) <= 5, "LAYOUT_REQUIRES_TWO_TO_FIVE_ROOMS")
    for room in rooms:
        fields(room, ("id", "name", "widthMM", "minAreaM2"), "LAYOUT_ROOM_FIELDS", ("purpose",))
    brief = semantic_brief(value, rooms)
    wall = value["wall"]
    material = BRIEF._name(wall["materialName"], "WALL_MATERIAL_NAME")
    category = value.get("zoneCategoryName")
    if category is not None:
        # Preserve reproducibility of existing isolated geometry-only jobs.
        category = BRIEF._name(category, "ZONE_CATEGORY_NAME")
    thickness = millimeters(wall["thicknessMM"], "WALL_THICKNESS", minimum=1)
    height = millimeters(wall["heightMM"], "WALL_HEIGHT", minimum=1)
    depth = millimeters(value["depthMM"], "ROOM_DEPTH", minimum=1)
    level = millimeters(value["storyLevelMM"], "STORY_LEVEL", minimum=-10_000_000)
    room_facts, span = room_dimensions(rooms, depth, thickness)
    if category is None:
        for room in rooms:
            purpose = room_purpose(room)
            require(purpose is not None, "LAYOUT_ROOM_PURPOSE_REQUIRED:" + room["id"])
            room_facts[room["id"]]["purpose"] = purpose
    runs = masonry_runs(room_facts, span, depth, thickness)
    walls, joints = (wall_paths(runs, dict.fromkeys(runs, thickness), room_junctions(len(rooms)))
                     if joined else (runs, []))
    doors = qualified_doors(value, room_facts, runs, height)
    profile, checks = masonry_checks(runs, wall, doors, thickness, height)
    routes = verify_requirements(brief, room_facts, doors)
    origins = {name: point(value["originsMM"][name]) for name in REGIONS}
    bounds = {name: region_bounds(origin, span, depth, thickness, level, height) for name, origin in origins.items()}
    first, second = bounds.values()
    require(any(first[axis + "Max"] < second[axis + "Min"] or second[axis + "Max"] < first[axis + "Min"]
                for axis in "xy"), "LAYOUT_REGIONS_OVERLAP_OR_TOUCH")
    require(all((a - b) % profile["planModuleMM"] == 0
                for a, b in zip(origins["experiment"], origins["acceptance"])), "LAYOUT_REGION_MODULE_ORIGIN_CONFLICT")
    graphs = {name: {"operations": region_operations(prefix, origins[name], walls, runs, room_facts, doors,
              thickness, height, depth, brief["projectId"])} for name, prefix in REGIONS.items()}
    reports = {name: GRAPH.compile_graph(router.catalog, graph, runtime_version="2.0.0")
               for name, graph in graphs.items()}
    require(all(report["status"] == "PLAN_VALIDATED_OFFLINE" for report in reports.values()), "LAYOUT_GRAPH_INVALID")
    graph = graphs["experiment"]
    operations = graph["operations"]
    room_dependencies = {
        rid: {
            "walls": ["exp-wall-bottom", "exp-wall-top",
                      "exp-wall-left" if i == 0 else f"exp-wall-part-{i}",
                      "exp-wall-right" if i + 1 == len(room_facts) else f"exp-wall-part-{i + 1}"],
            "doors": [f"exp-door-{door['id']}" for door in doors if rid in door["connects"]],
            "zone": f"exp-zone-{rid}",
        }
        for i, rid in enumerate(room_facts)
    }
    result = dict(kind="layout", status="LAYOUT_PLAN_VALIDATED_OFFLINE", projectId=brief["projectId"],
                stories=[dict(id="fragment", level=level / 1000)], graph=graph,
                sourcePlanHash=reports["experiment"]["sourcePlanHash"],
                inclusionGraph=graphs["acceptance"], inclusionGraphSha256=reports["acceptance"]["sourcePlanHash"],
                inclusionMode="USER_COPY_THEN_READBACK", roomDependencies=room_dependencies,
                copyTranslationMM=[b - a for a, b in zip(origins["experiment"], origins["acceptance"])],
                stairPlans={}, slabMaterial=None, wallMaterials={s["id"]: material for s in operations
                                                                 if s["command"] == "CreateWalls"},
                zoneCategory=category, roomFacts=room_facts, doors=doors, routes=routes,
                regions=bounds, masonryProfile=profile, masonryChecks=checks, executionPermission=False,
                precisionMM=1, normativeApplicability="NOT_VERIFIED")
    if joined:
        result["wallJunctions"] = {name: [
            dict(joint, walls=[f"{prefix}-{wall_id}" for wall_id in joint["walls"]],
                 pointMM=[value + shift for value, shift in zip(joint["pointMM"], origins[name])])
            for joint in joints] for name, prefix in REGIONS.items()}
    return result


def verify_native_zone(expected, row, quantities, expected_level):
    """Prove the actual rectangular, manual Zone and its measured area."""
    actual = row.get("details", {})
    require(row.get("type") == "Zone" and row.get("floorIndex") == expected["floorIndex"]
            and actual.get("isManual") is True and actual.get("name") == expected["name"]
            and actual.get("numberStr") == expected["numberStr"], "LAYOUT_NATIVE_ZONE_IDENTITY_DRIFT")
    expect_polygon = expected["geometry"]["polygonCoordinates"]
    polygon = actual.get("polygonOutline")
    require(not actual.get("holes") and not actual.get("polygonArcs")
            and RUN.compare_polygon(expect_polygon, polygon),
            "LAYOUT_NATIVE_ZONE_CONTOUR_DRIFT")
    category = actual.get("categoryAttributeId", {}).get("guid")
    require(isinstance(category, str) and category.casefold() == expected["categoryAttributeId"]["guid"].casefold()
            and RUN.close(actual.get("height"), expected["height"], tolerance=0.001)
            and RUN.close(actual.get("zCoordinate"), expected_level, tolerance=0.001)
            and RUN.close(actual.get("bottomOffset"), expected["bottomOffset"], tolerance=0.001)
            and actual.get("relativeTopStory") == 0, "LAYOUT_NATIVE_ZONE_HEIGHT_OR_CATEGORY_DRIFT")
    require(all(RUN.close(actual.get("stampPosition", {}).get(axis), expected["stampPosition"][axis],
                          tolerance=0.001) for axis in "xy"), "LAYOUT_NATIVE_ZONE_STAMP_DRIFT")
    width = expect_polygon[1]["x"] - expect_polygon[0]["x"]
    depth = expect_polygon[2]["y"] - expect_polygon[1]["y"]
    expected_area = width * depth
    # A 1 mm allowance on either dimension scales to an area allowance.
    area_tolerance = (width + depth) * .001 + .000001
    measurement = quantities.get("quantities", {})
    require(quantities.get("type") == "Zone"
            and RUN.close(measurement.get("area"), expected_area, tolerance=area_tolerance),
            "LAYOUT_NATIVE_ZONE_MEASURED_AREA_DRIFT")
    extents = {axis: (max(p[axis] for p in polygon) - min(p[axis] for p in polygon)) * 1000 for axis in "xy"}
    return {"name": actual["name"], "number": actual["numberStr"], "nativeStoryIndex": row["floorIndex"],
            "widthMM": round(extents["x"], 3), "depthMM": round(extents["y"], 3),
            "measuredAreaM2": measurement["area"], "calculatedAreaM2": measurement.get("calculatedArea"),
            "heightM": actual["height"], "categoryGuid": category}


def verify_wall_body(row, element, level, *, joined=False):
    """Check the realised solid against the authored orthogonal wall faces."""
    start, end = row["begCoordinate"], row["endCoordinate"]
    half = row["thickness"] / 2
    expected = []
    for axis in "xy":
        shift = half if start[axis] == end[axis] else 0
        expected.append((min(start[axis], end[axis]) - shift, max(start[axis], end[axis]) + shift))
    expected.append((level, level + row["height"]))
    vertices = [vertex for body in element["bodies"] for vertex in body["vertices"]]
    require(vertices, "LAYOUT_NATIVE_WALL_BODY_MISSING")
    for i, (lower, upper) in enumerate(expected):
        actual_min = min(v[i] for v in vertices)
        actual_max = max(v[i] for v in vertices)
        # Native cleanup can trim Wall ends. The joint proof checks the
        # resultant footprint against the entire wall system.
        trimmed = joined and i < 2 and start["xy"[i]] != end["xy"[i]]
        require((trimmed and actual_min >= lower - .001 and actual_max <= upper + .001)
                or (RUN.close(actual_min, lower, tolerance=.001) and RUN.close(actual_max, upper, tolerance=.001)),
                "LAYOUT_NATIVE_WALL_FACE_OR_EXTENT_DRIFT")
