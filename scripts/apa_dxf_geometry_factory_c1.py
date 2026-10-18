"""Opt-in three-command extension of the verified installed B1+B2 factory."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = Path(r"C:\LocalAI\APA_AC29_Stable\external-tools\apa-ifc-artifacts-b2\apa_ifc_artifacts_factory_b2.py")


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def native_command_router(schema_path=None, official_commands=None, include_functional_modules=False):
    receipt = json.loads((HERE / "installation-c1.json").read_text(encoding="utf8"))
    def sha(path):
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    if receipt.get("schema") != "APA_DXF_GEOMETRY_INSTALL_C1" or sha(BASE) != receipt["baseFactorySHA256"] or any(
            sha(HERE / name) != digest for name, digest in receipt["sourceSHA256"].items()):
        raise ValueError("C1_INSTALLED_SOURCE_OR_BASE_DRIFT")
    base = load(BASE, "apa_installed_b2_for_c1")
    router = base.native_command_router(schema_path, official_commands, include_functional_modules)
    before = set(router.catalog["commands"])
    provider = load(HERE / "apa_dxf_geometry_c1.py", "apa_installed_geometry_c1")
    provider.register(router)
    added = set(router.catalog["commands"]) - before
    if len(added) != 3 or any(router.operation_kind(k) != "READ_ONLY" for k in added):
        raise ValueError("C1_THREE_READONLY_CONTRACTS_REQUIRED")
    return router


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--command", required=True)
    parser.add_argument("--a", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if not args.command.startswith("AddOn.APADXFGeometryC1."):
        raise ValueError("ONLY_C1_COMMANDS_ALLOWED")
    router = native_command_router()
    ticket = router.prepare(args.command, {"a": args.a, "output": args.output})
    print(json.dumps(router.read(None, ticket, reviewed_read_only=True), ensure_ascii=False, indent=2))
