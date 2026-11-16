"""Guarded Cassis MCP client for one pinned, isolated Grasshopper test graph.

No arbitrary MCP tool forwarding, no model/PLN writes, no remote HTTP endpoints.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from threading import Lock
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

SCHEMA = "APA_CASSIS_TEST_V1"
ALLOWED = {"status", "document", "components", "connections", "output", "set_slider"}
GUID = re.compile(r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}")
MAX_BYTES = 262144


def _hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class CassisControl:
    def __init__(self, profile, *, transport=None):
        self.profile = Path(profile).resolve(strict=True)
        if self.profile.stat().st_size > 8192:
            raise ValueError("CASSIS_PROFILE_TOO_LARGE")
        raw = self.profile.read_bytes()
        config = json.loads(raw)
        if (not isinstance(config, dict) or set(config) !=
                {"schema", "testDocument", "documentSha256", "sliderIds"} or
                config["schema"] != SCHEMA):
            raise ValueError("CASSIS_PROFILE_INVALID")
        doc = Path(config["testDocument"])
        if (not doc.is_absolute() or doc.suffix.lower() != ".ghx" or
                doc.resolve(strict=True) != doc or
                "experiments" not in [part.lower() for part in doc.parts] or
                not re.fullmatch("[a-fA-F0-9]{64}", config["documentSha256"]) or
                not isinstance(config["sliderIds"], list) or
                len(config["sliderIds"]) != 2 or
                not all(isinstance(v, str) and GUID.fullmatch(v) for v in config["sliderIds"]) or
                len(set(config["sliderIds"])) != 2):
            raise ValueError("CASSIS_TEST_SCOPE_INVALID")
        self.document = doc
        self.document_hash = config["documentSha256"].lower()
        self.slider_ids = frozenset(config["sliderIds"])
        self.profile_hash = hashlib.sha256(raw).hexdigest()
        self._transport = transport or self._http
        self._lock = Lock()

    @staticmethod
    def _http(tool, arguments):
        url = "http://127.0.0.1:3003/mcp/"
        headers = {"Accept": "application/json, text/event-stream",
                   "MCP-Protocol-Version": "2025-06-18",
                   "Content-Type": "application/json"}
        def send(data, session=None):
            h = dict(headers)
            if session:
                h["Mcp-Session-Id"] = session
            request = Request(url, json.dumps(data, separators=(",", ":")).encode(),
                              headers=h, method="POST")
            with urlopen(request, timeout=12) as response:
                content = response.read(MAX_BYTES + 1)
                if len(content) > MAX_BYTES:
                    raise ValueError("CASSIS_RESPONSE_TOO_LARGE")
                raw = content.decode("utf-8")
                if response.headers.get("Content-Type", "").startswith("text/event-stream"):
                    packets = [line[6:] for line in raw.splitlines() if line.startswith("data: ")]
                    if not packets:
                        raise ValueError("CASSIS_NO_SSE_DATA")
                    body = json.loads(packets[0])
                else:
                    body = json.loads(raw)
                if "error" in body:
                    raise ValueError("CASSIS_PROTOCOL_ERROR")
                return body.get("result", {}), response.headers.get("Mcp-Session-Id")
        init, session = send({
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                       "clientInfo": {"name": "APA-Cassis", "version": "0.1"}}})
        if init.get("serverInfo", {}).get("name") != "Cassis":
            raise ValueError("CASSIS_SERVER_IDENTITY_INVALID")
        result, _ = send({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                          "params": {"name": tool, "arguments": arguments}}, session)
        if result.get("isError") or not result.get("content"):
            raise ValueError("CASSIS_TOOL_FAILED")
        item = result["content"][0]
        if item.get("type") != "text":
            raise ValueError("CASSIS_UNEXPECTED_TOOL_CONTENT")
        return json.loads(item["text"])

    def _guard(self, *, write=False):
        if _hash(self.profile) != self.profile_hash:
            raise ValueError("CASSIS_PROFILE_CHANGED")
        if write and _hash(self.document) != self.document_hash:
            raise ValueError("CASSIS_TEST_DOCUMENT_CHANGED")
        doc = self._transport("getdocumentinfo", {})
        if (not doc.get("ok") or not doc.get("open") or
                Path(doc.get("path", "")).resolve() != self.document):
            raise ValueError("CASSIS_ACTIVE_DOCUMENT_NOT_PINNED")
        return doc

    def perform(self, operation, component_id=None, value=None):
        with self._lock:
            try:
                return self._perform(operation, component_id, value)
            except (OSError, ValueError, TypeError, KeyError, URLError, HTTPError):
                return {"status": "BLOCKED", "reason": "CASSIS_GUARD_OR_TRANSPORT_FAILURE",
                        "operation": operation if operation in ALLOWED else "INVALID"}

    def _perform(self, operation, component_id, value):
        if (operation not in ALLOWED or
                (component_id is not None and
                 (not isinstance(component_id, str) or not GUID.fullmatch(component_id))) or
                (operation in {"output", "set_slider"} and not component_id) or
                (operation not in {"output", "set_slider"} and component_id is not None) or
                (operation == "set_slider" and
                 (not isinstance(value, int) or isinstance(value, bool) or value < 100 or value > 10000)) or
                (operation != "set_slider" and value is not None)):
            raise ValueError("CASSIS_ARGUMENTS_INVALID")
        if operation == "status":
            active = self._transport("getdocumentinfo", {})
            if not active.get("ok"):
                raise ValueError("CASSIS_SERVER_NOT_READY")
            return {"status": "CASSIS_CONNECTED", "readOnlyByDefault": True,
                    "activeDocumentPinned": bool(active.get("open") and
                        Path(active.get("path", "")).resolve() == self.document),
                    "testDocument": str(self.document), "profileSha256": self.profile_hash}
        doc = self._guard(write=operation == "set_slider")
        if operation == "document":
            result = {"file": doc["file"], "open": True}
        elif operation == "components":
            result = self._transport("get_allcomponents", {})
        elif operation == "connections":
            result = self._transport("getallconnections", {})
        elif operation == "output":
            result = self._transport("get_component_output",
                                     {"componentId": component_id, "outputIndex": 0})
        else:
            if component_id not in self.slider_ids:
                raise ValueError("CASSIS_SLIDER_ID_NOT_PINNED")
            snapshot = self._transport("get_componentcount", {})
            if (snapshot.get("components") != 1 or snapshot.get("parameters") != 2 or
                    snapshot.get("connections") != 2):
                raise ValueError("CASSIS_GRAPH_IS_NOT_ISOLATED")
            result = self._transport("set_component_value", {
                "componentId": component_id, "parameterName": "value", "value": str(value)})
            if not result.get("success") or result.get("value") != str(value):
                raise ValueError("CASSIS_WRITE_NOT_ACKNOWLEDGED")
        self._guard()
        return {"status": "CASSIS_TEST_" + ("PARAMETER_SET" if operation == "set_slider" else "READ"),
                "operation": operation, "modelWrites": 0,
                "document": str(self.document), "result": result}
