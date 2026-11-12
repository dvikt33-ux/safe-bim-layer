"""Adapt existing coordination and knowledge inputs to the common application."""

import hashlib
import json
from pathlib import Path
import re

from apa_release import read_json, read_release, sha256, verify_member


def arena_receipt(path):
    raw = path.read_bytes()
    row = json.loads(raw.decode("utf-8-sig"))
    turn = row.get("turn_id")
    if (row.get("protocol") != 1 or row.get("kind") != "terminal_ack"
            or type(turn) is not int or turn < 1 or row.get("ack_verified") is not True
            or row.get("signal_status") != "done" or row.get("signal_target") != "NONE"
            or not re.fullmatch(r"[a-f0-9]{40}", row.get("signal_blob_sha", ""))):
        raise ValueError("Выберите квитанцию завершённого обмена Arena с терминальным ACK")
    return {"status": "ARENA_TERMINAL_RECEIPT_IMPORTED", "turn": turn,
            "signalBlobSha1": row["signal_blob_sha"], "receiptSha256": hashlib.sha256(raw).hexdigest(),
            "source": row.get("source"), "reportMarker": row.get("report_marker"),
            "executionPermission": False}


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


def architecture_phase(root, job, phase, port):
    import apa_r03_architecture as architecture
    from apa_mailbox_profile import APX

    job = job.resolve(strict=True)
    recorded = read_json(job / "job.json")
    donor = Path(recorded["original"]).resolve(strict=True)
    manifest = architecture.check(job, donor, recorded["initialSHA256"])
    if phase == "status":
        return architecture.status(job, manifest)
    release = read_release(root)
    native = read_json(verify_member(root, release, "native/binary-receipt.json"))["binary"]
    if sha256(APX) != native["apxSHA256"]:
        raise ValueError("Установленный APX отличается от проверенного комплекта APA")
    pinned = (native["sourceRevision"], native["buildIdentity"])
    if phase == "preflight":
        return architecture.preflight(job, manifest, port or manifest["port"], pinned)
    if port is not None:
        raise ValueError("Исполнение использует порт сохранённого предконтроля")
    return architecture.execute(job, manifest, pinned)
