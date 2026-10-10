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
    active_claims = {}
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
            check(task["claim_ref"] not in active_claims,
                  "DUPLICATE_ACTIVE_RUN " + sid)
            active_claims[task["claim_ref"]] = sid
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
    topics = plan.get("topics")
    check(isinstance(topics, dict) and bool(topics), "Missing thematic registry")
    membership = {}
    for topic_id, topic in topics.items():
        check(topic.get("id") == topic_id and
              isinstance(topic.get("title"), str) and bool(topic["title"]) and
              isinstance(topic.get("task_ids"), list) and topic["task_ids"] and
              isinstance(topic.get("artifact_ids"), list) and
              topic.get("synthesis_state") in {"OPEN", "PARTIAL", "DONE_PUBLISHED", "BLOCKED"},
              "Bad topic " + topic_id)
        check(all(x in plan["artifacts"] for x in topic["artifact_ids"]),
              "Unknown topic artifact " + topic_id)
        for sid in topic["task_ids"]:
            check(sid in plan["tasks"], "Unknown topic task " + str(sid))
            check(sid not in membership, "DUPLICATE_TOPIC_MEMBERSHIP " + sid)
            membership[sid] = topic_id
    check(set(membership) == set(plan["tasks"]), "UNMAPPED_TASK_TOPIC")
    # Research and product work share exactly one dispatch/claim registry.
    routes = plan.get("research_routes", {})
    check(isinstance(routes, dict), "BAD_RESEARCH_ROUTES")
    product_ids = {sid for sid, t in plan["tasks"].items()
                   if t["plan_id"] == "APA-P70"}
    if product_ids:
        check(set(routes) == product_ids, "UNMAPPED_PRODUCT_RESEARCH")
    for sid, route in routes.items():
        check(isinstance(route, dict) and
              set(route) == {"research_task_ids", "readiness",
                             "readiness_evidence_ids", "note"},
              "BAD_RESEARCH_ROUTE " + sid)
        research_ids = route["research_task_ids"]
        check(isinstance(research_ids, list) and bool(research_ids) and
              len(set(research_ids)) == len(research_ids) and
              all(rid in plan["tasks"] for rid in research_ids),
              "UNKNOWN_RESEARCH_TASK " + sid)
        check(all(plan["tasks"][rid]["plan_id"] != "APA-P70"
                  for rid in research_ids), "RESEARCH_ROUTE_SELF_LINK " + sid)
        check(route["readiness"] in {"NOT_ASSESSED", "GAP", "SUFFICIENT"},
              "BAD_RESEARCH_READINESS " + sid)
        check(isinstance(route["note"], str), "BAD_RESEARCH_ROUTE_NOTE " + sid)
        evid = route["readiness_evidence_ids"]
        check(isinstance(evid, list) and len(set(evid)) == len(evid) and
              all(x in plan["artifacts"] for x in evid),
              "UNKNOWN_READINESS_EVIDENCE " + sid)
        if route["readiness"] == "SUFFICIENT":
            check(bool(evid) and all(
                plan["artifacts"][aid].get("kind") == "REVIEW" and
                plan["artifacts"][aid].get("verification") == "AUDIT_READBACK_VERIFIED"
                for aid in evid), "UNPROVEN_RESEARCH_SUFFICIENT " + sid)
        check(bool(plan["tasks"][sid]["inputs"]), "RESEARCH_HAS_NO_SOURCE " + sid)
    return plan


def load():
    return validate(read_json(PLAN))


def eligible(task, plan):
    return (task["status"] in DISPATCHABLE and not task["requires_approval"]
            and all(plan["tasks"][d]["status"] == "DONE_PUBLISHED"
                    for d in task["depends_on"]))


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
            check(task["status"] == "IN_PROGRESS",
                  "NOT_IN_PROGRESS " + sid + " — scheduled execution must commit status before work")
            check(task["owner"] == req.get("executor"), "CLAIM_OWNER_MISMATCH " + sid)
            check(task["claim_ref"] == req.get("executor_run_id"),
                  "RUN_ID_MISMATCH " + sid)
            lease = datetime.strptime(task["lease_until"], "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=timezone.utc)
            check(lease > datetime.now(timezone.utc), "CLAIM_LEASE_EXPIRED " + sid)
            check(all(plan["tasks"][dep]["status"] == "DONE_PUBLISHED"
                      for dep in task["depends_on"]), "CLAIM_DEPENDENCY_NOT_DONE " + sid)
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
    return "[" + name + "](../../../../../" + quote(uri, safe="/") + ")"


def write_if_changed(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.read_bytes() != raw:
        path.write_bytes(raw)


def build(plan):
    runs, orphans = existing_runs(plan)
    tasks = plan["tasks"]
    topics = plan["topics"]
    topic_of = {sid: tid for tid, topic in topics.items() for sid in topic["task_ids"]}
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
    # Product development uses the SAME S-ID registry and claim rules as research.
    # Parent P/A status is a derived projection: never mark a parent DONE early.
    def aggregate_status(members):
        if members and all(t["status"] == "DONE_PUBLISHED" for t in members):
            return "DONE_PUBLISHED"
        if any(t["status"] in ACTIVE for t in members):
            return "IN_PROGRESS"
        if any(t["status"] in {"PARTIAL", "DONE_PUBLISHED"} for t in members):
            return "PARTIAL"
        if any(eligible(t, plan) for t in members):
            return "READY"
        if any(t["status"] == "BLOCKED" for t in members):
            return "BLOCKED"
        return "WAITING"

    development_actions = []
    product_plan = plan["plans"].get("APA-P70")
    if product_plan:
        for action_id, action in sorted(product_plan["actions"].items()):
            members = sorted((t for t in tasks.values()
                              if t["action_id"] == action_id), key=lambda t: t["id"])
            development_actions.append({
                "id": action_id, "title": action["title"],
                "status": aggregate_status(members),
                "done": sum(t["status"] == "DONE_PUBLISHED" for t in members),
                "total": len(members),
                "tasks": members})
    development_members = [t for a in development_actions for t in a["tasks"]]
    development_active = [t for t in development_members if t["status"] in ACTIVE]
    development_next = next((t for t in development_members if eligible(t, plan)), None)
    development_plan_status = aggregate_status(development_members)
    routes = plan.get("research_routes", {})
    # Research is allowed to run ahead of BUILD. Only task.dependencies control
    # actual execution, not whether the corresponding product action has begun.
    research_lookahead = []
    for t in development_members:
        route = routes.get(t["id"])
        if not route:
            continue
        pending = [tasks[rid] for rid in route["research_task_ids"]
                   if tasks[rid]["status"] != "DONE_PUBLISHED"]
        eligible_research = [r for r in pending if eligible(r, plan)]
        research_lookahead.append({
            "target": t["id"], "stage": t["action_id"],
            "readiness": route["readiness"],
            "research_tasks": route["research_task_ids"],
            "eligible_research": [r["id"] for r in eligible_research],
            "sources": t["inputs"]})
    ahead = [x for x in research_lookahead
             if x["readiness"] != "SUFFICIENT" and x["eligible_research"]]
    # Earlier product stages first; research can work on later stages when an
    # earlier stage has sufficient evidence or its linked tasks are unavailable.
    ahead.sort(key=lambda x: (x["stage"], x["target"]))
    next_research = ahead[0] if ahead else None

    board = [
        "# APA — единственный Project Controller / Control Board", "",
        "**Source of truth:** " + link(str(PLAN), "PROJECT_PLAN.json") + ".",
        "This file is generated. Never dispatch from chat memory or edit this board.",
        "**Execution trigger:** ChatGPT Scheduled Tasks (user-configured, not a controller cron).",
        "**Scheduler state:** " + safe(plan.get("scheduler", {}).get("state", "NOT_CONFIGURED")) +
        "; **Publisher:** DEPLOYED; **verified 24/7:** NOT_RUNNING.",
        "", "## Task status", "", "| Status | Count |", "| --- | ---: |"]
    board.extend("| " + key + " | " + str(value) + " |" for key, value in counts.items())
    if product_plan:
        board.extend(["", "## Полный цикл разработки APA", "",
                      "[DEVELOPMENT_BOARD.md](DEVELOPMENT_BOARD.md) — стадии P → A → S, фактические статусы и следующий шаг.",
                      "Родительские стадии DONE только если все дочерние S-ID DONE_PUBLISHED.",
                      "[RESEARCH_LOOKAHEAD.md](RESEARCH_LOOKAHEAD.md) — исследования будущих этапов в том же реестре."])
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
                  "- Topic: " + topic_of[t["id"]],
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
        "| Task | Topic | Kind | Dependencies | Related | Inputs | Verified V2 runs |",
        "| --- | --- | --- | --- | --- | --- | ---: |"]
    for t in sorted(tasks.values(), key=lambda x: x["id"]):
        relationships.append("| " + t["id"] + " | " + topic_of[t["id"]] + " | " + t["kind"] + " | " +
                             ", ".join(t["depends_on"]) + " | " +
                             ", ".join(t["related"]) + " | " +
                             ", ".join(t["inputs"]) + " | " +
                             str(sum(r["verified"] for r in runs[t["id"]])) + " |")
    relationships.append("")
    themes = ["# APA — тематическая карта исследований, разработки и интеграции", "",
              "Generated from the sole project plan. Each task belongs to exactly one topic.",
              "Related tasks and evidence are preserved; do not repeat a topic review blindly.",
              "", "| Topic | Research/build tasks | Done | Ready | Existing inputs |",
              "| --- | ---: | ---: | ---: | --- |"]
    for tid, topic in sorted(topics.items()):
        ids = topic["task_ids"]
        done = sum(tasks[sid]["status"] == "DONE_PUBLISHED" for sid in ids)
        available = sum(eligible(tasks[sid], plan) for sid in ids)
        themes.append("| " + tid + " — " + safe(topic["title"]) + " | " +
                      str(len(ids)) + " | " + str(done) + " | " + str(available) +
                      " | " + ", ".join(topic["artifact_ids"]) + " |")
    themes += ["", "## Tasks by topic", ""]
    for tid, topic in sorted(topics.items()):
        themes += ["### " + tid + " — " + safe(topic["title"]), ""]
        for sid in topic["task_ids"]:
            t = tasks[sid]
            themes.append("- " + sid + " [" + t["kind"] + "/" + t["status"] +
                          "]: " + safe(t["title"]) + "; work_key=" + t["work_key"] +
                          "; related=" + (", ".join(t["related"]) or "none"))
        themes.append("")
    handoff = [
        "# APA — START HERE for any new chat or agent", "",
        "Authority: " + link(str(PLAN), "PROJECT_PLAN.json") +
        ". Read [CONTROL_BOARD](CONTROL_BOARD.md), [TASK_CARDS](TASK_CARDS.md) and " +
        "[RELATIONSHIPS](RELATIONSHIPS.md) and [THEMES](THEMES.md) before proposing work.",
        "", "## Mandatory procedure", "",
        "1. Select one eligible S-ID from the generated control board; inspect dependencies, related work and evidence.",
        "2. On a scheduled ChatGPT trigger, atomically set status IN_PROGRESS, owner, lease_until and claim_ref=unique executor_run_id via GitHub blob-SHA CAS. Re-read the committed file before starting work.",
        "3. If the CAS fails or task is already IN_PROGRESS/DONE_PUBLISHED, do not work. Select another eligible S-ID only after fresh readback.",
        "4. Work only within task scope. Commit PUBLISH_REQUEST_V1 with matching substep_id, executor and executor_run_id; publisher rejects an unstarted or expired run.",
        "5. Verify report, CI, receipt and acceptance. Then atomically set DONE_PUBLISHED and attach evidence; for partial results use PARTIAL, for failure BLOCKED with reason. Clear owner/lease/claim_ref.",
        "6. Record status to GitHub and re-read it. If write/readback fails, report failure and do not claim completion.",
        "7. Scheduler is created and managed by the user in ChatGPT Scheduled. Controller never starts research and cannot guarantee a scheduled task will run.",
        "", "## Parallel eligible work lanes", ""]
    for kind in ("CONTROL", "CONSOLIDATION", "RESEARCH", "BUILD", "INTEGRATION", "VALIDATION"):
        selected = [t["id"] for t in ready if t["kind"] == kind]
        handoff.append("- " + kind + ": " + (", ".join(selected[:4]) if selected else "none"))
    handoff += ["", "## Development context and mandatory response header", "",
                 "Read [DEVELOPMENT_BOARD](DEVELOPMENT_BOARD.md) and [RESEARCH_LOOKAHEAD](RESEARCH_LOOKAHEAD.md) for APA-P70.",
                 "Research uses the same PROJECT_PLAN.json task registry; when stage N has sufficient accepted sources, work ahead on independent eligible research for N+1.",
                 "A research substep has its own S-ID, claim and evidence. Link all research to its target product S-ID; avoid duplicating completed reports.",
                 "Start every APA work reply with four brief fields: Этап P-ID, задача A-ID, подзадача S-ID, сейчас (действие/статус).",
                 "Use current GitHub task status; never claim DONE without evidence, receipt and S-ID readback.",
                 "Never invent another controller or repeat proven low-level BIM tests without a regression trigger.",
                 "", "## Safety", "",
                "No autonomous ChatGPT research is started by this controller. 24/7 NOT_RUNNING.",
                "No Deep Research/paid API without explicit approval. No main, PLN, APX, tested branch edits or merge.",
                "Legacy reports are not fully mapped; see APA-P50.A01.S01.", ""]
    state = {"schema": "APA_PROJECT_CONTROLLER_STATE_V1",
             "plan_revision": plan["revision"], "source_plan": str(PLAN),
             "task_count": len(tasks), "artifact_count": len(plan["artifacts"]),
             "topic_count": len(topics),
             "topics": {tid: {"task_ids": topic["task_ids"],
                              "done": sum(tasks[sid]["status"] == "DONE_PUBLISHED" for sid in topic["task_ids"]),
                              "ready": sum(eligible(tasks[sid], plan) for sid in topic["task_ids"])}
                        for tid, topic in sorted(topics.items())},
             "counts": counts,
             "dispatchable": {kind: [t["id"] for t in ready if t["kind"] == kind]
                              for kind in sorted(KINDS)},
             "held": [t["id"] for t in held], "active": [t["id"] for t in active],
             "expired_leases": expired, "orphan_v2_manifests": orphans,
             "known_published_v2_runs": sum(r["verified"] for rs in runs.values() for r in rs),
             "scheduler": plan.get("scheduler", {"provider": "ChatGPT Scheduled Tasks", "state": "NOT_CONFIGURED"}),
             "research_runner_24h": "NOT_RUNNING",
             "publisher": "DEPLOYED_SYNTHETIC_E2E_PASS",
             "legacy_reports": "NOT_FULLY_INDEXED"}
    development_board = [
        "# APA — разработка продукта / DEVELOPMENT_BOARD", "",
        "Generated from [PROJECT_PLAN.json](../PROJECT_PLAN.json); this is not a second register.",
        "Source of truth: task statuses and evidence in PROJECT_PLAN.json.",
        "P/A completion is computed; DONE_PUBLISHED requires **every** child S-ID DONE_PUBLISHED.",
        "requires_approval tasks are not dispatchable until separate owner approval is recorded.", "",
        "## Краткая сводка", "",
        "- План: APA-P70 — " + (safe(product_plan["title"]) if product_plan else "not registered"),
        "- Статус: **" + development_plan_status + "**; завершено " +
        str(sum(t["status"] == "DONE_PUBLISHED" for t in development_members)) +
        "/" + str(len(development_members)) + " подзадач.",
        "- Сейчас: " + (", ".join(t["id"] for t in development_active)
                        if development_active else "не выполняется; нет IN_PROGRESS."),
        "- Следующая доступная: " + (development_next["id"] + " — " +
                                    safe(development_next["title"])
                                    if development_next else "нет, см. зависимости и разрешения"),
        "", "## Этапы → задачи", "",
        "| Задача | Состояние | Выполнено подзадач |",
        "| --- | --- | ---: |"]
    for action in development_actions:
        development_board.append("| " + action["id"] + " — " + safe(action["title"]) +
                                 " | " + action["status"] + " | " +
                                 str(action["done"]) + "/" + str(action["total"]) + " |")
    development_board += ["", "## Подзадачи и следующий шаг", ""]
    for action in development_actions:
        development_board += ["### " + action["id"] + " — " + safe(action["title"]), ""]
        for t in action["tasks"]:
            missing = [d for d in t["depends_on"]
                       if tasks[d]["status"] != "DONE_PUBLISHED"]
            label = t["status"] + (" / AWAITING_APPROVAL" if t["requires_approval"]
                                   else " / WAITING_DEPS" if missing
                                   else " / ELIGIBLE" if eligible(t, plan)
                                   else "")
            route = routes.get(t["id"], {})
            source_ids = t["inputs"]
            development_board.append("- **" + t["id"] + " [" + label + "]** " +
                                     safe(t["title"]) +
                                     ("; зависимости: " + ", ".join(missing) if missing else "") +
                                     "; исследования: " +
                                     ", ".join(route.get("research_task_ids", [])))
            development_board.append("  - Источники/ветки: " +
                                     ", ".join(link(plan["artifacts"][art]["uri"], art)
                                               for art in source_ids))
        development_board.append("")
    research_board = [
        "# APA — опережающие исследования / RESEARCH_LOOKAHEAD", "",
        "Generated from the SAME [PROJECT_PLAN.json](../PROJECT_PLAN.json).",
        "Research runs and BUILD use ONE registry, never independent plans.",
        "NOT_ASSESSED ≠ GAP and not proof that an additional research run is required.",
        "SUFFICIENT requires accepted evidence; it defers repetitive research on that target.",
        "A candidate research S-ID must still satisfy its own dependencies and claim gate.", "",
        "## Следующее исследование", "",
        (("- Цель: " + next_research["target"] + "; доступные исследовательские S-ID: " +
          ", ".join(next_research["eligible_research"]))
         if next_research else "- Нет доступного связанного исследования. Проверить результаты и зависимости."),
        "", "## Источники и очередь по продуктовым подзадачам", ""]
    for target in research_lookahead:
        t = tasks[target["target"]]
        research_board += [
            "### " + target["target"] + " — " + safe(t["title"]), "",
            "- Готовность исследования: **" + target["readiness"] + "**",
            "- Связанные исследования: " +
            ", ".join(rid + " (" + tasks[rid]["status"] + ")"
                      for rid in target["research_tasks"]),
            "- Доступны сейчас: " + (", ".join(target["eligible_research"]) or "нет"),
            "- Использовать источники (ветка/файл/PR): " +
            (", ".join(link(plan["artifacts"][art]["uri"], art) for art in target["sources"])
             or "не указаны"), ""]
    state["research_lookahead"] = {
        "next_target": next_research["target"] if next_research else None,
        "next_eligible_research": (next_research["eligible_research"] if next_research else []),
        "linked_product_substeps": len(research_lookahead),
        "unassessed": sum(x["readiness"] == "NOT_ASSESSED" for x in research_lookahead)}

    state["development"] = {
        "plan_id": "APA-P70", "status": development_plan_status,
        "total": len(development_members),
        "done": sum(t["status"] == "DONE_PUBLISHED" for t in development_members),
        "active": [t["id"] for t in development_active],
        "next_eligible": development_next["id"] if development_next else None,
        "actions": [{k: a[k] for k in ("id", "title", "status", "done", "total")}
                    for a in development_actions]}
    files = {"CONTROL_BOARD.md": "\n".join(board).encode(),
             "DEVELOPMENT_BOARD.md": "\n".join(development_board).encode(),
             "RESEARCH_LOOKAHEAD.md": "\n".join(research_board).encode(),
             "TASK_CARDS.md": "\n".join(cards).encode(),
             "RELATIONSHIPS.md": "\n".join(relationships).encode(),
             "THEMES.md": "\n".join(themes).encode(),
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
