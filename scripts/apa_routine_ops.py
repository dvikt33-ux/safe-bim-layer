"""Non-interactive, narrowly scoped routine workstation reads for APA.

This module deliberately has NO shell execution, writes to model files,
installer actions, process termination, command parameters or script staging.
The local Windows user opts in to a workspace root when starting the gateway.
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import re
import socket
from threading import Lock

JOB_ID = re.compile(r"[a-z0-9][a-z0-9-]{2,63}\Z")
VALID_PART = re.compile(r"[a-zA-Z0-9_\- .()/\\\u0400-\u04ff]+\Z")
ALLOWED_PORTS = frozenset({3003, 18787, 18790, 19723, 7801, 7802})
ALLOWED_PROCESSES = frozenset({
    "rhino.exe", "archicad.exe", "python.exe", "pythonw.exe",
    "tunnel-client.exe", "grasshopper.exe",
})
TEXT_EXTENSIONS = frozenset({".json", ".txt", ".md", ".ghx", ".yaml", ".yml", ".csv", ".log"})
MAX_TEXT_BYTES = 32768
MAX_RESULTS = 75
BLOCKED_NAMES = frozenset({".env", "id_rsa", "id_ed25519", "credentials.json", "secrets.json"})
BLOCKED_NAME_PARTS = ("secret", "token", "password", "credential", "private-key")


def _safe_json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False,
                      separators=(",", ":"))


class RoutineRead:
    """Typed read operations using a preselected working directory."""

    def __init__(self, root: Path, *, tasklist=None, socket_check=None):
        self.root = root.resolve(strict=True)
        if not self.root.is_dir():
            raise ValueError("ROUTINE_WORKSPACE_NOT_DIRECTORY")
        self.jobs = self.root / ".apa-routine-jobs"
        self.jobs.mkdir(exist_ok=True)
        self.lock = Lock()
        self._tasklist = tasklist or self._windows_tasklist
        self._socket_check = socket_check or self._port_check

    def _path(self, relative):
        if not isinstance(relative, str) or not relative or len(relative) > 180:
            raise ValueError("ROUTINE_RELATIVE_PATH_INVALID")
        if not VALID_PART.fullmatch(relative) or Path(relative).is_absolute():
            raise ValueError("ROUTINE_RELATIVE_PATH_INVALID")
        parts = relative.replace("\\", "/").split("/")
        if any(part in ("", ".", "..") for part in parts):
            raise ValueError("ROUTINE_PATH_TRAVERSAL_BLOCKED")
        candidate = (self.root / relative).resolve(strict=True)
        if not candidate.is_relative_to(self.root):
            raise ValueError("ROUTINE_OUTSIDE_WORKSPACE")
        return candidate

    @staticmethod
    def _windows_tasklist():
        """Enumerate processes using Windows Toolhelp APIs: no shell or child process."""
        if os.name != "nt":
            raise ValueError("ROUTINE_PROCESS_LIST_WINDOWS_ONLY")

        class PROCESSENTRY32W(ctypes.Structure):
            _fields_ = [
                ("dwSize", wintypes.DWORD),
                ("cntUsage", wintypes.DWORD),
                ("th32ProcessID", wintypes.DWORD),
                ("th32DefaultHeapID", ctypes.c_void_p),
                ("th32ModuleID", wintypes.DWORD),
                ("cntThreads", wintypes.DWORD),
                ("th32ParentProcessID", wintypes.DWORD),
                ("pcPriClassBase", wintypes.LONG),
                ("dwFlags", wintypes.DWORD),
                ("szExeFile", wintypes.WCHAR * 260),
            ]

        api = ctypes.WinDLL("kernel32", use_last_error=True)
        create = api.CreateToolhelp32Snapshot
        create.argtypes = (wintypes.DWORD, wintypes.DWORD)
        create.restype = wintypes.HANDLE
        first = api.Process32FirstW
        first.argtypes = (wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W))
        first.restype = wintypes.BOOL
        next_entry = api.Process32NextW
        next_entry.argtypes = (wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W))
        next_entry.restype = wintypes.BOOL
        close = api.CloseHandle
        close.argtypes = (wintypes.HANDLE,)
        close.restype = wintypes.BOOL

        handle = create(0x00000002, 0)
        if handle == ctypes.c_void_p(-1).value or handle is None:
            raise OSError("ROUTINE_PROCESS_SNAPSHOT_FAILED")
        rows = []
        try:
            entry = PROCESSENTRY32W()
            entry.dwSize = ctypes.sizeof(PROCESSENTRY32W)
            if not first(handle, ctypes.byref(entry)):
                raise OSError("ROUTINE_PROCESS_ENUMERATION_FAILED")
            while True:
                rows.append([entry.szExeFile, str(entry.th32ProcessID)])
                if not next_entry(handle, ctypes.byref(entry)):
                    break
        finally:
            close(handle)
        return rows

    @staticmethod
    def _port_check(port):
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.4):
                return True
        except OSError:
            return False

    @staticmethod
    def _args(intent):
        if not isinstance(intent, dict) or set(intent) != {"kind", "parameters"}:
            raise ValueError("ROUTINE_INTENT_SCHEMA_INVALID")
        kind, args = intent["kind"], intent["parameters"]
        if (kind not in {"status", "ports", "processes", "directory",
                         "file-stat", "text-read"}
                or not isinstance(args, dict)
                or len(_safe_json(args).encode("utf-8")) > 4096):
            raise ValueError("ROUTINE_OPERATION_NOT_ALLOWED")
        return kind, args

    def _query(self, kind, args):
        if kind == "status":
            if args:
                raise ValueError("ROUTINE_ARGUMENTS_INVALID")
            return {"workdir": str(self.root), "readOnly": True,
                    "requiresApprove": False,
                    "operations": ["status", "ports", "processes", "directory",
                                   "file-stat", "text-read"]}
        if kind == "ports":
            if set(args) != {"ports"} or not isinstance(args["ports"], list):
                raise ValueError("ROUTINE_ARGUMENTS_INVALID")
            ports = args["ports"]
            if (len(ports) > 12 or any(type(p) is not int or p not in ALLOWED_PORTS for p in ports)):
                raise ValueError("ROUTINE_PORT_NOT_ALLOWED")
            return {"ports": [{"port": p, "acceptingTcp": bool(self._socket_check(p))}
                              for p in dict.fromkeys(ports)]}
        if kind == "processes":
            if set(args) != {"names"} or not isinstance(args["names"], list):
                raise ValueError("ROUTINE_ARGUMENTS_INVALID")
            names = args["names"]
            if (len(names) > 8 or any(not isinstance(s, str)
                                      or s.lower() not in ALLOWED_PROCESSES for s in names)):
                raise ValueError("ROUTINE_PROCESS_NOT_ALLOWED")
            wanted = {s.lower() for s in names}
            matches = []
            for row in self._tasklist():
                if len(row) >= 2 and row[0].lower() in wanted:
                    try:
                        pid = int(row[1].replace(",", ""))
                    except ValueError:
                        continue
                    matches.append({"name": row[0], "pid": pid})
                if len(matches) >= MAX_RESULTS:
                    break
            return {"processes": matches}
        if set(args) != {"relativePath"}:
            raise ValueError("ROUTINE_ARGUMENTS_INVALID")
        target = self._path(args["relativePath"])
        if kind == "directory":
            if not target.is_dir():
                raise ValueError("ROUTINE_NOT_DIRECTORY")
            entries = sorted(target.iterdir(), key=lambda p: p.name.lower())
            return {"path": str(target), "entries": [
                {"name": p.name, "kind": "directory" if p.is_dir() else "file"}
                for p in entries[:MAX_RESULTS]],
                    "truncated": len(entries) > MAX_RESULTS}
        if not target.is_file():
            raise ValueError("ROUTINE_NOT_FILE")
        metadata = {"path": str(target), "bytes": target.stat().st_size}
        if kind == "file-stat":
            if target.stat().st_size <= 8_000_000:
                metadata["sha256"] = hashlib.sha256(target.read_bytes()).hexdigest()
            return metadata
        if kind == "text-read":
            name = target.name.lower()
            if (target.suffix.lower() not in TEXT_EXTENSIONS
                    or name in BLOCKED_NAMES
                    or any(blocked in name for blocked in BLOCKED_NAME_PARTS)
                    or target.stat().st_size > MAX_TEXT_BYTES):
                raise ValueError("ROUTINE_TEXT_READ_BLOCKED")
            return {**metadata, "text": target.read_text(encoding="utf-8-sig")}
        raise ValueError("ROUTINE_OPERATION_NOT_ALLOWED")

    def perform(self, job_id, target=None, intent=None):
        if target is not None or not isinstance(job_id, str) or not JOB_ID.fullmatch(job_id):
            raise ValueError("ROUTINE_INVALID_JOB_OR_TARGET")
        kind, args = self._args(intent)
        request = {"operation": "routine-read", "intent": intent, "target": None}
        with self.lock:
            folder = self.jobs / job_id
            if folder.exists():
                previous = json.loads((folder / "request.json").read_text("utf-8"))
                if previous != request:
                    raise ValueError("ROUTINE_JOB_ID_CONFLICT")
                result = folder / "result.json"
                if not result.is_file():
                    return {"status": "UNKNOWN_NO_RETRY", "jobId": job_id}
                return json.loads(result.read_text("utf-8"))
            folder.mkdir()
            with (folder / "request.json").open("x", encoding="utf-8") as file:
                file.write(_safe_json(request))
            try:
                result = self._query(kind, args)
                output = {"status": "COMPLETE", "jobId": job_id,
                          "operation": "routine-read", "kind": kind, "result": result,
                          "modelWrites": 0, "requiresApprove": False}
            except (OSError, ValueError) as error:
                output = {"status": "BLOCKED", "jobId": job_id,
                          "operation": "routine-read", "reason": str(error)[:160],
                          "modelWrites": 0, "requiresApprove": False}
            with (folder / "result.json").open("x", encoding="utf-8") as file:
                file.write(_safe_json(output))
            return output

    def read_job(self, job_id):
        if not isinstance(job_id, str) or not JOB_ID.fullmatch(job_id):
            raise ValueError("ROUTINE_INVALID_JOB_ID")
        folder = self.jobs / job_id
        if not folder.is_dir() or not (folder / "request.json").is_file():
            return None
        result = folder / "result.json"
        if not result.is_file():
            return {"status": "UNKNOWN_NO_RETRY", "jobId": job_id}
        return json.loads(result.read_text("utf-8"))
