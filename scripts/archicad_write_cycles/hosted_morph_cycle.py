"""Read, reproduce, verify, and delete a Morph from the live Archicad model."""
import collections
import contextlib
import importlib.util
import io
import json
import math
import urllib.request
from pathlib import Path
import os
import tempfile

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_ROOT = Path(os.environ.get("SAFE_BIM_MVP_EVIDENCE", Path(tempfile.gettempdir()) / "safe-bim-mvp-evidence"))
EVIDENCE = EVIDENCE_ROOT / "hosted-morph-cycle"
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
    with contextlib.redirect_stdout(io.StringIO()):
        result = module.dump(EVIDENCE / f"{stem}.json", PORT)
    return result[0] if isinstance(result, tuple) else result


def elem_map(dump):
    return {e["guid"].lower(): e for e in dump["elements"]}


def body_bounds(element):
    pts = [p for body in element.get("bodies", []) for p in body.get("vertices", [])]
    if not pts:
        return None
    return tuple((min(float(p[i]) for p in pts), max(float(p[i]) for p in pts)) for i in range(3))


def all_body_bounds(dump):
    result = []
    for e in dump["elements"] + dump.get("unresolvedBodyOwners", []):
        for body in e.get("bodies", []):
            pts = body.get("vertices", [])
            if pts:
                result.append((e["guid"].lower(), tuple(
                    (min(float(p[i]) for p in pts), max(float(p[i]) for p in pts)) for i in range(3))))
    return result


def material_pool(dump):
    return {m["id"]: (m.get("attribute", {}).get("guid") or m.get("guid"))
            for m in dump.get("materials", [])}


def face_material_guids(element, dump):
    pool = material_pool(dump)
    return [pool.get(f.get("materialId")) for b in element.get("bodies", [])
            for f in b.get("faces", [])]


def points_from_dump(element):
    return [tuple(float(c) for c in p) for b in element.get("bodies", []) for p in b.get("vertices", [])]


def identity_transform(transform):
    if not transform or len(transform) != 12:
        return False
    # Model Dump stores translation in slots 3, 7 and 11; inspect only the
    # linear basis for identity orientation.
    indices = {0: 1, 1: 0, 2: 0, 4: 0, 5: 1, 6: 0, 8: 0, 9: 0, 10: 1}
    return all(abs(float(transform[i])-v) <= TOL for i, v in indices.items())


def box_corners(points):
    bounds = tuple((min(p[i] for p in points), max(p[i] for p in points)) for i in range(3))
    corners = {(round(x, 7), round(y, 7), round(z, 7))
               for x in bounds[0] for y in bounds[1] for z in bounds[2]}
    actual = {tuple(round(c, 7) for c in p) for p in points}
    return len(points) == 8 and len(actual) == 8 and actual == corners, bounds


def choose_source(dump):
    candidates = []
    stories = {int(s["index"]): s for s in dump.get("stories", [])}
    for e in dump.get("elements", []):
        bodies = e.get("bodies", [])
        rg = e.get("placement", {}).get("referenceGeometry", {})
        if (e.get("type") != "Morph" or e.get("homeStory") not in stories or len(bodies) != 1):
            continue
        b = bodies[0]
        points = points_from_dump(e)
        is_box, bounds = box_corners(points)
        if (not b.get("closed") or len(b.get("vertices", [])) != 8
                or len(b.get("edges", [])) != 12 or len(b.get("faces", [])) != 6
                or not is_box or not identity_transform(rg.get("placementTransform"))):
            continue
        candidates.append((e, bounds, stories[int(e["homeStory"])]))
    if not candidates:
        return None
    candidates.sort(key=lambda x: (x[0]["guid"].lower(), x[0]["homeStory"]))
    return candidates[0]


def transform_point(point, origin, axes):
    keys = ("x", "y", "z")
    origin_v = tuple(float(origin[k]) for k in keys) if isinstance(origin, dict) else tuple(float(origin[i]) for i in range(3))
    point_v = tuple(float(point[k]) for k in keys) if isinstance(point, dict) else tuple(float(point[i]) for i in range(3))
    axis_v = [tuple(float(axis[k]) for k in keys) if isinstance(axis, dict) else tuple(float(axis[i]) for i in range(3))
              for axis in axes]
    return tuple(origin_v[i] + sum(axis_v[j][i] * point_v[j] for j in range(3))
                 for i in range(3))


def cloud_compare(expected, actual):
    if len(expected) != len(actual):
        return False, math.inf
    remaining = list(actual)
    max_delta = 0.0
    for p in expected:
        deltas = [(max(abs(a-b) for a, b in zip(p, q)), idx) for idx, q in enumerate(remaining)]
        delta, idx = min(deltas)
        max_delta = max(max_delta, delta)
        if delta > TOL:
            return False, max_delta
        remaining.pop(idx)
    return True, max_delta


def native_faces_from_body(body):
    return [{k: p.get(k) for k in ("vertexIds", "filled", "holes", "surfaceId")}
            for p in body.get("polygons", [])]


def model_faces_world(element, dump):
    pool = material_pool(dump)
    b = element["bodies"][0]
    verts = b["vertices"]
    out = []
    for face in b.get("faces", []):
        coords = sorted(tuple(round(float(verts[i][j]), 7) for j in range(3)) for i in face.get("vertices", []))
        out.append((tuple(coords), pool.get(face.get("materialId"))))
    return collections.Counter(out)


def main():
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    baseline = dump_now("baseline")
    selected = choose_source(baseline)
    if selected is None:
        raise RuntimeError("No simple, closed, axis-aligned Morph box with readable story/placement was found")
    source, source_bounds, source_story = selected
    read = api_call("GetDetailsOfElements", {"elements": [{"elementId": {"guid": source["guid"]}}]},
                    "read-source-morph-details")
    native_item = next((x for x in read.get("detailsOfElements", []) if x.get("type") == "Morph"), None)
    if native_item is None:
        raise RuntimeError("GetDetailsOfElements returned no Morph detail for the selected source")
    details = native_item["details"]
    body = details.get("body", {})
    origin = details.get("origin")
    axes = [details.get(k) for k in ("xAxis", "yAxis", "zAxis")]
    if not origin or any(a is None for a in axes) or not body.get("vertices") or not body.get("polygons"):
        raise RuntimeError("Native Morph details lack origin/axes/body geometry required for faithful creation")
    source_local = [tuple(float(v[k]) for k in ("x", "y", "z")) for v in body["vertices"]]
    source_world_native = [transform_point(p, origin, axes) for p in source_local]
    source_world_dump = points_from_dump(source)
    model_read_matches_native, model_read_delta = cloud_compare(source_world_native, source_world_dump)
    if not model_read_matches_native:
        raise RuntimeError(f"Model Dump and native Morph body placement disagree by {model_read_delta} m")

    all_bounds = all_body_bounds(baseline)
    global_max_x = max(b[0][1] for _, b in all_bounds)
    span_x = source_bounds[0][1] - source_bounds[0][0]
    span_y = source_bounds[1][1] - source_bounds[1][0]
    span_z = source_bounds[2][1] - source_bounds[2][0]
    margin = max(span_x, span_y, span_z)
    dx = global_max_x + margin - source_bounds[0][0]
    moved_origin = {k: float(origin[k]) + (dx if k == "x" else 0.0) for k in ("x", "y", "z")}
    expected_world = [tuple(p[i] + (dx if i == 0 else 0.0) for i in range(3)) for p in source_world_native]
    target_bounds = tuple((b[0]+dx, b[1]+dx) if i == 0 else b
                          for i, b in enumerate(source_bounds))
    collisions = [g for g, b in all_bounds if g != source["guid"].lower() and
                  all(min(target_bounds[i][1], b[i][1])-max(target_bounds[i][0], b[i][0]) > TOL
                      for i in range(3))]
    if collisions:
        raise RuntimeError(f"Computed Morph copy placement overlaps model bodies: {collisions[:8]}")
    baseline_map = elem_map(baseline)
    baseline_guids = set(baseline_map)
    source_geometry_before = source["bodies"]
    source_material_guids = face_material_guids(source, baseline)
    # GetDetailsOfElements returns the exact body shape accepted by CreateMorphs.
    create_body = {k: v for k, v in body.items() if k in
                   ("bodyType", "edgeDefault", "vertices", "polygons", "wireEdges", "edgeOverrides")}
    create_data = {"basePoint": moved_origin, "floorIndex": int(source["homeStory"]),
                   "body": create_body, "xAxis": axes[0], "yAxis": axes[1], "zAxis": axes[2]}
    for key in ("buildingMaterialId", "surfaceId", "castShadow", "receiveShadow", "isAutoOnStoryVisibility",
                "showContour", "showFill", "linkToSettings", "displayOption", "viewDepthLimitation",
                "cutFillPen", "cutFillBackgroundPen", "cutLineType", "cutLinePen", "uncutLineType",
                "uncutLinePen", "overheadLineType", "overheadLinePen", "useCoverFillType",
                "outlineContourDisplay", "coverFillType", "coverFillPen", "coverFillBGPen", "use3DHatching",
                "coverFillOrientation", "useDistortedCoverFill", "textureProjectionType",
                "textureProjectionCoords", "level"):
        if key in details:
            create_data[key] = details[key]
    plan = {"sourceGuid": source["guid"], "type": source["type"], "homeStory": source["homeStory"],
        "storyName": source_story.get("displayName"), "storyElevation": source_story.get("elevation"),
        "sourceOrigin": origin, "newOrigin": moved_origin, "axes": axes,
        "placementTransform": source["placement"]["referenceGeometry"]["placementTransform"],
        "dimensions": {"x": span_x, "y": span_y, "z": span_z}, "sourceBounds": source_bounds,
        "expectedBounds": target_bounds, "translation": {"dx": dx, "dy": 0, "dz": 0},
        "globalBodyMaxX": global_max_x, "margin": margin, "computedRule":
        "translate source body minX to current dump global maxX plus margin=max(source body X/Y/Z span)",
        "sourceLocalVertices": body.get("vertices"), "sourceWorldVertices": source_world_dump,
        "sourceFaceCount": len(source["bodies"][0]["faces"]),
        "sourceNativePolygons": body.get("polygons"), "sourceMaterialBindings": source["materialBindings"],
        "sourceFaceMaterialIds": [f.get("materialId") for b in source["bodies"] for f in b["faces"]],
        "sourceFaceMaterialGuids": source_material_guids, "sourceNativeDetails": native_item,
        "modelDumpMatchesNativeBodyTransform": model_read_matches_native,
        "modelDumpNativeMaxVertexDelta": model_read_delta,
        "aabbCollisions": collisions, "createData": create_data}
    write_json(EVIDENCE / "computed-morph-plan.json", plan)

    new_guid = None
    error = None
    geometry_verify = False
    materials_verify = False
    try:
        result = api_call("CreateMorphs", {"morphsData": [create_data]}, "create-morph")
        new_guid = next((e.get("elementId", {}).get("guid") for e in result.get("elements", [])
                         if e.get("elementId", {}).get("guid")), None)
        if not new_guid:
            raise RuntimeError(f"CreateMorphs returned no GUID: {result}")
        write_json(EVIDENCE / "created-guid.json", {"guid": new_guid, "response": result})
        after = dump_now("after-create")
        amap = elem_map(after)
        created = amap.get(new_guid.lower())
        if created is None:
            raise RuntimeError("Created Morph GUID absent from post-create Model Dump")
        new_details_envelope = api_call("GetDetailsOfElements", {"elements": [{"elementId": {"guid": new_guid}}]},
                                        "read-created-morph-details")
        new_item = next((x for x in new_details_envelope.get("detailsOfElements", []) if x.get("type") == "Morph"), None)
        if new_item is None:
            raise RuntimeError("Created Morph native read-back is missing")
        nd = new_item["details"]
        new_axes = [nd.get(k) for k in ("xAxis", "yAxis", "zAxis")]
        new_origin = nd.get("origin")
        nbody = nd.get("body", {})
        new_world_native = [transform_point(tuple(float(v[k]) for k in ("x", "y", "z")), new_origin, new_axes)
                            for v in nbody.get("vertices", [])]
        actual_world_dump = points_from_dump(created)
        vertices_match, max_delta = cloud_compare(expected_world, actual_world_dump)
        native_local_match, native_delta = cloud_compare(source_local,
            [tuple(float(v[k]) for k in ("x", "y", "z")) for v in nbody.get("vertices", [])])
        native_faces_match = native_faces_from_body(body) == native_faces_from_body(nbody)
        model_materials = face_material_guids(created, after)
        materials_verify = (collections.Counter(source_material_guids) == collections.Counter(model_materials)
                            and native_faces_match)
        expected_transform = list(source["placement"]["referenceGeometry"]["placementTransform"])
        expected_transform[3] += dx
        actual_transform = created["placement"]["referenceGeometry"].get("placementTransform", [])
        transform_match = (len(expected_transform) == len(actual_transform) and
                           max((abs(float(a)-float(b)) for a, b in zip(expected_transform, actual_transform)), default=math.inf) <= TOL)
        actual_bounds = body_bounds(created)
        no_collisions = not any(g != source["guid"].lower() and
            all(min(actual_bounds[i][1], b[i][1])-max(actual_bounds[i][0], b[i][0]) > TOL
                for i in range(3)) for g, b in all_bounds)
        geometry_verify = bool(created.get("type") == "Morph"
            and created.get("homeStory") == source.get("homeStory")
            and int(new_item.get("floorIndex", -1)) == int(source.get("homeStory"))
            and vertices_match and native_local_match and native_faces_match and transform_match
            and len(created.get("bodies", [])) == len(source.get("bodies", []))
            and len(created["bodies"][0].get("edges", [])) == len(source["bodies"][0].get("edges", []))
            and len(created["bodies"][0].get("faces", [])) == len(source["bodies"][0].get("faces", []))
            and created["bodies"][0].get("closed") == source["bodies"][0].get("closed")
            and no_collisions and len(after["elements"]) == len(baseline["elements"])+1)
        report = {"sourceGuid": source["guid"], "newGuid": new_guid, "type": created.get("type"),
            "homeStory": created.get("homeStory"), "expectedNewOrigin": moved_origin,
            "actualNewOrigin": new_origin, "axesExpected": axes, "axesActual": new_axes,
            "expectedTransform": expected_transform, "actualTransform": actual_transform,
            "expectedWorldVertices": expected_world, "actualWorldVertices": actual_world_dump,
            "worldVertexCloudMatches": vertices_match, "worldVertexMaxAbsDeltaMeters": max_delta,
            "nativeLocalVertexCloudMatches": native_local_match, "nativeLocalMaxAbsDeltaMeters": native_delta,
            "bodyClosedSourceAndNew": [source["bodies"][0].get("closed"), created["bodies"][0].get("closed")],
            "sourceAndNewVertexEdgeFaceCounts": {
                "source": [len(source["bodies"][0]["vertices"]), len(source["bodies"][0]["edges"]), len(source["bodies"][0]["faces"])],
                "new": [len(created["bodies"][0]["vertices"]), len(created["bodies"][0]["edges"]), len(created["bodies"][0]["faces"])]},
            "nativePolygonsMatch": native_faces_match,
            "bodyBoundsSource": source_bounds, "bodyBoundsNew": actual_bounds,
            "modelDumpFaceMaterialIdsNew": [f.get("materialId") for b in created["bodies"] for f in b["faces"]],
            "faceMaterialGuidsSource": source_material_guids, "faceMaterialGuidsNew": model_materials,
            "aabbNoCollision": no_collisions, "geometryVerification": geometry_verify,
            "materialsReadVerification": materials_verify}
        write_json(EVIDENCE / "geometry-material-verification.json", report)
        if not geometry_verify or not materials_verify:
            raise RuntimeError("Morph geometry/placement/material read-back did not match source data")
    except Exception as exc:
        error = repr(exc)
        write_json(EVIDENCE / "cycle-error.json", {"error": error, "newGuid": new_guid})
    finally:
        if not new_guid:
            try:
                recon = dump_now("create-outcome-reconciliation")
                additions = [e for e in recon["elements"] if e["guid"].lower() not in baseline_guids]
                morphs = [e for e in additions if e.get("type") == "Morph"]
                if len(additions) == 1 and len(morphs) == 1:
                    new_guid = morphs[0]["guid"]
                    write_json(EVIDENCE / "created-guid.json", {"guid": new_guid, "source": "Model Dump reconciliation"})
                elif additions:
                    error = error or f"Unexpected create additions: {[e['guid'] for e in additions]}"
            except Exception as exc:
                error = error or f"Create outcome reconciliation failed: {exc!r}"
        if new_guid:
            try:
                deleted = api_call("DeleteElements", {"elements": [{"elementId": {"guid": new_guid}}]}, "delete-morph")
                write_json(EVIDENCE / "delete-result.json", deleted)
                if not (len(deleted.get("executionResults", [])) == 1 and deleted["executionResults"][0].get("success") is True):
                    error = error or f"DeleteElements unsuccessful: {deleted}"
            except Exception as exc:
                error = error or f"Delete failed: {exc!r}"
                write_json(EVIDENCE / "delete-error.json", {"error": repr(exc), "newGuid": new_guid})
        restored = dump_now("after-delete")

    rmap = elem_map(restored)
    restored_source = rmap.get(source["guid"].lower())
    restoration = {"elementCountBefore": len(baseline["elements"]), "elementCountAfterDelete": len(restored["elements"]),
        "guidSetRestored": set(rmap) == baseline_guids,
        "newGuidAbsent": bool(new_guid and new_guid.lower() not in rmap),
        "sourceGuidPresent": bool(restored_source),
        "sourceGeometryUnchanged": bool(restored_source and restored_source.get("bodies") == source_geometry_before),
        "sourceMaterialsUnchanged": bool(restored_source and face_material_guids(restored_source, restored) == source_material_guids)}
    restoration["restorationPass"] = all((restoration["elementCountBefore"] == restoration["elementCountAfterDelete"],
        restoration["guidSetRestored"], restoration["newGuidAbsent"], restoration["sourceGuidPresent"],
        restoration["sourceGeometryUnchanged"], restoration["sourceMaterialsUnchanged"]))
    write_json(EVIDENCE / "restoration-verification.json", restoration)
    status = "PASS" if geometry_verify and materials_verify and restoration["restorationPass"] and error is None else "BLOCKED"
    summary = {"status": status, "type": "Morph", "sourceGuid": source["guid"], "newGuid": new_guid,
        "sourcePlacement": plan["sourceOrigin"], "newPlacement": plan["newOrigin"], "orientation": plan["axes"],
        "translation": plan["translation"], "sourceBounds": source_bounds, "newExpectedBounds": target_bounds,
        "geometryVerification": geometry_verify, "materialsReadVerification": materials_verify,
        "sourceFaceMaterials": source_material_guids,
        "restoration": restoration, "error": error,
        "commands": ["TapirCommand.GetModelDumpV1", "TapirCommand.GetDetailsOfElements",
                     "TapirCommand.CreateMorphs", "TapirCommand.GetModelDumpV1",
                     "TapirCommand.GetDetailsOfElements", "TapirCommand.DeleteElements", "TapirCommand.GetModelDumpV1"],
        "plnSaved": False}
    write_json(EVIDENCE / "cycle-summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if status != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
