"""Existing native group -> mass selector -> SceneWriter -> saved-copy reopen.

Only a new disposable PLN, pinned accepted baseline and already LIVE-accepted
SAFE-01. No mailbox, new router, project switching, retries or APX changes.
GUI open/close is external; CLI phases never call OpenProject or CloseProject.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sqlite3

import archicad_project_accelerator as A
import archicad_scene_run as R
import archicad_bim_documentation as D
import archicad_connected_components as C
import apa_ac29_hotlink_batch_oneshot as H
import apa_ac29_hotlink_oneshot as IDENTITY
import apa_ac29_native_group_clone_verifier as V
from apa_ac29_dynamic_write_scopes import build_existing_workflow_scopes
from apa_ac29_dynamic_native_verifiers import installed_verifiers
from apa_ac29_reusable_native_copy import GuardedSaveTransport
from apa_ac29_save_isolation import (ScratchWriteLease, preserve_guarded_save,
                                    copy_exclusive, sha256, write_new_json)
from apa_ac29_mass_request import placement_offsets, SCHEMA as MASS_SCHEMA

SCHEMA = "APA_AC29_NATIVE_GROUP_BATCH_V1"
AUTH = "USER_APPROVED_AC29_GROUP_BATCH_DISPOSABLE_20261019"
SOURCE_REF = "https://github.com/dvikt33-ux/safe-bim-layer/pull/172"
CREATE_SCENE = "NativeGroupBatch20261019V1"
SAVE_SCENE = "NativeGroupSave20261019V1"
need = V.require
read = H.read
SCHEMA_PATH = IDENTITY.SCHEMA_PATH
PRIOR174_SCRATCH = Path(r"C:\LocalAI\APA_Group_Acceptance\group-ac29-grid-8x4-20261018-01.pln")


def fingerprint(model):
    nodes = {r["guid"].lower(): r for r in model["elements"]}
    need(len(nodes) == len(model["elements"]), "GROUP_BATCH_DUPLICATE_NATIVE_GUID")
    return R.digest({g: C.ROOF.geometry_signature(nodes[g]) for g in sorted(nodes)})


def safe01_gate(path):
    state = Path(path).resolve()
    receipt, manifest = read(state / "reopened.json"), read(state / "manifest.json")
    need(receipt.get("status") == "LIVE_NATIVE_HOTLINK_BATCH_SAVED_REOPENED_PASS"
         and receipt.get("reopenVerified") is True and receipt.get("saveCalls") == 1
         and receipt.get("nativeBatchCalls") == 1 and receipt.get("automaticReplay") is False
         and sha256(manifest["scratch"]) == receipt["savedSHA256"]
         and read(state / "closed.json")["status"] == "NATIVE_NO_OPEN_PROJECT_CONFIRMED",
         "GROUP_BATCH_ACCEPTED_SAFE01_LIVE_REQUIRED")
    H.verify_guarded_snapshot_chain(state, read(state / "saved.json"))
    return sha256(state / "reopened.json")


def stage(source, scratch, state, baseline_trace, safe01, group, placements, port, *, prior_stage=None):
    source, scratch, state, baseline_trace, safe01 = [Path(p).resolve()
        for p in (source, scratch, state, baseline_trace, safe01)]
    shifts = placement_offsets(placements)
    need(source.is_file() and source.suffix.lower() == scratch.suffix.lower() == ".pln"
         and source != scratch and scratch.parent.is_dir() and state.parent.is_dir()
         and not state.exists() and type(port) is int
         and ((prior_stage is None and not scratch.exists() and 19727 <= port <= 19735)
              or (prior_stage is not None and port == 19726 and scratch == PRIOR174_SCRATCH))
         and V.GROUP_GUID.fullmatch(group or "")
         and 1 <= len(shifts) <= 32 and all(r["dz"] == 0 for r in shifts),
         "GROUP_BATCH_NEW_ISOLATED_PLN_AND_VALID_GROUP_REQUIRED")
    safe_hash = safe01_gate(safe01)
    rows = [json.loads(line) for line in baseline_trace.read_text(encoding="utf8").splitlines()]
    dumps = [r["response"] for r in rows if r.get("command") == "GetModelDumpV1"
             and isinstance(r.get("response"), dict) and "error" not in r["response"]]
    need(bool(dumps), "GROUP_BATCH_ACCEPTED_NATIVE_BASELINE_REQUIRED")
    baseline = C.G.normalize_dump(dumps[-1])
    ids = sorted(r["guid"].lower() for r in baseline["elements"])
    need(len(ids) == 44 and len(set(ids)) == 44,
         "GROUP_BATCH_ACCEPTED_44_GUID_BASELINE_REQUIRED")
    original_sha = sha256(source)
    adoption = {}
    if prior_stage is None:
        copy_exclusive(source, scratch)
    else:
        prior_path = Path(prior_stage).resolve()
        prior = read(prior_path)
        need(prior.get("schema") == "APA_AC29_GROUP_GRID_STAGE_V1"
             and prior.get("status") == "STAGED_SAVED_COPY_ONLY_NO_ARCHICAD_CALLS"
             and Path(prior["scratchProject"]).resolve() == scratch
             and Path(prior["sourceProject"]).resolve() == source
             and prior.get("sourceSavedSha256") == original_sha
             and prior.get("sourceGroupId", "").lower() == group.lower()
             and prior.get("shifts") == shifts and prior.get("expectedOriginalGuids") == 44
             and prior.get("expectedPostGuids") == 172
             and not any((prior_path.parent / name).exists() for name in
                ("attempted.json", "before-native-dispatch.json", "result.json", "original-scenewriter.sqlite")),
             "GROUP_BATCH_PRIOR174_MUST_BE_EXACT_UNATTEMPTED_ISOLATED_STAGE")
        adoption = dict(adoptedPrior174Stage=str(prior_path), priorStageSHA256=sha256(prior_path),
                        existingSavedTestCopyAdoptedWithoutFileWrite=True)
    need(sha256(scratch) == sha256(source) == original_sha, "GROUP_BATCH_COPY_SHA_DRIFT")
    state.mkdir(exist_ok=False)
    write_new_json(state / "baseline-native.json", baseline)
    manifest = dict(schema=SCHEMA, source=str(source), sourceSHA256=original_sha,
        scratch=str(scratch), scratchInitialSHA256=original_sha, port=port,
        sourceGroup=group.lower(), placements=placements, groupCount=len(shifts),
        baselineSHA256=sha256(state / "baseline-native.json"),
        baselineGuidSetSHA256=R.digest(ids), baselineBrepSHA256=fingerprint(baseline),
        sourceBaselineTrace=str(baseline_trace), sourceBaselineTraceSHA256=sha256(baseline_trace),
        safe01State=str(safe01), safe01ReceiptSHA256=safe_hash,
        status="STAGED_NO_MODEL_WRITES", automaticReplay=False)
    manifest.update(adoption)
    write_new_json(state / "manifest.json", manifest)
    return manifest


def manifest_for(state, *, initial=False):
    state = Path(state).resolve()
    m = read(state / "manifest.json")
    need(m["schema"] == SCHEMA and m["status"] == "STAGED_NO_MODEL_WRITES"
         and sha256(m["source"]) == m["sourceSHA256"]
         and sha256(state / "baseline-native.json") == m["baselineSHA256"]
         and sha256(m["sourceBaselineTrace"]) == m["sourceBaselineTraceSHA256"]
         and safe01_gate(m["safe01State"]) == m["safe01ReceiptSHA256"],
         "GROUP_BATCH_IMMUTABLE_SOURCE_OR_SAFE01_PROOF_DRIFT")
    if "adoptedPrior174Stage" in m:
        need(sha256(m["adoptedPrior174Stage"]) == m["priorStageSHA256"],
             "GROUP_BATCH_ORIGINAL_PRIOR174_RECEIPT_CHANGED")
    if initial:
        need(sha256(m["scratch"]) == m["scratchInitialSHA256"]
             and not any((state / name).exists() for name in
                ("attempted.json", "batch-scenewriter.sqlite", "saved.json", "failed.json")),
             "GROUP_BATCH_PREVIOUS_ATTEMPT_NO_REPLAY")
    return m


def prepare_api(m, state, *, execute, saved_sha=None):
    R.bind_authorized_saved_copy(m["port"], m["scratch"], Path(m["scratch"]).stem,
                                 saved_sha or m["scratchInitialSHA256"], AUTH)
    def bounded(command, params):
        if command == V.CMD:
            return R.tapir(R.PORT, "CloneNativeGroupV1", params, timeout=120)
        if command in {"GetModelDumpV1", "GetAllElements", "GetDetailsOfElements",
                       "GetSubelementsOfHierarchicalElements"}:
            return R.tapir(R.PORT, command, params, timeout=120)
        return A.native_transport(command, params)
    guard = GuardedSaveTransport(bounded, R.bind_authorized_saved_copy,
        m["scratch"], m["source"], lambda: sha256(m["scratch"]), lambda: sha256(m["source"]),
        Path(m["scratch"]).stem, m["port"], AUTH)
    folder = Path(state) / ("trace-write" if execute else "trace-read")
    folder.mkdir(exist_ok=True)
    return A.EvidenceAPI(guard, folder, execute=execute), guard


def capture(m, api):
    IDENTITY.current_project(api, m["scratch"])
    ids = sorted(A.inventory_guids(api))
    native = D.capture_full_model(api, ids)
    need({r["guid"].lower() for r in native["elements"]} == set(ids),
         "GROUP_BATCH_FULL_NATIVE_BREP_REQUIRED")
    return ids, native


def router_for(api):
    router = A.native_command_router(SCHEMA_PATH, include_functional_modules=True)
    for command in ("AddOn.TapirCommand.GetNativeGroupMembersV1", V.CMD):
        router.probe_runtime(api, command)
    runtime = api("GetAPARuntimeInfoV1", {})
    need(runtime.get("contract") == "APA_NATIVE_RUNTIME_IDENTITY_V1"
         and runtime.get("sdkMajor") == 29 and runtime.get("nativeModelWrites") == 0
         and re.fullmatch(r"[a-f0-9]{64}", runtime.get("buildIdentity", ""))
         and re.fullmatch(r"[a-f0-9]{40}", runtime.get("sourceRevision", "")),
         "GROUP_BATCH_LOADED_NATIVE_BUILD_IDENTITY_REQUIRED")
    return router, runtime


def build_plan(state):
    state = Path(state).resolve()
    m = manifest_for(state, initial=True)
    api, _ = prepare_api(m, state, execute=False)
    # Availability belongs to this exact process. A matching Tapir version
    # from another AC29 instance cannot qualify these SDK extensions.
    router, runtime = router_for(api)
    ids, native = capture(m, api)
    need(R.digest(ids) == m["baselineGuidSetSHA256"] and
         fingerprint(native) == m["baselineBrepSHA256"], "GROUP_BATCH_ACCEPTED_BASELINE_DRIFT")
    nodes = {r["guid"].lower(): r for r in native["elements"]}
    members = V.group_member_ids(api, m["sourceGroup"])
    facts = V.column_facts(api, nodes, members)
    existing = [dict(guid=g, type="Column", storyIndex=0, anchor=facts[g]["anchor"],
        familySignature=R.digest(dict(typed=facts[g]["typed"], native=facts[g]["solid"])),
        nativeReadbackVerified=True) for g in sorted(members)]
    task = dict(schemaVersion=MASS_SCHEMA,
        request="Тиражировать проверенную нативную группу по заданной сетке",
        sourceRef=SOURCE_REF, existing=existing, placements=m["placements"],
        assembly=dict(sourceRef=SOURCE_REF, memberGuids=sorted(members), sameStory=True,
            dependenciesVerified=True, existingGroupGuid=m["sourceGroup"], groupReadbackVerified=True))
    writer = R.SceneWriter(api, journal_path=state / "batch-scenewriter.sqlite",
                           schema_path=SCHEMA_PATH, allow_3d_view_for_write=True)
    selected = A.prepare_current_runtime_group_native_task(router, writer, task)["preview"]
    graph = selected["selectedNativeTaskPreview"]["workflow"]
    operations = graph["graph"]["operations"]
    need(len(operations) == 1 and operations[0]["command"] == V.CMD
         and selected["groupedTargetCount"] == 2 * m["groupCount"]
         and selected["individuallyRoutedTargetCount"] == 0 and api.write_attempts == 0,
         "GROUP_BATCH_ONE_EXISTING_NATIVE_GROUP_ROUTE_REQUIRED")
    proof = V.verify_before(api=api, command=V.CMD, parameters=operations[0]["params"],
                            affected=[], native_before=native)
    return dict(schema=SCHEMA, status="READONLY_FULL_BREP_GROUP_PLAN_PASS", task=task,
        preview=selected, params=operations[0]["params"], sourceProof=proof,
        runtimeIdentity=runtime,
        baselineGuids=ids, contractSHA256=router.contract_hash(V.CMD), nativeWrites=0)


def plan(state):
    need(not (Path(state) / "plan.json").exists(), "GROUP_BATCH_PLAN_ALREADY_EXISTS")
    result = build_plan(state)
    write_new_json(Path(state) / "plan.json", result)
    return result


def verify_group_model(m, api, plan, response, baseline):
    ids, native = capture(m, api)
    old = set(plan["baselineGuids"])
    nodes = {r["guid"].lower(): r for r in native["elements"]}
    need(old <= set(ids) and R.digest({g:C.ROOF.geometry_signature(nodes[g])
         for g in sorted(old)}) == m["baselineBrepSHA256"],
         "GROUP_BATCH_ALL_ORIGINAL_NATIVE_BREP_MUST_REMAIN_UNCHANGED")
    proof = V.verify_after(api=api, command=V.CMD, parameters=plan["params"],
        native_response=response, before_guids=old, after_guids=set(ids), affected=[],
        native_before=baseline, native_after=native, source_proof=plan["sourceProof"])
    return ids, native, proof


def execute(state):
    state = Path(state).resolve()
    m = manifest_for(state, initial=True)
    planned = read(state / "plan.json")
    # The pinned plan has crossed JSON: tuples in native geometry become arrays.
    # Compare the complete canonical content, retaining every field and value.
    need(R.canonical(build_plan(state)) == R.canonical(planned),
         "GROUP_BATCH_CURRENT_PLAN_DRIFT")
    lease = ScratchWriteLease(m["scratch"], state, m["scratchInitialSHA256"])
    lease.acquire()
    write_new_json(state / "attempted.json", dict(schema=SCHEMA, status="ONE_SHOT_RESERVED",
        planSHA256=sha256(state / "plan.json"), automaticReplay=False))
    try:
        api, guard = prepare_api(m, state, execute=True)
        router, runtime = router_for(api)
        need(runtime == planned["runtimeIdentity"], "GROUP_BATCH_LOADED_NATIVE_BUILD_DRIFT")
        preview = A.prepare_auto_optimized_native_task(router, planned["task"])
        graph = preview["selectedNativeTaskPreview"]["workflow"]
        op = graph["graph"]["operations"][0]
        need(router.contract_hash(V.CMD) == planned["contractSHA256"] and
             op["params"] == planned["params"] and lease.verify(), "GROUP_BATCH_CONTRACT_DRIFT")
        baseline = read(state / "baseline-native.json")
        with sqlite3.connect(state / "batch-scenewriter.sqlite") as db:
            db.execute("CREATE TABLE scenes(scene_id TEXT PRIMARY KEY,plan_hash TEXT NOT NULL,state TEXT NOT NULL,result TEXT NOT NULL)")
            db.execute("CREATE TABLE steps(scene_id TEXT NOT NULL,step_id TEXT NOT NULL,state TEXT NOT NULL,guid TEXT,output TEXT NOT NULL,PRIMARY KEY(scene_id,step_id))")
        writer = R.SceneWriter(api, journal_path=state / "batch-scenewriter.sqlite",
                               schema_path=SCHEMA_PATH, allow_3d_view_for_write=True)
        spec = dict(schemaVersion="apa-ac29-dynamic-mutation-scope/1",
            projectSha256=m["scratchInitialSHA256"], sourcePlanHash=graph["sourcePlanHash"],
            authorizationRef=AUTH, sourceEvidenceRef=SOURCE_REF, sceneId=CREATE_SCENE,
            stepId=op["id"], command=V.CMD, effect="CREATE", impact="MODEL",
            commandContractHash=planned["contractSHA256"], parametersHash=R.digest(op["params"]),
            expectedBeforeGuidSetHash=m["baselineGuidSetSHA256"],
            expectedBeforeNativeBrepHash=m["baselineBrepSHA256"], affectedGuids=[],
            retainedGuids=planned["baselineGuids"], verifierId="VerifiedNativeGroupClone")
        scopes = build_existing_workflow_scopes(spec=spec, plan=graph, router=router,
            registry=installed_verifiers(), writer=writer, api=api, capture_model=D.capture_full_model,
            guid_inventory=A.inventory_guids, current_project_sha=lambda:sha256(m["scratch"]),
            approved_project_sha=m["scratchInitialSHA256"], local_authorization=AUTH)
        result = A.run_auto_optimized_native_task(router, api, preview, writer, scopes)
        need(result["status"] == "WORKFLOW_CALLABLE_VERIFIED" and api.calls[V.CMD] == 1,
             "GROUP_BATCH_ONE_VERIFIED_SCENEWRITER_CLONE_REQUIRED")
        response = result["results"][op["id"]]
        return save_verified_batch(state, m, planned, api, guard, router, lease, response)
    except Exception as exc:
        write_new_json(state / "failed.json", dict(schema=SCHEMA,
            status="UNKNOWN_NO_REPLAY_READONLY_RECONCILIATION_REQUIRED", error=str(exc),
            nativeMutationMayHaveOccurred=True, automaticReplay=False))
        raise


def save_verified_batch(state, m, planned, api, guard, router, lease, response):
    """Save only after a fresh complete readback; never clones or replays."""
    baseline = read(state / "baseline-native.json")
    writes_before = api.write_attempts
    writer = R.SceneWriter(api, journal_path=state / "batch-scenewriter.sqlite",
                           schema_path=SCHEMA_PATH, allow_3d_view_for_write=True)
    ids, native, proof = verify_group_model(m, api, planned, response, baseline)
    after_hash = fingerprint(native)
    signatures = C.retained_geometry_signatures(native, ids)
    router.review_policy("SaveProject", "TRANSACTION", "PROJECT",
        dict(source=SOURCE_REF, sha256=router.contract_hash("SaveProject")))
    guard.enable_after_verified_copy()
    def before_save(live):
        fresh_ids, fresh_model, _ = verify_group_model(m, live, planned, response, baseline)
        need(lease.verify() and fresh_ids == ids and fingerprint(fresh_model) == after_hash
             and sha256(m["scratch"]) == m["scratchInitialSHA256"], "GROUP_BATCH_PRE_SAVE_DRIFT")
        return dict(status="GROUP_BATCH_PRE_SAVE_READBACK_PASS")
    def after_save(reply, _):
        need(reply == {"success":True} and guard.new_saved_sha and lease.verify(),
             "GROUP_BATCH_SAVE_NOT_CONFIRMED")
        snap = preserve_guarded_save(m["scratch"], state / "guarded-save.snapshot",
            guard.new_saved_sha, {m["source"]:m["sourceSHA256"]})
        write_new_json(state / "guarded-snapshot.json", snap)
        return dict(status="GROUP_BATCH_SAVED_SNAPSHOT_PASS", savedSHA256=guard.new_saved_sha)
    saved = router.execute(writer, SAVE_SCENE, router.prepare("SaveProject", {}), [],
        signatures, m["scratchInitialSHA256"], AUTH, "PROJECT", after_save, verify_before=before_save)
    need(saved["status"] == "PASS" and api.calls["SaveProject"] == 1
         and api.write_attempts == writes_before + 1 and sha256(m["scratch"]) == guard.new_saved_sha,
         "GROUP_BATCH_EXACT_ONE_CLONE_ONE_SAVE_REQUIRED")
    receipt = dict(schema=SCHEMA, status="GROUP_BATCH_SAVED_PENDING_REAL_REOPEN",
        sourceSHA256=m["sourceSHA256"], savedSHA256=guard.new_saved_sha,
        snapshotReceiptSHA256=sha256(state / "guarded-snapshot.json"),
        cooperativeLeaseSHA256=lease.lock_sha, nativeResponse=response, nativeReadback=proof,
        baselineGuidCount=len(planned["baselineGuids"]), finalGuidCount=len(ids),
        finalGuidSetSHA256=R.digest(ids), finalBrepSHA256=after_hash, groupCount=m["groupCount"],
        nativeCloneCalls=1, saveCalls=1, automaticReplay=False, reopenVerified=False)
    write_new_json(state / "saved.json", receipt)
    return receipt


def reconcile_completed_clone(state):
    """Read-only reconciliation of the specific post-JSON comparison stop.

    Requires an already PASS native SceneWriter scene, never an unknown clone.
    Leaves every original attempted/failed record and the lease unchanged.
    """
    state = Path(state).resolve()
    m = manifest_for(state)
    failure = read(state / "failed.json")
    need(failure.get("error") == "GROUP_WRITER_TRANSLATED_BREP_OR_ATTRIBUTES_MISMATCH"
         and not any((state / n).exists() for n in
                     ("saved.json", "reconciled-save-attempted.json"))
         and sha256(m["scratch"]) == m["scratchInitialSHA256"],
         "GROUP_BATCH_ONLY_COMPLETED_UNSAVED_CLONE_CAN_BE_RECONCILED")
    planned = read(state / "plan.json")
    need(read(state / "attempted.json")["planSHA256"] == sha256(state / "plan.json"),
         "GROUP_BATCH_ORIGINAL_ATTEMPT_PLAN_DRIFT")
    trace_path = state / "trace-write" / "raw.jsonl"
    rows = [json.loads(r) for r in trace_path.read_text(encoding="utf8").splitlines()]
    clones = [r for r in rows if r["command"] == V.CMD]
    need(len(clones) == 1 and not any(r["command"] == "SaveProject" for r in rows)
         and clones[0]["parameters"] == planned["params"],
         "GROUP_BATCH_RECONCILIATION_EXACTLY_ONE_CLONE_NO_SAVE_REQUIRED")
    with sqlite3.connect(f"file:{(state / 'batch-scenewriter.sqlite').as_posix()}?mode=ro", uri=True) as db:
        scenes = db.execute("SELECT scene_id,state,result FROM scenes").fetchall()
        steps = db.execute("SELECT scene_id,state,output FROM steps").fetchall()
    need(len(scenes) == len(steps) == 1 and scenes[0][:2] == steps[0][:2] == (CREATE_SCENE,"PASS"),
         "GROUP_BATCH_RECONCILIATION_NATIVE_SCENE_MUST_ALREADY_BE_PASS")
    result, step = json.loads(scenes[0][2]), json.loads(steps[0][2])
    response = clones[0]["response"]
    need(result == step and result.get("status") == "PASS"
         and result.get("nativeResponse") == response
         and result.get("intent", {}).get("parameters") == planned["params"],
         "GROUP_BATCH_RECONCILIATION_TRACE_SQLITE_DISAGREE")
    lease = ScratchWriteLease(m["scratch"],state,m["scratchInitialSHA256"])
    record = read(lease.lock)
    need(record.get("state") == str(state) and record.get("scratch") == m["scratch"]
         and record.get("expectedInitialSHA256") == m["scratchInitialSHA256"],
         "GROUP_BATCH_RECONCILIATION_ORIGINAL_LEASE_REQUIRED")
    api, _ = prepare_api(m,state,execute=False)
    _, runtime = router_for(api)
    need(runtime == planned["runtimeIdentity"], "GROUP_BATCH_RECONCILIATION_RUNTIME_DRIFT")
    ids, native, proof = verify_group_model(m,api,planned,response,read(state / "baseline-native.json"))
    need(api.write_attempts == 0, "GROUP_BATCH_RECONCILIATION_READ_ONLY_REQUIRED")
    evidence = dict(status="COMPLETED_CLONE_FULL_NATIVE_READONLY_RECONCILED",
        sourceSHA256=m["sourceSHA256"], planSHA256=sha256(state / "plan.json"),
        originalFailureSHA256=sha256(state / "failed.json"),
        originalAttemptSHA256=sha256(state / "attempted.json"),
        traceSHA256=sha256(trace_path), sqliteSHA256=sha256(state / "batch-scenewriter.sqlite"),
        originalLeaseSHA256=sha256(lease.lock), finalGuidSetSHA256=R.digest(ids),
        finalBrepSHA256=fingerprint(native), nativeReadback=proof,
        nativeResponse=response, nativeWrites=0, automaticReplay=False)
    return evidence


def save_reconciled_clone(state):
    """Explicit continuation after independent reconciliation; SAVE only once."""
    state = Path(state).resolve()
    evidence = read(state / "completed-clone-reconciliation.json")
    need(reconcile_completed_clone(state) == evidence,
         "GROUP_BATCH_RECONCILIATION_PROOF_DRIFT")
    m = manifest_for(state)
    lease = ScratchWriteLease(m["scratch"],state,m["scratchInitialSHA256"])
    lease.lock_sha = evidence["originalLeaseSHA256"]
    lease.verify()
    write_new_json(state / "reconciled-save-attempted.json",dict(
        status="SAVE_ONLY_AFTER_COMPLETED_CLONE_RECONCILIATION",
        reconciliationSHA256=sha256(state / "completed-clone-reconciliation.json"),
        nativeCloneAllowed=False, automaticReplay=False))
    api, guard = prepare_api(m,state,execute=True)
    router, runtime = router_for(api)
    planned = read(state / "plan.json")
    need(runtime == planned["runtimeIdentity"], "GROUP_BATCH_RECONCILED_SAVE_RUNTIME_DRIFT")
    return save_verified_batch(state,m,planned,api,guard,router,lease,evidence["nativeResponse"])


def saved_state(state):
    state = Path(state).resolve()
    m, saved = manifest_for(state), read(state / "saved.json")
    snap = read(state / "guarded-snapshot.json")
    need(saved["status"] == "GROUP_BATCH_SAVED_PENDING_REAL_REOPEN"
         and sha256(m["scratch"]) == sha256(state / "guarded-save.snapshot") == saved["savedSHA256"]
         and sha256(state / "guarded-snapshot.json") == saved["snapshotReceiptSHA256"]
         and snap["savedSHA256"] == snap["snapshotSHA256"] == saved["savedSHA256"]
         and snap["protectedSHA256"] == {str(Path(m["source"]).resolve()):m["sourceSHA256"]},
         "GROUP_BATCH_SAVED_BYTES_OR_SNAPSHOT_PROOF_DRIFT")
    return m, saved


def check_closed(state):
    state = Path(state).resolve()
    m, saved = saved_state(state)
    need(not (state / "closed.json").exists(), "GROUP_BATCH_CLOSE_ALREADY_RECORDED")
    api, _ = prepare_api(m, state, execute=False, saved_sha=saved["savedSHA256"])
    try: api("GetProjectInfo", {})
    except Exception as exc:
        need("4001" in str(exc) and "no open project" in str(exc).lower(),
             "GROUP_BATCH_NATIVE_NO_OPEN_PROJECT_NOT_CONFIRMED")
    else: raise ValueError("GROUP_BATCH_PROJECT_STILL_OPEN")
    record = dict(schema=SCHEMA, status="NATIVE_NO_OPEN_PROJECT_CONFIRMED",
                  savedSHA256=saved["savedSHA256"], nativeWrites=0)
    write_new_json(state / "closed.json", record)
    return record


def verify_reopen(state):
    state = Path(state).resolve()
    m, saved = saved_state(state)
    closed = read(state / "closed.json")
    need(not (state / "reopened.json").exists() and closed["status"] == "NATIVE_NO_OPEN_PROJECT_CONFIRMED"
         and closed["savedSHA256"] == saved["savedSHA256"], "GROUP_BATCH_REAL_CLOSE_REQUIRED")
    api, _ = prepare_api(m, state, execute=False, saved_sha=saved["savedSHA256"])
    _, runtime = router_for(api)
    need(runtime == read(state / "plan.json")["runtimeIdentity"], "GROUP_BATCH_REOPEN_RUNTIME_DRIFT")
    ids, native, proof = verify_group_model(m, api, read(state / "plan.json"),
        saved["nativeResponse"], read(state / "baseline-native.json"))
    need(len(ids) == saved["finalGuidCount"] and R.digest(ids) == saved["finalGuidSetSHA256"]
         and fingerprint(native) == saved["finalBrepSHA256"] and api.write_attempts == 0,
         "GROUP_BATCH_REOPEN_FULL_NATIVE_BREP_OR_GUID_DRIFT")
    result = dict(saved, status="LIVE_NATIVE_GROUP_BATCH_SAVED_REOPENED_PASS",
                  reopenVerified=True, reopenedReadback=proof, sourceUnchanged=True,
                  verificationNativeWrites=0)
    write_new_json(state / "reopened.json", result)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("phase", choices=("stage", "plan", "execute", "check-closed", "verify-reopen"))
    p.add_argument("--state", required=True)
    p.add_argument("--source"); p.add_argument("--scratch"); p.add_argument("--baseline-trace")
    p.add_argument("--safe01-state"); p.add_argument("--source-group"); p.add_argument("--placements-json")
    p.add_argument("--adopt-prior174-stage")
    p.add_argument("--port", type=int, default=19727)
    args = p.parse_args()
    if args.phase == "stage":
        need(all((args.source,args.scratch,args.baseline_trace,args.safe01_state,args.source_group,args.placements_json)),
             "GROUP_BATCH_STAGE_EXPLICIT_INPUTS_REQUIRED")
        out = stage(args.source,args.scratch,args.state,args.baseline_trace,args.safe01_state,
                    args.source_group,read(args.placements_json),args.port,
                    prior_stage=args.adopt_prior174_stage)
    else:
        need(not any((args.source,args.scratch,args.baseline_trace,args.safe01_state,args.source_group,args.placements_json,args.adopt_prior174_stage)),
             "GROUP_BATCH_REUSE_ONLY_PINNED_MANIFEST")
        out = {"plan":plan,"execute":execute,"check-closed":check_closed,"verify-reopen":verify_reopen}[args.phase](args.state)
    print(json.dumps(out,ensure_ascii=False,indent=2))


if __name__ == "__main__":
    main()
