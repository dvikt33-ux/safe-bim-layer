"""Three geometry reports on the existing installed C1 -> B2 -> V2 APA router."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXTERNAL = Path(r"C:\LocalAI\APA_AC29_Stable\external-tools")
BASE = EXTERNAL / "apa-dxf-geometry-c1/apa_dxf_geometry_factory_c1.py"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def native_command_router(schema_path=None, official_commands=None, include_functional_modules=False):
    record = json.loads((HERE / "installation-b3.json").read_text(encoding="utf8"))
    def sha(path):
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    if record.get("schema") != "APA_IFC_GEOMETRY_INSTALL_B3" or sha(BASE) != record["baseFactorySHA256"] or any(
            sha(HERE / name) != digest for name, digest in record["sourceSHA256"].items()):
        raise ValueError("B3_INSTALLED_SOURCE_DRIFT")
    original = load(BASE, "apa_installed_c1_for_b3")
    router = original.native_command_router(schema_path, official_commands, include_functional_modules)
    previous = set(router.catalog["commands"])
    provider = load(HERE / "apa_ifc_geometry_b3.py", "apa_installed_geometry_b3")
    provider.register(router, EXTERNAL / "apa-ifc-artifacts-b2/venv/Scripts/python.exe")
    added = set(router.catalog["commands"]) - previous
    if len(added) != 3 or any(router.operation_kind(k) != "READ_ONLY" for k in added):
        raise ValueError("B3_THREE_READONLY_CONTRACTS_REQUIRED")
    return router


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--command", required=True)
    parser.add_argument("--parameters", required=True)
    args = parser.parse_args()
    if not args.command.startswith("AddOn.APAIFCGeometryB3."):
        raise ValueError("ONLY_B3_COMMANDS_ALLOWED")
    router = native_command_router()
    ticket = router.prepare(args.command, json.loads(args.parameters))
    print(json.dumps(router.read(None, ticket, reviewed_read_only=True), indent=2))
