#!/usr/bin/env python3
"""APA-MOAG offline evidence/topology validator.

This is a read-only preparation stage. It never connects to Archicad and
never creates Walls, Zones, Floors, PLN, a SceneWriter ticket or a native command.
Spatial route graphs MAY contain cycles. Containment MUST NOT contain cycles.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import sys

STATES = {"TEXT_DIRECT", "TOPOLOGY_INFERRED", "RECHECK_REQUIRED", "HYPOTHESIS"}
CONTAINMENT = {"contains", "includes"}
ALLOWED_GEOMETRY_GATES = {"NOT_AUTHORIZED", "APPROVED"}
REQUIRED_PHASES = [
    ("P0_evidence", []),
    ("P1_topology", ["P0_evidence"]),
    ("P2_schematic_skeleton", ["P1_topology"]),
    ("P3_geometric_constraints", ["P2_schematic_skeleton"]),
    ("P4_structural_frame", ["P3_geometric_constraints"]),
    ("P5_walls_slabs_partitions", ["P4_structural_frame"]),
    ("P6_openings", ["P5_walls_slabs_partitions"]),
    ("P7_finishes", ["P6_openings"]),
    ("P8_mep_and_equipment", ["P7_finishes"]),
]
class ModelError(ValueError):
    pass

def _unique(items, kind):
    seen = set()
    for item in items:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"]:
            raise ModelError(kind + ": missing ID")
        if item["id"] in seen:
            raise ModelError(kind + ": duplicate " + item["id"])
        seen.add(item["id"])
    return seen

def _no_cycles(links):
    visited, active = set(), set()
    def visit(v):
        if v in active:
            raise ModelError("containment cycle: " + v)
        if v in visited:
            return
        active.add(v)
        for nxt in links.get(v, ()):
            visit(nxt)
        active.remove(v)
        visited.add(v)
    for k in links:
        visit(k)

def validate(data):
    if data.get("schema") != "APA-MOAG-EVIDENCE-GRAPH/0.1":
        raise ModelError("unsupported graph schema")
    nodes = data.get("nodes")
    edges = data.get("edges")
    sources = data.get("sources")
    if not all(isinstance(x, list) for x in (nodes, edges, sources)):
        raise ModelError("nodes, edges and sources must be lists")
    source_ids = _unique(sources, "source")
    node_ids = _unique(nodes, "node")
    _unique(edges, "edge")
    for src in sources:
        if src.get("medium") != "literary_text":
            raise ModelError("non-literary source is not allowed in evidence list")
        if not isinstance(src.get("url"), str) or not src["url"].startswith("https://"):
            raise ModelError("source requires a navigable HTTPS URL: " + src["id"])
    by_id = {n["id"]: n for n in nodes}
    for node in nodes:
        refs = node.get("source_ids")
        if not isinstance(refs, list) or not refs or any(r not in source_ids for r in refs):
            raise ModelError("node has missing source provenance: " + node["id"])
        if node.get("state") not in STATES:
            raise ModelError("node has unknown evidence state: " + node["id"])
        if node.get("geometry_gate") not in ALLOWED_GEOMETRY_GATES:
            raise ModelError("invalid geometry gate: " + node["id"])
        if node.get("geometry_gate") == "APPROVED" and node.get("state") == "RECHECK_REQUIRED":
            raise ModelError("unverified node cannot have approved geometry: " + node["id"])
        loc = node.get("position")
        if not isinstance(loc, dict):
            raise ModelError("position object required even if unknown: " + node["id"])
        if node.get("geometry_gate") == "NOT_AUTHORIZED" and any(loc.get(k) is not None
                              for k in ("x", "y", "z", "orientation", "dimension_m")):
            raise ModelError("unapproved spatial coordinate or size: " + node["id"])
        if node.get("level") not in (None, 1, 2, 3):
            raise ModelError("unknown level number: " + node["id"])
    containment = defaultdict(list)
    for edge in edges:
        a,b = edge.get("from"), edge.get("to")
        if a not in node_ids or b not in node_ids or a == b:
            raise ModelError("dangling/self edge: " + str(edge.get("id")))
        refs = edge.get("source_ids")
        if not isinstance(refs, list) or not refs or any(r not in source_ids for r in refs):
            raise ModelError("edge has missing source: " + edge["id"])
        if edge.get("state") not in STATES:
            raise ModelError("edge has unknown evidence state: " + edge["id"])
        if not isinstance(edge.get("type"), str) or not edge.get("claim"):
            raise ModelError("edge missing relation or claim: " + edge["id"])
        if edge["type"] in CONTAINMENT:
            containment[a].append(b)
            # All rooms physically contained in a level must share that level.
            left, right = by_id[a].get("level"), by_id[b].get("level")
            if left is not None and right is not None and left != right:
                raise ModelError("cross-level containment: " + edge["id"])
        if edge.get("metric") is not None:
            raise ModelError("unreviewed metric in v0.1: " + edge["id"])
    _no_cycles(containment)
    if data.get("corpus", {}).get("books_exhaustively_checked", -1) != 0:
        raise ModelError("v0.1 cannot assert exhaustive four-book reading")
    return {"validated": True, "nodes":len(nodes), "edges":len(edges),
            "sources":len(sources), "by_level":dict(sorted(Counter(
            str(n.get("level")) for n in nodes).items())),
            "states":dict(sorted(Counter(n["state"] for n in nodes).items())),
            "geometry_ready": False, "native_write_allowed": False,
            "reason": "Evidence extraction and geometric constraints not approved."}

def export_topology(data):
    """Non-executable reference model for later APA graph/SceneWriter translation."""
    result=validate(data)
    return {"schema":"APA-MOAG-TOPOLOGY-SNAPSHOT/0.1",
            "status":"GRAPH_ONLY_NO_COORDINATES",
            "space_refs":[{"id":n["id"],"label":n["label"],"level":n["level"]}
                          for n in data["nodes"]],
            "relationships":[{"id":e["id"],"from":e["from"],"to":e["to"],
                              "relation":e["type"],"state":e["state"],
                              "source_ids":e["source_ids"]}
                             for e in data["edges"]],
            "construction_dag":[{"id":id,"depends_on":deps} for id,deps in REQUIRED_PHASES],
            "gates":{"graph_validated":result["validated"],
                     "geometry_approved":False,"apa_native_execute":False,
                     "scene_writer_write":False},
            "instructions":"NO CreateWalls/Slabs/Doors; build graph and obtain geometry approval."}

def dot(data):
    validate(data)
    def escape(s):
        return json.dumps(str(s),ensure_ascii=False)
    rows=["digraph MOAG {","  graph [label=\"МОАГ: граф пространственных связей (без координат)\",labelloc=t];",
          "  node [shape=box, style=rounded];"]
    for node in data["nodes"]:
        rows.append("  "+escape(node["id"])+" [label="+escape(node["label"]+
             "\\n"+("уровень "+str(node["level"]) if node["level"] is not None else "уровень требует проверки"))+"];")
    for e in data["edges"]:
        color="black" if e["state"]=="TEXT_DIRECT" else "gray"
        rows.append("  "+escape(e["from"])+" -> "+escape(e["to"])+" [label="+escape(e["type"])+
                    ",color="+escape(color)+",style="+escape(
                    "solid" if e["state"]=="TEXT_DIRECT" else "dashed")+"];")
    return "\n".join(rows)+"\n}"

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("graph",type=Path)
    ap.add_argument("--mode",choices=("verify","snapshot","dot"),default="verify")
    ap.add_argument("--out",type=Path)
    args=ap.parse_args(argv)
    try:
        data=json.loads(args.graph.read_text(encoding="utf-8"))
        obj=validate(data) if args.mode=="verify" else (
            export_topology(data) if args.mode=="snapshot" else dot(data))
        result=obj if isinstance(obj,str) else json.dumps(obj,ensure_ascii=False,indent=2)
        if args.out:
            if args.out.exists():
                raise ModelError("refusing to overwrite existing output: "+str(args.out))
            args.out.parent.mkdir(parents=True,exist_ok=True)
            args.out.write_text(result+"\n",encoding="utf-8")
        else:
            print(result)
        return 0
    except (ModelError,ValueError,OSError) as e:
        print("MOAG_VALIDATION_FAIL: "+str(e),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
