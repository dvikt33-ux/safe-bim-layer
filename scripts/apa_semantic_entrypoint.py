"""Production opt-in bridge: original APA Router + six vendors + 3 semantic.

No custom dispatcher, no monkey patch, no writer. Existing APA factory is
loaded with its existing SHA receipts by apa_external_analytics_entrypoint.
The new provider is attached after that original six-command factory.
"""
from __future__ import annotations
import argparse
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(r"C:\LocalAI\APA_AC29_Stable")
OLD = ROOT / "external-tools" / "apa-readonly-v1"
SIDE = ROOT / "external-tools" / "apa-semantic-v1"
EXT = {
    "PDFPaths": {".pdf"},
    "OpenBIMSegments": {".png", ".jpg", ".jpeg"},
    "RasterFloorplan": {".png", ".jpg", ".jpeg"},
}


def require(test, reason):
    if not test:
        raise ValueError(reason)


def load_module(name, path):
    require(path.is_file(), "APPROVED_APA_MODULE_NOT_INSTALLED:" + name)
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def factory_session():
    old = load_module("apa_pinned_analytics",
                      OLD / "session-factory-v1"
                      / "apa_external_analytics_entrypoint.py")
    factory, schema = old.verified_session()
    router = factory.native_command_router(
        schema, include_functional_modules=False)
    before = {key for key in router.catalog["commands"]
              if key.startswith("AddOn.APAExternalReadOnly.")}
    require(len(before) == 6 and
            all(router.operation_kind(key) == "READ_ONLY" for key in before),
            "EXISTING_SIX_VENDOR_COMMANDS_NOT_READY")
    ext = load_module("apa_installed_semantic_provider",
                      SIDE / "apa_semantic_catalog.py")
    receipt = ext.register(router)
    keys = receipt["registered"]
    require(len(keys) == 3
            and all(key in router.catalog["commands"]
                    and router.operation_kind(key) == "READ_ONLY"
                    and router.catalog["commands"][key]["api"] == "local-python"
                    for key in keys),
            "SEMANTIC_COMMAND_REGISTRATION_INVALID")
    require(before == {key for key in router.catalog["commands"]
                       if key.startswith("AddOn.APAExternalReadOnly.")},
            "EXISTING_SIX_VENDOR_COMMANDS_CHANGED")
    return router, keys


def run(command=None, a=None, output=None, page=1):
    router, registered = factory_session()
    if command is None:
        return {
            "status": "APA_SEMANTIC_ROUTER_REGISTERED",
            "semanticCommands": registered,
            "originalSixCommandsPreserved": True,
            "modelReadiness": {
                "PDFPaths": "PYMUPDF_INSTALLED_CHECKED_AT_EXECUTION",
                "OpenBIMSegments": "REQUIRES_SEPARATE_VERIFIED_MODEL_CONFIG",
                "RasterFloorplan": "REQUIRES_SEPARATE_VERIFIED_MODEL_CONFIG",
            },
            "nativeCalls": 0, "modelWrites": 0,
        }
    require(command in EXT, "UNREVIEWED_SEMANTIC_COMMAND")
    src = Path(a).resolve(strict=True)
    out = Path(output).resolve()
    require(src.is_file() and src.suffix.lower() in EXT[command],
            "SEMANTIC_INPUT_FILE_SUFFIX_INVALID")
    require(out.parent.is_dir() and out.suffix.lower() == ".json"
            and not out.exists() and ROOT.resolve() not in out.parents,
            "SEMANTIC_OUTPUT_NOT_NEW_OR_INSIDE_STABLE_APA")
    key = "AddOn.APASemantic." + command
    params = {"a": str(src), "output": str(out)}
    if command == "PDFPaths":
        require(page >= 1, "SEMANTIC_PAGE_MUST_BE_POSITIVE")
        params["page"] = page
    ticket = router.prepare(key, params)
    require(ticket.get("nativeWritePermission") is False
            and ticket.get("effect") == "READ_ONLY",
            "SEMANTIC_NATIVE_WRITE_SCOPE_DETECTED")
    result = router.read(None, ticket, reviewed_read_only=True)
    require(result.get("schema") == "APA_SEMANTIC_SOURCE_EVIDENCE_V1"
            and result.get("nativeCalls") == result.get("modelWrites") == 0
            and result.get("sourceNotModified") is True
            and out.is_file(), "SEMANTIC_EVIDENCE_INVALID")
    return {
        "status": "APA_SEMANTIC_ROUTED_SOURCE_ONLY_PASS",
        "command": key,
        "output": str(out),
        "originalSixCommandsPreserved": True,
        "nativeCalls": 0, "modelWrites": 0,
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--probe", action="store_true")
    p.add_argument("--command", choices=sorted(EXT))
    p.add_argument("--a", help="existing PDF or raster floorplan")
    p.add_argument("--page", type=int, default=1,
                   help="1-based PDF page, for PDFPaths")
    p.add_argument("--output", help="new JSON report outside stable APA")
    options = p.parse_args(argv)
    require(options.probe or
            (options.command and options.a and options.output),
            "PROBE_OR_COMPLETE_SEMANTIC_COMMAND_REQUIRED")
    print(json.dumps(
        run() if options.probe
        else run(options.command, options.a, options.output, options.page),
        ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("APA_SEMANTIC_ROUTER_BLOCKED:" + type(e).__name__
              + ":" + str(e), file=sys.stderr)
        sys.exit(2)
