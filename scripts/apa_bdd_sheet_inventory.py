"""Read-only PDF sheet-title index. Avoid roof/structural sheets in floorplan AI tests.

Uses already installed PyMuPDF. NO automatic page selection or model execution.
Optional exact source SHA protects the accepted 24-page BDD.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

BDD_HASH = "75b3064dec93245a986e5060540651acfa5d6a87fd1a137d5b46eb591a7462e1"
FLOOR = re.compile(
    r"(?:план[а-яё\s]{0,28}(?:1|2|3|4|перв|втор|треть|этаж|этажа|уровн))|"
    r"(?:(?:1|2|3|4)[-\s]*(?:й|го)?[-\s]*этаж[а-яё\s]{0,15}план)",
    re.IGNORECASE)
ROOF = re.compile(
    r"стропил|кровл|фасад|разрез|перекрыт|фундамент|армирован|узел|спецификац",
    re.IGNORECASE)


def sha(path):
    out = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            out.update(block)
    return out.hexdigest()


def decoded(text):
    if sum('\u0400' <= char <= '\u052f' for char in text) >= 4:
        return text
    try:
        recovered = text.encode("latin1").decode("cp1251")
    except (UnicodeError, ValueError):
        return text
    if sum('\u0400' <= char <= '\u052f' for char in recovered) >= 4:
        return recovered
    return text


def inspect(pdf, expected_sha=None):
    import pymupdf
    if expected_sha and sha(pdf) != expected_sha:
        raise ValueError("PDF_SOURCE_SHA_MISMATCH")
    with pymupdf.open(str(pdf)) as doc:
        rows = []
        for index in range(len(doc)):
            page = doc[index]
            text = decoded(page.get_text("text", sort=True))
            fragments = [s.strip() for s in text.splitlines() if s.strip()]
            floor_hits = [x for x in fragments if FLOOR.search(x)][:5]
            roof_hits = [x for x in fragments if ROOF.search(x)][:5]
            score = 3 * len(floor_hits) - 2 * len(roof_hits)
            rows.append({
                "page": index+1,
                "floorTitleCandidates": floor_hits,
                "otherStructuralKeywords": roof_hits,
                "floorplanCandidate": bool(floor_hits) and score > 0,
                "textPreview": fragments[:5],
            })
        return {"schema": "APA_PDF_SHEET_INDEX_V1",
                "sourceSha256": sha(pdf),
                "pages": len(doc),
                "floorCandidates": [r["page"] for r in rows
                                    if r["floorplanCandidate"]],
                "rows": rows,
                "automaticBIMInference": False,
                "sourceModified": False}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--pdf", type=Path, required=True)
    p.add_argument("--bdd-exact-sha", action="store_true")
    args = p.parse_args()
    pdf = args.pdf.resolve(strict=True)
    if not pdf.is_file() or pdf.suffix.lower() != ".pdf":
        raise ValueError("SOURCE_NOT_PDF")
    result = inspect(pdf, BDD_HASH if args.bdd_exact_sha else None)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("APA_SHEET_INDEX_BLOCKED:" + type(exc).__name__ + ":"
              + str(exc), file=sys.stderr)
        sys.exit(2)
