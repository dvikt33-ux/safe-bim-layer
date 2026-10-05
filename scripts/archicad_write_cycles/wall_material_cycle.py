"""Geometry-derived Wall continuation, surface inheritance/change, and cleanup."""
import argparse
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
EVIDENCE = EVIDENCE_ROOT / "wall-material-cycle"
MODEL_DUMP_SCRIPT = ROOT / "archicad-addon" / "Examples" / "model_dump_v1.py"
PORT = 19723
WALL_LENGTH = 1.0
TOL = 1e-8


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


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
        raise RuntimeError(f"{command} failed: {envelope}")
    result = envelope.get("result", {}).get("addOnCommandResponse", {})
    if "error" in result:
        raise RuntimeError(f"{command} returned error: {result}")
    return result


def dump_now(stem):
    spec = importlib.util.spec_from_file_location("model_dump_v1", MODEL_DUMP_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.dump(EVIDENCE / f"{stem}.json", PORT)[0]


def body_boxes(dump):
    result = []
    for e in dump["elements"] + dump.get("unresolvedBodyOwners", []):
        for b in e.get("bodies", []):
            vs = b.get("vertices", [])
            if vs:
                result.append((e["guid"].lower(), [(min(p[i] for p in vs), max(p[i] for p in vs))
                                                   for i in range(3)]))
    return result


def wall_map(dump):
    return {e["guid"].lower(): e for e in dump["elements"]}


def body_face_material_guids(element, dump):
    pool = {m["id"]: m.get("attribute", {}).get("guid") for m in dump["materials"]}
    result = []
    for body in element.get("bodies", []):
        result.append([pool.get(face.get("materialId")) for face in body.get("faces", [])])
    return result


def face_material_counts(element, dump):
    return dict(collections.Counter(guid for body in body_face_material_guids(element, dump)
                                    for guid in body if guid is not None))


def choose_plan(dump):
    stories = {s["index"]: s["elevation"] for s in dump["stories"]}
    boxes = body_boxes(dump)
    candidates = []
    for wall in dump["elements"]:
        ref = wall.get("placement", {}).get("referenceGeometry", {})
        bind = wall.get("materialBindings", {})
        bodies = wall.get("bodies", [])
        if (wall.get("type") != "Wall" or ref.get("kind") != "WallReferenceLine"
                or ref.get("arcAngle") != 0 or ref.get("referenceLineLocation") != 1
                or bind.get("structureType") != 0 or len(bodies) != 1
                or len(bodies[0].get("vertices", [])) != 8
                or len(bodies[0].get("faces", [])) != 6
                or wall.get("homeStory") not in stories or ref.get("height", 0) < 2.5):
            continue
        material_guid = bind.get("buildingMaterial", {}).get("guid")
        if not material_guid:
            continue
        active = [k for k in ("refMat", "oppMat", "sidMat") if bind.get(k, {}).get("overridden")]
        if active:
            continue
        a, b = ref["begin"], ref["end"]
        dx, dy = b["x"] - a["x"], b["y"] - a["y"]
        length = math.hypot(dx, dy)
        if length < 0.25:
            continue
        ux, uy = dx / length, dy / length
        z0 = stories[wall["homeStory"]] + ref["bottomOffsetFromHomeStory"]
        z1 = z0 + ref["height"]
        th = ref["thickness"]
        for endpoint, p, sign in (("end", b, 1.0), ("begin", a, -1.0)):
            ex, ey = ux * sign, uy * sign
            nx, ny = -ey, ex
            cs = [(p["x"] + ex * d + nx * s, p["y"] + ey * d + ny * s)
                  for d in (0.0, WALL_LENGTH) for s in (-th / 2, th / 2)]
            x0, x1 = min(q[0] for q in cs), max(q[0] for q in cs)
            y0, y1 = min(q[1] for q in cs), max(q[1] for q in cs)
            clearance = math.inf
            blocked = False
            for guid, bb in boxes:
                if guid == wall["guid"].lower() or bb[2][1] < z0 - TOL or bb[2][0] > z1 + TOL:
                    continue
                gx = max(bb[0][0] - x1, x0 - bb[0][1], 0.0)
                gy = max(bb[1][0] - y1, y0 - bb[1][1], 0.0)
                gap = math.hypot(gx, gy)
                clearance = min(clearance, gap)
                if gap <= TOL:
                    blocked = True
                    break
            if blocked:
                continue
            start = {"x": p["x"], "y": p["y"]}
            end = {"x": p["x"] + ex * WALL_LENGTH, "y": p["y"] + ey * WALL_LENGTH}
            create = {"wallsData": [{
                "begCoordinate": start, "endCoordinate": end,
                "floorIndex": wall["homeStory"],
                "zCoordinate": ref["bottomOffsetFromHomeStory"],
                "height": ref["height"], "thickness": th, "offset": ref["offset"],
                "arcAngle": 0, "referenceLineLocation": "Center",
                "structureType": "Basic", "buildingMaterialId": {"guid": material_guid}}]}
            face_guids = body_face_material_guids(wall, dump)[0]
            source_surface_guids = set(face_guids)
            target = next((m for m in dump["materials"]
                           if m.get("attribute", {}).get("guid")
                           and m["attribute"]["guid"] not in source_surface_guids), None)
            if target is None:
                continue
            candidates.append({
                "sourceGuid": wall["guid"], "endpoint": endpoint,
                "sourceHomeStory": wall["homeStory"], "storyElevation": stories[wall["homeStory"]],
                "sourceReferenceGeometry": ref, "start": start, "end": end,
                "newLengthMeters": WALL_LENGTH, "createParameters": create,
                "sourceMaterialBindings": bind,
                "sourceFaceMaterialIds": [f["materialId"] for f in bodies[0]["faces"]],
                "sourceFaceMaterialGuids": face_guids,
                "sourceFaceMaterialCounts": dict(collections.Counter(face_guids)),
                "sourceGeometryVertexCount": len(bodies[0]["vertices"]),
                "sourceGeometryFaceCount": len(bodies[0]["faces"]),
                "sourceClearanceMeters": None if math.isinf(clearance) else clearance,
                "targetMaterialIdInBaselinePool": target["id"],
                "targetSurfaceGuid": target["attribute"]["guid"],
                "targetSurfaceName": target["attribute"].get("name"),
                "selectionRule": "Basic straight centered-line Wall; simple six-face body; inactive overrides; maximum clear extension corridor"
            })
    if not candidates:
        raise RuntimeError("No simple Basic Wall with readable face materials and a clear continuation was found")
    candidates.sort(key=lambda c: (-float(c["sourceClearanceMeters"] or 0), c["sourceGuid"], c["endpoint"]))
    return candidates[0]


def wall_surface_copy_parameters(source, new_guid):
    bindings = source["materialBindings"]
    details = {"elementId": {"guid": new_guid}}
    for source_key, target_key in (("refMat", "referenceMaterial"),
                                   ("oppMat", "oppositeMaterial"), ("sidMat", "sideMaterial")):
        native = bindings[source_key]
        item = {"overridden": bool(native.get("overridden"))}
        if item["overridden"]:
            item["attributeId"] = {"guid": native["guid"]}
        details[target_key] = item
    return {"wallsWithDetails": [details]}


def modify_result_ok(result):
    executions = result.get("executionResults", [])
    return len(executions) == 1 and executions[0].get("success") is True


def semantic_binding(bindings, key):
    value = bindings.get(key, {})
    return {"overridden": bool(value.get("overridden")),
            "surfaceGuid": value.get("guid") if value.get("overridden") else None}


def geometry_signature(element):
    result = []
    for body in element.get("bodies", []):
        result.append({k: body.get(k) for k in
                       ("nativeBodyIndex", "closed", "curved", "transform", "vertices",
                        "edges", "localNormals", "vertexCoordinates")})
        result[-1]["faces"] = [{k: v for k, v in face.items() if k != "materialId"}
                                for face in body.get("faces", [])]
    return result


def stable_element_records(dump):
    fields = ("guid", "type", "nativeTypeId", "homeStory", "materialBindings", "placement", "relationships", "bodies")
    return {e["guid"].lower(): {k: e.get(k) for k in fields} for e in dump["elements"]}


def verify_inheritance(baseline, after, plan, new_guid):
    bmap, amap = wall_map(baseline), wall_map(after)
    source, created = bmap[plan["sourceGuid"].lower()], amap[new_guid.lower()]
    sr = source["placement"]["referenceGeometry"]
    nr = created["placement"]["referenceGeometry"]
    p = sr[plan["endpoint"]]
    joint_distance = math.dist((p["x"], p["y"]), (nr["begin"]["x"], nr["begin"]["y"]))
    baseline_materials = body_face_material_guids(source, baseline)
    new_materials = body_face_material_guids(created, after)
    old_bind, new_bind = source["materialBindings"], created["materialBindings"]
    structural = {key: new_bind.get(key) == old_bind.get(key)
                  for key in ("structureType", "buildingMaterial", "composite", "profile")
                  if key in old_bind or key in new_bind}
    override_copy = {key: semantic_binding(old_bind, key) == semantic_binding(new_bind, key)
                     for key in ("refMat", "oppMat", "sidMat")}
    source_and_new_shared_mesh_points = sorted(set(tuple(p) for b in source["bodies"] for p in b["vertices"])
                                               & set(tuple(p) for b in created["bodies"] for p in b["vertices"]))
    z0_old = plan["storyElevation"] + sr["bottomOffsetFromHomeStory"]
    z0_new = plan["storyElevation"] + nr["bottomOffsetFromHomeStory"]
    report = {
        "newGuid": new_guid, "sourceGuid": source["guid"],
        "jointDistanceMeters": joint_distance, "jointWithinTolerance": joint_distance <= TOL,
        "directionContinues": math.dist((nr["begin"]["x"], nr["begin"]["y"]), (nr["end"]["x"], nr["end"]["y"])) > 0
                              and ((nr["end"]["x"] - nr["begin"]["x"]) *
                                   (sr["end"]["x"] - sr["begin"]["x"] if plan["endpoint"] == "end" else sr["begin"]["x"] - sr["end"]["x"])
                                   + (nr["end"]["y"] - nr["begin"]["y"]) *
                                   (sr["end"]["y"] - sr["begin"]["y"] if plan["endpoint"] == "end" else sr["begin"]["y"] - sr["end"]["y"])) > 0,
        "homeStorySource": source["homeStory"], "homeStoryNew": created["homeStory"],
        "homeStoryMatches": source["homeStory"] == created["homeStory"],
        "storyElevationMeters": plan["storyElevation"],
        "sourceBaseZMeters": z0_old, "newBaseZMeters": z0_new, "baseZMatches": abs(z0_old-z0_new) <= TOL,
        "sourceHeight": sr["height"], "newHeight": nr["height"], "heightMatches": sr["height"] == nr["height"],
        "sourceThickness": sr["thickness"], "newThickness": nr["thickness"], "thicknessMatches": sr["thickness"] == nr["thickness"],
        "sourceReferenceLineLocation": sr["referenceLineLocation"], "newReferenceLineLocation": nr["referenceLineLocation"],
        "referenceLineLocationMatches": sr["referenceLineLocation"] == nr["referenceLineLocation"],
        "structuralBindingMatches": structural, "surfaceOverrideBindingsMatch": override_copy,
        "sourceFaceMaterialGuids": baseline_materials, "newFaceMaterialGuids": new_materials,
        "sourceFaceMaterialCounts": dict(collections.Counter(g for b in baseline_materials for g in b)),
        "newFaceMaterialCounts": dict(collections.Counter(g for b in new_materials for g in b)),
        "faceMaterialAssignmentsMatch": baseline_materials == new_materials,
        "sharedSourceNewMeshVertices": source_and_new_shared_mesh_points,
        "pass": joint_distance <= TOL and source["homeStory"] == created["homeStory"]
                and abs(z0_old-z0_new) <= TOL and sr["height"] == nr["height"]
                and sr["thickness"] == nr["thickness"]
                and sr["referenceLineLocation"] == nr["referenceLineLocation"]
                and all(structural.values()) and all(override_copy.values())
                and baseline_materials == new_materials
    }
    return report


def verify_change(inherited_dump, changed_dump, plan, new_guid):
    before, after = wall_map(inherited_dump), wall_map(changed_dump)
    source_before, source_after = before[plan["sourceGuid"].lower()], after[plan["sourceGuid"].lower()]
    test_before, test_after = before[new_guid.lower()], after[new_guid.lower()]
    bind_before = test_before["materialBindings"]
    bind_after = test_after["materialBindings"]
    old_faces = body_face_material_guids(test_before, inherited_dump)
    new_faces = body_face_material_guids(test_after, changed_dump)
    target_guid = plan["targetSurfaceGuid"]
    target_hits = sum(guid == target_guid for body in new_faces for guid in body)
    changes = []
    for bi, (old_body, new_body) in enumerate(zip(old_faces, new_faces)):
        for fi, (old_guid, new_guid_face) in enumerate(zip(old_body, new_body)):
            if old_guid != new_guid_face:
                changes.append({"body": bi, "face": fi, "beforeSurfaceGuid": old_guid,
                                "afterSurfaceGuid": new_guid_face})
    old_binding = semantic_binding(bind_before, "refMat")
    new_binding = semantic_binding(bind_after, "refMat")
    structural_keys = ("structureType", "buildingMaterial", "composite", "profile")
    unchanged_bindings = {k: bind_before.get(k) == bind_after.get(k) for k in structural_keys}
    unaffected_overrides = {k: semantic_binding(bind_before, k) == semantic_binding(bind_after, k)
                            for k in ("oppMat", "sidMat")}
    geometry_same = geometry_signature(test_before) == geometry_signature(test_after)
    report = {
        "guidStable": test_before["guid"] == test_after["guid"] == new_guid,
        "sourceGuid": source_before["guid"], "sourceBindingsUnchanged": source_before["materialBindings"] == source_after["materialBindings"],
        "sourceGeometryUnchanged": geometry_signature(source_before) == geometry_signature(source_after),
        "testGeometryUnchanged": geometry_same,
        "verticesUnchanged": [b.get("vertices") for b in test_before.get("bodies", [])]
                              == [b.get("vertices") for b in test_after.get("bodies", [])],
        "edgesUnchanged": [b.get("edges") for b in test_before.get("bodies", [])]
                           == [b.get("edges") for b in test_after.get("bodies", [])],
        "faceContoursAndTopologyUnchanged": [
            [{k: v for k, v in f.items() if k != "materialId"} for f in b.get("faces", [])]
            for b in test_before.get("bodies", [])] == [
            [{k: v for k, v in f.items() if k != "materialId"} for f in b.get("faces", [])]
            for b in test_after.get("bodies", [])],
        "nativeBodyStatusBeforeAfter": {"before": [[b.get("status"), b.get("closed")]
                                                     for b in test_before.get("bodies", [])],
                                        "after": [[b.get("status"), b.get("closed")]
                                                    for b in test_after.get("bodies", [])]},
        "testVertexCountBefore": sum(len(b["vertices"]) for b in test_before.get("bodies", [])),
        "testVertexCountAfter": sum(len(b["vertices"]) for b in test_after.get("bodies", [])),
        "testFaceCountBefore": sum(len(b["faces"]) for b in test_before.get("bodies", [])),
        "testFaceCountAfter": sum(len(b["faces"]) for b in test_after.get("bodies", [])),
        "refMatBindingBefore": old_binding, "refMatBindingAfter": new_binding,
        "expectedTargetSurfaceGuid": target_guid,
        "targetSurfaceExistsInBaselinePool": any(m.get("attribute", {}).get("guid") == target_guid for m in inherited_dump["materials"]),
        "targetMaterialIdInBaselinePool": plan["targetMaterialIdInBaselinePool"],
        "targetFaceCountAfter": target_hits, "changedFaces": changes,
        "onlyExpectedSurfaceFaceMaterialsChanged": bool(changes) and all(c["afterSurfaceGuid"] == target_guid for c in changes),
        "structuralBindingsUnchanged": unchanged_bindings,
        "oppositeAndSideOverridesUnchanged": unaffected_overrides,
        "materialCountsBefore": dict(collections.Counter(g for b in old_faces for g in b if g)),
        "materialCountsAfter": dict(collections.Counter(g for b in new_faces for g in b if g)),
    }
    report["pass"] = (report["guidStable"] and report["sourceBindingsUnchanged"]
                      and report["sourceGeometryUnchanged"] and geometry_same
                      and new_binding == {"overridden": True, "surfaceGuid": target_guid}
                      and report["targetSurfaceExistsInBaselinePool"] and target_hits > 0
                      and report["onlyExpectedSurfaceFaceMaterialsChanged"]
                      and all(unchanged_bindings.values()) and all(unaffected_overrides.values()))
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("plan", "execute", "verify"))
    args = parser.parse_args()
    baseline = read_json(EVIDENCE / "baseline.json")
    if args.phase == "verify":
        plan = read_json(EVIDENCE / "computed-plan.json")
        new_guid = read_json(EVIDENCE / "created-guid.json")["newGuid"]
        inherited = read_json(EVIDENCE / "after-inherit.json")
        changed = read_json(EVIDENCE / "after-material-change.json")
        restored = read_json(EVIDENCE / "after-delete.json")
        inheritance = verify_inheritance(baseline, inherited, plan, new_guid)
        change = verify_change(inherited, changed, plan, new_guid)
        before_records = stable_element_records(baseline)
        after_records = stable_element_records(restored)
        restore = {
            "newGuidAbsent": new_guid.lower() not in wall_map(restored),
            "baselineGuidSetRestored": set(before_records) == set(after_records),
            "baselineElementRecordsExact": before_records == after_records,
            "baselineElementCount": len(before_records),
            "afterDeleteElementCount": len(after_records),
            "baselineCounts": baseline["counts"], "afterDeleteCounts": restored["counts"],
            "deleteResponse": read_json(EVIDENCE / "delete-result.json"),
            "plnSaved": False
        }
        restore["pass"] = (restore["newGuidAbsent"] and restore["baselineGuidSetRestored"]
                           and restore["baselineElementRecordsExact"])
        write_json(EVIDENCE / "inheritance-verification.json", inheritance)
        write_json(EVIDENCE / "material-change-verification.json", change)
        write_json(EVIDENCE / "restoration-verification.json", restore)
        success = inheritance["pass"] and change["pass"] and restore["pass"]
        summary = {"status": "PASS" if success else "BLOCKED", "sourceGuid": plan["sourceGuid"],
                   "newGuid": new_guid, "inheritanceVerification": inheritance,
                   "materialChangeVerification": change, "restoration": restore,
                   "executionCommand": "python scripts/archicad_write_cycles/wall_material_cycle.py",
                   "plnSaved": False}
        write_json(EVIDENCE / "cycle-summary.json", summary)
        print(json.dumps({"status": summary["status"], "newGuid": new_guid,
                          "inheritance": inheritance, "materialChange": change,
                          "restoration": restore}, ensure_ascii=False, indent=2))
        return
    plan = choose_plan(baseline)
    write_json(EVIDENCE / "computed-plan.json", plan)
    source = wall_map(baseline)[plan["sourceGuid"].lower()]
    write_json(EVIDENCE / "source-wall.json", source)
    print(json.dumps(plan, ensure_ascii=False, indent=2))
    if args.phase == "plan":
        return

    created_guid = None
    summary = {"status": "BLOCKED", "sourceGuid": plan["sourceGuid"], "plan": plan,
               "plnSaved": False, "cleanupAttempted": False}
    try:
        create_response = api_call("CreateWalls", plan["createParameters"], "create-wall")
        ids = [row.get("elementId", {}).get("guid") for row in create_response.get("elements", [])
               if row.get("elementId", {}).get("guid")]
        if len(ids) != 1:
            raise RuntimeError(f"CreateWalls did not return exactly one GUID: {create_response}")
        created_guid = ids[0]
        summary["newGuid"] = created_guid
        write_json(EVIDENCE / "created-guid.json", {"newGuid": created_guid})

        # Transfer the exact three native override states from the source Wall.
        inherit_parameters = wall_surface_copy_parameters(source, created_guid)
        inherit_response = api_call("ModifyWalls", inherit_parameters, "copy-surface-bindings")
        write_json(EVIDENCE / "copy-surface-bindings.result.json", inherit_response)
        if not modify_result_ok(inherit_response):
            raise RuntimeError(f"Surface binding inheritance ModifyWalls failed: {inherit_response}")
        inherited = dump_now("after-inherit")
        inherited_verification = verify_inheritance(baseline, inherited, plan, created_guid)
        write_json(EVIDENCE / "inheritance-verification.json", inherited_verification)
        summary["inheritanceVerification"] = inherited_verification

        if not inherited_verification["pass"]:
            raise RuntimeError("New Wall failed geometry/material inheritance read-back; stopping before test material change")

        change_parameters = {"wallsWithDetails": [{
            "elementId": {"guid": created_guid},
            "referenceMaterial": {"overridden": True,
                                  "attributeId": {"guid": plan["targetSurfaceGuid"]}}
        }]}
        change_response = api_call("ModifyWalls", change_parameters, "change-reference-surface")
        write_json(EVIDENCE / "change-reference-surface.result.json", change_response)
        if not modify_result_ok(change_response):
            raise RuntimeError(f"Native referenceMaterial override failed: {change_response}")
        changed = dump_now("after-material-change")
        change_verification = verify_change(inherited, changed, plan, created_guid)
        write_json(EVIDENCE / "material-change-verification.json", change_verification)
        summary["materialChangeVerification"] = change_verification
        summary["status"] = "PASS" if change_verification["pass"] else "BLOCKED"
    except Exception as error:
        summary["error"] = f"{type(error).__name__}: {error}"
    finally:
        if created_guid:
            try:
                delete_response = api_call("DeleteElements", {"elements": [{"elementId": {"guid": created_guid}}]},
                                           "delete-new-wall")
                write_json(EVIDENCE / "delete-result.json", delete_response)
                summary["deleteResponse"] = delete_response
                summary["cleanupAttempted"] = True
                restored = dump_now("after-delete")
                before_records, after_records = stable_element_records(baseline), stable_element_records(restored)
                restoration = {
                    "newGuidAbsent": created_guid.lower() not in wall_map(restored),
                    "baselineGuidSetRestored": set(before_records) == set(after_records),
                    "baselineElementRecordsExact": before_records == after_records,
                    "baselineElementCount": len(before_records), "afterDeleteElementCount": len(after_records),
                    "plnSaved": False
                }
                restoration["pass"] = all(restoration[k] for k in
                                          ("newGuidAbsent", "baselineGuidSetRestored", "baselineElementRecordsExact"))
                write_json(EVIDENCE / "restoration-verification.json", restoration)
                summary["restoration"] = restoration
                if not restoration["pass"]:
                    summary["status"] = "BLOCKED"
            except Exception as cleanup_error:
                summary["cleanupError"] = f"{type(cleanup_error).__name__}: {cleanup_error}"
                summary["status"] = "BLOCKED"
        else:
            summary["cleanupAttempted"] = False
    summary["executionCommand"] = "python scripts/archicad_write_cycles/wall_material_cycle.py"
    summary["plnSaved"] = False
    write_json(EVIDENCE / "cycle-summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
