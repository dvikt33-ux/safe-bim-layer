"""Existing parametric BuildingShell -> SceneWriter on a staged R03 copy."""
from pathlib import Path
import json
from uuid import uuid4

import apa_ac29_group_batch_oneshot as group
from apa_ac29_reusable_native_copy import GuardedSaveTransport
from apa_ac29_save_isolation import (
    ScratchWriteLease, copy_exclusive, preserve_guarded_save, require, sha256,
    timestamp, write_new_json,
)

A, R, C = group.A, group.R, group.C
SCHEMA = group.SCHEMA_PATH
MODEL = "APA-R03-architecture-test.pln"
MODEL_COMMANDS = {"CreateWalls", "CreateSlabs", "CreateDoors", "CreateWindows"}


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def stage(job, intent_path, port, donor, donor_sha, baseline_trace):
    require(19723 <= port <= 19743 and sha256(donor) == donor_sha,
            "APA_ARCHITECTURE_PINNED_DONOR_AND_PORT_REQUIRED")
    intent_sha = sha256(intent_path)
    intent = read(intent_path)
    compiled = A.compile_intent(intent, SCHEMA)
    steps = compiled["graph"]["operations"]
    require(intent["components"][0]["primitive"] == "building-shell-v1"
            and all(row["command"] in MODEL_COMMANDS for row in steps)
            and sha256(intent_path) == intent_sha, "APA_ARCHITECTURE_UNSUPPORTED_INTENT")
    baseline, ids = group.accepted_baseline(baseline_trace)
    job.parent.mkdir(exist_ok=True)
    job.mkdir()
    model = job / "model"
    model.mkdir()
    scratch = model / MODEL
    copy_exclusive(donor, scratch)
    require(sha256(scratch) == sha256(donor) == donor_sha, "APA_ARCHITECTURE_COPY_SHA_DRIFT")
    copy_exclusive(intent_path, job / "intent.json")
    require(sha256(job / "intent.json") == intent_sha, "APA_ARCHITECTURE_INTENT_SHA_DRIFT")
    record = dict(schema="APA_R03_ARCHITECTURE_JOB_V1", jobId=job.name, status="STAGED",
                  project=str(scratch), port=port, initialSHA256=donor_sha,
                  original=str(donor), intentSHA256=intent_sha, offlinePlanHash=compiled["sourcePlanHash"],
                  baselineGuidSetSHA256=R.digest(ids), baselineBrepSHA256=group.fingerprint(baseline),
                  authorizationRef=f"USER_APPROVED_APA_R03_{job.name}", stagedAt=timestamp(),
                  authorization="APA R03 §11.1 / R03.1: newly created disposable test copy")
    write_new_json(job / "job.json", record)
    return record


def check(job, donor, donor_sha):
    m = read(job / "job.json")
    path = job / "model" / MODEL
    require(m["schema"] == "APA_R03_ARCHITECTURE_JOB_V1" and m["jobId"] == job.name
            and m["project"] == str(path) and path.resolve() == path
            and m["initialSHA256"] == donor_sha and m["original"] == str(donor)
            and m["authorizationRef"] == f"USER_APPROVED_APA_R03_{job.name}"
            and sha256(donor) == donor_sha and sha256(job / "intent.json") == m["intentSHA256"],
            "APA_ARCHITECTURE_JOB_SCOPE_DRIFT")
    return m


def saved_record(job, m):
    result = read(job / "saved.json")
    require(sha256(m["project"]) == sha256(job / "guarded-save.snapshot") == result["savedSHA256"]
            and sha256(job / "snapshot.json") == result["snapshotReceiptSHA256"],
            "APA_ARCHITECTURE_SAVED_BYTES_DRIFT")
    return result


def approved_result(job, approval):
    relative = Path(approval.get("resultPath", "preflight/result.json"))
    path = job / relative
    require(not relative.is_absolute() and path.resolve() == path
            and path.is_relative_to(job) and path.name == "result.json"
            and (relative.as_posix() == "preflight/result.json"
                 or len(relative.parts) == 3 and relative.parts[0] == "preflight-attempts")
            and approval["preflightSHA256"] == sha256(path),
            "APA_ARCHITECTURE_PREFLIGHT_RESULT_DRIFT")
    result = read(path)
    require(approval["jobId"] == job.name and result["status"] == "READY_FOR_EXPLICIT_TEST_RUN"
            and result["modelWriteAttempts"] == 0
            and approval["confirmHash"] == result["confirmPlanHash"],
            "APA_ARCHITECTURE_PREFLIGHT_APPROVAL_DRIFT")
    return result


def status(job, m):
    if (job / "saved.json").is_file():
        state = saved_record(job, m)["status"]
    elif (job / "attempted.json").exists() or Path(m["project"] + ".apa-write.lock").exists():
        state = "UNKNOWN_NO_REPLAY_READONLY_RECONCILIATION_REQUIRED"
    elif (job / "approved-preflight.json").is_file():
        state = approved_result(job, read(job / "approved-preflight.json"))["status"]
    else:
        state = "STAGED"
    return dict(jobId=job.name, status=state, project=m["project"], port=m["port"])


def bind(m, port, pinned_runtime, *, saved_sha=None):
    require(19723 <= port <= 19743, "APA_ARCHITECTURE_INVALID_PORT")
    R.bind_authorized_saved_copy(port, m["project"], MODEL.removesuffix(".pln"),
                                 saved_sha or m["initialSHA256"], m["authorizationRef"])
    group.IDENTITY.current_project(A.native_transport, m["project"])
    runtime = A.native_transport("GetAPARuntimeInfoV1", {})
    require(runtime.get("sourceRevision") == pinned_runtime[0]
            and runtime.get("buildIdentity") == pinned_runtime[1],
            "APA_ARCHITECTURE_WRONG_LOADED_APX")
    return runtime


def capture(m, api):
    ids, native = group.capture({"scratch": m["project"]}, api)
    return ids, native, C.retained_geometry_signatures(native, ids)


def prove_retained(m, ids, native):
    require(R.digest(ids) == m["baselineGuidSetSHA256"]
            and group.fingerprint(native) == m["baselineBrepSHA256"],
            "APA_ARCHITECTURE_BASELINE_GUID_OR_BREP_DRIFT")


def preflight(job, m, port, pinned_runtime):
    require(status(job, m)["status"] == "STAGED", "APA_ARCHITECTURE_ALREADY_PREFLIGHTED_OR_ATTEMPTED")
    runtime = bind(m, port, pinned_runtime)
    ids, model, _ = capture(m, A.native_transport)
    prove_retained(m, ids, model)
    attempts = job / "preflight-attempts"
    require(attempts.resolve() == attempts, "APA_ARCHITECTURE_PREFLIGHT_PATH_DRIFT")
    attempts.mkdir(exist_ok=True)
    attempt = attempts / uuid4().hex
    result = A.run_project(read(job / "intent.json"), SCHEMA, attempt, job / "ledger",
                           mode="preflight", transport=A.native_transport)
    result_path = attempt / "result.json"
    if result["status"] == "READY_FOR_EXPLICIT_TEST_RUN":
        require(result["modelWriteAttempts"] == 0
                and read(attempt / "plan.json")["sourcePlanHash"] == m["offlinePlanHash"],
                "APA_ARCHITECTURE_PREFLIGHT_DRIFT")
        write_new_json(job / "approved-preflight.json", dict(
            jobId=job.name, port=port, runtime=runtime, confirmHash=result["confirmPlanHash"],
            resultPath=result_path.relative_to(job).as_posix(), preflightSHA256=sha256(result_path),
        ))
    return dict(result, evidencePath=str(result_path))


def execute(job, m, pinned_runtime):
    state = status(job, m)["status"]
    if state == "LIVE_ARCHITECTURE_SAVED_PENDING_REAL_REOPEN":
        return dict(status="ALREADY_APPLIED", receipt=saved_record(job, m), newNativeWrites=0)
    require(state == "READY_FOR_EXPLICIT_TEST_RUN", "APA_ARCHITECTURE_READY_PREFLIGHT_REQUIRED")
    approval = read(job / "approved-preflight.json")
    approved_result(job, approval)
    require(bind(m, approval["port"], pinned_runtime) == approval["runtime"],
            "APA_ARCHITECTURE_APPROVED_PLAN_OR_RUNTIME_DRIFT")
    old_ids, old_model, old_signatures = capture(m, A.native_transport)
    prove_retained(m, old_ids, old_model)
    lease = ScratchWriteLease(m["project"], job, m["initialSHA256"])
    lease.acquire()
    write_new_json(job / "attempted.json", dict(jobId=job.name, atUTC=timestamp(),
                   confirmHash=approval["confirmHash"], automaticReplay=False))
    result = A.run_project(read(job / "intent.json"), SCHEMA, job / "build", job / "ledger",
                           mode="execute", transport=A.native_transport,
                           run_id=job.name, confirm_hash=approval["confirmHash"])
    if result["status"] != "COMPLETE_UNSAVED" or not result.get("wholeAssemblyReadback"):
        return result
    ids, model, signatures = capture(m, A.native_transport)
    require(set(ids) == set(old_ids) | set(result["addedGuids"])
            and all(signatures[guid] == value for guid, value in old_signatures.items()),
            "APA_ARCHITECTURE_FINAL_MODEL_NOT_VERIFIED")
    write_new_json(job / "native-before-save.json", model)
    guard = GuardedSaveTransport(
        A.native_transport, R.bind_authorized_saved_copy, m["project"], m["original"],
        lambda: sha256(m["project"]), lambda: sha256(m["original"]),
        MODEL.removesuffix(".pln"), approval["port"], m["authorizationRef"],
    )
    trace = job / "save-trace"
    trace.mkdir()
    api = A.EvidenceAPI(guard, trace, execute=True)
    writer = R.SceneWriter(api, job / "ledger" / "scene-v1-attempts.sqlite3",
                           SCHEMA, allow_3d_view_for_write=True)
    router = A.native_command_router(SCHEMA, include_functional_modules=False)
    router.probe_runtime(api, "SaveProject")
    router.review_policy("SaveProject", "TRANSACTION", "PROJECT", {
        "source": str(job / "approved-preflight.json"), "sha256": router.contract_hash("SaveProject"),
    })
    guard.enable_after_verified_copy()

    def before_save(live):
        current_ids, _, current_signatures = capture(m, live)
        require(lease.verify() and current_ids == ids and current_signatures == signatures
                and sha256(m["project"]) == m["initialSHA256"], "APA_ARCHITECTURE_PRE_SAVE_DRIFT")
        return dict(status="ARCHITECTURE_ALL_RETAINED_BREP_AND_NEW_GUIDS_VERIFIED")

    def after_save(reply, _):
        require(reply == {"success": True} and guard.new_saved_sha, "APA_ARCHITECTURE_SAVE_UNCONFIRMED")
        record = preserve_guarded_save(m["project"], job / "guarded-save.snapshot",
                                      guard.new_saved_sha, {m["original"]: m["initialSHA256"]})
        write_new_json(job / "snapshot.json", record)
        return dict(status="ARCHITECTURE_SAVED_BYTES_CONFIRMED", savedSHA256=guard.new_saved_sha)

    save_scene_id = "Save-" + R.digest(job.name)[:24]
    outcome = router.execute(writer, save_scene_id, router.prepare("SaveProject", {}),
                             [], signatures, m["initialSHA256"], m["authorizationRef"],
                             "PROJECT", after_save, verify_before=before_save)
    require(outcome["status"] == "PASS" and api.calls["SaveProject"] == 1,
            "APA_ARCHITECTURE_SAVE_UNKNOWN_NO_REPLAY")
    result = dict(status="LIVE_ARCHITECTURE_SAVED_PENDING_REAL_REOPEN", jobId=job.name,
                  savedSHA256=guard.new_saved_sha, elementCount=len(ids),
                  addedGuids=result["addedGuids"], finalGuidSetSHA256=R.digest(ids),
                  finalBrepSHA256=group.fingerprint(model), wholeAssemblyReadback=True,
                  snapshotReceiptSHA256=sha256(job / "snapshot.json"), nativeSaveCalls=1)
    write_new_json(job / "saved.json", result)
    return result
