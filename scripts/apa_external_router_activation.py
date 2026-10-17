"""Real-process APA DynamicCommands registration and read-only execution probe.

Uses the EXACT installed DynamicCommands class and installed external provider.
Does not patch core, start Archicad, open PLN, access HTTP, or submit any job.
Only creates and analyzes throwaway DXF/PDF files inside a temporary folder.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(r"C:\LocalAI\APA_AC29_Stable")
EXT = ROOT / "external-tools" / "apa-readonly-v1"
SCRIPTS = ROOT / "scripts"
LIVE_SCHEMA = ROOT / "schemas" / "tapir-live-1.5.10" / "tapir-scene-live.json"


def check(condition, reason):
    if not condition:
        raise ValueError(reason)


def make_pdf(path):
    """Create one tiny vector PDF with literal line primitive (not a BIM file)."""
    stream = b"10 10 m 160 160 l S\n"
    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] /Resources << >> /Contents 4 0 R >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"endstream",
    ]
    result = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for i, obj in enumerate(objs, 1):
        offsets.append(len(result))
        result.extend(str(i).encode() + b" 0 obj\n" + obj + b"\nendobj\n")
    xref = len(result)
    result.extend(b"xref\n0 5\n0000000000 65535 f \n")
    for offset in offsets[1:]:
        result.extend(("%010d 00000 n \n" % offset).encode())
    result.extend(b"trailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n"
                  + str(xref).encode() + b"\n%%EOF\n")
    path.write_bytes(result)


def load_router():
    check(SCRIPTS.is_dir(), "STABLE_APA_SCRIPTS_NOT_FOUND")
    catalog_source = LIVE_SCHEMA
    if not catalog_source.is_file():
        catalog_source = (Path(__file__).resolve().parents[1] / "schemas" /
                          "tapir-live-1.5.10" / "tapir-scene-live.json")
    check(catalog_source.is_file(), "QUALIFIED_TAPIR_SCHEMA_NOT_FOUND")
    sys.path.insert(0, str(SCRIPTS))
    from archicad_batch_contracts import load_catalog
    from archicad_dynamic_commands import DynamicCommands
    catalog = load_catalog(catalog_source)
    return DynamicCommands(catalog), len(catalog["commands"])


def register_installed(router):
    file = EXT / "apa_external_catalog.py"
    check(file.is_file(), "INSTALLED_EXTERNAL_CATALOG_NOT_FOUND")
    spec = importlib.util.spec_from_file_location("apa_external_catalog", file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    receipt = module.register(router)
    keys = receipt["commands"]
    check(len(keys) == 6 and len(set(keys)) == 6, "EXTERNAL_REGISTERED_CARDINALITY")
    check(all(router.operation_kind(k) == "READ_ONLY" and
              router.select(k)["api"] == "local-python" for k in keys),
          "EXTERNAL_PROVIDER_SCOPE_MISMATCH")
    return receipt


def run_read(router, action, params):
    key = "AddOn.APAExternalReadOnly." + action
    ticket = router.prepare(key, params)
    check(ticket["effect"] == "READ_ONLY" and
          ticket["nativeWritePermission"] is False, "NATIVE_WRITE_GRANT_DETECTED")
    result = router.read(None, ticket, reviewed_read_only=True)
    check(result["schema"] == "APA_EXTERNAL_READONLY_EVIDENCE_V1"
          and result["nativeCalls"] == 0 and result["modelWrites"] == 0,
          "EXTERNAL_PROOF_MISMATCH")
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--real-ifc", type=Path, help="optional existing IFC for quantities")
    p.add_argument("--real-ids", type=Path, help="optional IDS for this IFC")
    args = p.parse_args()
    router, original = load_router()
    registered = register_installed(router)
    outcomes = {}
    with tempfile.TemporaryDirectory(prefix="apa-external-verify-") as t:
        temp = Path(t)
        py = EXT / "venv" / "Scripts" / "python.exe"
        check(py.is_file(), "ISOLATED_VENDOR_PYTHON_NOT_FOUND")
        dxf = temp / "check.dxf"
        code = "import ezdxf,sys; d=ezdxf.new('R2013'); d.modelspace().add_line((0,0),(3,4)); d.saveas(sys.argv[1])"
        subprocess.run([str(py), "-c", code, str(dxf)], timeout=45, check=True)
        pdf = temp / "check.pdf"
        make_pdf(pdf)
        for name, source, k in [("DXFVectors", dxf, "dxf-vectors"),
                                ("PDFVectors", pdf, "pdf-vectors")]:
            output = temp / (name + ".json")
            report = run_read(router, name, {"a": str(source), "output": str(output)})
            # The evidence envelope has a single `result` member:
            # PDF/DXF facts are stored directly in report["result"].
            facts = report["result"]
            check(isinstance(facts, dict), "EXTERNAL_VECTOR_FACTS_NOT_OBJECT")
            if name == "DXFVectors":
                check(facts["primitiveCount"] >= 1 and
                      facts["primitives"][0]["type"] == "LINE",
                      "VENDOR_DXF_PRIMITIVE_MISSING")
                count = facts["primitiveCount"]
            else:
                check(facts["pages"] and facts["pages"][0]["lineCount"] >= 1,
                      "VENDOR_PDF_LINE_MISSING")
                count = facts["pages"][0]["lineCount"]
            check(report["action"] == k, "VENDOR_ACTION_MISMATCH")
            outcomes[name] = {"status": "EXECUTED_REAL_VENDOR_READ_ONLY_PASS",
                              "primitiveCount": count}
        if args.real_ifc:
            file = args.real_ifc.resolve(strict=True)
            check(file.is_file() and file.suffix.casefold() == ".ifc",
                  "IFC_SOURCE_INVALID")
            out = temp / "user-quantities.json"
            try:
                proof = run_read(router, "IFCQuantities",
                                 {"a": str(file), "output": str(out)})
                outcomes["IFCQuantities"] = {
                    "status": "REAL_IFC_SOURCE_READ_PASS",
                    "elementCount": len(proof["result"]["result"].get("elements", []))}
            except Exception as error:
                outcomes["IFCQuantities"] = {
                    "status": "BLOCKED",
                    "reason": type(error).__name__ + ": " + str(error)[:400]}
            if args.real_ids:
                ids = args.real_ids.resolve(strict=True)
                out = temp / "user-ids.json"
                try:
                    proof = run_read(router, "IDSValidate", {
                        "a": str(file), "ids": str(ids), "output": str(out)})
                    outcomes["IDSValidate"] = {
                        "status": "REAL_IFC_IDS_SOURCE_READ_PASS",
                        "result": str(proof["result"].get("vendor", ""))}
                except Exception as error:
                    outcomes["IDSValidate"] = {
                        "status": "BLOCKED",
                        "reason": type(error).__name__ + ": " + str(error)[:400]}
    document = {
        "schema": "APA_AC29_EXTERNAL_ROUTER_LIVE_PROCESS_PROBE_V1",
        "status": "READ_ONLY_ROUTE_PROBE_PASS",
        "existingCatalogCommands": original,
        "registeredLocalCommands": registered["commands"],
        "registeredCount": len(registered["commands"]),
        "observedRuns": outcomes,
        "nativeCalls": 0,
        "plnWrites": 0,
        "autoRegistrationAcrossSessions": False,
    }
    print(json.dumps(document, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        print("APA_STATUS: EXTERNAL_ROUTER_PROBE_BLOCKED")
        print("ERROR:", type(error).__name__ + ": " + str(error))
        sys.exit(2)
