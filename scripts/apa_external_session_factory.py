"""Drop-in APA AC29 router factory with installed read-only vendor providers.

For opt-in launchers use `from apa_external_session_factory import native_command_router`
instead of importing that name from the original accelerator. Delegates to
the ORIGINAL accelerator factory then attaches six installed, source-reviewed
READ_ONLY handlers. It is session-local, no daemon/global monkey patch.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys

STABLE = Path(r"C:\LocalAI\APA_AC29_Stable")
INSTALLED_CATALOG = STABLE / "external-tools" / "apa-readonly-v1" / "apa_external_catalog.py"


def require(test, reason):
    if not test:
        raise ValueError(reason)


def original_factory():
    stable_scripts = STABLE / "scripts"
    require(stable_scripts.is_dir(), "STABLE_APA_SCRIPTS_NOT_FOUND")
    sys.path.insert(0, str(stable_scripts))
    from archicad_project_accelerator import native_command_router as original
    return original


def attach_existing(router):
    require(INSTALLED_CATALOG.is_file(), "ISOLATED_EXTERNAL_CATALOG_NOT_INSTALLED")
    spec = importlib.util.spec_from_file_location("apa_external_catalog_session",
                                                  INSTALLED_CATALOG)
    plugin = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(plugin)
    register = plugin.register(router)
    keys = register.get("commands", [])
    require(len(keys) == 6, "SIX_VENDOR_COMMANDS_REQUIRED")
    for name in keys:
        require(router.operation_kind(name) == "READ_ONLY" and
                router.catalog["commands"][name]["api"] == "local-python",
                "EXTERNAL_COMMAND_PERMISSION_OR_OWNER_DRIFT")
    return register


def native_command_router(schema_path, official_commands=None,
                          include_functional_modules=True):
    """Automatically attach six commands to each router created by THIS factory.

    Preserves the underlying catalog, SDK providers, and existing workflows.
    No permission to execute native edits is added.
    """
    original = original_factory()
    router = original(schema_path, official_commands, include_functional_modules)
    receipt = attach_existing(router)
    require(receipt.get("modelWrites") == 0 and
            receipt.get("nativeCalls") == 0, "EXTERNAL_ATTACH_WRITES_FORBIDDEN")
    return router


def probe(schema_path, include_functional_modules=False):
    router = native_command_router(schema_path, include_functional_modules=include_functional_modules)
    keys = sorted(x for x in router.catalog["commands"]
                  if x.startswith("AddOn.APAExternalReadOnly."))
    require(len(keys) == 6, "SESSION_FACTORY_VENDOR_COMMAND_CARDINALITY")
    return {"schema": "APA_AC29_EXTERNAL_SESSION_FACTORY_V1",
            "status": "FACTORY_SESSION_READ_ONLY_REGISTERED",
            "registered": keys,
            "catalogCommands": len(router.catalog["commands"]),
            "autoRegisteredWithinFactorySessions": True,
            "functionalModulesIncluded": include_functional_modules,
            "autoRegisteredInExistingRunningProcesses": False,
            "modelWrites": 0, "nativeCalls": 0}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--schema", type=Path)
    p.add_argument("--include-functional-modules", action="store_true",
                   help="Explicitly attach existing optional SDK/functional module contracts")
    args = p.parse_args(argv)
    default = STABLE / "schemas" / "tapir-live-1.5.10" / "tapir-scene-live.json"
    fallback = Path(__file__).resolve().with_name("tapir-scene-live.json")
    if not fallback.is_file():
        fallback = Path(__file__).resolve().parents[1] / "schemas" / "tapir-live-1.5.10" / "tapir-scene-live.json"
    schema = args.schema or (default if default.is_file() else fallback)
    require(schema.is_file(), "APPROVED_TAPIR_SCHEMA_NOT_FOUND")
    print(json.dumps(probe(schema, args.include_functional_modules), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("APA_STATUS: EXTERNAL_SESSION_FACTORY_BLOCKED")
        print("ERROR:", type(exc).__name__ + ": " + str(exc))
        sys.exit(2)
