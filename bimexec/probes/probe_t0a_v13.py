#!/usr/bin/env python3
"""BIMEXEC T0A v1.3 runner.

Patches the v1.2 probe at import time with the AC29/Tapir 1.5.9 compatibility
layer. T0A remains read-only. No geometry or property writes are performed.
"""
from __future__ import annotations

import probe_t0a as probe
from backends_v13 import (
    PROBE_VERSION,
    TAPIR_READ_COMMANDS_V13,
    build_backends_v13,
    discover_ports_v13,
)

probe.PROBE_VERSION = PROBE_VERSION
probe.TAPIR_READ_COMMANDS = TAPIR_READ_COMMANDS_V13
probe.build_backends = build_backends_v13
probe.discover_ports = discover_ports_v13


def _minimal_payload_v13(cmd: str) -> dict:
    if cmd == "GetElementsByType":
        return {"elementType": "Wall"}
    if cmd == "GetDetailsOfElements":
        # Empty list is read-only and valid for a command availability check.
        return {"elements": []}
    if cmd == "GetPropertyValuesOfElements":
        return {"elements": [], "properties": []}
    return {}


probe._minimal_payload = _minimal_payload_v13

if __name__ == "__main__":
    raise SystemExit(probe.main())
