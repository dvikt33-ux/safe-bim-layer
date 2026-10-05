"""Geometry-derived native Roof create/read-back/material-capability/delete cycle."""
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
EVIDENCE = EVIDENCE_ROOT / "hosted-roof-cycle"
MODEL_DUMP_SCRIPT = ROOT / "archicad-addon" / "Examples" / "model_dump_v1.py"
PORT = 19723
TOL = 1e-7


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def api_call(command, parameters, stem, timeout=120):
    request = {"command": "API.ExecuteAddOnCommand", "parameters": {
        "addOnCommandId": {"commandNamespace": "TapirCommand", "commandName": command},
        "addOnCommandParameters": parameters}}
    raw_request = json.dumps(request, ensure_ascii=False).encode("utf-8")
    (EVIDENCE / f"{stem}.request.json").write_bytes(raw_request)
    req = urllib.request.Request(f"http://127.0.0.1:{PORT}", raw_request,
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
    result = module.dump(EVIDENCE / f"{stem}.json", PORT)
    return result[0] if isinstance(result, tuple) else result


def elem_map(dump):
    return {e["guid"].lower(): e for e in dump["elements"]}


def bounds(element):
    pts = [p for body in element.get("bodies", []) for p in body.get("vertices", [])]
    if not pts:
        return None
    return tuple((min(p[i] for p in pts), max(p[i] for p in pts)) for i in range(3))


def all_bounds(dump):
    result = []
    for e in dump["elements"] + dump.get("unresolvedBodyOwners", []):
        for body in e.get("bodies", []):
            pts = body.get("vertices", [])
            if pts:
                result.append((e["guid"].lower(), tuple(
                    (min(p[i] for p in pts), max(p[i] for p in pts)) for i in range(3))))
    return result


def face_material_guids(element, dump):
    pool = {m["id"]: (m.get("attribute", {}).get("guid") or m.get("guid"))
            for m in dump.get("materials", [])}
    return [pool.get(f.get("materialId")) for b in element.get("bodies", [])
            for f in b.get("faces", [])]


def geometry_signature(element):
    sig = []
    for b in element.get("bodies", []):
        item = {k: b.get(k) for k in ("closed", "curved", "vertices", "edges", "localNormals", "vertexCoordinates")}
        item["faces"] = [{k: v for k, v in f.items() if k not in ("materialId", "nativeStatus")}
                          for f in b.get("faces", [])]
        sig.append(item)
    return sig


def surface_state(bindings):
    out = {}
    for key in ("topMat", "sidMat", "botMat"):
        v = bindings.get(key, {}) or {}
        out[key] = {"overridden": bool(v.get("overridden")),
                    "guid": v.get("guid") if v.get("overridden") else None}
    return out


def vec_points(body, dx=0.0, dy=0.0):
    return [tuple(float(v[i]) + (dx if i == 0 else dy if i == 1 else 0)
                  for i in range(3)) for v in body.get("vertices", [])]


def vertex_cloud_error(expected, actual):
    if len(expected) != len(actual):
        return False, math.inf
    remaining = list(actual)
    max_delta = 0.0
    for point in expected:
        choices = [(max(abs(a-b) for a, b in zip(point, candidate)), i)
                   for i, candidate in enumerate(remaining)]
        delta, index = min(choices)
        max_delta = max(max_delta, delta)
        if delta > TOL:
            return False, max_delta
        remaining.pop(index)
    return True, max_delta


def body_face_topology(body):
    return [{k: face.get(k) for k in ("signedLocalNormalIndex", "contours", "signedNativeEdgeReferences", "vertices", "holes")}
            for face in body.get("faces", [])]


def select_and_plan(dump, details):
    stories = {int(s["index"]): float(s["elevation"]) for s in dump["stories"]}
    candidates = []
    for e in dump["elements"]:
        if e.get("type") != "Roof" or e.get("homeStory") not in stories:
            continue
        bs = e.get("bodies", [])
        rg = e.get("placement", {}).get("referenceGeometry", {})
        mb = e.get("materialBindings", {})
        if (rg.get("roofClass") == 0 and len(bs) == 1 and bs[0].get("closed")
                and len(bs[0].get("vertices", [])) == 8 and len(bs[0].get("edges", [])) == 12
                and len(bs[0].get("faces", [])) == 6 and mb.get("structureType") == 0
                and (mb.get("buildingMaterial") or {}).get("guid")
                and all(not (mb.get(k) or {}).get("overridden") for k in ("topMat", "sidMat", "botMat"))):
            candidates.append(e)
    if not candidates:
        raise RuntimeError("No single-plane Basic Roof with a simple closed body and readable native bindings")
    source = min(candidates, key=lambda e: e["guid"].lower())
    detail_items = details.get("detailsOfElements", [])
    item = next((x for x in detail_items if x.get("type") == "Roof" and
                 x.get("details", {}).get("roofClass") == "SinglePlane"), None)
    if item is None:
        raise RuntimeError("GetDetailsOfElements did not return the selected single-plane Roof")
    d = item["details"]
    if item.get("floorIndex") != source.get("homeStory"):
        raise RuntimeError("Roof dump homeStory and native floorIndex disagree")
    body = source["bodies"][0]
    src_bounds = bounds(source)
    all_b = all_bounds(dump)
    global_max_x = max(bb[0][1] for _, bb in all_b)
    span_x = src_bounds[0][1] - src_bounds[0][0]
    span_y = src_bounds[1][1] - src_bounds[1][0]
    margin = max(span_x, span_y, float(d["thickness"]))
    dx = global_max_x + margin - src_bounds[0][0]
    outline = d["polygonOutline"]
    if len(outline) > 1 and math.hypot(outline[0]["x"]-outline[-1]["x"], outline[0]["y"]-outline[-1]["y"]) <= TOL:
        outline = outline[:-1]
    poly = [{"x": float(p["x"])+dx, "y": float(p["y"])} for p in outline]
    pivot = {"begCoordinate": {"x": float(d["pivotLine"]["begin"]["x"])+dx,
                                "y": float(d["pivotLine"]["begin"]["y"])},
             "endCoordinate": {"x": float(d["pivotLine"]["end"]["x"])+dx,
                                "y": float(d["pivotLine"]["end"]["y"])}}
    target_bounds = ((src_bounds[0][0]+dx, src_bounds[0][1]+dx), src_bounds[1], src_bounds[2])
    colliders = [guid for guid, bb in all_b if guid != source["guid"].lower() and
                 all(min(target_bounds[i][1], bb[i][1])-max(target_bounds[i][0], bb[i][0]) > TOL
                     for i in range(3))]
    if colliders:
        raise RuntimeError(f"Computed Roof placement overlaps existing model body bounds: {colliders[:8]}")
    source_binding = source["materialBindings"]
    structure_type = "Basic" if d["structureType"] == "Basic" else "Composite"
    create_data = {"level": float(d["zCoordinate"]), "floorIndex": int(item["floorIndex"]),
                   "thickness": float(d["thickness"]), "polygonCoordinates": poly,
                   "pivotLine": pivot, "angle": float(d["angle"]),
                   "structureType": structure_type,
                   "buildingMaterialId": {"guid": source_binding["buildingMaterial"]["guid"]}}
    return source, item, d, create_data, {
        "sourceGuid": source["guid"], "homeStory": source["homeStory"],
        "storyElevation": stories[source["homeStory"]], "nativeFloorIndex": item["floorIndex"],
        "absoluteZ": float(d["zCoordinate"]), "level": float(d["level"]),
        "pitchRadians": float(d["angle"]), "pitchDegrees": math.degrees(float(d["angle"])),
        "orientationVector": {"dx": float(d["pivotLine"]["end"]["x"])-float(d["pivotLine"]["begin"]["x"]),
                              "dy": float(d["pivotLine"]["end"]["y"])-float(d["pivotLine"]["begin"]["y"])},
        "pivotLineSource": d["pivotLine"], "polygonSource": outline,
        "thickness": float(d["thickness"]), "roofClass": d["roofClass"],
        "structureType": d["structureType"],
        "buildingMaterialGuid": source_binding["buildingMaterial"]["guid"],
        "surfaceBindings": surface_state(source_binding),
        "sourceFaceMaterialIds": [f.get("materialId") for f in body["faces"]],
        "sourceFaceMaterialGuids": face_material_guids(source, dump),
        "sourceBodyVertices": body["vertices"], "sourceBodyFaceCount": len(body["faces"]),
        "sourceBodyEdgeCount": len(body["edges"]), "sourceBounds": src_bounds,
        "globalBodyMaxX": global_max_x, "computedMargin": margin,
        "translation": {"dx": dx, "dy": 0.0}, "translatedPolygon": poly,
        "translatedPivotLine": pivot, "targetBounds": target_bounds,
        "otherBodyAabbColliders": colliders,
        "translationRule": "translate source body minX to current dump global maxX plus margin=max(source body X span, Y span, Roof thickness)"}


def main():
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    baseline = dump_now("baseline")
    # Candidate GUID is selected from the fresh dump before asking native detail API.
    preliminary = sorted((e for e in baseline["elements"] if e.get("type") == "Roof"
                          and e.get("placement", {}).get("referenceGeometry", {}).get("roofClass") == 0
                          and len(e.get("bodies", [])) == 1
                          and len(e["bodies"][0].get("vertices", [])) == 8
                          and len(e["bodies"][0].get("faces", [])) == 6
                          and e.get("materialBindings", {}).get("structureType") == 0),
                         key=lambda e: e["guid"].lower())
    if not preliminary:
        raise RuntimeError("No eligible single-plane Basic Roof in fresh Model Dump")
    src_guid = preliminary[0]["guid"]
    details_result = api_call("GetDetailsOfElements", {"elements": [{"elementId": {"guid": src_guid}}]},
                              "read-roof-details")
    source, native_item, details, create_data, plan = select_and_plan(baseline, details_result)
    write_json(EVIDENCE / "computed-roof-plan.json", {**plan, "createData": create_data,
               "nativeDetails": native_item, "sourceMaterialBindings": source["materialBindings"]})
    baseline_map = elem_map(baseline)
    baseline_guids = set(baseline_map)
    source_geom_before = geometry_signature(source)
    source_signature_before = {"guid": source["guid"], "geometry": source_geom_before,
                               "faceMaterialGuids": plan["sourceFaceMaterialGuids"],
                               "bindings": source["materialBindings"]}
    created_guid = None
    error = None
    geometry_verify = False
    material_inherit_verify = False
    change_blocker = None
    restored = None
    try:
        created_result = api_call("CreateRoofs", {"roofsData": [create_data]}, "create-roof")
        entries = created_result.get("elements", [])
        created_guid = next((x.get("elementId", {}).get("guid") for x in entries
                             if x.get("elementId", {}).get("guid")), None)
        if not created_guid:
            raise RuntimeError(f"CreateRoofs returned no new GUID: {created_result}")
        write_json(EVIDENCE / "created-guid.json", {"guid": created_guid, "response": created_result})
        after_create = dump_now("after-create")
        amap = elem_map(after_create)
        if created_guid.lower() not in amap:
            raise RuntimeError("Created Roof GUID missing from post-create Model Dump")
        created = amap[created_guid.lower()]
        new_details_result = api_call("GetDetailsOfElements", {"elements": [{"elementId": {"guid": created_guid}}]},
                                      "read-created-roof-details")
        new_native_item = next((x for x in new_details_result.get("detailsOfElements", [])
                                if x.get("type") == "Roof"), None)
        if new_native_item is None:
            raise RuntimeError("New Roof details unavailable on native read-back")
        nd = new_native_item["details"]
        dx = plan["translation"]["dx"]
        src_body = source["bodies"][0]
        new_body = created["bodies"][0] if len(created.get("bodies", [])) == 1 else {}
        vertices_equal, vertex_max_delta = vertex_cloud_error(
            vec_points(src_body, dx=dx), vec_points(new_body)) if new_body else (False, math.inf)
        body_topology_equal = bool(new_body and len(new_body.get("vertices", [])) == len(src_body["vertices"])
                                    and len(new_body.get("edges", [])) == len(src_body["edges"])
                                    and len(new_body.get("faces", [])) == len(src_body["faces"])
                                    and new_body.get("closed") == src_body.get("closed")
                                    and new_body.get("edges") == src_body.get("edges")
                                    and body_face_topology(new_body) == body_face_topology(src_body))
        src_line = plan["pivotLineSource"]
        expected_poly = sorted((round(p["x"], 8), round(p["y"], 8)) for p in plan["translatedPolygon"])
        actual_poly_raw = nd.get("polygonOutline", [])
        if len(actual_poly_raw) > 1 and actual_poly_raw[0] == actual_poly_raw[-1]:
            actual_poly_raw = actual_poly_raw[:-1]
        actual_poly = sorted((round(float(p["x"]), 8), round(float(p["y"]), 8)) for p in actual_poly_raw)
        nb = created.get("materialBindings", {})
        structural_match = (nb.get("structureType") == source["materialBindings"].get("structureType")
                            and (nb.get("buildingMaterial") or {}).get("guid") == plan["buildingMaterialGuid"])
        source_faces = collections.Counter(plan["sourceFaceMaterialGuids"])
        new_faces = collections.Counter(face_material_guids(created, after_create))
        material_inherit_verify = bool(structural_match and surface_state(nb) == plan["surfaceBindings"]
                                       and source_faces == new_faces)
        geometry_verify = bool(created.get("type") == "Roof"
            and created.get("homeStory") == plan["homeStory"]
            and int(new_native_item.get("floorIndex", -1)) == int(plan["nativeFloorIndex"])
            and abs(float(nd.get("zCoordinate", math.nan))-plan["absoluteZ"]) <= TOL
            and abs(float(nd.get("level", math.nan))-plan["level"]) <= TOL
            and abs(float(nd.get("thickness", math.nan))-plan["thickness"]) <= TOL
            and nd.get("structureType") == details.get("structureType")
            and abs(float(nd.get("angle", math.nan))-plan["pitchRadians"]) <= TOL
            and actual_poly == expected_poly and vertices_equal and body_topology_equal
            and len(after_create["elements"]) == len(baseline["elements"])+1)
        report = {"newGuid": created_guid, "sourceGuid": source["guid"], "type": created.get("type"),
            "homeStory": created.get("homeStory"), "nativeFloorIndex": new_native_item.get("floorIndex"),
            "expectedAbsoluteZ": plan["absoluteZ"], "actualAbsoluteZ": nd.get("zCoordinate"),
            "expectedThickness": plan["thickness"], "actualThickness": nd.get("thickness"),
            "expectedPitchRadians": plan["pitchRadians"], "actualPitchRadians": nd.get("angle"),
            "expectedOrientationVector": plan["orientationVector"], "actualPivotLine": nd.get("pivotLine"),
            "polygonExpected": expected_poly, "polygonActual": actual_poly,
            "bodyVerticesTranslatedMatch": vertices_equal, "bodyTopologyMatches": body_topology_equal,
            "bodyVertexMaxAbsDeltaMeters": vertex_max_delta, "vertexToleranceMeters": TOL,
            "sourceBodyBounds": plan["sourceBounds"], "newBodyBounds": bounds(created),
            "structureBindingMatches": structural_match,
            "surfaceBindingsSource": plan["surfaceBindings"], "surfaceBindingsNew": surface_state(nb),
            "faceMaterialGuidsSource": plan["sourceFaceMaterialGuids"],
            "faceMaterialGuidsNew": face_material_guids(created, after_create),
            "noOtherBodyAabbOverlap": not bool(plan["otherBodyAabbColliders"]),
            "geometryVerify": geometry_verify, "materialInheritanceVerify": material_inherit_verify}
        write_json(EVIDENCE / "geometry-material-verification.json", report)
        if not geometry_verify or not material_inherit_verify:
            raise RuntimeError("Created Roof read-back did not match derived geometry/material parameters")

        # The installed native Tapir implementation has no accepted roof-surface write path:
        # CreateRoofs schema has no surface bindings; ModifyRoofs only accepts multi-plane Roofs
        # and its executor rejects this selected single-plane Roof. Preserve this as an explicit blocker.
        change_blocker = {
            "status": "BLOCKED_UNSUPPORTED_NATIVE_ROOF_SURFACE_OVERRIDE",
            "reason": "Current native CreateRoofs schema exposes structure/BM but no topMat/sidMat/botMat; ModifyRoofs rejects single-plane roofs before applying details. No unsupported or substitute binding was attempted.",
            "sourceSurfaceBindings": plan["surfaceBindings"],
            "beforeFaceMaterialIds": [f.get("materialId") for b in created.get("bodies", []) for f in b.get("faces", [])],
            "beforeFaceMaterialGuids": face_material_guids(created, after_create),
            "afterFaceMaterialIds": None,
            "afterFaceMaterialGuids": None,
            "sourceEvidence": "ExtendedElementCommands.cpp: CreateRoofs schema and ModifyRoofs Execute single-plane guard"}
        write_json(EVIDENCE / "roof-material-change-blocker.json", change_blocker)
    except Exception as exc:
        error = repr(exc)
        write_json(EVIDENCE / "cycle-error.json", {"error": error, "createdGuid": created_guid})
    finally:
        if not created_guid:
            try:
                reconciled = dump_now("create-outcome-reconciliation")
                additions = [e for e in reconciled["elements"] if e["guid"].lower() not in baseline_guids]
                roofs = [e for e in additions if e.get("type") == "Roof"]
                if len(additions) == 1 and len(roofs) == 1:
                    created_guid = roofs[0]["guid"]
                    write_json(EVIDENCE / "created-guid.json", {"guid": created_guid,
                               "source": "Model Dump reconciliation after CreateRoofs outcome"})
                elif additions:
                    error = error or f"Unexpected additions after CreateRoofs: {[e['guid'] for e in additions]}"
            except Exception as exc:
                error = error or f"Create outcome reconciliation failed: {exc!r}"
        if created_guid:
            try:
                deletion = api_call("DeleteElements", {"elements": [{"elementId": {"guid": created_guid}}]},
                                    "delete-roof")
                write_json(EVIDENCE / "delete-result.json", deletion)
                if not (len(deletion.get("executionResults", [])) == 1 and
                        deletion["executionResults"][0].get("success") is True):
                    error = error or f"DeleteElements unsuccessful: {deletion}"
            except Exception as exc:
                error = error or f"Delete failed: {exc!r}"
                write_json(EVIDENCE / "delete-error.json", {"error": repr(exc), "createdGuid": created_guid})
        restored = dump_now("after-delete")

    rmap = elem_map(restored)
    restored_source = rmap.get(source["guid"].lower())
    restoration = {"elementCountBefore": len(baseline["elements"]),
        "elementCountAfterDelete": len(restored["elements"]),
        "guidSetRestored": set(rmap) == baseline_guids,
        "newGuidAbsent": bool(created_guid and created_guid.lower() not in rmap),
        "sourceGuidPresent": bool(restored_source),
        "sourceGeometryUnchanged": bool(restored_source and geometry_signature(restored_source) == source_geom_before),
        "sourceBindingsUnchanged": bool(restored_source and restored_source.get("materialBindings") == source_signature_before["bindings"])}
    restoration["restorationPass"] = all((restoration["elementCountBefore"] == restoration["elementCountAfterDelete"],
        restoration["guidSetRestored"], restoration["newGuidAbsent"], restoration["sourceGeometryUnchanged"],
        restoration["sourceBindingsUnchanged"]))
    write_json(EVIDENCE / "restoration-verification.json", restoration)
    status = "PASS" if geometry_verify and material_inherit_verify and not change_blocker and restoration["restorationPass"] and error is None else "BLOCKED"
    summary = {"status": status, "sourceGuid": source["guid"], "newGuid": created_guid,
        "polygon": plan["translatedPolygon"], "pitchRadians": plan["pitchRadians"],
        "pitchDegrees": plan["pitchDegrees"], "orientationVector": plan["orientationVector"],
        "story": plan["homeStory"], "absoluteZ": plan["absoluteZ"], "thickness": plan["thickness"],
        "materialBefore": {"bindings": plan["surfaceBindings"],
            "faceMaterialIds": plan["sourceFaceMaterialIds"],
            "faceMaterialGuids": plan["sourceFaceMaterialGuids"]},
        "materialAfter": change_blocker,
        "geometryVerification": geometry_verify, "materialInheritanceVerification": material_inherit_verify,
        "restoration": restoration, "error": error,
        "commands": ["TapirCommand.GetModelDumpV1", "TapirCommand.GetDetailsOfElements",
            "TapirCommand.CreateRoofs", "TapirCommand.GetModelDumpV1", "TapirCommand.GetDetailsOfElements",
            "TapirCommand.DeleteElements", "TapirCommand.GetModelDumpV1"], "plnSaved": False}
    write_json(EVIDENCE / "cycle-summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if status != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
