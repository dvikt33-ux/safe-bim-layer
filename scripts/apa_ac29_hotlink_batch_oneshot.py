"""APA29: batch placement of 1..32 existing Hotlink-node instances in ONE write.

Only fresh disposable saved PLN copies. Five explicit CLI phases:
  --stage        copy unchanged accepted PLN and source hashes (NO Archicad)
  --plan         read-only native BREP; stage deterministic collision-free plan
  --execute      one CreateHotlinkInstances + one guarded SaveProject
  --check-closed record actual AC29 "no open project" after GUI close
  --verify-reopen independently compare saved BREP, roots, owners and hashes

Uses *original* APA native router, graph, SQLite SceneWriter and source-owned
verifier protocol. No retries, no automatic OpenProject, no new native command.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

import archicad_project_accelerator as APA
import archicad_scene_run as RUN
import archicad_bim_documentation as DOC
import archicad_connected_components as C
from apa_ac29_dynamic_write_scopes import build_existing_workflow_scopes
from apa_ac29_hotlink_native_verifiers import (
    need, digest, flatten_hotlinks, canonical_location,
    verify_instance_root
)
from apa_ac29_reusable_native_copy import GuardedSaveTransport
import apa_ac29_hotlink_batch_geometry as GEO
from apa_ac29_hotlink_batch_verifier import (
    batch_parameters, parse_batch_response, installed_batch_verifier
)
import apa_ac29_hotlink_oneshot as HOTLINK
from apa_ac29_save_isolation import (
    ScratchWriteLease, preserve_guarded_save, stage_readonly_reopen,
    sha256 as file_sha, verify_snapshot_evidence, copy_exclusive,
)

SCHEMA = "APA_AC29_HOTLINK_BATCH_V1"
AUTH = "USER_APPROVED_AC29_HOTLINK_BATCH_DISPOSABLE_20261018"
SOURCE_REF = "https://github.com/dvikt33-ux/safe-bim-layer/pull/173"
SCHEMA_PATH = HOTLINK.SCHEMA_PATH
CREATE_SCENE = "HotlinkBatchCreate20261018V1"
SAVE_SCENE = "HotlinkBatchSave20261018V1"


def utc():
    return datetime.now(timezone.utc).isoformat()


def save_new(path, record):
    path = Path(path)
    with path.open("x", encoding="utf8") as stream:
        json.dump(record, stream, ensure_ascii=False, sort_keys=True,
                  indent=2, allow_nan=False)
        stream.write("\n")


def read(path):
    return json.loads(Path(path).read_text(encoding="utf8"))


def unique_stage(source, module, scratch, state, node_guid,
                 prototype_guid, count, gap, port):
    source, module, scratch, state = [Path(p).resolve()
                                     for p in (source, module, scratch, state)]
    need(source.is_file() and module.is_file() and
         source.suffix.lower() == scratch.suffix.lower() == ".pln" and
         module.suffix.lower() in {".pln", ".mod"} and
         len({source, module, scratch, state}) == 4 and
         not scratch.exists() and not state.exists() and
         scratch.parent.is_dir() and state.parent.is_dir() and
         not (str(scratch).lower().startswith(str(source.parent / "backups").lower())) and
         type(count) is int and 1 <= count <= GEO.MAX_INSTANCES and
         GEO.finite(gap) and 0.1 <= gap <= 100 and
         type(port) is int and 1 <= port <= 65535,
         "HOTLINK_BATCH_STAGE_REQUIRE_FRESH_TEST_COPY_AND_BOUNDED_COUNT")
    # Runtime will prove selected existing node and root. Stage cannot infer
    # whether arbitrary user data is a safe target: fail for unknown GUIDs.
    import re
    guid_pattern = r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}"
    need(re.fullmatch(guid_pattern, node_guid or "") and
         re.fullmatch(guid_pattern, prototype_guid or "") and
         node_guid.lower() != prototype_guid.lower(),
         "HOTLINK_BATCH_EXPLICIT_EXISTING_NODE_AND_ROOT_REQUIRED")
    original_sha, module_sha = digest(source), digest(module)
    copy_exclusive(source, scratch)
    need(digest(scratch) == original_sha and digest(source) == original_sha and
         digest(module) == module_sha,
         "HOTLINK_BATCH_SOURCE_COPY_HASH_NOT_EXACT")
    state.mkdir(exist_ok=False)
    manifest = {"schema": SCHEMA, "status": "STAGED_NO_MODEL_WRITES",
                "source": str(source), "sourceSHA256": original_sha,
                "module": str(module), "moduleSHA256": module_sha,
                "scratch": str(scratch), "scratchInitialSHA256": original_sha,
                "port": port, "nodeGuid": node_guid.lower(),
                "prototypeGuid": prototype_guid.lower(),
                "count": count, "gapMeters": gap,
                "modelWrites": 0, "automaticReplay": False,
                "needsManuallyOpenedScratch": True}
    save_new(state / "manifest.json", manifest)
    return manifest


def validate_stage(state, *, allow_plan=False):
    manifest = read(Path(state) / "manifest.json")
    need(manifest.get("schema") == SCHEMA and
         manifest.get("status") == "STAGED_NO_MODEL_WRITES" and
         manifest.get("snapshotVerificationOnly") is not True and
         not (Path(state) / "attempted.json").exists() and
         not (Path(state) / "batch-scenewriter.sqlite").exists() and
         all(Path(manifest[k]).is_file() for k in ("source", "module", "scratch")) and
         digest(manifest["source"]) == manifest["sourceSHA256"] and
         digest(manifest["module"]) == manifest["moduleSHA256"] and
         digest(manifest["scratch"]) == manifest["scratchInitialSHA256"] and
         (allow_plan or not (Path(state) / "plan.json").exists()),
         "HOTLINK_BATCH_STAGE_OR_IMMUTABLE_SOURCE_DRIFT")
    return manifest


def prepare_api(manifest, state, *, for_write, saved_sha=None):
    scratch, source = Path(manifest["scratch"]), Path(manifest["source"])
    current_sha = saved_sha or manifest["scratchInitialSHA256"]
    RUN.bind_authorized_saved_copy(
        manifest["port"], str(scratch), scratch.stem, current_sha, AUTH)
    guard = GuardedSaveTransport(
        APA.native_transport, RUN.bind_authorized_saved_copy,
        scratch, source, lambda: digest(scratch), lambda: digest(source),
        scratch.stem, manifest["port"], AUTH)
    folder = Path(state) / ("trace-write" if for_write else "trace-read")
    folder.mkdir(exist_ok=True)
    api = APA.EvidenceAPI(guard, folder, execute=for_write)
    api.allowed |= frozenset({"GetHotlinks"})
    return api, guard


def router_for(api):
    router = APA.native_command_router(SCHEMA_PATH,
                                        include_functional_modules=False)
    router.probe_runtime(api, "GetHotlinks")
    router.probe_runtime(api, "CreateHotlinkInstances")
    router.review_policy("CreateHotlinkInstances", "CREATE", "MODEL",
                         {"source": SOURCE_REF,
                          "sha256": router.contract_hash("CreateHotlinkInstances")})
    router.review_policy("SaveProject", "TRANSACTION", "PROJECT",
                         {"source": SOURCE_REF,
                          "sha256": router.contract_hash("SaveProject")})
    return router


def observed_origin(api, prototype_guid):
    rows = api("GetDetailsOfElements", {
        "elements": [{"elementId": {"guid": prototype_guid}}]
    }).get("detailsOfElements")
    need(isinstance(rows, list) and len(rows) == 1 and
         isinstance(rows[0], dict) and rows[0].get("type") == "Hotlink",
         "HOTLINK_BATCH_EXISTING_ROOT_DETAILS_REQUIRED")
    origin = (rows[0].get("details") or {}).get("origin")
    need(isinstance(origin, dict) and set(origin) == {"x", "y", "z"} and
         all(GEO.finite(x) for x in origin.values()),
         "HOTLINK_BATCH_EXISTING_ROOT_ORIGIN_UNVERIFIED")
    return origin


def probe_native(manifest, api):
    HOTLINK.current_project(api, manifest["scratch"])
    pairs = flatten_hotlinks(api("GetHotlinks", {}))
    need(pairs.count((canonical_location(manifest["module"]),
                      manifest["nodeGuid"])) == 1 and
         digest(manifest["module"]) == manifest["moduleSHA256"],
         "HOTLINK_BATCH_EXISTING_NODE_OR_MODULE_CHANGED")
    guids = sorted(APA.inventory_guids(api))
    native = DOC.capture_full_model(api, guids)
    nodes = {row["guid"].lower(): row for row in native["elements"]}
    need(set(nodes) == set(guids), "HOTLINK_BATCH_COMPLETE_NATIVE_BREP_REQUIRED")
    fingerprint = RUN.digest({g: C.ROOF.geometry_signature(nodes[g])
                              for g in guids})
    root_origin = observed_origin(api, manifest["prototypeGuid"])
    source = GEO.placed_prototype(
        api, native, manifest["nodeGuid"], manifest["prototypeGuid"],
        root_origin)
    plan = GEO.planned_batch(source, manifest["count"], manifest["gapMeters"])
    return guids, fingerprint, plan, native


def plan_readonly(state):
    state = Path(state).resolve()
    manifest = validate_stage(state)
    api, _ = prepare_api(manifest, state, for_write=False)
    router = router_for(api)
    guids, fingerprint, geometry, native = probe_native(manifest, api)
    params = batch_parameters(manifest["nodeGuid"], geometry["origins"],
                              geometry["prototypeSettings"])
    ticket = router.prepare("CreateHotlinkInstances", params)
    need(ticket["effect"] == "CREATE" and len(params["hotlinkInstances"]) ==
         manifest["count"] and api.write_attempts == 0,
         "HOTLINK_BATCH_OFFLINE_PLAN_MUST_NOT_WRITE")
    rec = {"schema": SCHEMA, "status": "READ_ONLY_BREP_PLAN_READY",
           "at": utc(), "savedSourceSHA256": manifest["scratchInitialSHA256"],
           "moduleSHA256": manifest["moduleSHA256"],
           "beforeGuidSetSHA256": RUN.digest(guids),
           "beforeBrepSHA256": fingerprint,
           "baselineGuids": guids, "geometry": geometry,
           "batchParameters": params, "contractSHA256":
           router.contract_hash("CreateHotlinkInstances"),
           "nativeCalls": 0, "automaticReplay": False}
    save_new(state / "plan.json", rec)
    return rec


def execute(state):
    state = Path(state).resolve()
    manifest = validate_stage(state, allow_plan=True)
    planned = read(state / "plan.json")
    need(planned["schema"] == SCHEMA and
         planned["status"] == "READ_ONLY_BREP_PLAN_READY" and
         planned["savedSourceSHA256"] == manifest["scratchInitialSHA256"] and
         planned["moduleSHA256"] == manifest["moduleSHA256"],
         "HOTLINK_BATCH_IMMUTABLE_PLAN_REQUIRED")
    api, save_guard = prepare_api(manifest, state, for_write=True)
    router = router_for(api)
    baseline_ids, baseline_brep, computed, _ = probe_native(manifest, api)
    need(RUN.digest(baseline_ids) == planned["beforeGuidSetSHA256"] and
         baseline_brep == planned["beforeBrepSHA256"] and
         computed == planned["geometry"] and
         router.contract_hash("CreateHotlinkInstances") == planned["contractSHA256"] and
         batch_parameters(manifest["nodeGuid"], computed["origins"],
                          computed["prototypeSettings"]) ==
             planned["batchParameters"],
         "HOTLINK_BATCH_NATIVE_BREP_OR_PLAN_CHANGED_BEFORE_DISPATCH")
    # Cross-process cooperative reservation keyed by the SCRATCH path, not
    # by this job's state folder. It persists for evidence on any UNKNOWN.
    # It cannot prevent unrelated Archicad writes; SHA+snapshot handles those.
    lease = ScratchWriteLease(manifest["scratch"], state,
                             manifest["scratchInitialSHA256"])
    lease.acquire()
    # Durable one-shot intent exists BEFORE any native model write. A timeout
    # or half-success is forensic state; never resend the batch.
    save_new(state / "attempted.json", {
        "status": "BATCH_NATIVE_DISPATCH_RESERVED", "at": utc(),
        "sourceSHA256": manifest["sourceSHA256"],
        "moduleSHA256": manifest["moduleSHA256"],
        "plannedSHA256": digest(state / "plan.json"),
        "nativeModelCallLimit": 1, "automaticRetry": False})
    ledger = state / "batch-scenewriter.sqlite"
    import sqlite3
    with sqlite3.connect(ledger) as db:
        db.execute("CREATE TABLE scenes (scene_id TEXT PRIMARY KEY,"
                   "plan_hash TEXT NOT NULL, state TEXT NOT NULL, result TEXT NOT NULL)")
        db.execute("CREATE TABLE steps (scene_id TEXT NOT NULL,"
                   "step_id TEXT NOT NULL, state TEXT NOT NULL, guid TEXT,"
                   "output TEXT NOT NULL, PRIMARY KEY(scene_id,step_id))")
        db.commit()
    writer = RUN.SceneWriter(api, journal_path=ledger,
                             schema_path=SCHEMA_PATH,
                             allow_3d_view_for_write=True)
    try:
        registry = installed_batch_verifier(
            manifest["module"], manifest["moduleSHA256"],
            manifest["nodeGuid"], manifest["prototypeGuid"],
            computed["prototypeOrigin"], manifest["count"],
            manifest["gapMeters"], computed)
        from apa_ac29_dynamic_native_verifiers import installed_verifiers
        # Scope registry is code-owned and command-specific, no blanket
        # authorization or mutation to the shared APA verifier registry.
        need("VerifiedHotlinkBatchReuseV1" not in installed_verifiers(),
             "HOTLINK_BATCH_REGISTRY_ID_COLLISION")
        preview = APA.prepare_native_task(router, {
            "schemaVersion": "apa-native-task/1",
            "request": "One reused native Hotlink node, one bounded native batch",
            "graph": {"operations": [{
                "id": "HotlinkBatchStep",
                "command": "CreateHotlinkInstances",
                "params": planned["batchParameters"], "after": []}]}})
        spec = {
            "schemaVersion": "apa-ac29-dynamic-mutation-scope/1",
            "projectSha256": manifest["scratchInitialSHA256"],
            "sourcePlanHash": preview["sourcePlanHash"],
            "authorizationRef": AUTH,
            "sourceEvidenceRef": SOURCE_REF,
            "sceneId": CREATE_SCENE, "stepId": "HotlinkBatchStep",
            "command": "CreateHotlinkInstances", "effect": "CREATE",
            "impact": "MODEL",
            "commandContractHash": router.contract_hash("CreateHotlinkInstances"),
            "parametersHash": RUN.digest(planned["batchParameters"]),
            "expectedBeforeGuidSetHash": RUN.digest(baseline_ids),
            "expectedBeforeNativeBrepHash": baseline_brep,
            "affectedGuids": [], "retainedGuids": baseline_ids,
            "verifierId": "VerifiedHotlinkBatchReuseV1"}
        scopes = build_existing_workflow_scopes(
            spec=spec, plan=preview["workflow"], router=router,
            registry=registry, writer=writer, api=api,
            capture_model=DOC.capture_full_model,
            guid_inventory=APA.inventory_guids,
            current_project_sha=lambda: digest(manifest["scratch"]),
            approved_project_sha=manifest["scratchInitialSHA256"],
            local_authorization=AUTH)
        result = APA.run_native_task(router, api, preview, writer, scopes)
        need(result.get("status") == "WORKFLOW_CALLABLE_VERIFIED" and
             api.calls["CreateHotlinkInstances"] == 1,
             "HOTLINK_BATCH_NOT_ONE_VERIFIED_NATIVE_CALL")
        roots = parse_batch_response(
            result["results"]["HotlinkBatchStep"], manifest["count"],
            set(baseline_ids))
        new_ids = sorted(APA.inventory_guids(api))
        native = DOC.capture_full_model(api, new_ids)
        native_map = {row["guid"].lower(): row for row in native["elements"]}
        after_brep = RUN.digest({g:C.ROOF.geometry_signature(native_map[g])
                                 for g in new_ids})
        need(set(native_map) == set(new_ids) and
             len(new_ids) == len(baseline_ids) +
                            manifest["count"]*(computed["sourceOwnedCount"]+1),
             "HOTLINK_BATCH_POST_MODEL_INVENTORY_DRIFT")
        signatures = C.retained_geometry_signatures(native, new_ids)
        need(set(signatures) == set(new_ids),
             "HOTLINK_BATCH_NATIVE_PRE_SAVE_SIGNATURES_MISSING")
        save_guard.enable_after_verified_copy()
        def before_save(live):
            HOTLINK.current_project(live, manifest["scratch"])
            need(digest(manifest["scratch"]) == manifest["scratchInitialSHA256"] and
                 sorted(APA.inventory_guids(live)) == new_ids and
                 digest(manifest["module"]) == manifest["moduleSHA256"],
                 "HOTLINK_BATCH_PRE_SAVE_PERSISTENCE_DRIFT")
            return {"status": "HOTLINK_BATCH_PRE_SAVE_READBACK_PASS"}
        def after_save(reply, _):
            need(reply == {"success": True} and save_guard.new_saved_sha and
                 lease.verify() and
                 digest(manifest["scratch"]) == save_guard.new_saved_sha and
                 digest(manifest["source"]) == manifest["sourceSHA256"] and
                 digest(manifest["module"]) == manifest["moduleSHA256"],
                 "HOTLINK_BATCH_GUARDED_SAVE_NOT_CONFIRMED")
            # Preserve the exact bytes DURING the guarded SaveProject callback,
            # not after the task has returned to a parallel Archicad session.
            snap = preserve_guarded_save(
                manifest["scratch"], state / "guarded-save.snapshot",
                save_guard.new_saved_sha, {
                    manifest["source"]: manifest["sourceSHA256"],
                    manifest["module"]: manifest["moduleSHA256"],
                })
            save_new(state / "guarded-snapshot.json", snap)
            return {"status": "HOTLINK_BATCH_SAVED_AND_PINNED_SNAPSHOT_PASS",
                    "savedSHA256": save_guard.new_saved_sha,
                    "snapshotSHA256": snap["snapshotSHA256"]}
        saved = router.execute(
            writer, SAVE_SCENE, router.prepare("SaveProject", {}),
            [], signatures, manifest["scratchInitialSHA256"],
            AUTH, "PROJECT", after_save, verify_before=before_save)
        need(saved.get("status") == "PASS" and
             api.calls["SaveProject"] == 1 and api.write_attempts == 2 and
             lease.verify() and
             file_sha(state / "guarded-save.snapshot") ==
                 save_guard.new_saved_sha and
             file_sha(manifest["scratch"]) == save_guard.new_saved_sha,
             "HOTLINK_BATCH_TWO_WRITES_AND_PINNED_SAVE_SNAPSHOT_REQUIRED")
        receipt = {"schema": SCHEMA,
                   "status": "BATCH_NATIVE_SAVED_PENDING_REAL_REOPEN",
                   "at": utc(), "nodeGuid": manifest["nodeGuid"],
                   "prototypeGuid": manifest["prototypeGuid"],
                   "instanceGuids": roots, "batchCount": manifest["count"],
                   "expectedOrigins": computed["origins"],
                   "sourceOwnedCount": computed["sourceOwnedCount"],
                   "sourceTypeHistogram": computed["sourceTypeHistogram"],
                   "beforeGuidCount": len(baseline_ids),
                   "afterGuidCount": len(new_ids),
                   "sourceSHA256": manifest["sourceSHA256"],
                   "moduleSHA256": manifest["moduleSHA256"],
                   "savedSHA256": save_guard.new_saved_sha,
                   "guardedSnapshotSHA256": save_guard.new_saved_sha,
                   "guardedSnapshotReceiptSHA256":
                       file_sha(state / "guarded-snapshot.json"),
                   "cooperativeLeaseSHA256": lease.lock_sha,
                   "afterGuidSetSHA256": RUN.digest(new_ids),
                   "afterBrepSHA256": after_brep,
                   "nativeBatchCalls": 1, "saveCalls": 1,
                   "automaticReplay": False, "reopenVerified": False}
        save_new(state / "saved.json", receipt)
        return receipt
    except Exception as exc:
        save_new(state / "failed.json", {
            "schema": SCHEMA,
            "status": "BATCH_UNKNOWN_NO_AUTOMATIC_RETRY_READONLY_RECONCILIATION",
            "at": utc(),
            "error": type(exc).__name__ + ": " + str(exc)[-1400:],
            "modelMutationMayHaveOccurred": True,
            "automaticReplay": False})
        raise


def verify_guarded_snapshot_chain(state, receipt):
    """Verify snapshot bytes and receipt independently of the active PLN."""
    state = Path(state).resolve()
    manifest = read(state / "manifest.json")
    if manifest.get("snapshotVerificationOnly") is True:
        provenance = read(state / "snapshot-provenance.json")
        parent = Path(manifest["parentStatePath"]).resolve()
        hashes = provenance.get("parentHashes", {})
        names = {"manifest.json", "plan.json", "saved.json", "attempted.json",
                 "batch-scenewriter.sqlite", "guarded-snapshot.json"}
        need(provenance.get("status") == "SNAPSHOT_ONLY_READBACK_NO_MODEL_WRITES" and
             Path(provenance["parent"]).resolve() == parent and
             set(hashes) == names and
             provenance.get("newVerificationPLN") == manifest["scratch"] and
             provenance.get("newPort") == manifest["port"] and
             provenance.get("sourceSavedSHA256") == receipt["savedSHA256"] and
             all(file_sha(parent / name) == checksum for name, checksum in hashes.items()) and
             all(file_sha(state / name) == hashes[name] for name in names - {"manifest.json"}),
             "HOTLINK_BATCH_SNAPSHOT_PARENT_OR_COPIED_EVIDENCE_DRIFT")
        original = read(parent / "manifest.json")
        expected = {**original, "scratch": manifest["scratch"], "port": manifest["port"],
                    "snapshotVerificationOnly": True, "parentStatePath": str(parent),
                    "parentManifestSHA256": hashes["manifest.json"],
                    "parentSavedReceiptSHA256": hashes["saved.json"],
                    "parentLedgerSHA256": hashes["batch-scenewriter.sqlite"],
                    "verifiedSourceSnapshotSHA256": receipt["savedSHA256"]}
        need(manifest == expected, "HOTLINK_BATCH_SNAPSHOT_DERIVED_MANIFEST_DRIFT")
        verify_snapshot_evidence(parent, original, receipt)
        return {"status": "GUARDED_SAVE_SNAPSHOT_SHA_RECHECK_PASS",
                "savedSHA256": receipt["savedSHA256"]}
    if "guardedSnapshotSHA256" not in receipt:
        # Backward compatibility with the already accepted PR #173 receipts.
        need(not (state / "guarded-snapshot.json").exists(),
             "HOTLINK_BATCH_PINNED_SNAPSHOT_CANNOT_DOWNGRADE_TO_LEGACY")
        return {"status": "LEGACY_SAVE_WITHOUT_PINNED_SNAPSHOT"}
    proof = read(state / "guarded-snapshot.json")
    need(proof.get("status") == "BYTE_EXACT_GUARDED_SAVE_SNAPSHOT_CAPTURED" and
         proof.get("savedSHA256") == proof.get("snapshotSHA256") ==
             receipt["savedSHA256"] == receipt["guardedSnapshotSHA256"] and
         file_sha(state / "guarded-snapshot.json") ==
             receipt["guardedSnapshotReceiptSHA256"] and
         file_sha(Path(proof["snapshot"])) == receipt["savedSHA256"],
         "HOTLINK_BATCH_GUARDED_SNAPSHOT_EVIDENCE_OR_BYTES_CHANGED")
    verify_snapshot_evidence(state, manifest, receipt)
    return {"status": "GUARDED_SAVE_SNAPSHOT_SHA_RECHECK_PASS",
            "savedSHA256": receipt["savedSHA256"]}


def confirm_open_snapshot(state):
    """First prove the snapshot was actually opened, BEFORE GUI close."""
    state = Path(state).resolve()
    manifest, receipt = read(state / "manifest.json"), read(state / "saved.json")
    need(manifest.get("snapshotVerificationOnly") is True and
         not (state / "opened-before-close.json").exists() and
         file_sha(manifest["scratch"]) == receipt["savedSHA256"] and
         file_sha(manifest["source"]) == receipt["sourceSHA256"] and
         file_sha(manifest["module"]) == receipt["moduleSHA256"],
         "HOTLINK_SNAPSHOT_FIRST_OPEN_IMMUTABLE_BYTES_REQUIRED")
    verify_guarded_snapshot_chain(state, receipt)
    api, _ = prepare_api(manifest, state, for_write=False,
                         saved_sha=receipt["savedSHA256"])
    guids, fingerprint, _, _ = probe_native(manifest, api)
    need(len(guids) == receipt["afterGuidCount"] and
         RUN.digest(guids) == receipt["afterGuidSetSHA256"] and
         fingerprint == receipt["afterBrepSHA256"] and
         api.write_attempts == 0,
         "HOTLINK_SNAPSHOT_FIRST_GUI_OPEN_NATIVE_BREP_DRIFT")
    record = {"schema": SCHEMA,
              "status": "SNAPSHOT_GUI_OPEN_NATIVE_READBACK_PASS",
              "snapshotSHA256": receipt["savedSHA256"],
              "guidSetSHA256": RUN.digest(guids),
              "nativeWrites": 0, "at": utc()}
    save_new(state / "opened-before-close.json", record)
    return record


def check_closed(state):
    state = Path(state).resolve()
    receipt, manifest = read(state / "saved.json"), read(state / "manifest.json")
    if manifest.get("snapshotVerificationOnly") is True:
        first_open = read(state / "opened-before-close.json")
        need(first_open["status"] == "SNAPSHOT_GUI_OPEN_NATIVE_READBACK_PASS" and
             first_open["snapshotSHA256"] == receipt["savedSHA256"] and
             first_open["guidSetSHA256"] == receipt["afterGuidSetSHA256"],
             "HOTLINK_SNAPSHOT_GUI_OPEN_REQUIRED_BEFORE_REAL_CLOSE")
    need(receipt["status"] == "BATCH_NATIVE_SAVED_PENDING_REAL_REOPEN" and
         not (state / "closed.json").exists() and
         digest(manifest["scratch"]) == receipt["savedSHA256"],
         "HOTLINK_BATCH_PERSISTED_SCRATCH_REQUIRED_BEFORE_GUI_CLOSE")
    verify_guarded_snapshot_chain(state, receipt)
    api, _ = prepare_api(manifest, state, for_write=False,
                         saved_sha=receipt["savedSHA256"])
    try:
        actual = api("GetProjectInfo", {})
    except Exception as exc:
        reason = str(exc)
        need("4001" in reason and "no open project" in reason.lower(),
             "HOTLINK_BATCH_CLOSE_NOT_VERIFIED_BY_NATIVE_API")
    else:
        raise ValueError("HOTLINK_BATCH_PROJECT_STILL_OPEN_NO_REOPEN_PROOF")
    record = {"schema": SCHEMA,
              "status": "NATIVE_NO_OPEN_PROJECT_CONFIRMED",
              "at": utc(), "scratchSHA256": receipt["savedSHA256"],
              "saveBeforeCloseVerified": True}
    save_new(state / "closed.json", record)
    return record


def verify_reopen(state):
    state = Path(state).resolve()
    manifest, receipt = read(state / "manifest.json"), read(state / "saved.json")
    closed = read(state / "closed.json")
    if manifest.get("snapshotVerificationOnly") is True:
        first_open = read(state / "opened-before-close.json")
        provenance = read(state / "snapshot-provenance.json")
        need(first_open["status"] == "SNAPSHOT_GUI_OPEN_NATIVE_READBACK_PASS" and
             first_open["guidSetSHA256"] == receipt["afterGuidSetSHA256"] and
             provenance["status"] == "SNAPSHOT_ONLY_READBACK_NO_MODEL_WRITES" and
             provenance["sourceSavedSHA256"] == receipt["savedSHA256"] and
             all(file_sha(Path(provenance["parent"]) / name) == checksum
                 for name, checksum in provenance["parentHashes"].items()),
             "HOTLINK_SNAPSHOT_REOPEN_PARENT_CHAIN_OR_PREVIOUS_OPEN_DRIFT")
    need(not (state / "reopened.json").exists() and
         closed["status"] == "NATIVE_NO_OPEN_PROJECT_CONFIRMED" and
         closed["scratchSHA256"] == receipt["savedSHA256"] and
         digest(manifest["scratch"]) == receipt["savedSHA256"] and
         digest(manifest["source"]) == manifest["sourceSHA256"] and
         digest(manifest["module"]) == manifest["moduleSHA256"],
         "HOTLINK_BATCH_ACTUAL_CLOSE_AND_SAVED_HASH_REQUIRED")
    verify_guarded_snapshot_chain(state, receipt)
    api, _ = prepare_api(manifest, state, for_write=False,
                         saved_sha=receipt["savedSHA256"])
    HOTLINK.current_project(api, manifest["scratch"])
    guids, fingerprint, _, native = probe_native(manifest, api)
    need(RUN.digest(guids) == receipt["afterGuidSetSHA256"] and
         fingerprint == receipt["afterBrepSHA256"] and
         len(guids) == receipt["afterGuidCount"],
         "HOTLINK_BATCH_REOPENED_COMPLETE_MODEL_CHANGED")
    before = set(read(state / "plan.json")["baselineGuids"])
    actual_new = set(guids) - before
    roots = receipt["instanceGuids"]
    need(len(actual_new) == receipt["batchCount"] *
                            (receipt["sourceOwnedCount"] + 1) and
         set(roots) <= actual_new, "HOTLINK_BATCH_REOPENED_GUID_DELTA_MISMATCH")
    nodes = {row["guid"].lower(): row for row in native["elements"]}
    children = sorted(actual_new - set(roots))
    rows = api("GetDetailsOfElements", {"elements": [
        {"elementId": {"guid": guid}} for guid in children],
        "fields": ["type", "hotlinkId", "floorIndex", "details"]
    }).get("detailsOfElements")
    need(isinstance(rows, list) and len(rows) == len(children),
         "HOTLINK_BATCH_REOPENED_CHILDREN_MISSING")
    owned = {root: [] for root in roots}
    kinds = {root: {} for root in roots}
    for guid, row in zip(children, rows):
        root = (row.get("hotlinkId") or {}).get("guid", "").lower()
        need(root in owned and row.get("floorIndex") == 0,
             "HOTLINK_BATCH_REOPENED_ORPHANED_CHILD")
        owned[root].append(guid)
        kind = row["type"]
        kinds[root][kind] = kinds[root].get(kind, 0) + 1
    plan = read(state / "plan.json")["geometry"]
    for index, root in enumerate(roots):
        native_root = verify_instance_root(
            api, manifest["nodeGuid"], root, receipt["expectedOrigins"][index])
        need(all(native_root["details"].get(k) == v and
                 type(native_root["details"].get(k)) is type(v)
                 for k, v in plan["prototypeSettings"].items()),
             "HOTLINK_BATCH_REOPENED_INSTANCE_FLAGS_CHANGED")
        need(len(owned[root]) == receipt["sourceOwnedCount"] and
             kinds[root] == receipt["sourceTypeHistogram"],
             "HOTLINK_BATCH_REOPENED_OWNER_HISTOGRAM_CHANGED")
        actual_box = GEO.union(list(GEO.world_boxes({
            "elements": [nodes[guid] for guid in owned[root]]
        }).values()))
        need(GEO.box_close(actual_box, plan["expectedBounds"][index]),
             "HOTLINK_BATCH_REOPENED_WORLD_BREP_PLACEMENT_CHANGED")
    proof = dict(receipt,
                 status="LIVE_NATIVE_HOTLINK_BATCH_SAVED_REOPENED_PASS",
                 verifiedAt=utc(), verifiedOwners=len(children),
                 reopenVerified=True, originalFileSHA256Unchanged=True)
    save_new(state / "reopened.json", proof)
    return proof


def main():
    p = argparse.ArgumentParser(description=__doc__)
    mode = p.add_mutually_exclusive_group(required=True)
    for command in ("stage", "plan", "execute", "check-closed",
                    "verify-reopen", "stage-snapshot-reopen", "confirm-open-snapshot"):
        mode.add_argument("--" + command, action="store_true")
    p.add_argument("--source-pln")
    p.add_argument("--module-pln")
    p.add_argument("--scratch-pln")
    p.add_argument("--state-dir", required=True)
    p.add_argument("--node-guid")
    p.add_argument("--prototype-guid")
    p.add_argument("--count", type=int)
    p.add_argument("--gap", type=float)
    p.add_argument("--port", type=int, default=19726)
    p.add_argument("--snapshot-pln")
    p.add_argument("--snapshot-state")
    p.add_argument("--reopen-port", type=int)
    args = p.parse_args()
    if args.stage:
        need(all((args.source_pln, args.module_pln, args.scratch_pln,
                  args.node_guid, args.prototype_guid)) and
             args.count is not None and args.gap is not None and
             not any((args.snapshot_pln, args.snapshot_state, args.reopen_port)),
             "HOTLINK_BATCH_STAGE_ALL_EXPLICIT_INPUTS_REQUIRED")
        out = unique_stage(args.source_pln, args.module_pln, args.scratch_pln,
                           args.state_dir, args.node_guid, args.prototype_guid,
                           args.count, args.gap, args.port)
    elif args.stage_snapshot_reopen:
        need(all((args.snapshot_pln, args.snapshot_state)) and
             args.reopen_port is not None and
             not any((args.source_pln, args.module_pln, args.scratch_pln,
                      args.node_guid, args.prototype_guid)) and
             args.count is None and args.gap is None,
             "HOTLINK_BATCH_SNAPSHOT_RECOVERY_EXPLICIT_CLEAN_TARGET_REQUIRED")
        out = stage_readonly_reopen(
            args.state_dir, args.snapshot_pln, args.snapshot_state,
            args.reopen_port)
    else:
        need(not any((args.source_pln, args.module_pln, args.scratch_pln,
                      args.node_guid, args.prototype_guid, args.snapshot_pln,
                      args.snapshot_state, args.reopen_port)) and
             args.count is None and args.gap is None,
             "HOTLINK_BATCH_REUSE_ONLY_STAGED_MANIFEST")
        if args.plan:
            out = plan_readonly(args.state_dir)
        elif args.execute:
            out = execute(args.state_dir)
        elif args.check_closed:
            out = check_closed(args.state_dir)
        elif args.confirm_open_snapshot:
            out = confirm_open_snapshot(args.state_dir)
        else:
            out = verify_reopen(args.state_dir)
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
