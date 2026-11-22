"""APA/Cassis compatibility gateway. New code; signed APA release is never modified.

Expose Grasshopper through the two names already present in the ChatGPT APA app:
  apa_execute(operation="gh-read", job_id=..., intent={"tool": "...", "arguments": {...}})
  apa_execute(operation="gh-write", job_id=..., intent={"tool": "...", "arguments": {...}})

NOT a bypass of local authorization: installing/repointing the tunnel requires
operator approval. Writes require an isolated, SHA-pinned Grasshopper document.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from threading import Lock
from urllib.request import Request, urlopen

MAX_BODY = 128_000
ID = re.compile(r"[a-z0-9][a-z0-9-]{2,63}\Z")
READ_TOOLS = frozenset({
    "getdocumentinfo", "get_componentcount", "get_allcomponents",
    "getallconnections", "get_component_output", "getsolutionstate",
    "getsystemhealth", "getdetailedcomponentinfobyid",
    "list_panels", "get_panel_text", "list_python_scripts",
    "list_csharp_scripts", "canvas_snapshot",
})
WRITE_TOOLS = frozenset({
    "addcomponent", "move_component", "connectcomponentswithvalidation",
    "set_component_value", "forcedocumentsolution", "savedocument",
})
BANNED_ARGUMENTS = frozenset({
    "script", "source", "code", "command", "shell", "url", "uri",
    "filepath", "filename", "file", "path", "directory",
})
MCP_ENDPOINT = "http://127.0.0.1:3003/mcp/"


def _digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _file_hash(path: Path) -> str:
    return _digest(path.read_bytes())


def _safe_json(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, allow_nan=False,
                      separators=(",", ":"))


class CassisTransport:
    """Streamable HTTP Cassis protocol on loopback; never a public endpoint."""

    def __init__(self, *, endpoint=MCP_ENDPOINT, project_root=None):
        if endpoint != MCP_ENDPOINT:
            raise ValueError("GH_ENDPOINT_MUST_BE_LOOPBACK_CASSIS")
        self.endpoint = endpoint
        self.project_root = project_root

    def call(self, name: str, arguments: dict):
        headers = {
            "Accept": "application/json, text/event-stream",
            "MCP-Protocol-Version": "2025-06-18",
            "Content-Type": "application/json",
        }
        if self.project_root:
            headers["X-Cassis-Root"] = str(self.project_root)

        def post(packet, session=None):
            h = dict(headers)
            if session:
                h["Mcp-Session-Id"] = session
            request = Request(self.endpoint, _safe_json(packet).encode("utf-8"),
                              headers=h, method="POST")
            with urlopen(request, timeout=12) as response:
                data = response.read(MAX_BODY + 1)
                if len(data) > MAX_BODY:
                    raise ValueError("GH_RESPONSE_TOO_LARGE")
                txt = data.decode("utf-8")
                if response.headers.get("Content-Type", "").startswith("text/event-stream"):
                    chunks = [s[6:] for s in txt.splitlines() if s.startswith("data: ")]
                    if not chunks:
                        raise ValueError("GH_MCP_EMPTY_SSE")
                    txt = chunks[0]
                body = json.loads(txt)
                if "error" in body:
                    raise ValueError("GH_MCP_JSONRPC_ERROR")
                return body.get("result", {}), response.headers.get("Mcp-Session-Id")

        init, session = post({
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                       "clientInfo": {"name": "APA-Cassis-Compat", "version": "1.0"}},
        })
        if init.get("serverInfo", {}).get("name") != "Cassis":
            raise ValueError("GH_CASSIS_IDENTITY_MISMATCH")
        result, _ = post({
            "jsonrpc": "2.0", "id": 2, "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        }, session)
        if result.get("isError") or not result.get("content"):
            raise ValueError("GH_TOOL_RETURNED_ERROR")
        first = result["content"][0]
        if first.get("type") != "text":
            raise ValueError("GH_TOOL_RESPONSE_NOT_TEXT")
        return json.loads(first["text"])


class GrasshopperGate:
    def __init__(self, *, workdir: Path, profile: Path | None = None, transport=None):
        self.workdir = workdir.resolve(strict=True)
        if not self.workdir.is_dir():
            raise ValueError("GH_WORKDIR_NOT_DIRECTORY")
        self.store = self.workdir / ".apa-gh-jobs"
        self.store.mkdir(exist_ok=True)
        self._lock = Lock()
        self.test_document = None
        self.expected_hash = None
        self.allow_writes = False
        self.project_root = None

        if profile is not None:
            p = profile.resolve(strict=True)
            raw = p.read_bytes()
            if len(raw) > 8192:
                raise ValueError("GH_PROFILE_TOO_LARGE")
            cfg = json.loads(raw)
            required = {"schema", "testDocument", "documentSha256", "allowWrites"}
            if (not isinstance(cfg, dict) or set(cfg) != required
                    or cfg["schema"] != "APA_GH_COMPAT_V1"
                    or type(cfg["allowWrites"]) is not bool):
                raise ValueError("GH_PROFILE_SCHEMA_INVALID")
            self.allow_writes = cfg["allowWrites"]
            doc = Path(cfg["testDocument"]).resolve(strict=self.allow_writes)
            if not doc.is_absolute() or "experiments" not in [
                    segment.lower() for segment in doc.parts]:
                raise ValueError("GH_TEST_DOCUMENT_NOT_EXPERIMENTAL")
            if doc != Path(cfg["testDocument"]):
                raise ValueError("GH_TEST_DOCUMENT_REDIRECTED")
            if self.allow_writes and not doc.is_file():
                raise ValueError("GH_TEST_DOCUMENT_MISSING")
            if not re.fullmatch(r"[a-f0-9]{64}", cfg["documentSha256"]):
                raise ValueError("GH_DOCUMENT_SHA_INVALID")
            if self.allow_writes and _file_hash(doc) != cfg["documentSha256"]:
                raise ValueError("GH_DOCUMENT_SHA_MISMATCH")
            self.test_document = doc
            self.expected_hash = cfg["documentSha256"]
            self.project_root = doc.parent
        self.transport = transport or CassisTransport(project_root=self.project_root)

    def _active(self):
        doc = self.transport.call("getdocumentinfo", {})
        if not isinstance(doc, dict) or not doc.get("ok") or not doc.get("open"):
            raise ValueError("GH_NO_ACTIVE_DOCUMENT")
        return doc

    def _verify_write(self):
        if not self.allow_writes or self.test_document is None:
            raise ValueError("GH_WRITES_REQUIRE_LOCAL_SANDBOX_PROFILE")
        doc = self._active()
        active = Path(doc.get("path", "")).resolve()
        if active != self.test_document:
            raise ValueError("GH_DIFFERENT_ACTIVE_DOCUMENT")
        if _file_hash(self.test_document) != self.expected_hash:
            raise ValueError("GH_TEST_DOCUMENT_MODIFIED_OUTSIDE_BRIDGE")
        return doc

    @staticmethod
    def _validate(intent, operation):
        if (not isinstance(intent, dict) or set(intent) != {"tool", "arguments"}
                or not isinstance(intent["tool"], str)
                or not isinstance(intent["arguments"], dict)):
            raise ValueError("GH_INTENT_SCHEMA_INVALID")
        tool, args = intent["tool"], intent["arguments"]
        if tool not in (READ_TOOLS if operation == "gh-read" else WRITE_TOOLS):
            raise ValueError("GH_TOOL_OUTSIDE_ALLOWLIST")
        if len(_safe_json(args).encode("utf-8")) > 8_192:
            raise ValueError("GH_ARGUMENTS_TOO_LARGE")
        if operation == "gh-write":
            if any(k.lower() in BANNED_ARGUMENTS for k in args):
                raise ValueError("GH_DANGEROUS_ARGUMENT_KEY")
            if tool == "set_component_value":
                if (set(args) != {"componentId", "parameterName", "value"}
                        or args["parameterName"] != "value"
                        or not re.fullmatch(r"-?\d+(?:\.\d+)?",
                                             str(args["value"]))):
                    raise ValueError("GH_ONLY_NUMERIC_PARAMETERS_ALLOWED")
            if tool == "savedocument" and args:
                raise ValueError("GH_SAVE_MUST_USE_ACTIVE_PINNED_FILE")
        return tool, args

    def _pending_writes(self):
        for entry in self.store.iterdir():
            if not entry.is_dir():
                continue
            request = entry / "request.json"
            result = entry / "result.json"
            if request.is_file() and not result.is_file():
                try:
                    if json.loads(request.read_text("utf-8")).get("operation") == "gh-write":
                        return True
                except (OSError, ValueError):
                    return True
        return False

    def perform(self, operation, job_id, target=None, intent=None):
        if operation not in {"gh-read", "gh-write"}:
            raise ValueError("GH_OPERATION_INVALID")
        if target is not None:
            raise ValueError("GH_TARGET_NOT_ALLOWED")
        if not isinstance(job_id, str) or not ID.fullmatch(job_id):
            raise ValueError("GH_JOB_ID_INVALID")
        tool, arguments = self._validate(intent, operation)
        request = {"operation": operation, "intent": intent, "target": None}
        with self._lock:
            folder = self.store / job_id
            if folder.exists():
                previous = json.loads((folder / "request.json").read_text("utf-8"))
                if previous != request:
                    raise ValueError("GH_JOB_ID_REUSED_DIFFERENT_REQUEST")
                result_file = folder / "result.json"
                if not result_file.is_file():
                    return {"status": "UNKNOWN_NO_AUTORETRY", "jobId": job_id}
                return json.loads(result_file.read_text("utf-8"))

            if operation == "gh-write":
                if self._pending_writes():
                    raise ValueError("GH_PREVIOUS_WRITE_NOT_RECONCILED")
                self._verify_write()
            folder.mkdir(exist_ok=False)
            # The job journal is written before dispatch. A lost result is never replayed.
            with (folder / "request.json").open("x", encoding="utf-8") as f:
                f.write(_safe_json(request))
            try:
                result = self.transport.call(tool, arguments)
                if operation == "gh-write":
                    self._verify_write()
                    if tool == "savedocument":
                        # Explicit save changes only our exact experimental document.
                        self.expected_hash = _file_hash(self.test_document)
                row = {"status": "COMPLETE", "jobId": job_id, "operation": operation,
                       "tool": tool, "result": result,
                       "document": str(self.test_document) if self.test_document else None}
            except Exception as exc:
                # Unknown outcome for an interrupted write: inspect the GH document,
                # never auto-retry the same command.
                row = {"status": "UNKNOWN_NO_AUTORETRY" if operation == "gh-write"
                       else "FAILED", "jobId": job_id, "operation": operation,
                       "reason": type(exc).__name__ + ": " + str(exc)[:140]}
            with (folder / "result.json").open("x", encoding="utf-8") as f:
                f.write(_safe_json(row))
            return row

    def read_job(self, job_id):
        if not isinstance(job_id, str) or not ID.fullmatch(job_id):
            raise ValueError("GH_JOB_ID_INVALID")
        folder = self.store / job_id
        if not folder.is_dir() or not (folder / "request.json").is_file():
            return None
        result = folder / "result.json"
        if not result.is_file():
            return {"status": "UNKNOWN_NO_AUTORETRY", "jobId": job_id}
        return json.loads(result.read_text("utf-8"))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-root", type=Path, required=True)
    parser.add_argument("--apa-profile", type=Path, required=True)
    parser.add_argument("--gh-workdir", type=Path, required=True)
    parser.add_argument("--gh-profile", type=Path)
    parser.add_argument("--port", type=int, default=18789)
    args = parser.parse_args(argv)
    if not (1024 <= args.port <= 65535):
        raise ValueError("GH_GATEWAY_PORT_INVALID")

    root = args.release_root.resolve(strict=True)
    sys.path.insert(0, str(root))
    sys.path.insert(0, str(root / "scripts"))
    from apa_control_mcp import Control, output_json
    from mcp.server import MCPServer
    from mcp.types import CallToolResult, TextContent, ToolAnnotations
    import anyio

    control = Control(root, args.apa_profile.resolve(strict=True))
    gh = GrasshopperGate(workdir=args.gh_workdir, profile=args.gh_profile)
    app = MCPServer("APA Windows")
    def reply(row, error=False):
        return CallToolResult(content=[TextContent(type="text", text=output_json(row))],
                              structured_content=row, is_error=error)

    @app.tool(annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=False))
    async def apa_read(kind: str, job_id: str | None = None,
                       artifact: str | None = None, offset: int = 0) -> CallToolResult:
        """Read APA jobs and Grasshopper operation receipts."""
        try:
            if kind == "job" and job_id and artifact is None and offset == 0:
                cached = await anyio.to_thread.run_sync(gh.read_job, job_id)
                if cached is not None:
                    return reply(cached)
            row = await anyio.to_thread.run_sync(control.read, kind, job_id, artifact, offset)
            return reply(row)
        except Exception:
            return reply({"status": "BLOCKED", "reason": "APA_READ_ERROR"}, error=True)

    @app.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True,
                                         idempotentHint=True, openWorldHint=False))
    async def apa_execute(operation: str, job_id: str, target: str | None = None,
                          intent: dict | None = None) -> CallToolResult:
        """Preserve APA operations; add gh-read / gh-write for scoped Cassis operations."""
        try:
            if operation in {"gh-read", "gh-write"}:
                row = await anyio.to_thread.run_sync(gh.perform, operation, job_id, target, intent)
            else:
                row = await anyio.to_thread.run_sync(control.submit, operation, job_id, target, intent)
            return reply(row, error=row.get("status") in {"BLOCKED", "FAILED"})
        except Exception as exc:
            message = str(exc)
            if not re.fullmatch(r"[A-Z0-9_]{5,100}", message):
                message = "APA_OR_GH_REQUEST_BLOCKED"
            return reply({"status": "BLOCKED", "reason": message}, error=True)

    try:
        app.run(transport="streamable-http", host="127.0.0.1", port=args.port,
                stateless_http=True, json_response=True,
                max_request_body_size=MAX_BODY)
    finally:
        control.close()


if __name__ == "__main__":
    raise SystemExit(main())
