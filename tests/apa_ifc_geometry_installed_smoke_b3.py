"""Three installed geometry operations and 30-route catalog smoke."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from apa_external_ifc_vendor_smoke import create_ifc
import apa_high_density_readonly_v2 as V2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    root = args.output_dir.resolve()
    V2.require(root != V2.STABLE.resolve() and V2.STABLE.resolve() not in root.parents, "OUTPUT_INSIDE_APA")
    root.mkdir(exist_ok=False)
    source = root / "sample.ifc"
    create_ifc(source, "B3 geometry wall")
    before = V2.digest(source)
    factory = V2.STABLE / "external-tools/apa-ifc-geometry-b3/apa_ifc_geometry_factory_b3.py"
    spec = importlib.util.spec_from_file_location("installed_b3_factory_smoke", factory)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    router = module.native_command_router()
    prefixes = tuple("AddOn." + n + "." for n in ("APAExternalReadOnly", "APAHighDensityReadOnlyV2",
                     "APAIFCReportsB1", "APAIFCArtifactsB2", "APADXFGeometryC1", "APAIFCGeometryB3"))
    keys = sorted(k for k in router.catalog["commands"] if k.startswith(prefixes))
    V2.require(len(keys) == 30 and all(router.operation_kind(k) == "READ_ONLY" for k in keys),
               "THIRTY_READONLY_CONTRACTS_REQUIRED")
    records = []
    for command in ("IFCGeometryOBJ", "IFCGeometryGLB", "IFCGeometryBounds"):
        out = root / command
        key = "AddOn.APAIFCGeometryB3." + command
        ticket = router.prepare(key, {"a": str(source), "output": str(out), "query": "IfcWall"})
        V2.require(ticket["nativeWritePermission"] is False, "NATIVE_WRITE_PERMISSION")
        result = router.read(None, ticket, reviewed_read_only=True)
        V2.require(result == json.loads((out / "report.json").read_text(encoding="utf8"))
                   and result["processedElements"] == 1, "REPORT_READBACK_MISMATCH")
        records.append({"command": key, "status": "PASS", "reportSHA256": V2.digest(out / "report.json"),
                        "artifactSHA256": result["artifact"]["sha256"]})
    V2.require(before == V2.digest(source), "SOURCE_CHANGED")
    receipt = {"schema": "APA_B3_INSTALLED_SMOKE", "commands": records, "passed": 3,
               "readOnlyCatalogCommands": keys, "catalogCount": 30, "sourceUnchanged": True,
               "fixtureKind": "SYNTHETIC_IFC4", "installedFactorySHA256": V2.digest(factory),
               "installedAdapterSHA256": V2.digest(factory.with_name("apa_ifc_geometry_b3.py")),
               "nativeCalls": 0, "plnWrites": 0}
    (root / "receipt.json").write_text(json.dumps(receipt, indent=2), encoding="utf8")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
