"""One-time opt-in deployment of APA AC29 read-only session factory.

Copies only a reviewed router wrapper and exact Tapir schema to a new folder
below the *existing* installed sidecar. Does not patch archicad_project_accelerator,
the signed dynamic router, other APA controllers, Dispatcher, APX, or any PLN.
Existing processes do not auto-attach and are NOT restarted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

STABLE = Path(r"C:\LocalAI\APA_AC29_Stable")
EXT = STABLE / "external-tools" / "apa-readonly-v1"
DEST = EXT / "session-factory-v1"
SOURCE = Path(__file__).resolve().with_name("apa_external_session_factory.py")
SCHEMA = Path(__file__).resolve().parents[1] / "schemas" / "tapir-live-1.5.10" / "tapir-scene-live.json"
EXPECTED_ADAPTER_SHA256 = "83421ab9a0315d5813bb5e0ce1ade2f616c0be830f5a87f35a6226c74b85a75a"


def require(condition, msg):
    if not condition:
        raise ValueError(msg)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def preflight():
    require(SOURCE.is_file() and SCHEMA.is_file(), "SOURCE_FACTORY_OR_TAPIR_SCHEMA_MISSING")
    py = EXT / "venv" / "Scripts" / "python.exe"
    require(py.is_file(), "INSTALLED_VENDOR_VENV_PYTHON_MISSING")
    receipt = EXT / "installation.json"
    adapter = EXT / "apa_external_readonly.py"
    catalog = EXT / "apa_external_catalog.py"
    require(receipt.is_file() and adapter.is_file() and catalog.is_file(),
            "INSTALLED_EXTERNAL_TOOLS_NOT_FOUND")
    metadata = json.loads(receipt.read_text(encoding="utf-8"))
    require(metadata.get("schema") == "APA_EXTERNAL_READONLY_INSTALL_V1" and
            metadata.get("status") == "EXTERNAL_READONLY_INSTALLED_READY",
            "INSTALLED_EXTERNAL_RECEIPT_INVALID")
    require(sha(adapter) == metadata.get("adapterSHA256") == EXPECTED_ADAPTER_SHA256,
            "INSTALLED_ADAPTER_VERSION_DRIFT")
    require(sha(catalog) == metadata.get("catalogSHA256"),
            "INSTALLED_EXTERNAL_CATALOG_DRIFT")
    require((STABLE / "scripts" / "archicad_project_accelerator.py").is_file() and
            (STABLE / "scripts" / "archicad_dynamic_commands.py").is_file(),
            "ORIGINAL_STABLE_APA_ROUTER_MISSING")
    return {"python": py,
            "schemaSHA256": sha(SCHEMA),
            "factorySHA256": sha(SOURCE),
            "adapterSHA256": sha(adapter),
            "catalogSHA256": sha(catalog)}


def verify_install():
    state = preflight()
    receipt = DEST / "session-factory-install.json"
    factory = DEST / SOURCE.name
    schema = DEST / "tapir-scene-live.json"
    require(receipt.is_file() and factory.is_file() and schema.is_file(),
            "SESSION_FACTORY_INSTALL_NOT_COMPLETE")
    data = json.loads(receipt.read_text(encoding="utf-8"))
    require(data.get("schema") == "APA_AC29_READONLY_SESSION_FACTORY_INSTALL_V1" and
            data.get("status") == "SESSION_FACTORY_INSTALLED_READY" and
            data.get("factorySHA256") == sha(factory) == state["factorySHA256"] and
            data.get("schemaSHA256") == sha(schema) == state["schemaSHA256"] and
            data.get("adapterSHA256") == state["adapterSHA256"] and
            data.get("catalogSHA256") == state["catalogSHA256"],
            "SESSION_FACTORY_OR_SOURCE_HASH_DRIFT")
    result = subprocess.run([str(state["python"]), str(factory),
                             "--schema", str(schema)], capture_output=True,
                            text=True, timeout=120)
    require(result.returncode == 0, "INSTALLED_FACTORY_PROBE_BLOCKED:"
            + result.stdout[-850:] + result.stderr[-850:])
    output = json.loads(result.stdout)
    require(output.get("status") == "FACTORY_SESSION_READ_ONLY_REGISTERED" and
            output.get("autoRegisteredWithinFactorySessions") is True and
            output.get("nativeCalls") == output.get("modelWrites") == 0 and
            len(output.get("registered", [])) == 6,
            "SESSION_FACTORY_PROBE_RESULT_INVALID")
    return {"status": "SESSION_FACTORY_INSTALLED_READY",
            "path": str(factory), "schemaPath": str(schema),
            "registeredCommands": output["registered"],
            "originalCorePatched": False,
            "existingProcessesModified": False,
            "nativeCalls": 0, "plnWrites": 0}


def install():
    state = preflight()
    require(not DEST.exists(), "SESSION_FACTORY_EXISTS_AUDIT_OR_CHECK")
    DEST.mkdir(parents=False, exist_ok=False)
    factory = DEST / SOURCE.name
    schema = DEST / "tapir-scene-live.json"
    with factory.open("xb") as fd:
        fd.write(SOURCE.read_bytes())
    with schema.open("xb") as fd:
        fd.write(SCHEMA.read_bytes())
    test = subprocess.run([str(state["python"]), str(factory), "--schema", str(schema)],
                          capture_output=True, text=True, timeout=120)
    require(test.returncode == 0,
            "SESSION_FACTORY_PROBE_FAILED:" + test.stdout[-850:] + test.stderr[-850:])
    output = json.loads(test.stdout)
    require(output.get("status") == "FACTORY_SESSION_READ_ONLY_REGISTERED" and
            len(output.get("registered", [])) == 6 and
            output.get("nativeCalls") == output.get("modelWrites") == 0,
            "SESSION_FACTORY_NOT_READ_ONLY")
    manifest = {
        "schema": "APA_AC29_READONLY_SESSION_FACTORY_INSTALL_V1",
        "status": "SESSION_FACTORY_INSTALLED_READY",
        "factorySHA256": sha(factory),
        "schemaSHA256": sha(schema),
        "adapterSHA256": state["adapterSHA256"],
        "catalogSHA256": state["catalogSHA256"],
        "originalCorePatched": False,
        "existingProcessesModified": False,
        "nativeCalls": 0, "plnWrites": 0}
    with (DEST / "session-factory-install.json").open("x", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
        f.write("\n")
    return verify_install()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--install", action="store_true")
    group.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if args.install:
        report = install()
    elif args.check:
        report = verify_install()
    else:
        state = preflight()
        require(not DEST.exists(), "SESSION_FACTORY_ALREADY_EXISTS_USE_CHECK")
        report = {"status": "SESSION_FACTORY_PREFLIGHT_READY_NO_CHANGES",
                  "factorySHA256": state["factorySHA256"],
                  "schemaSHA256": state["schemaSHA256"],
                  "nativeCalls": 0, "plnWrites": 0}
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("APA_STATUS: SESSION_FACTORY_INSTALL_BLOCKED")
        print("ERROR:", type(exc).__name__ + ": " + str(exc))
        sys.exit(2)
