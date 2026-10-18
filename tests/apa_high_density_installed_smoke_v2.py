"""Explicit installed V2 smoke, synthetic exported files; no Archicad calls."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from apa_external_ifc_vendor_smoke import create_ifc
import apa_high_density_readonly_v2 as P
import apa_high_density_session_factory_v2 as F
import ezdxf


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    root = args.output_dir.resolve()
    P.require(root != P.STABLE.resolve() and P.STABLE.resolve() not in root.parents,
              "OUTPUT_INSIDE_APA")
    root.mkdir(exist_ok=False)
    model = root / "sample.ifc"
    drawing = root / "sample.dxf"
    create_ifc(model, "V2 smoke wall")
    doc = ezdxf.new("R2013")
    doc.header["$INSUNITS"] = 4
    block = doc.blocks.new("REPEATED")
    block.add_line((0, 0), (2, 0))
    space = doc.modelspace()
    space.add_blockref("REPEATED", (3, 4))
    space.add_text("V2 annotation")
    space.add_linear_dim(base=(0, 2), p1=(0, 0), p2=(2, 0)).render()
    doc.saveas(str(drawing))
    before = {p.name: P.digest(p) for p in (model, drawing)}
    old, installed = F.verified_modules()
    schema = F.V1_FACTORY.with_name("tapir-scene-live.json")
    router = F.native_command_router(schema, include_functional_modules=False)
    records = []
    for name, (action, suffix) in installed.COMMANDS.items():
        source = model if suffix == ".ifc" else drawing
        output = root / (name + ".json")
        key = "AddOn." + installed.NAMESPACE + "." + name
        ticket = router.prepare(key, {"a": str(source), "output": str(output)})
        P.require(ticket["nativeWritePermission"] is False, "NATIVE_WRITE_PERMISSION")
        result = router.read(None, ticket, reviewed_read_only=True)
        actual = json.loads(output.read_text(encoding="utf8"))
        P.require(actual == result and actual["action"] == action
                  and actual["sources"][0]["sha256"] == before[source.name]
                  and actual["adapterSha256"] == P.digest(F.V2_SOURCE), "READBACK_FAILED")
        records.append({"command": key, "reportSHA256": P.digest(output), "status": "PASS"})
    P.require(before == {p.name: P.digest(p) for p in (model, drawing)}, "SOURCE_CHANGED")
    receipt = {"schema": "APA_V2_INSTALLED_VENDOR_SMOKE", "commands": records,
               "count": len(records), "originalV1Contracts": 6, "sourceUnchanged": True,
               "fixtureKind": "SYNTHETIC_IFC4_DXF", "nativeCalls": 0, "plnWrites": 0,
               "installedAdapterSHA256": P.digest(F.V2_SOURCE),
               "installedFactorySHA256": P.digest(F.V2_FACTORY)}
    (root / "receipt.json").write_text(json.dumps(receipt, indent=2), encoding="utf8")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
