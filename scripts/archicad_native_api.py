"""Wire transport shared by the APA router, SceneWriter and read adapters."""
from __future__ import annotations

import http.client
import json
import urllib.request


class ArchicadAPIError(RuntimeError):
    def __init__(self, code, command, detail=None):
        super().__init__(f"{code}: {command}" + (f": {detail!r}" if detail is not None else ""))
        self.code = code
        self.command = command
        self.detail = detail


def api_request(port, command, params=None, *, timeout=15, max_response=None):
    if type(port) is not int or not 1 <= port <= 65535:
        raise ValueError("INVALID_ARCHICAD_PORT")
    if type(timeout) not in (int, float) or not 0 < timeout <= 120:
        raise ValueError("INVALID_HTTP_TIMEOUT")
    if params is not None and not isinstance(params, dict):
        raise ValueError("COMMAND_PARAMETERS_OBJECT_REQUIRED")
    body = {"command": command, "parameters": {} if params is None else params}
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}", method="POST",
        data=json.dumps(body, ensure_ascii=False, allow_nan=False).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read() if max_response is None else response.read(max_response + 1)
    except (OSError, http.client.HTTPException) as exc:
        raise ArchicadAPIError("ARCHICAD_CONNECTION_FAILED", command, str(exc)) from exc
    if max_response is not None and len(raw) > max_response:
        raise ArchicadAPIError("ARCHICAD_RESPONSE_TOO_LARGE", command)
    try:
        envelope = json.loads(raw)
    except (UnicodeError, ValueError) as exc:
        raise ArchicadAPIError("ARCHICAD_RESPONSE_INVALID", command) from exc
    if not isinstance(envelope, dict) or type(envelope.get("succeeded")) is not bool:
        raise ArchicadAPIError("ARCHICAD_RESPONSE_INVALID", command)
    if not envelope["succeeded"]:
        raise ArchicadAPIError("ARCHICAD_COMMAND_REJECTED", command, envelope.get("error"))
    result = envelope.get("result")
    if not isinstance(result, dict):
        raise ArchicadAPIError("ARCHICAD_RESPONSE_INVALID", command)
    return result


def addon_id(command, namespace="TapirCommand"):
    if not isinstance(namespace, str) or not namespace or "." in namespace:
        raise ValueError("INVALID_ADDON_NAMESPACE")
    if not isinstance(command, str) or not command or "." in command:
        raise ValueError("INVALID_ADDON_COMMAND_NAME")
    return {"commandNamespace": namespace, "commandName": command}


def tapir(port, command, params=None, *, timeout=15, namespace="TapirCommand", max_response=None):
    if params is not None and not isinstance(params, dict):
        raise ValueError("COMMAND_PARAMETERS_OBJECT_REQUIRED")
    result = api_request(port, "API.ExecuteAddOnCommand", {
        "addOnCommandId": addon_id(command, namespace),
        "addOnCommandParameters": {} if params is None else params,
    }, timeout=timeout, max_response=max_response)
    payload = result.get("addOnCommandResponse")
    if not isinstance(payload, dict):
        raise ArchicadAPIError("ARCHICAD_ADDON_RESPONSE_MISSING", command)
    return payload


def native_command(port, command, params=None, *, timeout=15, max_response=None):
    if command.startswith("API."):
        return api_request(port, command, params, timeout=timeout, max_response=max_response)
    namespace = "TapirCommand"
    if command.startswith("AddOn."):
        parts = command.split(".")
        if len(parts) != 3:
            raise ValueError("INVALID_PROVIDER_COMMAND_ID")
        _, namespace, command = parts
    return tapir(port, command, params, namespace=namespace, timeout=timeout, max_response=max_response)
