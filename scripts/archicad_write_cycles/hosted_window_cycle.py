"""Geometry-derived hosted Window create/read-back/delete cycle."""
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
EVIDENCE = EVIDENCE_ROOT / "hosted-window-cycle"
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
    data, metrics = module.dump(EVIDENCE / f"{stem}.json", PORT)
    return data, metrics


def find_by_guid(dump):
    return {e["guid"].lower(): e for e in dump["elements"]}


def boxes(dump):
    result = []
    for e in dump["elements"] + dump.get("unresolvedBodyOwners", []):
        for body in e.get("bodies", []):
            points = body.get("vertices", [])
            if points:
                result.append((e["guid"].lower(), tuple(
                    (min(p[i] for p in points), max(p[i] for p in points)) for i in range(3))))
    return result


def select_wall(dump):
    stories = {int(s["index"]): float(s["elevation"]) for s in dump["stories"]}
    hosted = collections.defaultdict(list)
    for e in dump["elements"]:
        host = e.get("relationships", {}).get("hostGuid")
        if host:
            hosted[host.lower()].append(e)
    other_boxes = boxes(dump)
    candidates = []
    for wall in dump["elements"]:
        ref = wall.get("placement", {}).get("referenceGeometry", {})
        if (wall.get("type") != "Wall" or ref.get("kind") != "WallReferenceLine"
                or ref.get("arcAngle") != 0 or ref.get("referenceLineLocation") != 1
                or wall.get("homeStory") not in stories or len(wall.get("bodies", [])) != 1):
            continue
        body = wall["bodies"][0]
        if len(body.get("vertices", [])) != 8 or len(body.get("faces", [])) != 6 or not body.get("closed"):
            continue
        a, b = ref["begin"], ref["end"]
        dx, dy = b["x"] - a["x"], b["y"] - a["y"]
        length = math.hypot(dx, dy)
        h, th = float(ref.get("height", 0)), float(ref.get("thickness", 0))
        if length < 3.2 or h < 2.6 or th <= 0 or hosted[wall["guid"].lower()]:
            continue
        width = min(1.2, length * 0.12)
        height = min(1.5, h * 0.30)
        sill = min(h * 0.15, h - height - 0.25)
        offset = length / 2
        ux, uy = dx / length, dy / length
        cx, cy = a["x"] + ux * offset, a["y"] + uy * offset
        # The opening prism follows the measured wall axis and reference line.
        nx, ny = -uy, ux
        corners = [(cx + ux * along + nx * side, cy + uy * along + ny * side)
                   for along in (-width / 2, width / 2) for side in (-th / 2, th / 2)]
        obox = ((min(p[0] for p in corners), max(p[0] for p in corners)),
                (min(p[1] for p in corners), max(p[1] for p in corners)),
                (stories[wall["homeStory"]] + ref["bottomOffsetFromHomeStory"] + sill,
                 stories[wall["homeStory"]] + ref["bottomOffsetFromHomeStory"] + sill + height))
        colliders = []
        for guid, bb in other_boxes:
            if guid == wall["guid"].lower():
                continue
            if all(min(obox[i][1], bb[i][1]) - max(obox[i][0], bb[i][0]) > TOL for i in range(3)):
                colliders.append(guid)
        if colliders:
            continue
        candidates.append({
            "wallGuid": wall["guid"], "homeStory": wall["homeStory"],
            "storyElevation": stories[wall["homeStory"]], "referenceGeometry": ref,
            "referenceLine": {"begin": a, "end": b}, "length": length,
            "directionUnit": {"x": ux, "y": uy}, "thickness": th,
            "referenceSide": "center" if ref["referenceLineLocation"] == 1 else "edge",
            "centerOffsetAlongHost": offset, "computedCenterXY": {"x": cx, "y": cy},
            "width": width, "height": height, "sillHeightFromWallBase": sill,
            "absoluteSillZ": obox[2][0], "absoluteHeadZ": obox[2][1],
            "openingPrismXY": obox[:2], "otherBodyAabbColliders": colliders,
            "hostedElementsBefore": [], "wallBodyBefore": body,
            "selectionRule": "longest straight centered-line, simple closed Wall with no hosted openings and a clear geometry-derived opening prism"
        })
    if not candidates:
        raise RuntimeError("No simple straight Wall has a free, non-colliding hosted Window interval")
    candidates.sort(key=lambda c: (-c["length"], c["wallGuid"]))
    return candidates[0]


def geometry_signature(element):
    return [{k: body.get(k) for k in ("closed", "curved", "transform", "vertices", "edges",
                                      "localNormals", "faces", "vertexCoordinates")}
            for body in element.get("bodies", [])]


def main():
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    baseline, baseline_metrics = dump_now("baseline")
    plan = select_wall(baseline)
    write_json(EVIDENCE / "computed-placement.json", plan)
    bmap = find_by_guid(baseline)
    baseline_guids = set(bmap)
    wall = bmap[plan["wallGuid"].lower()]
    request = {"windowsData": [{
        "ownerWallId": {"guid": plan["wallGuid"]},
        "centerOffset": plan["centerOffsetAlongHost"],
        "sillHeight": plan["sillHeightFromWallBase"],
        "width": plan["width"], "height": plan["height"],
        "reflected": False, "refSide": False, "oSide": False
    }]}
    created_guid = None
    error = None
    after_create = None
    after_create_metrics = None
    delete_response = None
    restored = None
    restored_metrics = None
    try:
        created = api_call("CreateWindows", request, "create-window")
        entry = created.get("elements", [{}])[0]
        created_guid = entry.get("elementId", {}).get("guid")
        if not created_guid:
            raise RuntimeError(f"CreateWindows returned no GUID: {created}")
        write_json(EVIDENCE / "created-guid.json", {"guid": created_guid, "response": created})
        after_create, after_create_metrics = dump_now("after-create")
        amap = find_by_guid(after_create)
        if created_guid.lower() not in amap:
            raise RuntimeError("CreateWindows GUID was absent from fresh Model Dump")
        new = amap[created_guid.lower()]
        wall_after = amap[plan["wallGuid"].lower()]
        new_ref = new.get("placement", {}).get("referenceGeometry", {})
        host_guid = new.get("relationships", {}).get("hostGuid")
        joint_xy = math.hypot(new_ref.get("centerOffsetAlongHost", float("nan")) - plan["centerOffsetAlongHost"], 0)
        # The inserted aperture is evidenced by changed wall topology while the
        # wall outer envelope, closure, home story and reference line remain fixed.
        before_geom, after_geom = geometry_signature(wall), geometry_signature(wall_after)
        before_body, after_body = wall["bodies"][0], wall_after["bodies"][0]
        vb, va = before_body["vertices"], after_body["vertices"]
        def envelope(points):
            return [[min(p[i] for p in points), max(p[i] for p in points)] for i in range(3)]
        source_ref = wall["placement"]["referenceGeometry"]
        window_faces = [f for b in new.get("bodies", []) for f in b.get("faces", [])]
        hole_contours = []
        for face in after_body.get("faces", []):
            for contour in face.get("holes", []) or []:
                points = [va[index] for index in contour]
                projections = [(p[0]-source_ref["begin"]["x"])*plan["directionUnit"]["x"]
                               +(p[1]-source_ref["begin"]["y"])*plan["directionUnit"]["y"]
                               for p in points]
                hole_contours.append({
                    "nativeFaceIndex": face.get("nativeFaceIndex"), "vertexIndices": contour,
                    "verticesXYZ": points,
                    "alongRange": [min(projections), max(projections)],
                    "zRange": [min(p[2] for p in points), max(p[2] for p in points)],
                })
        # Projection of the window body's vertices checks that the physical object
        # straddles the host line at the requested station and stays within its ends.
        ux, uy = plan["directionUnit"]["x"], plan["directionUnit"]["y"]
        ax, ay = source_ref["begin"]["x"], source_ref["begin"]["y"]
        wverts = [p for b in new.get("bodies", []) for p in b.get("vertices", [])]
        along = [(p[0]-ax)*ux+(p[1]-ay)*uy for p in wverts]
        normal = [(p[0]-ax)*(-uy)+(p[1]-ay)*ux for p in wverts]
        host_body_verts = [p for b in wall_after.get("bodies", []) for p in b.get("vertices", [])]
        wall_zbase = plan["storyElevation"] + source_ref["bottomOffsetFromHomeStory"]
        actual = {
            "newGuid": created_guid, "newType": new.get("type"), "hostGuid": host_guid,
            "hostMatches": bool(host_guid and host_guid.lower() == plan["wallGuid"].lower()),
            "homeStoryNew": new.get("homeStory"), "homeStoryMatches": new.get("homeStory") == plan["homeStory"],
            "referenceGeometry": new_ref, "requestedCenterOffset": plan["centerOffsetAlongHost"],
            "centerOffsetDifference": joint_xy,
            "positionProjectionRangeAlongWall": [min(along), max(along)] if along else None,
            "positionProjectionRangeNormalToWall": [min(normal), max(normal)] if normal else None,
            "actualWindowBodyZ": [min(p[2] for p in wverts), max(p[2] for p in wverts)] if wverts else None,
            "expectedSillZ": plan["absoluteSillZ"], "expectedHeadZ": plan["absoluteHeadZ"],
            "wallBodyBefore": {"closed": before_body.get("closed"), "vertices": len(vb),
                               "edges": len(before_body.get("edges", [])), "faces": len(before_body.get("faces", [])),
                               "holeContours": sum(len(f.get("holes", []) or []) for f in before_body.get("faces", [])),
                               "envelope": envelope(vb)},
            "wallBodyAfter": {"closed": after_body.get("closed"), "vertices": len(va),
                              "edges": len(after_body.get("edges", [])), "faces": len(after_body.get("faces", [])),
                              "holeContours": sum(len(f.get("holes", []) or []) for f in after_body.get("faces", [])),
                              "envelope": envelope(va)},
            "apertureHoleContours": hole_contours,
            "holeContoursMatchRequestedAperture": bool(hole_contours) and all(
                abs(min(c["alongRange"]) - (plan["centerOffsetAlongHost"] - plan["width"] / 2)) <= TOL
                and abs(max(c["alongRange"]) - (plan["centerOffsetAlongHost"] + plan["width"] / 2)) <= TOL
                and abs(min(c["zRange"]) - plan["absoluteSillZ"]) <= TOL
                and abs(max(c["zRange"]) - plan["absoluteHeadZ"]) <= TOL
                for c in hole_contours),
            "wallFaceMaterialIdsBefore": [f.get("materialId") for f in before_body.get("faces", [])],
            "wallFaceMaterialIdsAfter": [f.get("materialId") for f in after_body.get("faces", [])],
            "wallFaceMaterialsUnchanged": bool(before_body.get("faces")) and
                set(f.get("materialId") for f in before_body.get("faces", [])) ==
                set(f.get("materialId") for f in after_body.get("faces", [])),
            "wallGeometryChanged": before_geom != after_geom,
            "wallOuterEnvelopeUnchanged": envelope(vb) == envelope(va),
            "wallClosedAfter": bool(after_body.get("closed")),
            "apertureTopologyEvidence": (len(va) > len(vb) or len(after_body.get("faces", [])) > len(before_body.get("faces", []))
                                          or sum(len(f.get("holes", []) or []) for f in after_body.get("faces", [])) >
                                             sum(len(f.get("holes", []) or []) for f in before_body.get("faces", []))),
            "windowHasPhysicalBody": bool(wverts and window_faces),
            "windowBodyVertexCount": len(wverts), "windowBodyFaceCount": len(window_faces),
            "wallBaseZ": wall_zbase, "wallTopZ": wall_zbase + source_ref["height"],
            "wallThickness": source_ref["thickness"],
            "newMaterialBindings": new.get("materialBindings"),
            "elementCountBefore": len(baseline["elements"]), "elementCountAfterCreate": len(after_create["elements"]),
        }
        actual["createVerifyPass"] = bool(
            actual["hostMatches"] and actual["homeStoryMatches"] and new.get("type") == "Window"
            and abs(joint_xy) <= TOL and actual["windowHasPhysicalBody"]
            and actual["apertureTopologyEvidence"] and actual["holeContoursMatchRequestedAperture"]
            and actual["wallFaceMaterialsUnchanged"] and actual["wallClosedAfter"]
            and actual["wallOuterEnvelopeUnchanged"] and len(after_create["elements"]) == len(baseline["elements"]) + 1
            and actual["actualWindowBodyZ"] is not None
            and actual["actualWindowBodyZ"][0] >= wall_zbase - TOL
            and actual["actualWindowBodyZ"][1] <= wall_zbase + source_ref["height"] + TOL
            and actual["positionProjectionRangeAlongWall"] is not None
            and actual["positionProjectionRangeAlongWall"][0] >= -TOL
            and actual["positionProjectionRangeAlongWall"][1] <= plan["length"] + TOL
            and actual["positionProjectionRangeNormalToWall"] is not None
            and actual["positionProjectionRangeNormalToWall"][0] <= source_ref["thickness"] / 2 + 0.25
            and actual["positionProjectionRangeNormalToWall"][1] >= -source_ref["thickness"] / 2 - 0.25
        )
        write_json(EVIDENCE / "hosted-window-verification.json", actual)
    except Exception as exc:
        error = repr(exc)
        write_json(EVIDENCE / "cycle-error.json", {"error": error, "createdGuid": created_guid})
    finally:
        # If CreateWindows returned an ambiguous result, reconcile by read-back;
        # never issue a second create on an unknown outcome.
        if not created_guid:
            try:
                reconciled, _ = dump_now("create-outcome-reconciliation")
                additions = [e for e in reconciled["elements"] if e["guid"].lower() not in baseline_guids]
                owned = [e for e in additions if e.get("type") == "Window"
                         and e.get("relationships", {}).get("hostGuid", "").lower() == plan["wallGuid"].lower()]
                if len(owned) == 1 and len(additions) == 1:
                    created_guid = owned[0]["guid"]
                    write_json(EVIDENCE / "created-guid.json", {
                        "guid": created_guid, "source": "fresh Model Dump reconciliation",
                        "newElements": additions})
                elif additions:
                    error = error or f"unexpected post-create additions require review: {[e['guid'] for e in additions]}"
            except Exception as exc:
                error = error or f"create outcome reconciliation failed: {exc!r}"
        if created_guid:
            try:
                delete_response = api_call("DeleteElements", {"elements": [{"elementId": {"guid": created_guid}}]},
                                           "delete-window")
                write_json(EVIDENCE / "delete-result.json", delete_response)
            except Exception as exc:
                error = error or f"delete failed: {exc!r}"
                write_json(EVIDENCE / "delete-error.json", {"error": repr(exc), "createdGuid": created_guid})
            restored, restored_metrics = dump_now("after-delete")
        else:
            # No creation was read back: this dump proves the untouched baseline.
            restored, restored_metrics = dump_now("after-delete")
    restored_pass = False
    restored_detail = {}
    if restored is not None:
        rmap = find_by_guid(restored)
        restored_wall = rmap.get(plan["wallGuid"].lower())
        restored_pass = (set(rmap) == baseline_guids and len(restored["elements"]) == len(baseline["elements"])
                         and restored_wall is not None
                         and geometry_signature(restored_wall) == geometry_signature(wall))
        restored_detail = {
            "elementCountBefore": len(baseline["elements"]), "elementCountAfterDelete": len(restored["elements"]),
            "guidSetRestored": set(rmap) == baseline_guids,
            "sourceWallGeometryRestored": bool(restored_wall and geometry_signature(restored_wall) == geometry_signature(wall)),
            "newGuidAbsent": created_guid.lower() not in rmap if created_guid else None,
            "restorationPass": restored_pass,
        }
        write_json(EVIDENCE / "restoration-verification.json", restored_detail)
    create_verify = False
    verify_file = EVIDENCE / "hosted-window-verification.json"
    if verify_file.exists():
        create_verify = json.loads(verify_file.read_text(encoding="utf-8")).get("createVerifyPass", False)
    summary = {
        "status": "PASS" if create_verify and restored_pass and error is None else "BLOCKED",
        "sourceWallGuid": plan["wallGuid"], "newGuid": created_guid,
        "type": "Window", "plan": {k: v for k, v in plan.items() if k != "wallBodyBefore"},
        "createVerifyPass": create_verify, "restoration": restored_detail,
        "error": error, "baselineMetrics": baseline_metrics,
        "afterCreateMetrics": after_create_metrics, "restoredMetrics": restored_metrics,
        "commands": ["TapirCommand.GetModelDumpV1", "TapirCommand.CreateWindows",
                     "TapirCommand.GetModelDumpV1", "TapirCommand.DeleteElements",
                     "TapirCommand.GetModelDumpV1"],
        "plnSaved": False,
    }
    write_json(EVIDENCE / "cycle-summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if summary["status"] != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
