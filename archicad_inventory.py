#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Read-only inventory of the currently opened Archicad document.

Output: GUID + native element type + story index + counts by type.
Uses Archicad's built-in JSON API plus Tapir GetDetailsOfElements.
No BIM mutations are performed.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from urllib.error import URLError, HTTPError
from urllib.request import Request, urlopen

PORT_MIN = 19723
PORT_MAX = 19743
DEFAULT_CHUNK = 500


def _post(port: int, payload: dict, timeout: float = 8.0) -> dict:
    req = Request(
        f"http://127.0.0.1:{port}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(req, timeout=timeout) as response:
        data = json.loads(response.read().decode("utf-8-sig"))

    if not data.get("succeeded", False):
        err = data.get("error") or {}
        code = err.get("code", "UNKNOWN")
        message = err.get("message", "Archicad command failed")
        raise RuntimeError(f"{code}: {message}")

    result = data.get("result")
    return result if isinstance(result, dict) else {}


def _is_alive(port: int) -> bool:
    try:
        _post(port, {"command": "API.IsAlive"}, timeout=0.7)
        return True
    except Exception:
        return False


def _detect_port(explicit_port: int | None) -> int:
    if explicit_port is not None:
        if not _is_alive(explicit_port):
            raise RuntimeError(f"Archicad does not answer on port {explicit_port}")
        return explicit_port

    active = [port for port in range(PORT_MIN, PORT_MAX + 1) if _is_alive(port)]
    if not active:
        raise RuntimeError("No active Archicad JSON API port found (19723-19743)")
    if len(active) > 1:
        raise RuntimeError(
            "Several Archicad instances are active: "
            + ", ".join(map(str, active))
            + ". Re-run with --port <PORT>."
        )
    return active[0]


def _run_tapir(port: int, command_name: str, parameters: dict) -> dict:
    result = _post(
        port,
        {
            "command": "API.ExecuteAddOnCommand",
            "parameters": {
                "addOnCommandId": {
                    "commandNamespace": "TapirCommand",
                    "commandName": command_name,
                },
                "addOnCommandParameters": parameters,
            },
        },
    )
    wrapped = result.get("addOnCommandResponse")
    return wrapped if isinstance(wrapped, dict) else result


def _extract_guid(element: dict) -> str | None:
    if not isinstance(element, dict):
        return None
    element_id = element.get("elementId")
    if isinstance(element_id, dict):
        guid = element_id.get("guid")
        if isinstance(guid, str):
            return guid
    guid = element.get("guid")
    return guid if isinstance(guid, str) else None


def _get_project_info(port: int) -> dict:
    try:
        return _run_tapir(port, "GetProjectInfo", {})
    except Exception:
        return {}


def collect_inventory(port: int, chunk_size: int = DEFAULT_CHUNK) -> dict:
    all_result = _post(port, {"command": "API.GetAllElements"})
    elements = all_result.get("elements")
    if not isinstance(elements, list):
        raise RuntimeError("API.GetAllElements returned no 'elements' list")

    inventory = []
    counts = Counter()

    for start in range(0, len(elements), chunk_size):
        chunk = elements[start:start + chunk_size]
        details_result = _run_tapir(
            port,
            "GetDetailsOfElements",
            {
                "elements": chunk,
                "fields": ["type", "floorIndex"],
            },
        )
        details = details_result.get("detailsOfElements")
        if not isinstance(details, list):
            raise RuntimeError(
                f"GetDetailsOfElements returned no 'detailsOfElements' list for chunk starting at {start}"
            )
        if len(details) != len(chunk):
            raise RuntimeError(
                f"GetDetailsOfElements count mismatch at chunk {start}: "
                f"requested {len(chunk)}, received {len(details)}"
            )

        for raw_element, raw_detail in zip(chunk, details):
            guid = _extract_guid(raw_element)
            if raw_detail is None:
                element_type = "UNKNOWN"
                story = None
            elif isinstance(raw_detail, dict):
                element_type = raw_detail.get("type") or "UNKNOWN"
                story = raw_detail.get("floorIndex")
            else:
                element_type = "UNKNOWN"
                story = None

            counts[element_type] += 1
            inventory.append(
                {
                    "guid": guid,
                    "type": element_type,
                    "story": story,
                }
            )

    project_info = _get_project_info(port)
    return {
        "port": port,
        "project": project_info,
        "total": len(inventory),
        "countsByType": dict(sorted(counts.items(), key=lambda item: item[0].lower())),
        "elements": inventory,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Read current Archicad model inventory (GUID + type + story), read-only."
    )
    parser.add_argument("--port", type=int, help="Archicad JSON API port, e.g. 19723")
    parser.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK)
    parser.add_argument(
        "--output",
        default="archicad_inventory.json",
        help="JSON output path (default: archicad_inventory.json)",
    )
    args = parser.parse_args()

    if args.chunk_size < 1:
        parser.error("--chunk-size must be >= 1")

    try:
        port = _detect_port(args.port)
        result = collect_inventory(port, args.chunk_size)
    except (RuntimeError, URLError, HTTPError, TimeoutError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    output_path = os.path.abspath(args.output)
    temp_path = output_path + ".tmp"
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(temp_path, output_path)

    print(f"Archicad port: {result['port']}")
    print(f"Total elements: {result['total']}")
    for element_type, count in result["countsByType"].items():
        print(f"  {element_type}: {count}")
    print(f"Saved: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
