"""Read-only Archicad instance discovery; intentionally no implicit project selection.

Inspired by MultiConn's explicit multi-instance metadata, but uses APA's existing
native API transport. This module does not import or execute arbitrary commands.
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable

from archicad_native_api import ArchicadAPIError, api_request, tapir

DEFAULT_PORTS = tuple(range(19723, 19733))
MIN_PORT = 19720
MAX_PORT = 19820
MAX_PROBES = 16
MAX_RESPONSE = 16384


def query_identity(port: int) -> dict:
    """Fetch only non-mutating identity commands through APA's loopback transport."""
    product = api_request(port, "API.GetProductInfo", {}, timeout=2, max_response=MAX_RESPONSE)
    project = tapir(port, "GetProjectInfo", {}, timeout=2, max_response=MAX_RESPONSE)
    addon = tapir(port, "GetAddOnVersion", {}, timeout=2, max_response=MAX_RESPONSE)
    return {"product": product, "project": project, "addon": addon}


def _validate_ports(ports):
    if not isinstance(ports, (tuple, list)) or not 1 <= len(ports) <= MAX_PROBES:
        raise ValueError("APA_DISCOVERY_PORT_COUNT_INVALID")
    if any(type(p) is not int or not MIN_PORT <= p <= MAX_PORT for p in ports):
        raise ValueError("APA_DISCOVERY_PORT_RANGE_INVALID")
    if len(set(ports)) != len(ports):
        raise ValueError("APA_DISCOVERY_DUPLICATE_PORTS")
    return tuple(ports)


def inspect(port, *, transport: Callable[[int], dict] = query_identity):
    try:
        raw = transport(port)
    except ArchicadAPIError as exc:
        return {"port": port, "status": "UNAVAILABLE", "reason": exc.code}
    except (OSError, TimeoutError, ValueError, TypeError, KeyError):
        return {"port": port, "status": "UNAVAILABLE", "reason": "APA_DISCOVERY_FAILED"}
    try:
        product, project, addon = (raw[key] for key in ("product", "project", "addon"))
        path = project.get("projectPath")
        version = product.get("version")
        tapir_version = addon.get("version")
        if (type(version) is not int or version < 25 or
                not isinstance(path, str) or not Path(path).is_absolute() or
                not path.lower().endswith(".pln") or
                project.get("isUntitled") is not False or
                project.get("isTeamwork") is not False or
                not isinstance(tapir_version, str) or not tapir_version):
            raise ValueError("APA_DISCOVERY_METADATA_INVALID")
        return {"port": port, "status": "IDENTIFIED",
                "projectPath": path, "archicadVersion": version,
                "archicadBuild": product.get("buildNumber"),
                "tapirVersion": tapir_version, "modelWrites": 0}
    except (ValueError, TypeError, KeyError, AttributeError):
        return {"port": port, "status": "UNAVAILABLE", "reason": "APA_DISCOVERY_METADATA_INVALID"}


class ArchicadInstanceDiscovery:
    def __init__(self, *, transport=query_identity):
        self.transport = transport

    def perform(self, operation, ports=None, expected_project=None,
                expected_archicad_version=None, expected_tapir_version=None):
        try:
            if operation not in {"list", "match"}:
                raise ValueError("APA_DISCOVERY_READ_ONLY")
            selected = _validate_ports(DEFAULT_PORTS if ports is None else ports)
            if operation == "list":
                if any(value is not None for value in
                       (expected_project, expected_archicad_version, expected_tapir_version)):
                    raise ValueError("APA_DISCOVERY_LIST_ARGUMENTS_INVALID")
                records = [inspect(port, transport=self.transport) for port in selected]
                return {"status": "APA_INSTANCES_SCANNED", "instances": records,
                        "inspectedPorts": list(selected), "modelWrites": 0,
                        "autoSelection": False}
            if len(selected) != 1 or type(expected_archicad_version) is not int or (
                    not isinstance(expected_tapir_version, str) or not expected_tapir_version) or (
                    not isinstance(expected_project, str) or not expected_project) or (
                    not Path(expected_project).is_absolute() or
                    Path(expected_project).suffix.lower() != ".pln"):
                raise ValueError("APA_DISCOVERY_EXPLICIT_PROJECT_PIN_REQUIRED")
            record = inspect(selected[0], transport=self.transport)
            if record["status"] != "IDENTIFIED":
                raise ValueError("APA_DISCOVERY_INSTANCE_UNAVAILABLE")
            actual = record["projectPath"].casefold()
            expected = expected_project.casefold()
            if (actual != expected or record["archicadVersion"] != expected_archicad_version
                    or record["tapirVersion"] != expected_tapir_version):
                raise ValueError("APA_DISCOVERY_WRONG_INSTANCE")
            return {"status": "APA_INSTANCE_IDENTITY_MATCH", "identity": record,
                    "modelWrites": 0, "writePermission": False,
                    "nativeReadbackVerified": False}
        except (TypeError, ValueError) as exc:
            return {"status": "BLOCKED", "reason": str(exc), "modelWrites": 0}
