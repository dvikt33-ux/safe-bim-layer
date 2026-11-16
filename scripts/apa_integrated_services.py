"""Adapt existing coordination and knowledge inputs to the common application."""

from collections import Counter
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


def detail_review(root, detail_id, observation=None, host_guid=None):
    """Recompile a source-dimensioned Beam preview without acquiring a writer target."""
    import archicad_connected_components as connected
    from archicad_native_beam_details import source_cross_section

    candidate = connected.details_candidate(root, detail_id)
    report = dict(status="DETAIL_SOURCE_REVIEWED", source=candidate, nativeWrites=0,
                  executionPermission=False, assemblyWriteAllowed=False)
    if observation is None:
        if host_guid is not None:
            raise ValueError("DETAIL_HOST_REQUIRES_OBSERVATION")
        return report

    observed, source_sha = _matching_json(observation)
    if (observed.get("schema") != "APA_LIVE_ROOF_SOURCE_SECTION_NONEXECUTABLE_PREVIEW"
            or observed.get("sourceDetailId") != detail_id or observed.get("nativeWrites") != 0
            or observed.get("sourceCommitAllowed") is not False
            or observed.get("preflightAuthority") != "READ_ONLY_OBSERVED_PROJECT_NO_ACCEPTED_WRITE_RELEASE"):
        raise ValueError("DETAIL_READ_ONLY_OBSERVATION_REQUIRED")
    matches = [row for row in observed["rows"]
               if row.get("beamPreviewStatus") == "OFFLINE_NATIVE_BEAM_SOURCE_GRAPH_PREPARED"
               and (host_guid is None or row.get("hostGuid", "").casefold() == host_guid.casefold())]
    if len(matches) != 1:
        raise ValueError("DETAIL_OBSERVED_BEAM_HOST_NOT_UNIQUE")
    row = matches[0]
    if not connected.RUN._GUID.fullmatch(row.get("hostGuid", "")):
        raise ValueError("DETAIL_OBSERVED_BEAM_HOST_INVALID")
    section = source_cross_section(candidate, observed["entityId"], row["sourceFactId"])
    params = row["beamParams"]
    if section != row.get("sourceSection") or any(params.get(key) != value for key, value in section.items()):
        raise ValueError("DETAIL_OBSERVED_BEAM_SECTION_MISMATCH")
    graph = {"operations": [{"id": "detail-source-beam", "command": "CreateBeams", "params": {"beamsData": [params]}}]}
    catalog = connected.A.catalog_with_provenance(connected.RUN.DEFAULT_SCENE_SCHEMA)
    checked = connected.A.SCENE.GRAPH.compile_graph(catalog, graph, runtime_version=connected.RUN.EXPECTED_TAPIR)
    if checked["status"] != "PLAN_VALIDATED_OFFLINE":
        raise ValueError("DETAIL_OBSERVED_BEAM_GRAPH_REFUSED:" + checked["status"])
    return dict(report, status="DETAIL_BEAM_PREVIEW_REVALIDATED", observationSha256=source_sha,
                observedHostGuid=row["hostGuid"], sourceFactId=row["sourceFactId"], sourceSectionMeters=section,
                observedHostStatus="ARCHIVED_READ_ONLY_OBSERVATION", graph=graph,
                sourcePlanHash=checked["sourcePlanHash"], sourceAssemblyApplicability="UNVERIFIED",
                nativeContactAndMaterials="PENDING_EXACT_PROJECT_READBACK")


def _verified_authored_job(job):
    """Read the same intent, assembly and persisted geometry used for acceptance."""
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
    if "authoredStoryBindings" in stage:
        stories = stage["authoredStoryBindings"]
        actual = {guid: elements[guid]["homeStory"] for guid in saved["addedGuids"]}
        counts = {str(index): count for index, count in Counter(actual.values()).items()}
        require(stories == result.get("authoredStoryBindings") == saved["authoredStoryBindings"]
                and actual == result.get("bimHomeStories")
                and counts == saved.get("elementCountsByStory")
                and set(counts) == {str(row["nativeIndex"]) for row in stories},
                "DESIGN_EVIDENCE_NATIVE_STORY_BINDING_DRIFT")
    provenance = dict(intentSha256=intent_sha, planSha256=manifest["plan.json"], resultSha256=manifest["result.json"],
                      nativeDumpSha256=native_sha, reopenedReceiptSha256=sha256(reopened_path),
                      savedPlnSha256=saved["savedSHA256"], guidSetSha256=saved["finalGuidSetSHA256"],
                      brepSha256=saved["finalBrepSHA256"])
    return intent, plan, result, native, signatures, reopened, provenance


def design_evidence(root, job, cache):
    """Apply the existing source-binding rules to one accepted authored model."""
    import archicad_normative_bindings as normative
    import archicad_project_accelerator as core

    intent, plan, result, native, signatures, _, provenance = _verified_authored_job(job)
    elements = {row["guid"].lower(): row for row in native["elements"]}
    targets = _design_window_junctions(plan["graph"], result["bimOperationReadback"], elements, result["addedGuids"])

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
                provenance=dict(provenance,
                                briefInputDigest=binding["normative"]["briefInputDigest"],
                                ruleCatalogSha256=sha256(normative.CATALOG)),
                executionPermission=False, nativeCalls=0, **binding)


def document_reopened_job(job, destination, story=None, *, publisher_folder=None, layout_name=None):
    """Publish existing BIM facts for the accepted operation GUIDs in one job."""
    from apa_ac29_save_isolation import require, write_new_json
    from archicad_bim_documentation import bundle, make_snapshot, write_package
    from archicad_bim_graph import CREATES
    from archicad_project_accelerator import requirement_readback
    from apa_high_density_readonly_v2 import STABLE

    require((publisher_folder is None) == (layout_name is None), "DOCUMENTATION_PUBLISHER_FOLDER_AND_LAYOUT_REQUIRED")
    job, destination = job.resolve(strict=True), destination.resolve()
    require(destination.parent.is_dir() and not destination.exists()
            and not destination.is_relative_to(job) and not destination.is_relative_to(STABLE.resolve()),
            "DOCUMENTATION_JOB_REQUIRES_NEW_DIRECTORY_OUTSIDE_HISTORY")
    from apa_ac30_native import Job as AC30Job, SCHEMA as AC30_SCHEMA

    manifest_path = job / "job.json"
    if manifest_path.is_file() and read_json(manifest_path).get("schema") == AC30_SCHEMA:
        require(publisher_folder is None, "AC30_PUBLISHER_LINKED_LAYOUT_NOT_QUALIFIED")
        return AC30Job(job).documentation(destination, story)
    intent, plan, result, native, signatures, reopened, provenance = _verified_authored_job(job)
    require(reopened.get("reopenedGuids") == sorted(signatures), "DOCUMENTATION_REOPENED_GUIDS_NOT_VERIFIED")
    selected = result["addedGuids"]
    elements = {row["guid"].lower(): row for row in native["elements"]}
    readback = result["bimOperationReadback"]
    operations = {op["id"]: op for op in plan["graph"]["operations"]}
    require(selected and set(readback) == operations.keys() and len(set(selected)) == len(selected)
            and set(selected) <= elements.keys(), "DOCUMENTATION_OPERATION_SCOPE_INCOMPLETE")
    bound = {}
    for key, operation in operations.items():
        row = readback[key]
        guid, kind = row["guid"].lower(), CREATES.get(operation["command"])
        require(guid in selected and kind is not None and row["status"] == "PASS"
                and row["kind"] == elements[guid]["type"] == kind, "DOCUMENTATION_BIM_READBACK_MISMATCH:" + key)
        bound[key] = guid
    segments = result.get("ownedColumnSegments", {})
    children = set()
    for parent, guids in segments.items():
        for guid in guids:
            require(parent in bound.values() and elements[parent]["type"] == "Column"
                    and guid in selected and guid not in children and elements[guid]["type"] == "ColumnSegment"
                    and elements[guid].get("relationships", {}).get("hostGuid", "").lower() == parent,
                    "DOCUMENTATION_COLUMN_SEGMENT_BINDING_MISMATCH")
            children.add(guid)
    require(len(set(bound.values())) == len(bound) and set(bound.values()) | children == set(selected),
            "DOCUMENTATION_UNEXPLAINED_OPERATION_GUIDS")

    occupied = sorted({elements[guid]["homeStory"] for guid in selected})
    stories = occupied if story is None else [story]
    require(set(stories) <= set(occupied), "DOCUMENTATION_STORY_OUTSIDE_VERIFIED_ASSEMBLY")
    story_indices = set(stories)
    document_guids = [guid for guid in selected if elements[guid]["homeStory"] in story_indices]
    document_guid_set = set(document_guids)
    document_operations = {sid: guid for sid, guid in bound.items() if guid in document_guid_set}
    requirements = requirement_readback(result)
    if story is not None:
        requirements = [row for row in requirements if row["operations"]
                        and row["operations"].keys() <= document_operations.keys()]
    snapshot = make_snapshot(native, document_guids)
    package = bundle(snapshot, stories[0])
    plans = {str(stories[0]): package["plan"]}
    plans.update({str(index): bundle(snapshot, index)["plan"] for index in stories[1:]})
    package.update(plansByStory=plans,
                   projectId=intent["projectId"], operationGuids=document_operations,
                   requirements=requirements, provenance=provenance)
    if "authoredStoryBindings" in reopened:
        package["authoredStoryBindings"] = [row for row in reopened["authoredStoryBindings"]
                                            if row["nativeIndex"] in stories]
        package["specificationsByStory"] = {
            index: dict(sorted(Counter(row["nativeType"] for row in plan_row["elements"]).items()))
            for index, plan_row in plans.items()
        }
    if "wallSystems" in result:
        wall_systems = result["wallSystems"]
        require(reopened.get("reopenedWallSystemsVerified") is True
                and wall_systems == reopened.get("wallSystems")
                and reopened.get("wallSystemPlanSHA256") == provenance["planSha256"]
                and all(bound.get(sid) == row["guid"].lower() for sid, row in wall_systems["readback"].items()),
                "DOCUMENTATION_REOPENED_WALL_SYSTEM_READBACK_REQUIRED")
        package["wallSystems"] = dict(wall_systems, readback={sid: row for sid, row in wall_systems["readback"].items()
                                                            if sid in document_operations})
        coordination = plan["authoredCandidate"].get("wallCoordination", [])
        package["wallDesignCoordination"] = (coordination if story is None else [row for row in coordination
                                            if "native-" + row["wallMemberId"] in document_operations])
    if publisher_folder is not None:
        from archicad_native_documentation import read_two_storey_sheet

        bindings = package.get("authoredStoryBindings", [])
        require(story is None and len(stories) == len(bindings) == 2
                and reopened.get("reopenedStoryBindingsVerified") is True,
                "DOCUMENTATION_PUBLISHER_REQUIRES_TWO_REOPENED_STORIES")
        labels = [row["label"] for row in sorted(bindings, key=lambda row: row["nativeIndex"])]
        sheet, pdf = read_two_storey_sheet(publisher_folder, layout_name, labels)
        package["publisherSheet"] = dict(sheet, file="лист.pdf")
    write_package(package, destination)
    if publisher_folder is not None:
        with (destination / "лист.pdf").open("xb") as handle:
            handle.write(pdf)
    files = {path.name: sha256(path) for path in sorted(destination.iterdir())}
    if publisher_folder is not None:
        require(files["лист.pdf"] == sheet["sourceFile"]["sha256"], "DOCUMENTATION_PUBLISHER_COPY_SHA_DRIFT")
    receipt = dict(status="REOPENED_ASSEMBLY_DOCUMENTATION_WRITTEN", jobId=job.name,
                   modelVersion=package["modelVersion"], stories=stories, elementCount=len(document_guids),
                   specifications={key: row["count"] for key, row in package["specifications"].items()},
                   provenance=provenance, files=files, nativeCalls=0, modelWrites=0)
    if "specificationsByStory" in package:
        receipt["specificationsByStory"] = package["specificationsByStory"]
    if "publisherSheet" in package:
        receipt["publisherSheet"] = package["publisherSheet"]
    write_new_json(destination / "receipt.json", receipt)
    return receipt


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


def design_stair_readback(root, intent_path, variant, requirement, bindings_path, project, project_sha, port, output):
    """Inspect one existing stair on an exact open test copy, without saving it."""
    import apa_project_design as design
    import apa_r03_architecture as architecture
    from apa_r03_mailbox import listener
    from apa_ac29_save_isolation import require
    from apa_mailbox_profile import APX
    from archicad_native_stair_connection import verify_planned_connection
    from archicad_semantic_brief import resolve_stories

    project = project.resolve(strict=True)
    require(project.suffix.lower() == ".pln" and not output.exists()
            and re.fullmatch(r"[a-f0-9]{64}", project_sha) and sha256(project) == project_sha,
            "STAIR_READBACK_EXACT_PLN_AND_NEW_OUTPUT_REQUIRED")
    intent, intent_sha = _matching_json(intent_path)
    bindings, bindings_sha = _matching_json(bindings_path)
    report = design.compile_design(intent)
    candidate = next((row.get("candidate") for row in report["variants"] if row["id"] == variant), None)
    require(candidate and report["brief"]["targetProjectPath"] == str(project)
            and any(row["requirementId"] == requirement for row in candidate.get("stairConnections", [])),
            "STAIR_READBACK_REQUIRES_EXACT_DESIGN_TARGET_AND_LINK")
    release = read_release(root)
    pinned = read_json(verify_member(root, release, "native/binary-receipt.json"))["binary"]
    require(sha256(APX) == pinned["apxSHA256"], "STAIR_READBACK_INSTALLED_APX_DRIFT")

    session = listener(port)
    core = architecture.A
    core.RUN.bind_authorized_saved_copy(port, str(project), project.stem, project_sha, "EXACT_STAIR_READBACK_ONLY")
    trace = output.with_suffix(".trace")
    trace.mkdir()
    api = core.EvidenceAPI(core.native_transport, trace, execute=False)
    facts = core.RUN.guarded_project_for_read(api)
    runtime = architecture.runtime_identity(api, (pinned["sourceRevision"], pinned["buildIdentity"]))
    require(core.archicad29(api)["buildNumber"] == 5101, "STAIR_READBACK_ARCHICAD_BUILD_DRIFT")
    resolved = resolve_stories(report["brief"], api)
    require(resolved["nativeResolution"] == "READY_FOR_ATTRIBUTE_RESOLUTION", "STAIR_READBACK_STORY_BINDING_UNRESOLVED")
    indices = {row["architecturalStoryId"]: row["nativeIndex"] for row in resolved["nativeStoryBindings"]}
    before = core.inventory_guids(api)
    try:
        result = verify_planned_connection(api, candidate, requirement, bindings, indices)
    except ValueError as exc:
        result = dict(status="NATIVE_STAIR_PLAN_NOT_VERIFIED", reason=str(exc), requirementId=requirement)
    after = core.inventory_guids(api)
    require(set(result.get("bimOperationGuids", {}).values()) <= set(after)
            and before == after and api.write_attempts == 0 and sha256(project) == project_sha
            and core.RUN.guarded_project_for_read(api)["storyTopology"] == facts["storyTopology"]
            and architecture.runtime_identity(api, (pinned["sourceRevision"], pinned["buildIdentity"])) == runtime
            and listener(port) == session and sha256(intent_path) == intent_sha and sha256(bindings_path) == bindings_sha,
            "STAIR_READBACK_PLN_INVENTORY_OR_INPUT_DRIFT")
    return dict(result, projectPath=str(project), projectSha256=project_sha, listener=session, runtime=runtime,
                intentSha256=intent_sha, bindingsSha256=bindings_sha, planHash=candidate["sourcePlanHash"],
                guidSetSha256=core.RUN.digest(before), nativeReadCalls=sum(api.calls.values()), nativeWriteCalls=0,
                traceSha256=sha256(trace / "raw.jsonl"), executionPermission=False)


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
