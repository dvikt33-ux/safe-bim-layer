"""Code-owned native CREATE verifiers for the existing APA dynamic scope binder.

These verifiers are installed Python code, never sourced from a GitHub task.
First supported contract: basic vertical, centered rectangular CreateColumns
with one real native ColumnSegment per root. Other commands must supply
independently source-reviewed callbacks before being offered for native write.
"""
from __future__ import annotations

import math

from apa_ac29_dynamic_write_scopes import NativeVerifier


def check(ok, why):
    if not ok:
        raise ValueError(why)


def close(actual, intended, tolerance=1e-5):
    return type(actual) in (float, int) and type(intended) in (float, int) and \
        math.isfinite(actual) and math.isfinite(intended) and \
        abs(actual - intended) < tolerance


def checked_column_source(parameters):
    check(isinstance(parameters, dict) and
          set(parameters) == {"columnsData"} and
          isinstance(parameters["columnsData"], list) and
          1 <= len(parameters["columnsData"]) <= 200,
          "APA_NATIVE_COLUMN_CREATE_REQUIRES_ONE_NATIVE_BATCH")
    approved = []
    ids = set()
    for item in parameters["columnsData"]:
        check(isinstance(item, dict) and
              {"coordinates", "width", "depth", "height", "zCoordinate",
               "floorIndex", "axisRotationAngle", "buildingMaterialId",
               "coreAnchor", "circleBased", "isSlanted",
               "isWidthAndHeightLinked"} <= set(item),
              "APA_NATIVE_COLUMN_COMPLETE_NATIVE_PROFILE_REQUIRED")
        point = item["coordinates"]
        material = item["buildingMaterialId"]
        check(isinstance(point, dict) and
              all(type(point.get(k)) in (float, int) and
                  math.isfinite(point[k]) for k in ("x", "y")) and
              isinstance(material, dict) and
              isinstance(material.get("guid"), str) and
              item["floorIndex"] == 0 and
              item["coreAnchor"] == "Center" and
              item["circleBased"] is False and
              item["isSlanted"] is False and
              item["isWidthAndHeightLinked"] is False and
              close(item["axisRotationAngle"], 0.0) and
              all(type(item[k]) in (int, float) and
                  0 < item[k] <= 30 and math.isfinite(item[k])
                  for k in ("width", "depth", "height")) and
              type(item["zCoordinate"]) in (int, float) and
              math.isfinite(item["zCoordinate"]),
              "APA_NATIVE_COLUMN_ONLY_VERIFIED_STRAIGHT_CENTERED_BASIC_PROFILE")
        expected = (
            round(point["x"], 6), round(point["y"], 6),
            round(item["zCoordinate"], 6)
        )
        check(expected not in ids,
              "APA_NATIVE_COLUMN_DUPLICATE_AUTHORED_POSITION")
        ids.add(expected)
        approved.append(item)
    return approved


def verify_column_create_before(*, api, command, parameters,
                                affected, native_before):
    check(command == "CreateColumns" and not affected,
          "APA_NATIVE_COLUMN_CREATE_CANNOT_MODIFY_EXISTING_GUID")
    items = checked_column_source(parameters)
    check(isinstance(native_before, dict) and
          isinstance(native_before.get("elements"), list) and
          len(native_before["elements"]) > 0,
          "APA_NATIVE_COLUMN_PREWRITE_BREP_MISSING")
    return {"status": "NATIVE_COLUMN_SOURCE_SCOPED_CREATE_PASS",
            "expectedCount": len(items)}


def verify_column_create_after(*, api, command, parameters,
                               native_response, before_guids, after_guids,
                               affected, native_before, native_after,
                               source_proof):
    import archicad_connected_components as C

    expected = checked_column_source(parameters)
    check(not affected and command == "CreateColumns" and
          source_proof["expectedCount"] == len(expected),
          "APA_NATIVE_COLUMN_AFTER_UNAPPROVED_COMMAND")
    rows = native_response.get("elements") if isinstance(native_response, dict) else None
    check(isinstance(rows, list) and len(rows) == len(expected),
          "APA_NATIVE_COLUMN_CREATED_ROOT_RETURN_COUNT_MISMATCH")
    roots = []
    for row in rows:
        guid = (row.get("elementId") or {}).get("guid") if isinstance(row, dict) else None
        check(isinstance(guid, str) and guid.lower() not in roots and
              guid.lower() not in before_guids,
              "APA_NATIVE_COLUMN_GUID_ALREADY_EXISTED_OR_DUPLICATED")
        roots.append(guid.lower())
    new = after_guids - before_guids
    check(before_guids <= after_guids and len(new) == 2*len(roots),
          "APA_NATIVE_COLUMN_NEW_ROOT_SEGMENT_GUID_DELTA_INVALID")
    physical = C.G.normalize_dump(native_after)
    current = {element["guid"].lower(): element for element in physical["elements"]}
    check(set(current) == after_guids, "APA_NATIVE_COLUMN_COMPLETE_BREP_REQUIRED")
    details = api("GetDetailsOfElements", {
        "elements": [{"elementId": {"guid": g}} for g in roots]
    }).get("detailsOfElements")
    check(isinstance(details, list) and len(details) == len(roots),
          "APA_NATIVE_COLUMN_ROOT_TYPED_READBACK_MISSING")
    children = set()
    for root, item, row in zip(roots, expected, details):
        check(current[root]["type"] == "Column" and
              row.get("type") == "Column" and row.get("floorIndex") == 0,
              "APA_NATIVE_COLUMN_ROOT_NATIVE_TYPE_OR_STORY_INVALID")
        values = row.get("details") or {}
        origin = values.get("origin") or {}
        point = item["coordinates"]
        check(all(close(origin.get(k), point[k]) for k in ("x", "y")) and
              all(close(values.get(k), item[k]) for k in
                  ("width", "depth", "height", "zCoordinate", "axisRotationAngle")) and
              values.get("coreAnchor") == "Center" and
              values.get("circleBased") is False and
              values.get("isSlanted") is False and
              values.get("isWidthAndHeightLinked") is False and
              (values.get("buildingMaterialId") or {}).get("guid", "").lower() ==
              item["buildingMaterialId"]["guid"].lower(),
              "APA_NATIVE_COLUMN_ACTUAL_TYPED_PARAMETERS_DIFFER_FROM_SOURCE")
        members = [(guid, n) for guid, n in current.items()
                   if n.get("type") == "ColumnSegment" and
                   (n.get("relationships", {}).get("hostGuid") or "").lower()
                   == root]
        check(len(members) == 1, "APA_NATIVE_COLUMN_ONE_NATIVE_SEGMENT_REQUIRED")
        child, segment = members[0]
        check(child in new and child not in children and
              (segment.get("materialBindings", {})
               .get("buildingMaterial", {}).get("guid", "")).lower() ==
              item["buildingMaterialId"]["guid"].lower(),
              "APA_NATIVE_COLUMN_SEGMENT_OWNERSHIP_OR_MATERIAL_MISMATCH")
        vertices = [v for body in segment.get("bodies", [])
                    for v in body.get("vertices", [])]
        check(bool(vertices) and
              all(body.get("closed") is True
                  for body in segment.get("bodies", [])),
              "APA_NATIVE_COLUMN_UNCLOSED_OR_MISSING_NATIVE_SEGMENT")
        box = [(min(v[i] for v in vertices), max(v[i] for v in vertices))
               for i in range(3)]
        for index, (centre, width) in enumerate((
                (point["x"], item["width"]),
                (point["y"], item["depth"]))):
            check(close(box[index][0], centre-width/2) and
                  close(box[index][1], centre+width/2),
                  "APA_NATIVE_COLUMN_NATIVE_SECTION_OR_XY_DRIFT")
        check(close(box[2][0], item["zCoordinate"]) and
              close(box[2][1], item["zCoordinate"] + item["height"]),
              "APA_NATIVE_COLUMN_ACTUAL_Z_HEIGHT_DRIFT")
        children.add(child)
    check(set(roots) | children == new,
          "APA_NATIVE_COLUMN_UNEXPECTED_NEW_ELEMENT_OR_SUBELEMENT")
    return {"status": "NATIVE_COLUMN_CREATE_TYPED_AND_BREP_READBACK_PASS",
            "newRootCount": len(roots),
            "newSegmentCount": len(children),
            "newRootGuids": roots,
            "nativeModelElementCount": len(after_guids)}


def installed_verifiers():
    """Conservative source-owned registry. No blanket Create/Modify grant."""
    return {
        "VerifiedNativeColumns": NativeVerifier(
            verifier_id="VerifiedNativeColumns", command="CreateColumns",
            effect="CREATE", before=verify_column_create_before,
            after=verify_column_create_after)
    }
