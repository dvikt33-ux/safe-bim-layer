"""Opt-in APA AC29 V1 + V2 session composition (draft; NOT installed).

No patch to the original DynamicCommands, no global monkey-patch, no Archicad
connection. Only NEW sessions made via this factory receive the 12 V2 reads.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

STABLE = Path(r"C:\LocalAI\APA_AC29_Stable")
V1_FACTORY = (STABLE / "external-tools" / "apa-readonly-v1" /
              "session-factory-v1" / "apa_external_session_factory.py")
V1_RECEIPT = V1_FACTORY.with_name("session-factory-install.json")
V2_DIR = STABLE / "external-tools" / "apa-readonly-v2"
V2_SOURCE = V2_DIR / "apa_high_density_readonly_v2.py"
V2_FACTORY = V2_DIR / "apa_high_density_session_factory_v2.py"
V2_RECEIPT = V2_DIR / "installation-v2.json"
V1_PREFIX = "AddOn.APAExternalReadOnly."
V2_PREFIX = "AddOn.APAHighDensityReadOnlyV2."


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, str(path))
    require(spec is not None and spec.loader is not None,
            "V2_MODULE_LOADER_UNAVAILABLE")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verified_modules():
    """Fail closed on both sidecar manifests without modifying either one."""
    require(all(p.is_file() for p in
                (V1_FACTORY, V1_RECEIPT, V2_SOURCE, V2_FACTORY, V2_RECEIPT)),
            "V1_OR_V2_INSTALL_RECEIPT_MISSING")
    v1 = json.loads(V1_RECEIPT.read_text(encoding="utf-8"))
    v2 = json.loads(V2_RECEIPT.read_text(encoding="utf-8"))
    require(v1.get("schema") == "APA_AC29_READONLY_SESSION_FACTORY_INSTALL_V1"
            and v1.get("factorySHA256") == sha256(V1_FACTORY),
            "V1_FACTORY_MANIFEST_OR_HASH_DRIFT")
    require(v2.get("schema") == "APA_AC29_HIGH_DENSITY_READONLY_INSTALL_V2"
            and v2.get("v2SourceSHA256") == sha256(V2_SOURCE)
            and v2.get("v2FactorySHA256") == sha256(V2_FACTORY)
            and v2.get("v1FactorySHA256") == sha256(V1_FACTORY),
            "V2_INSTALL_MANIFEST_OR_HASH_DRIFT")
    return load(V1_FACTORY, "apa_source_verified_v1_factory"), load(
        V2_SOURCE, "apa_source_verified_v2_provider")


def native_command_router(schema_path, official_commands=None,
                          include_functional_modules=True):
    original, v2 = verified_modules()
    router = original.native_command_router(
        schema_path, official_commands, include_functional_modules)
    previous = set(router.catalog["commands"])
    v1_commands = {x for x in previous if x.startswith(V1_PREFIX)}
    require(len(v1_commands) == 6 and
            all(router.operation_kind(x) == "READ_ONLY" and
                router.catalog["commands"][x].get("api") == "local-python"
                for x in v1_commands),
            "V1_SIX_BASELINE_NOT_VERIFIED")
    result = v2.register(router)
    final = set(router.catalog["commands"])
    v2_commands = {x for x in final if x.startswith(V2_PREFIX)}
    require(len(v2_commands) == 12 and result.get("addedCommands") == 12
            and final - previous == v2_commands
            and all(router.operation_kind(x) == "READ_ONLY" and
                    router.catalog["commands"][x].get("api") == "local-python"
                    for x in v2_commands),
            "V2_TWELVE_COMMAND_REGISTRATION_NOT_VERIFIED")
    require(result.get("nativeCalls") == result.get("modelWrites") == 0,
            "V2_WRITER_SCOPE_DETECTED")
    return router


def probe(schema_path, include_functional_modules=False):
    router = native_command_router(
        schema_path, include_functional_modules=include_functional_modules)
    names = set(router.catalog["commands"])
    v1 = sorted(x for x in names if x.startswith(V1_PREFIX))
    v2 = sorted(x for x in names if x.startswith(V2_PREFIX))
    return {"schema": "APA_AC29_COMPOSED_READONLY_V2_CATALOG",
            "status": "SOURCE_REGISTERED_ONLY_NO_VENDOR_EXECUTION",
            "oldReadOnlyCommands": v1, "newReadOnlyCommands": v2,
            "registeredV1": len(v1), "registeredV2": len(v2),
            "combined": len(v1) + len(v2),
            "nativeCalls": 0, "modelWrites": 0,
            "originalAPAFilesModified": False,
            "liveArchicadConnected": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schema", required=True)
    args = parser.parse_args(argv)
    print(json.dumps(probe(args.schema), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print("APA_STATUS: V2_REGISTRATION_BLOCKED")
        print("ERROR:", type(error).__name__ + ": " + str(error))
        raise SystemExit(2)
