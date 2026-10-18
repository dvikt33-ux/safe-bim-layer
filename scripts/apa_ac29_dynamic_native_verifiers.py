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
              set(item) == {
               "coordinates", "width", "depth", "height",
               "floorIndex", "axisRotationAngle", "buildingMaterialId",
               "coreAnchor", "circleBased",
               "isWidthAndHeightLinked"},
              "APA_NATIVE_COLUMN_COMPLETE_NATIVE_PROFILE_REQUIRED")
        point = item["coordinates"]
        material = item["buildingMaterialId"]
        check(isinstance(point, dict) and set(point) == {"x", "y", "z"} and
              all(type(point.get(k)) in (float, int) and
                  math.isfinite(point[k]) for k in ("x", "y", "z")) and
              isinstance(material, dict) and
              isinstance(material.get("guid"), str) and
              item["floorIndex"] == 0 and
              item["coreAnchor"] == "Center" and
              item["circleBased"] is False and
              item["isWidthAndHeightLinked"] is False and
              close(item["axisRotationAngle"], 0.0) and
              all(type(item[k]) in (int, float) and
                  0 < item[k] <= 30 and math.isfinite(item[k])
                  for k in ("width", "depth", "height")),
              "APA_NATIVE_COLUMN_ONLY_VERIFIED_STRAIGHT_CENTERED_BASIC_PROFILE")
        expected = (
            round(point["x"], 6), round(point["y"], 6),
            round(point["z"], 6)
        )
        check(expected not in ids,
              "APA_NATIVE_COLUMN_DUPLICATE_AUTHORED_POSITION")
        ids.add(expected)
        # The CREATE contract writes coordinates.z; the DETAILS contract
        # reads zCoordinate. Never send readback-only fields to CreateColumns.
        approved.append(dict(item, zCoordinate=point["z"]))
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
    from apa_ac29_reusable_native_copy import native_aabb_overlaps
    boxes = [[(p['coordinates']['x']-p['width']/2,
               p['coordinates']['x']+p['width']/2),
              (p['coordinates']['y']-p['depth']/2,
               p['coordinates']['y']+p['depth']/2),
              (p['zCoordinate'],p['zCoordinate']+p['height'])] for p in items]
    existing = []
    for element in native_before['elements']:
        for body in element.get('bodies', []):
            vertices=body.get('vertices', [])
            if vertices:
                existing.append([(min(v[i] for v in vertices),
                                  max(v[i] for v in vertices)) for i in range(3)])
    check(not any(native_aabb_overlaps(box, other)
                  for index, box in enumerate(boxes)
                  for other in boxes[index+1:] + existing),
          'APA_NATIVE_COLUMN_SOURCE_OR_BATCH_SOLIDS_INTERSECT')
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
    physical = native_after if (isinstance(native_after, dict) and
        isinstance(native_after.get("elements"), list) and
        all(isinstance(r, dict) and "guid" in r and "type" in r
            for r in native_after["elements"])) else C.G.normalize_dump(native_after)
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


def translation_rows(parameters):
    check(isinstance(parameters,dict) and set(parameters)=={'elementsWithMoveVectors'} and
          isinstance(parameters['elementsWithMoveVectors'],list) and
          1<=len(parameters['elementsWithMoveVectors'])<=200,
          'APA_NATIVE_TRANSLATION_ONE_BOUNDED_BATCH_REQUIRED')
    rows=parameters['elementsWithMoveVectors'];seen=set()
    for row in rows:
        check(isinstance(row,dict) and set(row)=={'elementId','moveVector','copy'} and
              row['copy'] is False and set(row['elementId'])=={'guid'},
              'APA_NATIVE_TRANSLATION_MUST_MODIFY_EXACT_EXISTING_GUID')
        guid=row['elementId']['guid'].lower();v=row['moveVector']
        check(guid not in seen and len(guid)==36 and isinstance(v,dict) and
              set(v)=={'x','y','z'} and all(type(x) in (float,int) and
              math.isfinite(x) and abs(x)<=10000 for x in v.values()) and
              v['z']==0 and (v['x']!=0 or v['y']!=0),
              'APA_NATIVE_TRANSLATION_UNIQUE_GUID_FINITE_HORIZONTAL_VECTOR_REQUIRED')
        seen.add(guid)
    return rows


def verify_translation_before(*,api,command,parameters,affected,native_before):
    import apa_ac29_multi_prototype_native_copy as M
    check(command=='MoveElements','APA_NATIVE_TRANSLATION_COMMAND_REQUIRED')
    rows=translation_rows(parameters)
    nodes={e['guid'].lower():e for e in native_before['elements']}
    ids=[r['elementId']['guid'].lower() for r in rows]
    details=M.SINGLE.column_details(api,ids)
    allowed=set();proof=[];groups=[];sources={};targets={}
    for row,guid in zip(rows,ids):
        check(guid in nodes and nodes[guid]['type'] in M.TYPES,
              'APA_NATIVE_TRANSLATION_ONLY_STANDALONE_COLUMN_BEAM_OBJECT')
        root=nodes[guid];kind=root['type'];children=M.owned_children(nodes,guid,kind)
        d=details[guid]['details']
        p=d['begCoordinate'] if kind=='Beam' else d['origin']
        anchor={'x':p['x'],'y':p['y'],'z':d['zCoordinate'] if kind!='Object' else p['z']}
        target={k:anchor[k]+row['moveVector'][k] for k in 'xyz'}
        allowed.add(guid);allowed.update(g for g,_ in children)
        proof.append({'guid':guid,'kind':kind,'anchor':anchor,'target':target,
            'children':[g for g,_ in children],
            'typed':M.source_detail_fingerprint(details[guid],kind,anchor),
            'header':{k:v for k,v in details[guid].items() if k!='details'},
            'solid':M.solid_fingerprint(root,children,anchor,parent_guid=guid)})
        groups.append({'prototypeGuid':guid,'prototypeType':kind,
                       'sourceAnchor':anchor,'targets':[target]})
        sources[guid]=(root,children);targets[guid]=[target]
    check(set(affected)==allowed,'APA_NATIVE_TRANSLATION_COMPLETE_OWNED_SUBTREE_REQUIRED')
    M.verify_batch_layout(groups,sources,{g:e for g,e in nodes.items() if g not in allowed},targets)
    return {'status':'NATIVE_TRANSLATION_OWNED_SOURCE_AND_COLLISION_PASS','roots':proof}


def verify_translation_after(*,api,command,parameters,native_response,
                             before_guids,after_guids,affected,native_before,
                             native_after,source_proof):
    import apa_ac29_multi_prototype_native_copy as M
    rows=translation_rows(parameters)
    check(command=='MoveElements' and before_guids==after_guids,
          'APA_NATIVE_TRANSLATION_MUST_RETAIN_ALL_EXISTING_GUIDS')
    replies=native_response.get('executionResults') if isinstance(native_response,dict) else None
    check(isinstance(replies,list) and len(replies)==len(rows) and
          all(r.get('success') is True and 'error' not in r for r in replies),
          'APA_NATIVE_TRANSLATION_NATIVE_BATCH_RESULT_NOT_CONFIRMED')
    nodes={e['guid'].lower():e for e in native_after['elements']}
    check(set(nodes)==after_guids,'APA_NATIVE_TRANSLATION_FULL_NATIVE_BREP_REQUIRED')
    details=M.SINGLE.column_details(api,[r['guid'] for r in source_proof['roots']])
    for source in source_proof['roots']:
        guid=source['guid'];kind=source['kind'];root=nodes[guid]
        children=M.owned_children(nodes,guid,kind)
        check([g for g,_ in children]==source['children'] and
              {k:v for k,v in details[guid].items() if k!='details'}==source['header'],
              'APA_NATIVE_TRANSLATION_HEADER_OR_CHILD_GUID_CHANGED')
        check(M.source_detail_fingerprint(details[guid],kind,source['target'])==source['typed'] and
              M.solid_fingerprint(root,children,source['target'],parent_guid=guid)==source['solid'],
              'APA_NATIVE_TRANSLATION_TYPED_POSITION_OR_NATIVE_SOLID_MISMATCH')
    return {'status':'NATIVE_TRANSLATION_TYPED_BREP_OWNERSHIP_READBACK_PASS',
            'movedRootGuids':[r['guid'] for r in source_proof['roots']],
            'affectedGuids':sorted(affected),'allExistingGuidsRetained':True}


def installed_verifiers():
    """Conservative source-owned registry. No blanket Create/Modify grant."""
    from apa_ac29_existing_create_verifiers import extended_verifiers
    from apa_ac29_existing_modify_verifiers import existing_slab_modify_verifiers
    from apa_ac29_native_group_clone_verifier import installed_group_clone_verifiers
    checked = {
        "VerifiedNativeColumns": NativeVerifier(
            verifier_id="VerifiedNativeColumns", command="CreateColumns",
            effect="CREATE", before=verify_column_create_before,
            after=verify_column_create_after),
        'VerifiedNativeTranslation': NativeVerifier(
            verifier_id='VerifiedNativeTranslation',command='MoveElements',effect='MODIFY',
            before=verify_translation_before,after=verify_translation_after)
    }
    for extra in (extended_verifiers(), existing_slab_modify_verifiers(),
                  installed_group_clone_verifiers()):
        check(not set(checked).intersection(extra),
              "APA_NATIVE_REGISTRY_VERIFIER_ID_COLLISION")
        checked.update(extra)
    return checked
