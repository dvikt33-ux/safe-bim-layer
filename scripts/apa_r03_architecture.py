"""Existing parametric BuildingShell -> SceneWriter on a staged R03 copy."""
from collections import Counter
import json
from pathlib import Path
from uuid import uuid4

import apa_ac29_group_batch_oneshot as group
from apa_ac29_reusable_native_copy import GuardedSaveTransport
from apa_ac29_save_isolation import (
    ScratchWriteLease, confirm_project_closed, copy_exclusive, preserve_guarded_save, require,
    reservation_owner_exited, sha256, timestamp, write_new_json,
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
    scratch = job / "model" / MODEL
    design = intent.get("schemaVersion") == "apa-authored-project/1"
    if design:
        from apa_project_design import SCHEMA as DESIGN_SCHEMA, compile_design

        variant_fields = {key: intent[key] for key in ("layout", "storyHeights", "floorPlans") if key in intent}
        proposal = dict(schemaVersion=DESIGN_SCHEMA, brief=intent["brief"],
                        cseCandidate=intent["cseCandidate"], variants=[dict(id="selected-variant", **variant_fields)])
        report = compile_design(proposal)
        variant = report["variants"][0]
        require(set(intent) == {"schemaVersion", "units", "projectId", "brief", "cseCandidate",
                                *variant_fields}
                and intent["units"] == "meters" and intent["projectId"] == report["brief"]["projectId"]
                and report["brief"]["mode"] == "ADAPT_EXISTING"
                and intent["brief"]["targetProjectPath"] == str(scratch)
                and len(report["brief"]["stories"]) == 1 and variant["status"] == "DESIGN_CHECKS_REVIEWABLE",
                "APA_ARCHITECTURE_AUTHORED_TEST_SCOPE_REQUIRED")
        compiled = variant["candidate"]
    else:
        compiled = A.compile_intent(intent, SCHEMA)
        require(intent["components"][0]["primitive"] == "building-shell-v1",
                "APA_ARCHITECTURE_UNSUPPORTED_INTENT")
    commands = {row["command"] for row in compiled["graph"]["operations"]}
    require(commands <= MODEL_COMMANDS and sha256(intent_path) == intent_sha,
            "APA_ARCHITECTURE_UNSUPPORTED_INTENT")
    baseline, ids = group.accepted_baseline(baseline_trace)
    job.parent.mkdir(exist_ok=True)
    job.mkdir()
    model = job / "model"
    model.mkdir()
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
    if design:
        record.update(authoredIntentHash=R.digest(intent), authoredCommands=sorted(commands),
                      authorization="R04 TEST_REQUEST: local preflight grant pending")
    write_new_json(job / "job.json", record)
    return record


def check(job, donor, donor_sha):
    m = read(job / "job.json")
    path = job / "model" / MODEL
    require(m["schema"] == "APA_R03_ARCHITECTURE_JOB_V1" and m["status"] == "STAGED"
            and m["jobId"] == job.name and m["project"] == str(path) and path.resolve() == path
            and path.is_file() and donor.is_file() and not path.samefile(donor)
            and m["initialSHA256"] == donor_sha and m["original"] == str(donor)
            and m["authorizationRef"] == f"USER_APPROVED_APA_R03_{job.name}"
            and sha256(donor) == donor_sha and sha256(job / "intent.json") == m["intentSHA256"],
            "APA_ARCHITECTURE_JOB_SCOPE_DRIFT")
    return m


def saved_record(job, m):
    result = read(job / "saved.json")
    snapshot = read(job / "snapshot.json")
    require(result.get("status") == "LIVE_ARCHITECTURE_SAVED_PENDING_REAL_REOPEN"
            and result.get("jobId") == m["jobId"]
            and snapshot.get("schema") == "APA_SAVE_EXACT_SNAPSHOT_V1"
            and snapshot.get("source") == m["project"]
            and snapshot.get("savedSHA256") == snapshot.get("snapshotSHA256") == result["savedSHA256"]
            and sha256(m["project"]) == sha256(job / "guarded-save.snapshot") == result["savedSHA256"]
            and sha256(job / "snapshot.json") == result["snapshotReceiptSHA256"]
            and snapshot.get("protectedSHA256") == {m["original"]: m["initialSHA256"]}
            and sha256(m["original"]) == m["initialSHA256"],
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
        saved = saved_record(job, m)
        state = saved["status"]
        if (job / "reopened.json").is_file():
            reopened = read(job / "reopened.json")
            require(reopened.get("status") == "LIVE_ARCHITECTURE_SAVED_REOPENED_PASS"
                    and reopened.get("reopenVerified") is True
                    and reopened.get("savedSHA256") == saved["savedSHA256"]
                    and reopened.get("reopenedGuidSetSHA256") == saved["finalGuidSetSHA256"]
                    and reopened.get("reopenedBrepSHA256") == saved["finalBrepSHA256"],
                    "APA_ARCHITECTURE_REOPEN_RECEIPT_DRIFT")
            state = reopened["status"]
    elif (job / "attempted.json").exists() or Path(m["project"] + ".apa-write.lock").exists():
        state = "UNKNOWN_NO_REPLAY_READONLY_RECONCILIATION_REQUIRED"
    elif (job / "approved-preflight.json").is_file():
        state = approved_result(job, read(job / "approved-preflight.json"))["status"]
    else:
        state = "STAGED"
    return dict(jobId=job.name, status=state, project=m["project"], port=m["port"])


def runtime_identity(api, pinned_runtime):
    runtime = api("GetAPARuntimeInfoV1", {})
    require(runtime.get("contract") == "APA_NATIVE_RUNTIME_IDENTITY_V1"
            and runtime.get("sdkMajor") == 29 and runtime.get("nativeModelWrites") == 0
            and runtime.get("sourceRevision") == pinned_runtime[0]
            and runtime.get("buildIdentity") == pinned_runtime[1], "APA_ARCHITECTURE_WRONG_LOADED_APX")
    return runtime


def bind(m, port, pinned_runtime, *, saved_sha=None):
    require(19723 <= port <= 19743, "APA_ARCHITECTURE_INVALID_PORT")
    R.bind_authorized_saved_copy(port, m["project"], MODEL.removesuffix(".pln"),
                                 saved_sha or m["initialSHA256"], m["authorizationRef"])
    group.IDENTITY.current_project(A.native_transport, m["project"])
    return runtime_identity(A.native_transport, pinned_runtime)


def capture(m, api):
    ids, native = group.capture({"scratch": m["project"]}, api)
    return ids, native, C.retained_geometry_signatures(native, ids)


def baseline_capture(job, m, trace):
    folder = job / trace
    folder.mkdir(parents=True)
    api = A.EvidenceAPI(A.native_transport, folder, execute=False)
    ids, native, signatures = capture(m, api)
    prove_retained(m, ids, native)
    return ids, signatures


def probe_shell_runtime(job, trace):
    folder = job / trace
    folder.mkdir(parents=True)
    api = A.EvidenceAPI(A.native_transport, folder, execute=False)
    intent = read(job / "intent.json")
    if intent.get("schemaVersion") == "apa-authored-project/1":
        staged = read(job / "job.json")
        require(staged.get("authoredIntentHash") == R.digest(intent)
                and set(staged["authoredCommands"]) <= MODEL_COMMANDS,
                "APA_ARCHITECTURE_AUTHORED_STAGE_DRIFT")
        commands = set(staged["authoredCommands"]) | {"SaveProject", "ModifySlabs"}
    else:
        commands = MODEL_COMMANDS | {"SaveProject"}
    if "components" in intent and intent["components"][0]["specification"].get("slabBasicMaterialName"):
        commands |= {"ModifySlabs"}
    router = A.native_command_router(SCHEMA, include_functional_modules=False)
    for command in sorted(commands):
        router.probe_runtime(api, command)
    require(api.write_attempts == 0, "APA_ARCHITECTURE_REGISTRATION_MUST_BE_READ_ONLY")


def prove_retained(m, ids, native):
    require(R.digest(ids) == m["baselineGuidSetSHA256"]
            and group.fingerprint(native) == m["baselineBrepSHA256"],
            "APA_ARCHITECTURE_BASELINE_GUID_OR_BREP_DRIFT")


def preflight(job, m, port, pinned_runtime, *, local_listener=None):
    require(status(job, m)["status"] == "STAGED", "APA_ARCHITECTURE_ALREADY_PREFLIGHTED_OR_ATTEMPTED")
    before = local_listener(port) if local_listener else None
    runtime = bind(m, port, pinned_runtime)
    attempts = job / "preflight-attempts"
    require(attempts.resolve() == attempts, "APA_ARCHITECTURE_PREFLIGHT_PATH_DRIFT")
    attempts.mkdir(exist_ok=True)
    attempt = attempts / uuid4().hex
    probe_shell_runtime(job, Path("registration-traces") / attempt.name)
    baseline_capture(job, m, Path("baseline-traces") / attempt.name)
    result = A.run_project(read(job / "intent.json"), SCHEMA, attempt, job / "ledger",
                           mode="preflight", transport=A.native_transport,
                           allow_3d_view_for_write=True)
    result_path = attempt / "result.json"
    if result["status"] == "READY_FOR_EXPLICIT_TEST_RUN":
        compiled = read(attempt / "plan.json")
        if "authoredIntentHash" in m:
            commands = {row["command"] for row in compiled["graph"]["operations"]}
            same_plan = compiled["intentHash"] == m["authoredIntentHash"] and commands == set(m["authoredCommands"])
        else:
            same_plan = compiled["sourcePlanHash"] == m["offlinePlanHash"]
        require(result["modelWriteAttempts"] == 0 and same_plan,
                "APA_ARCHITECTURE_PREFLIGHT_DRIFT")
        if local_listener:
            require(local_listener(port) == before, "APA_ARCHITECTURE_PREFLIGHT_PROCESS_DRIFT")
        write_new_json(job / "approved-preflight.json", dict(
            jobId=job.name, port=port, runtime=runtime, confirmHash=result["confirmPlanHash"],
            resultPath=result_path.relative_to(job).as_posix(), preflightSHA256=sha256(result_path),
            **({"listener": before} if before is not None else {}),
        ))
    return dict(result, evidencePath=str(result_path))


def execute(job, m, pinned_runtime, *, confirm_preflight=None):
    state = status(job, m)["status"]
    if state in {"LIVE_ARCHITECTURE_SAVED_PENDING_REAL_REOPEN", "LIVE_ARCHITECTURE_SAVED_REOPENED_PASS"}:
        return dict(status="ALREADY_APPLIED", receipt=saved_record(job, m), newNativeWrites=0)
    require(state == "READY_FOR_EXPLICIT_TEST_RUN", "APA_ARCHITECTURE_READY_PREFLIGHT_REQUIRED")
    approval = read(job / "approved-preflight.json")
    if "authoredIntentHash" in m:
        require(confirm_preflight == sha256(job / "approved-preflight.json"),
                "APA_ARCHITECTURE_AUTHORED_EXACT_PREFLIGHT_GRANT_REQUIRED")
    approved_result(job, approval)
    require(bind(m, approval["port"], pinned_runtime) == approval["runtime"],
            "APA_ARCHITECTURE_APPROVED_PLAN_OR_RUNTIME_DRIFT")
    probe_shell_runtime(job, Path("registration-traces") / uuid4().hex)
    old_ids, old_signatures = baseline_capture(job, m, Path("baseline-traces") / uuid4().hex)
    ledger = job / "ledger"
    require(ledger.resolve() == ledger and not (ledger / "scene-v1-attempts.sqlite3").exists(),
            "APA_ARCHITECTURE_EXISTING_LEDGER_NO_REPLAY")
    ledger.mkdir(exist_ok=True)
    lease = ScratchWriteLease(m["project"], job, m["initialSHA256"])
    lease.acquire()
    write_new_json(job / "attempted.json", dict(jobId=job.name, atUTC=timestamp(),
                   confirmHash=approval["confirmHash"], automaticReplay=False))
    result = A.run_project(read(job / "intent.json"), SCHEMA, job / "build", ledger,
                           mode="execute", transport=A.native_transport,
                           run_id=job.name, confirm_hash=approval["confirmHash"],
                           allow_3d_view_for_write=True)
    if result["status"] != "COMPLETE_UNSAVED" or not result.get("wholeAssemblyReadback"):
        return result
    final_trace = job / "before-save-trace"
    final_trace.mkdir()
    readback = A.EvidenceAPI(A.native_transport, final_trace, execute=False)
    ids, model, signatures = capture(m, readback)
    require(set(ids) == set(old_ids) | set(result["addedGuids"])
            and all(signatures[guid] == value for guid, value in old_signatures.items()),
            "APA_ARCHITECTURE_FINAL_MODEL_NOT_VERIFIED")
    added = set(result["addedGuids"])
    bodies = {row["guid"].lower(): len(row.get("bodies", [])) for row in model["elements"]
              if row["guid"].lower() in added}
    kinds = Counter(row["kind"] for row in result["scene"]["steps"].values())
    require(all(bodies[row["guid"].lower()] > 0 for row in result["scene"]["steps"].values()
                if row["kind"] in {"Wall", "Slab"}), "APA_ARCHITECTURE_NEW_PHYSICAL_BREP_UNAVAILABLE")
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
                and sha256(m["project"]) == sha256(m["original"]) == m["initialSHA256"],
                "APA_ARCHITECTURE_PRE_SAVE_DRIFT")
        return dict(status="PASS", check="ARCHITECTURE_ALL_RETAINED_BREP_AND_NEW_GUIDS")

    def after_save(reply, _):
        require(reply == {"success": True} and guard.new_saved_sha and lease.verify(),
                "APA_ARCHITECTURE_SAVE_UNCONFIRMED")
        record = preserve_guarded_save(m["project"], job / "guarded-save.snapshot",
                                      guard.new_saved_sha, {m["original"]: m["initialSHA256"]})
        write_new_json(job / "snapshot.json", record)
        return dict(status="PASS", check="ARCHITECTURE_SAVED_BYTES_CONFIRMED",
                    savedSHA256=guard.new_saved_sha)

    save_scene_id = "Save-" + R.digest(job.name)[:24]
    outcome = router.execute(writer, save_scene_id, router.prepare("SaveProject", {}),
                             [], signatures, m["initialSHA256"], m["authorizationRef"],
                             "PROJECT", after_save, verify_before=before_save)
    require(outcome["status"] == "PASS" and api.calls["SaveProject"] == 1,
            "APA_ARCHITECTURE_SAVE_UNKNOWN_NO_REPLAY")
    requirements = result.get("requirementReadback")
    result = dict(status="LIVE_ARCHITECTURE_SAVED_PENDING_REAL_REOPEN", jobId=job.name,
                  savedSHA256=guard.new_saved_sha, elementCount=len(ids),
                  addedGuids=result["addedGuids"], finalGuidSetSHA256=R.digest(ids),
                  finalBrepSHA256=group.fingerprint(model), wholeAssemblyReadback=True,
                  finalSignaturesSHA256=R.digest(signatures), addedByKind=dict(kinds),
                  bodyCountByAddedGuid=bodies, nativeModelWriteAttempts=result["modelWriteAttempts"],
                  snapshotReceiptSHA256=sha256(job / "snapshot.json"), nativeSaveCalls=1)
    if requirements is not None:
        result["requirementReadback"] = requirements
    write_new_json(job / "saved.json", result)
    return result


def check_closed(job, m, pinned_runtime, *, process_id=None):
    saved = saved_record(job, m)
    approval = read(job / "approved-preflight.json")
    approved_result(job, approval)
    path = job / "closed.json"
    require(not path.exists(), "APA_ARCHITECTURE_CLOSE_ALREADY_RECORDED")
    port = approval["port"]
    status_name = "NATIVE_NO_OPEN_PROJECT_CONFIRMED"
    if process_id is not None and reservation_owner_exited(process_id):
        status_name = "ARCHICAD_TEST_PROCESS_EXIT_CONFIRMED"
    else:
        R.bind_authorized_saved_copy(port, m["project"], MODEL.removesuffix(".pln"),
                                     saved["savedSHA256"], m["authorizationRef"])
        require(A.archicad29(A.native_transport)["buildNumber"] == 5101
                and runtime_identity(A.native_transport, pinned_runtime) == approval["runtime"],
                "APA_ARCHITECTURE_CLOSE_WRONG_RUNTIME")
        confirm_project_closed(A.native_transport)
    require(saved_record(job, m) == saved, "APA_ARCHITECTURE_SAVE_CHANGED_AT_CLOSE")
    result = dict(status=status_name, jobId=m["jobId"], port=port,
                  savedSHA256=saved["savedSHA256"], nativeWrites=0)
    if process_id is not None:
        result["pid"] = process_id
    write_new_json(path, result)
    return result


def verify_reopen(job, m, pinned_runtime, port):
    saved = saved_record(job, m)
    closed = read(job / "closed.json")
    approval = read(job / "approved-preflight.json")
    approved_result(job, approval)
    native_close = closed["status"] == "NATIVE_NO_OPEN_PROJECT_CONFIRMED" and port == approval["port"]
    process_exit = (closed["status"] == "ARCHICAD_TEST_PROCESS_EXIT_CONFIRMED"
                    and reservation_owner_exited(closed["pid"]))
    require((native_close or process_exit) and closed["jobId"] == m["jobId"]
            and closed["port"] == approval["port"]
            and closed["savedSHA256"] == saved["savedSHA256"] and closed["nativeWrites"] == 0,
            "APA_ARCHITECTURE_REAL_CLOSE_REQUIRED")
    require(bind(m, port, pinned_runtime, saved_sha=saved["savedSHA256"]) == approval["runtime"],
            "APA_ARCHITECTURE_REOPEN_RUNTIME_DRIFT")
    folder = job / "reopen-attempts" / uuid4().hex
    folder.mkdir(parents=True)
    api = A.EvidenceAPI(A.native_transport, folder, execute=False)
    ids, model, signatures = capture(m, api)
    guid_hash, brep_hash = R.digest(ids), group.fingerprint(model)
    require(len(ids) == saved["elementCount"] and guid_hash == saved["finalGuidSetSHA256"]
            and brep_hash == saved["finalBrepSHA256"]
            and R.digest(signatures) == saved["finalSignaturesSHA256"]
            and saved_record(job, m) == saved and api.write_attempts == 0,
            "APA_ARCHITECTURE_REOPEN_GUID_BREP_OR_ATTRIBUTES_DRIFT")
    result = dict(saved, status="LIVE_ARCHITECTURE_SAVED_REOPENED_PASS", reopenVerified=True,
                  reopenedGuids=ids, reopenedGuidSetSHA256=guid_hash, reopenedBrepSHA256=brep_hash,
                  verificationNativeWrites=0, sourceUnchanged=True, reopenPort=port)
    path = job / "reopened.json"
    if path.exists():
        require(read(path) == result, "APA_ARCHITECTURE_REOPEN_RECEIPT_DRIFT")
    else:
        write_new_json(path, result)
    return result
