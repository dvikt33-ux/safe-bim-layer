"""Explicit six-command installed B1+B2 smoke on generated files only."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from apa_external_ifc_vendor_smoke import create_ifc
from ifctester import ids
import apa_high_density_readonly_v2 as V2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    root = args.output_dir.resolve()
    V2.require(root != V2.STABLE.resolve() and V2.STABLE.resolve() not in root.parents,
               "OUTPUT_INSIDE_APA")
    root.mkdir(exist_ok=False)
    model = root / "sample.ifc"
    create_ifc(model, "Wall A")
    spec_path = root / "wall-name.ids"
    document = ids.Ids(title="B1 B2 smoke")
    specification = ids.Specification(name="Wall name", ifcVersion=["IFC4"])
    specification.applicability.append(ids.Entity(name="IFCWALL"))
    specification.requirements.append(ids.Attribute(name="Name"))
    document.specifications.append(specification)
    document.to_xml(str(spec_path))
    before = {p.name: V2.digest(p) for p in (model, spec_path)}
    folder = V2.STABLE / "external-tools/apa-ifc-artifacts-b2"
    factory = folder / "apa_ifc_artifacts_factory_b2.py"
    spec = importlib.util.spec_from_file_location("installed_b2_factory_smoke", factory)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    router = module.native_command_router()
    cases = [
        ("APAIFCReportsB1.IFCSelect", {"query": "IfcWall"}),
        ("APAIFCReportsB1.IFCSchemaValidate", {}),
        ("APAIFCReportsB1.IDSReportODS", {"ids": str(spec_path)}),
        ("APAIFCArtifactsB2.IFCCSVExport", {"query": "IfcWall", "attributes": ["Name"]}),
        ("APAIFCArtifactsB2.IFCExtractElements", {"query": "IfcWall"}),
        ("APAIFCArtifactsB2.IFCBCFIssues", {"query": "IfcWall", "title": "Review wall",
                                          "description": "Synthetic smoke", "author": "APA smoke"})]
    records = []
    for name, params in cases:
        out = root / name.split(".")[-1]
        params.update(a=str(model), output=str(out))
        key = "AddOn." + name
        ticket = router.prepare(key, params)
        V2.require(ticket["nativeWritePermission"] is False, "NATIVE_WRITE_PERMISSION")
        result = router.read(None, ticket, reviewed_read_only=True)
        actual = json.loads((out / "report.json").read_text(encoding="utf8"))
        V2.require(actual == result, "REPORT_READBACK_MISMATCH")
        records.append({"command": key, "status": "PASS", "reportSHA256": V2.digest(out / "report.json")})
    V2.require(before == {p.name: V2.digest(p) for p in (model, spec_path)}, "SOURCE_CHANGED")
    receipt = {"schema": "APA_B1_B2_INSTALLED_SMOKE", "commands": records,
               "passed": len(records), "sourceUnchanged": True, "fixtureKind": "SYNTHETIC_IFC4_IDS",
               "installedFactorySHA256": V2.digest(factory), "nativeCalls": 0, "plnWrites": 0}
    (root / "receipt.json").write_text(json.dumps(receipt, indent=2), encoding="utf8")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
