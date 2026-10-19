#!/usr/bin/env python3
"""MOAG primary-source page coverage and visual hypothesis validator.

Every page is listed, but a listed page is NOT evidence of having been read.
No use of network, image generation, Archicad or any native writer.
"""
from __future__ import annotations
from collections import Counter
import json
from pathlib import Path
import sys

BOOKS={"B1":(48197,114),"B2":(53370,148),"B3":(58610,71),"B4":(63971,79)}
STATUSES={"NOT_REVIEWED","REVIEWED_FULL_PAGE","INACCESSIBLE","PARTIAL_READ"}
EVIDENCE={"DIRECT_TEXT","CONTEXT_INFERENCE","MEMORY_NOT_SPATIAL","EXCLUSION_EVIDENCE","DREAM_NONFACT","MEDIATED_IMAGE_UNVERIFIED","CHARACTER_STATED_FALSEHOOD"}
STATIONS={"MOAG","MOAG_MEMORY_ONLY","THIRD_STATION_NOT_MOAG","OTHER_STATION_NOT_MOAG","MOAG_COVER_STORY_NOT_FACT","UNRESOLVED_OBJECT"}
VSTATUSES={"OPEN","INSUFFICIENT_EVIDENCE","TEXT_SUPPORTED_LOCAL_ONLY","REJECTED_AS_METRIC_EVIDENCE"}
ROOT=Path(__file__).resolve().parents[2]/"docs/research/apa-results/moag/v2"

def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))

def check(root=ROOT):
    graph=load(root.parent/"v1/evidence_graph.json")
    nodes={n["id"] for n in graph["nodes"]}
    ids=set(); counts=Counter(); pages={}
    for book,(site_id,total) in BOOKS.items():
        d=load(root/"pages"/f"{book}.json")
        if d["book_id"]!=book or d["expected_total"]!=total or len(d["pages"])!=total:
            raise ValueError("untrue page coverage manifest for "+book)
        for expected,p in enumerate(d["pages"],1):
            pid=f"{book}-{expected:03d}"
            if p["id"]!=pid or p["page_number"]!=expected or pid in ids:
                raise ValueError("missing/duplicate/reordered page "+pid)
            ids.add(pid);pages[pid]=p
            if p["url"]!=f"https://loveread.ec/read_book.php?id={site_id}&p={expected}":
                raise ValueError("wrong source URL "+pid)
            status=p.get("status")
            if status not in STATUSES:
                raise ValueError("unknown coverage status "+pid)
            if status=="REVIEWED_FULL_PAGE":
                if (not p.get("full_page_review_date") or not isinstance(p.get("recorded_spatial_hints"), int)
                        or isinstance(p.get("recorded_spatial_hints"), bool) or p["recorded_spatial_hints"] < 0
                        or not isinstance(p.get("notes"), str) or not p["notes"].strip()):
                    raise ValueError("false full reading status "+pid)
                if p.get("target_station")=="UNCLASSIFIED":
                    raise ValueError("unknown station scope in read page "+pid)
            elif p.get("full_page_review_date"):
                raise ValueError("nonreviewed page falsely dated "+pid)
            counts[status]+=1
    o=load(root/"page_observations.json");o_ids=set(); obs_per_page=Counter()
    if o["schema"]!="APA-MOAG-PAGE-OBSERVATIONS/1":
        raise ValueError("invalid observations schema")
    for row in o["observations"]:
        id=row["id"];pid=row["page_id"]
        if id in o_ids or pid not in pages:
            raise ValueError("duplicate observation or unknown page "+str(id))
        o_ids.add(id);obs_per_page[pid]+=1
        if pages[pid]["status"]!="REVIEWED_FULL_PAGE":
            raise ValueError("observation drawn from unaudited page "+pid)
        if row["citation_url"]!=pages[pid]["url"]:
            raise ValueError("observation broken page URL "+id)
        if row.get("evidence_class") not in EVIDENCE or row.get("station_id") not in STATIONS:
            raise ValueError("unknown evidence or station classification "+id)
        if not row.get("locator_hint") or not row.get("spatial_assertion"):
            raise ValueError("missing locator or interpretation "+id)
        if row.get("plan_coordinates") is not None or row.get("dimensions_m") is not None:
            raise ValueError("premature metric geometry in observation "+id)
        if not set(row.get("feature_refs",[]))<=nodes:
            raise ValueError("unknown graph node "+id)
        if row["evidence_class"]=="DREAM_NONFACT" and (row["feature_refs"] or row["visual_hypothesis_refs"]):
            raise ValueError("dream treated as physical evidence "+id)
        if row["evidence_class"]=="MEDIATED_IMAGE_UNVERIFIED" and row.get("visual_hypothesis_refs"):
            raise ValueError("hologram promoted to visual evidence "+id)
        if row["station_id"] in {"THIRD_STATION_NOT_MOAG","OTHER_STATION_NOT_MOAG"} and row["evidence_class"]!="EXCLUSION_EVIDENCE":
            raise ValueError("other station promoted to MOAG "+id)
        if row["station_id"]=="MOAG_COVER_STORY_NOT_FACT" and (row["evidence_class"]!="CHARACTER_STATED_FALSEHOOD" or row["feature_refs"] or row["visual_hypothesis_refs"]):
            raise ValueError("false character account treated as MOAG geometry "+id)
    v=load(root/"visual_hypotheses.json")
    for h in v["hypotheses"]:
        if h.get("adopt_as_geometry") is not False:
            raise ValueError("visual hypothesis inserted as geometry "+h["id"])
        if h.get("status") not in VSTATUSES:
            raise ValueError("illegal hypothesis state "+h["id"])
        if not set(h.get("checked_against_pages",[]))<=set(pages):
            raise ValueError("hypothesis references unknown page "+h["id"])
        if any(pages[x]["status"]!="REVIEWED_FULL_PAGE" for x in h["checked_against_pages"]):
            raise ValueError("visual hypothesis cited an unread page "+h["id"])
    return {"total_indexed_pages":len(pages),"coverage":dict(counts),
            "pages_with_observations":len(obs_per_page),"observations":len(o_ids),
            "visual_hypotheses":len(v["hypotheses"]),"geometry_authorized":False,
            "full_corpus_claim":counts["REVIEWED_FULL_PAGE"]==len(pages)}

if __name__=="__main__":
    try:
        print(json.dumps(check(),ensure_ascii=False,indent=2))
    except (KeyError,ValueError,FileNotFoundError) as e:
        print("MOAG_AUDIT_VALIDATION_FAIL: "+str(e),file=sys.stderr)
        sys.exit(2)
