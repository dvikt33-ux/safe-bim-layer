#!/usr/bin/env python3
"""Fail-closed audit for MOAG literary routes and vertical constraints.

Routes are ORDERED physical observations, not Archicad operations.
Levels 1/2/3 are the three global levels; `None` is an unknown intermediate
local stratum, never an automatic fourth Archicad story.
"""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parents[2] / "docs/research/apa-results/moag"
MOVEMENT = {"WALK","RUN","ELEVATOR_UP","ELEVATOR_DOWN","CRAWL",
            "DROP_DOWN","CLIMB_UP","CLIMB_DOWN","TURN_AND_CRAWL",
            "ROPE_LADDER","HATCH_CLIMB","LADDER_UP","DOOR"}
RELATIONS = {"RELATIVE_Z","ROUTE_WITH_ALTERNATE_VERT_PATH"}
def load(path):
    return json.loads(path.read_text(encoding="utf-8"))

def check(root=BASE):
    document=load(root/"v2/character_routes.json")
    if document.get("schema")!="APA-MOAG-CHARACTER-ROUTES/0.1":
        raise ValueError("route schema mismatch")
    graph=load(root/"v1/evidence_graph.json")
    node_ids={n["id"] for n in graph["nodes"]}
    if len(node_ids)!=len(graph["nodes"]):
        raise ValueError("duplicate space graph nodes")
    pages={}
    for book in ["B1","B2","B3","B4"]:
        src=load(root/"v2/pages"/f"{book}.json")
        pages.update({p["id"]:p for p in src["pages"]})
    route_ids=set()
    route_node_ids=set()
    constraints=0
    vertical_moves=0
    for route in document["routes"]:
        rid=route["id"]
        if rid in route_ids or route.get("route_kind")!="OBSERVED_CHARACTER_ROUTE":
            raise ValueError("non-observed or duplicate route: "+rid)
        route_ids.add(rid)
        if not route.get("participants") or not route.get("nodes"):
            raise ValueError("route missing participants or segments: "+rid)
        page_set=set(route.get("site_pages",[]))
        for p in page_set:
            if p not in pages or pages[p]["status"]!="REVIEWED_FULL_PAGE":
                raise ValueError("route cites unread page "+str(p))
        local_ids=set()
        ordered=route["nodes"]
        for step in ordered:
            name=step["id"]
            if name in local_ids or name in route_node_ids:
                raise ValueError("duplicate route anchor "+name)
            local_ids.add(name)
            route_node_ids.add(name)
            if step.get("source_page_id") not in page_set:
                raise ValueError("anchor has wrong source page "+name)
            if step.get("global_level") not in (None,1,2,3):
                raise ValueError("fabricated global floor "+name)
            if step.get("movement_method") not in MOVEMENT:
                raise ValueError("unknown movement "+name)
            if not step.get("observed_constraint") or not step.get("local_stratum"):
                raise ValueError("unjustified route anchor "+name)
            if step.get("relative_xy") is not None or step.get("absolute_z_m") is not None:
                raise ValueError("metric geometry claimed without source "+name)
            if step.get("existing_graph_node") is not None and step["existing_graph_node"] not in node_ids:
                raise ValueError("unknown space graph node "+name)
            if step["movement_method"] in ("CLIMB_UP","DROP_DOWN","ELEVATOR_DOWN","ELEVATOR_UP","ROPE_LADDER","HATCH_CLIMB","LADDER_UP"):
                vertical_moves+=1
        for c in route["constraints"]:
            constraints+=1
            if c.get("kind") not in RELATIONS:
                raise ValueError("unknown route constraint kind")
            if c.get("higher") not in local_ids or c.get("lower") not in local_ids:
                raise ValueError("route constraint refers to external anchor "+rid)
            if c.get("source_page_id") not in page_set or not c.get("claim"):
                raise ValueError("route constraint is not source-backed "+rid)
        for q in route.get("identity_hypotheses",[]):
            if q.get("status")!="UNVERIFIED_SAME_ROOM" and q.get("status")!="UNVERIFIED_SAME_DOOR":
                raise ValueError("hypothetical identity promoted to fact "+rid)
            if q["candidate"] not in local_ids or q["may_match"] not in node_ids:
                raise ValueError("unresolved identity not linked to valid nodes "+rid)
    if not route_ids:
        raise ValueError("no routes")
    return {"schema":"APA-MOAG-ROUTES-VALIDATION/0.1",
            "routes":len(route_ids),"anchors":len(route_node_ids),
            "constraints":constraints,"vertical_movements":vertical_moves,
            "write_authorized":False, "geometry_approved":False}

if __name__=="__main__":
    try:
        print(json.dumps(check(),ensure_ascii=False,indent=2))
    except (ValueError,KeyError,TypeError,OSError) as e:
        print("MOAG_ROUTE_AUDIT_FAIL: "+str(e),file=sys.stderr)
        sys.exit(2)
