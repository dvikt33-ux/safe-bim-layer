"""Create a geometry-derived, material-matched Slab copy and prove cleanup."""
import collections
import importlib.util
import json
import math
import urllib.request
from pathlib import Path
import os
import tempfile

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_ROOT = Path(os.environ.get("SAFE_BIM_MVP_EVIDENCE", Path(tempfile.gettempdir()) / "safe-bim-mvp-evidence"))
EVIDENCE = EVIDENCE_ROOT / "hosted-slab-cycle"
MODEL_DUMP_SCRIPT = ROOT / "archicad-addon" / "Examples" / "model_dump_v1.py"
PORT = 19723
TOL = 1e-7


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def api_call(command, parameters, stem, timeout=120):
    request = {"command": "API.ExecuteAddOnCommand", "parameters": {
        "addOnCommandId": {"commandNamespace": "TapirCommand", "commandName": command},
        "addOnCommandParameters": parameters}}
    payload = json.dumps(request, ensure_ascii=False).encode("utf-8")
    (EVIDENCE / f"{stem}.request.json").write_bytes(payload)
    req = urllib.request.Request(f"http://127.0.0.1:{PORT}", payload,
                                 {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        raw = response.read()
    (EVIDENCE / f"{stem}.response.json").write_bytes(raw)
    envelope = json.loads(raw)
    if not envelope.get("succeeded"):
        raise RuntimeError(f"{command} transport failed: {envelope}")
    result = envelope.get("result", {}).get("addOnCommandResponse", {})
    if "error" in result:
        raise RuntimeError(f"{command} failed: {result}")
    return result


def dump_now(stem):
    spec = importlib.util.spec_from_file_location("model_dump_v1", MODEL_DUMP_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.dump(EVIDENCE / f"{stem}.json", PORT)


def element_map(dump):
    return {e["guid"].lower(): e for e in dump["elements"]}


def body_bounds(element):
    points = [p for b in element.get("bodies", []) for p in b.get("vertices", [])]
    if not points:
        return None
    return tuple((min(p[i] for p in points), max(p[i] for p in points)) for i in range(3))


def all_body_bounds(dump):
    result = []
    for e in dump["elements"] + dump.get("unresolvedBodyOwners", []):
        for body in e.get("bodies", []):
            points = body.get("vertices", [])
            if points:
                result.append((e["guid"].lower(), tuple(
                    (min(p[i] for p in points), max(p[i] for p in points)) for i in range(3))))
    return result


def convex_hull(points):
    pts = sorted(set((float(p[0]), float(p[1])) for p in points))
    if len(pts) < 3:
        raise ValueError("Slab outline has fewer than three unique XY points")

    def cross(o, a, b):
        return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])

    lower = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= TOL:
            lower.pop()
        lower.append(p)
    upper = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= TOL:
            upper.pop()
        upper.append(p)
    hull = lower[:-1] + upper[:-1]
    if len(hull) < 3:
        raise ValueError("Slab outline is degenerate")
    return hull


def signed_area(poly):
    return sum(poly[i][0]*poly[(i+1) % len(poly)][1] -
               poly[(i+1) % len(poly)][0]*poly[i][1] for i in range(len(poly))) / 2


def material_pool(dump):
    return {m["id"]: m.get("attribute", {}).get("guid") or m.get("guid")
            for m in dump.get("materials", [])}


def face_material_guids(element, dump):
    pool = material_pool(dump)
    return [pool.get(face.get("materialId")) for body in element.get("bodies", [])
            for face in body.get("faces", [])]


def simple_surface_binding(binding):
    if not isinstance(binding, dict):
        return {"overridden": False, "surfaceGuid": None}
    overridden = bool(binding.get("overridden"))
    return {"overridden": overridden,
            "surfaceGuid": binding.get("guid") if overridden else None}


def geometry_signature(element):
    sig = []
    for body in element.get("bodies", []):
        item = {k: body.get(k) for k in ("closed", "curved", "transform", "vertices", "edges",
                                        "localNormals", "vertexCoordinates")}
        item["faces"] = [{k: v for k, v in face.items() if k not in ("materialId", "nativeStatus")}
                          for face in body.get("faces", [])]
        sig.append(item)
    return sig


def select_template_and_plan(dump):
    stories = {int(s["index"]): float(s["elevation"]) for s in dump["stories"]}
    candidates = []
    for e in dump["elements"]:
        if e.get("type") != "Slab" or e.get("homeStory") not in stories:
            continue
        bodies = e.get("bodies", [])
        binding = e.get("materialBindings", {})
        ref = e.get("placement", {}).get("referenceGeometry", {})
        if (len(bodies) != 1 or not bodies[0].get("closed")
                or len(bodies[0].get("vertices", [])) != 8
                or len(bodies[0].get("edges", [])) != 12
                or len(bodies[0].get("faces", [])) != 6
                or binding.get("structureType") != 0
                or not (binding.get("buildingMaterial") or {}).get("guid")
                or ref.get("referencePlaneLocation") not in (0, 1, 2, 3)
                or abs(float(ref.get("thickness", 0)) -
                       (max(v[2] for v in bodies[0]["vertices"]) - min(v[2] for v in bodies[0]["vertices"]))) > TOL):
            continue
        xy = convex_hull(bodies[0]["vertices"])
        if len(xy) != 4 or abs(signed_area(xy)) <= TOL:
            continue
        top = binding.get("topMat")
        if not isinstance(top, dict):
            continue
        if any(f.get("holes") for f in bodies[0].get("faces", [])):
            continue
        candidates.append((abs(signed_area(xy)), e, xy))
    if not candidates:
        raise RuntimeError("No simple, closed, rectangular Basic Slab with readable material bindings")
    # Prefer a simple sample whose reference plane is on its Story elevation,
    # then the smallest reliable rectangle to keep the disposable probe modest.
    candidates.sort(key=lambda item: (abs(float(item[1]["placement"]["referenceGeometry"]["levelFromHomeStory"])),
                                      item[0], item[1]["guid"]))
    area, source, source_polygon = candidates[0]
    sref = source["placement"]["referenceGeometry"]
    source_bounds = body_bounds(source)
    if source_bounds is None:
        raise RuntimeError("Selected source Slab has no 3D body bounds")
    # Move the sample just beyond the full current model's geometry envelope.
    # Both the translation and its margin are derived from current dump geometry.
    all_bounds = all_body_bounds(dump)
    global_max_x = max(bb[0][1] for _, bb in all_bounds)
    span_x = source_bounds[0][1] - source_bounds[0][0]
    span_y = source_bounds[1][1] - source_bounds[1][0]
    margin = max(span_x, span_y, float(sref["thickness"]))
    dx = global_max_x + margin - source_bounds[0][0]
    dy = 0.0
    translated = [(x + dx, y + dy) for x, y in source_polygon]
    if signed_area(translated) < 0:
        translated.reverse()
    z_ref = stories[source["homeStory"]] + float(sref["levelFromHomeStory"])
    target_bounds = ((source_bounds[0][0]+dx, source_bounds[0][1]+dx),
                     (source_bounds[1][0]+dy, source_bounds[1][1]+dy), source_bounds[2])
    colliders = []
    for guid, bb in all_bounds:
        if guid == source["guid"].lower():
            continue
        if all(min(target_bounds[i][1], bb[i][1])-max(target_bounds[i][0], bb[i][0]) > TOL
               for i in range(3)):
            colliders.append(guid)
    if colliders:
        raise RuntimeError(f"Computed sample translation collides with model body bounds: {colliders[:8]}")
    return {
        "sourceKind": "existing Slab geometry sample; centerline wall loops were not used because their joined/variable wall boundaries do not directly define a trustworthy slab perimeter",
        "sourceGuid": source["guid"], "sourceHomeStory": source["homeStory"],
        "storyElevation": stories[source["homeStory"]], "referenceLevelAbsoluteZ": z_ref,
        "referencePlaneLocationNative": sref["referencePlaneLocation"],
        "referencePlaneLocationName": ["Top", "CoreTop", "CoreBottom", "Bottom"][sref["referencePlaneLocation"]],
        "sourceLevelFromHomeStory": sref["levelFromHomeStory"],
        "sourceThickness": float(sref["thickness"]), "sourceBindings": source["materialBindings"],
        "sourceFaceMaterialIds": [f.get("materialId") for f in source["bodies"][0]["faces"]],
        "sourceFaceMaterialGuids": face_material_guids(source, dump),
        "sourcePolygonXY": [{"x": x, "y": y} for x, y in source_polygon],
        "sourcePolygonSignedArea": signed_area(source_polygon),
        "sourceBounds": source_bounds, "translation": {"dx": dx, "dy": dy},
        "translationRule": "move source outline to global body max X plus margin=max(source footprint X span, Y span, thickness), all from fresh Model Dump",
        "globalBodyMaxX": global_max_x, "computedClearanceMargin": margin,
        "polygonXY": [{"x": x, "y": y} for x, y in translated],
        "targetBounds": target_bounds, "otherBodyAabbColliders": colliders,
        "area": area, "geometryBefore": source["bodies"][0],
    }


def top_face_indices(element):
    faces = [f for b in element.get("bodies", []) for f in b.get("faces", [])]
    points = [p for b in element.get("bodies", []) for p in b.get("vertices", [])]
    top_z = max(p[2] for p in points)
    indices = []
    for i, f in enumerate(faces):
        ids = f.get("vertices", [])
        if ids and all(abs(points[j][2]-top_z) <= TOL for j in ids):
            indices.append(i)
    return indices


def main():
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    baseline, baseline_metrics = dump_now("baseline")
    plan = select_template_and_plan(baseline)
    write_json(EVIDENCE / "computed-slab-plan.json", {k: v for k, v in plan.items() if k != "geometryBefore"})
    bmap = element_map(baseline)
    baseline_guids = set(bmap)
    source = bmap[plan["sourceGuid"].lower()]
    source_geom_before = geometry_signature(source)
    materials_by_guid = {m.get("attribute", {}).get("guid") or m.get("guid"): m for m in baseline["materials"]}
    source_material_guids = set(plan["sourceFaceMaterialGuids"])
    target_surface = next((m for m in baseline["materials"]
                           if m.get("attribute", {}).get("guid") and
                           m["attribute"]["guid"] not in source_material_guids and
                           m.get("attribute", {}).get("attributeType") == 5), None)
    if not target_surface:
        raise RuntimeError("No existing project Surface is available for a safe temporary top override")
    target_surface_guid = target_surface["attribute"]["guid"]
    target_surface_id = target_surface["id"]
    create_data = {
        "level": plan["referenceLevelAbsoluteZ"],
        "floorIndex": plan["sourceHomeStory"],
        "thickness": plan["sourceThickness"],
        "referencePlaneLocation": plan["referencePlaneLocationName"],
        "polygonCoordinates": plan["polygonXY"],
    }
    created_guid = None
    error = None
    after_inherit = after_material = restored = None
    after_inherit_metrics = after_material_metrics = restored_metrics = None
    inheritance_verify = material_change_verify = False
    try:
        result = api_call("CreateSlabs", {"slabsData": [create_data]}, "create-slab")
        entry = result.get("elements", [{}])[0]
        created_guid = entry.get("elementId", {}).get("guid")
        if not created_guid:
            raise RuntimeError(f"CreateSlabs returned no GUID: {result}")
        write_json(EVIDENCE / "created-guid.json", {"guid": created_guid, "response": result})
        # Apply the source Slab's native structural binding and its unoverridden
        # Surface bindings through the existing ModifySlabs API.
        binding = plan["sourceBindings"]
        structure = {"structureType": "Basic",
                     "buildingMaterialId": {"guid": binding["buildingMaterial"]["guid"]},
                     "topMaterial": {"overridden": False},
                     "sideMaterial": {"overridden": False},
                     "bottomMaterial": {"overridden": False}}
        modify_item = {"elementId": {"guid": created_guid}, **structure}
        modify_result = api_call("ModifySlabs", {"slabsWithDetails": [modify_item]}, "inherit-slab-bindings")
        modify_ok = (len(modify_result.get("executionResults", [])) == 1 and
                     modify_result["executionResults"][0].get("success") is True)
        if not modify_ok:
            raise RuntimeError(f"ModifySlabs inheritance failed: {modify_result}")
        after_inherit, after_inherit_metrics = dump_now("after-inherit")
        imap = element_map(after_inherit)
        if created_guid.lower() not in imap:
            raise RuntimeError("Created Slab GUID absent from post-create Model Dump")
        created = imap[created_guid.lower()]
        actual_ref = created.get("placement", {}).get("referenceGeometry", {})
        actual_bounds = body_bounds(created)
        actual_poly = convex_hull([v for b in created.get("bodies", []) for v in b.get("vertices", [])])
        expected_poly = [(p["x"], p["y"]) for p in plan["polygonXY"]]
        # Compare polygon as an unordered exact vertex set, and z extent to the
        # native reference plane + thickness semantics.
        poly_actual = sorted((round(x, 8), round(y, 8)) for x, y in actual_poly)
        poly_expected = sorted((round(x, 8), round(y, 8)) for x, y in expected_poly)
        bindings = created.get("materialBindings", {})
        effective_bindings = {
            "structureType": bindings.get("structureType"),
            "buildingMaterialGuid": (bindings.get("buildingMaterial") or {}).get("guid"),
            "compositeGuid": (bindings.get("composite") or {}).get("guid"),
            "topMat": simple_surface_binding(bindings.get("topMat")),
            "sideMat": simple_surface_binding(bindings.get("sidMat", bindings.get("sideMat"))),
            "bottomMat": simple_surface_binding(bindings.get("botMat", bindings.get("bottomMat"))),
        }
        source_bindings = {
            "structureType": binding.get("structureType"),
            "buildingMaterialGuid": (binding.get("buildingMaterial") or {}).get("guid"),
            "compositeGuid": (binding.get("composite") or {}).get("guid"),
            "topMat": simple_surface_binding(binding.get("topMat")),
            "sideMat": simple_surface_binding(binding.get("sidMat", binding.get("sideMat"))),
            "bottomMat": simple_surface_binding(binding.get("botMat", binding.get("bottomMat"))),
        }
        new_face_materials = face_material_guids(created, after_inherit)
        src_face_materials = plan["sourceFaceMaterialGuids"]
        inherited_geom_equal = (len(actual_poly) == len(expected_poly) and
                                poly_actual == poly_expected and actual_bounds is not None and
                                abs(actual_bounds[2][1]-plan["referenceLevelAbsoluteZ"]) <= TOL and
                                abs(actual_bounds[2][0]-(plan["referenceLevelAbsoluteZ"]-plan["sourceThickness"])) <= TOL)
        inheritance_verify = bool(
            created.get("type") == "Slab" and created.get("homeStory") == plan["sourceHomeStory"]
            and actual_ref.get("referencePlaneLocation") == plan["referencePlaneLocationNative"]
            and abs(float(actual_ref.get("thickness", -1))-plan["sourceThickness"]) <= TOL
            and inherited_geom_equal and source_bindings == effective_bindings
            and collections.Counter(src_face_materials) == collections.Counter(new_face_materials)
            and len(after_inherit["elements"]) == len(baseline["elements"]) + 1
        )
        inheritance_report = {
            "newGuid": created_guid, "type": created.get("type"), "homeStory": created.get("homeStory"),
            "expectedHomeStory": plan["sourceHomeStory"], "referenceGeometry": actual_ref,
            "expectedReferenceLevelAbsoluteZ": plan["referenceLevelAbsoluteZ"],
            "actualBodyBounds": actual_bounds, "expectedBodyZ": [
                plan["referenceLevelAbsoluteZ"]-plan["sourceThickness"], plan["referenceLevelAbsoluteZ"]],
            "polygonExpectedXY": expected_poly, "polygonActualXY": poly_actual,
            "polygonMatches": poly_actual == poly_expected,
            "structureAndSurfaceBindingsExpected": source_bindings,
            "structureAndSurfaceBindingsActual": effective_bindings,
            "faceMaterialGuidsSource": src_face_materials,
            "faceMaterialGuidsNewBeforeOverride": new_face_materials,
            "faceMaterialBindingsMatch": collections.Counter(src_face_materials) == collections.Counter(new_face_materials),
            "bodyBoundsOutsideExistingGeometry": not any(
                all(min(actual_bounds[i][1], bb[i][1])-max(actual_bounds[i][0], bb[i][0]) > TOL
                    for i in range(3))
                for guid, bb in all_body_bounds(baseline) if guid != plan["sourceGuid"].lower()),
            "inheritancePass": inheritance_verify,
        }
        write_json(EVIDENCE / "geometry-material-inheritance-verification.json", inheritance_report)
        if not inheritance_verify:
            raise RuntimeError("Slab geometry/material inheritance read-back did not match the source template")

        # A surface override is supported by the existing native ModifySlabs API.
        inherit_geom = geometry_signature(created)
        before_material_face_guids = face_material_guids(created, after_inherit)
        modify_surface = api_call("ModifySlabs", {"slabsWithDetails": [{
            "elementId": {"guid": created_guid},
            "topMaterial": {"overridden": True, "attributeId": {"guid": target_surface_guid}}
        }]}, "change-slab-top-surface")
        if not (len(modify_surface.get("executionResults", [])) == 1 and
                modify_surface["executionResults"][0].get("success") is True):
            raise RuntimeError(f"ModifySlabs surface override failed: {modify_surface}")
        after_material, after_material_metrics = dump_now("after-surface-change")
        mmap = element_map(after_material)
        changed = mmap[created_guid.lower()]
        changed_bind = changed.get("materialBindings", {})
        after_face_guids = face_material_guids(changed, after_material)
        top_indices = top_face_indices(created)
        after_top_indices = top_face_indices(changed)
        changed_faces = [i for i, (a, b) in enumerate(zip(before_material_face_guids, after_face_guids)) if a != b]
        new_geom_equal = inherit_geom == geometry_signature(changed)
        target_seen = target_surface_guid in after_face_guids
        expected_top_change = bool(top_indices and top_indices == after_top_indices and
                                   changed_bind.get("topMat", {}).get("overridden") is True and
                                   changed_bind.get("topMat", {}).get("guid") == target_surface_guid and
                                   target_seen and all(i in top_indices for i in changed_faces) and
                                   all(after_face_guids[i] == target_surface_guid for i in top_indices))
        material_change_verify = bool(new_geom_equal and expected_top_change and
                                      changed.get("guid", "").lower() == created_guid.lower() and
                                      changed.get("homeStory") == plan["sourceHomeStory"] and
                                      abs(float(changed.get("placement", {}).get("referenceGeometry", {}).get("thickness", -1))-
                                          plan["sourceThickness"]) <= TOL)
        write_json(EVIDENCE / "surface-override-verification.json", {
            "guidStable": changed.get("guid", "").lower() == created_guid.lower(),
            "surfaceAttributeGuid": target_surface_guid, "surfaceModelMaterialId": target_surface_id,
            "surfaceName": target_surface.get("name"),
            "materialIdsBefore": [f.get("materialId") for b in created.get("bodies", []) for f in b.get("faces", [])],
            "faceMaterialGuidsBefore": before_material_face_guids,
            "materialIdsAfter": [f.get("materialId") for b in changed.get("bodies", []) for f in b.get("faces", [])],
            "faceMaterialGuidsAfter": after_face_guids, "changedFaceIndices": changed_faces,
            "topFaceIndices": top_indices, "topFacesNowUseTargetSurface": expected_top_change,
            "geometryUnchanged": new_geom_equal,
            "materialChangePass": material_change_verify,
        })
        if not material_change_verify:
            raise RuntimeError("Top Surface override read-back or geometry stability check failed")
    except Exception as exc:
        error = repr(exc)
        write_json(EVIDENCE / "cycle-error.json", {"error": error, "createdGuid": created_guid})
    finally:
        if not created_guid:
            try:
                reconciled, _ = dump_now("create-outcome-reconciliation")
                additions = [e for e in reconciled["elements"] if e["guid"].lower() not in baseline_guids]
                slabs = [e for e in additions if e.get("type") == "Slab"]
                if len(additions) == 1 and len(slabs) == 1:
                    created_guid = slabs[0]["guid"]
                    write_json(EVIDENCE / "created-guid.json", {
                        "guid": created_guid, "source": "Model Dump reconciliation"})
                elif additions:
                    error = error or f"unexpected additions after CreateSlabs: {[e['guid'] for e in additions]}"
            except Exception as exc:
                error = error or f"create outcome reconciliation failed: {exc!r}"
        if created_guid:
            try:
                delete_result = api_call("DeleteElements", {"elements": [{"elementId": {"guid": created_guid}}]},
                                         "delete-slab")
                write_json(EVIDENCE / "delete-result.json", delete_result)
                if not (len(delete_result.get("executionResults", [])) == 1 and
                        delete_result["executionResults"][0].get("success") is True):
                    error = error or f"DeleteElements unsuccessful: {delete_result}"
            except Exception as exc:
                error = error or f"delete failed: {exc!r}"
                write_json(EVIDENCE / "delete-error.json", {"error": repr(exc), "createdGuid": created_guid})
        restored, restored_metrics = dump_now("after-delete")

    rmap = element_map(restored)
    restored_source = rmap.get(plan["sourceGuid"].lower())
    restore_detail = {
        "elementCountBefore": len(baseline["elements"]), "elementCountAfterDelete": len(restored["elements"]),
        "guidSetRestored": set(rmap) == baseline_guids,
        "newGuidAbsent": created_guid.lower() not in rmap if created_guid else None,
        "sourceSlabGeometryUnchanged": bool(restored_source and geometry_signature(restored_source) == source_geom_before),
    }
    restore_detail["restorationPass"] = bool(
        restore_detail["elementCountBefore"] == restore_detail["elementCountAfterDelete"]
        and restore_detail["guidSetRestored"] and restore_detail["newGuidAbsent"]
        and restore_detail["sourceSlabGeometryUnchanged"])
    write_json(EVIDENCE / "restoration-verification.json", restore_detail)
    summary = {
        "status": "PASS" if inheritance_verify and material_change_verify and restore_detail["restorationPass"] and error is None else "BLOCKED",
        "sourceGuid": plan["sourceGuid"], "newGuid": created_guid,
        "plan": {k: v for k, v in plan.items() if k != "geometryBefore"},
        "inheritanceVerify": inheritance_verify, "materialChangeVerify": material_change_verify,
        "restoration": restore_detail, "error": error,
        "targetSurface": {"guid": target_surface_guid, "modelMaterialId": target_surface_id,
                          "name": target_surface.get("name")},
        "commands": ["TapirCommand.GetModelDumpV1", "TapirCommand.CreateSlabs",
                     "TapirCommand.ModifySlabs", "TapirCommand.GetModelDumpV1",
                     "TapirCommand.ModifySlabs", "TapirCommand.GetModelDumpV1",
                     "TapirCommand.DeleteElements", "TapirCommand.GetModelDumpV1"],
        "plnSaved": False,
    }
    write_json(EVIDENCE / "cycle-summary.json", summary)
    print(json.dumps({k: v for k, v in summary.items() if k not in
                      ("baselineMetrics", "afterInheritMetrics", "afterMaterialMetrics", "restoredMetrics")},
                     ensure_ascii=False, indent=2))
    if summary["status"] != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
