"""Read-only Archicad change watcher over the Tapir HTTP bridge.

The watcher never opens, switches, saves, closes, creates, modifies, selects, or
removes Archicad elements. It polls the currently open project and reports:
- added element GUIDs;
- removed element GUIDs;
- changed element fingerprints (type/details/floor/bounding box);
- project switches, which stop the watcher fail-closed.

Usage:
    python scripts/archicad_change_watch.py --port 19725
    python scripts/archicad_change_watch.py --port 19725 --interval 1.0
    python scripts/archicad_change_watch.py --port 19725 --once

Evidence is written under:
    %TEMP%\\safe-bim-mvp-evidence\\archicad-watch\\
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_PORT = 19723
DEFAULT_INTERVAL = 1.5
EVIDENCE = Path(
    os.environ.get(
        "SAFE_BIM_MVP_EVIDENCE",
        Path(tempfile.gettempdir()) / "safe-bim-mvp-evidence",
    )
) / "archicad-watch"


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def append_jsonl(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n")


def api_call(port: int, command: str, parameters: dict | None = None) -> dict:
    request = {
        "command": "API.ExecuteAddOnCommand",
        "parameters": {
            "addOnCommandId": {
                "commandNamespace": "TapirCommand",
                "commandName": command,
            },
            "addOnCommandParameters": parameters or {},
        },
    }
    payload = json.dumps(request, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as response:
        envelope = json.loads(response.read())
    if not envelope.get("succeeded"):
        raise RuntimeError(f"{command} transport failed: {envelope}")
    result = envelope.get("result", {}).get("addOnCommandResponse", {})
    if isinstance(result, dict) and result.get("error") is not None:
        raise RuntimeError(f"{command} failed: {result['error']}")
    return result


def project_identity(project: dict) -> dict:
    return {
        "projectPath": project.get("projectPath"),
        "projectName": project.get("projectName"),
        "isUntitled": project.get("isUntitled"),
        "isTeamwork": project.get("isTeamwork"),
    }


def element_rows(port: int) -> list[dict]:
    result = api_call(port, "GetAllElements")
    rows = result.get("elements", [])
    return [row for row in rows if row.get("elementId", {}).get("guid")]


def element_payload(guids: list[str]) -> list[dict]:
    return [{"elementId": {"guid": guid}} for guid in guids]


def stable_hash(value: Any) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def snapshot(port: int) -> dict:
    project = api_call(port, "GetProjectInfo")
    stories = api_call(port, "GetStories")
    rows = element_rows(port)

    guids = sorted(row["elementId"]["guid"] for row in rows)
    elements = element_payload(guids)

    details_rows: list[Any] = []
    bbox_rows: list[Any] = []

    if elements:
        details_rows = api_call(
            port, "GetDetailsOfElements", {"elements": elements}
        ).get("detailsOfElements", [])
        bbox_rows = api_call(
            port, "Get3DBoundingBoxes", {"elements": elements}
        ).get("boundingBoxes3D", [])

    state: dict[str, dict] = {}
    for i, guid in enumerate(guids):
        details = details_rows[i] if i < len(details_rows) else None
        bbox = bbox_rows[i] if i < len(bbox_rows) else None
        record = {
            "guid": guid,
            "details": details,
            "boundingBox": bbox,
        }
        record["fingerprint"] = stable_hash(
            {
                "details": details,
                "boundingBox": bbox,
            }
        )
        state[guid] = record

    return {
        "timestamp": now_iso(),
        "port": port,
        "project": project_identity(project),
        "activeStory": stories.get("actStory"),
        "stories": stories.get("stories", []),
        "elementCount": len(guids),
        "elements": state,
    }


def bbox_value(row: dict | None) -> dict | None:
    if not isinstance(row, dict):
        return None
    box = row.get("boundingBox3D")
    return box if isinstance(box, dict) else None


def detail_summary(row: dict | None) -> dict:
    if not isinstance(row, dict):
        return {}
    return {
        "type": row.get("type"),
        "id": row.get("id"),
        "floorIndex": row.get("floorIndex"),
        "layerIndex": row.get("layerIndex"),
    }


def summarize_change(before: dict, after: dict) -> dict:
    b_detail = before.get("details")
    a_detail = after.get("details")
    return {
        "guid": after.get("guid") or before.get("guid"),
        "before": {
            **detail_summary(b_detail),
            "boundingBox": bbox_value(before.get("boundingBox")),
        },
        "after": {
            **detail_summary(a_detail),
            "boundingBox": bbox_value(after.get("boundingBox")),
        },
    }


def compare(before: dict, after: dict) -> dict:
    b = before.get("elements", {})
    a = after.get("elements", {})
    b_ids = set(b)
    a_ids = set(a)

    added = sorted(a_ids - b_ids)
    removed = sorted(b_ids - a_ids)
    changed_ids = sorted(
        guid
        for guid in (a_ids & b_ids)
        if b[guid].get("fingerprint") != a[guid].get("fingerprint")
    )

    return {
        "timestamp": after["timestamp"],
        "port": after["port"],
        "project": after["project"],
        "activeStory": after.get("activeStory"),
        "elementCountBefore": before.get("elementCount"),
        "elementCountAfter": after.get("elementCount"),
        "added": [
            {
                "guid": guid,
                **detail_summary(a[guid].get("details")),
                "boundingBox": bbox_value(a[guid].get("boundingBox")),
            }
            for guid in added
        ],
        "removed": [
            {
                "guid": guid,
                **detail_summary(b[guid].get("details")),
                "boundingBox": bbox_value(b[guid].get("boundingBox")),
            }
            for guid in removed
        ],
        "changed": [summarize_change(b[guid], a[guid]) for guid in changed_ids],
    }


def print_event(event: dict) -> None:
    added = event["added"]
    removed = event["removed"]
    changed = event["changed"]
    print(
        f"[{event['timestamp']}] "
        f"count {event['elementCountBefore']} -> {event['elementCountAfter']} | "
        f"+{len(added)} -{len(removed)} ~{len(changed)}"
    )
    for row in added:
        print(
            f"  + {row.get('type') or '?'} "
            f"story={row.get('floorIndex')} guid={row['guid']}"
        )
    for row in removed:
        print(
            f"  - {row.get('type') or '?'} "
            f"story={row.get('floorIndex')} guid={row['guid']}"
        )
    for row in changed:
        b = row["before"]
        a = row["after"]
        print(
            f"  ~ {a.get('type') or b.get('type') or '?'} "
            f"story={b.get('floorIndex')}->{a.get('floorIndex')} "
            f"guid={row['guid']}"
        )
        if b.get("boundingBox") != a.get("boundingBox"):
            print(f"      bbox: {b.get('boundingBox')} -> {a.get('boundingBox')}")
    sys.stdout.flush()


def run(args: argparse.Namespace) -> int:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    latest_path = EVIDENCE / f"latest-{args.port}.json"
    events_path = EVIDENCE / f"events-{args.port}.jsonl"

    current = snapshot(args.port)
    baseline_project = current["project"]

    if args.expect_project_substring:
        path = baseline_project.get("projectPath") or ""
        if args.expect_project_substring.lower() not in path.lower():
            raise RuntimeError(
                "Target project guard failed: "
                f"expected path containing {args.expect_project_substring!r}, "
                f"got {path!r}"
            )

    write_json(latest_path, current)
    print(
        f"WATCHING port={args.port} "
        f"project={baseline_project.get('projectPath')!r} "
        f"elements={current['elementCount']} "
        f"interval={args.interval}s"
    )
    print(f"LATEST: {latest_path}")
    print(f"EVENTS: {events_path}")
    sys.stdout.flush()

    if args.once:
        return 0

    while True:
        time.sleep(args.interval)
        try:
            nxt = snapshot(args.port)
        except Exception as exc:
            event = {
                "timestamp": now_iso(),
                "port": args.port,
                "event": "poll_error",
                "error": str(exc),
            }
            append_jsonl(events_path, event)
            print(f"[{event['timestamp']}] POLL_ERROR: {exc}")
            sys.stdout.flush()
            continue

        if nxt["project"] != baseline_project:
            event = {
                "timestamp": nxt["timestamp"],
                "port": args.port,
                "event": "project_changed",
                "before": baseline_project,
                "after": nxt["project"],
            }
            append_jsonl(events_path, event)
            write_json(latest_path, nxt)
            print(
                f"[{event['timestamp']}] BLOCKED: project changed. "
                "Watcher stopped fail-closed."
            )
            print(
                f"  before={baseline_project.get('projectPath')!r}\n"
                f"  after ={nxt['project'].get('projectPath')!r}"
            )
            return 2

        event = compare(current, nxt)
        if event["added"] or event["removed"] or event["changed"]:
            append_jsonl(events_path, event)
            print_event(event)

        write_json(latest_path, nxt)
        current = nxt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--interval", type=float, default=DEFAULT_INTERVAL)
    parser.add_argument(
        "--expect-project-substring",
        default=None,
        help="Fail closed unless projectPath contains this text.",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Write one snapshot and exit.",
    )
    args = parser.parse_args()

    if args.interval < 0.5:
        raise SystemExit("--interval must be >= 0.5 seconds")

    try:
        raise SystemExit(run(args))
    except KeyboardInterrupt:
        print("\nWATCH STOPPED")
        raise SystemExit(0)
    except Exception as exc:
        print(
            json.dumps(
                {"status": "BLOCKED", "error": str(exc)},
                ensure_ascii=False,
                indent=2,
            )
        )
        raise SystemExit(2)


if __name__ == "__main__":
    main()
