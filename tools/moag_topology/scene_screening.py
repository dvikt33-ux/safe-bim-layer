#!/usr/bin/env python3
"""Fail-closed validation for one-pass MOAG page/scene screening records."""
from __future__ import annotations
import json
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parents[2] / "docs/research/apa-results/moag/v2"
CLASSES = {"STATION", "EXTERNAL", "MIXED", "REMOTE_EVIDENCE", "UNCERTAIN"}

def load(path):
    return json.loads(path.read_text(encoding="utf-8"))

def check(root=BASE):
    screen = load(root / "chapter_screening.json")
    if screen.get("schema") != "APA-MOAG-SCENE-SCREENING/1":
        raise ValueError("scene-screening schema mismatch")
    pages = {}
    for book in ("B1", "B2", "B3", "B4"):
        data = load(root / "pages" / f"{book}.json")
        pages.update({row["id"]: row for row in data["pages"]})
    scope = screen["scope"]
    if scope.get("total_pages") != len(pages) or len(pages) != 412:
        raise ValueError("screening corpus total does not match page ledgers")
    screened = scope.get("screened_page_ids", [])
    if len(screened) != len(set(screened)) or not set(screened) <= set(pages):
        raise ValueError("duplicate or unknown screened page")
    for page_id in screened:
        if pages[page_id]["status"] not in {"REVIEWED_FULL_PAGE", "PARTIAL_READ", "INACCESSIBLE"}:
            raise ValueError("screened page has no completed source check: " + page_id)
    for key in ("external_screened_page_ids", "remote_evidence_page_ids", "uncertain_page_ids"):
        vals = scope.get(key, [])
        if len(vals) != len(set(vals)) or not set(vals) <= set(screened):
            raise ValueError("invalid page classification list: " + key)
    chapter_ids, scene_ids = set(), set()
    for chapter in screen.get("chapters", []):
        cid = chapter["id"]
        if cid in chapter_ids:
            raise ValueError("duplicate chapter " + cid)
        chapter_ids.add(cid)
        if chapter.get("chapter_classification") not in CLASSES:
            raise ValueError("unknown chapter classification " + cid)
        span = chapter["page_span"]
        if span["start"] < 1 or span["end"] < span["start"]:
            raise ValueError("invalid chapter page span " + cid)
        chapter_pages = chapter.get("screened_pages", [])
        if not chapter_pages or not set(chapter_pages) <= set(screened):
            raise ValueError("chapter references unscreened pages " + cid)
        for scene in chapter.get("scenes", []):
            sid = scene["id"]
            if sid in scene_ids:
                raise ValueError("duplicate scene " + sid)
            scene_ids.add(sid)
            if scene.get("classification") not in CLASSES:
                raise ValueError("unknown scene classification " + sid)
            refs = [x["page_id"] for x in scene.get("page_fragments", [])]
            if not refs or not set(refs) <= set(chapter_pages):
                raise ValueError("scene fragment page missing from chapter screen " + sid)
            for ref in refs:
                if pages[ref]["status"] != "REVIEWED_FULL_PAGE":
                    raise ValueError("scene source page is not fully reviewed " + ref)
            if scene["classification"] == "EXTERNAL" and not scene.get("screened_out_material"):
                raise ValueError("external scene lacks reproducible exclusion basis " + sid)
            if scene["classification"] == "REMOTE_EVIDENCE" and not scene.get("station_relevance"):
                raise ValueError("remote evidence lacks station relevance " + sid)
    events = screen.get("character_location_events", [])
    for event in events:
        if not all(event.get(key) for key in ("character_id", "story_time", "current_location", "departure_event", "arrival_event", "source", "confidence")):
            raise ValueError("incomplete character-location event " + str(event.get("character_id", "<unknown>")))
        if not set(event["source"]) <= set(pages):
            raise ValueError("character event references unknown page " + str(event["character_id"]))
    if not chapter_ids or not scene_ids:
        raise ValueError("no chapter or scene screening records")
    return {
        "schema": "APA-MOAG-SCENE-SCREENING-VALIDATION/1",
        "screened_pages_in_package": len(screened),
        "chapters": len(chapter_ids),
        "scenes": len(scene_ids),
        "character_location_events": len(events),
        "full_page_audits_are_separate": True,
        "native_write_authorized": False,
    }

if __name__ == "__main__":
    try:
        print(json.dumps(check(), ensure_ascii=False, indent=2))
    except (KeyError, TypeError, ValueError, OSError) as exc:
        print("MOAG_SCENE_SCREENING_FAIL: " + str(exc), file=sys.stderr)
        sys.exit(2)
