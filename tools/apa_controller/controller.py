#!/usr/bin/env python3
"""APA Project Controller: deterministic project DAG, dispatch and handoff.
The sole dispatch authority is control/PROJECT_PLAN.json. Stdlib only.
"""
import argparse
import base64
from datetime import datetime, timezone
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
PLAN = ROOT / "control/PROJECT_PLAN.json"
GENERATED = ROOT / "control/generated"
RUNS = ROOT / "runs"
RECEIPTS = ROOT / "receipts"
INBOX = ROOT / "inbox"
PENDING = Path(".apa-controller-pending.json")
STEP = re.compile(r"^APA-P[0-9]{2}\.A[0-9]{2}\.S[0-9]{2}$")
PLAN_RE = re.compile(r"^APA-P[0-9]{2}$")
ACTION_RE = re.compile(r"^APA-P[0-9]{2}\.A[0-9]{2}$")
KINDS = {"RESEARCH", "BUILD", "INTEGRATION", "CONSOLIDATION", "CONTROL", "VALIDATION"}
STATUSES = {"READY", "PARTIAL", "CLAIMED", "IN_PROGRESS", "BLOCKED",
            "DONE_PUBLISHED", "SUPERSEDED"}
ACTIVE = {"CLAIMED", "IN_PROGRESS"}
DISPATCHABLE = {"READY", "PARTIAL"}
FIELDS = {"id", "plan_id", "action_id", "title", "kind", "status",
          "priority", "work_key", "depends_on", "related", "inputs",
          "outputs", "acceptance", "owner", "lease_until", "claim_ref",
          "requires_approval", "evidence", "blocked_reason"}


class ControllerError(ValueError):
    pass


def check(condition, message):
    if not condition:
        raise ControllerError(message)


def unique_pairs(pairs):
    result = {}
    for key, val in pairs:
        check(key not in result, "Duplicate JSON key " + key)
        result[key] = val
    return result


def read_json(path):
    raw = path.read_bytes()
    check(len(raw) <= 2 * 1024 * 1024, "JSON too large")
    return json.loads(raw.decode("utf-8"), object_pairs_hook=unique_pairs)


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def safe(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def validate(plan):
    check(isinstance(plan, dict) and plan.get("schema") == "APA_PROJECT_PLAN_V1",
          "Wrong plan schema")
    check(plan.get("repository") == REPO and plan.get("canonical_branch") == BRANCH,
          "Wrong repository or branch")
    check(isinstance(plan.get("revision"), int) and plan["revision"] >= 1, "Bad revision")
    check(isinstance(plan.get("plans"), dict) and isinstance(plan.get("tasks"), dict)
          and isinstance(plan.get("artifacts"), dict) and plan["tasks"], "Bad plan structure")
    for pid, node in plan["plans"].items():
        check(PLAN_RE.fullmatch(pid) and node.get("id") == pid and
              isinstance(node.get("actions"), dict), "Bad plan " + pid)
        for aid, action in node["actions"].items():
            check(ACTION_RE.fullmatch(aid) and aid.startswith(pid + ".") and
                  action.get("id") == aid, "Bad action " + aid)
    for aid, artifact in plan["artifacts"].items():
        check(artifact.get("id") == aid and isinstance(artifact.get("uri"), str)
              and bool(artifact["uri"]) and isinstance(artifact.get("verification"), str),
              "Bad artifact " + aid)
    keys = {}
    for sid, task in plan["tasks"].items():
        check(STEP.fullmatch(sid) and isinstance(task, dict) and
              set(task) == FIELDS and task["id"] == sid, "Bad task fields " + sid)
        check(task["plan_id"] == sid[:7] and task["action_id"] == sid[:11] and
              task["plan_id"] in plan["plans"] and
              task["action_id"] in plan["plans"][task["plan_id"]]["actions"],
              "Unknown task parent " + sid)
        check(isinstance(task["title"], str) and bool(task["title"]) and
              task["kind"] in KINDS and task["status"] in STATUSES and
              isinstance(task["priority"], int) and 0 <= task["priority"] <= 9,
              "Bad task kind/status/priority " + sid)
        key = task["work_key"]
        check(isinstance(key, str) and re.fullmatch(r"[a-z0-9][a-z0-9/_-]{3,127}", key),
              "Bad work key " + sid)
        check(key not in keys, "DUPLICATE_WORK_KEY " + key)
        keys[key] = sid
        for field in ("depends_on", "related", "inputs", "outputs", "evidence"):
            values = task[field]
            check(isinstance(values, list) and all(isinstance(x, str) for x in values)
                  and len(values) == len(set(values)), "Bad " + field + " " + sid)
        check(sid not in task["depends_on"] + task["related"] and
              all(x in plan["tasks"] for x in task["depends_on"] + task["related"]),
              "Broken task graph " + sid)
        check(all(x in plan["artifacts"] for x in task["inputs"] + task["evidence"]),
              "Unknown input/evidence " + sid)
        check(isinstance(task["acceptance"], str) and bool(task["acceptance"]) and
              isinstance(task["requires_approval"], bool), "Missing acceptance " + sid)
        if task["status"] in ACTIVE:
            check(all(isinstance(task[x], str) and bool(task[x])
                      for x in ("owner", "lease_until", "claim_ref")), "UNCLAIMED_ACTIVE " + sid)
            check(re.fullmatch(r"20[0-9]{2}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z",
                               task["lease_until"]), "Bad lease " + sid)
        else:
            check(task["owner"] is None and task["lease_until"] is None and
                  task["claim_ref"] is None, "STALE_CLAIM_FIELDS " + sid)
        if task["status"] == "DONE_PUBLISHED":
            check(bool(task["evidence"]), "DONE_WITHOUT_EVIDENCE " + sid)
        if task["status"] == "BLOCKED":
            check(bool(task["blocked_reason"]), "BLOCKED_WITHOUT_REASON " + sid)
    colors = {}
    def visit(sid):
        check(colors.get(sid, 0) != 1, "DEPENDENCY_CYCLE " + sid)
        if colors.get(sid) == 2:
            return
        colors[sid] = 1
        for dep in plan["tasks"][sid]["depends_on"]:
            visit(dep)
        colors[sid] = 2
    for sid in plan["tasks"]:
        visit(sid)
    for sid, task in plan["tasks"].items():
        for other in task["related"]:
            check(sid in plan["tasks"][other]["related"], "ASYMMETRIC_RELATED " + sid)
    return plan


def load():
    return validate(read_json(PLAN))


def eligible(task, plan):
    return task["status"] in DISPATCHABLE and all(
        plan["tasks"][d]["status"] == "DONE_PUBLISHED" for d in task["depends_on"])


def verify_inbox(plan):
    count = 0
    for path in sorted(INBOX.glob("*.json")):
        req = read_json(path)
        sid = req.get("substep_id")
        check(isinstance(sid, str) and sid in plan["tasks"],
              "ORPHAN_INBOX_TASK " + str(path))
        task = plan["tasks"][sid]
        check(req.get("plan_id") == task["plan_id"] and
              req.get("action_id") == task["action_id"], "WRONG_PARENT " + str(path))
        run_id = req.get("run_id")
        check(isinstance(run_id, str) and path.name == run_id + ".json",
              "BAD_INBOX_NAME " + str(path))
        published = list(RUNS.glob("*/" + run_id + "/manifest.json"))
        if not published:
            check(task["status"] in ACTIVE,
                  "UNCLAIMED_NEW_RUN " + sid + " — claim in PROJECT_PLAN before inbox")
            check(task["owner"] == req.get("executor"), "CLAIM_OWNER_MISMATCH " + sid)
            check(not task["requires_approval"] or req.get("phase") not in {"BUILD", "LIVE"},
                  "OWNER_APPROVAL_REQUIRED " + sid)
        count += 1
    print("APA_CONTROLLER_INBOX_VERIFIED", count)


def existing_runs(plan):
    result = {sid: [] for sid in plan["tasks"]}
    orphans = []
    for path in sorted(RUNS.glob("*/APA-RUN-*/manifest.json")):
        manifest = read_json(path)
        sid = manifest.get("substep_id")
        rid = manifest.get("run_id")
        if manifest.get("schema") != "APA_RUN_EVENT_V2" or sid not in result:
            orphans.append(str(path))
            continue
        receipt_path = RECEIPTS / (str(rid) + ".json")
        receipt = read_json(receipt_path) if receipt_path.is_file() else None
        verified = bool(receipt and receipt.get("run_id") == rid and
                        receipt.get("status") == "DONE_PUBLISHED" and
                        receipt.get("readback_verified") is True and
                        receipt.get("indexed") is True)
        result[sid].append({"run_id": rid, "report": str(path.parent / "REPORT.md"),
                            "receipt": str(receipt_path) if receipt else None,
                            "verified": verified})
    return result, orphans


def link(uri, label=None):
    name = safe(label or Path(uri).name)
    if uri.startswith("https://"):
        return "[" + name + "](" + uri + ")"
    return "[" + name + "](../../../../" + quote(uri, safe="/") + ")"


def write_if_changed(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.read_bytes() != raw:
        path.write_bytes(raw)


def build(plan):
    runs, orphans = existing_runs(plan)
    tasks = plan["tasks"]
    ready = sorted((t for t in tasks.values() if eligible(t, plan)),
                   key=lambda t: (t["priority"], t["id"]))
    held = sorted((t for t in tasks.values() if t["status"] in DISPATCHABLE
                   and not eligible(t, plan)), key=lambda t: t["id"])
    active = sorted((t for t in tasks.values() if t["status"] in ACTIVE),
                    key=lambda t: t["id"])
    now = datetime.now(timezone.utc)
    expired = [t["id"] for t in active if
               datetime.strptime(t["lease_until"], "%Y-%m-%dT%H:%M:%SZ").replace(
                   tzinfo=timezone.utc) <= now]
    counts = {status: sum(t["status"] == status for t in tasks.values())
              for status in sorted(STATUSES)}
    counts.update(DISPATCHABLE_NOW=len(ready), HELD_BY_DEPENDENCIES=len(held),
                  EXPIRED_LEASES=len(expired))
    board = [
        "# APA — единственный Project Controller / Control Board", "",
        "**Source of truth:** " + link(str(PLAN), "PROJECT_PLAN.json") + ".",
        "This file is generated. Never dispatch from chat memory or edit this board.",
        "**Publisher:** DEPLOYED; **24/7 research runner:** NOT_RUNNING.",
        "", "## Task status", "", "| Status | Count |", "| --- | ---: |"]
    board.extend("| " + key + " | " + str(value) + " |" for key, value in counts.items())
    board += ["", "## Claimed tasks", "",
              "| Task | Owner | Lease until | Work key |", "| --- | --- | --- | --- |"]
    board.extend("| " + t["id"] + " | " + safe(t["owner"]) + " | " +
                 safe(t["lease_until"]) + " | " + t["work_key"] + " |" for t in active)
    if not active:
        board.append("| — | — | — | — |")
    for kind in ("CONTROL", "CONSOLIDATION", "RESEARCH", "BUILD", "INTEGRATION", "VALIDATION"):
        subset = [t for t in ready if t["kind"] == kind]
        board += ["", "## " + kind + " — " + str(len(subset)) + " ready", "",
                  "| Priority | Task | Acceptance |", "| --- | --- | --- |"]
        for t in subset:
            board.append("| P" + str(t["priority"]) + " | " + t["id"] +
                         " — " + safe(t["title"]) + " | " + safe(t["acceptance"]) + " |")
        if not subset:
            board.append("| — | — | — |")
    board += ["", "## Waiting for dependencies", "",
              "| Task | Missing completed prerequisites |", "| --- | --- |"]
    for t in held:
        board.append("| " + t["id"] + " | " + ", ".join(
            d for d in t["depends_on"] if tasks[d]["status"] != "DONE_PUBLISHED") + " |")
    if not held:
        board.append("| — | — |")
    board += ["", "## Warnings", "",
              "- Unmapped V2 manifests: " + str(len(orphans)),
              "- Expired leases: " + (", ".join(expired) if expired else "none"),
              "- Legacy flat reports remain in ARTIFACT_REGISTER; do not silently infer their task links.",
              "- DONE_PUBLISHED needs accepted evidence, not only a receipt.", ""]
    cards = ["# APA — task cards / durable cross-chat context", "",
             "Generated from PROJECT_PLAN.json. Read before claiming a task.", ""]
    for t in sorted(tasks.values(), key=lambda x: x["id"]):
        cards += ["## " + t["id"], "",
                  "**" + safe(t["title"]) + "** — " + t["kind"] + " / " +
                  t["status"] + " / P" + str(t["priority"]), "",
                  "- Parent: " + t["plan_id"] + " → " + t["action_id"],
                  "- Work key: " + t["work_key"],
                  "- Depends on: " + (", ".join(t["depends_on"]) or "none"),
                  "- Related, check before duplicating: " + (", ".join(t["related"]) or "none"),
                  "- Acceptance: " + safe(t["acceptance"]),
                  "- Owner/lease: " + ((safe(t["owner"]) + " / " +
                    safe(t["lease_until"])) if t["owner"] else "unclaimed"),
                  "- Requires owner approval: " + str(t["requires_approval"]),
                  "- Source inputs: " + (", ".join(link(plan["artifacts"][a]["uri"], a)
                     for a in t["inputs"]) or "none"),
                  "- Existing V2 runs: " + (", ".join(link(r["report"], r["run_id"]) +
                    (" (receipt verified)" if r["verified"] else " (not verified)")
                    for r in runs[t["id"]]) or "none"),
                  "- Expected output: " + "; ".join(safe(o) for o in t["outputs"]), ""]
    relationships = [
        "# APA — dependency / research / integration traceability", "",
        "Explicit links from plan, not guessed semantic connections.", "",
        "| Task | Kind | Dependencies | Related | Inputs | Verified V2 runs |",
        "| --- | --- | --- | --- | --- | ---: |"]
    for t in sorted(tasks.values(), key=lambda x: x["id"]):
        relationships.append("| " + t["id"] + " | " + t["kind"] + " | " +
                             ", ".join(t["depends_on"]) + " | " +
                             ", ".join(t["related"]) + " | " +
                             ", ".join(t["inputs"]) + " | " +
                             str(sum(r["verified"] for r in runs[t["id"]])) + " |")
    relationships.append("")
    handoff = [
        "# APA — START HERE for any new chat or agent", "",
        "Authority: " + link(str(PLAN), "PROJECT_PLAN.json") +
        ". Read [CONTROL_BOARD](CONTROL_BOARD.md), [TASK_CARDS](TASK_CARDS.md) and " +
        "[RELATIONSHIPS](RELATIONSHIPS.md) before proposing work.",
        "", "## Mandatory procedure", "",
        "1. Select one eligible S-ID from the generated control board; inspect dependencies, related work and evidence.",
        "2. Claim the task in PROJECT_PLAN.json via GitHub blob-SHA compare-and-swap: status CLAIMED, owner, lease_until, claim_ref. Never overwrite a competing claim.",
        "3. Work only within the task scope and acceptance criteria. Check prior artifacts; do not repeat a work_key.",
        "4. Commit PUBLISH_REQUEST_V1 inbox JSON with matching S-ID and executor. Unclaimed new runs are rejected.",
        "5. Verify GitHub Actions success and DONE_PUBLISHED receipt; only then review acceptance, mark DONE_PUBLISHED, and clear claim.",
        "6. If blocked, preserve findings, document blocked_reason, and return to the controller. Do not create a parallel plan.",
        "", "## Parallel eligible work lanes", ""]
    for kind in ("CONTROL", "CONSOLIDATION", "RESEARCH", "BUILD", "INTEGRATION", "VALIDATION"):
        selected = [t["id"] for t in ready if t["kind"] == kind]
        handoff.append("- " + kind + ": " + (", ".join(selected[:4]) if selected else "none"))
    handoff += ["", "## Safety", "",
                "No autonomous ChatGPT research is started by this controller. 24/7 NOT_RUNNING.",
                "No Deep Research/paid API without explicit approval. No main, PLN, APX, tested branch edits or merge.",
                "Legacy reports are not fully mapped; see APA-P50.A01.S01.", ""]
    state = {"schema": "APA_PROJECT_CONTROLLER_STATE_V1",
             "plan_revision": plan["revision"], "source_plan": str(PLAN),
             "task_count": len(tasks), "artifact_count": len(plan["artifacts"]),
             "counts": counts,
             "dispatchable": {kind: [t["id"] for t in ready if t["kind"] == kind]
                              for kind in sorted(KINDS)},
             "held": [t["id"] for t in held], "active": [t["id"] for t in active],
             "expired_leases": expired, "orphan_v2_manifests": orphans,
             "known_published_v2_runs": sum(r["verified"] for rs in runs.values() for r in rs),
             "research_runner_24h": "NOT_RUNNING",
             "publisher": "DEPLOYED_SYNTHETIC_E2E_PASS",
             "legacy_reports": "NOT_FULLY_INDEXED"}
    files = {"CONTROL_BOARD.md": "\n".join(board).encode(),
             "TASK_CARDS.md": "\n".join(cards).encode(),
             "RELATIONSHIPS.md": "\n".join(relationships).encode(),
             "HANDOFF.md": "\n".join(handoff).encode(),
             "STATE.json": encoded(state)}
    for name, raw in files.items():
        write_if_changed(GENERATED / name, raw)
    PENDING.write_bytes(encoded({"schema": "APA_CONTROLLER_PENDING_V1",
                                 "files": {str(GENERATED / name): digest(raw)
                                           for name, raw in sorted(files.items())}}))
    print("APA_CONTROLLER_BUILT tasks=%d ready=%d published_v2=%d orphan=%d" %
          (len(tasks), len(ready), state["known_published_v2_runs"], len(orphans)))
    return state


def verify_remote(commit):
    check(isinstance(commit, str) and re.fullmatch(r"[a-f0-9]{40}", commit),
          "Invalid commit SHA")
    token = os.getenv("GITHUB_TOKEN")
    check(bool(token), "Missing GITHUB_TOKEN")
    for path, expected in read_json(PENDING)["files"].items():
        check(path.startswith(str(ROOT) + "/control/generated/") and
              ".." not in Path(path).parts, "Unsafe path")
        url = "https://api.github.com/repos/" + REPO + "/contents/" + \
              quote(path, safe="/") + "?ref=" + commit
        req = Request(url, headers={"Authorization": "Bearer " + token,
                      "Accept": "application/vnd.github+json",
                      "X-GitHub-Api-Version": "2022-11-28",
                      "User-Agent": "APA-Project-Controller"})
        with urlopen(req, timeout=30) as response:
            obj = json.loads(response.read())
        check(obj.get("encoding") == "base64", "Bad GitHub response")
        raw = base64.b64decode(obj["content"])
        check(digest(raw) == expected, "CONTROLLER_READBACK_MISMATCH " + path)
        blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        check(blob == obj["sha"], "CONTROLLER_BLOB_MISMATCH " + path)
        print("APA_CONTROLLER_READBACK_VERIFIED", path, blob)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["validate", "verify-inbox", "build", "verify-remote"])
    parser.add_argument("--commit", default="")
    args = parser.parse_args()
    try:
        check(os.getenv("GITHUB_REF", "refs/heads/" + BRANCH) ==
              "refs/heads/" + BRANCH, "Unsafe GitHub ref")
        plan = load()
        if args.command == "validate":
            print("APA_CONTROLLER_VALID", len(plan["tasks"]))
        elif args.command == "verify-inbox":
            verify_inbox(plan)
        elif args.command == "build":
            build(plan)
        else:
            verify_remote(args.commit)
    except (ControllerError, OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print("APA_CONTROLLER_BLOCKED:", str(exc), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
