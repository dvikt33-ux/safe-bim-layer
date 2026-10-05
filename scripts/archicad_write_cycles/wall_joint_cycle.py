"""One geometry-derived Archicad Wall continuation and exact cleanup cycle."""
import argparse
import importlib.util
import json
import math
import sys
import urllib.request
from pathlib import Path
import os
import tempfile

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_ROOT = Path(os.environ.get("SAFE_BIM_MVP_EVIDENCE", Path(tempfile.gettempdir()) / "safe-bim-mvp-evidence"))
EVIDENCE = EVIDENCE_ROOT / "wall-joint-cycle"
MODEL_DUMP_SCRIPT = ROOT / "archicad-addon" / "Examples" / "model_dump_v1.py"
PORT = 19723
TOL = 1e-8
LENGTH = 1.0


def load_dump_module():
    spec = importlib.util.spec_from_file_location("model_dump_v1", MODEL_DUMP_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def api_call(command, parameters, stem, timeout=120):
    request = {"command": "API.ExecuteAddOnCommand", "parameters": {
        "addOnCommandId": {"commandNamespace": "TapirCommand", "commandName": command},
        "addOnCommandParameters": parameters}}
    req_bytes = json.dumps(request, ensure_ascii=False).encode("utf-8")
    (EVIDENCE / f"{stem}.request.json").write_bytes(req_bytes)
    req = urllib.request.Request(f"http://127.0.0.1:{PORT}", req_bytes,
                                 {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        raw = response.read()
    (EVIDENCE / f"{stem}.response.json").write_bytes(raw)
    envelope = json.loads(raw)
    if not envelope.get("succeeded"):
        raise RuntimeError(f"{command} failed: {envelope}")
    result = envelope.get("result", {}).get("addOnCommandResponse", {})
    if "error" in result:
        raise RuntimeError(f"{command} returned error: {result}")
    return result


def body_boxes(dump):
    boxes = []
    for element in dump["elements"]:
        for body in element.get("bodies", []):
            vertices = body.get("vertices", [])
            if vertices:
                boxes.append((element["guid"].lower(), tuple(
                    (min(p[i] for p in vertices), max(p[i] for p in vertices))
                    for i in range(3))))
    for element in dump.get("unresolvedBodyOwners", []):
        for body in element.get("bodies", []):
            vertices = body.get("vertices", [])
            if vertices:
                boxes.append((element["guid"].lower(), tuple(
                    (min(p[i] for p in vertices), max(p[i] for p in vertices))
                    for i in range(3))))
    return boxes


def choose_plan(dump):
    story_elevations = {story["index"]: story["elevation"] for story in dump["stories"]}
    boxes = body_boxes(dump)
    walls = [e for e in dump["elements"] if e["type"] == "Wall"]
    candidates = []
    for wall in walls:
        ref = wall.get("placement", {}).get("referenceGeometry", {})
        bindings = wall.get("materialBindings", {})
        if (ref.get("kind") != "WallReferenceLine" or ref.get("arcAngle") != 0
                or ref.get("referenceLineLocation") != 1
                or bindings.get("structureType") != 0 or wall.get("homeStory") not in story_elevations):
            continue
        begin, end = ref["begin"], ref["end"]
        dx, dy = end["x"] - begin["x"], end["y"] - begin["y"]
        line_length = math.hypot(dx, dy)
        if line_length < 0.2 or ref.get("height", 0) < 2.5 or ref.get("thickness", 0) <= 0:
            continue
        material = bindings.get("buildingMaterial", {}).get("guid")
        if not material:
            continue
        ux, uy = dx / line_length, dy / line_length
        thickness = ref["thickness"]
        bottom_z = story_elevations[wall["homeStory"]] + ref["bottomOffsetFromHomeStory"]
        top_z = bottom_z + ref["height"]
        for endpoint, point, direction in (("end", end, 1.0), ("begin", begin, -1.0)):
            ex, ey = ux * direction, uy * direction
            nx, ny = -ey, ex
            corners = [(point["x"] + ex * along + nx * side,
                        point["y"] + ey * along + ny * side)
                       for along in (0.0, LENGTH) for side in (-thickness / 2, thickness / 2)]
            xmin, xmax = min(p[0] for p in corners), max(p[0] for p in corners)
            ymin, ymax = min(p[1] for p in corners), max(p[1] for p in corners)
            blocked = False
            min_clearance = math.inf
            for guid, ((bx0, bx1), (by0, by1), (bz0, bz1)) in boxes:
                if guid == wall["guid"].lower() or bz1 < bottom_z - TOL or bz0 > top_z + TOL:
                    continue
                gx = max(bx0 - xmax, xmin - bx1, 0.0)
                gy = max(by0 - ymax, ymin - by1, 0.0)
                gap = math.hypot(gx, gy)
                min_clearance = min(min_clearance, gap)
                if gap <= TOL:
                    blocked = True
                    break
            if blocked:
                continue
            candidates.append({
                "sourceGuid": wall["guid"], "sourceHomeStory": wall["homeStory"],
                "sourceEndpoint": endpoint,
                "sourceReferenceBegin": begin, "sourceReferenceEnd": end,
                "sourceReferenceLengthMeters": line_length,
                "sourceReferenceLineLocation": "Center", "sourceFlipped": ref.get("flipped"),
                "sourceBaseZ": bottom_z, "sourceHeight": ref["height"],
                "sourceThickness": thickness, "sourceBuildingMaterialGuid": material,
                "start": {"x": point["x"], "y": point["y"]},
                "end": {"x": point["x"] + ex * LENGTH, "y": point["y"] + ey * LENGTH},
                "directionUnitXY": {"x": ex, "y": ey},
                "newLengthMeters": LENGTH, "minimumOtherBodyAabbClearanceMeters":
                    None if math.isinf(min_clearance) else min_clearance,
                "clearanceRule": "proposed wall footprint AABB has no intersection with any other dumped body AABB at overlapping Z",
                "createParameters": {"wallsData": [{
                    "begCoordinate": {"x": point["x"], "y": point["y"]},
                    "endCoordinate": {"x": point["x"] + ex * LENGTH, "y": point["y"] + ey * LENGTH},
                    "floorIndex": wall["homeStory"],
                    "zCoordinate": ref["bottomOffsetFromHomeStory"],
                    "height": ref["height"], "thickness": thickness,
                    "offset": ref["offset"], "arcAngle": 0,
                    "referenceLineLocation": "Center", "structureType": "Basic",
                    "buildingMaterialId": {"guid": material}}]}
            })
    if not candidates:
        raise RuntimeError("No open straight basic Wall endpoint passed 3D body-AABB clearance")
    candidates.sort(key=lambda c: (-float(c["minimumOtherBodyAabbClearanceMeters"] or 0.0),
                                   c["sourceGuid"], c["sourceEndpoint"]))
    plan = candidates[0]
    plan["selection"] = {"eligibleOpenEndpoints": len(candidates),
                         "candidateOrder": "greatest 3D body-AABB clearance, then GUID and endpoint",
                         "sourceWallType": "Wall", "sourceStructureType": "Basic"}
    return plan


def element_map(dump):
    return {e["guid"].lower(): e for e in dump["elements"]}


def bounds_xyz(element):
    vertices = [p for body in element.get("bodies", []) for p in body.get("vertices", [])]
    return [[min(p[i] for p in vertices), max(p[i] for p in vertices)] for i in range(3)]


def verify_add(baseline, after, plan, new_guid):
    before_map, after_map = element_map(baseline), element_map(after)
    source = before_map[plan["sourceGuid"].lower()]
    created = after_map[new_guid.lower()]
    source_after = after_map[plan["sourceGuid"].lower()]
    src_ref = source["placement"]["referenceGeometry"]
    new_ref = created["placement"]["referenceGeometry"]
    p, q = src_ref[plan["sourceEndpoint"]], new_ref["begin"]
    ref_gap = math.dist((p["x"], p["y"]), (q["x"], q["y"]))
    old_story = source["homeStory"]
    new_story = created["homeStory"]
    story_elev = next(s["elevation"] for s in after["stories"] if s["index"] == old_story)
    old_base = story_elev + src_ref["bottomOffsetFromHomeStory"]
    new_base = story_elev + new_ref["bottomOffsetFromHomeStory"]
    src_dx = src_ref["end"]["x"] - src_ref["begin"]["x"]
    src_dy = src_ref["end"]["y"] - src_ref["begin"]["y"]
    if plan["sourceEndpoint"] == "begin":
        src_dx, src_dy = -src_dx, -src_dy
    new_dx = new_ref["end"]["x"] - new_ref["begin"]["x"]
    new_dy = new_ref["end"]["y"] - new_ref["begin"]["y"]
    cos_angle = ((src_dx * new_dx + src_dy * new_dy)
                 / (math.hypot(src_dx, src_dy) * math.hypot(new_dx, new_dy)))
    source_bounds, new_bounds = bounds_xyz(source), bounds_xyz(created)
    aabb_overlaps = []
    for guid, other_box in body_boxes(baseline):
        if guid == plan["sourceGuid"].lower():
            continue
        overlap = [min(new_bounds[i][1], other_box[i][1]) - max(new_bounds[i][0], other_box[i][0])
                   for i in range(3)]
        if all(v > TOL for v in overlap):
            aabb_overlaps.append({"guid": guid, "overlapMeters": overlap})
    source_body = source["bodies"][0]
    new_body = created["bodies"][0]
    source_points = {tuple(p) for p in source_body["vertices"]}
    new_points = {tuple(p) for p in new_body["vertices"]}
    shared_vertices = sorted(source_points & new_points)
    checks = {
        "newGuidAbsentBefore": new_guid.lower() not in before_map,
        "sourceGuidStable": source_after["guid"].lower() == plan["sourceGuid"].lower(),
        "referenceEndpointDistanceMeters": ref_gap,
        "referenceEndpointWithinTolerance": ref_gap <= TOL,
        "directionCosine": cos_angle,
        "directionContinues": cos_angle >= 1.0 - TOL,
        "homeStoryMatches": new_story == old_story,
        "sourceHomeStory": old_story, "newHomeStory": new_story,
        "storyElevationMeters": story_elev,
        "sourceBaseZMeters": old_base, "newBaseZMeters": new_base,
        "baseZDifferenceMeters": abs(old_base - new_base),
        "baseZMatches": abs(old_base - new_base) <= TOL,
        "sourceHeightMeters": src_ref["height"], "newHeightMeters": new_ref["height"],
        "sourceThicknessMeters": src_ref["thickness"], "newThicknessMeters": new_ref["thickness"],
        "referenceLineLocationMatches": new_ref["referenceLineLocation"] == src_ref["referenceLineLocation"],
        "sourceBoundingBoxXYZ": source_bounds, "newBoundingBoxXYZ": new_bounds,
        "sharedSourceNewMeshVertices": shared_vertices,
        "nonSourcePositiveAabbIntersections": aabb_overlaps,
        "aabbNoIncidentalIntersections": not aabb_overlaps,
        "newBodyCount": len(created.get("bodies", [])),
        "pass": ref_gap <= TOL and cos_angle >= 1.0 - TOL and new_story == old_story
                and abs(old_base - new_base) <= TOL
                and new_ref["height"] == src_ref["height"]
                and new_ref["thickness"] == src_ref["thickness"]
                and new_ref["referenceLineLocation"] == src_ref["referenceLineLocation"]
                and not aabb_overlaps and len(created.get("bodies", [])) == 1
    }
    return checks


def stable_elements(dump):
    return {e["guid"].lower(): {k: e.get(k) for k in
            ("guid", "type", "nativeTypeId", "homeStory", "materialBindings", "placement", "relationships", "bodies")}
            for e in dump["elements"]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("plan", "execute"))
    args = parser.parse_args()
    baseline_path = EVIDENCE / "baseline.json"
    plan_path = EVIDENCE / "computed-plan.json"
    baseline = read_json(baseline_path)
    plan = choose_plan(baseline)
    write_json(plan_path, plan)
    print(json.dumps(plan, ensure_ascii=False, indent=2))
    if args.phase == "plan":
        return

    result = api_call("CreateWalls", plan["createParameters"], "create-wall")
    elements = result.get("elements", [])
    ids = [item.get("elementId", {}).get("guid") for item in elements if item.get("elementId", {}).get("guid")]
    if len(ids) != 1:
        raise RuntimeError(f"CreateWalls returned no unique GUID; outcome requires inspection, no retry: {result}")
    new_guid = ids[0]
    write_json(EVIDENCE / "created-guid.json", {"newGuid": new_guid})
    dumper = load_dump_module()
    after, _ = dumper.dump(EVIDENCE / "after-add.json", PORT)
    verification = verify_add(baseline, after, plan, new_guid)
    write_json(EVIDENCE / "join-verification.json", verification)

    # One exact delete of only the GUID returned by this CreateWalls call.
    delete_result = api_call("DeleteElements", {"elements": [{"elementId": {"guid": new_guid}}]}, "delete-new-wall")
    write_json(EVIDENCE / "delete-result.json", delete_result)
    restored, _ = dumper.dump(EVIDENCE / "after-delete.json", PORT)
    before_elements, restored_elements = stable_elements(baseline), stable_elements(restored)
    restoration = {
        "newGuidAbsent": new_guid.lower() not in element_map(restored),
        "baselineGuidSetRestored": set(before_elements) == set(restored_elements),
        "baselineElementRecordsExact": before_elements == restored_elements,
        "baselineElementCount": len(before_elements), "afterDeleteElementCount": len(restored_elements),
        "baselineCounts": baseline["counts"], "afterDeleteCounts": restored["counts"],
        "deleteCommand": "TapirCommand.DeleteElements",
        "plnSaved": False
    }
    restoration["pass"] = (verification["pass"] and restoration["newGuidAbsent"]
                            and restoration["baselineGuidSetRestored"]
                            and restoration["baselineElementRecordsExact"])
    write_json(EVIDENCE / "restoration-verification.json", restoration)
    write_json(EVIDENCE / "cycle-summary.json", {
        "status": "PASS" if restoration["pass"] else "BLOCKED",
        "sourceGuid": plan["sourceGuid"], "newGuid": new_guid,
        "plan": plan, "joinVerification": verification, "restoration": restoration,
        "executionCommand": "python scripts/archicad_write_cycles/wall_joint_cycle.py",
        "plnSaved": False
    })
    print(json.dumps({"status": "PASS" if restoration["pass"] else "BLOCKED",
                      "newGuid": new_guid, "join": verification,
                      "restoration": restoration}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
