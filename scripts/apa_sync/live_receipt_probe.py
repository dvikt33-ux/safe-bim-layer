"""One-shot Windows acceptance probe for an *existing* APA Slack Socket Mode listener.

Default is read-only. --publish posts at most one explicit INFO receipt notice,
using the durable outbox in receipt_bridge. Never starts/stops the listener,
modifies the canonical controller, or touches Archicad/PLN/APX.
"""
from __future__ import annotations

import argparse
import getpass
import json
import os
import time
from urllib.parse import urlencode

from scripts.apa_sync import receipt_bridge as bridge

API_BASE = "http://127.0.0.1:8765"
MAX_PAGES = 100


def local_api(path: str) -> dict:
    if not path.startswith("/") or "://" in path:
        raise bridge.BridgeError("only fixed localhost paths are permitted")
    return bridge.http_json(API_BASE + path)


def healthy(get=local_api) -> None:
    r = get("/health")
    if r.get("ok") is not True or r.get("mode") != "read_only_local":
        raise bridge.BridgeError("APA local controller is not healthy/read-only")


def read_changes(after: int, get=local_api) -> dict:
    if not isinstance(after, int) or after < 0:
        raise bridge.BridgeError("invalid cursor")
    page = get("/v1/changes?" + urlencode({"after": after, "limit": 200}))
    rows = page.get("changes")
    if not isinstance(rows, list) or len(rows) > 200:
        raise bridge.BridgeError("invalid local change page")
    last = after
    for row in rows:
        if not isinstance(row, dict) or type(row.get("seq")) is not int or row["seq"] <= last:
            raise bridge.BridgeError("nonmonotonic local sequence")
        last = row["seq"]
    if page.get("next_cursor") != last:
        raise bridge.BridgeError("mismatched local cursor")
    return {"changes": rows, "next_cursor": last}


def scan_ledger(event_id: str, get=local_api) -> tuple[int, list[dict]]:
    """Bounded full history scan: establish baseline and detect prior delivery."""
    current, matches = 0, []
    for _ in range(MAX_PAGES):
        page = read_changes(current, get)
        for row in page["changes"]:
            if row.get("event_id") == event_id:
                matches.append(row)
        current = page["next_cursor"]
        if len(page["changes"]) < 200:
            return current, matches
    raise bridge.BridgeError("local ledger exceeds bounded scan; no send attempted")


def validate_row(row: dict, event: dict, slack_ts: str) -> None:
    if row.get("conflict") is not False:
        raise bridge.BridgeError("local delivery has conflict or unverified conflict flag")
    if row.get("slack_ts") != slack_ts or row.get("task_id") != event["task_id"]:
        raise bridge.BridgeError("local delivery differs from Slack readback")
    payload = row.get("payload")
    if not isinstance(payload, dict):
        raise bridge.BridgeError("local ledger payload missing")
    for key in ("event_id", "task_id", "source", "status", "phase", "summary"):
        if payload.get(key) != event.get(key):
            raise bridge.BridgeError("local delivery payload mismatch")
    if payload.get("evidence_urls") != event.get("evidence_urls"):
        raise bridge.BridgeError("local evidence URLs mismatch")


def wait_for_fresh(event: dict, after: int, slack_ts: str,
                   get=local_api, max_waits: int = 2) -> dict:
    """Correlate fresh Socket Mode commit by exact event, source and Slack ts."""
    current = after
    for _ in range(max_waits):
        page = get("/v1/wait?" + urlencode({"after": current, "timeout": 20}))
        rows = page.get("changes")
        if not isinstance(rows, list) or len(rows) > 200:
            raise bridge.BridgeError("invalid local wait response")
        for row in rows:
            if not isinstance(row, dict) or type(row.get("seq")) is not int:
                raise bridge.BridgeError("malformed local event")
            seq = row["seq"]
            if seq <= current:
                raise bridge.BridgeError("nonmonotonic waited sequence")
            current = seq
            if row.get("event_id") == event["event_id"]:
                validate_row(row, event, slack_ts)
                return {"seq": seq, "cursor": current, "conflict": False}
        if page.get("next_cursor") != current:
            raise bridge.BridgeError("local wait cursor mismatch")
    raise bridge.BridgeError("fresh Slack event not observed in local SQLite")


def run(plan_commit: str, task_id: str, receipt_path: str,
        *, publish: bool = False, get=local_api) -> dict:
    """Return VERIFIED only on a newly ingested event; never claim a fake LIVE."""
    reader = bridge.GitHubReader(token=os.environ.get("GITHUB_TOKEN"))
    proof = bridge.verify_receipt(reader, plan_commit, task_id, receipt_path)
    event = bridge.notification(proof)
    healthy(get)
    before, old_matches = scan_ledger(event["event_id"], get)
    if not publish:
        return {"status": "PREFLIGHT_PASS_NO_POST", "baseline_cursor": before,
                "existing_receipt_events": len(old_matches), "event_id": event["event_id"],
                "notification_task_id": event["task_id"], "canonical_task_id": task_id}
    if old_matches:
        raise bridge.BridgeError("notification is already present in SQLite; no fresh test or post")

    # Sender is opt-in only. A local bot token is required but never written,
    # printed or transmitted to ChatGPT; the operator can provide it hidden.
    provided = False
    if not os.environ.get("SLACK_BOT_TOKEN"):
        if not os.isatty(0):
            raise bridge.BridgeError("Slack token unavailable and no interactive terminal")
        value = getpass.getpass("Local SLACK_BOT_TOKEN (hidden): ")
        if not value.startswith("xoxb-"):
            raise bridge.BridgeError("invalid bot token type")
        os.environ["SLACK_BOT_TOKEN"] = value
        provided = True
    try:
        sent = bridge.publish_with_outbox(event)
        observed = bridge.find_notification(event)
        if not observed:
            raise bridge.BridgeError("Slack readback could not confirm outbound event")
        if sent.get("published") is not True:
            raise bridge.BridgeError("message was already sent; cannot claim fresh LIVE")
        result = wait_for_fresh(event, before, observed["slack_ts"], get)
        return {"status": "FRESH_LIVE_PASS", "event_id": event["event_id"],
                "canonical_task_id": task_id, "notification_task_id": event["task_id"],
                "slack_ts": observed["slack_ts"], **result}
    finally:
        if provided:
            os.environ.pop("SLACK_BOT_TOKEN", None)


def main() -> None:
    p = argparse.ArgumentParser(description="APA one-shot receipt→Slack→SQLite probe")
    p.add_argument("--plan-commit", required=True)
    p.add_argument("--task-id", required=True)
    p.add_argument("--receipt-path", required=True)
    p.add_argument("--publish", action="store_true", help="explicitly allow one Slack notification")
    args = p.parse_args()
    try:
        result = run(args.plan_commit, args.task_id, args.receipt_path, publish=args.publish)
    except (bridge.BridgeError, OSError, ValueError, KeyError, TypeError) as exc:
        p.exit(2, f"BRIDGE_LIVE_NOT_VERIFIED: {type(exc).__name__}\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
