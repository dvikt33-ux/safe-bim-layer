"""Code-owned material-only ModifySlabs through the original APA SceneWriter.

The installed native ModifySlabs can set buildingMaterialId and structureType
although CreateSlabs cannot. Only an already Basic standalone slab on story 0
may change construction material here. No thickness, polygon, holes, z, story,
dependents or user geometry are modified. Full pre/post BREP invariance required.
"""
from __future__ import annotations

import math

from apa_ac29_dynamic_write_scopes import NativeVerifier


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def material_request(parameters):
    require(isinstance(parameters, dict) and
            set(parameters) == {"slabsWithDetails"} and
            isinstance(parameters["slabsWithDetails"], list) and
            len(parameters["slabsWithDetails"]) == 1 and
            isinstance(parameters["slabsWithDetails"][0], dict),
            "APA_MODIFY_SLAB_ONE_NATIVE_SCOPED_ELEMENT_REQUIRED")
    row = parameters["slabsWithDetails"][0]
    require(set(row) == {"elementId", "structureType", "buildingMaterialId"} and
            isinstance(row["elementId"], dict) and
            set(row["elementId"]) == {"guid"} and
            isinstance(row["elementId"]["guid"], str) and
            len(row["elementId"]["guid"]) == 36 and
            row["structureType"] == "Basic" and
            isinstance(row["buildingMaterialId"], dict) and
            set(row["buildingMaterialId"]) == {"guid"} and
            isinstance(row["buildingMaterialId"]["guid"], str) and
            len(row["buildingMaterialId"]["guid"]) == 36,
            "APA_MODIFY_SLAB_ONLY_MATERIAL_OF_EXISTING_BASIC_SLAB")
    return row["elementId"]["guid"].lower(), row["buildingMaterialId"]["guid"].lower()


def details_for(api, guid):
    import archicad_scene_run as RUN
    row = RUN.requested_details(api, guid)
    require(row.get("type") == "Slab" and row.get("floorIndex") == 0 and
            isinstance(row.get("details"), dict),
            "APA_MODIFY_SLAB_TYPED_STORY0_SLAVE_REQUIRED")
    props = row["details"]
    require(props.get("structureType") == "Basic" and
            all(type(props.get(x)) in (int, float) and
                math.isfinite(props[x]) for x in
                ("thickness", "level", "zCoordinate")) and
            props["thickness"] > 0 and
            isinstance(props.get("polygonOutline"), list) and
            len(props["polygonOutline"]) >= 3 and
            (props.get("buildingMaterialId") or {}).get("guid"),
            "APA_MODIFY_SLAB_EXISTING_BASIC_GEOMETRY_REQUIRED")
    return row


def geom(api_map, guid):
    import archicad_connected_components as C
    require(guid in api_map and api_map[guid].get("type") == "Slab" and
            bool(api_map[guid].get("bodies")) and
            all(b.get("closed") is True for b in api_map[guid]["bodies"]),
            "APA_MODIFY_SLAB_CLOSED_NATIVE_BODY_REQUIRED")
    return C.ROOF.geometry_signature(api_map[guid])


def verify_slab_material_before(*, api, command, parameters,
                                affected, native_before):
    import archicad_scene_run as RUN
    require(command == "ModifySlabs",
            "APA_MODIFY_SLAB_ONLY_REVIEWED_NATIVE_COMMAND")
    guid, expected_material = material_request(parameters)
    require(set(affected) == {guid} and
            isinstance(native_before, dict) and
            isinstance(native_before.get("elements"), list),
            "APA_MODIFY_SLAB_EXACT_AFFECTED_GUID_REQUIRED")
    native = {e["guid"].lower(): e for e in native_before["elements"]}
    require(guid in native and
            not any((e.get("relationships", {}).get("hostGuid") or "").lower()
                    == guid for g, e in native.items() if g != guid),
            "APA_MODIFY_SLAB_HAS_DEPENDENT_ELEMENTS")
    require(not any(value not in (None, "", [], {})
                    for value in native[guid].get("relationships", {}).values()),
            "APA_MODIFY_SLAB_HOSTED_SOURCE_NOT_STANDALONE")
    source = details_for(api, guid)
    current_material = source["details"]["buildingMaterialId"]["guid"].lower()
    require(current_material != expected_material,
            "APA_MODIFY_SLAB_MATERIAL_ALREADY_SET")
    g = geom(native, guid)
    return {
        "status": "APA_MODIFY_SLAB_BASIC_MATERIAL_PREFLIGHT_PASS",
        "sourceGuid": guid,
        "beforeMaterialGuid": current_material,
        "expectedMaterialGuid": expected_material,
        "beforeTypedDetails": source,
        "beforeNativeGeometry": g,
    }


def verify_slab_material_after(*, api, command, parameters,
                               native_response, before_guids, after_guids,
                               affected, native_before, native_after,
                               source_proof):
    import archicad_scene_run as RUN
    guid, expected_material = material_request(parameters)
    require(command == "ModifySlabs" and
            set(affected) == {guid} and before_guids == after_guids and
            source_proof.get("sourceGuid") == guid and
            source_proof.get("expectedMaterialGuid") == expected_material and
            isinstance(native_response, dict) and
            native_response.get("executionResults") == [{"success": True}],
            "APA_MODIFY_SLAB_NATIVE_RESPONSE_OR_GUIDS_CHANGED")
    before = source_proof["beforeTypedDetails"]
    now = details_for(api, guid)
    old_props, props = before["details"], now["details"]
    require(now.get("type") == before.get("type") and
            now.get("floorIndex") == before.get("floorIndex") and
            props.get("buildingMaterialId", {}).get("guid", "").lower() ==
            expected_material and
            {k:v for k,v in props.items() if k!="buildingMaterialId"} ==
            {k:v for k,v in old_props.items() if k!="buildingMaterialId"},
            "APA_MODIFY_SLAB_UNAPPROVED_TYPED_PROPERTY_DRIFT")
    body = {e["guid"].lower(): e for e in native_after["elements"]}
    require(set(body) == after_guids and
            geom(body, guid) == source_proof["beforeNativeGeometry"] and
            body[guid].get("materialBindings", {}).get(
                "buildingMaterial", {}).get("guid", "").lower() ==
            expected_material,
            "APA_MODIFY_SLAB_PHYSICAL_BREP_OR_MATERIAL_DRIFT")
    return {
        "status": "APA_MODIFY_SLAB_MATERIAL_ONLY_NATIVE_BREP_PASS",
        "affectedGuid": guid,
        "oldMaterial": source_proof["beforeMaterialGuid"],
        "newMaterial": expected_material,
        "totalGuidCount": len(after_guids),
    }


def existing_slab_modify_verifiers():
    return {"VerifiedBasicSlabMaterial": NativeVerifier(
        verifier_id="VerifiedBasicSlabMaterial", command="ModifySlabs",
        effect="MODIFY", before=verify_slab_material_before,
        after=verify_slab_material_after)}
