"""Event-driven Slack Socket Mode receiver for the APA ledger.

Start: python -m scripts.apa_sync.socket_mode
Requires a separately configured Slack App with message.channels subscription.
"""
from __future__ import annotations

import logging
import os
import threading

from scripts.apa_sync.coordinator import EventStore, InvalidEvent, make_server

LOG = logging.getLogger("apa.sync")


def bootstrap_channel(store, client, channel_id: str, max_messages: int = 100) -> dict:
    """Best-effort historical replay, oldest first, with idempotent SQLite writes."""
    max_messages = min(500, max(1, int(max_messages)))
    pages = []
    cursor = None
    while len(pages) < max_messages:
        options = {"channel": channel_id, "limit": min(200, max_messages - len(pages))}
        if cursor:
            options["cursor"] = cursor
        response = client.conversations_history(**options)
        pages.extend(response.get("messages", []))
        cursor = response.get("response_metadata", {}).get("next_cursor")
        if not cursor:
            break
    accepted = 0
    conflicts = 0
    for message in reversed(pages):
        if message.get("subtype") not in (None, "bot_message"):
            continue
        try:
            result = store.ingest(
                message.get("text", ""),
                slack_channel=channel_id,
                slack_ts=str(message.get("ts", "")),
            )
        except InvalidEvent:
            continue
        if result.get("accepted"):
            accepted += 1
            conflicts += int(result["conflict"])
    return {"scanned": len(pages), "accepted": accepted, "conflicts": conflicts}


def run():
    # Import only here; offline ledger/tests do not require third-party packages.
    from slack_bolt import App
    from slack_bolt.adapter.socket_mode import SocketModeHandler

    bot_token = os.environ.get("SLACK_BOT_TOKEN")
    app_token = os.environ.get("SLACK_APP_TOKEN")
    if not bot_token or not app_token:
        raise SystemExit(
            "Set SLACK_BOT_TOKEN (xoxb-) and SLACK_APP_TOKEN (xapp-) in the process environment."
        )
    if not bot_token.startswith("xoxb-") or not app_token.startswith("xapp-"):
        raise SystemExit("Expected a bot token (xoxb-) and app-level token (xapp-).")
    channel_id = os.environ.get("APA_SYNC_CHANNEL_ID", "C0C886E1PGR")
    db_path = os.environ.get("APA_SYNC_DB", "data/apa-sync/events.sqlite3")
    port = int(os.environ.get("APA_SYNC_PORT", "8765"))
    store = EventStore(db_path)
    app = App(token=bot_token, process_before_response=True)

    # Events API normally delivers only new messages. Recover recent history
    # on restart so a temporarily stopped process does not lose all updates.
    try:
        stats = bootstrap_channel(
            store, app.client, channel_id,
            max_messages=int(os.environ.get("APA_SYNC_BOOTSTRAP_LIMIT", "100")),
        )
        LOG.info("APA Slack bootstrap %s", stats)
    except Exception as exc:
        LOG.warning("BOOTSTRAP NOT VERIFIED: %s; future events can still arrive", type(exc).__name__)

    @app.event("message")
    def capture_event(event, logger):
        # Only explicit root messages from the configured project channel.
        # Slack may redeliver messages; the ledger uses event_id and message ts for dedup.
        if (event.get("channel") != channel_id
                or event.get("subtype") not in (None, "bot_message")):
            return
        text = event.get("text", "")
        try:
            result = store.ingest(
                text,
                slack_channel=channel_id,
                slack_ts=str(event.get("ts", "")),
            )
            if result.get("accepted"):
                logger.info(
                    "APA event accepted: seq=%s conflict=%s",
                    result["seq"], result["conflict"],
                )
                if result["conflict"]:
                    logger.warning("APA state conflict at seq=%s; manual review needed", result["seq"])
        except InvalidEvent as exc:
            # Do not log raw Slack content or token-bearing payloads.
            logger.warning("Rejected APA event: %s", exc)
        except Exception:
            logger.exception("Unexpected error while processing APA event")

    server = make_server(store, host="127.0.0.1", port=port)
    thread = threading.Thread(
        target=server.serve_forever,
        daemon=True,
        name="apa-local-read-api",
    )
    thread.start()
    LOG.info("APA coordinator local read API at http://127.0.0.1:%s", port)
    LOG.info("Listening to Slack events only in channel %s", channel_id)
    try:
        SocketModeHandler(app, app_token).start()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    run()
