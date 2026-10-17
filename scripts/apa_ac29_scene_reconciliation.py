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
                             current_project_sha):
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
    with sqlite3.connect(f"file:{journal_path.as_posix()}?mode=ro", uri=True) as db:
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
    live = inventory_guid_set(read_api("GetAllElements", {}))
    require(live == prior,
            "RECONCILE_LIVE_GUID_SET_NOT_EQUAL_TO_PREWRITE")
    live_signatures = signatures(read_api("GetModelDumpV1", {}),
                                 normalized, geom_signature)
    require(live_signatures == prior_signatures,
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
        "guidSetHash": digest(sorted(prior)),
        "brepSignaturesHash": digest(prior_signatures),
        "savedProjectSHA256": current_project_sha,
        "modelWrites": 0,
        "replayPreviousScene": False,
    }
    require(read_api.write_attempts == 0,
            "RECONCILE_EVIDENCE_API_REPORTED_NATIVE_WRITE")
    return evidence
