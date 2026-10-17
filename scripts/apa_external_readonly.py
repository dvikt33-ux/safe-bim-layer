"""APA AC29 external read-only tools; isolated process, never a PLN writer.

IfcClash/IfcDiff/IfcTester run upstream CLIs. IFC quantities reuse the
existing archicad_connected_ifc implementation, never a new quantity engine.
PDF and DXF extract source primitives only; no inferred BIM dimensions.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(r"C:\LocalAI\APA_AC29_Stable")
VERSIONS = {
    "ifcopenshell": "0.8.5",
    "ifcclash": "0.8.5",
    "ifcdiff": "0.8.5",
    "ifctester": "0.8.5",
    "ifc5d": "0.8.5",
    "pdfplumber": "0.11.10",
    "ezdxf": "1.4.5",
    "networkx": "3.6.1",
    "shapely": "2.2.0",
    "odfpy": "1.4.1",
}
EXT = {"ifc": ".ifc", "ids": ".ids", "pdf": ".pdf", "dxf": ".dxf"}


def require(test, message):
    if not test:
        raise ValueError(message)


def source(value, kind):
    p = Path(value).resolve(strict=True)
    require(p.is_file() and p.suffix.lower() == EXT[kind],
            "SOURCE_TYPE_MISMATCH:" + kind)
    require(p.stat().st_size <= 4 * 1024 ** 3, "SOURCE_OVER_4GB_REFUSED")
    return p


def sha256(p):
    d = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            d.update(chunk)
    return d.hexdigest()


def check_environment():
    found = {}
    for name, wanted in VERSIONS.items():
        try:
            actual = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            actual = None
        found[name] = {"required": wanted, "installed": actual,
                       "match": actual == wanted}
    good = (sys.version_info[:2] == (3, 12)
            and platform.system() == "Windows"
            and all(v["match"] for v in found.values()))
    return {"schema": "APA_EXTERNAL_READONLY_DOCTOR_V1",
            "status": "READY" if good else "BLOCKED",
            "python": sys.version.split()[0], "platform": platform.platform(),
            "packages": found, "nativeCommands": 0, "plnWrites": 0}


def invoke_module(module, arguments, output):
    """Use a fixed Python module and argument vector, never shell or custom code."""
    require(module in {"ifcclash", "ifcdiff", "ifctester"},
            "UNREGISTERED_ANALYSIS_MODULE")
    with tempfile.TemporaryDirectory(prefix="apa-readonly-") as t:
        destination = Path(t) / "vendor-result.json"
        cmd = [sys.executable, "-m", module, *[str(x) for x in arguments],
               "-o", str(destination)]
        try:
            completed = subprocess.run(cmd, check=True, timeout=1200,
                                       capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            raise ValueError("UPSTREAM_ANALYSIS_FAILED:" + module
                             + ":returncode=" + str(e.returncode)
                             + ":stderr=" + (e.stderr or "")[-1200:]) from e
        require(destination.is_file() and destination.stat().st_size < 200 * 1024 ** 2,
                "UPSTREAM_JSON_MISSING_OR_OVERSIZED")
        result = json.loads(destination.read_text(encoding="utf-8-sig"))
        return {"vendorOutput": result, "vendor": module,
                "stdoutTail": completed.stdout[-1200:]}


def ifc_diff(args):
    a, b = source(args.a, "ifc"), source(args.b, "ifc")
    # -r selects semantic relationship types instead of geometry alone.
    return invoke_module("ifcdiff",
                         [a, b, "-r", "type property container aggregate classification"],
                         args.output), [a, b]


def ifc_clash(args):
    a = source(args.a, "ifc")
    b = source(args.b, "ifc") if args.b else None
    with tempfile.TemporaryDirectory(prefix="apa-clash-spec-") as t:
        config = Path(t) / "clashsets.json"
        spec = [{"name": "APA_SOURCE_QUALIFIED_CLASH_SET",
                 "a": [{"file": str(a)}]}]
        if b:
            spec[0]["b"] = [{"file": str(b)}]
        config.write_text(json.dumps(spec), encoding="utf-8")
        return invoke_module("ifcclash", [config], args.output), [a] + ([b] if b else [])


def ids_validate(args):
    ids = source(args.ids, "ids")
    model = source(args.a, "ifc")
    return invoke_module("ifctester", [ids, model, "-r", "Json"], args.output), [ids, model]


def ifc_qto(args):
    """Delegate to existing production IFC reader. No separate formula engine."""
    model = source(args.a, "ifc")
    module = ROOT / "scripts" / "archicad_connected_ifc.py"
    require(module.is_file(), "EXISTING_APA_IFC_READER_NOT_INSTALLED")
    sys.path.insert(0, str(module.parent))
    from archicad_connected_ifc import inspect_quantified_exchange
    result = inspect_quantified_exchange(model)
    return {"existingApaFunction": "archicad_connected_ifc.inspect_quantified_exchange",
            "result": result}, [model]


def pdf_vectors(args):
    import pdfplumber
    doc = source(args.a, "pdf")
    rows = []
    with pdfplumber.open(str(doc)) as pdf:
        require(len(pdf.pages) <= 500, "PDF_OVER_500_PAGES_REQUIRES_BATCHING")
        for i, page in enumerate(pdf.pages, start=1):
            lines = [{"x0": l.get("x0"), "x1": l.get("x1"),
                      "top": l.get("top"), "bottom": l.get("bottom")}
                     for l in page.lines[:20000]]
            rects = [{"x0": x.get("x0"), "x1": x.get("x1"),
                      "top": x.get("top"), "bottom": x.get("bottom")}
                     for x in page.rects[:20000]]
            rows.append({"page": i, "widthPt": page.width,
                         "heightPt": page.height,
                         "sourceCoordSystem": "PDF_TOP_LEFT_POINTS",
                         "lines": lines, "rectangles": rects,
                         "lineCount": len(page.lines),
                         "rectangleCount": len(page.rects),
                         "curveCountNotExtracted": len(page.curves),
                         "truncated": len(page.lines) > len(lines)
                                      or len(page.rects) > len(rects),
                         "textPreview": (page.extract_text() or "")[:12000]})
    return {"sourceType": "VECTOR_PDF_FACTS_NOT_BIM",
            "pages": rows, "scaleConfirmed": False,
            "coordinateCalibration": "NOT_VERIFIED"}, [doc]


def dxf_vectors(args):
    import ezdxf
    src = source(args.a, "dxf")
    drawing = ezdxf.readfile(str(src))
    rows, count = [], 0
    msp = drawing.modelspace()
    for ent in msp:
        count += 1
        if len(rows) >= 25000:
            continue
        typ = ent.dxftype()
        if typ == "LINE":
            data = {"type": typ, "start": list(ent.dxf.start),
                    "end": list(ent.dxf.end)}
        elif typ == "LWPOLYLINE":
            data = {"type": typ, "pointsXY": [list(xy) for xy in ent.get_points("xy")],
                    "closed": bool(ent.closed),
                    "ocsElevation": float(ent.dxf.get("elevation", 0))}
        elif typ in ("CIRCLE", "ARC"):
            data = {"type": typ, "center": list(ent.dxf.center),
                    "radius": float(ent.dxf.radius)}
            if typ == "ARC":
                data.update(startAngle=float(ent.dxf.start_angle),
                            endAngle=float(ent.dxf.end_angle))
        else:
            continue
        data["layer"] = ent.dxf.layer
        rows.append(data)
    return {"sourceType": "DXF_RAW_MODELSPACE_FACTS_NOT_BIM",
            "insunitsCode": drawing.header.get("$INSUNITS", 0),
            "unitConversionApplied": False, "coordinateCalibration": "NOT_VERIFIED",
            "entitiesVisited": count, "primitiveCount": len(rows),
            "truncated": len(rows) >= 25000, "primitives": rows}, [src]


OPERATIONS = {
    "ifc-diff": ifc_diff,
    "ifc-clash": ifc_clash,
    "ids-validate": ids_validate,
    "ifc-qto": ifc_qto,
    "pdf-vectors": pdf_vectors,
    "dxf-vectors": dxf_vectors,
}


def main(argv=None):
    parser = argparse.ArgumentParser(description="APA AC29 isolated read-only evidence adapter")
    parser.add_argument("action", choices=["doctor", *OPERATIONS])
    parser.add_argument("--a", help="IFC / PDF / DXF source")
    parser.add_argument("--b", help="second IFC source for compare or clash")
    parser.add_argument("--ids", help="IDS specification for ids-validate")
    parser.add_argument("--output", help="new local JSON evidence file; overwrite forbidden")
    args = parser.parse_args(argv)
    if args.action == "doctor":
        status = check_environment()
        print(json.dumps(status, indent=2, ensure_ascii=False))
        return 0 if status["status"] == "READY" else 2
    require(args.output, "EXPLICIT_NEW_OUTPUT_PATH_REQUIRED")
    status = check_environment()
    require(status["status"] == "READY", "ISOLATED_DEPENDENCIES_NOT_READY")
    report, sources = OPERATIONS[args.action](args)
    out = Path(args.output).resolve()
    require(out.suffix.lower() == ".json" and out.parent.is_dir(),
            "OUTPUT_EXISTING_DIRECTORY_AND_JSON_REQUIRED")
    require(not out.exists() and all(out != src for src in sources),
            "OUTPUT_ALREADY_EXISTS_OR_COLLIDES_WITH_SOURCE")
    document = {"schema": "APA_EXTERNAL_READONLY_EVIDENCE_V1",
                "status": "SOURCE_ANALYSIS_ONLY_NOT_ENGINEERING_ACCEPTANCE",
                "action": args.action, "sources": [
                    {"name": p.name, "sha256": sha256(p)} for p in sources],
                "result": report, "modelWrites": 0, "nativeCalls": 0,
                "existingAPAUnchanged": True}
    with out.open("x", encoding="utf-8") as f:
        json.dump(document, f, indent=2, ensure_ascii=False, allow_nan=False,
                  default=str)
        f.write("\n")
    print("APA_STATUS: READ_ONLY_REPORT_CREATED")
    print("EVIDENCE:", out)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print("APA_STATUS: READ_ONLY_BLOCKED")
        print("ERROR:", type(exc).__name__ + ": " + str(exc))
        sys.exit(2)
