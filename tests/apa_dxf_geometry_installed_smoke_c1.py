"""Explicit installed C1 report smoke on generated DXF only."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import ezdxf
import apa_high_density_readonly_v2 as V2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    root = args.output_dir.resolve()
    V2.require(root != V2.STABLE.resolve() and V2.STABLE.resolve() not in root.parents,
               "OUTPUT_INSIDE_APA")
    root.mkdir(exist_ok=False)
    source = root / "sample.dxf"
    doc = ezdxf.new("R2013")
    doc.header["$INSUNITS"] = 4
    block = doc.blocks.new("ASSEMBLY")
    block.add_lwpolyline([(0, 0), (2, 0), (2, 1), (0, 1)], close=True)
    doc.modelspace().add_blockref("ASSEMBLY", (10, 20))
    doc.modelspace().add_blockref("ASSEMBLY", (30, 20))
    doc.saveas(str(source))
    before = V2.digest(source)
    factory = V2.STABLE / "external-tools/apa-dxf-geometry-c1/apa_dxf_geometry_factory_c1.py"
    spec = importlib.util.spec_from_file_location("installed_c1_factory_smoke", factory)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    router = module.native_command_router()
    records = []
    for command in ("DXFWorldPaths", "DXFClosedContours", "DXFRepeatedAssemblies"):
        output = root / (command + ".json")
        key = "AddOn.APADXFGeometryC1." + command
        ticket = router.prepare(key, {"a": str(source), "output": str(output)})
        V2.require(ticket["nativeWritePermission"] is False, "NATIVE_WRITE_PERMISSION")
        result = router.read(None, ticket, reviewed_read_only=True)
        V2.require(result == json.loads(output.read_text(encoding="utf8")), "READBACK_MISMATCH")
        payload = result["result"]
        V2.require(payload["repeatedAssemblies"]["total"] == 1 if command == "DXFRepeatedAssemblies"
                   else payload["paths"]["total"] == 2, "GEOMETRY_RESULT_MISMATCH")
        records.append({"command": key, "status": "PASS", "reportSHA256": V2.digest(output)})
    V2.require(before == V2.digest(source), "SOURCE_CHANGED")
    receipt = {"schema": "APA_C1_INSTALLED_SMOKE", "commands": records, "passed": 3,
               "sourceUnchanged": True, "fixtureKind": "SYNTHETIC_DXF", "nativeCalls": 0,
               "plnWrites": 0, "installedFactorySHA256": V2.digest(factory)}
    (root / "receipt.json").write_text(json.dumps(receipt, indent=2), encoding="utf8")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
