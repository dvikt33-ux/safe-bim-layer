"""Reuse Wall.Ensure decisions and journal an approved AI_TRACE delta in APA."""

import importlib.util
import hashlib
import json
from pathlib import Path
import re
from uuid import uuid4

from apa_ac29_save_isolation import ScratchWriteLease, copy_exclusive, require, write_new_json
from apa_release import MANIFEST, read_json, read_release, sha256, verify_member


VENDOR = "local-components/tdk_wall_ensure.py"
READS = frozenset({"GetElementsByType", "GetAddOnVersion",
                   "GetFavoritesByType", "GetAllProperties", "GetPropertyValuesOfElements",
                   "GetDetailsOfElements"})
GUID = re.compile(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}", re.IGNORECASE)
TRACE_SCHEMA = "APA_TDK_TRACE_TEST_COPY_V1"
SET_TRACE = "SetPropertyValuesOfElements"


def vendor_module(root):
    release = read_release(root)
    if VENDOR not in release["files"]:
        raise ValueError("Для Wall.Ensure нужен локальный Windows-комплект с компонентом TDK")
    path = verify_member(root, release, VENDOR)
    spec = importlib.util.spec_from_file_location("apa_packaged_tdk_wall_ensure", path)
    vendor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(vendor)
    return vendor


class ReadOnlyTransport:
    def __init__(self, router, api, product):
        self.router = router
        self.evidence_api = api
        self.product = product

    def api(self, command, parameters=None, *, mutation=False):
        if mutation:
            raise ValueError(f"Wall.Ensure запросил запись в режиме сверки: {command}")
        if command == "API.GetProductInfo":
            return self.product
        if command == "API.GetElementsByType":
            command = "GetElementsByType"
        if command not in READS or self.router.operation_kind(command) != "READ_ONLY":
            raise ValueError(f"Команда Wall.Ensure вне области чтения APA: {command}")
        ticket = self.router.prepare(command, parameters or {})
        return self.router.read(self.evidence_api, ticket, reviewed_read_only=True)

    tapir = api


def trace_delta(runtime, payload, desired_hash, decision):
    if decision.get("status") != "WOULD_UPDATE_TRACE" or decision.get("dryRun") is not True:
        return None
    guid = decision["guid"]
    if not GUID.fullmatch(guid):
        raise ValueError("TDK_WALL_TRACE_TARGET_GUID_REQUIRED")
    values = runtime.trace_values(payload, desired_hash)
    changes = decision["traceDelta"]
    rows, seen = [], set()
    for name in sorted(changes):
        value = values.get(name)
        prop = runtime.properties.get(name, {})
        identity = prop.get("propertyId", {})
        key = identity.get("guid", "").lower()
        if (not GUID.fullmatch(key) or key in seen or not isinstance(value, str)
                or changes[name]["desired"] != value
                or prop.get("propertyGroupName") != "AI_TRACE"
                or prop.get("propertyName") != name
                or prop.get("propertyCollectionType") != "Single"
                or prop.get("propertyValueType") != "String"
                or prop.get("propertyIsEditable") is not True
                or prop.get("isExpressionBased") is True):
            raise ValueError("TDK_WALL_TRACE_PROPERTY_DEFINITION_DRIFT:" + name)
        seen.add(key)
        rows.append(dict(elementId={"guid": guid}, propertyId={"guid": identity["guid"]},
                         propertyValue={"value": value}))
    if not rows:
        raise ValueError("TDK_WALL_TRACE_DELTA_REQUIRED")
    return {"elementPropertyValues": rows}


def trace_candidate(router, runtime, payload, desired_hash, decision):
    """Compile the TDK-owned AI_TRACE values into APA's existing native graph."""
    from archicad_project_accelerator import prepare_native_task

    parameters = trace_delta(runtime, payload, desired_hash, decision)
    if parameters is None:
        return None
    router.review_policy(SET_TRACE, "MODIFY", "MODEL", {
        "source": "TDK Wall.Ensure AI_TRACE definitions and pinned Tapir contract",
        "sha256": router.contract_hash(SET_TRACE),
    })
    intent = dict(schemaVersion="apa-native-task/1",
                  request="Синхронизировать AI_TRACE для проверенного GUID стены",
                  graph={"operations": [dict(id="tdk-trace", command=SET_TRACE, params=parameters)]})
    return dict(prepare_native_task(router, intent), executionPermission=False)


def wall_runtime(router, core, vendor, api, journal):
    for command in READS:
        router.review_policy(command, "READ_ONLY", "READ_ONLY",
                             {"source": "TDK Wall.Ensure fixed read calls and pinned Tapir 1.5.10 export",
                              "sha256": router.contract_hash(command)})
    return vendor.WallEnsureRuntime(ReadOnlyTransport(router, api, core.archicad29(api)),
                                    vendor.Journal(journal), core.RUN.EXPECTED_TAPIR, 29)


def inspect_wall(root, payload_path, profile_path=None, journal_path=None, evidence_dir=None):
    vendor = vendor_module(root)
    raw = payload_path.read_bytes()
    payload = json.loads(raw.decode("utf-8-sig"))
    desired = vendor.validate_payload(payload)
    # Reject non-finite vendor numbers before passing data to the BIM contracts.
    json.dumps(desired, allow_nan=False)
    receipt = {"status": "TDK_WALL_PAYLOAD_NORMALIZED", "operationId": payload["operationId"],
               "payloadSha256": hashlib.sha256(raw).hexdigest(), "desiredState": desired,
               "desiredStateSha256": vendor.state_hash(desired), "executionPermission": False,
               "nativeCalls": 0, "modelWrites": 0}
    if profile_path is None:
        return receipt

    from apa import load_router
    from apa_mailbox_profile import PackageProfile
    import archicad_project_accelerator as core

    profile = PackageProfile(root, profile_path)
    evidence_dir.mkdir()
    core.RUN.bind_authorized_saved_copy(profile.port, str(profile.working), profile.working.stem,
                                        profile.saved["savedSHA256"], "APA_TDK_WALL_READ_ONLY_PROFILE")
    api = core.EvidenceAPI(core.native_transport, evidence_dir, execute=False)
    profile.check_native(api)
    expected_guids = core.inventory_guids(api)
    if len(expected_guids) != profile.guid_count or core.RUN.digest(sorted(expected_guids)) != profile.saved["finalGuidSetSHA256"]:
        raise ValueError("GUID открытой PLN отличаются от подтверждённой копии")
    router = load_router()
    runtime = wall_runtime(router, core, vendor, api, journal_path or evidence_dir / "tdk-journal.jsonl")
    decision = runtime.ensure(payload, commit=False)
    if api.write_attempts or core.inventory_guids(api) != expected_guids:
        raise ValueError("Состав модели изменился при сверке Wall.Ensure")
    profile.check_model_files()
    return dict(receipt, status="TDK_WALL_READBACK_PREVIEW", decision=decision,
                traceCandidate=trace_candidate(router, runtime, payload, receipt["desiredStateSha256"], decision),
                nativeCalls=sum(api.calls.values()))


def trace_source(payload, vendor):
    desired = vendor.validate_payload(payload)
    json.dumps(desired, allow_nan=False)
    return vendor.state_hash(desired)


def stage_trace(root, folder, source, payload_path):
    folder = folder.resolve()
    source = source.resolve(strict=True)
    require(re.fullmatch(r"tdk-[a-z0-9-]{5,44}", folder.name) and source.suffix.casefold() == ".pln"
            and source.is_file() and not source.is_relative_to(folder), "TDK_TRACE_NEW_TEST_FOLDER_REQUIRED")
    trace_source(read_json(payload_path), vendor_module(root))
    initial = sha256(source)
    folder.mkdir()
    scratch = folder / "TDK-AI-TRACE-test.pln"
    copy_exclusive(source, scratch)
    copy_exclusive(payload_path, folder / "wall.json")
    require(sha256(scratch) == sha256(source) == initial, "TDK_TRACE_COPY_SHA_DRIFT")
    release = read_release(root)
    manifest = dict(schema=TRACE_SCHEMA, id=folder.name, project=str(scratch), source=str(source),
                    projectSha256=initial, sourceSha256=initial, payloadSha256=sha256(folder / "wall.json"),
                    releaseRevision=release["revision"], releaseSha256=sha256(root / MANIFEST),
                    authorization="USER_APPROVED_APA_TDK_" + folder.name)
    write_new_json(folder / "trace-stage.json", manifest)
    return dict(manifest, status="TDK_TRACE_TEST_COPY_STAGED", nativeCalls=0)


def trace_snapshot(api, scratch):
    import apa_ac29_group_batch_oneshot as group

    ids, model = group.capture({"scratch": str(scratch)}, api)
    return ids, group.C.retained_geometry_signatures(model, ids)


def run_trace(root, folder, port, *, confirm=None):
    """Review or apply one AI_TRACE-only delta through the existing SceneWriter."""
    from apa import load_router
    from apa_ac29_group_batch_oneshot import IDENTITY
    from apa_mailbox_profile import APX
    from apa_r03_architecture import runtime_identity
    import archicad_project_accelerator as core

    folder = folder.resolve(strict=True)
    stage_path = folder / "trace-stage.json"
    stage_sha = sha256(stage_path)
    stage = read_json(stage_path)
    project = folder / "TDK-AI-TRACE-test.pln"
    donor = Path(stage["source"])
    release = read_release(root)
    def intact():
        require(sha256(stage_path) == stage_sha and sha256(project) == sha256(donor) == stage["projectSha256"]
                and sha256(folder / "wall.json") == stage["payloadSha256"], "TDK_TRACE_INPUT_BYTES_DRIFT")

    require(stage["schema"] == TRACE_SCHEMA and stage["id"] == folder.name and stage["project"] == str(project)
            and project.resolve() == project and not project.samefile(donor)
            and stage["sourceSha256"] == stage["projectSha256"]
            and stage["authorization"] == "USER_APPROVED_APA_TDK_" + folder.name
            and stage["releaseRevision"] == release["revision"] and stage["releaseSha256"] == sha256(root / MANIFEST)
            and type(port) is int and 19723 <= port <= 19743, "TDK_TRACE_TEST_SCOPE_DRIFT")
    intact()
    plan_path = folder / "trace-preflight.json"
    attempt = folder / "trace-attempted.json"
    ledger = folder / "scene-v1-attempts.sqlite3"
    require(not attempt.exists() and not ledger.exists()
            and not Path(str(project) + ".apa-write.lock").exists(), "TDK_TRACE_ATTEMPT_EXISTS_NO_REPLAY")
    if confirm is None:
        require(not plan_path.exists(), "TDK_TRACE_PREFLIGHT_ALREADY_EXISTS")
    else:
        require(sha256(plan_path) == confirm, "TDK_TRACE_PREFLIGHT_SHA_MISMATCH")
    native = read_json(verify_member(root, release, "native/binary-receipt.json"))["binary"]
    require(sha256(APX) == native["apxSHA256"], "TDK_TRACE_APX_DRIFT")
    pins = native["sourceRevision"], native["buildIdentity"]
    core.RUN.bind_authorized_saved_copy(port, str(project), project.stem, stage["projectSha256"],
                                        stage["authorization"])
    trace = folder / ("dispatch-" + uuid4().hex)
    trace.mkdir()
    api = core.EvidenceAPI(core.native_transport, trace, execute=False)
    IDENTITY.current_project(api, str(project))
    pinned_runtime = runtime_identity(api, pins)
    vendor = vendor_module(root)
    payload = read_json(folder / "wall.json")
    desired_hash = trace_source(payload, vendor)
    router = load_router()
    runtime = wall_runtime(router, core, vendor, api, trace / "tdk-read-journal.jsonl")
    decision = runtime.ensure(payload, commit=False)
    candidate = trace_candidate(router, runtime, payload, desired_hash, decision)
    if candidate is None:
        require(confirm is None and api.write_attempts == 0, "TDK_TRACE_PRECONDITIONS_CHANGED")
        return dict(status="TDK_TRACE_NO_MUTATION_PLAN", decision=decision, nativeWrites=0, plnSaved=False)
    router.probe_runtime(api, SET_TRACE)
    ids, signatures = trace_snapshot(api, project)
    require(decision["guid"].lower() in signatures, "TDK_TRACE_TARGET_MISSING_FROM_FULL_NATIVE_MODEL")
    before = dict(stageSha256=stage_sha, port=port, runtime=pinned_runtime, candidate=candidate, decision=decision,
                  guidSetSha256=core.RUN.digest(ids), signaturesSha256=core.RUN.digest(signatures),
                  desiredStateSha256=desired_hash)
    intact()
    require(api.write_attempts == 0, "TDK_TRACE_PREFLIGHT_MUTATION")
    if confirm is None:
        write_new_json(plan_path, before)
        return dict(status="TDK_TRACE_READY_FOR_EXPLICIT_TEST_RUN", preflightSha256=sha256(plan_path),
                    targetGuid=decision["guid"], traceDelta=decision["traceDelta"], nativeWrites=0, plnSaved=False)
    require(read_json(plan_path) == before, "TDK_TRACE_NATIVE_PREFLIGHT_DRIFT")
    lease = ScratchWriteLease(project, folder, stage["projectSha256"])
    lease.acquire()
    write_new_json(attempt, dict(status="ONE_SHOT_RESERVED", preflightSha256=confirm, automaticRetry=False))
    step, = candidate["workflow"]["graph"]["operations"]
    target = decision["guid"].lower()
    writer = core.RUN.SceneWriter(api, ledger, allow_3d_view_for_write=True)

    def verify_before(live):
        require(lease.verify() and sha256(plan_path) == confirm, "TDK_TRACE_RESERVATION_DRIFT")
        intact()
        require(runtime_identity(live, pins) == pinned_runtime, "TDK_TRACE_APX_RUNTIME_DRIFT")
        fresh = runtime.ensure(payload, commit=False)
        require(fresh == decision and trace_delta(runtime, payload, desired_hash, fresh) == step["params"]
                and trace_snapshot(live, project) == (ids, signatures), "TDK_TRACE_NATIVE_SCOPE_DRIFT")
        return {"status": "TDK_TRACE_PREWRITE_PASS"}

    def verify_after(reply, _):
        require(reply["executionResults"] == [{"success": True}] * len(step["params"]["elementPropertyValues"]),
                "TDK_TRACE_RESULT_COUNT_OR_VALUE_MISMATCH")
        fresh = runtime.ensure(payload, commit=False)
        require(fresh["status"] == "NO_CHANGE" and fresh["guid"].lower() == target
                and fresh["desiredHash"] == desired_hash and trace_snapshot(api, project) == (ids, signatures),
                "TDK_TRACE_VALUE_OR_GEOMETRY_READBACK_DRIFT")
        intact()
        return {"status": "TDK_TRACE_GUID_BREP_AND_VALUES_PASS", "targetGuid": target}

    scope = dict(scene_id="TdkTrace-" + confirm[:20], affected=[target], authorization=stage["authorization"],
                 retained_signatures={g: value for g, value in signatures.items() if g != target},
                 saved_sha256=stage["projectSha256"], impact="MODEL",
                 verify_before=verify_before, verify_after=verify_after)
    try:
        result = core.run_native_task(router, api, candidate, writer, {step["id"]: scope})
    except Exception as exc:
        result = dict(status="STOPPED_UNKNOWN_OUTCOME", error=type(exc).__name__ + ": " + str(exc))
    complete = result["status"] == "WORKFLOW_CALLABLE_VERIFIED" and api.write_attempts == 1
    receipt = dict(status="TDK_TRACE_READBACK_PASS" if complete else "STOPPED_RECONCILE_NO_AUTORETRY",
                   result=result, nativeWrites=api.write_attempts, plnSaved=False, automaticRetry=False)
    write_new_json(folder / "trace-result.json", receipt)
    return receipt
