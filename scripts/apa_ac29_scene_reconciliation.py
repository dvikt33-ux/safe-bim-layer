"""Read-only evidence gate for a historically UNKNOWN native SceneWriter operation.

Never changes existing SQLite scene state. A new native scene is allowed only
when the live GUID set AND every physical native BREP signature equal the
pre-mutation snapshot from the old attempt. Any missing/partial evidence
fails closed; original UNKNOWN remains recorded for audit.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sqlite3
from contextlib import closing


def verified_addition_checkpoint(journal_path, checkpoint, prior, prior_signatures,
                                 geom_signature, current_sha):
    """Admit only an independently captured, journaled Column addition.

    A checkpoint never converts the historical UNKNOWN to PASS. It explains
    the exact additional GUIDs from a later PASS scene and its verified save.
    Other commands and unjournaled additions remain blocked.
    """
    require(isinstance(checkpoint,dict) and {'sceneId','saveSceneId','nativeSnapshot'}<=set(checkpoint)
        <={'sceneId','saveSceneId','nativeSnapshot','mutationSceneIds'},
        'RECONCILE_EXACT_CHECKPOINT_REQUIRED')
    with closing(sqlite3.connect(f'file:{Path(journal_path).as_posix()}?mode=ro',uri=True)) as db:
        def accepted(scene):
            row=db.execute('SELECT state,result FROM scenes WHERE scene_id=?',(scene,)).fetchone()
            require(row is not None and row[0]=='PASS','RECONCILE_CHECKPOINT_SCENE_NOT_PASS')
            result=json.loads(row[1])
            require(result.get('status')=='PASS','RECONCILE_CHECKPOINT_RESULT_NOT_PASS')
            return result
        created=accepted(checkpoint['sceneId']);saved=accepted(checkpoint['saveSceneId'])
        changes=checkpoint.get('mutationSceneIds',[])
        require(isinstance(changes,list) and len(changes)<=20 and len(changes)==len(set(changes)),
                'RECONCILE_CHECKPOINT_UNIQUE_MUTATION_SCENES_REQUIRED')
        mutations=[accepted(scene) for scene in changes]
    require(created.get('command')=='CreateColumns' and saved.get('command')=='SaveProject' and
        saved.get('readback',{}).get('savedSha256')==current_sha,
        'RECONCILE_CHECKPOINT_COMMAND_OR_SAVED_HASH_NOT_QUALIFIED')
    proof=created.get('readback',{})
    require(proof.get('status')=='NATIVE_COLUMN_CREATE_TYPED_AND_BREP_READBACK_PASS',
            'RECONCILE_CHECKPOINT_TYPED_BREP_PROOF_MISSING')
    roots=[row['elementId']['guid'].lower() for row in created['nativeResponse']['elements']]
    require(roots and len(roots)==len(set(roots)) and
        set(roots)==set(proof.get('newRootGuids',[])) and
        len(roots)==proof.get('newRootCount')==proof.get('newSegmentCount'),
        'RECONCILE_CHECKPOINT_ROOT_RETURN_SCOPE_MISMATCH')
    snapshot=checkpoint['nativeSnapshot']
    nodes={row['guid'].lower():row for row in snapshot['elements']}
    require(len(nodes)==len(snapshot['elements']) and not set(roots)&set(prior),
            'RECONCILE_CHECKPOINT_GUID_AMBIGUITY')
    children=set()
    for root in roots:
        require(root in nodes and nodes[root]['type']=='Column',
                'RECONCILE_CHECKPOINT_ROOT_TYPE_CHANGED')
        owned=[g for g,e in nodes.items()
            if (e.get('relationships',{}).get('hostGuid') or '').lower()==root]
        require(len(owned)==1 and nodes[owned[0]]['type']=='ColumnSegment',
                'RECONCILE_CHECKPOINT_EXACT_NATIVE_SEGMENT_REQUIRED')
        children.update(owned)
    require(set(nodes)==set(prior)|set(roots)|children and
        len(nodes)==proof.get('nativeModelElementCount') and
        all(geom_signature(nodes[g])==prior_signatures[g] for g in prior),
        'RECONCILE_CHECKPOINT_UNEXPLAINED_ADDITION_OR_BASELINE_CHANGE')
    added=set(roots)|children
    for mutation in mutations:
        proof=mutation.get('readback',{})
        rows=mutation.get('intent',{}).get('parameters',{}).get('elementsWithMoveVectors',[])
        require(mutation.get('command')=='MoveElements' and rows and
            all(r.get('copy') is False and r['elementId']['guid'].lower() in roots for r in rows) and
            proof.get('status')=='NATIVE_TRANSLATION_TYPED_BREP_OWNERSHIP_READBACK_PASS' and
            set(proof.get('affectedGuids',[]))<=added and
            proof.get('allExistingGuidsRetained') is True and
            proof.get('createdGuids')==[] and proof.get('removedGuids')==[],
            'RECONCILE_CHECKPOINT_MODIFY_MUST_ONLY_MOVE_VERIFIED_ADDITIONS')
    if mutations:
        # Last accepted mutation proves this exact full postflight snapshot.
        import archicad_scene_run as RUN
        proof=mutations[-1]['readback']
        require(proof.get('afterGuidSetHash')==RUN.digest(sorted(nodes)) and
            proof.get('afterNativeBrepHash')==RUN.digest({
                g:geom_signature(nodes[g]) for g in sorted(nodes)}),
            'RECONCILE_CHECKPOINT_POSTFLIGHT_SNAPSHOT_HASH_MISMATCH')
    return {g:geom_signature(row) for g,row in nodes.items()}


MUTATIONS = frozenset({
    "MoveElements", "CreateColumns", "CreateWalls", "CreateBeams",
    "CreateSlabs", "CreateWindows", "CreateDoors", "SaveProject",
    "ModifyColumns", "ModifyWalls", "ModifyBeams", "ModifyRoofs",
})


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def snapshot_before_dispatch(records):
    require(isinstance(records, list) and records,
            "RECONCILE_RAW_RECORDS_MISSING")
    dispatched = next(
        (i for i, row in enumerate(records) if row.get("command") in MUTATIONS),
        None)
    require(dispatched is not None, "RECONCILE_NO_RECORDED_MUTATION")
    require(any(row.get("command") in MUTATIONS for row in records[dispatched:]),
            "RECONCILE_WRITE_DISPATCH_NOT_RECORDED")
    guids = [r for r in records[:dispatched]
             if r.get("command") == "GetAllElements" and
             isinstance(r.get("response"), dict)]
    dumps = [r for r in records[:dispatched]
             if r.get("command") == "GetModelDumpV1" and
             isinstance(r.get("response"), dict)]
    require(guids and dumps, "RECONCILE_NO_PREWRITE_NATIVE_BASELINE")
    return guids[-1]["response"], dumps[-1]["response"], dispatched


def inventory_guid_set(result):
    rows = result.get("elements")
    require(isinstance(rows, list), "RECONCILE_INVENTORY_SCHEMA_INVALID")
    values = []
    for row in rows:
        val = (row.get("elementId") or {}).get("guid")
        require(isinstance(val, str) and len(val) == 36,
                "RECONCILE_INVENTORY_GUID_INVALID")
        values.append(val.lower())
    require(len(values) == len(set(values)), "RECONCILE_DUPLICATE_GUID")
    return frozenset(values)


def signatures(raw, normalized, geom_signature):
    elements = normalized(raw)["elements"]
    require(isinstance(elements, list), "RECONCILE_NATIVE_DUMP_NOT_LIST")
    found = {}
    for row in elements:
        guid = row.get("guid")
        require(isinstance(guid, str) and isinstance(row.get("type"), str),
                "RECONCILE_NATIVE_TYPE_OR_GUID_MISSING")
        key = guid.lower()
        require(key not in found, "RECONCILE_NATIVE_DUPLICATE_GUID")
        found[key] = geom_signature(row)
    return found


def read_only_reconciliation(scene_id, journal_path, raw_path, read_api,
                             *, normalized, geom_signature, digest, expected_project_sha,
                             current_project_sha, accepted_checkpoint=None):
    """Compare recorded before-write snapshot to LIVE model; no native writes.

    Must be run by a currently scoped and guarded APA read-only API.
    read_api is ordinarily EvidenceAPI(execute=False), not a new transport.
    """
    journal_path, raw_path = Path(journal_path), Path(raw_path)
    require(journal_path.is_file() and raw_path.is_file(),
            "RECONCILE_EXISTING_JOURNAL_OR_RAW_LOG_MISSING")
    require(isinstance(scene_id, str) and len(scene_id) >= 8,
            "RECONCILE_SCENE_ID_REQUIRED")
    require(current_project_sha == expected_project_sha,
            "RECONCILE_CURRENT_SAVED_PROJECT_HASH_DRIFT")
    with closing(sqlite3.connect(f"file:{journal_path.as_posix()}?mode=ro", uri=True)) as db:
        row = db.execute("SELECT state,result FROM scenes WHERE scene_id=?",
                         (scene_id,)).fetchone()
        require(row is not None and row[0] in
                ("PARTIAL_OR_UNKNOWN_OUTCOME", "UNKNOWN_OUTCOME"),
                "RECONCILE_REQUIRES_EXISTING_UNKNOWN_SCENE")
        state = row[0]
        result = json.loads(row[1])
        step = db.execute("SELECT state FROM steps WHERE scene_id=?",
                          (scene_id,)).fetchall()
        require(step and any(x[0] == "UNKNOWN_OUTCOME" for x in step),
                "RECONCILE_STEP_UNKNOWN_MISSING")
    entries = [json.loads(line) for line in raw_path.read_text(encoding="utf8").splitlines()
               if line.strip()]
    inv, dump, dispatched = snapshot_before_dispatch(entries)
    prior = inventory_guid_set(inv)
    prior_signatures = signatures(dump, normalized, geom_signature)
    require(set(prior_signatures) == set(prior),
            "RECONCILE_PREWRITE_BREP_INVENTORY_INCOMPLETE")
    expected_signatures=prior_signatures
    if accepted_checkpoint is not None:
        expected_signatures=verified_addition_checkpoint(
            journal_path,accepted_checkpoint,prior,prior_signatures,
            geom_signature,current_project_sha)
    live = inventory_guid_set(read_api("GetAllElements", {}))
    require(live == set(expected_signatures),
            "RECONCILE_LIVE_GUID_SET_NOT_EQUAL_TO_PREWRITE")
    live_signatures = signatures(read_api("GetModelDumpV1", {}),
                                 normalized, geom_signature)
    require(live_signatures == expected_signatures,
            "RECONCILE_LIVE_BREP_NOT_EQUAL_TO_PREWRITE")
    # An UNKNOWN operation is not rewritten as PASS. The receipt means only
    # its effect is absent from CURRENT LIVE model, not that it never ran.
    evidence = {
        "schema": "APA_AC29_HISTORICAL_SCENE_RECONCILIATION_V1",
        "status": "PREVIOUS_UNKNOWN_EFFECT_ABSENT_FROM_CURRENT_MODEL_PASS",
        "sceneId": scene_id,
        "originalSceneState": state,
        "originalSceneReason": result.get("reason"),
        "originalUnknownRowsPreserved": True,
        "recordedMutationIndex": dispatched,
        "prewriteGuidCount": len(prior),
        "liveGuidCount": len(live),
        "guidSetHash": digest(sorted(live)),
        "brepSignaturesHash": digest(live_signatures),
        "savedProjectSHA256": current_project_sha,
        "modelWrites": 0,
        "replayPreviousScene": False,
        "acceptedAdditionCheckpoint": (accepted_checkpoint['sceneId']
                                        if accepted_checkpoint else None),
    }
    require(read_api.write_attempts == 0,
            "RECONCILE_EVIDENCE_API_REPORTED_NATIVE_WRITE")
    return evidence


# Historical BDD-only provenance pins: the two original UNKNOWN rows are NEVER
# changed. These digests were calculated directly from the original SQLite/raw
# files and separately match the accepted 298-GUID saved-copy receipt.
_BDD_HISTORY = {
    "BDD_BULK150_GRID_AND_LINE_20261016": (
        "ff51e3c205c99d6d134667cd95f53294f13eed8d4154b5a3c823728c90459c50",
        "MASS_COPY_UNEXPECTED_NATIVE_ELEMENT_TYPES", 150),
    "APA_AC29_REMOTE_COLUMN_BEAM_MULTI_COPY_20261017": (
        "1f84da89fb0387df3f707119bbb92d039cb89e874ddd98179a0202015092402c",
        "MULTI_COPY_NATIVE_ROOT_DETAILS_BREP_NOT_UNIQUE", 2),
}
_BDD_BULK_RAW_SHA = "96aaf47bd9f1b96e1b0b70af8708753cae16a6b1e0a0b447689fbb5905bac2b9"
_BDD_PREWRITE_GUID_HASH = "8d26a1e44fea2815743ca4998f091606ddc07a33942b4fa15076e95d37804b22"
_BDD_PREWRITE_BREP_HASH = "01b17d7f0be094e2c1e40709b621b8cb09e96054bcb083db0672b4007a3545bc"
_BDD_SAVED_298_SHA = "9293c799cf4a87792016cc76ca5f2c1d8e569f85d6cbab0b529f82d10a303a34"
_BDD_SAVES = {
    "BDD_KR13_1P12_1P13_AFTER_BATCH_SAVE_20261016":
        "e91d5670f20202c269d442bafc6e66a4cb13d223344122243b7237047a9ff3aa",
    "APA_AC29_REMOTE_COLUMNS_SAVE_20261017":
        "e43ac59f40dd04e00be3cfb3099d7944c4a63287aced6ffb50e0d6b4f708b311",
    "APA_AC29_REMOTE_TRANSLATION_SAVE_20261017":
        "72fcd891c8b43346a6dd871b2c9d89f3161199c50386e2fc498a00384a375d09",
    "APA_AC29_MULTI_RECONCILED_SAVE_20261017": _BDD_SAVED_298_SHA,
}


def reconcile_bdd_paired_history_read_only(
        journal_path, raw_path, read_api, *,
        current_project_sha, source_project_sha, expected_source_sha,
        guid_inventory, capture_model, geom_signature, digest):
    """Independently explain BOTH old UNKNOWNs using the saved 298-GUID model.

    Checks original raw input, SQLite result bytes, native dispatch outcomes,
    verified save sequence and a complete LIVE original-BREP preservation plus
    exact typed eight-GUID addition. Evidence is computed locally from READS,
    never sourced from GitHub task fields. A matching model does not rewrite
    any journal rows or retrospectively mark either native call PASS.
    """
    from collections import Counter
    journal_path, raw_path = Path(journal_path), Path(raw_path)
    require(current_project_sha == _BDD_SAVED_298_SHA and
            source_project_sha == expected_source_sha and
            journal_path.is_file() and raw_path.is_file(),
            "BDD_PAIRED_HISTORY_EXACT_SAVED_FILES_AND_LOGS_REQUIRED")
    require(hashlib.sha256(raw_path.read_bytes()).hexdigest() == _BDD_BULK_RAW_SHA,
            "BDD_PAIRED_HISTORY_ORIGINAL_BULK_RAW_SHA_DRIFT")
    # Snapshot-before-write is from the actual old 150-copy attempt.
    records = [json.loads(line) for line in
               raw_path.read_text(encoding="utf-8-sig").splitlines()
               if line.strip()]
    inv, dump, mutation_index = snapshot_before_dispatch(records)
    prior = inventory_guid_set(inv)
    prior_brep = signatures(dump, normalized=__import__(
        "archicad_connected_components").G.normalize_dump,
        geom_signature=geom_signature)
    require(len(prior) == len(prior_brep) == 290 and
            digest(sorted(prior)) == _BDD_PREWRITE_GUID_HASH and
            digest({g: prior_brep[g] for g in sorted(prior)}) ==
            _BDD_PREWRITE_BREP_HASH,
            "BDD_PAIRED_HISTORY_ORIGINAL_290_GUID_BREP_NOT_EXACT")

    old_rows = {}
    with closing(sqlite3.connect(
            f"file:{journal_path.as_posix()}?mode=ro", uri=True)) as db:
        rows = db.execute(
            "SELECT scene_id,state,result FROM scenes").fetchall()
        for scene_id, state, raw_result in rows:
            old_rows[scene_id] = (state, raw_result, json.loads(raw_result))
        unresolved = {
            name for name, state, _ in rows if state != "PASS"}
        require(unresolved == set(_BDD_HISTORY),
                "BDD_PAIRED_HISTORY_UNEXPECTED_UNRESOLVED_SCENES")
        history = []
        for scene_id, (expected_hash, reason, expected_count) in _BDD_HISTORY.items():
            require(scene_id in old_rows,
                    "BDD_PAIRED_HISTORY_MISSING_ORIGINAL_UNKNOWN")
            state, raw_result, result = old_rows[scene_id]
            step_states = db.execute(
                "SELECT state FROM steps WHERE scene_id=?",
                (scene_id,)).fetchall()
            native_rows = (result.get("nativeResponse") or {}).get(
                "executionResults")
            require(state == "PARTIAL_OR_UNKNOWN_OUTCOME" and
                    any(s[0] == "UNKNOWN_OUTCOME" for s in step_states) and
                    hashlib.sha256(raw_result.encode()).hexdigest() ==
                    expected_hash and result.get("command") == "MoveElements" and
                    reason in result.get("reason", "") and
                    isinstance(native_rows, list) and
                    len(native_rows) == expected_count and
                    all(row.get("success") is True for row in native_rows),
                    "BDD_PAIRED_HISTORY_UNKNOWN_ROW_OR_NATIVE_RESULT_DRIFT:" +
                    scene_id)
            history.append({
                "sceneId": scene_id, "originalSceneState": state,
                "originalResultSHA256": expected_hash,
                "nativeSuccessCount": expected_count,
                "originalUnknownPreserved": True
            })
        for save_scene, expected_sha in _BDD_SAVES.items():
            require(save_scene in old_rows,
                    "BDD_PAIRED_HISTORY_MISSING_VERIFIED_SAVE:" + save_scene)
            state, _, result = old_rows[save_scene]
            require(state == "PASS" and
                    result.get("command") == "SaveProject" and
                    (result.get("readback") or {}).get("savedSha256") ==
                    expected_sha,
                    "BDD_PAIRED_HISTORY_SAVE_CHAIN_NOT_VERIFIED:" + save_scene)
        # The only two standalone Column CREATE roots must have a code-owned
        # typed+BREP PASS in an original durable SceneWriter record.
        created_roots = []
        for name, (state, _, result) in old_rows.items():
            proof = result.get("readback") or {}
            if state == "PASS" and result.get("command") == "CreateColumns" and (
                    proof.get("status") ==
                    "NATIVE_COLUMN_CREATE_TYPED_AND_BREP_READBACK_PASS"):
                roots = proof.get("newRootGuids")
                require(isinstance(roots, list) and len(roots) == 2 and
                        proof.get("newRootCount") == 2 and
                        proof.get("newSegmentCount") == 2 and
                        all(isinstance(root, str) for root in roots),
                        "BDD_PAIRED_HISTORY_TWO_ORIGINAL_COLUMNS_NOT_PROVED")
                created_roots.extend(root.lower() for root in roots)
        require(len(created_roots) == len(set(created_roots)) == 2,
                "BDD_PAIRED_HISTORY_ORIGINAL_TWO_COLUMN_CREATES_ABSENT")

    live = sorted(g.lower() for g in guid_inventory(read_api))
    require(len(live) == len(set(live)) == 298 and
            prior.issubset(set(live)) and
            len(set(live) - prior) == 8,
            "BDD_PAIRED_HISTORY_298_LIVE_GUID_SET_NOT_EXPLAINED")
    full = capture_model(read_api, live)
    nodes = {e["guid"].lower(): e for e in full["elements"]}
    require(len(nodes) == len(full["elements"]) == len(live) and
            set(nodes) == set(live) and
            all(geom_signature(nodes[g]) == prior_brep[g] for g in prior),
            "BDD_PAIRED_HISTORY_ORIGINAL_290_BREP_CHANGED")
    added = set(live) - prior
    kinds = Counter(nodes[g]["type"] for g in added)
    require(kinds == {
        "Column": 3, "ColumnSegment": 3,
        "Beam": 1, "BeamSegment": 1
    }, "BDD_PAIRED_HISTORY_ADDED_NATIVE_FAMILIES_UNEXPLAINED")
    parents = {g for g in added if nodes[g]["type"] in {"Column","Beam"}}
    children = added - parents
    require(set(created_roots) <= parents and
            all(nodes[g]["type"] == "Column" for g in created_roots) and
            len(parents - set(created_roots)) == 2 and
            {nodes[g]["type"] for g in parents - set(created_roots)} ==
            {"Column","Beam"},
            "BDD_PAIRED_HISTORY_VERIFIED_CREATES_AND_COPIES_NOT_EXACT")
    for parent in parents:
        child_kind = nodes[parent]["type"] + "Segment"
        owned = [g for g in children if
                 (nodes[g].get("relationships",{}).get("hostGuid") or "").lower()
                 == parent]
        require(len(owned) == 1 and nodes[owned[0]]["type"] == child_kind,
                "BDD_PAIRED_HISTORY_UNEXPLAINED_NATIVE_CHILD_OWNERSHIP")
        vertices = [v for b in nodes[owned[0]].get("bodies",[])
                    for v in b.get("vertices", [])]
        require(vertices and all(100 < v[0] < 220 and 100 < v[1] < 200
                                 for v in vertices),
                "BDD_PAIRED_HISTORY_COPY_TARGET_NOT_IN_REVIEWED_EAST_ISOLATION")
    require(getattr(read_api, "write_attempts", None) == 0,
            "BDD_PAIRED_HISTORY_NATIVE_WRITE_ATTEMPT")
    brep_hash = digest({
        g: geom_signature(nodes[g]) for g in sorted(live)})
    return {
        "schema": "APA_AC29_BDD_PAIRED_HISTORY_RECONCILIATION_V1",
        "status": "BDD_PAIRED_HISTORY_CURRENT_MODEL_RECONCILED_PASS",
        "originalUnknownRowsPreserved": True,
        "savedProjectSHA256": current_project_sha,
        "guidSetHash": digest(live),
        "brepSignaturesHash": brep_hash,
        "source290BrepRetained": True,
        "addedGuidCount": 8,
        "verifiedColumnCreateRoots": sorted(created_roots),
        "newRootTypes": dict(kinds),
        "historicalProofs": history,
        "bulkRawSHA256": _BDD_BULK_RAW_SHA,
        "recordedBulkMutationIndex": mutation_index,
        "verifiedSaveScene": "APA_AC29_MULTI_RECONCILED_SAVE_20261017",
        "modelWrites": 0,
        "nativeSaveCalls": 0,
        "automaticRetry": False
    }
