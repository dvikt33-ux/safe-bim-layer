"""Opt-in six-report extension of the installed, verified V2 APA factory."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
STABLE = Path(r"C:\LocalAI\APA_AC29_Stable")
V2_FACTORY = STABLE / "external-tools/apa-readonly-v2/apa_high_density_session_factory_v2.py"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def native_command_router(schema_path=None, official_commands=None, include_functional_modules=False):
    import hashlib
    def sha(p):
        return hashlib.sha256(Path(p).read_bytes()).hexdigest()
    receipt = json.loads((HERE / "installation-b2.json").read_text(encoding="utf8"))
    if receipt.get("schema") != "APA_IFC_ARTIFACTS_INSTALL_B2" or any(
            sha(HERE / name) != digest for name, digest in receipt["sourceSHA256"].items()):
        raise ValueError("B2_INSTALLED_SOURCE_DRIFT")
    if sha(V2_FACTORY) != receipt["v2FactorySHA256"]:
        raise ValueError("B2_V2_FACTORY_DRIFT")
    sys.path.insert(0, str(HERE))
    original = load(V2_FACTORY, "apa_installed_original_v2_factory")
    schema = schema_path or STABLE / "external-tools/apa-readonly-v1/session-factory-v1/tapir-scene-live.json"
    router = original.native_command_router(schema, official_commands, include_functional_modules)
    old_keys = set(router.catalog["commands"])
    b1 = load(HERE / "apa_ifc_reports_b1.py", "apa_installed_b1")
    b2 = load(HERE / "apa_ifc_artifacts_b2.py", "apa_installed_b2")
    b1.register(router)
    b2.register(router, HERE / "venv/Scripts/python.exe")
    added = set(router.catalog["commands"]) - old_keys
    if len(added) != 6 or any(router.operation_kind(k) != "READ_ONLY" for k in added):
        raise ValueError("B2_SIX_READONLY_CONTRACTS_REQUIRED")
    return router


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--command", required=True)
    parser.add_argument("--parameters", required=True, help="JSON parameters for an existing report contract")
    args = parser.parse_args()
    router = native_command_router()
    if not args.command.startswith(("AddOn.APAIFCReportsB1.", "AddOn.APAIFCArtifactsB2.")):
        raise ValueError("ONLY_SIX_REPORT_COMMANDS_ALLOWED")
    ticket = router.prepare(args.command, json.loads(args.parameters))
    print(json.dumps(router.read(None, ticket, reviewed_read_only=True), ensure_ascii=False, indent=2))
