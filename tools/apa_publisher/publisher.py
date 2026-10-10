#!/usr/bin/env python3
"""Branch-scoped APA Research OS publisher. Python 3.11 standard library only."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import quote
from urllib.request import Request, urlopen

REPO = "dvikt33-ux/safe-bim-layer"
BRANCH = "research/apa-verified-results-hub-20261010"
ROOT = Path("docs/research/apa-results")
RUNS, INBOX = ROOT / "runs", ROOT / "inbox"
RECEIPTS, GENERATED = ROOT / "receipts", ROOT / "generated"
PENDING = Path(".apa-publisher-pending.json")
RUN_RE = re.compile(r"^APA-RUN-(20[0-9]{6})-([0-9]{6})Z-([a-z0-9][a-z0-9-]{2,63})$")
PLAN_RE = re.compile(r"^APA-P[0-9]{2}$")
ACTION_RE = re.compile(r"^APA-P[0-9]{2}\.A[0-9]{2}$")
STEP_RE = re.compile(r"^APA-P[0-9]{2}\.A[0-9]{2}\.S[0-9]{2}$")
PHASES = {"SOURCE", "OFFLINE", "SYNTHETIC", "BUILD", "LIVE"}
CLAIM_STATES = {"SOURCE_VERIFIED", "REPORTED", "NOT_VERIFIED", "TEST_REQUIRED",
                "OFFLINE_PASS", "BUILD_PASS", "LIVE_PASS", "CONFLICT"}
EVIDENCE_STATES = {"READBACK_VERIFIED", "SOURCE_READ", "REPORTED", "NOT_VERIFIED"}
EVIDENCE_KINDS = {"OFFICIAL_DOC", "SOURCE_CODE", "GITHUB_PR", "GITHUB_COMMIT",
                  "LOCAL_LOG", "TEST_RESULT", "USER_SUPPLIED", "OTHER"}
SAFETY = ("main_modified", "pln_modified", "apx_modified",
          "tested_branches_modified", "paid_runtime_used")
REQUEST_KEYS = {"schema", "run_id", "plan_id", "action_id", "substep_id", "executor",
                "executor_run_id", "phase", "started_at", "finished_at", "scope",
                "source_revisions", "inputs", "claims", "evidence", "report_markdown",
                "next_substep", "safety"}


class PublishError(ValueError):
    pass


def check(condition, message):
    if not condition:
        raise PublishError(message)


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        check(key not in result, "Duplicate JSON key: " + key)
        result[key] = value
    return result


def read_json(path):
    raw = path.read_bytes()
    check(len(raw) <= 1048576, "JSON too large: " + str(path))
    return json.loads(raw.decode(), object_pairs_hook=unique_pairs)


def write_if_absent(path, raw):
    if path.exists():
        check(path.read_bytes() == raw, "IMMUTABLE_CONFLICT: " + str(path))
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)


def write_projection(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.read_bytes() != raw:
        path.write_bytes(raw)


def run_path(run_id):
    m = RUN_RE.fullmatch(run_id) if isinstance(run_id, str) else None
    check(m is not None, "Unsafe run ID")
    date = m.group(1)
    return RUNS / (date[:4] + "-" + date[4:6] + "-" + date[6:]) / run_id


def validate(r):
    check(isinstance(r, dict) and set(r) == REQUEST_KEYS, "Request fields mismatch")
    check(r["schema"] == "APA_PUBLISH_REQUEST_V1", "Wrong request schema")
    run_path(r["run_id"])
    check(isinstance(r["plan_id"], str) and PLAN_RE.fullmatch(r["plan_id"]), "Bad plan")
    check(isinstance(r["action_id"], str) and ACTION_RE.fullmatch(r["action_id"]), "Bad action")
    check(isinstance(r["substep_id"], str) and STEP_RE.fullmatch(r["substep_id"]), "Bad substep")
    check(r["action_id"].startswith(r["plan_id"] + ".") and
          r["substep_id"].startswith(r["action_id"] + "."), "Inconsistent plan hierarchy")
    for key in ("executor", "executor_run_id"):
        check(isinstance(r[key], str) and 1 <= len(r[key]) <= 128, "Bad " + key)
    check(r["phase"] in PHASES, "Bad phase")
    for key in ("started_at", "finished_at"):
        check(isinstance(r[key], str) and re.fullmatch(
            r"20[0-9]{2}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z", r[key]), "Bad timestamp")
    check(r["finished_at"] >= r["started_at"], "Finish precedes start")
    check(isinstance(r["scope"], dict) and r["scope"].get("repository") == REPO and
          set(r["scope"]).issubset({"repository", "archicad", "sdk", "tapir", "source_branch"}),
          "Invalid repository/scope")
    check(isinstance(r["source_revisions"], list) and isinstance(r["inputs"], list) and
          all(isinstance(x, str) for x in r["inputs"]), "Bad inputs/sources")
    for source in r["source_revisions"]:
        check(isinstance(source, dict) and set(source) == {"uri", "revision", "source_sha"},
              "Bad source fields")
        check(isinstance(source["uri"], str) and bool(source["uri"]) and
              isinstance(source["revision"], str) and bool(source["revision"]), "Empty source")
        check(source["source_sha"] is None or (isinstance(source["source_sha"], str) and
              re.fullmatch(r"[a-f0-9]{40,64}", source["source_sha"])), "Bad source SHA")
    check(isinstance(r["claims"], list) and isinstance(r["evidence"], list), "Bad evidence/claims")
    ids = set()
    for ev in r["evidence"]:
        check(isinstance(ev, dict) and set(ev) ==
              {"evidence_id", "uri", "kind", "verification", "sha256", "source_revision"},
              "Bad evidence fields")
        check(isinstance(ev["evidence_id"], str) and bool(ev["evidence_id"]) and
              ev["evidence_id"] not in ids, "Duplicate evidence ID")
        ids.add(ev["evidence_id"])
        check(isinstance(ev["uri"], str) and bool(ev["uri"]) and
              ev["kind"] in EVIDENCE_KINDS and ev["verification"] in EVIDENCE_STATES,
              "Bad evidence classification")
        check(ev["sha256"] is None or (isinstance(ev["sha256"], str) and
              re.fullmatch(r"[a-f0-9]{64}", ev["sha256"])), "Bad evidence hash")
        check(ev["source_revision"] is None or isinstance(ev["source_revision"], str),
              "Bad source revision")
    claim_ids = set()
    for claim in r["claims"]:
        check(isinstance(claim, dict) and set(claim) ==
              {"claim_id", "statement", "status", "evidence_ids"}, "Bad claim fields")
        check(isinstance(claim["claim_id"], str) and
              re.fullmatch(r"APA-CLAIM-[A-Z0-9-]+", claim["claim_id"]) and
              claim["claim_id"] not in claim_ids, "Bad claim ID")
        claim_ids.add(claim["claim_id"])
        check(isinstance(claim["statement"], str) and bool(claim["statement"]) and
              claim["status"] in CLAIM_STATES, "Bad claim")
        check(isinstance(claim["evidence_ids"], list) and
              all(x in ids for x in claim["evidence_ids"]), "Claim references missing evidence")
        check(claim["status"] != "LIVE_PASS" or r["phase"] == "LIVE", "LIVE_PASS without LIVE phase")
        check(claim["status"] != "SOURCE_VERIFIED" or claim["evidence_ids"],
              "SOURCE_VERIFIED without evidence")
    check(isinstance(r["report_markdown"], str) and
          30 <= len(r["report_markdown"]) <= 500000, "Bad report size")
    check(r["next_substep"] is None or (isinstance(r["next_substep"], str) and
          STEP_RE.fullmatch(r["next_substep"])), "Bad next step")
    check(isinstance(r["safety"], dict) and set(r["safety"]) == set(SAFETY) and
          all(r["safety"][k] is False for k in SAFETY), "Safety gate failed")


def render(r):
    validate(r)
    sources = sorted(r["source_revisions"], key=lambda x: (x["uri"], x["revision"]))
    fingerprints = sorted(digest(canonical(e)) for e in r["evidence"])
    idempotency = "sha256:" + digest(canonical(
        [r["substep_id"], sources, fingerprints, r["executor_run_id"]]))
    manifest = {k: r[k] for k in REQUEST_KEYS - {"schema", "report_markdown"}}
    manifest.update(schema="APA_RUN_EVENT_V2", status="EVIDENCE_READY",
                    files_to_publish=["REPORT.md", "manifest.json", "evidence.json"],
                    idempotency_key=idempotency)
    evidence = {"schema": "APA_EVIDENCE_INDEX_V1", "run_id": r["run_id"],
                "claims": r["claims"], "evidence": r["evidence"]}
    report = r["report_markdown"].replace("\r\n", "\n").encode()
    if not report.endswith(b"\n"):
        report += b"\n"
    return manifest, evidence, report


def create_run(r):
    manifest, evidence, report = render(r)
    directory = run_path(r["run_id"])
    files = {"REPORT.md": report, "manifest.json": encoded(manifest),
             "evidence.json": encoded(evidence)}
    # All-or-nothing preflight: reject conflicts before any file write.
    for name, raw in files.items():
        p = directory / name
        if p.exists():
            check(p.read_bytes() == raw, "IMMUTABLE_CONFLICT: " + str(p))
    for name, raw in files.items():
        write_if_absent(directory / name, raw)
    return {"run_id": r["run_id"], "report": str(directory / "REPORT.md"),
            "files": [str(directory / name) for name in files],
            "idempotency_key": manifest["idempotency_key"]}


def rebuild_indexes():
    records = []
    for path in sorted(RUNS.glob("**/manifest.json")):
        manifest = read_json(path)
        check(manifest.get("schema") == "APA_RUN_EVENT_V2" and
              run_path(manifest["run_id"]) == path.parent and
              (path.parent / "REPORT.md").is_file(), "Broken immutable run: " + str(path))
        records.append({"run_id": manifest["run_id"], "substep_id": manifest["substep_id"],
                        "report": str(path.parent / "REPORT.md").removeprefix(str(ROOT) + "/"),
                        "phase": manifest["phase"], "evidence_status": manifest["status"]})
    records.sort(key=lambda x: x["run_id"])
    state = {"schema": "APA_GENERATED_INDEX_V1", "source": "immutable V2 runs",
             "run_count": len(records), "runs": records,
             "legacy_flat_runs": "preserved and indexed manually"}
    md = ["# APA Research OS — automatically generated V2 index", "",
          "Generated projection from immutable V2 runs. Legacy reports remain in ARTIFACT_REGISTER.md.",
          "", "| Run | Substep | Phase | Evidence status |",
          "| --- | --- | --- | --- |"]
    for row in records:
        md.append("| [" + row["run_id"] + "](../" + row["report"] + ") | " +
                  row["substep_id"] + " | " + row["phase"] + " | " + row["evidence_status"] + " |")
    md.extend(["", "Publication receipts are in ../receipts/. Evidence status is not publication status.", ""])
    write_projection(GENERATED / "INDEX.md", "\n".join(md).encode())
    write_projection(GENERATED / "STATE.json", encoded(state))
    return [str(GENERATED / "INDEX.md"), str(GENERATED / "STATE.json")]


def prepare():
    check(os.getenv("GITHUB_REF", "refs/heads/" + BRANCH) ==
          "refs/heads/" + BRANCH, "Ref safety gate")
    entries = []
    for path in sorted(INBOX.glob("*.json")):
        r = read_json(path)
        check(path.name == r.get("run_id", "") + ".json", "Inbox name mismatch")
        entries.append(create_run(r))
    paths = rebuild_indexes()
    paths.extend(path for entry in entries for path in entry["files"])
    pending = {"schema": "APA_PENDING_V1", "entries": entries,
               "verify_paths": {p: digest(Path(p).read_bytes()) for p in sorted(set(paths))}}
    PENDING.write_bytes(encoded(pending))
    print("APA_PREPARED", len(entries), "runs;", len(paths), "files")


def api_readback(paths, commit):
    token = os.environ.get("GITHUB_TOKEN")
    check(bool(token), "GITHUB_TOKEN missing")
    check(bool(re.fullmatch(r"[a-f0-9]{40}", commit)), "Invalid commit")
    for path, expected in paths.items():
        check(path.startswith(str(ROOT) + "/") and ".." not in Path(path).parts,
              "Unsafe readback path")
        url = "https://api.github.com/repos/" + REPO + "/contents/" + \
              quote(path, safe="/") + "?ref=" + commit
        req = Request(url, headers={"Authorization": "Bearer " + token,
                      "Accept": "application/vnd.github+json",
                      "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "APA-Publisher"})
        with urlopen(req, timeout=30) as response:
            obj = json.loads(response.read())
        check(obj.get("encoding") == "base64", "Bad GitHub response: " + path)
        raw = base64.b64decode(obj["content"])
        check(digest(raw) == expected, "READBACK_HASH_MISMATCH: " + path)
        blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        check(obj["sha"] == blob, "READBACK_BLOB_MISMATCH: " + path)
        print("READBACK_VERIFIED", path, blob)


def receipt(commit):
    pending = read_json(PENDING)
    for entry in pending["entries"]:
        raw = Path(entry["report"]).read_bytes()
        path = RECEIPTS / (entry["run_id"] + ".json")
        obj = {"schema": "APA_PUBLISH_RECEIPT_V1", "run_id": entry["run_id"],
               "report_path": entry["report"], "report_commit_sha": commit,
               "index_commit_sha": commit, "report_sha256": digest(raw),
               "readback_verified": True, "indexed": True,
               "index_mode": "AUTOMATIC_V2_PROJECTION", "status": "DONE_PUBLISHED",
               "idempotency_key": entry["idempotency_key"]}
        if path.exists():
            old = read_json(path)
            check(old.get("report_sha256") == obj["report_sha256"] and
                  old.get("idempotency_key") == obj["idempotency_key"] and
                  old.get("readback_verified") is True, "RECEIPT_CONFLICT")
        else:
            write_if_absent(path, encoded(obj))
        print("RECEIPT_READY", path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["prepare", "verify", "receipt", "verify-receipts"])
    parser.add_argument("--commit", default="")
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            prepare()
        elif args.command == "verify":
            api_readback(read_json(PENDING)["verify_paths"], args.commit)
        elif args.command == "receipt":
            receipt(args.commit)
        elif args.command == "verify-receipts":
            paths = {}
            for entry in read_json(PENDING)["entries"]:
                path = RECEIPTS / (entry["run_id"] + ".json")
                check(path.exists(), "Missing receipt: " + str(path))
                paths[str(path)] = digest(path.read_bytes())
            api_readback(paths, args.commit)
            print("APA_DONE_PUBLISHED", len(paths))
    except (PublishError, OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print("APA_PUBLISH_BLOCKED:", str(exc), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
