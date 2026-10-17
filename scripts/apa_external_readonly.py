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
    good = (sys.version_info[:2] in {(3, 11), (3, 12)}
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
                 "mode": "intersection", "tolerance": 0.001,
                 "check_all": False, "a": [{"file": str(a)}]}]
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


def _pdf_path_ops(path, height):
    """Preserve PDF path commands, with TOP-LEFT point coordinates throughout.

    pdfplumber paths use PDF BOTTOM-LEFT y; line/curve .pts use TOP-LEFT y.
    A cubic 'c' keeps all three control/endpoints exactly. Never tessellate.
    """
    rows = []
    for instruction in path:
        op, *raw_points = instruction
        require(op in {"m", "l", "c", "h"}, "UNSUPPORTED_PDF_VECTOR_PATH_OPERATION:" + op)
        require((op == "h" and not raw_points)
                or (op in {"m", "l"} and len(raw_points) == 1)
                or (op == "c" and len(raw_points) == 3),
                "MALFORMED_PDF_VECTOR_PATH")
        rows.append({"op": op, "pointsPt": [
            [float(pt[0]), float(height - pt[1])] for pt in raw_points
        ]})
    return rows


def _pdf_style(obj):
    return {key: obj.get(key) for key in (
        "linewidth", "stroke", "fill", "evenodd",
        "stroking_color", "non_stroking_color", "dash"
    )}


def _pdf_rect(obj):
    return {
        "x0": obj["x0"], "x1": obj["x1"],
        "top": obj["top"], "bottom": obj["bottom"],
        "cornersPt": [list(p) for p in obj.get("pts", ())],
        "style": _pdf_style(obj),
    }


def _pdf_line(obj, height):
    pts = obj.get("pts", ())
    require(len(pts) == 2, "PDF_LINE_NOT_EXACT_TWO_ENDPOINTS")
    return {
        "x0": obj["x0"], "x1": obj["x1"],
        "top": obj["top"], "bottom": obj["bottom"],
        "startPt": list(pts[0]), "endPt": list(pts[1]),
        "path": _pdf_path_ops(obj.get("path", ()), height),
        "style": _pdf_style(obj),
    }


def _pdf_curve(obj, height):
    return {
        "x0": obj["x0"], "x1": obj["x1"],
        "top": obj["top"], "bottom": obj["bottom"],
        "pointsPt": [list(p) for p in obj.get("pts", ())],
        "path": _pdf_path_ops(obj.get("path", ()), height),
        "style": _pdf_style(obj),
    }


def _pdf_recover_cyrillic(raw):
    """Repair the tested ARCHICAD Latin-1 displayed Windows-1251 text.

    Only apply whole-page reversible byte mapping if it produces substantial
    Cyrillic, and raw input had no genuine Cyrillic. Always retain raw text.
    Other encodings remain untouched; never use replacement characters.
    """
    if not raw:
        return raw, "EMPTY"
    if any("\u0400" <= c <= "\u052f" for c in raw):
        return raw, "ALREADY_UNICODE"
    try:
        recovered = raw.encode("latin-1").decode("cp1251")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return raw, "UNSUPPORTED_OR_MIXED_ENCODING_RAW_PRESERVED"
    cyrillic_count = sum("\u0400" <= c <= "\u052f" for c in recovered)
    if cyrillic_count >= 3 and cyrillic_count >= len(raw) * 0.06:
        return recovered, "LATIN1_CP1251_REVERSIBLE_RECOVERY"
    return raw, "RAW_PRESERVED_NO_CYRILLIC_EVIDENCE"


def pdf_vectors(args):
    """Complete vector primitive extraction, WITHOUT per-page truncation.

    Paths, cubic Bezier control points and line endpoints are PDF points in a
    single top-left coordinate frame. This is *not* BIM/world calibration.
    The report can be large: callers must choose a destination with disk space.
    """
    import pdfplumber
    doc = source(args.a, "pdf")
    rows = []
    totals = {"lines": 0, "rectangles": 0, "curves": 0, "textCharacters": 0}
    with pdfplumber.open(str(doc)) as pdf:
        require(len(pdf.pages) <= 500, "PDF_OVER_500_PAGES_REQUIRES_BATCHING")
        for i, page in enumerate(pdf.pages, start=1):
            lines = [_pdf_line(item, page.height) for item in page.lines]
            rects = [_pdf_rect(item) for item in page.rects]
            curves = [_pdf_curve(item, page.height) for item in page.curves]
            raw_text = page.extract_text() or ""
            text, encoding = _pdf_recover_cyrillic(raw_text)
            require(len(lines) == len(page.lines) and
                    len(rects) == len(page.rects) and
                    len(curves) == len(page.curves),
                    "PDF_VECTOR_PRIMITIVE_COVERAGE_MISMATCH")
            totals["lines"] += len(lines)
            totals["rectangles"] += len(rects)
            totals["curves"] += len(curves)
            totals["textCharacters"] += len(text)
            rows.append({
                "page": i, "widthPt": page.width, "heightPt": page.height,
                "sourceCoordSystem": "PDF_TOP_LEFT_POINTS",
                "lines": lines, "rectangles": rects, "curves": curves,
                "lineCount": len(lines), "rectangleCount": len(rects),
                "curveCount": len(curves),
                "curveCountNotExtracted": 0,
                "truncated": False,
                "text": text, "textRaw": raw_text,
                "textEncodingStatus": encoding,
                "textPreview": text[:12000],
                "embeddedImageCount": len(page.images),
            })
    return {
        "sourceType": "VECTOR_PDF_FACTS_NOT_BIM",
        "pages": rows, "totals": totals,
        "truncated": False,
        "vectorGeometryComplete": True,
        "curveCoordinates": "CUBIC_BEZIER_CONTROL_POINTS_NOT_TESSELLATED",
        "textRecovery": "PRESERVES_ORIGINAL_AND_RECOVERED_TEXT",
        "scaleConfirmed": False,
        "coordinateCalibration": "NOT_VERIFIED",
    }, [doc]


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
