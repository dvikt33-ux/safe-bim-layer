#!/usr/bin/env python3
"""R05 incremental constraint solver for MOAG spatial evidence.
Relates unplaced fragments; solves level domains with arc-consistency and
audits connected components. It DOES NOT invent XY, metric elevations or walls.
All inferred levels cite a chain of source-backed restrictions.
"""
from __future__ import annotations
import argparse
from collections import defaultdict, deque
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/"docs/research/apa-results/moag/synthesis"
UNIVERSE={1,2,3}
LEVEL_EQ={"SAME_LEVEL","INHERIT_IF_KNOWN"}
DISCONNECTED={"NOT_SAME_AS","NOT_PROVEN_SAME","NOT_PROVEN_NEAR","POSSIBLY_SAME_AS"}
# This is qualitative connectivity; never geometric wall adjacency.
TOPOLOGICAL={
    "CONTAINS_SPACE","CONTAINS_ACCESS","CONNECTS_ROUTE","BEYOND_RING",
    "ROUTE_TO","GATED_BY","RADIALLY_BRANCHES_TO","CONTAINS_EQUIPMENT",
    "ROUTE_VIA_PASSAGE","HAS_DOOR","CONNECTS_VIA_PORTAL","HAS_EXTERNAL_GATE",
    "OPENING_ROUTE_TO","HAS_HATCH","ROUTE_REACHES_GARBAGE",
    "DOOR_OF","PART_OF_SECTOR","BRANCHES_FROM_SHARED_FORK",
    "DOOR_TO_OTHER_ROOM"
}

def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def solve(graph, fragments, anchors=None):
    anchors={} if anchors is None else anchors
    if not isinstance(anchors,dict):
        raise ValueError("ANCHORS_MUST_BE_OBJECT")
    if fragments.get("schema")!="APA-MOAG-PROGRESSIVE-FRAGMENTS-R05/0.1":
        raise ValueError("BAD_FRAGMENT_SCHEMA")
    if graph.get("schema")!="APA-MOAG-FULL-INDEXED-PARAMETRIC-GRAPH/0.4":
        raise ValueError("BAD_R04_SCHEMA")
    base=graph["indexed_source_entities"]+graph["indexed_r03_entities"]
    allnodes={}
    for n in base:
        val=n.get("level")
        if n["id"] in allnodes or val not in (None,1,2,3):
            raise ValueError("BAD_BASE_NODE")
        allnodes[n["id"]]={"id":n["id"],"name":n["name"],"level":val,"kind":n["kind"],"r05":False}
    for n in fragments["physical_entities"]:
        val=n.get("global_level")
        if n["id"] in allnodes or val not in (None,1,2,3):
            raise ValueError("DUPLICATE_OR_INVALID_R05_NODE")
        allnodes[n["id"]]={"id":n["id"],"name":n["name"],"level":val,"kind":n["kind"],"r05":True}
    edges=fragments["typed_edges"]
    ids=set()
    adjacency=defaultdict(list)
    eq=defaultdict(list)
    evidence=[]
    for e in edges:
        if e["id"] in ids or e["from"] not in allnodes or e["to"] not in allnodes:
            raise ValueError("BAD_FRAGMENT_EDGE")
        ids.add(e["id"])
        if not e.get("source_ids"):
            raise ValueError("UNSOURCED_FRAGMENT_EDGE")
        if e["relation"]=="NOT_SAME_AS" and e["from"]==e["to"]:
            raise ValueError("SELF_NEGATIVE_IDENTITY")
        if e["relation"] in TOPOLOGICAL:
            a,b=e["from"],e["to"]
            adjacency[a].append((b,e["id"]))
            adjacency[b].append((a,e["id"]))
        if e["level_policy"] in LEVEL_EQ:
            eq[e["from"]].append((e["to"],e["id"]))
            eq[e["to"]].append((e["from"],e["id"]))
            evidence.append(e)
    for id,a in anchors.items():
        if id not in allnodes or not isinstance(a,dict) or set(a)!={"global_level"}:
            raise ValueError("UNKNOWN_ANCHOR_OR_SHAPE: "+str(id))
        if type(a["global_level"]) is not int or a["global_level"] not in UNIVERSE:
            raise ValueError("INVALID_GLOBAL_LEVEL_ANCHOR")
    domains={id:({n["level"]} if n["level"] else set(UNIVERSE)) for id,n in allnodes.items()}
    for id,a in anchors.items():
        val=a["global_level"]
        if val not in domains[id]:
            raise ValueError("ANCHOR_CONTRADICTS_TEXT_LEVEL: "+id)
        domains[id]={val}
    # Standard set-intersection propagation of equality constraints.
    queue=deque((id,nbr,edge) for id,lst in eq.items() for nbr,edge in lst)
    proof=defaultdict(set)
    iterations=0
    while queue:
        a,b,eid=queue.popleft()
        iterations+=1
        inter=domains[a]&domains[b]
        if not inter:
            raise ValueError("INCONSISTENT_LEVELS: "+a+" / "+b+" via "+eid)
        if inter!=domains[a]:
            domains[a]=set(inter)
            proof[a].add(eid)
            for c,ee in eq[a]:
                if c!=b: queue.append((c,a,ee))
        if inter!=domains[b]:
            domains[b]=set(inter)
            proof[b].add(eid)
            for c,ee in eq[b]:
                if c!=a: queue.append((c,b,ee))
    # With only qualitative topology, multiple graph components are expected.
    visited=set()
    comps=[]
    for id in sorted(allnodes):
        if id in visited:
            continue
        stack=[id];visited.add(id);members=[];used=set()
        while stack:
            cur=stack.pop()
            members.append(cur)
            for b,eid in adjacency[cur]:
                used.add(eid)
                if b not in visited:
                    visited.add(b);stack.append(b)
        if len(members)>1:
            comps.append({"member_ids":sorted(members),
                "supporting_edge_ids":sorted(used),
                "known_level_members":sum(len(domains[x])==1 for x in members),
                "unresolved_level_members":sum(len(domains[x])>1 for x in members),
                "spatial_embedding_unique":False,
                "status":"CONNECTED_TOPOLOGY_WITHOUT_METRIC_PLACEMENT"})
    unresolved=[
        {"node_id":id,"possible_global_levels":sorted(d),"inference_edges":sorted(proof[id])}
        for id,d in sorted(domains.items()) if len(d)>1
    ]
    singleton=[{"node_id":id,"global_level":next(iter(d)),
                "level_from":"SOURCE_OR_PROVISIONAL_ANCHOR" if (allnodes[id]["level"] is not None or id in anchors) else "PROPAGATED_FROM_EQUALITY",
                "inference_edges":sorted(proof[id])}
               for id,d in sorted(domains.items()) if len(d)==1]
    maybe=[{"from":e["from"],"to":e["to"],"source_ids":e["source_ids"],
            "status":"ALTERNATIVE_HYPOTHESIS_NOT_MERGED"}
           for e in edges if e["relation"]=="POSSIBLY_SAME_AS"]
    negative=[{"from":e["from"],"to":e["to"],"source_ids":e["source_ids"]}
              for e in edges if e["relation"]=="NOT_SAME_AS"]
    return {
        "schema":"APA-MOAG-PROGRESSIVE-SOLUTION-R05/0.1",
        "status":"CONSISTENT_PARTIAL_CONSTRAINT_SOLUTION",
        "counts":{"all_nodes":len(allnodes),"r05_new_nodes":len(fragments["physical_entities"]),
                  "typed_edges":len(edges),"multi_node_components":len(comps),
                  "level_singletons":len(singleton),"level_nonunique":len(unresolved),
                  "hypothetical_identity_links":len(maybe),"negative_identity_links":len(negative)},
        "known_or_inferred_levels":singleton,
        "level_domains_still_open":unresolved,
        "topological_fragments":sorted(comps,key=lambda x:(-len(x["member_ids"]),x["member_ids"][0])),
        "identity_hypotheses":maybe,
        "identity_exclusions":negative,
        "gates":{"metric_coordinates_known":False,"planar_embedding_unique":False,
                 "all_spatial_hypotheses_eliminated":False,"archicad_write":False,
                 "numeric_dimensions_approved":False},
        "explanation":"Only global-level constraints propagate. Route reachability and prose location do NOT prove shared wall, XY or absolute Z. Other hypotheses retained."
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--graph",type=Path,default=BASE/"full_indexed_parametric_graph_r04.json")
    p.add_argument("--fragments",type=Path,default=BASE/"progressive_fragments_r05.json")
    p.add_argument("--anchors",type=Path,help="Optional JSON {permanent_id:{global_level:1|2|3}} with separately documented provenance")
    p.add_argument("--out",type=Path)
    args=p.parse_args()
    g=load(args.graph); f=load(args.fragments)
    a=load(args.anchors) if args.anchors else None
    result=solve(g,f,a)
    payload=json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+"\n"
    if args.out: args.out.write_text(payload,encoding="utf-8")
    else: print(payload,end="")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
