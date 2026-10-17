"""APA AC29 autonomous GitHub job bridge; one persistent receiver, EXISTING APA engine.

No UI Dispatcher/Arena changes. No second BIM router or writer. The inbox may
request only source-verified READ_ONLY graphs or a pre-reviewed BDD production
preflight. Native model writes remain ungranted; any future CREATE/MODIFY path
must add a separate locally approved, fully scoped SceneWriter adapter.
"""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time

ROOT = Path(r"C:\LocalAI\APA_AC29_Stable")
SCRIPTS = ROOT / "scripts"
STATE = ROOT / "apa-job-bridge-state"
WORKING = Path(r"C:\LocalAI\SafeBIM_Global_Library_Test_Projects\BDD дом - по чертежам 2022.pln")
ORIGINAL = Path(r"C:\LocalAI\SafeBIM_Global_Library_Test_Projects\BDD дом .pln")
SOURCE_SHA = "33b96850ad07547a9b12524de8bc46479fd98fbbce6772436d388be679836d66"
BASE_SHA = "e91d5670f20202c269d442bafc6e66a4cb13d223344122243b7237047a9ff3aa"
MODULE_HASHES = {
    "archicad_project_accelerator.py": "5ce7cbb91c8f799265a541f79922b50455fecf661ed9278a1cc4ffaff766ba4b",
    "archicad_dynamic_commands.py": "8effd2f294197179b4b18b785de80f7f78091649e7f105ee4cf66877dbe0e6f8",
    "archicad_strategy_discovery.py": "32b7f1c161c545695b6db20aa87003d08cbd86916bc880f9eba1434f3a0801ce",
}
BRIDGE = "dvikt33-ux/safe-bim-bridge"
INBOX = "safe-bim-mailbox/apa-ac29/jobs"
RESULTS = "safe-bim-mailbox/apa-ac29/results"
ID = re.compile(r"^[a-z][a-z0-9-]{7,63}$")
# This pre-reviewed script uses only APA.EvidenceAPI(execute=False) and native
# BREP reads; it does NOT use a second SceneWriter or independent mutation.
REVIEW = ROOT / "controllers" / "apa_bdd114_native_roof_face_review.py"
ALLOWED = frozenset({"BDD114_ROOF_FINALIZE", "SOURCE_QUALIFIED_NATIVE_READ",
                     "APPROVED_NATIVE_COLUMN_COPY", "APPROVED_MULTI_PROTOTYPE_COPY",
                     "CURRENT_MODEL_FINGERPRINT"})


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_sha(blob):
    return hashlib.sha1(b"blob " + str(len(blob)).encode("ascii") + b"\0" + blob).hexdigest()


def runtime_release():
    """Local updater receipt, never supplied by an inbox task."""
    path=ROOT/'controllers'/'runtime-release.json'
    if not path.exists():
        return None
    receipt=json.loads(path.read_text(encoding='utf8'))
    old_keys={
        'schema','revision','workerSHA256','moduleHashes',
        'workingPlnSha256','expectedGuidCount'}
    basic_modules=set(MODULE_HASHES)|{
        'apa_ac29_dynamic_write_scopes.py','apa_ac29_dynamic_native_verifiers.py'}
    verified_extension_modules={
        'apa_ac29_existing_create_verifiers.py',
        'apa_ac29_existing_modify_verifiers.py'}
    helpers={'apa_ac29_reusable_native_copy.py','apa_ac29_multi_prototype_native_copy.py',
             'apa_ac29_scene_reconciliation.py'}
    require(isinstance(receipt,dict) and set(receipt) in (old_keys,old_keys|{'controllerHashes'}) and
        receipt['schema']=='APA_AC29_RUNTIME_RELEASE_V1' and
        re.fullmatch('[0-9a-f]{40}',receipt['revision']) and
        receipt['workerSHA256']==sha(Path(__file__)) and
        set(receipt['moduleHashes']) in (basic_modules,basic_modules|helpers, basic_modules|helpers|verified_extension_modules) and
        all(re.fullmatch('[0-9a-f]{64}',value) for value in receipt['moduleHashes'].values()) and
        re.fullmatch('[0-9a-f]{64}',receipt['workingPlnSha256']) and
        type(receipt['expectedGuidCount']) is int and receipt['expectedGuidCount']>0,
        'LOCAL_RUNTIME_RELEASE_RECEIPT_INVALID')
    if 'controllerHashes' in receipt:
        require(set(receipt['controllerHashes'])==helpers and all(
            re.fullmatch('[0-9a-f]{64}',value) for value in receipt['controllerHashes'].values()),
            'LOCAL_RUNTIME_CONTROLLER_RECEIPT_INVALID')
    return receipt


def approved_saved_sha():
    receipt=runtime_release()
    return receipt['workingPlnSha256'] if receipt else BASE_SHA


def approved_guid_count():
    receipt=runtime_release()
    return receipt['expectedGuidCount'] if receipt else 290


def gh_api(path, *, body=None):
    cmd = ["gh", "api"]
    if body is not None:
        cmd += ["--method", "PUT", path, "--input", str(body)]
    else:
        cmd.append(path)
    p = subprocess.run(cmd, capture_output=True, timeout=50)
    require(p.returncode == 0, "GITHUB_UNAVAILABLE:" +
            p.stderr.decode("utf-8", errors="replace")[-250:])
    return json.loads(p.stdout.decode("utf-8"))


def remote_json(repo, filename, ref, expected_blob=None):
    require(repo in (BRIDGE, "dvikt33-ux/safe-bim-layer"),
            "JOB_FILE_REPO_NOT_APPROVED")
    require(".." not in filename and filename.startswith("safe-bim-mailbox/") or
            repo == "dvikt33-ux/safe-bim-layer" and
            filename.startswith("examples/accelerator/"),
            "JOB_SOURCE_PATH_NOT_APPROVED")
    obj = gh_api(f"repos/{repo}/contents/{filename}?ref={ref}")
    data = base64.b64decode(obj["content"])
    digest = git_sha(data)
    require(digest == obj["sha"] and
            (expected_blob is None or digest == expected_blob),
            "JOB_GITHUB_BLOB_DRIFT")
    return json.loads(data.decode("utf-8-sig")), digest


def current_utc():
    return datetime.now(timezone.utc)


def date(value):
    require(isinstance(value, str) and value.endswith("Z"),
            "JOB_TIMESTAMP_INVALID")
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(dt.tzinfo is not None, "JOB_TZ_REQUIRED")
    return dt


def validate_job(job, name):
    expected = {"schema", "jobId", "action", "createdAt", "expiresAt",
                "projectSha256", "sourceTask"}
    require(isinstance(job, dict) and set(job) == expected,
            "JOB_ENVELOPE_KEYS_INVALID")
    require(job.get("schema") == "APA_AC29_AUTONOMOUS_JOB_V1" and
            job.get("jobId") == name and ID.fullmatch(name),
            "JOB_ID_NOT_BOUND_TO_FILE")
    require(job["action"] in ALLOWED and
            job["projectSha256"] == approved_saved_sha(),
            "JOB_ACTION_OR_TARGET_NOT_ALLOWED")
    created, expires, now = date(job["createdAt"]), date(job["expiresAt"]), current_utc()
    require(created <= now and expires > now and
            0 < (expires-created).total_seconds() <= 7*86400,
            "JOB_TIME_WINDOW_INVALID")
    ref = job["sourceTask"]
    if job["action"] in ("BDD114_ROOF_FINALIZE", "CURRENT_MODEL_FINGERPRINT"):
        require(ref is None, "LOCAL_APPROVED_ACTION_MUST_NOT_CONTAIN_SOURCE_TASK")
    else:
        require(isinstance(ref, dict) and set(ref) ==
                {"repo", "ref", "path", "blobSha1"} and
                ref["repo"] == "dvikt33-ux/safe-bim-layer" and
                re.fullmatch("[0-9a-f]{40}", ref["ref"]) and
                re.fullmatch("[0-9a-f]{40}", ref["blobSha1"]) and
                ref["path"].startswith("examples/accelerator/") and
                ".." not in ref["path"], "READ_TASK_NOT_PINNED")
    return job


def stable_preflight():
    require(SCRIPTS.is_dir() and
            (ROOT / "apa-selector-install-receipt.json").is_file(),
            "STABLE_APA_DEPLOYMENT_ABSENT")
    release=runtime_release()
    for name, expected in (release['moduleHashes'] if release else MODULE_HASHES).items():
        require(sha(SCRIPTS / name) == expected, "STABLE_APA_MODULE_DRIFT:" + name)
    if release:
        for name,expected in release.get('controllerHashes',{}).items():
            require(sha(ROOT/'controllers'/name)==expected,'STABLE_APA_CONTROLLER_DRIFT:'+name)
    require(WORKING.is_file() and ORIGINAL.is_file() and
            sha(WORKING) == approved_saved_sha() and sha(ORIGINAL) == SOURCE_SHA,
            "BDD_SAVED_OR_PROTECTED_PLN_CHANGED")
    receipt = json.loads((ROOT / "apa-selector-install-receipt.json").read_text(encoding="utf-8"))
    require(receipt.get("applied") is True and
            receipt.get("status") == "STABLE_SELECTOR_DEPLOYED_IMPORT_VERIFIED_NO_NATIVE_CALLS",
            "STABLE_INSTALL_RECEIPT_NOT_PASS")


def capture_read_task(job, folder):
    """End-to-end typed read through the ORIGINAL APA selector and executor."""
    spec = job["sourceTask"]
    task, task_blob = remote_json(spec["repo"], spec["path"], spec["ref"],
                                  spec["blobSha1"])
    require(task.get("schemaVersion") == "apa-capability-task/1" and
            isinstance(task.get("steps"), list) and 1 <= len(task["steps"]) <= 20 and
            all(row.get("effect") == "READ_ONLY" and
                row.get("impact") == "READ_ONLY" for row in task["steps"]),
            "AUTOMATED_WORKER_ONLY_TYPED_SOURCE_VERIFIED_READS")
    sys.path.insert(0, str(SCRIPTS))
    import archicad_project_accelerator as APA
    import archicad_strategy_discovery as DISC
    import archicad_scene_run as RUN
    RUN.bind_authorized_saved_copy(
        19727, str(WORKING), WORKING.stem, approved_saved_sha(),
        "APA_AC29_GITHUB_JOB_READ_ONLY_" + job["jobId"]
    )
    export = folder / "live-schema"
    exported = APA.export_schema(export, APA.native_transport)
    raw = folder / "raw"
    raw.mkdir()
    api = APA.EvidenceAPI(APA.native_transport, raw, execute=False)
    guids_before = APA.inventory_guids(api)
    require(len(guids_before) == approved_guid_count(), "BDD_NATIVE_GUID_COUNT_DRIFT")
    writer = RUN.SceneWriter(api, folder / "read-only-unused.sqlite",
                             schema_path=export / "tapir-scene-live.json",
                             allow_3d_view_for_write=True)
    router, preview, runtime = DISC.prepare_current_runtime_catalog_task(writer, task)
    require(preview.get("selectedNativeTaskPreview") is not None and
            preview.get("status") in (
                "ONE_SOURCE_QUALIFIED_STRATEGY_PREPARED",
                "COST_OPTIMAL_SOURCE_QUALIFIED_STRATEGY_PREPARED"),
            "AUTO_SELECTOR_DID_NOT_RESOLVE_TYPED_READ_TASK")
    require(all(router.operation_kind(row["command"]) == "READ_ONLY"
                for row in preview["selectedNativeTaskPreview"]["workflow"]["graph"]["operations"]),
            "WORKER_SELECTED_NON_READ_ONLY_COMMAND")
    result = APA.run_auto_optimized_native_task(
        router, api, preview, writer, scopes={}
    )
    after = APA.inventory_guids(api)
    require(after == guids_before and api.write_attempts == 0 and
            sha(WORKING) == approved_saved_sha() and sha(ORIGINAL) == SOURCE_SHA,
            "READ_JOB_MODEL_DRIFT")
    require(result.get("status") == "WORKFLOW_CALLABLE_VERIFIED",
            "READ_WORKFLOW_INCOMPLETE")
    # Keep the full result local; publish only a bounded summary/evidence hash.
    local = folder / "native-read-results.json"
    local.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                     encoding="utf-8")
    return {
        "status": "AUTO_SELECTED_NATIVE_READ_WORKFLOW_PASS",
        "selectorMethod": preview.get("selectionMethod"),
        "selectedCommands": runtime["selectedCommands"],
        "schemaExportCount": exported["commands"],
        "readTaskSourceBlob": task_blob,
        "readResultSHA256": sha(local),
        "readResultLocalFile": str(local),
        "guidCount": len(after),
        "modelWrites": 0,
    }


def capture_current_model_fingerprint(job, folder):
    """One read-only job yields exact live GUID/BREP binding for next native task."""
    sys.path.insert(0, str(SCRIPTS))
    import archicad_project_accelerator as APA
    import archicad_scene_run as RUN
    import archicad_connected_components as C
    import archicad_bim_documentation as D
    RUN.bind_authorized_saved_copy(
        19727, str(WORKING), WORKING.stem, approved_saved_sha(),
        "APA_AC29_READ_ONLY_NATIVE_MODEL_FINGERPRINT_" + job["jobId"])
    folder_raw = folder / "raw"
    folder_raw.mkdir()
    api = APA.EvidenceAPI(APA.native_transport, folder_raw, execute=False)
    target = RUN.guarded_project_for_read(api)
    require(target["activeViewStoryIndex"] in (0, -1) and
            APA.archicad29(api).get("buildNumber") == 5101,
            "NATIVE_MODEL_FINGERPRINT_WRONG_BDD_INSTANCE")
    before = sorted(APA.inventory_guids(api))
    require(len(before) == approved_guid_count(), "NATIVE_MODEL_FINGERPRINT_NOT_APPROVED_BASELINE")
    dump = D.capture_full_model(api, before)
    # capture_full_model already returns normalized nodes. A second native
    # normalization consumes bodies as raw provider records and fails.
    native = dump
    found = {e["guid"].lower(): e for e in native["elements"]}
    require(set(found) == set(before),
            "NATIVE_MODEL_FINGERPRINT_PARTIAL_BREP")
    geometry = {g: C.ROOF.geometry_signature(found[g]) for g in before}
    after = sorted(APA.inventory_guids(api))
    require(after == before and api.write_attempts == 0 and
            sha(WORKING) == approved_saved_sha() and sha(ORIGINAL) == SOURCE_SHA,
            "NATIVE_MODEL_FINGERPRINT_CHANGED_DURING_READ")
    return {
        "status": "EXACT_CURRENT_MODEL_GUID_AND_BREP_FINGERPRINT_PASS",
        "targetWorkingPlnSha256": approved_saved_sha(),
        "expectedGuidCount": len(before),
        "expectedGuidSetHash": RUN.digest(before),
        "expectedModelSignatureHash": RUN.digest(geometry),
        "currentPort": 19727,
        "nativeReadCommands": dict(api.calls),
        "nativeWriteAttempts": 0,
        "nativeSaveCalls": 0
    }


def capture_approved_native_copy(job, folder):
    """Source-qualified native copy with ORIGINAL DynamicCommands and SceneWriter.

    This bridge version remains pinned to its installed, explicitly approved
    BDD working PLN. Target positions and source GUID are read from the
    SOURCE-VERIFIED GitHub task; not hardcoded in the executor/worker.
    """
    source = job["sourceTask"]
    task, blob = remote_json(source["repo"], source["path"],
                             source["ref"], source["blobSha1"])
    sys.path.insert(0, str(SCRIPTS))
    import sqlite3
    import archicad_project_accelerator as APA
    import archicad_scene_run as RUN
    import archicad_connected_components as C
    import archicad_bim_documentation as D
    import apa_ac29_reusable_native_copy as BATCH
    import apa_ac29_multi_prototype_native_copy as MULTI
    import apa_ac29_scene_reconciliation as RECON
    multi = job["action"] == "APPROVED_MULTI_PROTOTYPE_COPY"
    require(multi or job["action"] == "APPROVED_NATIVE_COLUMN_COPY",
            "NATIVE_COPY_UNSUPPORTED_TASK_ACTION")

    (MULTI if multi else BATCH).validate_task(
        task, expected_project_sha=approved_saved_sha(),
        expected_project_path=str(WORKING))
    require(task["expectedGuidCount"] == approved_guid_count(),
            "APPROVED_BDD_TARGET_INITIAL_INVENTORY_COUNT_DRIFT")
    require(task["sourceEvidenceRef"].startswith("https://github.com/") and
            task["authorizationRef"].startswith("USER_APPROVED_"),
            "NATIVE_COPY_USER_APPROVAL_AND_SOURCE_REQUIRED")
    require_native_copy_grant(job, folder, blob, task["authorizationRef"])
    RUN.bind_authorized_saved_copy(
        19727, str(WORKING), WORKING.stem, approved_saved_sha(),
        task["authorizationRef"])
    pre_raw = folder / "preflight-raw"
    pre_raw.mkdir()
    read_api = APA.EvidenceAPI(APA.native_transport, pre_raw, execute=False)
    binding = RUN.guarded_project_for_read(read_api)
    require(binding["activeViewStoryIndex"] in (0, -1) and
            APA.archicad29(read_api).get("buildNumber") == 5101,
            "NATIVE_COPY_WRONG_CURRENT_PROJECT_VIEW_OR_BUILD")
    # Read the ORIGINAL existing SceneWriter journal, do not clear unknowns.
    ledger = Path(os.environ["LOCALAPPDATA"]) / "APA_BDD_Window1p8" / "apa_scene_writer.sqlite"
    existing = BATCH.stored_scenes_clear(
        ledger, (task["sceneId"], task["saveSceneId"]))
    historical = None
    if existing:
        known = "BDD_BULK150_GRID_AND_LINE_20261016"
        require(len(existing) == 1 and existing[0] ==
                {"sceneId": known, "state": "PARTIAL_OR_UNKNOWN_OUTCOME"},
                "UNRELATED_UNRECONCILED_NATIVE_WRITE_STOPPED")
        raw = Path(os.environ["LOCALAPPDATA"]) / "APA_BDD_Bulk150_NearHouse" / "raw" / "raw.jsonl"
        historical = RECON.read_only_reconciliation(
            known, ledger, raw, read_api,
            normalized=C.G.normalize_dump,
            geom_signature=C.ROOF.geometry_signature,
            digest=RUN.digest, expected_project_sha=approved_saved_sha(),
            current_project_sha=sha(WORKING))
        historical_receipt = folder / "historical-reconciliation.json"
        durable_write(historical_receipt, historical)
    require(read_api.write_attempts == 0 and
            sha(WORKING) == approved_saved_sha() and sha(ORIGINAL) == SOURCE_SHA,
            "NATIVE_COPY_PREFLIGHT_MUTATED_MODEL_OR_DISK")
    guard = BATCH.GuardedSaveTransport(
        APA.native_transport, RUN.bind_authorized_saved_copy,
        WORKING, ORIGINAL, lambda: sha(WORKING),
        lambda: sha(ORIGINAL), WORKING.stem, 19727,
        task["authorizationRef"])
    write_raw = folder / "execution-raw"
    write_raw.mkdir()
    api = APA.EvidenceAPI(guard, write_raw, execute=True)
    schema = ROOT / "schemas" / "tapir-live-1.5.10" / "tapir-scene-live.json"
    require(schema.is_file(), "STABLE_AC29_NATIVE_SCHEMA_NOT_FOUND")
    router = APA.native_command_router(
        schema, include_functional_modules=False)
    writer = RUN.SceneWriter(
        api, ledger, schema_path=schema, allow_3d_view_for_write=True)
    # ONE single logical operation + native save, no retry or alternate writer.
    result = (MULTI.execute_multi_task if multi else BATCH.execute_task)(
        task, api=api, writer=writer, router=router, APA=APA, RUN=RUN,
        components=C, capture_native=D.capture_full_model,
        saved_project_sha=approved_saved_sha(), current_sha=lambda: sha(WORKING),
        save_guard=guard, known_reconciliation=historical)
    total = (sum(len(g["targets"]) for g in task["prototypes"])
             if multi else len(task["targets"]))
    expected_new = (sum(MULTI.expected_new_types(task).values())
                    if multi else len(task["targets"])*2)
    require(result["copiedCount"] == total and
            result["finalGuidCount"] == approved_guid_count() + expected_new and
            (result["nativeMoveCalls"] if multi else result["nativeCopyCalls"]) == 1 and
            (result["nativeSaveCalls"] if multi else result["nativeSaveCalls"]) == 1 and
            (result["newSavedSha256"] if multi else
             result["newSavedProjectSha256"]) == sha(WORKING) and
            sha(ORIGINAL) == SOURCE_SHA,
            "NATIVE_COPY_WORKER_FULL_MODEL_CONFIRMATION_MISSING")
    durable_write(folder / ("native-multi-copy-result.json" if multi
                           else "native-column-copy-result.json"), result)
    return dict(result,
                sourceTaskBlob=blob,
                modelWrites=2,
                workingPlnSaved=True,
                originalPlnUnchanged=True,
                historicalReconciliation=(
                    historical["status"] if historical else None),
                authorizedNativeExecution=True)


def capture_roof_review(job, folder):
    """One existing source-reviewed production preflight; no subprocess writes."""
    require(REVIEW.is_file(), "APPROVED_BDD_ROOF_REVIEW_NOT_INSTALLED")
    cmd = [sys.executable, str(REVIEW)]
    p = subprocess.run(cmd, capture_output=True, timeout=180,
                       encoding="utf-8", errors="replace", cwd=ROOT)
    log = folder / "review-output.txt"
    log.write_text(p.stdout + "\n" + p.stderr, encoding="utf-8")
    require(p.returncode == 0 and "MODEL_WRITES: 0" in p.stdout and
            "PUBLISHED:" in p.stdout, "BDD114_NATIVE_ROOF_PREFLIGHT_INCOMPLETE")
    statuses = [x.split("APA_STATUS:", 1)[1].strip()
                for x in p.stdout.splitlines() if x.startswith("APA_STATUS:")]
    require(len(statuses) == 1 and statuses[0] in (
        "ROOF_NATIVE_FACE_CLEAR_NORTH_JUNCTION_MATCHES_EXISTING",
        "ROOF_NATIVE_FACE_CONTACT_REQUIRES_DETAIL"),
        "BDD114_REVIEW_OUTPUT_UNEXPECTED")
    return {"status": "BDD114_PRODUCTION_PREFLIGHT_COMPLETE",
            "geometryStatus": statuses[0], "logSHA256": sha(log),
            "localLogPath": str(log), "modelWrites": 0,
            "nativeBuildExecuted": False,
            "next": "REVIEW_GEOMETRY_AND_APPROVE_VERIFIED_X_BEFORE_ONE_SCENEWRITER_BATCH"}


def capture_approved_bdd114_copy(job, folder):
    """Only user's fixed seven-stud request; original APA writes and SQLite."""
    # Retired entry point: even direct callers cannot revive an old remote
    # job using a compiled-in approval string. Use the scoped copy contract.
    raise ValueError("LEGACY_BDD_WRITE_RETIRED_LOCAL_SCOPED_GRANT_REQUIRED")


def require_native_copy_grant(job, folder, task_blob, authorization):
    """Both copy actions require a local grant bound to immutable source blobs."""
    require(ID.fullmatch(job["jobId"]) and job["action"] in
            {"APPROVED_NATIVE_COLUMN_COPY", "APPROVED_MULTI_PROTOTYPE_COPY"},
            "NATIVE_COPY_ACTION_REQUIRES_SCOPED_CONTRACT")
    grant_path = ROOT / "controller-grants" / (job["jobId"] + ".json")
    require(grant_path.is_file(), "NATIVE_COPY_LOCAL_EXPLICIT_GRANT_NOT_INSTALLED")
    grant = json.loads(grant_path.read_text(encoding="utf-8"))
    accepted_schema = {"APA_AC29_LOCAL_NATIVE_COPY_GRANT_V1"}
    if job["action"] == "APPROVED_MULTI_PROTOTYPE_COPY":
        accepted_schema.add("APA_AC29_LOCAL_NATIVE_MULTI_COPY_GRANT_V1")
    require(isinstance(grant, dict) and
            set(grant) == {"schema", "jobId", "jobBlobSha1", "taskBlobSha1",
                           "projectSha256", "authorizationRef"} and
            grant["schema"] in accepted_schema and
            grant["jobId"] == job["jobId"] and
            grant["jobBlobSha1"] ==
            json.loads((folder / "attempted.json").read_text(encoding="utf-8"))["sourceBlob"] and
            grant["taskBlobSha1"] == task_blob and
            grant["projectSha256"] == approved_saved_sha() and
            grant["authorizationRef"] == authorization,
            "NATIVE_COPY_EXPLICIT_LOCAL_APPROVAL_NOT_BOUND_TO_JOB_BLOB")
    return grant


def durable_write(path, obj):
    temp = path.with_suffix(".writing")
    with temp.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    temp.replace(path)


def upload_result(name, folder):
    report = folder / "result.json"
    require(report.is_file(), "NO_DURABLE_REPORT_TO_PUBLISH")
    marker = folder / "published.json"
    if marker.exists():
        return
    content = base64.b64encode(report.read_bytes()).decode("ascii")
    payload = {"branch": "main",
               "message": "APA AC29 one-shot source-qualified job result " + name,
               "content": content}
    manifest = folder / "upload.json"
    durable_write(manifest, payload)
    remote = f"{RESULTS}/{name}.json"
    result = gh_api(f"repos/{BRIDGE}/contents/{remote}", body=manifest)
    durable_write(marker, {"sha": result["content"]["sha"],
                           "url": result["content"]["html_url"]})
    print("PUBLISHED:", result["content"]["html_url"], flush=True)


def process_job(name):
    require(ID.fullmatch(name), "UNSAFE_JOB_ID")
    folder = STATE / name
    if folder.is_dir():
        # Never re-execute a previously attempted job; retry publication only.
        if (folder / "result.json").exists():
            upload_result(name, folder)
        return
    job, source_blob = remote_json(BRIDGE, f"{INBOX}/{name}.json", "main")
    validate_job(job, name)
    stable_preflight()
    folder.mkdir(parents=False, exist_ok=False)
    # Persistent intent before ANY Archicad command. Unknown outcome never
    # replays automatically, even if process dies during execution.
    durable_write(folder / "attempted.json", {
        "job": name, "sourceBlob": source_blob,
        "startedAt": current_utc().isoformat(), "action": job["action"],
        "automaticRetry": False, "currentProject": str(WORKING)})
    try:
        if job["action"] == "BDD114_ROOF_FINALIZE":
            response = capture_roof_review(job, folder)
        elif job["action"] == "CURRENT_MODEL_FINGERPRINT":
            response = capture_current_model_fingerprint(job, folder)
        elif job["action"] in ("APPROVED_NATIVE_COLUMN_COPY",
                                "APPROVED_MULTI_PROTOTYPE_COPY"):
            response = capture_approved_native_copy(job, folder)
        else:
            response = capture_read_task(job, folder)
        response["jobStatus"] = "COMPLETE"
    except Exception as e:
        response = {"jobStatus": "STOPPED_RECONCILE_NO_AUTORETRY",
                    "error": type(e).__name__ + ": " + str(e)[:400]}
    payload = {"schema": "APA_AC29_JOB_RESULT_V1",
               "jobId": name, "action": job["action"],
               "sourceBlob": source_blob,
               "finishedAt": current_utc().isoformat(),
               "result": response, "automaticRetry": False,
               "modelWritesAuthorized": response.get("authorizedNativeExecution") is True}
    durable_write(folder / "result.json", payload)
    upload_result(name, folder)


def poll_once():
    """One pass for queued jobs; no repeated native functional testing."""
    items = gh_api(f"repos/{BRIDGE}/contents/{INBOX}?ref=main")
    require(isinstance(items, list) and len(items) < 750,
            "JOB_INBOX_NOT_A_BOUNDED_LIST")
    jobs = sorted(item["name"][:-5] for item in items
                  if item.get("type") == "file" and
                  item["name"].endswith(".json") and
                  ID.fullmatch(item["name"][:-5]))
    for name in jobs:
        try:
            process_job(name)
        except Exception as e:
            print("JOB_PENDING_OR_BLOCKED:", name, type(e).__name__, str(e)[:200],
                  flush=True)
    return len(jobs)


def acquire_singleton():
    """Windows process lock; no duplicate autostart worker may execute jobs."""
    import msvcrt
    lock = STATE / ".single-instance.lock"
    file = lock.open("a+b")
    file.seek(0)
    try:
        file.write(b"\0")
        file.flush()
        file.seek(0)
        msvcrt.locking(file.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        file.close()
        raise RuntimeError("APA_BRIDGE_ALREADY_RUNNING")
    return file


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--loop", action="store_true", help="Persistent single worker")
    ap.add_argument('--healthcheck',action='store_true',help='Local integrity/import check; no inbox or Archicad calls')
    ap.add_argument("--interval-seconds", type=int, default=30)
    args = ap.parse_args()
    if args.healthcheck:
        stable_preflight()
        sys.path.insert(0,str(SCRIPTS))
        import archicad_project_accelerator as APA
        import apa_ac29_dynamic_native_verifiers as VERIFIERS
        import apa_ac29_multi_prototype_native_copy as MULTI
        require(callable(APA.run_scoped_native_task),'SCOPED_CORE_ENTRY_POINT_MISSING')
        require(set(VERIFIERS.installed_verifiers())=={
                    'VerifiedNativeColumns','VerifiedNativeTranslation',
                    'VerifiedNativeBasicBeam','VerifiedNativeBasicWall',
                    'VerifiedNativeBasicRoof','VerifiedBasicSlabMaterial'} and
                callable(MULTI.reconcile_existing_multi_task),
                'SCOPED_RUNTIME_DEPENDENCIES_MISSING')
        print('APA_BRIDGE_HEALTHCHECK_PASS_NO_NATIVE_CALLS',flush=True)
        return
    require(10 <= args.interval_seconds <= 3600, "BAD_POLL_INTERVAL")
    STATE.mkdir(parents=True, exist_ok=True)
    handle = acquire_singleton()
    try:
        durable_write(STATE/'receiver-started.json',{
            'pid':os.getpid(),'workerSHA256':sha(Path(__file__)),
            'startedAt':current_utc().isoformat(),'nativeCalls':0})
        while True:
            try:
                print("APA_BRIDGE_SCAN:", poll_once(), flush=True)
            except Exception as exc:
                print("APA_BRIDGE_OFFLINE_OR_BLOCKED:",
                      type(exc).__name__, str(exc)[:240], flush=True)
            if not args.loop:
                break
            time.sleep(args.interval_seconds)
    finally:
        handle.close()


if __name__ == "__main__":
    main()
