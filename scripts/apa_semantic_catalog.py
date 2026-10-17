"""Read-only APA Semantic provider: attach AFTER verified original APA six tools.

Does not touch the installed six-tool factory/catalog, SDK, Tapir, or PLN.
The original DynamicCommands owns catalog, schema validation, and dispatch.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(r"C:\LocalAI\APA_AC29_Stable")
SIDE = ROOT / "external-tools" / "apa-semantic-v1"
NAMESPACE = "APASemantic"
COMMANDS = {
    "PDFPaths": ("pdf-paths", ("a", "page", "output")),
    "OpenBIMSegments": ("openbim", ("a", "output")),
    "RasterFloorplan": ("raster2seq", ("a", "output")),
}


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def installed():
    receipt = SIDE / "installation.json"
    worker = SIDE / "apa_semantic_readonly.py"
    catalog = SIDE / "apa_semantic_catalog.py"
    python = SIDE / "venv" / "Scripts" / "python.exe"
    require(all(p.is_file() for p in (receipt, worker, catalog, python)),
            "APA_SEMANTIC_INSTALL_MISSING")
    info = json.loads(receipt.read_text(encoding="utf-8"))
    require(info.get("schema") == "APA_SEMANTIC_BRIDGE_INSTALL_V1"
            and info.get("workerSHA256") == sha(worker)
            and info.get("catalogSHA256") == sha(catalog),
            "APA_SEMANTIC_INSTALL_HASH_DRIFT")
    return python, worker


def run(action, params):
    require(action in {x[0] for x in COMMANDS.values()},
            "UNREGISTERED_SEMANTIC_COMMAND")
    py, worker = installed()
    out = Path(params["output"]).resolve()
    require(out.suffix.lower() == ".json" and out.parent.is_dir()
            and not out.exists()
            and ROOT.resolve() not in out.parents,
            "SEMANTIC_OUTPUT_NOT_NEW_OUTSIDE_APA")
    cmd = [str(py), str(worker), action,
           "--a", params["a"], "--output", params["output"]]
    if action == "pdf-paths":
        cmd += ["--page", str(params["page"])]
    else:
        config = SIDE / "models.json"
        require(config.is_file(), "SEMANTIC_ML_MODEL_CONFIG_REQUIRED")
        cmd += ["--ml-config", str(config)]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=1900)
    require(result.returncode == 0 and out.is_file(),
            "SEMANTIC_VENDOR_FAILED:" + result.stderr[-850:])
    report = json.loads(out.read_text(encoding="utf-8"))
    require(report.get("schema") == "APA_SEMANTIC_SOURCE_EVIDENCE_V1"
            and report.get("action") == action
            and report.get("modelWrites") == report.get("nativeCalls") == 0
            and report.get("sourceNotModified") is True,
            "SEMANTIC_REPORT_CONTRACT_INVALID")
    return report


def register(router):
    installed()
    contracts, handlers, deps = {}, {}, {}
    for name, (action, required) in COMMANDS.items():
        props = {"a": {"type": "string", "minLength": 1},
                 "output": {"type": "string", "minLength": 1}}
        if name == "PDFPaths":
            props["page"] = {"type": "integer", "minimum": 1}
        contracts[name] = {
            "name": name, "version": "1",
            "category": "APA_SEMANTIC_SOURCE_ANALYSIS",
            "description": "Read-only vendor source analysis: " + action,
            "parameters": {"type": "object", "properties": props,
                           "required": list(required),
                           "additionalProperties": False},
            "returns": {
                "type": "object",
                "required": ["schema", "status", "action", "sources",
                             "result", "modelWrites", "nativeCalls"],
                "properties": {
                    "schema": {"type": "string"},
                    "status": {"type": "string"},
                    "action": {"type": "string"},
                    "sources": {"type": "array"},
                    "result": {"type": "object"},
                    "modelWrites": {"type": "integer"},
                    "nativeCalls": {"type": "integer"},
                },
            },
        }
        handlers[name] = (lambda selected:
                          lambda **kwargs: run(selected, kwargs))(action)
        deps[name] = []
    router.add_local_provider(NAMESPACE, contracts, handlers,
                              "APA_SEMANTIC_VENDOR_ANALYSIS_V1", deps)
    for name in COMMANDS:
        key = "AddOn." + NAMESPACE + "." + name
        router.review_policy(key, "READ_ONLY", "READ_ONLY",
                             {"source": "APA_SEMANTIC_V1",
                              "sha256": router.contract_hash(key)})
    return {
        "schema": "APA_SEMANTIC_PROVIDER_V1",
        "registered": sorted("AddOn." + NAMESPACE + "." + n
                             for n in COMMANDS),
        "nativeCalls": 0, "modelWrites": 0,
    }
