"""Run all SIX installed read-only external commands via original APA Router.

Real IFC4/IDS/DXF test fixtures are generated with pinned upstream vendors.
PDF uses --real-pdf for the original 24-page ARCHICAD BDD PDF, or a simple
vendor PDF in smoke mode. No Archicad connection, no PLN modification.
One fixed output directory with six distinct JSON files; no overwrites.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import time

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "scripts"))

import ezdxf
from ifctester import ids
from apa_external_ifc_vendor_smoke import create_ifc
from apa_external_router_activation import make_pdf
import apa_external_analytics_entrypoint as ROUTE

BDD_SHA256 = "75b3064dec93245a986e5060540651acfa5d6a87fd1a137d5b46eb591a7462e1"


def require(value, reason):
    if not value:
        raise RuntimeError(reason)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_ids(path):
    document = ids.Ids(title="APA IFC4 wall names")
    spec = ids.Specification(name="IFC4 wall naming", ifcVersion=["IFC4"])
    spec.applicability.append(ids.Entity(name="IFCWALL"))
    spec.requirements.append(ids.Attribute(name="Name"))
    document.specifications.append(spec)
    document.to_xml(str(path))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--real-pdf", type=Path,
                   help="original 24-page BDD PDF. SHA-256 checked if specified")
    p.add_argument("--output-dir", type=Path, required=True,
                   help="NEW results directory OUTSIDE stable APA")
    args = p.parse_args()
    directory = args.output_dir.resolve()
    require(not directory.exists(), "SIX_TOOL_REPORT_DIRECTORY_ALREADY_EXISTS")
    require(ROUTE.ROOT.resolve() not in directory.parents
            and directory != ROUTE.ROOT.resolve(),
            "OUTPUT_INSIDE_STABLE_APA_FORBIDDEN")
    directory.mkdir(parents=True, exist_ok=False)
    fixtures = directory / "generated-inputs"
    fixtures.mkdir()
    left, right = fixtures / "architecture.ifc", fixtures / "services.ifc"
    left_guid = create_ifc(left, "Wall A")
    right_guid = create_ifc(right, "Wall B")
    require(left_guid != right_guid, "IFC_FIXTURE_GUID_COLLISION")
    idspath = fixtures / "wall-name.ids"
    make_ids(idspath)

    dxf = fixtures / "plan.dxf"
    drawing = ezdxf.new("R2013")
    drawing.header["$INSUNITS"] = 4
    model = drawing.modelspace()
    model.add_line((0., 0.), (3., 4.))
    model.add_lwpolyline([(0, 0), (3, 0), (3, 2)], close=True)
    model.add_circle((5, 5), 2)
    model.add_arc((8, 8), radius=1, start_angle=0, end_angle=90)
    drawing.saveas(dxf)

    if args.real_pdf:
        pdf = args.real_pdf.resolve(strict=True)
        require(pdf.is_file() and pdf.suffix.lower() == ".pdf"
                and sha(pdf) == BDD_SHA256,
                "USER_PDF_NOT_THE_VERIFIED_BDD_24_PAGE_BYTES")
        pdf_mode = "REAL_ARCHICAD_24_PAGE_BDD"
    else:
        pdf = fixtures / "vector.pdf"
        make_pdf(pdf)
        pdf_mode = "SYNTHETIC_VECTOR_SMOKE_NOT_BDD"

    tasks = [
        ("PDFVectors", pdf, None, None),
        ("DXFVectors", dxf, None, None),
        ("IFCDiff", left, right, None),
        ("IFCClash", left, right, None),
        ("IDSValidate", left, None, idspath),
        ("IFCQuantities", left, None, None),
    ]
    outcomes = []
    for command, a, b, spec in tasks:
        out = directory / (command + ".json")
        t0 = time.perf_counter()
        routed = ROUTE.route_once(command, str(a), str(out),
                                  str(b) if b else None,
                                  str(spec) if spec else None)
        require(routed["status"] == "APA_EXTERNAL_ROUTED_READ_ONLY_PASS"
                and routed["plnWrites"] == 0
                and routed["nativeCalls"] == 0
                and out.is_file(),
                "UNEXPECTED_ROUTER_RESULT:" + command)
        report = json.loads(out.read_text(encoding="utf-8"))
        require(report["action"] in {
            "pdf-vectors", "dxf-vectors", "ifc-diff",
            "ifc-clash", "ids-validate", "ifc-qto"
        } and report["modelWrites"] == report["nativeCalls"] == 0,
                "WRONG_EXTERNAL_EVIDENCE_ENVELOPE:" + command)
        facts = report["result"]
        if command == "PDFVectors":
            totals = facts["totals"]
            require(facts["truncated"] is False
                    and facts["vectorGeometryComplete"] is True,
                    "PDF_VECTOR_INCOMPLETE")
            if pdf_mode == "REAL_ARCHICAD_24_PAGE_BDD":
                require(len(facts["pages"]) == 24
                        and totals["lines"] == 80414
                        and totals["curves"] == 25436
                        and totals["rectangles"] == 1668
                        and len(facts["pages"][18]["lines"]) == 36584
                        and len(facts["pages"][18]["curves"]) == 17243
                        and "Схема стропильной системы"
                            in facts["pages"][18]["text"],
                        "REAL_BDD_DOCUMENT_FULL_EXTRACTION_MISMATCH")
            else:
                require(totals["lines"] >= 1, "SYNTHETIC_PDF_LINE_MISSING")
        elif command == "DXFVectors":
            require(facts["primitiveCount"] == 4
                    and not facts["truncated"], "DXF_FOUR_PRIMITIVES_NOT_FOUND")
        elif command == "IFCDiff":
            require(facts["vendor"] == "ifcdiff"
                    and isinstance(facts["vendorOutput"], (dict, list)),
                    "IFCDIFF_VENDOR_RESULT_MISSING")
        elif command == "IFCClash":
            require(facts["vendor"] == "ifcclash"
                    and isinstance(facts["vendorOutput"], (dict, list)),
                    "IFCCLASH_VENDOR_RESULT_MISSING")
        elif command == "IDSValidate":
            require(facts["vendor"] == "ifctester"
                    and isinstance(facts["vendorOutput"], dict),
                    "IDSTESTER_VENDOR_RESULT_MISSING")
        elif command == "IFCQuantities":
            require(facts["existingApaFunction"]
                    == "archicad_connected_ifc.inspect_quantified_exchange"
                    and len(facts["result"]["elements"]) == 1,
                    "EXISTING_IFC_QTO_NOT_USED")
        duration = round(time.perf_counter() - t0, 3)
        row = {"command": command, "status": "ROUTED_REAL_VENDOR_PASS",
               "elapsedSeconds": duration,
               "evidenceSHA256": sha(out),
               "reportBytes": out.stat().st_size,
               "sources": report["sources"]}
        outcomes.append(row)
        print("PASS %-14s %.3f s" % (command, duration), flush=True)

    overall = {
        "status": "SIX_EXTERNAL_READ_ONLY_ROUTER_TESTS_PASS",
        "pdfMode": pdf_mode, "runs": outcomes,
        "passed": len(outcomes), "expected": 6,
        "modelWrites": 0, "nativeCalls": 0,
        "outputDirectory": str(directory),
        "archicadConnected": False,
    }
    summary = directory / "SUMMARY.json"
    with summary.open("x", encoding="utf-8") as file:
        json.dump(overall, file, ensure_ascii=False, indent=2)
    print(json.dumps(overall, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("APA_SIX_TOOLS_BLOCKED: " + type(exc).__name__
              + ": " + str(exc), file=sys.stderr, flush=True)
        raise SystemExit(2)
