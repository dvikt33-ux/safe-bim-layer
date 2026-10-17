"""Guarded one-time deployment of production read-only CLI for the installed factory.

Creates only a new sidecar script and its own SHA-bound receipt. Does not
change the installed factory, core APA, Dispatcher, PLN, APX, nor global Python.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(r"C:\LocalAI\APA_AC29_Stable")
SIDE = ROOT / "external-tools" / "apa-readonly-v1"
SESSION = SIDE / "session-factory-v1"
SOURCE = Path(__file__).resolve().with_name("apa_external_analytics_entrypoint.py")
TARGET = SESSION / SOURCE.name
RECEIPT = SESSION / "analytics-entrypoint-install.json"


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def preflight():
    py = SIDE / "venv" / "Scripts" / "python.exe"
    factory = SESSION / "apa_external_session_factory.py"
    receipt = SESSION / "session-factory-install.json"
    vendor_receipt = SIDE / "installation.json"
    require(all(p.is_file() for p in (SOURCE, py, factory, receipt, vendor_receipt)),
            "ISOLATED_PERSISTENT_FACTORY_NOT_INSTALLED")
    info = json.loads(receipt.read_text(encoding="utf-8"))
    vendor = json.loads(vendor_receipt.read_text(encoding="utf-8"))
    require(info.get("schema") == "APA_AC29_READONLY_SESSION_FACTORY_INSTALL_V1"
            and info.get("status") == "SESSION_FACTORY_INSTALLED_READY" and
            info.get("factorySHA256") == digest(factory) and
            info.get("adapterSHA256") == vendor.get("adapterSHA256") and
            info.get("catalogSHA256") == vendor.get("catalogSHA256"),
            "INSTALLED_FACTORY_HASH_OR_RECEIPT_DRIFT")
    require((SIDE / "apa_external_catalog.py").is_file() and
            digest(SIDE / "apa_external_catalog.py") == info["catalogSHA256"]
            and digest(SIDE / "apa_external_readonly.py") == info["adapterSHA256"],
            "INSTALLED_VENDOR_ADAPTER_DRIFT")
    require(not TARGET.exists() and not RECEIPT.exists(),
            "PRODUCTION_ANALYTICS_ENTRYPOINT_EXISTS_USE_CHECK")
    compile(SOURCE.read_bytes(), str(SOURCE), "exec")
    return {"python": py, "factorySHA256": digest(factory),
            "adapterSHA256": info["adapterSHA256"],
            "entrypointSHA256": digest(SOURCE)}


def install():
    info = preflight()
    with TARGET.open("xb") as f:
        f.write(SOURCE.read_bytes())
    require(digest(TARGET) == info["entrypointSHA256"],
            "PRODUCTION_ENTRYPOINT_COPY_HASH_DRIFT")
    cli = subprocess.run([str(info["python"]), str(TARGET), "--help"],
                         capture_output=True, text=True, timeout=90)
    require(cli.returncode == 0, "ENTRYPOINT_CLI_IMPORT_FAILED:"
            + cli.stderr[-600:])
    data = {
        "schema": "APA_AC29_EXTERNAL_PRODUCTION_ENTRYPOINT_INSTALL_V1",
        "status": "EXTERNAL_ANALYTICS_ENTRYPOINT_INSTALLED",
        "entrypointSHA256": digest(TARGET),
        "factorySHA256": info["factorySHA256"],
        "adapterSHA256": info["adapterSHA256"],
        "nativeCalls": 0, "plnWrites": 0,
        "coreModified": False, "existingProcessesModified": False}
    with RECEIPT.open("x", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
        file.write("\n")
    return check()


def check():
    require(TARGET.is_file() and RECEIPT.is_file(), "PRODUCTION_ENTRYPOINT_NOT_INSTALLED")
    d = json.loads(RECEIPT.read_text(encoding="utf-8"))
    factory = SESSION / "apa_external_session_factory.py"
    vendor = json.loads((SIDE / "installation.json").read_text(encoding="utf-8"))
    require(d.get("schema") == "APA_AC29_EXTERNAL_PRODUCTION_ENTRYPOINT_INSTALL_V1"
            and d.get("status") == "EXTERNAL_ANALYTICS_ENTRYPOINT_INSTALLED"
            and digest(TARGET) == digest(SOURCE) == d.get("entrypointSHA256")
            and digest(factory) == d.get("factorySHA256")
            and d.get("adapterSHA256") == vendor.get("adapterSHA256")
            and d.get("nativeCalls") == d.get("plnWrites") == 0,
            "EXTERNAL_PRODUCTION_ANALYTICS_RECEIPT_DRIFT")
    return {
        "status": "EXTERNAL_ANALYTICS_ENTRYPOINT_VERIFIED",
        "commandPath": str(TARGET),
        "entrypointSHA256": d["entrypointSHA256"],
        "router": "ORIGINAL_APA_DYNAMIC_COMMANDS",
        "autoAttachInThisEntrypoint": True,
        "autoAttachInExistingOldProcesses": False,
        "coreModified": False,
        "nativeCalls": 0, "plnWrites": 0}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    group = p.add_mutually_exclusive_group()
    group.add_argument("--install", action="store_true")
    group.add_argument("--check", action="store_true")
    args = p.parse_args(argv)
    result = install() if args.install else check() if args.check else preflight()
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("APA_STATUS: PRODUCTION_ANALYTICS_INSTALL_BLOCKED")
        print("ERROR:", type(exc).__name__ + ": " + str(exc))
        sys.exit(2)
