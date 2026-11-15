"""Separate read-only Archicad 30 / Tapir 2.0 MCP, not legacy APA MCP.

The process is pinned to the exact operator-supplied profile and GUID/type
inventory at startup, and checks both before and after every tool call.
It exposes NO creation/modification/deletion commands or arbitrary file paths.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from threading import Lock
from typing import Literal

from apa_ac30_tapir20 import (
    AC30ReadSession, exact_file, fail, hash_file, inputs_file, profile_from_path
)

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
    import anyio
    from mcp.server import MCPServer
    from mcp.types import CallToolResult, TextContent, ToolAnnotations

    server = MCPServer("APA AC30 Tapir 2 Read Only")

    @server.tool(annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=False))
    async def apa_ac30_read(kind: ReadKind):
        """Read only the pinned test AC30 model and typed quantity inventory."""
        try:
            row = await anyio.to_thread.run_sync(control.read, kind)
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(row, ensure_ascii=False))],
                structured_content=row)
        except (ValueError, OSError, KeyError, TypeError, RuntimeError) as exc:
            reason = str(exc)
            if not re.fullmatch(r"APA_AC30_[A-Z0-9_]{3,100}", reason):
                reason = "APA_AC30_MCP_READ_BLOCKED_CHECK_LOCAL_EVIDENCE"
            row = {"status": "BLOCKED", "reason": reason, "modelWrites": 0}
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(row))],
                structured_content=row, is_error=True)

    return server


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
    server = server_for(control)
    if args.port is None:
        server.run(transport="stdio")
    else:
        server.run(transport="streamable-http", host="127.0.0.1", port=args.port,
                   stateless_http=True, json_response=True, max_request_body_size=65_536)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
