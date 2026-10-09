"""Work-step Slack sync CLI for local APA agents (not a ChatGPT push service).

Read before each step and publish only evidence-backed events after each step.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from scripts.apa_sync.coordinator import InvalidEvent, format_event, parse_event

DEFAULT_CHANNEL = "C0C886E1PGR"


def _client():
    from slack_sdk import WebClient

    token = os.environ.get("SLACK_BOT_TOKEN")
    if not token or not token.startswith("xoxb-"):
        raise SystemExit("SLACK_BOT_TOKEN (xoxb-) required for Slack operations")
    return WebClient(token=token)


def before_step(channel: str, *, oldest: str | None = None, limit: int = 100) -> dict:
    """Read event-bearing Slack messages before work starts.

    Cursor is a Slack message timestamp, not an APA ledger sequence.
    """
    client = _client()
    options = {"channel": channel, "limit": min(200, max(1, limit))}
    if oldest:
        options["oldest"] = oldest
        options["inclusive"] = False
    response = client.conversations_history(**options)
    events = []
    for message in response.get("messages", []):
        text = message.get("text", "")
        try:
            event = parse_event(text)
        except InvalidEvent:
            # Do not silently mark malformed event as accepted.
            events.append({"slack_ts": message.get("ts"), "error": "malformed_apa_event"})
            continue
        if event:
            events.append({"slack_ts": message.get("ts"), "event": event})
    events.reverse()  # chronological order
    return {
        "events": events,
        "truncated": bool(response.get("has_more")),
        "oldest": oldest,
        "newest_ts": events[-1]["slack_ts"] if events else oldest,
        "rule": "Refresh again if truncated; reconcile new events before doing work.",
    }


def after_step(channel: str, event: dict, *, publish: bool = False) -> dict:
    """Publish a validated immutable evidence record, explicitly opted in."""
    rendered = format_event(event)
    validated = parse_event(rendered)
    if validated is None:
        raise InvalidEvent("Invalid event data")
    if not publish:
        return {"dry_run": True, "message": rendered}
    response = _client().chat_postMessage(
        channel=channel,
        text=rendered,
        unfurl_links=False,
        unfurl_media=False,
    )
    if not response.get("ok"):
        raise RuntimeError("Slack did not confirm publication")
    return {
        "published": True,
        "channel_id": response["channel"],
        "slack_ts": response["ts"],
    }


def main():
    parser = argparse.ArgumentParser(description="APA step-level Slack synchronization")
    parser.add_argument("--channel", default=os.environ.get("APA_SYNC_CHANNEL_ID", DEFAULT_CHANNEL))
    commands = parser.add_subparsers(dest="command", required=True)
    before = commands.add_parser("before", help="Read shared updates before any work step")
    before.add_argument("--oldest", default=None, help="Last Slack message ts seen")
    before.add_argument("--limit", type=int, default=100)
    after = commands.add_parser("after", help="Validate/publish a JSON APA event after work")
    after.add_argument("--event-file", required=True)
    after.add_argument("--publish", action="store_true", help="Actually send to Slack")
    args = parser.parse_args()
    if args.command == "before":
        result = before_step(args.channel, oldest=args.oldest, limit=args.limit)
    else:
        event = json.loads(Path(args.event_file).read_text(encoding="utf-8"))
        result = after_step(args.channel, event, publish=args.publish)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
