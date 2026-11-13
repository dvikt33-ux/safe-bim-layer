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
    authored = "authoredIntentHash" in manifest
    if authored:
        from apa_r03_mailbox import listener
    else:
        listener = None

    if phase == "preflight":
        return architecture.preflight(job, manifest, port or manifest["port"], pinned,
                                      local_listener=listener)
    if phase == "verify-reopen":
        approved = read_json(job / "approved-preflight.json")
        return architecture.verify_reopen(job, manifest, pinned, port or approved["port"])
    if port is not None:
        raise ValueError("Исполнение использует порт сохранённого предконтроля")
    if phase == "execute" and architecture.status(job, manifest)["status"] in {
            "LIVE_ARCHITECTURE_SAVED_PENDING_REAL_REOPEN", "LIVE_ARCHITECTURE_SAVED_REOPENED_PASS"}:
        return architecture.execute(job, manifest, pinned, confirm_preflight=confirm_preflight)
    if authored:
        from apa_ac29_save_isolation import reservation_owner_exited

        approval = read_json(job / "approved-preflight.json")
        expected = approval["listener"]
        if phase == "check-closed" and reservation_owner_exited(expected["pid"]):
            return architecture.check_closed(job, manifest, pinned, process_id=expected["pid"])
        if listener(approval["port"]) != expected:
            raise ValueError("APA_AUTHORED_PREFLIGHT_PROCESS_DRIFT")
    if phase == "check-closed":
        return architecture.check_closed(job, manifest, pinned)
    return architecture.execute(job, manifest, pinned, confirm_preflight=confirm_preflight)
