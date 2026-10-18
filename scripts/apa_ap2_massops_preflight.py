"""APA AC29: source-qualified repeat *candidates* from one PDF floorplan.

No geometric reconstruction, no BIM element creation, no PLN access.
Consumes the architectural PDF plus the real APA PDF crop/OpenBIM receipts.
Repeated opening marks are NOT automatically geometry-equivalent prototypes:
host wall, type, story, dimensions, flip/orientation must be independently read.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import sys

SCHEMA = "APA_AP2_MASSOPS_PREFLIGHT_V1"
OPENING_RE = re.compile(r"^(?:ОК|OK|Дн|Дш|Д|D)-[1-9][0-9]*$", re.I)
AP2_SHA = "2cf28450e868a5c742511fe40e6d0f061c9210744cb4f43875e0d7839725c55b"
AP2_CLIP = (125., 95., 685., 595.)
AP2_PAGE = 16


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    sha = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            sha.update(chunk)
    return sha.hexdigest()


def readable(text):
    """Recover common cp1251-to-Latin1 PDF text without OCR."""
    if any("А" <= x <= "я" for x in text):
        return text
    try:
        decoded = text.encode("latin1").decode("cp1251")
    except UnicodeError:
        return text
    return decoded if any("А" <= x <= "я" for x in decoded) else text


def normalize_mark(word):
    word = readable(word).strip().replace("–", "-").replace("—", "-")
    if not OPENING_RE.fullmatch(word):
        return None
    prefix, suffix = word.split("-", 1)
    prefix = prefix.upper().replace("OK", "ОК").replace("D", "Д")
    return f"{prefix}-{suffix}"


def family(mark):
    if mark.startswith("ОК-"):
        return "WINDOW_MARK"
    return "DOOR_MARK"


def marks_on_sheet(source, page_number, clip):
    import pymupdf
    rows = []
    with pymupdf.open(str(source)) as doc:
        require(1 <= page_number <= len(doc), "PAGE_NOT_FOUND")
        pg = doc[page_number - 1]
        require(pg.rect.contains(pymupdf.Rect(*clip)), "CLIP_OUTSIDE_PAGE")
        # Words have actual PDF point coordinates, not pixels.
        for item in pg.get_text("words", sort=False):
            x0, y0, x1, y1, word = item[:5]
            mark = normalize_mark(word)
            if mark is None:
                continue
            # Exclude specification legends, examples and title blocks.
            if not (clip[0] <= x0 <= x1 <= clip[2]
                    and clip[1] <= y0 <= y1 <= clip[3]):
                continue
            rows.append({
                "mark": mark, "family": family(mark),
                "bboxPt": [round(float(n), 4) for n in (x0, y0, x1, y1)],
                "midpointPt": [round((x0 + x1) / 2, 4),
                               round((y0 + y1) / 2, 4)],
                "sourceKind": "PDF_TEXT_MARK_ONLY",
            })
    return sorted(rows, key=lambda r: (r["mark"], r["bboxPt"][1], r["bboxPt"][0]))


def inspect(pdf, crop_receipt, model_report=None, *, page=AP2_PAGE,
            clip=AP2_CLIP, expected_source_hash=AP2_SHA):
    pdf = Path(pdf).resolve(strict=True)
    require(pdf.is_file() and pdf.suffix.lower() == ".pdf",
            "ARCHITECTURAL_PDF_REQUIRED")
    require(digest(pdf) == expected_source_hash,
            "SOURCE_PDF_SHA_MISMATCH")
    crop_receipt = Path(crop_receipt).resolve(strict=True)
    evidence = json.loads(crop_receipt.read_text(encoding="utf-8"))
    require(evidence.get("schema") == "APA_PDF_LAYERED_FLOORPLAN_EVIDENCE_V1"
            and evidence.get("sourceSHA256") == expected_source_hash
            and evidence.get("pdfPage") == page
            and evidence.get("pdfPointsClip") == list(clip)
            and evidence.get("nativeCalls") == evidence.get("modelWrites") == 0,
            "ARCH_PDF_CROP_RECEIPT_MISMATCH")
    root = crop_receipt.parent
    png = root / "floorplan.png"
    require(png.is_file() and digest(png) == evidence["rasterSHA256"],
            "ARCH_PLAN_PNG_SHA_MISMATCH")

    semantic = {"status": "OPENBIM_NOT_RUN", "evidenceAccepted": False}
    if model_report is not None:
        report = json.loads(Path(model_report).resolve(strict=True)
                            .read_text(encoding="utf-8"))
        require(report.get("schema") == "APA_SEMANTIC_SOURCE_EVIDENCE_V1"
                and report.get("action") == "openbim"
                and report.get("nativeCalls") == report.get("modelWrites") == 0
                and report.get("sourceNotModified") is True
                and any(x.get("sha256") == evidence["rasterSHA256"]
                        for x in report.get("sources", [])),
                "OPENBIM_RESULT_IS_NOT_FOR_THIS_RASTER")
        masks = report["result"]
        require(all(k in masks.get("classPixelCounts", {})
                    for k in ("wall", "window", "door", "background")),
                "OPENBIM_CLASS_MASKS_NOT_COMPLETE")
        semantic = {
            "status": "OPENBIM_MASK_EVIDENCE_ACCEPTED_NOT_BIM",
            "evidenceAccepted": True,
            "maskSizePx": masks.get("imageSizePx"),
            "rasterSizePx": evidence["rasterPixelSize"],
            "classPixelCounts": masks["classPixelCounts"],
            "maskAndRasterPixelsComparable":
                masks.get("imageSizePx") == evidence["rasterPixelSize"],
            "requiresGeometryRegistration": True,
        }

    placements = marks_on_sheet(pdf, page, clip)
    by_mark = defaultdict(list)
    for row in placements:
        by_mark[row["mark"]].append(row)
    batches = []
    for mark, items in sorted(by_mark.items()):
        n = len(items)
        batches.append({
            "mark": mark,
            "family": family(mark),
            "placements": n,
            "documentedType": "MARK_ONLY_NOT_VALIDATED_LIBPART",
            "candidateStrategy": ("DUPLICATE_OR_BATCH_CREATE_IF_QUALIFIED"
                                  if n > 1 else
                                  "SINGLE_CREATE_IF_QUALIFIED"),
            "positionsPt": [r["midpointPt"] for r in items],
            "sourceBoundsPt": [r["bboxPt"] for r in items],
            "nativeOperationChosen": None,
            "referenceGUID": None,
            "wallHostGUID": None,
            "dimensionsVerified": False,
            "rotationAndFlipVerified": False,
            "storyVerified": False,
            "requiresHumanReview": True,
        })
    count = Counter(p["family"] for p in placements)
    return {
        "schema": SCHEMA,
        "status": "READ_ONLY_CANDIDATE_PREVIEW_NO_NATIVE_WRITE",
        "sourceName": pdf.name,
        "sourceSHA256": expected_source_hash,
        "pdfPage": page,
        "pdfPointsClip": list(clip),
        "pdfCoordinatesAreNotBuildingMetres": True,
        "inputCropSHA256": evidence["rasterSHA256"],
        "semantic": semantic,
        "markCounts": dict(sorted(Counter(p["mark"] for p in placements).items())),
        "countsByFamily": dict(sorted(count.items())),
        "markPlacementCount": len(placements),
        "repeatGroups": sum(1 for b in batches if b["placements"] > 1),
        "repeatPlacementCount": sum(b["placements"] for b in batches
                                    if b["placements"] > 1),
        "candidateBatches": batches,
        "plannerMode": "QUALIFY_EXISTING_APA_AUTO_DISCOVERY_AFTER_BIM_READBACK",
        "copiedGroupsConfirmed": 0,
        "modelWrites": 0, "nativeCalls": 0,
        "permissionForPLNWrite": False,
        "readyForModelWrite": False,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pdf", type=Path, required=True)
    p.add_argument("--crop-receipt", type=Path, required=True)
    p.add_argument("--openbim-report", type=Path)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    out = args.output.resolve()
    require(out.suffix.lower() == ".json" and out.parent.is_dir()
            and not out.exists(), "OUTPUT_MUST_BE_NEW_JSON")
    result = inspect(args.pdf, args.crop_receipt, args.openbim_report)
    with out.open("x", encoding="utf-8") as fd:
        json.dump(result, fd, indent=2, ensure_ascii=True)
        fd.write("\n")
    print("APA_AP2_MASSOPS_PREFLIGHT_PASS")
    print(json.dumps({k:result[k] for k in
                      ("status","markCounts","markPlacementCount",
                       "repeatGroups","repeatPlacementCount",
                       "copiedGroupsConfirmed","nativeCalls","modelWrites",
                       "readyForModelWrite")}, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("APA_AP2_MASSOPS_PREFLIGHT_BLOCKED:"
              + type(exc).__name__ + ":" + str(exc), file=sys.stderr)
        sys.exit(2)
