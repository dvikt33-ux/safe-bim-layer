"""Read-only, privacy-safe diagnostic of Slack raw APA message envelopes.

Run from the checkout with the already installed isolated Python:
  python -m scripts.apa_sync.inspect_raw_envelopes

Prompts for the bot OAuth token locally. Outputs finite categories and counters
only. Never persists or echoes tokens, message text, IDs, authors, URLs or JSON.
Does not import, mutate or access the SQLite event ledger.
"""
from __future__ import annotations

from collections import Counter
from getpass import getpass
import json
from typing import Iterable

from scripts.apa_sync.coordinator import EVENT_PREFIX, InvalidEvent, parse_event

CHANNEL_ID = "C0C886E1PGR"
KNOWN_FOOTER = "*Sent using* <@U0C90JE4WAC|ChatGPT>"
KNOWN_BARE_MENTION_FOOTER = "*Sent using* <@U0C90JE4WAC>"
SECRETLESS_REASONS = {
    "Event exceeds 5000 characters": "length_rejected",
    "Expected APA_EVENT_V1 and one JSON code fence": "fence_envelope_rejected",
    "Invalid event JSON": "json_rejected",
    "Unexpected event keys": "unexpected_keys",
    "Unsupported schema discriminator": "wrong_schema",
    "Unknown status or phase": "invalid_phase_or_status",
    "Invalid evidence_urls": "invalid_evidence",
    "PASS requires a verifiable evidence URL": "pass_evidence_missing",
}


def _len_bucket(n: int) -> str:
    if n == 0:
        return "zero"
    if n <= 64:
        return "1-64"
    if n <= 160:
        return "65-160"
    return "over-160"


def _suffix_type(tail: str) -> str:
    cleaned = tail.strip()
    if not cleaned:
        return "empty"
    if cleaned == KNOWN_FOOTER:
        return "exact_known_footer"
    if cleaned == KNOWN_BARE_MENTION_FOOTER:
        return "exact_known_bare_mention_footer"
    if KNOWN_FOOTER in cleaned:
        return "contains_known_footer_plus_other"
    if "Sent using" in cleaned and "ChatGPT" in cleaned:
        return "other_chatgpt_attribution"
    if "Sent using" in cleaned:
        return "other_attribution"
    if "ChatGPT" in cleaned:
        return "other_chatgpt_text"
    return "other_suffix"


def characterize(text: str) -> str:
    """Return only finite, non-reversible structural features."""
    markers = text.count("```")
    fences = "none" if markers == 0 else "one" if markers == 1 else "two" if markers == 2 else "many"
    if markers >= 1:
        suffix = text.rsplit("```", 1)[-1]
        suffix_type = _suffix_type(suffix)
        suffix_length = _len_bucket(len(suffix))
        suffix_has_cr = "yes" if "\r" in suffix else "no"
        suffix_has_unicode_format = "yes" if any(
            c in "\u200b\u200c\u200d\ufeff" for c in suffix
        ) else "no"
    else:
        suffix_type = "not_applicable"
        suffix_length = "not_applicable"
        suffix_has_cr = "not_applicable"
        suffix_has_unicode_format = "not_applicable"
    return (
        f"fences={fences};tail={suffix_type};tail_len={suffix_length};"
        f"cr={suffix_has_cr};invisible={suffix_has_unicode_format}"
    )




# Explicit, content-free validation codes. Never print arbitrary exceptions.
VALIDATOR_REASON_CODES = {
    "Unexpected event keys": "unexpected_keys",
    "Unsupported schema discriminator": "wrong_schema",
    "Unknown status or phase": "unknown_status_or_phase",
    "Invalid source": "source_length",
    "Invalid summary": "summary_length",
    "Invalid evidence_urls": "invalid_evidence_collection",
    "Invalid evidence URL": "invalid_evidence_item",
    "Evidence URL must be HTTPS without credentials": "evidence_url_not_https",
    "PASS requires a verifiable evidence URL": "pass_missing_evidence",
    "Invalid supersedes event ID": "bad_supersedes",
    "Event exceeds 5000 characters": "size_limit",
    "Invalid event JSON": "json_decode_failed",
    "Expected APA_EVENT_V1 and one JSON code fence": "fence_pattern_failed",
}
for _required_field in ("event_id", "task_id", "status", "phase", "source", "summary"):
    VALIDATOR_REASON_CODES[f"Missing or invalid {_required_field}"] = f"missing_or_bad_{_required_field}"
for _identifier_field in ("event_id", "task_id"):
    VALIDATOR_REASON_CODES[f"Invalid {_identifier_field}"] = f"bad_{_identifier_field}"


def _safe_schema_rejection(exc: InvalidEvent, event: dict) -> str:
    """Fixed-category reason; never echoes event content or exception text."""
    reason = VALIDATOR_REASON_CODES.get(str(exc), "other_validation_failure")
    if reason == "evidence_url_not_https":
        urls = event.get("evidence_urls", [])
        if isinstance(urls, list) and any(
            isinstance(u, str) and u.startswith("<https://") for u in urls
        ):
            return reason + ":slack_angle_link"
        return reason + ":other_url_shape"
    return reason


def _staged_fence_diagnosis(text: str) -> str:
    """Content-free reason category after decoding between exactly two fences.

    This function is diagnostic only. It never returns copied source text,
    does not relax parse_event, and does not accept events into SQLite.
    """
    if not isinstance(text, str) or text.count("```") != 2:
        return "not_two_fences"
    head, middle, tail = text.split("```")
    lead = head[len(EVENT_PREFIX):] if head.startswith(EVENT_PREFIX) else head
    if "\n" in lead:
        preamble = "has_linebreak"
    elif "\\r" in lead:
        preamble = "has_cr"
    else:
        preamble = "no_linebreak"

    candidate = middle.lstrip()
    if candidate.startswith("json") and len(candidate) > 4 and candidate[4].isspace():
        kind = "json_language"
        candidate = candidate[4:].lstrip()
    elif candidate.startswith("JSON") and len(candidate) > 4 and candidate[4].isspace():
        kind = "json_language"
        candidate = candidate[4:].lstrip()
    elif candidate.startswith("{"):
        kind = "object_open"
    else:
        kind = "other_open"

    footer = _suffix_type(tail)
    if footer not in ("exact_known_footer", "exact_known_bare_mention_footer"):
        return "other_footer_or_no_footer"

    if not candidate.startswith("{"):
        return f"{preamble};{kind};no_object_start"
    try:
        value = json.loads(candidate)
    except (ValueError, TypeError):
        return f"{preamble};{kind};json_decoding_failed"
    if not isinstance(value, dict):
        return f"{preamble};{kind};json_not_object"

    # Re-package only in memory for a strictly validated control comparison.
    # JSON validation errors are grouped, not emitted with untrusted details.
    controlled = EVENT_PREFIX + "\n```json\n" + json.dumps(
        value, ensure_ascii=False, sort_keys=True,
    ) + "\n```"
    try:
        normalized = parse_event(controlled)
    except InvalidEvent as exc:
        reason = _safe_schema_rejection(exc, value)
        return f"{preamble};{kind};schema_rejected:{reason}"
    if normalized is None:
        return f"{preamble};{kind};prefix_rejected"
    return f"{preamble};{kind};valid_json_and_schema_envelope_mismatch"


def summarize(messages: Iterable[dict]) -> dict:
    """Summarize messages without returning any original message attributes."""
    counters: Counter = Counter()
    shapes: Counter = Counter()
    rejected_stage_shapes: Counter = Counter()
    for message in messages:
        counters["scanned"] += 1
        if message.get("subtype") not in (None, "bot_message"):
            counters["ignored_subtype"] += 1
            continue
        body = message.get("text", "")
        if not isinstance(body, str) or not body.startswith(EVENT_PREFIX):
            counters["non_event"] += 1
            continue
        counters["apa_prefix"] += 1
        shapes[characterize(body)] += 1
        try:
            event = parse_event(body)
        except InvalidEvent as exc:
            code = SECRETLESS_REASONS.get(str(exc), "other_static_validation_error")
            counters[code] += 1
            if code == "fence_envelope_rejected" and body.count("```") == 2:
                rejected_stage_shapes[_staged_fence_diagnosis(body)] += 1
        else:
            if event:
                counters["parse_valid"] += 1
    return {
        "read_only": True,
        "scope": "APA channel, capped at 100 recent messages",
        "counts": dict(sorted(counters.items())),
        "structural_shapes": dict(sorted(shapes.items())),
        "rejected_stage_shapes": dict(sorted(rejected_stage_shapes.items())),
    }



# Never emit raw Slack API errors: error.response may include arbitrary data.
# Map only allowlisted static codes and numeric HTTP/retry metadata.
SAFE_SLACK_ERROR_CODES = frozenset({
    "invalid_auth", "not_authed", "account_inactive", "token_revoked",
    "missing_scope", "not_in_channel", "channel_not_found",
    "no_permission", "team_access_not_granted", "ekm_access_denied",
    "org_login_required", "invalid_arguments", "restricted_action",
    "is_archived", "ratelimited", "rate_limited", "internal_error",
    "fatal_error", "request_timeout",
})


def safe_slack_error_summary(response) -> dict:
    """Whitelisted error code plus safe HTTP/retry metadata only."""
    try:
        raw_code = response.get("error")
    except (AttributeError, TypeError, KeyError):
        raw_code = None
    code = (raw_code if isinstance(raw_code, str)
            and raw_code in SAFE_SLACK_ERROR_CODES else "other_slack_error")
    details = {"error_code": code}
    status = getattr(response, "status_code", None)
    if type(status) is int and 100 <= status <= 599:
        details["http_status"] = status
    headers = getattr(response, "headers", None)
    if hasattr(headers, "get"):
        retry = headers.get("Retry-After")
        if retry is None:
            retry = headers.get("retry-after")
        if isinstance(retry, str) and retry.isascii() and retry.isdigit():
            delay = int(retry)
            if 1 <= delay <= 3600:
                details["retry_after_seconds"] = delay
    return details


def run() -> None:
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError

    token = getpass("Enter SLACK_BOT_TOKEN (xoxb-, hidden; not saved): ")
    if not token.startswith("xoxb-"):
        raise SystemExit("Invalid bot token prefix; no requests made")
    client = WebClient(token=token, timeout=15)
    del token
    try:
        messages = []
        cursor = None
        while len(messages) < 100:
            kwargs = {"channel": CHANNEL_ID, "limit": min(100, 100 - len(messages))}
            if cursor:
                kwargs["cursor"] = cursor
            response = client.conversations_history(**kwargs)
            messages.extend(response.get("messages", []))
            cursor = response.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break
    except SlackApiError as exc:
        details = safe_slack_error_summary(exc.response)
        raise SystemExit("Slack API request failed: " + json.dumps(details, sort_keys=True)) from None
    except Exception:
        raise SystemExit("Slack read-only probe failed (details withheld)") from None
    print(json.dumps(summarize(messages), ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    run()
