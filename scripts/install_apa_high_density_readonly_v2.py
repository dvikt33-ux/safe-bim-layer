"""Explicit, isolated APA 29 high-density V2 installer (NOT run on import).

Copies only two source-reviewed files into a new external-tools/apa-readonly-v2
folder. Does not edit the existing V1, core APA, Tapir, PLN, APX or main.
Never silently installs pip packages; reuses the verified V1 vendor interpreter.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import shutil
import sys
import tempfile

STABLE = Path(r"C:\LocalAI\APA_AC29_Stable")
EXTERNAL = STABLE / "external-tools"
V1 = EXTERNAL / "apa-readonly-v1"
V1_FACTORY = V1 / "session-factory-v1" / "apa_external_session_factory.py"
V1_FACTORY_RECEIPT = V1_FACTORY.with_name("session-factory-install.json")
V2 = EXTERNAL / "apa-readonly-v2"
HERE = Path(__file__).resolve().parent
SOURCES = ("apa_high_density_readonly_v2.py",
           "apa_high_density_session_factory_v2.py")
INSTALL_RECEIPT = "installation-v2.json"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def existing_v1():
    """Read exact hashes; do not infer vendor install from GitHub source code."""
    vendor = V1 / "installation.json"
    require(all(p.is_file() for p in (vendor, V1_FACTORY, V1_FACTORY_RECEIPT)),
            "V1_ISOLATED_INSTALL_MISSING")
    data = json.loads(vendor.read_text(encoding="utf-8"))
    session = json.loads(V1_FACTORY_RECEIPT.read_text(encoding="utf-8"))
    require(data.get("schema") == "APA_EXTERNAL_READONLY_INSTALL_V1"
            and session.get("schema") == "APA_AC29_READONLY_SESSION_FACTORY_INSTALL_V1"
            and session.get("factorySHA256") == sha256(V1_FACTORY),
            "V1_INSTALL_RECEIPT_SCHEMA_OR_HASH_DRIFT")
    for receipt_key, name in (
        ("adapterSHA256", "apa_external_readonly.py"),
        ("catalogSHA256", "apa_external_catalog.py"),
        ("requirementsSHA256", "requirements-external-readonly.txt"),
    ):
        file = V1 / name
        require(file.is_file() and data.get(receipt_key) == sha256(file),
                "V1_INSTALL_FILE_HASH_DRIFT:" + name)
    vendor_python = V1 / "venv" / "Scripts" / "python.exe"
    require(vendor_python.is_file(), "V1_VERIFIED_VENDOR_PYTHON_MISSING")
    return {"vendorManifestSHA256": sha256(vendor),
            "sessionReceiptSHA256": sha256(V1_FACTORY_RECEIPT),
            "v1FactorySHA256": sha256(V1_FACTORY)}


def verify_sources():
    require(all((HERE / name).is_file() for name in SOURCES),
            "V2_SOURCE_CHECKOUT_INCOMPLETE")
    source = (HERE / SOURCES[0]).read_text(encoding="utf-8")
    require("NAMESPACE = \"APAHighDensityReadOnlyV2\"" in source,
            "V2_EXPECTED_PROVIDER_NAMESPACE_MISSING")
    return {name: sha256(HERE / name) for name in SOURCES}


def preflight():
    require(platform.system() == "Windows" and
            platform.machine().lower() in {"amd64", "x86_64"},
            "WINDOWS_X64_REQUIRED")
    require(EXTERNAL.is_dir(), "STABLE_EXTERNAL_ROOT_NOT_FOUND")
    v1 = existing_v1()
    src = verify_sources()
    return {"status": "V2_SOURCE_READY_NOT_INSTALLED",
            "targetAvailable": not V2.exists(), "v1": v1,
            "sourceSHA256": src, "packagesInstalled": 0,
            "nativeCalls": 0, "plnWrites": 0}


def check():
    require(V2.is_dir(), "V2_NOT_INSTALLED")
    v1 = existing_v1()
    receipt = V2 / INSTALL_RECEIPT
    require(receipt.is_file(), "V2_INSTALL_RECEIPT_MISSING")
    record = json.loads(receipt.read_text(encoding="utf-8"))
    require(record.get("schema") == "APA_AC29_HIGH_DENSITY_READONLY_INSTALL_V2"
            and record.get("status") == "V2_OPT_IN_FILES_INSTALLED"
            and record.get("v1FactorySHA256") == v1["v1FactorySHA256"]
            and record.get("v1VendorManifestSHA256") == v1["vendorManifestSHA256"]
            and record.get("v1SessionReceiptSHA256") == v1["sessionReceiptSHA256"],
            "V2_PROVENANCE_OR_V1_DRIFT")
    for name, key in zip(SOURCES, ("v2SourceSHA256", "v2FactorySHA256")):
        require((V2 / name).is_file() and
                sha256(V2 / name) == record.get(key),
                "V2_INSTALLED_FILE_HASH_DRIFT:" + name)
    return {"status": "V2_FILES_INSTALLED_OPT_IN_NOT_ACTIVE",
            "sourceSHA256": record["v2SourceSHA256"],
            "factorySHA256": record["v2FactorySHA256"],
            "installed": str(V2), "registeredCommands": 0,
            "coreModified": False, "v1Modified": False,
            "nativeCalls": 0, "plnWrites": 0}


def install():
    gate = preflight()
    require(gate["targetAvailable"],
            "V2_ALREADY_EXISTS_CHECK_INSTEAD_OF_OVERWRITE")
    baseline = gate["v1"]
    # Stage in the same filesystem, then rename once. No changes to V1.
    with tempfile.TemporaryDirectory(
        prefix=".apa-readonly-v2-stage-", dir=str(EXTERNAL)) as tmp:
        stage = Path(tmp)
        for file in SOURCES:
            shutil.copy2(HERE / file, stage / file)
        receipt = {
            "schema": "APA_AC29_HIGH_DENSITY_READONLY_INSTALL_V2",
            "status": "V2_OPT_IN_FILES_INSTALLED",
            "v1FactorySHA256": baseline["v1FactorySHA256"],
            "v1VendorManifestSHA256": baseline["vendorManifestSHA256"],
            "v1SessionReceiptSHA256": baseline["sessionReceiptSHA256"],
            "v2SourceSHA256": sha256(stage / SOURCES[0]),
            "v2FactorySHA256": sha256(stage / SOURCES[1]),
            "newCommandsPlanned": 12,
            "originalV1Commands": 6,
            "vendorPackagesInstalled": 0,
            "plnWrites": 0,
            "nativeCalls": 0,
            "requiresOptInFactory": True,
        }
        with (stage / INSTALL_RECEIPT).open("x", encoding="utf-8") as stream:
            json.dump(receipt, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
        require(not V2.exists(), "V2_CONCURRENT_INSTALL_CONFLICT")
        stage.rename(V2)
    return check()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--preflight", action="store_true")
    group.add_argument("--install", action="store_true")
    group.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    outcome = (preflight() if args.preflight else
               install() if args.install else check())
    print(json.dumps(outcome, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        print("APA_STATUS: HIGH_DENSITY_V2_INSTALL_BLOCKED")
        print("ERROR:", type(error).__name__ + ": " + str(error))
        sys.exit(2)
