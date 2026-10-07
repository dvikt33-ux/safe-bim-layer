"""Emit compact JSON context from the local Archicad Tapir watcher.

This helper is read-only. It consumes the files written by
scripts/archicad_change_watch.py and produces a small machine-readable context
suitable for a dispatcher / chat adapter before the next Archicad action.

Usage:
    python scripts/archicad_watch_context.py --port 19725
    python scripts/archicad_watch_context.py --port 19725 --tail 10
"""
from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path
from typing import Any

WATCH_DIR = Path(
    os.environ.get(
        "SAFE_BIM_MVP_EVIDENCE",
        Path(tempfile.gettempdir()) / "safe-bim-mvp-evidence",
    )
) / "archicad-watch"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_jsonl_tail(path: Path, limit: int) -> list[Any]:
    if not path.is_file() or limit <= 0:
        return []
    rows: list[Any] = []
    with path.open("r", encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                rows.append({"event": "invalid_jsonl_row", "raw": line[-500:]})
    return rows[-limit:]


def compact_event(event: dict) -> dict:
    if event.get("event") in ("project_changed", "poll_error"):
        return event

    return {
        "timestamp": event.get("timestamp"),
        "elementCountBefore": event.get("elementCountBefore"),
        "elementCountAfter": event.get("elementCountAfter"),
        "added": [
            {
                "guid": row.get("guid"),
                "type": row.get("type"),
                "floorIndex": row.get("floorIndex"),
                "boundingBox": row.get("boundingBox"),
            }
            for row in event.get("added", [])
        ],
        "removed": [
            {
                "guid": row.get("guid"),
                "type": row.get("type"),
                "floorIndex": row.get("floorIndex"),
                "boundingBox": row.get("boundingBox"),
            }
            for row in event.get("removed", [])
        ],
        "changed": [
            {
                "guid": row.get("guid"),
                "before": row.get("before"),
                "after": row.get("after"),
            }
            for row in event.get("changed", [])
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=19723)
    parser.add_argument("--tail", type=int, default=20)
    args = parser.parse_args()

    latest_path = WATCH_DIR / f"latest-{args.port}.json"
    events_path = WATCH_DIR / f"events-{args.port}.jsonl"

    if not latest_path.is_file():
        raise SystemExit(
            json.dumps(
                {
                    "status": "BLOCKED",
                    "reason": "watcher_latest_missing",
                    "expected": str(latest_path),
                    "hint": (
                        "Start scripts/archicad_change_watch.py for this port "
                        "before requesting watcher context."
                    ),
                },
                ensure_ascii=False,
                indent=2,
            )
        )

    latest = read_json(latest_path)
    events = read_jsonl_tail(events_path, args.tail)

    output = {
        "status": "PASS",
        "source": "archicad_change_watch",
        "port": args.port,
        "latestTimestamp": latest.get("timestamp"),
        "project": latest.get("project"),
        "activeStory": latest.get("activeStory"),
        "elementCount": latest.get("elementCount"),
        "stories": [
            {
                "index": row.get("index"),
                "level": row.get("level"),
                "height": row.get("height"),
                "name": row.get("name"),
            }
            for row in latest.get("stories", [])
        ],
        "recentEventCount": len(events),
        "recentEvents": [compact_event(row) for row in events],
        "evidence": {
            "latest": str(latest_path),
            "events": str(events_path),
        },
    }

    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
