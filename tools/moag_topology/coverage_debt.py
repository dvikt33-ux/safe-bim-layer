#!/usr/bin/env python3
"""APA-MOAG read-only evidence coverage debt report.

A reviewed page with spatial hints but zero indexed observations is NOT a
completed page-to-evidence audit. This tool never changes any source file,
geometric model, Archicad project, or review status.
"""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "docs/research/apa-results/moag/v2"
BOOKS = ("B1", "B2", "B3", "B4")
READ = "REVIEWED_FULL_PAGE"


def evaluate(pages, observations):
    """Pure integrity/coverage analysis; suitable for synthetic tests."""
    page_by_id = {}
    status_counts = Counter()
    for page in pages:
        pid = page["id"]
        if pid in page_by_id:
            raise ValueError("duplicate page id: " + pid)
        page_by_id[pid] = page
        status_counts[page["status"]] += 1

    obs_count = Counter()
    obs_ids = set()
    for ob in observations:
        oid = ob["id"]
        pid = ob["page_id"]
        if oid in obs_ids:
            raise ValueError("duplicate observation id: " + oid)
        obs_ids.add(oid)
        if pid not in page_by_id:
            raise ValueError("orphan evidence on missing page: " + pid)
        if page_by_id[pid]["status"] != READ:
            raise ValueError("evidence attached to unread page: " + pid)
        obs_count[pid] += 1

    missing = []
    zero_hint_pages = []
    for pid, page in page_by_id.items():
        if page["status"] != READ:
            continue
        hints = page.get("recorded_spatial_hints")
        if not isinstance(hints, int) or hints < 0:
            raise ValueError("reviewed page lacks valid hint count: " + pid)
        if hints > 0 and obs_count[pid] == 0:
            missing.append(pid)
        if hints == 0 and obs_count[pid] == 0:
            zero_hint_pages.append(pid)

    missing.sort()
    zero_hint_pages.sort()
    all_pages_read = status_counts[READ] == len(page_by_id)
    return {
        "schema": "APA-MOAG-COVERAGE-DEBT/1",
        "indexed_pages": len(page_by_id),
        "reviewed_pages": status_counts[READ],
        "unreviewed_pages": len(page_by_id) - status_counts[READ],
        "observations": len(obs_ids),
        "read_pages_with_positive_hints_but_no_observations": missing,
        "valid_zero_hint_read_pages_without_observations": zero_hint_pages,
        "page_to_evidence_gap_free": not missing,
        "all_pages_read": all_pages_read,
        "textual_corpus_complete": all_pages_read and not missing,
        "metric_geometry_approved": False,
        "archicad_native_write_authorized": False,
    }


def check(root=ROOT):
    pages = []
    for book in BOOKS:
        pages.extend(json.loads((root / "pages" / (book + ".json")).read_text(encoding="utf-8"))["pages"])
    observations = json.loads((root / "page_observations.json").read_text(encoding="utf-8"))["observations"]
    return evaluate(pages, observations)


if __name__ == "__main__":
    try:
        print(json.dumps(check(), ensure_ascii=False, indent=2))
    except (ValueError, KeyError, OSError) as error:
        raise SystemExit("APA_MOAG_COVERAGE_DEBT_FAIL: " + str(error))
