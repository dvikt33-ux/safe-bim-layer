"""Reusable APA AC29 one-call native Column copy task.

This is an adapter to EXISTING DynamicCommands.copy_existing_many -> original
SceneWriter SQLite -> native SaveProject. It does not implement a new router,
transport, writer, or catalog. No BDD-specific coordinates, GUIDs or paths.

Source-qualified task inputs and explicitly authorized project binding are
supplied by the existing bridge. Unsupported families stop, never fall back
to equivalent CreateColumns or replay an ambiguous native result.
"""
from __future__ import annotations

import math
from pathlib import Path
import re
import sqlite3

GUID = re.compile(r"^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$")


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def almost(a, b, tolerance=0.0004):
    return type(a) in (float, int) and math.isfinite(a) and abs(a-b) <= tolerance


def validate_task(task, *, expected_project_sha, expected_project_path):
    keys = {"schemaVersion", "projectSha256", "projectPath",
            "expectedGuidCount", "expectedGuidSetHash", "expectedModelSignatureHash",
            "prototypeGuid", "prototypeOrigin", "targets", "sceneId",
            "saveSceneId", "authorizationRef", "sourceEvidenceRef", "save"}
    require(isinstance(task, dict) and set(task) == keys and
            task["schemaVersion"] == "apa-ac29-native-column-copy/1",
            "NATIVE_COPY_TASK_SCHEMA_INVALID")
    require(task["projectSha256"] == expected_project_sha and
            task["projectPath"] == expected_project_path,
            "NATIVE_COPY_EXACT_APPROVED_PLN_REQUIRED")
    require(type(task["expectedGuidCount"]) is int and
            task["expectedGuidCount"] > 0 and
            all(isinstance(task[k], str) and
                re.fullmatch(r"[0-9a-f]{64}", task[k]) for k in
                ("expectedGuidSetHash", "expectedModelSignatureHash")),
            "NATIVE_COPY_SOURCE_BASELINE_FINGERPRINT_REQUIRED")
    require(task["save"] is True and
            isinstance(task["authorizationRef"], str) and
            task["authorizationRef"].startswith("USER_APPROVED_") and
            len(task["authorizationRef"]) <= 200 and
            isinstance(task["sourceEvidenceRef"], str) and
            task["sourceEvidenceRef"].startswith("https://github.com/"),
            "NATIVE_COPY_EXPLICIT_USER_AND_SOURCE_APPROVAL_REQUIRED")
    require(isinstance(task["prototypeGuid"], str) and
            GUID.fullmatch(task["prototypeGuid"]) and
            isinstance(task["prototypeOrigin"], dict) and
            set(task["prototypeOrigin"]) == {"x", "y"} and
            all(type(n) in (float, int) and math.isfinite(n) for n in
                task["prototypeOrigin"].values()),
            "NATIVE_COPY_SOURCE_GUID_AND_ORIGIN_REQUIRED")
    require(isinstance(task["targets"], list) and
            1 <= len(task["targets"]) <= 200,
            "NATIVE_COPY_REQUIRES_1_TO_200_TARGETS")
    distinct = set()
    for item in task["targets"]:
        require(isinstance(item, dict) and set(item) == {"x", "y"}
                and all(type(v) in (float, int) and
                        math.isfinite(v) and abs(v) <= 10000
                        for v in item.values()),
                "NATIVE_COPY_TARGET_MUST_BE_EXACT_FINITE_XY")
        xy = (round(item["x"], 6), round(item["y"], 6))
        require(xy not in distinct and not (
            almost(item["x"], task["prototypeOrigin"]["x"]) and
            almost(item["y"], task["prototypeOrigin"]["y"])),
            "NATIVE_COPY_DUPLICATE_OR_SOURCE_POSITION")
        distinct.add(xy)
    for key in ("sceneId", "saveSceneId"):
        require(isinstance(task[key], str) and
                re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{3,79}",
                             task[key]),
                "NATIVE_COPY_SCENE_ID_INVALID")
    require(task["sceneId"] != task["saveSceneId"],
            "NATIVE_COPY_CREATE_AND_SAVE_SCENE_MUST_DIFFER")
    return task


def native_map(model, normalizer):
    rows = normalizer(model)["elements"]
    require(isinstance(rows, list), "NATIVE_COPY_MODEL_DUMP_INVALID")
    found = {}
    for row in rows:
        guid = row.get("guid")
        require(isinstance(guid, str) and GUID.fullmatch(guid.lower())
                and isinstance(row.get("type"), str) and
                guid.lower() not in found,
                "NATIVE_COPY_BREP_GUID_OR_TYPE_INVALID")
        found[guid.lower()] = row
    return found


def owned_segment(model, parent):
    matches = [(g, row) for g, row in model.items()
               if row.get("type") == "ColumnSegment" and
               (row.get("relationships", {}).get("hostGuid") or "").lower()
               == parent.lower()]
    require(len(matches) == 1,
            "NATIVE_COPY_COLUMN_MUST_OWN_EXACTLY_ONE_SEGMENT")
    return matches[0]


def column_details(api, guids):
    rows = api("GetDetailsOfElements", {
        "elements": [{"elementId": {"guid": g}} for g in guids]
    }).get("detailsOfElements")
    require(isinstance(rows, list) and len(rows) == len(guids) and
            all(isinstance(row, dict) and "error" not in row for row in rows),
            "NATIVE_COPY_TYPED_DETAILS_INCOMPLETE")
    return dict(zip(guids, rows))


def column_profile(row):
    require(row.get("type") == "Column" and row.get("floorIndex") == 0,
            "NATIVE_COPY_COLUMN_TYPE_OR_STORY_DRIFT")
    details = row.get("details") or {}
    origin = details.get("origin") or {}
    require(type(origin.get("x")) in (float, int) and
            type(origin.get("y")) in (float, int),
            "NATIVE_COPY_COLUMN_ORIGIN_MISSING")
    keys = ("width", "depth", "height", "zCoordinate",
            "axisRotationAngle", "buildingMaterialId")
    require(all(name in details for name in keys),
            "NATIVE_COPY_COLUMN_PROFILE_INCOMPLETE")
    return {name: details[name] for name in keys}, origin


def translated_vertices(segment, point):
    """Sorted actual native BREP vertices relative to root origin."""
    require(isinstance(segment.get("bodies"), list) and
            segment["bodies"], "NATIVE_COPY_SEGMENT_BREP_MISSING")
    shapes = []
    for body in segment["bodies"]:
        verts = body.get("vertices")
        require(isinstance(verts, list) and verts,
                "NATIVE_COPY_SEGMENT_BODY_VERTICES_MISSING")
        rel = []
        for vertex in verts:
            require(isinstance(vertex, (list, tuple)) and len(vertex) == 3
                    and all(type(v) in (float, int) and
                            math.isfinite(v) for v in vertex),
                    "NATIVE_COPY_INVALID_NATIVE_VERTEX")
            rel.append((round(vertex[0]-point["x"], 5),
                        round(vertex[1]-point["y"], 5),
                        round(vertex[2], 5)))
        shapes.append(tuple(sorted(rel)))
    return tuple(sorted(shapes))


def segment_profile(segment, xy):
    return {
        "material": segment.get("materialBindings", {}).get("buildingMaterial"),
        "vertices": translated_vertices(segment, xy),
    }


def stored_scenes_clear(journal, ids):
    require(Path(journal).is_file(), "NATIVE_COPY_EXISTING_SCENEWRITER_REQUIRED")
    with sqlite3.connect(f"file:{Path(journal).as_posix()}?mode=ro", uri=True) as db:
        for scene in ids:
            require(db.execute("SELECT 1 FROM scenes WHERE scene_id=?",
                               (scene,)).fetchone() is None,
                    "NATIVE_COPY_SCENE_ALREADY_ATTEMPTED_NEVER_RETRY")
        return [{"sceneId": scene, "state": state}
                for scene, state in db.execute(
                    "SELECT scene_id,state FROM scenes WHERE state != 'PASS'")]


class GuardedSaveTransport:
    """Wrap the ORIGINAL APA.native_transport; guard only a single SaveProject.

    The wrapper does not implement network transport. Exact saved-copy hash
    and protected source are checked before and after the ONLY allowed save.
    """

    def __init__(self, native_transport, bind_saved_copy, project_path,
                 original_path, current_sha, source_sha, project_name,
                 port, authorization_ref):
        self._native_transport = native_transport
        self._bind = bind_saved_copy
        self._project = Path(project_path)
        self._original = Path(original_path)
        self._current = current_sha
        self._source = source_sha
        self._name = project_name
        self._port = port
        self._auth = authorization_ref
        self._may_save = False
        self._save_attempted = False
        self.new_saved_sha = None
        require(current_sha() and self._source() and
                self._project.is_file() and self._original.is_file(),
                "NATIVE_COPY_PROJECT_PROTECTION_INCOMPLETE")

    def enable_after_verified_copy(self):
        require(not self._may_save and not self._save_attempted and
                self.new_saved_sha is None,
                "NATIVE_COPY_SAVE_ALREADY_ARMED_OR_ATTEMPTED")
        self._may_save = True

    def __call__(self, command, parameters):
        if command != "SaveProject":
            return self._native_transport(command, parameters)
        require(self._may_save and not self._save_attempted and
                parameters == {},
                "NATIVE_COPY_SAVE_ONLY_AFTER_COMPLETE_READBACK")
        self._save_attempted = True
        old_project = self._current()
        old_original = self._source()
        reply = self._native_transport(command, parameters)
        require(reply == {"success": True},
                "NATIVE_COPY_NATIVE_SAVE_NOT_CONFIRMED")
        new_project = self._current()
        require(new_project != old_project and
                self._source() == old_original,
                "NATIVE_COPY_SAVED_FILE_OR_PROTECTED_SOURCE_DRIFT")
        self._bind(self._port, str(self._project), self._name,
                   new_project, self._auth + ":SAVED")
        self.new_saved_sha = new_project
        return reply


def execute_task(task, *, api, writer, router, APA, RUN, components,
                 capture_native, saved_project_sha, current_sha,
                 save_guard, known_reconciliation=None):
    """One native copy call + one guarded SaveProject; no alternate executor.

    The caller already bound authorized saved project via RUN, constructed
    EvidenceAPI(execute=True), and pinned source manifest to exact Git blob.
    The save_guard wraps the same native transport and records the new file
    SHA only after a successful response.
    """
    require(api.write_attempts == 0,
            "NATIVE_COPY_FRESH_TASK_API_REQUIRED")
    validate_task(task, expected_project_sha=saved_project_sha,
                  expected_project_path=RUN.EXPECTED_PATH)
    require(current_sha() == saved_project_sha,
            "NATIVE_COPY_SAVED_PROJECT_CHANGED")
    unresolved = stored_scenes_clear(
        writer.journal_path, (task["sceneId"], task["saveSceneId"]))
    if unresolved:
        receipt = known_reconciliation
        require(isinstance(receipt, dict) and
                receipt.get("status") ==
                "PREVIOUS_UNKNOWN_EFFECT_ABSENT_FROM_CURRENT_MODEL_PASS" and
                {r["sceneId"] for r in unresolved} ==
                {receipt.get("sceneId")} and
                receipt.get("savedProjectSHA256") == saved_project_sha and
                receipt.get("modelWrites") == 0,
                "NATIVE_COPY_UNRECONCILED_HISTORY_NOT_VERIFIED")
    original = set(APA.inventory_guids(api))
    require(len(original) == task["expectedGuidCount"] and
            RUN.digest(sorted(original)) == task["expectedGuidSetHash"],
            "NATIVE_COPY_SOURCE_INVENTORY_DRIFT")
    model_before = capture_native(api, sorted(original))
    native_before = native_map(model_before, components.G.normalize_dump)
    require(set(native_before) == original,
            "NATIVE_COPY_COMPLETE_BASELINE_MODEL_REQUIRED")
    signatures_before = {
        guid: components.ROOF.geometry_signature(native_before[guid])
        for guid in sorted(original)
    }
    require(RUN.digest(signatures_before) == task["expectedModelSignatureHash"],
            "NATIVE_COPY_SOURCE_BREP_FINGERPRINT_DRIFT")
    if unresolved:
        require(known_reconciliation["guidSetHash"] ==
                RUN.digest(sorted(original)) and
                known_reconciliation["brepSignaturesHash"] == RUN.digest({
                    guid: components.ROOF.geometry_signature(native_before[guid])
                    for guid in sorted(original)
                }), "NATIVE_COPY_HISTORICAL_RECONCILIATION_IS_STALE")
    source = task["prototypeGuid"]
    require(source in original and native_before[source]["type"] == "Column",
            "NATIVE_COPY_SOURCE_ROOT_NOT_A_COLUMN")
    originals = column_details(api, [source])
    source_profile, source_xy = column_profile(originals[source])
    require(all(almost(source_xy[axis], task["prototypeOrigin"][axis])
                for axis in ("x", "y")),
            "NATIVE_COPY_SOURCE_ORIGIN_CHANGED")
    original_child_guid, source_child = owned_segment(native_before, source)
    original_segment = segment_profile(source_child, source_xy)
    original_root_brep = components.ROOF.geometry_signature(
        native_before[source])
    original_child_brep = components.ROOF.geometry_signature(source_child)

    # Strict broad-phase no-overlap policy: unsupported host/roof junctions
    # fail closed pending independent source-qualified geometry adapters.
    bounds = []
    for guid, row in native_before.items():
        for body in row.get("bodies", []):
            vertices = body.get("vertices") or []
            if vertices:
                bounds.append((guid, [(min(v[i] for v in vertices),
                                      max(v[i] for v in vertices))
                                     for i in range(3)]))
    local_shape = translated_vertices(source_child, source_xy)
    candidates = []
    for target in task["targets"]:
        # This bounding box is derived from every SOURCE BREP vertex,
        # translated to the requested target, not a guessed section size.
        expanded = []
        for body in local_shape:
            for x, y, z in body:
                expanded.append((x + target["x"], y + target["y"], z))
        candidate = [(min(v[i] for v in expanded), max(v[i] for v in expanded))
                     for i in range(3)]
        # Different approved coordinates can still make physical solids overlap.
        # Reject this BEFORE the single native batch is dispatched.
        for prior in candidates:
            require(not all(candidate[i][0] < prior[i][1] - 1e-7 and
                            prior[i][0] < candidate[i][1] - 1e-7
                            for i in range(3)),
                    "NATIVE_COPY_TARGETS_INTERSECT_EACH_OTHER")
        candidates.append(candidate)
        for guid, existing in bounds:
            require(not all(candidate[i][0] < existing[i][1] - 1e-7 and
                            existing[i][0] < candidate[i][1] - 1e-7
                            for i in range(3)),
                    "NATIVE_COPY_EXISTING_BREP_CONTACT_REQUIRES_VERIFIED_JUNCTION:"
                    + guid)
    retained = sorted(original - {source})
    signatures = components.retained_geometry_signatures(
        model_before, retained)
    require(set(signatures) == set(retained),
            "NATIVE_COPY_RETAINED_BASELINE_BREP_INCOMPLETE")
    expected = task["targets"]
    # Use the EXISTING copy-first selector, not a manually chosen native
    # command or bespoke prototype grouping.
    family_signature = RUN.digest({
        "type": "Column", "profile": source_profile,
        "childMaterialAndBREP": original_segment, "storyIndex": 0,
    })
    selected = router.plan_reuse_existing([{
        "type": "Column", "familySignature": family_signature,
        "storyIndex": 0, "anchor": {
            "x": source_xy["x"], "y": source_xy["y"], "z": 0.0
        }, "guid": source, "nativeReadbackVerified": True,
    }], [{
        "type": "Column", "familySignature": family_signature,
        "storyIndex": 0, "anchor": {
            "x": item["x"], "y": item["y"], "z": 0.0
        }, "sourceRef": task["sourceEvidenceRef"],
    } for item in expected])
    require(selected["status"] == "COPY_FIRST_PLAN_SOURCE_VERIFIED_NO_WRITES"
            and not selected["unmatchedTargetsPendingPrototype"]
            and selected["newCopyCount"] == len(expected)
            and selected["nativeCopyCallsRequired"] == 1
            and len(selected["copyGroups"]) == 1
            and selected["copyGroups"][0]["prototypeGuid"].lower() == source,
            "NATIVE_COPY_SELECTOR_DID_NOT_CONFIRM_REUSE")
    vectors = selected["copyGroups"][0]["displacements"]
    router.review_policy(
        "MoveElements", "CREATE", "MODEL",
        {"source": task["sourceEvidenceRef"],
         "sha256": router.contract_hash("MoveElements")})
    router.review_policy(
        "SaveProject", "TRANSACTION", "PROJECT",
        {"source": task["sourceEvidenceRef"],
         "sha256": router.contract_hash("SaveProject")})
    added_roots = []
    native_after = [None]
    after_guid_set = [None]

    def verify_before(native_api):
        require(set(APA.inventory_guids(native_api)) == original and
                current_sha() == saved_project_sha,
                "NATIVE_COPY_PREWRITE_MODEL_CHANGED")
        details_now = column_details(native_api, [source])
        current_profile, current_xy = column_profile(details_now[source])
        require(current_profile == source_profile and
                current_xy == source_xy,
                "NATIVE_COPY_PROTOTYPE_CHANGED_BEFORE_WRITE")
        return {"status": "NATIVE_SOURCE_AND_MODEL_PREFLIGHT_PASS"}

    def verify_after(reply, _prior):
        now = set(APA.inventory_guids(api))
        added = now - original
        count = len(expected)
        require(original <= now and len(added) == 2 * count and
                len(now) == len(original) + 2*count,
                "NATIVE_COPY_EXACT_COLUMNS_AND_SEGMENTS_GUID_DELTA_REQUIRED")
        dump = capture_native(api, sorted(now))
        native = native_map(dump, components.G.normalize_dump)
        require(set(native) == now,
                "NATIVE_COPY_POST_BREP_INCOMPLETE")
        root_ids = sorted(g for g in added if native[g]["type"] == "Column")
        child_ids = {g for g in added
                     if native[g]["type"] == "ColumnSegment"}
        require(len(root_ids) == len(child_ids) == count and
                set(root_ids) | child_ids == added,
                "NATIVE_COPY_ROOT_CHILD_TYPES_INDEPENDENT_BREP_FAILED")
        root_details = column_details(api, root_ids)
        seen = set()
        for target in expected:
            candidates = [
                g for g in root_ids
                if all(almost(column_profile(root_details[g])[1][k],
                              target[k]) for k in ("x", "y"))
            ]
            require(len(candidates) == 1 and candidates[0] not in seen,
                    "NATIVE_COPY_TYPED_ROOT_POSITION_NOT_UNIQUE")
            guid = candidates[0]
            profile, pos = column_profile(root_details[guid])
            require(profile == source_profile,
                    "NATIVE_COPY_COLUMN_SCALAR_PROFILE_NOT_EQUAL_TO_SOURCE")
            owner, segment = owned_segment(native, guid)
            require(owner in child_ids and
                    segment_profile(segment, pos) == original_segment,
                    "NATIVE_COPY_CHILD_OWNERSHIP_OR_TRANSLATED_BODY_MISMATCH")
            seen.add(guid)
        current_source = column_details(api, [source])[source]
        require(column_profile(current_source) ==
                (source_profile, source_xy),
                "NATIVE_COPY_ORIGINAL_COLUMN_DETAILS_CHANGED")
        src_child_now_id, src_child_now = owned_segment(native, source)
        require(src_child_now_id == original_child_guid and
                components.ROOF.geometry_signature(native[source]) ==
                original_root_brep and
                components.ROOF.geometry_signature(src_child_now) ==
                original_child_brep,
                "NATIVE_COPY_ORIGINAL_NATIVE_SOURCE_BREP_CHANGED")
        require(current_sha() == saved_project_sha,
                "NATIVE_COPY_UNEXPECTED_PRE_SAVE_PLN_CHANGE")
        added_roots.extend(root_ids)
        native_after[0] = dump
        after_guid_set[0] = now
        return {
            "status": "NATIVE_COLUMN_COPY_NATIVE_BREP_PASS",
            "newPhysicalCopyCount": count,
            "prototypeGuidUnchanged": True,
            "createdRoots": root_ids,
            "createdSegments": sorted(child_ids),
            "resultGuidCount": len(now),
        }

    copied = router.copy_existing_many(
        writer, task["sceneId"], source, "Column", vectors,
        signatures, saved_project_sha, task["authorizationRef"],
        verify_before, verify_after)
    require(copied["status"] == "PASS" and
            len(added_roots) == len(expected) and
            api.calls["MoveElements"] == 1 and native_after[0] is not None,
            "NATIVE_COPY_OUTCOME_UNKNOWN_NEVER_REPLAY_OR_SAVE")
    all_ids = sorted(after_guid_set[0])
    all_signatures = components.retained_geometry_signatures(
        native_after[0], all_ids)
    require(set(all_signatures) == set(all_ids),
            "NATIVE_COPY_PRE_SAVE_BREP_SIGNATURES_INCOMPLETE")
    save_guard.enable_after_verified_copy()
    def verify_before_save(_api):
        require(set(APA.inventory_guids(api)) == after_guid_set[0] and
                current_sha() == saved_project_sha,
                "NATIVE_COPY_PRE_SAVE_MODEL_OR_FILE_DRIFT")
        return {"status": "NATIVE_COPY_NATIVE_BREP_SAVE_ALLOWED_PASS"}
    def verify_after_save(reply, _prior):
        require(reply == {"success": True} and
                save_guard.new_saved_sha and
                current_sha() == save_guard.new_saved_sha and
                set(APA.inventory_guids(api)) == after_guid_set[0],
                "NATIVE_COPY_SAVE_RESPONSE_FILE_OR_INVENTORY_NOT_VERIFIED")
        return {"status": "NATIVE_COPY_GUARDED_WORKING_PLN_SAVE_PASS",
                "savedSha256": save_guard.new_saved_sha}
    saved = router.execute(
        writer, task["saveSceneId"],
        router.prepare("SaveProject", {}), [],
        all_signatures, saved_project_sha,
        task["authorizationRef"], "PROJECT",
        verify_after_save, verify_before=verify_before_save)
    require(saved["status"] == "PASS" and
            api.calls["SaveProject"] == 1,
            "NATIVE_COPY_SAVE_UNKNOWN_NEVER_RETRY")
    return {
        "schema": "APA_AC29_REUSABLE_NATIVE_COLUMN_COPY_RESULT_V1",
        "status": "EXACT_NATIVE_COLUMNS_COPIED_AND_WORKING_PLN_SAVED_PASS",
        "sourceGuid": source,
        "createdRootGuids": added_roots,
        "copiedCount": len(expected),
        "nativeCopyCalls": 1,
        "nativeSaveCalls": 1,
        "newSavedProjectSha256": save_guard.new_saved_sha,
        "finalGuidCount": len(after_guid_set[0]),
        "replayed": False,
    }
