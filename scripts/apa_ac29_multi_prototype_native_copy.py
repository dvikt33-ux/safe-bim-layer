"""Source-qualified multi-prototype Column/Beam/Object native copier for APA 29.

Reuses DynamicCommands.plan_reuse_existing + copy_multiple_prototypes,
SceneWriter SQLite, and guarded SaveProject. No new transport or writer.
Unknown source hierarchy, unsafe native associations, BREP differences or
uncertain results stop the operation without retries.
"""
from __future__ import annotations
import copy
import math
import re
from pathlib import Path
import json
import sqlite3
from contextlib import closing

import apa_ac29_reusable_native_copy as SINGLE

require = SINGLE.require
GUID = SINGLE.GUID
TYPES = {"Column": "ColumnSegment", "Beam": "BeamSegment", "Object": None}
COORDS = ("x", "y", "z")


def vector(point):
    require(isinstance(point, dict) and set(point) == set(COORDS) and
            all(type(point[k]) in (int, float) and
                math.isfinite(point[k]) and abs(point[k]) <= 10000
                for k in COORDS),
            "MULTI_COPY_FINITE_ABSOLUTE_XYZ_REQUIRED")
    return dict(point)


def validate_task(task, *, expected_project_sha, expected_project_path):
    fields = {"schemaVersion", "projectSha256", "projectPath",
              "expectedGuidCount", "expectedGuidSetHash",
              "expectedModelSignatureHash", "sceneId", "saveSceneId",
              "authorizationRef", "sourceEvidenceRef", "prototypes", "save"}
    require(isinstance(task, dict) and set(task) == fields and
            task["schemaVersion"] == "apa-ac29-multi-native-copy/1",
            "MULTI_COPY_TASK_SCHEMA_MISMATCH")
    require(task["projectSha256"] == expected_project_sha and
            task["projectPath"] == expected_project_path and task["save"] is True,
            "MULTI_COPY_APPROVED_PROJECT_AND_SAVE_REQUIRED")
    require(type(task["expectedGuidCount"]) is int and
            task["expectedGuidCount"] > 0 and
            all(isinstance(task[key], str) and
                re.fullmatch(r"[0-9a-f]{64}", task[key])
                for key in ("expectedGuidSetHash", "expectedModelSignatureHash")),
            "MULTI_COPY_EXACT_SOURCE_MODEL_SIGNATURE_REQUIRED")
    require(isinstance(task["sourceEvidenceRef"], str) and
            task["sourceEvidenceRef"].startswith("https://github.com/") and
            isinstance(task["authorizationRef"], str) and
            task["authorizationRef"].startswith("USER_APPROVED_") and
            len(task["authorizationRef"]) <= 200,
            "MULTI_COPY_EXPLICIT_SOURCE_AND_USER_AUTHORIZATION")
    for key in ("sceneId", "saveSceneId"):
        require(isinstance(task[key], str) and
                re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{3,79}",
                             task[key]), "MULTI_COPY_SCENE_ID_INVALID")
    require(task["sceneId"] != task["saveSceneId"],
            "MULTI_COPY_SCENE_IDS_CANNOT_MATCH")
    groups = task["prototypes"]
    require(isinstance(groups, list) and 1 <= len(groups) <= 200,
            "MULTI_COPY_PROTOTYPES_REQUIRE_1_TO_200")
    used, points, total = set(), set(), 0
    for group in groups:
        require(isinstance(group, dict) and
                set(group) == {"prototypeGuid", "prototypeType",
                               "sourceAnchor", "targets"},
                "MULTI_COPY_TYPED_GROUP_REQUIRED")
        guid = group["prototypeGuid"]
        require(isinstance(guid, str) and GUID.fullmatch(guid) and
                guid not in used and group["prototypeType"] in TYPES,
                "MULTI_COPY_UNIQUE_SUPPORTED_PROTOTYPE_REQUIRED")
        used.add(guid)
        anchor = vector(group["sourceAnchor"])
        targets = group["targets"]
        require(isinstance(targets, list) and targets,
                "MULTI_COPY_GROUP_WITHOUT_TARGETS")
        total += len(targets)
        for target in targets:
            point = vector(target)
            require(SINGLE.almost(point["z"], anchor["z"]),
                    "MULTI_COPY_VERTICAL_OFFSET_NEEDS_SEPARATE_TYPED_READBACK")
            dest = tuple(round(point[k], 6) for k in COORDS)
            require(dest not in points and
                    any(not SINGLE.almost(point[k], anchor[k])
                        for k in COORDS),
                    "MULTI_COPY_DUPLICATE_OR_ZERO_SHIFT_TARGET")
            points.add(dest)
    require(total <= 200, "MULTI_COPY_MORE_THAN_200_TARGETS")
    return task


def owned_children(elements, guid, family):
    """Only well-defined one-segment or no-child standalone instances."""
    children = [(g, row) for g, row in elements.items()
                if row.get("relationships", {}).get("hostGuid", "").lower()
                == guid]
    child_type = TYPES[family]
    if child_type is None:
        require(not children, "MULTI_COPY_OBJECT_HAS_DEPENDENTS")
    else:
        require(len(children) == 1 and children[0][1]["type"] == child_type,
                "MULTI_COPY_EXPECTED_ONE_NATIVE_SEGMENT")
    return children


def safe_native_lineage(row, *, parent=None):
    """Reject hosted objects and unrelated BIM dependencies, not just AABB."""
    relationships = row.get("relationships") or {}
    require(isinstance(relationships, dict), "MULTI_COPY_RELATIONSHIP_INVALID")
    if parent is None:
        require(not any(value not in (None, "", [], {}) for value in
                        relationships.values()),
                "MULTI_COPY_HOSTED_OR_DEPENDENT_ROOT_NOT_STANDALONE")
    else:
        require(relationships.get("hostGuid", "").lower() == parent and
                all(key == "hostGuid" or value in (None, "", [], {})
                    for key, value in relationships.items()),
                "MULTI_COPY_SEGMENT_HAS_UNRELATED_DEPENDENCIES")


def body_fingerprint(element, source_anchor):
    """Translated physical BREP, independent of generated native numbering.

    Reuse the existing oriented contour comparator. Native owner/body slots,
    vertex/edge indices and normal-pool order can change during a true copy;
    coordinates, oriented face loops, resolved normals and attributes cannot.
    """
    import archicad_connected_components as C
    bodies = element.get("bodies") or []
    require(isinstance(bodies, list) and bodies,
            "MULTI_COPY_SOURCE_NATIVE_BODY_MISSING")
    output = []
    for body in bodies:
        require(body.get("closed") is True,
                "MULTI_COPY_SOURCE_NATIVE_SOLID_NOT_CLOSED")
        vertices = body.get("vertices")
        require(isinstance(vertices, list) and vertices,
                "MULTI_COPY_NO_BREP_VERTICES")
        vnorm = []
        for vertex in vertices:
            require(isinstance(vertex, (list, tuple)) and len(vertex) == 3
                    and all(type(x) in (int, float) and math.isfinite(x)
                            for x in vertex),
                    "MULTI_COPY_NATIVE_VERTEX_INVALID")
            vnorm.append(tuple(round(vertex[i] - source_anchor[COORDS[i]], 5)
                               for i in range(3)))
        faces = body.get("faces")
        require(isinstance(faces, list) and faces,
                "MULTI_COPY_NO_NATIVE_FACES")
        canonical_faces=[]
        for face in faces:
            require(isinstance(face, dict) and
                    isinstance(face.get("contours"), list) and face['contours'] and
                    all(isinstance(ids, list) and len(ids) >= 3 and
                        all(type(idx) is int and 0 <= idx < len(vertices)
                            for idx in ids) for ids in face["contours"]),
                    "MULTI_COPY_FACE_CONTOURS_INVALID")
            contours=face['contours']
            geometry=C.body_face_keys({
                'vertices':[dict(zip(COORDS,v)) for v in vnorm],
                'polygons':[{'vertexIds':contours[0],'holes':contours[1:]}]})[0]
            properties={k:copy.deepcopy(v) for k,v in face.items() if k not in {
                'contours','vertices','holes','nativeFaceIndex',
                'signedLocalNormalIndex','signedNativeEdgeReferences'}}
            normal=None
            if 'signedLocalNormalIndex' in face:
                index=face['signedLocalNormalIndex'];normals=body.get('localNormals',[])
                require(type(index) is int and index!=0 and 0<abs(index)<=len(normals),
                        'MULTI_COPY_NATIVE_NORMAL_REFERENCE_INVALID')
                value=normals[abs(index)-1];sign=1 if index>0 else -1
                require(set(value)==set(COORDS) and all(type(value[k]) in (int,float)
                    and math.isfinite(value[k]) for k in COORDS),'MULTI_COPY_NATIVE_NORMAL_INVALID')
                normal=tuple(round(sign*value[k],7) for k in COORDS)
            canonical_faces.append({'geometry':geometry,'normal':normal,'properties':properties})
        canonical_faces.sort(key=lambda row:(row['geometry'],C.RUN.canonical(row['properties'])))
        canonical_edges=[]
        for edge in body.get('edges',[]):
            ids=edge.get('vertices',[])
            require(len(ids)==2 and all(type(i) is int and 0<=i<len(vnorm) for i in ids),
                    'MULTI_COPY_NATIVE_EDGE_REFERENCE_INVALID')
            canonical_edges.append({'endpoints':sorted(vnorm[i] for i in ids),
                'properties':{k:copy.deepcopy(v) for k,v in edge.items()
                    if k not in {'vertices','nativeEdgeIndex'}}})
        canonical_edges.sort(key=lambda row:(row['endpoints'],C.RUN.canonical(row['properties'])))
        if 'parentGuid' in body:
            require(body['parentGuid'].lower()==element.get('guid','').lower(),
                    'MULTI_COPY_NATIVE_BODY_OWNER_MISMATCH')
        other = {k: copy.deepcopy(v) for k, v in body.items()
                 if k not in {'vertices','faces','edges','localNormals','nativeBodyIndex','parentGuid'}}
        output.append({'relativeVertices':sorted(vnorm),'edges':canonical_edges,
                       'faces':canonical_faces,'bodyProperties':other})
    return sorted(output,key=C.RUN.canonical)


def solid_fingerprint(root, children, anchor, *, parent_guid):
    safe_native_lineage(root)
    for guid, row in children:
        safe_native_lineage(row, parent=parent_guid)
    return {
        "type": root["type"],
        "story": root.get("homeStory"),
        "rootMaterial": root.get("materialBindings"),
        "rootBREP": body_fingerprint(root, anchor)
                    if root.get("bodies") else [],
        "children": [{
            "type": row["type"],
            "material": row.get("materialBindings"),
            "BREP": body_fingerprint(row, anchor),
        } for _, row in children],
    }


def source_detail_fingerprint(detail, kind, anchor):
    """Normalize ONLY the documented coordinates for each native type.

    Unknown position encodings stop; never silently compare arbitrary fields
    as though they proved actual world placement.
    """
    require(detail.get("type") == kind and
            isinstance(detail.get("details"), dict),
            "MULTI_COPY_TYPED_DETAILS_MISSING")
    d = copy.deepcopy(detail["details"])
    if kind in ("Column", "Object"):
        origin = d.get("origin")
        require(isinstance(origin, dict) and
                all(SINGLE.almost(origin.get(k), anchor[k])
                    for k in ("x", "y")),
                "MULTI_COPY_ORIGIN_NOT_MATCHED_TO_NATIVE_ANCHOR")
        for k in ("x", "y"):
            origin[k] = round(origin[k] - anchor[k], 5)
        if "z" in origin:
            require(SINGLE.almost(origin["z"], anchor["z"]),
                    "MULTI_COPY_OBJECT_Z_ORIGIN_UNQUALIFIED")
            origin["z"] = round(origin["z"]-anchor["z"], 5)
    else:
        for key in ("begCoordinate", "endCoordinate"):
            origin = d.get(key)
            require(isinstance(origin, dict) and
                    all(type(origin.get(k)) in (int, float) for k in ("x", "y")),
                    "MULTI_COPY_BEAM_NATIVE_AXIS_NOT_AVAILABLE")
            for k in ("x", "y"):
                origin[k] = round(origin[k] - anchor[k], 5)
        require(SINGLE.almost(d.get("zCoordinate"), anchor["z"]),
                "MULTI_COPY_BEAM_SOURCE_Z_NOT_BOUND")
        d["zCoordinate"] = round(d["zCoordinate"]-anchor["z"], 5)
        if "level" in d:
            # Level must not be inferred from relative story changes.
            require(type(d["level"]) in (float, int),
                    "MULTI_COPY_BEAM_LEVEL_INVALID")
    return {"type": kind, "floorIndex": detail.get("floorIndex"),
            "details": d}


def destination_boxes(root, children, anchor, target):
    boxes = []
    for node in [root] + [r for _, r in children]:
        for body in node.get("bodies") or []:
            vs = body.get("vertices") or []
            require(vs, "MULTI_COPY_NATIVE_BODY_VERTEX_PROOF_REQUIRED")
            boxes.append([
                (min(v[i] - anchor[COORDS[i]] + target[COORDS[i]] for v in vs),
                 max(v[i] - anchor[COORDS[i]] + target[COORDS[i]] for v in vs))
                for i in range(3)])
    require(boxes, "MULTI_COPY_SOURCE_HAS_NO_TRANSLATABLE_SOLID")
    return boxes


def verify_batch_layout(prototypes, source_elements, full_model, targets):
    """Preflight all new solids against each other AND existing native solids."""
    external = []
    for guid, row in full_model.items():
        for body in row.get("bodies") or []:
            vs = body.get("vertices") or []
            if vs:
                external.append((guid, [
                    (min(v[i] for v in vs), max(v[i] for v in vs))
                    for i in range(3)]))
    incoming = []
    for source in prototypes:
        group = targets[source["prototypeGuid"]]
        root, children = source_elements[source["prototypeGuid"]]
        for target in group:
            candidate_boxes = destination_boxes(root, children,
                                                source["sourceAnchor"], target)
            for box in candidate_boxes:
                for old_guid, previous in external:
                    require(not SINGLE.native_aabb_overlaps(box, previous),
                            "MULTI_COPY_EXISTING_BREP_CONTACT_REQUIRES_VERIFIED_JUNCTION:"
                            + old_guid)
                for prior in incoming:
                    require(not SINGLE.native_aabb_overlaps(box, prior),
                            "MULTI_COPY_NEW_SOLIDS_INTERSECT")
            # A root and its owned BeamSegment may share their entire volume:
            # they are ONE destination, not two separate colliding copies.
            incoming.extend(candidate_boxes)
    return {"status": "MULTI_COPY_ALL_NATIVE_BREP_AABB_CLEAR_PASS",
            "evaluatedSolidBoxes": len(incoming)}


def prepare_verified_groups(task, model, typed_details, router, RUN):
    """Select existing prototypes from exact native family fingerprints."""
    sources, targets = [], []
    source_elements = {}
    for group in task["prototypes"]:
        guid = group["prototypeGuid"]
        kind = group["prototypeType"]
        require(guid in model and model[guid]["type"] == kind,
                "MULTI_COPY_SOURCE_NATIVE_TYPE_CHANGED")
        root = model[guid]
        children = owned_children(model, guid, kind)
        root_facts = source_detail_fingerprint(
            typed_details[guid], kind, group["sourceAnchor"])
        family = solid_fingerprint(root, children, group["sourceAnchor"],
                                   parent_guid=guid)
        signature = RUN.digest({"typed": root_facts, "BREP": family})
        source_elements[guid] = (root, children)
        sources.append({"type": kind, "familySignature": signature,
                        "storyIndex": typed_details[guid]["floorIndex"],
                        "anchor": group["sourceAnchor"],
                        "guid": guid, "nativeReadbackVerified": True})
        for target in group["targets"]:
            targets.append({"type": kind, "familySignature": signature,
                            "storyIndex": typed_details[guid]["floorIndex"],
                            "anchor": target,
                            "sourceRef": task["sourceEvidenceRef"]})
    chosen = router.plan_reuse_existing(sources, targets)
    require(chosen["status"] == "COPY_FIRST_PLAN_SOURCE_VERIFIED_NO_WRITES" and
            not chosen["unmatchedTargetsPendingPrototype"] and
            chosen["newCopyCount"] == len(targets) and
            len(chosen["copyGroups"]) == len(sources),
            "MULTI_COPY_EXISTING_SELECTOR_GROUP_MISMATCH")
    source_map = {s["guid"]: s for s in sources}
    for chosen_group in chosen["copyGroups"]:
        guid = chosen_group["prototypeGuid"].lower()
        require(guid in source_map and
                chosen_group["prototypeType"] == source_map[guid]["type"],
                "MULTI_COPY_SELECTOR_SOURCE_FAMILY_DRIFT")
    declared = {group["prototypeGuid"]: {
        tuple(round(target[k], 6) for k in COORDS)
        for target in group["targets"]} for group in task["prototypes"]}
    for selected in chosen["copyGroups"]:
        source = selected["prototypeGuid"].lower()
        anchor = next(g["sourceAnchor"] for g in task["prototypes"]
                      if g["prototypeGuid"] == source)
        actual = {tuple(round(anchor[k] + delta[k], 6) for k in COORDS)
                  for delta in selected["displacements"]}
        require(actual == declared[source],
                "MULTI_COPY_SELECTOR_CHANGED_APPROVED_PROTOTYPE_TARGETS")
    return chosen["copyGroups"], source_elements


def expected_new_types(task):
    counts = {}
    for group in task["prototypes"]:
        root = group["prototypeType"]
        n = len(group["targets"])
        counts[root] = counts.get(root, 0) + n
        child = TYPES[root]
        if child:
            counts[child] = counts.get(child, 0) + n
    return counts


def verify_after_copy(task, old, current, baseline, typed_details,
                      original_fingerprints, RUN):
    """Independent native postflight by copy family + ownership and positions."""
    old_set = set(old)
    newly = set(current) - old_set
    counts = expected_new_types(task)
    require(old_set <= set(current) and
            len(newly) == sum(counts.values()),
            "MULTI_COPY_NEW_NATIVE_GUID_DELTA_MISMATCH")
    actual = {}
    for guid in newly:
        kind = current[guid].get("type")
        actual[kind] = actual.get(kind, 0) + 1
    require(actual == counts, "MULTI_COPY_NATIVE_TYPE_COUNTS_NOT_PROVEN")
    proven_new_roots = set()
    for group in task["prototypes"]:
        guid = group["prototypeGuid"]
        kind = group["prototypeType"]
        origin_fp = original_fingerprints[guid]
        require(guid in current and
                current[guid] == baseline[guid],
                "MULTI_COPY_ORIGINAL_SOURCE_BREP_CHANGED")
        for target in group["targets"]:
            matches = []
            for candidate in newly:
                row = current[candidate]
                if row["type"] != kind or candidate not in typed_details:
                    continue
                try:
                    typed = source_detail_fingerprint(
                        typed_details[candidate], kind, target)
                except (ValueError, TypeError, KeyError):
                    continue
                if typed == origin_fp["typed"]:
                    owned = owned_children(current, candidate, kind)
                    actual_fp = solid_fingerprint(
                        row, owned, target, parent_guid=candidate)
                    if actual_fp == origin_fp["BREP"]:
                        matches.append(candidate)
            require(len(matches) == 1 and matches[0] not in proven_new_roots,
                    "MULTI_COPY_NATIVE_ROOT_DETAILS_BREP_NOT_UNIQUE")
            proven_new_roots.add(matches[0])
    expected_root_count = sum(len(g["targets"]) for g in task["prototypes"])
    require(len(proven_new_roots) == expected_root_count and
            proven_new_roots == {g for g in newly if current[g]["type"] in TYPES},
            "MULTI_COPY_ALL_NEW_ROOTS_NOT_ACCOUNTED_FOR")
    return {"status": "MULTI_COPY_TYPED_NATIVE_BREP_READBACK_PASS",
            "newPhysicalCopyCount": sum(
                len(group["targets"]) for group in task["prototypes"]),
            "unchangedPrototypeGuids": sorted(
                group["prototypeGuid"] for group in task["prototypes"]),
            "newGuidCount": len(newly), "newTypeCounts": counts}


def reconcile_existing_multi_task(task, *, original_snapshot, api, writer, router,
                                  APA, RUN, components, capture_native, current_sha):
    """Read-only acceptance of ONE already attempted copy; never re-send it."""
    validate_task(task,expected_project_sha=current_sha(),expected_project_path=RUN.EXPECTED_PATH)
    require(api.write_attempts==0,'MULTI_RECONCILE_FRESH_EVIDENCE_API_REQUIRED')
    old={e['guid'].lower():e for e in original_snapshot['elements']}
    require(len(old)==len(original_snapshot['elements'])==task['expectedGuidCount'] and
        RUN.digest(sorted(old))==task['expectedGuidSetHash'] and
        RUN.digest({g:components.ROOF.geometry_signature(old[g]) for g in sorted(old)})==
        task['expectedModelSignatureHash'],'MULTI_RECONCILE_ORIGINAL_APPROVED_SNAPSHOT_DRIFT')
    # Bind the actual previous dispatch to the same task, not just its label.
    with closing(sqlite3.connect(f'file:{Path(writer.journal_path).as_posix()}?mode=ro',uri=True)) as db:
        row=db.execute('SELECT state,result FROM scenes WHERE scene_id=?',(task['sceneId'],)).fetchone()
        require(row is not None and row[0]=='PARTIAL_OR_UNKNOWN_OUTCOME',
                'MULTI_RECONCILE_REQUIRES_ORIGINAL_UNKNOWN_SCENE')
        attempted=json.loads(row[1]);prior_hash=RUN.digest(attempted)
    ids=sorted(APA.inventory_guids(api));post=capture_native(api,ids)
    current={e['guid'].lower():e for e in post['elements']}
    require(set(current)==set(ids),'MULTI_RECONCILE_COMPLETE_LIVE_BREP_REQUIRED')
    new=set(current)-set(old)
    roots=sorted(g for g in new if current[g]['type'] in TYPES)
    source_ids=[g['prototypeGuid'] for g in task['prototypes']]
    typed=SINGLE.column_details(api,source_ids+roots)
    groups,_=prepare_verified_groups(task,old,typed,router,RUN)
    parameters={'elementsWithMoveVectors':[
        {'elementId':{'guid':group['prototypeGuid']},'moveVector':delta,'copy':True}
        for group in groups for delta in group['displacements']]}
    require(attempted.get('command')=='MoveElements' and
        attempted.get('intent',{}).get('parameters')==parameters and
        attempted.get('nativeResponse',{}).get('executionResults')==
        [{'success':True}]*sum(len(g['targets']) for g in task['prototypes']),
        'MULTI_RECONCILE_UNKNOWN_DISPATCH_NOT_BOUND_TO_EXACT_TASK')
    fingerprints={}
    for group in task['prototypes']:
        guid=group['prototypeGuid'];kind=group['prototypeType'];anchor=group['sourceAnchor']
        fingerprints[guid]={
            'typed':source_detail_fingerprint(typed[guid],kind,anchor),
            'BREP':solid_fingerprint(old[guid],owned_children(old,guid,kind),anchor,parent_guid=guid)}
    proof=verify_after_copy(task,set(old),current,old,typed,fingerprints,RUN)
    require(components.retained_geometry_signatures(post,sorted(old))==
        components.retained_geometry_signatures(original_snapshot,sorted(old)),
        'MULTI_RECONCILE_OLD_MODEL_GEOMETRY_OR_SEMANTICS_CHANGED')
    require(current_sha()==task['projectSha256'] and api.write_attempts==0,
            'MULTI_RECONCILE_SAVED_FILE_OR_NATIVE_WRITE_DRIFT')
    return {'status':'EXISTING_MULTI_COPY_INDEPENDENT_NATIVE_RECONCILIATION_PASS',
        'originalSceneId':task['sceneId'],'originalSceneStatePreserved':row[0],
        'originalJournalResultHash':prior_hash,'taskHash':RUN.digest(task),
        'newRootGuids':roots,'newGuids':sorted(new),'finalGuidCount':len(ids),
        'nativeReadback':proof,'retainedSignatures':components.retained_geometry_signatures(post,ids),
        'guidSetHash':RUN.digest(ids),'modelWrites':0,'nativeCopyCalls':0,'automaticRetry':False}


def save_reconciled_multi_task(task, *, save_scene_id, original_snapshot, api, writer,
                               router, APA, RUN, components, capture_native,
                               current_sha, save_guard):
    """Fresh independent reads followed by ONE existing journaled SaveProject.

    Keeps the failed copy scene UNKNOWN forever; this is a separate accepted
    reconciliation/save scene, never a retry of MoveElements or a new writer.
    """
    require(save_scene_id not in (task['sceneId'],task['saveSceneId']),
            'MULTI_RECONCILE_DISTINCT_SAVE_SCENE_REQUIRED')
    SINGLE.stored_scenes_clear(writer.journal_path,(save_scene_id,))
    receipt=reconcile_existing_multi_task(task,original_snapshot=original_snapshot,
        api=api,writer=writer,router=router,APA=APA,RUN=RUN,components=components,
        capture_native=capture_native,current_sha=current_sha)
    router.review_policy('SaveProject','TRANSACTION','PROJECT',
        {'source':task['sourceEvidenceRef'],'sha256':router.contract_hash('SaveProject')})
    save_guard.enable_after_verified_copy()
    def before_save(native_api):
        with closing(sqlite3.connect(f'file:{Path(writer.journal_path).as_posix()}?mode=ro',uri=True)) as db:
            state,result=db.execute('SELECT state,result FROM scenes WHERE scene_id=?',(task['sceneId'],)).fetchone()
        require(state=='PARTIAL_OR_UNKNOWN_OUTCOME' and RUN.digest(json.loads(result))==
            receipt['originalJournalResultHash'] and current_sha()==task['projectSha256'] and
            RUN.digest(sorted(APA.inventory_guids(native_api)))==receipt['guidSetHash'],
            'MULTI_RECONCILE_BASELINE_OR_ORIGINAL_JOURNAL_CHANGED')
        return {'status':'INDEPENDENT_EXISTING_MULTI_COPY_SAVE_READY_PASS',
                'reconciliationHash':RUN.digest(receipt)}
    def after_save(reply,_):
        require(reply=={'success':True} and save_guard.new_saved_sha==current_sha() and
            RUN.digest(sorted(APA.inventory_guids(api)))==receipt['guidSetHash'],
            'MULTI_RECONCILE_SAVE_NOT_CONFIRMED_NEVER_RETRY')
        return {'status':'RECONCILED_EXISTING_MULTI_COPY_SAVED_PASS',
            'savedSha256':save_guard.new_saved_sha,'originalCopySceneStillUnknown':True,
            'reconciliationHash':RUN.digest(receipt)}
    result=router.execute(writer,save_scene_id,router.prepare('SaveProject',{}),[],
        receipt['retainedSignatures'],task['projectSha256'],task['authorizationRef'],
        'PROJECT',after_save,verify_before=before_save)
    require(result.get('status')=='PASS','MULTI_RECONCILE_SAVE_UNKNOWN_NO_RETRY')
    return {'status':'RECONCILED_EXISTING_MULTI_COPY_AND_SAVE_PASS',
        'reconciliation':receipt,'save':result,'nativeCopyCalls':0,'nativeSaveCalls':1,
        'savedSha256':save_guard.new_saved_sha,'automaticRetry':False}


def execute_multi_task(task, *, api, writer, router, APA, RUN, components,
                       capture_native, saved_project_sha, current_sha,
                       save_guard, known_reconciliation=None):
    """One original native multi-copy transaction and one journaled save.

    The caller binds the existing verified project and uses original
    EvidenceAPI(execute=True) and SceneWriter. An unresolved old scene must
    have independent exact-model reconciliation first. Never replay.
    """
    validate_task(task, expected_project_sha=saved_project_sha,
                  expected_project_path=RUN.EXPECTED_PATH)
    require(api.write_attempts == 0 and
            current_sha() == saved_project_sha,
            "MULTI_COPY_FRESH_APPROVED_PROJECT_REQUIRED")
    unresolved = SINGLE.stored_scenes_clear(
        writer.journal_path, (task["sceneId"], task["saveSceneId"]))
    if unresolved:
        p = known_reconciliation
        require(isinstance(p, dict) and
                p.get("status") ==
                "PREVIOUS_UNKNOWN_EFFECT_ABSENT_FROM_CURRENT_MODEL_PASS" and
                {r["sceneId"] for r in unresolved} == {p.get("sceneId")} and
                p.get("savedProjectSHA256") == saved_project_sha and
                p.get("modelWrites") == 0,
                "MULTI_COPY_HISTORIC_UNKNOWN_REQUIRES_EXACT_RECONCILIATION")
    original_guids = set(APA.inventory_guids(api))
    require(len(original_guids) == task["expectedGuidCount"] and
            RUN.digest(sorted(original_guids)) == task["expectedGuidSetHash"],
            "MULTI_COPY_APPROVED_GUID_BASELINE_CHANGED")
    source_dump = capture_native(api, sorted(original_guids))
    require(isinstance(source_dump, dict) and
            isinstance(source_dump.get("elements"), list),
            "MULTI_COPY_NATIVE_DUMP_MISSING")
    source_map = {row["guid"].lower(): row
                  for row in source_dump["elements"]}
    require(set(source_map) == original_guids,
            "MULTI_COPY_FULL_NATIVE_BASELINE_REQUIRED")
    native_signatures = {
        g: components.ROOF.geometry_signature(source_map[g])
        for g in sorted(original_guids)
    }
    require(RUN.digest(native_signatures) ==
            task["expectedModelSignatureHash"],
            "MULTI_COPY_APPROVED_BREP_HASH_CHANGED")
    if unresolved:
        require(known_reconciliation["guidSetHash"] ==
                RUN.digest(sorted(original_guids)) and
                known_reconciliation["brepSignaturesHash"] ==
                RUN.digest(native_signatures),
                "MULTI_COPY_HISTORIC_RECEIPT_NOT_CURRENT")
    source_ids = [p["prototypeGuid"] for p in task["prototypes"]]
    donor_details = SINGLE.column_details(api, source_ids)
    groups, sources = prepare_verified_groups(
        task, source_map, donor_details, router, RUN)
    targets = {row["prototypeGuid"]: row["targets"]
               for row in task["prototypes"]}
    verify_batch_layout(task["prototypes"], sources, source_map, targets)
    donor_proofs = {}
    for group in task["prototypes"]:
        guid, kind = group["prototypeGuid"], group["prototypeType"]
        root, children = sources[guid]
        donor_proofs[guid] = {
            "typed": source_detail_fingerprint(
                donor_details[guid], kind, group["sourceAnchor"]),
            "BREP": solid_fingerprint(
                root, children, group["sourceAnchor"], parent_guid=guid),
        }
    retained = sorted(original_guids - set(source_ids))
    retained_signatures = components.retained_geometry_signatures(
        source_dump, retained)
    require(set(retained_signatures) == set(retained),
            "MULTI_COPY_RETAINED_BREP_SIGNATURES_NOT_COMPLETE")
    router.review_policy(
        "MoveElements", "CREATE", "MODEL",
        {"source": task["sourceEvidenceRef"],
         "sha256": router.contract_hash("MoveElements")})
    router.review_policy(
        "SaveProject", "TRANSACTION", "PROJECT",
        {"source": task["sourceEvidenceRef"],
         "sha256": router.contract_hash("SaveProject")})
    all_new_guids = [None]
    successful_post_dump = [None]
    new_root_ids = [None]

    def preflight(native_api):
        require(set(APA.inventory_guids(native_api)) == original_guids and
                current_sha() == saved_project_sha,
                "MULTI_COPY_PRE_DISPATCH_BASELINE_CHANGED")
        typed = SINGLE.column_details(native_api, source_ids)
        for group in task["prototypes"]:
            key = group["prototypeGuid"]
            new_fact = source_detail_fingerprint(
                typed[key], group["prototypeType"], group["sourceAnchor"])
            require(new_fact == donor_proofs[key]["typed"],
                    "MULTI_COPY_SOURCE_TYPED_PROPERTIES_DRIFT")
        return {"status": "MULTI_COPY_COMPLETE_SOURCE_PREFLIGHT_PASS"}

    def postflight(reply, prior):
        after_ids = set(APA.inventory_guids(api))
        new_ids = after_ids - original_guids
        require(original_guids <= after_ids,
                "MULTI_COPY_PREVIOUS_GUID_LOST")
        post_dump = capture_native(api, sorted(after_ids))
        require(isinstance(post_dump, dict) and
                isinstance(post_dump.get("elements"), list),
                "MULTI_COPY_POST_NATIVE_DUMP_INVALID")
        post = {r["guid"].lower(): r for r in post_dump["elements"]}
        require(set(post) == after_ids,
                "MULTI_COPY_POST_MODEL_INVENTORY_NOT_COMPLETE")
        parent_types = set(TYPES)
        roots = sorted(g for g in new_ids
                       if post[g]["type"] in parent_types)
        typed = SINGLE.column_details(api, roots)
        proof = verify_after_copy(
            task, original_guids, post, source_map,
            typed, donor_proofs, RUN)
        require(proof["newPhysicalCopyCount"] == sum(
            len(g["targets"]) for g in task["prototypes"]),
            "MULTI_COPY_NATIVE_POSTFLIGHT_COUNT_INVALID")
        require(all(
            components.ROOF.geometry_signature(post[g]) ==
            components.ROOF.geometry_signature(source_map[g])
            for g in source_ids),
            "MULTI_COPY_PROTOTYPE_GEOMETRY_CHANGED")
        require(current_sha() == saved_project_sha,
                "MULTI_COPY_UNEXPECTED_EARLY_PROJECT_SAVE")
        successful_post_dump[0] = post_dump
        all_new_guids[0] = after_ids
        new_root_ids[0] = roots
        return proof

    native = router.copy_multiple_prototypes(
        writer, task["sceneId"], groups, retained_signatures,
        saved_project_sha, task["authorizationRef"],
        preflight, postflight)
    require(native.get("status") == "PASS" and
            api.calls["MoveElements"] == 1 and
            all_new_guids[0] is not None and
            successful_post_dump[0] is not None,
            "MULTI_COPY_NATIVE_UNKNOWN_OUTCOME_DO_NOT_REPLAY_OR_SAVE")
    all_signatures = components.retained_geometry_signatures(
        successful_post_dump[0], sorted(all_new_guids[0]))
    require(set(all_signatures) == all_new_guids[0],
            "MULTI_COPY_BEFORE_SAVE_COMPLETE_BREP_REQUIRED")
    save_guard.enable_after_verified_copy()

    def before_save(_):
        require(set(APA.inventory_guids(api)) == all_new_guids[0] and
                current_sha() == saved_project_sha,
                "MULTI_COPY_SAVED_BASELINE_DRIFT")
        return {"status": "MULTI_COPY_INDEPENDENT_POSTFLIGHT_SAVE_READY_PASS"}

    def after_save(reply, _):
        require(reply == {"success": True} and
                save_guard.new_saved_sha and
                current_sha() == save_guard.new_saved_sha and
                set(APA.inventory_guids(api)) == all_new_guids[0],
                "MULTI_COPY_SAVE_RESPONSE_OR_NEW_FILE_UNVERIFIED")
        return {"status": "MULTI_COPY_GUARDED_WORKING_PLN_SAVE_PASS",
                "newSavedSha256": save_guard.new_saved_sha}
    saved = router.execute(
        writer, task["saveSceneId"],
        router.prepare("SaveProject", {}),
        [], all_signatures, saved_project_sha,
        task["authorizationRef"], "PROJECT",
        after_save, verify_before=before_save)
    require(saved.get("status") == "PASS" and
            api.calls["SaveProject"] == 1,
            "MULTI_COPY_SAVE_UNKNOWN_DO_NOT_RETRY")
    return {
        "schema": "APA_AC29_NATIVE_MULTI_COPY_RESULT_V1",
        "status": "MULTI_PROTOTYPE_NATIVE_COPY_AND_SAVE_PASS",
        "copiedCount": sum(len(g["targets"]) for g in task["prototypes"]),
        "sourcePrototypeGuids": source_ids,
        "newRootGuids": new_root_ids[0],
        "newGuidCount": len(all_new_guids[0] - original_guids),
        "finalGuidCount": len(all_new_guids[0]),
        "newSavedSha256": save_guard.new_saved_sha,
        "nativeMoveCalls": 1, "nativeSaveCalls": 1,
        "automaticRetry": False,
    }
