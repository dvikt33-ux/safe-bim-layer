#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Read-only inventory of the currently opened Archicad document.

Scopes:
- current: elements of the current Archicad database.
- whole-model: model elements across all StoryItem databases in the Project Map,
  deduplicated by GUID.

Output: GUID + native element type + story index + counts by type.
No BIM mutations are performed.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

PORT_MIN = 19723
PORT_MAX = 19743
DEFAULT_CHUNK = 500
DB_CHUNK = 100


def _post(port: int, payload: dict, timeout: float = 20.0) -> dict:
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


def _iter_tree_items(items):
    if not isinstance(items, list):
        return
    for item in items:
        if not isinstance(item, dict):
            continue
        yield item
        children = item.get("children")
        if isinstance(children, list):
            yield from _iter_tree_items(children)


def _story_databases(port: int) -> tuple[list[dict], int]:
    tree_result = _post(
        port,
        {
            "command": "API.GetNavigatorItemTree",
            "parameters": {"navigatorTreeId": {"type": "ProjectMap"}},
        },
    )
    navigator_tree = tree_result.get("navigatorTree")
    if not isinstance(navigator_tree, dict):
        raise RuntimeError("API.GetNavigatorItemTree returned no navigatorTree")
    root = navigator_tree.get("rootItem")
    if not isinstance(root, dict):
        raise RuntimeError("Project Map navigator tree has no rootItem")

    nav_ids = []
    for item in _iter_tree_items(root.get("children", [])):
        if item.get("itemType") != "StoryItem":
            continue
        nav_id = item.get("navigatorItemId")
        if isinstance(nav_id, dict):
            nav_ids.append(nav_id)

    if not nav_ids:
        raise RuntimeError("No StoryItem databases found in Project Map")

    databases = []
    seen_db_guids = set()
    for start in range(0, len(nav_ids), DB_CHUNK):
        response = _run_tapir(
            port,
            "GetDatabaseIdFromNavigatorItemId",
            {"navigatorItemIds": nav_ids[start:start + DB_CHUNK]},
        )
        batch = response.get("databases")
        if not isinstance(batch, list):
            raise RuntimeError(
                "GetDatabaseIdFromNavigatorItemId returned no databases list"
            )
        for item in batch:
            if not isinstance(item, dict):
                continue
            db_id = item.get("databaseId")
            if not isinstance(db_id, dict):
                continue
            guid = db_id.get("guid")
            if not isinstance(guid, str) or guid in seen_db_guids:
                continue
            seen_db_guids.add(guid)
            databases.append({"databaseId": {"guid": guid}})

    if not databases:
        raise RuntimeError("StoryItem navigator entries resolved to no usable databases")

    return databases, len(nav_ids)


def _get_elements(port: int, scope: str) -> tuple[list[dict], dict]:
    if scope == "current":
        result = _post(port, {"command": "API.GetAllElements"})
        elements = result.get("elements")
        if not isinstance(elements, list):
            raise RuntimeError("API.GetAllElements returned no 'elements' list")
        return elements, {
            "scope": "current",
            "rawElementOccurrences": len(elements),
            "databaseCount": 1,
        }

    databases, story_item_count = _story_databases(port)
    all_elements = []
    execution_results = []

    for start in range(0, len(databases), DB_CHUNK):
        db_chunk = databases[start:start + DB_CHUNK]
        result = _run_tapir(port, "GetAllElements", {"databases": db_chunk})
        elements = result.get("elements")
        if not isinstance(elements, list):
            raise RuntimeError(
                f"Tapir GetAllElements returned no elements for database chunk {start}"
            )
        all_elements.extend(elements)
        per_db = result.get("executionResultForDatabases")
        if isinstance(per_db, list):
            execution_results.extend(per_db)

    # Same model element can be visible/listed from more than one StoryItem database.
    # Whole-model inventory is an element inventory, not a view-occurrence inventory.
    unique_by_guid = {}
    guidless = []
    for element in all_elements:
        guid = _extract_guid(element)
        if guid is None:
            guidless.append(element)
        else:
            unique_by_guid.setdefault(guid, element)

    elements = list(unique_by_guid.values()) + guidless
    return elements, {
        "scope": "whole-model",
        "storyNavigatorItemCount": story_item_count,
        "databaseCount": len(databases),
        "rawElementOccurrences": len(all_elements),
        "duplicateOccurrencesRemoved": len(all_elements) - len(elements),
        "databaseExecutionResults": execution_results,
    }


def _get_details(port: int, elements: list[dict], chunk_size: int):
    inventory = []
    counts = Counter()
    missing_details = 0

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
                missing_details += 1
            elif isinstance(raw_detail, dict):
                element_type = raw_detail.get("type") or "UNKNOWN"
                story = raw_detail.get("floorIndex")
                if element_type == "UNKNOWN":
                    missing_details += 1
            else:
                element_type = "UNKNOWN"
                story = None
                missing_details += 1

            counts[element_type] += 1
            inventory.append({"guid": guid, "type": element_type, "story": story})

    return inventory, counts, missing_details


def collect_inventory(
    port: int,
    chunk_size: int = DEFAULT_CHUNK,
    scope: str = "current",
) -> dict:
    elements, scope_meta = _get_elements(port, scope)
    inventory, counts, missing_details = _get_details(port, elements, chunk_size)

    return {
        "port": port,
        "scope": scope_meta,
        "project": _get_project_info(port),
        "total": len(inventory),
        "missingDetails": missing_details,
        "countsByType": dict(sorted(counts.items(), key=lambda item: item[0].lower())),
        "elements": inventory,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Read Archicad inventory (GUID + type + story), read-only."
    )
    parser.add_argument("--port", type=int, help="Archicad JSON API port, e.g. 19723")
    parser.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK)
    parser.add_argument(
        "--scope",
        choices=["current", "whole-model"],
        default="current",
        help=(
            "current = active Archicad database; "
            "whole-model = all Project Map StoryItem databases, deduplicated by GUID"
        ),
    )
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
        result = collect_inventory(port, args.chunk_size, args.scope)
    except (RuntimeError, URLError, HTTPError, TimeoutError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    output_path = os.path.abspath(args.output)
    temp_path = output_path + ".tmp"
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(temp_path, output_path)

    scope = result["scope"]
    print(f"Archicad port: {result['port']}")
    print(f"Scope: {scope['scope']}")
    if scope["scope"] == "whole-model":
        print(f"Story databases: {scope['databaseCount']}")
        print(f"Raw occurrences: {scope['rawElementOccurrences']}")
        print(f"Duplicate occurrences removed: {scope['duplicateOccurrencesRemoved']}")
    print(f"Total unique elements: {result['total']}")
    print(f"Missing details: {result['missingDetails']}")
    for element_type, count in result["countsByType"].items():
        print(f"  {element_type}: {count}")
    print(f"Saved: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
