"""Minimal request-driven executor for the proven Archicad MVP write cycles.

Request files contain a structured action and optional source/placement values.
Every invocation starts with a fresh Model Dump; creates are read back and kept.
"""
import argparse
import contextlib
import importlib.util
import io
import json
import math
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CYCLES = ROOT / "scripts" / "archicad_write_cycles"
EVIDENCE = Path(os.environ.get("SAFE_BIM_MVP_EVIDENCE", Path(tempfile.gettempdir()) / "safe-bim-mvp-evidence")) / "executor"
PORT = 19723
TOL = 1e-7


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, CYCLES / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


wall = load("wall_joint_cycle", "wall_joint_cycle.py")
wall_material = load("wall_material_cycle", "wall_material_cycle.py")
window = load("hosted_window_cycle", "hosted_window_cycle.py")
slab = load("hosted_slab_cycle", "hosted_slab_cycle.py")
roof = load("hosted_roof_cycle", "hosted_roof_cycle.py")
morph = load("hosted_morph_cycle", "hosted_morph_cycle.py")


def dump(stem):
    with contextlib.redirect_stdout(io.StringIO()):
        data, _ = wall.load_dump_module().dump(EVIDENCE / f"{stem}.json", PORT)
    return data


def api(command, parameters, stem):
    # Reuse the established Tapir transport/error handling from the proven cycles.
    wall.EVIDENCE.mkdir(parents=True, exist_ok=True)
    return wall.api_call(command, parameters, f"executor-{stem}")


def emap(data):
    return {e["guid"].lower(): e for e in data["elements"]}


def guid_from(result):
    values = [x.get("elementId", {}).get("guid") for x in result.get("elements", [])]
    values = [x for x in values if x]
    if len(values) != 1:
        raise RuntimeError(f"Native create did not return exactly one GUID; inspect outcome before retry: {result}")
    return values[0]


def wall_from_source(data, source_guid, length):
    source = emap(data).get(source_guid.lower())
    if not source or source.get("type") != "Wall":
        raise ValueError(f"sourceGuid is not a Wall in the fresh Model Dump: {source_guid}")
    ref = source.get("placement", {}).get("referenceGeometry", {})
    bind = source.get("materialBindings", {})
    if ref.get("kind") != "WallReferenceLine" or ref.get("arcAngle") != 0:
        raise ValueError("Only straight Walls with a dumped reference line can be continued")
    stories = {s["index"]: float(s["elevation"]) for s in data["stories"]}
    if source.get("homeStory") not in stories:
        raise ValueError("Wall homeStory is absent from current dump")
    a, b = ref["begin"], ref["end"]
    dx, dy = b["x"]-a["x"], b["y"]-a["y"]
    size = math.hypot(dx, dy)
    if size <= TOL or not bind.get("buildingMaterial", {}).get("guid"):
        raise ValueError("Wall reference geometry or structural material is incomplete")
    ux, uy = dx/size, dy/size
    start = b
    end = {"x": start["x"]+ux*length, "y": start["y"]+uy*length}
    params = {"wallsData": [{"begCoordinate": {"x": start["x"], "y": start["y"]},
        "endCoordinate": end, "floorIndex": source["homeStory"],
        "zCoordinate": ref["bottomOffsetFromHomeStory"], "height": ref["height"],
        "thickness": ref["thickness"], "offset": ref["offset"], "arcAngle": 0,
        "referenceLineLocation": "Center", "structureType": "Basic",
        "buildingMaterialId": {"guid": bind["buildingMaterial"]["guid"]}}]}
    return source, {"sourceGuid": source["guid"], "start": {"x": start["x"], "y": start["y"]},
        "end": end, "length": length, "homeStory": source["homeStory"],
        "z": stories[source["homeStory"]]+ref["bottomOffsetFromHomeStory"],
        "height": ref["height"], "thickness": ref["thickness"], "createParameters": params}


def plan_action(action, data, request):
    if action == "create_wall":
        if request.get("sourceGuid"):
            length = float(request.get("length", 1.0))
            _, plan = wall_from_source(data, request["sourceGuid"], length)
        else:
            plan = wall.choose_plan(data)
        return "CreateWalls", plan["createParameters"], plan
    if action == "create_window":
        plan = window.select_wall(data)
        params = {"windowsData": [{"ownerWallId": {"guid": plan["wallGuid"]},
            "centerOffset": plan["centerOffsetAlongHost"], "sillHeight": plan["sillHeightFromWallBase"],
            "width": plan["width"], "height": plan["height"],
            "reflected": False, "refSide": False, "oSide": False}]}
        return "CreateWindows", params, plan
    if action == "create_slab":
        plan = slab.select_template_and_plan(data)
        params = {"slabsData": [{"level": plan["referenceLevelAbsoluteZ"],
            "floorIndex": plan["sourceHomeStory"], "thickness": plan["sourceThickness"],
            "referencePlaneLocation": plan["referencePlaneLocationName"],
            "polygonCoordinates": plan["polygonXY"]}]}
        return "CreateSlabs", params, plan
    if action == "create_roof":
        candidates = sorted((e for e in data["elements"] if e.get("type") == "Roof"
            and e.get("placement", {}).get("referenceGeometry", {}).get("roofClass") == 0
            and len(e.get("bodies", [])) == 1 and len(e["bodies"][0].get("vertices", [])) == 8
            and len(e["bodies"][0].get("faces", [])) == 6
            and e.get("materialBindings", {}).get("structureType") == 0), key=lambda e: e["guid"].lower())
        source = candidates[0] if candidates else None
        if not source:
            raise RuntimeError("No Roof available in current Model Dump")
        details_result = api("GetDetailsOfElements", {"elements": [{"elementId": {"guid": source["guid"]}}]}, "roof-details")
        source, _, _, create_data, plan = roof.select_and_plan(data, details_result)
        return "CreateRoofs", {"roofsData": [create_data]}, plan
    if action == "create_morph":
        selected = morph.choose_source(data)
        if selected is None:
            raise RuntimeError("No supported closed box Morph in current Model Dump")
        source, source_bounds, source_story = selected
        details_result = api("GetDetailsOfElements", {"elements": [{"elementId": {"guid": source["guid"]}}]}, "morph-details")
        item = next((x for x in details_result.get("detailsOfElements", []) if x.get("type") == "Morph"), None)
        if not item:
            raise RuntimeError("Native Morph details are unavailable")
        d = item["details"]
        body = d["body"]
        origin = d["origin"]
        axes = [d[k] for k in ("xAxis", "yAxis", "zAxis")]
        all_bounds = morph.all_body_bounds(data)
        max_x = max(bb[0][1] for _, bb in all_bounds)
        span_x = source_bounds[0][1]-source_bounds[0][0]
        margin = max(span_x, source_bounds[1][1]-source_bounds[1][0], source_bounds[2][1]-source_bounds[2][0])
        dx = max_x + margin - source_bounds[0][0]
        base = {k: float(origin[k]) + (dx if k == "x" else 0.0) for k in ("x", "y", "z")}
        create_body = {k: v for k, v in body.items() if k in
                       ("bodyType", "edgeDefault", "vertices", "polygons", "wireEdges", "edgeOverrides")}
        create_data = {"basePoint": base, "floorIndex": int(source["homeStory"]), "body": create_body,
                       "xAxis": axes[0], "yAxis": axes[1], "zAxis": axes[2]}
        for k in ("buildingMaterialId", "surfaceId", "castShadow", "receiveShadow", "isAutoOnStoryVisibility",
                  "showContour", "showFill", "linkToSettings", "displayOption", "viewDepthLimitation",
                  "cutFillPen", "cutFillBackgroundPen", "cutLineType", "cutLinePen", "uncutLineType",
                  "uncutLinePen", "overheadLineType", "overheadLinePen", "useCoverFillType",
                  "outlineContourDisplay", "coverFillType", "coverFillPen", "coverFillBGPen", "use3DHatching",
                  "coverFillOrientation", "useDistortedCoverFill", "textureProjectionType",
                  "textureProjectionCoords", "level"):
            if k in d:
                create_data[k] = d[k]
        return "CreateMorphs", {"morphsData": [create_data]}, {"sourceGuid": source["guid"], "homeStory": source["homeStory"],
            "sourceBounds": source_bounds, "translation": {"dx": dx, "dy": 0.0, "dz": 0.0}, "createData": create_data,
            "sourceMaterials": morph.face_material_guids(source, data)}
    raise ValueError(f"Unsupported create action: {action}")


def run(request):
    action = request.get("action")
    mode = request.get("mode", "execute")
    if mode not in ("dry-run", "execute"):
        raise ValueError("mode must be dry-run or execute")
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    before = dump("before")
    before_map = emap(before)
    if action == "delete":
        target_guid = request.get("guid")
        if not target_guid or target_guid.lower() not in before_map:
            raise ValueError("delete requires a GUID present in the fresh Model Dump")
        if mode == "dry-run":
            return {"status": "DRY_RUN", "action": action, "guid": target_guid, "present": True}
        result = api("DeleteElements", {"elements": [{"elementId": {"guid": target_guid}}]}, "delete")
        after = dump("after-delete")
        return {"status": "PASS" if target_guid.lower() not in emap(after) else "BLOCKED",
                "action": action, "guid": target_guid, "nativeResult": result,
                "elementCountBefore": len(before["elements"]), "elementCountAfter": len(after["elements"])}
    if action == "change_wall_material":
        source_guid = request.get("guid")
        source = before_map.get((source_guid or "").lower())
        if not source or source.get("type") != "Wall":
            raise ValueError("change_wall_material requires a Wall GUID in the current dump")
        target_surface = request.get("surfaceGuid")
        if not target_surface:
            source_mats = set(wall_material.body_face_material_guids(source, before)[0])
            candidate = next((m for m in before["materials"] if m.get("attribute", {}).get("attributeType") == 5
                              and m.get("attribute", {}).get("guid") not in source_mats), None)
            if candidate is None:
                raise RuntimeError("No alternate project Surface found in current Model Dump")
            target_surface = candidate["attribute"]["guid"]
        bindings = source.get("materialBindings", {})
        details = {"elementId": {"guid": source_guid}}
        for source_key, target_key in (("refMat", "referenceMaterial"),
                                       ("oppMat", "oppositeMaterial"),
                                       ("sidMat", "sideMaterial")):
            native = bindings.get(source_key, {})
            details[target_key] = {"overridden": bool(native.get("overridden"))}
            if native.get("overridden"):
                details[target_key]["attributeId"] = {"guid": native["guid"]}
        details["referenceMaterial"] = {"overridden": True, "attributeId": {"guid": target_surface}}
        params = {"wallsWithDetails": [details]}
        if mode == "dry-run":
            return {"status": "DRY_RUN", "action": action, "guid": source_guid, "surfaceGuid": target_surface}
        result = api("ModifyWalls", params, "wall-material")
        after = dump("after-wall-material")
        new = emap(after).get(source_guid.lower())
        unchanged = bool(new and wall_material.geometry_signature(source) == wall_material.geometry_signature(new))
        ref_binding = (new or {}).get("materialBindings", {}).get("refMat", {})
        binding_changed = bool(ref_binding.get("overridden") and ref_binding.get("guid", "").lower() == target_surface.lower())
        material_ids = {m.get("id"): (m.get("attribute", {}).get("guid") or m.get("guid"))
                        for m in after.get("materials", [])}
        face_material_guids = [material_ids.get(f.get("materialId")) for b in new.get("bodies", [])
                               for f in b.get("faces", [])] if new else []
        face_changed = target_surface.lower() in {str(g).lower() for g in face_material_guids if g}
        ok = wall_material.modify_result_ok(result) and bool(new) and unchanged and binding_changed and face_changed
        return {"status": "PASS" if ok else "BLOCKED", "action": action, "guid": source_guid,
                "surfaceGuid": target_surface, "materialBindings": new.get("materialBindings") if new else None,
                "geometryUnchanged": unchanged, "faceMaterialGuids": face_material_guids,
                "targetSurfaceReachedFaces": face_changed, "nativeResult": result}
    command, params, plan = plan_action(action, before, request)
    if mode == "dry-run":
        return {"status": "DRY_RUN", "action": action, "sourceGuids": [plan.get("sourceGuid") or plan.get("wallGuid")],
                "geometry": {k: plan[k] for k in ("start", "end", "polygonXY", "translation", "homeStory", "z") if k in plan},
                "nativeCommand": command, "parameters": params}
    created_result = api(command, params, action)
    created_guid = guid_from(created_result)
    if action == "create_slab":
        binding = plan["sourceBindings"]
        modify_item = {"elementId": {"guid": created_guid}, "structureType": "Basic",
            "buildingMaterialId": {"guid": binding["buildingMaterial"]["guid"]},
            "topMaterial": {"overridden": False}, "sideMaterial": {"overridden": False},
            "bottomMaterial": {"overridden": False}}
        modify_result = api("ModifySlabs", {"slabsWithDetails": [modify_item]}, "slab-inherit")
        if len(modify_result.get("executionResults", [])) != 1 or not modify_result["executionResults"][0].get("success"):
            raise RuntimeError(f"Created Slab GUID {created_guid}; native material inheritance needs inspection: {modify_result}")
    after = dump("after-create")
    new = emap(after).get(created_guid.lower())
    if new is None:
        return {"status": "BLOCKED", "action": action, "createdGuid": created_guid,
                "reason": "native create returned GUID absent from fresh Model Dump"}
    verification = {"guidPresent": True, "type": new.get("type"), "homeStory": new.get("homeStory"),
                    "bodyCount": len(new.get("bodies", [])), "faceMaterialIds": [f.get("materialId")
                    for b in new.get("bodies", []) for f in b.get("faces", [])]}
    source_guid = plan.get("sourceGuid") or plan.get("wallGuid")
    if action == "create_wall":
        source_ref = before_map[source_guid.lower()]["placement"]["referenceGeometry"]
        new_ref = new["placement"]["referenceGeometry"]
        endpoint = plan.get("sourceEndpoint", "end")
        p, q = source_ref[endpoint], new_ref["begin"]
        verification.update({"jointDistance": math.dist((p["x"], p["y"]), (q["x"], q["y"])),
            "z": new_ref.get("bottomOffsetFromHomeStory"), "homeStoryMatches": new.get("homeStory") == before_map[source_guid.lower()].get("homeStory"),
            "sourceGuidSeenBeforeCreate": source_guid.lower() in before_map,
            "elementCountBefore": len(before["elements"]), "elementCountAfter": len(after["elements"]),
            "direction": {"x": new_ref["end"]["x"]-new_ref["begin"]["x"], "y": new_ref["end"]["y"]-new_ref["begin"]["y"]}})
        verification["pass"] = (new.get("type") == "Wall" and verification["jointDistance"] <= TOL
                                 and verification["homeStoryMatches"] and len(new.get("bodies", [])) == 1)
    else:
        verification["pass"] = new.get("type") == {"create_window": "Window", "create_slab": "Slab",
            "create_roof": "Roof", "create_morph": "Morph"}.get(action) and bool(new.get("bodies"))
        if action == "create_window":
            host = new.get("relationships", {}).get("hostGuid")
            verification.update({"hostGuid": host, "hostMatches": bool(host and host.lower() == plan["wallGuid"].lower()),
                "hostHomeStory": before_map[plan["wallGuid"].lower()].get("homeStory"),
                "positionReference": new.get("placement", {}).get("referenceGeometry")})
            verification["pass"] = (verification["pass"] and verification["hostMatches"]
                                     and new.get("homeStory") == verification["hostHomeStory"])
        elif action == "create_slab":
            source = before_map[plan["sourceGuid"].lower()]
            actual_ref = new.get("placement", {}).get("referenceGeometry", {})
            expected_ref = source.get("placement", {}).get("referenceGeometry", {})
            verification.update({"thickness": actual_ref.get("thickness"),
                "expectedThickness": plan["sourceThickness"], "materialBindings": new.get("materialBindings"),
                "sourceMaterialBindings": plan["sourceBindings"], "geometrySignature": slab.geometry_signature(new)})
            verification["pass"] = (verification["pass"] and new.get("homeStory") == plan["sourceHomeStory"]
                and abs(float(actual_ref.get("thickness", -1))-float(plan["sourceThickness"])) <= TOL
                and new.get("materialBindings", {}).get("buildingMaterial", {}).get("guid") ==
                    plan["sourceBindings"].get("buildingMaterial", {}).get("guid"))
        elif action == "create_roof":
            verification.update({"materialBindings": new.get("materialBindings"),
                "sourcePlan": {k: plan.get(k) for k in ("homeStory", "absoluteZ", "pitchRadians", "thickness", "translatedPolygon")}})
            verification["pass"] = (verification["pass"] and new.get("homeStory") == plan.get("homeStory")
                and abs(float(new.get("placement", {}).get("referenceGeometry", {}).get("thickness", -1))
                        - float(plan.get("thickness", -2))) <= TOL)
    return {"status": "PASS" if verification["pass"] else "BLOCKED", "action": action,
            "createdGuid": created_guid, "sourceGuids": [source_guid] if source_guid else [],
            "geometry": {k: plan[k] for k in ("start", "end", "polygonXY", "translation", "homeStory", "z", "sourceEndpoint") if k in plan},
            "verification": verification, "retained": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", help="JSON request file")
    args = parser.parse_args()
    try:
        request = json.loads(Path(args.request).read_text(encoding="utf-8"))
        print(json.dumps(run(request), ensure_ascii=False, indent=2))
    except Exception as exc:
        print(json.dumps({"status": "BLOCKED", "error": str(exc)}, ensure_ascii=False, indent=2))
        raise SystemExit(2)


if __name__ == "__main__":
    main()
