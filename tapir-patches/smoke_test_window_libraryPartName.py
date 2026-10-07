from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path
from typing import Any

DEFAULT_BRIDGE = "http://127.0.0.1:19723"


def call(base_url: str, command: str, params: dict[str, Any]) -> dict[str, Any]:
    body = {
        "command": "API.ExecuteAddOnCommand",
        "parameters": {
            "addOnCommandId": {
                "commandNamespace": "TapirCommand",
                "commandName": command,
            },
            "addOnCommandParameters": params,
        },
    }
    req = urllib.request.Request(
        base_url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as response:
        return json.loads(response.read().decode("utf-8"))


def response_body(response: dict[str, Any]) -> dict[str, Any]:
    value = response.get("result", {}).get("addOnCommandResponse", {})
    return value if isinstance(value, dict) else {}


def read_one(base_url: str, guid: str) -> dict[str, Any]:
    response = call(
        base_url,
        "GetDetailsOfElements",
        {"elements": [{"elementId": {"guid": guid}}]},
    )
    rows = response_body(response).get("detailsOfElements", [])
    if len(rows) != 1:
        raise RuntimeError(f"read-back expected one element, got {len(rows)}")
    return rows[0]


def extract_created_guid(response: dict[str, Any]) -> str:
    rows = response_body(response).get("elements", [])
    errors = [row.get("error") for row in rows if isinstance(row, dict) and "error" in row]
    if errors:
        raise RuntimeError("CreateWindows returned error: " + json.dumps(errors, ensure_ascii=False, indent=2))
    guids = []
    for row in rows:
        try:
            guids.append(row["elementId"]["guid"])
        except Exception:
            pass
    if len(guids) != 1:
        raise RuntimeError(f"expected exactly one created window, got {guids}")
    return guids[0]


def load_wall_guid(state_path: Path, state_key: str) -> str:
    state = json.loads(state_path.read_text(encoding="utf-8"))
    entry = state.get("steps", {}).get(state_key)
    if not isinstance(entry, dict) or not entry.get("guid"):
        raise RuntimeError(f"state key {state_key!r} has no GUID in {state_path}")
    return str(entry["guid"])


def list_windows(base_url: str) -> list[dict[str, Any]]:
    response = call(base_url, "GetAvailableLibraryParts", {"filterByTypeId": "Window"})
    return response_body(response).get("libraryParts", [])


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Smoke-test patched Tapir CreateWindows.libraryPartName. Creates ONE real Window only when --library-part-name is supplied."
    )
    parser.add_argument("--bridge", default=DEFAULT_BRIDGE)
    parser.add_argument("--library-part-name")
    parser.add_argument(
        "--state",
        default="gothic_tower_top_stage_state.json",
        help="Tower state JSON used to resolve the host wall.",
    )
    parser.add_argument("--wall-state-key", default="WALL:SIDE_0")
    parser.add_argument("--center-offset", type=float, default=2.5)
    parser.add_argument("--sill-height", type=float, default=2.0)
    parser.add_argument("--width", type=float)
    parser.add_argument("--height", type=float)
    args = parser.parse_args()

    parts = list_windows(args.bridge)
    print(f"Available Window library parts: {len(parts)}")

    if not args.library_part_name:
        for part in parts[:40]:
            print(
                " -",
                part.get("documentName") or part.get("name") or part.get("fileName"),
                "| file=",
                part.get("fileName"),
                "| index=",
                part.get("index"),
            )
        print()
        print("No write performed. Re-run with --library-part-name <exact documentName> to create one test Window.")
        return 0

    target = args.library_part_name.casefold()
    matching = [
        part
        for part in parts
        if str(part.get("documentName") or part.get("name") or "").casefold() == target
    ]
    if len(matching) != 1:
        raise RuntimeError(
            f"Expected exactly one Window library part named {args.library_part_name!r}, found {len(matching)}. "
            "Run without --library-part-name to list available Window parts."
        )

    state_path = Path(args.state).resolve()
    wall_guid = load_wall_guid(state_path, args.wall_state_key)
    wall = read_one(args.bridge, wall_guid)
    if wall.get("type") != "Wall":
        raise RuntimeError(f"Host GUID {wall_guid} is {wall.get('type')}, not Wall")

    item: dict[str, Any] = {
        "ownerWallId": {"guid": wall_guid},
        "centerOffset": float(args.center_offset),
        "sillHeight": float(args.sill_height),
        "libraryPartName": args.library_part_name,
    }
    if args.width is not None:
        item["width"] = float(args.width)
    if args.height is not None:
        item["height"] = float(args.height)

    print("Creating ONE hosted Window with payload:")
    print(json.dumps(item, ensure_ascii=False, indent=2))

    response = call(args.bridge, "CreateWindows", {"windowsData": [item]})
    guid = extract_created_guid(response)
    detail = read_one(args.bridge, guid)

    if detail.get("type") != "Window":
        raise RuntimeError(f"Created element type is {detail.get('type')!r}, expected 'Window'")

    details = detail.get("details", {})
    owner = details.get("ownerElementId", {}).get("guid")
    if owner != wall_guid:
        raise RuntimeError(f"Owner mismatch: expected {wall_guid}, got {owner}")

    lib_part = details.get("libPart", {})
    actual_name = lib_part.get("name") or lib_part.get("documentName")
    if actual_name != args.library_part_name:
        raise RuntimeError(
            f"Library part mismatch: expected {args.library_part_name!r}, got {actual_name!r}; libPart={lib_part!r}"
        )

    print()
    print("========================================")
    print("HOSTED WINDOW SMOKE TEST: PASS")
    print("========================================")
    print("GUID:", guid)
    print("Owner wall:", owner)
    print("Library part:", actual_name)
    print("Archicad element type: Window")
    print()
    print("This script intentionally leaves the single verified test Window in place and does not delete any Morph prototype.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
