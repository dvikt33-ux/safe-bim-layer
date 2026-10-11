"""Bounded Slack ↔ GitHub evidence bridge for APA.

Read-only by default. GitHub Controller remains sole task authority;
no task claims, no GitHub writes, no research runner, no Archicad access.
Outgoing Slack posting is explicit via --publish, never daemonized.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import PurePosixPath
import re
from urllib.parse import quote
from urllib.request import Request, urlopen

REPO = "dvikt33-ux/safe-bim-layer"
BRANCH = "research/apa-verified-results-hub-20261010"
PLAN_PATH = "docs/research/apa-results/control/PROJECT_PLAN.json"
RECEIPT_PREFIX = "docs/research/apa-results/receipts/"
REPORT_PREFIX = "docs/research/apa-results/runs/"
API = f"https://api.github.com/repos/{REPO}/contents/"
SHA = re.compile(r"[0-9a-f]{40}\Z")
S_ID = re.compile(r"APA-P\d{2}\.A\d{2}\.S\d{2}\Z")
CHANNEL = "C0C886E1PGR"
MAX_BYTES = 2_000_000


class BridgeError(ValueError):
    """Fail-closed bridge contract violation."""


def safe_path(value: str, prefix: str) -> str:
    if (not isinstance(value, str) or not value.startswith(prefix)
            or len(value) > 300 or "\\" in value or "%" in value
            or "?" in value or "#" in value or not re.fullmatch(r"[A-Za-z0-9._/-]+", value)
            or any(x in ("", ".", "..") for x in value.split("/"))
            or PurePosixPath(value).as_posix() != value):
        raise BridgeError("unsafe repository path")
    return value


def sha(value: str) -> str:
    if not isinstance(value, str) or not SHA.fullmatch(value):
        raise BridgeError("required immutable 40-hex Git commit SHA")
    return value


def http_json(url: str, *, token: str | None = None) -> dict:
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "apa-receipt-bridge/0.1"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with urlopen(Request(url, headers=headers), timeout=8) as response:
        raw = response.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise BridgeError("HTTP response too large")
    result = json.loads(raw)
    if not isinstance(result, dict):
        raise BridgeError("expected JSON object")
    return result


class GitHubReader:
    """Constructs fixed-repository GitHub REST URLs; never follows Slack-supplied URLs."""

    def __init__(self, token: str | None = None):
        self.token = token

    def read(self, path: str, commit: str) -> bytes:
        safe_path(path, "docs/research/apa-results/")
        ref = sha(commit)
        url = API + quote(path, safe="/") + "?ref=" + ref
        data = http_json(url, token=self.token)
        if data.get("type") != "file" or data.get("encoding") != "base64":
            raise BridgeError("GitHub content is not a base64 file")
        try:
            raw = base64.b64decode(data["content"], validate=False)
        except (ValueError, KeyError) as exc:
            raise BridgeError("GitHub content decode failed") from exc
        if len(raw) > MAX_BYTES:
            raise BridgeError("GitHub file too large")
        return raw


def json_object(raw: bytes) -> dict:
    def reject_duplicate(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise BridgeError("duplicate JSON key")
            value[key] = item
        return value
    try:
        value = json.loads(raw, object_pairs_hook=reject_duplicate)
    except (TypeError, ValueError) as exc:
        raise BridgeError("invalid JSON") from exc
    if not isinstance(value, dict):
        raise BridgeError("expected JSON object")
    return value


def load_plan(reader: GitHubReader, commit: str) -> dict:
    plan = json_object(reader.read(PLAN_PATH, sha(commit)))
    if (plan.get("schema") != "APA_PROJECT_PLAN_V1"
            or plan.get("repository") != REPO
            or plan.get("canonical_branch") != BRANCH
            or not isinstance(plan.get("tasks"), dict)
            or not isinstance(plan.get("artifacts"), dict)):
        raise BridgeError("invalid canonical controller plan")
    return plan


def artifact_path(uri: str) -> str | None:
    """Only the exact canonical repo/tree location, never arbitrary HTTPS hosts."""
    if not isinstance(uri, str):
        return None
    prefix = f"https://github.com/{REPO}/blob/{BRANCH}/"
    candidate = uri[len(prefix):] if uri.startswith(prefix) else uri
    try:
        return safe_path(candidate, "docs/research/apa-results/")
    except BridgeError:
        return None


def verify_receipt(reader: GitHubReader, plan_commit: str, task_id: str, receipt_path: str) -> dict:
    """Verify plan registration + an immutable publisher receipt + report bytes."""
    sha(plan_commit)
    if not S_ID.fullmatch(task_id):
        raise BridgeError("invalid S-ID")
    safe_path(receipt_path, RECEIPT_PREFIX)
    if not receipt_path.endswith(".json"):
        raise BridgeError("receipt must be JSON")
    plan = load_plan(reader, plan_commit)
    task = plan["tasks"].get(task_id)
    if not isinstance(task, dict):
        raise BridgeError("task absent from canonical plan")
    receipts = [item for key in task.get("evidence", [])
                if isinstance((item := plan["artifacts"].get(key)), dict)
                and item.get("kind") == "RECEIPT"
                and artifact_path(item.get("uri")) == receipt_path]
    if len(receipts) != 1:
        raise BridgeError("receipt not registered in task evidence")
    receipt = json_object(reader.read(receipt_path, plan_commit))
    if (receipt.get("schema") != "APA_PUBLISH_RECEIPT_V1"
            or receipt.get("status") != "DONE_PUBLISHED"
            or receipt.get("indexed") is not True
            or receipt.get("readback_verified") is not True):
        raise BridgeError("receipt lacks publisher readback proof")
    key = receipt.get("idempotency_key")
    if not isinstance(key, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", key):
        raise BridgeError("receipt missing immutable idempotency key")
    run_id = receipt.get("run_id")
    if (not isinstance(run_id, str) or not re.fullmatch(r"APA-RUN-[A-Za-z0-9_-]{8,120}", run_id)
            or receipt_path != RECEIPT_PREFIX + run_id + ".json"):
        raise BridgeError("receipt path/run ID mismatch")
    report_path = safe_path(receipt.get("report_path"), REPORT_PREFIX)
    if not report_path.endswith("/REPORT.md") and not report_path.endswith(".md"):
        raise BridgeError("unexpected report path")
    report_commit = sha(receipt.get("report_commit_sha"))
    expected_hash = receipt.get("report_sha256")
    if not isinstance(expected_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_hash):
        raise BridgeError("invalid report checksum")
    report = reader.read(report_path, report_commit)
    if hashlib.sha256(report).hexdigest() != expected_hash:
        raise BridgeError("report SHA256 disagrees with receipt")
    if task_id not in report.decode("utf-8"):
        raise BridgeError("report does not bind the specified task")
    return {"task": task, "receipt": receipt, "report_commit": report_commit,
            "report_path": report_path, "receipt_path": receipt_path, "plan_commit": plan_commit}


def notification(proof: dict) -> dict:
    task = proof["task"]
    rec = proof["receipt"]
    identity = proof["receipt_path"] + ":" + rec["idempotency_key"]
    event_id = "apa-gh-receipt-" + hashlib.sha256(identity.encode()).hexdigest()[:24]
    report_url = f"https://github.com/{REPO}/blob/{proof['report_commit']}/{proof['report_path']}"
    receipt_url = f"https://github.com/{REPO}/blob/{proof['plan_commit']}/{proof['receipt_path']}"
    # Notifications use their own ledger key. Reusing a real task's task_id
    # could spuriously create CONFLICT against a previous PASS status for the
    # same task+phase in EventStore.latest_states().
    notice_stream = "APA-RECEIPT-EVENT-" + task["id"].replace(".", "-")
    return {"schema": "APA_EVENT_V1", "event_id": event_id,
            "task_id": notice_stream, "status": "INFO", "phase": "SOURCE",
            "source": "apa:receipt-bridge:git-verified",
            "summary": (f"Verified immutable publisher receipt for {rec['run_id']}; "
                        f"controller task at pinned commit is {task['status']}. "
                        "This INFO notification does not change the controller."),
            "evidence_urls": [receipt_url, report_url]}


def summarize_changes(get_json, plan: dict, after: int = 0, max_pages: int = 10) -> dict:
    """Read existing localhost ledger only, never treat messages as task writes."""
    if not isinstance(after, int) or after < 0:
        raise BridgeError("invalid cursor")
    counts = {"read": 0, "unknown_tasks": 0, "registered_evidence_matches": 0,
              "unmatched_evidence": 0, "conflicts": 0}
    known_paths = {artifact_path(x.get("uri")) for x in plan["artifacts"].values()
                   if isinstance(x, dict)}
    known_paths.discard(None)
    current = after
    for _ in range(max_pages):
        data = get_json(f"http://127.0.0.1:8765/v1/changes?after={current}&limit=200")
        rows = data.get("changes")
        if not isinstance(rows, list) or len(rows) > 200:
            raise BridgeError("invalid ledger change page")
        if not rows:
            break
        for row in rows:
            seq = row.get("seq")
            if not isinstance(seq, int) or seq <= current:
                raise BridgeError("invalid or nonmonotonic ledger seq")
            current = seq
            counts["read"] += 1
            counts["conflicts"] += int(row.get("conflict") is True)
            counts["unknown_tasks"] += int(row.get("task_id") not in plan["tasks"])
            payload = row.get("payload")
            if not isinstance(payload, dict) or payload.get("event_id") != row.get("event_id"):
                raise BridgeError("ledger payload/event mismatch")
            urls = payload.get("evidence_urls", [])
            if not isinstance(urls, list) or len(urls) > 8:
                raise BridgeError("invalid evidence URL list")
            for url in urls:
                if artifact_path(url) in known_paths:
                    counts["registered_evidence_matches"] += 1
                else:
                    counts["unmatched_evidence"] += 1
        if data.get("next_cursor") != current:
            raise BridgeError("local API cursor mismatch")
        if len(rows) < 200:
            break
    else:
        raise BridgeError("ledger pagination bound exceeded")
    return {"after": after, "next_cursor": current, **counts,
            "authority": "READ_ONLY_CANDIDATES_NOT_TASK_STATUS"}


def find_notification(event: dict, channel: str = CHANNEL) -> dict | None:
    """Read only: exact event ID + semantic payload equality, bounded history.

    A reused ID with different task/status/proof is a conflict, never a duplicate.
    """
    if channel != CHANNEL:
        raise BridgeError("outbound notification restricted to configured APA channel")
    from scripts.apa_sync.coordinator import parse_event
    from scripts.apa_sync.step_sync import _client
    client = _client()
    cursor = None
    for _ in range(6):
        params = {"channel": channel, "limit": 200}
        if cursor:
            params["cursor"] = cursor
        page = client.conversations_history(**params)
        for entry in page.get("messages", []):
            try:
                candidate = parse_event(entry.get("text", ""))
            except ValueError:
                continue
            if candidate and candidate.get("event_id") == event.get("event_id"):
                fields = ("task_id", "phase", "status", "source", "summary", "evidence_urls")
                if any(candidate.get(key, []) != event.get(key, [])
                       for key in fields):
                    raise BridgeError("Slack notification ID has conflicting payload")
                stamp = entry.get("ts")
                if not isinstance(stamp, str) or not stamp:
                    raise BridgeError("matching Slack notification lacks timestamp")
                return {"channel_id": channel, "slack_ts": stamp}
        cursor = page.get("response_metadata", {}).get("next_cursor")
        if not cursor:
            return None
    raise BridgeError("Slack history scan incomplete: refuse to send")


def send_notification(event: dict, channel: str = CHANNEL) -> dict:
    """Legacy opt-in helper: bounded dedup; use publish_with_outbox for durable send."""
    existing = find_notification(event, channel)
    if existing:
        return {"published": False, "already_present": True, **existing}
    from scripts.apa_sync.step_sync import after_step
    return after_step(channel, event, publish=True)


def publish_with_outbox(event: dict, *, outbox_path=None, channel: str = CHANNEL) -> dict:
    """Crash-conservative explicit send: don't blindly retry ambiguous posts."""
    if channel != CHANNEL:
        raise BridgeError("outbound notification restricted to configured APA channel")
    from scripts.apa_sync.notification_outbox import NotificationOutbox, OutboxError, default_path
    from scripts.apa_sync.step_sync import after_step
    outbox = NotificationOutbox(outbox_path if outbox_path is not None else default_path())
    state = outbox.reserve(event)
    if state == "SENT":
        return {"published": False, "already_recorded": True, "event_id": event["event_id"]}
    # Always reconcile against Slack before a new send, including recovered IN_FLIGHT.
    existing = find_notification(event, channel)
    if existing:
        outbox.mark_sent(event["event_id"], existing["slack_ts"])
        return {"published": False, "already_present": True, **existing}
    if state in ("IN_FLIGHT", "UNCERTAIN"):
        raise BridgeError("delivery uncertain: Slack scan found no event; manual review required")
    outbox.begin_send(event["event_id"])
    try:
        sent = after_step(channel, event, publish=True)
        if not isinstance(sent, dict) or sent.get("published") is not True:
            raise OutboxError("Slack send did not confirm publication")
        outbox.mark_sent(event["event_id"], sent.get("slack_ts"))
    except Exception:
        outbox.mark_uncertain(event["event_id"])
        raise BridgeError("Slack delivery uncertain; never retry blindly") from None
    return {"published": True, "event_id": event["event_id"],
            "slack_ts": sent["slack_ts"]}

def main() -> None:
    parser = argparse.ArgumentParser(description="APA receipt verification + Slack notification (opt-in)")
    parser.add_argument("--plan-commit", required=True, help="pinned canonical controller SHA")
    commands = parser.add_subparsers(dest="action", required=True)
    scan = commands.add_parser("scan", help="read-only local ledger against pinned GitHub plan")
    scan.add_argument("--after", type=int, default=0)
    notify = commands.add_parser("notify", help="verify receipt and print event; optional explicit send")
    notify.add_argument("--task-id", required=True)
    notify.add_argument("--receipt-path", required=True)
    notify.add_argument("--publish", action="store_true")
    notify.add_argument("--outbox-db", default=None, help="separate durable notification state")
    args = parser.parse_args()
    reader = GitHubReader(token=os.environ.get("GITHUB_TOKEN"))
    try:
        if args.action == "scan":
            result = summarize_changes(http_json, load_plan(reader, args.plan_commit), after=args.after)
        else:
            proof = verify_receipt(reader, args.plan_commit, args.task_id, args.receipt_path)
            event = notification(proof)
            if args.publish:
                result = {"event_id": event["event_id"], "send": publish_with_outbox(event, outbox_path=args.outbox_db)}
            else:
                result = {"dry_run": True, "event": event}
    except (BridgeError, OSError, KeyError, TypeError) as exc:
        # Fail closed: do not leak raw API payloads, credentials, or URLs.
        parser.exit(2, f"BRIDGE_BLOCKED: {type(exc).__name__}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
