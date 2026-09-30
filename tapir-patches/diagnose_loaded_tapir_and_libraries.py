from __future__ import annotations

import json
import urllib.request
from typing import Any

BASE = "http://127.0.0.1:19723"


def raw_call(command: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = {
        "command": "API.ExecuteAddOnCommand",
        "parameters": {
            "addOnCommandId": {
                "commandNamespace": "TapirCommand",
                "commandName": command,
            },
            "addOnCommandParameters": params or {},
        },
    }
    req = urllib.request.Request(
        BASE,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as response:
        return json.loads(response.read().decode("utf-8"))


def show(command: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    print()
    print("=" * 72)
    print(command)
    print("=" * 72)
    response = raw_call(command, params)
    print(json.dumps(response, ensure_ascii=False, indent=2))
    if "error" in response:
        print("[FAIL] top-level API error; do NOT interpret missing result as an empty inventory")
    else:
        print("[PASS] raw API call returned a result")
    return response


def main() -> int:
    print("SAFE BIM / TAPIR RAW DIAGNOSTIC")
    print("Bridge:", BASE)

    responses = {}
    responses["GetAddOnVersion"] = show("GetAddOnVersion")
    responses["GetProjectInfo"] = show("GetProjectInfo")
    responses["GetLibraries"] = show("GetLibraries")
    responses["GetAvailableLibraryParts"] = show("GetAvailableLibraryParts", {})
    responses["GetAvailableWindowLibraryParts"] = show(
        "GetAvailableLibraryParts",
        {"filterByTypeId": "Window"},
    )

    failed = [name for name, response in responses.items() if "error" in response]

    print()
    print("=" * 72)
    print("SUMMARY")
    print("=" * 72)
    if failed:
        print("Commands with top-level errors:")
        for name in failed:
            print(" -", name)
        print()
        print("The previous '0 libraries / 0 window parts' result is NOT trustworthy until these errors are resolved.")
        return 2

    print("All diagnostic commands returned result objects.")
    print("Only now is an empty library/library-part list a confirmed empty inventory.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
