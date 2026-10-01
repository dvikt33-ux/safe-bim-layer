from __future__ import annotations

import argparse
import json
import socket
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_HOST = "127.0.0.1"
DEFAULT_START = 19723
DEFAULT_END = 19743


@dataclass
class Probe:
    port: int
    http_alive: bool
    tapir_registered: bool
    response: dict[str, Any] | None = None
    error: str | None = None


def addon_call(host: str, port: int, command: str, params: dict[str, Any] | None = None, timeout: float = 1.5) -> dict[str, Any]:
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
    request = urllib.request.Request(
        f"http://{host}:{port}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def tcp_open(host: str, port: int, timeout: float = 0.25) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def is_registered_response(response: dict[str, Any]) -> bool:
    if response.get("succeeded") is True:
        return True
    if "result" in response and "error" not in response:
        return True
    error = response.get("error")
    if isinstance(error, dict) and int(error.get("code", 0) or 0) == 4010:
        return False
    return False


def probe(host: str, port: int) -> Probe:
    if not tcp_open(host, port):
        return Probe(port=port, http_alive=False, tapir_registered=False, error="closed")
    try:
        response = addon_call(host, port, "GetAddOnVersion")
    except urllib.error.HTTPError as exc:
        return Probe(port=port, http_alive=True, tapir_registered=False, error=f"HTTP {exc.code}")
    except Exception as exc:
        return Probe(port=port, http_alive=True, tapir_registered=False, error=repr(exc))
    return Probe(
        port=port,
        http_alive=True,
        tapir_registered=is_registered_response(response),
        response=response,
    )


def response_body(response: dict[str, Any]) -> dict[str, Any]:
    value = response.get("result", {}).get("addOnCommandResponse", {})
    return value if isinstance(value, dict) else {}


def main() -> int:
    parser = argparse.ArgumentParser(description="Find running Archicad JSON API ports and the instance that has TapirCommand registered.")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--start", type=int, default=DEFAULT_START)
    parser.add_argument("--end", type=int, default=DEFAULT_END)
    parser.add_argument("--write", default=".safe_bim_tapir_port", help="File that receives the selected Tapir port.")
    args = parser.parse_args()

    print("SAFE BIM / ARCHICAD PORT SCAN")
    print(f"Host: {args.host}")
    print(f"Ports: {args.start}..{args.end}")
    print()

    probes = [probe(args.host, port) for port in range(args.start, args.end + 1)]
    live = [item for item in probes if item.http_alive]
    tapir = [item for item in probes if item.tapir_registered]

    for item in probes:
        if not item.http_alive:
            continue
        if item.tapir_registered:
            marker = "TAPIR"
        else:
            marker = "ARCHICAD/OTHER"
        print(f"{item.port}: {marker}")
        if item.response is not None:
            print(json.dumps(item.response, ensure_ascii=False, indent=2))
        elif item.error:
            print("  error:", item.error)
        print()

    print("=" * 72)
    print("SUMMARY")
    print("=" * 72)
    print("Live JSON/API-like ports:", [item.port for item in live])
    print("Tapir ports:", [item.port for item in tapir])

    if not live:
        print("RESULT: no Archicad JSON API port was reachable in the scanned range.")
        return 3

    if not tapir:
        print("RESULT: Archicad is reachable, but TapirCommand.GetAddOnVersion is not registered on any scanned instance.")
        print("The patched APX is therefore not loaded in the running Archicad instance(s), or the active instance is outside this port range.")
        return 4

    if len(tapir) > 1:
        print("RESULT: multiple Tapir-enabled Archicad instances found; project information follows so the correct one can be selected.")
        for item in tapir:
            try:
                response = addon_call(args.host, item.port, "GetProjectInfo", timeout=3.0)
                print(f"PORT {item.port} PROJECT:")
                print(json.dumps(response, ensure_ascii=False, indent=2))
            except Exception as exc:
                print(f"PORT {item.port} GetProjectInfo failed: {exc!r}")
        return 5

    selected = tapir[0].port
    output = Path(args.write).resolve()
    output.write_text(str(selected) + "\n", encoding="utf-8")

    print(f"RESULT: Tapir found on port {selected}.")
    print("Saved port to:", output)
    print()
    print("PowerShell for this session:")
    print(f'$env:SAFE_BIM_TAPIR_PORT = "{selected}"')
    print()

    try:
        response = addon_call(args.host, selected, "GetProjectInfo", timeout=3.0)
        print("PROJECT ON SELECTED PORT:")
        print(json.dumps(response, ensure_ascii=False, indent=2))
    except Exception as exc:
        print("GetProjectInfo failed after Tapir detection:", repr(exc))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
