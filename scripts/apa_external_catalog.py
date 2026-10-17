"""Attach verified external read-only tools to existing DynamicCommands.

The existing router's add_local_provider/run_read handles command catalog,
schema validation and provenance. This module adds no new writer or transport.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(r"C:\LocalAI\APA_AC29_Stable")
FOLDER = ROOT / "external-tools" / "apa-readonly-v1"
NAMESPACE = "APAExternalReadOnly"
COMMANDS = {
    "IFCDiff": ("ifc-diff", ("a", "b", "output")),
    "IFCClash": ("ifc-clash", ("a", "output")),
    "IDSValidate": ("ids-validate", ("a", "ids", "output")),
    "IFCQuantities": ("ifc-qto", ("a", "output")),
    "PDFVectors": ("pdf-vectors", ("a", "output")),
    "DXFVectors": ("dxf-vectors", ("a", "output")),
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(ok, name):
    if not ok:
        raise ValueError(name)


def verified_environment():
    manifest = FOLDER / "installation.json"
    script = FOLDER / "apa_external_readonly.py"
    python = FOLDER / "venv" / "Scripts" / "python.exe"
    require(manifest.is_file() and script.is_file() and python.is_file(),
            "APA_EXTERNAL_ISOLATED_INSTALL_MISSING")
    m = json.loads(manifest.read_text(encoding="utf-8"))
    require(m.get("schema") == "APA_EXTERNAL_READONLY_INSTALL_V1"
            and m.get("adapterSHA256") == sha256(script),
            "APA_EXTERNAL_ADAPTER_MANIFEST_DRIFT")
    return python, script


def call(action, params):
    require(action in {v[0] for v in COMMANDS.values()},
            "UNREVIEWED_LOCAL_TOOL")
    python, script = verified_environment()
    arguments = [str(python), str(script), action]
    for key, value in params.items():
        require(key in {"a", "b", "ids", "output"} and isinstance(value, str)
                and value, "LOCAL_ANALYSIS_PARAMETER_INVALID")
        arguments.extend(["--" + key, value])
    completed = subprocess.run(arguments, capture_output=True,
                               text=True, timeout=1200)
    require(completed.returncode == 0,
            "APA_EXTERNAL_TOOL_BLOCKED:" + completed.stdout[-700:]
            + completed.stderr[-700:])
    output = Path(params["output"]).resolve()
    result = json.loads(output.read_text(encoding="utf-8"))
    require(result.get("schema") == "APA_EXTERNAL_READONLY_EVIDENCE_V1"
            and result.get("action") == action
            and result.get("modelWrites") == 0
            and result.get("nativeCalls") == 0,
            "APA_EXTERNAL_REPORT_RESULT_INVALID")
    return result


def register(router):
    """Register all six REVIEWED READ_ONLY local handlers on the original router.

    Caller selects commands via the existing DynamicCommands catalog.
    No auto-execution or Archicad write permission follows from registration.
    """
    verified_environment()
    contracts, handlers, dependencies = {}, {}, {}
    for command, (action, required) in COMMANDS.items():
        props = {name: {"type": "string", "minLength": 1}
                 for name in ("a", "b", "ids", "output")}
        contracts[command] = {
            "name": command, "version": "1",
            "category": "APA_EXTERNAL_ANALYTICS",
            "description": "Read-only local external analysis: " + action,
            "parameters": {"type": "object", "properties": props,
                           "required": list(required),
                           "additionalProperties": False},
            "returns": {"type": "object",
                        "required": ["schema", "status", "action", "sources",
                                     "result", "modelWrites", "nativeCalls"],
                        "properties": {
                            "schema": {"type": "string"},
                            "status": {"type": "string"},
                            "action": {"type": "string"},
                            "sources": {"type": "array"},
                            "result": {"type": "object"},
                            "modelWrites": {"type": "integer"},
                            "nativeCalls": {"type": "integer"}}}}
        handlers[command] = (lambda a: lambda **kwargs: call(a, kwargs))(action)
        # The original APA interpreter needs only Python stdlib.
        # All installed vendor versions are checked in the isolated interpreter.
        dependencies[command] = []
    router.add_local_provider(NAMESPACE, contracts, handlers,
                              "APA_SOURCE_READONLY_ISOLATED_ANALYSIS_V1",
                              dependencies)
    for command in COMMANDS:
        key = "AddOn." + NAMESPACE + "." + command
        router.review_policy(key, "READ_ONLY", "READ_ONLY",
                             {"source": "APA_EXTERNAL_READONLY_V1",
                              "sha256": router.contract_hash(key)})
    return {"schema": "APA_EXTERNAL_LOCAL_PROVIDER_V1",
            "status": "REGISTERED_READ_ONLY_NO_NATIVE_EXECUTION",
            "commands": sorted("AddOn." + NAMESPACE + "." + x for x in COMMANDS),
            "nativeCalls": 0, "modelWrites": 0}
