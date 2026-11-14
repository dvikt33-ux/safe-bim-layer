"""Adapt existing coordination and knowledge inputs to the common application."""

import hashlib
import json
from pathlib import Path
import re

from apa_release import read_json, read_release, sha256, verify_member


def arena_receipt(path, intent_path=None):
    raw = path.read_bytes()
    row = json.loads(raw.decode("utf-8-sig"))
    turn = row.get("turn_id")
    if (row.get("protocol") != 1 or row.get("kind") != "terminal_ack"
            or type(turn) is not int or turn < 1 or row.get("ack_verified") is not True
            or row.get("signal_status") != "done" or row.get("signal_target") != "NONE"
            or not re.fullmatch(r"[a-f0-9]{40}", row.get("signal_blob_sha", ""))):
        raise ValueError("Выберите квитанцию завершённого обмена Arena с терминальным ACK")
    receipt = {"status": "ARENA_TERMINAL_RECEIPT_IMPORTED", "turn": turn,
               "signalBlobSha1": row["signal_blob_sha"], "receiptSha256": hashlib.sha256(raw).hexdigest(),
               "source": row.get("source"), "reportMarker": row.get("report_marker"),
               "executionPermission": False}
    if intent_path is None:
        return receipt

    from apa import compile_plan, load_router

    intent_bytes = intent_path.read_bytes()
    intent = json.loads(intent_bytes.decode("utf-8-sig"))
    if not isinstance(intent, dict) or not isinstance(intent.get("schemaVersion"), str):
        raise ValueError("Для Arena нужен отдельный типизированный вход APA")
    plan = dict(compile_plan(load_router(), intent), executionPermission=False)
    return dict(receipt, status="ARENA_APA_PLAN_PREPARED",
                intentSchema=intent["schemaVersion"], intentSha256=hashlib.sha256(intent_bytes).hexdigest(),
                plan=plan)


def knowledge_query(root, cache, query, mode):
    from archicad_knowledge_access import KnowledgeAccess, PLAN

    release = read_release(root)
    verify_member(root, release, f"knowledge/{PLAN}")
    source = root / "knowledge"
    config = {"schema": "APA_KNOWLEDGE_ACCESS_V1", "enabled": True,
              "source_mode": "LOCAL_CHECKOUT", "repo_root": str(source), "cache_dir": str(cache),
              "code_root": str(root), "code_commit": release["revision"]}
    service = KnowledgeAccess(config)
    if not (Path(cache) / "apa-graph.json").is_file():
        service.rebuild()
    result = service.query(query, mode)
    return dict(result, releaseKnowledgeRevision=release["knowledgeRevision"], executionPermission=False)


def design_evidence(root, job, cache):
    """Apply the existing source-binding rules to one accepted authored model."""
    import archicad_normative_bindings as normative
    import apa_r03_architecture as architecture
    from apa_ac29_save_isolation import require

    job = job.resolve(strict=True)
    stage_path = job / "job.json"
    stage = read_json(stage_path)
    stage = architecture.check(job, Path(stage["original"]), stage["initialSHA256"])
    require("authoredIntentHash" in stage, "DESIGN_EVIDENCE_AUTHORED_JOB_REQUIRED")
    saved = architecture.saved_record(job, stage)
    status = "LIVE_ARCHITECTURE_SAVED_REOPENED_PASS"
    reopened_path = job / "reopened.json"
    require(architecture.status(job, stage)["status"] == status,
            "DESIGN_EVIDENCE_REOPEN_REQUIRED")
    reopened = read_json(reopened_path)
    require(reopened["status"] == status and reopened["reopenVerified"] is True
            and reopened["verificationNativeWrites"] == 0
            and all(reopened.get(key) == value for key, value in saved.items() if key != "status"),
            "DESIGN_EVIDENCE_SAVED_AND_REOPENED_DRIFT")

    build = job / "build"
    manifest = read_json(build / "SHA256.json")
    names = ("plan.json", "preflight.json", "result.json")
    require(all(isinstance(manifest.get(name), str) for name in names), "DESIGN_EVIDENCE_BUILD_HASHES_REQUIRED")
    plan, preflight, result = (_matching_json(build / name, manifest[name])[0] for name in names)
    intent, intent_sha = _matching_json(job / "intent.json", stage["intentSHA256"])
    approval = read_json(job / "approved-preflight.json")
    architecture.approved_result(job, approval)
    core, digest = architecture.A, architecture.R.digest
    require(intent["schemaVersion"] == "apa-authored-project/1" and plan["intent"] == intent
            and digest(intent) == stage["authoredIntentHash"] == plan["intentHash"] == result["intentHash"]
            and digest(plan["graph"]) == plan["sourcePlanHash"] == result["sourcePlanHash"]
            and plan["graph"] == preflight["graph"] and result["binding"] == preflight["binding"]
            and core.approval_hash(plan, preflight) == approval["confirmHash"] == result["confirmPlanHash"]
            and result["status"] == "COMPLETE_UNSAVED" and result["evidenceKind"] == "LIVE"
            and result["wholeAssemblyReadback"] is True and result["addedGuids"] == saved["addedGuids"]
            and result["requirements"] == plan["authoredCandidate"]["requirements"]
            and result.get("requirementReadback") == saved.get("requirementReadback"),
            "DESIGN_EVIDENCE_INTENT_PLAN_OR_EXECUTION_DRIFT")

    native_path = job / "native-before-save.json"
    native, native_sha = _matching_json(native_path)
    elements = {row["guid"].lower(): row for row in native["elements"]}
    guids = sorted(elements)
    require(len(guids) == len(native["elements"]) == saved["elementCount"]
            and digest(guids) == saved["finalGuidSetSHA256"]
            and architecture.group.fingerprint(native) == saved["finalBrepSHA256"],
            "DESIGN_EVIDENCE_NATIVE_GUID_OR_BREP_DRIFT")
    signatures = architecture.C.retained_geometry_signatures(native, guids)
    require(digest(signatures) == saved["finalSignaturesSHA256"], "DESIGN_EVIDENCE_NATIVE_SIGNATURE_DRIFT")
    targets = _design_window_junctions(plan["graph"], result["bimOperationReadback"], elements, saved["addedGuids"])

    brief = intent["brief"]
    pack = core.compile_project_library_pack(brief, intent["cseCandidate"])
    context = dict(units=native["units"], coordinateSystem=native["coordinateSystem"], elements=elements,
                   nativeGeometrySignatures=signatures)
    binding = core.compile_project_normative_pack(brief, pack, context, {}, targets)
    references = []
    for reference in binding["normative"]["registry"]["researchSources"]:
        source = knowledge_query(root, cache, reference["id"], "research")
        hit = next((item for item in source.get("items", ()) if item.get("id") == reference["id"]), {})
        references.append(dict(reference, uri=hit.get("uri"), registryVerification=hit.get("verification"),
                               status="REGISTERED_RESEARCH_REFERENCE" if hit.get("uri") else "SOURCE_NOT_RESOLVED",
                               planSha256=source.get("plan_sha256"), releaseRevision=source.get("releaseKnowledgeRevision")))
    return dict(status="DESIGN_NATIVE_NORMATIVE_EVIDENCE_LINKED", projectId=brief["projectId"],
                evidenceKind="ARCHIVED_NATIVE_REOPEN_READBACK", nativeJunctions=targets,
                requirements=core.requirement_readback(result),
                knowledge=dict(references=references, normativeAuthority=False,
                               status="REFERENCES_RESOLVED" if all(row["uri"] for row in references)
                               else "REFERENCES_INCOMPLETE"),
                provenance=dict(intentSha256=intent_sha, planSha256=manifest["plan.json"],
                                resultSha256=manifest["result.json"], nativeDumpSha256=native_sha,
                                reopenedReceiptSha256=sha256(reopened_path), savedPlnSha256=saved["savedSHA256"],
                                guidSetSha256=saved["finalGuidSetSHA256"], brepSha256=saved["finalBrepSHA256"],
                                briefInputDigest=binding["normative"]["briefInputDigest"],
                                ruleCatalogSha256=sha256(normative.CATALOG)),
                executionPermission=False, nativeCalls=0, **binding)


def _matching_json(path, expected=None):
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if expected is not None and expected != digest:
        raise ValueError("DESIGN_EVIDENCE_INPUT_HASH_MISMATCH:" + path.name)
    return json.loads(raw.decode("utf-8-sig")), digest


def _design_window_junctions(graph, readback, elements, added_guids):
    from apa_ac29_save_isolation import require

    by_id = {step["id"]: step for step in graph["operations"]}
    added = set(added_guids)

    def bound(operation_id, kind):
        row = readback.get(operation_id, {})
        guid = str(row.get("guid", "")).lower()
        element = elements.get(guid, {})
        require(row.get("status") == "PASS" and row.get("kind") == kind and guid in added
                and element.get("type") == kind and bool(element.get("bodies")),
                "DESIGN_EVIDENCE_OPERATION_READBACK_REQUIRED:" + operation_id)
        return guid, element

    targets = []
    for step in by_id.values():
        if step["command"] != "CreateWindows":
            continue
        window_id = step["id"]
        rows = step["params"]["windowsData"]
        require(len(rows) == 1, "DESIGN_EVIDENCE_REQUIRES_ONE_WINDOW_PER_OPERATION")
        wall_id = rows[0]["ownerWallId"]["guid"].get("$createdGuid")
        require(wall_id in by_id and by_id[wall_id]["command"] == "CreateWalls",
                "DESIGN_EVIDENCE_WINDOW_REQUIRES_PLANNED_WALL")
        window_guid, window = bound(window_id, "Window")
        wall_guid, wall = bound(wall_id, "Wall")
        host_guid = window.get("relationships", {}).get("hostGuid")
        require(isinstance(host_guid, str) and host_guid.lower() == wall_guid
                and window["homeStory"] == wall["homeStory"], "DESIGN_EVIDENCE_HOSTED_WINDOW_MISMATCH")
        targets.append(dict(id="junction-" + window_id, family="wall_window", guids=[wall_guid, window_guid],
                            bimOperationIds=[wall_id, window_id], relation="VERIFIED_NATIVE_WINDOW_HOST"))
    require(bool(targets), "DESIGN_EVIDENCE_VERIFIED_HOSTED_WINDOW_REQUIRED")
    return targets


def architecture_phase(root, job, phase, port, *, confirm_preflight=None, output=None, discover_port=False,
                       expected_stage_sha=None):
    import apa_r03_architecture as architecture
    from apa_mailbox_profile import APX

    job = job.resolve(strict=True)
    recorded = read_json(job / "job.json")
    donor = Path(recorded["original"]).resolve(strict=True)
    manifest = architecture.check(job, donor, recorded["initialSHA256"])
    if expected_stage_sha is not None and (
            sha256(job / "job.json") != expected_stage_sha or manifest != recorded):
        raise ValueError("APA_ARCHITECTURE_MCP_STAGE_DRIFT")
    if phase == "status":
        return architecture.status(job, manifest)
    release = read_release(root)
    native = read_json(verify_member(root, release, "native/binary-receipt.json"))["binary"]
    if sha256(APX) != native["apxSHA256"]:
        raise ValueError("Установленный APX отличается от проверенного комплекта APA")
    pinned = (native["sourceRevision"], native["buildIdentity"])
    if discover_port:
        from apa_r03_mailbox import open_test_port

        if port is not None or phase not in {"native-read", "preflight", "verify-reopen"}:
            raise ValueError("APA_ARCHITECTURE_PORT_DISCOVERY_PHASE_INVALID")
        port = open_test_port(Path(manifest["project"]))
        if port is None:
            raise ValueError("APA_ARCHITECTURE_EXACT_TEST_PLN_NOT_OPEN_OR_API_UNAVAILABLE")
    if phase == "native-read":
        return architecture.read_native(job, manifest, port or manifest["port"], pinned, output)
    from apa_r03_mailbox import listener

    if phase == "preflight":
        return architecture.preflight(job, manifest, port or manifest["port"], pinned,
                                      local_listener=listener)
    if phase == "verify-reopen":
        approved = read_json(job / "approved-preflight.json")
        return architecture.verify_reopen(job, manifest, pinned, port or approved["port"])
    if port is not None:
        raise ValueError("Исполнение использует порт сохранённого предконтроля")
    if phase == "check-closed":
        return architecture.check_closed(job, manifest, pinned)
    if phase == "execute" and architecture.status(job, manifest)["status"] in {
            "LIVE_ARCHITECTURE_SAVED_PENDING_REAL_REOPEN", "LIVE_ARCHITECTURE_SAVED_REOPENED_PASS"}:
        return architecture.execute(job, manifest, pinned, confirm_preflight=confirm_preflight)
    approval = read_json(job / "approved-preflight.json")
    if not approval.get("listener") or listener(approval["port"]) != approval["listener"]:
        raise ValueError("APA_ARCHITECTURE_PREFLIGHT_PROCESS_DRIFT")
    return architecture.execute(job, manifest, pinned, confirm_preflight=confirm_preflight)
