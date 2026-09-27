"""Small, dependency-free client for the existing Safe BIM localhost IPC."""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass


class ControllerConnectionError(RuntimeError):
    pass


@dataclass(frozen=True)
class RuntimeState:
    job_id: str
    task: str
    status: str
    step: str
    progress: str
    floor: object
    readback: str
    enum: str

    @classmethod
    def from_payload(cls, payload: dict) -> "RuntimeState":
        required = ("job_id", "task", "status", "step", "progress", "readback", "enum")
        missing = [key for key in required if key not in payload]
        if missing:
            raise ValueError("state missing fields: " + ", ".join(missing))
        return cls(*(payload[key] for key in required[:5]), payload.get("floor"),
                    payload["readback"], payload["enum"])


class SafeBIMClient:
    def __init__(self, base_url: str = "http://127.0.0.1:19731", timeout: float = 2.5):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _request(self, path: str, method: str = "GET") -> dict:
        request = urllib.request.Request(self.base_url + path, method=method)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (OSError, urllib.error.URLError, TimeoutError) as exc:
            raise ControllerConnectionError(str(exc)) from exc
        if not isinstance(payload, dict):
            raise ControllerConnectionError("runtime returned non-object JSON")
        if "error" in payload:
            raise ControllerConnectionError(str(payload["error"]))
        return payload

    def state(self, job_id: str = "active") -> RuntimeState:
        encoded = urllib.parse.quote(job_id, safe="")
        try:
            return RuntimeState.from_payload(self._request(f"/state?job_id={encoded}"))
        except ControllerConnectionError as exc:
            if "HTTP Error 404" in str(exc):
                return RuntimeState("", "—", "PENDING", "—", "—", None,
                                    "Активная задача отсутствует", "PENDING")
            raise

    def command(self, action: str, job_id: str = "active") -> dict:
        if action not in {"continue", "pause", "stop"}:
            raise ValueError(action)
        encoded = urllib.parse.quote(job_id, safe="")
        return self._request(f"/jobs/{encoded}/{action}", method="POST")
