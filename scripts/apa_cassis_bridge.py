"""Bounded Cassis -> Grasshopper bridge for APA. No native Archicad writes.

Only the exact, reviewed rectangle test graph may be edited. All other
Grasshopper tools remain unavailable through this bridge.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import sys
import time
from urllib.request import Request, urlopen

SCHEMA = "APA_CASSIS_PROFILE_V1"
INTENT_SCHEMA = "apa-gh-command/1"
ENDPOINT = "http://127.0.0.1:3003/mcp/"
PROTOCOL = "2025-06-18"
MAX_RESPONSE = 2_000_000
READ_TOOLS = frozenset({
    "getdocumentinfo", "get_componentcount", "get_allcomponents",
    "getallconnections", "getsolutionstate", "get_component_output",
    "getsystemhealth",
})
RECTANGLE_TYPE = "CurveComponents.Component_Rectangle_OBSOLETE"
SLIDER_TYPE = "Grasshopper.Kernel.Special.GH_NumberSlider"
GUID = re.compile(r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}\Z")
OUTPUT = re.compile(r"APA_Cassis_Rectangle_[A-Za-z0-9_-]{3,64}\.ghx\Z")


def require(condition, code):
    if not condition:
        raise ValueError(code)


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def same_path(left, right):
    return os.path.normcase(os.path.normpath(str(left))).casefold() == \
        os.path.normcase(os.path.normpath(str(right))).casefold()


class CassisClient:
    """Streamable HTTP MCP client. Deliberately fixed to loopback."""

    def __init__(self, root):
        self.root = str(root) if root is not None else None
        self.session = None
        self.seq = 0
        result = self._request("initialize", {
            "protocolVersion": PROTOCOL,
            "capabilities": {},
            "clientInfo": {"name": "APA-Cassis", "version": "0.1"},
        })
        info = result.get("serverInfo", {})
        require(info.get("name") == "Cassis" and info.get("version") == "1.6.0",
                "GH_UNREVIEWED_CASSIS_VERSION")

    def _request(self, method, params):
        self.seq += 1
        data = json.dumps({"jsonrpc": "2.0", "id": self.seq, "method": method,
                           "params": params}, ensure_ascii=False).encode("utf-8")
        require(len(data) <= 32_768, "GH_REQUEST_TOO_LARGE")
        headers = {
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
            "MCP-Protocol-Version": PROTOCOL,
        }
        if self.root is not None:
            headers["X-Cassis-Root"] = self.root
        if self.session:
            headers["Mcp-Session-Id"] = self.session
        request = Request(ENDPOINT, data=data, headers=headers, method="POST")
        with urlopen(request, timeout=12) as response:
            if not self.session:
                self.session = response.headers.get("Mcp-Session-Id")
            payload = response.read(MAX_RESPONSE + 1)
        require(len(payload) <= MAX_RESPONSE, "GH_RESPONSE_TOO_LARGE")
        body = payload.decode("utf-8")
        if body.startswith("data:"):
            events = [row[6:] for row in body.splitlines() if row.startswith("data: ")]
            require(len(events) > 0, "GH_MCP_EVENT_MISSING")
            body = events[0]
        reply = json.loads(body)
        require(reply.get("id") == self.seq, "GH_MCP_ID_MISMATCH")
        if "error" in reply:
            code = reply["error"].get("code", "unknown")
            raise ValueError("GH_MCP_REMOTE_ERROR_" + str(code))
        return reply["result"]

    def tool(self, name, arguments=None):
        result = self._request("tools/call", {"name": name,
                                               "arguments": arguments or {}})
        require(result.get("isError") is not True, "GH_TOOL_REJECTED_" + name.upper())
        rows = result.get("content")
        require(isinstance(rows, list) and len(rows) > 0, "GH_TOOL_EMPTY_RESPONSE")
        value = json.loads(rows[0]["text"])
        require(isinstance(value, dict) and value.get("success") is not False
                and value.get("Success") is not False and value.get("ok") is not False,
                "GH_TOOL_FAILED_" + name.upper())
        return value


class CassisBridge:
    def __init__(self, profile, client_factory=CassisClient):
        self.profile_path = Path(profile).resolve(strict=True)
        raw = self.profile_path.read_bytes()
        require(len(raw) < 64_000, "GH_PROFILE_TOO_LARGE")
        config = json.loads(raw)
        expected = {"schema", "testRoot", "document", "documentSha256",
                    "rectangleId", "widthSliderId", "heightSliderId", "writeEnabled"}
        require(isinstance(config, dict) and set(config) == expected
                and config.get("schema") == SCHEMA
                and type(config.get("writeEnabled")) is bool, "GH_PROFILE_INVALID")
        self.root = Path(config["testRoot"]).resolve(strict=True)
        self.doc = Path(config["document"]).resolve(strict=True)
        require(self.root.is_dir() and self.doc.is_file()
                and self.doc.parent == self.root
                and self.doc.name.startswith("APA_Cassis_")
                and self.doc.suffix.lower() == ".ghx", "GH_TEST_DOCUMENT_SCOPE_INVALID")
        self.expected_sha = config["documentSha256"]
        require(isinstance(self.expected_sha, str) and
                re.fullmatch(r"[a-f0-9]{64}", self.expected_sha) is not None,
                "GH_PROFILE_HASH_INVALID")
        self.ids = {"rectangle": config["rectangleId"],
                    "width": config["widthSliderId"], "height": config["heightSliderId"]}
        require(all(isinstance(v, str) and GUID.fullmatch(v) for v in self.ids.values())
                and len(set(self.ids.values())) == 3, "GH_COMPONENT_IDENTITIES_INVALID")
        self.writes = config["writeEnabled"]
        self.client_factory = client_factory

    def client(self):
        return self.client_factory(self.root)

    def pinned_doc(self, client, *, require_clean=False):
        info = client.tool("getdocumentinfo")
        require(info.get("open") is True and
                same_path(info.get("path", ""), self.doc), "GH_WRONG_ACTIVE_DOCUMENT")
        if require_clean:
            require(info.get("mod") is False and digest(self.doc) == self.expected_sha,
                    "GH_DOCUMENT_SHA_OR_DIRTY_STATE")
        return info

    def verify_graph(self, client):
        listing = client.tool("get_allcomponents")
        rows = listing.get("components", [])
        expected = {
            self.ids["rectangle"]: RECTANGLE_TYPE,
            self.ids["width"]: SLIDER_TYPE,
            self.ids["height"]: SLIDER_TYPE,
        }
        require(isinstance(rows, list) and len(rows) == 3
                and {str(x.get("id")): str(x.get("typeName")) for x in rows} == expected,
                "GH_GRAPH_OWNERSHIP_DRIFT")
        links = client.tool("getallconnections").get("connections", [])
        expected_links = {
            (self.ids["width"], self.ids["rectangle"], 1),
            (self.ids["height"], self.ids["rectangle"], 2),
        }
        actual_links = {(x["SourceComponentId"], x["TargetComponentId"],
                         x["TargetInputIndex"]) for x in links}
        require(len(links) == 2 and actual_links == expected_links,
                "GH_GRAPH_CONNECTION_DRIFT")
        return {"components": 3, "connections": 2}

    def _perimeter(self, client):
        data = client.tool("get_component_output", {
            "componentId": self.ids["rectangle"], "outputIndex": 1,
        })
        branches = data.get("Output", {}).get("Branches", [])
        require(len(branches) == 1 and len(branches[0].get("Items", [])) == 1,
                "GH_PERIMETER_MISSING")
        value = branches[0]["Items"][0].get("Value")
        require(type(value) in (int, float), "GH_PERIMETER_NOT_NUMERIC")
        return value

    def run(self, operation, intent):
        require(isinstance(intent, dict) and
                intent.get("schemaVersion") == INTENT_SCHEMA, "GH_INTENT_SCHEMA_INVALID")
        client = self.client()
        if operation == "gh-read":
            require(set(intent) == {"schemaVersion", "tool", "arguments"}
                    and intent["tool"] in READ_TOOLS
                    and isinstance(intent["arguments"], dict), "GH_READ_TOOL_INVALID")
            tool, args = intent["tool"], intent["arguments"]
            if tool == "get_component_output":
                require(set(args) == {"componentId", "outputIndex"}
                        and args["componentId"] in self.ids.values()
                        and type(args["outputIndex"]) is int
                        and args["outputIndex"] in (0, 1), "GH_READ_ARGUMENTS_INVALID")
            else:
                require(args == {}, "GH_READ_ARGUMENTS_INVALID")
            if tool != "getsystemhealth":
                self.pinned_doc(client)
            result = client.tool(tool, args)
            require(len(json.dumps(result, ensure_ascii=False)) <= 48_000,
                    "GH_RESULT_TOO_LARGE")
            return {"status": "GH_READ_VERIFIED", "tool": tool,
                    "document": str(self.doc), "result": result,
                    "nativeWrites": 0}
        require(operation in ("gh-rectangle", "gh-verify"),
                "GH_OPERATION_NOT_ALLOWED")
        require(self.writes, "GH_WRITE_NOT_ENABLED")
        if operation == "gh-verify":
            require(set(intent) == {"schemaVersion", "outputFile",
                                     "outputSha256", "expectedPerimeterMm"},
                    "GH_VERIFY_INTENT_INVALID")
            output = Path(intent["outputFile"])
            checksum = intent["outputSha256"]
            expected = intent["expectedPerimeterMm"]
            require(output.is_absolute() and output.parent.resolve(strict=True) == self.root
                    and OUTPUT.fullmatch(output.name) and output.is_file()
                    and isinstance(checksum, str) and re.fullmatch(r"[a-f0-9]{64}", checksum)
                    and digest(output) == checksum
                    and type(expected) in (int, float) and 400 <= expected <= 200_000,
                    "GH_VERIFY_FILE_OR_HASH_INVALID")
            info = client.tool("getdocumentinfo")
            require(info.get("open") is True
                    and same_path(info.get("path", ""), output)
                    and info.get("mod") is False, "GH_VERIFY_WRONG_ACTIVE_DOCUMENT")
            self.verify_graph(client)
            require(abs(self._perimeter(client) - expected) <= 0.001,
                    "GH_VERIFY_PRE_CLOSE_MISMATCH")
            client.tool("closedocument", {"saveFirst": False})
            # With no active document, Cassis 1.6.0 cannot resolve X-Cassis-Root.
            unbound = self.client_factory(None)
            unbound.tool("loaddocument", {"filePath": str(output)})
            checked = self.client()
            deadline = time.monotonic() + 3.0
            while True:
                reopened = checked.tool("getdocumentinfo")
                if reopened.get("open") is True and same_path(reopened.get("path", ""), output):
                    break
                require(time.monotonic() < deadline, "GH_VERIFY_REOPEN_FILE_MISMATCH")
                time.sleep(0.25)
            require(reopened.get("mod") is False and digest(output) == checksum,
                    "GH_VERIFY_REOPEN_FILE_MISMATCH")
            self.verify_graph(checked)
            after = self._perimeter(checked)
            require(abs(after - expected) <= 0.001,
                    "GH_VERIFY_REOPEN_PERIMETER_DRIFT")
            return {"status": "GH_RECTANGLE_REOPEN_VERIFIED", "output": str(output),
                    "outputSha256": checksum, "afterPerimeterMm": after,
                    "nativeWrites": 0}
        require(set(intent) == {"schemaVersion", "widthMm", "heightMm", "outputFile"},
                "GH_WRITE_INTENT_INVALID")
        width, height = intent["widthMm"], intent["heightMm"]
        require(type(width) in (int, float) and type(height) in (int, float)
                and all(100 <= v <= 50_000 for v in (width, height)),
                "GH_RECTANGLE_DIMENSIONS_INVALID")
        output = Path(intent["outputFile"])
        require(output.is_absolute() and output.parent.resolve(strict=True) == self.root
                and OUTPUT.fullmatch(output.name) and not output.exists()
                and not same_path(output, self.doc), "GH_OUTPUT_SCOPE_OR_EXISTS")
        self.pinned_doc(client, require_clean=True)
        self.verify_graph(client)
        before = self._perimeter(client)
        client.tool("set_component_value", {"componentId": self.ids["width"],
                                             "parameterName": "value", "value": str(width)})
        client.tool("set_component_value", {"componentId": self.ids["height"],
                                             "parameterName": "value", "value": str(height)})
        client.tool("forcedocumentsolution")
        observed = self._perimeter(client)
        require(abs(observed - 2 * (width + height)) <= 0.001,
                "GH_RECTANGLE_PERIMETER_MISMATCH")
        curve = client.tool("get_component_output", {
            "componentId": self.ids["rectangle"], "outputIndex": 0})
        branches = curve.get("Output", {}).get("Branches", [])
        require(len(branches) == 1 and len(branches[0].get("Items", [])) == 1
                and branches[0]["Items"][0].get("Value", {}).get("isClosed") is True,
                "GH_RECTANGLE_NOT_CLOSED")
        saved = client.tool("savedocument", {"filePath": str(output)})
        require(saved.get("ok") is True and output.is_file(), "GH_SAVE_NOT_VERIFIED")
        checksum = digest(output)
        saved_info = client.tool("getdocumentinfo")
        require(saved_info.get("open") is True
                and same_path(saved_info.get("path", ""), output)
                and abs(self._perimeter(client) - observed) <= 0.001,
                "GH_SAVE_ACTIVE_READBACK_FAILED")
        return {"status": "GH_RECTANGLE_SAVED_PENDING_REOPEN",
                "source": str(self.doc), "output": str(output),
                "outputSha256": checksum, "widthMm": width,
                "heightMm": height, "beforePerimeterMm": before,
                "afterPerimeterMm": observed, "nativeWrites": 0}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--profile", type=Path, required=True)
    p.add_argument("--intent", type=Path, required=True)
    p.add_argument("--operation", choices=("gh-read", "gh-rectangle", "gh-verify"), required=True)
    args = p.parse_args(argv)
    try:
        intent = json.loads(args.intent.read_text(encoding="utf-8"))
        result = CassisBridge(args.profile).run(args.operation, intent)
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
        return 0
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc)[:180]},
                         ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
