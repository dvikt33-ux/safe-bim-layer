"""UI-safe read-only status projection for the Safe BIM control surface.

The projection consumes an already-built ``BridgeHost.status()`` dictionary.
It performs no I/O, starts no bridge instance, calls no Archicad API and
contains no mutation path.
"""
from __future__ import annotations

from copy import deepcopy

from sync_bridge.connections import STATUSES

CONTROL_STATUS_VERSION = 1


def build_control_status(host_status: dict) -> dict:
    """Return the minimal status contract exposed to local UI surfaces.

    Machine-local paths, credentials, tokens, SIDs and raw backend payloads are
    intentionally not copied into the result.
    """
    if not isinstance(host_status, dict):
        raise TypeError("host_status must be a dict")

    source = deepcopy(host_status)
    running = source.get("running") is True
    bridge = source.get("bridge") if isinstance(source.get("bridge"), dict) else {}
    binding = source.get("archicad") if isinstance(source.get("archicad"), dict) else {}
    connections = bridge.get("connections") if isinstance(bridge.get("connections"), dict) else {}

    bridge_channel = _channel(
        connections,
        "BRIDGE",
        fallback_status="CONNECTED" if running else "OFFLINE",
        fallback_detail="runtime" if running else "stopped",
    )
    archicad_channel = _channel(
        connections,
        "ARCHICAD",
        fallback_status="CONNECTED" if binding else "OFFLINE",
        fallback_detail="live binding" if binding else "not connected",
    )
    remote_channel = _channel(
        connections,
        "REMOTE",
        fallback_status="CONNECTING" if running else "OFFLINE",
        fallback_detail="",
    )
    ai_channel = _channel(
        connections,
        "AI",
        fallback_status="CONNECTING" if running else "OFFLINE",
        fallback_detail="",
    )

    return {
        "schemaVersion": CONTROL_STATUS_VERSION,
        "host": {
            "status": _text(source.get("hostStatus")),
            "running": running,
            "pipeOpen": source.get("pipeOpen") is True,
        },
        "project": {
            "name": _text(binding.get("projectName")),
            "logicalProjectId": _text(binding.get("logicalProjectId")),
        },
        "archicad": {
            **archicad_channel,
            "instanceId": _text(binding.get("instanceId")),
            "version": _text(binding.get("applicationVersion")),
            "build": _text(binding.get("applicationBuild")),
            "language": _text(binding.get("applicationLanguage")),
        },
        "bridge": {
            **bridge_channel,
            "version": _text(bridge.get("version")),
            "protocolVersion": _integer_or_none(bridge.get("protocolVersion")),
            "ownership": _text(bridge.get("ownership")),
            "leaseState": _text(bridge.get("leaseState")),
            "sqliteLeaseRole": _text(bridge.get("sqliteLeaseRole")),
            "archicadWriteApi": bridge.get("archicadWriteApi") is True,
        },
        "github": {
            **remote_channel,
            "needsAuth": bridge.get("needsAuth") is True,
            "credentialSource": _credential_source(source.get("credentialSource")),
        },
        "ai": ai_channel,
    }


def _channel(connections: dict, name: str, *, fallback_status: str, fallback_detail: str) -> dict:
    raw = connections.get(name)
    if not isinstance(raw, dict):
        return {"status": fallback_status, "detail": fallback_detail}

    status = raw.get("status")
    if status not in STATUSES:
        status = fallback_status
    detail = raw.get("detail")
    if not isinstance(detail, str):
        detail = ""
    return {"status": status, "detail": detail}


def _text(value):
    return value if isinstance(value, str) and value else None


def _integer_or_none(value):
    return value if type(value) is int and value >= 0 else None


def _credential_source(value):
    # Source labels are useful to the UI; actual credentials never are.
    return value if value in {"environment", "gh-cli", "none", "injected"} else "unknown"
