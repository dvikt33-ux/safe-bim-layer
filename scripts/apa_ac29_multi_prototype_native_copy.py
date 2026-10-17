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
    """Exact translated vertices + native face topology + body attributes.

    Lists retain native face/index ordering deliberately: if a provider
    renumbers or changes source semantics, verification must not guess.
    """
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
        for face in faces:
            require(isinstance(face, dict) and
                    isinstance(face.get("contours"), list) and
                    all(isinstance(ids, list) and len(ids) >= 3 and
                        all(type(idx) is int and 0 <= idx < len(vertices)
                            for idx in ids) for ids in face["contours"]),
                    "MULTI_COPY_FACE_CONTOURS_INVALID")
        other = {k: copy.deepcopy(v) for k, v in body.items()
                 if k not in ("vertices", "faces")}
        output.append({"relativeVertices": vnorm,
                       "faces": copy.deepcopy(faces), "bodyProperties": other})
    return output


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
            for box in destination_boxes(root, children,
                                         source["sourceAnchor"], target):
                for old_guid, previous in external:
                    require(not SINGLE.native_aabb_overlaps(box, previous),
                            "MULTI_COPY_EXISTING_BREP_CONTACT_REQUIRES_VERIFIED_JUNCTION:"
                            + old_guid)
                for prior in incoming:
                    require(not SINGLE.native_aabb_overlaps(box, prior),
                            "MULTI_COPY_NEW_SOLIDS_INTERSECT")
                incoming.append(box)
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
            require(len(matches) == 1,
                    "MULTI_COPY_NATIVE_ROOT_DETAILS_BREP_NOT_UNIQUE")
    return {"status": "MULTI_COPY_TYPED_NATIVE_BREP_READBACK_PASS",
            "newPhysicalCopyCount": sum(
                len(group["targets"]) for group in task["prototypes"]),
            "unchangedPrototypeGuids": sorted(
                group["prototypeGuid"] for group in task["prototypes"]),
            "newGuidCount": len(newly), "newTypeCounts": counts}
