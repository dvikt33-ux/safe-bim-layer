from pathlib import Path
import json

from safe_bim_layer import TapirClient, SafeBIMLayer, SafeBIMError


BRIDGE = "http://127.0.0.1:19723"
PROJECT = r"C:\Users\Admin\Downloads\Test_House.pln"
SCHEMA = str(Path(__file__).with_name("tapir-1.5.8.json"))
CONTOUR = [
    {"x": 0.0, "y": 0.0}, {"x": 10.0, "y": 0.0},
    {"x": 10.0, "y": 8.0}, {"x": 0.0, "y": 8.0},
    {"x": 0.0, "y": 0.0},
]


def response_items(response):
    return response.get("result", {}).get("addOnCommandResponse", {})


def guids(response):
    return [x["elementId"]["guid"] for x in response_items(response).get("elements", [])]


def read_type(client, element_type):
    found = client.call("GetElementsByType", {"elementType": element_type})
    ids = guids(found)
    details = []
    if ids:
        read = client.call("GetDetailsOfElements", {
            "elements": [{"elementId": {"guid": g}} for g in ids]
        })
        details = response_items(read).get("detailsOfElements", [])
    return list(zip(ids, details))


def same(a, b, tol=1e-9):
    return isinstance(a, (int, float)) and isinstance(b, (int, float)) and abs(a - b) <= tol


def wall_key(detail):
    d = detail.get("details", {})
    return (
        detail.get("floorIndex"),
        tuple(d.get("begCoordinate", {}).get(k) for k in ("x", "y")),
        tuple(d.get("endCoordinate", {}).get(k) for k in ("x", "y")),
    )


def slab_matches(detail, floor_index, level):
    d = detail.get("details", {})
    return (detail.get("floorIndex") == floor_index and
            same(d.get("zCoordinate"), level) and
            same(d.get("thickness"), 0.20) and
            d.get("structureType") == "Basic")


def modify_slab_to_basic(client, guid, z):
    payload = {"slabsWithDetails": [{
        "elementId": {"guid": guid},
        "zCoordinate": float(z),
        "thickness": 0.20,
        "structureType": "Basic",
        "referencePlaneLocation": "Top",
    }]}
    client.validate_payload("ModifySlabs", payload)
    result = client.call("ModifySlabs", payload)
    read = client.call("GetDetailsOfElements", {
        "elements": [{"elementId": {"guid": guid}}]
    })
    detail = response_items(read).get("detailsOfElements", [{}])[0]
    actual = detail.get("details", {})
    ok = (detail.get("floorIndex") == 1 and actual.get("structureType") == "Basic" and
          same(actual.get("thickness"), 0.20) and same(actual.get("zCoordinate"), z))
    return result, read, ok


def create_slab_at_absolute_z(client, z):
    payload = {"slabsData": [{
        "level": float(z),
        "thickness": 0.20,
        "polygonCoordinates": CONTOUR[:-1],
    }]}
    client.validate_payload("CreateSlabs", payload)
    result = client.call("CreateSlabs", payload)
    ids = guids(result)
    if len(ids) != 1:
        return result, None, False
    guid = ids[0]
    modify_result, read, ok = modify_slab_to_basic(client, guid, z)
    return {"create": result, "modify": modify_result}, read, ok


def window_matches(detail, wall_guid, offset):
    d = detail.get("details", {})
    return (detail.get("floorIndex") == 1 and
            d.get("ownerElementId", {}).get("guid") == wall_guid and
            same(d.get("centerOffset"), offset) and
            same(d.get("width"), 1.5) and same(d.get("height"), 1.4) and
            same(d.get("sillHeight"), 0.9))


def find_story_navigator_guid(tree, story_index):
    """Find the Project Map StoryItem whose prefix is the requested index."""
    if isinstance(tree, dict):
        item = tree.get("navigatorItem", tree)
        if item.get("type") == "StoryItem" and item.get("prefix") == str(story_index):
            return item.get("navigatorItemId", {}).get("guid")
        for value in tree.values():
            found = find_story_navigator_guid(value, story_index)
            if found:
                return found
    elif isinstance(tree, list):
        for value in tree:
            found = find_story_navigator_guid(value, story_index)
            if found:
                return found
    return None


def report(label, result):
    print(f"{label}: {result}")
    if result != "PASS":
        raise SafeBIMError(label)


def main():
    if not Path(PROJECT).exists():
        raise FileNotFoundError(PROJECT)
    client = TapirClient(BRIDGE, SCHEMA)
    bim = SafeBIMLayer(client)

    info = client.call("GetProjectInfo", {})
    actual_path = response_items(info).get("projectPath")
    if actual_path != PROJECT:
        raise SafeBIMError(f"Refusing wrong project: {actual_path!r}")
    stories = response_items(client.call("GetStories", {}))
    print("PROJECT:", actual_path)
    print("STORIES:", json.dumps(stories, ensure_ascii=False))
    print("ACTIVE_STORY_BEFORE:", stories.get("actStory"))

    walls = read_type(client, "Wall")
    windows = read_type(client, "Window")
    slabs = read_type(client, "Slab")
    print("INVENTORY_BEFORE:", json.dumps({
        "walls": [(g, d.get("floorIndex"), wall_key(d)) for g, d in walls],
        "windows": len(windows),
        "slabs": [(g, d.get("floorIndex"), d.get("details", {}).get("level")) for g, d in slabs],
    }, ensure_ascii=False))

    expected_walls = [
        (1, (0.0, 0.0), (10.0, 0.0)),
        (1, (10.0, 0.0), (10.0, 8.0)),
        (1, (10.0, 8.0), (0.0, 8.0)),
        (1, (0.0, 8.0), (0.0, 0.0)),
    ]
    wall2 = []
    for expected in expected_walls:
        matches = [(g, d) for g, d in walls if wall_key(d) == expected]
        if len(matches) != 1:
            raise SafeBIMError(f"Expected exactly one existing second-floor wall for {expected}, got {len(matches)}")
        wall2.append(matches[0][0])
    print("SECOND_FLOOR_WALLS_CONFIRMED:", wall2)

    # Resolve the actual Project Map StoryItem, then use the schema-supported
    # ChangeWindow navigatorItemId form. The storyIndex-only form returned
    # success but did not change actStory in this Archicad session.
    tree_response = client.call("GetNavigatorItemTree", {"navigatorMapId": "ProjectMap"})
    story_guid = find_story_navigator_guid(
        response_items(tree_response).get("navigatorItemTree"), 1)
    if not story_guid:
        raise SafeBIMError("Could not resolve Project Map story navigator item for story 1")
    change_response = client.change_floor_plan_navigator_item(story_guid)
    report("CHANGE_WINDOW_TO_STORY_1", "PASS" if response_items(change_response).get("success") else "FAIL")
    active_after = response_items(client.call("GetStories", {})).get("actStory")
    if active_after != 1:
        raise SafeBIMError(f"Story switch read-back mismatch: {active_after}")
    print("ACTIVE_STORY_AFTER:", active_after)

    existing_slabs = [(g, d) for g, d in slabs]
    intermediate = [(g, d) for g, d in existing_slabs if d.get("floorIndex") == 1]
    if len(intermediate) > 1:
        raise SafeBIMError(f"Duplicate second-floor slabs: {len(intermediate)}")
    if intermediate and slab_matches(intermediate[0][1], 1, 3.0):
        report("INTERMEDIATE_SLAB_EXISTING_READBACK", "PASS")
    elif intermediate:
        _, _, ok = modify_slab_to_basic(client, intermediate[0][0], 3.0)
        report("INTERMEDIATE_SLAB_REPAIRED_READBACK", "PASS" if ok else "FAIL")
    else:
        _, _, ok = create_slab_at_absolute_z(client, 3.0)
        report("INTERMEDIATE_SLAB_CREATED_READBACK", "PASS" if ok else "FAIL")

    existing_slabs = read_type(client, "Slab")
    top = [(g, d) for g, d in existing_slabs if slab_matches(d, 2, 6.0)]
    if len(top) > 1:
        raise SafeBIMError(f"Duplicate top slabs: {len(top)}")
    if top:
        report("TOP_SLAB_EXISTING_READBACK", "PASS")
    else:
        _, _, ok = create_slab_at_absolute_z(client, 6.0)
        report("TOP_SLAB_CREATED_READBACK", "PASS" if ok else "FAIL")

    requested_windows = [(0, 2.5), (0, 7.5), (1, 4.0), (2, 2.5), (2, 7.5), (3, 4.0)]
    for number, (wall_index, offset) in enumerate(requested_windows, 1):
        matches = [(g, d) for g, d in read_type(client, "Window") if window_matches(d, wall2[wall_index], offset)]
        if len(matches) > 1:
            raise SafeBIMError(f"Duplicate second-floor window #{number}: {len(matches)}")
        if matches:
            report(f"WINDOW_2_{number}_EXISTING_READBACK", "PASS")
        else:
            created = bim.insert_window(wall2[wall_index], {
                "centerOffset": offset, "sillHeight": 0.9,
                "width": 1.5, "height": 1.4,
            })
            report(f"WINDOW_2_{number}_CREATED_READBACK", created.get("status"))

    final_walls = read_type(client, "Wall")
    final_windows = read_type(client, "Window")
    final_slabs = read_type(client, "Slab")
    counts = {
        "walls_floor_0": sum(d.get("floorIndex") == 0 for _, d in final_walls),
        "walls_floor_1": sum(d.get("floorIndex") == 1 for _, d in final_walls),
        "windows_floor_0": sum(d.get("floorIndex") == 0 for _, d in final_windows),
        "windows_floor_1": sum(d.get("floorIndex") == 1 for _, d in final_windows),
        "slabs_floor_0": sum(d.get("floorIndex") == 0 for _, d in final_slabs),
        "slabs_floor_1": sum(d.get("floorIndex") == 1 for _, d in final_slabs),
        "slabs_floor_2": sum(d.get("floorIndex") == 2 for _, d in final_slabs),
    }
    print("FINAL_COUNTS:", json.dumps(counts, ensure_ascii=False))
    expected = {"walls_floor_0": 4, "walls_floor_1": 4, "windows_floor_0": 6,
                "windows_floor_1": 6, "slabs_floor_0": 1, "slabs_floor_1": 1,
                "slabs_floor_2": 1}
    if counts != expected:
        raise SafeBIMError(f"Final inventory mismatch: {counts} != {expected}")
    print("TEST HOUSE CONTINUATION: PASS")


if __name__ == "__main__":
    main()
