"""Compatibility entry point for AC30 typed quantity verification.

The process is pinned to the exact operator-supplied profile and GUID/type
inventory at startup, and checks both before and after every tool call.
It exposes NO creation/modification/deletion commands or arbitrary file paths.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from threading import Lock
from typing import Literal

from apa_ac30_tapir20 import (
    AC30ReadSession, exact_file, fail, hash_file, inputs_file, profile_from_path
)
from apa_control_mcp import run_server, server_for as unified_server

ReadKind = Literal["status", "quantities"]
MAX_MCP_ELEMENTS = 64


class AC30MCPControl:
    def __init__(self, profile, elements, transport=None):
        self.profile = exact_file(str(profile))
        self.elements = exact_file(str(elements))
        self.profile_sha = hash_file(self.profile)
        self.elements_sha = hash_file(self.elements)
        self.transport = transport
        self.lock = Lock()
        self._files_and_inputs()

    def _files_and_inputs(self):
        if (hash_file(self.profile) != self.profile_sha
                or hash_file(self.elements) != self.elements_sha):
            fail("MCP_OPERATOR_INPUT_DRIFT")
        config = profile_from_path(self.profile)
        entries = inputs_file(self.elements)
        if len(entries) > MAX_MCP_ELEMENTS:
            fail("MCP_INPUT_LIMIT_EXCEEDED")
        if (hash_file(self.profile) != self.profile_sha
                or hash_file(self.elements) != self.elements_sha):
            fail("MCP_OPERATOR_INPUT_CHANGED_DURING_CHECK")
        return config, entries

    def read(self, kind: ReadKind):
        if kind not in ("status", "quantities"):
            fail("MCP_UNKNOWN_READ_KIND")
        with self.lock:
            config, entries = self._files_and_inputs()
            session = AC30ReadSession(config, transport=self.transport)
            before = session.guard()
            result = {
                "status": "AC30_MCP_READ_ONLY",
                "readKind": kind,
                "project": before["project"],
                "archicadVersion": before["archicadVersion"],
                "archicadBuild": before["archicadBuild"],
                "tapirVersion": before["tapirVersion"],
                "addonSha256": before["addonSha256"],
                "projectSha256": config["projectSha256"],
                "profileSha256": self.profile_sha,
                "elementsSha256": self.elements_sha,
                "elementCount": len(entries),
                "modelWrites": 0,
                "executionPermission": False,
            }
            if kind == "quantities":
                result["typedGroups"] = session.quantities(entries)
                result["status"] = "AC30_MCP_TYPED_QUANTITIES_PASS"
            after = session.guard()
            if before != after:
                fail("MCP_PROJECT_CHANGED_DURING_READ")
            self._files_and_inputs()
            result["readCommands"] = session.calls
            return result


def server_for(control):
    return unified_server(ac30_quantities=control.read)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--elements", type=Path, required=True)
    parser.add_argument("--port", type=int,
                        help="Optional isolated loopback HTTP port; stdio by default.")
    args = parser.parse_args(argv)
    if args.port is not None and not 1024 <= args.port <= 65535:
        fail("MCP_PORT_OUT_OF_RANGE")
    control = AC30MCPControl(args.profile, args.elements)
    run_server(server_for(control), args.port, max_request_body_size=65_536)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
