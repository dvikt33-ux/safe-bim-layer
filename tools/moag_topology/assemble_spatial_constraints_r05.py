#!/usr/bin/env python3
"""MOAG R05 unified incremental topological + relative area/volume constraint workflow.

Evidence fragments come from reviewed R04/R05 sources; all metric intervals are
noncanonical editable architectural hypotheses. No Archicad model writes.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import progressive_constraint_solver_r05 as topology
import area_volume_solver_r05 as metrics

BASE=Path(__file__).resolve().parents[2]/"docs/research/apa-results/moag/synthesis"

def run(graph, fragments, bounds, parameters=None, room_sizes=None, anchors=None, variants=None):
    variants=[] if variants is None else variants
    if not isinstance(variants,list):
        raise ValueError("PLACEMENT_VARIANTS_MUST_BE_ARRAY")
    top=topology.solve(graph,fragments,anchors)
    area=metrics.solve(bounds,graph,parameters,room_sizes,variants)
    domains={}
    for x in top["known_or_inferred_levels"]:
        domains[x["node_id"]]={x["global_level"]}
    for x in top["level_domains_still_open"]:
        domains[x["node_id"]]=set(x["possible_global_levels"])
    if len(domains)!=top["counts"]["all_nodes"]:
        raise ValueError("LEVEL_DOMAIN_COVERAGE_INCOMPLETE")
    compared=[]
    indexed={v["id"]:v for v in area["placement_variant_comparisons"]}
    for variant in variants:
        v=indexed[variant["id"]]
        contradictions=[]
        uncertain=[]
        for child,host in variant["assignments"].items():
            if child not in domains or host not in domains:
                raise ValueError("UNKNOWN_VARIANT_ENTITY")
            if child==host:
                contradictions.append({"id":child,"host":host,"reason":"SELF_CONTAINMENT"})
                continue
            shared=domains[child]&domains[host]
            if not shared:
                contradictions.append({"id":child,"host":host,"reason":"DISJOINT_SUPPORTED_LEVEL_DOMAINS"})
            elif len(shared)>1:
                uncertain.append({"id":child,"host":host,
                                  "possible_global_levels":sorted(shared)})
        viable=v["admissible_by_area"] and not contradictions
        compared.append({"id":v["id"],"passes_known_topology_and_area":viable,
                         "hard_topology_conflicts":contradictions,
                         "hard_area_conflicts":v["area_conflicts"],
                         "unresolved_level_assignments":uncertain,
                         "secondary_area_utilization_score":v["secondary_area_utilization_score"],
                         "geometry_unique":False,
                         "note":"One passing authored option does not prove it is the only solution in the whole station"})
    compared.sort(key=lambda x:(not x["passes_known_topology_and_area"],
                                 x["secondary_area_utilization_score"],x["id"]))
    accepted=sum(x["passes_known_topology_and_area"] for x in compared)
    return {"schema":"APA-MOAG-COMBINED-CONSTRAINT-RESULT-R05/0.1",
            "status":"CONFLICTS" if area["counts"]["fails"] else "CONSISTENT_PARTIAL_NOT_PROVEN",
            "graph_inventory":{"r04_source_nodes":len(graph["indexed_source_entities"]),
                               "r03_entities":len(graph["indexed_r03_entities"]),
                               "r05_new_entities":len(fragments["physical_entities"]),
                               "observations":len(graph["observations"]),
                               "narrative_movement_steps":len(graph["movements"])},
            "topology":top,"area_and_volume":area,
            "compared_variants":compared,
            "variation_summary":{"submitted":len(compared),"passing":accepted,
              "unique_among_submitted":accepted==1 if compared else False,
              "unique_in_all_possible_geometry":False},
            "gates":{"source_constraints_preserved":True,"coordinates_proven":False,
                     "exact_dimensions_proven":False,"geometry_approved":False,
                     "archicad_write":False}}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--graph",type=Path,default=BASE/"full_indexed_parametric_graph_r04.json")
    p.add_argument("--fragments",type=Path,default=BASE/"progressive_fragments_r05.json")
    p.add_argument("--bounds",type=Path,default=BASE/"area_volume_bounds_r05.json")
    p.add_argument("--r04-parameters",type=Path)
    p.add_argument("--area-overrides",type=Path)
    p.add_argument("--anchors",type=Path)
    p.add_argument("--variants",type=Path)
    p.add_argument("--out",type=Path)
    args=p.parse_args()
    read=lambda path:json.loads(path.read_text(encoding="utf-8")) if path else None
    result=run(read(args.graph),read(args.fragments),read(args.bounds),
               read(args.r04_parameters),read(args.area_overrides),
               read(args.anchors),read(args.variants))
    txt=json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+"\n"
    if args.out:args.out.write_text(txt,encoding="utf-8")
    else:print(txt,end="")
    return 2 if result["status"]=="CONFLICTS" else 0

if __name__=="__main__":raise SystemExit(main())
