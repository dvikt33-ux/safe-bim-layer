"""Localhost-only HTTP control surface for the Safe BIM Archicad palette."""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from safe_bim_runtime import ExecutorError, ResumableExecutor


class PaletteHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True

    def __init__(self, address, executor: ResumableExecutor):
        host, _ = address
        if host not in {"127.0.0.1", "localhost"}:
            raise ValueError("Safe BIM IPC must bind to localhost")
        self.executor = executor
        super().__init__(address, PaletteHandler)


class PaletteHandler(BaseHTTPRequestHandler):
    server: PaletteHTTPServer

    def log_message(self, *_):
        return

    def _send(self, code, payload):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path != "/state":
            return self._send(404, {"error": "not found"})
        job_id = parse_qs(parsed.query).get("job_id", [None])[0]
        if not job_id:
            return self._send(400, {"error": "job_id required"})
        try:
            return self._send(200, self.server.executor.palette_state(job_id))
        except ExecutorError as exc:
            return self._send(404, {"error": str(exc)})

    def do_POST(self):
        parts = [part for part in urlparse(self.path).path.split("/") if part]
        if len(parts) != 3 or parts[0] != "jobs":
            return self._send(404, {"error": "not found"})
        _, job_id, action = parts
        try:
            job_id = self.server.executor.resolve_job_id(job_id)
            if action == "continue":
                status = self.server.executor.resume(job_id)
            elif action == "pause":
                status = self.server.executor.pause(job_id)
            elif action == "stop":
                status = self.server.executor.stop(job_id)
            else:
                return self._send(404, {"error": "unknown action"})
            return self._send(200, {"job_id": job_id, "status": status.value})
        except Exception as exc:
            return self._send(409, {"error": f"{type(exc).__name__}: {exc}"})


def serve(executor: ResumableExecutor, port: int = 19731):
    server = PaletteHTTPServer(("127.0.0.1", port), executor)
    server.serve_forever()
