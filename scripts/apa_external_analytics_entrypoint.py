"""Production-facing READ_ONLY APA AC29 file analysis via installed session factory.

Always builds the existing source-verified DynamicCommands router through the
installed persistent wrapper and dispatches only the six reviewed provider
commands. Does not open/save PLN, connect to Archicad, or trigger native writes.
This is an opt-in analytics CLI, not a global patch or an automatic AI selector.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(r"C:\LocalAI\APA_AC29_Stable")
FOLDER = ROOT / "external-tools" / "apa-readonly-v1"
SESSION = FOLDER / "session-factory-v1"
COMMANDS = {
    "IFCDiff": ("a", "b", "output"),
    "IFCClash": ("a", "output"),
    "IDSValidate": ("a", "ids", "output"),
    "IFCQuantities": ("a", "output"),
    "PDFVectors": ("a", "output"),
    "DXFVectors": ("a", "output"),
}
EXTS = {"IFCDiff": ".ifc", "IFCClash": ".ifc",
        "IDSValidate": ".ifc", "IFCQuantities": ".ifc",
        "PDFVectors": ".pdf", "DXFVectors": ".dxf"}


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verified_session():
    """Fail closed on any sidecar or original Tapir source mismatch."""
    import importlib.util
    receipt = SESSION / "session-factory-install.json"
    factory = SESSION / "apa_external_session_factory.py"
    schema = SESSION / "tapir-scene-live.json"
    installed_receipt = FOLDER / "installation.json"
    require(all(p.is_file() for p in (receipt, factory, schema, installed_receipt)),
            "PERSISTENT_FACTORY_NOT_INSTALLED")
    manifest = json.loads(receipt.read_text(encoding="utf-8"))
    base = json.loads(installed_receipt.read_text(encoding="utf-8"))
    require(manifest.get("schema") == "APA_AC29_READONLY_SESSION_FACTORY_INSTALL_V1"
            and manifest.get("status") == "SESSION_FACTORY_INSTALLED_READY",
            "PERSISTENT_FACTORY_RECEIPT_INVALID")
    require(sha256(factory) == manifest.get("factorySHA256")
            and sha256(schema) == manifest.get("schemaSHA256")
            and sha256(FOLDER / "apa_external_readonly.py")
              == manifest.get("adapterSHA256") == base.get("adapterSHA256")
            and sha256(FOLDER / "apa_external_catalog.py")
              == manifest.get("catalogSHA256") == base.get("catalogSHA256"),
            "PERSISTENT_FACTORY_OR_VENDOR_HASH_DRIFT")
    proof = manifest.get("provenanceSHA256")
    require(isinstance(proof, dict)
            and set(proof) == {"command_definitions.js", "common_schema_definitions.js"}
            and all((SESSION / p).is_file()
                    and sha256(SESSION / p) == proof[p] for p in proof),
            "PERSISTENT_TAPIR_JS_PROVENANCE_DRIFT")
    spec = importlib.util.spec_from_file_location("apa_external_session_factory", factory)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod, schema


def route_once(command, a, output, b=None, ids=None):
    require(command in COMMANDS, "UNREVIEWED_EXTERNAL_COMMAND")
    inputs = {"a": a, "b": b, "ids": ids}
    expected_extension = EXTS[command]
    source = Path(a).resolve(strict=True)
    require(source.is_file() and source.suffix.casefold() == expected_extension,
            "SOURCE_SUFFIX_OR_FILE_INVALID")
    secondary = None
    if b is not None:
        require(command in {"IFCClash", "IFCDiff"}, "SECOND_IFC_NOT_ALLOWED")
        secondary = Path(b).resolve(strict=True)
        require(secondary.is_file() and secondary.suffix.casefold() == ".ifc",
                "SECOND_IFC_INVALID")
    if ids is not None:
        require(command == "IDSValidate", "IDS_ONLY_WITH_IDSVALIDATE")
        specfile = Path(ids).resolve(strict=True)
        require(specfile.is_file() and specfile.suffix.casefold() == ".ids",
                "IDS_FILE_INVALID")
    require(not (command == "IFCDiff" and secondary is None) and
            not (command == "IDSValidate" and ids is None),
            "SECONDARY_SOURCE_REQUIRED")
    dest = Path(output).resolve()
    require(dest.suffix.casefold() == ".json" and dest.parent.is_dir()
            and not dest.exists(), "OUTPUT_MUST_BE_NEW_JSON_IN_EXISTING_DIRECTORY")
    require(dest != source and dest != secondary, "REPORT_SOURCE_COLLISION")
    require(ROOT.resolve() not in dest.parents,
            "OUTPUT_INSIDE_STABLE_APA_FORBIDDEN")

    factory, schema = verified_session()
    router = factory.native_command_router(schema, include_functional_modules=False)
    key = "AddOn.APAExternalReadOnly." + command
    require(key in router.catalog["commands"] and
            router.operation_kind(key) == "READ_ONLY" and
            router.catalog["commands"][key].get("api") == "local-python",
            "COMMAND_NOT_REGISTERED_AS_REVIEWED_READ_ONLY")

    parameters = {"a": str(source), "output": str(dest)}
    if secondary is not None:
        parameters["b"] = str(secondary)
    if ids is not None:
        parameters["ids"] = str(Path(ids).resolve(strict=True))
    ticket = router.prepare(key, parameters)
    require(ticket.get("nativeWritePermission") is False and
            ticket.get("effect") == "READ_ONLY",
            "NATIVE_WRITE_SCOPE_DETECTED")
    result = router.read(None, ticket, reviewed_read_only=True)
    require(result.get("schema") == "APA_EXTERNAL_READONLY_EVIDENCE_V1"
            and result.get("nativeCalls") == result.get("modelWrites") == 0
            and result.get("action") in {
                "ifc-diff", "ifc-clash", "ids-validate", "ifc-qto",
                "pdf-vectors", "dxf-vectors"}
            and dest.is_file(), "REVIEWED_EXTERNAL_EVIDENCE_NOT_VERIFIED")
    return {
        "schema": "APA_AC29_READONLY_PRODUCTION_ANALYTICS_V1",
        "status": "APA_EXTERNAL_ROUTED_READ_ONLY_PASS",
        "command": key,
        "output": str(dest),
        "evidenceSHA256": sha256(dest),
        "nativeCalls": 0, "plnWrites": 0,
        "factorySessionAutoRegistered": True,
        "existingOtherAPASessionsChanged": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--command", choices=sorted(COMMANDS), required=True)
    parser.add_argument("--a", required=True, help="Existing IFC/PDF/DXF input")
    parser.add_argument("--b", help="Second existing IFC (diff or clash)")
    parser.add_argument("--ids", help="Existing IDS XML for IDSValidate")
    parser.add_argument("--output", required=True, help="New JSON report, outside stable APA")
    args = parser.parse_args(argv)
    print(json.dumps(route_once(args.command, args.a, args.output, args.b, args.ids),
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print("APA_STATUS: PRODUCTION_READ_ONLY_ANALYTICS_BLOCKED")
        print("ERROR:", type(exc).__name__ + ": " + str(exc))
        sys.exit(2)
