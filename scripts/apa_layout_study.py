"""Generate reviewable rectangular single-storey studies from a semantic brief."""
from __future__ import annotations

from itertools import pairwise, permutations
import math

import archicad_semantic_brief as BRIEF
import archicad_semantic_spatial as SPATIAL


DOOR_END_CLEARANCE = .10
ROOM_COUNT_LIMIT = 8


def room_order(rooms, criteria):
    direct = {priority: set() for priority in ("REQUIRED", "PREFERENCE")}
    for priority, criterion in criteria:
        if criterion["kind"] == "ROOM_CONNECTION":
            direct[priority].add(frozenset((criterion["from"], criterion["to"])))

    def score(order):
        adjacent = {frozenset(pair) for pair in pairwise(order)}
        return (len(direct["REQUIRED"] & adjacent), len(direct["PREFERENCE"] & adjacent))

    # The bounded search only orders rooms. Geometry, doors and checks use the
    # same typed layout and compiler as a manually authored option.
    return max(permutations(sorted(rooms)), key=score)


def connection_locations(order, criteria, width):
    positions = {room: i for i, room in enumerate(order)}
    entrances, partitions, paths = set(), set(), []
    for priority, criterion in criteria:
        kind = criterion["kind"]
        if kind not in {"ENTRANCE", "ROOM_CONNECTION", "ACCESS_PATH"}:
            continue
        a, b = criterion["from"], criterion["to"]
        if kind == "ENTRANCE":
            entrances.add(positions[b if a == BRIEF.EXTERIOR else a])
        elif kind == "ROOM_CONNECTION" and abs(positions[a] - positions[b]) == 1:
            partitions.add(min(positions[a], positions[b]))
        elif kind == "ACCESS_PATH" and width + SPATIAL.EPS >= criterion.get("minimumOpeningWidthM", 0):
            paths.append((priority, positions.get(a), positions[b]))

    external = [(p != "REQUIRED", end) for p, start, end in paths if start is None]
    if external and not entrances:
        entrances.add(min(external)[1])
    for _, start, end in paths:
        if start is None:
            start = min(entrances, key=lambda i: (abs(i - end), i))
        partitions.update(range(min(start, end), max(start, end)))
    return entrances, partitions


def strip_variant(direction, outline, story, rooms, order, entrances, partitions, thickness, door):
    cross = "y" if direction == "x" else "x"
    start, end = outline[direction + "Min"], outline[direction + "Max"]
    cross_start, cross_end = outline[cross + "Min"], outline[cross + "Max"]
    depth = cross_end - cross_start
    door_span = door["width"] + 2 * DOOR_END_CLEARANCE
    if partitions and depth < door_span - SPATIAL.EPS:
        return None, "INTERNAL_DOOR_DOES_NOT_FIT"
    minimum = [max(.6, rooms[room]["minAreaM2"] / depth, door_span if i in entrances else 0.)
               for i, room in enumerate(order)]
    remaining = end - start - math.fsum(minimum)
    if remaining < -SPATIAL.EPS:
        return None, "ROOM_AREA_OR_ENTRY_DOES_NOT_FIT"
    share = max(0., remaining) / len(order)

    layout = dict(schemaVersion=SPATIAL.SCHEMA, outline=outline, rooms=[], axes=[],
                  bearingLines=[], passages=[], loadPaths=[])

    def wall(name, fixed, coordinate, a, b):
        layout["axes"].append(dict(id=name, direction=fixed.upper(), coordinate=coordinate))
        layout["bearingLines"].append(dict(id=name, storyId=story, axisId=name, fromCoordinate=a,
                                           toCoordinate=b, wallThicknessMeters=thickness, cseCandidateId=None))

    def passage(name, host, offset, a, b):
        layout["passages"].append(dict(id=name, kind="DOOR", hostMemberId=host, centerOffset=offset,
                                       sillHeight=0, connects=[a, b], **door))

    for fixed, along in ((direction, cross), (cross, direction)):
        for side in ("Min", "Max"):
            wall("perimeter-" + fixed + "-" + side.lower(), fixed, outline[fixed + side],
                 outline[along + "Min"], outline[along + "Max"])

    left = start
    for i, room in enumerate(order):
        right = end if i == len(order) - 1 else left + minimum[i] + share
        bounds = dict(outline, **{direction + "Min": left, direction + "Max": right})
        layout["rooms"].append(dict(roomId=room, storyId=story, rectangle=bounds))
        if i in entrances:
            passage(f"entrance-{i + 1}", "perimeter-" + cross + "-min",
                    (left + right) / 2 - start, BRIEF.EXTERIOR, room)
        if i < len(order) - 1:
            name = f"partition-{i + 1}"
            wall(name, direction, right, cross_start, cross_end)
            if i in partitions:
                passage(f"connection-{i + 1}", name, depth / 2, room, order[i + 1])
        left = right
    return layout, None


def generate(brief, study):
    if not isinstance(study, dict) or set(study) != {"outline", "storyHeights", "wallThicknessMeters", "door"}:
        raise ValueError("APA_LAYOUT_STUDY_FIELDS_REQUIRED")
    outline = SPATIAL.rectangle(study["outline"], "STUDY_OUTLINE")
    if any(abs(x) > 1e6 for x in outline.values()):
        raise ValueError("COORDINATES_OUT_OF_BOUNDS")
    if len(brief["stories"]) != 1 or not 1 <= len(brief["rooms"]) <= ROOM_COUNT_LIMIT:
        raise ValueError("APA_LAYOUT_STUDY_REQUIRES_ONE_STOREY_AND_1_TO_8_ROOMS")
    sid = brief["stories"][0]["id"]
    heights = study["storyHeights"]
    if not isinstance(heights, dict) or set(heights) != {sid}:
        raise ValueError("STORY_HEIGHTS_MUST_BE_AUTHORED")
    height = SPATIAL.number(heights[sid], "STUDY_STORY_HEIGHT")
    thickness = SPATIAL.number(study["wallThicknessMeters"], "STUDY_WALL_THICKNESS")
    if not 2.4 <= height <= 4.5 or not .15 <= thickness <= .6:
        raise ValueError("APA_LAYOUT_STUDY_HEIGHT_OR_THICKNESS_UNSUPPORTED")
    door = study["door"]
    if not isinstance(door, dict) or set(door) != {"width", "height"}:
        raise ValueError("APA_LAYOUT_STUDY_DOOR_SIZE_REQUIRED")
    door = {k: SPATIAL.number(v, "STUDY_DOOR_" + k.upper()) for k, v in door.items()}
    if door["width"] <= 0 or not 0 < door["height"] <= height:
        raise ValueError("APA_LAYOUT_STUDY_DOOR_SIZE_INVALID")
    rooms = {room["id"]: room for room in brief["rooms"]}
    criteria = [(row["priority"], row["criterion"]) for row in brief["constraints"] if "criterion" in row]
    order = room_order(rooms, criteria)
    entrances, partitions = connection_locations(order, criteria, door["width"])
    variants, rejected = [], []
    for direction in ("x", "y"):
        variant_id = "strip-" + direction
        if min(outline[a + "Max"] - outline[a + "Min"] for a in ("x", "y")) < 1:
            layout, reason = None, "OUTLINE_TOO_SHORT_FOR_PERIMETER_WALL"
        else:
            layout, reason = strip_variant(direction, outline, sid, rooms, order, entrances, partitions,
                                           thickness, door)
        if layout is None:
            rejected.append(dict(id=variant_id, reason=reason))
        else:
            variants.append(dict(id=variant_id, layout=layout, storyHeights={sid: height}))
    return variants, dict(status="CANDIDATES_GENERATED" if variants else "NO_STRIP_LAYOUT_CANDIDATE",
                          method="RECTANGULAR_ROOM_STRIPS", rejected=rejected,
                          doorEndClearanceMeters=DOOR_END_CLEARANCE,
                          assumptions=["ROOM_RECTANGLES_MEASURED_TO_WALL_AXES", "CENTERED_HOSTED_DOORS",
                                       "ROUTES_MAY_CROSS_INTERMEDIATE_ROOMS", "NOMINAL_DOOR_WIDTH",
                                       "STRUCTURE_AND_CODE_REVIEW_REQUIRED"])
